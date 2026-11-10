# clientes_pedidos/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django_fsm import FSMField, transition
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from seguridad_usuarios.models import Persona, Empleado
from configuraciones_maestras.models import Moneda




# --------------------------------------------------------------------------
# Modelo para representar a un Cliente
# --------------------------------------------------------------------------
class Cliente(Persona):
    """
    Modelo que representa a un Cliente.
    """

    compras_realizadas = models.PositiveIntegerField(default=0)
    total_gastado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre', 'razon_social']

    def comprar_vehiculos(self, vehiculos, cantidad=1):
        pass  # Lógica para comprar vehículos

    def obtener_direccion_principal(self):
        """
        Retorna la dirección principal del cliente.
        de su contacto principal o la dirección del cliente si no tiene contactos.
        """
        contactos = self.contactos.all()
        if contactos:
            for contacto in contactos:
                if contacto.direccion:
                    return contacto.direccion
        return self.direccion

    def obtener_telefono_principal(self):
        """
        Retorna el teléfono principal del cliente.
        de su contacto principal o el teléfono del cliente si no tiene contactos.
        """
        contactos = self.contactos.all()
        if contactos:
            for contacto in contactos:
                if contacto.telefono:
                    return contacto.telefono
        return self.telefono
    
    
    def __str__(self):
        if self.razon_social:
            return f"{self.razon_social} ({self.ruc})"
        elif self.ruc:
            return f"{self.nombre} {self.apellidos} ({self.ruc})"
        return f"{self.nombre} {self.apellidos} ({self.documento_identidad})"

class ContactoCliente(Persona):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contactos')

    class Meta:
        verbose_name = "Contacto del Cliente"
        verbose_name_plural = "Contactos de Clientes"

    def __str__(self):
        return f"{self.nombre} {self.apellidos} "
