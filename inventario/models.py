# inventario/models.py

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import uuid
import re

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from configuraciones_maestras.models import Proveedor, Moneda
from colorfield.fields import ColorField
from core.models import EstadoMixin, TimeStampedModel, Moneda as MonedaFacade, TransicionInvalida



def es_vin_valido(vin):
    """
    Valida un número VIN de 17 caracteres según el estándar ISO 3779.
    """
    # 1. Verificar longitud
    if len(vin) != 17:
        return False
    
    # 2. Convertir a mayúsculas
    vin = vin.upper()
    
    # 3. Verificar caracteres prohibidos (I, O, Q)
    if re.search(r'[IOQ]', vin):
        return False
    
    # 4. Verificar caracteres alfanuméricos
    if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
        return False
        
    # Nota: El cálculo del dígito verificador (caracter 9) es un proceso
    # matemático complejo que varía según el mercado (ej. América del Norte).
    # Esta validación cubre el formato, que es lo más común en registros.
    return True

def validar_vin(value):
    if not es_vin_valido(value):
        raise ValidationError('El número de chasis (VIN) no es válido.')
# --------------------------------------------------------------------------
# Modelo para representar la Unidad de Medida de los repuestos
# --------------------------------------------------------------------------
class UnidadMedida(models.Model):
    """
    Modelo para definir las unidades de medida de los repuestos.
    Ej: 'Unidad', 'Litro', 'Caja', 'Metro'.
    """
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre de la Unidad")
    abreviatura = models.CharField(max_length=10, unique=True, verbose_name="Abreviatura")

    class Meta:
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nombre']

    def eliminable(self):
        return not self.repuesto_set.exists()  # Solo se puede eliminar si no tiene repuestos asociados
    
    def activar(self):
        self.estado = True
        self.save()
    
    def inactivar(self):
        self.estado = False
        self.save()
    
    def esta_activo(self):
        return self.estado

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"
    
# modelo deposito
class Deposito(models.Model):
    """
    Modelo que representa un depósito o almacén donde se guardan los vehículos y repuestos.
    """
    codigo = models.CharField(max_length=20, unique=True, blank=True, default='', verbose_name='Código del Depósito')
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Depósito")
    direccion = models.CharField(max_length=255, blank=True, default='', verbose_name='Dirección')
    ubicacion = models.CharField(max_length=255, verbose_name="Ubicación del Depósito")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    capacidad_maxima = models.PositiveIntegerField(default=0, verbose_name="Capacidad Máxima (unidades)")
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True,verbose_name="Fecha de Creación")
    activo = models.BooleanField(default=True, verbose_name='Activo')
    es_principal = models.BooleanField(default=False, verbose_name='Depósito principal')

    class Meta:
        verbose_name = "Depósito"
        verbose_name_plural = "Depósitos"
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['es_principal'], condition=Q(es_principal=True), name='uniq_deposito_principal'),
        ]

    def eliminarable(self):
        return not self.vehiculos.exists() and not self.repuesto_set.exists()  # Solo se puede eliminar si no tiene vehículos ni repuestos asociados

    @classmethod
    def principal(cls):
        """Depósito principal del sistema (se crea si todavía no existe)."""
        from inventario.services import deposito_principal
        return deposito_principal()

    def activar(self):
        self.activo = True
        self.save()

    def inactivar(self):
        self.activo = False
        self.save()

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or '').strip().upper()
        if self.es_principal:
            existing = Deposito.objects.filter(es_principal=True).exclude(pk=self.pk).exists()
            if existing:
                raise ValidationError('Solo puede existir un depósito principal activo.')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class MovimientoStock(TimeStampedModel):
    """
    Registra cada movimiento del stock físico de un repuesto.

    Convención de la casa: la **cantidad siempre es positiva**. La dirección
    del movimiento la indican los depósitos:

    - `deposito_destino` informado → el stock **entra** a ese depósito.
    - `deposito_origen` informado → el stock **sale** de ese depósito.
    - `AJUSTE` informa solo uno de los dos, según el signo de la diferencia.

    Es lo que permite el constraint `movimiento_signo_coherente_con_tipo`
    (`cantidad > 0`).
    """

    class Tipo(models.TextChoices):
        # Dirección que implica cada tipo (ver la convención del docstring):
        #   entrada  -> ENTRADA, ENTRADA_COMPRA, TRANSFERENCIA_ENTRADA
        #   salida   -> SALIDA, SALIDA_VENTA, TRANSFERENCIA_SALIDA
        #   sin dirección -> RESERVA, LIBERA (reservas sobre `stock_actual`)
        #   según el caso -> AJUSTE, TRANSFERENCIA
        ENTRADA = 'ENTRADA', 'Entrada'
        SALIDA = 'SALIDA', 'Salida'
        RESERVA = 'RESERVA', 'Reserva'
        LIBERA = 'LIBERA', 'Liberación de reserva'
        AJUSTE = 'AJUSTE', 'Ajuste'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'
        ENTRADA_COMPRA = 'ENTRADA_COMPRA', 'Entrada por compra / importación'
        SALIDA_VENTA = 'SALIDA_VENTA', 'Salida por venta'
        TRANSFERENCIA_SALIDA = 'TRANSFERENCIA_SALIDA', 'Transferencia (sale)'
        TRANSFERENCIA_ENTRADA = 'TRANSFERENCIA_ENTRADA', 'Transferencia (entra)'

    TIPO_CHOICES = Tipo.choices

    repuesto = models.ForeignKey('Repuesto', on_delete=models.CASCADE, related_name='movimientos_stock')
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES)
    cantidad = models.IntegerField(
        default=0,
        help_text=(
            'Siempre positiva. La dirección la dan los depósitos: '
            '`deposito_destino` (entrada) y `deposito_origen` (salida).'
        ),
    )
    motivo = models.CharField(max_length=255, blank=True, default='')
    deposito_origen = models.ForeignKey('Deposito', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_origen')
    deposito_destino = models.ForeignKey('Deposito', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_destino')
    referencia = models.CharField(max_length=100, blank=True, default='')
    costo_unitario = models.DecimalField('Costo unitario (moneda base)', max_digits=14, decimal_places=4, null=True, blank=True)
    saldo_posterior = models.PositiveIntegerField('Físico del depósito después del movimiento', null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    grupo = models.UUIDField(null=True, blank=True, db_index=True, help_text='Une las dos patas de una transferencia.')
    embarque_item = models.ForeignKey('importaciones.EmbarqueItem', null=True, blank=True, on_delete=models.PROTECT, related_name='movimientos_stock')
    venta = models.ForeignKey('ventas.Venta', null=True, blank=True, on_delete=models.PROTECT, related_name='movimientos_stock')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'Movimiento de stock'
        verbose_name_plural = 'Movimientos de stock'
        constraints = [
            models.CheckConstraint(
                condition=Q(cantidad__gt=0),
                name='movimiento_signo_coherente_con_tipo',
            ),
        ]

    def __str__(self):
        return f'{self.repuesto} · {self.get_tipo_display()} · {self.cantidad}'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Los movimientos de stock no se pueden modificar.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Los movimientos de stock no se pueden borrar.')


class StockRepuesto(TimeStampedModel):
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.PROTECT, related_name='stocks')
    deposito = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='stocks')
    cantidad = models.PositiveIntegerField('Físico', default=0, editable=False)
    reservado = models.PositiveIntegerField(default=0, editable=False)
    ubicacion = models.CharField('Ubicación (pasillo/estante)', max_length=40, blank=True)

    class Meta:
        ordering = ['repuesto__codigo_repuesto', 'deposito__codigo']
        verbose_name = 'stock de repuesto'
        verbose_name_plural = 'stocks de repuestos'
        constraints = [
            models.UniqueConstraint(fields=['repuesto', 'deposito'], name='uniq_stock_repuesto_deposito'),
            models.CheckConstraint(condition=Q(reservado__lte=F('cantidad')), name='stock_reservado_no_excede'),
        ]

    def __str__(self):
        return f'{self.repuesto.codigo_repuesto} @ {self.deposito.codigo}: {self.cantidad} ({self.reservado} reservadas)'

    @property
    def disponible(self):
        return self.cantidad - self.reservado


class ReservaStock(TimeStampedModel):
    venta_item = models.ForeignKey('ventas.VentaItem', on_delete=models.PROTECT, related_name='reservas_stock')
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.PROTECT, related_name='reservas')
    deposito = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='reservas')
    cantidad = models.PositiveIntegerField(help_text='Unidades reservadas originalmente.')
    consumida = models.PositiveIntegerField(default=0, help_text='Ya entregadas (salieron del stock).')
    liberada = models.PositiveIntegerField(default=0, help_text='Devueltas al disponible (venta anulada).')

    class Meta:
        ordering = ['id']
        constraints = [
            models.CheckConstraint(condition=Q(cantidad__gte=1), name='reserva_cantidad_positiva'),
            models.CheckConstraint(condition=Q(cantidad__gte=F('consumida') + F('liberada')), name='reserva_consumida_mas_liberada_no_excede'),
        ]

    def __str__(self):
        return f'Reserva {self.cantidad} · {self.repuesto.codigo_repuesto} @ {self.deposito.codigo}'

    @property
    def pendiente(self):
        return self.cantidad - self.consumida - self.liberada

    @property
    def activa(self):
        return self.pendiente > 0


