"""
Auditoría del ledger de stock (`MovimientoStock`).

El objetivo es detectar las incoherencias que hoy nadie mira, porque el
modelo multi-depósito (`StockRepuesto`) todavía no es la fuente de verdad de
producción:

1. Movimientos cuya cantidad o dirección no siguen la convención de la casa
   (cantidad positiva, dirección marcada por los depósitos).
2. Transferencias a medio hacer (una pata sin la otra).
3. Saldos posteriores que no cuadran con el físico real del depósito.
4. Repuestos que viven solo en el campo legacy `stock_actual`.

Los **errores** son incoherencias reales del ledger. Los **avisos** son
situaciones esperables mientras conviven los dos inventarios, pero que hay
que tener en cuenta.

Convención recordada: la cantidad de un movimiento es siempre positiva; la
dirección la indican `deposito_destino` (entrada) y `deposito_origen` (salida).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from django.db.models import Sum

from inventario.models import MovimientoStock, Repuesto, StockRepuesto
from inventario.services import verificar_consistencia

# Tipos de movimiento según la dirección que implican.
TIPOS_ENTRADA = ('ENTRADA', 'ENTRADA_COMPRA', 'TRANSFERENCIA_ENTRADA')
TIPOS_SALIDA = ('SALIDA', 'SALIDA_VENTA', 'TRANSFERENCIA_SALIDA')
# Tipos heredados que no llevan dirección (reservas sobre `stock_actual`).
TIPOS_SIN_DIRECCION = ('RESERVA', 'LIBERA')


@dataclass
class ResultadoAuditoria:
    """Resultado de una auditoría de stock."""

    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    movimientos_revisados: int = 0
    depositos_revisados: int = 0
    repuestos_revisados: int = 0

    @property
    def ok(self) -> bool:
        """True si no hay errores (los avisos no invalidate la auditoría)."""
        return not self.errores

    def resumen(self) -> str:
        partes = [f'{len(self.errores)} error(es)', f'{len(self.avisos)} aviso(s)']
        return ', '.join(partes)


def _descripcion(movimiento) -> str:
    deposito = movimiento.deposito_destino_id or movimiento.deposito_origen_id
    return (
        f'movimiento #{movimiento.pk} '
        f'({movimiento.repuesto.codigo_repuesto}, {movimiento.tipo}, '
        f'cantidad {movimiento.cantidad}, depósito {deposito})'
    )


def _auditar_direccion(movimientos, resultado: ResultadoAuditoria) -> None:
    """Cada movimiento debe tener una dirección coherente con su tipo."""
    for movimiento in movimientos:
        tiene_origen = movimiento.deposito_origen_id is not None
        tiene_destino = movimiento.deposito_destino_id is not None
        tipo = movimiento.tipo

        if movimiento.cantidad <= 0:
            resultado.errores.append(
                f'{_descripcion(movimiento)}: la cantidad debe ser positiva.'
            )
            continue

        if tipo in TIPOS_ENTRADA:
            if not tiene_destino:
                resultado.errores.append(
                    f'{_descripcion(movimiento)}: un movimiento de entrada debe '
                    f'informar `deposito_destino`.'
                )
            if tiene_origen:
                resultado.errores.append(
                    f'{_descripcion(movimiento)}: un movimiento de entrada no debe '
                    f'informar `deposito_origen`.'
                )
        elif tipo in TIPOS_SALIDA:
            if not tiene_origen:
                resultado.errores.append(
                    f'{_descripcion(movimiento)}: un movimiento de salida debe '
                    f'informar `deposito_origen`.'
                )
            if tiene_destino:
                resultado.errores.append(
                    f'{_descripcion(movimiento)}: un movimiento de salida no debe '
                    f'informar `deposito_destino`.'
                )
        elif tipo == 'AJUSTE':
            if tiene_origen == tiene_destino:
                resultado.errores.append(
                    f'{_descripcion(movimiento)}: un ajuste debe informar '
                    f'exactamente un depósito (el de origen o el de destino).'
                )
        elif tipo == 'TRANSFERENCIA':
            if not tiene_origen and not tiene_destino:
                resultado.errores.append(
                    f'{_descripcion(movimiento)}: una transferencia debe informar '
                    f'al menos un depósito.'
                )
        elif tipo in TIPOS_SIN_DIRECCION:
            if tiene_origen or tiene_destino:
                resultado.errores.append(
                    f'{_descripcion(movimiento)}: el tipo {tipo} no mueve físico, '
                    f'pero informa un depósito (alteraría el cálculo del stock).'
                )
        else:
            resultado.errores.append(
                f'{_descripcion(movimiento)}: tipo de movimiento desconocido.'
            )


def _auditar_grupos_transferencia(movimientos, resultado: ResultadoAuditoria) -> None:
    """Cada transferencia debe tener su par completo y con la misma cantidad."""
    grupos = {}
    for movimiento in movimientos:
        if movimiento.grupo is None:
            continue
        grupos.setdefault(movimiento.grupo, []).append(movimiento)

    for grupo, movimientos_grupo in grupos.items():
        salidas = [m for m in movimientos_grupo if m.tipo == 'TRANSFERENCIA_SALIDA']
        entradas = [m for m in movimientos_grupo if m.tipo == 'TRANSFERENCIA_ENTRADA']

        if len(salidas) != 1 or len(entradas) != 1:
            resultado.errores.append(
                f'Transferencia {grupo} incompleta: {len(salidas)} salida(s) y '
                f'{len(entradas)} entrada(s); se esperan una de cada.'
            )
            continue

        salida, entrada = salidas[0], entradas[0]
        if salida.cantidad != entrada.cantidad:
            resultado.errores.append(
                f'Transferencia {grupo} con cantidades distintas: sale '
                f'{salida.cantidad} y entra {entrada.cantidad}.'
            )
        if salida.deposito_origen_id == entrada.deposito_destino_id:
            resultado.errores.append(
                f'Transferencia {grupo} con el mismo depósito de origen y destino '
                f'({salida.deposito_origen_id}).'
            )


def _auditar_saldos(movimientos, resultado: ResultadoAuditoria) -> None:
    """
    El `saldo_posterior` del último movimiento de cada par (repuesto, depósito)
    debe coincidir con el físico actual de ese depósito.
    """
    fisicos = {
        (stock.repuesto_id, stock.deposito_id): stock.cantidad
        for stock in StockRepuesto.objects.all()
    }

    ultimo_por_deposito = {}
    for movimiento in movimientos:
        deposito_id = movimiento.deposito_origen_id or movimiento.deposito_destino_id
        if deposito_id is None or movimiento.saldo_posterior is None:
            continue
        clave = (movimiento.repuesto_id, deposito_id)
        actual = ultimo_por_deposito.get(clave)
        if actual is None or movimiento.pk > actual.pk:
            ultimo_por_deposito[clave] = movimiento

    for (repuesto_id, deposito_id), movimiento in ultimo_por_deposito.items():
        if (repuesto_id, deposito_id) not in fisicos:
            resultado.errores.append(
                f'{_descripcion(movimiento)}: el movimiento informa un saldo '
                f'posterior pero el depósito no tiene fila de stock.'
            )
            continue
        fisico = fisicos[(repuesto_id, deposito_id)]
        if movimiento.saldo_posterior != fisico:
            resultado.errores.append(
                f'{_descripcion(movimiento)}: el saldo posterior '
                f'({movimiento.saldo_posterior}) no coincide con el físico '
                f'del depósito ({fisico}).'
            )


def _auditar_stock_legacy(resultado: ResultadoAuditoria, repuesto=None) -> None:
    """
    Repuestos que solo existen en `Repuesto.stock_actual`.

    No es un error: es el inventario heredado, que convive con `StockRepuesto`
    hasta que se complete la migración. Pero conviene tenerlo a la vista.
    """
    legacy = Repuesto.objects.filter(stock_actual__gt=0)
    if repuesto:
        legacy = legacy.filter(codigo_repuesto=repuesto)
    for articulo in legacy.order_by('codigo_repuesto'):
        if not StockRepuesto.objects.filter(repuesto=articulo).exists():
            resultado.avisos.append(
                f'Repuesto {articulo.codigo_repuesto}: tiene stock_actual '
                f'{articulo.stock_actual} pero ninguna fila en `StockRepuesto` '
                f'(inventario legacy sin migrar).'
            )
            resultado.repuestos_revisados += 1
            continue

        fisico = StockRepuesto.objects.filter(repuesto=articulo).aggregate(t=Sum('cantidad'))['t'] or 0
        if int(fisico) != int(articulo.stock_actual):
            resultado.avisos.append(
                f'Repuesto {articulo.codigo_repuesto}: `stock_actual` '
                f'({articulo.stock_actual}) y el físico multi-depósito ({int(fisico)}) '
                f'no coinciden.'
            )
            resultado.repuestos_revisados += 1


def auditar_stock(repuesto=None) -> ResultadoAuditoria:
    """
    Audita el ledger de stock.

    `repuesto` puede ser un código de repuesto (`codigo_repuesto`) para
    limitar la auditoría a un solo artículo.
    """
    resultado = ResultadoAuditoria()

    repuesto_obj = None
    if repuesto:
        repuesto_obj = Repuesto.objects.filter(codigo_repuesto=repuesto).first()

    movimientos = MovimientoStock.objects.select_related('repuesto').order_by('pk')
    if repuesto_obj is not None:
        movimientos = movimientos.filter(repuesto=repuesto_obj)
    movimientos = list(movimientos)
    resultado.movimientos_revisados = len(movimientos)
    resultado.depositos_revisados = StockRepuesto.objects.values('deposito_id').distinct().count()

    # Chequeos propios de la auditoría.
    _auditar_direccion(movimientos, resultado)
    _auditar_grupos_transferencia(movimientos, resultado)
    _auditar_saldos(movimientos, resultado)

    # Chequeos de consistencia física (reutiliza el servicio ya probado).
    for problema in verificar_consistencia(repuesto_obj):
        resultado.errores.append(problema)

    # Chequeos del inventario legacy.
    _auditar_stock_legacy(resultado, repuesto)

    return resultado
