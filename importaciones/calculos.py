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


def repartir_costos(total: Decimal | str, lineas: Sequence[dict], criterio: str = 'POR_VALOR') -> list[dict]:
    total_decimal = Decimal(str(total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    items = []
    for linea in lineas:
        base = Decimal(str(linea.get('base', Decimal('0')))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        items.append({
            'id': linea.get('id'),
            'descripcion': linea.get('descripcion', ''),
            'base': base,
            'criterio': criterio,
        })

    if not items:
        return []

    base_total = sum((item['base'] for item in items), Decimal('0'))
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
        monto = (total_decimal * item['base'] / base_total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
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
