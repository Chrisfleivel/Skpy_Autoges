from django.forms import inlineformset_factory
# clientes_pedidos/forms.py
from django import forms
from .models import Cliente, Pedido, ItemPedido, Cotizacion


# Formulario para crear un Pedido
class PedidoCreateForm(forms.ModelForm):
	class Meta:
		model = Pedido
		fields = ['cliente', 'vendedor', 'estado', 'tipo', 'observaciones', 'monto_total', 'iva']

# Formulario para los ítems del pedido
class ItemPedidoForm(forms.ModelForm):
	class Meta:
		model = ItemPedido
		fields = ['vehiculo', 'repuesto', 'cantidad', 'precio_unitario']

# Formset para asociar varios ítems a un pedido
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

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear o editar un cliente.
    """
    class Meta:
        model = Cliente
        fields = ['tipo_persona', 'razon_social', 'nombre', 'apellidos', 'ruc', 'documento_identidad', 'telefono', 'email', 'direccion', 'estado', 'fecha_baja']
        widgets = {
            'fecha_registro': forms.DateInput(attrs={'type': 'date'}),
            'fecha_modificacion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_baja': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_persona = cleaned_data.get('tipo_persona')
        nombre = cleaned_data.get('nombre')
        razon_social = cleaned_data.get('razon_social')
        documento_identidad = cleaned_data.get('documento_identidad')

        if tipo_persona == 'FISICA':
            if not nombre:
                self.add_error('nombre', 'El nombre es obligatorio para persona física.')
            if not documento_identidad:
                self.add_error('documento_identidad', 'El documento de identidad es obligatorio para persona física.')
            cleaned_data['razon_social'] = None
        elif tipo_persona == 'JURIDICA':
            if not razon_social:
                self.add_error('razon_social', 'La razón social es obligatoria para persona jurídica.')
            cleaned_data['nombre'] = None
            cleaned_data['documento_identidad'] = None
        return cleaned_data



class PedidoForm(forms.ModelForm):
	class Meta:
		model = Pedido
		fields = ['cliente', 'vendedor', 'estado', 'tipo', 'observaciones', 'monto_total', 'iva']

class ItemPedidoForm(forms.ModelForm):
	class Meta:
		model = ItemPedido
		fields = ['pedido', 'vehiculo', 'repuesto', 'cantidad', 'precio_unitario']

class CotizacionForm(forms.ModelForm):
	class Meta:
		model = Cotizacion
		fields = ['pedido', 'estado', 'descripcion_solicitud', 'monto_estimado', 'fecha_validez']
