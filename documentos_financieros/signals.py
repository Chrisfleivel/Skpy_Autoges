# documentos_financieros/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Autofactura

try:
    from .services import crear_asiento_contable_desde_documento
except Exception:  # pragma: no cover - contabilidad deshabilitada en esta etapa
    crear_asiento_contable_desde_documento = None


def _documento_aprobado(documento):
    estado = str(getattr(documento, 'estado_sifen', '') or '').strip().lower()
    return estado in {'aprobado', 'procesado', 'autorizado', 'emitido'}


@receiver(post_save, sender=Autofactura)
def registrar_asiento_automatico_autofactura(sender, instance, **kwargs):
    if not _documento_aprobado(instance):
        return

    if crear_asiento_contable_desde_documento is None:
        return

    crear_asiento_contable_desde_documento(instance)
