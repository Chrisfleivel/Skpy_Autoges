# reposicion_stock/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class ReposicionStockConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'reposicion_stock'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Gestión de Reposición de Stock"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'reposicion_stock.ReposicionStockConfig'

# En un comentario, se puede agregar una descripción más detallada
"""
Esta aplicación gestiona la lógica de reposición de inventario en SKPY AutoGest.
Su objetivo es asegurar que los niveles de stock de vehículos y repuestos
se mantengan por encima de un umbral mínimo predefinido.
Las funcionalidades clave incluyen:
- Monitoreo automático del inventario para identificar productos con stock bajo.
- Generación de solicitudes de reposición de stock.
- Vinculación de estas solicitudes con el módulo de importaciones para su consolidación.
Esta aplicación trabaja en estrecha colaboración con los módulos 'inventario' e 'importaciones'.
"""