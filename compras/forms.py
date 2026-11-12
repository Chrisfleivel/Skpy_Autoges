from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from importaciones.models import DocumentoAdjunto

from .models import FacturaComercial, FacturaItem


class FacturaComercialForm(forms.ModelForm):
    """
    Formulario de la factura comercial (commercial invoice).

    Los datos del proveedor, comprador y condiciones de pago reproducen el
    documento original; los ítems se cargan con un formset en línea.
    """

    class Meta:
        model = FacturaComercial
        fields = [
            'proveedor',
            'numero',
            'fecha',
            'cliente_importador',
            'notify_party',
            'puerto_carga',
            'moneda',
            'incoterm',
            'condicion_pago',
            'lc_numero',
            'lc_banco',
            'total_declarado',
            'archivo',
            'observaciones',
        ]
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: 20260826'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cliente_importador': forms.Select(attrs={'class': 'form-select'}),
            'notify_party': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: TO ORDER'}),
            'puerto_carga': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: INCHEON, KOREA'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'incoterm': forms.Select(attrs={'class': 'form-select'}),
            'condicion_pago': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: CASH BASE'}),
            'lc_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'lc_banco': forms.Select(attrs={'class': 'form-select'}),
            'total_declarado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].queryset = self.fields['proveedor'].queryset.order_by('razon_social', 'nombre')
        self.fields['cliente_importador'].empty_label = 'Sin cliente / importador'
        self.fields['lc_banco'].empty_label = 'Sin banco emisor'


class FacturaItemForm(forms.ModelForm):
    """
    Línea de la factura comercial: vehículo o repuesto, descripción y,
    cuando el documento los informa, año, chasis, motor, peso y volumen.
    """

    class Meta:
        model = FacturaItem
        fields = [
            'vehiculo',
            'descripcion',
            'cantidad',
            'precio_unitario',
            'anio',
            'chasis',
            'motor',
            'peso_kg',
            'cbm',
        ]
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: Hyundai Tucson'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2100'}),
            'chasis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chasis No.'}),
            'motor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engine No.'}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cbm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehiculo'].empty_label = 'Sin vehículo en inventario'
        self.fields['vehiculo'].queryset = self.fields['vehiculo'].queryset.order_by('nombre')
        for campo in ('precio_unitario', 'peso_kg', 'cbm'):
            self.fields[campo].required = False
        self.fields['precio_unitario'].required = True

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        precio = cleaned_data.get('precio_unitario')
        if cantidad is not None and precio is not None and cantidad < 1:
            self.add_error('cantidad', 'La cantidad debe ser al menos 1.')
        return cleaned_data

    @property
    def subtotal(self):
        """Subtotal de la línea (cantidad x precio unitario)."""
        cantidad = Decimal('0')
        precio = Decimal('0')
        if self.is_bound and self.prefix:
            try:
                cantidad = Decimal(self.data.get(f'{self.prefix}-cantidad') or '0')
            except Exception:
                cantidad = Decimal('0')
            try:
                precio = Decimal(self.data.get(f'{self.prefix}-precio_unitario') or '0')
            except Exception:
                precio = Decimal('0')
        elif self.instance and self.instance.pk:
            cantidad = self.instance.cantidad or 0
            precio = self.instance.precio_unitario or Decimal('0')
        return (cantidad or 0) * (precio or 0)


class BaseFacturaItemFormSet(inlineformset_factory(
    FacturaComercial,
    FacturaItem,
    form=FacturaItemForm,
    extra=1,
    can_delete=True,
)):
    """Formset de ítems con control de chasis duplicados en la misma factura."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        vistos = {}
        for indice, form in enumerate(self.forms):
            if not form.has_changed() or not form.cleaned_data.get('chasis'):
                continue
            chasis = form.cleaned_data['chasis'].strip().upper()
            if chasis in vistos:
                self.non_form_errors().append(
                    f'El chasis {chasis} está repetido en las líneas {vistos[chasis] + 1} y {indice + 1}.'
                )
            else:
                vistos[chasis] = indice


FacturaItemFormSet = BaseFacturaItemFormSet


class DocumentoFacturaForm(forms.ModelForm):
    """
    Adjunto de la factura comercial (por ejemplo, el PDF del commercial invoice).

    El vínculo con la factura lo define la vista, no el usuario.
    """

    class Meta:
        model = DocumentoAdjunto
        fields = ['tipo', 'archivo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: PDF de la factura'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices = [
            (DocumentoAdjunto.Tipo.FACTURA, 'Factura comercial'),
            (DocumentoAdjunto.Tipo.OTRO, 'Otro'),
        ]
        self.fields['descripcion'].required = False

