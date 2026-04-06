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
    contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Persona de Contacto")
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
    contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Persona de Contacto")
    

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
    



# Departamentos en la empresa

class Departamento(models.Model):
    '''
    Modelo que representa un Departamento en la empresa.
    '''

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Departamento")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del Departamento")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo

    def activar(self):
        self.estado = True
        self.save()

    def inactivar(self):
        self.estado = False
        self.save()

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']


# Cargos o puestos de trabajo en la empresa segun departamentos
class Cargo(models.Model):
    """ 
    Modelo que representa un Cargo o Puesto de Trabajo en la empresa.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Cargo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del Cargo")
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='cargos', verbose_name="Departamento")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo
    vacantes = models.IntegerField(default=1, verbose_name="Número de Vacantes")
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Salario")
    
    def __str__(self):
        return f'{self.nombre} - {self.departamento.nombre}'

    def abrir_vacante(self):
        self.vacantes += 1
        self.save()
    
    def cerrar_vacante(self):
        if self.vacantes > 0:
            self.vacantes -= 1
            self.save()

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['nombre']



# --------------------------------------------------------------------------
# Modelo para almacenar la configuración global de apariencia
# --------------------------------------------------------------------------
class ConfiguracionApariencia(models.Model):
    THEME_DEFAULT = 'theme-default'
    THEME_DARK = 'theme-dark'
    THEME_EMERALD = 'theme-emerald'
    THEME_SUNSET = 'theme-sunset'
    THEME_OCEAN = 'theme-ocean'
    THEME_LIGHT = 'theme-light'

    THEME_CHOICES = [
        (THEME_DEFAULT, 'Azul Profesional (Defecto)'),
        (THEME_DARK, 'Modo Oscuro'),
        (THEME_EMERALD, 'Esmeralda Energético'),
        (THEME_SUNSET, 'Atardecer Cálido'),
        (THEME_OCEAN, 'Océano Profundo'),
        (THEME_LIGHT, 'Tema Luminoso'),
    ]

    FONT_ROBOTO = "'Roboto', sans-serif"
    FONT_PLAYFAIR = "'Playfair Display', serif"
    FONT_MONOSPACE = 'monospace'

    FONT_CHOICES = [
        (FONT_ROBOTO, 'Roboto'),
        (FONT_PLAYFAIR, 'Elegante (Serif)'),
        (FONT_MONOSPACE, 'Sistema (Monospace)'),
    ]

    tema = models.CharField(max_length=40, choices=THEME_CHOICES, default=THEME_DEFAULT, verbose_name='Tema')
    tipografia = models.CharField(max_length=100, choices=FONT_CHOICES, default=FONT_ROBOTO, verbose_name='Tipografía')
    tamanio = models.PositiveSmallIntegerField(default=16, verbose_name='Tamaño de texto (px)')
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Configuración de Apariencia'
        verbose_name_plural = 'Configuraciones de Apariencia'

    def __str__(self):
        return f'{self.get_tema_display()} — {self.tamanio}px'

