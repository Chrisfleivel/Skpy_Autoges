# inventario/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class InventarioConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'inventario'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Gestión de Inventario"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'inventario.InventarioConfig'

# En un comentario, se puede agregar una descripción más detallada
"""
Esta aplicación gestiona el inventario de vehículos y repuestos de SKPY AutoGest.
Sus funcionalidades principales incluyen:
- Registro de la entrada de nuevos productos al almacén.
- Registro de la salida de productos (por venta, traslado, etc.).
- Actualización de la información detallada de cada producto.
- Herramientas para la realización de inventarios físicos.
- Registro y consulta del historial de mantenimiento de vehículos.
Esta aplicación es crítica para el control de stock y la toma de decisiones en el negocio.
"""