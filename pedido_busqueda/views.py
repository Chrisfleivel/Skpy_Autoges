from django.db.models import Q
from django.shortcuts import render

from clientes_pedidos.models import Pedido
from seguridad_usuarios.decorators import revisar_permiso


@revisar_permiso('clientes_pedidos.listar_pedidos')
def lista_pedidos_busqueda(request):
    """Lista de pedidos de tipo búsqueda con filtros por estado y texto."""
    estado = request.GET.get('estado') or 'all'
    q = request.GET.get('q', '').strip()

    qs = Pedido.objects.filter(tipo='busqueda').select_related('cliente').order_by('-fecha_pedido')

    if estado and estado != 'all':
        qs = qs.filter(estado=estado)

    if q:
        qs = qs.filter(
            Q(cliente__nombre__icontains=q)
            | Q(cliente__apellidos__icontains=q)
            | Q(cliente__razon_social__icontains=q)
            | Q(cliente__ruc__icontains=q)
            | Q(cliente__documento_identidad__icontains=q)
            | Q(cliente__email__icontains=q)
            | Q(observaciones__icontains=q)
        )

    pedidos = qs.order_by('-fecha_pedido')
    return render(request, 'pedido_busqueda/lista_pedidos_busqueda.html', {
        'pedidos': pedidos,
        'q': q,
        'estado': estado,
    })


