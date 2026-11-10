from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes_pedidos', '0020_facturacompraproveedor_facturacompraitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='productobuscado',
            name='tipo_producto',
            field=models.CharField(choices=[('vehiculo', 'Vehículo'), ('repuesto', 'Repuesto')], default='vehiculo', max_length=10),
        ),
    ]