# --------------------------------------------------------------------------
# Modelo para representar un Pedido
# --------------------------------------------------------------------------
class Pedido(models.Model):
    """
    Modelo que representa un Pedido de un Cliente.
    Puede ser un pedido de venta, de búsqueda, de abastecimiento o de importación.
    """
    TIPO_PEDIDO = (
        ('venta', 'Pedido de Venta'), # terminado
        ('busqueda', 'Pedido de Búsqueda'), # en proceso de comprovacion
        ('abastecimiento', 'Pedido de Abastecimiento'),
        ('importacion', 'Pedido de Importación'),
        ('stock', 'Pedido de Stock'),
        ('medida', 'Pedido a Medida'),
    )
    ESTADO_PEDIDO = (
        ('pendiente_aprovacion', 'Pendiente Aprobación'),
        ('pendiente', 'Pendiente de Aprobación'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('espera_de_busqueda', 'Espera de Búsqueda'),
        ('busqueda_abastecimiento', 'Búsqueda de Abastecimiento'),
        ('abastecimiento_aprobado', 'Abastecimiento Aprobado'),
        ('buscando', 'Buscando'),
        ('espera_aprovacion', 'Espera de Aprobación'),
        ('seleccion_pendiente', 'Pendiente de Selección de Producto'),
        ('seleccion_confirmada', 'Selección Confirmada'),
        ('buqueda_concluida_aprobada', 'Búsqueda Concluida/Aprobada'),
        ('precio_enviado_cliente', 'Precio Enviado al Cliente'),
        ('precio_confirmado_cliente', 'Precio Confirmado por Cliente'),
        ('pendiente_cobro', 'Pendiente de Cobro'),
        ('facturado_contado', 'Facturado Contado'),
        ('transferencia_en_tramite', 'Transferencia en Trámite'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
        ('cobranzas', 'En Cobranzas'),
        ('pagado', 'Pagado'),
        ('facturado', 'Facturado'),
    )

    moneda = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos', verbose_name='Moneda', default=None)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos')
    vendedor = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, related_name='pedidos_venta')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = FSMField(max_length=30, choices=ESTADO_PEDIDO, default='pendiente')
    tipo = models.CharField(max_length=30, choices=TIPO_PEDIDO, default='venta')
    venta_tipo = models.CharField(
        max_length=20,
        choices=(('repuesto', 'Venta de Repuesto'), ('vehiculo', 'Venta de Vehículo')),
        null=True,
        blank=True,
        verbose_name='Tipo de Venta'
    )
    observaciones = models.TextField(blank=True, null=True)
    repuesto_a_abastecer = models.ForeignKey('inventario.Repuesto', on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_abastecimiento', verbose_name='Repuesto a abastecer')
    motivo_cancelacion = models.TextField(blank=True, null=True, verbose_name='Motivo de cancelación/rechazo')
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pago_realizado = models.BooleanField(default=False)
    fecha_transferencia = models.DateTimeField(null=True, blank=True)
    documento_transferencia = models.FileField(
        upload_to='transferencias/',
        null=True,
        blank=True,
        verbose_name='Documento de Transferencia'
    )
    factura_pdf = models.FileField(
        upload_to='facturas/',
        null=True,
        blank=True,
        verbose_name='Factura PDF'
    )
    proveedor_compra = models.ForeignKey(
        'configuraciones_maestras.Proveedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_compra',
        verbose_name='Proveedor de compra'
    )
    numero_factura = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Número de factura'
    )
    fecha_factura = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de factura'
    )

    def save(self, *args, **kwargs):
        """Ajusta el estado inicial según el tipo de pedido cuando se crea el pedido."""
        creating = self.pk is None
        if creating and self.tipo == 'venta' and self.estado == 'pendiente':
            if self.venta_tipo == 'repuesto':
                self.estado = 'pendiente_cobro'
            elif self.venta_tipo == 'vehiculo':
                self.estado = 'pendiente_aprovacion'
        elif creating and self.tipo == 'busqueda' and self.estado in {'pendiente', 'pendiente_aprovacion'}:
            self.estado = 'espera_de_busqueda'
        elif creating and self.tipo == 'abastecimiento' and self.estado in {'pendiente', 'pendiente_aprovacion', ''}:
            self.estado = 'busqueda_abastecimiento'
        super().save(*args, **kwargs)

    def reservar_stock_repuestos(self):
        """Reserva el stock de los repuestos incluidos en el pedido mientras esté activo."""
        if not self.es_venta_repuesto or self.estado in {'cancelado', 'rechazado', 'completado'}:
            return self

        for item in self.items.filter(tipo_producto='repuesto'):
            if item.repuesto:
                item.repuesto.reservar_stock(item.cantidad)
        return self

    def liberar_reservas_repuestos(self):
        """Libera las reservas de stock de un pedido cancelado o rechazado."""
        if not self.es_venta_repuesto:
            return self

        for item in self.items.filter(tipo_producto='repuesto'):
            if item.repuesto:
                item.repuesto.liberar_reserva(item.cantidad)
        return self

    def reservar_vehiculos(self):
        """Reserva los vehículos incluidos en un pedido de venta mientras esté activo."""
        if not self.es_venta_vehiculo or self.estado in {'cancelado', 'rechazado', 'completado'}:
            return self

        for item in self.items.filter(tipo_producto='vehiculo'):
            if item.vehiculo:
                item.vehiculo.estado = 'reservado'
                item.vehiculo.save(update_fields=['estado'])
        return self

    def liberar_reservas_vehiculos(self):
        """Libera la reserva de vehículos cuando el pedido se cancela o rechaza."""
        if not self.es_venta_vehiculo:
            return self

        for item in self.items.filter(tipo_producto='vehiculo'):
            if item.vehiculo and item.vehiculo.estado == 'reservado':
                item.vehiculo.estado = 'disponible'
                item.vehiculo.save(update_fields=['estado'])
        return self

    def get_available_state_transitions(self):
        return self.get_available_estado_transitions()

    @transition(field='estado', source=['aprobado', 'cobranzas', 'pendiente_cobro'], target='facturado_contado')
    def facturar_pedido_venta_contado(self):
        """
        Método para facturar el pedido de venta contado.
        """
        if self.tipo != 'venta':
            raise ValidationError('Solo se puede facturar un pedido de venta contado.')

        if self.venta_tipo_inferido == 'repuesto':
            for item in self.items.filter(tipo_producto='repuesto'):
                if item.repuesto and item.cantidad > item.repuesto.stock_actual:
                    raise ValidationError(
                        f'Stock insuficiente para el repuesto {item.repuesto}. '
                        'Actualice el stock antes de facturar.'
                    )
        elif self.venta_tipo_inferido == 'vehiculo':
            for item in self.items.filter(tipo_producto='vehiculo'):
                if item.vehiculo:
                    item.vehiculo.estado = 'vendido'
                    item.vehiculo.save(update_fields=['estado'])

        self.estado = 'facturado_contado'
        self.save(update_fields=['estado'])
        return self

    # Compatibilidad con referencias antiguas a pedidos de compra
    facturar_pedido_compra_contado = facturar_pedido_venta_contado

    def calcular_monto_total(self):
        return sum((item.subtotal for item in self.items.all()), Decimal('0.00'))

    @property
    def venta_tipo_inferido(self):
        if self.venta_tipo:
            return self.venta_tipo
        tipos = set(self.items.values_list('tipo_producto', flat=True))
        if tipos == {'repuesto'}:
            return 'repuesto'
        if tipos == {'vehiculo'}:
            return 'vehiculo'
        return None

    @property
    def es_venta_repuesto(self):
        return self.tipo == 'venta' and self.venta_tipo_inferido == 'repuesto'

    @property
    def es_venta_vehiculo(self):
        return self.tipo == 'venta' and self.venta_tipo_inferido == 'vehiculo'

    @transition(field='estado', source=['facturado_contado', 'pagado'], target='completado')
    def confirmar_entrega_repuesto(self):
        if not self.es_venta_repuesto:
            raise ValidationError('Solo se puede confirmar entrega en pedidos de venta de repuestos.')

        for item in self.items.filter(tipo_producto='repuesto'):
            repuesto = item.repuesto
            if repuesto:
                if item.cantidad > repuesto.stock_actual:
                    raise ValidationError(
                        f'Stock insuficiente para entregar {repuesto}. '
                        'Actualice el stock antes de continuar.'
                    )
                repuesto.confirmar_venta(item.cantidad)

        self.estado = 'completado'
        self.save(update_fields=['estado'])
        return self

    def programar_transferencia(self, fecha_transferencia):
        if not self.es_venta_vehiculo:
            raise ValidationError('Solo se puede programar transferencia para pedidos de venta de vehículos.')
        self.fecha_transferencia = fecha_transferencia
        self.save(update_fields=['fecha_transferencia'])
        return self

    @transition(field='estado', source=['facturado_contado', 'pagado'], target='transferencia_en_tramite')
    def iniciar_transferencia(self):
        if not self.es_venta_vehiculo:
            raise ValidationError('Solo se puede iniciar transferencia para pedidos de venta de vehículos.')
        self.estado = 'transferencia_en_tramite'
        self.save(update_fields=['estado'])
        return self

    @transition(field='estado', source='transferencia_en_tramite', target='completado')
    def confirmar_transferencia(self):
        if not self.es_venta_vehiculo:
            raise ValidationError('Solo se puede confirmar transferencia para pedidos de venta de vehículos.')
        if not self.documento_transferencia:
            raise ValidationError('Se debe subir el documento de la escribanía antes de confirmar la transferencia.')
        self.estado = 'completado'
        self.save(update_fields=['estado'])
        return self

    @transition(field='estado', source=['pendiente', 'pendiente_aprovacion', 'aprobado', 'cobranzas', 'pendiente_cobro', 'facturado_contado', 'transferencia_en_tramite', 'busqueda_abastecimiento'], target='cancelado')
    def cancelar(self, motivo=None):
        self.liberar_reservas_repuestos()
        self.liberar_reservas_vehiculos()
        self.motivo_cancelacion = motivo or self.motivo_cancelacion
        self.estado = 'cancelado'
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @property
    def es_pedido_venta(self):
        return self.tipo == 'venta'

    def calcular_iva(self):
        return (self.calcular_monto_total() * Decimal('0.10')).quantize(Decimal('0.01'))

    @property
    def tipo_descripcion(self):
        return dict(self.TIPO_PEDIDO).get(self.tipo, self.tipo)

    @property
    def esta_completado(self):
        return self.estado == 'completado'

    @property
    def es_pedido_importacion(self):
        return self.tipo == 'importacion'

    @property
    def es_pedido_busqueda(self):
        return self.tipo == 'busqueda'

    @property
    def es_pedido_abastecimiento(self):
        return self.tipo == 'abastecimiento'

    @property
    def esta_en_cobranzas(self):
        return self.estado == 'cobranzas'

    @transition(field='estado', source=['pendiente', 'pendiente_aprovacion'], target='aprobado')
    def aprobar(self):
        self.estado = 'aprobado'
        self.save(update_fields=['estado'])
        return self

    @transition(field='estado', source='busqueda_abastecimiento', target='abastecimiento_aprobado')
    def aprobar_abastecimiento(self, motivo=None):
        self.motivo_cancelacion = motivo or self.motivo_cancelacion
        self.estado = 'abastecimiento_aprobado'
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @transition(field='estado', source=['pendiente', 'pendiente_aprovacion', 'aprobado', 'cobranzas', 'pendiente_cobro', 'busqueda_abastecimiento'], target='rechazado')
    def rechazar(self, motivo=None):
        self.liberar_reservas_repuestos()
        self.liberar_reservas_vehiculos()
        self.motivo_cancelacion = motivo or self.motivo_cancelacion
        self.estado = 'rechazado'
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @transition(field='estado', source='aprobado', target='cobranzas')
    def enviar_a_cobranzas(self):
        self.estado = 'cobranzas'
        self.save(update_fields=['estado'])
        return self

    @transition(field='estado', source=['cobranzas', 'pendiente_cobro', 'facturado_contado'], target='pagado')
    def confirmar_pago(self):
        self.estado = 'pagado'
        self.pago_realizado = True
        self.save(update_fields=['estado', 'pago_realizado'])
        return self

    @transition(field='estado', source='pagado', target='facturado')
    def marcar_facturado(self):
        self.estado = 'facturado'
        self.save(update_fields=['estado'])
        return self

    def _actualizar_estado_producto(self, producto, nuevo_estado):
        if producto is None:
            return None
        if hasattr(producto, 'estado') and getattr(producto, 'estado', None) != nuevo_estado:
            producto.estado = nuevo_estado
            producto.save(update_fields=['estado'])
        return producto

    def _actualizar_productos_en_busqueda(self, nuevo_estado, producto=None):
        if producto is not None:
            self._actualizar_estado_producto(producto, nuevo_estado)
            return

        for producto_buscado in self.productos_buscados.select_related('seleccion').all():
            seleccion = getattr(producto_buscado, 'seleccion', None)
            if seleccion is None:
                continue
            if seleccion.vehiculo:
                self._actualizar_estado_producto(seleccion.vehiculo, nuevo_estado)
            elif seleccion.repuesto:
                self._actualizar_estado_producto(seleccion.repuesto, nuevo_estado)

    @transition(field='estado', source='espera_de_busqueda', target='buscando')
    def buscar(self):
        if self.tipo != 'busqueda':
            raise ValidationError('Solo se pueden buscar productos desde un pedido de búsqueda.')
        self.estado = 'buscando'
        self.save(update_fields=['estado'])
        return self

    @transition(field='estado', source='buscando', target='espera_aprovacion')
    def ingresar_repuesto(self, producto=None, motivo=None):
        if self.tipo != 'busqueda':
            raise ValidationError('Solo se pueden ingresar repuestos desde un pedido de búsqueda.')
        self.estado = 'espera_aprovacion'
        if motivo:
            self.motivo_cancelacion = motivo
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @transition(field='estado', source='espera_aprovacion', target='buqueda_concluida_aprobada')
    def aprobar_repuesto(self, producto=None, motivo=None):
        if self.tipo != 'busqueda':
            raise ValidationError('Solo se puede aprobar una búsqueda desde un pedido de búsqueda.')
        self._actualizar_productos_en_busqueda('pendiente_importacion', producto)
        self.estado = 'buqueda_concluida_aprobada'
        if motivo:
            self.motivo_cancelacion = motivo
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @transition(field='estado', source='buscando', target='seleccion_pendiente')
    def ingresar_lista_vehiculos(self, producto=None, motivo=None):
        if self.tipo != 'busqueda':
            raise ValidationError('Solo se pueden ingresar vehículos desde un pedido de búsqueda.')
        self.estado = 'seleccion_pendiente'
        if motivo:
            self.motivo_cancelacion = motivo
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @transition(field='estado', source='seleccion_pendiente', target='buqueda_concluida_aprobada')
    def confirmar_eleccion(self, producto=None, motivo=None):
        if self.tipo != 'busqueda':
            raise ValidationError('Solo se pueden confirmar selecciones desde un pedido de búsqueda.')
        self._actualizar_productos_en_busqueda('pendiente_importacion', producto)
        self.estado = 'buqueda_concluida_aprobada'
        if motivo:
            self.motivo_cancelacion = motivo
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @transition(field='estado', source=['espera_de_busqueda', 'buscando', 'seleccion_pendiente', 'espera_aprovacion'], target='cancelado')
    def cancelar_busqueda(self, motivo=None):
        if self.tipo != 'busqueda':
            raise ValidationError('Solo se pueden cancelar pedidos de búsqueda.')
        self.motivo_cancelacion = motivo or self.motivo_cancelacion
        self._actualizar_productos_en_busqueda('busqueda_cancelada')
        self.estado = 'cancelado'
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    @transition(field='estado', source=['espera_aprovacion', 'seleccion_pendiente'], target='rechazado')
    def rechazar_busqueda(self, motivo=None):
        if self.tipo != 'busqueda':
            raise ValidationError('Solo se pueden rechazar pedidos de búsqueda.')
        self.motivo_cancelacion = motivo or self.motivo_cancelacion
        self._actualizar_productos_en_busqueda('busqueda_rechazada')
        self.estado = 'rechazado'
        self.save(update_fields=['estado', 'motivo_cancelacion'])
        return self

    def enviar_a_seleccion(self):
        """Envía un pedido de búsqueda o abastecimiento al encargado de selección de producto."""
        if self.tipo in {'busqueda', 'abastecimiento'}:
            self.estado = 'seleccion_pendiente'
            self.save(update_fields=['estado'])
        return self

    def confirmar_seleccion(self):
        """Encargado confirma la selección del producto."""
        if self.estado == 'seleccion_pendiente':
            self.estado = 'seleccion_confirmada'
            self.save(update_fields=['estado'])
        return self

    def enviar_precio_cliente(self):
        """Envía el precio confirmado al cliente."""
        if self.estado == 'seleccion_confirmada':
            self.estado = 'precio_enviado_cliente'
            self.save(update_fields=['estado'])
        return self

    def confirmar_precio_cliente(self):
        """Cliente confirma el precio y se convierte en pedido de importación."""
        if self.estado == 'precio_enviado_cliente':
            self.estado = 'precio_confirmado_cliente'
            # Cambiar el tipo a importación si fue desde búsqueda
            if self.tipo == 'busqueda':
                self.tipo = 'importacion'
            self.save(update_fields=['estado', 'tipo'])
        return self

    def crear_importacion_desde_abastecimiento(self, proveedor=None):
        """Crea una importación a partir de productos abastecidos o buscados aprobados."""
        if self.tipo not in {'abastecimiento', 'busqueda'}:
            return None

        from importaciones.models import Importacion
        from configuraciones_maestras.models import Proveedor
        from django.utils import timezone

        importacion_existente = Importacion.objects.filter(pedido_origen=self).first()
        if importacion_existente:
            return importacion_existente

        productos_aprobados = self.productos_buscados.filter(
            seleccion__estado='encontrado',
            seleccion__aprobado_seo=True,
        )
        if productos_aprobados.count() != self.productos_buscados.count():
            return None

        proveedor_compra = proveedor or self.proveedor_compra
        if not proveedor_compra:
            proveedor_compra = Proveedor.objects.order_by('id').first()
        if not proveedor_compra:
            proveedor_compra = Proveedor.objects.create(
                tipo_persona='JURIDICA',
                razon_social='Proveedor por defecto',
                nombre='Proveedor por defecto',
            )

        importacion = Importacion.objects.create(
            codigo_seguimiento=f'AB-{self.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            proveedor=proveedor_compra,
            pedido_origen=self,
            estado='solicitada',
            monto_total_costos=self.monto_total or Decimal('0.00'),
        )

        for producto in productos_aprobados.select_related('seleccion'):
            seleccion = producto.seleccion
            if seleccion and seleccion.repuesto:
                from importaciones.models import ItemImportacion
                ItemImportacion.objects.create(
                    importacion=importacion,
                    repuesto=seleccion.repuesto,
                    costo_compra=seleccion.precio_unitario or Decimal('0.00'),
                    costo_por_item=seleccion.precio_total or Decimal('0.00'),
                )

        self.estado = 'en_proceso'
        self.save(update_fields=['estado'])
        return importacion

    def comprar_a_proveedor(self, proveedor=None, numero_factura=None, factura_pdf=None, observaciones=None):
        """Registra la compra desde un pedido aprobado y adjunta la factura si se envía."""
        if self.tipo not in {'abastecimiento', 'busqueda'}:
            raise ValidationError('Solo se pueden comprar pedidos de abastecimiento o búsqueda.')

        if self.tipo == 'abastecimiento' and self.estado not in {'seleccion_confirmada', 'buqueda_concluida_aprobada', 'aprobado', 'en_proceso'}:
            raise ValidationError('El pedido de abastecimiento debe estar aprobado para comprar.')

        if self.tipo == 'busqueda' and self.estado not in {'buqueda_concluida_aprobada', 'precio_confirmado_cliente', 'en_proceso'}:
            raise ValidationError('El pedido de búsqueda debe estar aprobada para comprar.')

        if not self.productos_buscados.exists():
            raise ValidationError('No hay productos aprobados para comprar en este pedido.')

        importacion = self.crear_importacion_desde_abastecimiento(proveedor=proveedor)
        if importacion is None:
            raise ValidationError('No fue posible crear la importación desde este pedido.')

        from django.utils import timezone

        self.proveedor_compra = proveedor or self.proveedor_compra
        self.numero_factura = numero_factura or self.numero_factura
        self.fecha_factura = self.fecha_factura or timezone.now().date()
        if factura_pdf:
            self.factura_pdf = factura_pdf
        if observaciones:
            self.observaciones = f"{self.observaciones}\n{observaciones}".strip() if self.observaciones else observaciones
        self.pago_realizado = bool(self.numero_factura or self.factura_pdf)
        self.estado = 'en_proceso'
        self.save(update_fields=['proveedor_compra', 'numero_factura', 'fecha_factura', 'factura_pdf', 'observaciones', 'pago_realizado', 'estado'])
        return importacion

    def actualizar_estado(self, nuevo_estado):

        if nuevo_estado in dict(self.ESTADO_PEDIDO):
            self.estado = nuevo_estado
            self.save()
        else:
            raise ValueError(f"Estado inválido: {nuevo_estado}")
        
    def obtener_items(self):
        return self.items.all()
    
    def cancelar_pedido(self):
        return self.estado in ['pendiente', 'aprobado']

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente}"



