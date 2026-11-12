from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Sequence


def normalizar_chasis(valor) -> str:
    if valor is None:
        return ""
    texto = str(valor).strip().upper()
    return re.sub(r"[^A-HJ-NPR-Z0-9]", "", texto)


def extraer_chasis(valor) -> str:
    return normalizar_chasis(valor)


@dataclass(frozen=True)
class Discrepancia:
    tipo: str
    detalle: str
    esperado: str = ""
    obtenido: str = ""


@dataclass(frozen=True)
class ResultadoVerificacion:
    chasis_bl: str
    chasis_vehiculo: str
    coincide: bool
    discrepancias: list[Discrepancia] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.coincide


def comparar_chasis(chasis_bl, chasis_vehiculo) -> ResultadoVerificacion:
    bl = normalizar_chasis(chasis_bl)
    vehiculo = normalizar_chasis(chasis_vehiculo)
    discrepancias: list[Discrepancia] = []

    if not bl and vehiculo:
        discrepancias.append(
            Discrepancia(
                tipo='FALTA_BL',
                detalle='No hay chasis informado en el B/L.',
                esperado=vehiculo,
                obtenido='',
            )
        )
    elif bl and not vehiculo:
        discrepancias.append(
            Discrepancia(
                tipo='FALTA_VEHICULO',
                detalle='No hay chasis asociado al vehículo.',
                esperado='',
                obtenido=bl,
            )
        )
    elif bl and vehiculo and bl != vehiculo:
        discrepancias.append(
            Discrepancia(
                tipo='DISTINTOS',
                detalle='El chasis del BL no coincide con el chasis del vehículo.',
                esperado=vehiculo,
                obtenido=bl,
            )
        )

    return ResultadoVerificacion(
        chasis_bl=bl,
        chasis_vehiculo=vehiculo,
        coincide=not discrepancias,
        discrepancias=discrepancias,
    )


def lineas_de_prorrateo(items: Iterable) -> list[dict]:
    """
    Arma las líneas de prorrateo a partir de los ítems de un embarque.

    Cada línea lleva el valor FOB (`base`), la cantidad de unidades y el peso,
    que son las bases de los criterios de reparto.
    """
    lineas = []
    for item in items:
        factura_item = getattr(item, 'factura_item', None)
        base = Decimal('0')
        peso = None
        cantidad = int(item.cantidad or 0)
        if factura_item is not None:
            base = Decimal(str(factura_item.precio_unitario)) * cantidad
            if item.peso_kg:
                peso = Decimal(str(item.peso_kg))
            elif factura_item.peso_kg:
                peso = Decimal(str(factura_item.peso_kg)) * cantidad
        lineas.append({
            'id': item.pk,
            'descripcion': factura_item.descripcion if factura_item else str(item),
            'base': base,
            'cantidad': cantidad,
            'peso': peso,
        })
    return lineas


def repartir_costos(total: Decimal | str, lineas: Sequence[dict], criterio: str = 'POR_VALOR') -> list[dict]:
    """
    Reparte un total entre las líneas según el criterio indicado.

    Criterios:

    - `POR_VALOR`: proporcional al valor FOB de la línea (`base`).
    - `POR_UNIDAD`: proporcional a la cantidad de unidades (`cantidad`).
    - `POR_PESO`: proporcional al peso de la línea (`peso`).

    Cuando el criterio no tiene datos (por ejemplo, ningún ítem tiene peso),
    el total se reparte en partes iguales. La suma de lo repartido siempre
    cuadra exactamente con el total.
    """
    total_decimal = Decimal(str(total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    items = []
    for linea in lineas:
        base = Decimal(str(linea.get('base', Decimal('0')))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if criterio == 'POR_UNIDAD':
            peso = Decimal(str(linea.get('cantidad') or 1))
        elif criterio == 'POR_PESO':
            peso = Decimal(str(linea.get('peso') or 0))
        else:
            peso = base
        items.append({
            'id': linea.get('id'),
            'descripcion': linea.get('descripcion', ''),
            'base': base,
            'criterio': criterio,
            'peso': peso,
        })

    if not items:
        return []

    base_total = sum((item['peso'] for item in items), Decimal('0'))
    if base_total == 0:
        monto_por_item = (total_decimal / Decimal(len(items))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        resultado = []
        for item in items:
            resultado.append({
                'id': item['id'],
                'descripcion': item['descripcion'],
                'base': item['base'],
                'criterio': criterio,
                'monto': monto_por_item,
            })
        return resultado

    acumulado = Decimal('0')
    resultado = []
    for idx, item in enumerate(items):
        monto = (total_decimal * item['peso'] / base_total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if idx == len(items) - 1:
            monto = total_decimal - acumulado
        acumulado += monto
        resultado.append({
            'id': item['id'],
            'descripcion': item['descripcion'],
            'base': item['base'],
            'criterio': criterio,
            'monto': monto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        })

    return resultado


def repartir_gastos_por_tipo(
    gastos: Iterable,
    lineas: Sequence[dict],
    criterio: str | None = None,
) -> dict:
    """
    Reparte cada gasto del embarque entre las líneas y devuelve el detalle.

    Cada gasto se reparte con **su propio** `criterio_prorrateo` (salvo que se
    fuerce uno con el parámetro `criterio`).

    Devuelve un diccionario con:

    - `detalle`: `{item_id: {tipo_gasto: monto}}`
    - `totales`: `{item_id: monto total asignado}`
    - `por_gasto`: `{gasto_id: {item_id: monto}}`
    """
    detalle: dict = {linea.get('id'): {} for linea in lineas}
    totales: dict = {linea.get('id'): Decimal('0') for linea in lineas}
    por_gasto: dict = {}

    for gasto in gastos:
        criterio_gasto = criterio or getattr(gasto, 'criterio_prorrateo', None) or 'POR_VALOR'
        monto = Decimal(str(getattr(gasto, 'monto_base', 0)))
        reparto = repartir_costos(monto, lineas, criterio=criterio_gasto)
        por_gasto[gasto.pk] = {entrada['id']: entrada['monto'] for entrada in reparto}
        for entrada in reparto:
            item_id = entrada['id']
            tipo = getattr(gasto, 'tipo', 'OTRO')
            detalle[item_id][tipo] = detalle[item_id].get(tipo, Decimal('0')) + entrada['monto']
            totales[item_id] = totales[item_id] + entrada['monto']

    return {'detalle': detalle, 'totales': totales, 'por_gasto': por_gasto}
