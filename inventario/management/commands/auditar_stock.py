"""
Comando de auditoría del ledger de stock.

Ejemplos:

    manage.py auditar_stock
    manage.py auditar_stock --repuesto FILT-003
    manage.py auditar_stock --strict
"""

from django.core.management.base import BaseCommand

from inventario.auditoria import auditar_stock


class Command(BaseCommand):
    help = (
        'Audita el ledger de stock (MovimientoStock) contra el físico real de '
        'los depósitos. Devuelve código de salida 1 si encuentra errores.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--repuesto',
            type=str,
            default='',
            help='Limita la auditoría al repuesto con ese código.',
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Tratar los avisos (stock legacy sin migrar) como errores.',
        )

    def handle(self, *args, **options):
        repuesto = (options.get('repuesto') or '').strip()
        estricto = options.get('strict', False)

        resultado = auditar_stock(repuesto=repuesto or None)

        self.stdout.write(self.style.MIGRATE_HEADING('Auditoría de stock'))
        self.stdout.write(
            f'  Movimientos revisados : {resultado.movimientos_revisados}'
        )
        self.stdout.write(
            f'  Depósitos con stock   : {resultado.depositos_revisados}'
        )
        self.stdout.write('')

        if resultado.errores:
            self.stdout.write(self.style.ERROR(f'ERRORES ({len(resultado.errores)}):'))
            for error in resultado.errores:
                self.stdout.write(f'  - {error}')
            self.stdout.write('')

        if resultado.avisos:
            encabezado = 'AVISOS' if not estricto else 'AVISOS (tratados como errores por --strict)'
            self.stdout.write(self.style.WARNING(f'{encabezado} ({len(resultado.avisos)}):'))
            for aviso in resultado.avisos:
                self.stdout.write(f'  - {aviso}')
            self.stdout.write('')

        if not resultado.errores and not resultado.avisos:
            self.stdout.write(self.style.SUCCESS('Sin errores ni avisos: el stock cuadra.'))

        if resultado.errores:
            self.stderr.write(self.style.ERROR(f'Auditoría fallida: {resultado.resumen()}.'))
            raise SystemExit(1)

        if estricto and resultado.avisos:
            self.stderr.write(
                self.style.ERROR(
                    f'Auditoría fallida (--strict): {resultado.resumen()}.'
                )
            )
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS(f'Auditoría correcta: {resultado.resumen()}.'))
