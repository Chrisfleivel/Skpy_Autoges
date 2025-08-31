# cobranzas/models.py

from django.db import models
from clientes_pedidos.models import Pedido, Cotizacion

class Pago(models.Model):
    """
    Modelo que representa un pago recibido de un cliente.
    """
    TIPO_PAGO = (
        ('pedido', 'Pago de Pedido'),
        ('cotizacion', 'Pago de Cotización'),
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
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto del Pago")
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora del Pago")
    metodo_pago = models.CharField(max_length=50, verbose_name="Método de Pago") # Ej: 'Efectivo', 'Transferencia', 'Cheque'
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de {self.monto} - {self.get_tipo_pago_display()}"