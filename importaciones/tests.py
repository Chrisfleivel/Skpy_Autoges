from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from configuraciones_maestras.models import AgenteTransporte, DespachanteAduana, Proveedor
from importaciones.models import Importacion, ContenedorImportacion, PedidoProveedorImportacion


class CrearAgentesImportacionCommandTests(TestCase):
    def test_crea_agentes_y_asigna_importaciones(self):
        usuario = get_user_model().objects.create_user(username='import-test', password='123456')
        proveedor = Proveedor.objects.create(nombre='Proveedor Test', razon_social='Proveedor Test', ruc='8001234560001')
        importacion = Importacion.objects.create(
            codigo_seguimiento='IMP-TEST-001',
            proveedor=proveedor,
            usuario_creador=usuario,
        )

        out = StringIO()
        call_command('crear_despachante_aduano_agente_transporte', stdout=out)

        importacion.refresh_from_db()
        self.assertTrue(AgenteTransporte.objects.filter(nombre='Agente Transporte Corea Test').exists())
        self.assertTrue(AgenteTransporte.objects.filter(nombre='Agente Transporte Paraguay Test').exists())
        self.assertTrue(DespachanteAduana.objects.filter(nombre='Despachante Aduana Test').exists())
        self.assertIsNotNone(importacion.agente_transporte_origen)
        self.assertIsNotNone(importacion.agente_transporte_destino)
        self.assertIsNotNone(importacion.despachante_aduana)


class ContenedorImportacionTests(TestCase):
    def test_varios_pedidos_de_proveedores_pueden_ir_al_mismo_contenedor(self):
        proveedor_a = Proveedor.objects.create(nombre='Proveedor A', razon_social='Proveedor A', ruc='8001111110001')
        proveedor_b = Proveedor.objects.create(nombre='Proveedor B', razon_social='Proveedor B', ruc='8002222220002')
        contenedor = ContenedorImportacion.objects.create(numero='CNT-TEST-001', estado='pendiente')

        pedido_a = PedidoProveedorImportacion.objects.create(
            contenedor=contenedor,
            proveedor=proveedor_a,
            codigo='PO-001',
            estado='pendiente',
        )
        pedido_b = PedidoProveedorImportacion.objects.create(
            contenedor=contenedor,
            proveedor=proveedor_b,
            codigo='PO-002',
            estado='pendiente',
        )

        self.assertEqual(contenedor.pedidos_proveedor.count(), 2)
        self.assertIn(pedido_a, contenedor.pedidos_proveedor.all())
        self.assertIn(pedido_b, contenedor.pedidos_proveedor.all())
        self.assertEqual(
            list(PedidoProveedorImportacion.objects.filter(proveedor=proveedor_a).values_list('codigo', flat=True)),
            ['PO-001'],
        )
