# seguridad_usuarios/views.py

from django.shortcuts import render, get_object_or_404, redirect, redirect
from django.contrib.auth.decorators import login_required
from .models import Rol, Permiso, Auditoria, Empleado, UsuarioPerfil
from .forms import UserRegisterForm, PermisoForm, RolForm, PermisoForm, PasswordChangeForm, EmpleadoForm, PerfilUsuarioForm
# User
from django.contrib.auth.models import User
from .decorators import revisar_permiso

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import logging
#from .decorators import requiere_privilegio

# Importa el modelo User de Django para manejar la autenticación
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
email= 'christianfleitas97@gmail.com' # Correo electrónico del remitente



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
def cambiar_contrasena(request):
    """
    Vista para cambiar la contraseña del usuario.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            # Lógica para cambiar la contraseña
            print("Contraseña cambiada")
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('login')
    else:
        print("get")
        form = PasswordChangeForm()

    return render(request, 'seguridad_usuarios/cambiar_contrasena.html', {'form': form})

@login_required
def editar_usuario(request, pk):
    """
    Vista para editar un usuario existente.
    Recibe la clave primaria (pk) del usuario a editar.
    """
    try:
        usuario = get_object_or_404(User, pk=pk) # Busca el usuario por su PK o devuelve un error 404
        if request.method == 'POST':
            # Si la solicitud es POST, actualiza el formulario con los nuevos datos
            user_form = UserRegisterForm(request.POST, instance=usuario)
            if user_form.is_valid():
                user_form.save()
                logger.info(f"Usuario {usuario.username} editado exitosamente.")
                messages.success(request, 'Usuario editado exitosamente.')
                return redirect('lista_usuarios')
        else:
            # Si la solicitud es GET, precarga el formulario con los datos del usuario
            user_form = UserRegisterForm(instance=usuario)
        return render(request, 'seguridad_usuarios/editar_usuario.html', {
            'form': user_form,
            'usuario': usuario
        })
    except Exception as e:
        logger.error(f"Error al editar usuario con PK {pk}: {e}")
        messages.error(request, "Ocurrió un error al editar el usuario.")
        return redirect('lista_usuarios')

@revisar_permiso('seguridad_usuarios.eliminar_usuario')
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
                perfil_usuario = getattr(user, 'perfil', None)
                if perfil_usuario and perfil_usuario.debe_cambiar_contrasena:
                    login(request, user)
                    messages.warning(request, "Debes cambiar tu contraseña antes de continuar.")
                    return redirect('cambiar_contrasena')
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

# En la vista de cambio de contraseña, después de cambiarla:
@login_required
def cambiar_contrasena(request):
    """
    Vista para cambiar la contraseña del usuario.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            # Si el usuario es empleado, marca que ya no debe cambiar la contraseña
            empleado = getattr(request.user, 'empleado', None)
            if empleado:
                empleado.debe_cambiar_contrasena = False
                empleado.save()
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('login')
    else:
        form = PasswordChangeForm()
    return render(request, 'seguridad_usuarios/cambiar_contrasena.html', {'form': form})

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
@revisar_permiso('seguridad_usuarios.registrar_usuario')
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
# Otras vistas relacionadas con la seguridad y gestión de usuarios pueden añadirse aquí     
# --------------------------------------------------------------------------

#  ...otras vistas para restablecer contraseñas, gestionar perfiles, etc.
@login_required
def enviar_correo_confirmacion(usuario):
    """
    Envía un correo de confirmación al usuario después de registrarse.
    """
    subject = 'Confirmación de registro'
    message = f'Hola {usuario.username}, gracias por registrarte.'
    from_email = 'noreply@tuapp.com'
    recipient_list = [usuario.email]
    send_mail(subject, message, from_email, recipient_list)
    logger.info(f"Correo de confirmación enviado a {usuario.email}")


# Nota: Para funcionalidades avanzadas de autenticación y registro, considera usar paquetes como django-allauth
# https://django-allauth.readthedocs.io/en/latest/installation.html


# --------------------------------------------------------------------------
# Vista de Empleados
# --------------------------------------------------------------------------

