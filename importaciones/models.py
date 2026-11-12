# importaciones/models.py

from decimal import Decimal
#from django.apps import apps
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from clientes_pedidos.models import Pedido
from inventario.models import Vehiculo, Repuesto
from configuraciones_maestras.models import Proveedor, AgenteTransporte, DespachanteAduana, Despachante
from django.utils import timezone

#from compras.models import FacturaItem
from core.models import EstadoMixin, Moneda, TimeStampedModel, TransicionInvalida


def _norm(valor: str) -> str:
    return (valor or '').strip().upper()


class Embarque(EstadoMixin, TimeStampedModel):
    class Estado(models.TextChoices):
        PROGRAMADO = 'PROGRAMADO', 'Programado'
        EMBARCADO = 'EMBARCADO', 'Embarcado'
        EN_TRANSITO = 'EN_TRANSITO', 'En tránsito'
        ARRIBADO = 'ARRIBADO', 'Arribado a puerto'
        EN_ADUANA = 'EN_ADUANA', 'En aduana'
        NACIONALIZADO = 'NACIONALIZADO', 'Nacionalizado'
        RECIBIDO = 'RECIBIDO', 'Recibido en depósito'
        CERRADO = 'CERRADO', 'Cerrado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    TRANSICIONES = {
        Estado.PROGRAMADO: (Estado.EMBARCADO, Estado.CANCELADO),
        Estado.EMBARCADO: (Estado.EN_TRANSITO, Estado.CANCELADO),
        Estado.EN_TRANSITO: (Estado.ARRIBADO,),
        Estado.ARRIBADO: (Estado.EN_ADUANA,),
        Estado.EN_ADUANA: (Estado.NACIONALIZADO,),
        Estado.NACIONALIZADO: (Estado.RECIBIDO,),
        Estado.RECIBIDO: (Estado.CERRADO,),
        Estado.CERRADO: (),
        Estado.CANCELADO: (),
    }

    referencia_interna = models.CharField(max_length=30, unique=True, null=True, blank=True)
    # ---- Bill of Lading --------------------------------------------------
    bl_numero = models.CharField('Nº de B/L', max_length=50, unique=True, null=True, blank=True)
    bl_liberado = models.BooleanField('B/L liberado (surrendered)', default=False,
                                      help_text='Marcar cuando el B/L fue entregado/liberado y se puede retirar la carga.')
    flete_prepago = models.BooleanField('Flete prepago', default=True)
    booking = models.CharField(max_length=50, blank=True)
    naviera = models.CharField(max_length=120, blank=True)
    buque_viaje = models.CharField('Buque / viaje', max_length=120, blank=True)
    
    shipper = models.CharField('Shipper', max_length=200, blank=True)
    consignatario = models.CharField('Consignee', max_length=200, blank=True)
    notify = models.CharField('Notify party', max_length=200, blank=True)
    # ---- Ruta -----------------------------------------------------------
    lugar_recepcion = models.CharField('Lugar de recepción', max_length=120, blank=True)
    puerto_carga = models.CharField('Puerto de carga', max_length=120, blank=True)
    puerto_descarga = models.CharField('Puerto de descarga', max_length=120, blank=True)
    destino_final = models.CharField('Destino final', max_length=120, blank=True)

    peso_bruto_kg = models.DecimalField('Peso bruto (kg)', max_digits=12, decimal_places=3, null=True, blank=True)
    volumen_m3 = models.DecimalField('Volumen (m³)', max_digits=10, decimal_places=3, null=True, blank=True)
    numero_bultos = models.PositiveIntegerField('Nº de bultos', null=True, blank=True)

    # ---- Fechas ----------------------------------------------------------
    fecha_emision = models.DateField('Fecha de emisión del B/L', null=True, blank=True)
    fecha_embarque = models.DateField(null=True, blank=True)
    eta = models.DateField('ETA', null=True, blank=True)
    fecha_arribo = models.DateField(null=True, blank=True)
    fecha_recepcion = models.DateField('Recepción en depósito', null=True, blank=True)
    
    # Lo marca el servicio de prorrateo cuando termina de repartir los gastos
    gastos_prorrateados = models.BooleanField(default=False, editable=False)
    
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROGRAMADO, editable=False)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return self.bl_numero or self.referencia_interna or f'Embarque #{self.pk}'

    @property
    def cantidad_unidades(self):
        return sum((item.cantidad for item in self.items.all()), 0)

    @property
    def cantidad_contenedores(self):
        """Cantidad de contenedores físicos del embarque."""
        return self.contenedores.count()

    @property
    def valor_fob(self):
        return sum((item.valor for item in self.items.select_related('factura_item')), Decimal('0'))

    @property
    def total_gastos_base(self):
        return sum((gasto.monto_base for gasto in self.gastos.filter(es_costeable=True)), Decimal('0'))

    @property
    def costo_landed_total(self):
        return self.valor_fob + self.total_gastos_base

    @property
    def flujo_operativo(self):
        items = list(self.items.select_related('factura_item__vehiculo'))
        if not items:
            chasis_verificado = False
        else:
            chasis_verificado = all(item.chasis_verificado for item in items)

        return {
            'embarque_registrado': bool(self.bl_numero and self.fecha_embarque),
            'contenedores_cargados': self.contenedores.exists(),
            'costos_cargados': self.gastos.exists(),
            'items_asociados': bool(items),
            'chasis_verificado': chasis_verificado,
            'prorrateado': self.gastos_prorrateados,
            'cerrado': self.estado == self.Estado.CERRADO,
        }

    def validar_embarcado(self):
        faltan = [
            nombre for nombre, valor in (
                ('Nº de B/L', self.bl_numero),
                ('fecha de embarque', self.fecha_embarque),
            ) if not valor
        ]
        if faltan:
            raise TransicionInvalida('Falta informar: ' + ', '.join(faltan) + '.')
        items = list(self.items.select_related('factura_item'))
        if not items:
            raise TransicionInvalida('El embarque no tiene ítems cargados.')
        sin_verificar = [item for item in items if not item.chasis_verificado]
        if sin_verificar:
            detalle = ', '.join(item.factura_item.descripcion for item in sin_verificar)
            raise TransicionInvalida('Los chasis no coinciden con el B/L o no fueron cargados: ' + detalle)

    def validar_en_transito(self):
        if not self.eta:
            raise TransicionInvalida('Informe la fecha estimada de arribo (ETA).')

    def validar_arribado(self):
        if not self.fecha_arribo:
            raise TransicionInvalida('Informe la fecha de arribo.')

    def validar_en_aduana(self):
        if not self.bl_liberado:
            raise TransicionInvalida('El B/L aún no está liberado (surrendered).')

    def validar_nacionalizado(self):
        despacho = getattr(self, 'despacho', None)
        if despacho is None or not despacho.nro_despacho or not despacho.fecha_oficializacion:
            raise TransicionInvalida('Cargue el despacho aduanero con su número y fecha de oficialización.')

    def validar_recibido(self):
        if not self.fecha_recepcion:
            raise TransicionInvalida('Informe la fecha de recepción en depósito.')

    def validar_cerrado(self):
        if not self.gastos_prorrateados:
            raise TransicionInvalida('Los gastos todavía no fueron prorrateados entre los ítems.')
        if self.items.filter(costo_prorrateado__isnull=True).exists():
            raise TransicionInvalida('Hay ítems sin costo landed asignado.')

    def validar_cancelado(self):
        if hasattr(self, 'despacho'):
            raise TransicionInvalida('No se puede cancelar un embarque con despacho aduanero.')
    
    # ---- sincronización con vehículos -----------------------------------
    def despues_de_cambiar_estado(self, anterior, nuevo):
        estado_vehiculo = Vehiculo.estado_desde_embarque(nuevo)
        if not estado_vehiculo:
            return
        Vehiculo.objects.filter(
            items_factura__embarque_items__embarque=self
        ).update(estado=estado_vehiculo)


