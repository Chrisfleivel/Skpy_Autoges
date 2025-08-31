# reportes/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class ReportesConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'reportes'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Reportes y Notificaciones"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'reportes.ReportesConfig'

# En un comentario, se puede agregar una descripción más detallada
"""
Esta aplicación gestiona la generación de reportes y las notificaciones
del sistema SKPY AutoGest. Su objetivo es proporcionar herramientas
para el análisis y la comunicación interna y externa.
Las funcionalidades clave incluyen:
- Generación de reportes de ventas, inventario y finanzas a partir de los
  datos de las otras aplicaciones.
- Opciones de filtrado y visualización de los datos.
- Gestión de plantillas y lógica para el envío de notificaciones automáticas
  (ej. estado de pedidos, stock bajo).
Esta aplicación es esencial para la supervisión del negocio y la comunicación.
"""