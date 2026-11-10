# contabilidad/views.py
from io import BytesIO

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_date
from seguridad_usuarios.decorators import revisar_permiso
from xhtml2pdf import pisa

from .reportes import obtener_balance_general, obtener_estado_resultados, obtener_libro_mayor
from .services import ejecutar_cierre_mensual
from .models import Asiento, SaldoMensualCuenta


@revisar_permiso('contabilidad.marcar_asientos_revisados')
def marcar_asiento_revisado(request, asiento_id):
    asiento = get_object_or_404(Asiento, id=asiento_id)

    if request.method == 'POST':
        asiento.revisado = True
        asiento.fecha_revision = timezone.now()
        asiento.revisado_por = request.user
        asiento.save()

    return redirect('auditoria_asientos_contables')


@revisar_permiso('contabilidad.ver_asientos_contables')
def listar_asientos_contables(request):
    fecha_desde_param = request.GET.get('fecha_desde')
    fecha_hasta_param = request.GET.get('fecha_hasta')
    documento_tipo_param = request.GET.get('documento_tipo')
    documento_id_param = request.GET.get('documento_id')

    asientos = Asiento.objects.select_related('revisado_por', 'documento_tipo').order_by('-fecha')

    fecha_desde = parse_date(fecha_desde_param) if fecha_desde_param else None
    fecha_hasta = parse_date(fecha_hasta_param) if fecha_hasta_param else None

    if fecha_desde:
        asientos = asientos.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        asientos = asientos.filter(fecha__date__lte=fecha_hasta)

    if documento_tipo_param and documento_tipo_param.isdigit():
        asientos = asientos.filter(documento_tipo_id=int(documento_tipo_param))
    if documento_id_param and documento_id_param.isdigit():
        asientos = asientos.filter(documento_id=int(documento_id_param))

    documento_tipos = ContentType.objects.filter(
        id__in=Asiento.objects.exclude(documento_tipo__isnull=True).values_list('documento_tipo', flat=True)
    ).order_by('app_label', 'model')

    return render(request, 'contabilidad/asientos_list.html', {
        'asientos': asientos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'documento_tipos': documento_tipos,
        'documento_tipo_seleccionado': documento_tipo_param,
        'documento_id': documento_id_param,
    })


@revisar_permiso('contabilidad.ver_movimientos_contables')
def detalle_asiento_contable(request, asiento_id):
    asiento = get_object_or_404(
        Asiento.objects.select_related('revisado_por').prefetch_related('movimientos__cuenta'),
        id=asiento_id,
    )
    return render(request, 'contabilidad/asiento_detail.html', {'asiento': asiento})


@revisar_permiso('contabilidad.ver_auditoria_asientos')
def auditoria_asientos_contables(request):
    asientos_auditados = Asiento.objects.filter(revisado=True).select_related('revisado_por').order_by('-fecha_revision', '-fecha')
    return render(request, 'contabilidad/auditoria_asientos.html', {'asientos': asientos_auditados})


@revisar_permiso('contabilidad.ver_reportes')
def vista_balance_general(request):
    fecha_param = request.GET.get('fecha')
    if fecha_param:
        fecha_corte = parse_date(fecha_param) or timezone.now().date()
    else:
        fecha_corte = timezone.now().date()

    datos = obtener_balance_general(fecha_corte)
    return render(request, 'contabilidad/balance.html', {'datos': datos, 'fecha': fecha_corte})


@revisar_permiso('contabilidad.ver_reportes')
def exportar_balance_pdf(request):
    fecha_param = request.GET.get('fecha')
    if fecha_param:
        fecha_corte = parse_date(fecha_param) or timezone.now().date()
    else:
        fecha_corte = timezone.now().date()

    datos = obtener_balance_general(fecha_corte)
    html = render_to_string('contabilidad/balance_pdf.html', {'datos': datos, 'fecha': fecha_corte})

    pdf_output = BytesIO()
    pdf_status = pisa.CreatePDF(html, dest=pdf_output)
    if pdf_status.err:
        return HttpResponse('Error al generar el PDF del balance general.', status=500)

    response = HttpResponse(pdf_output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="balance_general_{fecha_corte}.pdf"'
    return response


@revisar_permiso('contabilidad.ver_reportes')
def vista_estado_resultados(request):
    fecha_param = request.GET.get('fecha')
    if fecha_param:
        fecha_corte = parse_date(fecha_param) or timezone.now().date()
    else:
        fecha_corte = timezone.now().date()

    datos = obtener_estado_resultados(fecha_corte)
    return render(request, 'contabilidad/estado_resultados.html', {'datos': datos, 'fecha': fecha_corte})


@revisar_permiso('contabilidad.ver_reportes')
def cierre_mensual(request):
    mensaje = None
    error = None
    if request.method == 'POST':
        periodo = request.POST.get('periodo')
        if periodo:
            try:
                anio, mes = [int(x) for x in periodo.split('-')]
                ejecutar_cierre_mensual(anio, mes)
                mensaje = f'Cierre mensual formalizado para {anio}-{mes:02d}.'
            except Exception as exc:
                error = str(exc)
        else:
            error = 'Debe seleccionar un mes para cerrar.'

    ultimos_cierres = SaldoMensualCuenta.objects.order_by('-anio', '-mes')[:12]
    return render(request, 'contabilidad/cierre_mensual.html', {
        'mensaje': mensaje,
        'error': error,
        'ultimos_cierres': ultimos_cierres,
    })


@revisar_permiso('contabilidad.ver_reportes')
def vista_libro_mayor(request):
    fecha_desde_param = request.GET.get('fecha_desde')
    fecha_hasta_param = request.GET.get('fecha_hasta')
    cuenta_id_param = request.GET.get('cuenta')

    fecha_desde = parse_date(fecha_desde_param) if fecha_desde_param else None
    fecha_hasta = parse_date(fecha_hasta_param) if fecha_hasta_param else timezone.now().date()

    datos = obtener_libro_mayor(cuenta_id_param, fecha_desde, fecha_hasta)
    return render(request, 'contabilidad/libro_mayor.html', {
        'datos': datos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })


@revisar_permiso('contabilidad.ver_auditoria_asientos')
def dashboard_auditoria_ajustes(request):
    mes_actual = timezone.now().month
    anio_actual = timezone.now().year

    ajustes = Asiento.objects.filter(
        fecha__month=mes_actual,
        fecha__year=anio_actual,
        descripcion__icontains='AJUSTE'
    ).order_by('-fecha')

    return render(request, 'contabilidad/dashboard_ajustes.html', {
        'ajustes': ajustes,
        'mes': mes_actual,
        'anio': anio_actual,
    })