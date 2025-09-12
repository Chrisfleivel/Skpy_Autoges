# seguridad_usuarios/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('cambiar_contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),

    # Usuarios
    # path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    # path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    # path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    # path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),

    # Permisos
    path('permisos/', views.lista_permisos, name='lista_permisos'),
    path('permisos/crear/', views.agregar_permiso, name='agregar_permiso'),
    # path('permisos/<int:permiso_id>/', views.detalle_permiso, name='detalle_permiso'),
    path('permisos/<int:permiso_id>/editar/', views.editar_permiso, name='editar_permiso'),
    path('permisos/<int:permiso_id>/eliminar/', views.eliminar_permiso, name='eliminar_permiso'),

    # Historial de Cambios
    # path('historial/', views.historial_cambios, name='historial_cambios'),

    # Roles
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/crear/', views.agregar_rol, name='crear_rol'),
    # path('roles/<int:pk>/', views.detalle_rol, name='detalle_rol'),
    path('roles/<int:pk>/editar/', views.editar_rol, name='editar_rol'),
    # path('roles/<int:pk>/eliminar/', views.eliminar_rol, name='eliminar_rol'),

    # Empleados
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/crear/', views.agregar_empleado, name='agregar_empleado'),
    path('empleados/<int:pk>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleados/<int:pk>/', views.detalle_empleado, name='detalle_empleado'),
    # path('empleados/<int:pk>/eliminar/', views.eliminar_empleado, name='eliminar_empleado'),

    # Perfil
    path('perfil/', views.lista_perfiles, name='lista_perfiles'),
    # perfil usuario
    path('perfil/e/<int:empleado_id>/', views.perfil_usuario, name='perfil_usuario'),
    # path('perfil/crear/', views.crear_perfil, name='crear_perfil'),
    #lista perfiles
    path('perfiles/', views.lista_perfiles, name='lista_perfiles'),

    path('perfil/<int:pk>/', views.ver_perfil, name='perfil'),
    # crear_usuario_para_empleado 
    path('empleados/<int:empleado_id>/crear_usuario/', views.crear_usuario_para_empleado, name='crear_usuario_para_empleado'),
]