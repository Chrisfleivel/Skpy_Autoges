# inventario/views.py
from django.shortcuts import render, redirect
from .models import Vehiculo, Repuesto, MantenimientoVehiculo, Deposito, UnidadMedida, MarcaVehiculo, TipoVehiculo, ModeloVehiculo, TipoTransmision
from django.contrib import messages
from .forms import VehiculoForm, RepuestoForm, MantenimientoForm, DepositoForm, UnidadMedidaForm, MarcaVehiculoForm, TipoVehiculoForm, ModeloVehiculoForm, TipoTransmisionForm
from django import forms
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from seguridad_usuarios.decorators import requiere_privilegio

# Importar el decorador revisar_permiso
from seguridad_usuarios.decorators import revisar_permiso
from django.db import models

# --------------------------------------------------------------------------
# Vistas para la gestión de Inventario
# --------------------------------------------------------------------------

@revisar_permiso('inventario.listar_inventario')
def lista_inventario(request):
    """
    Esta vista permite ver la lista de inventario, incluyendo vehículos, repuestos,
    mantenimientos, depósitos y unidades de medida con filtros de búsqueda.
    """
    # Obtener todos los elementos inicialmente
    vehiculos = Vehiculo.objects.all()
    repuestos = Repuesto.objects.all()
    mantenimientos = MantenimientoVehiculo.objects.all()
    depositos = Deposito.objects.all()
    unidades_medida = UnidadMedida.objects.all()

    # Capturar parámetros GET
    search_query = request.GET.get('search_query', '')
    tipo_filtro = request.GET.get('tipo', '')

    # Aplicar filtros si hay búsqueda
    if search_query:
        if tipo_filtro == 'vehiculo' or not tipo_filtro:
            vehiculos = vehiculos.filter(
                models.Q(modelo__icontains=search_query) |
                models.Q(marca__icontains=search_query) |
                models.Q(nombre__icontains=search_query)
            )

        if tipo_filtro == 'repuesto' or not tipo_filtro:
            repuestos = repuestos.filter(
                models.Q(nombre__icontains=search_query) |
                models.Q(codigo_repuesto__icontains=search_query)
            )

        if tipo_filtro == 'mantenimiento' or not tipo_filtro:
            mantenimientos = mantenimientos.filter(
                models.Q(descripcion__icontains=search_query) |
                models.Q(observaciones__icontains=search_query)
            )

        if tipo_filtro == 'deposito' or not tipo_filtro:
            depositos = depositos.filter(
                models.Q(nombre__icontains=search_query) |
                models.Q(ubicacion__icontains=search_query)
            )

        if tipo_filtro == 'unidad_medida' or not tipo_filtro:
            unidades_medida = unidades_medida.filter(
                models.Q(nombre__icontains=search_query) |
                models.Q(abreviatura__icontains=search_query)
            )

    return render(request, 'inventario/lista_inventario.html', {
        'vehiculos': vehiculos,
        'repuestos': repuestos,
        'mantenimientos': mantenimientos,
        'depositos': depositos,
        'unidades_medida': unidades_medida,
        'search_query': search_query,
        'tipo_filtro': tipo_filtro
    })


# --------------------------------------------------------------------------
# Vistas para la gestión de Vehículos
# --------------------------------------------------------------------------

@revisar_permiso('inventario.agregar_vehiculo')
def agregar_vehiculo(request):
    """Vista para agregar un nuevo vehículo al inventario."""
    if request.method == 'POST':
        # Lógica para procesar el formulario y agregar el vehículo
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo = form.cleaned_data.get('nuevo_modelo')
            estado = form.cleaned_data.get('estado') or 'disponible'
            # Si se escribió un nuevo modelo, crear o obtener y asignar
            if nuevo and form.cleaned_data.get('marca') and not form.cleaned_data.get('modelo'):
                marca = form.cleaned_data.get('marca')
                modelo_obj, _ = ModeloVehiculo.objects.get_or_create(marca=marca, nombre=nuevo)
                vehiculo = form.save(commit=False)
                vehiculo.modelo = modelo_obj
            else:
                vehiculo = form.save(commit=False)
            vehiculo.tipo = 'vehiculo'
            vehiculo.estado = estado
            # Asignar valores requeridos que no están en el formulario
            if vehiculo.costo_compra is None:
                vehiculo.costo_compra = 0
            if vehiculo.precio_venta is None:
                vehiculo.precio_venta = 0
            vehiculo.save()
            return redirect('lista_vehiculos')  # Redirige a la lista de vehículos
        else:
            # Debug: imprimir errores del formulario
            print(f"Errores del formulario: {form.errors}")
    else:
        form = VehiculoForm()
    return render(request, 'inventario/agregar_vehiculo.html', {'form': form})