@revisar_permiso('seguridad_usuarios.listar_empleados')
def lista_empleados(request):
    """
    Vista para listar todos los empleados con buscador y filtros.
    """
    empleados = Empleado.objects.all()
    # Filtros por nombre, apellido, departamento, email, estado y tiene_usuario
    nombre = request.GET.get('nombre')
    apellido = request.GET.get('apellido')
    departamento = request.GET.get('departamento')
    email = request.GET.get('email')
    estado = request.GET.get('estado')
    tiene_usuario = request.GET.get('tiene_usuario')

    if nombre:
        empleados = empleados.filter(nombre__icontains=nombre)
    if apellido:
        empleados = empleados.filter(apellidos__icontains=apellido)
    if departamento:
        empleados = empleados.filter(departamento__icontains=departamento)
    if email:
        empleados = empleados.filter(email__icontains=email)
    if estado in ['True', 'False']:
        empleados = empleados.filter(estado=(estado == 'True'))
    if tiene_usuario in ['True', 'False']:
        empleados = empleados.filter(tiene_usuario=(tiene_usuario == 'True'))

    return render(request, 'seguridad_usuarios/lista_empleados.html', {
        'empleados': empleados,
        'nombre': nombre or '',
        'apellido': apellido or '',
        'departamento': departamento or '',
        'email': email or '',
        'estado': estado or '',
        'tiene_usuario': tiene_usuario or '',
    })

@revisar_permiso('seguridad_usuarios.agregar_empleado')
def agregar_empleado(request):
    """
    Vista para agregar un nuevo empleado.
    redirige al detalle del empleado al crearlo.
    """
    try:
        if request.method == 'POST':
            form = EmpleadoForm(request.POST)
            if form.is_valid():
                empleado = form.save()  
                messages.success(request, 'Empleado agregado correctamente.')
                return redirect('detalle_empleado', pk=empleado.id)
        else:
            form = EmpleadoForm()
        return render(request, 'seguridad_usuarios/agregar_empleado.html', {'form': form})
    except Exception as e:
        logger.error(f"Error al agregar empleado: {e}")
        messages.error(request, "Ocurrió un error al agregar el empleado.")
        return redirect('lista_empleados')

@revisar_permiso('seguridad_usuarios.editar_empleado')
def editar_empleado(request, pk):
    """
    Vista para editar un empleado existente.
    """
    try:
        empleado = get_object_or_404(Empleado, id=pk)
        if request.method == 'POST':
            form = EmpleadoForm(request.POST, instance=empleado)
            if form.is_valid():
                form.save()
                messages.success(request, 'Empleado editado correctamente.')
                return redirect('lista_empleados')
        else:
            form = EmpleadoForm(instance=empleado)
        return render(request, 'seguridad_usuarios/editar_empleado.html', {'form': form})
    except Exception as e:
        logger.error(f"Error al editar empleado: {e}")
        messages.error(request, "Ocurrió un error al editar el empleado.")
        return redirect('lista_empleados')


@revisar_permiso('seguridad_usuarios.eliminar_empleado')
def eliminar_empleado(request, empleado_id):
    """
    Vista para eliminar Rol de un empleado existente.

    """
    try:
        empleado = get_object_or_404(Empleado, id=empleado_id)
        if request.method == 'POST':
            empleado.delete()
            messages.success(request, 'Empleado eliminado correctamente.')
            return redirect('lista_empleados')
        return render(request, 'seguridad_usuarios/eliminar_empleado.html', {'empleado': empleado})
    except Exception as e:
        logger.error(f"Error al eliminar empleado: {e}")
        messages.error(request, "Ocurrió un error al eliminar el empleado.")
        return redirect('lista_empleados')

@revisar_permiso('seguridad_usuarios.detallar_empleado')
def detalle_empleado(request, pk):
    """
    Vista para ver los detalles de un empleado.
    """
    try:
        empleado = get_object_or_404(Empleado, pk=pk)
        return render(request, 'seguridad_usuarios/detalle_empleado.html', {'empleado': empleado})
    except Exception as e:
        logger.error(f"Error al ver detalles del empleado con PK {pk}: {e}")
        messages.error(request, "Ocurrió un error al cargar los detalles del empleado.")
        return redirect('lista_empleados')

# --------------------------------------------------------------------------
# Vista de Roles
# --------------------------------------------------------------------------

@revisar_permiso('seguridad_usuarios.agregar_rol')
def agregar_rol(request):
    """
    Vista para agregar un nuevo rol.
    """
    try:
        if request.method == 'POST':
            form = RolForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Rol agregado correctamente.')
                return redirect('lista_roles')
        else:
            form = RolForm()
        return render(request, 'seguridad_usuarios/agregar_rol.html', {'form': form})
    except Exception as e:
        logger.error(f"Error al agregar rol: {e}")
        messages.error(request, "Ocurrió un error al agregar el rol.")
        return redirect('lista_roles')

