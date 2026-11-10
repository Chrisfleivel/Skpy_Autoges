import pandas as pd
from django.core.management.base import BaseCommand
from contabilidad.models import Asiento, MovimientoContable, CuentaContable
from datetime import date

class Command(BaseCommand):
    help = 'Importa saldos iniciales desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('archivo_csv', type=str)

    def handle(self, *args, **options):
        archivo = options['archivo_csv']
        df = pd.read_csv(archivo)

        # Crear el asiento de apertura
        asiento = Asiento.objects.create(
            descripcion="ASIENTO DE APERTURA - CARGA MASIVA",
            fecha=date(2026, 1, 1)
        )

        for _, row in df.iterrows():
            try:
                cuenta = CuentaContable.objects.get(codigo=row['codigo_cuenta'])
                MovimientoContable.objects.create(
                    asiento=asiento,
                    cuenta=cuenta,
                    debe=row['monto'] if row['tipo'] == 'debe' else 0,
                    haber=row['monto'] if row['tipo'] == 'haber' else 0
                )
                self.stdout.write(self.style.SUCCESS(f"Cuenta {row['codigo_cuenta']} cargada."))
            except CuentaContable.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Cuenta {row['codigo_cuenta']} no encontrada."))
        
