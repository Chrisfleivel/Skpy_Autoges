from django.utils import timezone
from .models import TasaCambio

def obtener_tasa_para_fecha(fecha=None):
    """Devuelve la tasa (campo `valor`) válida para la fecha indicada.
    Si no se indica fecha, toma la fecha actual. Busca la tasa más reciente
    con `fecha__lte=fecha`.
    """
    if fecha is None:
        fecha = timezone.now().date()

    tasa = TasaCambio.objects.filter(fecha__lte=fecha).order_by('-fecha').first()

    if not tasa:
        raise ValueError("No hay tasa de cambio configurada en el sistema.")
    return tasa.valor