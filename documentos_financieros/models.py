# documentos_financieros/models.py
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from clientes_pedidos.models import Pedido
from configuraciones_maestras.models import Moneda, TasaCambio
from inventario.models import Vehiculo, Repuesto


# --------------------------------------------------------------------------
# Modelo Base para Documentos Financieros
# --------------------------------------------------------------------------
class DocumentoFinanciero(models.Model):
    """
    Modelo base para todos los documentos financieros del sistema.
    Se usa para ventas, compras, tesorería e importaciones.
    """
    TIPO_DOCUMENTO_CHOICES = (
        ('factura_venta', 'Factura de Venta'),
        ('nota_credito', 'Nota de Crédito'),
        ('recibo_dinero', 'Recibo de Dinero'),
        ('factura_comercial', 'Factura Comercial'),
        ('despacho_importacion', 'Despacho de Importación'),
        ('factura_gastos_locales', 'Factura de Gastos Locales'),
        ('comprobante_egreso', 'Comprobante de Egreso'),
        ('extracto_bancario', 'Extracto Bancario'),
        ('nota_debito', 'Nota de Débito'),
        ('autofactura', 'Autofactura'),
        ('nota_remision', 'Nota de Remisión'),
    )

    ESTADO_DOCUMENTO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('emitido', 'Emitido'),
        ('conciliado', 'Conciliado'),
        ('anulado', 'Anulado'),
    )

    tipo_documento = models.CharField(
        max_length=25,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name="Tipo de Documento",
    )
    timbrado = models.CharField(max_length=8, blank=True, null=True, verbose_name="Número de Timbrado")
    establecimiento = models.CharField(max_length=3, blank=True, null=True, verbose_name="Establecimiento")
    punto_expedicion = models.CharField(max_length=3, blank=True, null=True, verbose_name="Punto de Expedición")
    numero_documento = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número Secuencial")

    fecha_emision = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Emisión")
    fecha_vencimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de Vencimiento")
    moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Moneda")
    tipo_cambio = models.ForeignKey(TasaCambio, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tasa de Cambio")

    cliente = models.ForeignKey(
        'clientes_pedidos.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_financieros',
    )
    proveedor = models.ForeignKey(
        'configuraciones_maestras.Proveedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_financieros',
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_financieros',
    )
    documento_referencia = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_relacionados',
        verbose_name="Documento Relacionado",
    )
    asientos = GenericRelation(
        'contabilidad.Asiento',
        content_type_field='documento_tipo',
        object_id_field='documento_id',
        related_query_name='documento_financiero',
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_DOCUMENTO_CHOICES,
        default='pendiente',
        verbose_name="Estado del Documento",
    )
    estado_sifen = models.CharField(max_length=50, default='pendiente', verbose_name="Estado en SIFEN")

    total_bruto = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Total Bruto")
    total_descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Total Descuento")
    total_impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Total Impuestos")
    monto_total = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Monto Total")

    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    referencia_externa = models.CharField(max_length=255, blank=True, null=True, verbose_name="Referencia Externa")

    class Meta:
        verbose_name = "Documento Financiero"
        verbose_name_plural = "Documentos Financieros"
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['tipo_documento', 'timbrado', 'establecimiento', 'punto_expedicion', 'numero_documento']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_emision']),
        ]

    def __str__(self):
        if self.numero_documento:
            return f"{self.get_tipo_documento_display()} - Nº {self.establecimiento or '---'}-{self.punto_expedicion or '---'}-{self.numero_documento}"
        return f"{self.get_tipo_documento_display()} ({self.pk})"

    @property
    def ultimo_asiento(self):
        return self.asientos.order_by('-fecha').first()

    @property
    def numero_completo(self):
        return f"{self.timbrado or ''}-{self.establecimiento or ''}-{self.punto_expedicion or ''}-{self.numero_documento or ''}".strip('-')

    def calcular_totales(self):
        items = self.items_documento.all()
        self.total_bruto = sum((item.subtotal for item in items), 0)
        self.total_impuestos = sum((item.iva for item in items), 0)
        self.monto_total = self.total_bruto + self.total_impuestos - self.total_descuento
        return self.monto_total


