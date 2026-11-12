# inventario/forms.py
from django import forms
from django.forms import inlineformset_factory
from core.models import Moneda as MonedaFacade
from configuraciones_maestras.models import Moneda as MonedaCatalogo
from .models import (
    Vehiculo,
    VehiculoFoto,
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
    # Campos que la pantalla no muestra. Si no vienen en el POST se conserva
    # el valor actual (o el del modelo en un alta), así el formulario nunca
    # queda con un error de "campo obligatorio" invisible para el usuario.
    CAMPOS_OPCIONALES = (
        'stock_actual',
        'stock_minimo',
        'costo_unitario',
        'moneda_del_costo_unitario',
    )

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
        # Los modelos compatibles se eligen de una lista múltiple.
        self.fields['modelos_compatibles'].widget.attrs.update({
            'class': 'form-select', 'size': '6',
        })
        for field_name in self.CAMPOS_OPCIONALES:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def _conservar_si_vacio(self, field_name):
        """Devuelve el valor actual del modelo cuando el campo viene vacío."""
        valor = self.cleaned_data.get(field_name)
        if valor in (None, ''):
            return getattr(self.instance, field_name)
        return valor

    def clean_stock_actual(self):
        return self._conservar_si_vacio('stock_actual')

    def clean_stock_minimo(self):
        return self._conservar_si_vacio('stock_minimo')

    def clean_costo_unitario(self):
        return self._conservar_si_vacio('costo_unitario')

    def clean_moneda_del_costo_unitario(self):
        return self._conservar_si_vacio('moneda_del_costo_unitario')

    class Meta:
        model = Repuesto
        # `stock_reservado` es el espejo de StockRepuesto: lo maneja el
        # servicio de stock, no el usuario.
        exclude = ['fecha_ultima_entrada', 'stock_reservado']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'compatibilidad': forms.Textarea(attrs={'rows': 3}),
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

        # Los modelos compatibles se eligen de una lista múltiple.
        if 'modelos_compatibles' in self.fields:
            self.fields['modelos_compatibles'].widget.attrs.update({
                'class': 'form-select', 'size': '6',
            })

    class Meta:
        model = Repuesto
        fields = [
            'nombre', 'codigo_repuesto', 'proveedor', 'categoria', 'unidad_medida',
            'cantidad_a_comprar', 'costo_unitario_proveedor', 'moneda_compra_proveedor', 'moneda_venta',
            'compatibilidad', 'descripcion', 'imagen', 'tipo', 'estado', 'costo_compra',
            'fabricante', 'codigo_oem', 'modelos_compatibles',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'compatibilidad': forms.Textarea(attrs={'rows': 3}),
        }

class VehiculoFotoForm(forms.ModelForm):
    """Una foto de la galería del vehículo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El orden es opcional: si no se informa, la foto se guarda al final.
        self.fields['orden'].required = False
        # En las filas nuevas (las extra del formset) el "orden" no debe marcar
        # el formulario como modificado cuando la línea viene vacía: si no, la
        # fila en blanco se valida como error y el formset nunca es válido.
        if not self.instance.pk:
            self.initial['orden'] = None

    def clean_orden(self):
        valor = self.cleaned_data.get('orden')
        return 0 if valor is None else valor

    class Meta:
        model = VehiculoFoto
        fields = ['imagen', 'descripcion', 'orden']
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'descripcion': forms.TextInput(attrs={'placeholder': 'Ej.: frontal, lateral, interior'}),
            'orden': forms.NumberInput(attrs={'min': '0'}),
        }


VehiculoFotoFormSet = inlineformset_factory(
    Vehiculo,
    VehiculoFoto,
    form=VehiculoFotoForm,
    extra=1,
    can_delete=True,
)


class CategoriaRepuestoForm(forms.ModelForm):
    """
    Alta y edición de una categoría de repuestos.

    El nombre tiene que ser único **dentro del mismo nivel**: dos raíces no
    pueden llamarse igual, pero una subcategoría puede repetir el nombre de
    su padre. Tampoco se puede colgar de un descendiente (crearía un ciclo).
    """

    class Meta:
        model = CategoriaRepuesto
        fields = ['nombre', 'descripcion', 'padre', 'estado']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = CategoriaRepuesto.objects.filter(estado=True).order_by('nombre')
        if self.instance and self.instance.pk:
            # No se puede elegir la propia categoría ni una de sus descendientes.
            queryset = queryset.exclude(pk__in=self.instance.descendientes())
        self.fields['padre'].queryset = queryset
        self.fields['padre'].empty_label = 'Sin categoría superior (raíz)'
        self.fields['padre'].required = False
        self.fields['estado'].label = 'Activa'

        for field_name, field in self.fields.items():
            if field_name == 'estado':
                field.widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
            elif field_name == 'padre':
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            return nombre

        padre = self.cleaned_data.get('padre')
        if padre:
            repetidos = CategoriaRepuesto.objects.filter(
                nombre__iexact=nombre, padre=padre)
        else:
            repetidos = CategoriaRepuesto.objects.filter(
                nombre__iexact=nombre, padre__isnull=True)

        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)

        if repetidos.exists():
            nivel = f'"{padre.nombre}"' if padre else 'la raíz'
            raise forms.ValidationError(
                f'Ya existe una categoría con ese nombre en {nivel}.')
        return nombre

    def clean(self):
        cleaned = super().clean()
        padre = cleaned.get('padre')
        if padre and self.instance.pk:
            # El modelo valida esto en `CategoriaRepuesto.clean()`; acá se avisa
            # antes para que el error caiga en el campo correcto.
            if self.instance.pk in padre.ascendientes():
                self.add_error(
                    'padre',
                    'Una categoría no puede colgar de una de sus subcategorías.',
                )
        return cleaned


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


