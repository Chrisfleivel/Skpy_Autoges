from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from inventario.calculos import DECIMALES_COSTO, asignar_reserva, costo_promedio_ponderado, unidades_a_reponer
from inventario.models import Deposito, MovimientoStock, ReservaStock, Repuesto, StockRepuesto

Tipo = MovimientoStock.Tipo

# `Repuesto.costo_unitario` y `Repuesto.costo_compra` guardan 2 decimales,
# mientras que el movimiento de stock guarda 4.
DECIMALES_REPUESTO = Decimal('0.01')


def _cantidad_entera(valor, nombre='La cantidad'):
    try:
        cantidad = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f'{nombre} debe ser un número entero.')
    if cantidad <= 0:
        raise ValidationError(f'{nombre} debe ser mayor que cero.')
    return cantidad


def _bloquear(repuesto):
    return Repuesto.objects.select_for_update().get(pk=repuesto.pk)


def deposito_principal():
    """
    Devuelve el depósito principal del sistema, creándolo si hace falta.

    Es el depósito por defecto de los flujos que no manejan multi-depósito
    (pedidos de venta de repuestos, consumos de taller, etc.).
    """
    deposito = Deposito.objects.filter(es_principal=True).first()
    if deposito is not None:
        return deposito

    codigo = 'PRINCIPAL'
    intento = 1
    while Deposito.objects.filter(codigo=codigo).exists():
        intento += 1
        codigo = f'PRINCIPAL{intento}'

    return Deposito.objects.create(
        codigo=codigo,
        nombre='Depósito Principal',
        ubicacion='Asunción',
        es_principal=True,
        activo=True,
    )


def fila_stock(repuesto, deposito):
    """
    Fila de stock del repuesto en el depósito (se crea si no existe).

    La primera vez que se toca un repuesto que solo vive en el inventario
    heredado (`Repuesto.stock_actual`), ese stock se adopta como físico del
    depósito: a partir de ahí manda `StockRepuesto`.
    """
    fila = StockRepuesto.objects.filter(repuesto=repuesto, deposito=deposito).first()
    if fila is not None:
        return fila

    if not StockRepuesto.objects.filter(repuesto=repuesto).exists():
        cantidad = int(repuesto.stock_actual or 0)
        reservado = min(int(repuesto.stock_reservado or 0), cantidad)
        return StockRepuesto.objects.create(
            repuesto=repuesto,
            deposito=deposito,
            cantidad=cantidad,
            reservado=reservado,
        )

    return StockRepuesto.objects.create(repuesto=repuesto, deposito=deposito, cantidad=0)


def sincronizar_espejo(repuesto):
    """
    Refleja el stock multi-depósito en los campos heredados del repuesto.

    `Repuesto.stock_actual` y `Repuesto.stock_reservado` siguen siendo leídos
    por `clientes_pedidos` y por los reportes, así que se mantienen como
    espejo de `StockRepuesto` (siempre dentro de la misma transacción).
    """
    stocks = StockRepuesto.objects.filter(repuesto=repuesto)
    total = sum(stock.cantidad for stock in stocks)
    reservado = sum(stock.reservado for stock in stocks)
    Repuesto.objects.filter(pk=repuesto.pk).update(
        stock_actual=total,
        stock_reservado=reservado,
    )
    repuesto.stock_actual = total
    repuesto.stock_reservado = reservado
    return repuesto


def _entero_positivo(valor, nombre='La cantidad'):
    try:
        n = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f'{nombre} debe ser un número entero.')
    if n != valor or n <= 0:
        raise ValidationError(f'{nombre} debe ser un entero mayor que cero.')
    return n


def _fisico_total(repuesto):
    return StockRepuesto.objects.filter(repuesto=repuesto).aggregate(t=Sum('cantidad'))['t'] or 0


def stock_total(repuesto):
    """Físico total del repuesto, sumando todos sus depósitos."""
    return int(_fisico_total(repuesto))


