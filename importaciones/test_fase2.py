"""
Tests de la Fase 2: soporte multi-contenedor por embarque y sección de documentos.

Un mismo B/L puede traer más de un contenedor, por eso los datos del
contenedor viven en `EmbarqueContenedor` y cada ítem del embarque se asigna
a un contenedor concreto.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Proveedor
from importaciones.models import (
    DocumentoAdjunto,
    Embarque,
    EmbarqueContenedor,
    EmbarqueItem,
)


class EmbarqueContenedorTestCase(TestCase):
    """Base con los datos mínimos de un embarque y sus contenedores."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='embarque_user', password='123456', is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Importación',
            razon_social='Proveedor Importación SA',
            tipo_persona='JURIDICA',
        )
        self.factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-F2-001',
            fecha=date(2026, 1, 5),
            total_declarado=Decimal('15000.00'),
            moneda='USD',
        )
        self.item_fact = FacturaItem.objects.create(
            factura=self.factura,
            descripcion='Hyundai Tucson',
            cantidad=4,
            precio_unitario=Decimal('2500.00'),
        )
        self.embarque = Embarque.objects.create(
            referencia_interna='EMB-F2-001',
            bl_numero='MEDUKC733517',
            shipper='HYUNDAI MOTOR COMPANY',
            consignatario='RODRIGO DANIEL OCAMPOS PEREZ',
            notify='TO ORDER',
            puerto_carga='INCHEON, KOREA',
            puerto_descarga='IQUIQUE, CHILE',
            destino_final='ASUNCION, PARAGUAY',
            fecha_embarque=date(2026, 8, 20),
            estado=Embarque.Estado.PROGRAMADO,
        )

    def _crear_contenedor(self, numero='MEDUKC733517', **kwargs):
        return EmbarqueContenedor.objects.create(
            embarque=self.embarque, numero=numero, tipo='40HC', **kwargs)


class EmbarqueMultiContenedorTests(EmbarqueContenedorTestCase):
    """Un embarque admite más de un contenedor."""

    def test_un_embarque_acepta_varios_contenedores(self):
        primero = self._crear_contenedor('MEDUKC733517', peso_bruto_kg=Decimal('6030.00'))
        segundo = self._crear_contenedor('MEDUKC733518', peso_bruto_kg=Decimal('5820.00'))

        self.assertEqual(self.embarque.contenedores.count(), 2)
        self.assertEqual(self.embarque.cantidad_contenedores, 2)
        self.assertNotEqual(primero.pk, segundo.pk)

    def test_no_se_puede_repetir_el_numero_de_contenedor_en_el_mismo_embarque(self):
        self._crear_contenedor('MEDUKC733517')

        repetido = EmbarqueContenedor(embarque=self.embarque, numero='MEDUKC733517')
        with self.assertRaises(Exception):
            repetido.full_clean()

    def test_el_mismo_numero_puede_repetirse_en_otro_embarque(self):
        self._crear_contenedor('MEDUKC733517')
        otro = Embarque.objects.create(
            referencia_interna='EMB-F2-002',
            bl_numero='OTRO-001',
            estado=Embarque.Estado.PROGRAMADO,
        )

        contenedor = EmbarqueContenedor.objects.create(
            embarque=otro, numero='MEDUKC733517', tipo='40HC')

        self.assertEqual(contenedor.embarque, otro)

    def test_los_contenedores_reportan_las_unidades_cargadas(self):
        contenedor = self._crear_contenedor()
        EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item_fact,
            contenedor=contenedor,
            cantidad=2,
            chasis_bl='KMHJU81VBBU197503',
        )

        self.assertEqual(contenedor.unidades, 2)


class EmbarqueItemContenedorTests(EmbarqueContenedorTestCase):
    """Cada ítem del embarque pertenece a un contenedor del mismo embarque."""

    def test_el_item_se_asigna_a_un_contenedor_del_embarque(self):
        contenedor = self._crear_contenedor()

        item = EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item_fact,
            contenedor=contenedor,
            cantidad=2,
            chasis_bl='KMHJU81VBBU197503',
        )

        self.assertEqual(item.contenedor, contenedor)
        self.assertEqual(contenedor.items.count(), 1)

    def test_no_se_puede_asignar_un_contenedor_de_otro_embarque(self):
        contenedor = self._crear_contenedor()
        otro = Embarque.objects.create(
            referencia_interna='EMB-F2-003',
            bl_numero='OTRO-002',
            estado=Embarque.Estado.PROGRAMADO,
        )
        contenedor_ajeno = EmbarqueContenedor.objects.create(
            embarque=otro, numero='AJENO-001', tipo='20ft')

        item = EmbarqueItem(
            embarque=self.embarque,
            factura_item=self.item_fact,
            contenedor=contenedor_ajeno,
            cantidad=1,
        )
        with self.assertRaises(Exception):
            item.full_clean()

    def test_la_misma_linea_puede_repartirse_en_dos_contenedores(self):
        primero = self._crear_contenedor('CONT-A')
        segundo = self._crear_contenedor('CONT-B')

        item_a = EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item_fact,
            contenedor=primero,
            cantidad=2,
            chasis_bl='KMHJU81VBBU197503',
        )
        item_b = EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item_fact,
            contenedor=segundo,
            cantidad=2,
            chasis_bl='KMHJU81VBBU197504',
        )

        self.assertNotEqual(item_a.pk, item_b.pk)
        self.assertEqual(self.embarque.items.count(), 2)


