# configuraciones_maestras/admin.py

from django.contrib import admin
from .models import Proveedor, AgenteTransporte, DespachanteAduana, TasaCambio

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email', 'ruc')
    search_fields = ('nombre', 'ruc', 'contacto')
    list_filter = ('nombre',)

@admin.register(AgenteTransporte)
class AgenteTransporteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email', 'ruc')
    search_fields = ('nombre', 'ruc', 'contacto')
    list_filter = ('nombre',)

@admin.register(DespachanteAduana)
class DespachanteAduanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email', 'registro')
    search_fields = ('nombre', 'registro', 'contacto')
    list_filter = ('nombre',)

@admin.register(TasaCambio)
class TasaCambioAdmin(admin.ModelAdmin):
    list_display = ('moneda_origen', 'moneda_destino', 'valor', 'fecha_actualizacion')
    search_fields = ('moneda_origen', 'moneda_destino')
    list_filter = ('moneda_origen', 'moneda_destino', 'fecha_actualizacion')