class MarcaVehiculo(models.Model):
    """
    Modelo para representar las marcas de vehículos.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Marca")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo
    pais_origen = models.CharField(max_length=100, blank=True, null=True, verbose_name="País de Origen", default='Korea del Sur')
    

    def eliminable(self):
        return not self.modelos.exists()  # Solo se puede eliminar si no tiene modelos asociados
    
    def activar(self):
        self.estado = True
        self.save()
    
    def inactivar(self):
        self.estado = False
        self.save()

    def esta_activo(self):
        return self.estado
    
    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class TipoVehiculo(models.Model):
    """
    Modelo para representar los tipos de vehículos.
    Ej: 'Sedán', 'SUV', 'Hatchback', etc.
    """
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Tipo de Vehículo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo

    def eliminable(self):
        return not self.modelos.exists()  # Solo se puede eliminar si no tiene modelos asociados
    
    def activar(self):
        self.estado = True
        self.save()
    
    def inactivar(self):
        self.estado = False
        self.save()
    
    def esta_activo(self):
        return self.estado
    
    class Meta:
        verbose_name = "Tipo de Vehículo"
        verbose_name_plural = "Tipos de Vehículos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    

class ModeloVehiculo(models.Model):
    """
    Modelo para representar los modelos de vehículos.
    """
    marca = models.ForeignKey(MarcaVehiculo, on_delete=models.CASCADE, related_name='modelos', verbose_name="Marca del Vehículo")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Modelo")
    tipo_vehiculo = models.ForeignKey(TipoVehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='modelos', verbose_name="Tipo de Vehículo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo

    def eliminable(self):
        return not self.vehiculos.exists()  # Solo se puede eliminar si no tiene vehículos asociados
    
    def activar(self):
        self.estado = True
        self.save()
    
    def inactivar(self):
        self.estado = False
        self.save()
    
    def esta_activo(self):
        return self.estado

    class Meta:
        verbose_name = "Modelo de Vehículo"
        verbose_name_plural = "Modelos de Vehículos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.marca.nombre} {self.nombre}"
    
class TipoTransmision(models.Model):
    """
    Modelo para representar los tipos de transmisión de los vehículos.
    Ej: 'Manual', 'Automática', 'CVT', etc.
    """
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Tipo de Transmisión")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo

    def eliminable(self):
        return not self.vehiculos.exists()  # Solo se puede eliminar si no tiene vehículos asociados
    
    def activar(self):
        self.estado = True
        self.save()
    
    def inactivar(self):
        self.estado = False
        self.save()
    
    def esta_activo(self):
        return self.estado

    class Meta:
        verbose_name = "Tipo de Transmisión"
        verbose_name_plural = "Tipos de Transmisión"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# --------------------------------------------------------------------------
# Modelo para representar un producto en el inventario
# --------------------------------------------------------------------------
class Producto(models.Model):
    """
    Modelo que representa un producto genérico en el inventario.
    Puede ser un vehículo o un repuesto.
    """
    TIPO_PRODUCTO = (
        ('vehiculo', 'Vehículo'),
        ('repuesto', 'Repuesto'),
    )
    
    moneda_venta = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda de Venta")
    tipo = models.CharField(max_length=20, null=True, blank=True, choices=TIPO_PRODUCTO, verbose_name="Tipo de Producto")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    fecha_ingreso = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Fecha de Ingreso al Inventario")
    costo_compra = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo de Compra (Guaraníes)")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta Sugerido") 
    # ubicacion del deposito
    ubicacion = models.ForeignKey(Deposito, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Depósito de Ubicación")
    fecha_compra = models.DateField(blank=True, null=True, verbose_name="Fecha de Compra")
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Imagen del Producto")
    moneda_compra_proveedor = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda de Compra del Proveedor")
    costo_compra_provedor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Costo de Compra del Proveedor Total")
    costo_unitario_proveedor = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Costo Unitario del Proveedor")
    costo_flete1 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Costo de Flete 1")
    moneda_flete1 = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda del Flete 1")
    costo_aduana_extrangera = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Costo de Aduana Extranjera")
    moneda_aduana_extrangera = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda de Aduana Extranjera")
    costo_extra = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Costo Extra")
    descripcion_costo_extra = models.TextField(blank=True, null=True, verbose_name="Descripción del Costo Extra")
    moneda_costo_extra = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda del Costo Extra")
    costo_aduana_paraguaya = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Costo de Aduana Paraguaya")
    moneda_costo_aduana_paraguaya = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda de Aduana Paraguaya")
    costo_flete2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Costo de Flete 2")
    moneda_costo_flete2 = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda del Flete 2")
    costo_total_importacion = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Costo Total de Importación")
    moneda_costo_total_importacion = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name="Moneda del Costo Total de Importación")

    def _convertir_a_usd(self, monto, moneda):
        if monto in (None, ''):
            return Decimal('0.00')
        monto = Decimal(str(monto))
        if moneda and getattr(moneda, 'codigo', None) == 'USD':
            return monto
        if moneda and getattr(moneda, 'codigo', None) == 'PYG' and self.tasa_aplicada:
            return monto / Decimal(str(self.tasa_aplicada))
        return monto

    def actualizar_costos_importacion(self):
        total_usd = Decimal('0.00')
        costos = [
            self.costo_compra_provedor_total,
            self.costo_flete1,
            self.costo_aduana_extrangera,
            self.costo_extra,
            self.costo_aduana_paraguaya,
            self.costo_flete2,
        ]
        monedas = [
            self.moneda_compra_proveedor,
            self.moneda_flete1,
            self.moneda_aduana_extrangera,
            self.moneda_costo_extra,
            self.moneda_costo_aduana_paraguaya,
            self.moneda_costo_flete2,
        ]
        for monto, moneda in zip(costos, monedas):
            total_usd += self._convertir_a_usd(monto, moneda)

        self.costo_total_importacion = total_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if self.moneda_costo_total_importacion_id is None:
            moneda_usd = Moneda.objects.filter(codigo='USD').first()
            if moneda_usd:
                self.moneda_costo_total_importacion = moneda_usd

        if self.tasa_aplicada and self.costo_total_importacion:
            self.costo_compra = (self.costo_total_importacion * Decimal(str(self.tasa_aplicada))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif self.costo_compra in (None, ''):
            self.costo_compra = self.costo_total_importacion

    def get_tipo_display(self):
        return dict(self.TIPO_PRODUCTO).get(self.tipo, 'Desconocido')
    
    def es_vehiculo(self):
        return self.tipo == 'vehiculo'
    
    def es_repuesto(self):
        return self.tipo == 'repuesto'
    
    def moneda_producto(self):
        pass

    def costo_unitario_producto(self):
        pass
    
    def cantidad_producto(self):
        pass

    def save(self, *args, **kwargs):
        MonedaFacade.ensure_defaults()

        if self.moneda_venta_id is None:
            self.moneda_venta = Moneda.objects.filter(codigo='PYG').first() or MonedaFacade.agregar('PYG', 'Guaraní Paraguayo')

        if self.moneda_compra_proveedor_id is None:
            self.moneda_compra_proveedor = Moneda.objects.filter(codigo='USD').first() or MonedaFacade.agregar('USD', 'Dólar Estadounidense')

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_ingreso']
        abstract = True

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

# --------------------------------------------------------------------------
# Modelo para representar un Vehículo en el inventario
# --------------------------------------------------------------------------
class Vehiculo(Producto, EstadoMixin):
    """
    Modelo que representa un vehículo en el inventario.

    La fuente de verdad del ciclo de estados se centraliza aquí para que
    importaciones, ventas y cualquier otra app usen la misma API de transición.
    """
    ESTADO_VEHICULO = (
        # Estados posibles de un vehículo antes de la venta
        ('pendiente_importacion', 'Pendiente de Importación'),
        ('elegible_importacion', 'Elegible para Importación'),
        # Seleccionado para importación, pero aún no ha sido importado
        ('en_importacion', 'En Proceso de Importación'),
        # Estados posibles de un vehículo en el inventario
        ('disponible', 'Disponible'),
        ('vendido', 'Vendido'),
        ('mantenimiento', 'En Mantenimiento'),
        ('reservado', 'Reservado'),
        ('busqueda_cancelada', 'Búsqueda Cancelada'),
        ('busqueda_rechazada', 'Búsqueda Rechazada'),
        # no disponible, robo, accidente, etc.
        ('no_disponible', 'No Disponible'),
    )

    TRANSICIONES = {
        'pendiente_importacion': ('elegible_importacion', 'busqueda_cancelada'),
        'elegible_importacion': ('en_importacion', 'busqueda_cancelada', 'busqueda_rechazada'),
        'en_importacion': ('disponible', 'busqueda_cancelada', 'no_disponible'),
        'disponible': ('reservado', 'vendido', 'mantenimiento', 'no_disponible'),
        'reservado': ('disponible', 'vendido', 'no_disponible'),
        'vendido': (),
        'mantenimiento': ('disponible',),
        'busqueda_cancelada': (),
        'busqueda_rechazada': ('elegible_importacion',),
        'no_disponible': ('disponible',),
    }

    @classmethod
    def estado_desde_embarque(cls, estado_embarque):
        mapping = {
            'PROGRAMADO': 'elegible_importacion',
            'EMBARCADO': 'en_importacion',
            'EN_TRANSITO': 'en_importacion',
            'ARRIBADO': 'en_importacion',
            'EN_ADUANA': 'en_importacion',
            'NACIONALIZADO': 'disponible',
            'RECIBIDO': 'disponible',
            'CERRADO': 'disponible',
            'CANCELADO': 'busqueda_cancelada',
        }
        return mapping.get(str(estado_embarque).upper())
    TIPO_COMBUSTIBLE = (
        ('nafta', 'Nafta'),
        ('diesel', 'Diésel'),
        ('electrico', 'Eléctrico'),
        ('hibrido', 'Híbrido'),
        ('otro', 'Otro'),
    )
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos', verbose_name="Proveedor")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Vehículo")
    marca = models.ForeignKey(MarcaVehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos', verbose_name="Marca del Vehículo")
    modelo = models.ForeignKey(ModeloVehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos', verbose_name="Modelo del Vehículo")
    año = models.PositiveIntegerField(verbose_name="Año de Fabricación")
    nro_motor = models.CharField("Nº de motor", max_length=40, blank=True)
    cilindrada_cc = models.PositiveIntegerField("Cilindrada (cc)", null=True, blank=True)
    kilometraje = models.PositiveIntegerField(default=0, verbose_name="Kilometraje")
    codigo_chasis = models.CharField(max_length=17, unique=True, verbose_name="Código de Chasis (VIN)", validators=[validar_vin])
    estado = models.CharField(max_length=25, choices=ESTADO_VEHICULO, default='disponible', verbose_name="Estado")
    costo_compra = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo de Compra (Guaraníes)")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta Sugerido")
    fecha_ingreso = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Fecha de Ingreso al Inventario")
    color = ColorField(default='#FFFFFF', verbose_name="Color del Vehículo", blank=True, null=True, help_text="Selecciona el color del vehículo")
    combustible = models.CharField(max_length=50, blank=True, null=True, choices=TIPO_COMBUSTIBLE, verbose_name="Tipo de Combustible", default='gasolina')
    transmision = models.ForeignKey(TipoTransmision, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos', verbose_name="Tipo de Transmisión")
    
    precio_cif_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio CIF (USD)")
    precio_cif_guarani = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio CIF (Guaranies)")
    tasa_aplicada = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, verbose_name="Tasa de Cambio Aplicada")
    tasa_cambio = models.ForeignKey('configuraciones_maestras.TasaCambio', on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos', verbose_name="Tasa de Cambio Aplicada")
    imagen = models.ImageField(upload_to='vehiculos/', blank=True, null=True, verbose_name="Imagen del Vehiculo", default='vehiculos/default_vehicle.png')
    cantidad_a_comprar = models.PositiveIntegerField(default=1, blank=True, null=True, verbose_name="Cantidad a Comprar")

    volante_a_la_derecha = models.BooleanField(
            "Volante a la derecha",
            default=False,
            help_text="Relevante para la habilitación al importar.",
        )
    observaciones = models.TextField(blank=True)

    costo_fob = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, editable=False)
    costo_total = models.DecimalField(
        "Costo landed",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
    )
    precio_lista = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    
    def moneda_producto(self):
        if self.estado == 'disponible' or self.estado == 'vendido' or self.estado == 'mantenimiento' or self.estado == 'reservado':
            return self.moneda_venta
        else:
            return self.moneda_compra_proveedor
            
    
    def costo_unitario_producto(self):
        if self.estado == 'disponible' or self.estado == 'vendido' or self.estado == 'mantenimiento' or self.estado == 'reservado':
            return self.precio_venta
        else:
            return self.costo_unitario_proveedor
    
    def cantidad_producto(self):
        return 1  # Cada vehículo es único, por lo que la cantidad siempre es 1
    
    def formar_nombre_completo(self):
        if not self.marca or not self.modelo:
            return
        if not self.nombre or not self.nombre.strip():
            self.nombre = f"{self.marca.nombre} {self.modelo.nombre} ({self.año})"
    
    def dar_de_baja(self):
        """
        Marca el vehículo como no disponible.
        Solo aplica para vehículos.
        """
        if self.es_vehiculo():
            self.estado = 'no_disponible'
            self.save()
        else:
            raise ValidationError('Solo se puede dar de baja a un vehículo.')
        
    def registrar_tasa_cambio(self, tasa):
        """
        Registra la tasa de cambio aplicada al vehículo.
        """
        self.tasa_aplicada = tasa.valor
        self.tasa_cambio = tasa
        self.save()

    def iniciar_importacion(self):
        """
        Inicia el proceso de importación del vehículo.
        """
        pass

    def reservar(self):
        """
        Marca el vehículo como reservado.
        Solo aplica para vehículos.
        """
        if self.es_vehiculo():
            self.estado = 'reservado'
            self.save()
        else:
            raise ValidationError('Solo se puede reservar un vehículo.')

    def vender_producto(self):
        """
        Marca el producto como vendido.
        Solo aplica para vehículos.
        """
        if self.es_vehiculo():
            self.estado = 'vendido'
            self.save()
        else:
            raise ValidationError('Solo se puede marcar como vendido un vehículo.')

    def save(self, *args, **kwargs):
        self.formar_nombre_completo()
        self.actualizar_costos_importacion()
        super().save(*args, **kwargs)

    class Meta:
        
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['-fecha_ingreso']
        #indexes estado
        indexes = [
            models.Index(fields=['estado'], name='idx_estado_vehiculo'),]
        constraints = [
                    models.CheckConstraint(condition=Q(año__gte=1900), name="vehiculo_anio_minimo"),
                    models.CheckConstraint(
                        condition=Q(precio_lista__isnull=True) | Q(precio_lista__gte=0),
                        name="vehiculo_precio_no_negativo",
                    ),
                ]
    
    def __str__(self):
        return f"{self.modelo} ({self.año})"

    def save(self, *args, **kwargs):
        self.formar_nombre_completo()
        self.codigo_chasis = re.sub(r"[\s\-]", "", self.codigo_chasis or "").upper()
        self.actualizar_costos_importacion()
        super().save(*args, **kwargs)

    @property
    def margen_estimado(self):
        if self.precio_venta is None or self.costo_total_importacion is None:
            return None
        return self.precio_venta - self.costo_total_importacion

    @property
    def margen_porcentaje(self):
        margen = self.margen_estimado
        if margen is None or not self.precio_venta:
            return None
        return (margen / self.precio_venta * 100).quantize(Decimal("0.1"))

    @property
    def disponible_para_venta(self) -> bool:
        return self.estado == 'disponible'

    def validar_reservado(self):
        if self.precio_venta is None:
            raise TransicionInvalida("Defina el precio de venta antes de reservar el vehículo.")

    def validar_vendido(self):
        if self.costo_total_importacion is None:
            raise TransicionInvalida(
                "El vehículo no tiene costo total de importación: complete los costos antes de venderlo."
            )

# --------------------------------------------------------------------------
# Modelo para representar un Repuesto en el inventario
# --------------------------------------------------------------------------
class Repuesto(Producto):
    """
    Modelo que representa un repuesto en el inventario.
    """
    ESTADO_REPUESTO = (
        ('elegible_importacion', 'Elegible para Importación'),
        ('en_importacion', 'En Proceso de Importación'),
        ('disponible', 'Disponible'),
        ('vendido', 'Vendido'),
        ('no_disponible', 'No Disponible'),
    )

    nombre = models.CharField(max_length=200, verbose_name="Nombre del Repuesto")
    estado = models.CharField(max_length=25, choices=ESTADO_REPUESTO, default='elegible_importacion', verbose_name='Estado')
    cantidad_a_comprar = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="Cantidad a Comprar")
    moneda_del_costo_unitario = models.CharField(max_length=10, choices=(('PYG', 'Guaraníes'), ('USD', 'Dólares')), default='USD', verbose_name="Moneda del Costo Unitario")
    codigo_repuesto = models.CharField(max_length=50, unique=True, verbose_name="Código del Repuesto")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unidad de Medida")
    stock_actual = models.PositiveIntegerField(default=0, verbose_name="Stock Actual")
    stock_reservado = models.PositiveIntegerField(default=0, verbose_name="Stock Reservado por Pedidos")
    stock_minimo = models.PositiveIntegerField(default=0, verbose_name="Stock Minimo")
    costo_compra = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo de Compra (Guaranies)")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta Sugerido")
    fecha_ultima_entrada = models.DateTimeField(auto_now=True, verbose_name="Fecha de Ultima Entrada")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripcion Adicional")
    categoria = models.ForeignKey('CategoriaRepuesto', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría del Repuesto", default=None)
    compatibilidad = models.CharField(max_length=200, blank=True, null=True, verbose_name="Compatibilidad (Modelos/Marcas)")
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Costo Unitario (Guaranies)", default=0)
    tasa_aplicada = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, verbose_name="Tasa de Cambio Aplicada")
    tasa_cambio = models.ForeignKey('configuraciones_maestras.TasaCambio', on_delete=models.SET_NULL, null=True, blank=True, related_name='repuestos', verbose_name="Tasa de Cambio Aplicada")
    imagen = models.ImageField(upload_to='repuestos/', blank=True, null=True, verbose_name="Imagen del Repuesto", default='repuestos/default_repuesto.png')
    
    def cantidad_producto(self):
        if self.estado == 'disponible' or self.estado == 'vendido':
            return 1
        else:
            return self.cantidad_a_comprar

    def moneda_producto(self):
        if self.estado == 'disponible' or self.estado == 'vendido':
            return self.moneda_venta
        else:
            return self.moneda_compra_proveedor
        
    def costo_unitario_producto(self):
        if self.estado == 'disponible' or self.estado == 'vendido':
            return self.precio_venta
        else:
            return self.costo_unitario_proveedor

    def costo_unitario_en_guaranies_proveedor(self):
        """
        Retorna el costo unitario en guaraníes, calculado si es necesario.
        """
        if self.moneda_compra_proveedor == 'USD' and self.tasa_aplicada:
            return self.costo_unitario_proveedor * self.tasa_aplicada
        if self.costo_unitario_proveedor and self.tasa_aplicada:
            return self.costo_unitario_proveedor * self.tasa_aplicada
        return self.costo_unitario_proveedor

    def tasa_cambio_aplicada_moneda(self, tasa_cambio):
        """
        Busca la tasa de cambio aplicada al repuesto.
        """
        self.tasa_aplicada = tasa_cambio.valor
        self.tasa_cambio = tasa_cambio
    
    def reabastecer_stock(self, cantidad):
        """Aumenta el stock actual del repuesto"""
        self.stock_actual += cantidad
        self.save(update_fields=['stock_actual'])

    def crear_pedido_abastecimiento(self, cantidad, descripcion=None, cliente=None):
        """Crea un pedido de abastecimiento para el repuesto cuando su stock está bajo."""
        from clientes_pedidos.models import Pedido, ItemPedido
        from clientes_pedidos.models import Cliente

        if cantidad <= 0:
            raise ValidationError('La cantidad a pedir debe ser mayor que cero.')
        if self.stock_actual > self.stock_minimo:
            raise ValidationError('Solo se pueden solicitar abastecimientos para repuestos con stock bajo.')

        pedido_activo = Pedido.objects.filter(
            tipo='abastecimiento',
            repuesto_a_abastecer=self,
        ).exclude(estado__in=['completado', 'cancelado', 'rechazado']).first()
        if pedido_activo:
            raise ValidationError('Ya existe un pedido de abastecimiento activo para este repuesto.')

        if cliente is None:
            cliente = Cliente.objects.order_by('id').first()
        if cliente is None:
            raise ValidationError('No existe un cliente para asociar el pedido de abastecimiento.')

        pedido = Pedido.objects.create(
            cliente=cliente,
            tipo='abastecimiento',
            estado='busqueda_abastecimiento',
            observaciones=descripcion or f'Abastecimiento solicitado para {self.nombre}',
            repuesto_a_abastecer=self,
        )

        precio_unitario = Decimal(str(self.costo_compra or '0'))
        subtotal = Decimal(str(cantidad)) * precio_unitario
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=self,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
        )

        self.estado = 'pendiente_importacion'
        self.save(update_fields=['estado'])

        pedido.monto_total = pedido.calcular_monto_total()
        pedido.iva = pedido.calcular_iva()
        pedido.save(update_fields=['monto_total', 'iva'])
        return pedido
        
    
    @property
    def stock_disponible(self):
        """Calcula el stock disponible (sin las reservas de pedidos)"""
        return max(0, self.stock_actual - self.stock_reservado)
    
    def puede_reservar(self, cantidad):
        """Verifica si hay suficiente stock disponible para reservar"""
        return self.stock_disponible >= cantidad
    
    def reservar_stock(self, cantidad):
        """Reserva stock para un pedido de venta."""
        from inventario.services import reservar_unidades
        movimiento = reservar_unidades(self, cantidad)
        self.refresh_from_db(fields=['stock_actual', 'stock_reservado'])
        return movimiento

    def liberar_reserva(self, cantidad):
        """Libera stock reservado (por cancelación de pedido)"""
        from inventario.services import liberar_unidades
        movimiento = liberar_unidades(self, cantidad)
        self.refresh_from_db(fields=['stock_actual', 'stock_reservado'])
        return movimiento

    def confirmar_venta(self, cantidad):
        """Confirma la venta: reduce stock_actual y stock_reservado"""
        from inventario.services import confirmar_venta, deposito_principal
        movimiento = confirmar_venta(
            self,
            cantidad,
            deposito=deposito_principal(),
            motivo='Confirmación de venta',
        )
        self.refresh_from_db(fields=['stock_actual', 'stock_reservado'])
        return movimiento

    def registrar_entrada(self, cantidad, motivo='Entrada de stock', deposito=None, referencia=''):
        from inventario.services import deposito_principal, registrar_entrada
        movimiento = registrar_entrada(
            self,
            cantidad,
            costo_unitario=self.costo_unitario or self.costo_compra or Decimal('0.00'),
            tipo=MovimientoStock.Tipo.ENTRADA,
            deposito=deposito or deposito_principal(),
            motivo=motivo,
            referencia=referencia,
        )
        self.refresh_from_db(fields=['stock_actual', 'stock_reservado', 'costo_unitario', 'costo_compra'])
        return movimiento

    def registrar_salida(self, cantidad, motivo='Salida de stock', deposito=None, referencia=''):
        from inventario.services import deposito_principal, registrar_salida
        movimiento = registrar_salida(
            self,
            cantidad,
            deposito=deposito or deposito_principal(),
            motivo=motivo,
            referencia=referencia,
        )
        self.refresh_from_db(fields=['stock_actual', 'stock_reservado'])
        return movimiento

    def ajustar_stock(self, cantidad, motivo='Ajuste de stock', deposito=None, referencia=''):
        """Ajusta el stock en la cantidad informada (positiva suma, resta si es negativa)."""
        from inventario.services import ajustar_stock, deposito_principal
        deposito = deposito or deposito_principal()
        cantidad_real = max(0, int(self.stock_actual) + int(cantidad))
        movimiento = ajustar_stock(
            self,
            cantidad_real,
            motivo=motivo,
            deposito=deposito,
            referencia=referencia,
        )
        self.refresh_from_db(fields=['stock_actual', 'stock_reservado'])
        return movimiento

    def transferir_stock(self, cantidad, deposito_origen=None, deposito_destino=None, motivo='Transferencia de stock', referencia=''):
        from inventario.services import deposito_principal, transferir
        principal = deposito_principal()
        origen = deposito_origen or principal
        destino = deposito_destino or principal
        movimientos = transferir(
            self,
            cantidad,
            deposito_origen=origen,
            deposito_destino=destino,
            motivo=motivo,
            referencia=referencia,
        )
        self.refresh_from_db(fields=['stock_actual', 'stock_reservado'])
        return movimientos

    def save(self, *args, **kwargs):
        try:
            costo_unitario = Decimal(str(self.costo_unitario_proveedor)) if self.costo_unitario_proveedor not in (None, '') else None
        except (InvalidOperation, ValueError):
            costo_unitario = None

        if costo_unitario is not None:
            cantidad = Decimal(str(self.cantidad_a_comprar or 0))
            total = costo_unitario * cantidad
            try:
                self.costo_compra_provedor_total = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except (InvalidOperation, ValueError):
                self.costo_compra_provedor_total = total
        elif self.costo_compra_provedor_total in (None, ''):
            self.costo_compra_provedor_total = None

        self.actualizar_costos_importacion()
        super().save(*args, **kwargs)

    def disminuir_stock(self, cantidad):
        """
        Disminuye el stock del producto en la cantidad especificada.
        Solo aplica para repuestos.
        """
        if self.es_repuesto():
            if self.stock_actual >= cantidad:
                self.stock_actual -= cantidad
                self.save()
            else:
                raise ValidationError('No hay suficiente stock para disminuir.')
        else:
            raise ValidationError('Solo se puede disminuir stock de repuestos.')

    def aumentar_stock(self, cantidad):
        """
        Aumenta el stock del producto en la cantidad especificada.
        Solo aplica para repuestos.
        """
        if self.es_repuesto():
            self.stock_actual += cantidad
            self.save()
        else:
            raise ValidationError('Solo se puede aumentar stock de repuestos.')
       
    def registrar_tasa_cambio(self, tasa):
        """
        Registra la tasa de cambio aplicada al repuesto.
        """
        self.tasa_aplicada = tasa.valor
        self.tasa_cambio = tasa
        self.save()

    class Meta:
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo_repuesto})"


class CategoriaRepuesto(models.Model):
    """
    Modelo para representar las categorías de repuestos.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")
    estado = models.BooleanField(default=True, verbose_name="Estado")  # True para activo, False para inactivo

    def eliminable(self):
        return not self.repuesto_set.exists()  # Solo se puede eliminar si no tiene repuestos asociados
    
    def activar(self):
        self.estado = True
        self.save()
    
    def inactivar(self):
        self.estado = False
        self.save()
    
    def esta_activo(self):
        return self.estado

    class Meta:
        verbose_name = "Categoría de Repuesto"
        verbose_name_plural = "Categorías de Repuestos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre



