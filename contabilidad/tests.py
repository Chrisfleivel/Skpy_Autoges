import unittest
from decimal import Decimal
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

# La app `contabilidad` está deshabilitada en INSTALLED_APPS (y depende de
# `documentos_financieros`, también deshabilitada). Sus modelos no se pueden
# importar sin registrarlos en INSTALLED_APPS, así que el módulo se saltea
# en vez de fallar. Si se reactiva la app, los tests vuelven a correr solos.
if 'contabilidad' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest(
        'La app contabilidad está deshabilitada en INSTALLED_APPS; sus tests no aplican.'
    )

from configuraciones_maestras.models import Moneda, Proveedor
from documentos_financieros.models import Autofactura, FacturaComercial
from .models import Asiento, CuentaContable, MovimientoContable, SaldoMensualCuenta
from .services import ejecutar_cierre_mensual, facturar_documento_financiero, facturar_pedido_compra


class FacturacionPedidoCompraTests(TestCase):
    def test_facturar_pedido_compra_crea_factura_y_asiento(self):
        moneda = Moneda.objects.create(codigo='PYG', nombre='Guaraní')
        proveedor = Proveedor.objects.create(nombre='Proveedor Test', razon_social='Proveedor Test')
        pedido = SimpleNamespace(id=99, proveedor=proveedor, monto_total=Decimal('1500.00'), estado='PENDIENTE')

        factura, asiento, pedido_actualizado = facturar_pedido_compra(pedido, '001-0001')

        self.assertIsInstance(factura, FacturaComercial)
        self.assertEqual(factura.proveedor, proveedor)
        self.assertEqual(factura.monto_total, Decimal('1500.00'))
        self.assertEqual(asiento.descripcion, 'Factura de Compra 001-0001 - Pedido 99')
        self.assertTrue(asiento.movimientos.exists())
        self.assertEqual(pedido_actualizado.estado, 'FACTURADO')

    def test_facturar_autofactura_crea_documento_y_asiento(self):
        proveedor = Proveedor.objects.create(nombre='Proveedor Autofactura', razon_social='Proveedor Autofactura')
        documento = SimpleNamespace(
            id=77,
            proveedor=proveedor,
            monto_total=Decimal('800.00'),
            estado='pendiente',
            numero_documento='A-001',
        )

        factura, asiento, documento_actualizado = facturar_documento_financiero(
            documento,
            tipo_documento='autofactura',
            numero_documento='A-001',
        )

        self.assertIsInstance(factura, Autofactura)
        self.assertEqual(factura.proveedor, proveedor)
        self.assertEqual(factura.monto_total, Decimal('800.00'))
        self.assertTrue(asiento.movimientos.exists())
        self.assertEqual(documento_actualizado.estado, 'FACTURADO')


class AuditoriaContableTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='contador', password='secret123')
        self.moneda = Moneda.objects.create(codigo='PYG', nombre='Guaraní')
        self.content_type = ContentType.objects.get(app_label='contabilidad', model='asiento')

        for codename in [
            'ver_asientos_contables',
            'ver_movimientos_contables',
            'marcar_asientos_revisados',
            'ver_auditoria_asientos',
            'ver_reportes',
        ]:
            Permission.objects.get_or_create(
                codename=codename,
                content_type=self.content_type,
                defaults={'name': codename},
            )

        self.cuenta = CuentaContable.objects.create(
            codigo='1.1.01',
            nombre='Caja',
            tipo='A',
            moneda=self.moneda,
        )
        self.asiento = Asiento.objects.create(
            fecha=timezone.now(),
            descripcion='Asiento de prueba',
        )
        MovimientoContable.objects.create(asiento=self.asiento, cuenta=self.cuenta, debe=Decimal('100.00'))
        MovimientoContable.objects.create(asiento=self.asiento, cuenta=self.cuenta, haber=Decimal('100.00'))

    def test_listar_asientos_requiere_permiso(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('listar_asientos_contables'))
        self.assertEqual(response.status_code, 302)

    def test_listar_asientos_y_detalle_con_permiso(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_asientos_contables', content_type=self.content_type)
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_movimientos_contables', content_type=self.content_type)
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename='marcar_asientos_revisados', content_type=self.content_type)
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_auditoria_asientos', content_type=self.content_type)
        )
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse('listar_asientos_contables'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Asiento de prueba')

        detail_response = self.client.get(reverse('detalle_asiento_contable', args=[self.asiento.id]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, '100.00')

    def test_marcar_asiento_revisado_y_auditoria(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_asientos_contables', content_type=self.content_type)
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_movimientos_contables', content_type=self.content_type)
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename='marcar_asientos_revisados', content_type=self.content_type)
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_auditoria_asientos', content_type=self.content_type)
        )
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post(reverse('marcar_asiento_revisado', args=[self.asiento.id]))
        self.assertEqual(response.status_code, 302)

        self.asiento.refresh_from_db()
        self.assertTrue(self.asiento.revisado)
        self.assertEqual(self.asiento.revisado_por, self.user)
        self.assertIsNotNone(self.asiento.fecha_revision)

        audit_response = self.client.get(reverse('auditoria_asientos_contables'))
        self.assertEqual(audit_response.status_code, 200)
        self.assertContains(audit_response, self.user.username)

    def test_estado_resultados_con_permiso(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_reportes', content_type=self.content_type)
        )
        self.user.save()
        self.client.force_login(self.user)

        ingreso = CuentaContable.objects.create(
            codigo='4.1.01',
            nombre='Ventas',
            tipo='I',
            moneda=self.moneda,
        )
        gasto = CuentaContable.objects.create(
            codigo='5.1.01',
            nombre='Sueldos',
            tipo='E',
            moneda=self.moneda,
        )

        asiento_ingreso = Asiento.objects.create(fecha=timezone.now(), descripcion='Ingreso de prueba')
        MovimientoContable.objects.create(asiento=asiento_ingreso, cuenta=ingreso, haber=Decimal('500.00'))

        asiento_gasto = Asiento.objects.create(fecha=timezone.now(), descripcion='Gasto de prueba')
        MovimientoContable.objects.create(asiento=asiento_gasto, cuenta=gasto, debe=Decimal('200.00'))

        response = self.client.get(reverse('vista_estado_resultados'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ventas')
        self.assertContains(response, 'Sueldos')
        self.assertContains(response, 'Utilidad neta')

    def test_listar_asientos_por_fecha_y_documento(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_asientos_contables', content_type=self.content_type)
        )
        self.user.save()
        self.client.force_login(self.user)

        documento_tipo = ContentType.objects.get_for_model(Asiento)
        documento_asiento = Asiento.objects.create(fecha=timezone.now(), descripcion='Documento origen')

        asiento_filtrado = Asiento.objects.create(
            fecha=timezone.now(),
            descripcion='Asiento con documento',
            documento_tipo=documento_tipo,
            documento_id=documento_asiento.id,
        )

        response = self.client.get(reverse('listar_asientos_contables'), {
            'fecha_desde': timezone.now().date().isoformat(),
            'fecha_hasta': timezone.now().date().isoformat(),
            'documento_tipo': str(documento_tipo.id),
            'documento_id': str(documento_asiento.id),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Asiento con documento')
        self.assertContains(response, 'Asiento origen')

    def test_libro_mayor_por_cuenta(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_reportes', content_type=self.content_type)
        )
        self.user.save()
        self.client.force_login(self.user)

        cuenta = CuentaContable.objects.create(
            codigo='1.1.02',
            nombre='Caja',
            tipo='A',
            moneda=self.moneda,
        )
        asiento_entrada = Asiento.objects.create(fecha=timezone.now(), descripcion='Entrada de caja')
        MovimientoContable.objects.create(asiento=asiento_entrada, cuenta=cuenta, debe=Decimal('100.00'))

        asiento_salida = Asiento.objects.create(fecha=timezone.now(), descripcion='Salida de caja')
        MovimientoContable.objects.create(asiento=asiento_salida, cuenta=cuenta, haber=Decimal('40.00'))

        fecha = timezone.now().date().isoformat()
        response = self.client.get(
            reverse('vista_libro_mayor'),
            {'cuenta': cuenta.id, 'fecha_desde': fecha, 'fecha_hasta': fecha},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Libro mayor')
        self.assertContains(response, 'Caja')
        self.assertContains(response, 'Entrada de caja')
        self.assertContains(response, 'Salida de caja')

    def test_ejecutar_cierre_mensual_registra_saldos(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_reportes', content_type=self.content_type)
        )
        self.user.save()
        self.client.force_login(self.user)

        cuenta = CuentaContable.objects.create(
            codigo='1.1.50',
            nombre='Caja cierre',
            tipo='A',
            moneda=self.moneda,
        )
        asiento = Asiento.objects.create(fecha=timezone.now(), descripcion='Asiento de cierre')
        MovimientoContable.objects.create(asiento=asiento, cuenta=cuenta, debe=Decimal('150.00'))

        fecha = timezone.now().date()
        ejecutar_cierre_mensual(fecha.year, fecha.month)

        cierre = SaldoMensualCuenta.objects.get(cuenta=cuenta, anio=fecha.year, mes=fecha.month)
        self.assertEqual(cierre.saldo_final, Decimal('150.00'))

    def test_cierre_mensual_view(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='ver_reportes', content_type=self.content_type)
        )
        self.user.save()
        self.client.force_login(self.user)

        periodo = timezone.now().date().strftime('%Y-%m')
        response = self.client.post(reverse('cierre_mensual'), {'periodo': periodo})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cierre mensual formalizado')
