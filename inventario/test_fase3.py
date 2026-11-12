from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventario.models import Deposito, MovimientoStock, Repuesto, StockRepuesto, UnidadMedida
from inventario.services import ajustar_stock, registrar_entrada, registrar_salida, transferir


class InventarioFase3TestCase(TestCase):
    """
    El stock vive en `StockRepuesto` (una fila por repuesto y depósito).

    Las cantidades de los movimientos son siempre positivas: la dirección la
    indican `deposito_destino` (entrada) y `deposito_origen` (salida).
    """

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
        self.stock_origen = StockRepuesto.objects.create(
            repuesto=self.repuesto, deposito=self.origen, cantidad=10, reservado=2)
        self.stock_destino = StockRepuesto.objects.create(
            repuesto=self.repuesto, deposito=self.destino, cantidad=5)

    def test_registrar_entrada_incrementa_stock_y_guarda_movimiento(self):
        movimiento = registrar_entrada(
            self.repuesto,
            self.destino,
            5,
            Decimal('60.00'),
            motivo='Compra de reposición',
            referencia='FAC-001',
        )

        self.stock_destino.refresh_from_db()
        self.assertEqual(self.stock_destino.cantidad, 10)
        self.assertEqual(movimiento.tipo, MovimientoStock.Tipo.ENTRADA_COMPRA)
        self.assertEqual(movimiento.cantidad, 5)
        self.assertEqual(movimiento.deposito_destino, self.destino)
        self.assertEqual(movimiento.saldo_posterior, 10)

    def test_registrar_entrada_actualiza_el_costo_promedio_ponderado(self):
        # Físico total 15 a costo base 50; entran 5 a 60 → (15*50 + 5*60)/20 = 52.50
        registrar_entrada(self.repuesto, self.destino, 5, Decimal('60.00'))

        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.costo_unitario, Decimal('52.50'))

    def test_registrar_entrada_exige_deposito_activo(self):
        inactivo = Deposito.objects.create(
            codigo='INACTIVO', nombre='Depósito Inactivo', ubicacion='Luque', activo=False)

        with self.assertRaises(ValidationError):
            registrar_entrada(self.repuesto, inactivo, 5, Decimal('60.00'))

    def test_ajustar_stock_no_permite_bajar_del_reservado(self):
        with self.assertRaises(ValidationError):
            ajustar_stock(self.repuesto, 1, motivo='Conteo físico', deposito=self.origen)

    def test_ajustar_stock_deja_el_stock_real_y_crea_movimiento(self):
        movimiento = ajustar_stock(self.repuesto, 12, motivo='Conteo final', deposito=self.origen)

        self.stock_origen.refresh_from_db()
        self.assertEqual(self.stock_origen.cantidad, 12)
        self.assertIsNotNone(movimiento)
        self.assertEqual(movimiento.tipo, MovimientoStock.Tipo.AJUSTE)
        self.assertEqual(movimiento.cantidad, 2)
        self.assertEqual(movimiento.deposito_destino, self.origen)

    def test_ajustar_stock_a_la_baja_marca_el_deposito_de_origen(self):
        movimiento = ajustar_stock(self.repuesto, 9, motivo='Merma', deposito=self.origen)

        self.stock_origen.refresh_from_db()
        self.assertEqual(self.stock_origen.cantidad, 9)
        self.assertEqual(movimiento.deposito_origen, self.origen)
        self.assertIsNone(movimiento.deposito_destino)

    def test_transferir_registra_movimiento_sin_alterar_stock_total(self):
        antes = self.stock_origen.cantidad + self.stock_destino.cantidad

        salida, entrada = transferir(
            self.repuesto,
            3,
            deposito_origen=self.origen,
            deposito_destino=self.destino,
            motivo='Traslado entre depósitos',
            referencia='TR-01',
        )

        self.stock_origen.refresh_from_db()
        self.stock_destino.refresh_from_db()

        self.assertEqual(self.stock_origen.cantidad + self.stock_destino.cantidad, antes)
        self.assertEqual(salida.tipo, MovimientoStock.Tipo.TRANSFERENCIA_SALIDA)
        self.assertEqual(entrada.tipo, MovimientoStock.Tipo.TRANSFERENCIA_ENTRADA)
        self.assertEqual(salida.cantidad, 3)
        self.assertEqual(salida.deposito_origen, self.origen)
        self.assertEqual(entrada.deposito_destino, self.destino)
        self.assertEqual(salida.grupo, entrada.grupo)

    def test_transferir_no_puede_superar_el_disponible(self):
        with self.assertRaises(ValidationError):
            # En origen hay 10 físicos pero 2 reservados → disponible 8.
            transferir(
                self.repuesto,
                9,
                deposito_origen=self.origen,
                deposito_destino=self.destino,
                motivo='Traslado sin disponible',
            )

    def test_registrar_salida_descuenta_el_fisico_y_deja_movimiento(self):
        movimiento = registrar_salida(
            self.repuesto,
            3,
            deposito=self.destino,
            motivo='Consumo en taller',
            referencia='MANT-1',
        )

        self.stock_destino.refresh_from_db()
        self.assertEqual(self.stock_destino.cantidad, 2)
        self.assertEqual(movimiento.tipo, MovimientoStock.Tipo.SALIDA)
        self.assertEqual(movimiento.cantidad, 3)
        self.assertEqual(movimiento.deposito_origen, self.destino)
        self.assertIsNone(movimiento.deposito_destino)
        self.assertEqual(movimiento.saldo_posterior, 2)

    def test_registrar_salida_no_toca_la_reserva(self):
        registrar_salida(self.repuesto, 2, deposito=self.destino)

        self.stock_destino.refresh_from_db()
        self.assertEqual(self.stock_destino.reservado, 0)

    def test_registrar_salida_no_puede_superar_el_disponible(self):
        with self.assertRaises(ValidationError):
            # En origen hay 10 físicos pero 2 reservados → disponible 8.
            registrar_salida(self.repuesto, 9, deposito=self.origen)

    def test_registrar_salida_exige_deposito_de_salida(self):
        with self.assertRaises(ValidationError):
            registrar_salida(self.repuesto, 1)

    def test_registrar_salida_exige_fila_de_stock_en_el_deposito(self):
        deposito_vacio = Deposito.objects.create(
            codigo='VACIO',
            nombre='Depósito sin stock',
            ubicacion='Luque',
            activo=True,
        )

        with self.assertRaises(ValidationError):
            registrar_salida(self.repuesto, 1, deposito=deposito_vacio)
