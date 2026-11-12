"""
Tests del CRUD de facturas comerciales (Fase 1 de importación de documentos).
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes_pedidos.models import Cliente
from configuraciones_maestras.models import Proveedor
from seguridad_usuarios.models import Permiso, Rol

from .models import FacturaComercial, FacturaItem
from . import services


class FacturaComercialCrudTests(TestCase):
    """Alta, edición, detalle, confirmación y eliminación de facturas."""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='SKPY Trading',
            razon_social='SKPY Trading Co. Ltd.',
            documento_identidad='4658103426',
            tipo_persona='JURIDICA',
            pais='Corea del Sur',
        )
        self.cliente = Cliente.objects.create(
            nombre='Rodrigo Daniel',
            apellidos='Ocampos Perez',
            documento_identidad='1884336',
            tipo_persona='FISICA',
        )
        self.usuario = User.objects.create_user(username='compras_user', password='testpass123')
        self._asignar_permisos('compras.lista_facturas')
        self._asignar_permisos('compras.agregar_factura')
        self._asignar_permisos('compras.editar_factura')
        self._asignar_permisos('compras.detalle_factura')
        self._asignar_permisos('compras.eliminar_factura')
        self._asignar_permisos('compras.confirmar_factura')
        self.client.force_login(self.usuario)

    def _asignar_permisos(self, codename):
        """Asigna un permiso del sistema propio al usuario, como hace el rol."""
        permiso, _ = Permiso.objects.get_or_create(
            codename=codename,
            defaults={'nombre': codename, 'sector': 'Compras'},
        )
        rol, _ = Rol.objects.get_or_create(nombre=f'Rol_{codename}', defaults={'descripcion': 'Test'})
        rol.permisos.add(permiso)
        perfil = self.usuario.perfil
        perfil.roles.add(rol)
        perfil.save()

    def _post_factura(self, **overrides):
        datos = {
            'proveedor': self.proveedor.pk,
            'numero': '20260826',
            'fecha': '2026-08-26',
            'cliente_importador': self.cliente.pk,
            'notify_party': 'TO ORDER',
            'puerto_carga': 'INCHEON, KOREA',
            'moneda': 'USD',
            'incoterm': 'FOB',
            'condicion_pago': 'CASH BASE',
            'total_declarado': '2800.00',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-vehiculo': '',
            'items-0-descripcion': 'Hyundai Tucson',
            'items-0-cantidad': '1',
            'items-0-precio_unitario': '2800.00',
            'items-0-chasis': 'KMHJU81VBBU197503',
            'items-0-anio': '2011',
            'items-0-motor': '',
            'items-0-peso_kg': '',
            'items-0-cbm': '',
        }
        datos.update(overrides)
        return self.client.post(reverse('agregar_factura_comercial'), datos)

    # ------------------------------------------------------------------
    # Alta
    # ------------------------------------------------------------------
    def test_crea_factura_con_sus_items(self):
        respuesta = self._post_factura()

        self.assertEqual(respuesta.status_code, 302)
        factura = FacturaComercial.objects.get(numero='20260826')
        self.assertEqual(factura.estado, FacturaComercial.Estado.BORRADOR)
        self.assertEqual(factura.items.count(), 1)
        item = factura.items.first()
        self.assertEqual(item.chasis, 'KMHJU81VBBU197503')
        self.assertEqual(item.anio, 2011)
        self.assertEqual(factura.cliente_importador, self.cliente)
        self.assertEqual(factura.notify_party, 'TO ORDER')
        self.assertEqual(factura.puerto_carga, 'INCHEON, KOREA')
        self.assertEqual(factura.unidades, 1)

    def test_no_crea_factura_si_falta_el_proveedor(self):
        respuesta = self._post_factura(proveedor='')

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(FacturaComercial.objects.exists())

    def test_no_crea_factura_con_chasis_duplicado(self):
        respuesta = self._post_factura(
            **{'items-TOTAL_FORMS': '2',
               'items-1-vehiculo': '',
               'items-1-descripcion': 'Kia Sportage',
               'items-1-cantidad': '1',
               'items-1-precio_unitario': '1000.00',
               'items-1-chasis': 'KMHJU81VBBU197503',
               'items-1-anio': '2012',
               'items-1-motor': '',
               'items-1-peso_kg': '',
               'items-1-cbm': ''}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(FacturaComercial.objects.exists())

    # ------------------------------------------------------------------
    # Listado y detalle
    # ------------------------------------------------------------------
    def test_lista_las_facturas_registradas(self):
        FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-100',
            fecha='2026-08-26',
            total_declarado=Decimal('2800.00'),
            moneda='USD',
        )

        respuesta = self.client.get(reverse('lista_facturas_comerciales'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'FAC-100')

    def test_detalle_muestra_los_datos_de_la_factura(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-200',
            fecha='2026-08-26',
            total_declarado=Decimal('2800.00'),
            moneda='USD',
            notify_party='TO ORDER',
        )

        respuesta = self.client.get(reverse('detalle_factura_comercial', args=[factura.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'FAC-200')
        self.assertContains(respuesta, 'TO ORDER')

    # ------------------------------------------------------------------
    # Confirmación
    # ------------------------------------------------------------------
    def test_confirma_factura_con_total_que_coincide(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-300',
            fecha='2026-08-26',
            total_declarado=Decimal('100.00'),
            moneda='USD',
        )
        FacturaItem.objects.create(
            factura=factura,
            descripcion='Hyundai Tucson',
            cantidad=1,
            precio_unitario=Decimal('100.00'),
        )

        respuesta = self.client.post(reverse('confirmar_factura_comercial', args=[factura.pk]))

        self.assertEqual(respuesta.status_code, 302)
        factura.refresh_from_db()
        self.assertEqual(factura.estado, FacturaComercial.Estado.CONFIRMADA)

    def test_no_confirma_factura_con_total_desfasado(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-400',
            fecha='2026-08-26',
            total_declarado=Decimal('200.00'),
            moneda='USD',
        )
        FacturaItem.objects.create(
            factura=factura,
            descripcion='Hyundai Tucson',
            cantidad=1,
            precio_unitario=Decimal('100.00'),
        )

        self.client.post(reverse('confirmar_factura_comercial', args=[factura.pk]))

        factura.refresh_from_db()
        self.assertEqual(factura.estado, FacturaComercial.Estado.BORRADOR)

    # ------------------------------------------------------------------
    # Edición y eliminación
    # ------------------------------------------------------------------
    def test_actualiza_factura_en_borrador(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-500',
            fecha='2026-08-26',
            total_declarado=Decimal('2800.00'),
            moneda='USD',
        )

        respuesta = self.client.post(reverse('editar_factura_comercial', args=[factura.pk]), {
            'proveedor': self.proveedor.pk,
            'numero': 'FAC-500',
            'fecha': '2026-08-26',
            'moneda': 'USD',
            'incoterm': 'FOB',
            'total_declarado': '2800.00',
            'items-TOTAL_FORMS': '0',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
        })

        self.assertEqual(respuesta.status_code, 302)
        factura.refresh_from_db()
        self.assertEqual(factura.numero, 'FAC-500')

    def test_no_editar_factura_confirmada(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-600',
            fecha='2026-08-26',
            total_declarado=Decimal('100.00'),
            moneda='USD',
        )
        FacturaItem.objects.create(
            factura=factura,
            descripcion='Hyundai Tucson',
            cantidad=1,
            precio_unitario=Decimal('100.00'),
        )
        factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)

        respuesta = self.client.get(reverse('editar_factura_comercial', args=[factura.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertRedirects(respuesta, reverse('detalle_factura_comercial', args=[factura.pk]))

    def test_elimina_factura_en_borrador(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-700',
            fecha='2026-08-26',
            total_declarado=Decimal('100.00'),
            moneda='USD',
        )

        respuesta = self.client.post(reverse('eliminar_factura_comercial', args=[factura.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(FacturaComercial.objects.filter(pk=factura.pk).exists())

    def test_no_elimina_factura_con_pagos(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-800',
            fecha='2026-08-26',
            total_declarado=Decimal('100.00'),
            moneda='USD',
        )
        permitido, motivo = services.puede_eliminarse(factura)
        self.assertTrue(permitido, motivo)


class FacturaComercialReglasTests(TestCase):
    """Reglas de negocio puras sobre los totales y la edición."""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            razon_social='Proveedor Test SA',
            tipo_persona='JURIDICA',
        )

    def test_total_items_es_la_suma_de_las_lineas(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-900',
            fecha='2026-08-26',
            total_declarado=Decimal('5800.00'),
            moneda='USD',
        )
        FacturaItem.objects.create(
            factura=factura, descripcion='Tucson', cantidad=1, precio_unitario=Decimal('2800.00'))
        FacturaItem.objects.create(
            factura=factura, descripcion='E300', cantidad=1, precio_unitario=Decimal('3000.00'))

        self.assertEqual(factura.total_items, Decimal('5800.00'))
        self.assertEqual(factura.diferencia_total, Decimal('0.00'))
        self.assertEqual(factura.unidades, 2)

    def test_una_factura_confirmada_no_es_editable(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-950',
            fecha='2026-08-26',
            total_declarado=Decimal('0.00'),
            moneda='USD',
        )
        self.assertTrue(services.puede_editarse(factura))

        factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)
        self.assertFalse(services.puede_editarse(factura))

    def test_chasis_declarados_solo_incluye_los_informados(self):
        factura = FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero='FAC-960',
            fecha='2026-08-26',
            total_declarado=Decimal('0.00'),
            moneda='USD',
        )
        FacturaItem.objects.create(
            factura=factura, descripcion='Tucson', cantidad=1,
            precio_unitario=Decimal('2800.00'), chasis='KMHJU81VBBU197503')
        FacturaItem.objects.create(
            factura=factura, descripcion='E300', cantidad=1, precio_unitario=Decimal('5000.00'))

        self.assertEqual(factura.chasis_declarados, ['KMHJU81VBBU197503'])
