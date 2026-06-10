# inventario/forms.py
from django import forms
from .models import Vehiculo, Repuesto, MantenimientoVehiculo, Deposito, UnidadMedida, MarcaVehiculo, ModeloVehiculo, TipoVehiculo, TipoTransmision


class MarcaVehiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'estado':
                # Checkbox con clase custom
                field.widget = forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                })
                field.label = 'Estado Activo'
            else:
                field.widget.attrs.update({'class': 'form-control'})
        # Valor inicial para estado
        if 'estado' in self.fields:
            self.fields['estado'].initial = True

    class Meta:
        model = MarcaVehiculo
        fields = '__all__'

class ModeloVehiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'estado':
                # Checkbox con clase custom
                field.widget = forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                })
                field.label = 'Estado Activo'
            else:
                field.widget.attrs.update({'class': 'form-control'})
        # Valor inicial para estado
        if 'estado' in self.fields:
            self.fields['estado'].initial = True

    class Meta:
        model = ModeloVehiculo
        fields = '__all__'

class TipoVehiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'estado':
                # Checkbox con clase custom
                field.widget = forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                })
                field.label = 'Estado Activo'
            else:
                field.widget.attrs.update({'class': 'form-control'})
        # Valor inicial para estado
        if 'estado' in self.fields:
            self.fields['estado'].initial = True

    class Meta:
        model = TipoVehiculo
        fields = '__all__'

class TipoTransmisionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'estado':
                # Checkbox con clase custom
                field.widget = forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                })
                field.label = 'Estado Activo'
            else:
                field.widget.attrs.update({'class': 'form-control'})
        # Valor inicial para estado
        if 'estado' in self.fields:
            self.fields['estado'].initial = True

    class Meta:
        model = TipoTransmision
        fields = '__all__'

class VehiculoForm(forms.ModelForm):
    nuevo_modelo = forms.CharField(
        required=False, 
        label='Nuevo Modelo (opcional)', 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Escribe para crear un nuevo modelo si no existe'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ocultar el campo tipo
        self.fields['tipo'].widget = forms.HiddenInput()
        self.fields['tipo'].required = False
        self.fields['tipo'].initial = 'vehiculo'
        # Valor por defecto para estado
        if 'estado' in self.fields:
            self.fields['estado'].initial = 'disponible'
            self.fields['estado'].required = False
        # Aplicar form-control a todos excepto el hidden
        for field_name, field in self.fields.items():
            if field_name != 'tipo' and field.widget.__class__ != forms.HiddenInput:
                field.widget.attrs.update({'class': 'form-control'})
        # Color picker especial
        if 'color' in self.fields:
            self.fields['color'].widget = forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'style': 'height: 3rem; width: 100%; padding: .375rem .75rem;'
            })

    class Meta:
        model = Vehiculo
        exclude = ['nombre', 'fecha_ingreso', 'costo_compra', 'precio_venta']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_compra': forms.DateInput(attrs={'type': 'date'}),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'style': 'height: 3.2rem; width: 100%; padding: .375rem .75rem;'
            }),
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


