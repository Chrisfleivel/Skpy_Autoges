"""
Conciliación informativa de los documentos de importación.

Compara, para cada factura comercial, los tres documentos de la operación:

1. la **factura comercial** (`compras.FacturaComercial`),
2. el **B/L y sus contenedores** (`importaciones.Embarque`),
3. la **liquidación bancaria y su pago** (`OrdenPagoExterior` / `finanzas.PagoExterior`).

La conciliación es **informativa**: no bloquea la carga de los documentos ni la
operación. Solo señala, con semáforos, qué falta cargar y qué no cuadra, para
que el usuario pueda corregirlo cuando tenga todos los documentos a la vista.

El cálculo se hace al vuelo: no se persiste ningún estado de conciliación.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Sum

from compras.models import FacturaComercial
from finanzas.models import PagoExterior

from .calculos import normalizar_chasis
from .models import DocumentoAdjunto, EmbarqueItem


class EstadoConciliacion:
    """Estados posibles de un hallazgo de conciliación."""

    OK = 'OK'
    ATENCION = 'ATENCION'
    DIFERENCIA = 'DIFERENCIA'
    PENDIENTE = 'PENDIENTE'

    ETIQUETAS = {
        OK: 'Cuadra',
        ATENCION: 'Revisar',
        DIFERENCIA: 'No cuadra',
        PENDIENTE: 'Sin cargar',
    }

    SEMAFOROS = {
        OK: 'success',
        ATENCION: 'warning',
        DIFERENCIA: 'danger',
        PENDIENTE: 'secondary',
    }

    # Orden de severidad: el peor estado manda en el resumen.
    SEVERIDAD = {
        DIFERENCIA: 0,
        ATENCION: 1,
        PENDIENTE: 2,
        OK: 3,
    }

    @classmethod
    def etiqueta(cls, estado: str) -> str:
        return cls.ETIQUETAS.get(estado, estado)

    @classmethod
    def semaforo(cls, estado: str) -> str:
        return cls.SEMAFOROS.get(estado, 'secondary')

    @classmethod
    def peor(cls, estados) -> str:
        """Devuelve el estado más severo de la lista."""
        estados = [e for e in estados if e]
        if not estados:
            return cls.OK
        return min(estados, key=lambda e: cls.SEVERIDAD.get(e, 99))


@dataclass(frozen=True)
class Hallazgo:
    """Resultado de una verificación puntual entre documentos."""

    concepto: str
    estado: str
    detalle: str = ''
    valor: str = ''

    @property
    def etiqueta(self) -> str:
        return EstadoConciliacion.etiqueta(self.estado)

    @property
    def semaforo(self) -> str:
        return EstadoConciliacion.semaforo(self.estado)


@dataclass(frozen=True)
class Conciliacion:
    """Conciliación de los tres documentos de una misma factura."""

    factura: FacturaComercial
    hallazgos: tuple = field(default_factory=tuple)
    orden: object = None
    pago: object = None
    embarques: tuple = field(default_factory=tuple)
    detalles: tuple = field(default_factory=tuple)

    @property
    def estado(self) -> str:
        return EstadoConciliacion.peor([h.estado for h in self.hallazgos])

    @property
    def etiqueta(self) -> str:
        return EstadoConciliacion.etiqueta(self.estado)

    @property
    def semaforo(self) -> str:
        return EstadoConciliacion.semaforo(self.estado)

    @property
    def conciliado(self) -> bool:
        return self.estado == EstadoConciliacion.OK

    @property
    def unidades_facturadas(self) -> int:
        return sum((item.cantidad for item in self.factura.items.all()), 0)

    @property
    def unidades_embarcadas(self) -> int:
        return sum((detalle.cantidad for detalle in self.detalles), 0)

    @property
    def monto_pagado(self) -> Decimal:
        """Importe efectivamente pagado (calculado desde los pagos)."""
        return _monto_pagado(self.factura)

    @property
    def saldo_pendiente(self) -> Decimal:
        return self.factura.total_declarado - self.monto_pagado

def _detalles_embarque(factura: FacturaComercial):
    """Ítems del embarque que pertenecen a los renglones de la factura."""
    return list(
        EmbarqueItem.objects.filter(factura_item__factura=factura)
        .select_related('embarque', 'contenedor', 'factura_item')
    )


def _monto_pagado(factura: FacturaComercial) -> Decimal:
    """
    Importe efectivamente pagado a la factura.

    Se calcula desde los pagos y no desde `FacturaComercial.monto_pagado`,
    que puede estar desactualizado en memoria.
    """
    total = (
        factura.pagos.exclude(estado=PagoExterior.Estado.RECHAZADO)
        .aggregate(total=Sum('importe'))['total']
        or Decimal('0')
    )
    return total


def _conciliar_embarque(factura: FacturaComercial, detalles) -> tuple:
    """Verificaciones entre la factura comercial y el B/L con sus contenedores."""
    hallazgos = []

    # --- ¿Hay embarque? ---------------------------------------------------
    embarques = list({d.embarque_id: d.embarque for d in detalles}.values())
    if not embarques:
        hallazgos.append(Hallazgo(
            concepto='Embarque',
            estado=EstadoConciliacion.PENDIENTE,
            detalle='La factura todavía no tiene unidades embarcadas.',
        ))
    else:
        referencias = ', '.join(
            f'#{e.pk} {e.referencia_interna or e.bl_numero or ""}'.strip() for e in embarques
        )
        hallazgos.append(Hallazgo(
            concepto='Embarque',
            estado=EstadoConciliacion.OK,
            detalle=f'Ítems embarcados en {referencias}.',
            valor=str(len(embarques)),
        ))

    # --- Unidades facturadas vs embarcadas -------------------------------
    unidades_facturadas = sum((item.cantidad for item in factura.items.all()), 0)
    unidades_embarcadas = sum((d.cantidad for d in detalles), 0)
    if not unidades_embarcadas:
        hallazgos.append(Hallazgo(
            concepto='Unidades',
            estado=EstadoConciliacion.PENDIENTE,
            detalle='Ninguna unidad de la factura está embarcada.',
            valor=f'0 / {unidades_facturadas}',
        ))
    elif unidades_embarcadas > unidades_facturadas:
        hallazgos.append(Hallazgo(
            concepto='Unidades',
            estado=EstadoConciliacion.DIFERENCIA,
            detalle=(
                f'Se embarcaron {unidades_embarcadas} unidades y la factura '
                f'solo factura {unidades_facturadas}.'
            ),
            valor=f'{unidades_embarcadas} / {unidades_facturadas}',
        ))
    elif unidades_embarcadas < unidades_facturadas:
        hallazgos.append(Hallazgo(
            concepto='Unidades',
            estado=EstadoConciliacion.ATENCION,
            detalle=(
                f'Faltan {unidades_facturadas - unidades_embarcadas} unidades por embarcar.'
            ),
            valor=f'{unidades_embarcadas} / {unidades_facturadas}',
        ))
    else:
        hallazgos.append(Hallazgo(
            concepto='Unidades',
            estado=EstadoConciliacion.OK,
            detalle='Las unidades embarcadas coinciden con las facturadas.',
            valor=f'{unidades_embarcadas} / {unidades_facturadas}',
        ))

    # --- Chasis de la factura vs chasis del B/L ----------------------------
    chasis_declarados = [
        item.chasis for item in factura.items.all() if item.chasis
    ]
    if not chasis_declarados:
        hallazgos.append(Hallazgo(
            concepto='Chasis',
            estado=EstadoConciliacion.PENDIENTE,
            detalle='La factura no declara chassis para contrastar con el B/L.',
        ))
    elif not unidades_embarcadas:
        hallazgos.append(Hallazgo(
            concepto='Chasis',
            estado=EstadoConciliacion.PENDIENTE,
            detalle='Sin embarque no se pueden contrastar los chasis.',
        ))
    else:
        chasis_bl = {normalizar_chasis(d.chasis_bl) for d in detalles if d.chasis_bl}
        faltantes = [
            chasis for chasis in chasis_declarados
            if normalizar_chasis(chasis) not in chasis_bl
        ]
        if faltantes:
            hallazgos.append(Hallazgo(
                concepto='Chasis',
                estado=EstadoConciliacion.DIFERENCIA,
                detalle=(
                    f'{len(faltantes)} chassis de la factura no aparecen en el B/L: '
                    f'{", ".join(faltantes[:5])}'
                    + ('…' if len(faltantes) > 5 else '')
                ),
                valor=f'{len(chasis_declarados) - len(faltantes)} / {len(chasis_declarados)}',
            ))
        else:
            hallazgos.append(Hallazgo(
                concepto='Chasis',
                estado=EstadoConciliacion.OK,
                detalle='Todos los chassis de la factura aparecen en el B/L.',
                valor=f'{len(chasis_declarados)} / {len(chasis_declarados)}',
            ))

    # --- Contenedores ------------------------------------------------------
    sin_contenedor = [d for d in detalles if not d.contenedor_id]
    provisorios = [
        d for d in detalles
        if d.contenedor_id and (d.contenedor.numero or '').upper() == 'SIN-DEFINIR'
    ]
    if sin_contenedor:
        hallazgos.append(Hallazgo(
            concepto='Contenedores',
            estado=EstadoConciliacion.DIFERENCIA,
            detalle=f'{len(sin_contenedor)} ítems embarcados no tienen contenedor asignado.',
        ))
    elif provisorios:
        hallazgos.append(Hallazgo(
            concepto='Contenedores',
            estado=EstadoConciliacion.ATENCION,
            detalle=(
                f'{len(provisorios)} ítems siguen en el contenedor provisorio '
                '"SIN-DEFINIR": definí el contenedor real del B/L.'
            ),
        ))
    elif detalles:
        contenedores = {d.contenedor_id for d in detalles}
        hallazgos.append(Hallazgo(
            concepto='Contenedores',
            estado=EstadoConciliacion.OK,
            detalle=f'Los ítems están asignados a {len(contenedores)} contenedor(es).',
            valor=str(len(contenedores)),
        ))
    else:
        hallazgos.append(Hallazgo(
            concepto='Contenedores',
            estado=EstadoConciliacion.PENDIENTE,
            detalle='Todavía no hay contenedores cargados en el embarque.',
        ))

    # --- Documento B/L adjunto ---------------------------------------------
    sin_bl = [
        e for e in embarques
        if not e.documentos.filter(tipo=DocumentoAdjunto.Tipo.BL).exists()
    ]
    if not embarques:
        hallazgos.append(Hallazgo(
            concepto='Documento B/L',
            estado=EstadoConciliacion.PENDIENTE,
            detalle='Sin embarque no hay B/L que adjuntar.',
        ))
    elif sin_bl:
        hallazgos.append(Hallazgo(
            concepto='Documento B/L',
            estado=EstadoConciliacion.ATENCION,
            detalle=(
                f'{len(sin_bl)} embarque(s) sin el B/L escaneado adjunto: '
                + ', '.join(f'#{e.pk}' for e in sin_bl)
            ),
        ))
    else:
        hallazgos.append(Hallazgo(
            concepto='Documento B/L',
            estado=EstadoConciliacion.OK,
            detalle='Todos los embarques tienen el B/L adjunto.',
        ))

    return hallazgos, embarques


def _conciliar_liquidacion(factura: FacturaComercial):
    """Verificaciones entre la factura comercial y la liquidación bancaria."""
    hallazgos = []

    orden = None
    ordenes = list(factura.ordenes_pago.all())
    if ordenes:
        orden = sorted(ordenes, key=lambda o: (o.pk or 0), reverse=True)[0]
        detalle = f'Liquidación #{orden.pk} · {orden.referencia_op or "sin referencia"}'
        if len(ordenes) > 1:
            detalle += f' (hay {len(ordenes)} liquidaciones vinculadas)'
        hallazgos.append(Hallazgo(
            concepto='Liquidación',
            estado=EstadoConciliacion.OK,
            detalle=detalle,
            valor=str(orden.pk),
        ))
    elif factura.pagos.exists():
        hallazgos.append(Hallazgo(
            concepto='Liquidación',
            estado=EstadoConciliacion.ATENCION,
            detalle='Hay un pago al exterior registrado pero sin liquidación vinculada.',
        ))
    else:
        hallazgos.append(Hallazgo(
            concepto='Liquidación',
            estado=EstadoConciliacion.PENDIENTE,
            detalle='La factura todavía no tiene liquidación de orden de pago.',
        ))

    pago = orden.pago_exterior if orden and orden.pago_exterior_id else None

    # --- Asiento financiero ------------------------------------------------
    if orden and pago is None:
        hallazgos.append(Hallazgo(
            concepto='Pago registrado',
            estado=EstadoConciliacion.ATENCION,
            detalle='La liquidación no tiene asiento financiero registrado.',
        ))
    elif orden:
        hallazgos.append(Hallazgo(
            concepto='Pago registrado',
            estado=EstadoConciliacion.OK,
            detalle=f'Pago {pago.referencia_op or pago.pk} en estado {pago.get_estado_display()}.',
            valor=pago.get_estado_display(),
        ))

    # --- Moneda -------------------------------------------------------------
    if pago:
        if pago.moneda != factura.moneda:
            hallazgos.append(Hallazgo(
                concepto='Moneda',
                estado=EstadoConciliacion.DIFERENCIA,
                detalle=(
                    f'El pago está en {pago.moneda} y la factura en {factura.moneda}.'
                ),
            ))
        else:
            hallazgos.append(Hallazgo(
                concepto='Moneda',
                estado=EstadoConciliacion.OK,
                detalle=f'Factura y pago en {factura.moneda}.',
            ))

    # --- Importe pagado ----------------------------------------------------
    if pago:
        pagado = _monto_pagado(factura)
        saldo = factura.total_declarado - pagado
        if pago.estado == pago.Estado.RECHAZADO:
            hallazgos.append(Hallazgo(
                concepto='Importe',
                estado=EstadoConciliacion.ATENCION,
                detalle='El pago al exterior está rechazado: la factura sigue impaga.',
                valor=str(saldo),
            ))
        elif saldo <= 0:
            hallazgos.append(Hallazgo(
                concepto='Importe',
                estado=EstadoConciliacion.OK,
                detalle='La factura está cancelada.',
                valor=str(factura.total_declarado),
            ))
        elif pagado > 0:
            hallazgos.append(Hallazgo(
                concepto='Importe',
                estado=EstadoConciliacion.ATENCION,
                detalle=f'Pago parcial: queda un saldo pendiente de {saldo} {factura.moneda}.',
                valor=str(pagado),
            ))
        else:
            hallazgos.append(Hallazgo(
                concepto='Importe',
                estado=EstadoConciliacion.ATENCION,
                detalle=(
                    f'El pago no impacta el saldo de la factura: faltan '
                    f'{saldo} {factura.moneda}.'
                ),
                valor=str(pagado),
            ))

    # --- Comisión bancaria --------------------------------------------------
    if pago and (pago.comision or Decimal('0')) > 0:
        if pago.gasto_comision_id:
            hallazgos.append(Hallazgo(
                concepto='Comisión bancaria',
                estado=EstadoConciliacion.OK,
                detalle=(
                    f'Imputada al embarque #{pago.gasto_comision.embarque_id} '
                    f'como {pago.gasto_comision.get_tipo_display()}.'
                ),
                valor=str(pago.comision),
            ))
        else:
            hallazgos.append(Hallazgo(
                concepto='Comisión bancaria',
                estado=EstadoConciliacion.ATENCION,
                detalle=(
                    'La comisión del pago no está imputada a ningún embarque: '
                    'indicá el embarque en el registro del pago.'
                ),
                valor=str(pago.comision),
            ))

    return hallazgos, orden, pago


def conciliar_factura(factura: FacturaComercial) -> Conciliacion:
    """Concilia los tres documentos de la operación de una factura."""
    detalles = _detalles_embarque(factura)

    hallazgos_embarque, embarques = _conciliar_embarque(factura, detalles)
    hallazgos_liquidacion, orden, pago = _conciliar_liquidacion(factura)

    return Conciliacion(
        factura=factura,
        hallazgos=tuple(hallazgos_embarque + hallazgos_liquidacion),
        orden=orden,
        pago=pago,
        embarques=tuple(embarques),
        detalles=tuple(detalles),
    )


def conciliar_facturas(facturas=None):
    """Concilia un conjunto de facturas y devuelve las conciliaciones."""
    if facturas is None:
        facturas = (
            FacturaComercial.objects
            .exclude(estado=FacturaComercial.Estado.ANULADA)
            .select_related('proveedor')
            .prefetch_related('items', 'ordenes_pago', 'pagos')
        )
    return [conciliar_factura(factura) for factura in facturas]
