from django.core.management.base import BaseCommand
from seguridad_usuarios.models import Permiso

class Command(BaseCommand):
    help = 'Carga permisos iniciales en la base de datos'

    def handle(self, *args, **kwargs):
        permisos_iniciales = [
            {
            'codename': 'seguridad_usuarios.registrar_usuario',
            'nombre': 'Registrar usuario',
            'descripcion': 'Permite registrar nuevos usuarios en el sistema.'
        },
        {
            'codename': 'seguridad_usuarios.editar_usuario',
            'nombre': 'Editar usuario',
            'descripcion': 'Permite editar los datos de usuarios existentes.'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_usuario',
            'nombre': 'Eliminar usuario',
            'descripcion': 'Permite eliminar usuarios del sistema.'
        },
        {
            'codename': 'seguridad_usuarios.listar_usuarios',
            'nombre': 'Listar usuarios',
            'descripcion': 'Permite ver la lista de usuarios registrados.'
        },
        {
            'codename': 'seguridad_usuarios.cambiar_contrasena',
            'nombre': 'Cambiar contraseña',
            'descripcion': 'Permite cambiar la contraseña de usuario.'
        },
        {
            'codename': 'seguridad_usuarios.agregar_empleado',
            'nombre': 'Agregar empleado',
            'descripcion': 'Permite agregar nuevos empleados.'
        },
        {
            'codename': 'seguridad_usuarios.editar_empleado',
            'nombre': 'Editar empleado',
            'descripcion': 'Permite editar los datos de empleados.'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_empleado',
            'nombre': 'Eliminar empleado',
            'descripcion': 'Permite eliminar empleados del sistema.'
        },
        {
            'codename': 'seguridad_usuarios.listar_empleados',
            'nombre': 'Listar empleados',
            'descripcion': 'Permite ver la lista de empleados registrados.'
        },
        {
            'codename': 'seguridad_usuarios.detallar_empleado',
            'nombre': 'Detalle de empleado',
            'descripcion': 'Permite ver el detalle de un empleado.'
        },
        {
            'codename': 'seguridad_usuarios.agregar_rol',
            'nombre': 'Agregar rol',
            'descripcion': 'Permite agregar nuevos roles.'
        },
        {
            'codename': 'seguridad_usuarios.editar_rol',
            'nombre': 'Editar rol',
            'descripcion': 'Permite editar los datos de roles.'
        },
        {
            'codename': 'seguridad_usuarios.listar_rol',
            'nombre': 'Listar roles',
            'descripcion': 'Permite ver la lista de roles registrados.'
        },
        {
            'codename': 'seguridad_usuarios.agregar_permiso',
            'nombre': 'Agregar permiso',
            'descripcion': 'Permite agregar nuevos permisos.'
        },
        {
            'codename': 'seguridad_usuarios.editar_permiso',
            'nombre': 'Editar permiso',
            'descripcion': 'Permite editar los datos de permisos.'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_permiso',
            'nombre': 'Eliminar permiso',
            'descripcion': 'Permite eliminar permisos del sistema.'
        },
        {
            'codename': 'seguridad_usuarios.listar_permisos',
            'nombre': 'Listar permisos',
            'descripcion': 'Permite ver la lista de permisos registrados.'
        },
        {
            'codename': 'seguridad_usuarios.ver_perfil',
            'nombre': 'Ver perfil',
            'descripcion': 'Permite ver el perfil de usuario.'
        },
        {
            'codename': 'seguridad_usuarios.ver_perfil_usuario',
            'nombre': 'Ver perfil de empleado',
            'descripcion': 'Permite ver el perfil de usuario asociado a un empleado.'
        },
        {
            'codename': 'seguridad_usuarios.listar_perfiles',
            'nombre': 'Listar perfiles',
            'descripcion': 'Permite ver la lista de perfiles de usuario.'
        },
        {
            'codename': 'seguridad_usuarios.crear_usuario_para_empleado',
            'nombre': 'Crear usuario para empleado',
            'descripcion': 'Permite crear un usuario y perfil para un empleado.'
        },
            
        ]
        for permiso in permisos_iniciales:
            Permiso.objects.get_or_create(
                codename=permiso['codename'],
                defaults={
                    'nombre': permiso['nombre'],
                    'descripcion': permiso['descripcion']
                }
            )
        self.stdout.write(self.style.SUCCESS('Permisos cargados correctamente.'))