class EmbarqueContenedor(TimeStampedModel):
    """
    Contenedor físico de un embarque.

    Un mismo B/L puede traer más de un contenedor, por eso los datos del
    contenedor (número, tipo, sello, peso y volumen) viven en su propia tabla
    y los ítems del embarque se asignan a un contenedor concreto.
    """

    embarque = models.ForeignKey(Embarque, on_delete=models.CASCADE, related_name='contenedores')
    numero = models.CharField('Nº de contenedor', max_length=20)
    tipo = models.CharField('Tipo', max_length=30, blank=True,
                            help_text='Ej.: 20ft, 40ft, 40HC')
    sello = models.CharField('Nº de sello', max_length=30, blank=True)
    peso_bruto_kg = models.DecimalField('Peso bruto (kg)', max_digits=12, decimal_places=3, null=True, blank=True)
    volumen_m3 = models.DecimalField('Volumen (m³)', max_digits=10, decimal_places=3, null=True, blank=True)
    bultos = models.PositiveIntegerField('Bultos', null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ['embarque', 'id']
        verbose_name = 'contenedor de embarque'
        verbose_name_plural = 'contenedores de embarque'
        constraints = [
            models.UniqueConstraint(fields=['embarque', 'numero'], name='uniq_contenedor_por_embarque'),
        ]

    def __str__(self):
        return f'{self.numero} · {self.embarque}'

    def clean(self):
        super().clean()
        if not self.embarque_id or not self.numero:
            return
        repetidos = EmbarqueContenedor.objects.filter(
            embarque_id=self.embarque_id,
            numero__iexact=self.numero.strip(),
        ).exclude(pk=self.pk)
        if repetidos.exists():
            raise ValidationError(
                f'El contenedor {self.numero.strip()} ya está cargado en este embarque.'
            )

    @property
    def unidades(self):
        """Unidades embarcadas en este contenedor."""
        return sum((item.cantidad for item in self.items.all()), 0)

    @property
    def chasis(self):
        """Chasis declarados en el B/L para este contenedor."""
        return [item.chasis_bl for item in self.items.all() if item.chasis_bl]


class EmbarqueItem(TimeStampedModel):
    embarque = models.ForeignKey(Embarque, on_delete=models.CASCADE, related_name='items')
    factura_item = models.ForeignKey('compras.FacturaItem', on_delete=models.PROTECT, related_name='embarque_items')
    contenedor = models.ForeignKey(
        EmbarqueContenedor,
        on_delete=models.PROTECT,
        related_name='items',
        help_text='Contenedor del embarque donde se carga esta unidad.',
    )
    cantidad = models.PositiveIntegerField(default=1)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Chasis tal como figura en el B/L, para contrastarlo con el de la factura
    chasis_bl = models.CharField('Chasis según B/L', max_length=30, blank=True)
    costo_prorrateado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, editable=False)

    class Meta:
        ordering = ['embarque', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['embarque', 'factura_item', 'contenedor'],
                name='uniq_embarque_factura_item',
            ),
            models.CheckConstraint(condition=Q(cantidad__gte=1), name='embarque_item_cantidad_positiva'),
        ]

    def __str__(self):
        return f'{self.factura_item.descripcion} → {self.embarque}'

    def clean(self):
        super().clean()
        
        if not self.factura_item_id:
            return
        if self.contenedor_id and self.embarque_id and self.contenedor.embarque_id != self.embarque_id:
            raise ValidationError('El contenedor seleccionado pertenece a otro embarque.')
        ya_embarcado = (
            self.factura_item.embarque_items.exclude(pk=self.pk)
            .aggregate(total=models.Sum("cantidad"))["total"] or 0
        )
        if ya_embarcado + self.cantidad > self.factura_item.cantidad:
            raise ValidationError(
                f"Se embarcarían {ya_embarcado + self.cantidad} unidades de "
                f"{self.factura_item.cantidad} facturadas."
            )
        if self.embarque_id and self.embarque.estado != Embarque.Estado.PROGRAMADO:
            raise ValidationError("Solo se pueden modificar ítems de un embarque programado.")
        
    @property
    def valor(self):
        return self.cantidad * self.factura_item.precio_unitario

    @property
    def chasis_verificado(self):
        vehiculo = self.factura_item.vehiculo
        if vehiculo is None:
            return True
        return bool(self.chasis_bl) and _norm(self.chasis_bl) == _norm(vehiculo.codigo_chasis)