def ajax_modelos_por_marca(request):
    """Endpoint AJAX que retorna JSON con modelos filtrados por marca."""
    marca_id = request.GET.get('marca_id')
    modelos = []
    if marca_id:
        qs = ModeloVehiculo.objects.filter(marca_id=marca_id).order_by('nombre')
        modelos = list(qs.values('id', 'nombre'))
    return JsonResponse({'modelos': modelos})


@revisar_permiso('inventario.listar_vehiculos')
def lista_vehiculos(request):
    """Vista mejorada con filtros avanzados."""
    vehiculos = Vehiculo.objects.all()

    # Capturar parámetros GET
    query = request.GET.get('search_query', '')
    marca = request.GET.get('marca', '')
    anio_min = request.GET.get('anio_min')
    anio_max = request.GET.get('anio_max')
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')

    # Filtro de texto (Modelo)
    if query:
        vehiculos = vehiculos.filter(modelo__nombre__icontains=query)
    
    # Filtro por Marca exacta
    if marca:
        vehiculos = vehiculos.filter(marca=marca)

    # Filtros de Rango de Año
    if anio_min:
        vehiculos = vehiculos.filter(año__gte=anio_min)
    if anio_max:
        vehiculos = vehiculos.filter(año__lte=anio_max)

    # Filtros de Rango de Precio
    if precio_min:
        vehiculos = vehiculos.filter(costo_compra__gte=precio_min)
    if precio_max:
        vehiculos = vehiculos.filter(costo_compra__lte=precio_max)

    # Obtener marcas únicas para el select del template
    marcas_disponibles = Vehiculo.objects.values_list('marca', flat=True).distinct()

    return render(request, 'inventario/lista_vehiculos.html', {
        'vehiculos': vehiculos,
        'marcas': marcas_disponibles
    })

@revisar_permiso('inventario.detallar_vehiculo')
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
        form = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            nuevo = form.cleaned_data.get('nuevo_modelo')
            if nuevo and form.cleaned_data.get('marca') and not form.cleaned_data.get('modelo'):
                marca = form.cleaned_data.get('marca')
                modelo_obj, _ = ModeloVehiculo.objects.get_or_create(marca=marca, nombre=nuevo)
                veh = form.save(commit=False)
                veh.modelo = modelo_obj
                veh.save()
            else:
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
        form = RepuestoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_repuestos')
    else:
        form = RepuestoForm()
    return render(request, 'inventario/agregar_repuesto.html', {'form': form})

@revisar_permiso('inventario.listar_repuestos')
def lista_repuestos(request):
    """Vista mejorada para ver la lista de repuestos con filtros avanzados."""
    repuestos = Repuesto.objects.all()

    # Capturar parámetros GET
    query = request.GET.get('search_query', '')
    categoria = request.GET.get('categoria', '')
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    stock_min = request.GET.get('stock_min')

    # Filtro de texto (Nombre o Código)
    if query:
        repuestos = repuestos.filter(
            models.Q(nombre__icontains=query) | 
            models.Q(codigo_repuesto__icontains=query)
        )
    
    # Filtro por Categoría exacta
    if categoria:
        repuestos = repuestos.filter(categoria=categoria)

    # Filtros de Rango de Precio
    if precio_min:
        repuestos = repuestos.filter(precio_venta__gte=precio_min)
    if precio_max:
        repuestos = repuestos.filter(precio_venta__lte=precio_max)

    # Filtro por Stock Disponible
    if stock_min:
        repuestos = repuestos.filter(stock_actual__gte=stock_min)

    # Obtener categorías únicas para el select del template
    categorias_disponibles = Repuesto.objects.values_list('categoria', flat=True).distinct().exclude(categoria__isnull=True).exclude(categoria='')

    return render(request, 'inventario/lista_repuestos.html', {
        'repuestos': repuestos,
        'categorias': categorias_disponibles
    })

@revisar_permiso('inventario.detallar_repuesto')
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

