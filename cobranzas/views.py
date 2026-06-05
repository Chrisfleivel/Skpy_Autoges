from django.shortcuts import render
from seguridad_usuarios.decorators import revisar_permiso

# CRUD de cobranzas
@revisar_permiso('cobranzas.agregar_venta')
def agregar_venta(request):
    """Vista para agregar una nueva venta."""
    # Lógica para agregar una venta
    return render(request, 'cobranzas/agregar_venta.html')