# modelo para representar documento de descripcion de vehiculo o repuesto solicitado por el cliente para importacion a medida
# rango de año, marca, modelo, version, color, tipo de combustible, tipo de carroceria, tipo de transmision, tipo de traccion, tipo de motor, tipo de direccion, tipo de frenos, tipo de suspension, tipo de llantas, tipo de sistema electrico, tipo de sistema de audio, tipo de sistema de navegacion, tipo de sistema de seguridad, tipo de sistema de climatizacion, tipo de sistema de entretenimiento, tipo de sistema de conectividad, tipo de sistema de asistencia al conductor
# es la descripcion del vehiculo o repuesto que el cliente solicita para importacion a medida, y se adjunta al pedido de importacion a medida
class PedidoVehiculo(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pedido_vehiculo')
    descripcion = models.TextField(verbose_name="Descripción del Vehículo o Repuesto Solicitado")
    inicio_rango_anio = models.CharField(max_length=20, blank=True, null=True)
    fin_rango_anio = models.CharField(max_length=20, blank=True, null=True)
    marca = models.CharField(max_length=50, blank=True, null=True)
    modelo = models.CharField(max_length=50, blank=True, null=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    tipo_combustible = models.CharField(max_length=30, blank=True, null=True)
    tipo_carroceria = models.CharField(max_length=30, blank=True, null=True)
    tipo_transmision = models.CharField(max_length=30, blank=True, null=True)
    tipo_traccion = models.CharField(max_length=30, blank=True, null=True)
    tipo_motor = models.CharField(max_length=30, blank=True, null=True)
    tipo_direccion = models.CharField(max_length=30, blank=True, null=True)
    tipo_frenos = models.CharField(max_length=30, blank=True, null=True)
    tipo_suspension = models.CharField(max_length=30, blank=True, null=True)
    tipo_llantas = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_electrico = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_audio = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_navegacion = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_seguridad = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_climatizacion = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_entretenimiento = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_conectividad = models.CharField(max_length=30, blank=True, null=True)
    tipo_sistema_asistencia_conductor = models.CharField(max_length=30, blank=True, null=True)

# modelo para representar un ítem de pedido (descripcion de vehiculo)



# --------------------------------------------------------------------------
# Modelo para representar un Ítem de Pedido
# --------------------------------------------------------------------------
class ItemPedido(models.Model):
    """
    Modelo que representa un ítem dentro de un Pedido.
    """
    from inventario.models import Vehiculo, Repuesto

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    tipo_producto = models.CharField(max_length=10, choices=(('vehiculo', 'Vehículo'), ('repuesto', 'Repuesto')), default='vehiculo')
    vehiculo = models.ForeignKey('inventario.Vehiculo', on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def producto(self):
        if self.tipo_producto == 'vehiculo':
            return self.vehiculo
        if self.tipo_producto == 'repuesto':
            return self.repuesto
        return None

    def clean(self):
        if self.tipo_producto == 'vehiculo':
            if self.repuesto:
                raise ValidationError('Un ítem de tipo vehículo no puede contener un repuesto.')
            if not self.vehiculo:
                raise ValidationError('Debe seleccionar un vehículo para este ítem.')
        elif self.tipo_producto == 'repuesto':
            if self.vehiculo:
                raise ValidationError('Un ítem de tipo repuesto no puede contener un vehículo.')
            if not self.repuesto:
                raise ValidationError('Debe seleccionar un repuesto para este ítem.')
        else:
            raise ValidationError('Tipo de producto inválido.')

    def save(self, *args, **kwargs):
        if self.tipo_producto == 'vehiculo':
            self.repuesto = None
        elif self.tipo_producto == 'repuesto':
            self.vehiculo = None
        self.subtotal = self.cantidad * self.precio_unitario
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if self.tipo_producto == 'repuesto' and self.repuesto and self.pedido_id:
            if is_new:
                self.pedido.reservar_stock_repuestos()
            else:
                self.pedido.liberar_reservas_repuestos()
                self.pedido.reservar_stock_repuestos()
        elif self.tipo_producto == 'vehiculo' and self.vehiculo and self.pedido_id:
            self.pedido.reservar_vehiculos()

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"

    def __str__(self):
        producto = self.producto
        if producto:
            return f"{self.cantidad} x {producto} - Subtotal: {self.subtotal}"
        return "Ítem de Pedido sin producto"


class FacturaCompraProveedor(models.Model):
    proveedor = models.ForeignKey(
        'configuraciones_maestras.Proveedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas_compra'
    )
    pedidos = models.ManyToManyField('Pedido', related_name='facturas_compra', blank=True)
    numero_factura = models.CharField(max_length=100, blank=True, null=True)
    fecha_factura = models.DateField(null=True, blank=True)
    factura_pdf = models.FileField(
        upload_to='facturas_compras/',
        null=True,
        blank=True
    )
    observaciones = models.TextField(blank=True, null=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Factura de Compra'
        verbose_name_plural = 'Facturas de Compras'
        ordering = ['-creado']

    def calcular_totales(self):
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        self.monto_total = total
        self.iva = (total * Decimal('0.10')).quantize(Decimal('0.01'))
        self.save(update_fields=['monto_total', 'iva'])
        return self.monto_total

    def __str__(self):
        return f'Factura {self.numero_factura or self.pk} - {self.proveedor or "Proveedor desconocido"}'


class FacturaCompraItem(models.Model):
    factura = models.ForeignKey(
        FacturaCompraProveedor,
        on_delete=models.CASCADE,
        related_name='items'
    )
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Ítem de Factura de Compra'
        verbose_name_plural = 'Ítems de Facturas de Compra'

    def __str__(self):
        return f'{self.cantidad} x {self.repuesto or "Repuesto"} - {self.subtotal}'


# --------------------------------------------------------------------------
# Modelo para Productos Buscados en Pedidos de Búsqueda
# --------------------------------------------------------------------------
class ProductoBuscado(models.Model):
    """
    Modelo que representa un producto buscado por el cliente en un pedido de búsqueda.
    Contiene la descripción del producto que el cliente está buscando.
    """
    TIPO_PRODUCTO_CHOICES = (
        ('vehiculo', 'Vehículo'),
        ('repuesto', 'Repuesto'),
    )

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='productos_buscados')
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO_CHOICES, default='vehiculo')
    vehiculo = models.ForeignKey('inventario.Vehiculo', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='productos_buscados_vehiculo')
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='productos_buscados_repuesto')
    descripcion = models.TextField(verbose_name="Descripción del Producto Buscado")
    cantidad = models.PositiveIntegerField(default=1)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    especificaciones = models.TextField(blank=True, null=True, verbose_name="Especificaciones Adicionales")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto Buscado"
        verbose_name_plural = "Productos Buscados"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.descripcion} (Pedido #{self.pedido.id})"


# --------------------------------------------------------------------------
# Modelo para Selección de Productos Buscados
# --------------------------------------------------------------------------
class SeleccionProductoBuscado(models.Model):
    """
    Modelo que registra la respuesta del encargado de selección de producto.
    Contiene el producto encontrado, precio y confirmación del cliente.
    """
    ESTADO_SELECCION = (
        ('pendiente', 'Pendiente de Confirmación'),
        ('encontrado', 'Producto Encontrado'),
        ('no_encontrado', 'Producto No Encontrado'),
    )

    producto_buscado = models.OneToOneField(ProductoBuscado, on_delete=models.CASCADE, related_name='seleccion')
    estado = models.CharField(max_length=20, choices=ESTADO_SELECCION, default='pendiente')
    
    # Información del producto encontrado
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='selecciones_busqueda')
    vehiculo = models.ForeignKey('inventario.Vehiculo', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='selecciones_busqueda_vehiculo')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name="Precio Total (cantidad x unitario)")
    
    # Información de confirmación del cliente
    cliente_confirma = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)
    
    # Auditoría
    encargado_seleccion = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='selecciones_producto',
                                            verbose_name="Encargado de Selección")
    aprobado_seo = models.BooleanField(default=False, verbose_name="Aprobado por SEO")
    fecha_seleccion = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion_cliente = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Selección de Producto Buscado"
        verbose_name_plural = "Selecciones de Productos Buscados"
        ordering = ['-fecha_seleccion']

    def calcular_precio_total(self):
        """Calcula el precio total basado en cantidad y precio unitario."""
        if self.precio_unitario and self.producto_buscado.cantidad:
            self.precio_total = self.precio_unitario * self.producto_buscado.cantidad
            self.save(update_fields=['precio_total'])
        return self.precio_total

    def confirmar_cliente(self):
        """Registra la confirmación del cliente."""
        from django.utils import timezone
        self.cliente_confirma = True
        self.fecha_confirmacion_cliente = timezone.now()
        self.save(update_fields=['cliente_confirma', 'fecha_confirmacion_cliente'])
        
        # Crear un ítem en el pedido de importación
        pedido = self.producto_buscado.pedido
        if self.repuesto:
            ItemPedido.objects.create(
                pedido=pedido,
                tipo_producto='repuesto',
                repuesto=self.repuesto,
                cantidad=self.producto_buscado.cantidad,
                precio_unitario=self.precio_unitario,
                subtotal=self.precio_total or Decimal('0.00')
            )
        elif self.vehiculo:
            ItemPedido.objects.create(
                pedido=pedido,
                tipo_producto='vehiculo',
                vehiculo=self.vehiculo,
                cantidad=self.producto_buscado.cantidad,
                precio_unitario=self.precio_unitario,
                subtotal=self.precio_total or Decimal('0.00')
            )

        # Actualizar el monto total del pedido
        pedido.monto_total = pedido.calcular_monto_total()
        pedido.iva = pedido.calcular_iva()
        pedido.save(update_fields=['monto_total', 'iva'])

    def __str__(self):
        return f"Selección de {self.producto_buscado} - {self.get_estado_display()}"