@revisar_permiso('inventario.agregar_mantenimiento')
def agregar_mantenimiento(request):
    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_mantenimientos')  # Redirige a la lista de mantenimientos (debes crear esta vista y url)
    else:
        form = MantenimientoForm()
    return render(request, 'inventario/agregar_mantenimiento.html', {'form': form})

@revisar_permiso('inventario.listar_mantenimientos')
def lista_mantenimientos(request):
    """Vista mejorada para ver la lista de mantenimientos con filtros avanzados."""
    mantenimientos = MantenimientoVehiculo.objects.all().select_related('vehiculo')

    # Capturar parámetros GET
    query = request.GET.get('search_query', '')
    vehiculo = request.GET.get('vehiculo', '')
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    costo_min = request.GET.get('costo_min')
    costo_max = request.GET.get('costo_max')

    # Filtro de texto (Descripción)
    if query:
        mantenimientos = mantenimientos.filter(
            models.Q(descripcion__icontains=query) |
            models.Q(observaciones__icontains=query)
        )

    # Filtro por Vehículo
    if vehiculo:
        mantenimientos = mantenimientos.filter(vehiculo_id=vehiculo)

    # Filtro por Estado del Mantenimiento
    if estado:
        mantenimientos = mantenimientos.filter(estado_mantenimiento=estado)

    # Filtros de Fecha
    if fecha_desde:
        mantenimientos = mantenimientos.filter(fecha_mantenimiento__gte=fecha_desde)
    if fecha_hasta:
        mantenimientos = mantenimientos.filter(fecha_mantenimiento__lte=fecha_hasta)

    # Filtros de Costo
    if costo_min:
        mantenimientos = mantenimientos.filter(costo__gte=costo_min)
    if costo_max:
        mantenimientos = mantenimientos.filter(costo__lte=costo_max)

    # Obtener listas para los filtros
    vehiculos_disponibles = Vehiculo.objects.all()
    estados_disponibles = MantenimientoVehiculo.ESTADO_MANTENIMIENTO

    return render(request, 'inventario/lista_mantenimientos.html', {
        'mantenimientos': mantenimientos,
        'vehiculos': vehiculos_disponibles,
        'estados_mantenimiento': estados_disponibles,
        'query': query,
        'vehiculo': vehiculo,
        'estado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'costo_min': costo_min,
        'costo_max': costo_max
    })

@revisar_permiso('inventario.detallar_mantenimiento')
def detalle_mantenimiento(request, mantenimiento_id):
    mantenimiento = MantenimientoVehiculo.objects.get(id=mantenimiento_id)
    return render(request, 'inventario/detalle_mantenimiento.html', {'mantenimiento': mantenimiento})

@revisar_permiso('inventario.eliminar_mantenimiento')
def eliminar_mantenimiento(request, mantenimiento_id):
    mantenimiento = MantenimientoVehiculo.objects.get(id=mantenimiento_id)
    mantenimiento.delete()
    return redirect('lista_mantenimientos')

@revisar_permiso('inventario.editar_mantenimiento')
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

@revisar_permiso('inventario.agregar_deposito')
def agregar_deposito(request):
    if request.method == 'POST':
        form = DepositoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_depositos')  # Redirige a la lista de depósitos (debes crear esta vista y url)
    else:
        form = DepositoForm()
    return render(request, 'inventario/agregar_deposito.html', {'form': form})

@revisar_permiso('inventario.listar_depositos')
def lista_depositos(request):
    """Vista mejorada para ver la lista de depósitos con filtros avanzados."""
    depositos = Deposito.objects.all()

    # Capturar parámetros GET
    query = request.GET.get('search_query', '')
    capacidad_min = request.GET.get('capacidad_min')
    capacidad_max = request.GET.get('capacidad_max')

    # Filtro de texto (Nombre o Ubicación)
    if query:
        depositos = depositos.filter(
            models.Q(nombre__icontains=query) | 
            models.Q(ubicacion__icontains=query)
        )
    
    # Filtros de Rango de Capacidad
    if capacidad_min:
        depositos = depositos.filter(capacidad_maxima__gte=capacidad_min)
    if capacidad_max:
        depositos = depositos.filter(capacidad_maxima__lte=capacidad_max)

    return render(request, 'inventario/lista_depositos.html', {
        'depositos': depositos,
        'query': query,
        'capacidad_min': capacidad_min,
        'capacidad_max': capacidad_max
    })

