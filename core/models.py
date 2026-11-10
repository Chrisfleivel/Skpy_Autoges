"""
core/models.py

Base compartida por todas las apps:
  - TimeStampedModel : fechas de creación / actualización
  - Moneda           : choices de monedas
  - HistorialEstado  : bitácora de cada cambio de estado (quién, cuándo, de→a)
  - EstadoMixin      : máquina de estados ligera (sin dependencias externas)

Cómo funciona EstadoMixin
-------------------------
Cada modelo define:
    TRANSICIONES = {ESTADO_ACTUAL: (ESTADOS_PERMITIDOS, ...)}

y opcionalmente, por cada estado destino, un método guarda:
    def validar_<estado_en_minusculas>(self): ...   # lanza TransicionInvalida

y un hook posterior:
    def despues_de_cambiar_estado(self, anterior, nuevo): ...

El estado SOLO se cambia con `obj.cambiar_estado(nuevo, usuario=..., nota=...)`.
El campo `estado` se declara con editable=False para que ni el admin ni los
formularios lo modifiquen directamente.
"""
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class TimeStampedModel(models.Model):
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Moneda:
    """Facade compartido para las monedas del sistema.

    La fuente real de verdad es el modelo persistido de configuraciones_maestras.
    Esto permite mantener los códigos por defecto y, al mismo tiempo, agregar
    nuevas monedas en runtime sin romper las referencias del resto de la app.
    """

    USD = "USD"
    PYG = "PYG"
    KRW = "KRW"
    EUR = "EUR"
    BRL = "BRL"

    DEFAULTS = (
        ("USD", "Dólar estadounidense"),
        ("PYG", "Guaraní"),
        ("KRW", "Won coreano"),
        ("EUR", "Euro"),
        ("BRL", "Real"),
    )

    @classmethod
    def ensure_defaults(cls):
        from configuraciones_maestras.models import Moneda as MonedaCatalogo

        return MonedaCatalogo.ensure_defaults()

    @classmethod
    def get_choices(cls):
        from configuraciones_maestras.models import Moneda as MonedaCatalogo

        return MonedaCatalogo.get_choices()

    @classmethod
    def agregar(cls, codigo, nombre):
        from configuraciones_maestras.models import Moneda as MonedaCatalogo

        codigo = str(codigo).strip().upper()
        nombre = str(nombre).strip()
        if not codigo or len(codigo) != 3:
            raise ValueError("El código de la moneda debe tener exactamente 3 caracteres.")
        moneda, created = MonedaCatalogo.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre})
        if not created and moneda.nombre != nombre:
            moneda.nombre = nombre
            moneda.save(update_fields=["nombre"])
        return moneda


class TasaCambio:
    """Facade compartido para las tasas de cambio del sistema.

    La fuente real de verdad sigue siendo el modelo persistido en
    configuraciones_maestras.models.TasaCambio, pero la API del proyecto queda
    centralizada aquí para evitar duplicaciones y permitir registrar cambios en
    runtime sin acoplar el resto de la app a un modelo concreto.
    """

    DEFAULTS = (
        ("USD", "PYG"),
    )

    @classmethod
    def get_model(cls):
        from configuraciones_maestras.models import TasaCambio as TasaCambioModel

        return TasaCambioModel

    @classmethod
    def registrar(cls, *, moneda_origen="USD", moneda_destino="PYG", valor=1, fecha=None, usuario=None):
        model = cls.get_model()
        fecha = fecha or timezone.now().date()
        valor = Decimal(str(valor))

        tasa, created = model.objects.get_or_create(
            moneda_origen=str(moneda_origen).upper(),
            moneda_destino=str(moneda_destino).upper(),
            fecha=fecha,
            defaults={"valor": valor, "usuario_creo": usuario},
        )

        if not created:
            tasa.valor = valor
            if usuario is not None:
                tasa.usuario_creo = usuario
            tasa.save(update_fields=["valor", "usuario_creo"])

        return tasa

    @classmethod
    def obtener_tasa_actual(cls, moneda_origen="USD", moneda_destino="PYG"):
        return cls.get_model().obtener_tasa_actual(moneda_origen, moneda_destino)

    @classmethod
    def existe_tasa_para_hoy(cls, moneda_origen="USD", moneda_destino="PYG"):
        return cls.get_model().existe_tasa_para_hoy(moneda_origen, moneda_destino)

    @classmethod
    def get_choices(cls):
        return Moneda.get_choices()


class TransicionInvalida(ValidationError):
    """Transición no permitida, o no se cumplen los requisitos del estado destino."""


class HistorialEstado(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    objeto = GenericForeignKey("content_type", "object_id")

    estado_anterior = models.CharField(max_length=30)
    estado_nuevo = models.CharField(max_length=30)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    nota = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        indexes = [models.Index(fields=["content_type", "object_id"])]
        verbose_name = "historial de estado"
        verbose_name_plural = "historial de estados"

    def __str__(self):
        return f"{self.estado_anterior} → {self.estado_nuevo} ({self.fecha:%Y-%m-%d %H:%M})"


class EstadoMixin:
    """Mixin (no es un modelo). El modelo debe tener un campo `estado`."""

    TRANSICIONES: dict = {}

    @property
    def historial(self):
        ct = ContentType.objects.get_for_model(self)
        return HistorialEstado.objects.filter(content_type=ct, object_id=self.pk)

    def transiciones_posibles(self):
        return self.TRANSICIONES.get(self.estado, ())

    def puede_pasar_a(self, nuevo) -> bool:
        return nuevo in self.transiciones_posibles()

    @transaction.atomic
    def cambiar_estado(self, nuevo, *, usuario=None, nota=""):
        if self.pk is None:
            raise ValidationError("El objeto debe guardarse antes de cambiar su estado.")

        # Bloquea la fila y relee el estado real para evitar carreras entre usuarios.
        if self.pk:
            self.estado = (
                type(self)
                .objects.select_for_update()
                .values_list("estado", flat=True)
                .get(pk=self.pk)
            )

        anterior = self.estado
        if nuevo not in self.TRANSICIONES.get(anterior, ()):
            raise TransicionInvalida(f"No se puede pasar de {anterior} a {nuevo}.")

        guarda = getattr(self, f"validar_{str(nuevo).lower()}", None)
        if guarda:
            guarda()

        self.estado = nuevo
        self.save()

        HistorialEstado.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            estado_anterior=anterior,
            estado_nuevo=str(nuevo),
            usuario=usuario,
            nota=nota,
        )

        despues = getattr(self, "despues_de_cambiar_estado", None)
        if despues:
            despues(anterior, nuevo)
        return self
