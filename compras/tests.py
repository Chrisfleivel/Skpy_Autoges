from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Proveedor


class FacturaComercialTestCase(TestCase):
    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            razon_social='Proveedor Test SA',
            documento_identidad='1234567',
            telefono='123',
            email='prov@test.com',
            direccion='Calle 1',
            ruc='1234567',
            tipo_persona='JURIDICA',
        )

    def test_factura_confirma_si_total_coincide_con_items(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-001',
            fecha='2026-01-01',
            total_declarado=Decimal('100.00'),
            moneda='USD',
        )

        FacturaItem.objects.create(
            factura=factura,
            descripcion='Item prueba',
            cantidad=1,
            precio_unitario=Decimal('100.00'),
            vehiculo_id=None,
            repuesto_id=None,
        )

        factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)
        self.assertEqual(factura.estado, FacturaComercial.Estado.CONFIRMADA)

    def test_factura_no_puede_confirmarse_si_total_no_coincide(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-002',
            fecha='2026-01-01',
            total_declarado=Decimal('200.00'),
            moneda='USD',
        )

        FacturaItem.objects.create(
            factura=factura,
            descripcion='Item prueba',
            cantidad=1,
            precio_unitario=Decimal('100.00'),
            vehiculo_id=None,
            repuesto_id=None,
        )

        with self.assertRaises(Exception):
            factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)
