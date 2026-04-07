# configuraciones_maestras/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Proveedor, AgenteTransporte, DespachanteAduana, TasaCambio, Departamento, Cargo
from .forms import ProveedorForm, AgenteTransporteForm, DespachanteAduanaForm, TasaCambioForm, DepartamentoForm, CargoForm
from seguridad_usuarios.decorators import revisar_permiso
# login_required
from django.contrib.auth.decorators import login_required

# Vista principal de datos maestros
def home_maestras(request):
    return render(request, 'configuraciones_maestras/home_maestras.html')

# CRUD Proveedor
@revisar_permiso('configuraciones_maestras.agregar_proveedor')
def agregar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'configuraciones_maestras/agregar_proveedor.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_proveedor')
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

@revisar_permiso('configuraciones_maestras.inactivar_proveedor')
def inactivar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.inactivar()
        return redirect('lista_proveedores')
    return render(request, 'configuraciones_maestras/inactivar_proveedor.html', {'proveedor': proveedor})

@revisar_permiso('configuraciones_maestras.eliminar_proveedor')
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        return redirect('lista_proveedores')
    return render(request, 'configuraciones_maestras/eliminar_proveedor.html', {'proveedor': proveedor})

@revisar_permiso('configuraciones_maestras.detallar_proveedor')
def detalle_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_proveedor.html', {'proveedor': proveedor})

# Listado de proveedores
@revisar_permiso('configuraciones_maestras.listar_proveedores')
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
@revisar_permiso('configuraciones_maestras.agregar_agente_transporte')
def agregar_agente_transporte(request):
    if request.method == 'POST':
        form = AgenteTransporteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_agentes_transporte')
    else:
        form = AgenteTransporteForm()
    return render(request, 'configuraciones_maestras/agregar_agente_transporte.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_agente_transporte')
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

@revisar_permiso('configuraciones_maestras.eliminar_agente_transporte')
def eliminar_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    if request.method == 'POST':
        agente.delete()
        return redirect('lista_agentes_transporte')
    return render(request, 'configuraciones_maestras/eliminar_agente_transporte.html', {'agente': agente})

