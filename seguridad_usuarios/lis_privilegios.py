# Ejecuta en el shell: python manage.py shell

from seguridad_usuarios.models import Privilegio

privilegios = [
    ('ver_usuarios', 'Puede ver la lista de usuarios'),
    ('crear_usuario', 'Puede crear nuevos usuarios'),
    ('editar_usuario', 'Puede editar usuarios existentes'),
    ('eliminar_usuario', 'Puede eliminar usuarios'),
    ('ver_roles', 'Puede ver la lista de roles'),
    ('crear_rol', 'Puede crear nuevos roles'),
    ('editar_rol', 'Puede editar roles existentes'),
    ('eliminar_rol', 'Puede eliminar roles'),
    ('ver_privilegios', 'Puede ver la lista de privilegios'),
    ('crear_privilegio', 'Puede crear nuevos privilegios'),
    ('editar_privilegio', 'Puede editar privilegios existentes'),
    ('eliminar_privilegio', 'Puede eliminar privilegios')]

for privilegio in privilegios:
    nombre, descripcion = privilegio
    if not Privilegio.objects.filter(nombre=nombre).exists():
        Privilegio.objects.create(nombre=nombre, descripcion=descripcion)

