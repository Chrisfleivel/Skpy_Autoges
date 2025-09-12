from django.contrib import admin
from .models import Vehiculo, Repuesto, MantenimientoVehiculo, Deposito, UnidadMedida


admin.site.register(Vehiculo)
admin.site.register(Repuesto)
admin.site.register(MantenimientoVehiculo)
admin.site.register(Deposito)
admin.site.register(UnidadMedida)

