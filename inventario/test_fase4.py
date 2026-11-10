from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventario.models import Deposito, MovimientoStock, Repuesto, UnidadMedida


class InventarioFase4TestCase(TestCase):
    def setUp(self):
        self.deposito = Deposito.objects.create(
            nombre='Deposito Central',
            ubicacion='Asunción',
            capacidad_maxima=100,
        )
        self.unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-001',
            unidad_medida=self.unidad,
            stock_actual=10,
            stock_reservado=0,
            stock_minimo=2,
            costo_compra=Decimal('50.00'),
            precio_venta=Decimal('80.00'),
            proveedor_id=None,
            moneda_compra_proveedor_id=None,
            moneda_venta_id=None,
            costo_unitario_proveedor=Decimal('50.00'),
        )

    def test_reservar_stock_reduce_reserva_pero_no_stock_actual(self):
        self.repuesto.reservar_stock(3)

        self.assertEqual(self.repuesto.stock_actual, 10)
        self.assertEqual(self.repuesto.stock_reservado, 3)
        self.assertEqual(self.repuesto.stock_disponible, 7)

    def test_cuando_se_libera_reserva_queda_disponible(self):
        self.repuesto.reservar_stock(3)
        self.repuesto.liberar_reserva(2)

        self.assertEqual(self.repuesto.stock_reservado, 1)
        self.assertEqual(self.repuesto.stock_disponible, 9)

    def test_entrada_de_stock_registra_movimiento(self):
        self.repuesto.registrar_entrada(5, motivo='Compra de reposición')

        self.assertEqual(self.repuesto.stock_actual, 15)
        self.assertEqual(MovimientoStock.objects.filter(repuesto=self.repuesto, tipo='ENTRADA').count(), 1)

    def test_salida_de_stock_no_permite_superar_disponible(self):
        with self.assertRaises(ValidationError):
            self.repuesto.registrar_salida(20, motivo='Venta por encima del stock')
