from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente, Pedido, ItemPedido, Cotizacion
from inventario.models import Vehiculo, Repuesto
from .forms import ClienteForm, PedidoForm, ItemPedidoForm, CotizacionForm, PedidoCreateForm, ItemPedidoFormSet
from seguridad_usuarios.decorators import revisar_permiso
# login_required
from django.contrib.auth.decorators import login_required
# Q para búsquedas complejas
from django.db.models import Q


# --------------------------------------------------------------------------
# Vistas para la gestión de Pedidos
# --------------------------------------------------------------------------

@revisar_permiso('clientes_pedidos.realizar_pedido')
def realizar_pedido(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    usuario_vendedor = getattr(request.user, 'perfil', None)
    empleado = usuario_vendedor.empleado if usuario_vendedor else None
    if request.method == 'POST':
        pedido_form = PedidoCreateForm(request.POST)
        # Define prefix='items' para sincronizar con el JavaScript
        formset = ItemPedidoFormSet(request.POST, prefix='items')
        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.cliente = cliente
            tipo = 'stock'
            pedido.tipo = tipo
            pedido.save()  # Guardar la cabecera del pedido primero
            formset.instance = pedido
            formset.save()  # Luego guardar todos los ítems vinculados
            return redirect('detalle_pedido', pedido.id)
        else:
            # Imprimir errores en consola para depuración
            print("Errores del formulario de pedido:", pedido_form.errors)
            print("Errores del formset:", formset.errors)
    else:
        tipo = 'stock'
        pedido_form = PedidoCreateForm(initial={'cliente': cliente, 'vendedor': empleado, 'tipo': tipo})
        # Define prefix='items' también en GET para mantener consistencia
        formset = ItemPedidoFormSet(prefix='items')
    vehiculos = Vehiculo.objects.all()
    repuestos = Repuesto.objects.all()
    return render(request, 'clientes_pedidos/realizar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'cliente': cliente, 'tipo': tipo,
        'vehiculos': vehiculos,
        'repuestos': repuestos
    })

@revisar_permiso('clientes_pedidos.realizar_pedido_a_medida')
def realizar_pedido_a_medida(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        pedido_form = PedidoCreateForm(request.POST)
        formset = ItemPedidoFormSet(request.POST)
        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.cliente = cliente
            pedido.tipo = 'Importación a Medida'
            pedido.save()
            formset.instance = pedido
            formset.save()
            return redirect('detalle_pedido', pedido.id)
    else:
        pedido_form = PedidoCreateForm(initial={'cliente': cliente, 'tipo': 'Importación a Medida'})
        formset = ItemPedidoFormSet()
    return render(request, 'clientes_pedidos/realizar_pedido_a_medida.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'cliente': cliente,
    })

@revisar_permiso('clientes_pedidos.editar_pedido')
def editar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        pedido_form = PedidoCreateForm(request.POST, instance=pedido)
        formset = ItemPedidoFormSet(request.POST, instance=pedido)
        if pedido_form.is_valid() and formset.is_valid():
            pedido_form.save()
            formset.save()
            return redirect('lista_pedidos')  # Debes tener esta vista y url
    else:
        pedido_form = PedidoCreateForm(instance=pedido)
        formset = ItemPedidoFormSet(instance=pedido)
    vehiculos = Vehiculo.objects.all()
    repuestos = Repuesto.objects.all()
    return render(request, 'clientes_pedidos/editar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'pedido': pedido,
        'vehiculos': vehiculos,
        'repuestos': repuestos
    })

@revisar_permiso('clientes_pedidos.agregar_pedido')
def agregar_pedido(request):
    if request.method == 'POST':
        pedido_form = PedidoCreateForm(request.POST)
        formset = ItemPedidoFormSet(request.POST)
        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save()
            items = formset.save(commit=False)
            for item in items:
                item.pedido = pedido
                item.save()
            formset.save_m2m()
            return redirect('lista_pedidos')  # Debes tener esta vista y url
    else:
        pedido_form = PedidoCreateForm()
        formset = ItemPedidoFormSet()
    vehiculos = Vehiculo.objects.all()
    repuestos = Repuesto.objects.all()
    return render(request, 'clientes_pedidos/agregar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'vehiculos': vehiculos,
        'repuestos': repuestos
    })

