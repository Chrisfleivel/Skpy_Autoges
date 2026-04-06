# configuraciones_maestras/admin.py

from django.contrib import admin
from .models import ConfiguracionApariencia, Proveedor, AgenteTransporte, DespachanteAduana, TasaCambio, Departamento, Cargo

admin.site.register(ConfiguracionApariencia)
admin.site.register(Proveedor)
admin.site.register(AgenteTransporte)
admin.site.register(DespachanteAduana)
admin.site.register(TasaCambio)
admin.site.register(Departamento)
admin.site.register(Cargo)