class GastoImportacion(TimeStampedModel):
    class Tipo(models.TextChoices):
        FLETE = 'FLETE', 'Flete internacional'
        SEGURO = 'SEGURO', 'Seguro'
        COMISION_BANCARIA = 'COMISION_BANCARIA', 'Comisión bancaria'
        ARANCEL = 'ARANCEL', 'Aranceles / impuestos de importación'
        DESPACHANTE = 'DESPACHANTE', 'Honorarios de despachante'
        PUERTO = 'PUERTO', 'Gastos portuarios / terminal'
        TRANSPORTE_INTERNO = 'TRANSPORTE_INTERNO', 'Transporte interno'
        OTRO = 'OTRO', 'Otro'

    class Criterio(models.TextChoices):
        POR_VALOR = 'POR_VALOR', 'Proporcional al valor FOB'
        POR_UNIDAD = 'POR_UNIDAD', 'Igual por unidad'
        POR_PESO = 'POR_PESO', 'Proporcional al peso'

    embarque = models.ForeignKey(Embarque, on_delete=models.CASCADE, related_name='gastos')
    tipo = models.CharField(max_length=25, choices=Tipo.choices)
    descripcion = models.CharField(max_length=200, blank=True)
    proveedor_servicio = models.CharField(max_length=150, blank=True)
    fecha = models.DateField(default=timezone.localdate)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    moneda = models.CharField(max_length=3, choices=Moneda.get_choices, default=Moneda.USD)
    tipo_cambio = models.DecimalField(max_digits=14, decimal_places=6, default=Decimal('1'))
    criterio_prorrateo = models.CharField(max_length=12, choices=Criterio.choices, default=Criterio.POR_VALOR)
    es_costeable = models.BooleanField(default=True,
                                       help_text="Desmarcar para gastos que no integran el costo (ej.: IVA recuperable).")
    comprobante = models.FileField(upload_to='importaciones/gastos/%Y/%m/', blank=True)

    class Meta:
        ordering = ['embarque', 'fecha']
        verbose_name = 'gasto de importación'
        verbose_name_plural = 'gastos de importación'
        constraints = [
            models.CheckConstraint(condition=Q(monto__gte=0), name='gasto_monto_no_negativo'),
            models.CheckConstraint(condition=Q(tipo_cambio__gt=0), name='gasto_tc_positivo'),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} · {self.monto} {self.moneda}'

    @property
    def monto_base(self):
        return (self.monto * self.tipo_cambio).quantize(Decimal('0.01'))

    def clean(self):
        if self.embarque_id and self.embarque.estado in (Embarque.Estado.CERRADO, Embarque.Estado.CANCELADO):
            raise ValidationError('No se pueden agregar gastos a un embarque cerrado o cancelado.')


