from django.urls import path

from . import views

urlpatterns = [
    path('', views.lista_pedidos_cobranzas, name='lista_pedidos_cobranzas'),
    path('dashboard/', views.dashboard_caja, name='dashboard_caja'),
    path('reporte-caja/', views.reporte_caja, name='reporte_caja'),
    path('reporte-caja/exportar/', views.exportar_reporte_caja_csv, name='exportar_reporte_caja_csv'),
    path('reporte-comparativo/', views.reporte_comparativo, name='reporte_comparativo'),
    path('reporte-comparativo/pdf/', views.reporte_comparativo_pdf, name='reporte_comparativo_pdf'),
    path('reporte-comparativo/excel/', views.reporte_comparativo_excel, name='reporte_comparativo_excel'),
    path('panel-caja/', views.panel_caja, name='panel_caja'),
    path('resumen-dia/', views.resumen_dia, name='resumen_dia'),
    path('caja/abrir/', views.abrir_caja, name='abrir_nueva_caja'),
    path('caja/abrir/<int:caja_id>/', views.abrir_caja, name='abrir_caja'),
    path('caja/cerrar/<int:caja_id>/', views.cerrar_caja, name='cerrar_caja'),
    path('transferencia/', views.lista_pedidos_transferencia, name='lista_pedidos_transferencia'),
    path('despacho/', views.lista_pedidos_despacho, name='lista_pedidos_despacho'),
    path('pedidos/<int:pedido_id>/confirmar-pago/', views.confirmar_pago_cobranzas, name='confirmar_pago_cobranzas'),
    path('pedidos/<int:pedido_id>/facturar/', views.facturar_pedido_cobranzas, name='facturar_pedido_cobranzas'),
    path('pedidos/<int:pedido_id>/cancelar/', views.cancelar_pedido_cobranzas, name='cancelar_pedido_cobranzas'),
    path('pedidos/<int:pedido_id>/facturar-contado/', views.facturar_contado_cobranzas, name='facturar_contado_cobranzas'),
    path('pedidos/<int:pedido_id>/entregar-repuesto/', views.entregar_repuesto_cobranzas, name='entregar_repuesto_cobranzas'),
    path('pedidos/<int:pedido_id>/iniciar-transferencia/', views.iniciar_transferencia_cobranzas, name='iniciar_transferencia_cobranzas'),
    path('pedidos/<int:pedido_id>/confirmar-transferencia/', views.confirmar_transferencia_cobranzas, name='confirmar_transferencia_cobranzas'),
    path('pedidos/<int:pedido_id>/preview-factura/', views.previsualizar_factura_cobranzas, name='previsualizar_factura_cobranzas'),
    path('pedidos/<int:pedido_id>/descargar-factura/', views.descargar_factura_cobranzas, name='descargar_factura_cobranzas'),
    path('pedidos/<int:pedido_id>/cobrar/', views.cobrar_pedido, name='cobrar_pedido'),
]
