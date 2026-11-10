from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from ventas.models import Venta


@transaction.atomic
def registrar_cobro_venta(
    venta: Venta,
    *,
    caja,
    empleado=None,
    sucursal=None,
    monto,
    metodo_pago="EFECTIVO",
    observaciones="",
):
    """Valida la caja y registra el cobro de la venta en la sucursal y empleado correctos."""
    venta = Venta.objects.select_for_update().get(pk=venta.pk)
    if Decimal(str(monto)) <= 0:
        raise ValidationError("El monto del cobro debe ser mayor que cero.")

    return venta.registrar_pago(
        monto,
        caja=caja,
        empleado=empleado,
        sucursal=sucursal,
        metodo_pago=metodo_pago,
        observaciones=observaciones,
    )
