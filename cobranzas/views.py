import csv
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.db.models import Count, Q, Sum
from django.contrib import messages
from django.utils import timezone
from xhtml2pdf import pisa

from clientes_pedidos.models import Pedido
from configuraciones_maestras.models import Empresa, Sucursal
from seguridad_usuarios.decorators import revisar_permiso, revisar_permisos_roles

from .forms import AperturaCajaForm, CierreCajaForm
from .models import Caja, Pago, AperturaCaja, CierreCaja


@revisar_permiso('cobranzas.agregar_venta')
def agregar_venta(request):
    """Vista para agregar una nueva venta."""
    return render(request, 'cobranzas/agregar_venta.html')


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido'])
def panel_caja(request):
    """Panel principal de control de cajas por sucursal."""
    cajas = Caja.objects.select_related('sucursal', 'empleado_actual').all().order_by('sucursal__nombre', 'nombre')
    empleado = getattr(getattr(request.user, 'perfil', None), 'empleado', None) or getattr(request.user, 'empleado', None)
    caja_actual = None
    if empleado:
        caja_actual = Caja.objects.filter(estado='abierta', empleado_actual=empleado).select_related('sucursal').first()
    return render(request, 'cobranzas/panel_caja.html', {
        'cajas': cajas,
        'empleado': empleado,
        'caja_actual': caja_actual,
    })


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido', 'cobranzas.cerrar_caja'])
def dashboard_caja(request):
    """Dashboard ejecutivo con resumen de caja y rendimiento del día."""
    fecha_raw = request.GET.get('fecha') or timezone.localdate().isoformat()
    try:
        fecha = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
    except ValueError:
        fecha = timezone.localdate()

    pagos = Pago.objects.filter(fecha_pago__date=fecha).select_related('caja', 'sucursal', 'empleado')
    pagos_ayer = Pago.objects.filter(fecha_pago__date=fecha - timedelta(days=1)).select_related('caja', 'sucursal', 'empleado')
    total_cobrado = sum((p.monto for p in pagos), Decimal('0.00'))
    total_efectivo = sum(
        (p.monto for p in pagos if str(p.metodo_pago).lower() == 'efectivo'),
        Decimal('0.00'),
    )
    total_transferencia = sum(
        (p.monto for p in pagos if str(p.metodo_pago).lower() in {'transferencia', 'transferencia bancaria', 'banco'}),
        Decimal('0.00'),
    )
    total_ayer = sum((p.monto for p in pagos_ayer), Decimal('0.00'))
    total_pagos_hoy = pagos.count()
    ticket_promedio = (total_cobrado / total_pagos_hoy) if total_pagos_hoy else Decimal('0.00')
    crecimiento = ((total_cobrado - total_ayer) / total_ayer * Decimal('100')) if total_ayer else Decimal('0.00')
    cajas_abiertas = Caja.objects.filter(estado='abierta').count()

    tendencia_hora = []
    for item in pagos.extra(select={'hora': "strftime('%H', fecha_pago)"}).values('hora').annotate(total=Sum('monto'), cantidad=Count('id')).order_by('hora'):
        total_hora = item.get('total') or Decimal('0.00')
        tendencia_hora.append({
            'hora': f"{int(item['hora']):02d}:00",
            'total': total_hora,
            'cantidad': item.get('cantidad') or 0,
            'pct': (total_hora / total_cobrado * Decimal('100')) if total_cobrado else Decimal('0.00'),
        })

    top_sucursal = []
    for item in pagos.values('sucursal_id', 'sucursal__nombre').annotate(total=Sum('monto')).order_by('-total')[:5]:
        top_sucursal.append({
            'nombre': item.get('sucursal__nombre') or 'Sin sucursal',
            'total': item.get('total') or Decimal('0.00'),
        })

    top_empleado = []
    for item in pagos.values('empleado_id', 'empleado__nombre', 'empleado__apellidos').annotate(total=Sum('monto')).order_by('-total')[:5]:
        nombre = item.get('empleado__nombre') or ''
        apellidos = item.get('empleado__apellidos') or ''
        empleado_nombre = f'{nombre} {apellidos}'.strip() or 'Sin empleado'
        top_empleado.append({
            'nombre': empleado_nombre,
            'total': item.get('total') or Decimal('0.00'),
        })

    return render(request, 'cobranzas/dashboard_caja.html', {
        'fecha': fecha,
        'pagos': pagos.order_by('-fecha_pago'),
        'total_cobrado': total_cobrado,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'ticket_promedio': ticket_promedio,
        'crecimiento': crecimiento,
        'total_ayer': total_ayer,
        'total_pagos_hoy': total_pagos_hoy,
        'cajas_abiertas': cajas_abiertas,
        'tendencia_hora': tendencia_hora,
        'top_sucursal': top_sucursal,
        'top_empleado': top_empleado,
    })


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido', 'cobranzas.cerrar_caja'])
def reporte_caja(request):
    """Reporte de caja por rango de fechas con análisis por día, sucursal y empleado."""
    fecha_inicio_raw = request.GET.get('fecha_inicio') or (timezone.localdate() - timedelta(days=6)).isoformat()
    fecha_fin_raw = request.GET.get('fecha_fin') or timezone.localdate().isoformat()

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date()
    except ValueError:
        fecha_inicio = timezone.localdate() - timedelta(days=6)

    try:
        fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date()
    except ValueError:
        fecha_fin = timezone.localdate()

    if fecha_fin < fecha_inicio:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    pagos = Pago.objects.filter(fecha_pago__date__range=[fecha_inicio, fecha_fin]).select_related('caja', 'sucursal', 'empleado')
    total_cobrado = sum((p.monto for p in pagos), Decimal('0.00'))
    total_efectivo = sum(
        (p.monto for p in pagos if str(p.metodo_pago).lower() == 'efectivo'),
        Decimal('0.00'),
    )
    total_transferencia = sum(
        (p.monto for p in pagos if str(p.metodo_pago).lower() in {'transferencia', 'transferencia bancaria', 'banco'}),
        Decimal('0.00'),
    )

    pagos_por_dia = list(
        pagos.values('fecha_pago__date').annotate(total=Sum('monto')).order_by('fecha_pago__date')
    )
    total_por_dia = {item['fecha_pago__date']: item['total'] or Decimal('0.00') for item in pagos_por_dia}

    serie_dias = []
    actual = fecha_inicio
    while actual <= fecha_fin:
        serie_dias.append({
            'fecha': actual,
            'total': total_por_dia.get(actual, Decimal('0.00')),
        })
        actual += timedelta(days=1)

    detalle_sucursales = list(
        pagos.values('sucursal_id', 'sucursal__nombre').annotate(total=Sum('monto')).order_by('-total')
    )
    detalle_empleados = list(
        pagos.values('empleado_id', 'empleado__nombre', 'empleado__apellidos').annotate(total=Sum('monto')).order_by('-total')
    )

    return render(request, 'cobranzas/reporte_caja.html', {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'pagos': pagos.order_by('-fecha_pago'),
        'total_cobrado': total_cobrado,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'serie_dias': serie_dias,
        'detalle_sucursales': detalle_sucursales,
        'detalle_empleados': detalle_empleados,
    })


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido', 'cobranzas.cerrar_caja'])
def exportar_reporte_caja_csv(request):
    """Exporta el resumen de caja a CSV para un rango determinado."""
    fecha_inicio_raw = request.GET.get('fecha_inicio') or (timezone.localdate() - timedelta(days=6)).isoformat()
    fecha_fin_raw = request.GET.get('fecha_fin') or timezone.localdate().isoformat()

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date()
    except ValueError:
        fecha_inicio = timezone.localdate() - timedelta(days=6)

    try:
        fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date()
    except ValueError:
        fecha_fin = timezone.localdate()

    pagos = Pago.objects.filter(fecha_pago__date__range=[fecha_inicio, fecha_fin]).select_related('sucursal', 'empleado', 'caja').order_by('fecha_pago')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reporte_caja_{fecha_inicio}_a_{fecha_fin}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Sucursal', 'Empleado', 'Caja', 'Metodo', 'Monto'])
    for pago in pagos:
        writer.writerow([
            pago.fecha_pago.strftime('%Y-%m-%d %H:%M:%S'),
            pago.sucursal.nombre if pago.sucursal else '-',
            str(pago.empleado) if pago.empleado else '-',
            pago.caja.nombre if pago.caja else '-',
            pago.metodo_pago,
            str(pago.monto),
        ])
    return response


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido', 'cobranzas.cerrar_caja'])
def reporte_comparativo(request):
    """Reporte comparativo de tendencia por sucursal y empleado contra el período anterior."""
    try:
        dias = int(request.GET.get('dias', '7'))
    except ValueError:
        dias = 7
    dias = max(1, min(dias, 90))

    fecha_fin = timezone.localdate()
    fecha_inicio = fecha_fin - timedelta(days=dias - 1)
    periodo_anterior_fin = fecha_inicio - timedelta(days=1)
    periodo_anterior_inicio = periodo_anterior_fin - timedelta(days=dias - 1)

    pagos_actual = Pago.objects.filter(fecha_pago__date__range=[fecha_inicio, fecha_fin]).select_related('sucursal', 'empleado')
    pagos_anterior = Pago.objects.filter(fecha_pago__date__range=[periodo_anterior_inicio, periodo_anterior_fin]).select_related('sucursal', 'empleado')

    total_actual = sum((p.monto for p in pagos_actual), Decimal('0.00'))
    total_anterior = sum((p.monto for p in pagos_anterior), Decimal('0.00'))
    diferencia_total = total_actual - total_anterior
    variacion_total = (diferencia_total / total_anterior * Decimal('100')) if total_anterior else Decimal('0.00')

    tendencia = []
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        total_dia = pagos_actual.filter(fecha_pago__date=fecha_actual).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        tendencia.append({
            'fecha': fecha_actual,
            'total': total_dia,
        })
        fecha_actual += timedelta(days=1)

    por_sucursal = []
    max_sucursal = Decimal('0.00')
    for item in pagos_actual.values('sucursal_id', 'sucursal__nombre').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('sucursal__nombre') or 'Sin sucursal'
        total = item.get('total') or Decimal('0.00')
        if total > max_sucursal:
            max_sucursal = total
        prev_total = pagos_anterior.filter(sucursal_id=item['sucursal_id']).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        diferencia = total - prev_total
        variacion = (diferencia / prev_total * Decimal('100')) if prev_total else Decimal('0.00')
        por_sucursal.append({
            'nombre': nombre,
            'total': total,
            'anterior': prev_total,
            'diferencia': diferencia,
            'variacion': variacion,
            'porcentaje': (total / max(total_actual, Decimal('0.01')) * Decimal('100')) if total_actual else Decimal('0.00'),
        })

    por_empleado = []
    max_empleado = Decimal('0.00')
    for item in pagos_actual.values('empleado_id', 'empleado__nombre', 'empleado__apellidos').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('empleado__nombre') or ''
        apellidos = item.get('empleado__apellidos') or ''
        empleado_nombre = f'{nombre} {apellidos}'.strip() or 'Sin empleado'
        total = item.get('total') or Decimal('0.00')
        if total > max_empleado:
            max_empleado = total
        prev_total = pagos_anterior.filter(empleado_id=item['empleado_id']).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        diferencia = total - prev_total
        variacion = (diferencia / prev_total * Decimal('100')) if prev_total else Decimal('0.00')
        por_empleado.append({
            'nombre': empleado_nombre,
            'total': total,
            'anterior': prev_total,
            'diferencia': diferencia,
            'variacion': variacion,
            'porcentaje': (total / max(total_actual, Decimal('0.01')) * Decimal('100')) if total_actual else Decimal('0.00'),
        })

    return render(request, 'cobranzas/reporte_comparativo.html', {
        'dias': dias,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'periodo_anterior_inicio': periodo_anterior_inicio,
        'periodo_anterior_fin': periodo_anterior_fin,
        'total_actual': total_actual,
        'total_anterior': total_anterior,
        'diferencia_total': diferencia_total,
        'variacion_total': variacion_total,
        'tendencia': tendencia,
        'por_sucursal': por_sucursal,
        'por_empleado': por_empleado,
        'max_sucursal': max_sucursal,
        'max_empleado': max_empleado,
    })


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido', 'cobranzas.cerrar_caja'])
def reporte_comparativo_pdf(request):
    """Genera un PDF del reporte comparativo para compartir o enviar por email."""
    dias = 7
    try:
        dias = int(request.GET.get('dias', '7'))
    except ValueError:
        dias = 7
    dias = max(1, min(dias, 90))

    fecha_fin = timezone.localdate()
    fecha_inicio = fecha_fin - timedelta(days=dias - 1)
    periodo_anterior_fin = fecha_inicio - timedelta(days=1)
    periodo_anterior_inicio = periodo_anterior_fin - timedelta(days=dias - 1)

    pagos_actual = Pago.objects.filter(fecha_pago__date__range=[fecha_inicio, fecha_fin]).select_related('sucursal', 'empleado')
    pagos_anterior = Pago.objects.filter(fecha_pago__date__range=[periodo_anterior_inicio, periodo_anterior_fin]).select_related('sucursal', 'empleado')

    total_actual = sum((p.monto for p in pagos_actual), Decimal('0.00'))
    total_anterior = sum((p.monto for p in pagos_anterior), Decimal('0.00'))
    diferencia_total = total_actual - total_anterior
    variacion_total = (diferencia_total / total_anterior * Decimal('100')) if total_anterior else Decimal('0.00')

    por_sucursal = []
    for item in pagos_actual.values('sucursal_id', 'sucursal__nombre').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('sucursal__nombre') or 'Sin sucursal'
        total = item.get('total') or Decimal('0.00')
        prev_total = pagos_anterior.filter(sucursal_id=item['sucursal_id']).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        por_sucursal.append({
            'nombre': nombre,
            'total': total,
            'prev_total': prev_total,
            'diferencia': total - prev_total,
        })

    por_empleado = []
    for item in pagos_actual.values('empleado_id', 'empleado__nombre', 'empleado__apellidos').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('empleado__nombre') or ''
        apellidos = item.get('empleado__apellidos') or ''
        empleado_nombre = f'{nombre} {apellidos}'.strip() or 'Sin empleado'
        total = item.get('total') or Decimal('0.00')
        prev_total = pagos_anterior.filter(empleado_id=item['empleado_id']).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        por_empleado.append({
            'nombre': empleado_nombre,
            'total': total,
            'prev_total': prev_total,
            'diferencia': total - prev_total,
        })

    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'periodo_anterior_inicio': periodo_anterior_inicio,
        'periodo_anterior_fin': periodo_anterior_fin,
        'total_actual': total_actual,
        'total_anterior': total_anterior,
        'diferencia_total': diferencia_total,
        'variacion_total': variacion_total,
        'por_sucursal': por_sucursal,
        'por_empleado': por_empleado,
    }

    html = render_to_string('cobranzas/reporte_comparativo_pdf.html', context)
    pdf_buffer = BytesIO()
    pdf_status = pisa.CreatePDF(BytesIO(html.encode('UTF-8')), pdf_buffer)
    if pdf_status.err:
        return HttpResponse('Error al generar el PDF del reporte comparativo.', status=500)

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_comparativo.pdf"'
    return response


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido', 'cobranzas.cerrar_caja'])
def reporte_comparativo_excel(request):
    """Exporta el reporte comparativo como archivo Excel/CSV compatible."""
    try:
        dias = int(request.GET.get('dias', '7'))
    except ValueError:
        dias = 7
    dias = max(1, min(dias, 90))

    fecha_fin = timezone.localdate()
    fecha_inicio = fecha_fin - timedelta(days=dias - 1)
    periodo_anterior_fin = fecha_inicio - timedelta(days=1)
    periodo_anterior_inicio = periodo_anterior_fin - timedelta(days=dias - 1)

    pagos_actual = Pago.objects.filter(fecha_pago__date__range=[fecha_inicio, fecha_fin]).select_related('sucursal', 'empleado')
    pagos_anterior = Pago.objects.filter(fecha_pago__date__range=[periodo_anterior_inicio, periodo_anterior_fin]).select_related('sucursal', 'empleado')

    total_actual = sum((p.monto for p in pagos_actual), Decimal('0.00'))
    total_anterior = sum((p.monto for p in pagos_anterior), Decimal('0.00'))
    diferencia_total = total_actual - total_anterior

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_comparativo.xlsx"'

    writer = csv.writer(response)
    writer.writerow(['Reporte comparativo de caja'])
    writer.writerow(['Periodo actual', f'{fecha_inicio} a {fecha_fin}'])
    writer.writerow(['Periodo anterior', f'{periodo_anterior_inicio} a {periodo_anterior_fin}'])
    writer.writerow([])
    writer.writerow(['Indicador', 'Valor'])
    writer.writerow(['Total cobrado', str(total_actual)])
    writer.writerow(['Total anterior', str(total_anterior)])
    writer.writerow(['Diferencia', str(diferencia_total)])
    writer.writerow([])
    writer.writerow(['Sucursal', 'Actual', 'Anterior', 'Diferencia'])
    for item in pagos_actual.values('sucursal_id', 'sucursal__nombre').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('sucursal__nombre') or 'Sin sucursal'
        total = item.get('total') or Decimal('0.00')
        prev_total = pagos_anterior.filter(sucursal_id=item['sucursal_id']).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        writer.writerow([nombre, str(total), str(prev_total), str(total - prev_total)])

    writer.writerow([])
    writer.writerow(['Empleado', 'Actual', 'Anterior', 'Diferencia'])
    for item in pagos_actual.values('empleado_id', 'empleado__nombre', 'empleado__apellidos').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('empleado__nombre') or ''
        apellidos = item.get('empleado__apellidos') or ''
        empleado_nombre = f'{nombre} {apellidos}'.strip() or 'Sin empleado'
        total = item.get('total') or Decimal('0.00')
        prev_total = pagos_anterior.filter(empleado_id=item['empleado_id']).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        writer.writerow([empleado_nombre, str(total), str(prev_total), str(total - prev_total)])

    return response


