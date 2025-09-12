# configuraciones_maestras/models.py

from django.db import models
from seguridad_usuarios.models import Persona
from django.contrib.auth.models import User

# --------------------------------------------------------------------------
# Modelo para representar un Proveedor
# --------------------------------------------------------------------------
class Proveedor(Persona):
    """
    Modelo que representa un Proveedor de SKPY.
    """
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_proveedor')
    # ...otros campos y métodos...

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# --------------------------------------------------------------------------
# Modelo para representar un Agente de Transporte
# --------------------------------------------------------------------------
class AgenteTransporte(Persona):
    """
    Modelo que representa un Agente de Transporte utilizado en las importaciones.
    """
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_agente_transporte')
    # ...otros campos y métodos...
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    

    class Meta:
        verbose_name = "Agente de Transporte"
        verbose_name_plural = "Agentes de Transporte"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# --------------------------------------------------------------------------
# Modelo para representar un Despachante de Aduana
# --------------------------------------------------------------------------
class DespachanteAduana(Persona):
    """
    Modelo que representa un Despachante de Aduana.
    """
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_despachante_aduana')
    # ...otros campos y métodos...
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Despachante")
    contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Persona de Contacto")
    registro = models.CharField(max_length=50, unique=True, verbose_name="Número de Registro")

    class Meta:
        verbose_name = "Despachante de Aduana"
        verbose_name_plural = "Despachantes de Aduana"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# --------------------------------------------------------------------------
# Modelo para representar una Tasa de Cambio de Moneda
# --------------------------------------------------------------------------
class TasaCambio(models.Model):
    """
    Modelo para registrar las Tasas de Cambio utilizadas en el sistema.
    """
    moneda_origen = models.CharField(max_length=3, verbose_name="Moneda de Origen", default="KRW")
    moneda_destino = models.CharField(max_length=3, verbose_name="Moneda de Destino", default="PYG")
    valor = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Valor de la Tasa")
    fecha_actualizacion = models.DateField(auto_now_add=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"1 {self.moneda_origen} = {self.valor} {self.moneda_destino} (al {self.fecha_actualizacion})"