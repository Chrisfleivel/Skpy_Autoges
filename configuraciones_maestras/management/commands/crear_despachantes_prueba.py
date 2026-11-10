from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from configuraciones_maestras.models import Despachante
from importaciones.models import Importacion


class Command(BaseCommand):
    help = 'Crea despachantes de prueba para las importaciones y los asigna a las importaciones sin despachante.'

    def handle(self, *args, **options):
        hoy = timezone.now().date()

        despachante_py, created_py = Despachante.objects.get_or_create(
            nombre_razon_social='Despachante Test Paraguay',
            defaults={
                'pais_codigo': 'PY',
                'ruc_o_brn': '8001234567-1',
                'tipo_representacion': 'CUSTOMS_BROKER',
                'sistema_gestion': 'VUI_SOFIA',
                'fecha_vencimiento_mandato': hoy + timedelta(days=365),
                'contacto_email': 'despachante.py@test.local',
                'es_activo': True,
            },
        )

        if created_py:
            self.stdout.write(self.style.SUCCESS(f'✓ Despachante creado (Paraguay): {despachante_py.nombre_razon_social}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ Despachante ya existe (Paraguay): {despachante_py.nombre_razon_social}'))

        despachante_kr, created_kr = Despachante.objects.get_or_create(
            nombre_razon_social='Despachante Test Corea',
            defaults={
                'pais_codigo': 'KR',
                'ruc_o_brn': 'KR-123456789',
                'tipo_representacion': 'IOR',
                'sistema_gestion': 'UNI_PASS',
                'fecha_vencimiento_mandato': hoy + timedelta(days=180),
                'contacto_email': 'despachante.kr@test.local',
                'es_activo': True,
            },
        )

        if created_kr:
            self.stdout.write(self.style.SUCCESS(f'✓ Despachante creado (Corea): {despachante_kr.nombre_razon_social}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ Despachante ya existe (Corea): {despachante_kr.nombre_razon_social}'))

        importaciones = Importacion.objects.filter(despachante__isnull=True)
        actualizadas = 0

        for importacion in importaciones:
            importacion.despachante = despachante_py
            importacion.save(update_fields=['despachante'])
            actualizadas += 1

        if actualizadas > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ Importaciones actualizadas con despachante: {actualizadas}'))
        else:
            self.stdout.write(self.style.WARNING('ℹ No hay importaciones sin despachante para actualizar'))

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Despachantes disponibles:'))
        for despachante in Despachante.objects.all():
            self.stdout.write(f'  • {despachante.nombre_razon_social} ({despachante.get_pais_codigo_display()})')
        self.stdout.write(self.style.SUCCESS('=' * 60))
