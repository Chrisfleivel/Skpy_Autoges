"""from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def requiere_privilegio(nombre_privilegio):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            usuario = request.user
            privilegios_usuario = set(usuario.user_permissions.values_list('nombre', flat=True))
            # También sumar privilegios de roles
            for rol in usuario.groups.all():
                privilegios_usuario.update(rol.privilegios.values_list('nombre', flat=True))
            if nombre_privilegio in privilegios_usuario:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator"""