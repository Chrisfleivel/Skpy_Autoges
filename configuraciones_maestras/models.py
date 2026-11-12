# configuraciones_maestras/models.py

from django.conf import settings
from django.db import models
from django.utils import timezone
from seguridad_usuarios.models import Persona, Rol, Empleado
from django.contrib.auth.models import User

# --------------------------------------------------------------------------
# Modelo para representar un Proveedor
# --------------------------------------------------------------------------
class Proveedor(Persona):
    """
    Modelo que representa un Proveedor de SKPY.
    """
    pais = models.CharField(max_length=80, blank=True, null=True, verbose_name="País del Proveedor")
    tax_id = models.CharField("ID fiscal", max_length=50, blank=True)
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_proveedor')
    contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Persona de Contacto")
    # ...otros campos y métodos...

    # Datos bancarios para la orden de pago al exterior
    banco = models.CharField(max_length=150, blank=True)
    cuenta_bancaria = models.CharField(max_length=60, blank=True)
    swift = models.CharField("SWIFT/BIC", max_length=20, blank=True)

    activo = models.BooleanField(default=True)

    def inactivar(self):
        self.estado = False
        self.save()

    def eliminable(self):
        return not self.contactos.exists()  # Solo se puede eliminar si no tiene contactos asociados
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.razon_social or self.nombre or f"Proveedor #{self.id}"



class ContactoProveedor(Persona):
    """
    Modelo que representa un Contacto específico de un Proveedor.
    """
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='contactos', verbose_name="Proveedor")
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_contacto_proveedor')
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo del Contacto")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono del Contacto")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico del Contacto")

    class Meta:
        verbose_name = "Contacto de Proveedor"
        verbose_name_plural = "Contactos de Proveedores"
        ordering = ['nombre']

    def __str__(self):
        proveedor_name = str(self.proveedor) if self.proveedor else "Sin Proveedor"
        nombre = self.nombre or f"Contacto #{self.id}"
        return f'{nombre} ({proveedor_name})'
    
    
# --------------------------------------------------------------------------
# Modelo para representar un Agente de Transporte
# --------------------------------------------------------------------------
class AgenteTransporte(Persona):
    """
    Modelo que representa un Agente de Transporte utilizado en las importaciones.
    Permite distinguir entre tramos internacionales de origen y tramos locales de destino.
    """
    PAIS_OPERACION_CHOICES = [
        ('KR', 'Corea del Sur'),
        ('PY', 'Paraguay'),
        ('OT', 'Otro'),
    ]

    TIPO_SERVICIO_CHOICES = [
        ('MARITIMO', 'Marítimo'),
        ('AEREO', 'Aéreo'),
        ('TERRESTRE', 'Terrestre'),
        ('MULTIMODAL', 'Multimodal'),
    ]

    TIPO_CARGA_CHOICES = [
        ('VEHICULOS', 'Vehículos'),
        ('REPUESTOS', 'Repuestos'),
        ('MIXTO', 'Mixto'),
    ]

    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_agente_transporte')
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Persona de Contacto")
    pais_operacion = models.CharField(max_length=2, choices=PAIS_OPERACION_CHOICES, blank=True, null=True, verbose_name="País de Operación")
    registro_autoridad = models.CharField(max_length=50, blank=True, null=True, verbose_name="Registro Autoridad (IATA/FIATA/DINATRAN)")
    tipo_servicio = models.CharField(max_length=20, choices=TIPO_SERVICIO_CHOICES, blank=True, null=True, verbose_name="Tipo de Transporte")
    lugar_operacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Puerto/Aeropuerto habitual")
    tipo_carga_especialidad = models.CharField(max_length=30, choices=TIPO_CARGA_CHOICES, blank=True, null=True, verbose_name="Especialidad de Carga")
    contacto_emergencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Contacto de Emergencia")
    numero_poliza_seguro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Póliza de Seguro de Carga")
    placa_vehiculo = models.CharField(max_length=30, blank=True, null=True, verbose_name="Placa de Vehículo/Cigüeña")
    cedula_verde = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cédula Verde")
    nombre_chofer = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre del Chofer")
    cedula_chofer = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula del Chofer")

    class Meta:
        verbose_name = "Agente de Transporte"
        verbose_name_plural = "Agentes de Transporte"
        ordering = ['nombre']

    def __str__(self):
        return self.razon_social or self.nombre or f"Agente #{self.id}"

