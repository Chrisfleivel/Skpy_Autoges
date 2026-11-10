import calendar
from django.db import models
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils import timezone
from datetime import date
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from configuraciones_maestras.models import Moneda




class CuentaContable(models.Model):
    TIPO_CUENTA = [('A', 'Activo'), ('P', 'Pasivo'), ('PN', 'Patrimonio'), ('I', 'Ingreso'), ('E', 'Egreso')]
    # El código debe seguir una estructura como:
    # 1.1.01 (Activo -> Activo Corriente -> Caja)
    codigo = models.CharField(max_length=20, unique=True) # Ej: 1.1.01.01
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=2, choices=TIPO_CUENTA)
    es_imputable = models.BooleanField(default=True) # Si se pueden registrar movimientos en ella
    moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT, default=1) # Moneda por defecto: Guaraníes'
    
    def get_saldo(self, fecha_hasta):
        """Calcula el saldo acumulado a una fecha dada."""
        cierre = SaldoMensualCuenta.objects.filter(
            cuenta=self
        ).filter(
            models.Q(anio__lt=fecha_hasta.year) |
            (models.Q(anio=fecha_hasta.year) & models.Q(mes__lt=fecha_hasta.month))
        ).order_by('-anio', '-mes').first()

        if cierre:
            cierre_fecha = date(cierre.anio, cierre.mes, calendar.monthrange(cierre.anio, cierre.mes)[1])
            movimientos = self.movimientocontable_set.filter(
                asiento__fecha__gt=cierre_fecha,
                asiento__fecha__lte=fecha_hasta,
            )
            total_debe = movimientos.aggregate(models.Sum('debe'))['debe__sum'] or 0
            total_haber = movimientos.aggregate(models.Sum('haber'))['haber__sum'] or 0

            if self.tipo in ['A', 'E']:
                return cierre.saldo_final + total_debe - total_haber
            return cierre.saldo_final + total_haber - total_debe

        movimientos = self.movimientocontable_set.filter(asiento__fecha__lte=fecha_hasta)
        total_debe = movimientos.aggregate(models.Sum('debe'))['debe__sum'] or 0
        total_haber = movimientos.aggregate(models.Sum('haber'))['haber__sum'] or 0

        # Lógica contable: 
        # Si es Activo/Egreso, saldo = Debe - Haber
        # Si es Pasivo/Patrimonio/Ingreso, saldo = Haber - Debe
        if self.tipo in ['A', 'E']:
            return total_debe - total_haber
        return total_haber - total_debe
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    

class Asiento(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    descripcion = models.CharField(max_length=255)

    class Meta:
        permissions = [
            ('ver_asientos_contables', 'Puede ver asientos contables'),
            ('ver_movimientos_contables', 'Puede ver movimientos de asientos contables'),
            ('marcar_asientos_revisados', 'Puede marcar asientos como revisados'),
            ('ver_auditoria_asientos', 'Puede ver auditoría de asientos'),
            ('ver_reportes', 'Puede ver reportes contables'),
        ]
    tasa_cambio_al_momento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.00,
        null=True,
        blank=True,
    )
    # Vinculamos el asiento a un documento financiero cuando exista.
    documento_tipo = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asientos_contables',
    )
    documento_id = models.PositiveIntegerField(null=True, blank=True)
    documento = GenericForeignKey('documento_tipo', 'documento_id')
    revisado = models.BooleanField(default=False)
    fecha_revision = models.DateTimeField(null=True, blank=True)
    revisado_por = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)

    def es_bloqueado(self):
        """
        Retorna True si la fecha del asiento es igual o anterior 
        a la fecha de cierre configurada.
        """
        if 'contabilidad_configuracioncontable' not in connection.introspection.table_names():
            return False

        config = ConfiguracionContable.objects.first()
        if config and config.fecha_cierre_bloqueo:
            return self.fecha.date() <= config.fecha_cierre_bloqueo
        return False
    
    def crear_asiento_ajuste(self, descripcion_ajuste, movimientos_inversos):
        """
        Crea un nuevo asiento en la fecha actual para corregir 
        este asiento bloqueado.
        """
        if not self.es_bloqueado():
            raise ValidationError("Este asiento no está bloqueado, puede editarlo directamente.")
            
        nuevo_asiento = Asiento.objects.create(
            fecha=timezone.now(),
            descripcion=f"AJUSTE: {descripcion_ajuste} (Ref: {self.id})",
            documento=self.documento,
            tasa_cambio_al_momento=self.tasa_cambio_al_momento or 1.00,
        )
        # Aquí añades la lógica para registrar los MovimientosContables
        # que revierten o corrigen el error original.
        return nuevo_asiento

    def clean(self):
        super().clean()

        if self.pk and self.es_bloqueado():
            raise ValidationError(
                f"Acción denegada: El asiento corresponde a un periodo cerrado (hasta {ConfiguracionContable.objects.first().fecha_cierre_bloqueo})."
            )

        if self.pk:
            movimientos = list(self.movimientos.all())
            if movimientos:
                total_debe = sum((mov.debe or 0) for mov in movimientos)
                total_haber = sum((mov.haber or 0) for mov in movimientos)
                if total_debe != total_haber:
                    raise ValidationError(
                        f"El asiento no está balanceado: debe={total_debe}, haber={total_haber}."
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.pk and self.es_bloqueado():
            raise ValidationError(
                f"Acción denegada: El asiento corresponde a un periodo cerrado (hasta {ConfiguracionContable.objects.first().fecha_cierre_bloqueo})."
            )
        super().save(*args, **kwargs)

class MovimientoContable(models.Model):
    asiento = models.ForeignKey(Asiento, on_delete=models.CASCADE, related_name='movimientos')
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.PROTECT)
    debe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    haber = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def clean(self):
        super().clean()
        if self.debe and self.haber:
            raise ValidationError("Un movimiento no puede tener valor en debe y haber al mismo tiempo.")
        if self.debe < 0 or self.haber < 0:
            raise ValidationError("Los importes de debe y haber no pueden ser negativos.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    
class SaldoMensualCuenta(models.Model):
    cuenta = models.ForeignKey('CuentaContable', on_delete=models.CASCADE)
    anio = models.IntegerField()
    mes = models.IntegerField()
    saldo_final = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ('cuenta', 'anio', 'mes') # Un solo registro por cuenta/mes


class ConfiguracionContable(models.Model):
    empresa = models.OneToOneField('configuraciones_maestras.Empresa', on_delete=models.CASCADE)
    fecha_cierre_bloqueo = models.DateField(verbose_name="Fecha de cierre contable")

    def __str__(self):
        return f"Bloqueo hasta: {self.fecha_cierre_bloqueo}"