# --------------------------------------------------------------------------
# Modelo para registrar el mantenimiento de un vehículo
# --------------------------------------------------------------------------
class MantenimientoVehiculo(EstadoMixin, models.Model):
    """
    Registro de una orden de trabajo del taller.

    El ciclo de vida va por `EstadoMixin`: `pendiente` → `en_proceso` →
    `finalizado` (o `cancelado` desde los dos primeros).

    El costo está **separado** entre mano de obra y repuestos, y el total
    (`costo`) se calcula solo. Los repuestos utilizados tienen cantidad real
    (tabla `MantenimientoRepuesto`) y, al finalizar el mantenimiento,
    descuentan del stock del depósito.
    """

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_PROCESO = 'en_proceso', 'En proceso'
        FINALIZADO = 'finalizado', 'Finalizado'
        CANCELADO = 'cancelado', 'Cancelado'

    TRANSICIONES = {
        Estado.PENDIENTE: (Estado.EN_PROCESO, Estado.CANCELADO),
        Estado.EN_PROCESO: (Estado.FINALIZADO, Estado.CANCELADO),
        Estado.FINALIZADO: (),
        Estado.CANCELADO: (),
    }

    # Alias por compatibilidad con las vistas y templates anteriores.
    ESTADO_MANTENIMIENTO = Estado.choices

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='mantenimientos')
    fecha_mantenimiento = models.DateField(verbose_name="Fecha de Mantenimiento")
    descripcion = models.TextField(verbose_name="Descripción del Mantenimiento")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones Adicionales")
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, verbose_name="Estado")
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Fecha de Registro")

    # Costo del mantenimiento: la mano de obra y los repuestos van separados.
    costo_mano_obra = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Costo de Mano de Obra (Guaraníes)")
    costo = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Costo Total del Mantenimiento (Guaraníes)")

    deposito = models.ForeignKey(
        Deposito, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mantenimientos', verbose_name="Depósito de los Repuestos")
    stock_descontado = models.BooleanField(
        default=False, editable=False, verbose_name="Stock ya descontado")

    repuestos_utilizados = models.ManyToManyField(
        Repuesto, through='MantenimientoRepuesto', blank=True,
        related_name='mantenimientos', verbose_name="Repuestos Utilizados")

    class Meta:
        verbose_name = "Mantenimiento de Vehículo"
        verbose_name_plural = "Mantenimientos de Vehículos"
        ordering = ['-fecha_mantenimiento']

    def __str__(self):
        return f"Mantenimiento de {self.vehiculo} - {self.fecha_mantenimiento}"

    @property
    def costo_repuestos(self):
        """Costo total de los repuestos utilizados."""
        if not self.pk:
            # Todavía no está guardado: no hay líneas que sumar.
            return Decimal('0.00')
        return sum((linea.subtotal for linea in self.repuestos.all()), Decimal('0.00'))

    def recalcular_costo(self):
        """Recalcula el costo total (mano de obra + repuestos) y lo guarda."""
        getattr(self, '_prefetched_objects_cache', {}).pop('repuestos', None)
        self.costo = (self.costo_mano_obra or Decimal('0.00')) + self.costo_repuestos
        MantenimientoVehiculo.objects.filter(pk=self.pk).update(costo=self.costo)
        return self.costo

    def save(self, *args, **kwargs):
        # El costo total es la suma de mano de obra y repuestos.
        if self.pk:
            self.recalcular_costo()
        super().save(*args, **kwargs)

    def validar_finalizado(self):
        """Antes de finalizar tiene que haber stock suficiente para los repuestos."""
        from inventario.services import deposito_principal, disponible_en_deposito

        if self.stock_descontado:
            raise TransicionInvalida('El stock de este mantenimiento ya fue descontado.')

        deposito = self.deposito or deposito_principal()
        faltantes = []
        for linea in self.repuestos.select_related('repuesto'):
            disponible = disponible_en_deposito(linea.repuesto, deposito)
            if linea.cantidad > disponible:
                faltantes.append(
                    f'{linea.repuesto.codigo_repuesto} '
                    f'(disponible {disponible}, se necesitan {linea.cantidad})'
                )
        if faltantes:
            raise TransicionInvalida(
                'No hay stock suficiente para: ' + ', '.join(faltantes) + '.'
            )

    def despues_de_cambiar_estado(self, anterior, nuevo):
        if str(nuevo) == str(self.Estado.FINALIZADO):
            self.descontar_stock()

    @transaction.atomic
    def descontar_stock(self):
        """
        Descuenta del stock los repuestos utilizados en este mantenimiento.

        Solo corre una vez: si el stock ya fue descontado, no vuelve a
        descontar (el movimiento de stock es inmutable por diseño).
        """
        from inventario.services import deposito_principal, registrar_salida

        if self.stock_descontado:
            return []

        deposito = self.deposito or deposito_principal()
        movimientos = []
        for linea in self.repuestos.select_related('repuesto'):
            movimiento = registrar_salida(
                linea.repuesto,
                linea.cantidad,
                deposito=deposito,
                motivo=f'Mantenimiento #{self.pk} · {self.descripcion[:80]}',
                referencia=f'MANT-{self.pk}',
            )
            linea.movimiento = movimiento
            linea.save(update_fields=['movimiento'])
            movimientos.append(movimiento)

        self.stock_descontado = True
        self.save(update_fields=['stock_descontado'])
        return movimientos


class MantenimientoRepuesto(models.Model):
    """
    Repuesto utilizado en un mantenimiento, con su cantidad y su costo.

    `costo_unitario` es una foto del costo del repuesto al momento de
    registrar el mantenimiento: los costos del stock pueden cambiar después
    y el histórico del taller no debe moverse.
    """

    mantenimiento = models.ForeignKey(
        MantenimientoVehiculo, on_delete=models.CASCADE, related_name='repuestos')
    repuesto = models.ForeignKey(
        Repuesto, on_delete=models.PROTECT, related_name='usos_en_mantenimientos')
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad Utilizada")
    costo_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Costo Unitario (Guaraníes)")
    movimiento = models.ForeignKey(
        'inventario.MovimientoStock', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name="Movimiento de Stock")

    class Meta:
        verbose_name = "repuesto de mantenimiento"
        verbose_name_plural = "repuestos de mantenimiento"
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['mantenimiento', 'repuesto'], name='uniq_repuesto_por_mantenimiento'),
            models.CheckConstraint(
                condition=Q(cantidad__gte=1), name='mantenimiento_repuesto_cantidad_positiva'),
        ]

    def __str__(self):
        return f'{self.cantidad} x {self.repuesto}'

    @property
    def subtotal(self):
        return (self.cantidad or 0) * (self.costo_unitario or Decimal('0.00'))

    def save(self, *args, **kwargs):
        if not self.costo_unitario:
            self.costo_unitario = (
                self.repuesto.costo_unitario or self.repuesto.costo_compra or Decimal('0.00')
            )
        super().save(*args, **kwargs)
        # El costo total del mantenimiento se mantiene al día.
        if self.mantenimiento_id:
            mantenimiento = MantenimientoVehiculo.objects.filter(pk=self.mantenimiento_id).first()
            if mantenimiento is not None:
                mantenimiento.recalcular_costo()

    def delete(self, *args, **kwargs):
        mantenimiento_id = self.mantenimiento_id
        super().delete(*args, **kwargs)
        if mantenimiento_id:
            mantenimiento = MantenimientoVehiculo.objects.filter(pk=mantenimiento_id).first()
            if mantenimiento is not None:
                mantenimiento.recalcular_costo()


