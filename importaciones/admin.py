from django.contrib import admin
from .models import (
    Embarque,
    EmbarqueContenedor,
    GastoImportacion,
    DespachoAduana,
    DocumentoAdjunto,
    ContenedorImportacion,
    PedidoProveedorImportacion,
)


@admin.register(Embarque)
class EmbarqueAdmin(admin.ModelAdmin):
    list_display = ('referencia_interna', 'bl_numero', 'estado', 'fecha_embarque', 'destino_final')
    list_filter = ('estado', 'bl_liberado', 'fecha_embarque')
    search_fields = ('referencia_interna', 'bl_numero', 'naviera', 'buque_viaje')
    readonly_fields = ('estado',)


@admin.register(EmbarqueContenedor)
class EmbarqueContenedorAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'sello', 'embarque', 'peso_bruto_kg', 'volumen_m3')
    list_filter = ('tipo',)
    search_fields = ('numero', 'sello', 'embarque__referencia_interna', 'embarque__bl_numero')


@admin.register(GastoImportacion)
class GastoImportacionAdmin(admin.ModelAdmin):
    list_display = ('embarque', 'tipo', 'monto', 'moneda', 'es_costeable')
    list_filter = ('tipo', 'moneda', 'es_costeable')
    search_fields = ('embarque__referencia_interna', 'descripcion', 'proveedor_servicio')


@admin.register(DespachoAduana)
class DespachoAduanaAdmin(admin.ModelAdmin):
    list_display = ('embarque', 'nro_despacho', 'fecha_oficializacion', 'canal')
    list_filter = ('canal', 'fecha_oficializacion')
    search_fields = ('embarque__referencia_interna', 'nro_despacho', 'aduana', 'despachante')


@admin.register(DocumentoAdjunto)
class DocumentoAdjuntoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'descripcion', 'archivo', 'embarque', 'factura')
    list_filter = ('tipo', 'embarque', 'factura')
    search_fields = ('descripcion', 'archivo')


@admin.register(ContenedorImportacion)
class ContenedorImportacionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'estado', 'fecha_embarque', 'despachante')
    list_filter = ('estado', 'fecha_embarque')
    search_fields = ('numero', 'descripcion')


@admin.register(PedidoProveedorImportacion)
class PedidoProveedorImportacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'proveedor', 'contenedor', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'contenedor', 'proveedor')
    search_fields = ('codigo', 'proveedor__nombre', 'proveedor__razon_social')

