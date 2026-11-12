"""
Limpia las tablas de la app `catalogo`, que fue eliminada del proyecto.

La app `catalogo` estuvo deshabilitada durante un tiempo: sus tablas quedaron
en las bases que ya existían (siempre vacías) y su migración quedó registrada
en `django_migrations` sin que el app existiera más. Con el app eliminado, esas
tablas son huérfanas: nadie las crea, nadie las migra y el esquema de una base
limpia difiere del de una base vieja.

Este comando las elimina. Es idempotente: si no existen, no hace nada.

    python manage.py limpiar_catalogo
    python manage.py limpiar_catalogo --dry-run   # solo muestra lo que haría
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction

TABLAS_CATALOGO = (
    'catalogo_marca',
    'catalogo_modelo',
    'catalogo_vehiculo',
    'catalogo_vehiculofoto',
    'catalogo_categoriarepuesto',
    'catalogo_repuesto',
    'catalogo_repuesto_compatibilidad',
)


class Command(BaseCommand):
    help = 'Elimina las tablas huérfanas de la app `catalogo` ( eliminada del proyecto).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se borraría sin tocar la base.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        with connection.cursor() as cursor:
            existentes = set(connection.introspection.table_names(cursor))

        a_borrar = [tabla for tabla in TABLAS_CATALOGO if tabla in existentes]
        sobrantes = [tabla for tabla in existentes if tabla.startswith('catalogo_')]

        if not sobrantes:
            self.stdout.write('No hay tablas de `catalogo` en la base: nada que hacer.')
            return

        # Nadie debe apuntar a estas tablas: si algo lo hace, no se tocan.
        referencias = self._referencias(sobrantes)
        if referencias:
            self.stdout.write(self.style.ERROR(
                'Hay otras tablas apuntando a `catalogo`:\n  '
                + '\n  '.join(referencias)
                + '\nSe aborta: revisá esas referencias antes de borrar.'
            ))
            return

        desconocidas = sorted(set(sobrantes) - set(a_borrar))
        if desconocidas:
            self.stdout.write(self.style.WARNING(
                'Hay tablas `catalogo_*` fuera de la lista conocida: '
                + ', '.join(desconocidas)
            ))

        for tabla in a_borrar:
            if dry_run:
                self.stdout.write(f'[dry-run] DROP TABLE "{tabla}"')
                continue
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP TABLE IF EXISTS "{tabla}"')
            self.stdout.write(f'Drop: {tabla}')

        # La migración del app eliminado queda huérfana en el historial.
        if dry_run:
            self.stdout.write('[dry-run] Se limpiaría django_migrations (app=catalogo).')
            return

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM django_migrations WHERE app = 'catalogo'")
            borradas = cursor.rowcount

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {len(a_borrar)} tabla(s) eliminada(s), '
            f'{borradas} registro(s) de migración limpiado(s).'
        ))

    def _referencias(self, tablas):
        """Tablas (fuera de `catalogo`) que tienen FKs hacia las tablas dadas."""
        referencias = []
        with connection.cursor() as cursor:
            existentes = connection.introspection.table_names(cursor)
            for tabla in existentes:
                if tabla.startswith('catalogo_'):
                    continue
                constraints = connection.introspection.get_constraints(cursor, tabla)
                for nombre, info in constraints.items():
                    if not info.get('foreign_key'):
                        continue
                    referenciada = info.get('references') or info.get('foreign_key')
                    if referenciada and referenciada[0] in tablas:
                        referencias.append(f'{tabla}.{nombre} -> {referenciada[0]}')
        return referencias
