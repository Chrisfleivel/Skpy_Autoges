import csv
import io
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from compras.models import FacturaComercial
from .models import (
    Importacion,
    DocumentoAduanero,
    FaseImportacion,
    DocumentoImportacion,
    ControlFaseImportacion,
    ContenedorImportacion,
    PedidoProveedorImportacion,
    Embarque,
    EmbarqueContenedor,
    EmbarqueItem,
    GastoImportacion,
)
from .forms import (
    DocumentoAduaneroForm,
    DocumentoEmbarqueForm,
    ImportacionAduanaUpdateForm,
    ImportacionForm,
    FaseImportacionForm,
    DocumentoImportacionForm,
    ControlFaseImportacionForm,
    ContenedorImportacionForm,
    EmbarqueContenedorForm,
    EmbarqueContenedorFormSet,
    FacturaImportacionForm,
    EmbarqueForm,
    EmbarqueItemForm,
    GastoImportacionForm,
)
from .services import verificar_chasis, prorratear_costos
from .conciliacion import EstadoConciliacion, conciliar_factura, conciliar_facturas
from seguridad_usuarios.decorators import revisar_permiso
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from inventario.models import Vehiculo
from .models import ImportacionVehiculo


@revisar_permiso('importaciones.listar_documentos')
def lista_documentos(request, importacion_id):
	importacion = get_object_or_404(Importacion, pk=importacion_id)
	documentos = importacion.documentos.all()
	return render(request, 'importaciones/lista_documentos.html', {'importacion': importacion, 'documentos': documentos})


@revisar_permiso('importaciones.agregar_documento')
def agregar_documento(request, importacion_id):
	importacion = get_object_or_404(Importacion, pk=importacion_id)
	if request.method == 'POST':
		form = DocumentoAduaneroForm(request.POST, request.FILES)
		if form.is_valid():
			doc = form.save(commit=False)
			doc.importacion = importacion
			doc.subido_por = request.user if request.user.is_authenticated else None
			doc.save()
			return redirect('lista_documentos_importacion', importacion_id=importacion.id)
	else:
		form = DocumentoAduaneroForm()
	return render(request, 'importaciones/agregar_documento.html', {'form': form, 'importacion': importacion})


@revisar_permiso('importaciones.editar_importacion_aduana')
def editar_importacion_aduana(request, importacion_id):
	importacion = get_object_or_404(Importacion, pk=importacion_id)
	if request.method == 'POST':
		form = ImportacionAduanaUpdateForm(request.POST, instance=importacion)
		if form.is_valid():
			form.save()
			return redirect('lista_documentos_importacion', importacion_id=importacion.id)
	else:
		form = ImportacionAduanaUpdateForm(instance=importacion)
	return render(request, 'importaciones/editar_importacion_aduana.html', {'form': form, 'importacion': importacion})

# --------------------------------------------------------------------------
# CRUD de Contenedores
# --------------------------------------------------------------------------

@revisar_permiso('importaciones.listar_importaciones')
def lista_contenedores(request):
    contenedores = ContenedorImportacion.objects.select_related('despachante').all().order_by('-fecha_creacion')
    return render(request, 'importaciones/lista_contenedores.html', {'contenedores': contenedores})


@revisar_permiso('importaciones.agregar_importacion')
def agregar_contenedor(request):
    if request.method == 'POST':
        form = ContenedorImportacionForm(request.POST)
        if form.is_valid():
            contenedor = form.save()
            return redirect('detalle_contenedor', pk=contenedor.id)
    else:
        form = ContenedorImportacionForm()
    return render(request, 'importaciones/agregar_contenedor.html', {'form': form})


@revisar_permiso('importaciones.editar_importacion')
def editar_contenedor(request, pk):
    contenedor = get_object_or_404(ContenedorImportacion, pk=pk)
    if request.method == 'POST':
        form = ContenedorImportacionForm(request.POST, instance=contenedor)
        if form.is_valid():
            form.save()
            return redirect('detalle_contenedor', pk=contenedor.id)
    else:
        form = ContenedorImportacionForm(instance=contenedor)
    return render(request, 'importaciones/editar_contenedor.html', {'form': form, 'contenedor': contenedor})