# --------------------------------------------------------------------------
# Modelo para representar un Despachante de Aduana
# --------------------------------------------------------------------------
class DespachanteAduana(Persona):
    """
    Modelo que representa un Despachante de Aduana.
    """
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_despachante_aduana')
    # ...otros campos y métodos...
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Despachante")
    contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Persona de Contacto")
    registro = models.CharField(max_length=50, unique=True, verbose_name="Número de Registro")

    class Meta:
        verbose_name = "Despachante de Aduana"
        verbose_name_plural = "Despachantes de Aduana"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre or f"Despachante #{self.id}"


class Despachante(models.Model):
    """
    Representa un despachante o agente encargado del despacho/importación.
    Diseñado para cubrir tanto despachantes paraguayos como representantes en Corea.
    """
    PAIS_CHOICES = [
        ('PY', 'Paraguay'),
        ('KR', 'Corea del Sur'),
        ('OT', 'Otro'),
    ]

    TIPO_REPRESENTACION = [
        ('CUSTOMS_BROKER', 'Customs Broker'),
        ('IOR', 'Importer of Record'),
    ]

    SISTEMA_GESTION = [
        ('VUI_SOFIA', 'VUI / SOFIA'),
        ('UNI_PASS', 'UNI-PASS'),
        ('OTRO', 'Otro'),
    ]

    nombre_razon_social = models.CharField(max_length=255, verbose_name="Nombre o Razón Social")
    pais_codigo = models.CharField(max_length=2, choices=PAIS_CHOICES, verbose_name="Código de País")
    ruc_o_brn = models.CharField(max_length=50, blank=True, null=True, verbose_name="RUC / BRN")
    tipo_representacion = models.CharField(max_length=20, choices=TIPO_REPRESENTACION, verbose_name="Tipo de Representación")
    sistema_gestion = models.CharField(max_length=20, choices=SISTEMA_GESTION, blank=True, null=True, verbose_name="Sistema de Gestión")
    fecha_vencimiento_mandato = models.DateField(blank=True, null=True, verbose_name="Fecha Vencimiento Mandato")
    contacto_email = models.EmailField(blank=True, null=True, verbose_name="Email de Contacto")
    es_activo = models.BooleanField(default=True, verbose_name="Es Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Despachante"
        verbose_name_plural = "Despachantes"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre_razon_social} ({self.pais_codigo})"


class MonedaManager(models.Manager):
    def cargar_monedas_iniciales(self):
        return Moneda.ensure_defaults()


class Moneda(models.Model):
    """
    Modelo para representar una Moneda.
    """
    DEFAULTS = (
        ('USD', 'Dólar Estadounidense'),
        ('PYG', 'Guaraní Paraguayo'),
        ('KRW', 'Won Surcoreano'),
        ('EUR', 'Euro'),
        ('BRL', 'Real'),
    )

    codigo = models.CharField(max_length=3, unique=True, verbose_name="Código de la Moneda")
    nombre = models.CharField(max_length=50, verbose_name="Nombre de la Moneda")

    objects = MonedaManager()

    class Meta:
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        ordering = ['codigo']

    @classmethod
    def ensure_defaults(cls):
        """
        Crea la lista base de monedas si aún no existen.

        Idempotente y barato: una sola consulta para saber cuáles ya están.
        """
        codigos = [codigo for codigo, _ in cls.DEFAULTS]
        existentes = set(
            cls.objects.filter(codigo__in=codigos).values_list('codigo', flat=True)
        )
        created = []
        for codigo, nombre in cls.DEFAULTS:
            if codigo in existentes:
                continue
            created.append(cls.objects.create(codigo=codigo, nombre=nombre))
        return created

    @classmethod
    def get_choices(cls):
        """
        Lista (código, nombre) de las monedas del sistema.

        Importante: este método **no escribe** en la base de datos. Se usa como
        `choices` de varios campos de modelo y Django evalúa los callables de
        `choices` durante los *system checks* (`manage.py check`), que se ejecutan
        en `runserver`, `test`, `migrate` y `makemigrations`. Si escribiera aquí,
        los checks modificarían la base de datos y la siembra quedaría como
        efecto secundario invisible.

        Las monedas base se siembran con la migración de datos
        `0023_seed_monedas_iniciales` y, en runtime, con `ensure_defaults()`.
        """
        return [(moneda.codigo, moneda.nombre) for moneda in cls.objects.order_by('codigo')]

    @classmethod
    def cargar_monedas_iniciales(cls):
        return cls.ensure_defaults()

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Banco(models.Model):
    """
    Banco corresponsal o beneficiario involucrado en la operación de pago exterior.
    """
    codigo = models.CharField(max_length=30, blank=True, null=True, unique=True, verbose_name="Código del Banco")
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Banco")
    pais_codigo = models.CharField(max_length=2, blank=True, null=True, verbose_name="País del Banco")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    swift = models.CharField(max_length=50, blank=True, null=True, verbose_name="SWIFT / BIC")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"
        ordering = ['nombre']

    def __str__(self):
        if self.codigo and self.nombre:
            return f"{self.nombre} ({self.codigo})"
        return self.nombre or f"Banco #{self.pk}"


