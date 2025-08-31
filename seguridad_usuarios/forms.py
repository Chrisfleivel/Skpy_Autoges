# seguridad_usuarios/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Perfil

class UserRegisterForm(forms.ModelForm):
    """
    Formulario para registrar un nuevo usuario estándar de Django.
    """
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Crear el perfil con el teléfono
            Perfil.objects.create(user=user, telefono=self.cleaned_data.get('telefono', ''))
        return user

class PerfilForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario.
    """
    class Meta:
        model = Perfil
        fields = ('telefono',)