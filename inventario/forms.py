# inventario/forms.py
from django import forms
from .models import Vehiculo, Repuesto, MantenimientoVehiculo, Deposito, UnidadMedida


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = '__all__'

class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = '__all__'

class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = MantenimientoVehiculo
        fields = '__all__'

class DepositoForm(forms.ModelForm):
    class Meta:
        model = Deposito
        fields = '__all__'

class UnidadMedidaForm(forms.Form):
    class Meta:
        model = UnidadMedida
        fields = '__all__'
