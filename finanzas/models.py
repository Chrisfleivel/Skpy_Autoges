import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum

from core.models import EstadoMixin, Moneda, TimeStampedModel, TransicionInvalida

ESTADOS_EMBARQUE_CON_CARGA_EN_VIAJE = (
    "EMBARCADO",
    "EN_TRANSITO",
    "ARRIBADO",
    "EN_ADUANA",
    "NACIONALIZADO",
    "RECIBIDO",
    "CERRADO",
)


class PagoExterior(EstadoMixin, TimeStampedModel):
    class Estado(models.TextChoices):
        ORDENADO = "ORDENADO", "Orden de pago emitida"
        ACREDITADO = "ACREDITADO", "Acreditado al beneficiario"
        RECHAZADO = "RECHAZADO", "Rechazado / devuelto"

    class FormaPago(models.TextChoices):
        DEBITO_CUENTA = "DEBITO_CUENTA", "Débito en cuenta"
        EFECTIVO = "EFECTIVO", "Efectivo en ventanilla"
        CHEQUE = "CHEQUE", "Cheque"
        OTRA = "OTRA", "Otra"

    TRANSICIONES = {
        Estado.ORDENADO: (Estado.ACREDITADO, Estado.RECHAZADO),
        Estado.ACREDITADO: (),
        Estado.RECHAZADO: (),
    }

    factura = models.ForeignKey(
        "compras.FacturaComercial", on_delete=models.PROTECT, related_name="pagos"
    )
    fecha_operacion = models.DateField()
    moneda = models.CharField(max_length=3, choices=Moneda.get_choices, default=Moneda.USD)
    importe = models.DecimalField("Importe de la orden", max_digits=14, decimal_places=2)
    comision = models.DecimalField("Comisión bancaria", max_digits=14, decimal_places=2, default=Decimal("0"))
    cotizacion = models.DecimalField(
        "Cotización a moneda base",
        max_digits=14,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Solo si la moneda del pago no es la moneda base del sistema.",
    )

    forma_pago = models.CharField(max_length=15, choices=FormaPago.choices, default=FormaPago.DEBITO_CUENTA)
    ordenante = models.CharField(max_length=200, blank=True)
    cuenta_debito = models.CharField(max_length=40, blank=True)
    referencia_op = models.CharField("Referencia OP Nº", max_length=40, blank=True)
    nro_lote = models.CharField(max_length=40, blank=True)
    banco_corresponsal = models.CharField(max_length=120, blank=True)
    banco_beneficiario = models.CharField(max_length=150, blank=True)
    pais_beneficiario = models.CharField(max_length=80, blank=True)
    cuenta_beneficiario = models.CharField(max_length=60, blank=True)
    beneficiario = models.CharField(max_length=200, blank=True)
    motivo_transferencia = models.CharField(max_length=150, blank=True, help_text="Ej.: INVOICE 20260826")
    concepto = models.CharField(max_length=100, blank=True, help_text="Ej.: FONDOS PROPIOS")
    archivo = models.FileField("Liquidación escaneada", upload_to="finanzas/pagos/%Y/%m/", blank=True)

    fecha_acreditacion = models.DateField(null=True, blank=True)
    motivo_rechazo = models.CharField(max_length=255, blank=True)

    gasto_comision = models.OneToOneField(
        "importaciones.GastoImportacion",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="pago_origen",
    )

    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.ORDENADO,
        editable=False,
    )

    class Meta:
        ordering = ["-fecha_operacion", "-id"]
        verbose_name = "pago al exterior"
        verbose_name_plural = "pagos al exterior"
        constraints = [
            models.CheckConstraint(condition=Q(importe__gt=0), name="pago_importe_positivo"),
            models.CheckConstraint(condition=Q(comision__gte=0), name="pago_comision_no_negativa"),
            models.UniqueConstraint(
                fields=["referencia_op"],
                condition=~Q(referencia_op=""),
                name="uniq_pago_referencia_op",
            ),
        ]

    def __str__(self):
        return f"Pago {self.referencia_op or self.pk} · {self.importe} {self.moneda}"

    @property
    def total(self) -> Decimal:
        return self.importe + self.comision

    def clean(self):
        if self.factura_id and self.moneda != self.factura.moneda:
            raise ValidationError({"moneda": "La moneda del pago debe ser la de la factura."})

    def validar_acreditado(self):
        if not self.fecha_acreditacion:
            raise TransicionInvalida("Informe la fecha de acreditación.")

    def validar_rechazado(self):
        if not self.motivo_rechazo:
            raise TransicionInvalida("Informe el motivo del rechazo o devolución.")
        factura = self.factura
        if factura.estado in ("RECIBIDA", "CERRADA", "ANULADA"):
            raise TransicionInvalida(f"La factura está {factura.estado}; no se puede rechazar el pago.")
        if factura.items.filter(
            embarque_items__embarque__estado__in=ESTADOS_EMBARQUE_CON_CARGA_EN_VIAJE
        ).exists():
            raise TransicionInvalida(
                "Ya hay mercadería de esta factura embarcada; resuelva el rechazo con administración."
            )
        if self.gasto_comision_id and self.gasto_comision.embarque.estado == "CERRADO":
            raise TransicionInvalida("La comisión está en un embarque cerrado.")

    def despues_de_cambiar_estado(self, anterior, nuevo):
        from . import services

        if nuevo == self.Estado.RECHAZADO:
            services.retirar_comision(self)
        services.sincronizar_factura(self.factura)


