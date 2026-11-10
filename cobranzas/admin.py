from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'cliente_display', 'monto', 'metodo_pago', 'estado', 'fecha_pago')
    list_filter = ('estado', 'metodo_pago', 'tipo_pago', 'sucursal')
    search_fields = ('pedido__cliente__nombre', 'pedido__cliente__razon_social', 'metodo_pago', 'observaciones')
    readonly_fields = ('fecha_pago',)

    def cliente_display(self, obj):
        if obj.pedido and obj.pedido.cliente:
            return str(obj.pedido.cliente)
        return '-'

    cliente_display.short_description = 'Cliente'
