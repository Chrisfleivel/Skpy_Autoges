# inventario/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_inventario, name='lista_inventario'),
    
    # Vistas para la gestión de Vehículos
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('vehiculos/agregar/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/', views.detalle_vehiculo, name='detalle_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/editar/', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/<int:vehiculo_id>/eliminar/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    
    # Vistas para la gestión de Repuestos
    path('repuestos/', views.lista_repuestos, name='lista_repuestos'),
    path('repuestos/agregar/', views.agregar_repuesto, name='agregar_repuesto'),
    path('repuestos/<int:repuesto_id>/', views.detalle_repuesto, name='detalle_repuesto'),
    path('repuestos/<int:repuesto_id>/editar/', views.editar_repuesto, name='editar_repuesto'),
    path('repuestos/<int:repuesto_id>/eliminar/', views.eliminar_repuesto, name='eliminar_repuesto'),

    # Vistas para la gestión de Mantenimientos
    path('mantenimientos/', views.lista_mantenimientos, name='lista_mantenimientos'),
    path('mantenimientos/agregar/', views.agregar_mantenimiento, name='agregar_mantenimiento'),
    path('mantenimientos/<int:mantenimiento_id>/', views.detalle_mantenimiento, name='detalle_mantenimiento'),
    path('mantenimientos/<int:mantenimiento_id>/editar/', views.editar_mantenimiento, name='editar_mantenimiento'),
    path('mantenimientos/<int:mantenimiento_id>/eliminar/', views.eliminar_mantenimiento, name='eliminar_mantenimiento'),

    # Vistas para la gestión de Depósitos
    path('depositos/', views.lista_depositos, name='lista_depositos'),
    path('depositos/agregar/', views.agregar_deposito, name='agregar_deposito'),
    path('depositos/<int:deposito_id>/', views.detalle_deposito, name='detalle_deposito'),
    path('depositos/<int:deposito_id>/editar/', views.editar_deposito, name='editar_deposito'),
    path('depositos/<int:deposito_id>/eliminar/', views.eliminar_deposito, name='eliminar_deposito'),   

    # Vistas para la gestión de Unidades de Medida
    path('unidades_medida/', views.lista_unidades_medida, name='lista_unidades_medida'),
    path('unidades_medida/agregar/', views.agregar_unidad_medida, name='agregar_unidad_medida'),
    path('unidades_medida/<int:unidad_id>/', views.detalle_unidad_medida, name='detalle_unidad_medida'),
    path('unidades_medida/<int:unidad_id>/editar/', views.editar_unidad_medida, name='editar_unidad_medida'),
    path('unidades_medida/<int:unidad_id>/eliminar/', views.eliminar_unidad_medida, name='eliminar_unidad_medida'),
]