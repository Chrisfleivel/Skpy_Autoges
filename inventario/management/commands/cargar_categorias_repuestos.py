from django.core.management.base import BaseCommand
from django.db import models
from inventario.models import Repuesto, CategoriaRepuesto

CATEGORIES = [
    'Sistema de Motor y Mantenimiento',
    'Sistema de Frenos y Seguridad',
    'Suspensión y Dirección',
    'Sistema Eléctrico y Sensores',
    'Transmisión y Otros',
    'Carrocería y Accesorios',
    'Climatización',
    'Iluminación',
    'Accesorios Interiores',
    'Herramientas y Mantenimiento',
]

class Command(BaseCommand):
    help = 'Muestra y sugiere categorías de repuestos. Opcionalmente asigna una categoría por defecto a repuestos sin categoría.'

    def add_arguments(self, parser):
        parser.add_argument('--assign-default', type=str, dest='default', help='Asignar la categoría dada a repuestos sin categoría')
        parser.add_argument('--dry-run', action='store_true', dest='dry_run', help='No aplicar cambios, solo mostrar lo que se haría')

    def handle(self, *args, **options):
        default = options.get('default')
        dry_run = options.get('dry_run')

        self.stdout.write(self.style.MIGRATE_HEADING('Categorías sugeridas:'))
        for cat in CATEGORIES:
            count = Repuesto.objects.filter(categoria__nombre=cat).count()
            self.stdout.write(f' - {cat} (repuestos existentes: {count})')

        total = Repuesto.objects.count()
        sin_cat = Repuesto.objects.filter(categoria__isnull=True).count()
        self.stdout.write('\n')
        self.stdout.write(f'Total repuestos: {total}')
        self.stdout.write(f'Repuestos sin categoría: {sin_cat}')

        if default:
            default_category, created = CategoriaRepuesto.objects.get_or_create(
                nombre=default,
                defaults={'descripcion': '', 'estado': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoría "{default}" creada.'))

            self.stdout.write('\n')
            self.stdout.write(self.style.WARNING(f"Asignando '{default}' a {sin_cat} repuestos sin categoría"))
            if dry_run:
                self.stdout.write(self.style.SUCCESS('Dry-run: no se realizaron cambios.'))
                return
            updated = Repuesto.objects.filter(categoria__isnull=True).update(categoria=default_category)
            self.stdout.write(self.style.SUCCESS(f'Se asignaron {updated} repuestos a la categoría "{default}"'))
