"""
Tests de la Fase 3: liquidación de orden de pago al exterior y su vínculo
con el asiento financiero (`finanzas.PagoExterior`).

La liquidación es el documento bancario capturado a mano; el pago es el
asiento contable. Este módulo verifica el registro del pago desde la
liquidación, la imputación de la comisión al embarque y los bloqueos.
"""
from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from compras.models import FacturaComercial, FacturaItem
from finanzas.models import PagoExterior
from importaciones.models import Embarque, EmbarqueContenedor, EmbarqueItem, GastoImportacion

from .models import Moneda, OrdenPagoExterior, Proveedor


class LiquidacionPagoTests(TestCase):
    """Base con una operación completa: factura, embarque y liquidación."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='liquidacion_user', password='123456', is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

        Moneda.ensure_defaults()
        self.moneda_usd = Moneda.objects.get(codigo='USD')
        self.moneda_pyg = Moneda.objects.get(codigo='PYG')

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
            total_declarado=Decimal('25150.00'),
            incoterm=FacturaComercial.Incoterm.FOB,
            condicion_pago='CASH BASE',
        )
        self.item_factura = FacturaItem.objects.create(
            factura=self.factura,
            descripcion='Hyundai Tucson 2011',
            cantidad=8,
            precio_unitario=Decimal('3143.75'),
            chasis='KMHJU81VBBU197503',
        )
        self.factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)

        self.embarque = Embarque.objects.create(
            referencia_interna='EMB-2026-001',
            bl_numero='MEDUKC733517',
            puerto_carga='INCHEON, KOREA',
            puerto_descarga='IQUIQUE, CHILE',
            destino_final='ASUNCION, PARAGUAY',
            fecha_embarque=date(2026, 8, 20),
            estado=Embarque.Estado.PROGRAMADO,
        )
        self.contenedor = EmbarqueContenedor.objects.create(
            embarque=self.embarque,
            numero='MEDUKC733517',
            tipo='40HC',
            peso_bruto_kg=Decimal('6030.00'),
        )
        EmbarqueItem.objects.create(
            embarque=self.embarque,
            factura_item=self.item_factura,
            contenedor=self.contenedor,
            cantidad=4,
            chasis_bl='KMHJU81VBBU197503',
        )

        self.orden = OrdenPagoExterior.objects.create(
            tipo_documento_remitente='RUC',
            numero_documento_remitente='8001234560001',
            remitente_nombre='SKPY Trading',
            remitente_direccion='Asunción, Paraguay',
            forma_pago='TRANSFERENCIA',
            numero_cuenta='1234567890',
            moneda=self.moneda_usd,
            importe_orden=Decimal('25150.00'),
            comision_orden=Decimal('85.00'),
            referencia_op='136294',
            numero_lote='132115',
            fecha_operacion=date(2026, 8, 26),
            hora_operacion=time(14, 30),
            usuario_banco='NVILLAMA',
            firmante='NERY VILLAMAYOR',
            ordenante='SKPY Trading S.A.',
            beneficiario='HYUNDAI MOTOR COMPANY',
            pais_beneficiario='KR',
            cuenta_beneficiaria='620-123456-789',
            motivo_transferencia='INVOICE 20260826',
            concepto='FONDOS PROPIOS',
            cotizacion=Decimal('1'),
        )

    def _post_registro(self, **overrides):
        datos = {
            'factura': self.factura.pk,
            'embarque': self.embarque.pk,
            'fecha_operacion': '2026-08-26',
            'importe': '25150.00',
            'comision': '85.00',
            'cotizacion': '',
            'forma_pago': 'DEBITO_CUENTA',
            'referencia_op': '136294',
            'numero_lote': '132115',
        }
        datos.update(overrides)
        return self.client.post(
            reverse('registrar_pago_orden_pago_exterior', args=[self.orden.pk]),
            datos,
        )


class RegistroPagoDesdeLiquidacionTests(LiquidacionPagoTests):
    """Registro del pago al exterior a partir de la liquidación."""

    def test_registra_el_pago_y_enlaza_la_liquidacion(self):
        respuesta = self._post_registro()

        self.assertEqual(respuesta.status_code, 302)
        pago = PagoExterior.objects.get()
        self.assertEqual(pago.importe, Decimal('25150.00'))
        self.assertEqual(pago.comision, Decimal('85.00'))
        self.assertEqual(pago.moneda, 'USD')

        self.orden.refresh_from_db()
        self.assertEqual(self.orden.pago_exterior, pago)
        self.assertEqual(self.orden.factura, self.factura)
        self.assertEqual(self.orden.embarque, self.embarque)
        self.assertEqual(self.orden.estado, OrdenPagoExterior.Estado.ENVIADA)
        self.assertTrue(self.orden.pago_registrado)

    def test_el_pago_hereda_los_datos_bancarios_de_la_liquidacion(self):
        self._post_registro()

        pago = PagoExterior.objects.get()
        self.assertEqual(pago.referencia_op, '136294')
        self.assertEqual(pago.nro_lote, '132115')
        self.assertEqual(pago.beneficiario, 'HYUNDAI MOTOR COMPANY')
        self.assertEqual(pago.motivo_transferencia, 'INVOICE 20260826')
        self.assertEqual(pago.concepto, 'FONDOS PROPIOS')
        self.assertEqual(pago.forma_pago, PagoExterior.FormaPago.DEBITO_CUENTA)
        self.assertEqual(pago.cuenta_beneficiario, '620-123456-789')
        self.assertEqual(pago.pais_beneficiario, 'KR')
        self.assertEqual(pago.cuenta_debito, '1234567890')

    def test_el_pago_desconta_el_saldo_de_la_factura(self):
        self._post_registro()

        self.factura.refresh_from_db()
        self.assertEqual(self.factura.monto_pagado, Decimal('25150.00'))
        self.assertEqual(self.factura.saldo_pendiente, Decimal('0'))
        self.assertEqual(self.factura.estado, FacturaComercial.Estado.PAGADA)

    def test_imputa_la_comision_al_embarque_como_gasto_bancario(self):
        self._post_registro()

        gasto = GastoImportacion.objects.get()
        self.assertEqual(gasto.tipo, GastoImportacion.Tipo.COMISION_BANCARIA)
        self.assertEqual(gasto.monto, Decimal('85.00'))
        self.assertEqual(gasto.moneda, 'USD')
        self.assertEqual(gasto.embarque, self.embarque)

        pago = PagoExterior.objects.get()
        self.assertEqual(pago.gasto_comision, gasto)

    def test_sin_embarque_la_comision_queda_solo_en_el_pago(self):
        respuesta = self._post_registro(embarque='')

        self.assertEqual(respuesta.status_code, 302)
        pago = PagoExterior.objects.get()
        self.assertEqual(pago.comision, Decimal('85.00'))
        self.assertFalse(GastoImportacion.objects.exists())
        self.assertIsNone(pago.gasto_comision)

        self.orden.refresh_from_db()
        self.assertIsNone(self.orden.embarque)

    def test_no_permite_registrar_dos_pagos_para_la_misma_liquidacion(self):
        self._post_registro()
        respuesta = self._post_registro()

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(PagoExterior.objects.count(), 1)

    def test_no_registra_el_pago_si_la_moneda_no_coincide(self):
        self.orden.moneda = self.moneda_pyg
        self.orden.save()

        respuesta = self._post_registro()

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(PagoExterior.objects.exists())
        self.assertContains(respuesta, 'PYG')

    def test_no_registra_un_importe_mayor_al_saldo_pendiente(self):
        respuesta = self._post_registro(importe='99999.00')

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(PagoExterior.objects.exists())
        self.assertContains(respuesta, 'saldo pendiente')

    def test_no_registra_el_pago_si_la_factura_no_es_pagable(self):
        borrador = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='20260999',
            fecha=date(2026, 9, 1),
            moneda='USD',
            total_declarado=Decimal('1000.00'),
        )

        respuesta = self._post_registro(factura=borrador.pk, importe='1000.00')

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(PagoExterior.objects.exists())
        self.assertContains(respuesta, 'BORRADOR')

    def test_el_servicio_rechaza_una_liquidacion_con_pago_ya_registrado(self):
        from django.core.exceptions import ValidationError

        from .services import registrar_pago_desde_orden

        self._post_registro()
        self.orden.refresh_from_db()

        with self.assertRaises(ValidationError):
            registrar_pago_desde_orden(
                self.orden,
                factura=self.factura,
                fecha_operacion=date(2026, 8, 26),
                importe=Decimal('25150.00'),
            )


class TotalesLiquidacionTests(LiquidacionPagoTests):
    """Los totales del documento se calculan a partir del importe y la comisión."""

    def test_el_total_es_el_importe_mas_la_comision(self):
        self.assertEqual(self.orden.total_orden, Decimal('25235.00'))
        self.assertEqual(self.orden.capital, Decimal('25150.00'))
        self.assertEqual(self.orden.comision, Decimal('85.00'))
        self.assertEqual(self.orden.total, Decimal('25235.00'))

    def test_los_totales_se_recalculan_al_guardar(self):
        self.orden.importe_orden = Decimal('1000.00')
        self.orden.comision_orden = Decimal('25.00')
        self.orden.total_orden = Decimal('999999.00')
        self.orden.save()

        self.orden.refresh_from_db()
        self.assertEqual(self.orden.total_orden, Decimal('1025.00'))
        self.assertEqual(self.orden.capital, Decimal('1000.00'))
        self.assertEqual(self.orden.comision, Decimal('25.00'))

    def test_la_forma_de_pago_del_documento_se_traduce_al_asiento(self):
        self.orden.forma_pago = 'CHEQUE'
        self.assertEqual(self.orden.forma_pago_finanzas, 'CHEQUE')

        self.orden.forma_pago = 'DBCUENTA'
        self.assertEqual(self.orden.forma_pago_finanzas, 'DEBITO_CUENTA')

        self.orden.forma_pago = 'TRANSFERENCIA'
        self.assertEqual(self.orden.forma_pago_finanzas, 'DEBITO_CUENTA')


class CapturaManualLiquidacionTests(LiquidacionPagoTests):
    """Captura manual de la liquidación (datos y archivo del documento)."""

    def _post_agregar(self, **overrides):
        datos = {
            'tipo_documento_remitente': 'RUC',
            'numero_documento_remitente': '8001234560001',
            'remitente_nombre': 'SKPY Trading',
            'remitente_direccion': 'Asunción',
            'remitente_telefono': '021123456',
            'forma_pago': 'TRANSFERENCIA',
            'numero_cuenta': '1234567890',
            'moneda': 'USD',
            'importe_orden': '25150.00',
            'comision_orden': '85.00',
            'referencia_op': '136294',
            'numero_lote': '132115',
            'fecha_operacion': '2026-08-26',
            'hora_operacion': '14:30',
            'usuario_banco': 'NVILLAMA',
            'firmante': 'NERY VILLAMAYOR',
            'banco_corresponsal': '',
            'ordenante': 'SKPY Trading S.A.',
            'banco_beneficiario': '',
            'pais_beneficiario': 'KR',
            'cuenta_beneficiaria': '620-123456-789',
            'beneficiario': 'HYUNDAI MOTOR COMPANY',
            'motivo_transferencia': 'INVOICE 20260826',
            'concepto': 'FONDOS PROPIOS',
            'cotizacion': '1',
            'factura': '',
            'embarque': '',
            'archivo': SimpleUploadedFile(
                'liquidacion.jpg', b'contenido-liquidacion', content_type='image/jpeg'),
            'estado': 'BORRADOR',
            'observaciones': '',
        }
        datos.update(overrides)
        return self.client.post(reverse('agregar_orden_pago_exterior'), datos)

    def test_registra_la_liquidacion_con_el_documento_adjunto(self):
        respuesta = self._post_agregar()

        self.assertEqual(respuesta.status_code, 302)
        orden = OrdenPagoExterior.objects.exclude(pk=self.orden.pk).get()
        self.assertTrue(orden.archivo)
        self.assertEqual(orden.importe_orden, Decimal('25150.00'))
        self.assertEqual(orden.comision_orden, Decimal('85.00'))
        self.assertEqual(orden.total_orden, Decimal('25235.00'))
        self.assertEqual(orden.usuario_banco, 'NVILLAMA')
        self.assertEqual(orden.firmante, 'NERY VILLAMAYOR')
        self.assertEqual(orden.hora_operacion, time(14, 30))
        self.assertEqual(orden.estado, OrdenPagoExterior.Estado.BORRADOR)

    def test_rechaza_una_liquidacion_sin_importe(self):
        respuesta = self._post_agregar(importe_orden='0')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(OrdenPagoExterior.objects.count(), 1)

    def test_rechaza_una_moneda_distinta_a_la_de_la_factura(self):
        respuesta = self._post_agregar(moneda='PYG', factura=self.factura.pk)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(OrdenPagoExterior.objects.count(), 1)


class PantallasLiquidacionTests(LiquidacionPagoTests):
    """Renderizado de las pantallas de la liquidación."""

    def test_el_detalle_muestra_los_datos_nuevos(self):
        respuesta = self.client.get(reverse('detalle_orden_pago_exterior', args=[self.orden.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'NVILLAMA')
        self.assertContains(respuesta, 'NERY VILLAMAYOR')
        self.assertContains(respuesta, '14:30')
        self.assertContains(respuesta, 'Registrar pago')

    def test_el_detalle_muestra_el_pago_registrado(self):
        self._post_registro()

        respuesta = self.client.get(reverse('detalle_orden_pago_exterior', args=[self.orden.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'HYUNDAI MOTOR COMPANY')
        self.assertContains(respuesta, '136294')

    def test_la_pantalla_de_registro_de_pago_se_renderiza(self):
        respuesta = self.client.get(reverse('registrar_pago_orden_pago_exterior', args=[self.orden.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Registrar pago al exterior')
        self.assertContains(respuesta, 'name="importe"')
        self.assertContains(respuesta, 'name="embarque"')

    def test_el_formulario_de_alta_permite_subir_el_documento(self):
        respuesta = self.client.get(reverse('agregar_orden_pago_exterior'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'multipart/form-data')
        self.assertContains(respuesta, 'name="archivo"')
        self.assertContains(respuesta, 'name="usuario_banco"')
        self.assertContains(respuesta, 'name="firmante"')

    def test_el_formulario_de_edicion_permite_subir_el_documento(self):
        respuesta = self.client.get(reverse('editar_orden_pago_exterior', args=[self.orden.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'multipart/form-data')
        self.assertContains(respuesta, 'name="archivo"')

    def test_la_lista_muestra_el_boton_de_registrar_pago(self):
        respuesta = self.client.get(reverse('lista_ordenes_pago_exterior'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Registrar pago')

    def test_no_se_puede_eliminar_una_liquidacion_con_pago_registrado(self):
        self._post_registro()

        respuesta = self.client.post(reverse('eliminar_orden_pago_exterior', args=[self.orden.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(OrdenPagoExterior.objects.filter(pk=self.orden.pk).exists())