@revisar_permiso('inventario.detallar_deposito')
def detalle_deposito(request, deposito_id):
    deposito = Deposito.objects.get(id=deposito_id)
    return render(request, 'inventario/detalle_deposito.html', {'deposito': deposito})

@revisar_permiso('inventario.eliminar_deposito')
def eliminar_deposito(request, deposito_id):
    deposito = Deposito.objects.get(id=deposito_id)
    if deposito.eliminable():
        deposito.delete()
    else:
        messages.error(request, 'No se puede eliminar este depósito porque tiene vehículos o repuestos asociados.')
    return redirect('lista_depositos')

@revisar_permiso('inventario.editar_deposito')
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

@revisar_permiso('inventario.agregar_unidad_medida')
def agregar_unidad_medida(request):
    if request.method == 'POST':
        form = UnidadMedidaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_unidades_medida')  # Redirige a la lista de unidades de medida (debes crear esta vista y url)
    else:
        form = UnidadMedidaForm()
    return render(request, 'inventario/agregar_unidad_medida.html', {'form': form})

@revisar_permiso('inventario.listar_unidades_medida')
def lista_unidades_medida(request):
    """Vista mejorada para ver la lista de unidades de medida con filtros avanzados."""
    unidades_medida = UnidadMedida.objects.all()

    # Capturar parámetros GET
    query = request.GET.get('search_query', '')

    # Filtro de texto (Nombre o Abreviatura)
    if query:
        unidades_medida = unidades_medida.filter(
            models.Q(nombre__icontains=query) | models.Q(abreviatura__icontains=query)
        )

    return render(request, 'inventario/lista_unidades_medida.html', {
        'unidades_medida': unidades_medida,
        'query': query
    })

@revisar_permiso('inventario.detallar_unidad_medida')
def detalle_unidad_medida(request, unidad_id):
    unidad = UnidadMedida.objects.get(id=unidad_id)
    return render(request, 'inventario/detalle_unidad_medida.html', {'unidad': unidad})

@revisar_permiso('inventario.eliminar_unidad_medida')
def eliminar_unidad_medida(request, unidad_id):
    unidad = UnidadMedida.objects.get(id=unidad_id)
    if unidad.eliminable():
        unidad.delete()
    else:
        messages.error(request, 'No se puede eliminar esta unidad de medida porque tiene repuestos asociados.')
    return redirect('lista_unidades_medida')

@revisar_permiso('inventario.editar_unidad_medida')
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

# --------------------------------------------------------------------------
# Vistas para la gestión de Marcas de Vehículos
# --------------------------------------------------------------------------

@revisar_permiso('inventario.agregar_marcas_vehiculos')
def agregar_marca_vehiculo(request):
    if request.method == 'POST':
        form = MarcaVehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_marcas_vehiculos')
    else:
        form = MarcaVehiculoForm()
    return render(request, 'inventario/agregar_marca_vehiculo.html', {'form': form})

@revisar_permiso('inventario.listar_marcas_vehiculos')
def lista_marcas_vehiculos(request):
    marcas = MarcaVehiculo.objects.all()
    query = request.GET.get('search_query', '')
    if query:
        marcas = marcas.filter(nombre__icontains=query)
    return render(request, 'inventario/lista_marcas_vehiculos.html', {
        'marcas': marcas,
        'query': query
    })

@revisar_permiso('inventario.detallar_marcas_vehiculos')
def detalle_marca_vehiculo(request, marca_id):
    marca = MarcaVehiculo.objects.get(id=marca_id)
    return render(request, 'inventario/detalle_marca_vehiculo.html', {'marca': marca})

@revisar_permiso('inventario.editar_marcas_vehiculos')
def editar_marca_vehiculo(request, marca_id):
    marca = MarcaVehiculo.objects.get(id=marca_id)
    if request.method == 'POST':
        form = MarcaVehiculoForm(request.POST, instance=marca)
        if form.is_valid():
            form.save()
            return redirect('detalle_marca_vehiculo', marca_id=marca.id)
    else:
        form = MarcaVehiculoForm(instance=marca)
    return render(request, 'inventario/editar_marca_vehiculo.html', {'form': form, 'marca': marca})

@revisar_permiso('inventario.eliminar_marcas_vehiculos')
def eliminar_marca_vehiculo(request, marca_id):
    marca = MarcaVehiculo.objects.get(id=marca_id)
    if marca.eliminable():
        marca.delete()
    else:
        messages.error(request, 'No se puede eliminar esta marca de vehículo porque tiene modelos asociados.')
    return redirect('lista_marcas_vehiculos')

