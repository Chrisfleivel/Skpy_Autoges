from django import forms
from compras.models import FacturaItem
from .models import (
    ContenedorImportacion,
    DocumentoAdjunto,
    DocumentoAduanero,
    Embarque,
    EmbarqueItem,
    GastoImportacion,
)


class ContenedorImportacionForm(forms.ModelForm):
    class Meta:
        model = ContenedorImportacion
        fields = ['numero', 'descripcion', 'fecha_embarque', 'estado', 'despachante', 'observaciones']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_embarque': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'despachante': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DocumentoAduaneroForm(forms.ModelForm):
    class Meta:
        model = DocumentoAdjunto
        fields = ['tipo', 'archivo', 'descripcion', 'embarque', 'factura']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'embarque': forms.Select(attrs={'class': 'form-control'}),
            'factura': forms.Select(attrs={'class': 'form-control'}),
        }


class FacturaImportacionForm(forms.Form):
    numero_factura = forms.CharField(max_length=100, required=False, label='Número de factura')
    fecha_factura = forms.DateField(required=False, label='Fecha de factura', widget=forms.DateInput(attrs={'type': 'date'}))
    factura_pdf = forms.FileField(required=False, label='Factura PDF')
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones'}), label='Observaciones')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('numero_factura') and not cleaned_data.get('factura_pdf'):
            raise forms.ValidationError('Ingresa el número de factura o sube un archivo PDF.')
        return cleaned_data


class EmbarqueForm(forms.ModelForm):
    class Meta:
        model = Embarque
        fields = [
            'referencia_interna',
            'bl_numero',
            'bl_liberado',
            'flete_prepago',
            'booking',
            'naviera',
            'buque_viaje',
            'puerto_carga',
            'puerto_descarga',
            'destino_final',
            'peso_bruto_kg',
            'volumen_m3',
            'fecha_embarque',
            'eta',
            'fecha_arribo',
            'fecha_recepcion',
            'observaciones',
        ]
        widgets = {
            'referencia_interna': forms.TextInput(attrs={'class': 'form-control'}),
            'bl_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bl_liberado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'flete_prepago': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'booking': forms.TextInput(attrs={'class': 'form-control'}),
            'naviera': forms.TextInput(attrs={'class': 'form-control'}),
            'buque_viaje': forms.TextInput(attrs={'class': 'form-control'}),
            'puerto_carga': forms.TextInput(attrs={'class': 'form-control'}),
            'puerto_descarga': forms.TextInput(attrs={'class': 'form-control'}),
            'destino_final': forms.TextInput(attrs={'class': 'form-control'}),
            'peso_bruto_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'volumen_m3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'fecha_embarque': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'eta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_arribo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_recepcion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmbarqueItemForm(forms.ModelForm):
    class Meta:
        model = EmbarqueItem
        fields = ['factura_item', 'cantidad', 'peso_kg', 'chasis_bl']
        widgets = {
            'factura_item': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'chasis_bl': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'factura_item' in self.fields:
            self.fields['factura_item'].queryset = FacturaItem.objects.select_related('factura').order_by('-factura__fecha', '-id')


class GastoImportacionForm(forms.ModelForm):
    class Meta:
        model = GastoImportacion
        fields = [
            'tipo',
            'descripcion',
            'proveedor_servicio',
            'fecha',
            'monto',
            'moneda',
            'tipo_cambio',
            'criterio_prorrateo',
            'es_costeable',
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'proveedor_servicio': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'moneda': forms.Select(attrs={'class': 'form-control'}),
            'tipo_cambio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'criterio_prorrateo': forms.Select(attrs={'class': 'form-control'}),
            'es_costeable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Compatibilidad con nombres antiguos usados por rutas/views legacy que aún pueden quedar importados.
class ImportacionAduanaUpdateForm(EmbarqueForm):
    pass


class ImportacionForm(EmbarqueForm):
    pass


class FaseImportacionForm(forms.Form):
    fase = forms.CharField(max_length=50, required=False)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    notas = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)


class DocumentoImportacionForm(forms.Form):
    tipo = forms.CharField(max_length=50, required=False)
    numero_referencia = forms.CharField(max_length=120, required=False)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)


class ControlFaseImportacionForm(forms.Form):
    requisito = forms.CharField(max_length=50, required=False)
    completado = forms.BooleanField(required=False)
    observaciones = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