@revisar_permisos_roles(['cobranzas.panel_caja', 'cobranzas.cobrar_pedido', 'cobranzas.cerrar_caja'])
def resumen_dia(request):
    """Resumen financiero del día para cada caja y cierre de turno."""
    fecha_raw = request.GET.get('fecha') or timezone.localdate().isoformat()
    try:
        fecha = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
    except ValueError:
        fecha = timezone.localdate()

    pagos = Pago.objects.filter(fecha_pago__date=fecha).select_related('caja', 'sucursal', 'empleado')
    pagos_ayer = Pago.objects.filter(fecha_pago__date=fecha - timedelta(days=1)).select_related('sucursal', 'empleado')
    cierres = CierreCaja.objects.filter(fecha_hora__date=fecha).select_related('caja', 'empleado')

    total_cobrado = sum((p.monto for p in pagos), Decimal('0.00'))
    total_efectivo = sum(
        (p.monto for p in pagos if str(p.metodo_pago).lower() == 'efectivo'),
        Decimal('0.00'),
    )
    total_transferencia = sum(
        (p.monto for p in pagos if str(p.metodo_pago).lower() in {'transferencia', 'transferencia bancaria', 'banco'}),
        Decimal('0.00'),
    )
    total_esperado = sum((c.monto_esperado for c in cierres), Decimal('0.00'))
    total_real = sum((c.monto_real for c in cierres), Decimal('0.00'))
    diferencia_total = sum((c.diferencia for c in cierres), Decimal('0.00'))

    resumen_por_sucursal = []
    hoy_por_sucursal = {}
    ayer_por_sucursal = {}
    for item in pagos.values('sucursal_id', 'sucursal__nombre').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('sucursal__nombre') or 'Sin sucursal'
        hoy_por_sucursal[nombre] = item.get('total') or Decimal('0.00')
    for item in pagos_ayer.values('sucursal_id', 'sucursal__nombre').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('sucursal__nombre') or 'Sin sucursal'
        ayer_por_sucursal[nombre] = item.get('total') or Decimal('0.00')
    for nombre, total in sorted(hoy_por_sucursal.items(), key=lambda x: x[1], reverse=True):
        total_ayer = ayer_por_sucursal.get(nombre, Decimal('0.00'))
        participacion = (total / total_cobrado * Decimal('100')) if total_cobrado else Decimal('0.00')
        diferencia_anterior = total - total_ayer
        resumen_por_sucursal.append({
            'nombre': nombre,
            'total': total,
            'participacion': participacion,
            'diferencia_anterior': diferencia_anterior,
        })

    resumen_por_empleado = []
    hoy_por_empleado = {}
    ayer_por_empleado = {}
    for item in pagos.values('empleado_id', 'empleado__nombre', 'empleado__apellidos').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('empleado__nombre') or ''
        apellidos = item.get('empleado__apellidos') or ''
        empleado_nombre = f'{nombre} {apellidos}'.strip() or 'Sin empleado'
        hoy_por_empleado[empleado_nombre] = item.get('total') or Decimal('0.00')
    for item in pagos_ayer.values('empleado_id', 'empleado__nombre', 'empleado__apellidos').annotate(total=Sum('monto')).order_by('-total'):
        nombre = item.get('empleado__nombre') or ''
        apellidos = item.get('empleado__apellidos') or ''
        empleado_nombre = f'{nombre} {apellidos}'.strip() or 'Sin empleado'
        ayer_por_empleado[empleado_nombre] = item.get('total') or Decimal('0.00')
    for nombre, total in sorted(hoy_por_empleado.items(), key=lambda x: x[1], reverse=True):
        total_ayer = ayer_por_empleado.get(nombre, Decimal('0.00'))
        participacion = (total / total_cobrado * Decimal('100')) if total_cobrado else Decimal('0.00')
        diferencia_anterior = total - total_ayer
        resumen_por_empleado.append({
            'nombre': nombre,
            'total': total,
            'participacion': participacion,
            'diferencia_anterior': diferencia_anterior,
        })

    return render(request, 'cobranzas/resumen_dia.html', {
        'fecha': fecha,
        'fecha_anterior': fecha - timedelta(days=1),
        'pagos': pagos.order_by('-fecha_pago'),
        'cierres': cierres.order_by('-fecha_hora'),
        'total_cobrado': total_cobrado,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_esperado': total_esperado,
        'total_real': total_real,
        'diferencia_total': diferencia_total,
        'resumen_por_sucursal': resumen_por_sucursal,
        'resumen_por_empleado': resumen_por_empleado,
    })


