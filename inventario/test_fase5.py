from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventario.models import Deposito, MovimientoStock, Repuesto, UnidadMedida
from inventario.services import confirmar_venta


class InventarioFase5TestCase(TestCase):
    def setUp(self):
        self.deposito = Deposito.objects.create(
            nombre='Depósito Fase 5',
            ubicacion='Asunción',
            capacidad_maxima=100,
        )
        self.unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro de aire',
            codigo_repuesto='FILTRO-005',
            unidad_medida=self.unidad,
            stock_actual=10,
            stock_reservado=3,
            stock_minimo=2,
            costo_compra=Decimal('60.00'),
            precio_venta=Decimal('90.00'),
            proveedor_id=None,
            moneda_compra_proveedor_id=None,
            moneda_venta_id=None,
            costo_unitario_proveedor=Decimal('60.00'),
        )

    def test_confirmar_venta_resta_stock_actual_y_reserva(self):
        movimiento = confirmar_venta(
            self.repuesto,
            2,
            motivo='Entrega a cliente',
            deposito=self.deposito,
            referencia='PED-150',
        )

        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock_actual, 8)
        self.assertEqual(self.repuesto.stock_reservado, 1)
        self.assertEqual(movimiento.tipo, 'SALIDA')
        self.assertEqual(movimiento.cantidad, 2)
        self.assertEqual(movimiento.deposito_origen, self.deposito)

    def test_confirmar_venta_no_permite_cantidad_mayor_al_stock_real(self):
        with self.assertRaises(ValidationError):
            confirmar_venta(self.repuesto, 15, motivo='Venta excedida')