@revisar_permiso('configuraciones_maestras.detallar_agente_transporte')
def detalle_agente_transporte(request, pk):
    agente = get_object_or_404(AgenteTransporte, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_agente_transporte.html', {'agente': agente})

# Listado de agentes de transporte
@revisar_permiso('configuraciones_maestras.listar_agentes_transporte')
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
@revisar_permiso('configuraciones_maestras.agregar_despachante_aduana')
def agregar_despachante_aduana(request):
    if request.method == 'POST':
        form = DespachanteAduanaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_despachantes_aduana')
    else:
        form = DespachanteAduanaForm()
    return render(request, 'configuraciones_maestras/agregar_despachante_aduana.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_despachante_aduana')
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

@revisar_permiso('configuraciones_maestras.eliminar_despachante_aduana')
def eliminar_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    if request.method == 'POST':
        despachante.delete()
        return redirect('lista_despachantes_aduana')
    return render(request, 'configuraciones_maestras/eliminar_despachante_aduana.html', {'despachante': despachante})

@revisar_permiso('configuraciones_maestras.detallar_despachante_aduana')
def detalle_despachante_aduana(request, pk):
    despachante = get_object_or_404(DespachanteAduana, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_despachante_aduana.html', {'despachante': despachante})

# Listado de despachantes de aduana
@revisar_permiso('configuraciones_maestras.listar_despachantes_aduana')
def lista_despachantes_aduana(request):
    despachantes = DespachanteAduana.objects.all()
    return render(request, 'configuraciones_maestras/lista_despachantes_aduana.html', {'despachantes': despachantes})

# CRUD TasaCambio
@revisar_permiso('configuraciones_maestras.agregar_tasa_cambio')
def agregar_tasa_cambio(request):
    if request.method == 'POST':
        form = TasaCambioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_tasas_cambio')
    else:
        form = TasaCambioForm()
    return render(request, 'configuraciones_maestras/agregar_tasa_cambio.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_tasa_cambio')
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

@revisar_permiso('configuraciones_maestras.eliminar_tasa_cambio')
def eliminar_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    if request.method == 'POST':
        tasa.delete()
        return redirect('lista_tasas_cambio')
    return render(request, 'configuraciones_maestras/eliminar_tasa_cambio.html', {'tasa': tasa})

@revisar_permiso('configuraciones_maestras.detallar_tasa_cambio')
def detalle_tasa_cambio(request, pk):
    tasa = get_object_or_404(TasaCambio, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_tasa_cambio.html', {'tasa': tasa})

# Listado de tasas de cambio
@revisar_permiso('configuraciones_maestras.listar_tasas_cambio')
def lista_tasas_cambio(request):
    tasas = TasaCambio.objects.all()
    return render(request, 'configuraciones_maestras/lista_tasas_cambio.html', {'tasas': tasas})

# --------------------------------------------------------------------------
# Vista de Departamentos
# --------------------------------------------------------------------------

@revisar_permiso('configuraciones_maestras.listar_departamentos')
def lista_departamentos(request):
    departamentos = Departamento.objects.all()
    return render(request, 'configuraciones_maestras/lista_departamentos.html', {'departamentos': departamentos})

@revisar_permiso('configuraciones_maestras.agregar_departamento')
def agregar_departamento(request):
    if request.method == 'POST':
        form = DepartamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_departamentos')
    else:
        form = DepartamentoForm()
    return render(request, 'configuraciones_maestras/agregar_departamento.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_departamento')
def editar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        form = DepartamentoForm(request.POST, instance=departamento)
        if form.is_valid():
            form.save()
            return redirect('lista_departamentos')
    else:
        form = DepartamentoForm(instance=departamento)
    return render(request, 'configuraciones_maestras/editar_departamento.html', {'form': form, 'departamento': departamento})

@revisar_permiso('configuraciones_maestras.eliminar_departamento')
def eliminar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        departamento.delete()
        return redirect('lista_departamentos')
    return render(request, 'configuraciones_maestras/eliminar_departamento.html', {'departamento': departamento})

@revisar_permiso('configuraciones_maestras.detallar_departamento')
def detalle_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_departamento.html', {'departamento': departamento})

#desactivar departamento
@revisar_permiso('configuraciones_maestras.inactivar_departamento')
def inactivar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        departamento.inactivar()
        return redirect('lista_departamentos')
    return render(request, 'configuraciones_maestras/inactivar_departamento.html', {'departamento': departamento})

# activar departamento
@revisar_permiso('configuraciones_maestras.activar_departamento')
def activar_departamento(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    if request.method == 'POST':
        departamento.activar()
        return redirect('lista_departamentos')
    return render(request, 'configuraciones_maestras/activar_departamento.html', {'departamento': departamento})


# --------------------------------------------------------------------------
# Vista de Cargos
# --------------------------------------------------------------------------

@revisar_permiso('configuraciones_maestras.listar_cargos')
def lista_cargos(request):
    cargos = Cargo.objects.all()
    return render(request, 'configuraciones_maestras/lista_cargos.html', {'cargos': cargos})

@revisar_permiso('configuraciones_maestras.agregar_cargo')
def agregar_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_cargos')
    else:
        form = CargoForm()
    return render(request, 'configuraciones_maestras/agregar_cargo.html', {'form': form})

@revisar_permiso('configuraciones_maestras.editar_cargo')
def editar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        form = CargoForm(request.POST, instance=cargo)
        if form.is_valid():
            form.save()
            return redirect('lista_cargos')
    else:
        form = CargoForm(instance=cargo)
    return render(request, 'configuraciones_maestras/editar_cargo.html', {'form': form, 'cargo': cargo})

@revisar_permiso('configuraciones_maestras.eliminar_cargo')
def eliminar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        cargo.delete()
        return redirect('lista_cargos')
    return render(request, 'configuraciones_maestras/eliminar_cargo.html', {'cargo': cargo})

@revisar_permiso('configuraciones_maestras.detallar_cargo')
def detalle_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    return render(request, 'configuraciones_maestras/detalle_cargo.html', {'cargo': cargo})

# activar cargo
@revisar_permiso('configuraciones_maestras.activar_cargo')
def activar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        cargo.activar()
        return redirect('lista_cargos')
    return render(request, 'configuraciones_maestras/activar_cargo.html', {'cargo': cargo})

# desactivar cargo
@revisar_permiso('configuraciones_maestras.inactivar_cargo')
def inactivar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        cargo.inactivar()
        return redirect('lista_cargos')
    return render(request, 'configuraciones_maestras/inactivar_cargo.html', {'cargo': cargo})




permisos_iniciales_configuraciones_maestras = [
        {
            'codename': 'configuraciones_maestras.agregar_proveedor',
            'nombre': 'Agregar Proveedor',
            'descripcion': 'Permite registrar nuevos Proveedores.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_proveedor',
            'nombre': 'Editar Proveedor',
            'descripcion': 'Permite editar los datos de Proveedores existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_proveedor',
            'nombre': 'Eliminar Proveedor',
            'descripcion': 'Permite eliminar Proveedores del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.inactivar_proveedor',
            'nombre': 'Inactivar Proveedor',
            'descripcion': 'Permite inactivar Proveedores del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_proveedores',
            'nombre': 'Listar Proveedores',
            'descripcion': 'Permite ver la lista de Proveedores registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_proveedor',
            'nombre': 'Detalle de Proveedor',
            'descripcion': 'Permite ver el detalle de un Proveedor.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_agente_transporte',
            'nombre': 'Agregar Agente de Transporte',
            'descripcion': 'Permite registrar nuevos Agentes de Transporte.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_agente_transporte',
            'nombre': 'Editar Agente de Transporte',
            'descripcion': 'Permite editar los datos de Agentes de Transporte existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_agente_transporte',
            'nombre': 'Eliminar Agente de Transporte',
            'descripcion': 'Permite eliminar Agentes de Transporte del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_agentes_transporte',
            'nombre': 'Listar Agentes de Transporte',
            'descripcion': 'Permite ver la lista de Agentes de Transporte registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_agente_transporte',
            'nombre': 'Detalle de Agente de Transporte',
            'descripcion': 'Permite ver el detalle de un Agente de Transporte.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_despachante_aduana',
            'nombre': 'Agregar Despachante de Aduana',
            'descripcion': 'Permite registrar nuevos Despachantes de Aduana.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_despachante_aduana',
            'nombre': 'Editar Despachante de Aduana',
            'descripcion': 'Permite editar los datos de Despachantes de Aduana existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_despachante_aduana',
            'nombre': 'Eliminar Despachante de Aduana',
            'descripcion': 'Permite eliminar Despachantes de Aduana del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_despachantes_aduana',
            'nombre': 'Listar Despachantes de Aduana',
            'descripcion': 'Permite ver la lista de Despachantes de Aduana registrados.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_despachante_aduana',
            'nombre': 'Detalle de Despachante de Aduana',
            'descripcion': 'Permite ver el detalle de un Despachante de Aduana.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.agregar_tasa_cambio',
            'nombre': 'Agregar Tasa de Cambio',
            'descripcion': 'Permite registrar nuevas Tasas de Cambio.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.editar_tasa_cambio',
            'nombre': 'Editar Tasa de Cambio',
            'descripcion': 'Permite editar los datos de Tasas de Cambio existentes.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.eliminar_tasa_cambio',
            'nombre': 'Eliminar Tasa de Cambio',
            'descripcion': 'Permite eliminar Tasas de Cambio del sistema.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.listar_tasas_cambio',
            'nombre': 'Listar Tasas de Cambio',
            'descripcion': 'Permite ver la lista de Tasas de Cambio registradas.',
            'sector': 'Configuraciones Maestras'
        },
        {
            'codename': 'configuraciones_maestras.detallar_tasa_cambio',
            'nombre': 'Detalle de Tasa de Cambio',
            'descripcion': 'Permite ver el detalle de una Tasa de Cambio.',
            'sector': 'Configuraciones Maestras'
        },
        
    ]
