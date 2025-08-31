# configuraciones_maestras/forms.py

from django import forms
from .models import Proveedor, AgenteTransporte, DespachanteAduana, TasaCambio

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono', 'email', 'ruc']

class AgenteTransporteForm(forms.ModelForm):
    class Meta:
        model = AgenteTransporte
        fields = ['nombre', 'contacto', 'telefono', 'email', 'ruc']

class DespachanteAduanaForm(forms.ModelForm):
    class Meta:
        model = DespachanteAduana
        fields = ['nombre', 'contacto', 'telefono', 'email', 'registro']

class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['moneda_origen', 'moneda_destino', 'valor', 'fecha_actualizacion']

