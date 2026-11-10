from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0016_alter_vehiculo_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='repuesto',
            name='stock_reservado',
            field=models.PositiveIntegerField(default=0, verbose_name='Stock Reservado por Pedidos'),
        ),
    ]