@revisar_permiso('importaciones.detallar_importacion')
def detalle_contenedor(request, pk):
    contenedor = get_object_or_404(ContenedorImportacion, pk=pk)
    pedidos = contenedor.pedidos_proveedor.select_related('proveedor').all()
    # candidatos para asociación: pedidos de tipo abastecimiento o importacion
    from clientes_pedidos.models import Pedido
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from django.db.models import Case, IntegerField, Value, When
    from .models import PedidoProveedorImportacion

    pedidos_en_otros_contenedores = PedidoProveedorImportacion.objects.exclude(contenedor=contenedor).values_list('pedido_origen_id', flat=True)
    asociados_ids = list(contenedor.pedidos_proveedor.filter(pedido_origen__isnull=False).values_list('pedido_origen_id', flat=True))

    pedidos_bloqueados_qs = (
        Pedido.objects.filter(tipo__in=['abastecimiento', 'importacion'])
        .filter(id__in=pedidos_en_otros_contenedores)
        .order_by('-fecha_pedido')
        .distinct()
    )

    candidatos_qs = (
        Pedido.objects.filter(tipo__in=['abastecimiento', 'importacion'])
        .exclude(id__in=pedidos_en_otros_contenedores)
        .annotate(
            asociado_a_este=Case(
                When(id__in=asociados_ids, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by('asociado_a_este', '-fecha_pedido')
        .distinct()
    )

    # filtros desde GET
    search = request.GET.get('search', '').strip()
    proveedor_sel = request.GET.get('proveedor', '').strip()
    if search:
        candidatos_qs = candidatos_qs.filter(cliente__nombre__icontains=search) | candidatos_qs.filter(id__icontains=search) | candidatos_qs.filter(observaciones__icontains=search)
    if proveedor_sel:
        try:
            pid = int(proveedor_sel)
            candidatos_qs = candidatos_qs.filter(proveedor_compra__id=pid)
        except ValueError:
            pass

    # paginación de candidatos (parámetro cpage)
    paginator = Paginator(candidatos_qs, 10)
    page = request.GET.get('cpage', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # lista de proveedores para el select (tomados de candidatos_qs sin paginar, limitados)
    proveedores_list = candidatos_qs.values_list('proveedor_compra__id', 'proveedor_compra__nombre')[:50]

    return render(request, 'importaciones/detalle_contenedor.html', {
        'contenedor': contenedor,
        'pedidos': pedidos,
        'candidatos_page': page_obj,
        'paginator': paginator,
        'search': search,
        'proveedor_selected': proveedor_sel,
        'proveedores_list': proveedores_list,
        'asociados_ids': asociados_ids,
        'pedidos_bloqueados': pedidos_bloqueados_qs,
    })


@revisar_permiso('importaciones.editar_importacion')
def asociar_pedidos_contenedor(request, pk):
    """Asocia/desasocia pedidos al contenedor usando update_or_create."""
    contenedor = get_object_or_404(ContenedorImportacion, pk=pk)
    from clientes_pedidos.models import Pedido

    if request.method == 'POST':
        pedido_ids = request.POST.getlist('pedido_ids')
        # Convertir a int
        pedido_ids = [int(x) for x in pedido_ids if x]

        # Crear o actualizar asociaciones para los seleccionados
        creados = 0
        for pid in pedido_ids:
            try:
                p = Pedido.objects.get(pk=pid)
            except Pedido.DoesNotExist:
                continue
            defaults = {
                'contenedor': contenedor,
                'proveedor': getattr(p, 'proveedor_compra', None) or getattr(p, 'proveedor', None),
                'codigo': f'PO-{p.id}',
            }
            obj, created = PedidoProveedorImportacion.objects.update_or_create(pedido_origen=p, defaults=defaults)
            if created:
                creados += 1

        # Eliminar asociaciones que ya no están seleccionadas
        existentes = contenedor.pedidos_proveedor.filter(pedido_origen__isnull=False)
        for ex in existentes:
            if ex.pedido_origen and ex.pedido_origen.id not in pedido_ids:
                ex.delete()

        messages.success(request, f'Asociadas/actualizadas: {len(pedido_ids)} (nuevas: {creados})')
        return redirect('detalle_contenedor', pk=contenedor.id)

    # Para GET, redirigir al detalle donde está el modal
    return redirect('detalle_contenedor', pk=contenedor.id)


@revisar_permiso('importaciones.eliminar_importacion')
def eliminar_contenedor(request, pk):
    contenedor = get_object_or_404(ContenedorImportacion, pk=pk)
    if request.method == 'POST':
        contenedor.delete()
        return redirect('lista_contenedores')
    return render(request, 'importaciones/eliminar_contenedor.html', {'contenedor': contenedor})


# --------------------------------------------------------------------------
# CRUD de Importaciones
# --------------------------------------------------------------------------

@revisar_permiso('importaciones.listar_importaciones')
def lista_importaciones(request):
    importaciones = Importacion.objects.all().order_by('-fecha_embarque')
    return render(request, 'importaciones/lista_importaciones.html', {'importaciones': importaciones})


@revisar_permiso('importaciones.agregar_importacion')
def agregar_importacion(request):
    if request.method == 'POST':
        form = ImportacionForm(request.POST)
        if form.is_valid():
            imp = form.save(commit=False)
            imp.usuario_creador = request.user if request.user.is_authenticated else None
            imp.save()
            return redirect('detalle_importacion', pk=imp.id)
    else:
        form = ImportacionForm()
    return render(request, 'importaciones/agregar_importacion.html', {'form': form})


@revisar_permiso('importaciones.editar_importacion')
def editar_importacion(request, pk):
    importacion = get_object_or_404(Importacion, pk=pk)
    if request.method == 'POST':
        form = ImportacionForm(request.POST, instance=importacion)
        if form.is_valid():
            form.save()
            return redirect('detalle_importacion', pk=importacion.id)
    else:
        form = ImportacionForm(instance=importacion)
    return render(request, 'importaciones/editar_importacion.html', {'form': form, 'importacion': importacion})


@revisar_permiso('importaciones.detallar_importacion')
def detalle_importacion(request, pk):
    importacion = get_object_or_404(Importacion, pk=pk)
    return render(request, 'importaciones/detalle_importacion.html', {'importacion': importacion})


@revisar_permiso('importaciones.editar_importacion')
def cargar_factura_importacion(request, pk):
    importacion = get_object_or_404(Importacion, pk=pk)
    if request.method == 'POST':
        form = FacturaImportacionForm(request.POST, request.FILES)
        if form.is_valid():
            if importacion.pedido_origen:
                try:
                    importacion.pedido_origen.comprar_a_proveedor(
                        proveedor=importacion.proveedor,
                        numero_factura=form.cleaned_data['numero_factura'],
                        factura_pdf=form.cleaned_data['factura_pdf'],
                        observaciones=form.cleaned_data['observaciones'],
                    )
                    importacion.numero_factura = form.cleaned_data['numero_factura']
                    importacion.save(update_fields=['numero_factura'])
                    messages.success(request, 'Factura cargada correctamente para la importación.')
                except ValidationError as exc:
                    messages.error(request, str(exc))
            else:
                importacion.numero_factura = form.cleaned_data['numero_factura']
                importacion.save(update_fields=['numero_factura'])
                messages.success(request, 'Número de factura actualizado.')
            return redirect('detalle_importacion', pk=importacion.id)
    else:
        form = FacturaImportacionForm(initial={
            'numero_factura': importacion.numero_factura,
        })
    return render(request, 'importaciones/cargar_factura_importacion.html', {'importacion': importacion, 'form': form})


@revisar_permiso('importaciones.eliminar_importacion')
def eliminar_importacion(request, pk):
    importacion = get_object_or_404(Importacion, pk=pk)
    if request.method == 'POST':
        importacion.delete()
        return redirect('lista_importaciones')
    return render(request, 'importaciones/eliminar_importacion.html', {'importacion': importacion})



@receiver(post_save, sender=ImportacionVehiculo)
def actualizar_estado_vehiculo_tras_importacion(sender, instance, **kwargs):
    """
    Sincroniza el estado del vehículo a partir del estado canónico del embarque.
    La UI no debe duplicar un mapeo paralelo: la fuente de verdad vive en
    Vehiculo.estado_desde_embarque(...).
    """
    nuevo_estado_vehiculo = Vehiculo.estado_desde_embarque(instance.estado)
    if not nuevo_estado_vehiculo:
        return

    vehiculo = instance.vehiculo
    if vehiculo is None:
        return

    if vehiculo.estado != nuevo_estado_vehiculo:
        vehiculo.estado = nuevo_estado_vehiculo
        vehiculo.save(update_fields=['estado'])


# --------------------------------------------------------------------------
# UI para embarques importación
# --------------------------------------------------------------------------

@revisar_permiso('importaciones.listar_importaciones')
def lista_embarques(request):
    embarques = Embarque.objects.prefetch_related('items', 'gastos', 'contenedores').order_by('-pk')
    return render(request, 'importaciones/lista_embarques.html', {'embarques': embarques})


@revisar_permiso('importaciones.agregar_importacion')
def crear_embarque(request):
    if request.method == 'POST':
        form = EmbarqueForm(request.POST)
        formset = EmbarqueContenedorFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                embarque = form.save()
                formset.instance = embarque
                formset.save()
            messages.success(request, 'Embarque creado correctamente.')
            return redirect('detalle_embarque', pk=embarque.pk)
    else:
        form = EmbarqueForm()
        formset = EmbarqueContenedorFormSet()
    return render(request, 'importaciones/formulario_embarque.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nuevo embarque',
    })


@revisar_permiso('importaciones.editar_importacion')
def editar_embarque(request, pk):
    embarque = get_object_or_404(Embarque, pk=pk)
    if request.method == 'POST':
        form = EmbarqueForm(request.POST, instance=embarque)
        formset = EmbarqueContenedorFormSet(request.POST, instance=embarque)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Embarque actualizado.')
            return redirect('detalle_embarque', pk=embarque.pk)
    else:
        form = EmbarqueForm(instance=embarque)
        formset = EmbarqueContenedorFormSet(instance=embarque)
    return render(request, 'importaciones/formulario_embarque.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Editar embarque',
        'embarque': embarque,
    })


@revisar_permiso('importaciones.detallar_importacion')
def detalle_embarque(request, pk):
    embarque = get_object_or_404(
        Embarque.objects.prefetch_related(
            'items__factura_item__factura',
            'items__contenedor',
            'gastos',
            'contenedores',
            'documentos',
        ),
        pk=pk,
    )
    item_form = EmbarqueItemForm(embarque=embarque)
    gasto_form = GastoImportacionForm()
    contenedor_form = EmbarqueContenedorForm()
    documento_form = DocumentoEmbarqueForm()
    verificacion = verificar_chasis(embarque)
    flujo = embarque.flujo_operativo
    return render(request, 'importaciones/detalle_embarque.html', {
        'embarque': embarque,
        'items': embarque.items.select_related('factura_item__factura', 'contenedor').all(),
        'gastos': embarque.gastos.all(),
        'contenedores': embarque.contenedores.all(),
        'documentos': embarque.documentos.all(),
        'item_form': item_form,
        'gasto_form': gasto_form,
        'contenedor_form': contenedor_form,
        'documento_form': documento_form,
        'verificacion': verificacion,
        'flujo_operativo': flujo,
    })


@revisar_permiso('importaciones.editar_importacion')
def agregar_item_embarque(request, pk):
    embarque = get_object_or_404(Embarque, pk=pk)
    if request.method == 'POST':
        form = EmbarqueItemForm(request.POST, embarque=embarque)
        if form.is_valid():
            item = form.save(commit=False)
            item.embarque = embarque
            item.save()
            messages.success(request, 'Ítem asociado al embarque.')
            return redirect('detalle_embarque', pk=embarque.pk)
        for error in form.errors.get('__all__', []):
            messages.error(request, error)
        for campo, errores in form.errors.items():
            if campo == '__all__':
                continue
            for error in errores:
                messages.error(request, f'{campo}: {error}')
    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.editar_importacion')
def agregar_contenedor_embarque(request, pk):
    """Agrega un contenedor al embarque desde la pantalla de detalle."""
    embarque = get_object_or_404(Embarque, pk=pk)
    if request.method == 'POST':
        form = EmbarqueContenedorForm(request.POST)
        if form.is_valid():
            contenedor = form.save(commit=False)
            contenedor.embarque = embarque
            contenedor.save()
            messages.success(request, f'Contenedor {contenedor.numero} agregado al embarque.')
            return redirect('detalle_embarque', pk=embarque.pk)
        for error in form.errors.get('__all__', []):
            messages.error(request, error)
        for campo, errores in form.errors.items():
            if campo == '__all__':
                continue
            for error in errores:
                messages.error(request, f'{campo}: {error}')
    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.eliminar_importacion')
def eliminar_contenedor_embarque(request, pk, contenedor_pk):
    """Elimina un contenedor vacío del embarque."""
    embarque = get_object_or_404(Embarque, pk=pk)
    contenedor = get_object_or_404(embarque.contenedores.all(), pk=contenedor_pk)

    if contenedor.items.exists():
        messages.error(request, 'El contenedor tiene ítems asignados: quitá los ítems antes de eliminarlo.')
        return redirect('detalle_embarque', pk=embarque.pk)

    if request.method == 'POST':
        numero = contenedor.numero
        contenedor.delete()
        messages.success(request, f'Contenedor {numero} eliminado.')
        return redirect('detalle_embarque', pk=embarque.pk)

    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.agregar_documento')
def agregar_documento_embarque(request, pk):
    """Adjunta un documento al embarque (B/L, packing list, despacho, póliza)."""
    embarque = get_object_or_404(Embarque, pk=pk)

    if request.method == 'POST':
        form = DocumentoEmbarqueForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.embarque = embarque
            documento.save()
            messages.success(request, 'Documento adjuntado al embarque.')
            return redirect('detalle_embarque', pk=embarque.pk)
        for error in form.errors.get('__all__', []):
            messages.error(request, error)
        for campo, errores in form.errors.items():
            if campo == '__all__':
                continue
            for error in errores:
                messages.error(request, f'{campo}: {error}')
    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.eliminar_importacion')
def eliminar_documento_embarque(request, pk, documento_pk):
    """Quita un documento adjunto del embarque."""
    embarque = get_object_or_404(Embarque, pk=pk)
    documento = get_object_or_404(embarque.documentos.all(), pk=documento_pk)

    if request.method == 'POST':
        documento.delete()
        messages.success(request, 'Documento eliminado.')
        return redirect('detalle_embarque', pk=embarque.pk)

    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.editar_importacion')
def agregar_gasto_embarque(request, pk):
    embarque = get_object_or_404(Embarque, pk=pk)
    if request.method == 'POST':
        form = GastoImportacionForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.embarque = embarque
            gasto.save()
            messages.success(request, 'Gasto agregado correctamente.')
            return redirect('detalle_embarque', pk=embarque.pk)
    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.editar_importacion')
def verificar_embarque(request, pk):
    embarque = get_object_or_404(Embarque, pk=pk)
    resultado = verificar_chasis(embarque)
    if resultado['ok']:
        messages.success(request, 'Los chasis coinciden con el B/L y el vehículo.')
    else:
        messages.error(request, 'Se detectaron discrepancias en los chasis.')
    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.editar_importacion')
def prorratear_embarque(request, pk):
    embarque = get_object_or_404(Embarque, pk=pk)
    resultado = prorratear_costos(embarque)
    if resultado['ok']:
        messages.success(request, 'Los gastos fueron prorrateados correctamente.')
    else:
        messages.error(request, resultado.get('mensaje', 'No fue posible prorratear los costos.'))
    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.editar_importacion')
def cerrar_embarque(request, pk):
    embarque = get_object_or_404(Embarque, pk=pk)
    try:
        embarque.cambiar_estado(Embarque.Estado.CERRADO)
        messages.success(request, 'El embarque fue cerrado correctamente.')
    except Exception as exc:
        messages.error(request, str(exc))
    return redirect('detalle_embarque', pk=embarque.pk)


@revisar_permiso('importaciones.detallar_importacion')
def resumen_embarque(request, pk):
    embarque = get_object_or_404(
        Embarque.objects.prefetch_related('items__factura_item', 'items__contenedor', 'gastos', 'contenedores'),
        pk=pk,
    )
    items = list(embarque.items.select_related('factura_item__factura', 'contenedor').all())
    gastos = list(embarque.gastos.all())
    total_gastos = sum((gasto.monto_base for gasto in gastos), 0)
    total_prorrateado = sum((item.costo_prorrateado or 0 for item in items), 0)
    diferencia = total_gastos - total_prorrateado
    verificacion = verificar_chasis(embarque)

    context = {
        'embarque': embarque,
        'items': items,
        'gastos': gastos,
        'contenedores': embarque.contenedores.all(),
        'total_gastos': total_gastos,
        'total_prorrateado': total_prorrateado,
        'diferencia': diferencia,
        'verificacion': verificacion,
    }
    return render(request, 'importaciones/resumen_embarque.html', context)


@revisar_permiso('importaciones.detallar_importacion')
def exportar_resumen_embarque(request, pk):
    embarque = get_object_or_404(
        Embarque.objects.prefetch_related('items__factura_item', 'items__contenedor', 'gastos', 'contenedores'),
        pk=pk,
    )
    items = list(embarque.items.select_related('factura_item__factura', 'contenedor').all())
    gastos = list(embarque.gastos.all())
    total_gastos = sum((gasto.monto_base for gasto in gastos), 0)
    total_prorrateado = sum((item.costo_prorrateado or 0 for item in items), 0)
    diferencia = total_gastos - total_prorrateado
    verificacion = verificar_chasis(embarque)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['EMBARQUE_RESUMEN'])
    writer.writerow(['ID', embarque.pk])
    writer.writerow(['REFERENCIA', embarque.referencia_interna or '-'])
    writer.writerow(['B/L', embarque.bl_numero or '-'])
    writer.writerow(['SHIPPER', embarque.shipper or '-'])
    writer.writerow(['CONSIGNEE', embarque.consignatario or '-'])
    writer.writerow(['NOTIFY', embarque.notify or '-'])
    writer.writerow(['DESTINO', embarque.destino_final or '-'])
    writer.writerow(['ESTADO', embarque.get_estado_display()])
    writer.writerow(['TOTAL_GASTOS', str(total_gastos)])
    writer.writerow(['TOTAL_PRORRATEADO', str(total_prorrateado)])
    writer.writerow(['DIFERENCIA', str(diferencia)])
    writer.writerow(['VERIFICACION_CHASIS', 'OK' if verificacion['ok'] else 'DISCREPANTE'])
    writer.writerow([])
    writer.writerow(['CONTENEDOR', 'TIPO', 'SELLO', 'PESO_BRUTO_KG', 'VOLUMEN_M3', 'UNIDADES'])
    for contenedor in embarque.contenedores.all():
        writer.writerow([
            contenedor.numero,
            contenedor.tipo or '-',
            contenedor.sello or '-',
            str(contenedor.peso_bruto_kg or ''),
            str(contenedor.volumen_m3 or ''),
            contenedor.unidades,
        ])
    writer.writerow([])
    writer.writerow(['ITEM', 'DESCRIPCION', 'CONTENEDOR', 'CHASIS_BL', 'COSTO_PRORRATEADO'])
    for item in items:
        writer.writerow([
            item.pk,
            item.factura_item.descripcion if item.factura_item else '-',
            item.contenedor.numero if item.contenedor else '-',
            item.chasis_bl or '-',
            str(item.costo_prorrateado or 0),
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="RESUMEN_EMBARQUE_{embarque.pk}.csv"'
    return response


# --------------------------------------------------------------------------
# Vistas para Gestión de Fases de Importación
# --------------------------------------------------------------------------

@revisar_permiso('importaciones.detallar_importacion')
def listar_fases_importacion(request, importacion_id):
    """Lista todas las fases de una importación."""
    importacion = get_object_or_404(Importacion, pk=importacion_id)
    fases = FaseImportacion.objects.filter(importacion=importacion).select_related('control')
    
    context = {
        'importacion': importacion,
        'fases': fases,
    }
    return render(request, 'importaciones/listar_fases.html', context)


@revisar_permiso('importaciones.editar_importacion')
def crear_fase_importacion(request, importacion_id):
    """Crea una nueva fase para una importación."""
    importacion = get_object_or_404(Importacion, pk=importacion_id)
    
    if request.method == 'POST':
        form = FaseImportacionForm(request.POST)
        if form.is_valid():
            fase = form.save(commit=False)
            fase.importacion = importacion
            fase.save()
            return redirect('listar_fases_importacion', importacion_id=importacion.id)
    else:
        form = FaseImportacionForm()
    
    context = {
        'form': form,
        'importacion': importacion,
    }
    return render(request, 'importaciones/crear_fase.html', context)


@revisar_permiso('importaciones.editar_importacion')
def editar_fase_importacion(request, fase_id):
    """Edita una fase de importación."""
    fase = get_object_or_404(FaseImportacion, pk=fase_id)
    
    if request.method == 'POST':
        form = FaseImportacionForm(request.POST, instance=fase)
        if form.is_valid():
            form.save()
            return redirect('listar_fases_importacion', importacion_id=fase.importacion.id)
    else:
        form = FaseImportacionForm(instance=fase)
    
    context = {
        'form': form,
        'fase': fase,
        'importacion': fase.importacion,
    }
    return render(request, 'importaciones/editar_fase.html', context)


@revisar_permiso('importaciones.detallar_importacion')
def detalle_fase_importacion(request, fase_id):
    """Muestra el detalle de una fase con sus documentos."""
    fase = get_object_or_404(FaseImportacion, pk=fase_id)
    documentos = DocumentoImportacion.objects.filter(fase=fase)
    
    context = {
        'fase': fase,
        'importacion': fase.importacion,
        'documentos': documentos,
    }
    return render(request, 'importaciones/detalle_fase.html', context)


@revisar_permiso('importaciones.agregar_documento')
def marcar_fase_completada(request, fase_id):
    """Marca una fase como completada."""
    fase = get_object_or_404(FaseImportacion, pk=fase_id)
    
    if request.method == 'POST':
        fase.estado_completado = True
        fase.fecha_completado = timezone.now()
        fase.save()
        return redirect('detalle_fase_importacion', fase_id=fase.id)
    
    context = {
        'fase': fase,
        'importacion': fase.importacion,
    }
    return render(request, 'importaciones/confirmar_completar_fase.html', context)


# --------------------------------------------------------------------------
# Vistas para Gestión de Documentos de Importación
# --------------------------------------------------------------------------

@revisar_permiso('importaciones.agregar_documento')
def agregar_documento_fase(request, fase_id):
    """Carga un documento en una fase específica de la importación."""
    fase = get_object_or_404(FaseImportacion, pk=fase_id)
    
    if request.method == 'POST':
        form = DocumentoImportacionForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.fase = fase
            doc.cargado_por = request.user if request.user.is_authenticated else None
            doc.save()
            return redirect('detalle_fase_importacion', fase_id=fase.id)
    else:
        form = DocumentoImportacionForm()
    
    context = {
        'form': form,
        'fase': fase,
        'importacion': fase.importacion,
    }
    return render(request, 'importaciones/agregar_documento_fase.html', context)


@revisar_permiso('importaciones.detallar_importacion')
def listar_documentos_fase(request, fase_id):
    """Lista todos los documentos de una fase."""
    fase = get_object_or_404(FaseImportacion, pk=fase_id)
    documentos = DocumentoImportacion.objects.filter(fase=fase)
    
    context = {
        'fase': fase,
        'importacion': fase.importacion,
        'documentos': documentos,
    }
    return render(request, 'importaciones/listar_documentos_fase.html', context)


@revisar_permiso('importaciones.editar_importacion')
def validar_documento(request, documento_id):
    """Valida un documento de la importación."""
    documento = get_object_or_404(DocumentoImportacion, pk=documento_id)
    
    if request.method == 'POST':
        documento.marcar_validado(usuario=request.user if request.user.is_authenticated else None)
        return redirect('detalle_fase_importacion', fase_id=documento.fase.id)
    
    context = {
        'documento': documento,
        'fase': documento.fase,
        'importacion': documento.fase.importacion,
    }
    return render(request, 'importaciones/confirmar_validar_documento.html', context)


@revisar_permiso('importaciones.editar_importacion')
def rechazar_documento(request, documento_id):
    """Rechaza un documento de la importación."""
    documento = get_object_or_404(DocumentoImportacion, pk=documento_id)
    
    if request.method == 'POST':
        documento.marcar_rechazado(usuario=request.user if request.user.is_authenticated else None)
        return redirect('detalle_fase_importacion', fase_id=documento.fase.id)
    
    context = {
        'documento': documento,
        'fase': documento.fase,
        'importacion': documento.fase.importacion,
    }
    return render(request, 'importaciones/confirmar_rechazar_documento.html', context)


@revisar_permiso('importaciones.eliminar_importacion')
def eliminar_documento(request, documento_id):
    """Elimina un documento de la importación."""
    documento = get_object_or_404(DocumentoImportacion, pk=documento_id)
    fase_id = documento.fase.id
    
    if request.method == 'POST':
        # Eliminar archivo si existe
        if documento.archivo:
            documento.archivo.delete()
        documento.delete()
        return redirect('detalle_fase_importacion', fase_id=fase_id)
    
    context = {
        'documento': documento,
        'fase': documento.fase,
        'importacion': documento.fase.importacion,
    }
    return render(request, 'importaciones/confirmar_eliminar_documento.html', context)


# --------------------------------------------------------------------------
# Vistas para Control de Cumplimiento de Fases
# --------------------------------------------------------------------------

@revisar_permiso('importaciones.editar_importacion')
def registrar_control_fase(request, fase_id):
    """Registra el cumplimiento de requisitos en una fase."""
    fase = get_object_or_404(FaseImportacion, pk=fase_id)
    control, created = ControlFaseImportacion.objects.get_or_create(fase=fase)
    
    if request.method == 'POST':
        form = ControlFaseImportacionForm(request.POST, instance=control)
        if form.is_valid():
            ctrl = form.save(commit=False)
            ctrl.verificado_por = request.user if request.user.is_authenticated else None
            ctrl.save()
            return redirect('detalle_fase_importacion', fase_id=fase.id)
    else:
        form = ControlFaseImportacionForm(instance=control)
    
    context = {
        'form': form,
        'fase': fase,
        'importacion': fase.importacion,
        'control': control,
    }
    return render(request, 'importaciones/registrar_control_fase.html', context)


# --------------------------------------------------------------------------
# Conciliación informativa de los documentos de importación
# --------------------------------------------------------------------------

@revisar_permiso('importaciones.listar_conciliacion')
def lista_conciliacion(request):
    """
    Conciliación informativa de los tres documentos de la operación.

    Compara, para cada factura comercial, la factura, el B/L con sus
    contenedores y la liquidación con su pago. No bloquea nada: solo informa.
    """
    conciliaciones = conciliar_facturas()

    # Resumen por estado (sobre el total, antes de filtrar).
    resumen = {estado: 0 for estado in EstadoConciliacion.SEMAFOROS}
    for conciliacion in conciliaciones:
        resumen[conciliacion.estado] = resumen.get(conciliacion.estado, 0) + 1

    estado_filtro = (request.GET.get('estado') or '').strip().upper()
    if estado_filtro in EstadoConciliacion.SEMAFOROS:
        conciliaciones = [c for c in conciliaciones if c.estado == estado_filtro]

    busqueda = (request.GET.get('q') or '').strip()
    if busqueda:
        busqueda = busqueda.lower()
        conciliaciones = [
            c for c in conciliaciones
            if busqueda in (c.factura.numero or '').lower()
            or busqueda in (c.factura.proveedor.nombre or '').lower()
            or busqueda in (c.factura.proveedor.razon_social or '').lower()
        ]

    return render(request, 'importaciones/lista_conciliacion.html', {
        'conciliaciones': conciliaciones,
        'resumen': resumen,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
        'estados': EstadoConciliacion,
    })


@revisar_permiso('importaciones.listar_conciliacion')
def detalle_conciliacion(request, pk):
    """Detalle de la conciliación de los documentos de una factura."""
    factura = get_object_or_404(
        FacturaComercial.objects.select_related('proveedor').prefetch_related('items'),
        pk=pk,
    )
    conciliacion = conciliar_factura(factura)

    return render(request, 'importaciones/detalle_conciliacion.html', {
        'conciliacion': conciliacion,
        'factura': factura,
        'estados': EstadoConciliacion,
    })


@revisar_permiso('importaciones.listar_conciliacion')
def exportar_conciliacion(request):
    """Exporta la conciliación a CSV (informe para el auditor)."""
    conciliaciones = conciliar_facturas()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['CONCILIACION_DOCUMENTOS'])
    writer.writerow(['FECHA', timezone.now().date()])
    writer.writerow([])
    writer.writerow([
        'FACTURA', 'PROVEEDOR', 'FECHA', 'MONEDA', 'TOTAL',
        'ESTADO', 'UNIDADES_FACTURADAS', 'UNIDADES_EMBARCADAS',
        'EMBARCQUES', 'LIQUIDACION', 'PAGO', 'SALDO_PENDIENTE',
        'HALLAZGOS',
    ])
    for conciliacion in conciliaciones:
        factura = conciliacion.factura
        writer.writerow([
            factura.numero,
            factura.proveedor.razon_social or factura.proveedor.nombre,
            factura.fecha,
            factura.moneda,
            str(factura.total_declarado),
            conciliacion.etiqueta,
            conciliacion.unidades_facturadas,
            conciliacion.unidades_embarcadas,
            '; '.join(
                f'#{e.pk} {e.referencia_interna or e.bl_numero or ""}'.strip()
                for e in conciliacion.embarques
            ),
            conciliacion.orden.pk if conciliacion.orden else '',
            conciliacion.pago.referencia_op if conciliacion.pago else '',
            str(conciliacion.saldo_pendiente),
            ' | '.join(f'{h.concepto}: {h.detalle}' for h in conciliacion.hallazgos),
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="CONCILIACION_DOCUMENTOS.csv"'
    return response


permisos_iniciales_importaciones = [
        
        {
            'codename': 'importaciones.listar_documentos',
            'nombre': 'Listar Documentos',
            'descripcion': 'Permite ver la lista de Documentos registrados.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.agregar_documento',
            'nombre': 'Agregar Documento',
            'descripcion': 'Permite agregar un nuevo Documento a una Importación.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.editar_importacion_aduana',
            'nombre': 'Editar Importación Aduana',
            'descripcion': 'Permite editar los datos de la Importación relacionados con Aduana.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.listar_importaciones',
            'nombre': 'Listar Importaciones',
            'descripcion': 'Permite ver la lista de Importaciones registradas.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.agregar_importacion',
            'nombre': 'Agregar Importación',
            'descripcion': 'Permite agregar una nueva Importación.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.editar_importacion',
            'nombre': 'Editar Importación',
            'descripcion': 'Permite editar los datos de una Importación existente.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.detallar_importacion',
            'nombre': 'Detallar Importación',
            'descripcion': 'Permite ver el detalle completo de una Importación.',
            'sector': 'Importaciones',
        },
        {
            'codename': 'importaciones.eliminar_importacion',
            'nombre': 'Eliminar Importación',
            'descripcion': 'Permite eliminar una Importación existente.',
            'sector': 'Importaciones',
        }
]