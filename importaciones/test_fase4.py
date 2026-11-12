"""
Tests de la Fase 4: conciliación informativa de los documentos de importación.

La conciliación compara la factura comercial, el B/L con sus contenedores y
la liquidación con su pago. Es informativa: nunca bloquea la carga de los
documentos, solo señala con semáforos qué falta y qué no cuadra.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Moneda, OrdenPagoExterior, Proveedor
from finanzas.models import PagoExterior
from importaciones.conciliacion import (
    Conciliacion,
    EstadoConciliacion,
    conciliar_factura,
    conciliar_facturas,
)
from importaciones.models import (
    DocumentoAdjunto,
    Embarque,
    EmbarqueContenedor,
    EmbarqueItem,
)


class ConciliacionTestCase(TestCase):
    """Base con una factura, un embarque con contenedor y una liquidación."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='conciliacion_user', password='123456', is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

        Moneda.ensure_defaults()
        self.proveedor = Proveedor.objects.create(
            nombre='SKPY Trading',
            razon_social='SKPY Trading Co. Ltd.',
            tipo_persona='JURIDICA',
        )
        self.factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='20260826',
            fecha=date(2026, 8, 26),
            moneda='USD',
            total_declarado=Decimal('8000.00'),
        )
        self.item = FacturaItem.objects.create(
            factura=self.factura,
            descripcion='Hyundai Tucson',
            cantidad=2,
            precio_unitario=Decimal('4000.00'),
            chasis='KMHJU81VBBU197503',
        )
        self.factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)

        self.embarque = Embarque.objects.create(
            referencia_interna='EMB-F4-001',
            bl_numero='MEDUKC733517',
            destino_final='ASUNCION, PARAGUAY',
            fecha_embarque=date(2026, 8, 20),
            estado=Embarque.Estado.PROGRAMADO,
        )
        self.contenedor = EmbarqueContenedor.objects.create(
            embarque=self.embarque, numero='MEDUKC733517', tipo='40HC')
        self.detalle = EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item,
            contenedor=self.contenedor,
            cantidad=2,
            chasis_bl='KMHJU81VBBU197503',
        )
        DocumentoAdjunto.objects.create(
            embarque=self.embarque,
            tipo=DocumentoAdjunto.Tipo.BL,
            archivo=SimpleUploadedFile('bl.pdf', b'%PDF-1.4'),
            descripcion='B/L original',
        )

        self.orden = OrdenPagoExterior.objects.create(
            tipo_documento_remitente='RUC',
            numero_documento_remitente='8001234560001',
            remitente_nombre='SKPY Trading',
            forma_pago='TRANSFERENCIA',
            moneda=Moneda.objects.get(codigo='USD'),
            importe_orden=Decimal('8000.00'),
            comision_orden=Decimal('50.00'),
            referencia_op='136294',
            fecha_operacion=date(2026, 8, 26),
            ordenante='SKPY Trading S.A.',
            beneficiario='HYUNDAI MOTOR COMPANY',
            factura=self.factura,
        )

    def _hallazgo(self, conciliacion: Conciliacion, concepto: str):
        return next(h for h in conciliacion.hallazgos if h.concepto == concepto)


