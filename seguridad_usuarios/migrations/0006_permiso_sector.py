# Generated manually: add sector field to Permiso model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seguridad_usuarios', '0005_rol_utilizado'),
    ]

    operations = [
        migrations.AddField(
            model_name='permiso',
            name='sector',
            field=models.CharField(max_length=50, blank=True, null=True),
        ),
    ]