class DespachoAduana(TimeStampedModel):
    class Canal(models.TextChoices):
        VERDE = 'VERDE', 'Verde'
        NARANJA = 'NARANJA', 'Naranja'
        ROJO = 'ROJO', 'Rojo'

    embarque = models.OneToOneField(Embarque, on_delete=models.PROTECT, related_name='despacho')
    nro_despacho = models.CharField(max_length=50, blank=True)
    fecha_oficializacion = models.DateField(null=True, blank=True)
    aduana = models.CharField(max_length=120, blank=True)
    despachante = models.CharField(max_length=150, blank=True)
    canal = models.CharField(max_length=10, choices=Canal.choices, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'despacho aduanero'
        verbose_name_plural = 'despachos aduaneros'

    def __str__(self):
        return f'Despacho {self.nro_despacho or "s/n"} · {self.embarque}'


class DocumentoAdjunto(TimeStampedModel):
    class Tipo(models.TextChoices):
        BL = 'BL', 'Bill of Lading'
        FACTURA = 'FACTURA', 'Factura comercial'
        ORDEN_PAGO = 'ORDEN_PAGO', 'Orden de pago al exterior'
        PACKING = 'PACKING', 'Packing list'
        DESPACHO = 'DESPACHO', 'Despacho aduanero'
        SEGURO = 'SEGURO', 'Póliza de seguro'
        OTRO = 'OTRO', 'Otro'

    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    archivo = models.FileField(upload_to='importaciones/documentos/%Y/%m/')
    descripcion = models.CharField(max_length=200, blank=True)
    embarque = models.ForeignKey(Embarque, null=True, blank=True, on_delete=models.CASCADE, related_name='documentos')
    factura = models.ForeignKey('compras.FacturaComercial', null=True, blank=True, on_delete=models.CASCADE, related_name='documentos')

    class Meta:
        ordering = ['-creado']
        constraints = [
            models.CheckConstraint(condition=Q(embarque__isnull=False) | Q(factura__isnull=False), name='documento_con_embarque_o_factura'),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} · {self.descripcion or self.archivo.name}'

# --------------------------------------------------------------------------
# Modelos para agrupar pedidos de proveedores en un mismo contenedor
# --------------------------------------------------------------------------
class ContenedorImportacion(models.Model):
    """
    Representa un contenedor o lote consolidado para varias órdenes de importación.
    """
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('embarcado', 'Embarcado'),
        ('aduana', 'En Aduana'),
        ('despachado', 'Despachado'),
        ('completado', 'Completado'),
    )

    numero = models.CharField(max_length=50, unique=True, verbose_name='Número de Contenedor')
    descripcion = models.CharField(max_length=255, blank=True, null=True, verbose_name='Descripción')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_embarque = models.DateField(blank=True, null=True, verbose_name='Fecha de Embarque')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    despachante = models.ForeignKey(
        'configuraciones_maestras.Despachante',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contenedores',
        verbose_name='Despachante',
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Contenedor de Importación'
        verbose_name_plural = 'Contenedores de Importación'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.numero


class PedidoProveedorImportacion(models.Model):
    """
    Representa un pedido específico realizado a un proveedor para importación,
    y permite agruparlo bajo un mismo contenedor.
    """
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('embarcado', 'Embarcado'),
        ('despachado', 'Despachado'),
        ('cancelado', 'Cancelado'),
    )

    contenedor = models.ForeignKey(
        ContenedorImportacion,
        on_delete=models.CASCADE,
        related_name='pedidos_proveedor',
        verbose_name='Contenedor',
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='pedidos_importacion',
        verbose_name='Proveedor',
    )
    pedido_origen = models.ForeignKey(
        Pedido,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_proveedor_importacion',
        verbose_name='Pedido Origen',
    )
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código del Pedido')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Pedido de Proveedor para Importación'
        verbose_name_plural = 'Pedidos de Proveedores para Importación'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.codigo} - {self.proveedor}'