def disponible_total(repuesto):
    """Disponible total: físico menos lo reservado, en depósitos activos."""
    stocks = StockRepuesto.objects.filter(repuesto=repuesto, deposito__activo=True)
    return sum(s.disponible for s in stocks)


def disponibilidad_para_linea(venta_item):
    if hasattr(venta_item, 'reservas_stock'):
        propio = sum(r.pendiente for r in venta_item.reservas_stock.all())
        return disponible_total(venta_item.repuesto) + propio
    return 0


def repuestos_bajo_minimo():
    faltantes = []
    for repuesto in Repuesto.objects.filter(activo=True, stock_minimo__gt=0).order_by('sku'):
        disponible = disponible_total(repuesto)
        a_reponer = unidades_a_reponer(repuesto.stock_minimo, disponible)
        if a_reponer > 0:
            faltantes.append({'repuesto': repuesto, 'disponible': disponible, 'a_reponer': a_reponer})
    return faltantes


@transaction.atomic
def registrar_entrada(repuesto, *args, **kwargs):
    """
    Registra una entrada de stock en un depósito.

    La cantidad siempre es positiva (lo exige el constraint del modelo) y la
    dirección se marca con `deposito_destino`.
    """
    if args and isinstance(args[0], Deposito):
        deposito, cantidad, costo_unitario = args[0], args[1], args[2] if len(args) > 2 else kwargs.get('costo_unitario')
    else:
        deposito = kwargs.get('deposito')
        cantidad = args[0] if args else kwargs.get('cantidad')
        costo_unitario = kwargs.get('costo_unitario')

    tipo = kwargs.get('tipo', Tipo.ENTRADA_COMPRA)
    embarque_item = kwargs.get('embarque_item')
    usuario = kwargs.get('usuario')
    referencia = kwargs.get('referencia', '')
    motivo = kwargs.get('motivo', '')
    cantidad = _entero_positivo(cantidad)

    if costo_unitario is None:
        raise ValidationError('Debe indicar el costo unitario de la entrada.')
    costo = Decimal(str(costo_unitario))
    if costo < 0:
        raise ValidationError('El costo de entrada no puede ser negativo.')
    if deposito is None or not deposito.activo:
        raise ValidationError('Debe indicar un depósito activo para la entrada.')

    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    stock = fila_stock(repuesto, deposito)
    fisico_antes = stock_total(repuesto)
    costo_base = repuesto.costo_unitario or repuesto.costo_compra or Decimal('0.00')
    nuevo_costo = costo_promedio_ponderado(
        fisico_antes, costo_base if costo_base else None, cantidad, costo
    )

    stock.cantidad += cantidad
    stock.save(update_fields=['cantidad', 'actualizado'])

    movimiento = MovimientoStock.objects.create(
        repuesto=repuesto,
        deposito_destino=deposito,
        tipo=tipo,
        cantidad=cantidad,
        costo_unitario=costo.quantize(DECIMALES_COSTO, rounding=ROUND_HALF_UP),
        saldo_posterior=stock.cantidad,
        embarque_item=embarque_item,
        usuario=usuario,
        referencia=referencia,
        motivo=motivo.strip() if motivo else '',
    )
    Repuesto.objects.filter(pk=repuesto.pk).update(
        costo_unitario=nuevo_costo.quantize(DECIMALES_REPUESTO, rounding=ROUND_HALF_UP),
        costo_compra=nuevo_costo.quantize(DECIMALES_REPUESTO, rounding=ROUND_HALF_UP),
    )
    repuesto.costo_unitario = nuevo_costo.quantize(DECIMALES_REPUESTO, rounding=ROUND_HALF_UP)
    repuesto.costo_compra = repuesto.costo_unitario
    sincronizar_espejo(repuesto)
    return movimiento


