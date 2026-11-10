from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes_pedidos.models import Cliente, ItemPedido, Pedido
from configuraciones_maestras.models import Sucursal
from cobranzas.models import Caja as CajaOperativa, Pago
from inventario.models import Repuesto, UnidadMedida
from seguridad_usuarios.models import Empleado, UsuarioPerfil


class CobranzasViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='caja', password='secret123', is_superuser=True, is_staff=True)
        self.cliente = Cliente.objects.create(nombre='Cliente', apellidos='Cobranzas', razon_social='Cliente Cobranzas')
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            estado='aprobado',
            monto_total=150000,
            iva=15000,
        )

    def test_lista_cobranzas_muestra_pedidos_aprobados(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('lista_pedidos_cobranzas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pedido')
        self.assertContains(response, self.pedido.id)

    def test_confirmar_pago_cambia_estado_a_pagado_y_crea_pago(self):
        self.client.force_login(self.user)
        self.pedido.estado = 'facturado_contado'
        self.pedido.save()

        response = self.client.post(
            reverse('confirmar_pago_cobranzas', kwargs={'pedido_id': self.pedido.id}),
            {'metodo_pago': 'Transferencia'},
        )
        self.assertEqual(response.status_code, 302)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'pagado')
        self.assertTrue(self.pedido.pago_realizado)
        self.assertTrue(self.pedido.pagos.exists())

    def test_confirmar_pago_no_se_permitede_antes_de_facturar(self):
        self.client.force_login(self.user)
        self.pedido.estado = 'aprobado'
        self.pedido.save()

        response = self.client.post(
            reverse('confirmar_pago_cobranzas', kwargs={'pedido_id': self.pedido.id}),
            {'metodo_pago': 'Transferencia'},
        )
        self.assertEqual(response.status_code, 302)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'aprobado')
        self.assertFalse(self.pedido.pagos.exists())

    def test_facturar_pedido_cambia_estado_a_facturado(self):
        self.client.force_login(self.user)
        self.pedido.estado = 'pagado'
        self.pedido.pago_realizado = True
        self.pedido.save()

        response = self.client.post(reverse('facturar_pedido_cobranzas', kwargs={'pedido_id': self.pedido.id}))
        self.assertEqual(response.status_code, 302)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'facturado')

    def test_lista_pedidos_despacho_muestra_ventas_pagadas(self):
        self.client.force_login(self.user)
        Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            venta_tipo='repuesto',
            estado='pagado',
            pago_realizado=True,
            monto_total=100000,
            iva=10000,
        )

        response = self.client.get(reverse('lista_pedidos_despacho'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmar entrega')

    def test_confirmar_entrega_repuesto_desde_pagado_completa_el_pedido(self):
        self.client.force_login(self.user)
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            venta_tipo='repuesto',
            estado='pagado',
            pago_realizado=True,
            monto_total=100000,
            iva=10000,
        )

        response = self.client.post(
            reverse('entregar_repuesto_cobranzas', kwargs={'pedido_id': pedido.id}),
            {'next': 'despacho'},
        )

        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'completado')

    def test_lista_pedidos_transferencia_filtra_por_busqueda_y_estado(self):
        self.client.force_login(self.user)
        cliente_busqueda = Cliente.objects.create(
            nombre='Carlos',
            apellidos='Pérez',
            razon_social='Carlos Pérez SRL',
            documento_identidad='5555555',
            ruc='80055555-6',
        )
        Pedido.objects.create(
            cliente=cliente_busqueda,
            tipo='venta',
            venta_tipo='vehiculo',
            estado='pagado',
            pago_realizado=True,
            monto_total=2000000,
            iva=200000,
        )
        Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            venta_tipo='vehiculo',
            estado='transferencia_en_tramite',
            pago_realizado=True,
            monto_total=1500000,
            iva=150000,
        )

        response = self.client.get(reverse('lista_pedidos_transferencia'), {'q': 'Carlos', 'estado': 'pagado'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['pedidos']), [Pedido.objects.get(cliente=cliente_busqueda)])

    def test_lista_pedidos_busqueda_muestra_solo_pedidos_de_busqueda(self):
        self.client.force_login(self.user)
        Pedido.objects.create(
            cliente=self.cliente,
            tipo='busqueda',
            estado='espera_de_busqueda',
            monto_total=50000,
            iva=5000,
        )
        Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            venta_tipo='repuesto',
            estado='pagado',
            pago_realizado=True,
            monto_total=100000,
            iva=10000,
        )

        response = self.client.get(reverse('lista_pedidos_busqueda'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(response.context['pedidos'])), 1)
        self.assertEqual(response.context['pedidos'][0].tipo, 'busqueda')

    def test_cobrar_pedido_asocia_pago_a_caja_abierta_empleado_y_sucursal(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Central', direccion='Calle 1')
        empleado = Empleado.objects.create(nombre='Ana', apellidos='Gómez', documento_identidad='1234567')
        self.user.perfil.empleado = empleado
        self.user.perfil.save(update_fields=['empleado'])
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja 1',
            estado='abierta',
            saldo_inicial=Decimal('0.00'),
            saldo_actual=Decimal('0.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )
        self.pedido.estado = 'pendiente_cobro'
        self.pedido.tipo = 'venta'
        self.pedido.venta_tipo = 'repuesto'
        self.pedido.save()

        response = self.client.post(
            reverse('cobrar_pedido', kwargs={'pedido_id': self.pedido.id}),
            {
                'monto_recibido': '150000',
                'metodo_pago': 'Efectivo',
                'sucursal': str(sucursal.id),
                'caja': str(caja.id),
            },
        )

        self.assertEqual(response.status_code, 302)
        pago = self.pedido.pagos.order_by('-id').first()
        self.assertIsNotNone(pago)
        self.assertEqual(pago.sucursal, sucursal)
        self.assertEqual(pago.caja, caja)
        self.assertEqual(pago.empleado, empleado)
        self.assertEqual(pago.monto, Decimal('150000'))
        caja.refresh_from_db()
        self.assertEqual(caja.saldo_actual, Decimal('150000'))

    def test_cierre_de_caja_calcula_monto_esperado_y_diferencia(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Arqueo', direccion='Calle 2')
        empleado = Empleado.objects.create(nombre='Luis', apellidos='Pérez', documento_identidad='7654321')
        self.user.perfil.empleado = empleado
        self.user.perfil.save(update_fields=['empleado'])
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Arqueo',
            estado='abierta',
            saldo_inicial=Decimal('50000.00'),
            saldo_actual=Decimal('250000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )

        response = self.client.post(
            reverse('cerrar_caja', kwargs={'caja_id': caja.id}),
            {'monto_real': '245000', 'observaciones': 'Arqueo del día'},
        )

        self.assertEqual(response.status_code, 302)
        cierre = caja.cierres.order_by('-id').first()
        self.assertIsNotNone(cierre)
        self.assertEqual(cierre.monto_esperado, Decimal('250000.00'))
        self.assertEqual(cierre.monto_real, Decimal('245000.00'))
        self.assertEqual(cierre.diferencia, Decimal('-5000.00'))

    def test_resumen_del_dia_muestra_totales_y_diferencia(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Resumen', direccion='Calle 3')
        empleado = Empleado.objects.create(nombre='Nora', apellidos='Díaz', documento_identidad='2468135')
        self.user.perfil.empleado = empleado
        self.user.perfil.save(update_fields=['empleado'])
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Resumen',
            estado='abierta',
            saldo_inicial=Decimal('50000.00'),
            saldo_actual=Decimal('275000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )
        self.pedido.estado = 'pagado'
        self.pedido.pago_realizado = True
        self.pedido.save()
        self.pedido.pagos.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('150000.00'),
            monto_recibido=Decimal('150000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            fecha_pago=timezone.now(),
            estado='confirmado',
        )
        self.pedido.pagos.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('75000.00'),
            monto_recibido=Decimal('75000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Transferencia',
            fecha_pago=timezone.now(),
            estado='confirmado',
        )

        response = self.client.get(reverse('resumen_dia'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumen del día')
        self.assertContains(response, '225000')
        self.assertContains(response, '150000')
        self.assertContains(response, '75000')

    def test_resumen_del_dia_muestra_rendimiento_por_sucursal_y_empleado(self):
        self.client.force_login(self.user)
        sucursal_1 = Sucursal.objects.create(nombre='Sucursal Norte', direccion='Calle Norte 1')
        sucursal_2 = Sucursal.objects.create(nombre='Sucursal Sur', direccion='Calle Sur 1')
        empleado_1 = Empleado.objects.create(nombre='Ana', apellidos='Gómez', documento_identidad='1111111')
        empleado_2 = Empleado.objects.create(nombre='Luis', apellidos='Pérez', documento_identidad='2222222')

        caja_1 = CajaOperativa.objects.create(
            sucursal=sucursal_1,
            nombre='Caja Norte',
            estado='abierta',
            saldo_inicial=Decimal('10000.00'),
            saldo_actual=Decimal('120000.00'),
            empleado_actual=empleado_1,
            fecha_apertura=timezone.now(),
        )
        caja_2 = CajaOperativa.objects.create(
            sucursal=sucursal_2,
            nombre='Caja Sur',
            estado='abierta',
            saldo_inicial=Decimal('10000.00'),
            saldo_actual=Decimal('80000.00'),
            empleado_actual=empleado_2,
            fecha_apertura=timezone.now(),
        )

        self.pedido.estado = 'pagado'
        self.pedido.pago_realizado = True
        self.pedido.save(update_fields=['estado', 'pago_realizado'])

        Pago.objects.create(
            tipo_pago='pedido',
            pedido=self.pedido,
            sucursal=sucursal_1,
            caja=caja_1,
            empleado=empleado_1,
            monto=Decimal('120000.00'),
            monto_recibido=Decimal('120000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.now(),
        )
        Pago.objects.create(
            tipo_pago='pedido',
            pedido=self.pedido,
            sucursal=sucursal_2,
            caja=caja_2,
            empleado=empleado_2,
            monto=Decimal('80000.00'),
            monto_recibido=Decimal('80000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Transferencia',
            estado='confirmado',
            fecha_pago=timezone.now(),
        )

        response = self.client.get(reverse('resumen_dia'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumen por sucursal')
        self.assertContains(response, 'Sucursal Norte')
        self.assertContains(response, 'Sucursal Sur')
        self.assertContains(response, 'Ana Gómez')
        self.assertContains(response, 'Luis Pérez')

    def test_dashboard_ejecutivo_muestra_resumen_general_de_caja(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Dashboard', direccion='Calle Dashboard 1')
        empleado = Empleado.objects.create(nombre='Carla', apellidos='Mendoza', documento_identidad='3333333')
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Dashboard',
            estado='abierta',
            saldo_inicial=Decimal('5000.00'),
            saldo_actual=Decimal('180000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )

        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('120000.00'),
            monto_recibido=Decimal('120000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.now(),
        )

        response = self.client.get(reverse('dashboard_caja'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard ejecutivo')
        self.assertContains(response, 'Total cobrado')
        self.assertContains(response, 'Sucursal Dashboard')
        self.assertContains(response, 'Carla Mendoza')

    def test_dashboard_ejecutivo_incluye_kpis_y_tendencia_fase_9(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Fase 9', direccion='Calle Fase 9 1')
        empleado = Empleado.objects.create(nombre='Javier', apellidos='Silva', documento_identidad='8888888')
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Fase 9',
            estado='abierta',
            saldo_inicial=Decimal('2000.00'),
            saldo_actual=Decimal('260000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )

        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('200000.00'),
            monto_recibido=Decimal('200000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.now(),
        )
        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('60000.00'),
            monto_recibido=Decimal('60000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Transferencia',
            estado='confirmado',
            fecha_pago=timezone.now() - timezone.timedelta(days=1),
        )

        response = self.client.get(reverse('dashboard_caja'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ticket promedio')
        self.assertContains(response, 'Crecimiento')
        self.assertContains(response, 'Sucursal Fase 9')

    def test_ranking_de_rendimiento_incluye_participacion_y_diferencia_vs_dia_anterior(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Ranking', direccion='Calle Ranking 1')
        empleado = Empleado.objects.create(nombre='Carla', apellidos='Mendoza', documento_identidad='3333333')
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Ranking',
            estado='abierta',
            saldo_inicial=Decimal('5000.00'),
            saldo_actual=Decimal('180000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )

        fecha_actual = timezone.localdate()
        fecha_anterior = fecha_actual - timezone.timedelta(days=1)

        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('120000.00'),
            monto_recibido=Decimal('120000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.datetime.combine(fecha_actual, timezone.datetime.min.time()),
        )
        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('60000.00'),
            monto_recibido=Decimal('60000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Transferencia',
            estado='confirmado',
            fecha_pago=timezone.datetime.combine(fecha_anterior, timezone.datetime.min.time()),
        )

        response = self.client.get(reverse('resumen_dia'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ranking de rendimiento')
        self.assertContains(response, 'Participación')
        self.assertContains(response, 'Diferencia vs. día anterior')
        self.assertContains(response, 'Sucursal Ranking')
        self.assertContains(response, 'Carla Mendoza')

    def test_reporte_caja_por_rango_de_fechas_muestra_totales_y_series(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Reporte', direccion='Calle Reporte 1')
        empleado = Empleado.objects.create(nombre='Lucía', apellidos='Fernández', documento_identidad='4444444')
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Reporte',
            estado='abierta',
            saldo_inicial=Decimal('10000.00'),
            saldo_actual=Decimal('300000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )

        fecha_inicio = timezone.localdate()
        fecha_fin = fecha_inicio + timezone.timedelta(days=2)

        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('120000.00'),
            monto_recibido=Decimal('120000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.datetime.combine(fecha_inicio, timezone.datetime.min.time()),
        )
        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('80000.00'),
            monto_recibido=Decimal('80000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Transferencia',
            estado='confirmado',
            fecha_pago=timezone.datetime.combine(fecha_fin, timezone.datetime.min.time()),
        )

        response = self.client.get(reverse('reporte_caja'), {'fecha_inicio': fecha_inicio.isoformat(), 'fecha_fin': fecha_fin.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporte por rango')
        self.assertContains(response, 'Total cobrado')
        self.assertContains(response, 'Lucía Fernández')
        self.assertContains(response, 'Sucursal Reporte')

    def test_reporte_comparativo_muestra_tendencia_por_sucursal_y_empleado(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Comparativa', direccion='Calle Comparativa 1')
        empleado = Empleado.objects.create(nombre='Mateo', apellidos='Rojas', documento_identidad='5555555')
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Comparativa',
            estado='abierta',
            saldo_inicial=Decimal('5000.00'),
            saldo_actual=Decimal('400000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )

        fecha_actual = timezone.localdate()
        fecha_anterior = fecha_actual - timezone.timedelta(days=1)

        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('180000.00'),
            monto_recibido=Decimal('180000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.datetime.combine(fecha_actual, timezone.datetime.min.time()),
        )
        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('120000.00'),
            monto_recibido=Decimal('120000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Transferencia',
            estado='confirmado',
            fecha_pago=timezone.datetime.combine(fecha_anterior, timezone.datetime.min.time()),
        )

        response = self.client.get(reverse('reporte_comparativo'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comparativo de tendencia')
        self.assertContains(response, 'Por sucursal')
        self.assertContains(response, 'Por empleado')
        self.assertContains(response, 'Sucursal Comparativa')
        self.assertContains(response, 'Mateo Rojas')

    def test_reporte_comparativo_exporta_pdf(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal PDF', direccion='Calle PDF 1')
        empleado = Empleado.objects.create(nombre='Nadia', apellidos='Ortiz', documento_identidad='6666666')
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja PDF',
            estado='abierta',
            saldo_inicial=Decimal('1000.00'),
            saldo_actual=Decimal('150000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )
        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('150000.00'),
            monto_recibido=Decimal('150000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.now(),
        )

        response = self.client.get(reverse('reporte_comparativo_pdf'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_reporte_comparativo_exporta_excel(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Excel', direccion='Calle Excel 1')
        empleado = Empleado.objects.create(nombre='Esteban', apellidos='Mora', documento_identidad='7777777')
        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Excel',
            estado='abierta',
            saldo_inicial=Decimal('500.00'),
            saldo_actual=Decimal('125000.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )
        Pago.objects.create(
            tipo_pago='pedido',
            sucursal=sucursal,
            caja=caja,
            empleado=empleado,
            monto=Decimal('125000.00'),
            monto_recibido=Decimal('125000.00'),
            vuelto=Decimal('0.00'),
            metodo_pago='Efectivo',
            estado='confirmado',
            fecha_pago=timezone.now(),
        )

        response = self.client.get(reverse('reporte_comparativo_excel'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheet', response['Content-Type'])

    def test_flujo_completo_venta_repuesto_reserva_stock_paga_en_caja_y_entrega(self):
        self.client.force_login(self.user)
        sucursal = Sucursal.objects.create(nombre='Sucursal Comercial', direccion='Av. Comercial 123')
        empleado = Empleado.objects.create(nombre='María', apellidos='López', documento_identidad='9876543')
        self.user.perfil.empleado = empleado
        self.user.perfil.save(update_fields=['empleado'])

        caja = CajaOperativa.objects.create(
            sucursal=sucursal,
            nombre='Caja Comercial',
            estado='abierta',
            saldo_inicial=Decimal('0.00'),
            saldo_actual=Decimal('0.00'),
            empleado_actual=empleado,
            fecha_apertura=timezone.now(),
        )
        unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-VENTA-001',
            unidad_medida=unidad,
            stock_actual=10,
            stock_reservado=0,
            stock_minimo=2,
            costo_compra=Decimal('50.00'),
            precio_venta=Decimal('120.00'),
            costo_unitario=Decimal('50.00'),
            costo_unitario_proveedor=Decimal('50.00'),
        )

        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            venta_tipo='repuesto',
            estado='pendiente_cobro',
            monto_total=Decimal('240.00'),
            iva=Decimal('24.00'),
            vendedor=empleado,
        )
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal('120.00'),
            subtotal=Decimal('240.00'),
        )

        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock_actual, 10)
        self.assertEqual(repuesto.stock_reservado, 2)

        response = self.client.post(
            reverse('cobrar_pedido', kwargs={'pedido_id': pedido.id}),
            {
                'monto_recibido': '240',
                'metodo_pago': 'Efectivo',
                'sucursal': str(sucursal.id),
                'caja': str(caja.id),
            },
        )

        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'pagado')
        self.assertTrue(pedido.pagos.exists())
        caja.refresh_from_db()
        self.assertEqual(caja.saldo_actual, Decimal('240.00'))

        pedido.confirmar_entrega_repuesto()
        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock_actual, 8)
        self.assertEqual(repuesto.stock_reservado, 0)
