from django import forms

from .models import (
    Autofactura,
    ComprobanteEgreso,
    DocumentoFinanciero,
    Factura,
    ReciboDinero,
)

COMMON_FIELDS = [
    'tipo_documento',
    'timbrado',
    'establecimiento',
    'punto_expedicion',
    'numero_documento',
    'fecha_emision',
    'fecha_vencimiento',
    'moneda',
    'tipo_cambio',
    'cliente',
    'proveedor',
    'pedido',
    'documento_referencia',
    'estado',
    'estado_sifen',
    'total_bruto',
    'total_descuento',
    'total_impuestos',
    'monto_total',
    'observaciones',
    'referencia_externa',
]


class DocumentoFinancieroForm(forms.ModelForm):
    class Meta:
        model = DocumentoFinanciero
        fields = COMMON_FIELDS
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = COMMON_FIELDS + ['tipo_factura']
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }


class AutofacturaForm(forms.ModelForm):
    class Meta:
        model = Autofactura
        fields = COMMON_FIELDS + ['tipo_factura']
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }


class ReciboDineroForm(forms.ModelForm):
    class Meta:
        model = ReciboDinero
        fields = COMMON_FIELDS + ['factura_relacionada', 'medio_pago', 'cuenta_contable']
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }


class ComprobanteEgresoForm(forms.ModelForm):
    class Meta:
        model = ComprobanteEgreso
        fields = COMMON_FIELDS + ['beneficiario', 'medio_pago', 'cuenta_contable']
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
