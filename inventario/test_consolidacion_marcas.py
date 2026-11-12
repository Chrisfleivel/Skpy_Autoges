"""
Tests de la unificación de marcas y modelos (Tanda 0).

La lógica vive en la migración `0042_unificar_marcas_modelos`; estos tests
la ejecutan contra la base de pruebas para asegurar que:

- La marca duplicada desaparece y sus vehículos pasan a la canónica.
- Los modelos con el mismo nombre se fusionan (los vehículos también).
- Los modelos sin equivalente se trasladan a la marca canónica.
- Los modelos repetidos dentro de una misma marca se limpian.
- La operación es idempotente: correrla dos veces no cambia nada.
"""

import importlib
from decimal import Decimal

from django.apps import apps as django_apps
from django.test import TestCase

from inventario.models import MarcaVehiculo, ModeloVehiculo, Vehiculo

MIGRACION = importlib.import_module(
    'inventario.migrations.0042_unificar_marcas_modelos')


def unificar():
    """Ejecuta la lógica de unificación sobre la base de pruebas."""
    MIGRACION.unificar_marcas_modelos(django_apps)


class UnificacionMarcasTestCase(TestCase):
    def setUp(self):
        # Marca canónica (la que ya existe) y su duplicada en mayúsculas.
        self.hyundai = MarcaVehiculo.objects.create(nombre='Hyundai')
        self.hyundai_mayus = MarcaVehiculo.objects.create(nombre='HYUNDAI')

        # Un modelo con el mismo nombre en cada marca y otro solo en la vieja.
        self.tucson = ModeloVehiculo.objects.create(
            marca=self.hyundai, nombre='Tucson')
        self.tucson_mayus = ModeloVehiculo.objects.create(
            marca=self.hyundai_mayus, nombre='Tucson')
        self.veloster = ModeloVehiculo.objects.create(
            marca=self.hyundai_mayus, nombre='Veloster')

        self.vehiculo = self._vehiculo('TUCSON-001', self.hyundai_mayus, self.tucson_mayus)
        self.vehiculo_sin_modelo = self._vehiculo('VELOSTER-01', self.hyundai_mayus, None)

    def _vehiculo(self, chasis, marca, modelo):
        return Vehiculo.objects.create(
            nombre='Test',
            codigo_chasis=chasis,
            **{'año': 2024},
            marca=marca,
            modelo=modelo,
            costo_compra=Decimal('0.00'),
            precio_venta=Decimal('1000.00'),
        )

    # ------------------------------------------------------------------
    def test_la_marca_duplicada_desaparece(self):
        unificar()

        self.assertFalse(MarcaVehiculo.objects.filter(pk=self.hyundai_mayus.pk).exists())
        self.assertTrue(MarcaVehiculo.objects.filter(pk=self.hyundai.pk).exists())

    def test_los_vehiculos_pasan_a_la_marca_canonica(self):
        unificar()

        self.vehiculo.refresh_from_db()
        self.vehiculo_sin_modelo.refresh_from_db()

        self.assertEqual(self.vehiculo.marca, self.hyundai)
        self.assertEqual(self.vehiculo_sin_modelo.marca, self.hyundai)

    def test_los_modelos_con_el_mismo_nombre_se_fusionan(self):
        unificar()

        self.assertFalse(ModeloVehiculo.objects.filter(pk=self.tucson_mayus.pk).exists())
        self.assertTrue(ModeloVehiculo.objects.filter(pk=self.tucson.pk).exists())

        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.modelo, self.tucson)

    def test_los_modelos_sin_equivalente_se_trasladan(self):
        unificar()

        veloster = ModeloVehiculo.objects.get(nombre='Veloster')
        self.assertEqual(veloster.marca, self.hyundai)

    def test_los_modelos_que_no_coinciden_no_se_mezclan(self):
        """'Tucson' y 'Tucson / Sport' son modelos distintos."""
        sport = ModeloVehiculo.objects.create(
            marca=self.hyundai_mayus, nombre='Tucson / Sport')

        unificar()

        sport.refresh_from_db()
        self.assertEqual(sport.marca, self.hyundai)
        self.assertEqual(ModeloVehiculo.objects.filter(nombre__startswith='Tucson').count(), 2)

    def test_se_limpian_los_duplicados_dentro_de_una_marca(self):
        """Dos modelos con el mismo nombre en la misma marca: queda uno."""
        primero = ModeloVehiculo.objects.create(marca=self.hyundai, nombre='Kona')
        segundo = ModeloVehiculo.objects.create(marca=self.hyundai, nombre='Kona')
        vehiculo = self._vehiculo('KONA-001', self.hyundai, segundo)

        unificar()

        self.assertEqual(
            ModeloVehiculo.objects.filter(marca=self.hyundai, nombre='Kona').count(), 1)
        vehiculo.refresh_from_db()
        self.assertIn(vehiculo.modelo_id, (primero.pk, segundo.pk))

    def test_es_idempotente(self):
        unificar()

        marcas = set(MarcaVehiculo.objects.values_list('nombre', flat=True))
        modelos = ModeloVehiculo.objects.count()
        vehiculos = Vehiculo.objects.count()

        unificar()  # segunda pasada

        self.assertEqual(set(MarcaVehiculo.objects.values_list('nombre', flat=True)), marcas)
        self.assertEqual(ModeloVehiculo.objects.count(), modelos)
        self.assertEqual(Vehiculo.objects.count(), vehiculos)

    def test_no_toca_marcas_fuera_de_la_lista(self):
        """Solo se fusionan las familias configuradas en CANONICOS."""
        toyota = MarcaVehiculo.objects.create(nombre='Toyota')
        toyota_mayus = MarcaVehiculo.objects.create(nombre='TOYOTA')
        modelo = ModeloVehiculo.objects.create(marca=toyota_mayus, nombre='Corolla')

        unificar()

        self.assertTrue(MarcaVehiculo.objects.filter(pk=toyota_mayus.pk).exists())
        self.assertEqual(modelo.marca, toyota_mayus)

    def test_no_deja_el_vehiculo_con_marca_distinta_a_la_de_su_modelo(self):
        unificar()

        for vehiculo in Vehiculo.objects.select_related('marca', 'modelo__marca'):
            if vehiculo.modelo_id:
                self.assertEqual(vehiculo.marca_id, vehiculo.modelo.marca_id)
