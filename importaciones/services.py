from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from django.conf import settings

from importaciones.calculos import comparar_chasis, repartir_costos


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


def prorratear_costos(embarque, *, criterio: str = 'POR_VALOR') -> dict[str, Any]:
    gastos = list(embarque.gastos.filter(es_costeable=True))
    items = list(embarque.items.select_related('factura_item'))

    if not items:
        return {'ok': False, 'mensaje': 'El embarque no tiene ítems para prorratear.', 'lineas': []}

    if not gastos:
        return {'ok': False, 'mensaje': 'El embarque no tiene gastos costeables.', 'lineas': []}

    total = sum((gasto.monto_base for gasto in gastos), Decimal('0'))
    lineas = []
    for item in items:
        base = Decimal('0')
        if getattr(item, 'factura_item', None) is not None:
            base = (item.factura_item.precio_unitario * item.cantidad)
        lineas.append({'id': item.pk, 'descripcion': item.factura_item.descripcion if item.factura_item else str(item), 'base': base})

    reparto = repartir_costos(total, lineas, criterio=criterio)

    for entrada in reparto:
        item = next((i for i in items if i.pk == entrada['id']), None)
        if item is None:
            continue
        item.costo_prorrateado = entrada['monto']
        item.save(update_fields=['costo_prorrateado'])

    embarque.gastos_prorrateados = True
    embarque.save(update_fields=['gastos_prorrateados'])

    moneda_base = getattr(settings, 'MONEDA_BASE', 'USD')
    final_lines = [
        LineaCosto(
            item_id=item['id'],
            descripcion=item['descripcion'],
            base=item['base'],
            monto=item['monto'],
            moneda=moneda_base,
        )
        for item in reparto
    ]

    return {
        'ok': True,
        'total': total,
        'lineas': final_lines,
        'mensaje': 'Prorrateo realizado correctamente.',
    }