@revisar_permiso('seguridad_usuarios.editar_rol')
def editar_rol(request, pk):
    """
    Vista para editar un rol existente.
    """
    try:
        rol = get_object_or_404(Rol, id=pk)
        if request.method == 'POST':
            form = RolForm(request.POST, instance=rol)
            if form.is_valid():
                form.save()
                messages.success(request, 'Rol editado correctamente.')
                return redirect('lista_roles')
        else:
            form = RolForm(instance=rol)
        return render(request, 'seguridad_usuarios/editar_rol.html', {'form': form})
    except Exception as e:
        logger.error(f"Error al editar rol: {e}")
        messages.error(request, "Ocurrió un error al editar el rol.")
        return redirect('lista_roles')

@revisar_permiso('seguridad_usuarios.listar_rol')
def lista_roles(request):
    """
    Vista para listar todos los roles.
    """
    roles = Rol.objects.all()
    if request.method == 'POST':
        # filtrar por nombre
        nombre = request.POST.get('nombre')
        if nombre:
            roles = Rol.objects.filter(nombre__icontains=nombre)
        
    return render(request, 'seguridad_usuarios/lista_roles.html', {'roles': roles})

# --------------------------------------------------------------------------
# Vista de Permisos
# --------------------------------------------------------------------------

@login_required
def lista_permisos(request):
    """
    Vista para listar todos los permisos.
    """
    permisos = Permiso.objects.all()
    return render(request, 'seguridad_usuarios/lista_permisos.html', {'permisos': permisos})

@login_required
def agregar_permiso(request):
    """
    Vista para agregar un nuevo permiso.
    """
    try:
        if request.method == 'POST':
            form = PermisoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Permiso agregado correctamente.')
                return redirect('lista_permisos')
        else:
            form = PermisoForm()
        return render(request, 'seguridad_usuarios/agregar_permiso.html', {'form': form})
    except Exception as e:
        logger.error(f"Error al agregar permiso: {e}")
        messages.error(request, "Ocurrió un error al agregar el permiso.")
        return redirect('lista_permisos')

@login_required
def eliminar_permiso(request, permiso_id):
    """
    Vista para eliminar un permiso existente.
    """
    try:
        permiso = get_object_or_404(Permiso, id=permiso_id)
        if request.method == 'POST':
            permiso.delete()
            messages.success(request, 'Permiso eliminado correctamente.')
            return redirect('lista_permisos')
        return render(request, 'seguridad_usuarios/eliminar_permiso.html', {'permiso': permiso})
    except Exception as e:
        logger.error(f"Error al eliminar permiso: {e}")
        messages.error(request, "Ocurrió un error al eliminar el permiso.")
        return redirect('lista_permisos')

@login_required
def editar_permiso(request, permiso_id):
    """
    Vista para editar un permiso existente.
    """
    try:
        permiso = get_object_or_404(Permiso, id=permiso_id)
        if request.method == 'POST':
            form = PermisoForm(request.POST, instance=permiso)
            if form.is_valid():
                form.save()
                messages.success(request, 'Permiso editado correctamente.')
                return redirect('lista_permisos')
        else:
            form = PermisoForm(instance=permiso)
        return render(request, 'seguridad_usuarios/editar_permiso.html', {'form': form})
    except Exception as e:
        logger.error(f"Error al editar permiso: {e}")
        messages.error(request, "Ocurrió un error al editar el permiso.")
        return redirect('lista_permisos')

# --------------------------------------------------------------------------
# Vista de Perfil de Usuario
# --------------------------------------------------------------------------

# @revisar_permiso('seguridad_usuarios.ver_perfil')
def ver_perfil(request, pk):
    """
    Vista para ver el perfil de un usuario.
    Recibe la clave primaria (pk) del usuario cuyo perfil se desea ver.
    """
    try:
        usuario = get_object_or_404(User, pk=pk) # Busca el usuario por su PK o devuelve un error 404
        usuario_perfil = getattr(usuario, 'perfil', None)  # Intenta obtener el perfil asociado
        empleado = usuario_perfil.empleado if usuario_perfil else None  # Intenta obtener el empleado asociado
        print(empleado)
        if usuario_perfil and empleado:
            return render(request, 'seguridad_usuarios/perfil_usuario.html', {'usuario': usuario, 'usuario_perfil': usuario_perfil, 'empleado': empleado})
        return redirect('home')
    except Exception as e:
        logger.error(f"Error al ver perfil de usuario con PK {pk}: {e}")
        messages.error(request, "Ocurrió un error al cargar el perfil del usuario.")
        return redirect('home')


