# clientes_pedidos/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class ClientesPedidosConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'clientes_pedidos'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Clientes y Pedidos"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'clientes_pedidos.ClientesPedidosConfig'

# En un comentario, se puede agregar una descripción más detallada
"""
Esta aplicación gestiona la interacción con los clientes y el ciclo de vida de los pedidos
en el sistema SKPY AutoGest. Sus funcionalidades principales incluyen:
- CRUD de clientes.
- Creación y gestión de cotizaciones para pedidos a medida.
- Realización de pedidos a partir del catálogo o de una cotización.
- Mantenimiento del historial de pedidos y del estado de los mismos.
Esta aplicación es crucial para el área de ventas y la relación con los clientes.
"""