# --------------------------------------------------------------------------
# Compatibilidad con nombres legacy removidos tras la migración a Embarque.
# Estos aliases evitan ImportError durante el arranque mientras el código viejo
# aún referencia modelos antiguos. La lógica operativa actual debe seguir usando
# Embarque, EmbarqueItem, GastoImportacion, DespachoAduana y DocumentoAdjunto.
# --------------------------------------------------------------------------

class DocumentoAduanero(models.Model):
    class Meta:
        managed = False
        app_label = 'importaciones'
        verbose_name = 'documento aduanero legacy'
        verbose_name_plural = 'documentos aduaneros legacy'

    tipo = models.CharField(max_length=20, blank=True)
    archivo = models.FileField(upload_to='importaciones/aduana/%Y/%m/', blank=True)
    descripcion = models.CharField(max_length=200, blank=True)
    importacion = models.ForeignKey('importaciones.Importacion', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='documentos_legacy')


class CostoImportacion(models.Model):
    importacion = models.ForeignKey('Importacion', on_delete=models.CASCADE, related_name='costos', null=True, blank=True)
    tipo_costo = models.CharField(max_length=20, choices=[('flete', 'Flete'), ('seguro', 'Seguro'), ('aduana', 'Aduana'), ('impuesto', 'Impuesto'), ('otros', 'Otros')], verbose_name='Tipo de Costo')
    descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    monto = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto del Costo')
    fecha_pago = models.DateField(verbose_name='Fecha de Pago')

    class Meta:
        verbose_name = 'Costo de Importación'
        verbose_name_plural = 'Costos de Importación'

    def __str__(self):
        return f'{self.tipo_costo} - {self.descripcion}'