# @revisar_permiso('seguridad_usuarios.ver_perfil_usuario')
def perfil_usuario(request, empleado_id):
    """
    Vista para ver el perfil de un usuario a partir del id de empleado.
    """
    try:
        
        empleado = get_object_or_404(Empleado, id=empleado_id)
        
        usuario_perfil = getattr(empleado, 'usuario_perfil', None)
        
        usuario = usuario_perfil.user if usuario_perfil else None
        
        return render(request, 'seguridad_usuarios/perfil_usuario.html', {
            'empleado': empleado,
            'usuario': usuario,
            'usuario_perfil': usuario_perfil
        })
    except Exception as e:
        logger.error(f"Error al ver perfil de usuario con ID {empleado_id}: {e}")
        messages.error(request, "Ocurrió un error al cargar el perfil del usuario.")
        return redirect('home')
    
@revisar_permiso('seguridad_usuarios.listar_perfiles')
def lista_perfiles(request):
    """
    Vista para listar todos los perfiles de usuario.
    """
    perfiles = UsuarioPerfil.objects.all()
    username = request.GET.get('username', '').strip()
    documento_identidad = request.GET.get('documento_identidad', '').strip()
    estado = request.GET.get('estado', '')

    if request.method == 'GET':

        if username:
            if request.GET['estado'] == 'ACTIVO':

                perfiles = perfiles.filter(user__is_active=True, user__username__icontains=username)
            else:
                if request.GET['estado'] == 'INACTIVO':
                    perfiles = perfiles.filter(user__is_active=False, user__username__icontains=username)
                else:
                    perfiles = perfiles.filter(user__username__icontains=username)
        documento_identidad = request.GET.get('documento_identidad')
        if documento_identidad:
            
            if request.GET['estado'] == 'ACTIVO':

                perfiles = perfiles.filter(user__is_active=True, empleado__documento_identidad__icontains=documento_identidad)
            else:
                if request.GET['estado'] == 'INACTIVO':
                    perfiles = perfiles.filter(user__is_active=False, empleado__documento_identidad__icontains=documento_identidad)
                else:
                    perfiles = perfiles.filter(empleado__documento_identidad__icontains=documento_identidad)
        if estado == 'True':
            perfiles = perfiles.filter(user__is_active=True)
        elif estado == 'False':
            perfiles = perfiles.filter(user__is_active=False)
    return render(request, 'seguridad_usuarios/lista_perfiles.html', {'perfiles': perfiles})

@revisar_permiso('seguridad_usuarios.crear_usuario_para_empleado')
def crear_usuario_para_empleado(request, empleado_id):
    """
    Vista para crear un usuario y perfil asociado a un empleado.
    """
    try:
        empleado = get_object_or_404(Empleado, id=empleado_id)
        if empleado.tiene_usuario:
            messages.warning(request, 'Este empleado ya tiene un usuario asociado.')
            return redirect('detalle_empleado', pk=empleado.id)
        if request.method == 'POST':
            form = PerfilUsuarioForm(request.POST, request.FILES)
            if form.is_valid():
                username = empleado.email
                password = empleado.documento_identidad
                nombre = empleado.nombre
                apellidos = empleado.apellidos
                usuario = User.objects.create_user(
                    username=username,
                    email=empleado.email,
                    password=password,
                    first_name=nombre,
                    last_name=apellidos
                )
                perfil_usuario = form.save(commit=False)
                perfil_usuario.empleado = empleado
                perfil_usuario.user = usuario
                perfil_usuario.save()
                # Guardar los roles seleccionados
                perfil_usuario.roles.set(form.cleaned_data['roles'])
                # Marcar que el empleado tiene un usuario asociado
                empleado.tiene_usuario = True
                empleado.save()
                messages.success(request, 'Usuario y perfil creados correctamente para el empleado.')
                return redirect('detalle_empleado', pk=empleado.id)
        else:
            form = PerfilUsuarioForm()
            form.fields['empleado'].initial = empleado
        return render(request, 'seguridad_usuarios/crear_usuario_para_empleado.html', {'form': form, 'empleado': empleado})
    except Exception as e:
        logger.error(f"Error al crear usuario para empleado con ID {empleado_id}: {e}")
        messages.error(request, "Ocurrió un error al crear el usuario para el empleado.")
        return redirect('lista_empleados')


