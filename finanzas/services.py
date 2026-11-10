from __future__ import annotations

import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from compras.models import FacturaComercial
from importaciones.models import Embarque, GastoImportacion

from .models import PagoExterior

MONEDA_BASE = getattr(settings, "MONEDA_BASE", "USD")
CENTAVO = Decimal("0.01")

_ESTADOS_PAGO = (
    FacturaComercial.Estado.CONFIRMADA,
    FacturaComercial.Estado.PAGO_PARCIAL,
    FacturaComercial.Estado.PAGADA,
)


def _dinero(valor) -> Decimal:
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


@transaction.atomic
def sincronizar_factura(factura: FacturaComercial, *, usuario=None) -> FacturaComercial:
    """Recalcula monto_pagado y mueve la factura entre estados de pago."""
    factura = FacturaComercial.objects.select_for_update().get(pk=factura.pk)
    pagado = (
        factura.pagos.exclude(estado=PagoExterior.Estado.RECHAZADO)
        .aggregate(t=Sum("importe"))["t"] or Decimal("0")
    )
    factura.monto_pagado = pagado
    factura.save(update_fields=["monto_pagado", "actualizado"])

    if factura.estado not in _ESTADOS_PAGO:
        return factura

    if pagado >= factura.total_declarado:
        objetivo = FacturaComercial.Estado.PAGADA
    elif pagado > 0:
        objetivo = FacturaComercial.Estado.PAGO_PARCIAL
    else:
        objetivo = FacturaComercial.Estado.CONFIRMADA

    if objetivo != factura.estado:
        factura.cambiar_estado(
            objetivo,
            usuario=usuario,
            nota=f"Pagado {pagado} de {factura.total_declarado}",
        )

    try:
        Vehiculo = apps.get_model("inventario", "Vehiculo")
    except LookupError:
        return factura

    vehiculos = Vehiculo.objects.filter(items_factura__factura=factura)
    if objetivo == FacturaComercial.Estado.PAGADA:
        vehiculos.filter(estado="COMPRADO").update(estado="PAGADO")
    else:
        vehiculos.filter(estado="PAGADO").update(estado="COMPRADO")

    return factura


@transaction.atomic
def registrar_pago_exterior(
    factura: FacturaComercial,
    *,
    fecha_operacion: datetime.date,
    importe,
    comision=Decimal("0"),
    embarque: Embarque | None = None,
    usuario=None,
    **datos,
) -> PagoExterior:
    """Crea una orden de pago al exterior y sincroniza la factura."""
    if "estado" in datos:
        raise ValueError("El estado del pago no se puede indicar: lo gestiona la máquina de estados.")

    factura = FacturaComercial.objects.select_for_update().get(pk=factura.pk)
    if factura.estado not in (
        FacturaComercial.Estado.CONFIRMADA,
        FacturaComercial.Estado.PAGO_PARCIAL,
    ):
        raise ValidationError(f"No se puede pagar una factura en estado {factura.estado}.")

    importe = _dinero(importe)
    comision = _dinero(comision)
    if importe <= 0:
        raise ValidationError("El importe debe ser mayor que cero.")
    if importe > factura.saldo_pendiente:
        raise ValidationError(
            f"El importe ({importe}) supera el saldo pendiente de la factura ({factura.saldo_pendiente})."
        )

    datos.setdefault("moneda", factura.moneda)
    if datos.get("moneda") != factura.moneda:
        raise ValidationError("La moneda del pago debe coincidir con la moneda de la factura.")

    pago = PagoExterior(
        factura=factura,
        fecha_operacion=fecha_operacion,
        importe=importe,
        comision=comision,
        **datos,
    )
    pago.full_clean()
    pago.save()

    sincronizar_factura(factura, usuario=usuario)

    if embarque is not None and comision > 0:
        asignar_comision_a_embarque(pago, embarque)

    return pago


@transaction.atomic
def acreditar_pago(pago: PagoExterior, *, fecha: datetime.date | None = None, usuario=None) -> PagoExterior:
    pago.fecha_acreditacion = fecha or datetime.date.today()
    return pago.cambiar_estado(
        PagoExterior.Estado.ACREDITADO,
        usuario=usuario,
        nota="Acreditación confirmada",
    )


@transaction.atomic
def rechazar_pago(pago: PagoExterior, *, motivo: str, usuario=None) -> PagoExterior:
    """Rechaza o devuelve un pago. La factura y los vehículos retroceden en el hook del modelo."""
    pago.motivo_rechazo = motivo
    return pago.cambiar_estado(
        PagoExterior.Estado.RECHAZADO,
        usuario=usuario,
        nota=motivo,
    )


@transaction.atomic
def asignar_comision_a_embarque(pago: PagoExterior, embarque: Embarque) -> GastoImportacion:
    """Crea el gasto de comisión bancaria asociado al embarque."""
    pago = PagoExterior.objects.select_for_update().get(pk=pago.pk)

    if pago.estado == PagoExterior.Estado.RECHAZADO:
        raise ValidationError("El pago está rechazado: no genera gastos.")
    if pago.comision <= 0:
        raise ValidationError("El pago no tiene comisión bancaria.")
    if not embarque.items.filter(factura_item__factura=pago.factura).exists():
        raise ValidationError("El embarque no incluye ítems de la factura de este pago.")

    if pago.gasto_comision_id:
        if pago.gasto_comision.embarque_id == embarque.pk:
            return pago.gasto_comision
        raise ValidationError(
            "La comisión ya está imputada a otro embarque. Retírela primero con retirar_comision()."
        )

    if pago.moneda == MONEDA_BASE:
        tipo_cambio = Decimal("1")
    elif pago.cotizacion and pago.cotizacion > 0:
        tipo_cambio = pago.cotizacion
    else:
        raise ValidationError(
            f"El pago está en {pago.moneda} y la moneda base es {MONEDA_BASE}: cargue la cotización del pago."
        )

    gasto = GastoImportacion(
        embarque=embarque,
        tipo=GastoImportacion.Tipo.COMISION_BANCARIA,
        descripcion=f"Comisión orden de pago {pago.referencia_op or pago.pk}",
        fecha=pago.fecha_operacion,
        monto=pago.comision,
        moneda=pago.moneda,
        tipo_cambio=tipo_cambio,
        criterio_prorrateo=GastoImportacion.Criterio.POR_VALOR,
    )
    gasto.full_clean()
    gasto.save()

    pago.gasto_comision = gasto
    pago.save(update_fields=["gasto_comision", "actualizado"])
    return gasto


@transaction.atomic
def retirar_comision(pago: PagoExterior) -> None:
    """Elimina el gasto de comisión asociado al pago."""
    if not pago.gasto_comision_id:
        return

    gasto = pago.gasto_comision
    pago.gasto_comision = None
    pago.save(update_fields=["gasto_comision", "actualizado"])
    gasto.delete()
