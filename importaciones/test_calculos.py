from decimal import Decimal
from datetime import date

from django.test import TestCase

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Proveedor
from importaciones.calculos import comparar_chasis, normalizar_chasis, repartir_costos
from importaciones.models import Embarque, EmbarqueItem, GastoImportacion
from importaciones.services import prorratear_costos, verificar_chasis
from inventario.models import MarcaVehiculo, ModeloVehiculo, Vehiculo


class ImportacionesCalculosTests(TestCase):
    def test_normaliza_y_compara_chasis(self):
        self.assertEqual(normalizar_chasis(' 1hgc-m82633a004352 '), '1HGCM82633A004352')

        resultado = comparar_chasis('1HGCM82633A004352', '1HGCM82633A004352')
        self.assertTrue(resultado.coincide)
        self.assertEqual(resultado.discrepancias, [])

    def test_reparte_costos_proporcionalmente(self):
        lineas = repartir_costos(
            Decimal('300.00'),
            [
                {'id': 1, 'base': Decimal('100.00')},
                {'id': 2, 'base': Decimal('200.00')},
            ],
            criterio='POR_VALOR',
        )

        self.assertEqual(lineas[0]['monto'], Decimal('100.00'))
        self.assertEqual(lineas[1]['monto'], Decimal('200.00'))

    def test_verificar_chasis_y_prorrateo_con_modelos_reales(self):
        proveedor = Proveedor.objects.create(
            nombre='Proveedor Importación',
            razon_social='Proveedor Importación SA',
            documento_identidad='1234567',
            telefono='123',
            email='provimp@test.com',
            direccion='Calle 1',
            ruc='1234567',
            tipo_persona='JURIDICA',
        )
        marca = MarcaVehiculo.objects.create(nombre='Toyota', pais_origen='Japón')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Corolla', estado=True)
        vehiculo = Vehiculo.objects.create(
            proveedor=proveedor,
            nombre='Corolla',
            marca=marca,
            modelo=modelo,
            año=2024,
            codigo_chasis='1HGCM82633A004352',
            costo_compra=Decimal('25000.00'),
            precio_venta=Decimal('30000.00'),
        )
        factura = FacturaComercial.objects.create(
            proveedor=proveedor,
            numero='FAC-IMP-001',
            fecha=date(2026, 1, 5),
            total_declarado=Decimal('1500.00'),
            moneda='USD',
        )
        factura_item = FacturaItem.objects.create(
            factura=factura,
            vehiculo=vehiculo,
            descripcion='Vehículo de prueba',
            cantidad=1,
            precio_unitario=Decimal('1500.00'),
        )
        embarque = Embarque.objects.create(
            referencia_interna='EMB-TEST-001',
            bl_numero='BL-TEST-001',
            fecha_embarque=date(2026, 2, 1),
            destino_final='Asunción',
            estado=Embarque.Estado.PROGRAMADO,
        )
        item = EmbarqueItem.objects.create(
            embarque=embarque,
            factura_item=factura_item,
            cantidad=1,
            chasis_bl='1HGCM82633A004352',
        )
        GastoImportacion.objects.create(
            embarque=embarque,
            tipo=GastoImportacion.Tipo.FLETE,
            descripcion='Flete principal',
            monto=Decimal('100.00'),
            moneda='USD',
            tipo_cambio=Decimal('1'),
        )

        verificacion = verificar_chasis(embarque)
        self.assertTrue(verificacion['ok'])
        self.assertTrue(verificacion['items'][0]['coincide'])

        prorrateado = prorratear_costos(embarque)
        self.assertTrue(prorrateado['ok'])
        self.assertTrue(embarque.gastos_prorrateados)
        item.refresh_from_db()
        self.assertEqual(item.costo_prorrateado, Decimal('100.00'))
