# seguridad_usuarios/models.py

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
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

    def permisos_asignados_simplificados(self):
        return [permiso.obtener_permisos_simplificados() for permiso in self.permisos.all()]

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

    def obtener_permisos_simplificados(self):
        """Devuelve el codename simplificado del permiso, que es la parte después del punto."""
        return self.codename.split('.')[-1]  # Obtener la parte después del punto
         
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
    
    def guardar_nombre_camel_case(self):
        if self.nombre:
            self.nombre = self.nombre.title()
        if self.apellidos:
            self.apellidos = self.apellidos.title()
        if self.razon_social:
            self.razon_social = self.razon_social.title()

    def guardar_email_minusculas(self):
        if self.email:
            self.email = self.email.lower()
    
    def guardar_direccion_minusculas(self):
        if self.direccion:
            self.direccion = self.direccion.lower()
           
    def guardar_ruc_sin_espacios(self):
        if self.ruc:
            self.ruc = self.ruc.replace(" ", "")
    
    def guardar_telefono_sin_espacios(self):
        if self.telefono:
            self.telefono = self.telefono.replace(" ", "")
    
    def guardar_persona(self):
        self.guardar_nombre_camel_case()
        self.guardar_email_minusculas()
        self.guardar_direccion_minusculas()
        self.guardar_ruc_sin_espacios()
        self.guardar_telefono_sin_espacios()
    
    class Meta:
        abstract = True
    

