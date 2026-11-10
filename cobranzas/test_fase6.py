import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from cobranzas.models import Caja, Pago
from cobranzas.services import abrir_caja, cerrar_caja, registrar_pago_en_caja
from configuraciones_maestras.models import Sucursal
from seguridad_usuarios.models import Empleado


class CobranzasFase6Tests(TestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(nombre='Sucursal Fase 6', direccion='Ruta 7')
        self.empleado = Empleado.objects.create(
            nombre='Fase',
            apellidos='Seis',
            documento_identidad='fase6',
            estado=True,
        )
        self.caja = Caja.objects.create(
            sucursal=self.sucursal,
            nombre='Caja Fase 6',
            estado='cerrada',
            saldo_inicial=Decimal('1000.00'),
            saldo_actual=Decimal('1000.00'),
            empleado_actual=None,
        )

    def test_abrir_caja_valida_monto_inicial_y_asigna_empleado(self):
        caja = abrir_caja(
            self.caja,
            empleado=self.empleado,
            monto_inicial=Decimal('2500.00'),
            observaciones='Apertura de prueba',
        )

        self.assertEqual(caja.estado, 'abierta')
        self.assertEqual(caja.empleado_actual, self.empleado)
        self.assertEqual(caja.saldo_actual, Decimal('2500.00'))

    def test_registrar_pago_en_caja_actualiza_saldo_y_estado(self):
        caja = abrir_caja(self.caja, empleado=self.empleado, monto_inicial=Decimal('500.00'))

        pago = registrar_pago_en_caja(
            caja=caja,
            empleado=self.empleado,
            sucursal=self.sucursal,
            monto=Decimal('350.00'),
            metodo_pago='Efectivo',
        )

        caja.refresh_from_db()
        self.assertEqual(pago.estado, 'confirmado')
        self.assertEqual(pago.caja, caja)
        self.assertEqual(caja.saldo_actual, Decimal('850.00'))

    def test_cerrar_caja_calcula_diferencia_y_no_permite_caja_cerrada(self):
        caja = abrir_caja(self.caja, empleado=self.empleado, monto_inicial=Decimal('1000.00'))
        registrar_pago_en_caja(
            caja=caja,
            empleado=self.empleado,
            sucursal=self.sucursal,
            monto=Decimal('200.00'),
            metodo_pago='Transferencia',
        )

        cierre = cerrar_caja(
            caja=caja,
            empleado=self.empleado,
            monto_real=Decimal('1180.00'),
            observaciones='Arqueo final',
        )

        self.assertEqual(cierre.monto_esperado, Decimal('1200.00'))
        self.assertEqual(cierre.monto_real, Decimal('1180.00'))
        self.assertEqual(cierre.diferencia, Decimal('-20.00'))
        self.assertEqual(caja.estado, 'cerrada')

        with self.assertRaises(ValidationError):
            cerrar_caja(
                caja=caja,
                empleado=self.empleado,
                monto_real=Decimal('1000.00'),
            )
