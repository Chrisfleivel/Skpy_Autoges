import datetime
from decimal import Decimal

from django.test import TestCase

from compras.models import FacturaComercial
from configuraciones_maestras.models import Proveedor
from finanzas.models import PagoExterior
from finanzas.services import registrar_pago_exterior, rechazar_pago, sincronizar_factura


class FinanzasServicesTests(TestCase):
    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            razon_social='Proveedor Test SRL',
            ruc='1234567-1',
            estado=True,
        )
        self.factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='F-1001',
            fecha=datetime.date.today(),
            moneda='USD',
            total_declarado=Decimal('1000.00'),
            estado=FacturaComercial.Estado.CONFIRMADA,
        )

    def test_registrar_pago_exterior_actualiza_factura(self):
        pago = registrar_pago_exterior(
            self.factura,
            fecha_operacion=datetime.date.today(),
            importe=Decimal('700.00'),
            comision=Decimal('25.00'),
            referencia_op='OP-001',
            ordenante='Empresa',
        )

        self.factura.refresh_from_db()
        self.assertEqual(pago.estado, PagoExterior.Estado.ORDENADO)
        self.assertEqual(self.factura.monto_pagado, Decimal('700.00'))
        self.assertEqual(self.factura.estado, FacturaComercial.Estado.PAGO_PARCIAL)

    def test_rechazar_pago_reversa_factura(self):
        pago = registrar_pago_exterior(
            self.factura,
            fecha_operacion=datetime.date.today(),
            importe=Decimal('500.00'),
            comision=Decimal('10.00'),
            referencia_op='OP-002',
            ordenante='Empresa',
        )
        pago.motivo_rechazo = 'Rechazado por banco'

        rechazar_pago(pago, motivo='Rechazado por banco')

        pago.refresh_from_db()
        self.factura.refresh_from_db()
        self.assertEqual(pago.estado, PagoExterior.Estado.RECHAZADO)
        self.assertEqual(self.factura.estado, FacturaComercial.Estado.CONFIRMADA)

    def test_sincronizar_factura_paga_cuando_llega_al_total(self):
        registrar_pago_exterior(
            self.factura,
            fecha_operacion=datetime.date.today(),
            importe=Decimal('1000.00'),
            comision=Decimal('0.00'),
            referencia_op='OP-003',
            ordenante='Empresa',
        )

        self.factura.refresh_from_db()
        self.assertEqual(self.factura.estado, FacturaComercial.Estado.PAGADA)
        self.assertEqual(self.factura.monto_pagado, Decimal('1000.00'))
