from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Proveedor
from core.models import TransicionInvalida
from importaciones.models import DespachoAduana, Embarque, GastoImportacion
from importaciones.services import verificar_chasis, prorratear_costos
from inventario.models import MarcaVehiculo, ModeloVehiculo, Vehiculo


class EmbarqueImportacionFase3TestCase(TestCase):
    def setUp(self):
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
        self.factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-IMP-001',
            fecha=date(2026, 1, 5),
            total_declarado=Decimal('1500.00'),
            moneda='USD',
        )
        self.item = FacturaItem.objects.create(
            factura=self.factura,
            descripcion='Kit prueba',
            cantidad=1,
            precio_unitario=Decimal('1500.00'),
        )

    def test_embarque_puede_avanzar_a_embarcado_con_bl_y_fecha(self):
        embarque = Embarque.objects.create(
            referencia_interna='EMB-001',
            bl_numero='BL-001',
            fecha_embarque=date(2026, 2, 1),
            estado=Embarque.Estado.PROGRAMADO,
        )
        embarque.items.create(factura_item=self.item, cantidad=1, chasis_bl='VIN-123')

        embarque.cambiar_estado(Embarque.Estado.EMBARCADO)

        self.assertEqual(embarque.estado, Embarque.Estado.EMBARCADO)

    def test_embarque_no_puede_ir_a_transito_sin_eta(self):
        embarque = Embarque.objects.create(
            referencia_interna='EMB-002',
            bl_numero='BL-002',
            fecha_embarque=date(2026, 2, 1),
            estado=Embarque.Estado.EMBARCADO,
        )
        embarque.items.create(factura_item=self.item, cantidad=1, chasis_bl='VIN-456')

        with self.assertRaises(TransicionInvalida):
            embarque.cambiar_estado(Embarque.Estado.EN_TRANSITO)

    def test_embarque_solo_cierra_si_gastos_prorrateados(self):
        embarque = Embarque.objects.create(
            referencia_interna='EMB-003',
            bl_numero='BL-003',
            fecha_embarque=date(2026, 2, 1),
            eta=date(2026, 2, 15),
            fecha_arribo=date(2026, 2, 16),
            fecha_recepcion=date(2026, 2, 18),
            estado=Embarque.Estado.RECIBIDO,
        )
        embarque.items.create(
            factura_item=self.item,
            cantidad=1,
            chasis_bl='VIN-789',
            costo_prorrateado=Decimal('1500.00'),
        )
        embarque.gastos_prorrateados = True
        embarque.save(update_fields=['gastos_prorrateados'])

        embarque.cambiar_estado(Embarque.Estado.CERRADO)
        self.assertEqual(embarque.estado, Embarque.Estado.CERRADO)

    def test_gasto_importacion_calcula_monto_base(self):
        gasto = GastoImportacion.objects.create(
            embarque=Embarque.objects.create(
                referencia_interna='EMB-004',
                bl_numero='BL-004',
                fecha_embarque=date(2026, 2, 1),
            ),
            tipo=GastoImportacion.Tipo.FLETE,
            descripcion='Flete principal',
            monto=Decimal('100.00'),
            moneda='USD',
            tipo_cambio=Decimal('7.50'),
        )

        self.assertEqual(gasto.monto_base, Decimal('750.00'))

    def test_flujo_operativo_completo_del_embarque(self):
        embarque = Embarque.objects.create(
            referencia_interna='EMB-006',
            bl_numero='BL-006',
            fecha_embarque=date(2026, 2, 1),
            estado=Embarque.Estado.PROGRAMADO,
        )
        item = embarque.items.create(
            factura_item=self.item,
            cantidad=1,
            chasis_bl='VIN-100',
        )
        gasto = GastoImportacion.objects.create(
            embarque=embarque,
            tipo=GastoImportacion.Tipo.FLETE,
            descripcion='Flete principal',
            monto=Decimal('100.00'),
            moneda='USD',
            tipo_cambio=Decimal('1'),
        )

        flujo = embarque.flujo_operativo
        self.assertTrue(flujo['embarque_registrado'])
        self.assertTrue(flujo['costos_cargados'])
        self.assertTrue(flujo['items_asociados'])
        self.assertTrue(flujo['chasis_verificado'])
        self.assertFalse(flujo['prorrateado'])

        embarque.cambiar_estado(Embarque.Estado.EMBARCADO)
        embarque.eta = date(2026, 2, 12)
        embarque.save(update_fields=['eta'])
        embarque.cambiar_estado(Embarque.Estado.EN_TRANSITO)

        embarque.fecha_arribo = date(2026, 2, 13)
        embarque.save(update_fields=['fecha_arribo'])
        embarque.cambiar_estado(Embarque.Estado.ARRIBADO)

        embarque.bl_liberado = True
        embarque.save(update_fields=['bl_liberado'])
        embarque.cambiar_estado(Embarque.Estado.EN_ADUANA)

        DespachoAduana.objects.create(
            embarque=embarque,
            nro_despacho='D-100',
            fecha_oficializacion=date(2026, 2, 14),
            aduana='Aduana Central',
            despachante='Despachante demo',
            canal=DespachoAduana.Canal.VERDE,
        )
        embarque.cambiar_estado(Embarque.Estado.NACIONALIZADO)

        embarque.fecha_recepcion = date(2026, 2, 15)
        embarque.save(update_fields=['fecha_recepcion'])
        embarque.cambiar_estado(Embarque.Estado.RECIBIDO)

        item.costo_prorrateado = Decimal('100.00')
        item.save(update_fields=['costo_prorrateado'])
        embarque.gastos_prorrateados = True
        embarque.save(update_fields=['gastos_prorrateados'])
        self.assertTrue(embarque.flujo_operativo['prorrateado'])

        embarque.cambiar_estado(Embarque.Estado.CERRADO)
        self.assertEqual(embarque.estado, Embarque.Estado.CERRADO)
        self.assertTrue(embarque.flujo_operativo['cerrado'])

    def test_validacion_final_de_integracion_real(self):
        marca = MarcaVehiculo.objects.create(nombre='Toyota', pais_origen='Japón')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Corolla', estado=True)
        vehiculo = Vehiculo.objects.create(
            proveedor=self.proveedor,
            nombre='Corolla test',
            marca=marca,
            modelo=modelo,
            año=2024,
            codigo_chasis='VIN-REAL-001',
            costo_compra=Decimal('25000.00'),
            precio_venta=Decimal('30000.00'),
        )
        self.item.vehiculo = vehiculo
        self.item.save(update_fields=['vehiculo'])

        embarque = Embarque.objects.create(
            referencia_interna='EMB-REAL-001',
            bl_numero='BL-REAL-001',
            fecha_embarque=date(2026, 2, 1),
            estado=Embarque.Estado.PROGRAMADO,
        )
        item = embarque.items.create(
            factura_item=self.item,
            cantidad=1,
            chasis_bl='VIN-REAL-001',
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
        self.assertTrue(embarque.flujo_operativo['items_asociados'])
        self.assertTrue(embarque.flujo_operativo['costos_cargados'])

        resultado = prorratear_costos(embarque)
        self.assertTrue(resultado['ok'])
        self.assertTrue(embarque.gastos_prorrateados)

        item_db = embarque.items.get(pk=item.pk)
        self.assertIsNotNone(item_db.costo_prorrateado)

        item_db.costo_prorrateado = Decimal('50.00')
        item_db.save(update_fields=['costo_prorrateado'])
        self.assertFalse(Embarque.objects.get(pk=embarque.pk).gastos_prorrateados)

    def test_cambios_en_gasto_o_item_invalidan_prorrateo(self):
        embarque = Embarque.objects.create(
            referencia_interna='EMB-005',
            bl_numero='BL-005',
            fecha_embarque=date(2026, 2, 1),
        )
        embarque.gastos_prorrateados = True
        embarque.save(update_fields=['gastos_prorrateados'])

        GastoImportacion.objects.create(
            embarque=embarque,
            tipo=GastoImportacion.Tipo.FLETE,
            descripcion='Flete 1',
            monto=Decimal('100.00'),
            moneda='USD',
            tipo_cambio=Decimal('1'),
        )
        self.assertFalse(Embarque.objects.get(pk=embarque.pk).gastos_prorrateados)

        embarque.gastos_prorrateados = True
        embarque.save(update_fields=['gastos_prorrateados'])
        item = embarque.items.create(
            factura_item=self.item,
            cantidad=1,
            chasis_bl='VIN-555',
        )
        self.assertFalse(Embarque.objects.get(pk=embarque.pk).gastos_prorrateados)

        item.delete()
        self.assertFalse(Embarque.objects.get(pk=embarque.pk).gastos_prorrateados)
