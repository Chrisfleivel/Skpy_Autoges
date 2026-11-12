from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from django.conf import settings

from importaciones.calculos import comparar_chasis, lineas_de_prorrateo, repartir_costos, repartir_gastos_por_tipo


@dataclass(frozen=True)
class LineaCosto:
    item_id: int | None
    descripcion: str
    base: Decimal
    monto: Decimal
    moneda: str


@dataclass(frozen=True)
class ResultadoProrrateo:
    ok: bool
    total: Decimal
    lineas: list[LineaCosto] = field(default_factory=list)
    mensaje: str = ""


def verificar_chasis(embarque) -> dict[str, Any]:
    items = list(embarque.items.select_related('factura_item__vehiculo'))
    resultados = []
    ok = True

    for item in items:
        vehiculo = item.factura_item.vehiculo if item.factura_item else None
        valor_bl = item.chasis_bl or ""
        valor_vehiculo = vehiculo.codigo_chasis if vehiculo else ""
        resultado = comparar_chasis(valor_bl, valor_vehiculo)
        ok = ok and resultado.coincide
        resultados.append({
            'id': item.id,
            'descripcion': getattr(item.factura_item, 'descripcion', ''),
            'coincide': resultado.coincide,
            'chasis_bl': resultado.chasis_bl,
            'chasis_vehiculo': resultado.chasis_vehiculo,
            'discrepancias': [
                {
                    'tipo': d.tipo,
                    'detalle': d.detalle,
                    'esperado': d.esperado,
                    'obtenido': d.obtenido,
                }
                for d in resultado.discrepancias
            ],
        })

    return {'ok': ok, 'items': resultados}


def verificar_destino(embarque) -> dict[str, Any]:
    destino = (embarque.destino_final or '').strip()
    if not destino:
        return {'ok': False, 'mensaje': 'El embarque no tiene destino final definido.'}
    return {'ok': True, 'destino_final': destino}


def prorratear_costos(embarque, *, criterio: str | None = None) -> dict[str, Any]:
    """
    Reparte los gastos costeables del embarque entre sus ítems.

    Cada gasto se reparte con **su propio** `criterio_prorrateo` (salvo que se
    fuerce uno con el parámetro `criterio`). El resultado se guarda en
    `EmbarqueItem.costo_prorrateado` y el desglose por tipo de gasto queda
    disponible para el cierre a inventario.
    """
    gastos = list(embarque.gastos.filter(es_costeable=True))
    items = list(embarque.items.select_related('factura_item'))

    if not items:
        return {'ok': False, 'mensaje': 'El embarque no tiene ítems para prorratear.', 'lineas': []}

    if not gastos:
        return {'ok': False, 'mensaje': 'El embarque no tiene gastos costeables.', 'lineas': []}

    lineas = lineas_de_prorrateo(items)
    reparto = repartir_gastos_por_tipo(gastos, lineas, criterio=criterio)
    total = sum((gasto.monto_base for gasto in gastos), Decimal('0'))

    for item in items:
        item.costo_prorrateado = reparto['totales'].get(item.pk, Decimal('0.00'))
        item.save(update_fields=['costo_prorrateado'])

    embarque.gastos_prorrateados = True
    embarque.save(update_fields=['gastos_prorrateados'])

    moneda_base = getattr(settings, 'MONEDA_BASE', 'USD')
    final_lines = [
        LineaCosto(
            item_id=linea['id'],
            descripcion=linea['descripcion'],
            base=linea['base'],
            monto=reparto['totales'].get(linea['id'], Decimal('0.00')),
            moneda=moneda_base,
        )
        for linea in lineas
    ]

    return {
        'ok': True,
        'total': total,
        'lineas': final_lines,
        'detalle': reparto['detalle'],
        'mensaje': 'Prorrateo realizado correctamente.',
    }
