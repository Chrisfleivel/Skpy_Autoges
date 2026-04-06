# inventario/forms.py
from django import forms
from .models import Vehiculo, Repuesto, MantenimientoVehiculo, Deposito, UnidadMedida

class VehiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].initial = 'vehiculo'
        self.fields['tipo'].widget = forms.HiddenInput()
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Vehiculo
        exclude = ['nombre', 'fecha_ingreso']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_compra': forms.DateInput(attrs={'type': 'date'}),
        }

class RepuestoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].initial = 'repuesto'
        self.fields['tipo'].widget = forms.HiddenInput()
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Repuesto
        exclude = ['fecha_ultima_entrada']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class MantenimientoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = MantenimientoVehiculo
        exclude = ['fecha_registro']
        widgets = {
            'fecha_mantenimiento': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class DepositoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Deposito
        exclude = ['fecha_creacion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class UnidadMedidaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        # Campo nombre con placeholder
        self.fields['nombre'].widget.attrs.update({
            'placeholder': 'Ej: Unidad, Litro, Caja...',
            'maxlength': '50'
        })
        # Campo abreviatura con placeholder y conversión a mayúsculas
        self.fields['abreviatura'].widget.attrs.update({
            'placeholder': 'Ej: Und, Lt, Cja...',
            'maxlength': '10',
            'style': 'text-transform: uppercase;'
        })

    class Meta:
        model = UnidadMedida
        fields = '__all__'