# --------------------------------------------------------------------------
# Modelo para registrar la salida de un repuesto del inventario
# --------------------------------------------------------------------------
class SalidaRepuesto(models.Model):
    """
    Modelo para registrar la salida de un repuesto del inventario.
    """
    TIPO_SALIDA = (
        ('venta', 'Venta'),
        ('uso_interno', 'Uso Interno'),
        ('devolucion', 'Devolución'),
        ('otro', 'Otro'),
    )
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name='salidas')
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Salida")
    fecha_salida = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Salida")
    motivo = models.TextField(blank=True, null=True, verbose_name="Motivo de la Salida")
    tipo_salida = models.CharField(max_length=20, choices=TIPO_SALIDA, default='venta', verbose_name="Tipo de Salida")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción Adicional")

    class Meta:
        verbose_name = "Salida de Repuesto"
        verbose_name_plural = "Salidas de Repuestos"
        ordering = ['-fecha_salida']

    def __str__(self):
        return f"Salida de {self.cantidad} unidades de {self.repuesto} - {self.fecha_salida}" 


# Centro de Ventas
class CentroVentas(models.Model):
    """
    Modelo que representa un centro de ventas asociado a un depósito.
    """
    deposito = models.ForeignKey(Deposito, on_delete=models.CASCADE, related_name='centros_ventas', verbose_name="Depósito Asociado")
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Centro de Ventas")
    direccion = models.CharField(max_length=255, verbose_name="Dirección del Centro de Ventas")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de Contacto")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico de Contacto")
    gerente = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del Gerente")
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Centro de Ventas"
        verbose_name_plural = "Centros de Ventas"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.deposito.nombre}"
    
# Modelo para registrar la transferencia de productos entre depósitos

