from decimal import Decimal

from django.test import SimpleTestCase

from inventario.calculos import asignar_reserva, costo_promedio_ponderado, unidades_a_reponer


class InventarioFase2TestCase(SimpleTestCase):
    def test_costo_promedio_ponderado_primera_entrada(self):
        self.assertEqual(costo_promedio_ponderado(0, None, 10, Decimal('30')), Decimal('30.0000'))

    def test_costo_promedio_ponderado_con_stock_preexistente(self):
        self.assertEqual(costo_promedio_ponderado(10, Decimal('30'), 10, Decimal('40')), Decimal('35.0000'))
        self.assertEqual(costo_promedio_ponderado(10, Decimal('30'), 5, Decimal('36')), Decimal('32.0000'))

    def test_costo_promedio_ponderado_redondea_a_cuatro_decimales(self):
        self.assertEqual(costo_promedio_ponderado(10, Decimal('30'), 3, Decimal('31')), Decimal('30.2308'))

    def test_asignar_reserva_usa_orden_de_preferencia(self):
        self.assertEqual(asignar_reserva(5, [('A', 3), ('B', 8), ('C', 20)]), [('B', 5)])
        self.assertEqual(asignar_reserva(5, [('principal', 6), ('otro', 50)]), [('principal', 5)])

    def test_asignar_reserva_reparte_si_ninguno_cubre(self):
        self.assertEqual(asignar_reserva(10, [('A', 4), ('B', 3), ('C', 5)]), [('A', 4), ('B', 3), ('C', 3)])

    def test_asignar_reserva_valida_errores(self):
        with self.assertRaises(ValueError):
            asignar_reserva(0, [('A', 4)])
        with self.assertRaises(ValueError):
            asignar_reserva(10, [('A', 4), ('B', 3)])

    def test_unidades_a_reponer(self):
        self.assertEqual(unidades_a_reponer(10, 3), 7)
        self.assertEqual(unidades_a_reponer(10, 10), 0)
        self.assertEqual(unidades_a_reponer(10, 25), 0)
