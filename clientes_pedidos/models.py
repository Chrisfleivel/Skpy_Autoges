# clientes_pedidos/models.py

from django.db import models
from django.contrib.auth import get_user_model
from inventario.models import Vehiculo, Repuesto

Usuario = get_user_model()

# --------------------------------------------------------------------------
# Modelo para representar a un Cliente
# --------------------------------------------------------------------------
class Cliente(models.Model):
    """
    Modelo que representa a un Cliente.
    """
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento_identidad = models.CharField(max_length=20, unique=True, verbose_name="Cédula/RUC")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

# --------------------------------------------------------------------------
# Modelo para representar un Pedido
# --------------------------------------------------------------------------
class Pedido(models.Model):
    """
    Modelo que representa un Pedido de un Cliente.
    Puede ser de stock (catálogo) o un pedido a medida (por importar).
    """
    TIPO_PEDIDO = (
        ('stock', 'Pedido de Stock'),
        ('medida', 'Pedido a Medida'),
    )
    ESTADO_PEDIDO = (
        ('pendiente', 'Pendiente de Aprobación'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    )

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos')
    vendedor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='pedidos_venta')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO, default='pendiente')
    tipo = models.CharField(max_length=10, choices=TIPO_PEDIDO)
    observaciones = models.TextField(blank=True, null=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente}"

# --------------------------------------------------------------------------
# Modelo para representar un Ítem de Pedido
# --------------------------------------------------------------------------
class ItemPedido(models.Model):
    """
    Modelo que representa un ítem dentro de un Pedido.
    """
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"

    def __str__(self):
        if self.vehiculo:
            return f"Ítem de Pedido: {self.vehiculo.nombre} - Cantidad: {self.cantidad}"
        elif self.repuesto:
            return f"Ítem de Pedido: {self.repuesto.nombre} - Cantidad: {self.cantidad}"
        return "Ítem de Pedido sin producto"

# --------------------------------------------------------------------------
# Modelo para representar una Cotización de un Pedido a Medida
# --------------------------------------------------------------------------
class Cotizacion(models.Model):
    """
    Modelo que representa una Cotización para un Pedido a Medida.
    """
    ESTADO_COTIZACION = (
        ('solicitada', 'Solicitada'),
        ('enviada', 'Enviada al Cliente'),
        ('aprobada', 'Aprobada por el Cliente'),
        ('rechazada', 'Rechazada por el Cliente'),
    )

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cotizaciones')
    vendedor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='cotizaciones_venta')
    fecha_cotizacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_COTIZACION, default='solicitada')
    descripcion_solicitud = models.TextField(verbose_name="Descripción del Producto Solicitado")
    monto_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_validez = models.DateField(verbose_name="Fecha de Validez de la Cotización", null=True, blank=True)

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_cotizacion']

    def __str__(self):
        return f"Cotización #{self.pk} para {self.cliente}"
