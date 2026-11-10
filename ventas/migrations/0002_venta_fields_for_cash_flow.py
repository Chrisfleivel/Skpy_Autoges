from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cobranzas", "0002_pago_empleado_pago_estado_pago_monto_recibido_and_more"),
        ("seguridad_usuarios", "0001_initial"),
        ("ventas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="venta",
            name="caja",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ventas",
                to="cobranzas.caja",
            ),
        ),
        migrations.AddField(
            model_name="venta",
            name="empleado",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ventas",
                to="seguridad_usuarios.empleado",
            ),
        ),
        migrations.AddField(
            model_name="venta",
            name="fecha_cobro",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="venta",
            name="monto_pagado",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=14),
        ),
        migrations.AddField(
            model_name="venta",
            name="observaciones",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="venta",
            name="saldo_pendiente",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=14),
        ),
        migrations.AddField(
            model_name="venta",
            name="sucursal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ventas",
                to="configuraciones_maestras.sucursal",
            ),
        ),
        migrations.AlterField(
            model_name="venta",
            name="cliente",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AlterField(
            model_name="venta",
            name="estado",
            field=models.CharField(blank=True, choices=[('BORRADOR', 'Borrador'), ('PENDIENTE_COBRO', 'Pendiente de cobro'), ('PAGADA', 'Pagada'), ('PARCIAL', 'Parcial'), ('ANULADA', 'Anulada')], default='BORRADOR', max_length=20),
        ),
    ]
