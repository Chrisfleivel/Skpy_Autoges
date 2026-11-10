from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes_pedidos', '0009_pedido_pago_realizado'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_pago', models.CharField(choices=[('pedido', 'Pago de Pedido'), ('cotizacion', 'Pago de Cotización')], max_length=10, verbose_name='Tipo de Pago')),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto del Pago')),
                ('fecha_pago', models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora del Pago')),
                ('metodo_pago', models.CharField(max_length=50, verbose_name='Método de Pago')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('cotizacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pagos', to='clientes_pedidos.cotizacion', verbose_name='Cotización Relacionada')),
                ('pedido', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pagos', to='clientes_pedidos.pedido', verbose_name='Pedido Relacionado')),
            ],
            options={
                'verbose_name': 'Pago',
                'verbose_name_plural': 'Pagos',
                'ordering': ['-fecha_pago'],
            },
        ),
    ]