@revisar_permisos_roles(['cobranzas.abrir_caja', 'cobranzas.cobrar_pedido'])
def abrir_caja(request, caja_id=None):
    """Abre una caja y registra el monto inicial."""
    caja = get_object_or_404(Caja, pk=caja_id) if caja_id else None
    form = AperturaCajaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        empleado = getattr(getattr(request.user, 'perfil', None), 'empleado', None) or getattr(request.user, 'empleado', None)
        if not empleado:
            messages.error(request, 'No se pudo determinar el empleado asociado a este usuario.')
            return redirect('panel_caja')

        if caja is None:
            caja = Caja.objects.create(
                sucursal=form.cleaned_data.get('sucursal') or Sucursal.objects.first(),
                nombre=form.cleaned_data.get('nombre') or f"Caja {Caja.objects.count() + 1}",
                estado='cerrada',
            )

        caja.abrir(
            empleado=empleado,
            monto_inicial=form.cleaned_data['monto_inicial'],
            observaciones=form.cleaned_data.get('observaciones', '')
        )
        AperturaCaja.objects.create(
            caja=caja,
            empleado=empleado,
            monto_inicial=form.cleaned_data['monto_inicial'],
            observaciones=form.cleaned_data.get('observaciones', '')
        )
        messages.success(request, f'Caja abierta correctamente: {caja.nombre}')
        return redirect('panel_caja')

    return render(request, 'cobranzas/abrir_caja.html', {
        'caja': caja,
        'form': form,
        'sucursales': Sucursal.objects.filter(activa=True),
    })


