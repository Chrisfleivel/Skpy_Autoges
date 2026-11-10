import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from cobranzas.models import Caja
from configuraciones_maestras.models import Sucursal
from seguridad_usuarios.models import Empleado
from ventas.models import Venta
from ventas.services import registrar_cobro_venta


class VentasFase4Tests(TestCase):
    def setUp(self):
        self.sucursal = Sucursal.objects.create(nombre='Sucursal Norte', direccion='Av. Siempre Viva 123')
        self.empleado = Empleado.objects.create(
            nombre='Ana',
            apellidos='Gómez',
            documento_identidad='1234567',
            estado=True,
        )
        self.caja = Caja.objects.create(
            sucursal=self.sucursal,
            nombre='Caja 1',
            estado='abierta',
            saldo_actual=Decimal('0.00'),
            empleado_actual=self.empleado,
            saldo_inicial=Decimal('0.00'),
        )
        self.venta = Venta.objects.create(
            numero='V-1001',
            cliente='Cliente Demo',
            total=Decimal('1000.00'),
            moneda='PYG',
            estado='PENDIENTE_COBRO',
            sucursal=self.sucursal,
            empleado=self.empleado,
            caja=self.caja,
        )

    def test_registrar_cobro_venta_abre_caja_y_actualiza_estado(self):
        pago = registrar_cobro_venta(
            self.venta,
            caja=self.caja,
            empleado=self.empleado,
            sucursal=self.sucursal,
            monto=Decimal('400.00'),
            metodo_pago='EFECTIVO',
        )

        self.venta.refresh_from_db()
        self.caja.refresh_from_db()

        self.assertEqual(pago.monto, Decimal('400.00'))
        self.assertEqual(self.venta.monto_pagado, Decimal('400.00'))
        self.assertEqual(self.venta.estado, 'PENDIENTE_COBRO')
        self.assertEqual(self.caja.saldo_actual, Decimal('400.00'))

        registrar_cobro_venta(
            self.venta,
            caja=self.caja,
            empleado=self.empleado,
            sucursal=self.sucursal,
            monto=Decimal('600.00'),
            metodo_pago='TRANSFERENCIA',
        )

        self.venta.refresh_from_db()
        self.assertEqual(self.venta.monto_pagado, Decimal('1000.00'))
        self.assertEqual(self.venta.estado, 'PAGADA')

    def test_registrar_cobro_venta_rechaza_caja_cerrada(self):
        self.caja.estado = 'cerrada'
        self.caja.save(update_fields=['estado'])

        with self.assertRaises(ValidationError):
            registrar_cobro_venta(
                self.venta,
                caja=self.caja,
                empleado=self.empleado,
                sucursal=self.sucursal,
                monto=Decimal('100.00'),
                metodo_pago='EFECTIVO',
            )

    def test_registrar_cobro_venta_no_permite_monto_superior_al_total(self):
        with self.assertRaises(ValidationError):
            registrar_cobro_venta(
                self.venta,
                caja=self.caja,
                empleado=self.empleado,
                sucursal=self.sucursal,
                monto=Decimal('1500.00'),
                metodo_pago='EFECTIVO',
            )