@revisar_permiso('clientes_pedidos.listar_pedidos')
def lista_pedidos(request):
    pedidos = Pedido.objects.all()
    # filtrar por cliente, vendedor, estado, tipo, fecha_pedido
    # Si se envían parámetros de búsqueda, aplicarlos
    cliente = request.GET.get('cliente')
    vendedor = request.GET.get('vendedor')
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    fecha_pedido = request.GET.get('fecha_pedido')


    if cliente:
        cliente_id = buscar_cliente_id_por_nombre(cliente)
        if cliente_id:
            pedidos = pedidos.filter(cliente__id=cliente_id)
    if vendedor:
        pedidos = pedidos.filter(vendedor__id=vendedor)
    if estado:
        pedidos = pedidos.filter(estado=estado)
    if tipo:
        pedidos = pedidos.filter(tipo=tipo)
    if fecha_pedido:
        pedidos = pedidos.filter(fecha_pedido=fecha_pedido)

    return render(request, 'clientes_pedidos/lista_pedidos.html', {'pedidos': pedidos})

@login_required
def buscar_cliente_id_por_nombre(nombre):
    cliente = filter(Cliente, nombre__iexact=nombre).first()
    # icontains
    return cliente.id if cliente else None

@login_required
def lista_pedidos_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    pedidos = getattr(cliente, 'pedidos', None)
    return render(request, 'clientes_pedidos/lista_pedidos_cliente.html', {'cliente': cliente, 'pedidos': pedidos})

