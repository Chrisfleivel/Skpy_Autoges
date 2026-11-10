import csv
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db import OperationalError
from django.db.models import Q, Sum
from io import BytesIO

from .models import Cliente, Pedido, ItemPedido, Cotizacion, ProductoBuscado, SeleccionProductoBuscado
from configuraciones_maestras.models import Empresa, Moneda
from django.db import OperationalError
from inventario.models import Vehiculo, Repuesto
from .forms import ClienteForm, ContactoClienteFormSet, PedidoForm, ItemPedidoForm, CotizacionForm, PedidoCreateForm, ItemPedidoFormSet, ProductoBuscadoFormSet, FacturaPedidoForm
from seguridad_usuarios.decorators import revisar_permiso
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
import unicodedata

try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None


# --------------------------------------------------------------------------
# Vistas para la gestión de Pedidos
# --------------------------------------------------------------------------

def _obtener_empleado_vendedor(request):
    usuario_vendedor = getattr(request.user, 'perfil', None)
    return usuario_vendedor.empleado if usuario_vendedor else None


def _limpiar_formset_vacio(post_data, formset_prefix, campos_relevantes):
    total_forms = int(post_data.get(f'{formset_prefix}-TOTAL_FORMS', '0') or 0)
    if total_forms <= 0:
        return post_data

    cleaned_post = post_data.copy()
    indices_a_conservar = []

    for index in range(total_forms):
        prefix = f'{formset_prefix}-{index}-'
        tiene_datos = False
        for campo in campos_relevantes:
            value = cleaned_post.get(f'{prefix}{campo}', '')
            if isinstance(value, (list, tuple)):
                value = value[0] if value else ''
            if value not in ('', None):
                tiene_datos = True
                break

        if not tiene_datos:
            delete_marker = cleaned_post.get(f'{prefix}DELETE', '')
            if isinstance(delete_marker, (list, tuple)):
                delete_marker = delete_marker[0] if delete_marker else ''
            if delete_marker not in ('', None):
                tiene_datos = True

        if tiene_datos:
            indices_a_conservar.append(index)

    if len(indices_a_conservar) != total_forms:
        for key in list(cleaned_post.keys()):
            if key.startswith(f'{formset_prefix}-') and not key.endswith(('-TOTAL_FORMS', '-INITIAL_FORMS', '-MIN_NUM_FORMS', '-MAX_NUM_FORMS')):
                parts = key.split('-')
                if len(parts) >= 3:
                    index = parts[1]
                    if not index.isdigit():
                        continue
                    if int(index) not in indices_a_conservar:
                        del cleaned_post[key]

        cleaned_post[f'{formset_prefix}-TOTAL_FORMS'] = str(len(indices_a_conservar))
        cleaned_post[f'{formset_prefix}-INITIAL_FORMS'] = '0'

    return cleaned_post


def _realizar_pedido_por_tipo(request, cliente, tipo):
    empleado = _obtener_empleado_vendedor(request)

    # Seleccionar el formset según el tipo de pedido
    FormsetClass = ProductoBuscadoFormSet if tipo == 'busqueda' else ItemPedidoFormSet
    formset_prefix = 'productos' if tipo == 'busqueda' else 'items'

    if request.method == 'POST':
        post_data = request.POST.copy()
        if not post_data.get('cliente'):
            post_data['cliente'] = str(cliente.id)
        if not post_data.get('monto_total'):
            post_data['monto_total'] = '0'
        if not post_data.get('iva'):
            post_data['iva'] = '0'

        campos_relevantes = ['vehiculo', 'repuesto', 'cantidad', 'precio_unitario']
        if tipo == 'busqueda':
            campos_relevantes = ['descripcion', 'vehiculo', 'repuesto', 'cantidad', 'marca', 'modelo', 'especificaciones']

        post_data = _limpiar_formset_vacio(post_data, formset_prefix, campos_relevantes)

        pedido_form = PedidoCreateForm(post_data)
        has_formset_management = bool(post_data.get(f'{formset_prefix}-TOTAL_FORMS') or post_data.get(f'{formset_prefix}-INITIAL_FORMS'))
        # Solo pasar `form_kwargs` cuando el formset lo espere (ItemPedidoFormSet)
        formset_kwargs = {'prefix': formset_prefix, 'form_kwargs': {'pedido_tipo': tipo}}
        formset = FormsetClass(post_data, **formset_kwargs) if has_formset_management else FormsetClass(**formset_kwargs)
        formset_valid = formset.is_valid() or formset.total_form_count() == 0
        if pedido_form.is_valid() and formset_valid:
            pedido = pedido_form.save(commit=False)
            pedido.cliente = cliente
            pedido.vendedor = empleado
            pedido.tipo = tipo
            pedido.save()
            formset.instance = pedido
            formset.save()
            return redirect('detalle_pedido', pedido.id)
    else:
        pedido_form = PedidoCreateForm(initial={'cliente': cliente})
        formset = FormsetClass(prefix=formset_prefix, form_kwargs={'pedido_tipo': tipo})

    vehiculos = Vehiculo.objects.select_related('modelo').only('id', 'nombre', 'modelo')
    repuestos = Repuesto.objects.only('id', 'nombre', 'codigo_repuesto')
    if tipo in {'busqueda', 'abastecimiento'}:
        vehiculos = vehiculos.filter(estado='elegible_importacion')
        repuestos = repuestos.filter(estado='elegible_importacion')
    elif tipo == 'venta':
        vehiculos = vehiculos.filter(estado='disponible')
        repuestos = repuestos.filter(estado='disponible')
    monedas = Moneda.objects.all()
    return render(request, 'clientes_pedidos/realizar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'cliente': cliente,
        'tipo': tipo,
        'tipo_label': dict(Pedido.TIPO_PEDIDO).get(tipo, tipo),
        'vehiculos': vehiculos,
        'repuestos': repuestos,
        'monedas': monedas,
        'es_busqueda': tipo == 'busqueda',
        'formset_prefix': formset_prefix,
    })

