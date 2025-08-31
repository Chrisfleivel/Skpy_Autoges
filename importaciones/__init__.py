# importaciones/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class ImportacionesConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'importaciones'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Gestión de Importaciones"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'importaciones.ImportacionesConfig'

# En un comentario, se puede agregar una descripción más detallada
"""
Esta aplicación gestiona el proceso completo de importación de productos
desde Corea del Sur a Paraguay para SKPY AutoGest.
Sus funcionalidades clave incluyen:
- Planificación y consolidación de solicitudes de reposición y pedidos a medida.
- Seguimiento del estado de cada importación (ej. en tránsito, en aduana).
- Registro y liquidación de todos los costos de importación (flete, aduana, etc.).
- Gestión de documentos asociados a cada importación (facturas, BL, etc.).
Esta aplicación es esencial para calcular el costo real de los productos y
supervisar la cadena de suministro.
"""