class OrdenPagoExterior(models.Model):
    """
    Liquidación de orden de pago al exterior, alineada con la estructura del documento de remesa.
    """
    TIPO_DOCUMENTO_CHOICES = [
        ('CI', 'Cédula de Identidad'),
        ('RUC', 'RUC'),
        ('PASAPORTE', 'Pasaporte'),
        ('OTRO', 'Otro'),
    ]

    FORMA_PAGO_CHOICES = [
        ('DBCUENTA', 'Domiciliación / Cuenta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CHEQUE', 'Cheque'),
        ('OTRO', 'Otro'),
    ]

    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADA = 'APROBADA', 'Aprobada'
        ENVIADA = 'ENVIADA', 'Enviada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    ESTADO_CHOICES = Estado.choices

    # Formas de pago del documento -> formas de pago del asiento financiero.
    MAPEO_FORMA_PAGO = {
        'DBCUENTA': 'DEBITO_CUENTA',
        'TRANSFERENCIA': 'DEBITO_CUENTA',
        'CHEQUE': 'CHEQUE',
        'OTRO': 'OTRA',
    }

    tipo_documento_remitente = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, verbose_name="Tipo de Documento del Remitente")
    numero_documento_remitente = models.CharField(max_length=50, verbose_name="Nro. Documento del Remitente")
    remitente_nombre = models.CharField(max_length=200, verbose_name="Nombre del Remitente")
    remitente_direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección del Remitente")
    remitente_telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono del Remitente")

    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, default='TRANSFERENCIA', verbose_name="Forma de Pago")
    numero_cuenta = models.CharField(max_length=80, blank=True, null=True, verbose_name="Nro. de Cuenta")
    moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT, related_name='ordenes_pago_exterior', verbose_name="Moneda")

    capital = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Capital")
    comision = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Comisión")
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Total")

    referencia_op = models.CharField(max_length=50, blank=True, null=True, verbose_name="Referencia OP")
    numero_lote = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nro. de Lote")
    fecha_operacion = models.DateField(verbose_name="Fecha de Operación")

    banco_corresponsal = models.ForeignKey(Banco, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_pago_corresponsal', verbose_name="Banco Corresponsal")
    ordenante = models.CharField(max_length=200, verbose_name="Ordenante")
    banco_beneficiario = models.ForeignKey(Banco, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_pago_beneficiario', verbose_name="Banco Beneficiario")
    pais_beneficiario = models.CharField(max_length=2, blank=True, null=True, verbose_name="País del Beneficiario")
    cuenta_beneficiaria = models.CharField(max_length=80, blank=True, null=True, verbose_name="Cuenta Beneficiaria")
    beneficiario = models.CharField(max_length=200, verbose_name="Beneficiario")
    motivo_transferencia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motivo de la Transferencia")
    concepto = models.CharField(max_length=255, blank=True, null=True, verbose_name="Concepto")
    cotizacion = models.DecimalField(max_digits=12, decimal_places=4, default=1, verbose_name="Cotización")
    importe_orden = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Importe Orden")
    comision_orden = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Comisión Orden")
    total_orden = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Total Orden")

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR, verbose_name="Estado")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    usuario_creo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_pago_exterior_creadas', verbose_name="Usuario que creó")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    # ---- Captura manual del documento ------------------------------------
    archivo = models.FileField(
        'Imagen o PDF de la liquidación',
        upload_to='configuraciones_maestras/ordenes_pago/%Y/%m/',
        blank=True,
    )
    firmante = models.CharField('Firmante', max_length=200, blank=True)
    hora_operacion = models.TimeField('Hora de operación', null=True, blank=True)
    usuario_banco = models.CharField('Usuario del banco', max_length=120, blank=True)

    # ---- Vínculos con la operación ---------------------------------------
    factura = models.ForeignKey(
        'compras.FacturaComercial',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ordenes_pago',
        verbose_name='Factura comercial',
    )
    embarque = models.ForeignKey(
        'importaciones.Embarque',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ordenes_pago',
        verbose_name='Embarque',
    )
    pago_exterior = models.OneToOneField(
        'finanzas.PagoExterior',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='orden_pago',
        verbose_name='Pago al exterior',
    )

    class Meta:
        verbose_name = "Orden de Pago Exterior"
        verbose_name_plural = "Órdenes de Pago Exterior"
        ordering = ['-fecha_operacion', '-created_at']

    def __str__(self):
        return f"OP-{self.pk or 'nuevo'} {self.beneficiario} - {self.total_orden} {self.moneda.codigo}"

    def save(self, *args, **kwargs):
        """Los totales del documento se calculan siempre a partir del importe y la comisión."""
        self.guardar_totales_desde_documento()
        super().save(*args, **kwargs)

    @property
    def pago_registrado(self):
        """Indica si la liquidación ya tiene su asiento financiero."""
        return self.pago_exterior_id is not None

    @property
    def forma_pago_finanzas(self):
        """Forma de pago del documento traducida al asiento financiero."""
        return self.MAPEO_FORMA_PAGO.get(self.forma_pago, 'OTRA')

    def recalcular_totales(self):
        self.capital = self.importe_orden
        self.comision = self.comision_orden
        self.total = self.total_orden
        return self.total

    def guardar_totales_desde_documento(self):
        """
        Convencionalmente el documento usa estas reglas:
        - capital = importe_orden
        - comisión = comisión_orden
        - total = importe_orden + comisión_orden
        """
        self.capital = self.importe_orden
        self.comision = self.comision_orden
        self.total = self.importe_orden + self.comision_orden
        self.total_orden = self.total
        return self.total


# --------------------------------------------------------------------------
# Modelo para representar una Tasa de Cambio de Moneda
# --------------------------------------------------------------------------
class TasaCambio(models.Model):
    """
    Modelo para registrar las Tasas de Cambio utilizadas en el sistema.
    Garantiza trazabilidad al registrar la tasa de cambio aplicada en cada transaccion.
    """
    MONEDA_CHOICES = [
        ('USD', 'Dólar Estadounidense'),
        ('PYG', 'Guaraní Paraguayo'),
    ]
    moneda_origen = models.CharField(max_length=3, verbose_name="Moneda de Origen", default="USD", choices=MONEDA_CHOICES)
    moneda_destino = models.CharField(max_length=3, verbose_name="Moneda de Destino", default="PYG", choices=MONEDA_CHOICES)
    valor = models.DecimalField(max_digits=12, decimal_places=4, verbose_name="Valor de la Tasa")
    fecha = models.DateField(unique=True, verbose_name="Fecha de Tasa (Validez)")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Registro")
    usuario_creo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasas_cambio_creadas', verbose_name="Usuario que registro")

    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ['-fecha']
        unique_together = [['moneda_origen', 'moneda_destino', 'fecha']]

    def __str__(self):
        return f"1 {self.moneda_origen} = {self.valor} {self.moneda_destino} (al {self.fecha})"

    @classmethod
    def registrar(cls, *, moneda_origen='USD', moneda_destino='PYG', valor=1, fecha=None, usuario=None):
        """Crea o actualiza la tasa para un par y fecha determinados."""
        from decimal import Decimal
        from django.utils import timezone

        fecha = fecha or timezone.now().date()
        valor = Decimal(str(valor))

        tasa, created = cls.objects.get_or_create(
            moneda_origen=str(moneda_origen).upper(),
            moneda_destino=str(moneda_destino).upper(),
            fecha=fecha,
            defaults={'valor': valor, 'usuario_creo': usuario},
        )

        if not created:
            tasa.valor = valor
            if usuario is not None:
                tasa.usuario_creo = usuario
            tasa.save(update_fields=['valor', 'usuario_creo'])

        return tasa

    @classmethod
    def obtener_tasa_actual(cls, moneda_origen='USD', moneda_destino='PYG'):
        """
        Obtiene la tasa de cambio mas reciente para el par de monedas especificado.
        """
        from django.utils import timezone
        hoy = timezone.now().date()
        return cls.objects.filter(
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            fecha__lte=hoy
        ).order_by('-fecha').first()

    @classmethod
    def existe_tasa_para_hoy(cls, moneda_origen='USD', moneda_destino='PYG'):
        """
        Verifica si existe una tasa de cambio registrada para hoy.
        """
        from django.utils import timezone
        hoy = timezone.now().date()
        return cls.objects.filter(
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            fecha=hoy
        ).exists()

    @classmethod
    def get_choices(cls):
        return [(codigo, nombre) for codigo, nombre in Moneda.get_choices()]
    


# Departamentos en la empresa

class Departamento(models.Model):
    '''
    Modelo que representa la Dependencia en la empresa.
    '''

    empresa = models.ForeignKey('Empresa', on_delete=models.PROTECT, related_name='departamentos', null=True, blank=True, verbose_name="Empresa")
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Departamento")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del Departamento")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo
    eliminable = models.BooleanField(default=True, verbose_name="Eliminable")  # True si se puede eliminar, False si no

    def activar(self):
        """Activa el departamento y lo marca como disponible.
        solo si no existe un departamento con el mismo nombre que esté activo."""
        if Departamento.objects.filter(nombre=self.nombre, estado=True).exists():
            raise ValueError("No se puede activar el departamento porque ya existe un departamento activo con el mismo nombre.")
        self.estado = True
        self.save()

    def eliminable(self):
        """Se puede eliminar un departamento si no tiene cargos asociados.
        O si tiene cargos, pero todos esos cargos son eliminables (no tienen empleados ni historial)."""
        if self.cargos.exists():
            for cargo in self.cargos.all():
                if not cargo.eliminable():
                    return False
        return True
    
    def editable(self):
        """Se puede editar un departamento si no tiene cargos asociados.
        O si tiene cargos, pero todos esos cargos son eliminables (no tienen empleados ni historial)."""
        if self.cargos.exists():
            for cargo in self.cargos.all():
                if not cargo.eliminable():
                    return False
        return True

    def activable(self):
        """Se puede activar un departamento si no tiene cargos asociados que no sean eliminables."""
        if self.cargos.exists():
            for cargo in self.cargos.all():
                if not cargo.eliminable():
                    return False
        return True

    def inactivar(self):
        """Inactiva el departamento y lo marca como no disponible.
        solo si no tiene cargos asociados que estén activos."""
        if self.cargos.filter(estado=True).exists():
            raise ValueError("No se puede inactivar el departamento porque tiene cargos activos.")
        self.estado = False
        self.save()

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']


