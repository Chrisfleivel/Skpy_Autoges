# cobranzas/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class CobranzasConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'cobranzas'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Gestión de Cobranzas"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'cobranzas.CobranzasConfig'

# En un comentario, se puede agregar una descripción más detallada
"""
Esta aplicación gestiona el registro y seguimiento de los pagos de los clientes
dentro del sistema SKPY AutoGest. Su funcionalidad principal es:
- Registrar los pagos recibidos, ya sean por pedidos confirmados o por pagos iniciales de cotizaciones.
- Vincular cada pago con el pedido o cotización correspondiente.
- Mantener un registro de los saldos pendientes de los clientes.
Esta app trabaja en estrecha colaboración con la aplicación 'clientes_pedidos'.
"""