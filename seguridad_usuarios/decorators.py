from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def revisar_permiso(nombre_permiso):
    """
    Decorador para revisar si el usuario tiene un permiso específico.
    Si no está autenticado, lo redirige a login.
    Si no tiene el permiso, lo redirige a home.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            usuario = request.user
            if not usuario.is_authenticated:
                return redirect('login')
            # Verificar si el usuario tiene el permiso directamente
            if usuario.has_perm(nombre_permiso):
                return view_func(request, *args, **kwargs)
            # Verificar si el usuario tiene el permiso a través de sus roles
            perfil_usuario = getattr(usuario, 'perfil', None) 
            if perfil_usuario and nombre_permiso in perfil_usuario.permisos_asignados():
                return view_func(request, *args, **kwargs)
            return redirect('home')
        return _wrapped_view
    return decorator

def login_y_permiso_requerido(nombre_permiso):
    def decorator(view_func):
        @login_required
        @revisar_permiso(nombre_permiso)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def revisar_permisos_roles(nombres_permisos):
    """
    Decorador para revisar si el usuario tiene al menos uno de los permisos en la lista.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            usuario = request.user
            if usuario.is_authenticated:
                # Verificar si el usuario tiene alguno de los permisos directamente
                for permiso in nombres_permisos:
                    if usuario.has_perm(permiso):
                        return view_func(request, *args, **kwargs)
                
                # Verificar si el usuario tiene alguno de los permisos a través de sus roles
                empleado = getattr(usuario, 'empleado', None)
                if empleado:
                    permisos_asignados = empleado.permisos_asignados()
                    if any(permiso in permisos_asignados for permiso in nombres_permisos):
                        return view_func(request, *args, **kwargs)
            
            raise PermissionDenied
        return _wrapped_view
    return decorator

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
    return decorator

def login_y_privilegio_requerido(nombre_privilegio):
    def decorator(view_func):
        @login_required
        @requiere_privilegio(nombre_privilegio)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator