from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0033_alter_repuesto_moneda_venta_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposito',
            name='activo',
            field=models.BooleanField(default=True, verbose_name='Activo'),
        ),
        migrations.AddField(
            model_name='deposito',
            name='codigo',
            field=models.CharField(blank=True, default='', max_length=20, unique=True, verbose_name='Código del Depósito'),
        ),
        migrations.AddField(
            model_name='deposito',
            name='es_principal',
            field=models.BooleanField(default=False, verbose_name='Depósito principal'),
        ),
        migrations.AddConstraint(
            model_name='deposito',
            constraint=models.UniqueConstraint(condition=models.Q(es_principal=True), fields=('es_principal',), name='uniq_deposito_principal'),
        ),
    ]
