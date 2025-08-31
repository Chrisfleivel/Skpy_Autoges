# inventario/models.py

from django.db import models
from configuraciones_maestras.models import Proveedor

# --------------------------------------------------------------------------
# Modelo para representar la Unidad de Medida de los repuestos
# --------------------------------------------------------------------------
class UnidadMedida(models.Model):
    """
    Modelo para definir las unidades de medida de los repuestos.
    Ej: 'Unidad', 'Litro', 'Caja', 'Metro'.
    """
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre de la Unidad")
    abreviatura = models.CharField(max_length=10, unique=True, verbose_name="Abreviatura")

    class Meta:
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"

# --------------------------------------------------------------------------
# Modelo para representar un Vehículo en el inventario
# --------------------------------------------------------------------------
class Vehiculo(models.Model):
    """
    Modelo que representa un vehículo en el inventario.
    """
    ESTADO_VEHICULO = (
        ('disponible', 'Disponible'),
        ('vendido', 'Vendido'),
        ('mantenimiento', 'En Mantenimiento'),
        ('reservado', 'Reservado'),
    )

    nombre = models.CharField(max_length=150, verbose_name="Nombre del Vehículo")
    marca = models.CharField(max_length=100, verbose_name="Marca")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    año = models.PositiveIntegerField(verbose_name="Año de Fabricación")
    kilometraje = models.PositiveIntegerField(default=0, verbose_name="Kilometraje")
    codigo_chasis = models.CharField(max_length=50, unique=True, verbose_name="Código de Chasis (VIN)")
    estado = models.CharField(max_length=20, choices=ESTADO_VEHICULO, default='disponible', verbose_name="Estado")
    costo_compra = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo de Compra (Guaraníes)")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta Sugerido")
    fecha_ingreso = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Ingreso al Inventario")

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return f"{self.nombre} {self.modelo} ({self.año})"

# --------------------------------------------------------------------------
# Modelo para representar un Repuesto en el inventario
# --------------------------------------------------------------------------
class Repuesto(models.Model):
    """
    Modelo que representa un repuesto en el inventario.
    """
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Repuesto")
    codigo_repuesto = models.CharField(max_length=50, unique=True, verbose_name="Código del Repuesto")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unidad de Medida")
    stock_actual = models.PositiveIntegerField(default=0, verbose_name="Stock Actual")
    stock_minimo = models.PositiveIntegerField(default=0, verbose_name="Stock Mínimo")
    costo_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo de Compra (Guaraníes)")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta Sugerido")
    fecha_ultima_entrada = models.DateTimeField(auto_now=True, verbose_name="Fecha de Última Entrada")

    class Meta:
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo_repuesto})"

# --------------------------------------------------------------------------
# Modelo para registrar el mantenimiento de un vehículo
# --------------------------------------------------------------------------
class MantenimientoVehiculo(models.Model):
    """
    Modelo para registrar las acciones de mantenimiento realizadas a un vehículo.
    """
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='mantenimientos')
    fecha_mantenimiento = models.DateField(verbose_name="Fecha de Mantenimiento")
    descripcion = models.TextField(verbose_name="Descripción del Mantenimiento")
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo del Mantenimiento")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones Adicionales")

    class Meta:
        verbose_name = "Mantenimiento de Vehículo"
        verbose_name_plural = "Mantenimientos de Vehículos"
        ordering = ['-fecha_mantenimiento']

    def __str__(self):
        return f"Mantenimiento de {self.vehiculo} - {self.fecha_mantenimiento}"