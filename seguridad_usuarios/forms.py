# seguridad_usuarios/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Rol, Permiso, Empleado, UsuarioPerfil

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
        return user

class UserUpdateForm(forms.ModelForm):
    """
    Formulario para editar un usuario existente.
    """
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class PasswordChangeForm(forms.Form):
    """
    Formulario para cambiar la contraseña del usuario.
    """
    old_password = forms.CharField(label='Contraseña actual', widget=forms.PasswordInput)
    new_password = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirmar nueva contraseña', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error("confirm_password", "Las contraseñas no coinciden.")

        return cleaned_data


class RolForm(forms.ModelForm):
    """
    Formulario para crear o editar roles.
    """

    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'permisos']
        widgets = {
            'permisos': forms.CheckboxSelectMultiple(),
        }


class PermisoForm(forms.ModelForm):
    """
    Formulario para crear o editar permisos.
    """
    class Meta:
        model = Permiso
        fields = ['nombre', 'descripcion']


class EmpleadoForm(forms.ModelForm):
    """
    Formulario para crear o editar un empleado.
    """

    class Meta:
        model = Empleado
        fields = ['nombre', 'apellidos', 'documento_identidad', 'ruc', 'telefono', 'email', 'direccion', 'cargo', 'descripcion_trabajo', 'departamento', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'required': 'required'}),
            'apellidos': forms.TextInput(attrs={'required': 'required'}),
            'documento_identidad': forms.TextInput(attrs={'required': 'required'}),
            'email': forms.EmailInput(attrs={'required': 'required'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_persona = cleaned_data.get('tipo_persona')
        nombre = cleaned_data.get('nombre')
        apellidos = cleaned_data.get('apellidos')
        documento_identidad = cleaned_data.get('documento_identidad')
        email = cleaned_data.get('email')
        
   
        if not nombre:
            self.add_error('nombre', 'El nombre es obligatorio')
        if not apellidos:
            self.add_error('apellidos', 'Los apellidos son obligatorios')
        if not documento_identidad:
                self.add_error('documento_identidad', 'El documento de identidad es obligatorio ')
        if not email:
                self.add_error('email', 'El correo electrónico es obligatorio')
        return cleaned_data

class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario, incluyendo la foto de perfil.
    """
    class Meta: 
        model = UsuarioPerfil
        fields = ['empleado', 'roles', 'foto_perfil']
        widgets = {
            'roles': forms.CheckboxSelectMultiple(),
        }
    def clean(self):
        cleaned_data = super().clean()
        roles = cleaned_data.get('roles')
        if not roles or roles.count() == 0:
            self.add_error('roles', 'Debe asignar al menos un rol al usuario.')
        return cleaned_data