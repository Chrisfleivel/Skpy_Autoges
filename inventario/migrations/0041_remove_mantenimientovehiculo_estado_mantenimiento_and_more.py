"""
Taller: estado único con `EstadoMixin`, repuestos con cantidad y costo
separados de la mano de obra.

El estado del mantenimiento venía en dos campos (`estado` booleano y
`estado_mantenimiento` texto). Se unifican en `estado`: se borra el booleano
y se renombra el de texto, que es el que tenía la información real.
"""

import django.db.models.deletion
from django.db import migrations, models


def copiar_repuestos_utilizados(apps, schema_editor):
    """
    Pasa los repuestos del M2M viejo (sin cantidad) a la tabla nueva.

    El M2M viejo solo guardaba "qué repuestos se usaron"; la cantidad y el
    costo salen del propio repuesto.
    """
    from django.db import connection

    tabla = 'inventario_mantenimientovehiculo_repuestos_utilizados'
    with connection.cursor() as cursor:
        if tabla not in connection.introspection.table_names(cursor):
            return
        cursor.execute(f'SELECT "mantenimiento_id", "repuesto_id" FROM "{tabla}"')
        lineas = cursor.fetchall()

    MantenimientoRepuesto = apps.get_model('inventario', 'MantenimientoRepuesto')
    Repuesto = apps.get_model('inventario', 'Repuesto')
    for mantenimiento_id, repuesto_id in lineas:
        repuesto = Repuesto.objects.filter(pk=repuesto_id).first()
        if repuesto is None:
            continue
        MantenimientoRepuesto.objects.get_or_create(
            mantenimiento_id=mantenimiento_id,
            repuesto_id=repuesto_id,
            defaults={
                'cantidad': 1,
                'costo_unitario': repuesto.costo_unitario or 0,
            },
        )


def completar_descripciones(apps, schema_editor):
    """Rellena las descripciones nulas antes de volverlas obligatorias."""
    MantenimientoVehiculo = apps.get_model('inventario', 'MantenimientoVehiculo')
    MantenimientoVehiculo.objects.filter(descripcion__isnull=True).update(descripcion='')


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0040_sembrar_stock_repuesto'),
    ]

    operations = [
        # --- estado: un solo campo, conservando el dato real --------------
        migrations.RemoveField(
            model_name='mantenimientovehiculo',
            name='estado',
        ),
        migrations.RenameField(
            model_name='mantenimientovehiculo',
            old_name='estado_mantenimiento',
            new_name='estado',
        ),
        migrations.AlterField(
            model_name='mantenimientovehiculo',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En proceso'), ('finalizado', 'Finalizado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=20, verbose_name='Estado'),
        ),

        # --- costos: mano de obra separada de los repuestos ---------------
        migrations.AddField(
            model_name='mantenimientovehiculo',
            name='costo_mano_obra',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Costo de Mano de Obra (Guaraníes)'),
        ),
        migrations.AlterField(
            model_name='mantenimientovehiculo',
            name='costo',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Costo Total del Mantenimiento (Guaraníes)'),
        ),

        # --- repuestos con cantidad y costo propio -------------------------
        migrations.CreateModel(
            name='MantenimientoRepuesto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1, verbose_name='Cantidad Utilizada')),
                ('costo_unitario', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Costo Unitario (Guaraníes)')),
                ('mantenimiento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repuestos', to='inventario.mantenimientovehiculo')),
                ('movimiento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='inventario.movimientostock', verbose_name='Movimiento de Stock')),
                ('repuesto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='usos_en_mantenimientos', to='inventario.repuesto')),
            ],
            options={
                'verbose_name': 'repuesto de mantenimiento',
                'verbose_name_plural': 'repuestos de mantenimiento',
                'ordering': ['id'],
            },
        ),

        # Los repuestos del M2M viejo (sin cantidad) pasan a la tabla nueva.
        migrations.RunPython(copiar_repuestos_utilizados, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='mantenimientovehiculo',
            name='repuestos_utilizados',
        ),
        migrations.AddField(
            model_name='mantenimientovehiculo',
            name='repuestos_utilizados',
            field=models.ManyToManyField(blank=True, related_name='mantenimientos', through='inventario.MantenimientoRepuesto', to='inventario.repuesto', verbose_name='Repuestos Utilizados'),
        ),
        migrations.AddConstraint(
            model_name='mantenimientorepuesto',
            constraint=models.UniqueConstraint(fields=('mantenimiento', 'repuesto'), name='uniq_repuesto_por_mantenimiento'),
        ),
        migrations.AddConstraint(
            model_name='mantenimientorepuesto',
            constraint=models.CheckConstraint(condition=models.Q(('cantidad__gte', 1)), name='mantenimiento_repuesto_cantidad_positiva'),
        ),

        # --- depósito y control de descuento de stock ----------------------
        migrations.AddField(
            model_name='mantenimientovehiculo',
            name='deposito',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mantenimientos', to='inventario.deposito', verbose_name='Depósito de los Repuestos'),
        ),
        migrations.AddField(
            model_name='mantenimientovehiculo',
            name='stock_descontado',
            field=models.BooleanField(default=False, editable=False, verbose_name='Stock ya descontado'),
        ),

        # --- la descripción vuelve a ser obligatoria ------------------------
        migrations.RunPython(completar_descripciones, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mantenimientovehiculo',
            name='descripcion',
            field=models.TextField(verbose_name='Descripción del Mantenimiento'),
        ),
    ]
