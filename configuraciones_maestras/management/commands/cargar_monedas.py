from django.core.management.base import BaseCommand
from configuraciones_maestras.models import Moneda


class Command(BaseCommand):
    help = 'Carga las monedas por defecto en la base de datos si no existen'

    def handle(self, *args, **options):
        if Moneda.objects.exists():
            self.stdout.write(
                self.style.WARNING('Ya existen monedas en la base de datos')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Cargando monedas por defecto...')
            )
            Moneda.objects.cargar_monedas_iniciales()