class Empleado(Persona):
    """
    Modelo que representa un Empleado de SKPY.
    """
    departamento = models.ForeignKey('configuraciones_maestras.Departamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Departamento")
    cargo = models.ForeignKey('configuraciones_maestras.Cargo', on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Cargo")
    sucursal = models.ForeignKey(
        'configuraciones_maestras.Sucursal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empleados',
        verbose_name='Sucursal'
    )
    fecha_contratacion = models.DateField(blank=True, null=True, verbose_name="Fecha de Contratación")
    fecha_terminacion = models.DateField(blank=True, null=True, verbose_name="Fecha de Terminación")
    descripcion_trabajo = models.TextField(blank=True, null=True, verbose_name="Descripción del Trabajo")
    tiene_usuario = models.BooleanField(default=False, verbose_name="Tiene Usuario")

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ['nombre']

    def obtener_contacto_principal(self):
        contacto_principal = self.contactos.filter(es_principal=True).first()
        if contacto_principal:
            return contacto_principal
        return None
    
    def obtener_contactos_por_categoria(self, categoria):
        return self.contactos.filter(categoria=categoria)
    
    def obtener_contactos_profesionales(self):
        return self.contactos.filter(categoria='PROFESIONAL')
    
    def obtener_contactos_personales(self):
        return self.contactos.filter(categoria='PERSONAL')
    
    def tiene_contacto_principal(self):
        return self.contactos.filter(es_principal=True).exists()
    
    def tiene_contactos_profesionales(self):
        return self.contactos.filter(categoria='PROFESIONAL').exists()
    
    def tiene_contactos_personales(self):
        return self.contactos.filter(categoria='PERSONAL').exists()
    
    def obtener_contacto(self):
        """
        Devuelve el contacto principal del empleado si existe, 
        de lo contrario verifica si hay contactos profesionales o personales y devuelve el primero que encuentre. 
        """
        contacto_principal = self.obtener_contacto_principal()
        if contacto_principal:
            return contacto_principal
        
        contactos_profesionales = self.obtener_contactos_profesionales()
        if contactos_profesionales.exists():
            return contactos_profesionales.first()
        
        contactos_personales = self.obtener_contactos_personales()
        if contactos_personales.exists():
            return contactos_personales.first()
        
        return None
    
    def obtener_telefono(self):
        contacto = self.obtener_contacto()
        if contacto:
            return contacto.telefono
        return None
    
    def obtener_direccion(self):
        contacto = self.obtener_contacto()
        if contacto:
            return contacto.direccion
        return None
    
    def obtener_email(self):
        contacto = self.obtener_contacto()
        if contacto:
            return contacto.email
        return None
    
    def obtener_nombre_completo(self):
        nombre = self.nombre or ""
        apellidos = self.apellidos or ""
        return f"{nombre} {apellidos}".strip()
    
    def obtener_nombre_o_razon_social(self):
        if self.tipo_persona == 'FISICA':
            return self.obtener_nombre_completo()
        elif self.tipo_persona == 'JURIDICA':
            return self.razon_social or ""
        return ""
    
    def __str__(self):
        nombre = self.nombre or ""
        apellidos = self.apellidos or ""
        return f"{nombre} {apellidos}".strip() or f"Empleado #{self.id}"
    
    def save(self, *args, **kwargs):
        # Guardar la persona antes de guardar el empleado
        self.guardar_persona()

        old_cargo_id = None
        if self.pk:
            old = Empleado.objects.filter(pk=self.pk).only('cargo_id').first()
            old_cargo_id = old.cargo_id if old else None

        super().save(*args, **kwargs)

        try:
            from configuraciones_maestras.models import CargoEmpleadoHistorial
        except ImportError:
            CargoEmpleadoHistorial = None

        if CargoEmpleadoHistorial is not None:
            new_cargo_id = self.cargo_id
            if new_cargo_id and new_cargo_id != old_cargo_id:
                CargoEmpleadoHistorial.objects.get_or_create(
                    cargo_id=new_cargo_id,
                    empleado=self,
                )
            if old_cargo_id and old_cargo_id != new_cargo_id:
                CargoEmpleadoHistorial.objects.get_or_create(
                    cargo_id=old_cargo_id,
                    empleado=self,
                )
        


class ContactoEmpleado(Persona):
    CATEGORIA_CHOICES = [
        ('PERSONAL', 'Personal'),
        ('PROFESIONAL', 'Profesional'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='contactos')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='PERSONAL', verbose_name='Categoría')
    es_principal = models.BooleanField(default=False, verbose_name='Es Principal')

    class Meta:
        verbose_name = "Contacto de Empleado"
        verbose_name_plural = "Contactos de Empleados"

    def __str__(self):
        nombre = self.nombre or ''
        apellidos = self.apellidos or ''
        return f"{self.get_categoria_display()} - {nombre} {apellidos}".strip()


class UsuarioPerfil(models.Model):
    """
    Modelo que representa el perfil de un usuario en el sistema.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name='usuario_perfil', null=True, blank=True)
    roles = models.ManyToManyField(Rol, blank=True, related_name='usuarios')
    debe_cambiar_contrasena = models.BooleanField(default=True) # Indica si el usuario debe cambiar su contraseña en el próximo inicio de sesión
    rol_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rol")
    tema = models.CharField(
        max_length=50,
        choices=[
            ('theme-default', 'Tema Predeterminado'),
            ('theme-dark', 'Modo Oscuro'),
            ('theme-light', 'Modo Claro'),
            ('theme-emerald', 'Verde'),
            ('theme-ocean', 'Ocean'),
            ('theme-sunset', 'Sunset'),
        ],
        default='theme-default',
        verbose_name="Tema",
        help_text="Preferencia de tema del usuario"
    )
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True, verbose_name="Foto de Perfil")
    Contrasena_temporal = models.CharField(max_length=255, blank=True, null=True, verbose_name="Contraseña Temporal")

    def roles_asignados(self):
        if self.empleado and getattr(self.empleado, 'cargo_id', None):
            return self.empleado.cargo.roles.all() | self.roles.all()
        return self.roles.all()

    def permisos_asignados(self):
        permisos = set()
        for rol in self.roles_asignados():
            permisos.update(rol.permisos.values_list('codename', flat=True))
        return permisos

    def permisos_simplificados(self):
        permisos = set()
        for rol in self.roles_asignados():
            for permiso in rol.permisos.all():
                permisos.add(permiso.obtener_permisos_simplificados())
        return permisos
    
    def enviar_contrasena_temporal(self):
        if self.empleado and self.empleado.email:
            enviar_contrasena_temporal(self.empleado.email)

    def tiene_permiso(self, codename):
        return codename in self.permisos_asignados()

    def tiene_any_permiso(self, *codename_permisos):
        permisos = self.permisos_asignados()
        return any(codename in permisos for codename in codename_permisos)
    
    class Meta:
        verbose_name = "Usuario Perfil"
        verbose_name_plural = "Usuarios Perfil"
        ordering = ['user__username']


@receiver(post_save, sender=User)
def crear_usuario_perfil(sender, instance, created, **kwargs):
    if created:
        UsuarioPerfil.objects.create(user=instance)


@receiver(post_save, sender=User)
def asegurar_usuario_perfil(sender, instance, **kwargs):
    if not hasattr(instance, 'perfil'):
        UsuarioPerfil.objects.create(user=instance)


def enviar_contrasena_temporal(email_destino):
    asunto = "Contraseña Temporal para tu Cuenta en SKPY"
    mensaje = f"Hola,\n\nSe ha generado una contraseña temporal para tu cuenta en SKPY. Por favor, utiliza la siguiente contraseña para iniciar sesión y recuerda cambiarla después de ingresar:\n\nContraseña Temporal: {Contrasena_temporal}\n\nSi no solicitaste esta contraseña, por favor ignora este correo.\n\nSaludos,\nEquipo de SKPY"
    send_mail(asunto, mensaje, email, [email_destino], fail_silently=False)

def enviar_email_notificacion(email_destino, asunto, mensaje):
    send_mail(asunto, mensaje, email, [email_destino], fail_silently=False)



