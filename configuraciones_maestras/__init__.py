# configuraciones_maestras/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class ConfiguracionesMaestrasConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'configuraciones_maestras'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Configuraciones y Datos Maestros"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'configuraciones_maestras.ConfiguracionesMaestrasConfig'

# descripción más detallada
"""
Esta aplicación gestiona los datos maestros del sistema SKPY AutoGest.
Su función es proporcionar un CRUD (Crear, Leer, Actualizar, Borrar) para
entidades de configuración estática y de referencia, como:
- Proveedores
- Agentes de Transporte
- Despachantes de Aduana
- Tasas de Cambio
- Otros datos que sirvan como base para los módulos principales del negocio.
Esta separación permite que los módulos de procesos (ventas, inventario)
utilicen estos datos sin necesidad de gestionar su mantenimiento.
"""