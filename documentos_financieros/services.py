from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from configuraciones_maestras.models import Moneda

try:
    from contabilidad.models import Asiento, CuentaContable, MovimientoContable
except Exception:  # pragma: no cover - contabilidad deshabilitada en esta etapa
    Asiento = None
    CuentaContable = None
    MovimientoContable = None


DEFAULT_CUENTAS = {
    'clientes': ('1.1.01', 'Clientes', 'A'),
    'proveedores': ('2.1.01', 'Proveedores', 'P'),
    'ventas': ('4.1.01', 'Ventas', 'I'),
    'compras': ('5.1.01', 'Compras', 'E'),
    'gastos_operativos': ('5.2.01', 'Gastos Operativos', 'E'),
    'caja': ('1.1.02', 'Caja', 'A'),
    'bancos': ('1.1.03', 'Bancos', 'A'),
    'iva_por_pagar': ('2.1.02', 'IVA por pagar', 'P'),
    'costos_importacion': ('5.1.02', 'Costos de Importación', 'E'),
    'inventario': ('1.2.01', 'Inventario', 'A'),
}


def _obtener_o_crear_cuenta(codigo, nombre, tipo):
    cuenta = CuentaContable.objects.filter(codigo=codigo).first()
    if cuenta:
        return cuenta

    moneda = Moneda.objects.first()
    if not moneda:
        moneda = Moneda.objects.create(codigo='PYG', nombre='Guaraní')

    return CuentaContable.objects.create(
        codigo=codigo,
        nombre=nombre,
        tipo=tipo,
        moneda=moneda,
    )


def _obtener_cuenta(clave):
    codigo, nombre, tipo = DEFAULT_CUENTAS[clave]
    return _obtener_o_crear_cuenta(codigo, nombre, tipo)


def _calcular_totales(documento):
    subtotal = Decimal('0.00')
    iva = Decimal('0.00')

    if hasattr(documento, 'items_documento') and documento.items_documento.exists():
        for item in documento.items_documento.all():
            subtotal += Decimal(str(getattr(item, 'subtotal', 0) or 0))
            iva += Decimal(str(getattr(item, 'iva', 0) or 0))

    monto_total = Decimal(str(getattr(documento, 'monto_total', 0) or 0))
    if monto_total == 0 and subtotal > 0:
        monto_total = subtotal + iva - Decimal(str(getattr(documento, 'total_descuento', 0) or 0))

    if subtotal == 0 and iva == 0 and monto_total > 0:
        subtotal = monto_total

    return subtotal, iva, monto_total


def _descripcion_documento(documento):
    tipo = getattr(documento, 'tipo_documento', None)
    if tipo == 'autofactura':
        return f"Compra autofactura {getattr(documento, 'numero_documento', documento.pk)}"
    if tipo == 'factura_venta':
        return f"Venta {getattr(documento, 'numero_documento', documento.pk)}"
    if tipo == 'recibo_dinero':
        return f"Recibo de dinero {getattr(documento, 'numero_documento', documento.pk)}"
    if tipo == 'comprobante_egreso':
        return f"Comprobante de egreso {getattr(documento, 'numero_documento', documento.pk)}"
    if tipo:
        nombre = getattr(documento, 'get_tipo_documento_display', lambda: lambda: tipo)()
        return f"Asiento contable - {nombre} {getattr(documento, 'numero_completo', documento.pk)}"
    return f"Asiento contable documento {documento.pk}"


def _obtener_partidas(documento, subtotal, iva, monto_total):
    tipo = getattr(documento, 'tipo_documento', None)
    partidas = []

    if tipo == 'factura_venta':
        partidas = [
            (_obtener_cuenta('clientes'), subtotal + iva, Decimal('0.00')),
            (_obtener_cuenta('ventas'), Decimal('0.00'), subtotal),
        ]
        if iva:
            partidas.append((_obtener_cuenta('iva_por_pagar'), Decimal('0.00'), iva))

    elif tipo in {'autofactura', 'factura_comercial'}:
        partidas = [
            (_obtener_cuenta('compras'), subtotal, Decimal('0.00')),
        ]
        if iva:
            partidas.append((_obtener_cuenta('iva_por_pagar'), iva, Decimal('0.00')))
        partidas.append((_obtener_cuenta('proveedores'), Decimal('0.00'), subtotal + iva))

    elif tipo == 'factura_gastos_locales':
        cuenta_debe = _obtener_cuenta('inventario') if getattr(documento, 'capitalizable', False) else _obtener_cuenta('costos_importacion')
        partidas = [
            (cuenta_debe, subtotal + iva, Decimal('0.00')),
            (_obtener_cuenta('proveedores'), Decimal('0.00'), subtotal + iva),
        ]

    elif tipo == 'despacho_importacion':
        partidas = [
            (_obtener_cuenta('costos_importacion'), subtotal + iva, Decimal('0.00')),
            (_obtener_cuenta('proveedores'), Decimal('0.00'), subtotal + iva),
        ]

    elif tipo == 'recibo_dinero':
        partidas = [
            (_obtener_cuenta('caja'), monto_total, Decimal('0.00')),
            (_obtener_cuenta('clientes'), Decimal('0.00'), monto_total),
        ]

    elif tipo == 'comprobante_egreso':
        partidas = [
            (_obtener_cuenta('gastos_operativos'), monto_total, Decimal('0.00')),
            (_obtener_cuenta('bancos'), Decimal('0.00'), monto_total),
        ]

    elif tipo == 'nota_credito':
        partidas = [
            (_obtener_cuenta('ventas'), monto_total, Decimal('0.00')),
            (_obtener_cuenta('clientes'), Decimal('0.00'), monto_total),
        ]

    elif tipo == 'nota_debito':
        partidas = [
            (_obtener_cuenta('clientes'), monto_total, Decimal('0.00')),
            (_obtener_cuenta('ventas'), Decimal('0.00'), monto_total),
        ]

    else:
        partidas = [
            (_obtener_cuenta('compras'), subtotal, Decimal('0.00')),
            (_obtener_cuenta('iva_por_pagar'), iva, Decimal('0.00')),
            (_obtener_cuenta('proveedores'), Decimal('0.00'), subtotal + iva),
        ]

    return partidas


def _crear_asiento(documento, descripcion, partidas, content_type):
    asiento = Asiento.objects.create(
        fecha=timezone.now(),
        descripcion=descripcion,
        documento_tipo=content_type,
        documento_id=documento.pk,
    )

    for cuenta, debe, haber in partidas:
        if debe == 0 and haber == 0:
            continue
        MovimientoContable.objects.create(
            asiento=asiento,
            cuenta=cuenta,
            debe=debe,
            haber=haber,
        )

    return asiento


@transaction.atomic
def crear_asiento_contable_desde_documento(documento, *, descripcion=None, force=False):
    """Crea el asiento contable para un documento financiero aprobado."""
    if not hasattr(documento, 'monto_total'):
        return None

    content_type = ContentType.objects.get_for_model(documento)
    existing_asiento = Asiento.objects.filter(
        documento_tipo=content_type,
        documento_id=documento.pk,
    ).first()
    if existing_asiento and not force:
        return existing_asiento

    subtotal, iva, monto_total = _calcular_totales(documento)
    if not force and monto_total == 0:
        return None

    descripcion = descripcion or _descripcion_documento(documento)
    partidas = _obtener_partidas(documento, subtotal, iva, monto_total)
    if not partidas:
        return None

    asiento = _crear_asiento(documento, descripcion, partidas, content_type)
    return asiento
