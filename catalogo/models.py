import re
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from core.models import EstadoMixin, TimeStampedModel, TransicionInvalida

validar_vin = RegexValidator(
    regex=r"^[A-HJ-NPR-Z0-9]{17}$",
    flags=re.IGNORECASE,
    message="El chasis (VIN) debe tener 17 caracteres alfanuméricos, sin las letras I, O ni Q.",
)


class Marca(TimeStampedModel):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Modelo(TimeStampedModel):
    class Carroceria(models.TextChoices):
        SEDAN = "SEDAN", "Sedán"
        HATCHBACK = "HATCHBACK", "Hatchback"
        SUV = "SUV", "SUV / Todoterreno"
        PICKUP = "PICKUP", "Pick-up"
        UTILITARIO = "UTILITARIO", "Utilitario / Camión liviano"
        COUPE = "COUPE", "Coupé"
        FURGON = "FURGON", "Furgón / Minivan"
        OTRO = "OTRO", "Otro"

    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="modelos")
    nombre = models.CharField(max_length=100)
    carroceria = models.CharField(max_length=12, choices=Carroceria.choices, default=Carroceria.OTRO)

    class Meta:
        ordering = ["marca__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["marca", "nombre"], name="uniq_modelo_por_marca"),
        ]

    def __str__(self):
        return f"{self.marca} {self.nombre}"

