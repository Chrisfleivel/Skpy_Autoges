# urlpatterns para la gestión de Solicitudes de Reposición de Stock
from django.urls import path
from . import views

urlpatterns = [
    path("agregar/", views.agregar_solicitud_reposicion, name="agregar_solicitud_reposicion"),
    path("listar/", views.listar_solicitudes_reposicion, name="listar_solicitudes_reposicion"),
    path("detalle/<int:pk>/", views.detalle_solicitud_reposicion, name="detalle_solicitud_reposicion"),
    path("editar/<int:pk>/", views.editar_solicitud_reposicion, name="editar_solicitud_reposicion"),
]
