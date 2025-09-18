from django.shortcuts import render, redirect
from .forms import PedidoCreateForm, ItemPedidoFormSet
from .models import Cliente, Pedido, ItemPedido, Cotizacion
from .forms import ClienteForm, PedidoForm, ItemPedidoForm, CotizacionForm
from django.shortcuts import get_object_or_404


# --------------------------------------------------------------------------
# Vistas para la gestión de Pedidos
# --------------------------------------------------------------------------

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
    return render(request, 'clientes_pedidos/editar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'pedido': pedido
    })

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
    return render(request, 'clientes_pedidos/agregar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset
    })

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

def buscar_cliente_id_por_nombre(nombre):
    cliente = filter(Cliente, nombre__iexact=nombre).first()
    # icontains
    return cliente.id if cliente else None

def lista_pedidos_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    pedidos = getattr(cliente, 'pedidos', None)
    return render(request, 'clientes_pedidos/lista_pedidos_cliente.html', {'cliente': cliente, 'pedidos': pedidos})

def detalle_pedido(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    items = pedido.itempedido_set.all()
    return render(request, 'clientes_pedidos/detalle_pedido.html', {'pedido': pedido, 'items': items})

# --------------------------------------------------------------------------
# Vistas para la gestión de Clientes
# --------------------------------------------------------------------------

def agregar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de clientes o a otra página
    else:
        form = ClienteForm()
    return render(request, 'clientes_pedidos/agregar_cliente.html', {'form': form})

def lista_clientes(request):
    clientes = Cliente.objects.all()
    # Aquí puedes agregar lógica adicional si es necesario

    if request.method == 'POST':
        # Aquí puedes manejar la lógica de filtrado si usas un formulario POST
        # buscar por ruc o documento_identidad
        ruc = request.POST.get('ruc')
        documento_identidad = request.POST.get('documento_identidad')
        if ruc:
            clientes = clientes.filter(ruc__icontains=ruc)
        if documento_identidad:
            clientes = clientes.filter(documento_identidad__icontains=documento_identidad)
    return render(request, 'clientes_pedidos/lista_clientes.html', {'clientes': clientes})

def detalle_cliente(request, cliente_id):
    cliente = Cliente.objects.get(id=cliente_id)
    pedidos = cliente.pedidos.all()
    return render(request, 'clientes_pedidos/detalle_cliente.html', {'cliente': cliente, 'pedidos': pedidos})

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

# --------------------------------------------------------------------------
# Vistas para la gestión de Pedidos 2
# --------------------------------------------------------------------------

def agregar_pedido(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('crear_item_pedido')
    else:
        form = PedidoForm()
    return render(request, 'clientes_pedidos/agregar_pedido.html', {'form': form})

def detalle_pedido(request, pedido_id):
    pedido = Pedido.objects.get(id=pedido_id)
    items = pedido.itempedido_set.all()
    return render(request, 'clientes_pedidos/detalle_pedido.html', {'pedido': pedido, 'items': items})

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

# --------------------------------------------------------------------------
# Vistas para la gestión de Items de Pedido  
# --------------------------------------------------------------------------

def lista_items_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    items = ItemPedido.objects.filter(pedido=pedido)
    return render(request, 'clientes_pedidos/lista_items_pedido.html', {'pedido': pedido, 'items': items})

def agregar_item_pedido(request):
    if request.method == 'POST':
        form = ItemPedidoForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de pedidos o a otra página
    else:
        form = ItemPedidoForm()
    return render(request, 'clientes_pedidos/agregar_item_pedido.html', {'form': form})

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

def detalle_item_pedido(request, item_id):
    item = ItemPedido.objects.get(id=item_id)
    return render(request, 'clientes_pedidos/detalle_item_pedido.html', {'item': item})

# --------------------------------------------------------------------------
# Vistas para la gestión de Cotizaciones    
# --------------------------------------------------------------------------

def agregar_cotizacion(request):
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de cotizaciones o a otra página
    else:
        form = CotizacionForm()
    return render(request, 'clientes_pedidos/agregar_cotizacion.html', {'form': form})

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

def lista_cotizaciones(request):
    pedidos = Pedido.objects.all()
    cotizaciones = Cotizacion.objects.all()
    return render(request, 'clientes_pedidos/lista_cotizaciones.html', {'cotizaciones': cotizaciones, 'pedidos': pedidos})

def detalle_cotizacion(request, cotizacion_id):
    cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    return render(request, 'clientes_pedidos/detalle_cotizacion.html', {'cotizacion': cotizacion})

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