# --------------------------------------------------------------------------
# Vistas para la gestión de Tipos de Vehículos
# --------------------------------------------------------------------------

@revisar_permiso('inventario.agregar_tipos_vehiculos')
def agregar_tipo_vehiculo(request):
    if request.method == 'POST':
        form = TipoVehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_tipos_vehiculos')
    else:
        form = TipoVehiculoForm()
    return render(request, 'inventario/agregar_tipo_vehiculo.html', {'form': form})

@revisar_permiso('inventario.listar_tipos_vehiculos')
def lista_tipos_vehiculos(request):
    tipos = TipoVehiculo.objects.all()
    query = request.GET.get('search_query', '')
    if query:
        tipos = tipos.filter(nombre__icontains=query)
    return render(request, 'inventario/lista_tipos_vehiculos.html', {
        'tipos': tipos,
        'query': query
    })

@revisar_permiso('inventario.detallar_tipos_vehiculos')
def detalle_tipo_vehiculo(request, tipo_id):
    tipo = TipoVehiculo.objects.get(id=tipo_id)
    return render(request, 'inventario/detalle_tipo_vehiculo.html', {'tipo': tipo})

@revisar_permiso('inventario.editar_tipos_vehiculos')
def editar_tipo_vehiculo(request, tipo_id):
    tipo = TipoVehiculo.objects.get(id=tipo_id)
    if request.method == 'POST':
        form = TipoVehiculoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect('detalle_tipo_vehiculo', tipo_id=tipo.id)
    else:
        form = TipoVehiculoForm(instance=tipo)
    return render(request, 'inventario/editar_tipo_vehiculo.html', {'form': form, 'tipo': tipo})

@revisar_permiso('inventario.eliminar_tipos_vehiculos')
def eliminar_tipo_vehiculo(request, tipo_id):
    tipo = TipoVehiculo.objects.get(id=tipo_id)
    if tipo.eliminable:
        tipo.delete()
    else:
        messages.error(request, 'No se puede eliminar este tipo de vehículo porque tiene modelos asociados.')
    return redirect('lista_tipos_vehiculos')

# --------------------------------------------------------------------------
# Vistas para la gestión de Tipos de Transmisión
# --------------------------------------------------------------------------

@revisar_permiso('inventario.agregar_tipos_transmision')
def agregar_tipo_transmision(request):
    if request.method == 'POST':
        form = TipoTransmisionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_tipos_transmision')
    else:
        form = TipoTransmisionForm()
    return render(request, 'inventario/agregar_tipo_transmision.html', {'form': form})

@revisar_permiso('inventario.listar_tipos_transmision')
def lista_tipos_transmision(request):
    tipos = TipoTransmision.objects.all()
    query = request.GET.get('search_query', '')
    if query:
        tipos = tipos.filter(nombre__icontains=query)
    return render(request, 'inventario/lista_tipos_transmision.html', {
        'tipos': tipos,
        'query': query
    })

@revisar_permiso('inventario.detallar_tipos_transmision')
def detalle_tipo_transmision(request, tipo_id):
    tipo = TipoTransmision.objects.get(id=tipo_id)
    return render(request, 'inventario/detalle_tipo_transmision.html', {'tipo': tipo})

@revisar_permiso('inventario.editar_tipos_transmision')
def editar_tipo_transmision(request, tipo_id):
    tipo = TipoTransmision.objects.get(id=tipo_id)
    if request.method == 'POST':
        form = TipoTransmisionForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect('detalle_tipo_transmision', tipo_id=tipo.id)
    else:
        form = TipoTransmisionForm(instance=tipo)
    return render(request, 'inventario/editar_tipo_transmision.html', {'form': form, 'tipo': tipo})

@revisar_permiso('inventario.eliminar_tipos_transmision')
def eliminar_tipo_transmision(request, tipo_id):
    tipo = TipoTransmision.objects.get(id=tipo_id)
    if tipo.eliminable:
        tipo.delete()
    else:
        messages.error(request, 'No se puede eliminar este tipo de transmisión porque tiene modelos asociados.')
    return redirect('lista_tipos_transmision')

# --------------------------------------------------------------------------
# Vistas para la gestión de Modelos de Vehículos
# --------------------------------------------------------------------------

