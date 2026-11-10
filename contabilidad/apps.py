from django.apps import AppConfig
from django.db.models.signals import post_migrate


def crear_permisos_contabilidad(sender, **kwargs):
    if sender.name != 'contabilidad':
        return

    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    content_type, _ = ContentType.objects.get_or_create(app_label='contabilidad', model='asiento')
    permisos = [
        ('ver_asientos_contables', 'Puede ver asientos contables'),
        ('ver_movimientos_contables', 'Puede ver movimientos de asientos contables'),
        ('marcar_asientos_revisados', 'Puede marcar asientos como revisados'),
        ('ver_auditoria_asientos', 'Puede ver auditoría de asientos'),
        ('ver_reportes', 'Puede ver reportes contables'),
    ]

    for codename, nombre in permisos:
        Permission.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={'name': nombre},
        )


class ContabilidadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contabilidad'

    def ready(self):
        post_migrate.connect(crear_permisos_contabilidad, sender=self)
