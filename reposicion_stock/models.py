# reposicion_stock/models.py

from django.db import models
from inventario.models import Repuesto, Vehiculo
from django.contrib.auth import get_user_model
from seguridad_usuarios.models import UsuarioPerfil, User


# --------------------------------------------------------------------------
# Modelo para representar una Solicitud de Reposición de Stock
# --------------------------------------------------------------------------
class SolicitudReposicion(models.Model):
    """
    Modelo que representa una solicitud de reposición de stock para
    vehículos o repuestos.
    """
    ESTADO_SOLICITUD = (
        ('generada', 'Generada'),
        ('enviada', 'Enviada para Consolidación'),
        ('consolidada', 'Consolidada en Importación'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    creador = models.ForeignKey(UsuarioPerfil, on_delete=models.SET_NULL, null=True, related_name='solicitudes_creadas')
    estado = models.CharField(max_length=20, choices=ESTADO_SOLICITUD, default='generada', verbose_name="Estado de la Solicitud")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Solicitud de Reposición"
        verbose_name_plural = "Solicitudes de Reposición"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Solicitud de Reposición #{self.pk} - Estado: {self.get_estado_display()}"


# --------------------------------------------------------------------------
# Modelo para los ítems de la solicitud de reposición
# --------------------------------------------------------------------------
class ItemSolicitud(models.Model):
    """
    Modelo que representa un ítem (vehículo o repuesto) dentro de una
    solicitud de reposición.
    """
    solicitud = models.ForeignKey(SolicitudReposicion, on_delete=models.CASCADE, related_name='items_solicitados')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Solicitada")
    # Opcional: campo para un comentario específico sobre el ítem
    comentario_item = models.TextField(blank=True, null=True, verbose_name="Comentario del Ítem")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Unitario")
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Costo Unitario")
    
    class Meta:
        verbose_name = "Ítem de Solicitud"
        verbose_name_plural = "Ítems de Solicitud"

    def __str__(self):
        if self.vehiculo:
            return f"Ítem: {self.vehiculo.nombre} - Cantidad: {self.cantidad}"
        elif self.repuesto:
            return f"Ítem: {self.repuesto.nombre} - Cantidad: {self.cantidad_solicitada}"
        return "Ítem de Solicitud sin producto"

