# cobranzas/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Pago


@receiver(post_save, sender=Pago)
def registrar_pago_caja(sender, instance, **kwargs):
    """Mantiene la caja y el flujo del pedido sincronizados sin depender de contabilidad."""
    if not instance.pedido:
        return

    if instance.estado == 'confirmado':
        if hasattr(instance.pedido, 'confirmar_pago') and getattr(instance.pedido, 'estado', None) != 'pagado':
            instance.pedido.confirmar_pago()

    if instance.caja_id and instance.monto and instance.estado == 'confirmado':
        caja = instance.caja
        if caja and getattr(caja, 'estado', None) == 'abierta':
            caja.saldo_actual = (caja.saldo_actual or 0) + instance.monto
            caja.save(update_fields=['saldo_actual'])
