from django.urls import path

from .views import DocumentoListView, documento_crear

urlpatterns = [
    path('', DocumentoListView.as_view(), name='documento_list'),
    path('crear/', documento_crear, name='documento_crear_general'),
    path('crear/<str:tipo>/', documento_crear, name='documento_crear'),
]
