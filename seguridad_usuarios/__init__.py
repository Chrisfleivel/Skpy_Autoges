# seguridad_usuarios/__init__.py

from django.apps import AppConfig

# Se define una clase de configuración para la aplicación
class SeguridadUsuariosConfig(AppConfig):
    # Nombre de la aplicación (nombre de la carpeta)
    name = 'seguridad_usuarios'
    # Nombre descriptivo que aparecerá en el panel de administración, etc.
    verbose_name = "Seguridad y Gestión de Usuarios"

# Se importa la clase de configuración para que esté disponible
default_app_config = 'seguridad_usuarios.SeguridadUsuariosConfig'

# descripción más detallada
"""
Esta aplicación gestiona la seguridad del sistema SKPY AutoGest.
Incluye la gestión de usuarios, roles y privilegios para controlar
el acceso y las acciones de cada usuario dentro de la plataforma.
Es el núcleo de la autenticación y autorización del sistema.
"""

"""Esta aplicación es el pilar de la seguridad del sistema SKPY AutoGest. Su función principal es gestionar la autenticación y autorización de todos los usuarios.

Funcionalidad:

Usuarios: CRUD para crear, leer, actualizar y eliminar usuarios.

Roles: CRUD para definir los roles del sistema (Vendedor, Almacenero, etc.).

Privilegios: Definir y asociar privilegios específicos (permisos granulares) a cada rol.

Autenticación: Proporciona la lógica para el inicio de sesión y la gestión de sesiones.

Autorización: Controla el acceso a las vistas y funcionalidades del sistema basándose en los roles y privilegios asignados al usuario.
"""