class ConciliacionCalculosTests(ConciliacionTestCase):
    """Cálculo de los semáforos de cada verificación."""

    def test_sin_pago_registrado_la_liquidacion_queda_para_revisar(self):
        conciliacion = conciliar_factura(self.factura)

        liquidacion = self._hallazgo(conciliacion, 'Liquidación')
        self.assertEqual(liquidacion.estado, EstadoConciliacion.OK)

        pago = self._hallazgo(conciliacion, 'Pago registrado')
        self.assertEqual(pago.estado, EstadoConciliacion.ATENCION)

    def test_con_pago_registrado_la_factura_queda_cancelada(self):
        self._registrar_pago()

        conciliacion = conciliar_factura(self.factura)

        pago = self._hallazgo(conciliacion, 'Pago registrado')
        self.assertEqual(pago.estado, EstadoConciliacion.OK)

        importe = self._hallazgo(conciliacion, 'Importe')
        self.assertEqual(importe.estado, EstadoConciliacion.OK)

        moneda = self._hallazgo(conciliacion, 'Moneda')
        self.assertEqual(moneda.estado, EstadoConciliacion.OK)

    def test_detecta_unidad_embarcada_de_mas(self):
        self.detalle.cantidad = 3
        self.detalle.save()

        conciliacion = conciliar_factura(self.factura)

        unidades = self._hallazgo(conciliacion, 'Unidades')
        self.assertEqual(unidades.estado, EstadoConciliacion.DIFERENCIA)
        self.assertEqual(conciliacion.estado, EstadoConciliacion.DIFERENCIA)

    def test_detecta_unidades_faltantes_por_embarcar(self):
        self.detalle.cantidad = 1
        self.detalle.save()

        conciliacion = conciliar_factura(self.factura)

        unidades = self._hallazgo(conciliacion, 'Unidades')
        self.assertEqual(unidades.estado, EstadoConciliacion.ATENCION)
        self.assertIn('Faltan 1 unidades', unidades.detalle)

    def test_detecta_chasis_de_la_factura_que_no_estan_en_el_bl(self):
        self.detalle.chasis_bl = 'OTROCHASIS999999999'
        self.detalle.save()

        conciliacion = conciliar_factura(self.factura)

        chasis = self._hallazgo(conciliacion, 'Chasis')
        self.assertEqual(chasis.estado, EstadoConciliacion.DIFERENCIA)

    def test_detecta_contenedor_provisorio(self):
        self.contenedor.numero = 'SIN-DEFINIR'
        self.contenedor.save()

        conciliacion = conciliar_factura(self.factura)

        contenedores = self._hallazgo(conciliacion, 'Contenedores')
        self.assertEqual(contenedores.estado, EstadoConciliacion.ATENCION)
        self.assertIn('SIN-DEFINIR', contenedores.detalle)

    def test_detecta_embarque_sin_bl_adjunto(self):
        DocumentoAdjunto.objects.filter(embarque=self.embarque).delete()

        conciliacion = conciliar_factura(self.factura)

        documento = self._hallazgo(conciliacion, 'Documento B/L')
        self.assertEqual(documento.estado, EstadoConciliacion.ATENCION)

    def test_detecta_pago_en_moneda_distinta(self):
        self._registrar_pago(moneda='PYG')

        conciliacion = conciliar_factura(self.factura)

        moneda = self._hallazgo(conciliacion, 'Moneda')
        self.assertEqual(moneda.estado, EstadoConciliacion.DIFERENCIA)

    def test_detecta_pago_parcial(self):
        self._registrar_pago(importe=Decimal('1000.00'))

        conciliacion = conciliar_factura(self.factura)

        importe = self._hallazgo(conciliacion, 'Importe')
        self.assertEqual(importe.estado, EstadoConciliacion.ATENCION)
        self.assertIn('saldo pendiente', importe.detalle)

    def test_detecta_comision_sin_imputar_en_el_embarque(self):
        self._registrar_pago(comision=Decimal('50.00'))

        conciliacion = conciliar_factura(self.factura)

        comision = self._hallazgo(conciliacion, 'Comisión bancaria')
        self.assertEqual(comision.estado, EstadoConciliacion.ATENCION)

    def test_comision_imputada_al_embarque_queda_verde(self):
        self._registrar_pago(comision=Decimal('50.00'), imputar_comision=True)

        conciliacion = conciliar_factura(self.factura)

        comision = self._hallazgo(conciliacion, 'Comisión bancaria')
        self.assertEqual(comision.estado, EstadoConciliacion.OK)

    def test_factura_sin_embarque_ni_liquidacion_queda_pendiente(self):
        otra = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='20260901',
            fecha=date(2026, 9, 1),
            moneda='USD',
            total_declarado=Decimal('1000.00'),
        )

        conciliacion = conciliar_factura(otra)

        embarque = self._hallazgo(conciliacion, 'Embarque')
        liquidacion = self._hallazgo(conciliacion, 'Liquidación')
        self.assertEqual(embarque.estado, EstadoConciliacion.PENDIENTE)
        self.assertEqual(liquidacion.estado, EstadoConciliacion.PENDIENTE)
        self.assertEqual(conciliacion.estado, EstadoConciliacion.PENDIENTE)

    def test_la_conciliacion_no_guarda_nada_en_la_base(self):
        """La conciliación es de lectura: no crea ni modifica documentos."""
        antes = (
            PagoExterior.objects.count(),
            OrdenPagoExterior.objects.count(),
            Embarque.objects.count(),
            EmbarqueItem.objects.count(),
        )

        conciliar_factura(self.factura)
        conciliar_facturas()

        despues = (
            PagoExterior.objects.count(),
            OrdenPagoExterior.objects.count(),
            Embarque.objects.count(),
            EmbarqueItem.objects.count(),
        )
        self.assertEqual(antes, despues)

    def test_conciliar_facturas_devuelve_una_conciliacion_por_factura(self):
        conciliaciones = conciliar_facturas()

        self.assertEqual(len(conciliaciones), 1)
        self.assertEqual(conciliaciones[0].factura, self.factura)

    def test_el_estado_global_toma_el_peor_hallazgo(self):
        conciliacion = conciliar_factura(self.factura)

        self.assertEqual(conciliacion.estado, EstadoConciliacion.ATENCION)
        self.assertFalse(conciliacion.conciliado)
        self.assertEqual(conciliacion.semaforo, 'warning')

    def _registrar_pago(self, *, importe=Decimal('8000.00'), moneda='USD',
                         comision=Decimal('0'), imputar_comision=False):
        """Registra un pago al exterior para la factura de la liquidación."""
        pago = PagoExterior.objects.create(
            factura=self.factura,
            fecha_operacion=date(2026, 8, 26),
            moneda=moneda,
            importe=importe,
            comision=comision,
            forma_pago=PagoExterior.FormaPago.DEBITO_CUENTA,
            referencia_op='136294',
        )
        self.orden.pago_exterior = pago
        self.orden.save(update_fields=['pago_exterior', 'updated_at'])

        from finanzas.services import sincronizar_factura
        sincronizar_factura(self.factura)

        if imputar_comision:
            from finanzas.services import asignar_comision_a_embarque
            asignar_comision_a_embarque(pago, self.embarque)
        return pago


