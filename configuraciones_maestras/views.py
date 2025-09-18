# configuraciones_maestras/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Proveedor, AgenteTransporte, DespachanteAduana, TasaCambio
from .forms import ProveedorForm, AgenteTransporteForm, DespachanteAduanaForm, TasaCambioForm

# Vista principal de datos maestros
def home_maestras(request):
    return render(request, 'configuraciones_maestras/home_maestras.html')

# CRUD Proveedor
def agregar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'configuraciones_maestras/agregar_proveedor.html', {'form': form})

def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'configuraciones_maestras/editar_proveedor.html', {'form': form, 'proveedor': proveedor})

def inactivar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.inactivar()
        return redirect('lista_proveedores')
    return render(request, 'configuraciones_maestras/inactivar_proveedor.html', {'proveedor': proveedor})

def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        return redirect('lista_proveedores')
    return render(request, 'configuraciones_maestras/eliminar_proveedor.html', {'proveedor': proveedor})

def detalle_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_proveedor.html', {'proveedor': proveedor})

# Listado de proveedores
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    # filtro por estado y nombre
    if 'estado' in request.GET: 
        if request.GET['estado'] == 'ACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                proveedores = proveedores.filter(nombre__icontains=request.GET['nombre'], estado= True)
            else:
                proveedores = proveedores.filter(estado= True)
        elif request.GET['estado'] == 'INACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                proveedores = proveedores.filter(nombre__icontains=request.GET['nombre'], estado= False)
            else:
                proveedores = proveedores.filter(estado= False)
        else:
            if 'nombre' in request.GET and request.GET['nombre']:
                proveedores = proveedores.filter(nombre__icontains=request.GET['nombre'])
            
    return render(request, 'configuraciones_maestras/lista_proveedores.html', {'proveedores': proveedores})

# CRUD AgenteTransporte
def agregar_agente_transporte(request):
    if request.method == 'POST':
        form = AgenteTransporteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_agentes_transporte')
    else:
        form = AgenteTransporteForm()
    return render(request, 'configuraciones_maestras/agregar_agente_transporte.html', {'form': form})

def editar_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    if request.method == 'POST':
        form = AgenteTransporteForm(request.POST, instance=agente)
        if form.is_valid():
            form.save()
            return redirect('lista_agentes_transporte')
    else:
        form = AgenteTransporteForm(instance=agente)
    return render(request, 'configuraciones_maestras/editar_agente_transporte.html', {'form': form, 'agente': agente})

def eliminar_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    if request.method == 'POST':
        agente.delete()
        return redirect('lista_agentes_transporte')
    return render(request, 'configuraciones_maestras/eliminar_agente_transporte.html', {'agente': agente})

def detalle_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_agente_transporte.html', {'agente': agente})

# Listado de agentes de transporte
def lista_agentes_transporte(request):
    # filtro por estado y nombre
    agentes = AgenteTransporte.objects.all()
    if 'estado' in request.GET:
        if request.GET['estado'] == 'ACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                agentes = agentes.filter(nombre__icontains=request.GET['nombre'], estado=True)
            else:
                agentes = agentes.filter(estado=True)
        elif request.GET['estado'] == 'INACTIVO':
            if 'nombre' in request.GET and request.GET['nombre']:
                agentes = agentes.filter(nombre__icontains=request.GET['nombre'], estado=False)
            else:
                agentes = agentes.filter(estado=False)
        else:
            if 'nombre' in request.GET and request.GET['nombre']:
                agentes = agentes.filter(nombre__icontains=request.GET['nombre'])

    return render(request, 'configuraciones_maestras/lista_agentes_transporte.html', {'agentes': agentes})

# CRUD DespachanteAduana
def agregar_despachante_aduana(request):
    if request.method == 'POST':
        form = DespachanteAduanaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_despachantes_aduana')
    else:
        form = DespachanteAduanaForm()
    return render(request, 'configuraciones_maestras/agregar_despachante_aduana.html', {'form': form})

def editar_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    if request.method == 'POST':
        form = DespachanteAduanaForm(request.POST, instance=despachante)
        if form.is_valid():
            form.save()
            return redirect('lista_despachantes_aduana')
    else:
        form = DespachanteAduanaForm(instance=despachante)
    return render(request, 'configuraciones_maestras/editar_despachante_aduana.html', {'form': form, 'despachante': despachante})

def eliminar_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    if request.method == 'POST':
        despachante.delete()
        return redirect('lista_despachantes_aduana')
    return render(request, 'configuraciones_maestras/eliminar_despachante_aduana.html', {'despachante': despachante})

def detalle_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_despachante_aduana.html', {'despachante': despachante})

# Listado de despachantes de aduana
def lista_despachantes_aduana(request):
    despachantes = DespachanteAduana.objects.all()
    return render(request, 'configuraciones_maestras/lista_despachantes_aduana.html', {'despachantes': despachantes})

# CRUD TasaCambio
def agregar_tasa_cambio(request):
    if request.method == 'POST':
        form = TasaCambioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_tasas_cambio')
    else:
        form = TasaCambioForm()
    return render(request, 'configuraciones_maestras/agregar_tasa_cambio.html', {'form': form})

def editar_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    if request.method == 'POST':
        form = TasaCambioForm(request.POST, instance=tasa)
        if form.is_valid():
            form.save()
            return redirect('lista_tasas_cambio')
    else:
        form = TasaCambioForm(instance=tasa)
    return render(request, 'configuraciones_maestras/editar_tasa_cambio.html', {'form': form, 'tasa': tasa})

def eliminar_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    if request.method == 'POST':
        tasa.delete()
        return redirect('lista_tasas_cambio')
    return render(request, 'configuraciones_maestras/eliminar_tasa_cambio.html', {'tasa': tasa})

def detalle_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_tasa_cambio.html', {'tasa': tasa})

# Listado de tasas de cambio
def lista_tasas_cambio(request):
    tasas = TasaCambio.objects.all()
    return render(request, 'configuraciones_maestras/lista_tasas_cambio.html', {'tasas': tasas})

