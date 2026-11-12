from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError

from core.models import EstadoMixin, Moneda, TimeStampedModel, TransicionInvalida


class FacturaComercial(EstadoMixin, TimeStampedModel):
    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        PAGO_PARCIAL = 'PAGO_PARCIAL', 'Pago parcial'
        PAGADA = 'PAGADA', 'Pagada'
        RECIBIDA = 'RECIBIDA', 'Recibida'
        CERRADA = 'CERRADA', 'Cerrada'
        ANULADA = 'ANULADA', 'Anulada'

    class Incoterm(models.TextChoices):
        EXW = 'EXW', 'EXW'
        FCA = 'FCA', 'FCA'
        FOB = 'FOB', 'FOB'
        CFR = 'CFR', 'CFR'
        CIF = 'CIF', 'CIF'
        OTRO = 'OTRO', 'Otro'

    TRANSICIONES = {
        Estado.BORRADOR: (Estado.CONFIRMADA, Estado.ANULADA),
        Estado.CONFIRMADA: (Estado.PAGO_PARCIAL, Estado.PAGADA, Estado.ANULADA),
        Estado.PAGO_PARCIAL: (Estado.PAGADA, Estado.CONFIRMADA),
        Estado.PAGADA: (Estado.RECIBIDA, Estado.PAGO_PARCIAL, Estado.CONFIRMADA),
        Estado.RECIBIDA: (Estado.CERRADA,),
        Estado.CERRADA: (),
        Estado.ANULADA: (),
    }

    proveedor = models.ForeignKey(
        'configuraciones_maestras.Proveedor',
        on_delete=models.PROTECT,
        related_name='facturas_comerciales',
        verbose_name='Proveedor',
    )
    numero = models.CharField('Nº de factura', max_length=50)
    fecha = models.DateField()
    moneda = models.CharField(max_length=3, choices=Moneda.get_choices, default=Moneda.USD)
    incoterm = models.CharField(max_length=5, choices=Incoterm.choices, default=Incoterm.FOB)
    condicion_pago = models.CharField(max_length=100, blank=True, help_text='Ej.: CASH BASE, L/C, 30 días')
    total_declarado = models.DecimalField(max_digits=14, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'), editable=False)
    archivo = models.FileField(upload_to='compras/facturas/%Y/%m/', blank=True)
    observaciones = models.TextField(blank=True)

    # ---- Datos del commercial invoice -------------------------------------
    cliente_importador = models.ForeignKey(
        'clientes_pedidos.Cliente',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='facturas_comerciales',
        verbose_name='Cliente / Importador',
        help_text='Para quién se emitió la factura (for account & risk of).',
    )
    notify_party = models.CharField(
        'Notify party',
        max_length=200,
        blank=True,
        help_text='A quién se notifica el envío (ej.: TO ORDER).',
    )
    puerto_carga = models.CharField('Puerto de carga', max_length=120, blank=True)
    lc_numero = models.CharField('Nº de L/C', max_length=50, blank=True)
    lc_banco = models.ForeignKey(
        'configuraciones_maestras.Banco',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas_comerciales',
        verbose_name='Banco emisor de L/C',
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        editable=False,
    )

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'factura comercial'
        verbose_name_plural = 'facturas comerciales'
        constraints = [
            models.UniqueConstraint(fields=['proveedor', 'numero'], name='uniq_factura_proveedor_numero'),
            models.CheckConstraint(condition=Q(total_declarado__gte=0), name='factura_total_no_negativo'),
            models.CheckConstraint(condition=Q(monto_pagado__gte=0), name='factura_pagado_no_negativo'),
        ]

    def __str__(self):
        return f'{self.proveedor} · {self.numero}'

    @property
    def total_items(self):
        return sum((item.subtotal for item in self.items.all()), Decimal('0'))

    @property
    def diferencia_total(self):
        return self.total_declarado - self.total_items

    @property
    def saldo_pendiente(self):
        return self.total_declarado - self.monto_pagado

    @property
    def unidades(self):
        """Cantidad total de unidades facturadas."""
        return sum((item.cantidad for item in self.items.all()), 0)

    @property
    def chasis_declarados(self):
        """Chasis informados en las líneas de la factura."""
        return [item.chasis for item in self.items.all() if item.chasis]

    @property
    def editable(self):
        """Solo las facturas en borrador admiten cambios en sus ítems."""
        return self.estado == self.Estado.BORRADOR

    def validar_confirmada(self):
        if not self.items.exists():
            return
        if self.diferencia_total != 0:
            raise TransicionInvalida(
                f'El total declarado ({self.total_declarado}) no coincide con la suma '
                f'de los ítems ({self.total_items}).'
            )

    def validar_pago_parcial(self):
        if not (0 < self.monto_pagado < self.total_declarado):
            raise TransicionInvalida('El monto pagado debe ser mayor que 0 y menor que el total.')

    def validar_pagada(self):
        if self.monto_pagado < self.total_declarado:
            raise TransicionInvalida(
                f'Falta pagar {self.saldo_pendiente} {self.moneda} para completar la factura.'
            )

    def validar_recibida(self):
        pendientes = [item for item in self.items.all() if item.cantidad_recibida < item.cantidad]
        if pendientes:
            raise TransicionInvalida(
                'Hay ítems sin recibir en depósito: ' + ', '.join(item.descripcion for item in pendientes)
            )

    def validar_anulada(self):
        if self.monto_pagado > 0:
            raise TransicionInvalida('No se puede anular una factura con pagos registrados.')
        if any(item.embarque_items.exists() for item in self.items.all()):
            raise TransicionInvalida('No se puede anular: hay ítems asignados a un embarque.')


class FacturaItem(TimeStampedModel):
    factura = models.ForeignKey(FacturaComercial, on_delete=models.CASCADE, related_name='items')
    vehiculo = models.ForeignKey(
        'inventario.Vehiculo',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='items_factura',
    )
    repuesto = models.ForeignKey(
        'inventario.Repuesto',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='items_factura',
    )
    descripcion = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)

    # ---- Datos de la línea del commercial invoice --------------------------
    anio = models.PositiveSmallIntegerField('Año', null=True, blank=True)
    chasis = models.CharField('Chasis', max_length=30, blank=True)
    motor = models.CharField('Motor', max_length=30, blank=True)
    peso_kg = models.DecimalField('Peso (kg)', max_digits=10, decimal_places=2, null=True, blank=True)
    cbm = models.DecimalField('Volumen (m³)', max_digits=10, decimal_places=3, null=True, blank=True)

    class Meta:
        ordering = ['factura', 'id']
        constraints = [
            models.CheckConstraint(condition=Q(cantidad__gte=1), name='item_cantidad_positiva'),
        ]

    def __str__(self):
        return f'{self.descripcion} x{self.cantidad}'

    def clean(self):
        if self.factura_id and self.factura.estado != FacturaComercial.Estado.BORRADOR:
            raise ValidationError('Solo se pueden modificar ítems de una factura en borrador.')

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    @property
    def cantidad_embarcada(self):
        return sum((detalle.cantidad for detalle in self.embarque_items.all()), 0)

    @property
    def cantidad_recibida(self):
        return self.cantidad_embarcada

    @property
    def cantidad_pendiente_embarque(self):
        return self.cantidad - self.cantidad_embarcada
