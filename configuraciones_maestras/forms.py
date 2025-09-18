# configuraciones_maestras/forms.py

from django import forms
from .models import Proveedor, AgenteTransporte, DespachanteAduana, TasaCambio

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'apellidos', 'razon_social', 'contacto', 'telefono', 'email', 'ruc']
        
        def clean(self):
            cleaned_data = super().clean()
            tipo_persona = cleaned_data.get('tipo_persona')
            nombre = cleaned_data.get('nombre')
            razon_social = cleaned_data.get('razon_social')
            documento_identidad = cleaned_data.get('documento_identidad')
            ruc = cleaned_data.get('ruc')

            if tipo_persona == 'FISICA':
                if not nombre:
                    self.add_error('nombre', 'El nombre es obligatorio para persona física.')
                if not documento_identidad:
                    self.add_error('documento_identidad', 'El documento de identidad es obligatorio para persona física.')
                cleaned_data['razon_social'] = None
            elif tipo_persona == 'JURIDICA':
                if not razon_social:
                    self.add_error('razon_social', 'La razón social es obligatoria para persona jurídica.')
                if not ruc:
                    self.add_error('ruc', 'El RUC es obligatorio para persona jurídica.')
                cleaned_data['nombre'] = None
                cleaned_data['apellidos'] = None

            return cleaned_data

class AgenteTransporteForm(forms.ModelForm):
    class Meta:
        model = AgenteTransporte
        fields = ['nombre', 'apellidos', 'razon_social', 'contacto', 'telefono', 'email', 'ruc']

class DespachanteAduanaForm(forms.ModelForm):
    class Meta:
        model = DespachanteAduana
        fields = ['nombre', 'apellidos', 'razon_social', 'contacto', 'telefono', 'email', 'registro']

class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['moneda_origen', 'moneda_destino', 'valor']