class ItemImportacion(models.Model):
    importacion = models.ForeignKey('Importacion', on_delete=models.CASCADE, related_name='items_legacy', null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    costo_compra = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Costo de Compra (Origen)')
    costo_por_item = models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Costo Total por Ítem (Final)')

    class Meta:
        verbose_name = 'Ítem de Importación'
        verbose_name_plural = 'Ítems de Importación'

    def __str__(self):
        return f'{self.vehiculo or self.repuesto or "Ítem"} - {self.costo_por_item}'


class Importacion(models.Model):
    ESTADO_CHOICES = (
        ('solicitada', 'Solicitada'),
        ('en_transito', 'En Tránsito'),
        ('en_aduana', 'En Aduana'),
        ('despachada', 'Despachada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    )

    ESTADO_DESPACHO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso de Despacho'),
        ('despachado', 'Despachado'),
        ('liberado', 'Liberado por Aduana'),
    )

    codigo_seguimiento = models.CharField(max_length=50, unique=True, verbose_name='Código de Seguimiento')
    fecha_embarque = models.DateField(blank=True, null=True, verbose_name='Fecha de Embarque')
    fecha_arribo_estimada = models.DateField(blank=True, null=True, verbose_name='Fecha de Arribo Estimada')
    fecha_completado = models.DateField(blank=True, null=True, verbose_name='Fecha de Finalización')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='solicitada', verbose_name='Estado de Importación')
    monto_total_costos = models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Costo Total de Importación')
    numero_bl = models.CharField(blank=True, max_length=100, null=True, verbose_name='Número BL')
    numero_factura = models.CharField(blank=True, max_length=100, null=True, verbose_name='Número de Factura')
    referencia_swift = models.CharField(blank=True, max_length=100, null=True, verbose_name='Referencia SWIFT')
    vins_vehiculos = models.JSONField(blank=True, null=True, verbose_name='VINs de Vehículos')
    estado_despacho = models.CharField(max_length=20, choices=ESTADO_DESPACHO_CHOICES, default='pendiente', verbose_name='Estado de Despacho')
    agente_transporte = models.ForeignKey(AgenteTransporte, on_delete=models.SET_NULL, blank=True, null=True, related_name='importaciones_legacy', verbose_name='Agente de Transporte')
    agente_transporte_origen = models.ForeignKey(AgenteTransporte, on_delete=models.SET_NULL, blank=True, null=True, related_name='importaciones_origen', verbose_name='Agente de Transporte Origen')
    agente_transporte_destino = models.ForeignKey(AgenteTransporte, on_delete=models.SET_NULL, blank=True, null=True, related_name='importaciones_destino', verbose_name='Agente de Transporte Destino')
    despachante_aduana = models.ForeignKey(DespachanteAduana, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Despachante de Aduana')
    despachante = models.ForeignKey(Despachante, on_delete=models.SET_NULL, blank=True, null=True, related_name='importaciones', verbose_name='Despachante / Agente de Despacho')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name='Proveedor')
    usuario_creador = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='importaciones_creadas')
    numero_booking = models.CharField(blank=True, max_length=100, null=True, verbose_name='Número Booking')
    numero_contenedor = models.CharField(blank=True, max_length=50, null=True, verbose_name='Número de Contenedor')
    numero_hbl_awb = models.CharField(blank=True, max_length=100, null=True, verbose_name='Número HBL/AWB')
    numero_precinto = models.CharField(blank=True, max_length=50, null=True, verbose_name='Número de Precinto')
    placa_vehiculo_destino = models.CharField(blank=True, max_length=30, null=True, verbose_name='Placa del Vehículo en Destino')
    registro_dinatran = models.CharField(blank=True, max_length=50, null=True, verbose_name='Habilitación DINATRAN')
    cedula_chofer_destino = models.CharField(blank=True, max_length=20, null=True, verbose_name='Cédula del Chofer')
    certificado_kc_cargado = models.BooleanField(default=False, verbose_name='Certificado KC Cargado')
    poa_cargado = models.BooleanField(default=False, verbose_name='POA Cargado')
    codigo_identificador_importador_corea = models.CharField(blank=True, max_length=100, null=True, verbose_name='Código Importador Corea (KCS)')
    numero_mandato_vui = models.CharField(blank=True, max_length=100, null=True, verbose_name='Número de Mandato VUI')
    numero_expediente_vui = models.CharField(blank=True, max_length=100, null=True, verbose_name='Número de Expediente VUI')
    fecha_vencimiento_mandato_paraguay = models.DateField(blank=True, null=True, verbose_name='Vencimiento Mandato VUI')
    fecha_vencimiento_poa_corea = models.DateField(blank=True, null=True, verbose_name='Vencimiento POA Corea')
    pedido_origen = models.ForeignKey('clientes_pedidos.Pedido', on_delete=models.SET_NULL, blank=True, null=True, related_name='importaciones_origen', verbose_name='Pedido Origen')

    class Meta:
        verbose_name = 'Importación'
        verbose_name_plural = 'Importaciones'
        ordering = ['-fecha_embarque']

    def __str__(self):
        return f'{self.codigo_seguimiento} - {self.proveedor}'


