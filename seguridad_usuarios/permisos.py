DEFAULT_SECTOR = 'Seguridad y Usuarios'


"""Permisos iniciales derivados de los decoradores @revisar_permiso en views.py."""


def generar_permisos_iniciales_seguridad_usuarios():
    """Devuelve los permisos declarados en los views de seguridad_usuarios."""
    return [
        {
            'codename': 'seguridad_usuarios.registrar_usuario',
            'nombre': 'Registrar usuario',
            'descripcion': 'Registrar nuevos usuarios en el sistema.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.editar_perfil',
            'nombre': 'Editar perfil',
            'descripcion': 'Editar el perfil de usuario.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.editar_usuario',
            'nombre': 'Editar usuario',
            'descripcion': 'Editar los datos de usuarios existentes.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_usuario',
            'nombre': 'Eliminar usuario',
            'descripcion': 'Eliminar usuarios del sistema.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.listar_usuarios',
            'nombre': 'Listar usuarios',
            'descripcion': 'Ver la lista de usuarios registrados.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.cambiar_contrasena',
            'nombre': 'Cambiar contraseña',
            'descripcion': 'Permite cambiar la contraseña de usuario.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.agregar_empleado',
            'nombre': 'Agregar empleado',
            'descripcion': 'Agregar nuevos empleados.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.editar_empleado',
            'nombre': 'Editar empleado',
            'descripcion': 'Editar los datos de empleados.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_empleado',
            'nombre': 'Eliminar empleado',
            'descripcion': 'Eliminar empleados del sistema.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.listar_empleados',
            'nombre': 'Listar empleados',
            'descripcion': 'Ver la lista de empleados registrados.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.detallar_empleado',
            'nombre': 'Detalle de empleado',
            'descripcion': 'Ver el detalle de un empleado.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.agregar_rol',
            'nombre': 'Agregar rol',
            'descripcion': 'Agregar nuevos roles.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.editar_rol',
            'nombre': 'Editar rol',
            'descripcion': 'Editar los datos de roles.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.listar_rol',
            'nombre': 'Listar roles',
            'descripcion': 'Ver la lista de roles registrados.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.detallar_rol',
            'nombre': 'Detalle de rol',
            'descripcion': 'Ver el detalle de un rol.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.inactivar_rol',
            'nombre': 'Inactivar rol',
            'descripcion': 'Inactivar un rol existente.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.activar_rol',
            'nombre': 'Activar rol',
            'descripcion': 'Activar un rol existente.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_rol',
            'nombre': 'Eliminar rol',
            'descripcion': 'Eliminar roles del sistema.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.agregar_permiso',
            'nombre': 'Agregar permiso',
            'descripcion': 'Agregar nuevos permisos.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.editar_permiso',
            'nombre': 'Editar permiso',
            'descripcion': 'Editar los datos de permisos.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_permiso',
            'nombre': 'Eliminar permiso',
            'descripcion': 'Permite eliminar permisos del sistema.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.listar_permisos',
            'nombre': 'Listar permisos',
            'descripcion': 'Permite ver la lista de permisos registrados.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.ver_perfil',
            'nombre': 'Ver perfil',
            'descripcion': 'Permite ver el perfil de usuario.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.ver_perfil_usuario',
            'nombre': 'Ver perfil de empleado',
            'descripcion': 'Permite ver el perfil de usuario asociado a un empleado.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.listar_perfiles',
            'nombre': 'Listar perfiles',
            'descripcion': 'Permite ver la lista de perfiles de usuario.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.crear_usuario_para_empleado',
            'nombre': 'Crear usuario para empleado',
            'descripcion': 'Permite crear un usuario y perfil para un empleado.',
            'sector': 'Seguridad y Usuarios'
        },
        {
            'codename': 'seguridad_usuarios.crear_usuario',
            'nombre': 'Crear usuario',
            'descripcion': 'Permite crear nuevos usuarios.',
            'sector': 'Seguridad y Usuarios'
        }
    ]

    