class Cobro(EstadoMixin, TimeStampedModel):
    class Estado(models.TextChoices):
        REGISTRADO = "REGISTRADO", "Registrado"
        ANULADO = "ANULADO", "Anulado"

    class Medio(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        DEPOSITO = "DEPOSITO", "Depósito bancario"
        CHEQUE = "CHEQUE", "Cheque"
        TARJETA = "TARJETA", "Tarjeta"

    TRANSICIONES = {
        Estado.REGISTRADO: (Estado.ANULADO,),
        Estado.ANULADO: (),
    }

    venta = models.ForeignKey("ventas.Venta", on_delete=models.PROTECT, related_name="cobros")
    fecha = models.DateField(default=datetime.date.today)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    moneda = models.CharField(max_length=3, choices=Moneda.get_choices, default=Moneda.USD)
    tipo_cambio = models.DecimalField(
        max_digits=14,
        decimal_places=6,
        default=Decimal("1"),
        help_text="Cotización a la moneda base (1 si ya está en moneda base).",
    )
    medio = models.CharField(max_length=15, choices=Medio.choices, default=Medio.EFECTIVO)
    referencia = models.CharField(max_length=80, blank=True)
    observaciones = models.TextField(blank=True)

    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.REGISTRADO,
        editable=False,
    )

    class Meta:
        ordering = ["-fecha", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(monto__gt=0), name="cobro_monto_positivo"),
            models.CheckConstraint(condition=Q(tipo_cambio__gt=0), name="cobro_tc_positivo"),
        ]

    def __str__(self):
        return f"Cobro {self.pk} · {self.monto} {self.moneda}"

    @property
    def monto_base(self) -> Decimal:
        return (self.monto * self.tipo_cambio).quantize(Decimal("0.01"))

    @property
    def monto_aplicado(self) -> Decimal:
        return self.aplicaciones.aggregate(t=Sum("monto"))["t"] or Decimal("0")

    @property
    def monto_sin_aplicar(self) -> Decimal:
        return self.monto - self.monto_aplicado


class Cuota(TimeStampedModel):
    venta = models.ForeignKey("ventas.Venta", on_delete=models.CASCADE, related_name="cuotas")
    numero = models.PositiveSmallIntegerField()
    vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["venta", "numero"]
        constraints = [
            models.UniqueConstraint(fields=["venta", "numero"], name="uniq_cuota_por_venta"),
            models.CheckConstraint(condition=Q(monto__gt=0), name="cuota_monto_positivo"),
        ]

    def __str__(self):
        return f"Cuota {self.numero} · vence {self.vencimiento:%d/%m/%Y}"

    @property
    def monto_cobrado(self) -> Decimal:
        return (
            self.aplicaciones.filter(cobro__estado=Cobro.Estado.REGISTRADO)
            .aggregate(t=Sum("monto"))["t"]
            or Decimal("0")
        )

    @property
    def saldo(self) -> Decimal:
        return self.monto - self.monto_cobrado

    @property
    def vencida(self) -> bool:
        return self.vencimiento < datetime.date.today() and self.saldo > 0

    @property
    def situacion(self) -> str:
        if self.saldo <= 0:
            return "CANCELADA"
        if self.vencida:
            return "VENCIDA"
        return "PENDIENTE"


class CobroAplicacion(TimeStampedModel):
    """Cuánto de un cobro se imputa a cada cuota."""

    cobro = models.ForeignKey(Cobro, on_delete=models.CASCADE, related_name="aplicaciones")
    cuota = models.ForeignKey(Cuota, on_delete=models.PROTECT, related_name="aplicaciones")
    monto = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(monto__gt=0), name="aplicacion_monto_positivo"),
            models.UniqueConstraint(fields=["cobro", "cuota"], name="uniq_aplicacion_cobro_cuota"),
        ]

    def __str__(self):
        return f"{self.monto} → {self.cuota}"

    def clean(self):
        if not (self.cobro_id and self.cuota_id):
            raise ValidationError("Debe indicar cobro y cuota.")
        if self.cobro.venta_id != self.cuota.venta_id:
            raise ValidationError("La aplicación debe corresponder a la misma venta.")
        if self.cobro.estado != Cobro.Estado.REGISTRADO:
            raise ValidationError("Solo se pueden aplicar cobros registrados.")
        otras = self.cobro.aplicaciones.exclude(pk=self.pk).aggregate(t=Sum("monto"))["t"] or Decimal("0")
        if otras + self.monto > self.cobro.monto:
            raise ValidationError("La suma de aplicaciones supera el monto del cobro.")
        previo = (
            CobroAplicacion.objects.filter(pk=self.pk).values_list("monto", flat=True).first()
            or Decimal("0")
        )
        saldo_disponible = self.cuota.saldo + previo
        if self.monto > saldo_disponible:
            raise ValidationError("La aplicación excede el saldo disponible de la cuota.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
