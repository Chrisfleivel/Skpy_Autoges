# inventario/views.py
from django.shortcuts import render, redirect
from .models import Vehiculo, Repuesto, MantenimientoVehiculo, Deposito, UnidadMedida
from django.contrib import messages
from .forms import VehiculoForm, RepuestoForm, MantenimientoForm, DepositoForm, UnidadMedidaForm
from django import forms
from django.contrib.auth.decorators import login_required
from seguridad_usuarios.decorators import requiere_privilegio

# Importar el decorador revisar_permiso
from seguridad_usuarios.decorators import revisar_permiso

# --------------------------------------------------------------------------
# Vistas para la gestión de Inventario
# --------------------------------------------------------------------------

@revisar_permiso('inventario.ver_inventario')
def lista_inventario(request):
    """
    Esta vista permite ver la lista de inventario, incluyendo vehículos, repuestos,
    mantenimientos, depósitos y unidades de medida.
    """
    vehiculos = Vehiculo.objects.all()
    repuestos = Repuesto.objects.all()
    mantenimientos = MantenimientoVehiculo.objects.all()
    depositos = Deposito.objects.all()
    unidades_medida = UnidadMedida.objects.all()
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')
        if search_query:
            vehiculos = vehiculos.filter(modelo__icontains=search_query) | vehiculos.filter(marca__icontains=search_query)
            repuestos = repuestos.filter(nombre__icontains=search_query) | repuestos.filter(codigo__icontains=search_query)
            mantenimientos = mantenimientos.filter(descripcion__icontains=search_query)
            depositos = depositos.filter(nombre__icontains=search_query)
            unidades_medida = unidades_medida.filter(nombre__icontains=search_query) | unidades_medida.filter(simbolo__icontains=search_query)
        else:
            messages.error(request, "Por favor ingrese un término de búsqueda.")
    return render(request, 'inventario/lista_inventario.html', {
        'vehiculos': vehiculos,
        'repuestos': repuestos,
        'mantenimientos': mantenimientos,
        'depositos': depositos,
        'unidades_medida': unidades_medida
    })


# --------------------------------------------------------------------------
# Vistas para la gestión de Vehículos
# --------------------------------------------------------------------------

@revisar_permiso('inventario.agregar_vehiculo')
def agregar_vehiculo(request):
    """Vista para agregar un nuevo vehículo al inventario."""
    if request.method == 'POST':
        # Lógica para procesar el formulario y agregar el vehículo
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_vehiculos')  # Redirige a la lista de vehículos (debes crear esta vista y url)
    else:
        form = VehiculoForm()
    return render(request, 'inventario/agregar_vehiculo.html', {'form': form})

@revisar_permiso('inventario.ver_vehiculo')
def lista_vehiculos(request):
    """Vista para ver la lista de vehículos en el inventario."""
    vehiculos = Vehiculo.objects.all()
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')
        if search_query:
            vehiculos = vehiculos.filter(modelo__icontains=search_query) | vehiculos.filter(marca__icontains=search_query)
        else:
            messages.error(request, "Por favor ingrese un término de búsqueda.")
    return render(request, 'inventario/lista_vehiculos.html', {'vehiculos': vehiculos})

@revisar_permiso('inventario.ver_vehiculo')
def detalle_vehiculo(request, vehiculo_id):
    """Vista para ver los detalles de un vehículo en el inventario."""
    vehiculo = Vehiculo.objects.get(id=vehiculo_id)
    return render(request, 'inventario/detalle_vehiculo.html', {'vehiculo': vehiculo})  

@revisar_permiso('inventario.eliminar_vehiculo')
def eliminar_vehiculo(request, vehiculo_id):
    vehiculo = Vehiculo.objects.get(id=vehiculo_id)
    vehiculo.delete()
    return redirect('lista_vehiculos')

@revisar_permiso('inventario.editar_vehiculo')
def editar_vehiculo(request, vehiculo_id):
    """Vista para editar un vehículo en el inventario."""
    vehiculo = Vehiculo.objects.get(id=vehiculo_id)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            return redirect('detalle_vehiculo', vehiculo_id=vehiculo.id)
    else:
        form = VehiculoForm(instance=vehiculo)
    return render(request, 'inventario/editar_vehiculo.html', {'form': form, 'vehiculo': vehiculo}) 


# --------------------------------------------------------------------------
# Vistas para la gestión de Repuestos
# --------------------------------------------------------------------------

@revisar_permiso('inventario.agregar_repuesto')
def agregar_repuesto(request):
    """Vista para agregar un nuevo repuesto al inventario."""
    if request.method == 'POST':
        form = RepuestoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_repuestos')  # Redirige a la lista de repuestos (debes crear esta vista y url)
    else:
        form = RepuestoForm()
    return render(request, 'inventario/agregar_repuesto.html', {'form': form})

@revisar_permiso('inventario.ver_repuesto_lista')
def lista_repuestos(request):
    """Vista para ver la lista de repuestos en el inventario."""
    repuestos = Repuesto.objects.all()
    return render(request, 'inventario/lista_repuestos.html', {'repuestos': repuestos})

@revisar_permiso('inventario.ver_repuesto')
def detalle_repuesto(request, repuesto_id):
    """Vista para ver los detalles de un repuesto en el inventario."""
    repuesto = Repuesto.objects.get(id=repuesto_id)
    return render(request, 'inventario/detalle_repuesto.html', {'repuesto': repuesto})

