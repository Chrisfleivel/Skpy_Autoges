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
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_vehiculos')  # Redirige a la lista de vehículos (debes crear esta vista y url)
    else:
        form = VehiculoForm()
    return render(request, 'inventario/agregar_vehiculo.html', {'form': form})
'''
@revisar_permiso('inventario.listar_vehiculos')
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
'''

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
        vehiculos = vehiculos.filter(modelo__icontains=query)
    
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
    deposito.delete()
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
    unidad.delete()
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

permisos_iniciales_inventario = [
    {
        'codename': 'inventario.listar_inventario',
        'nombre': 'Listar Inventario',
        'descripcion': 'Permite agregar un nuevo vehículo al inventario.'
    },
    {
        'codename': 'inventario.agregar_vehiculo',
        'nombre': 'Agregar Vehículo',
        'descripcion': 'Permite agregar un nuevo vehículo al inventario.'
    },
    {
        'codename': 'inventario.listar_vehiculos',
        'nombre': 'Listar Vehículos',
        'descripcion': 'Permite ver la lista de vehículos en el inventario.'
    },
    {
        'codename': 'inventario.detallar_vehiculo',
        'nombre': 'Detalle Vehículo',
        'descripcion': 'Permite ver los detalles de un vehículo en el inventario.'
    },
    {
        'codename': 'inventario.editar_vehiculo',
        'nombre': 'Editar Vehículo',
        'descripcion': 'Permite editar un vehículo en el inventario.'
    },
    {
        'codename': 'inventario.eliminar_vehiculo',
        'nombre': 'Eliminar Vehículo',
        'descripcion': 'Permite eliminar un vehículo del inventario.'
    },
    {
        'codename': 'inventario.agregar_repuesto',
        'nombre': 'Agregar Repuesto',
        'descripcion': 'Permite agregar un nuevo repuesto al inventario.'
    },
    {
        'codename': 'inventario.listar_repuestos',
        'nombre': 'Listar Repuestos',
        'descripcion': 'Permite ver la lista de repuestos en el inventario.'
    },
    {
        'codename': 'inventario.detallar_repuesto',
        'nombre': 'Detalle Repuesto',
        'descripcion': 'Permite ver los detalles de un repuesto en el inventario.'
    },
    {
        'codename': 'inventario.editar_repuesto',
        'nombre': 'Editar Repuesto',
        'descripcion': 'Permite editar un repuesto en el inventario.'
    },
    {
        'codename': 'inventario.eliminar_repuesto',
        'nombre': 'Eliminar Repuesto',
        'descripcion': 'Permite eliminar un repuesto del inventario.'
    },
    {
        'codename': 'inventario.agregar_mantenimiento',
        'nombre': 'Agregar Mantenimiento',
        'descripcion': 'Permite agregar un nuevo mantenimiento al inventario.'
    },
    {
        'codename': 'inventario.listar_mantenimientos',
        'nombre': 'Listar Mantenimientos',
        'descripcion': 'Permite ver la lista de mantenimientos en el inventario.'
    },
    {
        'codename': 'inventario.detallar_mantenimiento',
        'nombre': 'Detalle Mantenimiento',
        'descripcion': 'Permite ver los detalles de un mantenimiento en el inventario.'
    },
    {
        'codename': 'inventario.editar_mantenimiento',
        'nombre': 'Editar Mantenimiento',
        'descripcion': 'Permite editar un mantenimiento en el inventario.'
    },
    {
        'codename': 'inventario.eliminar_mantenimiento',
        'nombre': 'Eliminar Mantenimiento',
        'descripcion': 'Permite eliminar un mantenimiento del inventario.'
    },
    {
        'codename': 'inventario.agregar_deposito',
        'nombre': 'Agregar Depósito',
        'descripcion': 'Permite agregar un nuevo depósito al inventario.'
    },
    {
        'codename': 'inventario.listar_depositos',
        'nombre': 'Listar Depósitos',
        'descripcion': 'Permite ver la lista de depósitos en el inventario.'
    },
    {
        'codename': 'inventario.detallar_deposito',
        'nombre': 'Detalle Depósito',
        'descripcion': 'Permite ver los detalles de un depósito en el inventario.'
    },
    {
        'codename': 'inventario.editar_deposito',
        'nombre': 'Editar Depósito',
        'descripcion': 'Permite editar un depósito en el inventario.'
    },
    {
        'codename': 'inventario.eliminar_deposito',
        'nombre': 'Eliminar Depósito',
        'descripcion': 'Permite eliminar un depósito del inventario.'
    },
    {
        'codename': 'inventario.agregar_unidad_medida',
        'nombre': 'Agregar Unidad de Medida',
        'descripcion': 'Permite agregar una nueva unidad de medida al inventario.'
    },
    {
        'codename': 'inventario.listar_unidades_medida',
        'nombre': 'Listar Unidades de Medida',
        'descripcion': 'Permite ver la lista de unidades de medida en el inventario.'
    },
    {
        'codename': 'inventario.detallar_unidad_medida',
        'nombre': 'Detalle Unidad de Medida',
        'descripcion': 'Permite ver los detalles de una unidad de medida en el inventario.'
    },
    {
        'codename': 'inventario.editar_unidad_medida',
        'nombre': 'Editar Unidad de Medida',
        'descripcion': 'Permite editar una unidad de medida en el inventario.'
    },
]
