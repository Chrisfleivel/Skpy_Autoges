# seguridad_usuarios/admin.py
from django.contrib import admin
from .models import Auditoria, Rol, Permiso, Empleado, UsuarioPerfil

admin.site.register(Auditoria)
admin.site.register(Rol)
admin.site.register(Permiso)
admin.site.register(Empleado)
admin.site.register(UsuarioPerfil)
