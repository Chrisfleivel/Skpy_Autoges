from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Sum

from inventario.calculos import DECIMALES_COSTO, asignar_reserva, costo_promedio_ponderado, unidades_a_reponer
from inventario.models import Deposito, MovimientoStock, ReservaStock, Repuesto, StockRepuesto

Tipo = MovimientoStock.Tipo


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


def _fila_stock(repuesto, deposito):
    return Repuesto.objects.get_or_create(pk=repuesto.pk)[0]


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
    if hasattr(repuesto, 'stock_actual'):
        return int(repuesto.stock_actual)
    return _fisico_total(repuesto)


def disponible_total(repuesto):
    if hasattr(repuesto, 'stock_disponible'):
        return int(repuesto.stock_disponible)
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
    if hasattr(repuesto, 'stock_actual') and not hasattr(repuesto, 'stocks'):
        cantidad = args[0] if args else kwargs.get('cantidad')
        motivo = kwargs.get('motivo', 'Entrada de stock')
        deposito = kwargs.get('deposito')
        referencia = kwargs.get('referencia', '')
        costo_unitario = kwargs.get('costo_unitario')
        cantidad = _cantidad_entera(cantidad)

        repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
        stock_anterior = int(repuesto.stock_actual)
        costo_base = repuesto.costo_unitario or repuesto.costo_compra or Decimal('0.00')

        if costo_unitario is not None:
            costo = Decimal(str(costo_unitario))
            if costo < 0:
                raise ValidationError('El costo unitario no puede ser negativo.')
            repuesto.costo_unitario = costo_promedio_ponderado(stock_anterior, costo_base if costo_base else None, cantidad, costo)
            repuesto.costo_compra = repuesto.costo_unitario

        repuesto.stock_actual += cantidad
        repuesto.save(update_fields=['stock_actual', 'costo_unitario', 'costo_compra', 'fecha_ultima_entrada'])
        return MovimientoStock.objects.create(
            repuesto=repuesto,
            tipo='ENTRADA',
            cantidad=cantidad,
            motivo=motivo or 'Entrada de stock',
            deposito_destino=deposito,
            referencia=referencia,
        )

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
    fisico_antes = stock_total(repuesto)
    nuevo_promedio = costo_promedio_ponderado(fisico_antes, repuesto.costo_promedio, cantidad, costo)

    stock = StockRepuesto.objects.get_or_create(repuesto=repuesto, deposito=deposito)[0]
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
    Repuesto.objects.filter(pk=repuesto.pk).update(costo_promedio=nuevo_promedio)
    return movimiento


@transaction.atomic
def ajustar_stock(repuesto, *args, **kwargs):
    if hasattr(repuesto, 'stock_actual') and not hasattr(repuesto, 'stocks'):
        cantidad_real = args[0] if args else kwargs.get('cantidad_real')
        motivo = kwargs.get('motivo')
        deposito = kwargs.get('deposito')
        referencia = kwargs.get('referencia', '')
        if not motivo or not str(motivo).strip():
            raise ValidationError('Debe indicar un motivo para el ajuste.')
        cantidad_real = int(cantidad_real)
        if cantidad_real < 0:
            raise ValidationError('La cantidad real no puede ser negativa.')

        repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
        if cantidad_real < repuesto.stock_reservado:
            raise ValidationError(f'La cantidad real no puede ser menor que el stock reservado. Esperado mínimo: {repuesto.stock_reservado}.')

        diferencia = cantidad_real - repuesto.stock_actual
        if diferencia == 0:
            return None

        repuesto.stock_actual = cantidad_real
        repuesto.save(update_fields=['stock_actual'])
        return MovimientoStock.objects.create(
            repuesto=repuesto,
            tipo='AJUSTE',
            cantidad=abs(diferencia),
            motivo=str(motivo).strip(),
            deposito_origen=deposito if diferencia < 0 else None,
            deposito_destino=deposito if diferencia > 0 else None,
            referencia=referencia,
        )

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
    stock = StockRepuesto.objects.select_for_update().get(repuesto=repuesto, deposito=deposito)
    diferencia = cantidad_real - stock.cantidad
    if diferencia == 0:
        return None
    if cantidad_real < stock.reservado:
        raise ValidationError(f'La cantidad real no puede ser menor que lo reservado ({stock.reservado}).')
    stock.cantidad = cantidad_real
    stock.save(update_fields=['cantidad', 'actualizado'])
    return MovimientoStock.objects.create(
        repuesto=repuesto,
        deposito=deposito,
        tipo=Tipo.AJUSTE_NEGATIVO if diferencia < 0 else Tipo.AJUSTE_POSITIVO,
        cantidad=diferencia,
        costo_unitario=repuesto.costo_promedio,
        saldo_posterior=stock.cantidad,
        motivo=str(motivo).strip(),
        usuario=kwargs.get('usuario'),
        referencia=kwargs.get('referencia', ''),
    )


@transaction.atomic
def confirmar_venta(repuesto, cantidad, *, motivo='Confirmación de venta', deposito=None, referencia=''):
    cantidad = _cantidad_entera(cantidad)
    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
    if cantidad > repuesto.stock_actual:
        raise ValidationError(f'Stock insuficiente para confirmar la venta. Actual: {repuesto.stock_actual}, solicitado: {cantidad}.')
    repuesto.stock_reservado = max(0, repuesto.stock_reservado - cantidad)
    repuesto.stock_actual = max(0, repuesto.stock_actual - cantidad)
    repuesto.save(update_fields=['stock_actual', 'stock_reservado'])
    return MovimientoStock.objects.create(
        repuesto=repuesto,
        tipo='SALIDA',
        cantidad=cantidad,
        motivo=motivo or 'Confirmación de venta',
        deposito_origen=deposito,
        referencia=referencia,
    )


