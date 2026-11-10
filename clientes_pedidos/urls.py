# clientes_pedidos/templates/clientes_pedidos/detalle_cliente.html
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('clientes/exportar/csv/', views.exportar_clientes_csv, name='exportar_clientes_csv'),
    path('clientes/exportar/pdf/', views.exportar_clientes_pdf, name='exportar_clientes_pdf'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/reporte/', views.reporte_clientes, name='reporte_clientes'),
    path('clientes/crear/', views.agregar_cliente, name='agregar_cliente'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/<int:cliente_id>/realizar_pedido/', views.realizar_pedido, name='realizar_pedido'),
    path('clientes/<int:cliente_id>/realizar_pedido_busqueda/', views.realizar_pedido_busqueda, name='realizar_pedido_busqueda'),
    path('clientes/<int:cliente_id>/realizar_pedido_importacion/', views.realizar_pedido_a_medida, name='realizar_pedido_a_medida'),

    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/abastecimiento/', views.lista_pedidos_abastecimiento, name='lista_pedidos_abastecimiento'),
    path('pedidos/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedidos/<int:pedido_id>/editar/', views.editar_pedido, name='editar_pedido'),
    path('pedidos/<int:pedido_id>/aprobar/', views.aprobar_pedido, name='aprobar_pedido'),
    path('pedidos/<int:pedido_id>/rechazar/', views.rechazar_pedido, name='rechazar_pedido'),
    path('pedidos/<int:pedido_id>/aprobar_rechazar_abastecimiento/', views.aprobar_rechazar_abastecimiento, name='aprobar_rechazar_abastecimiento'),
    path('pedidos/<int:pedido_id>/items/<int:item_id>/actualizar/', views.actualizar_item_pedido, name='actualizar_item_pedido'),
    path('pedidos/<int:pedido_id>/cobranzas/', views.enviar_a_cobranzas, name='enviar_a_cobranzas'),
    path('pedidos/<int:pedido_id>/facturar_contado/', views.facturar_pedido_contado, name='facturar_pedido_contado'),
    path('pedidos/<int:pedido_id>/confirmar_entrega_repuesto/', views.confirmar_entrega_repuesto, name='confirmar_entrega_repuesto'),
    path('pedidos/<int:pedido_id>/programar_transferencia/', views.programar_transferencia, name='programar_transferencia'),
    path('pedidos/<int:pedido_id>/iniciar_transferencia/', views.iniciar_transferencia, name='iniciar_transferencia'),
    path('pedidos/<int:pedido_id>/confirmar_transferencia/', views.confirmar_transferencia, name='confirmar_transferencia'),
    path('pedidos/<int:pedido_id>/cargar_factura/', views.cargar_factura_pedido, name='cargar_factura_pedido'),
    path('pedidos/<int:pedido_id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
    path('pedidos/<int:pedido_id>/exportar_pdf/', views.exportar_pedido_pdf, name='exportar_pedido_pdf'),
    
    # Rutas para el flujo de búsqueda y selección de productos
    path('pedidos/<int:pedido_id>/enviar_seleccion/', views.enviar_a_seleccion, name='enviar_a_seleccion'),
    path('pedidos/<int:pedido_id>/accion_busqueda/<str:accion>/', views.avanzar_pedido_busqueda, name='avanzar_pedido_busqueda'),
    path('seleccion/', views.listar_pedidos_seleccion, name='listar_pedidos_seleccion'),
    path('pedidos/<int:pedido_id>/productos/<int:producto_buscado_id>/confirmar/', 
         views.confirmar_producto_buscado, name='confirmar_producto_buscado'),
    path('pedidos/<int:pedido_id>/productos/<int:producto_buscado_id>/imprimir/', 
         views.imprimir_producto_buscado, name='imprimir_producto_buscado'),
    path('pedidos/<int:pedido_id>/enviar_precio/', views.enviar_precio_cliente, name='enviar_precio_cliente'),
    path('pedidos/<int:pedido_id>/confirmar_precio/', views.confirmar_precio_cliente, name='confirmar_precio_cliente'),
    
    # path('cotizaciones/', login_required(views.lista_cotizaciones), name='lista_cotizaciones'),
    # path('cotizaciones/<int:cotizacion_id>/', login_required(views.detalle_cotizacion), name='detalle_cotizacion'),
    # path('cotizaciones/<int:cotizacion_id>/editar/', login_required(views.editar_cotizacion), name='editar_cotizacion'),
    
    path('pedidos/agregar/', views.agregar_pedido, name='agregar_pedido'),
    path('pedidos/abastecimiento/', views.realizar_pedido_abastecimiento_general, name='realizar_pedido_abastecimiento'),
    path('repuestos/<int:repuesto_id>/abastecer/', views.crear_pedido_abastecimiento, name='crear_pedido_abastecimiento'),
    path('pedidos/búsqueda/', views.realizar_pedido_busqueda_general, name='realizar_pedido_busqueda_general'),

    # API para obtener precio de repuesto y vehículo
    path('api/repuesto/<int:repuesto_id>/precio/', views.obtener_precio_repuesto, name='obtener_precio_repuesto'),
    path('api/vehiculo/<int:vehiculo_id>/precio/', views.obtener_precio_vehiculo, name='obtener_precio_vehiculo'),
    path('api/productos/buscar/', views.buscar_productos_api, name='buscar_productos_api'),

    # path('pedidos/<int:pedido_id>/cotizacion/crear/', login_required(views.crear_cotizacion), name='crear_cotizacion'),
    
    # path('item_pedido/crear/', login_required(views.crear_item_pedido), name='crear_item_pedido'),
    # path('item_pedido/<int:item_id>/editar/', login_required(views.editar_item_pedido), name='editar_item_pedido'),
    # path('item_pedido/<int:item_id>/eliminar/', login_required(views.eliminar_item_pedido), name='eliminar_item_pedido'),
    # path('item_pedido/<int:item_id>/', login_required(views.detalle_item_pedido), name='detalle_item_pedido'),
    
]