# cobranzas/models.py
from decimal import Decimal

from django.db import models
from django.utils import timezone

from configuraciones_maestras.models import Sucursal
from configuraciones_maestras.utils import obtener_tasa_para_fecha
from seguridad_usuarios.models import Empleado
from clientes_pedidos.models import Pedido, Cotizacion


class Caja(models.Model):
    """Caja operativa de la sucursal para cobros y arqueos."""
    ESTADO_CHOICES = (
        ('cerrada', 'Cerrada'),
        ('abierta', 'Abierta'),
    )

    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='cajas_operativas', verbose_name='Sucursal')
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Caja')
    TIPO_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('BANCO', 'Banco'),
        ('MIXTA', 'Mixta'),
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='EFECTIVO', verbose_name='Tipo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='cerrada', verbose_name='Estado')
    saldo_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Saldo Inicial')
    saldo_actual = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Saldo Actual')
    empleado_actual = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='cajas_asignadas', verbose_name='Empleado actual')
    fecha_apertura = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Apertura')
    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Cierre')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creada el')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizada el')

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'
        ordering = ['sucursal__nombre', 'nombre']
        constraints = [
            # El nombre de la caja es único dentro de cada sucursal
            models.UniqueConstraint(fields=['sucursal', 'nombre'], name='uniq_caja_sucursal_nombre'),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.sucursal}"

    def abrir(self, empleado, monto_inicial=0, observaciones=''):
        self.estado = 'abierta'
        self.empleado_actual = empleado
        self.saldo_inicial = Decimal(str(monto_inicial))
        self.saldo_actual = Decimal(str(monto_inicial))
        self.fecha_apertura = timezone.now()
        self.fecha_cierre = None
        self.observaciones = observaciones
        self.save(update_fields=['estado', 'empleado_actual', 'saldo_inicial', 'saldo_actual', 'fecha_apertura', 'fecha_cierre', 'observaciones', 'updated_at'])

    def cerrar(self, empleado, monto_real, observaciones=''):
        self.estado = 'cerrada'
        self.empleado_actual = empleado
        self.fecha_cierre = timezone.now()
        self.saldo_actual = Decimal(str(monto_real))
        self.observaciones = observaciones
        self.save(update_fields=['estado', 'empleado_actual', 'fecha_cierre', 'saldo_actual', 'observaciones', 'updated_at'])


class AperturaCaja(models.Model):
    """Registro del movimiento de apertura de caja."""
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='aperturas')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='aperturas_realizadas')
    monto_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    fecha_hora = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Apertura de Caja'
        verbose_name_plural = 'Aperturas de Caja'

    def __str__(self):
        return f"Apertura {self.caja} - {self.fecha_hora}"


class CierreCaja(models.Model):
    """Registro del arqueo y cierre de caja."""
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='cierres')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='cierres_realizados')
    monto_esperado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_real = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    diferencia = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    fecha_hora = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Cierre de Caja'
        verbose_name_plural = 'Cierres de Caja'

    def __str__(self):
        return f"Cierre {self.caja} - {self.fecha_hora}"


class Pago(models.Model):
    """
    Modelo que representa un pago recibido de un cliente en la caja de una sucursal.
    Diseñado para esta etapa del proyecto sin depender de contabilidad.
    """
    TIPO_PAGO = (
        ('pedido', 'Pago de Pedido'),
        ('cotizacion', 'Pago de Cotización'),
    )

    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('anulado', 'Anulado'),
    )

    tipo_pago = models.CharField(max_length=10, choices=TIPO_PAGO, verbose_name="Tipo de Pago")
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos',
        verbose_name="Pedido Relacionado"
    )
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos',
        verbose_name="Cotización Relacionada"
    )
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='pagos', null=True, blank=True, verbose_name='Sucursal')
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='pagos', null=True, blank=True, verbose_name='Caja')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='pagos_realizados', null=True, blank=True, verbose_name='Empleado')
    monto = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Monto del Pago")
    monto_recibido = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Monto Recibido")
    vuelto = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Vuelto")
    fecha_pago = models.DateTimeField(default=timezone.now, verbose_name="Fecha y Hora del Pago")
    metodo_pago = models.CharField(max_length=50, verbose_name="Método de Pago")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='confirmado', verbose_name='Estado')
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de {self.monto} - {self.get_tipo_pago_display()}"

    def confirmar(self):
        self.estado = 'confirmado'
        self.save(update_fields=['estado'])
        if self.pedido_id and hasattr(self.pedido, 'confirmar_pago'):
            self.pedido.confirmar_pago()

    def anular(self):
        self.estado = 'anulado'
        self.save(update_fields=['estado'])

    @property
    def es_efectivo(self):
        return str(self.metodo_pago).lower() in {'efectivo', 'cash'}

    def calcular_vuelto(self):
        if self.monto_recibido <= 0:
            return Decimal('0.00')
        return max(Decimal(str(self.monto_recibido)) - Decimal(str(self.monto)), Decimal('0.00'))


# --------------------------------------------------------------------------
# Helpers de negocio para cobranza
# --------------------------------------------------------------------------

def calcular_diferencia_cambio(self):
    """Calcula la diferencia entre la tasa de factura y la tasa del pago."""
    if not self.pedido:
        return Decimal('0.00')

    tasa_factura = getattr(self.pedido, 'tasa_cambio_original', None)
    tasa_pago = obtener_tasa_para_fecha(self.fecha_pago.date())

    if not tasa_factura or not tasa_pago:
        return Decimal('0.00')

    monto_pyg_facturado = Decimal(str(getattr(self, 'monto_usd', 0))) * Decimal(str(tasa_factura))
    monto_pyg_pagado = Decimal(str(getattr(self, 'monto_usd', 0))) * Decimal(str(tasa_pago.valor))

    return monto_pyg_pagado - monto_pyg_facturado


def facturar_pedido_compra(self):
    """
    Método para facturar un pedido de compra.
    """
    pass

