"""
Tests del módulo de taller (mantenimientos).

Cubre lo que se corrigió del CRUD existente:

- El campo `descripcion` (estaba declarado dos veces) es único y obligatorio.
- El estado es uno solo y sigue las transiciones de `EstadoMixin`.
- La mano de obra va separada del costo de los repuestos.
- Los repuestos utilizados tienen cantidad y **descuentan stock** al finalizar.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.models import TransicionInvalida
from inventario.models import (
    Deposito,
    MantenimientoRepuesto,
    MantenimientoVehiculo,
    MarcaVehiculo,
    ModeloVehiculo,
    MovimientoStock,
    Repuesto,
    StockRepuesto,
    UnidadMedida,
    Vehiculo,
)


class TallerTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='taller_user', password='123456', is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

        self.deposito = Deposito.objects.create(
            codigo='TALLER',
            nombre='Depósito Taller',
            ubicacion='Asunción',
            activo=True,
        )
        self.unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        self.marca = MarcaVehiculo.objects.create(nombre='Toyota', pais_origen='Japón')
        self.modelo = ModeloVehiculo.objects.create(marca=self.marca, nombre='Corolla', estado=True)
        self.vehiculo = Vehiculo.objects.create(
            nombre='Corolla',
            marca=self.marca,
            modelo=self.modelo,
            **{'año': 2024},
            costo_compra=Decimal('0.00'),
            precio_venta=Decimal('30000.00'),
        )
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro de aceite',
            codigo_repuesto='TALL-001',
            unidad_medida=self.unidad,
            stock_actual=10,
            stock_minimo=2,
            costo_compra=Decimal('50.00'),
            precio_venta=Decimal('80.00'),
            costo_unitario_proveedor=Decimal('50.00'),
        )
        self.stock = StockRepuesto.objects.create(
            repuesto=self.repuesto, deposito=self.deposito, cantidad=10, reservado=0)

    def _mantenimiento(self, **campos):
        datos = dict(
            vehiculo=self.vehiculo,
            fecha_mantenimiento='2026-04-01',
            descripcion='Cambio de aceite y filtros',
            deposito=self.deposito,
            costo_mano_obra=Decimal('15000.00'),
        )
        datos.update(campos)
        return MantenimientoVehiculo.objects.create(**datos)

    def _linea(self, mantenimiento, cantidad=2, costo_unitario=None):
        return MantenimientoRepuesto.objects.create(
            mantenimiento=mantenimiento,
            repuesto=self.repuesto,
            cantidad=cantidad,
            costo_unitario=Decimal('50.00') if costo_unitario is None else costo_unitario,
        )

    # ------------------------------------------------------------------
    # Modelo
    # ------------------------------------------------------------------
    def test_la_descripcion_es_un_campo_unico_y_obligatorio(self):
        campos = [f.name for f in MantenimientoVehiculo._meta.get_fields()]
        self.assertEqual(campos.count('descripcion'), 1)

        campo = MantenimientoVehiculo._meta.get_field('descripcion')
        self.assertFalse(campo.null)
        self.assertEqual(campo.verbose_name, 'Descripción del Mantenimiento')

        with self.assertRaises(ValidationError):
            MantenimientoVehiculo.objects.create(
                vehiculo=self.vehiculo,
                fecha_mantenimiento='2026-04-01',
                descripcion='',
            ).full_clean()

    def test_el_mantenimiento_arranca_pendiente(self):
        mantenimiento = self._mantenimiento()

        self.assertEqual(mantenimiento.estado, MantenimientoVehiculo.Estado.PENDIENTE)

    def test_el_costo_total_suma_mano_de_obra_y_repuestos(self):
        mantenimiento = self._mantenimiento(costo_mano_obra=Decimal('15000.00'))
        self._linea(mantenimiento, cantidad=2, costo_unitario=Decimal('5000.00'))

        mantenimiento.refresh_from_db()

        self.assertEqual(mantenimiento.costo_repuestos, Decimal('10000.00'))
        self.assertEqual(mantenimiento.costo, Decimal('25000.00'))

    # ------------------------------------------------------------------
    # Estados
    # ------------------------------------------------------------------
    def test_no_se_puede_finalizar_sin_pasar_por_en_proceso(self):
        mantenimiento = self._mantenimiento()

        with self.assertRaises(TransicionInvalida):
            mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.FINALIZADO)

    def test_la_transicion_valida_inicia_el_trabajo(self):
        mantenimiento = self._mantenimiento()

        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.EN_PROCESO)

        mantenimiento.refresh_from_db()
        self.assertEqual(mantenimiento.estado, MantenimientoVehiculo.Estado.EN_PROCESO)

    def test_se_puede_cancelar_desde_pendiente(self):
        mantenimiento = self._mantenimiento()

        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.CANCELADO)

        mantenimiento.refresh_from_db()
        self.assertEqual(mantenimiento.estado, MantenimientoVehiculo.Estado.CANCELADO)

    # ------------------------------------------------------------------
    # Descuento de stock
    # ------------------------------------------------------------------
    def test_finalizar_descuenta_el_stock_de_los_repuestos(self):
        mantenimiento = self._mantenimiento()
        linea = self._linea(mantenimiento, cantidad=3)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.EN_PROCESO)

        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.FINALIZADO)

        self.stock.refresh_from_db()
        linea.refresh_from_db()
        mantenimiento.refresh_from_db()

        self.assertEqual(self.stock.cantidad, 7)
        self.assertTrue(mantenimiento.stock_descontado)
        self.assertIsNotNone(linea.movimiento)
        self.assertEqual(linea.movimiento.tipo, MovimientoStock.Tipo.SALIDA)
        self.assertEqual(linea.movimiento.cantidad, 3)
        self.assertEqual(linea.movimiento.deposito_origen, self.deposito)
        self.assertEqual(linea.movimiento.referencia, f'MANT-{mantenimiento.pk}')

    def test_el_stock_no_se_descuenta_dos_veces(self):
        mantenimiento = self._mantenimiento()
        self._linea(mantenimiento, cantidad=2)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.EN_PROCESO)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.FINALIZADO)

        # Aunque se llame de nuevo, el stock no se mueve.
        mantenimiento.descontar_stock()

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad, 8)
        self.assertEqual(
            MovimientoStock.objects.filter(
                repuesto=self.repuesto, tipo=MovimientoStock.Tipo.SALIDA).count(), 1)

    def test_no_se_puede_finalizar_sin_stock_suficiente(self):
        mantenimiento = self._mantenimiento()
        self._linea(mantenimiento, cantidad=50)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.EN_PROCESO)

        with self.assertRaises(TransicionInvalida):
            mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.FINALIZADO)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad, 10)

    def test_el_stock_descontado_no_vuelve_a_moverse(self):
        mantenimiento = self._mantenimiento()
        self._linea(mantenimiento, cantidad=2)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.EN_PROCESO)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.FINALIZADO)

        with self.assertRaises(TransicionInvalida):
            mantenimiento.validar_finalizado()

    # ------------------------------------------------------------------
    # Vistas
    # ------------------------------------------------------------------
    def test_la_vista_registra_un_mantenimiento_con_repuestos(self):
        respuesta = self.client.post(reverse('agregar_mantenimiento'), {
            'vehiculo': self.vehiculo.pk,
            'fecha_mantenimiento': '2026-04-01',
            'descripcion': 'Cambio de aceite',
            'observaciones': '',
            'costo_mano_obra': '15000.00',
            'deposito': self.deposito.pk,
            'repuestos-TOTAL_FORMS': '1',
            'repuestos-INITIAL_FORMS': '0',
            'repuestos-MIN_NUM_FORMS': '0',
            'repuestos-MAX_NUM_FORMS': '1000',
            'repuestos-0-repuesto': self.repuesto.pk,
            'repuestos-0-cantidad': '2',
            'repuestos-0-costo_unitario': '5000.00',
        })

        self.assertEqual(respuesta.status_code, 302)
        mantenimiento = MantenimientoVehiculo.objects.get()
        self.assertEqual(mantenimiento.descripcion, 'Cambio de aceite')
        self.assertEqual(mantenimiento.estado, MantenimientoVehiculo.Estado.PENDIENTE)
        self.assertEqual(mantenimiento.costo_repuestos, Decimal('10000.00'))
        self.assertEqual(mantenimiento.costo, Decimal('25000.00'))
        self.assertEqual(mantenimiento.repuestos.count(), 1)
        self.assertEqual(mantenimiento.repuestos.first().cantidad, 2)

    def test_la_vista_cambia_el_estado_y_finaliza(self):
        mantenimiento = self._mantenimiento()
        self._linea(mantenimiento, cantidad=2)

        respuesta = self.client.post(
            reverse('cambiar_estado_mantenimiento', args=[mantenimiento.pk]),
            {'estado': MantenimientoVehiculo.Estado.EN_PROCESO},
        )
        self.assertEqual(respuesta.status_code, 302)
        mantenimiento.refresh_from_db()
        self.assertEqual(mantenimiento.estado, MantenimientoVehiculo.Estado.EN_PROCESO)

        self.client.post(
            reverse('cambiar_estado_mantenimiento', args=[mantenimiento.pk]),
            {'estado': MantenimientoVehiculo.Estado.FINALIZADO},
        )
        mantenimiento.refresh_from_db()
        self.stock.refresh_from_db()
        self.assertEqual(mantenimiento.estado, MantenimientoVehiculo.Estado.FINALIZADO)
        self.assertEqual(self.stock.cantidad, 8)

    def test_la_vista_no_acepta_una_transicion_invalida(self):
        mantenimiento = self._mantenimiento()

        self.client.post(
            reverse('cambiar_estado_mantenimiento', args=[mantenimiento.pk]),
            {'estado': MantenimientoVehiculo.Estado.FINALIZADO},
        )

        mantenimiento.refresh_from_db()
        self.assertEqual(mantenimiento.estado, MantenimientoVehiculo.Estado.PENDIENTE)

    def test_un_mantenimiento_con_stock_descontado_no_se_puede_eliminar(self):
        mantenimiento = self._mantenimiento()
        self._linea(mantenimiento, cantidad=2)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.EN_PROCESO)
        mantenimiento.cambiar_estado(MantenimientoVehiculo.Estado.FINALIZADO)

        self.client.post(reverse('eliminar_mantenimiento', args=[mantenimiento.pk]))

        self.assertTrue(MantenimientoVehiculo.objects.filter(pk=mantenimiento.pk).exists())

    def test_el_listado_filtra_por_estado(self):
        pendiente = self._mantenimiento()
        finalizado = self._mantenimiento(descripcion='Otro servicio')
        finalizado.cambiar_estado(MantenimientoVehiculo.Estado.EN_PROCESO)
        finalizado.cambiar_estado(MantenimientoVehiculo.Estado.FINALIZADO)

        respuesta = self.client.get(reverse('lista_mantenimientos'), {
            'estado': MantenimientoVehiculo.Estado.FINALIZADO,
        })

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Otro servicio')
        self.assertNotContains(respuesta, 'Cambio de aceite y filtros')

    def test_el_detalle_muestra_los_costos_separados(self):
        mantenimiento = self._mantenimiento()
        self._linea(mantenimiento, cantidad=2, costo_unitario=Decimal('5000.00'))

        respuesta = self.client.get(reverse('detalle_mantenimiento', args=[mantenimiento.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Mano de obra')
        self.assertContains(respuesta, 'Repuestos')

    def test_el_navbar_tiene_la_entrada_del_taller(self):
        respuesta = self.client.get(reverse('lista_mantenimientos'))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn(reverse('lista_mantenimientos'), contenido)
        self.assertIn('Taller', contenido)
