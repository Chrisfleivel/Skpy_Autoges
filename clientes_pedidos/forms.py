from django.forms import inlineformset_factory
# clientes_pedidos/forms.py
from django import forms
from .models import Cliente, Pedido, ItemPedido, Cotizacion, Carrito


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{css} form-control'.strip()


class PedidoCreateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'observaciones', 'monto_total', 'iva']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'monto_total': forms.NumberInput(attrs={'step': '0.01'}),
            'iva': forms.NumberInput(attrs={'step': '0.01'}),
        }


class ItemPedidoForm(BootstrapFormMixin, forms.ModelForm):
    tipo_item = forms.ChoiceField(
        choices=[('vehiculo', 'Vehículo'), ('repuesto', 'Repuesto')],
        required=True,
        label='Tipo de Ítem',
        widget=forms.Select()
    )

    class Meta:
        model = ItemPedido
        fields = ['pedido', 'tipo_item', 'vehiculo', 'repuesto', 'cantidad', 'precio_unitario']
        widgets = {
            'pedido': forms.HiddenInput(),
            'vehiculo': forms.Select(),
            'repuesto': forms.Select(),
            'cantidad': forms.NumberInput(attrs={'step': '1', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


ItemPedidoFormSet = inlineformset_factory(
    Pedido,
    ItemPedido,
    form=ItemPedidoForm,
    extra=1,
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
        fields = ['tipo_persona', 'razon_social', 'nombre', 'apellidos', 'ruc', 'documento_identidad', 'telefono', 'email', 'direccion', 'estado', 'fecha_baja']
        widgets = {
            'fecha_baja': forms.DateInput(attrs={'type': 'date'}),
            'tipo_persona': forms.Select(),
            'razon_social': forms.TextInput(),
            'nombre': forms.TextInput(),
            'apellidos': forms.TextInput(),
            'documento_identidad': forms.TextInput(),
            'ruc': forms.TextInput(),
            'telefono': forms.TextInput(),
            'email': forms.EmailInput(),
            'direccion': forms.Textarea(attrs={'rows': 3}),
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
        return cleaned_data


class PedidoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'vendedor', 'estado', 'tipo', 'observaciones', 'monto_total', 'iva']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'monto_total': forms.NumberInput(attrs={'step': '0.01'}),
            'iva': forms.NumberInput(attrs={'step': '0.01'}),
        }


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



