from django.urls import path

from . import views

urlpatterns = [
    path('facturas/', views.lista_facturas, name='lista_facturas_comerciales'),
    path('facturas/nueva/', views.agregar_factura, name='agregar_factura_comercial'),
    path('facturas/<int:pk>/', views.detalle_factura, name='detalle_factura_comercial'),
    path('facturas/<int:pk>/editar/', views.editar_factura, name='editar_factura_comercial'),
    path('facturas/<int:pk>/eliminar/', views.eliminar_factura, name='eliminar_factura_comercial'),
    path('facturas/<int:pk>/confirmar/', views.confirmar_factura, name='confirmar_factura_comercial'),
    path('facturas/<int:pk>/documentos/agregar/', views.agregar_documento_factura, name='agregar_documento_factura_comercial'),
    path(
        'facturas/<int:pk>/documentos/<int:documento_pk>/eliminar/',
        views.eliminar_documento_factura,
        name='eliminar_documento_factura_comercial',
    ),
]