@revisar_permisos_roles(['cobranzas.cerrar_caja', 'cobranzas.cobrar_pedido'])
def cerrar_caja(request, caja_id):
    """Cierra una caja y registra el arqueo del día."""
    caja = get_object_or_404(Caja, pk=caja_id)
    form = CierreCajaForm(request.POST or None, initial={'monto_real': caja.saldo_actual})

    if request.method == 'POST' and form.is_valid():
        empleado = getattr(getattr(request.user, 'perfil', None), 'empleado', None) or getattr(request.user, 'empleado', None)
        if not empleado:
            messages.error(request, 'No se pudo determinar el empleado asociado a este usuario.')
            return redirect('panel_caja')

        monto_esperado = Decimal(str(caja.saldo_actual))
        monto_real = form.cleaned_data['monto_real']
        diferencia = Decimal(str(monto_real)) - monto_esperado

        caja.cerrar(
            empleado=empleado,
            monto_real=monto_real,
            observaciones=form.cleaned_data.get('observaciones', '')
        )
        CierreCaja.objects.create(
            caja=caja,
            empleado=empleado,
            monto_esperado=monto_esperado,
            monto_real=monto_real,
            diferencia=diferencia,
            observaciones=form.cleaned_data.get('observaciones', '')
        )
        messages.success(request, f'Caja cerrada correctamente: {caja.nombre}')
        return redirect('panel_caja')

    return render(request, 'cobranzas/cerrar_caja.html', {'caja': caja, 'form': form})