# --------------------------------------------------------------------------
# Documentos de Ventas / Ingresos
# --------------------------------------------------------------------------
class Factura(DocumentoFinanciero):
    """
    Factura de Venta / Factura Electrónica SIFEN.
    """
    TIPO_FACTURA_CHOICES = [('contado', 'Contado'), ('credito', 'Crédito')]

    tipo_factura = models.CharField(max_length=10, choices=TIPO_FACTURA_CHOICES, verbose_name="Tipo de Factura")

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"


class NotaCredito(DocumentoFinanciero):
    """
    Nota de Crédito para devoluciones o descuentos posteriores.
    """
    factura_relacionada = models.ForeignKey(
        Factura,
        on_delete=models.PROTECT,
        related_name='notas_credito',
        verbose_name="Factura Relacionada",
    )
    motivo = models.TextField(verbose_name="Motivo de la Nota de Crédito")

    class Meta:
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"


class ReciboDinero(DocumentoFinanciero):
    """
    Documento que respalda la cobranza de efectivo o transferencia.
    """
    factura_relacionada = models.ForeignKey(
        Factura,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recibos_dinero',
        verbose_name="Factura Relacionada",
    )
    medio_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('cheque', 'Cheque'),
            ('tarjeta', 'Tarjeta'),
        ],
        default='efectivo',
        verbose_name="Medio de Pago",
    )
    cuenta_contable = models.ForeignKey(
        'contabilidad.CuentaContable',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recibos_dinero',
        verbose_name="Cuenta de Caja/Banco",
    )

    class Meta:
        verbose_name = "Recibo de Dinero"
        verbose_name_plural = "Recibos de Dinero"


class NotaDebito(DocumentoFinanciero):
    """
    Nota de Débito para ajustes o cargos posteriores.
    """
    documento_asociado = models.ForeignKey(
        Factura,
        on_delete=models.PROTECT,
        related_name='notas_debito',
        verbose_name="Factura Relacionada",
    )
    motivo = models.TextField(verbose_name="Motivo de la Nota de Débito")

    class Meta:
        verbose_name = "Nota de Débito"
        verbose_name_plural = "Notas de Débito"


# --------------------------------------------------------------------------
# Compras e Importaciones
# --------------------------------------------------------------------------
class DocumentoCompra(DocumentoFinanciero):
    """
    Base abstracta para compras e importaciones.
    """
    fecha_documento_origen = models.DateField(blank=True, null=True, verbose_name="Fecha del Documento Origen")

    class Meta:
        abstract = True


class Autofactura(DocumentoCompra):
    """
    Autofactura emitida para compras o servicios con proveedor.
    """
    TIPO_FACTURA_CHOICES = [('contado', 'Contado'), ('credito', 'Crédito')]

    tipo_factura = models.CharField(max_length=10, choices=TIPO_FACTURA_CHOICES, verbose_name="Tipo de Factura")

    class Meta:
        verbose_name = "Autofactura"
        verbose_name_plural = "Autofacturas"


class NotaRemision(DocumentoFinanciero):
    """
    Nota de Remisión para despachos o entregas internas.
    """
    destino = models.CharField(max_length=255, verbose_name="Lugar de Destino")
    transportista = models.CharField(max_length=255, verbose_name="Nombre del Transportista")

    class Meta:
        verbose_name = "Nota de Remisión"
        verbose_name_plural = "Notas de Remisión"


class FacturaComercial(DocumentoCompra):
    """
    Factura comercial del proveedor extranjero.
    """
    numero_comercial = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número Comercial")
    fecha_embarque = models.DateField(blank=True, null=True, verbose_name="Fecha de Embarque")
    incoterm = models.CharField(max_length=20, blank=True, null=True, verbose_name="Incoterm")
    valor_fob = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Valor FOB")
    valor_cif = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Valor CIF")
    impuestos_aduaneros = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Impuestos Aduaneros")
    aranceles = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Aranceles")
    otros_costos_importacion = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Otros Costos de Importación")

    class Meta:
        verbose_name = "Factura Comercial"
        verbose_name_plural = "Facturas Comerciales"


