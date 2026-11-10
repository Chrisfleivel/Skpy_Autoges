from django.urls import path

from . import views

urlpatterns = [
    path('balance/', views.vista_balance_general, name='vista_balance_general'),
    path('balance/pdf/', views.exportar_balance_pdf, name='exportar_balance_pdf'),
    path('estado-resultados/', views.vista_estado_resultados, name='vista_estado_resultados'),
    path('cierre-mensual/', views.cierre_mensual, name='cierre_mensual'),
    path('libro-mayor/', views.vista_libro_mayor, name='vista_libro_mayor'),
    path('asientos/', views.listar_asientos_contables, name='listar_asientos_contables'),
    path('asientos/<int:asiento_id>/', views.detalle_asiento_contable, name='detalle_asiento_contable'),
    path('asientos/<int:asiento_id>/revisar/', views.marcar_asiento_revisado, name='marcar_asiento_revisado'),
    path('asientos/auditoria/', views.auditoria_asientos_contables, name='auditoria_asientos_contables'),
    path('auditoria-ajustes/', views.dashboard_auditoria_ajustes, name='dashboard_auditoria_ajustes'),
]
