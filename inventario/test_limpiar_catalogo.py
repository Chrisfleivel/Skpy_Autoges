"""
Tests del comando `limpiar_catalogo`.

El comando borra las tablas huérfanas de la app `catalogo` (eliminada del
proyecto). Tiene que ser:

- idempotente: si no hay tablas, no hace nada;
- prudente: si alguna otra tabla tiene una FK hacia `catalogo_*`, se niega a
  borrar en lugar de romper la integridad referencial.
"""

from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase

TABLA_FAKE = 'catalogo_repuesto'


class LimpiarCatalogoTestCase(TestCase):
    def _crear_tabla_fake(self):
        with connection.cursor() as cursor:
            cursor.execute(
                f'CREATE TABLE "{TABLA_FAKE}" ("id" integer primary key, "nombre" varchar(50))'
            )

    def _existe(self, tabla):
        with connection.cursor() as cursor:
            return tabla in connection.introspection.table_names(cursor)

    def _salida(self, *args):
        buffer = StringIO()
        call_command('limpiar_catalogo', *args, stdout=buffer)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    def test_borra_las_tablas_orphan(self):
        self._crear_tabla_fake()
        self.assertTrue(self._existe(TABLA_FAKE))

        salida = self._salida()

        self.assertFalse(self._existe(TABLA_FAKE))
        self.assertIn('Listo', salida)

    def test_es_idempotente(self):
        salida = self._salida()

        self.assertIn('nada que hacer', salida)

    def test_el_dry_run_no_toca_la_base(self):
        self._crear_tabla_fake()

        salida = self._salida('--dry-run')

        self.assertTrue(self._existe(TABLA_FAKE))
        self.assertIn('dry-run', salida)

    def test_no_borra_si_algo_la_referencia(self):
        self._crear_tabla_fake()
        with connection.cursor() as cursor:
            cursor.execute(
                'CREATE TABLE "test_referencia_catalogo" ('
                '"id" integer primary key, '
                '"repuesto_id" integer NOT NULL REFERENCES "catalogo_repuesto"("id"))'
            )
        try:
            salida = self._salida()

            self.assertTrue(self._existe(TABLA_FAKE))
            self.assertIn('Hay otras tablas apuntando', salida)
        finally:
            with connection.cursor() as cursor:
                cursor.execute('DROP TABLE "test_referencia_catalogo"')
                cursor.execute(f'DROP TABLE "{TABLA_FAKE}"')

    def test_las_migraciones_de_catalogo_no_quedan_registradas(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM django_migrations WHERE app = 'catalogo'")

            self.assertEqual(cursor.fetchone()[0], 0)