@revisar_permiso('inventario.agregar_modelos_vehiculos')
def agregar_modelo_vehiculo(request):
    if request.method == 'POST':
        form = ModeloVehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_modelos_vehiculos')
    else:
        form = ModeloVehiculoForm()
    return render(request, 'inventario/agregar_modelo_vehiculo.html', {'form': form})

@revisar_permiso('inventario.listar_modelos_vehiculos')
def lista_modelos_vehiculos(request):
    modelos = ModeloVehiculo.objects.select_related('marca').all()
    marcas = MarcaVehiculo.objects.all()
    query = request.GET.get('search_query', '')
    marca_id = request.GET.get('marca_id', '')

    if query:
        modelos = modelos.filter(
            models.Q(nombre__icontains=query) |
            models.Q(marca__nombre__icontains=query)
        )

    if marca_id:
        modelos = modelos.filter(marca_id=marca_id)

    return render(request, 'inventario/lista_modelos_vehiculos.html', {
        'modelos': modelos,
        'query': query,
        'marca_id': marca_id,
        'marcas': marcas,
    })

@revisar_permiso('inventario.detallar_modelos_vehiculos')
def detalle_modelo_vehiculo(request, modelo_id):
    modelo = ModeloVehiculo.objects.get(id=modelo_id)
    return render(request, 'inventario/detalle_modelo_vehiculo.html', {'modelo': modelo})

@revisar_permiso('inventario.editar_modelos_vehiculos')
def editar_modelo_vehiculo(request, modelo_id):
    modelo = ModeloVehiculo.objects.get(id=modelo_id)
    if request.method == 'POST':
        form = ModeloVehiculoForm(request.POST, instance=modelo)
        if form.is_valid():
            form.save()
            return redirect('detalle_modelo_vehiculo', modelo_id=modelo.id)
    else:
        form = ModeloVehiculoForm(instance=modelo)
    return render(request, 'inventario/editar_modelo_vehiculo.html', {'form': form, 'modelo': modelo})

@revisar_permiso('inventario.eliminar_modelos_vehiculos')
def eliminar_modelo_vehiculo(request, modelo_id):
    modelo = ModeloVehiculo.objects.get(id=modelo_id)
    modelo.delete()
    return redirect('lista_modelos_vehiculos')

