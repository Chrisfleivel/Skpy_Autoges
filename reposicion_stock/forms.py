# reposicion_stock/forms.py
from django.forms import inlineformset_factory
from django import forms    
from .models import SolicitudReposicion, ItemSolicitud

class SolicitudReposicionForm(forms.ModelForm):
    class Meta:
        model = SolicitudReposicion
        fields = ['estado', 'observaciones']

ItemSolicitudFormSet = inlineformset_factory(SolicitudReposicion, ItemSolicitud, fields=('vehiculo', 'repuesto', 'cantidad', 'comentario_item', 'precio_unitario', 'costo_unitario'), extra=1)
# Permite agregar múltiples ítems a una solicitud de reposición
# Los campos 'precio_unitario' y 'costo_unitario' se han añadido al formset
# para capturar esta información al crear o editar una solicitud.
# Puedes ajustar 'extra' según cuántos ítems quieras mostrar por defecto
# en el formulario.
# El formset facilita la gestión de los ítems relacionados con una solicitud
# dentro de un solo formulario.
# Puedes personalizar los widgets y validaciones según tus necesidades.
# --------------------------------------------------------------------------    
# Formulario para crear o editar una Solicitud de Reposición de Stock
# --------------------------------------------------------------------------
class ItemSolicitudForm(forms.ModelForm):
    class Meta:
        model = ItemSolicitud
        fields = ['vehiculo', 'repuesto', 'cantidad', 'comentario_item', 'precio_unitario', 'costo_unitario']   
        widgets = {
            'comentario_item': forms.Textarea(attrs={'rows': 2}),
        }