@revisar_permiso('inventario.eliminar_repuesto')
def eliminar_repuesto(request, repuesto_id):
    repuesto = Repuesto.objects.get(id=repuesto_id)
    repuesto.delete()
    return redirect('lista_repuestos')

@revisar_permiso('inventario.editar_repuesto')
def editar_repuesto(request, repuesto_id):
    repuesto = Repuesto.objects.get(id=repuesto_id)
    if request.method == 'POST':
        form = RepuestoForm(request.POST, instance=repuesto)
        if form.is_valid():
            form.save()
            return redirect('detalle_repuesto', repuesto_id=repuesto.id)
    else:
        form = RepuestoForm(instance=repuesto)
    return render(request, 'inventario/editar_repuesto.html', {'form': form, 'repuesto': repuesto})

# --------------------------------------------------------------------------
# Vistas para la gestión de Mantenimientos
# --------------------------------------------------------------------------

@login_required
def agregar_mantenimiento(request):
    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_mantenimientos')  # Redirige a la lista de mantenimientos (debes crear esta vista y url)
    else:
        form = MantenimientoForm()
    return render(request, 'inventario/agregar_mantenimiento.html', {'form': form})

@login_required
def lista_mantenimientos(request):
    mantenimientos = MantenimientoVehiculo.objects.all()
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')
        if search_query:
            mantenimientos = mantenimientos.filter(descripcion__icontains=search_query)
        else:
            messages.error(request, "Por favor ingrese un término de búsqueda.")
    return render(request, 'inventario/lista_mantenimientos.html', {'mantenimientos': mantenimientos})

def detalle_mantenimiento(request, mantenimiento_id):
    mantenimiento = MantenimientoVehiculo.objects.get(id=mantenimiento_id)
    return render(request, 'inventario/detalle_mantenimiento.html', {'mantenimiento': mantenimiento})

def eliminar_mantenimiento(request, mantenimiento_id):
    mantenimiento = MantenimientoVehiculo.objects.get(id=mantenimiento_id)
    mantenimiento.delete()
    return redirect('lista_mantenimientos')

def editar_mantenimiento(request, mantenimiento_id):
    mantenimiento = MantenimientoVehiculo.objects.get(id=mantenimiento_id)
    if request.method == 'POST':
        form = MantenimientoForm(request.POST, instance=mantenimiento)
        if form.is_valid():
            form.save()
            return redirect('detalle_mantenimiento', mantenimiento_id=mantenimiento.id)
    else:
        form = MantenimientoForm(instance=mantenimiento)
    return render(request, 'inventario/editar_mantenimiento.html', {'form': form, 'mantenimiento': mantenimiento})  

# --------------------------------------------------------------------------
# Vistas para la gestión de Depósitos
# --------------------------------------------------------------------------

@login_required
def agregar_deposito(request):
    if request.method == 'POST':
        form = DepositoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_depositos')  # Redirige a la lista de depósitos (debes crear esta vista y url)
    else:
        form = DepositoForm()
    return render(request, 'inventario/agregar_deposito.html', {'form': form})

@login_required
def lista_depositos(request):
    depositos = Deposito.objects.all()
    return render(request, 'inventario/lista_depositos.html', {'depositos': depositos})

def detalle_deposito(request, deposito_id):
    deposito = Deposito.objects.get(id=deposito_id)
    return render(request, 'inventario/detalle_deposito.html', {'deposito': deposito})

def eliminar_deposito(request, deposito_id):
    deposito = Deposito.objects.get(id=deposito_id)
    deposito.delete()
    return redirect('lista_depositos')

def editar_deposito(request, deposito_id):
    deposito = Deposito.objects.get(id=deposito_id)
    if request.method == 'POST':
        form = DepositoForm(request.POST, instance=deposito)
        if form.is_valid():
            form.save()
            return redirect('detalle_deposito', deposito_id=deposito.id)
    else:
        form = DepositoForm(instance=deposito)
    return render(request, 'inventario/editar_deposito.html', {'form': form, 'deposito': deposito})


# --------------------------------------------------------------------------
# Vistas para la gestión de Unidades de Medida
# --------------------------------------------------------------------------

@login_required
def agregar_unidad_medida(request):
    if request.method == 'POST':
        form = UnidadMedidaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_unidades_medida')  # Redirige a la lista de unidades de medida (debes crear esta vista y url)
    else:
        form = UnidadMedidaForm()
    return render(request, 'inventario/agregar_unidad_medida.html', {'form': form})

@login_required
def lista_unidades_medida(request):
    unidades = UnidadMedida.objects.all()
    return render(request, 'inventario/lista_unidades_medida.html', {'unidades': unidades})

def detalle_unidad_medida(request, unidad_id):
    unidad = UnidadMedida.objects.get(id=unidad_id)
    return render(request, 'inventario/detalle_unidad_medida.html', {'unidad': unidad})

def eliminar_unidad_medida(request, unidad_id):
    unidad = UnidadMedida.objects.get(id=unidad_id)
    unidad.delete()
    return redirect('lista_unidades_medida')

def editar_unidad_medida(request, unidad_id):
    unidad = UnidadMedida.objects.get(id=unidad_id)
    if request.method == 'POST':
        form = UnidadMedidaForm(request.POST, instance=unidad)
        if form.is_valid():
            form.save()
            return redirect('detalle_unidad_medida', unidad_id=unidad.id)
    else:
        form = UnidadMedidaForm(instance=unidad)
    return render(request, 'inventario/editar_unidad_medida.html', {'form': form, 'unidad': unidad})

