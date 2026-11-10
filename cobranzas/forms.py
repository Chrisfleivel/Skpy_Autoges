from django import forms

from configuraciones_maestras.models import Sucursal

from .models import Caja, Pago, AperturaCaja, CierreCaja


class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['sucursal', 'nombre', 'observaciones']


class AperturaCajaForm(forms.ModelForm):
    sucursal = forms.ModelChoiceField(queryset=None, label='Sucursal')
    nombre = forms.CharField(max_length=100, required=False, label='Nombre de la caja')
    monto_inicial = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0, initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sucursal'].queryset = Sucursal.objects.filter(activa=True)

    class Meta:
        model = AperturaCaja
        fields = ['sucursal', 'nombre', 'monto_inicial', 'observaciones']
        widgets = {'observaciones': forms.Textarea(attrs={'rows': 3})}


class CierreCajaForm(forms.ModelForm):
    monto_real = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0)

    class Meta:
        model = CierreCaja
        fields = ['monto_real', 'observaciones']
        widgets = {'observaciones': forms.Textarea(attrs={'rows': 3})}


class CobroForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = [
            'tipo_pago',
            'pedido',
            'cotizacion',
            'sucursal',
            'caja',
            'empleado',
            'monto',
            'monto_recibido',
            'metodo_pago',
            'observaciones',
        ]
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'fecha_pago': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get('monto')
        monto_recibido = cleaned_data.get('monto_recibido') or 0

        if monto is not None and monto_recibido and monto_recibido < monto:
            raise forms.ValidationError('El monto recibido es menor que el monto a cobrar.')

        return cleaned_data


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['pedido', 'monto', 'metodo_pago', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