@revisar_permiso('cobranzas.lista_pedidos_cobranzas')
def lista_pedidos_cobranzas(request):
    """Lista de pedidos aprobados que requieren confirmación de pago o facturación."""
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    qs = Pedido.objects.all()
    if estado:
        qs = qs.filter(estado=estado)
    else:
        qs = qs.filter(estado__in=[
            'aprobado', 'cobranzas', 'pendiente_cobro', 'facturado_contado', 'transferencia_en_tramite', 'pagado'
        ])
    if tipo:
        # tipo puede ser 'repuesto' o 'vehiculo' (venta_tipo)
        qs = qs.filter(venta_tipo=tipo)
    pedidos = qs.order_by('-fecha_pedido')
    return render(request, 'cobranzas/lista_pedidos_cobranzas.html', {'pedidos': pedidos})


@revisar_permiso('cobranzas.lista_pedidos_busqueda')
def lista_pedidos_busqueda(request):
    """Lista de pedidos de tipo búsqueda para seguimiento del proceso."""
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
    return render(request, 'cobranzas/lista_pedidos_busqueda.html', {
        'pedidos': pedidos,
        'q': q,
        'estado': estado,
    })


@revisar_permiso('cobranzas.lista_pedidos_transferencia')
def lista_pedidos_transferencia(request):
    """Lista de pedidos de vehículos pagados listos para transferir la propiedad."""
    estado = request.GET.get('estado') or 'pagado'
    q = request.GET.get('q', '').strip()

    qs = Pedido.objects.filter(tipo='venta', venta_tipo='vehiculo').select_related('cliente').order_by('-fecha_pedido')

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
    return render(request, 'cobranzas/lista_pedidos_transferencia.html', {
        'pedidos': pedidos,
        'q': q,
        'estado': estado,
    })


