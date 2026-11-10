from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import Moneda, TimeStampedModel


class VentaItem(TimeStampedModel):
    """Línea de una venta de repuestos o vehículos."""

    venta = models.ForeignKey("Venta", on_delete=models.CASCADE, related_name="items")
    repuesto = models.ForeignKey("inventario.Repuesto", on_delete=models.PROTECT, null=True, blank=True, related_name="items_venta")
    cantidad = models.PositiveIntegerField(default=0)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    descripcion = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        repuesto_desc = self.repuesto.codigo_repuesto if self.repuesto_id else "Sin repuesto"
        return f"{repuesto_desc} × {self.cantidad}"


class Venta(TimeStampedModel):
    """Venta comercial con control de caja, sucursal y flujo de cobro."""

    ESTADO_CHOICES = (
        ("BORRADOR", "Borrador"),
        ("PENDIENTE_COBRO", "Pendiente de cobro"),
        ("PAGADA", "Pagada"),
        ("PARCIAL", "Parcial"),
        ("ANULADA", "Anulada"),
    )

    numero = models.CharField(max_length=50, unique=True)
    cliente = models.CharField(max_length=200, blank=True, default="")
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    monto_pagado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    saldo_pendiente = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    moneda = models.CharField(max_length=3, choices=Moneda.get_choices, default=Moneda.USD)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="BORRADOR", blank=True)
    sucursal = models.ForeignKey(
        "configuraciones_maestras.Sucursal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
    )
    empleado = models.ForeignKey(
        "seguridad_usuarios.Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
    )
    caja = models.ForeignKey(
        "cobranzas.Caja",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
    )
    fecha_cobro = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-creado", "-id"]

    @property
    def saldo_restante(self):
        return max(self.total - self.monto_pagado, Decimal("0.00"))

    def save(self, *args, **kwargs):
        self.total = Decimal(str(self.total or "0"))
        self.monto_pagado = Decimal(str(self.monto_pagado or "0"))
        self.saldo_pendiente = max(self.total - self.monto_pagado, Decimal("0.00"))

        if self.total > 0 and self.monto_pagado >= self.total:
            self.estado = "PAGADA"
        elif self.total > 0 and self.monto_pagado > 0:
            self.estado = "PENDIENTE_COBRO"
        elif self.estado == "PAGADA" and self.monto_pagado < self.total:
            self.estado = "PENDIENTE_COBRO"

        super().save(*args, **kwargs)

    def registrar_pago(
        self,
        monto,
        *,
        caja=None,
        empleado=None,
        sucursal=None,
        metodo_pago="EFECTIVO",
        observaciones="",
    ):
        from cobranzas.models import Pago

        monto = Decimal(str(monto))
        if monto <= 0:
            raise ValidationError("El monto del cobro debe ser mayor que cero.")

        if caja is not None:
            self.caja = caja
        if empleado is not None:
            self.empleado = empleado
        if sucursal is not None:
            self.sucursal = sucursal

        if self.caja_id is None:
            raise ValidationError("Debe indicar una caja para registrar el cobro.")
        if self.caja.estado not in {"ABIERTA", "abierta"}:
            raise ValidationError("La caja debe estar abierta para registrar este cobro.")
        if self.sucursal_id and self.caja.sucursal_id != self.sucursal_id:
            raise ValidationError("La caja no pertenece a la sucursal de la venta.")
        if self.empleado_id and self.caja.empleado_actual_id and self.caja.empleado_actual_id != self.empleado_id:
            raise ValidationError("El empleado del cobro no coincide con el responsable de la caja.")
        if monto > self.saldo_restante:
            raise ValidationError(
                f"El monto cobrado ({monto}) supera el saldo restante de la venta ({self.saldo_restante})."
            )

        pago = Pago.objects.create(
            tipo_pago="pedido",
            pedido=None,
            cotizacion=None,
            sucursal=self.sucursal or self.caja.sucursal,
            caja=self.caja,
            empleado=self.empleado,
            monto=monto,
            monto_recibido=monto,
            vuelto=Decimal("0.00"),
            metodo_pago=str(metodo_pago).upper(),
            estado="confirmado",
            observaciones=observaciones,
            fecha_pago=timezone.now(),
        )

        self.monto_pagado = self.monto_pagado + monto
        self.fecha_cobro = timezone.now()
        self.observaciones = observaciones or self.observaciones
        self.save(update_fields=["monto_pagado", "fecha_cobro", "observaciones", "estado", "saldo_pendiente"])

        self.caja.saldo_actual = Decimal(str(self.caja.saldo_actual)) + monto
        self.caja.save(update_fields=["saldo_actual"])

        return pago

    def __str__(self):
        return f"Venta {self.numero}"