def cargar_permisos(request):
    """
    Vista para cargar permisos iniciales en la base de datos, con nombre y descripción.
    """
    permisos_iniciales = [
        {
            'codename': 'seguridad_usuarios.registrar_usuario',
            'nombre': 'Registrar usuario',
            'descripcion': 'Permite registrar nuevos usuarios en el sistema.'
        },
        {
            'codename': 'seguridad_usuarios.editar_usuario',
            'nombre': 'Editar usuario',
            'descripcion': 'Permite editar los datos de usuarios existentes.'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_usuario',
            'nombre': 'Eliminar usuario',
            'descripcion': 'Permite eliminar usuarios del sistema.'
        },
        {
            'codename': 'seguridad_usuarios.listar_usuarios',
            'nombre': 'Listar usuarios',
            'descripcion': 'Permite ver la lista de usuarios registrados.'
        },
        {
            'codename': 'seguridad_usuarios.cambiar_contrasena',
            'nombre': 'Cambiar contraseña',
            'descripcion': 'Permite cambiar la contraseña de usuario.'
        },
        {
            'codename': 'seguridad_usuarios.agregar_empleado',
            'nombre': 'Agregar empleado',
            'descripcion': 'Permite agregar nuevos empleados.'
        },
        {
            'codename': 'seguridad_usuarios.editar_empleado',
            'nombre': 'Editar empleado',
            'descripcion': 'Permite editar los datos de empleados.'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_empleado',
            'nombre': 'Eliminar empleado',
            'descripcion': 'Permite eliminar empleados del sistema.'
        },
        {
            'codename': 'seguridad_usuarios.listar_empleados',
            'nombre': 'Listar empleados',
            'descripcion': 'Permite ver la lista de empleados registrados.'
        },
        {
            'codename': 'seguridad_usuarios.detallar_empleado',
            'nombre': 'Detalle de empleado',
            'descripcion': 'Permite ver el detalle de un empleado.'
        },
        {
            'codename': 'seguridad_usuarios.agregar_rol',
            'nombre': 'Agregar rol',
            'descripcion': 'Permite agregar nuevos roles.'
        },
        {
            'codename': 'seguridad_usuarios.editar_rol',
            'nombre': 'Editar rol',
            'descripcion': 'Permite editar los datos de roles.'
        },
        {
            'codename': 'seguridad_usuarios.listar_rol',
            'nombre': 'Listar roles',
            'descripcion': 'Permite ver la lista de roles registrados.'
        },
        {
            'codename': 'seguridad_usuarios.agregar_permiso',
            'nombre': 'Agregar permiso',
            'descripcion': 'Permite agregar nuevos permisos.'
        },
        {
            'codename': 'seguridad_usuarios.editar_permiso',
            'nombre': 'Editar permiso',
            'descripcion': 'Permite editar los datos de permisos.'
        },
        {
            'codename': 'seguridad_usuarios.eliminar_permiso',
            'nombre': 'Eliminar permiso',
            'descripcion': 'Permite eliminar permisos del sistema.'
        },
        {
            'codename': 'seguridad_usuarios.listar_permisos',
            'nombre': 'Listar permisos',
            'descripcion': 'Permite ver la lista de permisos registrados.'
        },
        {
            'codename': 'seguridad_usuarios.ver_perfil',
            'nombre': 'Ver perfil',
            'descripcion': 'Permite ver el perfil de usuario.'
        },
        {
            'codename': 'seguridad_usuarios.ver_perfil_usuario',
            'nombre': 'Ver perfil de empleado',
            'descripcion': 'Permite ver el perfil de usuario asociado a un empleado.'
        },
        {
            'codename': 'seguridad_usuarios.listar_perfiles',
            'nombre': 'Listar perfiles',
            'descripcion': 'Permite ver la lista de perfiles de usuario.'
        },
        {
            'codename': 'seguridad_usuarios.crear_usuario_para_empleado',
            'nombre': 'Crear usuario para empleado',
            'descripcion': 'Permite crear un usuario y perfil para un empleado.'
        },
    ]
    for permiso in permisos_iniciales:
        Permiso.objects.get_or_create(
            codename=permiso['codename'],
            defaults={
                'nombre': permiso['nombre'],
                'descripcion': permiso['descripcion']
            }
        )
    return redirect('home')