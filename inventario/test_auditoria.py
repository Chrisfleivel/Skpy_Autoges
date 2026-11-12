"""
Tests de la auditoría del ledger de stock (`manage.py auditar_stock`).

La auditoría tiene que encontrar las incoherencias reales: movimientos sin
dirección, transferencias a medio hacer, saldos que no cuadran con el físico
y repuestos que solo existen en el campo legacy `stock_actual`.
"""

from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from inventario.auditoria import auditar_stock
from inventario.models import Deposito, MovimientoStock, Repuesto, StockRepuesto, UnidadMedida


class AuditoriaStockTestCase(TestCase):
    def setUp(self):
        self.unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        self.deposito = Deposito.objects.create(
            codigo='AUD',
            nombre='Depósito Auditoría',
            ubicacion='Asunción',
            capacidad_maxima=100,
            activo=True,
        )
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro de auditoría',
            codigo_repuesto='AUD-001',
            unidad_medida=self.unidad,
            stock_actual=10,
            stock_reservado=0,
            stock_minimo=2,
            costo_compra=Decimal('50.00'),
            precio_venta=Decimal('80.00'),
            costo_unitario_proveedor=Decimal('50.00'),
        )
        self.stock = StockRepuesto.objects.create(
            repuesto=self.repuesto,
            deposito=self.deposito,
            cantidad=10,
            reservado=0,
        )

    def _entrada_coherente(self, **kwargs):
        """Movimiento de entrada que cuadra con el físico actual."""
        return MovimientoStock.objects.create(
            repuesto=self.repuesto,
            deposito_destino=self.deposito,
            tipo=MovimientoStock.Tipo.ENTRADA,
            cantidad=10,
            saldo_posterior=10,
            motivo='Entrada de prueba',
            **kwargs,
        )

    def _repuesto_legacy(self, codigo='AUD-002', stock=7):
        """Repuesto que solo existe en `stock_actual` (sin `StockRepuesto`)."""
        return Repuesto.objects.create(
            nombre=f'Repuesto legacy {codigo}',
            codigo_repuesto=codigo,
            unidad_medida=self.unidad,
            stock_actual=stock,
            stock_reservado=0,
            stock_minimo=1,
            costo_compra=Decimal('10.00'),
            precio_venta=Decimal('20.00'),
            costo_unitario_proveedor=Decimal('10.00'),
        )

    # ------------------------------------------------------------------
    # Escenario sano
    # ------------------------------------------------------------------
    def test_auditoria_sin_incoherencias_no_reporta_nada(self):
        self._entrada_coherente()

        resultado = auditar_stock()

        self.assertEqual(resultado.errores, [])
        self.assertEqual(resultado.avisos, [])
        self.assertTrue(resultado.ok)
        self.assertEqual(resultado.movimientos_revisados, 1)

    def test_comando_auditar_stock_termina_con_codigo_cero_si_todo_cuadra(self):
        self._entrada_coherente()

        call_command('auditar_stock')

    # ------------------------------------------------------------------
    # Incoherencias del ledger
    # ------------------------------------------------------------------
    def test_detecta_movimiento_sin_deposito(self):
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            tipo=MovimientoStock.Tipo.SALIDA,
            cantidad=1,
            motivo='Salida sin depósito',
        )

        resultado = auditar_stock()

        self.assertFalse(resultado.ok)
        self.assertTrue(any('deposito_origen' in error for error in resultado.errores))

    def test_detecta_direccion_incoherente_con_el_tipo(self):
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            deposito_origen=self.deposito,
            tipo=MovimientoStock.Tipo.ENTRADA,
            cantidad=1,
            motivo='Entrada con depósito de origen',
        )

        resultado = auditar_stock()

        self.assertFalse(resultado.ok)
        self.assertTrue(
            any('entrada debe informar `deposito_destino`' in error for error in resultado.errores)
        )

    def test_detecta_ajuste_con_los_dos_depositos(self):
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            deposito_origen=self.deposito,
            deposito_destino=self.deposito,
            tipo=MovimientoStock.Tipo.AJUSTE,
            cantidad=1,
            motivo='Ajuste ambiguo',
        )

        resultado = auditar_stock()

        self.assertFalse(resultado.ok)
        self.assertTrue(any('exactamente un depósito' in error for error in resultado.errores))

    def test_detecta_transferencia_a_medias(self):
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            deposito_origen=self.deposito,
            tipo=MovimientoStock.Tipo.TRANSFERENCIA_SALIDA,
            cantidad=3,
            saldo_posterior=7,
            motivo='Transferencia sin entrada',
            grupo='11111111-1111-1111-1111-111111111111',
        )

        resultado = auditar_stock()

        self.assertFalse(resultado.ok)
        self.assertTrue(any('incompleta' in error for error in resultado.errores))

    def test_detecta_transferencia_con_cantidades_distintas(self):
        origen = Deposito.objects.create(
            codigo='AUD2', nombre='Depósito Auditoría 2', ubicacion='Luque', activo=True)
        grupo = '22222222-2222-2222-2222-222222222222'
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            deposito_origen=self.deposito,
            tipo=MovimientoStock.Tipo.TRANSFERENCIA_SALIDA,
            cantidad=3,
            saldo_posterior=7,
            grupo=grupo,
        )
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            deposito_destino=origen,
            tipo=MovimientoStock.Tipo.TRANSFERENCIA_ENTRADA,
            cantidad=5,
            saldo_posterior=5,
            grupo=grupo,
        )

        resultado = auditar_stock()

        self.assertFalse(resultado.ok)
        self.assertTrue(any('cantidades distintas' in error for error in resultado.errores))

    def test_detecta_saldo_posterior_que_no_cuadra_con_el_fisico(self):
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            deposito_destino=self.deposito,
            tipo=MovimientoStock.Tipo.ENTRADA,
            cantidad=4,
            saldo_posterior=4,
            motivo='Entrada parcial',
        )
        self.stock.cantidad = 10
        self.stock.save(update_fields=['cantidad'])

        resultado = auditar_stock()

        self.assertFalse(resultado.ok)
        self.assertTrue(any('saldo posterior' in error for error in resultado.errores))

    def test_detecta_fisico_que_no_cuadra_con_los_movimientos(self):
        self._entrada_coherente()
        self.stock.cantidad = 12
        self.stock.save(update_fields=['cantidad'])

        resultado = auditar_stock()

        self.assertFalse(resultado.ok)
        self.assertTrue(any('Físico inconsistente' in error for error in resultado.errores))

    # ------------------------------------------------------------------
    # Inventario legacy
    # ------------------------------------------------------------------
    def test_avisa_repuesto_legacy_sin_fila_en_stock_repuesto(self):
        self._entrada_coherente()
        self._repuesto_legacy()

        resultado = auditar_stock()

        self.assertEqual(resultado.errores, [])
        self.assertTrue(any('AUD-002' in aviso for aviso in resultado.avisos))
        self.assertTrue(any('stock_actual' in aviso for aviso in resultado.avisos))

    def test_avisa_divergencia_entre_stock_actual_y_fisico_multi_deposito(self):
        self.stock.cantidad = 4
        self.stock.save(update_fields=['cantidad'])
        self._entrada_coherente()

        resultado = auditar_stock()

        self.assertTrue(any('no coinciden' in aviso for aviso in resultado.avisos))

    def test_auditoria_limitada_a_un_repuesto(self):
        self._entrada_coherente()
        self._repuesto_legacy(codigo='AUD-003', stock=9)

        resultado = auditar_stock(repuesto='AUD-003')

        self.assertTrue(any('AUD-003' in aviso for aviso in resultado.avisos))
        self.assertFalse(any('AUD-001' in aviso for aviso in resultado.avisos))

    # ------------------------------------------------------------------
    # Comando
    # ------------------------------------------------------------------
    def test_comando_devuelve_codigo_de_salida_1_hay_errores(self):
        MovimientoStock.objects.create(
            repuesto=self.repuesto,
            tipo=MovimientoStock.Tipo.SALIDA,
            cantidad=1,
            motivo='Salida sin depósito',
        )

        with self.assertRaises(SystemExit) as contexto:
            call_command('auditar_stock')

        self.assertEqual(contexto.exception.code, 1)

    def test_comando_estricto_falla_con_avisos(self):
        self._entrada_coherente()
        self._repuesto_legacy()

        with self.assertRaises(SystemExit) as contexto:
            call_command('auditar_stock', '--strict')

        self.assertEqual(contexto.exception.code, 1)

    def test_comando_estricto_pasa_si_no_hay_ni_errores_ni_avisos(self):
        self._entrada_coherente()

        call_command('auditar_stock', '--strict')
