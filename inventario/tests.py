from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from clientes_pedidos.models import Cliente
from configuraciones_maestras.models import Moneda, Proveedor
from inventario.forms import RepuestoForm
from inventario.models import MarcaVehiculo, ModeloVehiculo, Repuesto, Vehiculo


class VehiculoCostTests(TestCase):
    def test_calcula_costo_total_importacion_en_guaranies(self):
        moneda_usd = Moneda.objects.create(codigo='USD', nombre='Dólar')
        moneda_pyg = Moneda.objects.create(codigo='PYG', nombre='Guaraní')
        marca = MarcaVehiculo.objects.create(nombre='Marca Test')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Modelo Test')
        vehiculo = Vehiculo.objects.create(
            nombre='Vehículo Test',
            marca=marca,
            modelo=modelo,
            año=2023,
            codigo_chasis='1HGCM82633A004352',
            costo_compra='100000',
            costo_compra_provedor_total='50000',
            moneda_compra_proveedor=moneda_pyg,
            costo_flete1='1000',
            moneda_flete1=moneda_usd,
            costo_aduana_paraguaya='1500',
            moneda_costo_aduana_paraguaya=moneda_pyg,
            tasa_aplicada='7500',
            moneda_costo_total_importacion=moneda_usd,
        )

        self.assertEqual(vehiculo.costo_total_importacion, Decimal('1006.87'))
        self.assertEqual(vehiculo.costo_compra, Decimal('7551525.00'))
        self.assertEqual(vehiculo.moneda_costo_total_importacion, moneda_usd)


class VehiculoFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='vehiculotester',
            email='vehiculotester@example.com',
            password='12345678',
        )
        self.proveedor = Proveedor.objects.create(
            tipo_persona='JURIDICA',
            razon_social='Proveedor Vehículo',
            nombre='Proveedor Vehículo',
        )

    def test_agregar_vehiculo_muestra_campo_proveedor(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('agregar_vehiculo'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="proveedor"')


class RepuestoCommandTests(TestCase):
    def test_cargar_repuestos_recrea_repuesto_sin_pedidos_y_lo_deja_disponible(self):
        Repuesto.objects.create(
            nombre='Filtro legado',
            codigo_repuesto='26320-2F000',
            costo_compra='10000',
            precio_venta='12000',
            stock_actual=1,
            stock_minimo=1,
            estado='elegible_importacion',
        )

        call_command('cargar_repuestos', verbosity=0)

        repuesto = Repuesto.objects.get(codigo_repuesto='26320-2F000')
        self.assertEqual(repuesto.estado, 'disponible')
        self.assertEqual(repuesto.nombre, 'Filtro de Aceite CRDi (Eco)')


class RepuestoFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='tester',
            email='tester@example.com',
            password='12345678',
        )
        Moneda.objects.get_or_create(codigo='PYG', defaults={'nombre': 'Guaraní'})
        self.proveedor = Proveedor.objects.create(
            tipo_persona='JURIDICA',
            razon_social='Proveedor Test',
            nombre='Proveedor Test',
        )

    def test_agregar_repuesto_prefills_provider_and_state(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('agregar_repuesto'), {'proveedor': self.proveedor.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['proveedor'], self.proveedor.pk)
        self.assertEqual(response.context['form'].initial['estado'], 'disponible')

    def test_agregar_repuesto_proveedor_prefills_provider_and_state(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('agregar_repuesto_proveedor'), {'proveedor': self.proveedor.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['proveedor'], self.proveedor.pk)
        self.assertEqual(response.context['form'].initial['estado'], 'elegible_importacion')

    def test_agregar_repuesto_muestra_campo_moneda_venta(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('agregar_repuesto'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="moneda_venta"')

    def test_formulario_repuesto_asegura_monedas_por_defecto(self):
        Moneda.objects.all().delete()

        form = RepuestoForm()
        codes = list(form.fields['moneda_venta'].queryset.values_list('codigo', flat=True))

        self.assertIn('PYG', codes)
        self.assertIn('USD', codes)

    def test_editar_repuesto_muestra_campo_moneda_venta(self):
        self.client.force_login(self.user)
        moneda = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dólar'})[0]
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aire',
            codigo_repuesto='FILTRO-002',
            costo_compra='10000',
            precio_venta='15000',
            stock_actual=2,
            stock_minimo=1,
            moneda_venta=moneda,
        )

        response = self.client.get(reverse('editar_repuesto', kwargs={'repuesto_id': repuesto.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="moneda_venta"')

    def test_save_normalizes_costo_compra_provedor_total(self):
        repuesto = Repuesto.objects.create(
            nombre='Filtro normalizado',
            codigo_repuesto='FILTRO-003',
            costo_compra='10000',
            precio_venta='15000',
            stock_actual=3,
            stock_minimo=1,
            costo_unitario_proveedor='12000',
            cantidad_a_comprar=4,
        )

        self.assertEqual(repuesto.costo_compra_provedor_total, Decimal('48000.00'))

    def test_detalle_repuesto_muestra_boton_editar_costos(self):
        self.client.force_login(self.user)
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aire',
            codigo_repuesto='FILTRO-004',
            costo_compra='10000',
            precio_venta='15000',
            stock_actual=2,
            stock_minimo=1,
        )

        response = self.client.get(reverse('detalle_repuesto', kwargs={'repuesto_id': repuesto.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-bs-target="#modalEditarCostos"')

    def test_detalle_repuesto_muestra_estado_de_pedido_de_abastecimiento(self):
        self.client.force_login(self.user)
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-006',
            costo_compra='10000',
            precio_venta='15000',
            stock_actual=0,
            stock_minimo=1,
        )
        cliente = Cliente.objects.create(nombre='Cliente Pedido', apellidos='Prueba', documento_identidad='1234567')

        repuesto.crear_pedido_abastecimiento(cantidad=2, descripcion='Pedido de prueba', cliente=cliente)

        response = self.client.get(reverse('detalle_repuesto', kwargs={'repuesto_id': repuesto.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pedido de abastecimiento en curso')
        self.assertContains(response, 'Búsqueda de Abastecimiento')


class RepuestoCostTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='costrepuesto',
            email='costrepuesto@example.com',
            password='12345678',
        )
        Moneda.objects.get_or_create(codigo='PYG', defaults={'nombre': 'Guaraní'})
        self.moneda_usd = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dólar'})[0]
        self.moneda_pyg = Moneda.objects.get(codigo='PYG')

    def test_editar_costos_repuesto_actualiza_costos_importacion(self):
        self.client.force_login(self.user)
        repuesto = Repuesto.objects.create(
            nombre='Filtro importado',
            codigo_repuesto='FILTRO-005',
            costo_compra='10000',
            precio_venta='15000',
            stock_actual=1,
            stock_minimo=0,
        )

        response = self.client.post(reverse('editar_costos_repuesto', kwargs={'repuesto_id': repuesto.pk}), {
            'costo_unitario_proveedor': '50000',
            'cantidad_a_comprar': '1',
            'moneda_compra_proveedor': str(self.moneda_pyg.pk),
            'costo_flete1': '1000',
            'moneda_flete1': str(self.moneda_usd.pk),
            'costo_aduana_paraguaya': '1500',
            'moneda_costo_aduana_paraguaya': str(self.moneda_pyg.pk),
            'tasa_aplicada': '7500',
        })

        repuesto.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(repuesto.costo_compra_provedor_total, Decimal('50000.00'))
        self.assertEqual(repuesto.costo_total_importacion, Decimal('1006.87'))
        self.assertEqual(repuesto.costo_compra, Decimal('7551525.00'))
        self.assertEqual(repuesto.moneda_costo_total_importacion, self.moneda_usd)


class RepuestoListTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='repuestolist',
            email='repuestolist@example.com',
            password='12345678',
        )

    def test_lista_repuestos_no_falla_con_valores_decimales_invalidos(self):
        self.client.force_login(self.user)
        Moneda.objects.get_or_create(codigo='PYG', defaults={'nombre': 'Guaraníes'})
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-001',
            costo_compra='10000',
            precio_venta='15000',
            stock_actual=3,
            stock_minimo=1,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE inventario_repuesto SET costo_unitario_proveedor = %s WHERE id = %s",
                ['NaN', repuesto.pk],
            )

        response = self.client.get(reverse('lista_repuestos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Filtro de aceite')
