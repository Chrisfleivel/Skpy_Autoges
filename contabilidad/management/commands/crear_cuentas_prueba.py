from django.core.management.base import BaseCommand
from django.db import connection
from configuraciones_maestras.models import Moneda
from contabilidad.models import CuentaContable


def ensure_table(model):
    with connection.schema_editor() as schema_editor:
        table_name = model._meta.db_table
        if table_name not in connection.introspection.table_names():
            schema_editor.create_model(model)


class Command(BaseCommand):
    help = 'Crea cuentas contables básicas para pruebas del módulo de contabilidad.'

    def handle(self, *args, **options):
        ensure_table(Moneda)
        ensure_table(CuentaContable)

        moneda, _ = Moneda.objects.get_or_create(
            codigo='PYG',
            defaults={'nombre': 'Guaraníes'}
        )

        cuentas = [
            ('1.1.01', 'Cuentas por Cobrar', 'A'),
            ('1.1.02', 'Caja', 'A'),
            ('1.1.03', 'Clientes', 'A'),
            ('2.1.01', 'Proveedores', 'P'),
            ('2.1.02', 'IVA por Pagar', 'P'),
            ('3.1.01', 'Capital Social', 'PN'),
            ('4.1.01', 'Ventas', 'I'),
            ('4.1.02', 'Ingresos por Servicios', 'I'),
            ('5.1.01', 'Gastos Administrativos', 'E'),
            ('5.1.02', 'Gastos de Ventas', 'E'),
            ('6.1.01', 'Ganancia x Dif. Cambio', 'I'),
            ('6.1.02', 'Pérdida x Dif. Cambio', 'E'),
        ]

        creadas = 0
        actualizadas = 0

        for codigo, nombre, tipo in cuentas:
            cuenta, created = CuentaContable.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'tipo': tipo,
                    'es_imputable': True,
                    'moneda': moneda,
                },
            )
            if created:
                creadas += 1
            else:
                actualizadas += 1
            self.stdout.write(self.style.SUCCESS(f"{'Creada' if created else 'Actualizada'}: {codigo} - {nombre}"))

        self.stdout.write(self.style.SUCCESS(f'Proceso finalizado. Creadas: {creadas} | Actualizadas: {actualizadas}'))
