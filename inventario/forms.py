# inventario/forms.py
from django import forms
from django.forms import inlineformset_factory
from core.models import Moneda as MonedaFacade
from configuraciones_maestras.models import Moneda as MonedaCatalogo
from .models import (
    Vehiculo,
    Repuesto,
    MantenimientoVehiculo,
    MantenimientoRepuesto,
    Deposito,
    UnidadMedida,
    MarcaVehiculo,
    ModeloVehiculo,
    TipoVehiculo,
    TipoTransmision,
    CategoriaRepuesto,
)


def _aplicar_moneda_choices(form, *field_names):
    MonedaFacade.ensure_defaults()
    queryset = MonedaCatalogo.objects.order_by('codigo')
    for field_name in field_names:
        if field_name in form.fields:
            field = form.fields[field_name]
            field.queryset = queryset
            field.empty_label = 'Seleccione una moneda'
            field.widget.attrs.update({'class': 'form-select'})


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
        _aplicar_moneda_choices(self, 'moneda_venta')
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
        self.fields['estado'].initial = 'elegible_importacion'
        self.fields['estado'].widget = forms.HiddenInput()
        self.fields['estado'].required = False
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        _aplicar_moneda_choices(self, 'moneda_venta')

    class Meta:
        model = Repuesto
        exclude = ['fecha_ultima_entrada']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class RepuestoProveedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].initial = 'repuesto'
        self.fields['tipo'].widget = forms.HiddenInput()
        self.fields['estado'].initial = 'elegible_importacion'
        self.fields['estado'].widget = forms.HiddenInput()
        self.fields['estado'].required = False
        self.fields['costo_compra'].initial = 0
        self.fields['costo_compra'].required = False
        self.fields['costo_compra'].widget = forms.HiddenInput()
        self.fields['costo_unitario_proveedor'].initial = 0
        self.fields['cantidad_a_comprar'].initial = 1

        self.fields['categoria'].queryset = CategoriaRepuesto.objects.filter(estado=True).order_by('nombre')
        self.fields['categoria'].empty_label = 'Seleccione una categoría'

        _aplicar_moneda_choices(self, 'moneda_compra_proveedor', 'moneda_venta')
        self.fields['unidad_medida'].widget.attrs.update({'class': 'form-select'})

        for field_name, field in self.fields.items():
            if field.widget.__class__ != forms.HiddenInput and field_name not in ['moneda_compra_proveedor', 'unidad_medida', 'moneda_venta']:
                field.widget.attrs.update({'class': 'form-control'})

        if 'imagen' in self.fields:
            self.fields['imagen'].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Repuesto
        fields = [
            'nombre', 'codigo_repuesto', 'proveedor', 'categoria', 'unidad_medida',
            'cantidad_a_comprar', 'costo_unitario_proveedor', 'moneda_compra_proveedor', 'moneda_venta',
            'compatibilidad', 'descripcion', 'imagen', 'tipo', 'estado', 'costo_compra'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'compatibilidad': forms.Textarea(attrs={'rows': 3}),
        }

class MantenimientoForm(forms.ModelForm):
    """
    Datos del mantenimiento.

    El estado no se edita: se cambia con las transiciones (`EstadoMixin`).
    El costo total se calcula solo (mano de obra + repuestos).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['deposito'].empty_label = 'Depósito principal'

    class Meta:
        model = MantenimientoVehiculo
        exclude = [
            'fecha_registro',
            'estado',
            'stock_descontado',
            'costo',
            'repuestos_utilizados',
        ]
        widgets = {
            'fecha_mantenimiento': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'costo_mano_obra': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class MantenimientoRepuestoForm(forms.ModelForm):
    """Línea de repuesto utilizado en un mantenimiento."""

    class Meta:
        model = MantenimientoRepuesto
        fields = ['repuesto', 'cantidad', 'costo_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': '1'}),
            'costo_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


MantenimientoRepuestoFormSet = inlineformset_factory(
    MantenimientoVehiculo,
    MantenimientoRepuesto,
    form=MantenimientoRepuestoForm,
    extra=1,
    can_delete=True,
)

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


