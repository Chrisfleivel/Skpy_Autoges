# contabilidad/services.py
import calendar
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from documentos_financieros.models import Autofactura, ComprobanteEgreso, FacturaComercial, FacturaGastosLocales
from documentos_financieros.services import crear_asiento_contable_desde_documento

from .models import CuentaContable, SaldoMensualCuenta, Asiento, MovimientoContable, ConfiguracionContable


def registrar_asiento_apertura(datos_iniciales, descripcion="ASIENTO DE APERTURA", fecha=None):
    """
    Crea un asiento de apertura de forma transaccional.

    datos_iniciales: lista de diccionarios con estructura:
    {'codigo_cuenta': '1.1.01', 'monto': 1000000, 'tipo': 'debe'/'haber'}
    """
    if fecha is None:
        fecha = date(2026, 1, 1)

    if not datos_iniciales:
        raise ValueError("Debe proporcionar al menos un movimiento para el asiento de apertura.")

    with transaction.atomic():
        asiento = Asiento.objects.create(
            descripcion=descripcion,
            fecha=fecha,
            documento=None,
            tasa_cambio_al_momento=1.00,
        )

        try:
            movimientos = []
            for item in datos_iniciales:
                codigo_cuenta = item.get('codigo_cuenta')
                monto = Decimal(str(item.get('monto', 0)))
                tipo = item.get('tipo', '').lower()

                if not codigo_cuenta:
                    raise ValueError("Cada movimiento debe incluir un código de cuenta.")
                if monto <= 0:
                    raise ValueError(f"El monto para la cuenta {codigo_cuenta} debe ser mayor a cero.")
                if tipo not in {'debe', 'haber'}:
                    raise ValueError(f"Tipo inválido para la cuenta {codigo_cuenta}: {tipo}")

                cuenta = CuentaContable.objects.filter(codigo=codigo_cuenta).first()
                if not cuenta:
                    raise ValueError(f"No existe la cuenta contable con código {codigo_cuenta}.")

                movimientos.append(
                    MovimientoContable(
                        asiento=asiento,
                        cuenta=cuenta,
                        debe=monto if tipo == 'debe' else Decimal('0.00'),
                        haber=monto if tipo == 'haber' else Decimal('0.00'),
                    )
                )

            MovimientoContable.objects.bulk_create(movimientos)
            asiento.full_clean()
            validar_asiento(asiento)
        except Exception:
            transaction.set_rollback(True)
            raise

        return asiento


def ejecutar_cierre_mensual(anio, mes):
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fecha_corte = date(anio, mes, ultimo_dia)

    cuentas = CuentaContable.objects.all()
    resultados = []

    with transaction.atomic():
        for cuenta in cuentas:
            saldo = cuenta.get_saldo(fecha_corte)
            cierre, creado = SaldoMensualCuenta.objects.update_or_create(
                cuenta=cuenta,
                anio=anio,
                mes=mes,
                defaults={'saldo_final': saldo}
            )
            resultados.append((cuenta, cierre, creado))

        config = ConfiguracionContable.objects.first()
        if config and (config.fecha_cierre_bloqueo is None or config.fecha_cierre_bloqueo < fecha_corte):
            config.fecha_cierre_bloqueo = fecha_corte
            config.save(update_fields=['fecha_cierre_bloqueo'])

    return resultados

def validar_asiento(asiento):
    """
    Valida que el asiento esté balanceado (debe = haber) usando Decimal.
    """
    total_debe = sum((Decimal(str(m.debe)) if m.debe is not None else Decimal('0.00')) for m in asiento.movimientos.all())
    total_haber = sum((Decimal(str(m.haber)) if m.haber is not None else Decimal('0.00')) for m in asiento.movimientos.all())

    if total_debe != total_haber:
        raise ValueError(f"Asiento {asiento.id} no está balanceado: Debe={total_debe}, Haber={total_haber}")

    for movimiento in asiento.movimientos.all():
        debe = Decimal(str(movimiento.debe)) if movimiento.debe is not None else Decimal('0.00')
        haber = Decimal(str(movimiento.haber)) if movimiento.haber is not None else Decimal('0.00')
        if debe and haber:
            raise ValueError(f"El movimiento {movimiento.id} no puede tener valores en debe y haber simultáneamente.")
        
    


