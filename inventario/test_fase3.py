from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventario.models import Deposito, MovimientoStock, Repuesto, UnidadMedida
from inventario.services import ajustar_stock, registrar_entrada, transferir


class InventarioFase3TestCase(TestCase):
    def setUp(self):
        self.unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        self.origen = Deposito.objects.create(
            codigo='ORIGEN',
            nombre='Depósito Origen',
            ubicacion='Asunción',
            capacidad_maxima=100,
            es_principal=False,
            activo=True,
        )
        self.destino = Deposito.objects.create(
            codigo='DESTINO',
            nombre='Depósito Destino',
            ubicacion='San Lorenzo',
            capacidad_maxima=100,
            es_principal=False,
            activo=True,
        )
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-003',
            unidad_medida=self.unidad,
            stock_actual=10,
            stock_reservado=2,
            stock_minimo=3,
            costo_compra=Decimal('50.00'),
            precio_venta=Decimal('80.00'),
            costo_unitario_proveedor=Decimal('50.00'),
        )

    def test_registrar_entrada_incrementa_stock_y_guarda_movimiento(self):
        movimiento = registrar_entrada(
            self.repuesto,
            5,
            motivo='Compra de reposición',
            deposito=self.destino,
            referencia='FAC-001',
            costo_unitario=Decimal('60.00'),
        )

        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock_actual, 15)
        self.assertEqual(movimiento.tipo, 'ENTRADA')
        self.assertEqual(movimiento.cantidad, 5)
        self.assertEqual(movimiento.deposito_destino, self.destino)

    def test_ajustar_stock_no_permite_bajar_del_reservado(self):
        with self.assertRaises(ValidationError):
            ajustar_stock(self.repuesto, 1, motivo='Conteo físico')

    def test_ajustar_stock_deja_el_stock_real_y_crea_movimiento(self):
        movimiento = ajustar_stock(self.repuesto, 12, motivo='Conteo final', deposito=self.destino)

        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock_actual, 12)
        self.assertIsNotNone(movimiento)
        self.assertEqual(movimiento.tipo, 'AJUSTE')
        self.assertEqual(movimiento.cantidad, 2)

    def test_transferir_registra_movimiento_sin_alterar_stock_total(self):
        antes = self.repuesto.stock_actual
        movimiento = transferir(
            self.repuesto,
            3,
            deposito_origen=self.origen,
            deposito_destino=self.destino,
            motivo='Traslado entre depósitos',
            referencia='TR-01',
        )

        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.stock_actual, antes)
        self.assertEqual(movimiento.tipo, 'TRANSFERENCIA')
        self.assertEqual(movimiento.cantidad, 3)
        self.assertEqual(movimiento.deposito_origen, self.origen)
        self.assertEqual(movimiento.deposito_destino, self.destino)