@revisar_permiso('clientes_pedidos.realizar_pedido') # Permiso 1
def realizar_pedido(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    return _realizar_pedido_por_tipo(request, cliente, 'venta')

@revisar_permiso('clientes_pedidos.realizar_pedido_busqueda') # Permiso 2
def realizar_pedido_busqueda(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    return _realizar_pedido_por_tipo(request, cliente, 'busqueda')

@revisar_permiso('clientes_pedidos.realizar_pedido_abastecimiento') # Permiso 3
def realizar_pedido_abastecimiento(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    return _realizar_pedido_por_tipo(request, cliente, 'abastecimiento')

@revisar_permiso('clientes_pedidos.realizar_pedido_a_medida') # Permiso 4
def realizar_pedido_a_medida(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    return _realizar_pedido_por_tipo(request, cliente, 'importacion')

@revisar_permiso('clientes_pedidos.editar_pedido.aprobar') # Permiso 5
def aprobar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        pedido.aprobar()
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.rechazar') # Permiso 6
def rechazar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        motivo = (request.POST.get('motivo_cancelacion') or '').strip()
        try:
            if pedido.es_pedido_busqueda and pedido.estado in {'espera_aprovacion', 'seleccion_pendiente'}:
                pedido.rechazar_busqueda(motivo=motivo)
            else:
                pedido.rechazar(motivo=motivo)
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.aprobar_rechazar_abastecimiento') # Permiso 7
def aprobar_rechazar_abastecimiento(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        accion = (request.POST.get('accion') or '').strip().lower()
        motivo = (request.POST.get('motivo') or '').strip()

        if not pedido.es_pedido_abastecimiento:
            messages.error(request, 'Este pedido no corresponde a abastecimiento.')
        elif pedido.estado != 'busqueda_abastecimiento':
            messages.error(request, 'Este pedido no está en búsqueda de abastecimiento.')
        elif accion == 'aprobar':
            try:
                pedido.aprobar_abastecimiento(motivo=motivo)
                messages.success(request, 'Abastecimiento aprobado correctamente.')
            except ValidationError as exc:
                messages.error(request, str(exc))
        elif accion == 'rechazar':
            try:
                pedido.rechazar(motivo=motivo)
                messages.success(request, 'Abastecimiento rechazado correctamente.')
            except ValidationError as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, 'Acción no válida.')

    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.actualizar_item') # Permiso 8
def actualizar_item_pedido(request, pedido_id, item_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    item = get_object_or_404(ItemPedido, pk=item_id, pedido=pedido)
    
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', item.cantidad))
            precio_unitario = Decimal(request.POST.get('precio_unitario', item.precio_unitario))
            
            if cantidad < 1:
                messages.error(request, 'La cantidad debe ser mayor a 0.')
            else:
                item.cantidad = cantidad
                item.precio_unitario = precio_unitario
                item.save()
                # Recalcular totales del pedido (monto total e IVA)
                try:
                    pedido.monto_total = pedido.calcular_monto_total()
                    pedido.iva = pedido.calcular_iva()
                    pedido.save(update_fields=['monto_total', 'iva'])
                except Exception:
                    # Evitar que una excepción en el cálculo bloquee la actualización del item
                    pass
                messages.success(request, f'Producto {item.producto.nombre} actualizado correctamente.')
        except (ValueError, TypeError) as exc:
            messages.error(request, f'Error al actualizar el producto: {str(exc)}')
    
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.enviar_a_cobranzas') # Permiso 9
def enviar_a_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        pedido.enviar_a_cobranzas()
    return redirect('lista_pedidos')


@revisar_permiso('clientes_pedidos.editar_pedido.facturar_pedido_contado') # Permiso 10
def facturar_pedido_contado(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        try:
            pedido.facturar_pedido_venta_contado()
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.confirmar_entrega_repuesto') # Permiso 11
def confirmar_entrega_repuesto(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        try:
            pedido.confirmar_entrega_repuesto()
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.programar_transferencia') # Permiso 12
def programar_transferencia(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        fecha = request.POST.get('fecha_transferencia')
        if fecha:
            fecha_dt = parse_datetime(fecha)
            if fecha_dt is None:
                messages.error(request, 'Fecha de transferencia inválida.')
            else:
                try:
                    pedido.programar_transferencia(fecha_dt)
                except ValidationError as exc:
                    messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.iniciar_transferencia') # Permiso 13
def iniciar_transferencia(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        try:
            pedido.iniciar_transferencia()
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.confirmar_transferencia') # Permiso 14
def confirmar_transferencia(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        if 'documento_transferencia' in request.FILES:
            pedido.documento_transferencia = request.FILES['documento_transferencia']
            pedido.save(update_fields=['documento_transferencia'])
        try:
            pedido.confirmar_transferencia()
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.cancelar') # Permiso 15
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        motivo = (request.POST.get('motivo_cancelacion') or '').strip()
        try:
            if pedido.es_pedido_busqueda and pedido.estado in {'espera_de_busqueda', 'buscando', 'espera_aprovacion', 'seleccion_pendiente'}:
                pedido.cancelar_busqueda(motivo=motivo)
            else:
                pedido.cancelar()
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.avanzar_busqueda') # Permiso 16
def avanzar_pedido_busqueda(request, pedido_id, accion):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        motivo = (request.POST.get('motivo_cancelacion') or '').strip()
        producto = None
        producto_id = request.POST.get('producto_id') or request.POST.get('vehiculo_id')
        if producto_id:
            producto = get_object_or_404(Vehiculo, pk=producto_id)
        try:
            if accion == 'buscar':
                pedido.buscar()
            elif accion == 'ingresar_repuesto':
                pedido.ingresar_repuesto(producto=producto)
            elif accion == 'aprobar_repuesto':
                pedido.aprobar_repuesto(producto=producto, motivo=motivo)
            elif accion == 'ingresar_lista_vehiculos':
                pedido.ingresar_lista_vehiculos(producto=producto)
            elif accion == 'confirmar_eleccion':
                pedido.confirmar_eleccion(producto=producto, motivo=motivo)
            elif accion == 'cancelar_busqueda':
                pedido.cancelar_busqueda(motivo=motivo)
            elif accion == 'rechazar_busqueda':
                pedido.rechazar_busqueda(motivo=motivo)
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido') # Permiso 17
def editar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data = _limpiar_formset_vacio(post_data, 'items', ['vehiculo', 'repuesto', 'cantidad', 'precio_unitario'])
        pedido_form = PedidoCreateForm(post_data, instance=pedido)
        has_formset_management = bool(post_data.get('items-TOTAL_FORMS') or post_data.get('items-INITIAL_FORMS'))
        if has_formset_management:
            formset = ItemPedidoFormSet(post_data, instance=pedido, prefix='items', form_kwargs={'pedido_tipo': pedido.tipo})
        else:
            formset = ItemPedidoFormSet(instance=pedido, prefix='items', form_kwargs={'pedido_tipo': pedido.tipo})
        if pedido_form.is_valid() and formset.is_valid():
            pedido_form.save()
            formset.save()
            return redirect('lista_pedidos')  # Debes tener esta vista y url
    else:
        pedido_form = PedidoCreateForm(instance=pedido)
        formset = ItemPedidoFormSet(instance=pedido, prefix='items', form_kwargs={'pedido_tipo': pedido.tipo})
    vehiculos = Vehiculo.objects.select_related('modelo').only('id', 'nombre', 'modelo')
    repuestos = Repuesto.objects.only('id', 'nombre', 'codigo_repuesto')
    monedas = Moneda.objects.only('id', 'codigo', 'nombre')
    return render(request, 'clientes_pedidos/editar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'pedido': pedido,
        'vehiculos': vehiculos,
        'repuestos': repuestos,
        'monedas': monedas,
    })

def _obtener_cliente_empresa():
    try:
        empresa = Empresa.objects.first()
    except OperationalError:
        # Database schema may be missing (migrations not applied). Avoid 500.
        return None
    if not empresa:
        return None
    cliente, _ = Cliente.objects.get_or_create(
        razon_social=empresa.nombre,
        defaults={
            'tipo_persona': 'JURIDICA',
            'nombre': empresa.nombre,
            'apellidos': '',
            'documento_identidad': '',
            'ruc': getattr(empresa, 'ruc', '') or '',
            'direccion': empresa.direccion or '',
            'telefono': empresa.telefono or '',
            'email': empresa.email or '',
        }
    )
    return cliente


@revisar_permiso('clientes_pedidos.realizar_pedido_abastecimiento') # Permiso 18
def realizar_pedido_abastecimiento_general(request):
    """Vista envoltorio para crear un pedido de abastecimiento usando la Empresa del sistema como cliente."""
    empresa_cliente = _obtener_cliente_empresa()
    if not empresa_cliente:
        return redirect('lista_pedidos')
    return _realizar_pedido_por_tipo(request, empresa_cliente, 'abastecimiento')


@revisar_permiso('clientes_pedidos.realizar_pedido_abastecimiento') # Permiso 18
def crear_pedido_abastecimiento(request, repuesto_id):
    repuesto = get_object_or_404(Repuesto, pk=repuesto_id)
    cliente = _obtener_cliente_empresa()
    if not cliente:
        messages.error(request, 'No se pudo encontrar un cliente para crear el pedido de abastecimiento.')
        return redirect('detalle_repuesto', repuesto_id=repuesto.id)

    if request.method == 'POST':
        cantidad_raw = (request.POST.get('cantidad') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        try:
            cantidad = int(cantidad_raw)
        except (TypeError, ValueError):
            messages.error(request, 'La cantidad debe ser un número válido.')
            return render(request, 'clientes_pedidos/crear_pedido_abastecimiento.html', {'repuesto': repuesto, 'cliente': cliente})

        try:
            pedido = repuesto.crear_pedido_abastecimiento(cantidad=cantidad, descripcion=descripcion, cliente=cliente)
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect('detalle_repuesto', repuesto_id=repuesto.id)

        messages.success(request, f'Se creó un pedido de abastecimiento para {repuesto.nombre}.')
        return redirect('detalle_pedido', pedido_id=pedido.id)

    return render(request, 'clientes_pedidos/crear_pedido_abastecimiento.html', {'repuesto': repuesto, 'cliente': cliente})


@revisar_permiso('clientes_pedidos.realizar_pedido_busqueda') # Permiso 2
def realizar_pedido_busqueda_general(request):
    """Vista envoltorio para crear un pedido de búsqueda usando la Empresa del sistema como cliente."""
    empresa_cliente = _obtener_cliente_empresa()
    if not empresa_cliente:
        return redirect('lista_pedidos')
    return _realizar_pedido_por_tipo(request, empresa_cliente, 'busqueda')


@revisar_permiso('clientes_pedidos.agregar_pedido') # Permiso 19
def agregar_pedido(request):
    empresa_cliente = _obtener_cliente_empresa()
    if request.method == 'POST':
        post_data = request.POST.copy()
        if not post_data.get('cliente') and empresa_cliente:
            post_data['cliente'] = str(empresa_cliente.pk)
        pedido_form = PedidoCreateForm(post_data)
        has_formset_management = bool(post_data.get('items-TOTAL_FORMS') or post_data.get('items-INITIAL_FORMS'))
        if has_formset_management:
            formset = ItemPedidoFormSet(post_data, prefix='items', form_kwargs={'pedido_tipo': 'venta'})
        else:
            formset = ItemPedidoFormSet(prefix='items', form_kwargs={'pedido_tipo': 'venta'})
        formset_valid = formset.is_valid() or formset.total_form_count() == 0
        if pedido_form.is_valid() and formset_valid:
            pedido = pedido_form.save(commit=False)
            if not pedido.cliente and empresa_cliente:
                pedido.cliente = empresa_cliente
            if not pedido.cliente:
                pedido_form.add_error('cliente', 'No se ha encontrado la empresa para asignar el pedido.')
            else:
                pedido.vendedor = _obtener_empleado_vendedor(request)
                pedido.save()
                formset.instance = pedido
                formset.save()
                return redirect('lista_pedidos')
    else:
        initial = {}
        if empresa_cliente:
            initial['cliente'] = empresa_cliente.pk
        pedido_form = PedidoCreateForm(initial=initial)
        formset = ItemPedidoFormSet(prefix='items', form_kwargs={'pedido_tipo': 'venta'})
    vehiculos = Vehiculo.objects.select_related('modelo').only('id', 'nombre', 'modelo')
    repuestos = Repuesto.objects.only('id', 'nombre', 'codigo_repuesto')
    return render(request, 'clientes_pedidos/agregar_pedido.html', {
        'pedido_form': pedido_form,
        'formset': formset,
        'vehiculos': vehiculos,
        'repuestos': repuestos
    })

@revisar_permiso('clientes_pedidos.listar_pedidos') # Permiso 20
def lista_pedidos(request):
    pedidos = Pedido.objects.all()
    search_query = request.GET.get('search_query')
    fecha = request.GET.get('fecha')
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')

    if search_query:
        pedidos = pedidos.filter(
            Q(id__icontains=search_query)
            | Q(cliente__nombre__icontains=search_query)
            | Q(cliente__apellidos__icontains=search_query)
            | Q(cliente__razon_social__icontains=search_query)
            | Q(items__vehiculo__nombre__icontains=search_query)
            | Q(items__repuesto__nombre__icontains=search_query)
        ).distinct()
    if estado:
        pedidos = pedidos.filter(estado=estado)
    if tipo:
        pedidos = pedidos.filter(tipo=tipo)
    if fecha:
        pedidos = pedidos.filter(fecha_pedido__date=fecha)

    total_general = pedidos.aggregate(total=Sum('monto_total'))['total'] or 0
    total_pedidos = pedidos.count()
    pedidos_completados = pedidos.filter(estado='completado').count()
    pedidos_en_proceso = pedidos.filter(estado='en_proceso').count()
    pedidos_cancelados = pedidos.filter(estado='cancelado').count()

    return render(request, 'clientes_pedidos/lista_pedidos.html', {
        'pedidos': pedidos,
        'total_general': total_general,
        'total_pedidos': total_pedidos,
        'pedidos_completados': pedidos_completados,
        'pedidos_en_proceso': pedidos_en_proceso,
        'pedidos_cancelados': pedidos_cancelados,
    })


@revisar_permiso('clientes_pedidos.listar_pedidos') # Permiso 20
def lista_pedidos_abastecimiento(request):
    pedidos = Pedido.objects.filter(tipo='abastecimiento').select_related('cliente').order_by('-fecha_pedido')
    search_query = (request.GET.get('search_query') or '').strip()
    fecha = request.GET.get('fecha')
    estado = request.GET.get('estado')

    if search_query:
        pedidos = pedidos.filter(
            Q(id__icontains=search_query)
            | Q(cliente__nombre__icontains=search_query)
            | Q(cliente__apellidos__icontains=search_query)
            | Q(cliente__razon_social__icontains=search_query)
            | Q(items__vehiculo__nombre__icontains=search_query)
            | Q(items__repuesto__nombre__icontains=search_query)
        ).distinct()
    if estado:
        pedidos = pedidos.filter(estado=estado)
    if fecha:
        pedidos = pedidos.filter(fecha_pedido__date=fecha)

    total_general = pedidos.aggregate(total=Sum('monto_total'))['total'] or 0
    pedidos_aprobados = pedidos.filter(estado='aprobado').count()
    pedidos_en_proceso = pedidos.filter(estado='en_proceso').count()
    pedidos_cancelados = pedidos.filter(estado='cancelado').count()

    return render(request, 'clientes_pedidos/lista_pedidos_abastecimiento.html', {
        'pedidos': pedidos,
        'total_general': total_general,
        'pedidos_aprobados': pedidos_aprobados,
        'pedidos_en_proceso': pedidos_en_proceso,
        'pedidos_cancelados': pedidos_cancelados,
        'search_query': search_query,
        'fecha': fecha or '',
        'estado': estado or '',
    })

@login_required
def buscar_cliente_id_por_nombre(nombre):
    cliente = Cliente.objects.filter(nombre__iexact=nombre).first()
    return cliente.id if cliente else None

@login_required
def lista_pedidos_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    pedidos = getattr(cliente, 'pedidos', None)
    return render(request, 'clientes_pedidos/lista_pedidos_cliente.html', {'cliente': cliente, 'pedidos': pedidos})

@revisar_permiso('clientes_pedidos.detallar_pedido') # Permiso 21
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    items = pedido.items.all()
    return render(request, 'clientes_pedidos/detalle_pedido.html', {'pedido': pedido, 'items': items})


@revisar_permiso('clientes_pedidos.editar_pedido.cargar_factura') # Permiso 22
def cargar_factura_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        form = FacturaPedidoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                pedido.comprar_a_proveedor(
                    proveedor=form.cleaned_data['proveedor'] or pedido.proveedor_compra,
                    numero_factura=form.cleaned_data['numero_factura'],
                    factura_pdf=form.cleaned_data['factura_pdf'],
                    observaciones=form.cleaned_data['observaciones'],
                )
                messages.success(request, 'Factura cargada correctamente.')
            except ValidationError as exc:
                messages.error(request, str(exc))
            return redirect('detalle_pedido', pedido_id=pedido.id)
    else:
        form = FacturaPedidoForm(initial={
            'proveedor': pedido.proveedor_compra,
            'numero_factura': pedido.numero_factura,
            'fecha_factura': pedido.fecha_factura,
        })

    return render(request, 'clientes_pedidos/cargar_factura_pedido.html', {'pedido': pedido, 'form': form})

@revisar_permiso('clientes_pedidos.exportar_pedido_pdf') # Permiso 23
def exportar_pedido_pdf(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    html = render_to_string('clientes_pedidos/pedido_pdf.html', {'pedido': pedido})
    if pisa is None:
        return HttpResponse(
            'Para exportar en PDF se requiere el paquete opcional xhtml2pdf.',
            content_type='text/plain',
            status=501
        )

    pdf_output = BytesIO()
    pdf_status = pisa.CreatePDF(html, dest=pdf_output)
    if pdf_status.err:
        return HttpResponse('Error al generar el PDF del pedido.', status=500)

    response = HttpResponse(pdf_output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="pedido_{pedido.id}.pdf"'
    return response

# --------------------------------------------------------------------------
# Vistas para la gestión de Clientes
# --------------------------------------------------------------------------
@revisar_permiso('clientes_pedidos.agregar_cliente') # Permiso 24
def agregar_cliente(request):
    cliente = Cliente()
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        contact_formset = ContactoClienteFormSet(request.POST, instance=cliente)
        if form.is_valid() and contact_formset.is_valid():
            cliente = form.save(commit=False)
            cliente.fecha_registro = timezone.now() # Establecer la fecha de registro al momento de guardar
            cliente.save()
            contactos = contact_formset.save(commit=False)
            for contacto in contactos:
                contacto.cliente = cliente
                contacto.save()
            for contacto in contact_formset.deleted_objects:
                contacto.delete()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
        contact_formset = ContactoClienteFormSet(instance=cliente)
    return render(request, 'clientes_pedidos/agregar_cliente.html', {'form': form, 'contact_formset': contact_formset})

def _obtener_clientes_filtrados(request):
    clientes = Cliente.objects.all().order_by('nombre', 'apellidos', 'razon_social')

    tipo_persona = (request.GET.get('tipo_persona') or '').strip()
    estado = (request.GET.get('estado') or '').strip()
    busqueda = (request.GET.get('q') or request.GET.get('nombre') or '').strip()
    ruc = (request.GET.get('ruc') or '').strip()
    documento_identidad = (request.GET.get('documento_identidad') or '').strip()

    if tipo_persona in ('FISICA', 'JURIDICA'):
        clientes = clientes.filter(tipo_persona=tipo_persona)

    if estado in ('Activo', 'Inactivo'):
        clientes = clientes.filter(estado=(estado == 'Activo'))

    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda)
            | Q(apellidos__icontains=busqueda)
            | Q(razon_social__icontains=busqueda)
            | Q(ruc__icontains=busqueda)
            | Q(documento_identidad__icontains=busqueda)
        )

    if ruc:
        clientes = clientes.filter(ruc__icontains=ruc)

    if documento_identidad:
        clientes = clientes.filter(documento_identidad__icontains=documento_identidad)

    return clientes, {
        'tipo_persona': tipo_persona,
        'estado': estado,
        'q': busqueda,
        'ruc': ruc,
        'documento_identidad': documento_identidad,
    }


@revisar_permiso('clientes_pedidos.listar_clientes') # Permiso 25
def lista_clientes(request):
    clientes, filtros = _obtener_clientes_filtrados(request)
    return render(request, 'clientes_pedidos/lista_clientes.html', {
        'clientes': clientes,
        **filtros,
    })


@revisar_permiso('clientes_pedidos.listar_clientes') # Permiso 25
def exportar_clientes_csv(request):
    clientes, _ = _obtener_clientes_filtrados(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clientes.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Tipo', 'Nombre', 'RUC', 'Documento', 'Email', 'Teléfono', 'Dirección', 'Estado'])

    for cliente in clientes:
        nombre = ' '.join(filter(None, [cliente.nombre, cliente.apellidos])).strip()
        if not nombre:
            nombre = cliente.razon_social or ''

        writer.writerow([
            cliente.id,
            'Persona física' if cliente.tipo_persona == 'FISICA' else 'Persona jurídica',
            nombre,
            cliente.ruc or '',
            cliente.documento_identidad or '',
            cliente.email or '',
            cliente.telefono or '',
            cliente.direccion or '',
            'Activo' if cliente.estado else 'Inactivo',
        ])

    return response


@revisar_permiso('clientes_pedidos.listar_clientes') # Permiso 25
def exportar_clientes_pdf(request):
    clientes, _ = _obtener_clientes_filtrados(request)

    if pisa is None:
        return HttpResponse(
            'Para exportar en PDF se requiere el paquete opcional xhtml2pdf.',
            content_type='text/plain',
            status=501
        )

    html = render_to_string('clientes_pedidos/clientes_pdf.html', {'clientes': clientes})
    pdf_output = BytesIO()
    pdf_status = pisa.CreatePDF(html, dest=pdf_output)
    
    if pdf_status.err:
        return HttpResponse('Error al generar el PDF de clientes.', status=500)

    response = HttpResponse(pdf_output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="clientes.pdf"'
    return response


@revisar_permiso('clientes_pedidos.listar_clientes') # Permiso 25
def reporte_clientes(request):
    """Alias para exportar_clientes_csv para compatibilidad con rutas existentes."""
    return exportar_clientes_csv(request)


@revisar_permiso('clientes_pedidos.detallar_cliente') # Permiso 26
def detalle_cliente(request, cliente_id):
    cliente = Cliente.objects.get(id=cliente_id)
    pedidos = cliente.pedidos.all()
    return render(request, 'clientes_pedidos/detalle_cliente.html', {'cliente': cliente, 'pedidos': pedidos})

@revisar_permiso('clientes_pedidos.editar_cliente') # Permiso 27
def editar_cliente(request, cliente_id):
    cliente = Cliente.objects.get(id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        contact_formset = ContactoClienteFormSet(request.POST, instance=cliente)
        if form.is_valid() and contact_formset.is_valid():
            cliente = form.save()
            contactos = contact_formset.save(commit=False)
            for contacto in contactos:
                contacto.cliente = cliente
                contacto.save()
            for contacto in contact_formset.deleted_objects:
                contacto.delete()
            return redirect('detalle_cliente', cliente.id)
    else:
        form = ClienteForm(instance=cliente)
        contact_formset = ContactoClienteFormSet(instance=cliente)
    return render(request, 'clientes_pedidos/editar_cliente.html', {'form': form, 'cliente': cliente, 'contact_formset': contact_formset})

@revisar_permiso('clientes_pedidos.eliminar_cliente') # Permiso 28
def eliminar_cliente(request, cliente_id):
    cliente = Cliente.objects.get(id=cliente_id)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'clientes_pedidos/eliminar_cliente.html', {'cliente': cliente})


# --------------------------------------------------------------------------
# Vistas para la gestión de Items de Pedido  
# --------------------------------------------------------------------------
@revisar_permiso('clientes_pedidos.listar_items_pedido') # Permiso 29
def lista_items_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    items = ItemPedido.objects.filter(pedido=pedido)
    return render(request, 'clientes_pedidos/lista_items_pedido.html', {'pedido': pedido, 'items': items})

@revisar_permiso('clientes_pedidos.agregar_item_pedido') # Permiso 30
def agregar_item_pedido(request):

    if request.method == 'POST':
        form = ItemPedidoForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de pedidos o a otra página
    else:
        form = ItemPedidoForm()
    return render(request, 'clientes_pedidos/agregar_item_pedido.html', {'form': form})


@revisar_permiso('clientes_pedidos.obtener_precio_repuesto') # Permiso 31
def obtener_precio_repuesto(request, repuesto_id):
    """
    Devuelve los datos de compra de un repuesto en formato JSON para precargar el formulario.
    """
    try:
        repuesto = Repuesto.objects.filter(pk=repuesto_id).select_related(
            'moneda_venta', 'moneda_compra_proveedor'
        ).first()
        if not repuesto:
            return JsonResponse({'error': 'Repuesto no encontrado'}, status=404)

        moneda = repuesto.moneda_producto()
        precio_unitario = repuesto.costo_unitario_producto()
        cantidad_producto = repuesto.cantidad_producto()
        return JsonResponse({
            'precio_venta': str(repuesto.precio_venta) if repuesto.precio_venta else '0.00',
            'precio_unitario': str(precio_unitario) if precio_unitario is not None else '0.00',
            'cantidad_a_comprar': str(repuesto.cantidad_a_comprar or 0),
            'cantidad_producto': str(cantidad_producto or 0),
            'moneda_id': str(moneda.id) if moneda else '',
            'moneda_codigo': moneda.codigo if moneda else '',
            'codigo': repuesto.codigo_repuesto,
            'nombre': repuesto.nombre,
        })
    except Exception:
        return JsonResponse({'error': 'No se pudieron obtener los datos del repuesto'}, status=400)


@revisar_permiso('clientes_pedidos.obtener_precio_vehiculo') # Permiso 32
def obtener_precio_vehiculo(request, vehiculo_id):
    """
    Devuelve los datos de un vehículo en formato JSON para precargar el formulario.
    """
    try:
        vehiculo = Vehiculo.objects.select_related('moneda_venta', 'moneda_compra_proveedor').get(id=vehiculo_id)
        moneda = vehiculo.moneda_producto()
        precio_unitario = vehiculo.costo_unitario_producto()
        return JsonResponse({
            'precio_venta': str(vehiculo.precio_venta) if vehiculo.precio_venta else '0.00',
            'precio_unitario': str(precio_unitario) if precio_unitario is not None else '0.00',
            'cantidad_producto': str(vehiculo.cantidad_producto() or 0),
            'moneda_id': str(moneda.id) if moneda else '',
            'moneda_codigo': moneda.codigo if moneda else '',
            'nombre': vehiculo.nombre,
            'codigo': vehiculo.codigo_chasis,
        })
    except Vehiculo.DoesNotExist:
        return JsonResponse({'error': 'Vehículo no encontrado'}, status=404)

@login_required
def buscar_productos_api(request):
    """Busca vehículos y repuestos disponibles para el modal de selección de productos."""
    def _normalizar_texto(value):
        if not value:
            return ''
        return ''.join(
            char for char in unicodedata.normalize('NFKD', value)
            if not unicodedata.combining(char)
        ).lower()

    tipo = (request.GET.get('tipo') or '').strip().lower()
    pedido_tipo = (request.GET.get('pedido_tipo') or '').strip().lower()
    query = (request.GET.get('q') or '').strip()
    query_normalizado = _normalizar_texto(query)
    estado_producto = 'elegible_importacion' if pedido_tipo in {'busqueda', 'abastecimiento'} else 'disponible'

    if tipo == 'repuesto':
        queryset = Repuesto.objects.filter(estado=estado_producto).order_by('nombre')
        if query_normalizado:
            queryset = [
                repuesto for repuesto in queryset
                if query_normalizado in _normalizar_texto(' '.join([
                    repuesto.nombre or '',
                    repuesto.codigo_repuesto or '',
                    repuesto.descripcion or '',
                    repuesto.compatibilidad or '',
                ]))
            ][:20]
        else:
            queryset = list(queryset)[:20]
        results = [
            {
                'id': repuesto.id,
                'nombre': repuesto.nombre,
                'codigo': repuesto.codigo_repuesto,
                'descripcion': repuesto.descripcion or '',
                'tipo': 'repuesto',
            }
            for repuesto in queryset
        ]
    elif tipo == 'vehiculo':
        queryset = Vehiculo.objects.filter(estado=estado_producto).select_related('marca', 'modelo').order_by('nombre')
        if query_normalizado:
            queryset = [
                vehiculo for vehiculo in queryset
                if query_normalizado in _normalizar_texto(' '.join([
                    vehiculo.nombre or '',
                    vehiculo.codigo_chasis or '',
                    vehiculo.descripcion or '',
                    getattr(vehiculo.marca, 'nombre', '') or '',
                    getattr(vehiculo.modelo, 'nombre', '') or '',
                ]))
            ][:20]
        else:
            queryset = list(queryset)[:20]
        results = [
            {
                'id': vehiculo.id,
                'nombre': vehiculo.nombre,
                'codigo': vehiculo.codigo_chasis,
                'descripcion': vehiculo.descripcion or '',
                'tipo': 'vehiculo',
            }
            for vehiculo in queryset
        ]
    else:
        results = []

    return JsonResponse({'results': results})


@revisar_permiso('clientes_pedidos.editar_item_pedido') # Permiso 33
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

@revisar_permiso('clientes_pedidos.detallar_item_pedido') # Permiso 34
def detalle_item_pedido(request, item_id):
    item = ItemPedido.objects.get(id=item_id)
    return render(request, 'clientes_pedidos/detalle_item_pedido.html', {'item': item})

# --------------------------------------------------------------------------
# Vistas para la gestión de Cotizaciones    
# --------------------------------------------------------------------------
@revisar_permiso('clientes_pedidos.agregar_cotizacion') # Permiso 35
def agregar_cotizacion(request):
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir a la lista de cotizaciones o a otra página
    else:
        form = CotizacionForm()
    return render(request, 'clientes_pedidos/agregar_cotizacion.html', {'form': form})

@revisar_permiso('clientes_pedidos.agregar_cotizacion') # Permiso 35
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

@revisar_permiso('clientes_pedidos.listar_cotizaciones') # Permiso 36
def lista_cotizaciones(request):
    pedidos = Pedido.objects.all()
    cotizaciones = Cotizacion.objects.all()
    return render(request, 'clientes_pedidos/lista_cotizaciones.html', {'cotizaciones': cotizaciones, 'pedidos': pedidos})

@revisar_permiso('clientes_pedidos.detallar_cotizacion') # Permiso 37
def detalle_cotizacion(request, cotizacion_id):
    cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    return render(request, 'clientes_pedidos/detalle_cotizacion.html', {'cotizacion': cotizacion})

@revisar_permiso('clientes_pedidos.editar_cotizacion') # Permiso 38
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


@revisar_permiso('clientes_pedidos.detalle_carrito') # Permiso 39
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

@revisar_permiso('clientes_pedidos.agregar_al_carrito') # Permiso 40
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


# --------------------------------------------------------------------------
# Vistas para el flujo de Búsqueda y Selección de Productos
# --------------------------------------------------------------------------

@revisar_permiso('clientes_pedidos.editar_pedido.enviar_a_seleccion') # Permiso 41
def enviar_a_seleccion(request, pedido_id):
    """Envía un pedido de búsqueda o abastecimiento al encargado de selección de producto."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST' and pedido.tipo in {'busqueda', 'abastecimiento'}:
        pedido.enviar_a_seleccion()
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('clientes_pedidos.editar_pedido.listar_pedidos_seleccion') # Permiso 42
def listar_pedidos_seleccion(request):
    """Lista pedidos de búsqueda y abastecimiento pendientes de selección para el encargado."""
    pedidos = Pedido.objects.filter(tipo__in=['busqueda', 'abastecimiento'], estado='seleccion_pendiente')
    return render(request, 'clientes_pedidos/listar_pedidos_seleccion.html', {
        'pedidos': pedidos,
        'estado': 'Pendiente de Selección'
    })


@revisar_permiso('clientes_pedidos.editar_pedido.confirmar_producto_buscado') # Permiso 43
def confirmar_producto_buscado(request, pedido_id, producto_buscado_id):
    """Encargado confirma el producto encontrado y establece el precio."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    producto = get_object_or_404(ProductoBuscado, pk=producto_buscado_id, pedido=pedido)
    
    if request.method == 'POST':
        repuesto_id = request.POST.get('repuesto_id')
        vehiculo_id = request.POST.get('vehiculo_id')
        precio_unitario = request.POST.get('precio_unitario')
        aprobado_seo = request.POST.get('aprobado_seo') == 'on'
        
        if (repuesto_id or vehiculo_id) and precio_unitario:
            from decimal import Decimal
            precio = Decimal(precio_unitario)
            
            # Crear o actualizar la selección del producto
            seleccion, created = SeleccionProductoBuscado.objects.get_or_create(
                producto_buscado=producto
            )
            seleccion.repuesto = get_object_or_404(Repuesto, pk=repuesto_id) if repuesto_id else None
            seleccion.vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id) if vehiculo_id else None
            seleccion.precio_unitario = precio
            seleccion.estado = 'encontrado'
            seleccion.aprobado_seo = aprobado_seo
            seleccion.save()
            seleccion.calcular_precio_total()
            
            # Si todos los productos fueron confirmados, cambiar estado del pedido
            productos_sin_confirmar = pedido.productos_buscados.exclude(
                seleccion__estado='encontrado'
            ).count()
            
            if productos_sin_confirmar == 0:
                pedido.confirmar_seleccion()
                if pedido.tipo == 'abastecimiento':
                    pedido.crear_importacion_desde_abastecimiento()
                return redirect('detalle_pedido', pedido_id=pedido.id)
            
            return redirect('confirmar_producto_buscado', pedido_id=pedido.id, 
                          producto_buscado_id=producto_buscado_id)
    
    repuestos = Repuesto.objects.only('id', 'nombre', 'codigo_repuesto')
    seleccion = getattr(producto, 'seleccion', None)
    
    return render(request, 'clientes_pedidos/confirmar_producto_buscado.html', {
        'pedido': pedido,
        'producto': producto,
        'repuestos': repuestos,
        'seleccion': seleccion
    })


@revisar_permiso('clientes_pedidos.detallar_pedido.imprimir_producto_buscado') # Permiso 45
def imprimir_producto_buscado(request, pedido_id, producto_buscado_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    producto = get_object_or_404(ProductoBuscado, pk=producto_buscado_id, pedido=pedido)
    seleccion = getattr(producto, 'seleccion', None)

    return render(request, 'clientes_pedidos/print_producto_buscado.html', {
        'pedido': pedido,
        'producto': producto,
        'seleccion': seleccion,
    })


@revisar_permiso('clientes_pedidos.editar_pedido.enviar_precio_cliente') # Permiso 44
def enviar_precio_cliente(request, pedido_id):
    """Envía el precio confirmado al cliente para su aprobación."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    if request.method == 'POST':
        if pedido.estado == 'seleccion_confirmada':
            pedido.enviar_precio_cliente()
        return redirect('detalle_pedido', pedido_id=pedido.id)
    
    selecciones = SeleccionProductoBuscado.objects.filter(
        producto_buscado__pedido=pedido,
        estado='encontrado'
    )
    
    return render(request, 'clientes_pedidos/enviar_precio_cliente.html', {
        'pedido': pedido,
        'selecciones': selecciones,
        'monto_total': sum([s.precio_total or 0 for s in selecciones])
    })


@revisar_permiso('clientes_pedidos.detallar_pedido.confirmar_precio_cliente') # Permiso 46
def confirmar_precio_cliente(request, pedido_id):
    """Cliente confirma el precio y el pedido se convierte en pedido de importación."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    if request.method == 'POST':
        if pedido.estado == 'precio_enviado_cliente':
            # Confirmar cliente y crear items en el pedido
            selecciones = SeleccionProductoBuscado.objects.filter(
                producto_buscado__pedido=pedido,
                estado='encontrado'
            )
            
            for seleccion in selecciones:
                seleccion.confirmar_cliente()
            
            # Cambiar el estado del pedido
            pedido.confirmar_precio_cliente()
            return redirect('detalle_pedido', pedido_id=pedido.id)
    
    if pedido.estado != 'precio_enviado_cliente':
        return redirect('detalle_pedido', pedido_id=pedido.id)
    
    selecciones = SeleccionProductoBuscado.objects.filter(
        producto_buscado__pedido=pedido,
        estado='encontrado'
    )
    
    return render(request, 'clientes_pedidos/confirmar_precio_cliente.html', {
        'pedido': pedido,
        'selecciones': selecciones,
        'monto_total': sum([s.precio_total or 0 for s in selecciones])
    })


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
        {
            'codename': 'clientes_pedidos.realizar_pedido_abastecimiento',
            'nombre': 'Realizar Pedido de Abastecimiento',
            'descripcion': 'Permite a los empleados realizar pedidos de abastecimiento para los clientes.'
        },
        {
            'codename': 'clientes_pedidos.realizar_pedido_busqueda',
            'nombre': 'Realizar Pedido de Búsqueda',
            'descripcion': 'Permite a los empleados realizar pedidos de búsqueda para los clientes.'
        },
        {
            'codename': 'clientes_pedidos.exportar_pedido_pdf',
            'nombre': 'Exportar Pedido a PDF',
            'descripcion': 'Permite exportar los detalles de un pedido a un archivo PDF.'
        },
        {
            'codename': 'clientes_pedidos.cargar_factura_pedido',
            'nombre': 'Cargar Factura de Pedido',
            'descripcion': 'Permite cargar la factura correspondiente a un pedido.'
        },
        {
            'codename': 'clientes_pedidos.detalle_carrito',
            'nombre': 'Detalle de Carrito',
            'descripcion': 'Permite ver los detalles del carrito de compras del cliente.'
        },
        {
            'codename': 'clientes_pedidos.agregar_al_carrito',
            'nombre': 'Agregar al Carrito',
            'descripcion': 'Permite agregar productos al carrito de compras del cliente.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.enviar_a_seleccion',
            'nombre': 'Enviar Pedido a Selección',
            'descripcion': 'Permite enviar un pedido de búsqueda o abastecimiento al encargado de selección de producto.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.listar_pedidos_seleccion',
            'nombre': 'Listar Pedidos para Selección',
            'descripcion': 'Permite listar pedidos de búsqueda y abastecimiento pendientes de selección para el encargado.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.confirmar_producto_buscado',
            'nombre': 'Confirmar Producto Buscado',
            'descripcion': 'Permite al encargado confirmar el producto encontrado y establecer el precio.'
        },
        {
            'codename': 'clientes_pedidos.detallar_pedido.imprimir_producto_buscado',
            'nombre': 'Imprimir Producto Buscado',
            'descripcion': 'Permite imprimir los detalles del producto buscado en un pedido.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.enviar_precio_cliente',
            'nombre': 'Enviar Precio al Cliente',
            'descripcion': 'Permite enviar el precio confirmado al cliente para su aprobación.'
        },
        {
            'codename': 'clientes_pedidos.detallar_pedido.confirmar_precio_cliente',
            'nombre': 'Confirmar Precio por Cliente',
            'descripcion': 'Permite al cliente confirmar el precio y convertir el pedido en un pedido de importación.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.aprobar',
            'nombre': 'Aprobar Pedido',
            'descripcion': 'Permite aprobar un pedido pendiente.'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.rechazar',
            'nombre': 'Rechazar Pedido',
            'descripcion': 'Permite rechazar un pedido pendiente.'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.aprobar_rechazar_abastecimiento',
            'nombre': 'Aprobar/Rechazar Pedido de Abastecimiento',
            'descripcion': 'Permite aprobar o rechazar un pedido de abastecimiento.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.actualizar_item',
            'nombre': 'Actualizar Item de Pedido',
            'descripcion': 'Permite actualizar la información de un item en el pedido.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.enviar_a_cobranzas',
            'nombre': 'Enviar a Cobranzas',
            'descripcion': 'Permite enviar un pedido a la sección de cobranzas.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.facturar_pedido_contado',
            'nombre': 'Facturar Pedido Contado',
            'descripcion': 'Permite facturar un pedido realizado en efectivo.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.confirmar_entrega_repuesto',
            'nombre': 'Confirmar Entrega de Repuesto',
            'descripcion': 'Permite confirmar la entrega de un repuesto en un pedido.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.programar_transferencia',
            'nombre': 'Programar Transferencia',
            'descripcion': 'Permite programar la transferencia de un pedido.'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.iniciar_transferencia',
            'nombre': 'Iniciar Transferencia',
            'descripcion': 'Permite iniciar la transferencia de un pedido.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.confirmar_transferencia',
            'nombre': 'Confirmar Transferencia',
            'descripcion': 'Permite confirmar la transferencia de un pedido.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.cancelar',
            'nombre': 'Cancelar Pedido',
            'descripcion': 'Permite cancelar un pedido.'
        }, 
        {
            'codename': 'clientes_pedidos.editar_pedido.avanzar_busqueda',
            'nombre': 'Avanzar Búsqueda',
            'descripcion': 'Permite avanzar en la búsqueda de un producto.'
        },
        {
            'codename': 'clientes_pedidos.editar_pedido.cargar_factura',
            'nombre': 'Cargar Factura',
            'descripcion': 'Permite cargar la factura de un pedido.'
        },
        {
            'codename': 'clientes_pedidos.eliminar_cliente',
            'nombre': 'Eliminar Cliente',
            'descripcion': 'Permite eliminar un cliente del sistema.'
        },
        {
            'codename': 'clientes_pedidos.obtener_precio_repuesto',
            'nombre': 'Obtener Precio de Repuesto',
            'descripcion': 'Permite obtener el precio de un repuesto.'
        },
        {
            'codename': 'clientes_pedidos.obtener_precio_vehiculo',
            'nombre': 'Obtener Precio de Vehículo',
            'descripcion': 'Permite obtener el precio de un vehículo.'
        }
        
        
        

    ]
