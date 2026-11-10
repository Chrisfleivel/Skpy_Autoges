# contabilidad/forms.py
from django import forms
from .models import AsientoContable, DetalleAsiento

class AsientoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Verificar si el asiento es antiguo
        if self.instance.pk and self.instance.es_bloqueado():
            for field in self.fields.values():
                field.disabled = True # Deshabilita todos los campos