@revisar_permiso('clientes_pedidos.detallar_pedido')
def detalle_pedido(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    items = pedido.itempedido_set.all()
    return render(request, 'clientes_pedidos/detalle_pedido.html', {'pedido': pedido, 'items': items})

# --------------------------------------------------------------------------
# Vistas para la gestión de Clientes
# --------------------------------------------------------------------------
@revisar_permiso('clientes_pedidos.agregar_cliente')
def agregar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes_pedidos/agregar_cliente.html', {'form': form})

@revisar_permiso('clientes_pedidos.listar_clientes')
def lista_clientes(request):
    clientes = Cliente.objects.all()
    ruc = request.GET.get('ruc')
    documento_identidad = request.GET.get('documento_identidad')
    nombre = request.GET.get('nombre')
    estado = request.GET.get('estado')
    # filtrar por estado, ruc, documento_identidad, nombre (mesclado con apellidos)
    if estado in ('Activo', 'Inactivo'):
        clientes = clientes.filter(estado=(estado == 'Activo'))
    if ruc:
        clientes = clientes.filter(ruc__icontains=ruc)
    if documento_identidad:
        clientes = clientes.filter(documento_identidad__icontains=documento_identidad)
    if nombre:
        #nombre mesclado con apellidos
        clientes = clientes.filter((Q(nombre__icontains=nombre) | Q(apellidos__icontains=nombre)))
    # Si se envían múltiples parámetros, combinarlos
    if ruc and estado in ('Activo', 'Inactivo'):
        clientes = clientes.filter(ruc__icontains=ruc, estado=(estado == 'Activo'))
    if documento_identidad and estado in ('Activo', 'Inactivo'):
        clientes = clientes.filter(documento_identidad__icontains=documento_identidad, estado=(estado == 'Activo'))
    if nombre and estado in ('Activo', 'Inactivo'):
        clientes = clientes.filter((Q(nombre__icontains=nombre) | Q(apellidos__icontains=nombre)), estado=(estado == 'Activo'))
    return render(request, 'clientes_pedidos/lista_clientes.html', {'clientes': clientes})

@revisar_permiso('clientes_pedidos.detallar_cliente')
def detalle_cliente(request, cliente_id):
    cliente = Cliente.objects.get(id=cliente_id)
    pedidos = cliente.pedidos.all()
    return render(request, 'clientes_pedidos/detalle_cliente.html', {'cliente': cliente, 'pedidos': pedidos})

@revisar_permiso('clientes_pedidos.editar_cliente')
def editar_cliente(request, cliente_id):
    cliente = Cliente.objects.get(id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de clientes o a otra página
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes_pedidos/editar_cliente.html', {'form': form, 'cliente': cliente})

def realizar_pedido(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    usuario = request.user
    if request.method == 'POST':
        pedido_form = PedidoCreateForm(request.POST)
        formset = ItemPedidoFormSet(request.POST)
        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.cliente = cliente
            pedido.save()
            items = formset.save(commit=False)
            for item in items:
                item.pedido = pedido
                item.save()
            formset.save_m2m()
            return redirect('lista_pedidos')  # Debes tener esta vista y url
    else:
        empleado = getattr(usuario, 'empleado', None)
        if empleado:
            pedido_form = PedidoCreateForm(initial={'cliente': cliente, 'vendedor': empleado})
        else:
            pedido_form = PedidoCreateForm(initial={'cliente': cliente})
        formset = ItemPedidoFormSet()
    vehiculos = Vehiculo.objects.all()
    repuestos = Repuesto.objects.all()
    return render(request, 'clientes_pedidos/realizar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'cliente': cliente,
        'vehiculos': vehiculos,
        'repuestos': repuestos
    })
# --------------------------------------------------------------------------
# Vistas para la gestión de Pedidos 2
# --------------------------------------------------------------------------
@revisar_permiso('clientes_pedidos.agregar_pedido')
def agregar_pedido(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('crear_item_pedido')
    else:
        form = PedidoForm()
    return render(request, 'clientes_pedidos/agregar_pedido.html', {'form': form})

@revisar_permiso('clientes_pedidos.detallar_pedido')
def detalle_pedido(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    items = pedido.itempedido_set.all()
    return render(request, 'clientes_pedidos/detalle_pedido.html', {'pedido': pedido, 'items': items})

@revisar_permiso('clientes_pedidos.editar_pedido')
def editar_pedido(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            return redirect('lista_pedidos')  # Debes tener esta vista y url
    else:
        form = PedidoForm(instance=pedido)
    return render(request, 'clientes_pedidos/editar_pedido.html', {'form': form, 'pedido': pedido})

"""
def realizar_pedido(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    usuario = request.user
    if request.method == 'POST':
        pedido_form = PedidoCreateForm(request.POST)
        formset = ItemPedidoFormSet(request.POST)
        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.cliente = cliente
            pedido.save()
            items = formset.save(commit=False)
            for item in items:
                item.pedido = pedido
                item.save()
            formset.save_m2m()
            return redirect('lista_pedidos')  # Debes tener esta vista y url
    else:
        empleado = getattr(usuario, 'empleado', None)
        if empleado:
            pedido_form = PedidoCreateForm(initial={'cliente': cliente, 'vendedor': empleado})
        else:
            pedido_form = PedidoCreateForm(initial={'cliente': cliente})
        formset = ItemPedidoFormSet()
    return render(request, 'clientes_pedidos/realizar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'cliente': cliente
    }) """

# --------------------------------------------------------------------------
# Vistas para la gestión de Items de Pedido  
# --------------------------------------------------------------------------
@revisar_permiso('clientes_pedidos.listar_items_pedido')
def lista_items_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    items = ItemPedido.objects.filter(pedido=pedido)
    return render(request, 'clientes_pedidos/lista_items_pedido.html', {'pedido': pedido, 'items': items})

@revisar_permiso('clientes_pedidos.agregar_item_pedido')
def agregar_item_pedido(request):

    if request.method == 'POST':
        form = ItemPedidoForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de pedidos o a otra página
    else:
        form = ItemPedidoForm()
    return render(request, 'clientes_pedidos/agregar_item_pedido.html', {'form': form})

@revisar_permiso('clientes_pedidos.editar_item_pedido')
def editar_item_pedido(request, item_id):
    item = ItemPedido.objects.get(id=item_id)
    if request.method == 'POST':
        form = ItemPedidoForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de pedidos o a otra página
    else:
        form = ItemPedidoForm(instance=item)
    return render(request, 'clientes_pedidos/editar_item_pedido.html', {'form': form, 'item': item})    

@revisar_permiso('clientes_pedidos.detallar_item_pedido')
def detalle_item_pedido(request, item_id):
    item = ItemPedido.objects.get(id=item_id)
    return render(request, 'clientes_pedidos/detalle_item_pedido.html', {'item': item})

# --------------------------------------------------------------------------
# Vistas para la gestión de Cotizaciones    
# --------------------------------------------------------------------------
@revisar_permiso('clientes_pedidos.agregar_cotizacion')
def agregar_cotizacion(request):
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de cotizaciones o a otra página
    else:
        form = CotizacionForm()
    return render(request, 'clientes_pedidos/agregar_cotizacion.html', {'form': form})

@revisar_permiso('clientes_pedidos.agregar_cotizacion')
def agregar_cotizacion(request, pedido_id):
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        if form.is_valid():
            cotizacion = form.save(commit=False)
            cotizacion.pedido = get_object_or_404(Pedido, id=pedido_id)
            cotizacion.save()
            # Redirigir a la lista de cotizaciones o a otra página
    else:
        form = CotizacionForm()
        form.fields['pedido'].initial = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'clientes_pedidos/agregar_cotizacion.html', {'form': form})

@revisar_permiso('clientes_pedidos.listar_cotizaciones')
def lista_cotizaciones(request):
    pedidos = Pedido.objects.all()
    cotizaciones = Cotizacion.objects.all()
    return render(request, 'clientes_pedidos/lista_cotizaciones.html', {'cotizaciones': cotizaciones, 'pedidos': pedidos})

@revisar_permiso('clientes_pedidos.detallar_cotizacion')
def detalle_cotizacion(request, cotizacion_id):
    cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    return render(request, 'clientes_pedidos/detalle_cotizacion.html', {'cotizacion': cotizacion})

@revisar_permiso('clientes_pedidos.editar_cotizacion')
def editar_cotizacion(request, cotizacion_id):
    cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    if request.method == 'POST':
        form = CotizacionForm(request.POST, instance=cotizacion)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de cotizaciones o a otra página
    else:
        form = CotizacionForm(instance=cotizacion)
    return render(request, 'clientes_pedidos/editar_cotizacion.html', {'form': form, 'cotizacion': cotizacion})


def detalle_carrito(request):
    usuario = request.user
    empleado = getattr(usuario, 'empleado', None)
    cliente = getattr(usuario, 'cliente', None)
    carrito = None
    if cliente:
        carrito = cliente.carrito if cliente else None
    elif empleado:
        carrito = empleado.carrito if empleado else None
    return render(request, 'clientes_pedidos/detalle_carrito.html', {'carrito': carrito})

def agregar_al_carrito(request, producto_id, cliente_id = None, cantidad=1):
    # Lógica para agregar el producto al carrito
    if request.method == ' ':
        vehiculo = get_object_or_404(Vehiculo, pk=producto_id)
        repuesto = get_object_or_404(Repuesto, pk=producto_id)
        usuario = request.user
        empleado = getattr(usuario, 'empleado', None)
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id) 
            carrito = cliente.carrito if cliente else None
            if vehiculo:
                carrito.agregar_vehiculo(vehiculo, cantidad)
            if repuesto:
                carrito.agregar_repuesto(repuesto, cantidad)
        else:   
            carrito = empleado.carrito if empleado else None
            if vehiculo:
                carrito.agregar_vehiculo(vehiculo, cantidad)    
            if repuesto:
                carrito.agregar_repuesto(repuesto, cantidad)
        return redirect('detalle_carrito')  # Redirigir a la vista del carrito
    return redirect('detalle_producto', producto_id=producto_id)  # Redirigir a





def cargar_permisos(request):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from .models import Cliente, Pedido, ItemPedido, Cotizacion

    modelos_y_permisos = {
        Cliente: ['add_cliente', 'change_cliente', 'delete_cliente', 'view_cliente'],
        Pedido: ['add_pedido', 'change_pedido', 'delete_pedido', 'view_pedido'],
        ItemPedido: ['add_itempedido', 'change_itempedido', 'delete_itempedido', 'view_itempedido'],
        Cotizacion: ['add_cotizacion', 'change_cotizacion', 'delete_cotizacion', 'view_cotizacion'],
    }

    for modelo, permisos in modelos_y_permisos.items():
        content_type = ContentType.objects.get_for_model(modelo)
        for permiso_codename in permisos:
            permiso, created = Permission.objects.get_or_create(
                codename=permiso_codename,
                name=f'Can {permiso_codename.replace("_", " ")}',
                content_type=content_type
            )
            if created:
                print(f'Permiso {permiso_codename} creado para {modelo.__name__}')
            else:
                print(f'Permiso {permiso_codename} ya existe para {modelo.__name__}')


permisos_iniciales_clientes_pedidos = [
        {
            'codename': 'clientes_pedidos.agregar_cliente',
            'nombre': 'Agregar Cliente',
            'descripcion': 'Permite registrar nuevos Clientes.'
        },
        {
            'codename': 'clientes_pedidos.editar_cliente',
            'nombre': 'Editar Cliente',
            'descripcion': 'Permite modificar la información de Clientes existentes.'
        },
        {
            'codename': 'clientes_pedidos.listar_clientes',
            'nombre': 'Listar Clientes',
            'descripcion': 'Permite ver la lista de todos los Clientes.'
        },
        {
            'codename': 'clientes_pedidos.detallar_cliente',
            'nombre': 'Detalle de Cliente',
            'descripcion': 'Permite ver los detalles de un Cliente específico.'
        },
        {
            'codename': 'clientes_pedidos.agregar_pedido',
            'nombre': 'Agregar Pedido',
            'descripcion': 'Permite registrar nuevos Pedidos.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido',
            'nombre': 'Editar Pedido',
            'descripcion': 'Permite modificar la información de Pedidos existentes.'
        },
        {
            'codename': 'clientes_pedidos.listar_pedidos',
            'nombre': 'Listar Pedidos',
            'descripcion': 'Permite ver la lista de todos los Pedidos.'
        },
        {
            'codename': 'clientes_pedidos.detallar_pedido',
            'nombre': 'Detalle de Pedido',
            'descripcion': 'Permite ver los detalles de un Pedido específico.'
        },
        {
            'codename': 'clientes_pedidos.agregar_item_pedido',
            'nombre': 'Agregar Item de Pedido',
            'descripcion': 'Permite agregar nuevos Items a un Pedido.'
        },
        {
            'codename': 'clientes_pedidos.editar_item_pedido',
            'nombre': 'Editar Item de Pedido',
            'descripcion': 'Permite modificar la información de Items de Pedidos existentes.'
        },
        {
            'codename': 'clientes_pedidos.listar_items_pedido',
            'nombre': 'Listar Items de Pedido',
            'descripcion': 'Permite ver la lista de todos los Items de un Pedido.'
        },
        {
            'codename': 'clientes_pedidos.detallar_item_pedido',
            'nombre': 'Detalle de Item de Pedido',
            'descripcion': 'Permite ver los detalles de un Item específico de un Pedido.'
        },
        {
            'codename': 'clientes_pedidos.agregar_cotizacion',
            'nombre': 'Agregar Cotización',
            'descripcion': 'Permite registrar nuevas Cotizaciones.'
        },
        {
            'codename': 'clientes_pedidos.editar_cotizacion',
            'nombre': 'Editar Cotización',
            'descripcion': 'Permite modificar la información de Cotizaciones existentes.'
        },
        {
            'codename': 'clientes_pedidos.listar_cotizaciones',
            'nombre': 'Listar Cotizaciones',
            'descripcion': 'Permite ver la lista de todas las Cotizaciones.'
        },
        {
            'codename': 'clientes_pedidos.detallar_cotizacion',
            'nombre': 'Detalle de Cotización',
            'descripcion': 'Permite ver los detalles de una Cotización específica.'
        },
        {
            'codename': 'clientes_pedidos.realizar_pedido',
            'nombre': 'Realizar Pedido',
            'descripcion': 'Permite a los empleados realizar pedidos para los clientes.'
        },
        {
            'codename': 'clientes_pedidos.realizar_pedido_a_medida',
            'nombre': 'Realizar Pedido a Medida',
            'descripcion': 'Permite a los empleados realizar pedidos de importación a medida para los clientes.'
        },
    ]
