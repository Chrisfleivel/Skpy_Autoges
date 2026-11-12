from django import forms
from django.forms import inlineformset_factory
from compras.models import FacturaItem
from .models import (
    ContenedorImportacion,
    DocumentoAdjunto,
    DocumentoAduanero,
    Embarque,
    EmbarqueContenedor,
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
            'shipper',
            'consignatario',
            'notify',
            'lugar_recepcion',
            'puerto_carga',
            'puerto_descarga',
            'destino_final',
            'peso_bruto_kg',
            'volumen_m3',
            'numero_bultos',
            'fecha_emision',
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
            'shipper': forms.TextInput(attrs={'class': 'form-control'}),
            'consignatario': forms.TextInput(attrs={'class': 'form-control'}),
            'notify': forms.TextInput(attrs={'class': 'form-control'}),
            'lugar_recepcion': forms.TextInput(attrs={'class': 'form-control'}),
            'puerto_carga': forms.TextInput(attrs={'class': 'form-control'}),
            'puerto_descarga': forms.TextInput(attrs={'class': 'form-control'}),
            'destino_final': forms.TextInput(attrs={'class': 'form-control'}),
            'peso_bruto_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'volumen_m3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'numero_bultos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'fecha_emision': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_embarque': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'eta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_arribo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_recepcion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmbarqueContenedorForm(forms.ModelForm):
    """Datos de un contenedor físico del embarque."""

    class Meta:
        model = EmbarqueContenedor
        fields = ['numero', 'tipo', 'sello', 'peso_bruto_kg', 'volumen_m3', 'bultos', 'observaciones']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: MEDUKC733517'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: 40HC'}),
            'sello': forms.TextInput(attrs={'class': 'form-control'}),
            'peso_bruto_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'volumen_m3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'bultos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_numero(self):
        numero = (self.cleaned_data.get('numero') or '').strip().upper()
        if not numero:
            raise forms.ValidationError('Ingrese el número de contenedor.')
        return numero


class EmbarqueContenedorFormSet(inlineformset_factory(
    Embarque,
    EmbarqueContenedor,
    form=EmbarqueContenedorForm,
    extra=2,
    can_delete=True,
)):
    """Formset de contenedores: valida que no se repitan números en un embarque."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        vistos = {}
        for indice, form in enumerate(self.forms):
            if not form.has_changed() or form.cleaned_data.get('DELETE'):
                continue
            numero = (form.cleaned_data.get('numero') or '').strip().upper()
            if not numero:
                continue
            if numero in vistos:
                self.non_form_errors().append(
                    f'El contenedor {numero} está repetido en las filas {vistos[numero] + 1} y {indice + 1}.'
                )
            else:
                vistos[numero] = indice


class DocumentoEmbarqueForm(forms.ModelForm):
    """
    Documento asociado a un embarque (B/L, packing list, despacho, póliza).

    El vínculo con el embarque lo define la vista, no el usuario.
    """

    class Meta:
        model = DocumentoAdjunto
        fields = ['tipo', 'archivo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: B/L original'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices = [
            (DocumentoAdjunto.Tipo.BL, 'Bill of Lading'),
            (DocumentoAdjunto.Tipo.PACKING, 'Packing list'),
            (DocumentoAdjunto.Tipo.DESPACHO, 'Despacho aduanero'),
            (DocumentoAdjunto.Tipo.SEGURO, 'Póliza de seguro'),
            (DocumentoAdjunto.Tipo.OTRO, 'Otro'),
        ]
        self.fields['descripcion'].required = False


class EmbarqueItemForm(forms.ModelForm):
    class Meta:
        model = EmbarqueItem
        fields = ['factura_item', 'contenedor', 'cantidad', 'peso_kg', 'chasis_bl']
        widgets = {
            'factura_item': forms.Select(attrs={'class': 'form-control'}),
            'contenedor': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'chasis_bl': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.embarque = kwargs.pop('embarque', None)
        super().__init__(*args, **kwargs)
        if 'factura_item' in self.fields:
            self.fields['factura_item'].queryset = FacturaItem.objects.select_related('factura').order_by('-factura__fecha', '-id')
        if 'contenedor' in self.fields:
            contenedores = EmbarqueContenedor.objects.all().order_by('numero')
            if self.embarque is not None:
                contenedores = contenedores.filter(embarque=self.embarque)
            elif self.instance and self.instance.embarque_id:
                contenedores = contenedores.filter(embarque_id=self.instance.embarque_id)
            self.fields['contenedor'].queryset = contenedores
            self.fields['contenedor'].empty_label = 'Seleccione el contenedor'
            self.fields['contenedor'].help_text = (
                'Contenedor del embarque donde se carga la unidad.'
            )


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
