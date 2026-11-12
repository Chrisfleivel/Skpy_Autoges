from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from .models import FacturaComercial


def crear_factura_con_items(form, formset):
    """
    Crea la factura comercial junto con sus ítems en una sola transacción.

    La factura queda en estado BORRADOR: el total declarado se contrasta con la
    suma de los ítems recién al confirmar (validar_confirmada).
    """
    with transaction.atomic():
        factura = form.save()
        formset.instance = factura
        formset.save()
    return factura


def actualizar_factura_con_items(form, formset):
    """Actualiza la factura y sus ítems (solo válido en estado borrador)."""
    with transaction.atomic():
        factura = form.save()
        formset.instance = factura
        formset.save()
    return factura


def puede_editarse(factura: FacturaComercial) -> bool:
    """Solo las facturas en borrador admiten cambios."""
    return factura.estado == FacturaComercial.Estado.BORRADOR


def puede_eliminarse(factura: FacturaComercial) -> tuple[bool, str]:
    """
    Indica si la factura puede eliminarse y, si no, el motivo.

    No se permite borrar una factura que ya tiene pagos, embarques o documentos
    asociados, porque el movimiento ya tiene efecto en el inventario y en la caja.
    """
    if factura.estado != FacturaComercial.Estado.BORRADOR:
        return False, 'Solo se pueden eliminar facturas en estado borrador.'

    if factura.pagos.exists():
        return False, 'La factura tiene pagos al exterior registrados.'

    if any(item.embarque_items.exists() for item in factura.items.all()):
        return False, 'La factura tiene ítems asignados a un embarque.'

    if factura.documentos.exists():
        return False, 'La factura tiene documentos adjuntos.'

    return True, ''


def total_items_de_formulario(formset) -> Decimal:
    """Suma de los subtotales de las líneas habilitadas del formset."""
    total = Decimal('0')
    for form in formset.forms:
        if not form.cleaned_data or form.cleaned_data.get('DELETE'):
            continue
        cantidad = form.cleaned_data.get('cantidad') or 0
        precio = form.cleaned_data.get('precio_unitario') or Decimal('0')
        total += cantidad * precio
    return total


def validar_chasis_contra_inventario(factura: FacturaComercial) -> list[dict]:
    """
    Compara los chasis informados en la factura con los vehículos de inventario.

    Devuelve una lista de discrepancias informativas (no bloquean el guardado).
    """
    from inventario.models import Vehiculo

    discrepancias = []
    for item in factura.items.all():
        if not item.chasis:
            continue
        vehiculo = item.vehiculo
        if vehiculo is None:
            continue
        chasis_inventario = (vehiculo.codigo_chasis or '').strip().upper()
        chasis_factura = item.chasis.strip().upper()
        if chasis_inventario and chasis_inventario != chasis_factura:
            discrepancias.append({
                'item': item,
                'chasis_factura': chasis_factura,
                'chasis_inventario': chasis_inventario,
            })
    return discrepancias


def confirmar_factura(factura: FacturaComercial, usuario=None):
    """Confirma la factura usando su máquina de estados (valida el total)."""
    factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA, usuario=usuario)
    return factura
