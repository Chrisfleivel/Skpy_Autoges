from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

DECIMALES_COSTO = Decimal('0.0001')


def costo_promedio_ponderado(
    stock_actual: int,
    costo_actual: Decimal | None,
    cantidad_entrada: int,
    costo_entrada: Decimal,
) -> Decimal:
    """Calcula el costo promedio ponderado luego de una entrada de stock."""
    if cantidad_entrada <= 0:
        raise ValueError('La cantidad de entrada debe ser mayor que cero.')

    costo_entrada = Decimal(costo_entrada)
    if costo_entrada < 0:
        raise ValueError('El costo de entrada no puede ser negativo.')

    if stock_actual <= 0 or costo_actual is None:
        return costo_entrada.quantize(DECIMALES_COSTO, rounding=ROUND_HALF_UP)

    total = Decimal(stock_actual) * Decimal(costo_actual) + Decimal(cantidad_entrada) * costo_entrada
    return (total / Decimal(stock_actual + cantidad_entrada)).quantize(
        DECIMALES_COSTO,
        rounding=ROUND_HALF_UP,
    )


def asignar_reserva(necesidad: int, disponibles: list[tuple]) -> list[tuple]:
    """Asignación de reserva por depósito, respetando orden de preferencia."""
    if necesidad <= 0:
        raise ValueError('La cantidad a reservar debe ser mayor que cero.')

    total = sum(max(d, 0) for _, d in disponibles)
    if total < necesidad:
        raise ValueError(f'Stock insuficiente: se necesitan {necesidad} y hay {total} disponibles.')

    for clave, disponible in disponibles:
        if disponible >= necesidad:
            return [(clave, necesidad)]

    asignado = []
    restante = necesidad
    for clave, disponible in disponibles:
        if disponible <= 0:
            continue
        tomar = min(disponible, restante)
        asignado.append((clave, tomar))
        restante -= tomar
        if restante == 0:
            break

    return asignado


def unidades_a_reponer(stock_minimo: int, disponible: int) -> int:
    """Devuelve cuántas unidades faltan para llegar al mínimo."""
    return max(stock_minimo - disponible, 0)
