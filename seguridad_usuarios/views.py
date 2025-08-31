# seguridad_usuarios/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Perfil
from .forms import UserRegisterForm, PerfilForm

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import logging
#from .decorators import requiere_privilegio

# Importa el modelo User de Django para manejar la autenticación
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# Configura el logger para registrar eventos de la aplicación
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Vistas para la gestión de Usuarios
# --------------------------------------------------------------------------

@login_required
def lista_usuarios(request):
    """
    Vista que muestra una lista de todos los usuarios registrados en el sistema.
    Requiere que el usuario esté autenticado.
    """
    usuarios = User.objects.all()  # Usar el modelo estándar User
    return render(request, 'seguridad_usuarios/lista_usuarios.html', {'usuarios': usuarios}) # Renderiza la plantilla HTML con la lista de usuarios

@login_required
def crear_usuario(request):
    """
    Vista para crear un nuevo usuario.
    Maneja la solicitud GET (mostrar formulario) y POST (enviar formulario).
    """
    try:
        if request.method == 'POST':
            # Si la solicitud es POST, crea una instancia del formulario con los datos enviados
            form = UserRegisterForm(request.POST)
            if form.is_valid():
                # Si el formulario es válido, guarda el nuevo usuario en la base de datos
                form.save()
                logger.info(f"Usuario {form.cleaned_data['username']} creado exitosamente.")
                messages.success(request, 'Usuario creado exitosamente.') # Envía un mensaje de éxito al usuario
                return redirect('lista_usuarios') # Redirecciona a la lista de usuarios
        else:
            # Si la solicitud es GET, crea una instancia de formulario vacía
            form = UserRegisterForm()
        return render(request, 'seguridad_usuarios/crear_usuario.html', {'form': form}) # Renderiza el formulario de creación
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}")
        messages.error(request, "Ocurrió un error al crear el usuario.")
        return redirect('lista_usuarios')

@login_required
def editar_usuario(request, pk):
    """
    Vista para editar un usuario existente.
    Recibe la clave primaria (pk) del usuario a editar.
    """
    try:
        usuario = get_object_or_404(User, pk=pk) # Busca el usuario por su PK o devuelve un error 404
        perfil = getattr(usuario, 'perfil', None)
        if request.method == 'POST':
            # Si la solicitud es POST, actualiza el formulario con los nuevos datos
            user_form = UserRegisterForm(request.POST, instance=usuario)
            perfil_form = PerfilForm(request.POST, instance=perfil)
            if user_form.is_valid() and perfil_form.is_valid():
                user_form.save()
                perfil_form.save()
                logger.info(f"Usuario {usuario.username} editado exitosamente.")
                messages.success(request, 'Usuario editado exitosamente.')
                return redirect('lista_usuarios')
        else:
            # Si la solicitud es GET, precarga el formulario con los datos del usuario
            user_form = UserRegisterForm(instance=usuario)
            perfil_form = PerfilForm(instance=perfil)
        return render(request, 'seguridad_usuarios/editar_usuario.html', {
            'form': user_form,
            'perfil_form': perfil_form,
            'usuario': usuario
        })
    except Exception as e:
        logger.error(f"Error al editar usuario con PK {pk}: {e}")
        messages.error(request, "Ocurrió un error al editar el usuario.")
        return redirect('lista_usuarios')

@login_required
def eliminar_usuario(request, pk):
    """
    Vista para eliminar un usuario.
    Recibe la clave primaria (pk) del usuario a eliminar.
    """
    try:
        usuario = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            usuario.delete() # Elimina el objeto de la base de datos
            logger.info(f"Usuario {usuario.username} eliminado exitosamente.")
            messages.success(request, 'Usuario eliminado exitosamente.')
            return redirect('lista_usuarios')
        return render(request, 'seguridad_usuarios/eliminar_usuario.html', {'usuario': usuario})
    except Exception as e:
        logger.error(f"Error al eliminar usuario con PK {pk}: {e}")
        messages.error(request, "Ocurrió un error al eliminar el usuario.")
        return redirect('lista_usuarios')


# --------------------------------------------------------------------------
# Vista de Login
# --------------------------------------------------------------------------

def login_view(request):
    """
    Vista que maneja la autenticación de usuarios.
    Maneja el envío del formulario de login y la validación de credenciales.
    """
    try:
        if request.method == 'POST':
            # Obtiene el usuario y la contraseña del formulario
            username = request.POST['username']
            password = request.POST['password']
            
            # Autentica las credenciales del usuario
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Si las credenciales son válidas, inicia sesión y redirecciona al inicio
                login(request, user)
                return redirect('home') # 'home' sería la página principal de la aplicación
            else:
                # Si las credenciales son inválidas, muestra un mensaje de error
                messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
        
        # Muestra el formulario de login en la página
        return render(request, 'seguridad_usuarios/login.html')
    except Exception as e:
        logger.error(f"Error en login: {e}")
        messages.error(request, "Ocurrió un error en el inicio de sesión.")
        return render(request, 'seguridad_usuarios/login.html')

# --------------------------------------------------------------------------
# Vista de Logout
# --------------------------------------------------------------------------

@login_required
def logout_view(request):
    """
    Vista que cierra la sesión del usuario actual.
    """
    try:
        logout(request) # Llama a la función de logout de Django
        return redirect('login') # Redirecciona al usuario a la página de login
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        messages.error(request, "Ocurrió un error al cerrar sesión.")
        return redirect('login')
    
# --------------------------------------------------------------------------
# Vista de Registro de Usuario
# --------------------------------------------------------------------------

def registro_view(request):
    """
    Vista que permite a los nuevos usuarios registrarse en el sistema.
    """
    try:
        if request.method == 'POST':
            form = UserRegisterForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Usuario registrado correctamente.')
                return redirect('login')
        else:
            form = UserRegisterForm()
        return render(request, 'seguridad_usuarios/registro.html', {'form': form})
    except Exception as e:
        logger.error(f"Error en registro de usuario: {e}")
        print(e)
        messages.error(request, "Ocurrió un error al registrar el usuario.")
        return redirect('login')
    


# --------------------------------------------------------------------------
# Señal para crear perfil automáticamente
# --------------------------------------------------------------------------

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)



# --------------------------------------------------------------------------
# Otras vistas relacionadas con la seguridad y gestión de usuarios pueden añadirse aquí     
# --------------------------------------------------------------------------

#  ...otras vistas para restablecer contraseñas, gestionar perfiles, etc.

# registrarse con google
# https://django-allauth.readthedocs.io/en/latest/installation.html