from django.core.management.base import BaseCommand

from configuraciones_maestras.models import DespachanteAduana


class Command(BaseCommand):
    help = 'Crea despachantes de aduana base para las importaciones de prueba'

    def handle(self, *args, **options):
        # Crear despachante de aduana en Paraguay
        despachante_py, created_py = DespachanteAduana.objects.get_or_create(
            nombre='Despachante Aduana Paraguay Test',
            defaults={
                'razon_social': 'Despachante Aduana Paraguay Test S.A.',
                'registro': 'TEST-PY-0001',
                'contacto': 'Despachante de Prueba',
                'telefono': '0981-111111',
                'email': 'despachante.py@test.local',
                'direccion': 'Asunción, Paraguay',
                'ruc': '8001111110001',
                'estado': True,
            },
        )

        if created_py:
            self.stdout.write(self.style.SUCCESS(f'✓ Despachante de aduana (Paraguay) creado: {despachante_py.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ Despachante de aduana (Paraguay) ya existe: {despachante_py.nombre}'))

        # Crear despachante de aduana en Corea
        despachante_kr, created_kr = DespachanteAduana.objects.get_or_create(
            nombre='Despachante Aduana Corea Test',
            defaults={
                'razon_social': 'Despachante Aduana Corea Test Co., Ltd.',
                'registro': 'TEST-KR-0001',
                'contacto': 'Despachante Corea',
                'telefono': '+82-10-1234-5678',
                'email': 'despachante.kr@test.local',
                'direccion': 'Seúl, Corea del Sur',
                'ruc': 'KR-0001111110',
                'estado': True,
            },
        )

        if created_kr:
            self.stdout.write(self.style.SUCCESS(f'✓ Despachante de aduana (Corea) creado: {despachante_kr.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ Despachante de aduana (Corea) ya existe: {despachante_kr.nombre}'))

        # Asignar a las importaciones que no tienen despachante_aduana
        from importaciones.models import Importacion

        importaciones = Importacion.objects.filter(despachante_aduana__isnull=True)
        actualizadas = 0

        for importacion in importaciones:
            importacion.despachante_aduana = despachante_py
            importacion.save(update_fields=['despachante_aduana'])
            actualizadas += 1

        if actualizadas > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ Importaciones actualizadas: {actualizadas}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ No hay importaciones sin despachante de aduana'))

        # Resumen final
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Despachantes de aduana disponibles:'))
        despachantes = DespachanteAduana.objects.all()
        for d in despachantes:
            self.stdout.write(f'  • {d.nombre} ({d.ruc})')
        self.stdout.write(self.style.SUCCESS('='*60))