@transaction.atomic
def transferir(repuesto, *args, **kwargs):
    if hasattr(repuesto, 'stock_actual') and not hasattr(repuesto, 'stocks'):
        cantidad = args[0] if args else kwargs.get('cantidad')
        deposito_origen = kwargs.get('deposito_origen')
        deposito_destino = kwargs.get('deposito_destino')
        motivo = kwargs.get('motivo', 'Transferencia de stock')
        referencia = kwargs.get('referencia', '')
        cantidad = _cantidad_entera(cantidad)
        if not deposito_origen and not deposito_destino:
            raise ValidationError('Debe indicar origen y/o destino para la transferencia.')
        if deposito_origen and deposito_destino and deposito_origen.pk == deposito_destino.pk:
            raise ValidationError('El origen y destino de la transferencia no pueden ser iguales.')
        repuesto = Repuesto.objects.select_for_update().get(pk=repuesto.pk)
        if repuesto.stock_disponible < cantidad:
            raise ValidationError(f'Stock insuficiente para transferir. Disponible: {repuesto.stock_disponible}, solicitado: {cantidad}.')
        return MovimientoStock.objects.create(
            repuesto=repuesto,
            tipo='TRANSFERENCIA',
            cantidad=cantidad,
            motivo=motivo or 'Transferencia de stock',
            deposito_origen=deposito_origen,
            deposito_destino=deposito_destino,
            referencia=referencia,
        )

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
    stock_origen = StockRepuesto.objects.select_for_update().get(repuesto=repuesto, deposito=origen)
    stock_destino = StockRepuesto.objects.select_for_update().get(repuesto=repuesto, deposito=destino)
    if stock_origen.disponible < cantidad:
        raise ValidationError(f'Stock insuficiente para transferir. Disponible: {stock_origen.disponible}, solicitado: {cantidad}.')

    stock_origen.cantidad -= cantidad
    stock_destino.cantidad += cantidad
    stock_origen.save(update_fields=['cantidad', 'actualizado'])
    stock_destino.save(update_fields=['cantidad', 'actualizado'])

    grupo = uuid.uuid4()
    comunes = dict(repuesto=repuesto, costo_unitario=repuesto.costo_promedio, grupo=grupo, usuario=usuario, motivo=motivo)
    salida = MovimientoStock.objects.create(
        deposito=origen,
        tipo=Tipo.TRANSFERENCIA_SALIDA,
        cantidad=-cantidad,
        saldo_posterior=stock_origen.cantidad,
        **comunes,
    )
    entrada = MovimientoStock.objects.create(
        deposito=destino,
        tipo=Tipo.TRANSFERENCIA_ENTRADA,
        cantidad=cantidad,
        saldo_posterior=stock_destino.cantidad,
        **comunes,
    )
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
    items = list(embarque.items.select_related('factura_item__repuesto').filter(factura_item__repuesto__isnull=False))
    if not items:
        return []
    if embarque.deposito_destino_id is None:
        raise ValidationError('El embarque debe tener un depósito destino para recibir repuestos.')

    movimientos = []
    for item in sorted(items, key=lambda i: i.factura_item.repuesto_id):
        repuesto = item.factura_item.repuesto
        if repuesto is None:
            continue
        cantidad = int(item.cantidad)
        if cantidad <= 0:
            continue
        costo = Decimal(str(item.costo_unitario or item.factura_item.precio_unitario or 0))
        movimientos.append(
            registrar_entrada(
                repuesto,
                embarque.deposito_destino,
                cantidad,
                costo,
                tipo=Tipo.ENTRADA_COMPRA,
                referencia=f'Embarque {embarque.pk}',
                motivo='Recepción de embarque',
                usuario=usuario,
            )
        )
    return movimientos


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
            deposito=reserva.deposito,
            tipo=Tipo.SALIDA_VENTA,
            cantidad=-tomar,
            costo_unitario=reserva.repuesto.costo_promedio,
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
    problemas = []
    stocks = StockRepuesto.objects.select_related('repuesto', 'deposito')
    if repuesto is not None:
        stocks = stocks.filter(repuesto=repuesto)

    for stock in stocks:
        total_movimientos = MovimientoStock.objects.filter(repuesto=stock.repuesto, deposito=stock.deposito).aggregate(t=Sum('cantidad'))['t'] or 0
        if total_movimientos != stock.cantidad:
            problemas.append(f'Físico inconsistente para {stock.repuesto.codigo_repuesto} @ {stock.deposito.codigo}: esperado {total_movimientos} y hay {stock.cantidad}.')
        reservado_esperado = sum(r.pendiente for r in ReservaStock.objects.filter(repuesto=stock.repuesto, deposito=stock.deposito))
        if reservado_esperado != stock.reservado:
            problemas.append(f'Reservado inconsistente para {stock.repuesto.codigo_repuesto} @ {stock.deposito.codigo}: esperado {reservado_esperado} y hay {stock.reservado}.')
        ultimo = MovimientoStock.objects.filter(repuesto=stock.repuesto, deposito=stock.deposito).order_by('-id').first()
        if ultimo and ultimo.saldo_posterior is not None and ultimo.saldo_posterior != stock.cantidad:
            problemas.append(f'Último saldo posterior inconsistente para {stock.repuesto.codigo_repuesto} @ {stock.deposito.codigo}: {ultimo.saldo_posterior} vs {stock.cantidad}.')
    return problemas