class ConciliacionVistasTests(ConciliacionTestCase):
    """Pantallas de conciliación."""

    def test_la_lista_muestra_las_facturas_con_semaforo(self):
        respuesta = self.client.get(reverse('lista_conciliacion'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, '20260826')
        self.assertContains(respuesta, 'SKPY Trading')
        self.assertContains(respuesta, 'Conciliación de documentos')

    def test_la_lista_filtra_por_estado(self):
        respuesta = self.client.get(reverse('lista_conciliacion'), {'estado': 'DIFERENCIA'})

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, '20260826')

    def test_la_lista_filtra_por_busqueda(self):
        respuesta = self.client.get(reverse('lista_conciliacion'), {'q': '20260826'})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, '20260826')

    def test_el_detalle_muestra_los_tres_documentos_y_las_verificaciones(self):
        respuesta = self.client.get(reverse('detalle_conciliacion', args=[self.factura.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Factura comercial')
        self.assertContains(respuesta, 'B/L y contenedores')
        self.assertContains(respuesta, 'Liquidación y pago')
        self.assertContains(respuesta, 'Resultado de las verificaciones')
        self.assertContains(respuesta, 'MEDUKC733517')
        self.assertContains(respuesta, '136294')

    def test_el_detalle_es_informativo_y_no_bloquea(self):
        """Una factura sin documentos cargados se muestra, no se rechaza."""
        otra = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='20260901',
            fecha=date(2026, 9, 1),
            moneda='USD',
            total_declarado=Decimal('1000.00'),
        )

        respuesta = self.client.get(reverse('detalle_conciliacion', args=[otra.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, '20260901')

    def test_exporta_la_conciliacion_en_csv(self):
        respuesta = self.client.get(reverse('exportar_conciliacion'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('text/csv', respuesta['Content-Type'])
        self.assertIn('CONCILIACION_DOCUMENTOS', respuesta.headers.get('Content-Disposition', ''))
        contenido = respuesta.content.decode()
        self.assertIn('20260826', contenido)
        self.assertIn('Unidades', contenido)

    def test_un_usuario_sin_permiso_no_accede(self):
        usuario = get_user_model().objects.create_user(username='sin_permiso', password='123456')
        self.client.force_login(usuario)

        respuesta = self.client.get(reverse('lista_conciliacion'))

        # Sin permiso el usuario es redirigido (no ve la conciliación).
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn('20260826', respuesta.content.decode())