class FaseImportacion(models.Model):
    class Meta:
        managed = False
        app_label = 'importaciones'

    importacion = models.ForeignKey('importaciones.Importacion', on_delete=models.CASCADE, related_name='fases_legacy', null=True, blank=True)
    fase = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    estado_completado = models.BooleanField(default=False)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)


class DocumentoImportacion(models.Model):
    class Meta:
        managed = False
        app_label = 'importaciones'

    fase = models.ForeignKey('importaciones.FaseImportacion', on_delete=models.CASCADE, related_name='documentos_legacy', null=True, blank=True)
    tipo = models.CharField(max_length=30, blank=True)
    archivo = models.FileField(upload_to='importaciones/documentos/%Y/%m/', blank=True)
    numero_referencia = models.CharField(max_length=120, blank=True)
    fecha_documento = models.DateField(null=True, blank=True)
    monto_asociado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, default='pendiente')


class ControlFaseImportacion(models.Model):
    class Meta:
        managed = False
        app_label = 'importaciones'

    fase = models.ForeignKey('importaciones.FaseImportacion', on_delete=models.CASCADE, related_name='control_legacy', null=True, blank=True)
    requisito = models.CharField(max_length=50, blank=True)
    completado = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)
    verificado_por = models.CharField(max_length=120, blank=True)
    fecha_verificacion = models.DateTimeField(null=True, blank=True)


class ImportacionVehiculo(models.Model):
    class Meta:
        managed = False
        app_label = 'importaciones'

    importacion = models.ForeignKey('importaciones.Importacion', on_delete=models.CASCADE, related_name='vehiculos_legacy', null=True, blank=True)
    vehiculo = models.ForeignKey('inventario.Vehiculo', on_delete=models.CASCADE, null=True, blank=True)
    chasis = models.CharField(max_length=50, blank=True)