@revisar_permiso('cobranzas.lista_pedidos_despacho')
def lista_pedidos_despacho(request):
    """Lista de pedidos pagados de venta para confirmar la entrega del repuesto."""
    pedidos = Pedido.objects.filter(tipo='venta', estado='pagado').order_by('-fecha_pedido')
    return render(request, 'cobranzas/lista_pedidos_despacho.html', {'pedidos': pedidos})


@revisar_permiso('cobranzas.cancelar_pedido_cobranzas')
def cancelar_pedido_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        try:
            pedido.cancelar()
        except Exception as e:
            # Simplemente redirigimos; la plantilla debería mostrar mensajes
            pass
    return redirect('lista_pedidos_cobranzas')


def _generar_factura_pdf_para_pedido(pedido):
    from .utils import render_to_pdf_xhtml2pdf
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    empresa = Empresa.objects.first()
    logo_path = None
    if empresa and empresa.logo and empresa.logo.path:
        logo_path = Path(empresa.logo.path).as_uri()
    else:
        default_logo = Path(settings.BASE_DIR) / 'static' / 'img' / 'skpy_logo.png'
        if default_logo.exists():
            logo_path = default_logo.as_uri()

    context = {
        'pedido': pedido,
        'cliente': pedido.cliente,
        'items': pedido.obtener_items(),
        'empresa': empresa,
        'logo_path': logo_path,
        'fecha_emision': pedido.fecha_pedido,
        'subtotal_neto': pedido.monto_total - pedido.iva,
    }
    pdf_bytes = render_to_pdf_xhtml2pdf('cobranzas/factura_contado.html', context)
    if not pdf_bytes:
        return None
    filename = f'facturas/pedido_{pedido.id}.pdf'
    saved_path = default_storage.save(filename, ContentFile(pdf_bytes))
    pedido.factura_pdf.name = saved_path
    pedido.save(update_fields=['factura_pdf'])
    return saved_path


@revisar_permiso('cobranzas.facturar_contado_cobranzas')
def facturar_contado_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        try:
            pedido.facturar_pedido_venta_contado()
            _generar_factura_pdf_para_pedido(pedido)
        except Exception:
            pass
    return redirect('detalle_pedido', pedido_id=pedido.id)


@revisar_permiso('cobranzas.descargar_factura_cobranzas')
def descargar_factura_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if not pedido.factura_pdf:
        if pedido.estado != 'facturado_contado':
            raise Http404('Factura no disponible para este pedido')
        if not _generar_factura_pdf_para_pedido(pedido):
            raise Http404('No se pudo generar la factura')

    try:
        file_path = pedido.factura_pdf.path
    except ValueError:
        raise Http404('Ruta de factura inválida')

    try:
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf', filename=f'factura_pedido_{pedido.id}.pdf')
    except FileNotFoundError:
        raise Http404('Factura no encontrada')