@transaction.atomic
def facturar_documento_financiero(documento, *, tipo_documento, numero_documento=None, proveedor=None, monto_total=None, descripcion=None):
    """Crea un documento financiero de compra/gasto y genera su asiento contable."""
    if documento is None:
        raise ValueError("Debe proporcionar un documento o un objeto con los datos para facturar.")

    if not tipo_documento:
        raise ValueError("Debe indicar el tipo de documento a facturar.")

    documento_obj = documento
    if isinstance(documento_obj, int):
        raise ValueError("Debe proporcionar un objeto de documento, no un ID entero.")

    proveedor = proveedor or getattr(documento_obj, 'proveedor', None)
    monto_total = Decimal(str(monto_total if monto_total is not None else getattr(documento_obj, 'monto_total', 0) or 0))
    numero_doc = numero_documento or getattr(documento_obj, 'numero_documento', None) or getattr(documento_obj, 'id', None)
    numero_pedido = getattr(documento_obj, 'id', None) or getattr(documento_obj, 'pk', None)

    model_map = {
        'factura_comercial': FacturaComercial,
        'autofactura': Autofactura,
        'factura_gastos_locales': FacturaGastosLocales,
        'comprobante_egreso': ComprobanteEgreso,
    }
    if tipo_documento not in model_map:
        raise ValueError(f"Tipo de documento no soportado: {tipo_documento}")

    model_class = model_map[tipo_documento]
    kwargs = {
        'tipo_documento': tipo_documento,
        'numero_documento': str(numero_doc),
        'proveedor': proveedor,
        'monto_total': monto_total,
        'total_bruto': monto_total,
        'total_impuestos': Decimal('0.00'),
        'fecha_emision': timezone.now(),
        'estado': 'aprobado',
        'estado_sifen': 'aprobado',
    }

    if tipo_documento == 'factura_comercial':
        kwargs.update({
            'numero_comercial': str(numero_doc),
            'valor_fob': monto_total,
            'valor_cif': monto_total,
        })
    elif tipo_documento == 'autofactura':
        kwargs['tipo_factura'] = getattr(documento_obj, 'tipo_factura', 'contado')
    elif tipo_documento == 'factura_gastos_locales':
        kwargs.update({
            'tipo_gasto': getattr(documento_obj, 'tipo_gasto', 'otros'),
            'capitalizable': getattr(documento_obj, 'capitalizable', False),
        })
    elif tipo_documento == 'comprobante_egreso':
        kwargs.update({
            'beneficiario': getattr(documento_obj, 'beneficiario', None) or getattr(proveedor, 'nombre', None),
            'medio_pago': getattr(documento_obj, 'medio_pago', 'transferencia'),
        })

    factura = model_class.objects.create(**kwargs)

    descripcion = descripcion or f"Factura de Compra {numero_doc} - Pedido {numero_pedido}"
    asiento = crear_asiento_contable_desde_documento(
        factura,
        descripcion=descripcion,
        force=True,
    )

    if hasattr(documento_obj, 'estado'):
        documento_obj.estado = 'FACTURADO'
        if hasattr(documento_obj, 'save'):
            documento_obj.save(update_fields=['estado'])

    return factura, asiento, documento_obj


@transaction.atomic
def facturar_pedido_compra(pedido, numero_factura_legal):
    """Factura un pedido de compra y genera el asiento contable asociado."""
    factura, asiento, pedido_obj = facturar_documento_financiero(
        pedido,
        tipo_documento='factura_comercial',
        numero_documento=numero_factura_legal,
        proveedor=getattr(pedido, 'proveedor', None),
        monto_total=getattr(pedido, 'monto_total', 0),
        descripcion=f"Factura de Compra {numero_factura_legal} - Pedido {getattr(pedido, 'id', None)}",
    )
    return factura, asiento, pedido_obj



