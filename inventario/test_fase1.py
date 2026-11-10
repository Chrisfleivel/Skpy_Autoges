from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventario.models import Deposito, Repuesto, UnidadMedida


class InventarioFase1TestCase(TestCase):
    def setUp(self):
        self.unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        self.deposito = Deposito.objects.create(
            codigo='central',
            nombre='Depósito Central',
            ubicacion='Asunción',
            capacidad_maxima=100,
            es_principal=True,
            activo=True,
        )
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-001',
            unidad_medida=self.unidad,
            stock_actual=10,
            stock_reservado=2,
            stock_minimo=3,
            costo_compra=Decimal('50.00'),
            precio_venta=Decimal('80.00'),
            costo_unitario_proveedor=Decimal('50.00'),
        )

    def test_deposito_normaliza_codigo_y_marca_principal(self):
        self.assertEqual(self.deposito.codigo, 'CENTRAL')
        self.assertTrue(self.deposito.es_principal)
        self.assertTrue(self.deposito.activo)

    def test_no_se_permite_dos_depositos_principales(self):
        with self.assertRaises(ValidationError):
            Deposito.objects.create(
                codigo='sucursal',
                nombre='Sucursal Principal',
                ubicacion='San Lorenzo',
                capacidad_maxima=50,
                es_principal=True,
            )

    def test_stock_disponible_se_calcula_sobre_stock_real_y_reservado(self):
        self.assertEqual(self.repuesto.stock_disponible, 8)
        self.assertTrue(self.repuesto.puede_reservar(8))
        self.assertFalse(self.repuesto.puede_reservar(9))

    def test_entrada_de_stock_aumenta_el_disponible(self):
        self.repuesto.registrar_entrada(5, motivo='Compra de reposición')

        self.assertEqual(self.repuesto.stock_actual, 15)
        self.assertEqual(self.repuesto.stock_disponible, 13)