@transaction.atomic
def ajustar_stock(repuesto, *args, **kwargs):
    """
    Ajusta el físico de un depósito al conteo real.

    La diferencia se registra como movimiento `AJUSTE` con cantidad positiva:
    la dirección la indican `deposito_destino` (sube) o `deposito_origen` (baja).
    """
    if args and isinstance(args[0], Deposito):
        deposito = args[0]
        cantidad_real = kwargs.get('cantidad_real')
        motivo = kwargs.get('motivo')
    else:
        deposito = kwargs.get('deposito')
        cantidad_real = args[0] if args else kwargs.get('cantidad_real')
        motivo = kwargs.get('motivo')

    if not motivo or not str(motivo).strip():
        raise ValidationError('Debe indicar un motivo para el ajuste.')
    cantidad_real = int(cantidad_real)
    if cantidad_real < 0:
        raise ValidationError('La cantidad real no puede ser negativa.')

    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    stock = fila_stock(repuesto, deposito)
    diferencia = cantidad_real - stock.cantidad
    if diferencia == 0:
        return None
    if cantidad_real < stock.reservado:
        raise ValidationError(f'La cantidad real no puede ser menor que lo reservado ({stock.reservado}).')
    stock.cantidad = cantidad_real
    stock.save(update_fields=['cantidad', 'actualizado'])
    movimiento = MovimientoStock.objects.create(
        repuesto=repuesto,
        deposito_origen=deposito if diferencia < 0 else None,
        deposito_destino=deposito if diferencia > 0 else None,
        tipo=Tipo.AJUSTE,
        cantidad=abs(diferencia),
        costo_unitario=repuesto.costo_unitario,
        saldo_posterior=stock.cantidad,
        motivo=str(motivo).strip(),
        usuario=kwargs.get('usuario'),
        referencia=kwargs.get('referencia', ''),
    )
    sincronizar_espejo(repuesto)
    return movimiento


@transaction.atomic
def confirmar_venta(repuesto, cantidad, *, motivo='Confirmación de venta', deposito=None, referencia='', usuario=None):
    """
    Confirma una salida de stock por venta en un depósito.

    Descuenta el físico y la reserva del depósito, y deja el movimiento
    `SALIDA` con cantidad positiva y `deposito_origen` apuntando al depósito.
    """
    cantidad = _cantidad_entera(cantidad)
    if deposito is None:
        raise ValidationError('Debe indicar el depósito de salida.')

    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    stock = fila_stock(repuesto, deposito)
    if cantidad > stock.cantidad:
        raise ValidationError(
            f'Stock insuficiente para confirmar la venta. '
            f'Actual: {stock.cantidad}, solicitado: {cantidad}.'
        )
    stock.cantidad -= cantidad
    stock.reservado = max(0, stock.reservado - cantidad)
    stock.save(update_fields=['cantidad', 'reservado', 'actualizado'])
    movimiento = MovimientoStock.objects.create(
        repuesto=repuesto,
        deposito_origen=deposito,
        tipo=Tipo.SALIDA,
        cantidad=cantidad,
        costo_unitario=repuesto.costo_unitario,
        saldo_posterior=stock.cantidad,
        motivo=motivo or 'Confirmación de venta',
        usuario=usuario,
        referencia=referencia,
    )
    sincronizar_espejo(repuesto)
    return movimiento


@transaction.atomic
def registrar_salida(repuesto, cantidad, *, deposito=None, motivo='Salida de stock', referencia='', usuario=None, tipo=Tipo.SALIDA, costo_unitario=None):
    """
    Registra una salida de stock de un depósito.

    Es la salida genérica (taller, consumo interno, merma): a diferencia de
    `confirmar_venta`, no toca las reservas, porque no viene de una venta.

    La cantidad siempre es positiva (lo exige el constraint del modelo) y la
    dirección se marca con `deposito_origen`.
    """
    cantidad = _entero_positivo(cantidad)
    if deposito is None:
        raise ValidationError('Debe indicar el depósito de salida.')
    if not deposito.activo:
        raise ValidationError('El depósito de salida debe estar activo.')

    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    stock = fila_stock(repuesto, deposito)
    if stock.disponible < cantidad:
        raise ValidationError(
            f'Stock insuficiente para la salida. '
            f'Disponible: {stock.disponible}, solicitado: {cantidad}.'
        )

    stock.cantidad -= cantidad
    stock.save(update_fields=['cantidad', 'actualizado'])
    movimiento = MovimientoStock.objects.create(
        repuesto=repuesto,
        deposito_origen=deposito,
        tipo=tipo,
        cantidad=cantidad,
        costo_unitario=(
            repuesto.costo_unitario if costo_unitario is None
            else Decimal(str(costo_unitario)).quantize(DECIMALES_COSTO, rounding=ROUND_HALF_UP)
        ),
        saldo_posterior=stock.cantidad,
        motivo=motivo or 'Salida de stock',
        usuario=usuario,
        referencia=referencia,
    )
    sincronizar_espejo(repuesto)
    return movimiento


