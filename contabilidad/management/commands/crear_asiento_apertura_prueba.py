from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from configuraciones_maestras.models import Moneda
from contabilidad.models import CuentaContable, Asiento
from contabilidad.services import registrar_asiento_apertura


class Command(BaseCommand):
    help = 'Crea un asiento de apertura de prueba con cuentas básicas y evita duplicados.'

    def handle(self, *args, **options):
        with transaction.atomic():
            moneda, _ = Moneda.objects.get_or_create(
                codigo='PYG',
                defaults={'nombre': 'Guaraníes'}
            )

            cuentas = [
                ('1.1.02', 'Caja', 'A'),
                ('3.1.01', 'Capital Social', 'PN'),
            ]

            for codigo, nombre, tipo in cuentas:
                CuentaContable.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        'nombre': nombre,
                        'tipo': tipo,
                        'es_imputable': True,
                        'moneda': moneda,
                    },
                )

            descripcion = 'ASIENTO DE APERTURA PRUEBA'
            if Asiento.objects.filter(descripcion=descripcion).exists():
                self.stdout.write(self.style.WARNING('Ya existe un asiento de apertura de prueba. No se creó uno nuevo.'))
                return

            asiento = registrar_asiento_apertura(
                [
                    {'codigo_cuenta': '1.1.02', 'monto': 100000, 'tipo': 'debe'},
                    {'codigo_cuenta': '3.1.01', 'monto': 100000, 'tipo': 'haber'},
                ],
                descripcion=descripcion,
                fecha=timezone.now().date(),
            )

            self.stdout.write(self.style.SUCCESS(f'Asiento de apertura de prueba creado: {asiento.id}'))
