# seguridad_usuarios/forms.py

from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import Rol, Permiso, Empleado, UsuarioPerfil, ContactoEmpleado

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
    old_password = forms.CharField(label='Contraseña actual', widget=forms.PasswordInput) # , attrs={'required': 'required', 'class': 'form-control'}
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
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Administrador'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Breve descripción del rol...'}),
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
        fields = ['tipo_persona', 'nombre', 'apellidos', 'documento_identidad', 'ruc', 'email', 'departamento', 'cargo', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'required': 'required','class': 'form-control', 'placeholder': 'Ej: Jose Luis'}),
            'apellidos': forms.TextInput(attrs={'required': 'required', 'class': 'form-control', 'placeholder': 'Ej: Perez Gomez'}),
            'documento_identidad': forms.TextInput(attrs={'required': 'required', 'class': 'form-control', 'placeholder': 'Ej: 12345678'}),
            'email': forms.EmailInput(attrs={'required': 'required', 'class': 'form-control', 'placeholder': 'Ej: jose@example.com'}),
            'departamento': forms.Select(attrs={'id': 'id_departamento', 'class': 'form-control'}),
            'cargo': forms.Select(attrs={'id': 'id_cargo', 'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1234567-7'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_persona = cleaned_data.get('tipo_persona')
        nombre = cleaned_data.get('nombre')
        apellidos = cleaned_data.get('apellidos')
        documento_identidad = cleaned_data.get('documento_identidad')
        ruc = cleaned_data.get('ruc')
        email = cleaned_data.get('email')
        
   
        if tipo_persona == 'FISICA':
            if not nombre:
                self.add_error('nombre', 'El nombre es obligatorio para persona física')
            if not documento_identidad:
                self.add_error('documento_identidad', 'El documento de identidad es obligatorio para persona física')
        
        if tipo_persona == 'JURIDICA':
            if not ruc:
                self.add_error('ruc', 'El RUC es obligatorio para persona jurídica')

        if not nombre and tipo_persona != 'JURIDICA':
            self.add_error('nombre', 'El nombre es obligatorio')
        if not apellidos:
            self.add_error('apellidos', 'Los apellidos son obligatorios')
        if not documento_identidad:
                self.add_error('documento_identidad', 'El documento de identidad es obligatorio ')
        if not email:
                self.add_error('email', 'El correo electrónico es obligatorio')
        # Validaciones de unicidad para documento_identidad y ruc
        qs = Empleado.objects.all()
        if self.instance and getattr(self.instance, 'pk', None):
            qs = qs.exclude(pk=self.instance.pk)

        if documento_identidad:
            if qs.filter(documento_identidad=documento_identidad).exists():
                self.add_error('documento_identidad', 'El documento de identidad ya está registrado para otro empleado.')

        if ruc:
            if qs.filter(ruc=ruc).exists():
                self.add_error('ruc', 'El RUC ya está registrado para otro empleado.')

        return cleaned_data

class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario, incluyendo la foto de perfil.
    """
    class Meta:
        model = UsuarioPerfil
        fields = ['empleado', 'foto_perfil', 'tema']
        widgets = {
            'tema': forms.Select(attrs={'class': 'form-select'}),
        }


class ContactoEmpleadoForm(forms.ModelForm):
    class Meta:
        model = ContactoEmpleado
        fields = ['categoria', 'tipo_persona', 'nombre', 'apellidos', 'telefono', 'direccion', 'email']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del contacto'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del contacto'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': field.widget.attrs.get('class', '') + ' form-control'
                })


ContactoEmpleadoFormSet = inlineformset_factory(
    Empleado,
    ContactoEmpleado,
    form=ContactoEmpleadoForm,
    extra=1,
    can_delete=True,
)