class EmbarqueFormularioTests(EmbarqueContenedorTestCase):
    """Formulario de embarque con formset de contenedores."""

    def _post_embarque(self, **overrides):
        datos = {
            'referencia_interna': 'EMB-F2-NUEVO',
            'bl_numero': 'BL-F2-NUEVO',
            'flete_prepago': 'on',
            'shipper': 'HYUNDAI MOTOR COMPANY',
            'consignatario': 'RODRIGO DANIEL OCAMPOS PEREZ',
            'notify': 'TO ORDER',
            'puerto_carga': 'INCHEON, KOREA',
            'puerto_descarga': 'IQUIQUE, CHILE',
            'destino_final': 'ASUNCION, PARAGUAY',
            'contenedores-TOTAL_FORMS': '2',
            'contenedores-INITIAL_FORMS': '0',
            'contenedores-MIN_NUM_FORMS': '0',
            'contenedores-MAX_NUM_FORMS': '1000',
            'contenedores-0-numero': 'MEDUKC733517',
            'contenedores-0-tipo': '40HC',
            'contenedores-0-sello': 'SL-001',
            'contenedores-0-peso_bruto_kg': '6030.00',
            'contenedores-0-volumen_m3': '',
            'contenedores-0-bultos': '',
            'contenedores-0-observaciones': '',
            'contenedores-1-numero': 'MEDUKC733518',
            'contenedores-1-tipo': '40HC',
            'contenedores-1-sello': '',
            'contenedores-1-peso_bruto_kg': '',
            'contenedores-1-volumen_m3': '',
            'contenedores-1-bultos': '',
            'contenedores-1-observaciones': '',
        }
        datos.update(overrides)
        return self.client.post(reverse('crear_embarque'), datos)

    def test_crea_el_embarque_con_dos_contenedores(self):
        respuesta = self._post_embarque()

        self.assertEqual(respuesta.status_code, 302)
        embarque = Embarque.objects.get(referencia_interna='EMB-F2-NUEVO')
        self.assertEqual(embarque.contenedores.count(), 2)
        self.assertEqual(
            sorted(embarque.contenedores.values_list('numero', flat=True)),
            ['MEDUKC733517', 'MEDUKC733518'],
        )

    def test_no_crea_el_embarque_con_contenedores_repetidos(self):
        respuesta = self._post_embarque(**{
            'contenedores-1-numero': 'MEDUKC733517',
        })

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Embarque.objects.filter(referencia_interna='EMB-F2-NUEVO').exists())

    def test_editar_agrega_un_contenedor(self):
        contenedor = self._crear_contenedor('CONT-001')

        respuesta = self.client.post(reverse('editar_embarque', args=[self.embarque.pk]), {
            'referencia_interna': 'EMB-F2-001',
            'bl_numero': 'MEDUKC733517',
            'flete_prepago': 'on',
            'contenedores-TOTAL_FORMS': '2',
            'contenedores-INITIAL_FORMS': '1',
            'contenedores-MIN_NUM_FORMS': '0',
            'contenedores-MAX_NUM_FORMS': '1000',
            'contenedores-0-id': contenedor.pk,
            'contenedores-0-numero': 'CONT-001',
            'contenedores-0-tipo': '40HC',
            'contenedores-0-sello': '',
            'contenedores-0-peso_bruto_kg': '',
            'contenedores-0-volumen_m3': '',
            'contenedores-0-bultos': '',
            'contenedores-0-observaciones': '',
            'contenedores-1-numero': 'CONT-002',
            'contenedores-1-tipo': '40HC',
            'contenedores-1-sello': '',
            'contenedores-1-peso_bruto_kg': '',
            'contenedores-1-volumen_m3': '',
            'contenedores-1-bultos': '',
            'contenedores-1-observaciones': '',
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.embarque.contenedores.count(), 2)


class EmbarqueFormularioRenderTests(EmbarqueContenedorTestCase):
    """Las pantallas de alta y edición muestran el formset de contenedores."""

    def test_el_formulario_de_alta_muestra_el_formset_de_contenedores(self):
        respuesta = self.client.get(reverse('crear_embarque'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Contenedores del embarque')
        self.assertContains(respuesta, 'contenedores-0-numero')
        self.assertContains(respuesta, 'name="bl_numero"')

    def test_el_formulario_de_edicion_muestra_los_contenedores_cargados(self):
        self._crear_contenedor('MEDUKC733517')

        respuesta = self.client.get(reverse('editar_embarque', args=[self.embarque.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'MEDUKC733517')

    def test_el_detalle_ofrece_el_selector_de_contenedores_para_los_items(self):
        self._crear_contenedor('MEDUKC733517')

        respuesta = self.client.get(reverse('detalle_embarque', args=[self.embarque.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'MEDUKC733517')


class EmbarqueContenedorVistasTests(EmbarqueContenedorTestCase):
    """Alta y baja de contenedores desde la pantalla de detalle."""

    def test_agrega_un_contenedor_desde_el_detalle(self):
        respuesta = self.client.post(reverse('agregar_contenedor_embarque', args=[self.embarque.pk]), {
            'numero': 'MEDUKC733517',
            'tipo': '40HC',
            'sello': 'SL-001',
            'peso_bruto_kg': '6030.00',
            'volumen_m3': '',
            'bultos': '',
            'observaciones': '',
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.embarque.contenedores.count(), 1)

    def test_no_puede_eliminar_un_contenedor_con_items(self):
        contenedor = self._crear_contenedor()
        EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item_fact,
            contenedor=contenedor,
            cantidad=1,
            chasis_bl='KMHJU81VBBU197503',
        )

        respuesta = self.client.post(
            reverse('eliminar_contenedor_embarque', args=[self.embarque.pk, contenedor.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(EmbarqueContenedor.objects.filter(pk=contenedor.pk).exists())

    def test_elimina_un_contenedor_vacio(self):
        contenedor = self._crear_contenedor()

        respuesta = self.client.post(
            reverse('eliminar_contenedor_embarque', args=[self.embarque.pk, contenedor.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(EmbarqueContenedor.objects.filter(pk=contenedor.pk).exists())

    def test_agrega_un_item_asignando_el_contenedor(self):
        contenedor = self._crear_contenedor()

        respuesta = self.client.post(reverse('agregar_item_embarque', args=[self.embarque.pk]), {
            'factura_item': self.item_fact.pk,
            'contenedor': contenedor.pk,
            'cantidad': '1',
            'peso_kg': '',
            'chasis_bl': 'KMHJU81VBBU197503',
        })

        self.assertEqual(respuesta.status_code, 302)
        item = EmbarqueItem.objects.get(embarque=self.embarque)
        self.assertEqual(item.contenedor, contenedor)

    def test_no_agrega_un_item_sin_contenedor(self):
        self._crear_contenedor()

        respuesta = self.client.post(reverse('agregar_item_embarque', args=[self.embarque.pk]), {
            'factura_item': self.item_fact.pk,
            'contenedor': '',
            'cantidad': '1',
            'peso_kg': '',
            'chasis_bl': 'KMHJU81VBBU197503',
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(EmbarqueItem.objects.filter(embarque=self.embarque).exists())


class EmbarqueDocumentosTests(EmbarqueContenedorTestCase):
    """Sección de documentos adjuntos del embarque."""

    def test_adjunta_un_documento_al_embarque(self):
        archivo = SimpleUploadedFile('bl.pdf', b'%PDF-1.4 contenido', content_type='application/pdf')

        respuesta = self.client.post(reverse('agregar_documento_embarque', args=[self.embarque.pk]), {
            'tipo': DocumentoAdjunto.Tipo.BL,
            'archivo': archivo,
            'descripcion': 'B/L original',
        })

        self.assertEqual(respuesta.status_code, 302)
        documento = DocumentoAdjunto.objects.get(embarque=self.embarque)
        self.assertEqual(documento.tipo, DocumentoAdjunto.Tipo.BL)
        self.assertEqual(documento.descripcion, 'B/L original')

    def test_elimina_un_documento_del_embarque(self):
        documento = DocumentoAdjunto.objects.create(
            embarque=self.embarque,
            tipo=DocumentoAdjunto.Tipo.BL,
            archivo=SimpleUploadedFile('bl.pdf', b'%PDF-1.4'),
            descripcion='B/L original',
        )

        respuesta = self.client.post(
            reverse('eliminar_documento_embarque', args=[self.embarque.pk, documento.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(DocumentoAdjunto.objects.filter(pk=documento.pk).exists())

    def test_el_detalle_muestra_los_contenedores_y_los_documentos(self):
        self._crear_contenedor('MEDUKC733517')
        DocumentoAdjunto.objects.create(
            embarque=self.embarque,
            tipo=DocumentoAdjunto.Tipo.BL,
            archivo=SimpleUploadedFile('bl.pdf', b'%PDF-1.4'),
            descripcion='B/L original',
        )

        respuesta = self.client.get(reverse('detalle_embarque', args=[self.embarque.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'MEDUKC733517')
        self.assertContains(respuesta, 'Documentos del embarque')
        self.assertContains(respuesta, 'B/L original')
