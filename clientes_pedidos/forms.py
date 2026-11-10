from django.forms import inlineformset_factory
# clientes_pedidos/forms.py
from django import forms
from configuraciones_maestras.models import Moneda, Proveedor
from .models import Cliente, ContactoCliente, Pedido, ItemPedido, Cotizacion, Carrito, ProductoBuscado, SeleccionProductoBuscado


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{css} form-control'.strip()


class PedidoCreateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'observaciones', 'monto_total', 'iva', 'moneda']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'monto_total': forms.NumberInput(attrs={'step': '0.01'}),
            'iva': forms.NumberInput(attrs={'step': '0.01'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].required = False
        self.fields['cliente'].widget = forms.HiddenInput()
        self.fields['monto_total'].required = False
        self.fields['iva'].required = False
        self.fields['monto_total'].initial = 0
        self.fields['iva'].initial = 0
        self.fields['moneda'].queryset = Moneda.objects.only('id', 'codigo', 'nombre')
        self.fields['moneda'].required = False

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['monto_total'] = cleaned_data.get('monto_total') or 0
        cleaned_data['iva'] = cleaned_data.get('iva') or 0
        return cleaned_data


class ItemPedidoForm(BootstrapFormMixin, forms.ModelForm):
    tipo_producto = forms.ChoiceField(
        choices=[('vehiculo', 'Vehículo'), ('repuesto', 'Repuesto')],
        initial='vehiculo',
        required=True,
        label='Tipo de Ítem',
        widget=forms.Select(attrs={'class': 'form-select tipo-item-select'})
    )

    class Meta:
        model = ItemPedido
        fields = ['tipo_producto', 'vehiculo', 'repuesto', 'cantidad', 'precio_unitario', 'moneda']
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'repuesto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'step': '1', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.pedido_tipo = kwargs.pop('pedido_tipo', None)
        super().__init__(*args, **kwargs)
        from inventario.models import Vehiculo, Repuesto

        vehiculos_qs = Vehiculo.objects.select_related('modelo').only('id', 'nombre', 'modelo')
        repuestos_qs = Repuesto.objects.only('id', 'nombre', 'codigo_repuesto')
        if self.pedido_tipo in {'busqueda', 'abastecimiento'}:
            vehiculos_qs = vehiculos_qs.filter(estado='elegible_importacion')
            repuestos_qs = repuestos_qs.filter(estado='elegible_importacion')
        elif self.pedido_tipo == 'venta':
            vehiculos_qs = vehiculos_qs.filter(estado='disponible')
            repuestos_qs = repuestos_qs.filter(estado='disponible')

        self.fields['vehiculo'].queryset = vehiculos_qs
        self.fields['repuesto'].queryset = repuestos_qs
        self.fields['moneda'].queryset = Moneda.objects.only('id', 'codigo', 'nombre')
        self.fields['vehiculo'].required = False
        self.fields['repuesto'].required = False
        self.fields['moneda'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_producto = (cleaned_data.get('tipo_producto') or '').strip()
        vehiculo = cleaned_data.get('vehiculo')
        repuesto = cleaned_data.get('repuesto')

        if not tipo_producto and not vehiculo and not repuesto:
            cleaned_data['tipo_producto'] = None
            cleaned_data['vehiculo'] = None
            cleaned_data['repuesto'] = None
            return cleaned_data

        if not tipo_producto:
            if vehiculo and not repuesto:
                tipo_producto = 'vehiculo'
            elif repuesto and not vehiculo:
                tipo_producto = 'repuesto'

        if tipo_producto == 'vehiculo' and repuesto and not vehiculo:
            tipo_producto = 'repuesto'

        if tipo_producto == 'repuesto' and vehiculo and not repuesto:
            tipo_producto = 'vehiculo'

        if tipo_producto == 'vehiculo':
            cleaned_data['repuesto'] = None
            cleaned_data['tipo_producto'] = 'vehiculo'
            if not vehiculo:
                self.add_error('vehiculo', 'Debe seleccionar un vehículo.')
            elif self.pedido_tipo in {'busqueda', 'abastecimiento'} and getattr(vehiculo, 'estado', None) != 'elegible_importacion':
                self.add_error('vehiculo', 'El vehículo debe estar elegible para importación para este pedido.')
            elif self.pedido_tipo == 'venta' and getattr(vehiculo, 'estado', None) != 'disponible':
                self.add_error('vehiculo', 'El vehículo debe estar disponible para este pedido de venta.')
        elif tipo_producto == 'repuesto':
            cleaned_data['vehiculo'] = None
            cleaned_data['tipo_producto'] = 'repuesto'
            if not repuesto:
                self.add_error('repuesto', 'Debe seleccionar un repuesto.')
            elif self.pedido_tipo in {'busqueda', 'abastecimiento'} and getattr(repuesto, 'estado', None) != 'elegible_importacion':
                self.add_error('repuesto', 'El repuesto debe estar elegible para importación para este pedido.')
            elif self.pedido_tipo == 'venta' and getattr(repuesto, 'estado', None) != 'disponible':
                self.add_error('repuesto', 'El repuesto debe estar disponible para este pedido de venta.')
        else:
            self.add_error(None, 'Tipo de producto inválido.')

        return cleaned_data


ItemPedidoFormSet = inlineformset_factory(
    Pedido,
    ItemPedido,
    form=ItemPedidoForm,
    extra=0,
    can_delete=True
)


class ClienteForm2(forms.ModelForm):
    class Meta:
        model = Cliente
        exclude = ['pedidos', 'compras_realizadas', 'total_gastado']


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulario para crear o editar un cliente.
    """
    class Meta:
        model = Cliente
        fields = ['tipo_persona', 'razon_social', 'nombre', 'apellidos', 'ruc', 'documento_identidad', 'email', 'estado', 'fecha_baja']
        widgets = {
            'fecha_baja': forms.DateInput(attrs={'type': 'date'}),
            'tipo_persona': forms.Select(),
            'razon_social': forms.TextInput(),
            'nombre': forms.TextInput(),
            'apellidos': forms.TextInput(),
            'documento_identidad': forms.TextInput(),
            'ruc': forms.TextInput(),
            'email': forms.EmailInput(),
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
            cleaned_data['documento_identidad'] = None
        # Validaciones de unicidad: cédula y RUC deben ser únicos entre clientes
        qs = Cliente.objects.all()
        if self.instance and getattr(self.instance, 'pk', None):
            qs = qs.exclude(pk=self.instance.pk)

        if documento_identidad:
            if qs.filter(documento_identidad=documento_identidad).exists():
                self.add_error('documento_identidad', 'La cédula ya está registrada para otro cliente.')

        if ruc:
            if qs.filter(ruc=ruc).exists():
                self.add_error('ruc', 'El RUC ya está registrado para otro cliente.')

        return cleaned_data


class ContactoClienteForm(forms.ModelForm):
    class Meta:
        model = ContactoCliente
        fields = ['tipo_persona', 'nombre', 'apellidos', 'telefono', 'email', 'direccion']
        widgets = {
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del contacto'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del contacto'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección del contacto'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': field.widget.attrs.get('class', '') + ' form-control'
                })


ContactoClienteFormSet = inlineformset_factory(
    Cliente,
    ContactoCliente,
    form=ContactoClienteForm,
    extra=1,
    can_delete=True,
)


class PedidoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'vendedor', 'estado', 'tipo', 'observaciones', 'monto_total', 'iva', 'moneda']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'monto_total': forms.NumberInput(attrs={'step': '0.01'}),
            'iva': forms.NumberInput(attrs={'step': '0.01'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['moneda'].queryset = Moneda.objects.only('id', 'codigo', 'nombre')
        self.fields['moneda'].required = False


class FacturaPedidoForm(BootstrapFormMixin, forms.Form):
    proveedor = forms.ModelChoiceField(queryset=Proveedor.objects.all(), required=False, label='Proveedor')
    numero_factura = forms.CharField(max_length=100, required=False, label='Número de factura')
    fecha_factura = forms.DateField(required=False, label='Fecha de factura', widget=forms.DateInput(attrs={'type': 'date'}))
    factura_pdf = forms.FileField(required=False, label='Factura PDF')
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones'}), label='Observaciones')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('numero_factura') and not cleaned_data.get('factura_pdf'):
            raise forms.ValidationError('Ingresa el número de factura o sube un archivo PDF.')
        return cleaned_data


class CotizacionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['pedido', 'estado', 'descripcion_solicitud', 'monto_estimado', 'fecha_validez']
        widgets = {
            'descripcion_solicitud': forms.Textarea(attrs={'rows': 3}),
            'monto_estimado': forms.NumberInput(attrs={'step': '0.01'}),
            'fecha_validez': forms.DateInput(attrs={'type': 'date'}),
        }


class CarritoForm(forms.ModelForm):
    class Meta:
        model = Carrito
        fields = ['cliente', 'vehiculos', 'repuestos']
        widgets = {
            'cliente': forms.HiddenInput(),
        }
        

# --------------------------------------------------------------------------
# Formularios para ProductoBuscado y SeleccionProductoBuscado
# --------------------------------------------------------------------------

class ProductoBuscadoForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulario para crear productos buscados en un pedido de búsqueda.
    """
    tipo_producto = forms.ChoiceField(
        choices=[('vehiculo', 'Vehículo'), ('repuesto', 'Repuesto')],
        initial='vehiculo',
        required=True,
        label='Tipo de Producto',
        widget=forms.Select(attrs={'class': 'form-select tipo-item-select'})
    )

    class Meta:
        model = ProductoBuscado
        fields = ['descripcion', 'tipo_producto', 'vehiculo', 'repuesto', 'cantidad', 'marca', 'modelo', 'especificaciones']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción del producto buscado'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-select'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'repuesto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'min': '1', 'value': '1'}),
            'marca': forms.TextInput(attrs={'placeholder': 'Ej. Toyota, Honda'}),
            'modelo': forms.TextInput(attrs={'placeholder': 'Ej. Corolla, Civic'}),
            'especificaciones': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Especificaciones adicionales'}),
        }

    def __init__(self, *args, **kwargs):
        self.pedido_tipo = kwargs.pop('pedido_tipo', None)
        super().__init__(*args, **kwargs)
        from inventario.models import Vehiculo, Repuesto

        vehiculos_qs = Vehiculo.objects.select_related('modelo').only('id', 'nombre', 'modelo')
        repuestos_qs = Repuesto.objects.only('id', 'nombre', 'codigo_repuesto')
        if self.pedido_tipo in {'busqueda', 'abastecimiento'}:
            vehiculos_qs = vehiculos_qs.filter(estado='elegible_importacion')
            repuestos_qs = repuestos_qs.filter(estado='elegible_importacion')
        elif self.pedido_tipo == 'venta':
            vehiculos_qs = vehiculos_qs.filter(estado='disponible')
            repuestos_qs = repuestos_qs.filter(estado='disponible')

        self.fields['vehiculo'].queryset = vehiculos_qs
        self.fields['repuesto'].queryset = repuestos_qs
        self.fields['vehiculo'].required = False
        self.fields['repuesto'].required = False
        self.fields['tipo_producto'].required = True

    def clean(self):
        cleaned_data = super().clean()
        tipo_producto = (cleaned_data.get('tipo_producto') or '').strip()
        vehiculo = cleaned_data.get('vehiculo')
        repuesto = cleaned_data.get('repuesto')

        if not tipo_producto:
            if vehiculo and not repuesto:
                tipo_producto = 'vehiculo'
            elif repuesto and not vehiculo:
                tipo_producto = 'repuesto'

        if tipo_producto == 'vehiculo':
            cleaned_data['repuesto'] = None
            if vehiculo and self.pedido_tipo in {'busqueda', 'abastecimiento'} and getattr(vehiculo, 'estado', None) != 'elegible_importacion':
                self.add_error('vehiculo', 'El vehículo debe estar elegible para importación para este pedido.')
        elif tipo_producto == 'repuesto':
            cleaned_data['vehiculo'] = None
            if repuesto and self.pedido_tipo in {'busqueda', 'abastecimiento'} and getattr(repuesto, 'estado', None) != 'elegible_importacion':
                self.add_error('repuesto', 'El repuesto debe estar elegible para importación para este pedido.')

        cleaned_data['tipo_producto'] = tipo_producto or 'vehiculo'
        return cleaned_data


ProductoBuscadoFormSet = inlineformset_factory(
    Pedido,
    ProductoBuscado,
    form=ProductoBuscadoForm,
    extra=1,
    can_delete=True
)


class SeleccionProductoBuscadoForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulario para que el encargado de selección confirme el producto y establezca el precio.
    """
    class Meta:
        model = SeleccionProductoBuscado
        fields = ['repuesto', 'precio_unitario', 'observaciones']
        widgets = {
            'repuesto': forms.Select(attrs={'class': 'form-select'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Precio unitario'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Observaciones sobre la selección'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from inventario.models import Repuesto
        self.fields['repuesto'].queryset = Repuesto.objects.only('id', 'nombre', 'codigo_repuesto')
        self.fields['repuesto'].required = True
        self.fields['precio_unitario'].required = True