# --------------------------------------------------------------------------
# Modelo para representar una Cotización de un Pedido a Medida
# --------------------------------------------------------------------------
class Cotizacion(models.Model):

    """
    Modelo que representa una Cotización para un Pedido a Medida.
    """
    ESTADO_COTIZACION = (
        ('solicitada', 'Solicitada'),
        ('enviada', 'Enviada al Cliente'),
        ('aprobada', 'Aprobada por el Cliente'),
        ('rechazada', 'Rechazada por el Cliente'),
    )
    pedido = models.OneToOneField(Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizacion')
    fecha_cotizacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_COTIZACION, default='solicitada')
    descripcion_solicitud = models.TextField(verbose_name="Descripción del Producto Solicitado")
    monto_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_validez = models.DateField(verbose_name="Fecha de Validez de la Cotización", null=True, blank=True)

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_cotizacion']

    def __str__(self):
        if self.pedido and self.pedido.cliente:
            return f"Cotización #{self.pk} para {self.pedido.cliente}"
        return f"Cotización #{self.pk}"


class ItemCarritoVehiculo(models.Model):
    carrito = models.ForeignKey('Carrito', on_delete=models.CASCADE)
    vehiculo = models.ForeignKey('inventario.Vehiculo', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.vehiculo}"

class ItemCarritoRepuesto(models.Model):
    carrito = models.ForeignKey('Carrito', on_delete=models.CASCADE)
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.repuesto}"

