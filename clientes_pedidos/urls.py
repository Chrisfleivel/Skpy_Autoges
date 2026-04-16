# clientes_pedidos/templates/clientes_pedidos/detalle_cliente.html
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.agregar_cliente, name='agregar_cliente'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/realizar_pedido/', views.realizar_pedido, name='realizar_pedido'),
    path('clientes/<int:cliente_id>/realizar_pedido_importacion/', views.realizar_pedido_a_medida, name='realizar_pedido_a_medida'),

    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedidos/<int:pedido_id>/editar/', views.editar_pedido, name='editar_pedido'),
    
    # path('cotizaciones/', login_required(views.lista_cotizaciones), name='lista_cotizaciones'),
    # path('cotizaciones/<int:cotizacion_id>/', login_required(views.detalle_cotizacion), name='detalle_cotizacion'),
    # path('cotizaciones/<int:cotizacion_id>/editar/', login_required(views.editar_cotizacion), name='editar_cotizacion'),
    
    path('pedidos/agregar/', views.agregar_pedido, name='agregar_pedido'),
    # path('pedidos/<int:pedido_id>/cotizacion/crear/', login_required(views.crear_cotizacion), name='crear_cotizacion'),
    
    # path('item_pedido/crear/', login_required(views.crear_item_pedido), name='crear_item_pedido'),
    # path('item_pedido/<int:item_id>/editar/', login_required(views.editar_item_pedido), name='editar_item_pedido'),
    # path('item_pedido/<int:item_id>/eliminar/', login_required(views.eliminar_item_pedido), name='eliminar_item_pedido'),
    # path('item_pedido/<int:item_id>/', login_required(views.detalle_item_pedido), name='detalle_item_pedido'),
    
]