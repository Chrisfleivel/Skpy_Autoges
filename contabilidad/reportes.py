# contabilidad/reportes.py
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import CuentaContable, SaldoMensualCuenta


def obtener_balance_general(fecha_corte):
    grupos = {
        'A': {'titulo': 'Activos', 'items': [], 'total': 0},
        'P': {'titulo': 'Pasivos', 'items': [], 'total': 0},
        'PN': {'titulo': 'Patrimonio', 'items': [], 'total': 0},
    }

    cuentas = CuentaContable.objects.filter(tipo__in=['A', 'P', 'PN']).order_by('codigo')

    for cuenta in cuentas:
        saldo = cuenta.get_saldo(fecha_corte)
        grupos[cuenta.tipo]['items'].append({
            'codigo': cuenta.codigo,
            'nombre': cuenta.nombre,
            'saldo': saldo,
        })
        grupos[cuenta.tipo]['total'] += saldo or 0

    return {
        'grupos': grupos,
        'total_activos': grupos['A']['total'],
        'total_pasivos': grupos['P']['total'],
        'total_patrimonio': grupos['PN']['total'],
    }


def obtener_saldo_optimizador(cuenta, fecha):
    # Buscamos el cierre mensual más reciente anterior a la fecha solicitada
    cierre = SaldoMensualCuenta.objects.filter(
        cuenta=cuenta, 
        anio__lte=fecha.year, 
        mes__lte=fecha.month
    ).order_by('-anio', '-mes').first()
    
    if cierre:
        # Saldo inicial = Saldo del mes cerrado
        # Saldo final = Saldo inicial + Movimientos desde el inicio del mes actual hasta la fecha
        # ... lógica de suma de movimientos cortos ...
        return cierre.saldo_final
    else:
        return cuenta.get_saldo(fecha) # Fallback si no hay cierres

def obtener_libro_mayor(cuenta_id=None, fecha_desde=None, fecha_hasta=None):
    cuentas = CuentaContable.objects.filter(es_imputable=True).order_by('codigo')
    cuenta = None
    if cuenta_id:
        cuenta = cuentas.filter(id=cuenta_id).first()
    elif cuentas.exists():
        cuenta = cuentas.first()

    movimientos = []
    saldo_inicial = 0
    saldo_actual = 0

    if cuenta:
        if fecha_desde:
            saldo_inicial = cuenta.get_saldo(fecha_desde - timedelta(days=1)) or 0
        else:
            saldo_inicial = 0

        queryset = cuenta.movimientocontable_set.select_related('asiento').order_by('asiento__fecha', 'id')
        if fecha_desde:
            queryset = queryset.filter(asiento__fecha__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(asiento__fecha__date__lte=fecha_hasta)

        saldo_actual = saldo_inicial
        for movimiento in queryset:
            if cuenta.tipo in ['A', 'E']:
                delta = (movimiento.debe or 0) - (movimiento.haber or 0)
            else:
                delta = (movimiento.haber or 0) - (movimiento.debe or 0)

            saldo_actual += delta
            movimientos.append({
                'fecha': movimiento.asiento.fecha.date(),
                'descripcion': movimiento.asiento.descripcion,
                'debe': movimiento.debe,
                'haber': movimiento.haber,
                'saldo': saldo_actual,
            })

    return {
        'cuentas': cuentas,
        'cuenta': cuenta,
        'movimientos': movimientos,
        'saldo_inicial': saldo_inicial,
        'saldo_final': saldo_actual,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }


def obtener_estado_resultados(fecha_hasta=None):
    if fecha_hasta is None:
        fecha_hasta = timezone.now().date()

    cuentas = CuentaContable.objects.filter(tipo__in=['I', 'E']).order_by('codigo')

    reporte = {
        'ingresos': [],
        'egresos': [],
        'total_ingresos': 0,
        'total_egresos': 0,
        'utilidad_neta': 0,
        'fecha': fecha_hasta,
    }

    for cuenta in cuentas:
        saldo = cuenta.get_saldo(fecha_hasta) or 0
        item = {
            'codigo': cuenta.codigo,
            'nombre': cuenta.nombre,
            'saldo': saldo,
        }

        if cuenta.tipo == 'I':
            reporte['ingresos'].append(item)
            reporte['total_ingresos'] += saldo
        else:
            reporte['egresos'].append(item)
            reporte['total_egresos'] += saldo

    reporte['utilidad_neta'] = reporte['total_ingresos'] - reporte['total_egresos']
    return reporte



"""En tu plantilla estado_resultados.html, puedes presentar esta información de forma estructurada para que el contador vea el flujo de la empresa:

Bloque Ingresos: Ventas de vehículos, ventas de repuestos, servicios de taller.

(-) Bloque Costos de Venta: Costo de vehículos importados (el costo de mercadería vendida).

(=) Margen Bruto.

(-) Gastos Operativos: Salarios, alquileres, gastos de oficina.

(=) Utilidad Antes de Impuestos."""