class Carrito(models.Model):
    """
    Modelo que representa un Carrito de Compras para un Cliente.
    """
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='carrito')
    vehiculos = models.ManyToManyField('inventario.Vehiculo', through='ItemCarritoVehiculo')
    repuestos = models.ManyToManyField('inventario.Repuesto', through='ItemCarritoRepuesto')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def cancelar_carrito(self):
        self.vehiculos.clear()
        self.repuestos.clear()
        self.save()

    def vaciar_carrito(self):
        self.vehiculos.clear()
        self.repuestos.clear()
        self.save()

    def agregar_vehiculo(self, vehiculo, cantidad=1):
        item, created = ItemCarritoVehiculo.objects.get_or_create(carrito=self, vehiculo=vehiculo)
        if not created:
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad
        item.save()

    def agregar_repuesto(self, repuesto, cantidad=1):
        item, created = ItemCarritoRepuesto.objects.get_or_create(carrito=self, repuesto=repuesto)
        if not created:
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad
        item.save()
    
    def total_items(self):
        total_vehiculos = sum(item.cantidad for item in ItemCarritoVehiculo.objects.filter(carrito=self))
        total_repuestos = sum(item.cantidad for item in ItemCarritoRepuesto.objects.filter(carrito=self))
        return total_vehiculos + total_repuestos
    
    def total_precio(self):
        total_vehiculos = sum(item.cantidad * item.vehiculo.precio for item in ItemCarritoVehiculo.objects.filter(carrito=self))
        total_repuestos = sum(item.cantidad * item.repuesto.precio for item in ItemCarritoRepuesto.objects.filter(carrito=self))
        return total_vehiculos + total_repuestos
    
    def quitar_vehiculo(self, vehiculo):
        ItemCarritoVehiculo.objects.filter(carrito=self, vehiculo=vehiculo).delete()
    
    def quitar_repuesto(self, repuesto):
        ItemCarritoRepuesto.objects.filter(carrito=self, repuesto=repuesto).delete()

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    def __str__(self):
        return f"Carrito de {self.cliente}"
    