@revisar_permiso('cobranzas.previsualizar_factura_cobranzas')
def previsualizar_factura_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if not pedido.factura_pdf and pedido.estado != 'facturado_contado':
        raise Http404('Factura no disponible para este pedido')

    empresa = Empresa.objects.first()
    logo_path = None
    if empresa and empresa.logo:
        try:
            logo_path = empresa.logo.url
        except Exception:
            logo_path = None
    if not logo_path:
        logo_path = static('img/skpy_logo.png')

    context = {
        'pedido': pedido,
        'cliente': pedido.cliente,
        'items': pedido.obtener_items(),
        'empresa': empresa,
        'logo_path': logo_path,
        'fecha_emision': pedido.fecha_pedido,
        'subtotal_neto': pedido.monto_total - pedido.iva,
    }
    return render(request, 'cobranzas/factura_preview.html', context)


@revisar_permiso('cobranzas.entregar_repuesto_cobranzas')
def entregar_repuesto_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        try:
            pedido.confirmar_entrega_repuesto()
        except Exception:
            pass
        if request.POST.get('next') == 'despacho':
            return redirect('lista_pedidos_despacho')
    return redirect('lista_pedidos_cobranzas')


@revisar_permiso('cobranzas.iniciar_transferencia_cobranzas')
def iniciar_transferencia_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        try:
            pedido.iniciar_transferencia()
        except Exception:
            pass
    if pedido.venta_tipo == 'vehiculo':
        return redirect('lista_pedidos_transferencia')
    return redirect('lista_pedidos_cobranzas')


@revisar_permiso('cobranzas.confirmar_transferencia_cobranzas')
def confirmar_transferencia_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        # Esperamos que el archivo se haya subido en un formulario separado
        try:
            pedido.confirmar_transferencia()
        except Exception:
            pass
    if pedido.venta_tipo == 'vehiculo':
        return redirect('lista_pedidos_transferencia')
    return redirect('lista_pedidos_cobranzas')


@revisar_permiso('cobranzas.confirmar_pago_cobranzas')
def confirmar_pago_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST' and pedido.estado == 'facturado_contado':
        pedido.confirmar_pago()
        Pago.objects.create(
            tipo_pago='pedido',
            pedido=pedido,
            monto=pedido.monto_total,
            metodo_pago=request.POST.get('metodo_pago', 'Efectivo'),
            observaciones='Pago confirmado desde la vista de cobranza',
        )
    if pedido.venta_tipo == 'vehiculo':
        return redirect('detalle_pedido', pedido_id=pedido.id)
    return redirect('lista_pedidos_cobranzas')


