from django.urls import path

from . import views

urlpatterns = [
    path('', views.lista_pedidos_busqueda, name='lista_pedidos_busqueda'),
]
