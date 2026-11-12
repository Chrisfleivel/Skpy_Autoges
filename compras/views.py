from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from seguridad_usuarios.decorators import revisar_permiso

from .forms import DocumentoFacturaForm, FacturaComercialForm, FacturaItemFormSet
from .models import FacturaComercial
from . import services


def _filtros_desde_request(request):
    """Normaliza los filtros de la lista de facturas."""
    estado = request.GET.get('estado', '').strip()
    moneda = request.GET.get('moneda', '').strip()
    busqueda = request.GET.get('q', '').strip()

    queryset = FacturaComercial.objects.select_related(
        'proveedor', 'cliente_importador'
    ).prefetch_related('items')

    if estado:
        queryset = queryset.filter(estado=estado)
    if moneda:
        queryset = queryset.filter(moneda=moneda)
    if busqueda:
        queryset = queryset.filter(
            Q(numero__icontains=busqueda)
            | Q(proveedor__razon_social__icontains=busqueda)
            | Q(proveedor__nombre__icontains=busqueda)
            | Q(cliente_importador__razon_social__icontains=busqueda)
            | Q(cliente_importador__nombre__icontains=busqueda)
        )
    return queryset, {'estado': estado, 'moneda': moneda, 'q': busqueda}


@revisar_permiso('compras.lista_facturas')
def lista_facturas(request):
    """Listado de facturas comerciales con filtros y resumen de cartera."""
    queryset, filtros = _filtros_desde_request(request)
    facturas = queryset.order_by('-fecha', '-id')

    resumen = facturas.aggregate(
        total=Sum('total_declarado'),
        pagado=Sum('monto_pagado'),
    )

    context = {
        'facturas': facturas,
        'filtros': filtros,
        'resumen_total': resumen['total'] or Decimal('0'),
        'resumen_pagado': resumen['pagado'] or Decimal('0'),
        'estados': FacturaComercial.Estado.choices,
        'monedas': FacturaComercial._meta.get_field('moneda').choices,
    }
    return render(request, 'compras/lista_facturas.html', context)


@revisar_permiso('compras.agregar_factura')
def agregar_factura(request):
    """Alta de factura comercial con sus ítems en línea."""
    if request.method == 'POST':
        form = FacturaComercialForm(request.POST, request.FILES)
        formset = FacturaItemFormSet(request.POST, instance=FacturaComercial())
        if form.is_valid() and formset.is_valid():
            factura = services.crear_factura_con_items(form, formset)
            messages.success(request, f'Factura {factura.numero} registrada correctamente.')
            return redirect('detalle_factura_comercial', pk=factura.pk)
    else:
        form = FacturaComercialForm()
        formset = FacturaItemFormSet(instance=FacturaComercial())

    return render(request, 'compras/formulario_factura.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nueva factura comercial',
        'accion': 'agregar_factura_comercial',
    })


@revisar_permiso('compras.editar_factura')
def editar_factura(request, pk):
    """Edición de una factura comercial en estado borrador."""
    factura = get_object_or_404(FacturaComercial, pk=pk)

    if not services.puede_editarse(factura):
        messages.warning(request, 'Solo las facturas en borrador pueden editarse.')
        return redirect('detalle_factura_comercial', pk=factura.pk)

    if request.method == 'POST':
        form = FacturaComercialForm(request.POST, request.FILES, instance=factura)
        formset = FacturaItemFormSet(request.POST, instance=factura)
        if form.is_valid() and formset.is_valid():
            factura = services.actualizar_factura_con_items(form, formset)
            messages.success(request, f'Factura {factura.numero} actualizada.')
            return redirect('detalle_factura_comercial', pk=factura.pk)
    else:
        form = FacturaComercialForm(instance=factura)
        formset = FacturaItemFormSet(instance=factura)

    return render(request, 'compras/formulario_factura.html', {
        'form': form,
        'formset': formset,
        'factura': factura,
        'titulo': f'Editar factura {factura.numero}',
        'accion': 'editar_factura_comercial',
    })


@revisar_permiso('compras.detalle_factura')
def detalle_factura(request, pk):
    """Detalle de la factura comercial: datos, ítems, documentos y pagos."""
    factura = get_object_or_404(
        FacturaComercial.objects.select_related(
            'proveedor', 'cliente_importador', 'lc_banco'
        ).prefetch_related('items__vehiculo', 'documentos', 'pagos'),
        pk=pk,
    )

    documentos = factura.documentos.all()
    pagos = factura.pagos.all()
    discrepancias = services.validar_chasis_contra_inventario(factura)

    context = {
        'factura': factura,
        'items': factura.items.all(),
        'documentos': documentos,
        'pagos': pagos,
        'documento_form': DocumentoFacturaForm(),
        'discrepancias': discrepancias,
        'puede_editar': services.puede_editarse(factura),
    }
    return render(request, 'compras/detalle_factura.html', context)


@revisar_permiso('compras.eliminar_factura')
def eliminar_factura(request, pk):
    """Eliminación de una factura comercial en estado borrador."""
    factura = get_object_or_404(FacturaComercial, pk=pk)

    permitido, motivo = services.puede_eliminarse(factura)
    if not permitido:
        messages.error(request, motivo)
        return redirect('detalle_factura_comercial', pk=factura.pk)

    if request.method == 'POST':
        numero = factura.numero
        factura.delete()
        messages.success(request, f'Factura {numero} eliminada.')
        return redirect('lista_facturas_comerciales')

    return render(request, 'compras/confirmar_eliminar_factura.html', {'factura': factura})


@revisar_permiso('compras.confirmar_factura')
def confirmar_factura(request, pk):
    """Confirma la factura (valida que el total declarado coincida con los ítems)."""
    factura = get_object_or_404(FacturaComercial, pk=pk)

    if request.method == 'POST':
        try:
            services.confirmar_factura(factura, usuario=request.user)
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
        except Exception as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f'Factura {factura.numero} confirmada.')
        return redirect('detalle_factura_comercial', pk=factura.pk)

    return redirect('detalle_factura_comercial', pk=factura.pk)


@revisar_permiso('compras.editar_factura')
def agregar_documento_factura(request, pk):
    """Adjunta un documento a la factura comercial."""
    factura = get_object_or_404(FacturaComercial, pk=pk)

    if request.method == 'POST':
        form = DocumentoFacturaForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.factura = factura
            documento.save()
            messages.success(request, 'Documento adjuntado a la factura.')
            return redirect('detalle_factura_comercial', pk=factura.pk)
    else:
        form = DocumentoFacturaForm()

    return render(request, 'compras/detalle_factura.html', {
        'factura': factura,
        'items': factura.items.all(),
        'documentos': factura.documentos.all(),
        'pagos': factura.pagos.all(),
        'documento_form': form,
        'discrepancias': services.validar_chasis_contra_inventario(factura),
        'puede_editar': services.puede_editarse(factura),
    })


@revisar_permiso('compras.editar_factura')
def eliminar_documento_factura(request, pk, documento_pk):
    """Quita un documento adjunto de la factura comercial."""
    factura = get_object_or_404(FacturaComercial, pk=pk)
    documento = get_object_or_404(factura.documentos.all(), pk=documento_pk)

    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado.')
        return redirect('detalle_factura_comercial', pk=factura.pk)

    return redirect('detalle_factura_comercial', pk=factura.pk)
