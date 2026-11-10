"""Señales para invalidar el prorrateo cuando cambian gastos o ítems del embarque."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Embarque, EmbarqueItem, GastoImportacion


def _invalidar_prorrateo_si_corresponde(instance):
    embarque_id = getattr(instance, 'embarque_id', None)
    if embarque_id is None:
        return
    Embarque.objects.filter(pk=embarque_id).update(gastos_prorrateados=False)


@receiver([post_save, post_delete], sender=GastoImportacion)
@receiver([post_save, post_delete], sender=EmbarqueItem)
def invalidar_prorrateo(sender, instance, **kwargs):
    _invalidar_prorrateo_si_corresponde(instance)
