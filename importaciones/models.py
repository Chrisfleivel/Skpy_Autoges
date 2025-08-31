# importaciones/models.py

from django.db import models
from clientes_pedidos.models import Pedido
from inventario.models import Vehiculo, Repuesto
from configuraciones_maestras.models import Proveedor, AgenteTransporte, DespachanteAduana
from django.contrib.auth import get_user_model

Usuario = get_user_model()

# --------------------------------------------------------------------------
# Modelo para representar una Importación Consolidada
# --------------------------------------------------------------------------
class Importacion(models.Model):
    """
    Modelo que representa un proceso de importación consolidado desde Corea.
    """
    ESTADO_IMPORTACION = (
        ('solicitada', 'Solicitada'),
        ('en_transito', 'En Tránsito'),
        ('en_aduana', 'En Aduana'),
        ('despachada', 'Despachada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    )
    
    codigo_seguimiento = models.CharField(max_length=50, unique=True, verbose_name="Código de Seguimiento")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Proveedor")
    agente_transporte = models.ForeignKey(AgenteTransporte, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Agente de Transporte")
    despachante_aduana = models.ForeignKey(DespachanteAduana, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Despachante de Aduana")
    fecha_embarque = models.DateField(null=True, blank=True, verbose_name="Fecha de Embarque")
    fecha_arribo_estimada = models.DateField(null=True, blank=True, verbose_name="Fecha de Arribo Estimada")
    fecha_completado = models.DateField(null=True, blank=True, verbose_name="Fecha de Finalización")
    estado = models.CharField(max_length=20, choices=ESTADO_IMPORTACION, default='solicitada', verbose_name="Estado de Importación")
    usuario_creador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='importaciones_creadas')
    monto_total_costos = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Costo Total de Importación")
    
    class Meta:
        verbose_name = "Importación"
        verbose_name_plural = "Importaciones"
        ordering = ['-fecha_embarque']

    def __str__(self):
        return f"Importación de {self.proveedor} ({self.codigo_seguimiento})"

# --------------------------------------------------------------------------
# Modelo para los ítems de una importación (Vehículos o Repuestos)
# --------------------------------------------------------------------------
class ItemImportacion(models.Model):
    """
    Modelo que representa un ítem (vehículo o repuesto) dentro de una importación.
    """
    importacion = models.ForeignKey(Importacion, on_delete=models.CASCADE, related_name='items')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)
    costo_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo de Compra (Origen)")
    costo_por_item = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo Total por Ítem (Final)")
    
    class Meta:
        verbose_name = "Ítem de Importación"
        verbose_name_plural = "Ítems de Importación"

    def __str__(self):
        if self.vehiculo:
            return f"{self.vehiculo.nombre} - Costo: {self.costo_por_item}"
        elif self.repuesto:
            return f"{self.repuesto.nombre} - Costo: {self.costo_por_item}"
        return "Ítem de Importación"

# --------------------------------------------------------------------------
# Modelo para los costos asociados a una importación
# --------------------------------------------------------------------------
class CostoImportacion(models.Model):
    """
    Modelo que representa un costo asociado a una importación (ej. flete, aduana).
    """
    TIPO_COSTO = (
        ('flete', 'Flete'),
        ('seguro', 'Seguro'),
        ('aduana', 'Aduana'),
        ('impuesto', 'Impuesto'),
        ('otros', 'Otros'),
    )

    importacion = models.ForeignKey(Importacion, on_delete=models.CASCADE, related_name='costos')
    tipo_costo = models.CharField(max_length=20, choices=TIPO_COSTO, verbose_name="Tipo de Costo")
    descripcion = models.CharField(max_length=255, verbose_name="Descripción")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto del Costo")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    
    class Meta:
        verbose_name = "Costo de Importación"
        verbose_name_plural = "Costos de Importación"
        
    def __str__(self):
        return f"{self.get_tipo_costo_display()} - {self.monto}"