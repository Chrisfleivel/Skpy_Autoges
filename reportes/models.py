# reportes/models.py

from django.db import models
from django.contrib.auth import get_user_model

Usuario = get_user_model()

# --------------------------------------------------------------------------
# Modelo para representar la información de un reporte generado
# --------------------------------------------------------------------------
class ReporteGenerado(models.Model):
    """
    Modelo que registra un reporte que ha sido generado en el sistema.
    """
    TIPO_REPORTE = (
        ('ventas', 'Reporte de Ventas'),
        ('inventario', 'Reporte de Inventario'),
        ('financiero', 'Reporte Financiero'),
        ('importaciones', 'Reporte de Importaciones'),
    )

    nombre = models.CharField(max_length=255, verbose_name="Nombre del Reporte")
    tipo = models.CharField(max_length=20, choices=TIPO_REPORTE, verbose_name="Tipo de Reporte")
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Generación")
    usuario_generador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='reportes_generados')
    # Opcional: un campo para almacenar la ruta o el ID del archivo generado
    archivo_ruta = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ruta del Archivo")

    class Meta:
        verbose_name = "Reporte Generado"
        verbose_name_plural = "Reportes Generados"
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.get_tipo_display()} generado por {self.usuario_generador} el {self.fecha_generacion}"


# --------------------------------------------------------------------------
# Modelo para gestionar notificaciones del sistema
# --------------------------------------------------------------------------
class Notificacion(models.Model):
    """
    Modelo para la gestión de notificaciones automáticas y alertas del sistema.
    """
    ESTADO_NOTIFICACION = (
        ('enviada', 'Enviada'),
        ('leida', 'Leída'),
        ('fallida', 'Fallida'),
    )

    asunto = models.CharField(max_length=255, verbose_name="Asunto")
    cuerpo = models.TextField(verbose_name="Cuerpo del Mensaje")
    destinatario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas')
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Envío")
    estado = models.CharField(max_length=10, choices=ESTADO_NOTIFICACION, default='enviada', verbose_name="Estado")
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"Notificación para {self.destinatario} - {self.asunto}"