@transaction.atomic
def reservar_unidades(repuesto, cantidad, *, deposito=None, usuario=None, motivo='Reserva de stock por operación comercial'):
    """
    Reserva unidades de un repuesto sin mover el físico.

    Es la reserva del flujo de pedidos (`clientes_pedidos`): no va por
    `ReservaStock` (ese modelo pertenece al flujo de `ventas`), sino por el
    contador `reservado` de la fila de stock del depósito.

    El movimiento `RESERVA` **no lleva depósito**: una reserva no mueve
    unidades, y anotarla en un depósito alteraría el cálculo del físico.
    """
    cantidad = _entero_positivo(cantidad)
    deposito = deposito or deposito_principal()

    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    stock = fila_stock(repuesto, deposito)
    if stock.disponible < cantidad:
        raise ValidationError(
            f'Stock insuficiente para reservar. '
            f'Disponible: {stock.disponible}, solicitado: {cantidad}.'
        )

    stock.reservado += cantidad
    stock.save(update_fields=['reservado', 'actualizado'])
    movimiento = MovimientoStock.objects.create(
        repuesto=repuesto,
        tipo=Tipo.RESERVA,
        cantidad=cantidad,
        motivo=motivo,
        usuario=usuario,
    )
    sincronizar_espejo(repuesto)
    return movimiento


@transaction.atomic
def liberar_unidades(repuesto, cantidad, *, deposito=None, usuario=None, motivo='Liberación de reserva'):
    """Libera unidades reservadas (por cancelación de un pedido)."""
    cantidad = _entero_positivo(cantidad)
    deposito = deposito or deposito_principal()

    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    stock = fila_stock(repuesto, deposito)
    cantidad = min(cantidad, stock.reservado)
    if cantidad <= 0:
        return None

    stock.reservado -= cantidad
    stock.save(update_fields=['reservado', 'actualizado'])
    movimiento = MovimientoStock.objects.create(
        repuesto=repuesto,
        tipo=Tipo.LIBERA,
        cantidad=cantidad,
        motivo=motivo,
        usuario=usuario,
    )
    sincronizar_espejo(repuesto)
    return movimiento