# vehicle model represents a vehicle in the inventory, with various attributes such as chassis number, model, year, color, engine number, and more. It also includes methods for calculating estimated margin and checking availability for sale. The model uses the EstadoMixin to manage state transitions and enforce business rules related to vehicle status.
class Vehiculo(EstadoMixin, TimeStampedModel):
    class Estado(models.TextChoices):
        COMPRADO = "COMPRADO", "Comprado"
        PAGADO = "PAGADO", "Pagado al proveedor"
        EMBARCADO = "EMBARCADO", "Embarcado"
        EN_TRANSITO = "EN_TRANSITO", "En tránsito"
        EN_ADUANA = "EN_ADUANA", "En aduana"
        EN_STOCK = "EN_STOCK", "En stock"
        RESERVADO = "RESERVADO", "Reservado"
        VENDIDO = "VENDIDO", "Vendido"
        ENTREGADO = "ENTREGADO", "Entregado"

    class Combustible(models.TextChoices):
        NAFTA = "NAFTA", "Nafta"
        DIESEL = "DIESEL", "Diésel"
        HIBRIDO = "HIBRIDO", "Híbrido"
        ELECTRICO = "ELECTRICO", "Eléctrico"
        GNC = "GNC", "GNC / GLP"
        OTRO = "OTRO", "Otro"

    class Transmision(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        AUTOMATICA = "AUTOMATICA", "Automática"
        OTRA = "OTRA", "Otra"

    TRANSICIONES = {
        Estado.COMPRADO: (Estado.PAGADO,),
        Estado.PAGADO: (Estado.COMPRADO, Estado.EMBARCADO),
        Estado.EMBARCADO: (Estado.EN_TRANSITO, Estado.PAGADO),
        Estado.EN_TRANSITO: (Estado.EN_ADUANA,),
        Estado.EN_ADUANA: (Estado.EN_STOCK,),
        Estado.EN_STOCK: (Estado.RESERVADO, Estado.VENDIDO),
        Estado.RESERVADO: (Estado.EN_STOCK, Estado.VENDIDO),
        Estado.VENDIDO: (Estado.ENTREGADO, Estado.EN_STOCK),
        Estado.ENTREGADO: (),
    }

    chasis = models.CharField(
        "Chasis (VIN)", max_length=17, unique=True, validators=[validar_vin]
    )
    modelo = models.ForeignKey("Modelo", on_delete=models.PROTECT, related_name="vehiculos")
    version = models.CharField(max_length=100, blank=True, help_text="Ej.: 2.0 CRDi, 320D, E300")
    anio = models.PositiveSmallIntegerField("Año")
    color = models.CharField(max_length=40, blank=True)
    nro_motor = models.CharField("Nº de motor", max_length=40, blank=True)
    cilindrada_cc = models.PositiveIntegerField("Cilindrada (cc)", null=True, blank=True)
    combustible = models.CharField(max_length=10, choices=Combustible.choices, default=Combustible.OTRO)
    transmision = models.CharField(max_length=10, choices=Transmision.choices, default=Transmision.OTRA)
    kilometraje = models.PositiveIntegerField(null=True, blank=True)
    volante_a_la_derecha = models.BooleanField(
        "Volante a la derecha",
        default=False,
        help_text="Relevante para la habilitación al importar.",
    )
    observaciones = models.TextField(blank=True)

    costo_fob = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, editable=False)
    costo_total = models.DecimalField(
        "Costo landed",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
    )
    precio_lista = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.COMPRADO,
        editable=False,
    )

    class Meta:
        ordering = ["-creado"]
        indexes = [models.Index(fields=["estado"]) ]
        constraints = [
            models.CheckConstraint(condition=Q(anio__gte=1900), name="vehiculo_anio_minimo"),
            models.CheckConstraint(
                condition=Q(precio_lista__isnull=True) | Q(precio_lista__gte=0),
                name="vehiculo_precio_no_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.modelo} {self.anio} · {self.chasis}"

    def save(self, *args, **kwargs):
        self.chasis = re.sub(r"[\s\-]", "", self.chasis or "").upper()
        super().save(*args, **kwargs)

    @property
    def margen_estimado(self):
        if self.precio_lista is None or self.costo_total is None:
            return None
        return self.precio_lista - self.costo_total

    @property
    def margen_porcentaje(self):
        margen = self.margen_estimado
        if margen is None or not self.precio_lista:
            return None
        return (margen / self.precio_lista * 100).quantize(Decimal("0.1"))

    @property
    def disponible_para_venta(self) -> bool:
        return self.estado == self.Estado.EN_STOCK

    def validar_reservado(self):
        if self.precio_lista is None:
            raise TransicionInvalida("Defina el precio de lista antes de reservar el vehículo.")

    def validar_vendido(self):
        if self.costo_total is None:
            raise TransicionInvalida(
                "El vehículo no tiene costo landed: prorratee los costos del embarque antes de venderlo."
            )


class VehiculoFoto(TimeStampedModel):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="catalogo/vehiculos/%Y/%m/")
    descripcion = models.CharField(max_length=120, blank=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["vehiculo", "orden", "id"]

    def __str__(self):
        return f"Foto de {self.vehiculo.chasis}"


class CategoriaRepuesto(TimeStampedModel):
    nombre = models.CharField(max_length=100)
    padre = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="subcategorias"
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "categoría de repuesto"
        verbose_name_plural = "categorías de repuestos"
        constraints = [
            models.UniqueConstraint(fields=["padre", "nombre"], name="uniq_categoria_por_padre"),
        ]

    def __str__(self):
        return f"{self.padre} › {self.nombre}" if self.padre_id else self.nombre

    def clean(self):
        if self.padre_id and self.padre_id == self.pk:
            raise ValidationError({"padre": "Una categoría no puede ser su propio padre."})


class Repuesto(TimeStampedModel):
    class Unidad(models.TextChoices):
        UNIDAD = "UN", "Unidad"
        JUEGO = "JG", "Juego"
        PAR = "PAR", "Par"
        LITRO = "LT", "Litro"
        KILO = "KG", "Kilogramo"

    sku = models.CharField("SKU", max_length=40, unique=True, blank=True, default="")
    descripcion = models.CharField(max_length=255)
    categoria = models.ForeignKey(
        CategoriaRepuesto, null=True, blank=True, on_delete=models.PROTECT, related_name="repuestos"
    )
    fabricante = models.CharField(max_length=100, blank=True)
    codigo_oem = models.CharField("Código OEM", max_length=60, blank=True, db_index=True)
    unidad = models.CharField(max_length=3, choices=Unidad.choices, default=Unidad.UNIDAD)
    compatibilidad = models.ManyToManyField("Modelo", blank=True, related_name="repuestos_compatibles")

    precio_lista = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    stock_minimo = models.PositiveIntegerField(default=0)
    costo_promedio = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, editable=False)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["sku"]

    def __str__(self):
        return f"{self.sku} · {self.descripcion}"

    @property
    def stock_total(self) -> int:
        try:
            return int(sum(stock.cantidad for stock in self.stocks.all()))
        except Exception:
            return 0

    @property
    def disponible_total(self) -> int:
        try:
            return int(sum(stock.disponible for stock in self.stocks.filter(deposito__activo=True)))
        except Exception:
            return 0

    @property
    def bajo_minimo(self) -> bool:
        if self.stock_minimo <= 0:
            return False
        return self.stock_total < self.stock_minimo

    def save(self, *args, **kwargs):
        self.sku = (self.sku or "").strip().upper()
        super().save(*args, **kwargs)