class HistorialCompras(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='historial_compras')
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historial_compras')
    fecha_compra = models.DateTimeField(auto_now_add=True)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Historial de Compra"
        verbose_name_plural = "Historiales de Compras"
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"Compra #{self.pedido.pk} - {self.cliente}"



class ItemCarritoVehiculoVendedor(models.Model):
    carrito = models.ForeignKey('CarritoVendedor', on_delete=models.CASCADE)
    vehiculo = models.ForeignKey('inventario.Vehiculo', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.vehiculo}"
    
class ItemCarritoRepuestoVendedor(models.Model):
    carrito = models.ForeignKey('CarritoVendedor', on_delete=models.CASCADE)
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.repuesto}"
    
    
class CarritoVendedor(models.Model):
    """
    Modelo que representa un Carrito de Compras para un Vendedor.
    """
    vendedor = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name='carrito_vendedor')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    vehiculos = models.ManyToManyField('inventario.Vehiculo', through='ItemCarritoVehiculoVendedor')
    repuestos = models.ManyToManyField('inventario.Repuesto', through='ItemCarritoRepuestoVendedor')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='carritos_vendedor')

    def agregar_cliente(self, cliente):
        self.cliente = cliente
        self.save()
        
    def vaciar_carrito(self):
        self.vehiculos.clear()
        self.repuestos.clear()
        self.save()

    def transferir_a_cliente(self, cliente):
        if hasattr(cliente, 'carrito'):
            cliente.carrito.vaciar_carrito()
            for item in ItemCarritoVehiculoVendedor.objects.filter(carrito=self):
                cliente.carrito.agregar_vehiculo(item.vehiculo, item.cantidad)
            for item in ItemCarritoRepuestoVendedor.objects.filter(carrito=self):
                cliente.carrito.agregar_repuesto(item.repuesto, item.cantidad)
            self.vaciar_carrito()

    def agregar_vehiculo(self, vehiculo, cantidad=1):
        item, created = ItemCarritoVehiculoVendedor.objects.get_or_create(carrito=self, vehiculo=vehiculo)
        if not created:
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad
        item.save()

    def agregar_repuesto(self, repuesto, cantidad=1):
        item, created = ItemCarritoRepuestoVendedor.objects.get_or_create(carrito=self, repuesto=repuesto)
        if not created:
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad
        item.save()
    
    def total_items(self):
        total_vehiculos = sum(item.cantidad for item in ItemCarritoVehiculoVendedor.objects.filter(carrito=self))
        total_repuestos = sum(item.cantidad for item in ItemCarritoRepuestoVendedor.objects.filter(carrito=self))
        return total_vehiculos + total_repuestos
    
    def total_precio(self):
        total_vehiculos = sum(item.cantidad * item.vehiculo.precio for item in ItemCarritoVehiculoVendedor.objects.filter(carrito=self))
        total_repuestos = sum(item.cantidad * item.repuesto.precio for item in ItemCarritoRepuestoVendedor.objects.filter(carrito=self))
        return total_vehiculos + total_repuestos
    
    def quitar_vehiculo(self, vehiculo):
        ItemCarritoVehiculoVendedor.objects.filter(carrito=self, vehiculo=vehiculo).delete()
    
    def quitar_repuesto(self, repuesto):
        ItemCarritoRepuestoVendedor.objects.filter(carrito=self, repuesto=repuesto).delete()

    class Meta:
        verbose_name = "Carrito del Vendedor"
        verbose_name_plural = "Carritos de los Vendedores"