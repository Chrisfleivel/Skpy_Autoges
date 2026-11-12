from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Proveedor
from importaciones.models import Embarque, EmbarqueContenedor, EmbarqueItem, GastoImportacion
from inventario.models import MarcaVehiculo, ModeloVehiculo, Vehiculo


class ImportacionesUiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='uiuser', password='123456', is_superuser=True)
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Importación',
            razon_social='Proveedor Importación SA',
            documento_identidad='1234567',
            telefono='123',
            email='provimp@test.com',
            direccion='Calle 1',
            ruc='1234567',
            tipo_persona='JURIDICA',
        )
        self.marca = MarcaVehiculo.objects.create(nombre='Toyota', pais_origen='Japón')
        self.modelo = ModeloVehiculo.objects.create(marca=self.marca, nombre='Corolla', estado=True)
        self.vehiculo = Vehiculo.objects.create(
            proveedor=self.proveedor,
            nombre='Corolla',
            marca=self.marca,
            modelo=self.modelo,
            año=2024,
            codigo_chasis='1HGCM82633A004352',
            costo_compra=Decimal('25000.00'),
            precio_venta=Decimal('30000.00'),
        )
        self.factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-IMP-UI-001',
            fecha=date(2026, 1, 5),
            total_declarado=Decimal('1500.00'),
            moneda='USD',
        )
        self.item_fact = FacturaItem.objects.create(
            factura=self.factura,
            vehiculo=self.vehiculo,
            descripcion='Vehículo de prueba',
            cantidad=1,
            precio_unitario=Decimal('1500.00'),
        )
        self.embarque = Embarque.objects.create(
            referencia_interna='EMB-UI-001',
            bl_numero='BL-UI-001',
            fecha_embarque=date(2026, 2, 1),
            destino_final='Asunción',
            estado=Embarque.Estado.PROGRAMADO,
        )
        self.contenedor = EmbarqueContenedor.objects.create(
            embarque=self.embarque,
            numero='MEDUKC733517',
            tipo='40HC',
            peso_bruto_kg=Decimal('6030.00'),
        )
        self.embarque_item = EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item_fact,
            cantidad=1,
            chasis_bl='1HGCM82633A004352',
            contenedor=self.contenedor,
        )
        GastoImportacion.objects.create(
            embarque=self.embarque,
            tipo=GastoImportacion.Tipo.FLETE,
            descripcion='Flete principal',
            monto=Decimal('100.00'),
            moneda='USD',
            tipo_cambio=Decimal('1'),
        )

    def test_detalle_embarque_renders(self):
        response = self.client.get(f'/importaciones/embarques/{self.embarque.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Verificación de chasis')
        self.assertContains(response, 'Prorrateo y cierre')

    def test_exportar_resumen_embarque_csv(self):
        response = self.client.get(f'/importaciones/embarques/{self.embarque.pk}/resumen/exportar/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('RESUMEN_EMBARQUE', response.headers.get('Content-Disposition', ''))