# Cargos o puestos de trabajo en la empresa segun departamentos
class Cargo(models.Model):
    """ 
    Modelo que representa un Cargo o Puesto de Trabajo en la empresa.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Cargo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del Cargo")
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='cargos', verbose_name="Departamento")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo
    vacantes = models.IntegerField(default=1, verbose_name="Número de Vacantes")
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Salario")
    roles = models.ManyToManyField(Rol, blank=True, related_name='cargos', verbose_name="Roles Asociados")
    

    def __str__(self):
        return f'{self.nombre} - {self.departamento.nombre}'
    
    def eliminable(self):
        return not self.empleados.exists() and not self.historial_empleados.exists()
    
    def editable(self):
        """Se puede editar un cargo si no tiene empleados asociados.
        O si tiene empleados, pero todos esos empleados son eliminables (no tienen historial)."""
        if self.empleados.exists():
            return not self.historial_empleados.exists()
        return True
    
    def inactivar(self):
        self.estado = False
        self.save()

    def activar(self):
        """Activa el cargo y lo marca como disponible.
        solo si no existe un cargo con el mismo nombre y departamento que esté activo."""
        if Cargo.objects.filter(nombre=self.nombre, departamento=self.departamento, estado=True).exists():
            raise ValueError("No se puede activar el cargo porque ya existe un cargo activo con el mismo nombre y departamento.")
        self.estado = True
        self.save()

    def abrir_vacante(self):
        self.vacantes += 1
        self.save()
    
    def cerrar_vacante(self):
        if self.vacantes > 0:
            self.vacantes -= 1
            self.save()

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['nombre']


class CargoEmpleadoHistorial(models.Model):
    cargo = models.ForeignKey('Cargo', on_delete=models.CASCADE, related_name='historial_empleados', verbose_name='Cargo')
    empleado = models.ForeignKey('seguridad_usuarios.Empleado', on_delete=models.CASCADE, related_name='historial_cargos', verbose_name='Empleado')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Relación')

    def __str__(self):
        return f"{self.empleado} - {self.cargo} ({self.fecha:%Y-%m-%d %H:%M})"

    class Meta:
        verbose_name = 'Historial de Cargo de Empleado'
        verbose_name_plural = 'Historiales de Cargo de Empleados'
        unique_together = ('cargo', 'empleado')


# --------------------------------------------------------------------------
# Modelo para almacenar la configuración global de apariencia
# --------------------------------------------------------------------------
class ConfiguracionApariencia(models.Model):
    THEME_DEFAULT = 'theme-default'
    THEME_DARK = 'theme-dark'
    THEME_EMERALD = 'theme-emerald'
    THEME_SUNSET = 'theme-sunset'
    THEME_OCEAN = 'theme-ocean'
    THEME_LIGHT = 'theme-light'

    THEME_CHOICES = [
        (THEME_DEFAULT, 'Azul Profesional (Defecto)'),
        (THEME_DARK, 'Modo Oscuro'),
        (THEME_EMERALD, 'Esmeralda Energético'),
        (THEME_SUNSET, 'Atardecer Cálido'),
        (THEME_OCEAN, 'Océano Profundo'),
        (THEME_LIGHT, 'Tema Luminoso'),
    ]

    FONT_ROBOTO = "'Roboto', sans-serif"
    FONT_PLAYFAIR = "'Playfair Display', serif"
    FONT_MONOSPACE = 'monospace'

    FONT_CHOICES = [
        (FONT_ROBOTO, 'Roboto'),
        (FONT_PLAYFAIR, 'Elegante (Serif)'),
        (FONT_MONOSPACE, 'Sistema (Monospace)'),
    ]

    tema = models.CharField(max_length=40, choices=THEME_CHOICES, default=THEME_DEFAULT, verbose_name='Tema')
    tipografia = models.CharField(max_length=100, choices=FONT_CHOICES, default=FONT_ROBOTO, verbose_name='Tipografía')
    tamanio = models.PositiveSmallIntegerField(default=16, verbose_name='Tamaño de texto (px)')
    actualizado_el = models.DateTimeField(auto_now=True, verbose_name='Actualizado el')

    class Meta:
        verbose_name = 'Configuración de Apariencia'
        verbose_name_plural = 'Configuraciones de Apariencia'

    def __str__(self):
        return f'{self.get_tema_display()} — {self.tamanio}px'

class Empresa(models.Model):
    """
    Modelo que representa la información de la empresa.
    """
    
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Empresa")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo de la Empresa")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_empresa')
    sucursales = models.ManyToManyField('Sucursal', blank=True, related_name='empresas', verbose_name="Sucursales")
    ruc = models.CharField(max_length=20, blank=True, null=True, verbose_name="RUC de la Empresa")
    timbrado = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de Timbrado")

    @classmethod
    def get_empresa_activa(cls):
        """Devuelve la empresa activa del sistema. Solo debe existir una."""
        return cls.objects.order_by('id').first()

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    


class Sucursal(models.Model):
    """
    Modelo que representa una sucursal de la empresa.
    Cada sucursal puede tener varias cajas, empleados y operaciones de cobranza.
    """
    empresa = models.ForeignKey('Empresa', on_delete=models.PROTECT, related_name='sucursales_registradas', null=True, blank=True, verbose_name="Empresa")
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Sucursal")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_sucursal')

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Caja(models.Model):
    """
    Modelo que representa una caja de cobro de una sucursal.
    """
    TIPO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('BANCO', 'Banco'),
        ('MIXTA', 'Mixta'),
    ]

    ESTADO_CHOICES = [
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
        ('SUSPENDIDA', 'Suspendida'),
    ]

    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='cajas', verbose_name="Sucursal")
    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Caja")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción de la Caja")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='EFECTIVO', verbose_name="Tipo")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='CERRADA', verbose_name="Estado")
    saldo_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Saldo Inicial")
    saldo_actual = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Saldo Actual")
    empleado_apertura = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_abiertas',
        verbose_name='Empleado apertura'
    )
    empleado_cierre = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_cerradas',
        verbose_name='Empleado cierre'
    )
    fecha_apertura = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Apertura")
    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Cierre")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_modifico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modificaciones_caja')

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['sucursal__nombre', 'nombre']

    def __str__(self):
        return f"{self.sucursal} - {self.nombre}"


class AperturaCaja(models.Model):
    """Registro de la apertura de una caja."""
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='aperturas')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='aperturas_caja')
    monto_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    fecha_hora = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Apertura de Caja"
        verbose_name_plural = "Aperturas de Caja"

    def __str__(self):
        return f"Apertura {self.caja} - {self.fecha_hora:%Y-%m-%d %H:%M}"


class CierreCaja(models.Model):
    """Registro del cierre de caja con arqueo."""
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='cierres')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='cierres_caja')
    monto_esperado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_real = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    diferencia = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    fecha_hora = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Cierre de Caja"
        verbose_name_plural = "Cierres de Caja"

    def __str__(self):
        return f"Cierre {self.caja} - {self.fecha_hora:%Y-%m-%d %H:%M}"


class MedioPago(models.Model):
    """Medios de pago aceptados para cobrar a clientes."""
    TIPO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('CHEQUE', 'Cheque'),
        ('OTRO', 'Otro'),
    ]

    nombre = models.CharField(max_length=60, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='EFECTIVO')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Medio de Pago"
        verbose_name_plural = "Medios de Pago"

    def __str__(self):
        return self.nombre


class Factura(models.Model):
    """Factura emitida a un cliente por una venta."""
    TIPO_CHOICES = [
        ('CONTADO', 'Contado'),
        ('CREDITO', 'Crédito'),
        ('NOTA_CREDITO', 'Nota de Crédito'),
    ]

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('COBRADA', 'Cobrada'),
        ('PARCIAL', 'Parcial'),
        ('ANULADA', 'Anulada'),
    ]

    cliente = models.ForeignKey('clientes_pedidos.Cliente', on_delete=models.PROTECT, related_name='facturas')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='facturas')
    caja = models.ForeignKey(Caja, on_delete=models.SET_NULL, null=True, blank=True, related_name='facturas')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='facturas')
    numero_factura = models.CharField(max_length=30, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='CONTADO')
    fecha_emision = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    saldo_pendiente = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        constraints = [
            models.UniqueConstraint(fields=['sucursal', 'numero_factura'], name='uniq_factura_sucursal_numero')
        ]

    def __str__(self):
        return f"{self.numero_factura} - {self.cliente}"

    def save(self, *args, **kwargs):
        if self.saldo_pendiente == 0 and self.total > 0:
            self.estado = 'COBRADA'
        elif self.saldo_pendiente > 0 and self.saldo_pendiente < self.total:
            self.estado = 'PARCIAL'
        super().save(*args, **kwargs)


class Cobro(models.Model):
    """Cobro realizado por un cliente de una factura en una caja determinada."""
    ESTADO_CHOICES = [
        ('COBRADO', 'Cobrado'),
        ('PENDIENTE', 'Pendiente'),
        ('ANULADO', 'Anulado'),
    ]

    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name='cobros')
    cliente = models.ForeignKey('clientes_pedidos.Cliente', on_delete=models.PROTECT, related_name='cobros')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='cobros')
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='cobros')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='cobros')
    medio_pago = models.ForeignKey(MedioPago, on_delete=models.PROTECT, related_name='cobros')
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    cambio = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    referencia = models.CharField(max_length=100, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='COBRADO')
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Cobro"
        verbose_name_plural = "Cobros"

    def __str__(self):
        return f"Cobro {self.id} - {self.factura.numero_factura}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.estado == 'COBRADO':
            acumulado = self.factura.cobros.filter(estado='COBRADO').aggregate(total=models.Sum('monto'))['total'] or 0
            self.factura.saldo_pendiente = max(self.factura.total - acumulado, 0)
            self.factura.save(update_fields=['saldo_pendiente', 'estado'])


class MovimientoCaja(models.Model):
    """Movimiento de entrada/salida asociado a una caja."""
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
        ('AJUSTE', 'Ajuste'),
        ('APERTURA', 'Apertura'),
        ('CIERRE', 'Cierre'),
    ]

    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='movimientos')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='movimientos_caja')
    cobro = models.ForeignKey(Cobro, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos')
    factura = models.ForeignKey(Factura, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    concepto = models.CharField(max_length=150)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_hora = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"

    def __str__(self):
        return f"{self.caja} - {self.tipo} - {self.monto}"
