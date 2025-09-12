# documentos_financieros/models.py

from django.db import models
from django.contrib.auth import get_user_model
from clientes_pedidos.models import Pedido, ItemPedido
from configuraciones_maestras.models import TasaCambio
from inventario.models import Vehiculo, Repuesto

Usuario = get_user_model()

# --------------------------------------------------------------------------
# Modelo Base para Documentos Financieros (DE)
# --------------------------------------------------------------------------
class DocumentoFinanciero(models.Model):
    """
    Modelo base que representa un Documento Financiero Electrónico (DE).
    Contiene campos comunes para Facturas, Notas de Crédito, etc.
    """
    TIPO_DOCUMENTO_CHOICES = (
        ('factura_c', 'Factura Contado'),
        ('factura_cr', 'Factura Crédito'),
        ('nota_credito', 'Nota de Crédito'),
        ('nota_debito', 'Nota de Débito'),
        ('autofactura', 'Autofactura'),
        ('nota_remision', 'Nota de Remisión'),
    )

    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, verbose_name="Tipo de Documento")
    # Campos del Grupo C del SIFEN
    timbrado = models.CharField(max_length=8, verbose_name="Número de Timbrado")
    establecimiento = models.CharField(max_length=3, verbose_name="Establecimiento")
    punto_expedicion = models.CharField(max_length=3, verbose_name="Punto de Expedición")
    numero_documento = models.CharField(max_length=7, verbose_name="Número Secuencial")
    
    # Campos del Grupo D del SIFEN
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Emisión")
    moneda = models.CharField(max_length=3, default='PYG', verbose_name="Moneda de la Operación")
    tipo_cambio = models.ForeignKey(TasaCambio, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Referencia a la operación en el sistema
    pedido = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos_fiscales')
    
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Monto Total")
    estado_sifen = models.CharField(max_length=50, default='pendiente', verbose_name="Estado en SIFEN")
    
    class Meta:
        verbose_name = "Documento Financiero"
        verbose_name_plural = "Documentos Financieros"
        ordering = ['-fecha_emision']
        abstract = True # Esta clase no creará una tabla en la base de datos

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - Nº {self.establecimiento}-{self.punto_expedicion}-{self.numero_documento}"


# --------------------------------------------------------------------------
# Modelos para Tipos de Documentos Específicos
# --------------------------------------------------------------------------
class Factura(DocumentoFinanciero):
    """
    Modelo que representa una Factura Electrónica (Contado o Crédito).
    """
    tipo_factura = models.CharField(max_length=10, choices=[('contado', 'Contado'), ('credito', 'Crédito')], verbose_name="Tipo de Factura")
    # Referencia al cliente, si es de crédito
    cliente = models.ForeignKey('clientes_pedidos.Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    
    def imprimir(self):
        # Lógica para generar e imprimir la factura
        pass

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"


class NotaCredito(DocumentoFinanciero):
    """
    Modelo que representa una Nota de Crédito.
    """
    documento_asociado = models.ForeignKey(Factura, on_delete=models.PROTECT, verbose_name="Factura Relacionada")
    motivo = models.TextField(verbose_name="Motivo de la Nota de Crédito")
    
    class Meta:
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"


class NotaDebito(DocumentoFinanciero):
    """
    Modelo que representa una Nota de Débito.
    """
    documento_asociado = models.ForeignKey(Factura, on_delete=models.PROTECT, verbose_name="Factura Relacionada")
    motivo = models.TextField(verbose_name="Motivo de la Nota de Débito")
    
    class Meta:
        verbose_name = "Nota de Débito"
        verbose_name_plural = "Notas de Débito"


class Autofactura(DocumentoFinanciero):
    """
    Modelo que representa una Autofactura.
    """
    proveedor = models.ForeignKey('configuraciones_maestras.Proveedor', on_delete=models.PROTECT, verbose_name="Proveedor")
    
    class Meta:
        verbose_name = "Autofactura"
        verbose_name_plural = "Autofacturas"


class NotaRemision(DocumentoFinanciero):
    """
    Modelo que representa una Nota de Remisión.
    """
    destino = models.CharField(max_length=255, verbose_name="Lugar de Destino")
    transportista = models.CharField(max_length=255, verbose_name="Nombre del Transportista")
    
    class Meta:
        verbose_name = "Nota de Remisión"
        verbose_name_plural = "Notas de Remisión"


# --------------------------------------------------------------------------
# Modelo para los Ítems de los Documentos
# --------------------------------------------------------------------------
class ItemDocumento(models.Model):
    """
    Modelo que representa los ítems (productos o servicios) de un documento financiero.
    """
    documento = models.ForeignKey(DocumentoFinanciero, on_delete=models.CASCADE, related_name='items_documento')
    # Opcional: Referencia a un producto del inventario para auto-completar datos
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)

    descripcion = models.CharField(max_length=255, verbose_name="Descripción del Ítem")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")
    iva = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="IVA")
    
    class Meta:
        verbose_name = "Ítem de Documento"
        verbose_name_plural = "Ítems de Documentos"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ítem: {self.descripcion} ({self.cantidad})"