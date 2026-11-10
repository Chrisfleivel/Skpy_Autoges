from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes_pedidos', '0008_seleccionproductobuscado_aprobado_seo'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='pago_realizado',
            field=models.BooleanField(default=False),
        ),
    ]