permisos_iniciales_inventario = [
    {
        'codename': 'inventario.listar_inventario',
        'nombre': 'Listar Inventario',
        'descripcion': 'Permite agregar un nuevo vehículo al inventario.', 
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_vehiculo',
        'nombre': 'Agregar Vehículo',
        'descripcion': 'Permite agregar un nuevo vehículo al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_vehiculos',
        'nombre': 'Listar Vehículos',
        'descripcion': 'Permite ver la lista de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_vehiculo',
        'nombre': 'Detalle Vehículo',
        'descripcion': 'Permite ver los detalles de un vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_vehiculo',
        'nombre': 'Editar Vehículo',
        'descripcion': 'Permite editar un vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_vehiculo',
        'nombre': 'Eliminar Vehículo',
        'descripcion': 'Permite eliminar un vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_repuesto',
        'nombre': 'Agregar Repuesto',
        'descripcion': 'Permite agregar un nuevo repuesto al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_repuestos',
        'nombre': 'Listar Repuestos',
        'descripcion': 'Permite ver la lista de repuestos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_repuesto',
        'nombre': 'Detalle Repuesto',
        'descripcion': 'Permite ver los detalles de un repuesto en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_repuesto',
        'nombre': 'Editar Repuesto',
        'descripcion': 'Permite editar un repuesto en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_repuesto',
        'nombre': 'Eliminar Repuesto',
        'descripcion': 'Permite eliminar un repuesto del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_mantenimiento',
        'nombre': 'Agregar Mantenimiento',
        'descripcion': 'Permite agregar un nuevo mantenimiento al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_mantenimientos',
        'nombre': 'Listar Mantenimientos',
        'descripcion': 'Permite ver la lista de mantenimientos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_mantenimiento',
        'nombre': 'Detalle Mantenimiento',
        'descripcion': 'Permite ver los detalles de un mantenimiento en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_mantenimiento',
        'nombre': 'Editar Mantenimiento',
        'descripcion': 'Permite editar un mantenimiento en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_mantenimiento',
        'nombre': 'Eliminar Mantenimiento',
        'descripcion': 'Permite eliminar un mantenimiento del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_deposito',
        'nombre': 'Agregar Depósito',
        'descripcion': 'Permite agregar un nuevo depósito al inventario.' ,
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_depositos',
        'nombre': 'Listar Depósitos',
        'descripcion': 'Permite ver la lista de depósitos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_deposito',
        'nombre': 'Detalle Depósito',
        'descripcion': 'Permite ver los detalles de un depósito en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_deposito',
        'nombre': 'Editar Depósito',
        'descripcion': 'Permite editar un depósito en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_deposito',
        'nombre': 'Eliminar Depósito',
        'descripcion': 'Permite eliminar un depósito del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_unidad_medida',
        'nombre': 'Agregar Unidad de Medida',
        'descripcion': 'Permite agregar una nueva unidad de medida al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_unidades_medida',
        'nombre': 'Listar Unidades de Medida',
        'descripcion': 'Permite ver la lista de unidades de medida en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_unidad_medida',
        'nombre': 'Detalle Unidad de Medida',
        'descripcion': 'Permite ver los detalles de una unidad de medida en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_unidad_medida',
        'nombre': 'Editar Unidad de Medida',
        'descripcion': 'Permite editar una unidad de medida en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_marcas_vehiculos',
        'nombre': 'Agregar Marcas de Vehículos',
        'descripcion': 'Permite agregar nuevas marcas de vehículos al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_marcas_vehiculos',
        'nombre': 'Listar Marcas de Vehículos',
        'descripcion': 'Permite ver la lista de marcas de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_marcas_vehiculos',
        'nombre': 'Detalle Marca de Vehículo',
        'descripcion': 'Permite ver los detalles de una marca de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_marcas_vehiculos',
        'nombre': 'Editar Marcas de Vehículos',
        'descripcion': 'Permite editar una marca de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_marcas_vehiculos',
        'nombre': 'Eliminar Marcas de Vehículos',
        'descripcion': 'Permite eliminar una marca de vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_tipos_vehiculos',
        'nombre': 'Agregar Tipos de Vehículos',
        'descripcion': 'Permite agregar nuevos tipos de vehículos al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_tipos_vehiculos',
        'nombre': 'Listar Tipos de Vehículos',
        'descripcion': 'Permite ver la lista de tipos de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_tipos_vehiculos',
        'nombre': 'Detalle Tipo de Vehículo',
        'descripcion': 'Permite ver los detalles de un tipo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_tipos_vehiculos',
        'nombre': 'Editar Tipos de Vehículos',
        'descripcion': 'Permite editar un tipo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_tipos_vehiculos',
        'nombre': 'Eliminar Tipos de Vehículos',
        'descripcion': 'Permite eliminar un tipo de vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_modelos_vehiculos',
        'nombre': 'Agregar Modelos de Vehículos',
        'descripcion': 'Permite agregar nuevos modelos de vehículos al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_modelos_vehiculos',
        'nombre': 'Listar Modelos de Vehículos',
        'descripcion': 'Permite ver la lista de modelos de vehículos en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_modelos_vehiculos',
        'nombre': 'Detalle Modelo de Vehículo',
        'descripcion': 'Permite ver los detalles de un modelo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_modelos_vehiculos',
        'nombre': 'Editar Modelos de Vehículos',
        'descripcion': 'Permite editar un modelo de vehículo en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_modelos_vehiculos',
        'nombre': 'Eliminar Modelos de Vehículos',
        'descripcion': 'Permite eliminar un modelo de vehículo del inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.agregar_tipos_transmision',
        'nombre': 'Agregar Tipos de Transmisión',
        'descripcion': 'Permite agregar nuevos tipos de transmisión al inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.listar_tipos_transmision',
        'nombre': 'Listar Tipos de Transmisión',
        'descripcion': 'Permite ver la lista de tipos de transmisión en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.detallar_tipos_transmision',
        'nombre': 'Detalle Tipo de Transmisión',
        'descripcion': 'Permite ver los detalles de un tipo de transmisión en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.editar_tipos_transmision',
        'nombre': 'Editar Tipos de Transmisión',
        'descripcion': 'Permite editar un tipo de transmisión en el inventario.',
        'sector': 'Inventario'
    },
    {
        'codename': 'inventario.eliminar_tipos_transmision',
        'nombre': 'Eliminar Tipos de Transmisión',
        'descripcion': 'Permite eliminar un tipo de transmisión del inventario.',
        'sector': 'Inventario'
    },
]
