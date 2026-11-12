from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from seguridad_usuarios.models import Empleado, UsuarioPerfil
from importaciones.models import Importacion
from inventario.models import Repuesto, Vehiculo, MarcaVehiculo, ModeloVehiculo
from configuraciones_maestras.models import Moneda, Proveedor
from .forms import ClienteForm, ContactoClienteForm, ItemPedidoForm
from .models import Cliente, Pedido, ItemPedido, ProductoBuscado, SeleccionProductoBuscado, ContactoCliente


class ClienteFormTests(TestCase):
    def test_cliente_form_no_incluye_telefono_y_direccion(self):
        form = ClienteForm()

        self.assertNotIn('telefono', form.fields)
        self.assertNotIn('direccion', form.fields)

    def test_contacto_form_incluye_direccion(self):
        form = ContactoClienteForm()

        self.assertIn('direccion', form.fields)


class ClienteSeedCommandTests(TestCase):
    def test_crear_clientes_prueba_crea_clientes_y_contactos(self):
        call_command('crear_clientes_prueba', verbosity=0)

        fisico = Cliente.objects.get(documento_identidad='1234567')
        juridico = Cliente.objects.get(ruc='80012345-6')

        self.assertEqual(fisico.tipo_persona, 'FISICA')
        self.assertEqual(fisico.ruc, '1234567-0')
        self.assertEqual(fisico.telefono, '')
        self.assertEqual(fisico.direccion, '')

        self.assertTrue(ContactoCliente.objects.filter(cliente=fisico).exists())
        contacto_fisico = fisico.contactos.first()
        self.assertTrue(contacto_fisico.telefono)
        self.assertTrue(contacto_fisico.direccion)

        self.assertEqual(juridico.tipo_persona, 'JURIDICA')
        self.assertTrue(ContactoCliente.objects.filter(cliente=juridico).exists())


class ClienteListFilterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='filteruser',
            email='filter@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def test_lista_clientes_filtra_por_tipo_estado_y_busqueda(self):
        Cliente.objects.create(
            tipo_persona='FISICA',
            nombre='Ana',
            apellidos='Gómez',
            documento_identidad='1234567',
            ruc='1234567-0',
            estado=True,
        )
        Cliente.objects.create(
            tipo_persona='JURIDICA',
            razon_social='Consultora SRL',
            ruc='80012345-6',
            estado=True,
        )
        Cliente.objects.create(
            tipo_persona='FISICA',
            nombre='Luis',
            apellidos='Pérez',
            documento_identidad='7654321',
            ruc='7654321-0',
            estado=False,
        )

        response = self.client.get(f"{reverse('lista_clientes')}?tipo_persona=FISICA&estado=Activo&q=Ana")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana')
        self.assertNotContains(response, 'Consultora SRL')
        self.assertNotContains(response, 'Luis')

    def test_reporte_clientes_descarga_csv_con_filtros(self):
        Cliente.objects.create(
            tipo_persona='FISICA',
            nombre='Ana',
            apellidos='Gómez',
            documento_identidad='1234567',
            ruc='1234567-0',
            estado=True,
        )
        Cliente.objects.create(
            tipo_persona='JURIDICA',
            razon_social='Consultora SRL',
            ruc='80012345-6',
            estado=True,
        )

        response = self.client.get(f"{reverse('reporte_clientes')}?tipo_persona=FISICA&estado=Activo&q=Ana")

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertContains(response, 'Ana Gómez')
        self.assertNotContains(response, 'Consultora SRL')


class ClienteCreateViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='clientecreateuser',
            email='clientecreate@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def test_agregar_cliente_persiste_y_no_falla_por_conflicto_de_timezone(self):
        response = self.client.post(reverse('agregar_cliente'), {
            'tipo_persona': 'FISICA',
            'nombre': 'Ana',
            'apellidos': 'Gómez',
            'documento_identidad': '1234568',
            'ruc': '1234568-0',
            'email': 'ana@example.com',
            'estado': 'on',
            'contactos-TOTAL_FORMS': '0',
            'contactos-INITIAL_FORMS': '0',
            'contactos-MIN_NUM_FORMS': '0',
            'contactos-MAX_NUM_FORMS': '1000',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cliente.objects.filter(documento_identidad='1234568').exists())


class ItemPedidoFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def test_buscar_productos_api_devuelve_resultados_disponibles(self):
        # Código de 3 letras (SQLite no valida max_length, pero el modelo sí lo exige).
        moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso Argentino'})
        marca = MarcaVehiculo.objects.create(nombre='Marca Buscador')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Modelo Buscador')

        Repuesto.objects.create(
            nombre='Filtro de aire buscador',
            codigo_repuesto='FILTRO-BUSCADOR',
            costo_compra='10000',
            precio_venta='12000',
            stock_actual=2,
            stock_minimo=1,
            estado='disponible',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        Repuesto.objects.create(
            nombre='Filtro no visible',
            codigo_repuesto='FILTRO-NO-VISIBLE',
            costo_compra='9000',
            precio_venta='11000',
            stock_actual=0,
            stock_minimo=1,
            estado='vendido',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        Vehiculo.objects.create(
            nombre='Vehículo buscador',
            marca=marca,
            modelo=modelo,
            año=2023,
            codigo_chasis='1HGCM82633A004356',
            costo_compra='500000',
            precio_venta='600000',
            estado='disponible',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )

        response = self.client.get(reverse('buscar_productos_api'), {'tipo': 'repuesto', 'q': 'filtro'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        nombres_repuestos = [item['nombre'] for item in data['results']]
        self.assertIn('Filtro de aire buscador', nombres_repuestos)
        self.assertNotIn('Filtro no visible', nombres_repuestos)

        response = self.client.get(reverse('buscar_productos_api'), {'tipo': 'vehiculo', 'q': 'vehículo'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        nombres_vehiculos = [item['nombre'] for item in data['results']]
        self.assertTrue(any('buscador' in nombre.lower() for nombre in nombres_vehiculos))

    def test_item_pedido_form_filtra_productos_disponibles_para_ventas(self):
        moneda, _ = Moneda.objects.get_or_create(codigo='PYG', defaults={'nombre': 'Guaraní Paraguayo'})
        marca = MarcaVehiculo.objects.create(nombre='Marca Test')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Modelo Test')

        disponible_repuesto = Repuesto.objects.create(
            nombre='Filtro disponible',
            codigo_repuesto='FILTRO-DISP',
            costo_compra='10000',
            precio_venta='12000',
            stock_actual=2,
            stock_minimo=1,
            estado='disponible',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        no_disponible_repuesto = Repuesto.objects.create(
            nombre='Filtro no disponible',
            codigo_repuesto='FILTRO-NODISP',
            costo_compra='9000',
            precio_venta='11000',
            stock_actual=0,
            stock_minimo=1,
            estado='vendido',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        disponible_vehiculo = Vehiculo.objects.create(
            nombre='Vehículo disponible',
            marca=marca,
            modelo=modelo,
            año=2023,
            codigo_chasis='1HGCM82633A004351',
            costo_compra='500000',
            precio_venta='600000',
            estado='disponible',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        no_disponible_vehiculo = Vehiculo.objects.create(
            nombre='Vehículo no disponible',
            marca=marca,
            modelo=modelo,
            año=2022,
            codigo_chasis='1HGCM82633A004352',
            costo_compra='450000',
            precio_venta='550000',
            estado='reservado',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )

        form = ItemPedidoForm(pedido_tipo='venta')

        self.assertIn(disponible_repuesto, form.fields['repuesto'].queryset)
        self.assertNotIn(no_disponible_repuesto, form.fields['repuesto'].queryset)
        self.assertIn(disponible_vehiculo, form.fields['vehiculo'].queryset)
        self.assertNotIn(no_disponible_vehiculo, form.fields['vehiculo'].queryset)

    def test_item_pedido_form_filtra_productos_elegibles_para_busqueda_y_abastecimiento(self):
        moneda, _ = Moneda.objects.get_or_create(codigo='PYG', defaults={'nombre': 'Guaraní Paraguayo'})
        marca = MarcaVehiculo.objects.create(nombre='Marca Elegible')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Modelo Elegible')

        repuesto_elegible = Repuesto.objects.create(
            nombre='Filtro elegible',
            codigo_repuesto='FILTRO-ELEGIBLE',
            costo_compra='10000',
            precio_venta='12000',
            stock_actual=2,
            stock_minimo=1,
            estado='elegible_importacion',
            descripcion='Filtro para importación',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        repuesto_no_elegible = Repuesto.objects.create(
            nombre='Filtro no elegible',
            codigo_repuesto='FILTRO-NO-ELEGIBLE',
            costo_compra='9000',
            precio_venta='11000',
            stock_actual=0,
            stock_minimo=1,
            estado='vendido',
            descripcion='Filtro que no aplica',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        vehiculo_elegible = Vehiculo.objects.create(
            nombre='Vehículo elegible',
            marca=marca,
            modelo=modelo,
            año=2023,
            codigo_chasis='1HGCM82633A004353',
            costo_compra='500000',
            precio_venta='600000',
            estado='elegible_importacion',
            descripcion='Vehículo apto para importación',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        vehiculo_no_elegible = Vehiculo.objects.create(
            nombre='Vehículo no elegible',
            marca=marca,
            modelo=modelo,
            año=2022,
            codigo_chasis='1HGCM82633A004354',
            costo_compra='450000',
            precio_venta='550000',
            estado='reservado',
            descripcion='Vehículo no apto',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )

        form = ItemPedidoForm(pedido_tipo='abastecimiento')

        self.assertIn(repuesto_elegible, form.fields['repuesto'].queryset)
        self.assertNotIn(repuesto_no_elegible, form.fields['repuesto'].queryset)
        self.assertIn(vehiculo_elegible, form.fields['vehiculo'].queryset)
        self.assertNotIn(vehiculo_no_elegible, form.fields['vehiculo'].queryset)

    def test_buscar_productos_api_filtra_productos_elegibles_para_busqueda_y_abastecimiento(self):
        moneda = Moneda.objects.create(codigo='PYG2', nombre='Guaraní 2')
        marca = MarcaVehiculo.objects.create(nombre='Marca API')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Modelo API')

        Repuesto.objects.create(
            nombre='Filtro importable',
            codigo_repuesto='FILTRO-IMPORTABLE',
            costo_compra='10000',
            precio_venta='12000',
            stock_actual=2,
            stock_minimo=1,
            estado='elegible_importacion',
            descripcion='Filtro útil para importación',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        Repuesto.objects.create(
            nombre='Filtro no importable',
            codigo_repuesto='FILTRO-NO-IMPORTABLE',
            costo_compra='9000',
            precio_venta='11000',
            stock_actual=0,
            stock_minimo=1,
            estado='vendido',
            descripcion='Filtro que no aplica',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )
        Vehiculo.objects.create(
            nombre='Vehículo importable',
            marca=marca,
            modelo=modelo,
            año=2023,
            codigo_chasis='1HGCM82633A004355',
            costo_compra='500000',
            precio_venta='600000',
            estado='elegible_importacion',
            descripcion='Vehículo cómodo para importar',
            moneda_venta=moneda,
            moneda_compra_proveedor=moneda,
        )

        response = self.client.get(reverse('buscar_productos_api'), {'tipo': 'repuesto', 'q': 'importación', 'pedido_tipo': 'abastecimiento'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(item['nombre'] == 'Filtro importable' for item in data['results']))
        self.assertFalse(any(item['nombre'] == 'Filtro no importable' for item in data['results']))

        response = self.client.get(reverse('buscar_productos_api'), {'tipo': 'vehiculo', 'q': 'importar', 'pedido_tipo': 'busqueda'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(item['nombre'] == 'Vehículo importable' for item in data['results']))


class PedidoViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testadmin',
            email='admin@example.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(self.user)
        Moneda.objects.get_or_create(id=1, defaults={'codigo': 'PYG', 'nombre': 'Guaraníes'})
        self.cliente = Cliente.objects.create(
            tipo_persona='FISICA',
            nombre='Juan',
            apellidos='Pérez',
            documento_identidad='12345678',
        )

    def test_realizar_pedido_guarda_cuando_el_cliente_viene_del_contexto(self):
        response = self.client.post(
            reverse('realizar_pedido', kwargs={'cliente_id': self.cliente.pk}),
            {
                'observaciones': 'Pedido de prueba',
                'monto_total': '0',
                'iva': '0',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Pedido.objects.filter(cliente=self.cliente, observaciones='Pedido de prueba').exists())

    def test_realizar_pedido_asigna_tipo_venta(self):
        response = self.client.post(
            reverse('realizar_pedido', kwargs={'cliente_id': self.cliente.pk}),
            {
                'observaciones': 'Pedido de venta',
                'monto_total': '0',
                'iva': '0',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Pedido.objects.filter(cliente=self.cliente, tipo='venta').exists())

    def test_realizar_pedido_importacion_asigna_tipo_importacion(self):
        response = self.client.post(
            reverse('realizar_pedido_a_medida', kwargs={'cliente_id': self.cliente.pk}),
            {
                'observaciones': 'Pedido de importación',
                'monto_total': '0',
                'iva': '0',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Pedido.objects.filter(cliente=self.cliente, tipo='importacion').exists())

    def test_realizar_pedido_guarda_con_item_valido_y_fila_vacia(self):
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO123',
            estado='disponible',
            stock_actual=5,
            costo_compra='10000',
            precio_venta='15000'
        )

        response = self.client.post(
            reverse('realizar_pedido', kwargs={'cliente_id': self.cliente.pk}),
            {
                'observaciones': 'Pedido con item válido y fila vacía',
                'monto_total': '15000',
                'iva': '1500',
                'items-TOTAL_FORMS': '2',
                'items-INITIAL_FORMS': '0',
                'items-0-tipo_producto': 'repuesto',
                'items-0-repuesto': str(repuesto.pk),
                'items-0-cantidad': '1',
                'items-0-precio_unitario': '15000',
                'items-1-tipo_producto': 'repuesto',
            },
        )

        self.assertEqual(response.status_code, 302)
        pedido = Pedido.objects.get(observaciones='Pedido con item válido y fila vacía')
        self.assertTrue(ItemPedido.objects.filter(pedido=pedido).exists())

    def test_realizar_pedido_guarda_cuando_el_repuesto_seleccionado_desde_el_busqueda_no_cambia_el_tipo(self):
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO123-REGRESION',
            estado='disponible',
            stock_actual=5,
            costo_compra='10000',
            precio_venta='15000'
        )

        response = self.client.post(
            reverse('realizar_pedido', kwargs={'cliente_id': self.cliente.pk}),
            {
                'observaciones': 'Pedido con repuesto seleccionado desde el buscador',
                'monto_total': '15000',
                'iva': '1500',
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '0',
                'items-0-tipo_producto': 'vehiculo',
                'items-0-repuesto': str(repuesto.pk),
                'items-0-cantidad': '1',
                'items-0-precio_unitario': '15000',
            },
        )

        self.assertEqual(response.status_code, 302)
        pedido = Pedido.objects.get(observaciones='Pedido con repuesto seleccionado desde el buscador')
        self.assertTrue(ItemPedido.objects.filter(pedido=pedido, repuesto=repuesto).exists())

    def test_detalle_pedido_muestra_opcion_transferencia_para_venta_facturada_contado(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='facturado_contado',
            observaciones='Pedido de venta facturado',
            monto_total='100000',
            iva='10000',
        )

        response = self.client.get(reverse('detalle_pedido', kwargs={'pedido_id': pedido.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registrar transferencia bancaria')

    def test_detalle_pedido_muestra_accion_ver_para_producto_buscado(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='busqueda',
            estado='seleccion_pendiente',
            observaciones='Pedido de búsqueda',
            monto_total='0',
            iva='0',
        )
        producto = ProductoBuscado.objects.create(
            pedido=pedido,
            descripcion='Bujía de motor',
            cantidad=1,
        )
        SeleccionProductoBuscado.objects.create(producto_buscado=producto)

        response = self.client.get(reverse('detalle_pedido', kwargs={'pedido_id': pedido.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('confirmar_producto_buscado', kwargs={'pedido_id': pedido.pk, 'producto_buscado_id': producto.pk}),
        )
        self.assertContains(response, 'Ver')
        self.assertContains(
            response,
            reverse('imprimir_producto_buscado', kwargs={'pedido_id': pedido.pk, 'producto_buscado_id': producto.pk}),
        )
        self.assertContains(response, 'Imprimir')

    def test_imprimir_producto_buscado_muestra_detalle_de_impresion(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='busqueda',
            estado='seleccion_pendiente',
            observaciones='Pedido de búsqueda para imprimir',
            monto_total='0',
            iva='0',
        )
        producto = ProductoBuscado.objects.create(
            pedido=pedido,
            descripcion='Correa de distribución',
            cantidad=1,
        )

        response = self.client.get(reverse('imprimir_producto_buscado', kwargs={'pedido_id': pedido.pk, 'producto_buscado_id': producto.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Imprimir')
        self.assertContains(response, 'Correa de distribución')

    def test_aprobar_abastecimiento_cambia_estado_y_guarda_motivo(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='abastecimiento',
            estado='busqueda_abastecimiento',
            observaciones='Pedido de abastecimiento',
            monto_total='0',
            iva='0',
        )

        response = self.client.post(
            reverse('aprobar_rechazar_abastecimiento', kwargs={'pedido_id': pedido.pk}),
            {
                'accion': 'aprobar',
                'motivo': 'Se confirmó la búsqueda para abastecimiento',
            },
        )

        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'abastecimiento_aprobado')
        self.assertEqual(pedido.motivo_cancelacion, 'Se confirmó la búsqueda para abastecimiento')

    def test_actualizar_item_pedido_abastecimiento(self):
        from decimal import Decimal
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='abastecimiento',
            estado='busqueda_abastecimiento',
            observaciones='Pedido de abastecimiento',
            monto_total=Decimal('100.00'),
            iva=Decimal('10.00'),
        )
        repuesto = Repuesto.objects.create(
            nombre='Filtro',
            codigo_repuesto='FILTRO-TEST',
            stock_actual=0,
            costo_compra=Decimal('25.00'),
        )
        item = ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=repuesto,
            cantidad=5,
            precio_unitario=Decimal('50.00'),
        )

        response = self.client.post(
            reverse('actualizar_item_pedido', kwargs={'pedido_id': pedido.pk, 'item_id': item.pk}),
            {
                'cantidad': '10',
                'precio_unitario': '75.50',

            },
        )

        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 10)
        self.assertEqual(item.precio_unitario, Decimal('75.50'))
        self.assertEqual(item.subtotal, Decimal('755.00'))

    def test_editar_pedido_muestra_el_formulario_sin_error(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            observaciones='Pedido para editar',
            monto_total='0',
            iva='0',
        )

        response = self.client.get(reverse('editar_pedido', kwargs={'pedido_id': pedido.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Pedido')

    def test_editar_pedido_muestra_selector_de_moneda_en_items(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            observaciones='Pedido con item',
            monto_total='0',
            iva='0',
        )
        moneda, _ = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dólar'})
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-EDIT',
            stock_actual=2,
            costo_compra='10000',
            precio_venta='15000',
        )
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=repuesto,
            cantidad=1,
            precio_unitario='15000',
            subtotal='15000',
            moneda=moneda,
        )

        response = self.client.get(reverse('editar_pedido', kwargs={'pedido_id': pedido.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="items-0-moneda"')

    def test_obtener_precio_repuesto_devuelve_datos_de_compra(self):
        moneda, _ = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dólar'})
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO123',
            stock_actual=5,
            costo_compra='10000',
            precio_venta='15000',
            cantidad_a_comprar=4,
            moneda_compra_proveedor=moneda,
            costo_unitario_proveedor='12000',
        )

        response = self.client.get(reverse('obtener_precio_repuesto', kwargs={'repuesto_id': repuesto.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cantidad_a_comprar'], '4')
        self.assertEqual(response.json()['cantidad_producto'], '4')
        self.assertEqual(response.json()['precio_unitario'], '12000.00')
        self.assertEqual(response.json()['moneda_codigo'], 'USD')
        self.assertEqual(response.json()['moneda_id'], str(moneda.pk))

    def test_obtener_precio_vehiculo_devuelve_precio_de_venta(self):
        marca = MarcaVehiculo.objects.create(nombre='Toyota')
        modelo = ModeloVehiculo.objects.create(nombre='Corolla', marca=marca)
        vehiculo = Vehiculo.objects.create(
            nombre='Toyota Corolla',
            marca=marca,
            modelo=modelo,
            año=2020,
            kilometraje=12000,
            codigo_chasis='1HGCM82633A004352',
            costo_compra='10000000',
            precio_venta='18000000',
        )

        response = self.client.get(reverse('obtener_precio_vehiculo', kwargs={'vehiculo_id': vehiculo.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['precio_venta'], '18000000.00')
        self.assertEqual(response.json()['precio_unitario'], '18000000.00')
        self.assertEqual(response.json()['cantidad_producto'], '1')

    def test_realizar_pedido_de_vehiculo_reserva_el_vehiculo(self):
        marca = MarcaVehiculo.objects.create(nombre='Toyota')
        modelo = ModeloVehiculo.objects.create(nombre='Corolla', marca=marca)
        vehiculo = Vehiculo.objects.create(
            nombre='Toyota Corolla',
            marca=marca,
            modelo=modelo,
            año=2020,
            kilometraje=12000,
            codigo_chasis='1HGCM82633A004353',
            costo_compra='10000000',
            precio_venta='18000000',
        )

        response = self.client.post(
            reverse('realizar_pedido', kwargs={'cliente_id': self.cliente.pk}),
            {
                'observaciones': 'Pedido de vehículo reservado',
                'monto_total': '0',
                'iva': '0',
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '0',
                'items-0-tipo_producto': 'vehiculo',
                'items-0-vehiculo': str(vehiculo.pk),
                'items-0-cantidad': '1',
                'items-0-precio_unitario': '18000000',
            },
        )

        self.assertEqual(response.status_code, 302)
        vehiculo.refresh_from_db()
        self.assertEqual(vehiculo.estado, 'reservado')

    def test_realizar_pedido_asigna_al_vendedor_actual(self):
        empleado = Empleado.objects.create(nombre='Ana', apellidos='Gómez')
        perfil, _ = UsuarioPerfil.objects.get_or_create(user=self.user)
        perfil.empleado = empleado
        perfil.save()

        self.client.post(
            reverse('realizar_pedido', kwargs={'cliente_id': self.cliente.pk}),
            {
                'observaciones': 'Pedido con vendedor',
                'monto_total': '0',
                'iva': '0',
            },
        )

        pedido = Pedido.objects.get(observaciones='Pedido con vendedor')
        self.assertEqual(pedido.vendedor, empleado)

    def test_agregar_pedido_asigna_al_vendedor_actual(self):
        empleado = Empleado.objects.create(nombre='Luis', apellidos='Torres')
        perfil, _ = UsuarioPerfil.objects.get_or_create(user=self.user)
        perfil.empleado = empleado
        perfil.save()

        self.client.post(
            reverse('agregar_pedido'),
            {
                'cliente': self.cliente.pk,
                'observaciones': 'Pedido agregado directamente',
                'monto_total': '0',
                'iva': '0',
            },
        )

        pedido = Pedido.objects.get(observaciones='Pedido agregado directamente')
        self.assertEqual(pedido.vendedor, empleado)

    def test_aprobar_pedido_cambia_a_estado_aprobado(self):
        pedido = Pedido.objects.create(cliente=self.cliente, estado='pendiente', tipo='venta')

        response = self.client.post(reverse('aprobar_pedido', kwargs={'pedido_id': pedido.pk}))

        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'aprobado')

    def test_pedido_busqueda_inicia_en_espera_de_busqueda(self):
        pedido = Pedido.objects.create(cliente=self.cliente, tipo='busqueda', estado='pendiente')

        self.assertEqual(pedido.estado, 'espera_de_busqueda')

    def test_crear_pedido_abastecimiento_para_repuesto_bajo_stock_y_prevenir_duplicados(self):
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO-ABAST',
            stock_actual=1,
            stock_minimo=5,
            costo_compra='10000',
            precio_venta='15000',
        )

        pedido = repuesto.crear_pedido_abastecimiento(
            cantidad=3,
            descripcion='Abastecimiento inicial',
            cliente=self.cliente,
        )

        self.assertEqual(pedido.tipo, 'abastecimiento')
        self.assertEqual(pedido.estado, 'busqueda_abastecimiento')
        self.assertEqual(pedido.repuesto_a_abastecer, repuesto)
        self.assertEqual(pedido.items.count(), 1)
        self.assertEqual(repuesto.estado, 'pendiente_importacion')

        with self.assertRaises(ValidationError):
            repuesto.crear_pedido_abastecimiento(cantidad=2, descripcion='Duplicado', cliente=self.cliente)

    def test_pedido_busqueda_repuesto_avanza_hasta_aprobacion(self):
        pedido = Pedido.objects.create(cliente=self.cliente, tipo='busqueda', estado='espera_de_busqueda')

        pedido.buscar()
        pedido.ingresar_repuesto()
        pedido.aprobar_repuesto()
        pedido.refresh_from_db()

        self.assertEqual(pedido.estado, 'buqueda_concluida_aprobada')

    def test_pedido_busqueda_vehiculo_avanza_hasta_confirmar_eleccion(self):
        marca = MarcaVehiculo.objects.create(nombre='Toyota')
        modelo = ModeloVehiculo.objects.create(nombre='Corolla', marca=marca)
        vehiculo = Vehiculo.objects.create(
            nombre='Toyota Corolla',
            marca=marca,
            modelo=modelo,
            año=2020,
            kilometraje=12000,
            codigo_chasis='1HGCM82633A004355',
            costo_compra='10000000',
            precio_venta='18000000',
            estado='elegible_importacion',
        )
        pedido = Pedido.objects.create(cliente=self.cliente, tipo='busqueda', estado='espera_de_busqueda')

        pedido.buscar()
        pedido.ingresar_lista_vehiculos()
        pedido.confirmar_eleccion(vehiculo)
        pedido.refresh_from_db()
        vehiculo.refresh_from_db()

        self.assertEqual(pedido.estado, 'buqueda_concluida_aprobada')
        self.assertEqual(vehiculo.estado, 'pendiente_importacion')

    def test_enviar_pedido_a_cobranzas_cambia_estado(self):
        pedido = Pedido.objects.create(cliente=self.cliente, estado='aprobado', tipo='venta')

        response = self.client.post(reverse('enviar_a_cobranzas', kwargs={'pedido_id': pedido.pk}))

        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'cobranzas')

    def test_pedido_venta_tiene_transiciones_fsm_para_aprobacion(self):
        pedido = Pedido.objects.create(cliente=self.cliente, estado='pendiente_aprovacion', tipo='venta', venta_tipo='vehiculo')

        self.assertIn('aprobado', [transition.target for transition in pedido.get_available_state_transitions()])

    def test_crear_importacion_desde_pedido_abastecimiento(self):
        pedido = Pedido.objects.create(cliente=self.cliente, tipo='abastecimiento', estado='seleccion_confirmada')
        producto = ProductoBuscado.objects.create(pedido=pedido, descripcion='Filtro de aceite', cantidad=2)
        SeleccionProductoBuscado.objects.create(
            producto_buscado=producto,
            estado='encontrado',
            precio_unitario='15000',
            aprobado_seo=True,
        )

        importacion = pedido.crear_importacion_desde_abastecimiento()

        self.assertTrue(Importacion.objects.filter(pedido_origen=pedido).exists())
        self.assertEqual(importacion.pedido_origen, pedido)

    def test_comprar_pedido_aprobado_importa_y_guarda_factura(self):
        proveedor = Proveedor.objects.create(nombre='Proveedor Compra', razon_social='Proveedor Compra', ruc='8003333330003')
        pedido = Pedido.objects.create(cliente=self.cliente, tipo='busqueda', estado='buqueda_concluida_aprobada')
        producto = ProductoBuscado.objects.create(pedido=pedido, descripcion='Filtro de aceite', cantidad=2)
        SeleccionProductoBuscado.objects.create(
            producto_buscado=producto,
            estado='encontrado',
            precio_unitario='15000',
            aprobado_seo=True,
        )

        importacion = pedido.comprar_a_proveedor(
            proveedor=proveedor,
            numero_factura='FAC-001',
            observaciones='Factura cargada',
        )

        pedido.refresh_from_db()
        self.assertEqual(importacion.proveedor, proveedor)
        self.assertEqual(pedido.proveedor_compra, proveedor)
        self.assertEqual(pedido.numero_factura, 'FAC-001')
        self.assertTrue(pedido.pago_realizado)
        self.assertEqual(pedido.estado, 'en_proceso')

    def test_cargar_factura_por_vista_guarda_archivo_y_numero(self):
        pedido = Pedido.objects.create(cliente=self.cliente, tipo='abastecimiento', estado='seleccion_confirmada')
        repuesto = Repuesto.objects.create(
            nombre='Producto de prueba',
            codigo_repuesto='PROD-TEST',
            stock_actual=0,
            costo_compra=Decimal('100.00'),
        )
        producto_buscado = ProductoBuscado.objects.create(
            pedido=pedido,
            descripcion='Producto de prueba'
        )
        seleccion = SeleccionProductoBuscado.objects.create(
            producto_buscado=producto_buscado,
            estado='encontrado',
            repuesto=repuesto,
            precio_unitario=Decimal('100.00'),
            precio_total=Decimal('100.00'),
            aprobado_seo=True,
        )
        archivo = SimpleUploadedFile('factura.pdf', b'pdf-bytes', content_type='application/pdf')

        response = self.client.post(
            reverse('cargar_factura_pedido', kwargs={'pedido_id': pedido.pk}),
            {
                'numero_factura': 'FAC-777',
                'fecha_factura': '2026-07-07',
                'factura_pdf': archivo,
                'observaciones': 'Factura cargada desde la web',
            },
        )

        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.numero_factura, 'FAC-777')
        self.assertTrue(pedido.factura_pdf)
        self.assertEqual(pedido.observaciones, 'Factura cargada desde la web')

    def test_facturar_pedido_venta_contado_para_vehiculo_cambia_estado_a_vendido(self):
        marca = MarcaVehiculo.objects.create(nombre='Toyota')
        modelo = ModeloVehiculo.objects.create(nombre='Corolla', marca=marca)
        vehiculo = Vehiculo.objects.create(
            nombre='Toyota Corolla',
            marca=marca,
            modelo=modelo,
            año=2020,
            kilometraje=12000,
            codigo_chasis='1HGCM82633A004354',
            costo_compra='10000000',
            precio_venta='18000000',
            estado='reservado',
        )
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='aprobado',
            venta_tipo='vehiculo',
            monto_total=Decimal('18000000.00'),
            iva=Decimal('1800000.00')
        )
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='vehiculo',
            vehiculo=vehiculo,
            cantidad=1,
            precio_unitario=Decimal('18000000.00')
        )

        pedido.facturar_pedido_venta_contado()
        vehiculo.refresh_from_db()

        self.assertEqual(pedido.estado, 'facturado_contado')
        self.assertEqual(vehiculo.estado, 'vendido')

    def test_facturar_pedido_venta_contado_para_repuesto(self):
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='FILTRO123',
            stock_actual=10,
            costo_compra='10000',
            precio_venta='15000'
        )
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='aprobado',
            venta_tipo='repuesto',
            monto_total=Decimal('15000.00'),
            iva=Decimal('1500.00')
        )
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal('15000.00')
        )

        pedido.facturar_pedido_venta_contado()
        pedido.refresh_from_db()

        self.assertEqual(pedido.estado, 'facturado_contado')
        self.assertFalse(pedido.pago_realizado)

    def test_confirmar_pago_desde_facturado_contado(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='facturado_contado',
            venta_tipo='repuesto',
            monto_total=Decimal('15000.00'),
            iva=Decimal('1500.00')
        )

        pedido.confirmar_pago()
        pedido.refresh_from_db()

        self.assertEqual(pedido.estado, 'pagado')
        self.assertTrue(pedido.pago_realizado)

    def test_crear_item_de_pedido_reserva_stock_para_repuesto(self):
        repuesto = Repuesto.objects.create(
            nombre='Filtro de aire',
            codigo_repuesto='FILTRO789',
            stock_actual=5,
            costo_compra='12000',
            precio_venta='18000'
        )
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='pendiente_cobro',
            venta_tipo='repuesto',
            monto_total=Decimal('36000.00'),
            iva=Decimal('3600.00')
        )

        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal('18000.00')
        )
        repuesto.refresh_from_db()

        self.assertEqual(repuesto.stock_actual, 5)
        self.assertEqual(repuesto.stock_reservado, 2)

    def test_cancelar_pedido_libera_reserva_de_repuesto(self):
        repuesto = Repuesto.objects.create(
            nombre='Bujía',
            codigo_repuesto='BUJIA001',
            stock_actual=4,
            costo_compra='5000',
            precio_venta='8000'
        )
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='pendiente_cobro',
            venta_tipo='repuesto',
            monto_total=Decimal('16000.00'),
            iva=Decimal('1600.00')
        )
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal('8000.00')
        )

        pedido.cancelar()
        repuesto.refresh_from_db()

        self.assertEqual(pedido.estado, 'cancelado')
        self.assertEqual(repuesto.stock_reservado, 0)

    def test_confirmar_entrega_repuesto_descuenta_stock_y_completa(self):
        repuesto = Repuesto.objects.create(
            nombre='Filtro aire',
            codigo_repuesto='FILTRO456',
            stock_actual=5,
            costo_compra='12000',
            precio_venta='18000'
        )
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='facturado_contado',
            venta_tipo='repuesto',
            monto_total=Decimal('36000.00'),
            iva=Decimal('3600.00'),
            pago_realizado=True
        )
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='repuesto',
            repuesto=repuesto,
            cantidad=2,
            precio_unitario=Decimal('18000.00')
        )

        pedido.confirmar_entrega_repuesto()
        pedido.refresh_from_db()
        repuesto.refresh_from_db()

        self.assertEqual(pedido.estado, 'completado')
        self.assertEqual(repuesto.stock_actual, 3)

    def test_transferencia_vehiculo_workflow(self):
        from inventario.models import MarcaVehiculo, ModeloVehiculo, TipoTransmision

        marca = MarcaVehiculo.objects.create(nombre='Toyota')
        tipo_vehiculo = TipoTransmision.objects.create(nombre='Automática')
        modelo = ModeloVehiculo.objects.create(marca=marca, nombre='Hilux', tipo_vehiculo=None)
        vehiculo = Vehiculo.objects.create(
            nombre='Toyota Hilux',
            marca=marca,
            modelo=modelo,
            año=2024,
            kilometraje=0,
            codigo_chasis='1HGBH41JXMN109186',
            estado='disponible',
            costo_compra='40000000',
            precio_venta='50000000',
            transmision=tipo_vehiculo,
        )
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tipo='venta',
            estado='facturado_contado',
            venta_tipo='vehiculo',
            monto_total=Decimal('50000000.00'),
            iva=Decimal('5000000.00'),
            pago_realizado=True
        )
        ItemPedido.objects.create(
            pedido=pedido,
            tipo_producto='vehiculo',
            vehiculo=vehiculo,
            cantidad=1,
            precio_unitario=Decimal('50000000.00')
        )

        from django.utils import timezone
        fecha = timezone.now()
        pedido.programar_transferencia(fecha)
        pedido.refresh_from_db()
        self.assertEqual(pedido.fecha_transferencia.replace(microsecond=0), fecha.replace(microsecond=0))

        pedido.iniciar_transferencia()
        self.assertEqual(pedido.estado, 'transferencia_en_tramite')
