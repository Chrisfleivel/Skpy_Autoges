from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cobranzas.models import Caja, CierreCaja, Pago
from configuraciones_maestras.models import Sucursal


@transaction.atomic
def abrir_caja(caja: Caja, *, empleado, monto_inicial=Decimal('0.00'), observaciones='') -> Caja:
    if caja.estado == 'abierta':
        raise ValidationError('La caja ya está abierta.')

    caja.estado = 'abierta'
    caja.empleado_actual = empleado
    caja.saldo_inicial = Decimal(str(monto_inicial))
    caja.saldo_actual = Decimal(str(monto_inicial))
    caja.fecha_apertura = timezone.now()
    caja.fecha_cierre = None
    caja.observaciones = observaciones
    caja.save(update_fields=[
        'estado',
        'empleado_actual',
        'saldo_inicial',
        'saldo_actual',
        'fecha_apertura',
        'fecha_cierre',
        'observaciones',
        'updated_at',
    ])
    return caja


@transaction.atomic
def registrar_pago_en_caja(*, caja: Caja, empleado, sucursal: Sucursal, monto, metodo_pago='Efectivo', observaciones='') -> Pago:
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValidationError('El monto del pago debe ser mayor que cero.')
    if caja.estado != 'abierta':
        raise ValidationError('La caja debe estar abierta para registrar el cobro.')
    if sucursal_id := getattr(sucursal, 'id', None):
        if caja.sucursal_id != sucursal_id:
            raise ValidationError('La caja no pertenece a la sucursal indicada.')

    pago = Pago.objects.create(
        tipo_pago='pedido',
        pedido=None,
        cotizacion=None,
        sucursal=sucursal,
        caja=caja,
        empleado=empleado,
        monto=monto,
        monto_recibido=monto,
        vuelto=Decimal('0.00'),
        fecha_pago=timezone.now(),
        metodo_pago=str(metodo_pago),
        estado='confirmado',
        observaciones=observaciones,
    )

    caja.saldo_actual = Decimal(str(caja.saldo_actual)) + monto
    caja.save(update_fields=['saldo_actual'])
    return pago


@transaction.atomic
def cerrar_caja(*, caja: Caja, empleado, monto_real, observaciones='') -> CierreCaja:
    if caja.estado != 'abierta':
        raise ValidationError('La caja ya está cerrada.')

    monto_esperado = Decimal(str(caja.saldo_actual))
    monto_real = Decimal(str(monto_real))
    diferencia = monto_real - monto_esperado

    caja.estado = 'cerrada'
    caja.empleado_actual = empleado
    caja.fecha_cierre = timezone.now()
    caja.saldo_actual = monto_real
    caja.observaciones = observaciones
    caja.save(update_fields=['estado', 'empleado_actual', 'fecha_cierre', 'saldo_actual', 'observaciones', 'updated_at'])

    cierre = CierreCaja.objects.create(
        caja=caja,
        empleado=empleado,
        monto_esperado=monto_esperado,
        monto_real=monto_real,
        diferencia=diferencia,
        observaciones=observaciones,
    )
    return cierre
