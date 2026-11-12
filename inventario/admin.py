from django.contrib import admin
from .models import (
    Vehiculo,
    VehiculoFoto,
    Repuesto,
    MantenimientoVehiculo,
    Deposito,
    UnidadMedida,
    CategoriaRepuesto,
)


class VehiculoFotoInline(admin.TabularInline):
    """Galería de fotos del vehículo."""

    model = VehiculoFoto
    extra = 1
    fields = ['imagen', 'descripcion', 'orden']
    ordering = ['orden', 'id']


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    inlines = [VehiculoFotoInline]


admin.site.register(Repuesto)
admin.site.register(MantenimientoVehiculo)
admin.site.register(Deposito)
admin.site.register(UnidadMedida)


@admin.register(CategoriaRepuesto)
class CategoriaRepuestoAdmin(admin.ModelAdmin):
    """Las categorías se manejan desde el sistema; el admin solo las muestra."""

    list_display = ['nombre', 'padre', 'estado', 'cantidad_repuestos']
    list_filter = ['estado', 'padre']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']

    @admin.display(description='Repuestos')
    def cantidad_repuestos(self, obj):
        return obj.repuesto_set.count()
