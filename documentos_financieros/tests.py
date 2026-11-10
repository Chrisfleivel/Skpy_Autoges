from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from configuraciones_maestras.models import Moneda, Proveedor
from contabilidad.models import Asiento, CuentaContable, MovimientoContable
from .models import Autofactura


class AutofacturaContableTests(TestCase):
    def test_autofactura_aprobada_registra_asiento_contable(self):
        moneda = Moneda.objects.create(codigo='PYG', nombre='Guaraní')
        proveedor = Proveedor.objects.create(nombre='Proveedor Test', razon_social='Proveedor Test')

        cuenta_proveedores = CuentaContable.objects.create(
            codigo='2.1.01',
            nombre='Proveedores',
            tipo='P',
            moneda=moneda,
        )
        cuenta_compras = CuentaContable.objects.create(
            codigo='5.1.01',
            nombre='Compras',
            tipo='E',
            moneda=moneda,
        )

        factura = Autofactura.objects.create(
            tipo_documento='autofactura',
            timbrado='12345678',
            establecimiento='001',
            punto_expedicion='001',
            numero_documento='0000001',
            monto_total=Decimal('1500.00'),
            estado_sifen='aprobado',
            proveedor=proveedor,
            tipo_factura='contado',
        )

        asiento = factura.asientos.first()

        self.assertIsNotNone(asiento)
        self.assertEqual(asiento.descripcion, f'Compra autofactura {factura.numero_documento}')
        self.assertEqual(asiento.movimientos.count(), 2)
        self.assertTrue(
            asiento.movimientos.filter(cuenta=cuenta_compras, debe=Decimal('1500.00')).exists()
        )
        self.assertTrue(
            asiento.movimientos.filter(cuenta=cuenta_proveedores, haber=Decimal('1500.00')).exists()
        )
