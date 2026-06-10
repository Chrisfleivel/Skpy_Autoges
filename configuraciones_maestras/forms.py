# configuraciones_maestras/forms.py

from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Proveedor, ContactoProveedor, AgenteTransporte, DespachanteAduana, TasaCambio, Departamento, Cargo

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            'tipo_persona',
            'razon_social',
            'nombre',
            'apellidos',
            'documento_identidad',
            'ruc',
            'direccion',
            'telefono',
            'email',
            'contacto',
            'estado',
        ]
        widgets = {
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Hyundai Motor Company'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez'}),
            'documento_identidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula o pasaporte'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 80012345-6'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección en Corea del Sur o Paraguay'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. +595981234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej. contacto@proveedor.com'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contacto principal'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

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

        if ruc:
            digits = re.sub(r'\D', '', ruc)
            if len(digits) not in (10, 11, 13):
                self.add_error('ruc', 'El RUC debe contener entre 10 y 13 dígitos numéricos.')
            cleaned_data['ruc'] = digits

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in self.Meta.widgets:
                if isinstance(field.widget, forms.CheckboxInput):
                    continue
                field.widget.attrs.update({'class': 'form-control'})

class ContactoProveedorForm(forms.ModelForm):
    class Meta:
        model = ContactoProveedor
        fields = ['tipo_persona', 'nombre', 'apellidos', 'cargo', 'telefono', 'email']
        widgets = {
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del contacto'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del contacto'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': field.widget.attrs.get('class', '') + ' form-control'})

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

class DepartamentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Departamento
        fields = ['nombre', 'descripcion']

class CargoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Cargo
        fields = ['nombre', 'departamento', 'descripcion', 'vacantes', 'salario', 'roles']
        widgets = {
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'roles': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        }