class DespachoImportacion(DocumentoCompra):
    """
    Documento de despacho de importación con impuestos e importes asociados.
    """
    numero_despacho = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número de Despacho")
    despachante = models.ForeignKey(
        'configuraciones_maestras.DespachanteAduana',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='despachos_importacion',
    )
    agente_transporte = models.ForeignKey(
        'configuraciones_maestras.AgenteTransporte',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='despachos_importacion',
    )
    impuestos_aduaneros = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="IVA Aduanero")
    aranceles = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Aranceles")
    fletes = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Fletes Locales")
    seguros = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Seguros Locales")
    otros_gastos = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Otros Gastos")

    class Meta:
        verbose_name = "Despacho de Importación"
        verbose_name_plural = "Despachos de Importación"


class FacturaGastosLocales(DocumentoCompra):
    """
    Factura de gastos locales que pueden capitalizarse en el inventario.
    """
    TIPO_GASTO_CHOICES = [
        ('flete', 'Flete'),
        ('seguro', 'Seguro'),
        ('aduana', 'Trámites Aduaneros'),
        ('otros', 'Otros Gastos'),
    ]

    tipo_gasto = models.CharField(max_length=20, choices=TIPO_GASTO_CHOICES, verbose_name="Tipo de Gasto")
    importacion = models.ForeignKey(
        'importaciones.Importacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas_gastos_locales',
        verbose_name="Importación Relacionada",
    )
    capitalizable = models.BooleanField(default=True, verbose_name="Capitalizable al Inventario")

    class Meta:
        verbose_name = "Factura de Gastos Locales"
        verbose_name_plural = "Facturas de Gastos Locales"


# --------------------------------------------------------------------------
# Tesorería y conciliación
# --------------------------------------------------------------------------
class ComprobanteEgreso(DocumentoFinanciero):
    """
    Registro de pagos a proveedores o gastos operativos.
    """
    beneficiario = models.CharField(max_length=255, blank=True, null=True, verbose_name="Beneficiario")
    medio_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('cheque', 'Cheque'),
            ('tarjeta', 'Tarjeta'),
        ],
        default='transferencia',
        verbose_name="Medio de Pago",
    )
    cuenta_contable = models.ForeignKey(
        'contabilidad.CuentaContable',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comprobantes_egreso',
        verbose_name="Cuenta de Caja/Banco",
    )

    class Meta:
        verbose_name = "Comprobante de Egreso"
        verbose_name_plural = "Comprobantes de Egreso"


class ExtractoBancario(models.Model):
    """
    Modelo para importar o registrar extractos bancarios para conciliación.
    """
    cuenta_contable = models.ForeignKey(
        'contabilidad.CuentaContable',
        on_delete=models.PROTECT,
        related_name='extractos_bancarios',
    )
    fecha_inicio = models.DateField(verbose_name="Fecha Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha Fin")
    saldo_apertura = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Saldo Apertura")
    saldo_cierre = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Saldo Cierre")
    referencia_banco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Referencia Bancaria")
    conciliado = models.BooleanField(default=False, verbose_name="Conciliado")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Extracto Bancario"
        verbose_name_plural = "Extractos Bancarios"
        ordering = ['-fecha_fin']

    def __str__(self):
        return f"Extracto {self.cuenta_contable} ({self.fecha_inicio} - {self.fecha_fin})"


# --------------------------------------------------------------------------
# Modelo para los Ítems de los Documentos
# --------------------------------------------------------------------------
class ItemDocumento(models.Model):
    """
    Modelo que representa los ítems (productos o servicios) de un documento financiero.
    """
    documento = models.ForeignKey(DocumentoFinanciero, on_delete=models.CASCADE, related_name='items_documento')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)

    descripcion = models.CharField(max_length=255, verbose_name="Descripción del Ítem")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Precio Unitario")
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Descuento")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Subtotal")
    iva = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="IVA")
    total_linea = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Total de Línea")
    capitalizable = models.BooleanField(default=False, verbose_name="Capitalizable")

    class Meta:
        verbose_name = "Ítem de Documento"
        verbose_name_plural = "Ítems de Documentos"

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad or 0) * (self.precio_unitario or 0)
        self.total_linea = self.subtotal - (self.descuento or 0) + (self.iva or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ítem: {self.descripcion} ({self.cantidad})"