@transaction.atomic
def transferir(repuesto, *args, **kwargs):
    """
    Transfiere stock entre dos depósitos.

    Genera los dos movimientos de la transferencia (salida y entrada) unitedos
    por `grupo`, con cantidades positivas y la dirección marcada por
    `deposito_origen` / `deposito_destino`.
    """
    if args and isinstance(args[0], Deposito):
        origen, destino, cantidad = args[0], args[1], args[2]
        usuario = kwargs.get('usuario')
        motivo = kwargs.get('motivo', '')
    else:
        origen = kwargs.get('deposito_origen')
        destino = kwargs.get('deposito_destino')
        cantidad = args[0] if args else kwargs.get('cantidad')
        usuario = kwargs.get('usuario')
        motivo = kwargs.get('motivo', '')

    cantidad = _entero_positivo(cantidad)
    if origen is None or destino is None:
        raise ValidationError('Debe indicar origen y destino para la transferencia.')
    if origen.pk == destino.pk:
        raise ValidationError('El origen y destino de la transferencia no pueden ser iguales.')
    if not destino.activo:
        raise ValidationError('El depósito destino debe estar activo.')

    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    stock_origen = fila_stock(repuesto, origen)
    stock_destino = fila_stock(repuesto, destino)
    if stock_origen.disponible < cantidad:
        raise ValidationError(f'Stock insuficiente para transferir. Disponible: {stock_origen.disponible}, solicitado: {cantidad}.')

    stock_origen.cantidad -= cantidad
    stock_destino.cantidad += cantidad
    stock_origen.save(update_fields=['cantidad', 'actualizado'])
    stock_destino.save(update_fields=['cantidad', 'actualizado'])

    grupo = uuid.uuid4()
    comunes = dict(repuesto=repuesto, costo_unitario=repuesto.costo_unitario, grupo=grupo, usuario=usuario, motivo=motivo)
    salida = MovimientoStock.objects.create(
        deposito_origen=origen,
        tipo=Tipo.TRANSFERENCIA_SALIDA,
        cantidad=cantidad,
        saldo_posterior=stock_origen.cantidad,
        **comunes,
    )
    entrada = MovimientoStock.objects.create(
        deposito_destino=destino,
        tipo=Tipo.TRANSFERENCIA_ENTRADA,
        cantidad=cantidad,
        saldo_posterior=stock_destino.cantidad,
        **comunes,
    )
    sincronizar_espejo(repuesto)
    return salida, entrada


@transaction.atomic
def reservar_stock(venta_item, *, usuario=None):
    if not getattr(venta_item, 'repuesto_id', None):
        raise ValidationError('La línea de venta debe tener un repuesto asociado.')

    repuesto = _bloquear(venta_item.repuesto)
    ya_reservado = sum(r.cantidad - r.liberada for r in venta_item.reservas_stock.select_for_update())
    necesidad = venta_item.cantidad - ya_reservado
    if necesidad <= 0:
        return []

    principales = set(Deposito.objects.filter(es_principal=True).values_list('pk', flat=True))
    stocks = list(StockRepuesto.objects.select_for_update().filter(repuesto=repuesto, deposito__activo=True))
    stocks.sort(key=lambda s: (s.deposito_id not in principales, -s.disponible, s.deposito_id))
    try:
        asignacion = asignar_reserva(necesidad, [(s.deposito_id, s.disponible) for s in stocks])
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

    reservas = []
    for deposito_id, cantidad in asignacion:
        stock = StockRepuesto.objects.select_for_update().get(repuesto=repuesto, deposito_id=deposito_id)
        stock.reservado += cantidad
        stock.save(update_fields=['reservado', 'actualizado'])
        reserva = ReservaStock.objects.create(
            venta_item=venta_item,
            repuesto=repuesto,
            deposito_id=deposito_id,
            cantidad=cantidad,
        )
        reservas.append(reserva)
    return reservas


@transaction.atomic
def recibir_embarque(embarque, *, usuario=None):
    """
    Ingresa los repuestos de un embarque al depósito destino.

    Atajo sobre el servicio de cierre (`importaciones.cierre.ejecutar_cierre`),
    que además carga los costos de los vehículos y cierra el embarque. Se
    mantiene solo como punto de entrada cómodo; el cálculo del costo landed
    y de la tasa de cambio vive en `importaciones.cierre`.
    """
    from importaciones.cierre import ejecutar_cierre

    resultado = ejecutar_cierre(embarque, usuario=usuario)
    return resultado


@transaction.atomic
def reservar_lineas(venta, *, usuario=None):
    reservas = []
    for item in venta.items.filter(repuesto__isnull=False).order_by('id'):
        reservas.extend(reservar_stock(item, usuario=usuario))
    return reservas


@transaction.atomic
def liberar_reservas(venta):
    total = 0
    for reserva in ReservaStock.objects.filter(venta_item__venta=venta):
        pendiente = reserva.pendiente
        if pendiente <= 0:
            continue
        stock = StockRepuesto.objects.select_for_update().get(repuesto=reserva.repuesto, deposito=reserva.deposito)
        stock.reservado -= min(pendiente, stock.reservado)
        stock.save(update_fields=['reservado', 'actualizado'])
        reserva.liberada += pendiente
        reserva.save(update_fields=['liberada'])
        total += pendiente
    return total


