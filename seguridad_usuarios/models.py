# seguridad_usuarios/models.py

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from abc import ABC
from django.core.mail import send_mail
email = 'christianfleitas97@gmail.com' # Correo electrónico del remitente
Contrasena_temporal = "12345678"


class Auditoria(models.Model):
    """
    Modelo que representa una auditoría en el sistema.
    """
    TIPO_ACCION_CHOICES = [
        ('CREACION', 'Creación'),
        ('MODIFICACION', 'Modificación'),
        ('ELIMINACION', 'Eliminación'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auditorias')
    accion = models.CharField(max_length=255, choices=TIPO_ACCION_CHOICES)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    id_tabla = models.IntegerField(blank=True, null=True)
    tabla = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'Acción: {self.accion} por {self.user.username} en {self.fecha_hora}'
        
    
class Rol(models.Model):
    """
    Modelo que representa un Rol en el sistema.
    """

    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Rol")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del Rol")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")
    fecha_vigencia = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Vigencia")
    permisos = models.ManyToManyField('Permiso', blank=True, verbose_name="Permisos")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo
    utilizado = models.BooleanField(default=False, verbose_name="Utilizado")  # Indica si el rol está asignado a algún usuario

    def agregar_permiso(self, permiso):
        if self.utilizado or self.estado == False:
            raise ValueError("No se pueden modificar los permisos de un rol que ya está asignado a usuarios.")
        else:
            self.permisos.add(permiso)
            self.save()
    

    def eliminar_permiso(self, permiso):
        if self.utilizado or self.estado == False:
            raise ValueError("No se pueden modificar los permisos de un rol que ya está asignado a usuarios.")
        else:
            self.permisos.remove(permiso)
            self.save()
    
    def finalizar_vigencia(self):
        self.fecha_vigencia = timezone.now()
        self.estado = False
        self.save()

    def reactivar_rol(self):
        self.fecha_vigencia = None
        self.estado = True
        self.save()
    
    def inactivar_rol(self):
        self.fecha_vigencia = timezone.now()
        self.estado = False
        self.save()
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']


class Permiso(models.Model):
    """
    Modelo que representa un Permiso en el sistema.
    """
    codename = models.CharField(max_length=100, unique=True, default='sin_codename')
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    sector = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        if self.sector:
            return f" ({self.sector.upper()}) - {self.nombre}"
        return self.nombre

    class Meta:
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        ordering = ['codename']


class Persona(models.Model): 
    """
    Modelo abstracto que representa una Persona.
    """

    TIPO_PERSONA_CHOICES = [
        ('FISICA', 'Persona Física'),
        ('JURIDICA', 'Persona Jurídica'),
    ]
    
    tipo_persona = models.CharField(max_length=10, choices=TIPO_PERSONA_CHOICES, default='FISICA', verbose_name="Tipo de Persona")
    razon_social = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razón Social")
    nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombres")
    apellidos = models.CharField(max_length=255, blank=True, null=True, verbose_name="Apellidos")
    ruc = models.CharField(max_length=13, blank=True, null=True, verbose_name="RUC o Identificador Fiscal")
    documento_identidad = models.CharField(max_length=20, blank=True, null=True, verbose_name="Documento de Identidad")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    fecha_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)  # True para activo, False para inactivo
    fecha_baja = models.DateTimeField(blank=True, null=True)

    def cambiar_telefono(self, nuevo_telefono):
        self.telefono = nuevo_telefono
        self.save()

    def __str__(self):
        return f'{self.razon_social or self.nombre} ({self.documento_identidad or self.ruc})'

    def inactivar(self):
        self.estado = False
        self.fecha_baja = timezone.now()
        self.save()
    
    def reactivar(self):
        self.estado = True
        self.fecha_baja = None
        self.save()

    class Meta:
        abstract = True
    

class Empleado(Persona):
    """
    Modelo que representa un Empleado de SKPY.
    """
    from configuraciones_maestras.models import Departamento, Cargo

    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Departamento")
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Cargo")
    fecha_contratacion = models.DateField(blank=True, null=True, verbose_name="Fecha de Contratación")
    fecha_terminacion = models.DateField(blank=True, null=True, verbose_name="Fecha de Terminación")
    descripcion_trabajo = models.TextField(blank=True, null=True, verbose_name="Descripción del Trabajo")
    tiene_usuario = models.BooleanField(default=False, verbose_name="Tiene Usuario")
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ['nombre']


    def __str__(self):
        nombre = self.nombre or ""
        apellidos = self.apellidos or ""
        return f"{nombre} {apellidos}".strip() or f"Empleado #{self.id}"


class UsuarioPerfil(models.Model):
    """
    Modelo que representa el perfil de un usuario en el sistema.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name='usuario_perfil', null=True, blank=True)
    roles = models.ManyToManyField(Rol, blank=True, related_name='usuarios')
    debe_cambiar_contrasena = models.BooleanField(default=True) # Indica si el usuario debe cambiar su contraseña en el próximo inicio de sesión
    rol_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rol")
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True, verbose_name="Foto de Perfil")

    def permisos_asignados(self):
        permisos = set()
        for rol in self.roles.all():
            permisos.update(rol.permisos.values_list('codename', flat=True))
        return permisos

    class Meta:
        verbose_name = "Usuario Perfil"
        verbose_name_plural = "Usuarios Perfil"
        ordering = ['user__username']