@revisar_permisos_roles(['cobranzas.cobrar_pedido', 'cobranzas.panel_caja'])
def cobrar_pedido(request, pedido_id):
    """Registra el cobro a cliente vinculando el pago a la caja abierta del empleado autenticado."""
    from decimal import Decimal, ROUND_HALF_UP

    pedido = get_object_or_404(Pedido, pk=pedido_id)
    error = None
    denominaciones = getattr(settings, 'DENOMINACIONES_MONEDA', ['100', '50', '20', '10', '5', '1', '0.5', '0.1'])
    metodo_pago_default = request.GET.get('metodo_pago') or request.POST.get('metodo_pago') or 'Efectivo'
    perfil = getattr(request.user, 'perfil', None)
    empleado = getattr(perfil, 'empleado', None) or getattr(request.user, 'empleado', None)

    cajas_abiertas = Caja.objects.filter(estado='abierta').select_related('sucursal').order_by('sucursal__nombre', 'nombre')
    sucursal_id = request.POST.get('sucursal') or request.GET.get('sucursal') or (cajas_abiertas.first().sucursal_id if cajas_abiertas.exists() else None)
    sucursal = Sucursal.objects.filter(pk=sucursal_id).first() if sucursal_id else None
    cajas_disponibles = cajas_abiertas.filter(sucursal=sucursal) if sucursal else cajas_abiertas
    caja_seleccionada = None
    caja_id = request.POST.get('caja') or request.GET.get('caja') or (cajas_disponibles.first().id if cajas_disponibles.exists() else None)
    if caja_id:
        caja_seleccionada = cajas_abiertas.filter(pk=caja_id).first()

    if not empleado:
        error = 'No hay un empleado asociado a este usuario para registrar el cobro.'

    if request.method == 'POST':
        monto_recibido_raw = request.POST.get('monto_recibido')
        metodo_pago = request.POST.get('metodo_pago', 'Efectivo')
        caja_id = request.POST.get('caja')
        sucursal_id = request.POST.get('sucursal')
        sucursal = Sucursal.objects.filter(pk=sucursal_id).first() if sucursal_id else None
        caja_seleccionada = Caja.objects.filter(pk=caja_id, estado='abierta').select_related('sucursal').first() if caja_id else None

        if not caja_seleccionada:
            error = 'Debe seleccionar una caja abierta para registrar el cobro.'
        elif not empleado:
            error = 'No existe empleado asociado al usuario.'
        else:
            try:
                monto_recibido = Decimal(monto_recibido_raw or '0').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                total = Decimal(pedido.monto_total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                if monto_recibido < total:
                    error = 'El monto recibido es insuficiente.'
                else:
                    vuelto = (monto_recibido - total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    pedido.confirmar_pago()
                    Pago.objects.create(
                        tipo_pago='pedido',
                        pedido=pedido,
                        sucursal=caja_seleccionada.sucursal,
                        caja=caja_seleccionada,
                        empleado=empleado,
                        monto=total,
                        monto_recibido=monto_recibido,
                        vuelto=vuelto,
                        metodo_pago=metodo_pago,
                        estado='confirmado',
                        observaciones=f'Recibido: {monto_recibido} | Vuelto: {vuelto} | Caja: {caja_seleccionada.nombre}',
                    )
                    messages.success(request, f'Cobro registrado en {caja_seleccionada.nombre} - {caja_seleccionada.sucursal}.')
                    return redirect('lista_pedidos_cobranzas')
            except Exception:
                error = 'Valor de monto inválido.'

    context = {
        'pedido': pedido,
        'cliente': pedido.cliente,
        'error': error,
        'denominaciones': denominaciones,
        'metodo_pago': metodo_pago_default,
        'empleado': empleado,
        'sucursales': Sucursal.objects.filter(activa=True).order_by('nombre'),
        'cajas': cajas_disponibles if sucursal else cajas_abiertas,
        'sucursal_seleccionada': sucursal,
        'caja_seleccionada': caja_seleccionada,
    }
    return render(request, 'cobranzas/cobrar_pedido.html', context)


@revisar_permiso('cobranzas.facturar_pedido_cobranzas')
def facturar_pedido_cobranzas(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        if pedido.estado != 'pagado':
            pedido.confirmar_pago()
        pedido.marcar_facturado()
    return redirect('lista_pedidos_cobranzas')

permisos_iniciales = [
    {
        'codename': 'cobranzas.lista_pedidos_cobranzas',
        'nombre': 'Listar Pedidos en Cobranzas',
        'descripcion': 'Permite ver la lista de todos los pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.lista_pedidos_busqueda',
        'nombre': 'Buscar Pedidos en Cobranzas',
        'descripcion': 'Permite buscar pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.lista_pedidos_transferencia',
        'nombre': 'Listar Pedidos en Transferencia',
        'descripcion': 'Permite ver la lista de todos los pedidos en transferencia.'
    },
    {
        'codename': 'cobranzas.lista_pedidos_despacho',
        'nombre': 'Listar Pedidos en Despacho',
        'descripcion': 'Permite ver la lista de todos los pedidos en despacho.'
    },
    {
        'codename': 'cobranzas.cancelar_pedido_cobranzas',
        'nombre': 'Cancelar Pedido en Cobranzas',
        'descripcion': 'Permite cancelar pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.facturar_contado_cobranzas',
        'nombre': 'Facturar Contado en Cobranzas',
        'descripcion': 'Permite facturar pedidos al contado en cobranzas.'
    },
    {
        'codename': 'cobranzas.descargar_factura_cobranzas',
        'nombre': 'Descargar Factura en Cobranzas',
        'descripcion': 'Permite descargar la factura de pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.cobrar_pedido',
        'nombre': 'Cobrar Pedido',
        'descripcion': 'Permite registrar el cobro de un pedido en cobranzas.'
    },
    {
        'codename': 'cobranzas.agregar_venta',
        'nombre': 'Agregar Venta',
        'descripcion': 'Permite registrar nuevas ventas en cobranzas.'
    },
    {
        'codename': 'cobranzas.previsualizar_factura_cobranzas',
        'nombre': 'Previsualizar Factura en Cobranzas',
        'descripcion': 'Permite previsualizar la factura de pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.entregar_repuesto_cobranzas',
        'nombre': 'Entregar Repuesto en Cobranzas',
        'descripcion': 'Permite registrar la entrega de repuestos en cobranzas.'
    },
    {
        'codename': 'cobranzas.iniciar_transferencia_cobranzas',
        'nombre': 'Iniciar Transferencia en Cobranzas',
        'descripcion': 'Permite iniciar el proceso de transferencia de pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.confirmar_transferencia_cobranzas',
        'nombre': 'Confirmar Transferencia en Cobranzas',
        'descripcion': 'Permite confirmar el proceso de transferencia de pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.confirmar_pago_cobranzas',
        'nombre': 'Confirmar Pago en Cobranzas',
        'descripcion': 'Permite confirmar el pago de pedidos en cobranzas.'
    },
    {
        'codename': 'cobranzas.facturar_pedido_cobranzas',
        'nombre': 'Facturar Pedido en Cobranzas',
        'descripcion': 'Permite facturar pedidos en cobranzas.'
    }

]