@transaction.atomic
def consumir_reserva(venta_item, cantidad, *, referencia='', usuario=None):
    cantidad = int(cantidad)
    if cantidad <= 0:
        raise ValidationError('La cantidad a consumir debe ser mayor que cero.')

    reservas = list(ReservaStock.objects.select_for_update().filter(venta_item=venta_item).order_by('id'))
    movimientos = []
    restante = cantidad
    for reserva in reservas:
        if restante <= 0:
            break
        tomar = min(reserva.pendiente, restante)
        stock = StockRepuesto.objects.select_for_update().get(repuesto=reserva.repuesto, deposito=reserva.deposito)
        stock.cantidad -= tomar
        stock.reservado -= tomar
        stock.save(update_fields=['cantidad', 'reservado', 'actualizado'])
        reserva.consumida += tomar
        reserva.save(update_fields=['consumida'])
        movimiento = MovimientoStock.objects.create(
            repuesto=reserva.repuesto,
            deposito_origen=reserva.deposito,
            tipo=Tipo.SALIDA_VENTA,
            cantidad=tomar,
            costo_unitario=reserva.repuesto.costo_unitario,
            saldo_posterior=stock.cantidad,
            usuario=usuario,
            referencia=referencia,
        )
        movimientos.append(movimiento)
        restante -= tomar
    if restante > 0:
        raise ValidationError(f'No alcanzó a consumir la reserva pedida: faltan {restante}.')
    return movimientos


def verificar_consistencia(repuesto=None):
    """
    Verifica que el físico de cada depósito cuadre con sus movimientos.

    Las cantidades de los movimientos son siempre positivas; la dirección la
    indican `deposito_destino` (entrada) y `deposito_origen` (salida).
    """
    problemas = []
    stocks = StockRepuesto.objects.select_related('repuesto', 'deposito')
    if repuesto is not None:
        stocks = stocks.filter(repuesto=repuesto)

    for stock in stocks:
        movimientos = MovimientoStock.objects.filter(repuesto=stock.repuesto)
        entradas = movimientos.filter(deposito_destino=stock.deposito).aggregate(t=Sum('cantidad'))['t'] or 0
        salidas = movimientos.filter(deposito_origen=stock.deposito).aggregate(t=Sum('cantidad'))['t'] or 0
        total_movimientos = entradas - salidas
        if total_movimientos != stock.cantidad:
            problemas.append(f'Físico inconsistente para {stock.repuesto.codigo_repuesto} @ {stock.deposito.codigo}: esperado {total_movimientos} y hay {stock.cantidad}.')
        reservas = ReservaStock.objects.filter(repuesto=stock.repuesto, deposito=stock.deposito)
        if reservas.exists():
            # Solo el flujo de `ventas` usa `ReservaStock`. Las reservas del
            # flujo de pedidos (`clientes_pedidos`) viven solo en el contador
            # `reservado` de la fila de stock.
            reservado_esperado = sum(r.pendiente for r in reservas)
            if reservado_esperado != stock.reservado:
                problemas.append(f'Reservado inconsistente para {stock.repuesto.codigo_repuesto} @ {stock.deposito.codigo}: esperado {reservado_esperado} y hay {stock.reservado}.')
        ultimo = movimientos.filter(deposito_origen=stock.deposito).order_by('-id').first() or movimientos.filter(deposito_destino=stock.deposito).order_by('-id').first()
        if ultimo and ultimo.saldo_posterior is not None and ultimo.saldo_posterior != stock.cantidad:
            problemas.append(f'Último saldo posterior inconsistente para {stock.repuesto.codigo_repuesto} @ {stock.deposito.codigo}: {ultimo.saldo_posterior} vs {stock.cantidad}.')
    return problemas
