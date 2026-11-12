"""
Tests de la Fase 5: cierre de un embarque de importación contra el inventario.

El cierre es el momento en que la importación pasa a ser inventario real:

- Los vehículos quedan con su costo landed desglosado por tipo de gasto y con
  la tasa de cambio aplicada (auditoría DNIT).
- Los repuestos ingresan al depósito destino con su costo en guaraníes y
  generan el movimiento de stock correspondiente.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Proveedor, TasaCambio
from core.models import TransicionInvalida
from importaciones.cierre import ejecutar_cierre, previsualizar_cierre
from importaciones.models import Embarque, EmbarqueContenedor, GastoImportacion
from importaciones.services import prorratear_costos
from inventario.models import (
    Deposito,
    MarcaVehiculo,
    ModeloVehiculo,
    MovimientoStock,
    Repuesto,
    StockRepuesto,
    UnidadMedida,
    Vehiculo,
)


class CierreImportacionTestCase(TestCase):
    """Base con proveedor, factura en USD, vehículo, repuesto y tasa de cambio."""

    fecha_recepcion = date(2026, 3, 10)
    valor_tasa = Decimal('7500.0000')

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Importación',
            razon_social='Proveedor Importación SA',
            documento_identidad='1234567',
            telefono='123',
            email='provimp@test.com',
            direccion='Calle 1',
            ruc='1234567',
            tipo_persona='JURIDICA',
        )
        self.tasa = TasaCambio.registrar(
            moneda_origen='USD',
            moneda_destino='PYG',
            valor=self.valor_tasa,
            fecha=self.fecha_recepcion,
        )
        self.deposito = Deposito.objects.create(
            codigo='DEPO-F5',
            nombre='Depósito Importación',
            ubicacion='Asunción',
            activo=True,
        )
        self.marca = MarcaVehiculo.objects.create(nombre='Toyota', pais_origen='Japón')
        self.modelo = ModeloVehiculo.objects.create(marca=self.marca, nombre='Corolla', estado=True)
        self.vehiculo = Vehiculo.objects.create(
            proveedor=self.proveedor,
            nombre='Corolla',
            marca=self.marca,
            modelo=self.modelo,
            año=2024,
            codigo_chasis='1HGCM82633A004352',
            costo_compra=Decimal('0.00'),
            precio_venta=Decimal('30000.00'),
        )
        self.unidad = UnidadMedida.objects.create(nombre='Unidad', abreviatura='UND')
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro importado',
            codigo_repuesto='F5-001',
            unidad_medida=self.unidad,
            stock_actual=0,
            stock_minimo=2,
            costo_compra=Decimal('0.00'),
            precio_venta=Decimal('20.00'),
            costo_unitario_proveedor=Decimal('0.00'),
        )

    def _factura(self, numero='FAC-F5', moneda='USD'):
        return FacturaComercial.objects.create(
            proveedor=self.proveedor,
            numero=numero,
            fecha=date(2026, 1, 5),
            total_declarado=Decimal('1500.00'),
            moneda=moneda,
        )

    def _embarque(self, estado=Embarque.Estado.RECIBIDO, bl='BL-F5'):
        return Embarque.objects.create(
            referencia_interna=f'EMB-{bl}',
            bl_numero=bl,
            fecha_embarque=date(2026, 2, 1),
            fecha_recepcion=self.fecha_recepcion,
            estado=estado,
            deposito_destino=self.deposito,
        )

    def _agregar_item(self, embarque, factura_item, cantidad=1, numero='CONT-F5'):
        contenedor = EmbarqueContenedor.objects.create(
            embarque=embarque, numero=numero, tipo='40HC')
        return embarque.items.create(
            factura_item=factura_item,
            cantidad=cantidad,
            chasis_bl='1HGCM82633A004352',
            contenedor=contenedor,
        )

    def _gasto(self, embarque, tipo=GastoImportacion.Tipo.FLETE, monto='100.00',
               criterio=GastoImportacion.Criterio.POR_VALOR):
        return GastoImportacion.objects.create(
            embarque=embarque,
            tipo=tipo,
            descripcion=tipo,
            monto=Decimal(monto),
            moneda='USD',
            tipo_cambio=Decimal('1'),
            criterio_prorrateo=criterio,
        )

    # ------------------------------------------------------------------
    # Vista previa
    # ------------------------------------------------------------------
    def test_la_vista_previa_calcula_el_costo_landed_por_unidad(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque, GastoImportacion.Tipo.FLETE, '300.00')
        prorratear_costos(embarque)

        resultado = previsualizar_cierre(embarque)

        self.assertTrue(resultado.ok, resultado.mensaje)
        linea = resultado.lineas[0]
        self.assertEqual(linea.fob_usd, Decimal('1500.00'))
        self.assertEqual(linea.gastos_usd, Decimal('300.00'))
        self.assertEqual(linea.landed_usd, Decimal('1800.00'))
        # 1800 USD x 7500 = 13.500.000 PYG
        self.assertEqual(linea.costo_unitario_pyg, Decimal('13500000.00'))

    def test_la_vista_previa_avisa_si_falta_el_prorrateo(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)

        resultado = previsualizar_cierre(embarque)

        self.assertFalse(resultado.ok)
        self.assertTrue(any('prorrateados' in b for b in resultado.bloqueos))

    def test_la_vista_previa_avisa_si_no_hay_tasa_de_cambio(self):
        TasaCambio.objects.all().delete()
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        resultado = previsualizar_cierre(embarque)

        self.assertFalse(resultado.ok)
        self.assertTrue(any('tasa de cambio' in b for b in resultado.bloqueos))

    def test_la_vista_previa_exige_deposito_si_hay_repuestos(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, repuesto=self.repuesto,
            descripcion='Filtro', cantidad=2, precio_unitario=Decimal('50.00'))
        embarque = self._embarque()
        embarque.deposito_destino = None
        embarque.save(update_fields=['deposito_destino'])
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        resultado = previsualizar_cierre(embarque)

        self.assertFalse(resultado.ok)
        self.assertTrue(any('depósito de destino' in b for b in resultado.bloqueos))

    # ------------------------------------------------------------------
    # Cierre de vehículos
    # ------------------------------------------------------------------
    def test_el_cierre_carga_el_costo_landed_del_vehiculo(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque, GastoImportacion.Tipo.FLETE, '300.00')
        self._gasto(embarque, GastoImportacion.Tipo.ARANCEL, '200.00')
        prorratear_costos(embarque)

        resultado = ejecutar_cierre(embarque)

        self.assertTrue(resultado.ok)
        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.costo_compra_provedor_total, Decimal('1500.00'))
        self.assertEqual(self.vehiculo.costo_flete1, Decimal('300.00'))
        self.assertEqual(self.vehiculo.costo_aduana_paraguaya, Decimal('200.00'))
        self.assertEqual(self.vehiculo.costo_total_importacion, Decimal('2000.00'))
        self.assertEqual(self.vehiculo.tasa_aplicada, self.valor_tasa)
        self.assertEqual(self.vehiculo.tasa_cambio, self.tasa)
        # Costo en guaraníes: 2000 USD x 7500
        self.assertEqual(self.vehiculo.costo_compra, Decimal('15000000.00'))
        self.assertEqual(self.vehiculo.costo_fob, Decimal('1500.00'))
        self.assertEqual(self.vehiculo.costo_total, Decimal('2000.00'))

    def test_el_cierre_deja_el_embarque_cerrado(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        ejecutar_cierre(embarque)

        embarque.refresh_from_db()
        self.assertEqual(embarque.estado, Embarque.Estado.CERRADO)

    def test_el_cierre_no_se_puede_repetir(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)
        ejecutar_cierre(embarque)

        # Se vuelve atrás en el estado para intentar un segundo cierre.
        Embarque.objects.filter(pk=embarque.pk).update(estado=Embarque.Estado.RECIBIDO)

        with self.assertRaises(ValidationError):
            ejecutar_cierre(embarque)

    def test_el_cierre_falla_si_la_factura_no_esta_en_usd(self):
        factura = self._factura(moneda='PYG')
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        with self.assertRaises(ValidationError):
            ejecutar_cierre(embarque)

    def test_el_cierre_registra_la_tasa_informada_si_no_hay_una(self):
        TasaCambio.objects.all().delete()
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        resultado = ejecutar_cierre(embarque, tasa=Decimal('7200'))

        self.assertTrue(resultado.ok)
        self.assertEqual(resultado.tasa.valor, Decimal('7200.0000'))
        self.assertTrue(
            TasaCambio.objects.filter(
                moneda_origen='USD', moneda_destino='PYG',
                fecha=self.fecha_recepcion, valor=Decimal('7200.0000'),
            ).exists()
        )
        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.tasa_aplicada, Decimal('7200.0000'))

    def test_el_cierre_no_modifica_una_tasa_historica(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        with self.assertRaises(ValidationError):
            ejecutar_cierre(embarque, tasa=Decimal('9999'))

        # La tasa del día sigue como estaba (auditoría DNIT).
        self.tasa.refresh_from_db()
        self.assertEqual(self.tasa.valor, self.valor_tasa)

    # ------------------------------------------------------------------
    # Cierre de repuestos
    # ------------------------------------------------------------------
    def test_el_cierre_ingresa_los_repuestos_al_deposito(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, repuesto=self.repuesto,
            descripcion='Filtro', cantidad=3, precio_unitario=Decimal('50.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item, cantidad=3)
        self._gasto(embarque, GastoImportacion.Tipo.FLETE, '150.00')
        prorratear_costos(embarque)

        ejecutar_cierre(embarque)

        stock = StockRepuesto.objects.get(repuesto=self.repuesto, deposito=self.deposito)
        self.assertEqual(stock.cantidad, 3)

        movimiento = MovimientoStock.objects.get(repuesto=self.repuesto)
        self.assertEqual(movimiento.tipo, MovimientoStock.Tipo.ENTRADA_COMPRA)
        self.assertEqual(movimiento.cantidad, 3)
        self.assertEqual(movimiento.deposito_destino, self.deposito)
        self.assertEqual(movimiento.saldo_posterior, 3)

        # Costo unitario: (50 FOB + 50 gastos) x 7500 = 750.000 PYG
        self.repuesto.refresh_from_db()
        self.assertEqual(self.repuesto.costo_unitario, Decimal('750000.00'))
        self.assertEqual(self.repuesto.tasa_aplicada, self.valor_tasa)
        self.assertEqual(self.repuesto.tasa_cambio, self.tasa)

    def test_el_cierre_no_crea_stock_si_no_hay_deposito(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, repuesto=self.repuesto,
            descripcion='Filtro', cantidad=3, precio_unitario=Decimal('50.00'))
        embarque = self._embarque()
        embarque.deposito_destino = None
        embarque.save(update_fields=['deposito_destino'])
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        with self.assertRaises(ValidationError):
            ejecutar_cierre(embarque)

        self.assertEqual(StockRepuesto.objects.filter(repuesto=self.repuesto).count(), 0)

    def test_el_cierre_descompone_los_gastos_en_los_campos_de_costo(self):
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        for tipo in (GastoImportacion.Tipo.FLETE, GastoImportacion.Tipo.ARANCEL,
                     GastoImportacion.Tipo.DESPACHANTE, GastoImportacion.Tipo.PUERTO,
                     GastoImportacion.Tipo.TRANSPORTE_INTERNO, GastoImportacion.Tipo.SEGURO):
            self._gasto(embarque, tipo, '100.00')
        prorratear_costos(embarque)

        ejecutar_cierre(embarque)

        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.costo_flete1, Decimal('100.00'))
        # Arancel y despachante van al mismo campo (aduana paraguaya).
        self.assertEqual(self.vehiculo.costo_aduana_paraguaya, Decimal('200.00'))
        self.assertEqual(self.vehiculo.costo_aduana_extrangera, Decimal('100.00'))
        self.assertEqual(self.vehiculo.costo_flete2, Decimal('100.00'))
        self.assertEqual(self.vehiculo.costo_extra, Decimal('100.00'))
        # 1500 FOB + 600 de gastos
        self.assertEqual(self.vehiculo.costo_total_importacion, Decimal('2100.00'))

    # ------------------------------------------------------------------
    # Prorrateo por criterio
    # ------------------------------------------------------------------
    def test_el_prorrateo_respeta_el_criterio_de_cada_gasto(self):
        factura = self._factura()
        item_vehiculo = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla', cantidad=1, precio_unitario=Decimal('1500.00'))
        item_repuesto = FacturaItem.objects.create(
            factura=factura, repuesto=self.repuesto,
            descripcion='Filtro', cantidad=1, precio_unitario=Decimal('100.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item_vehiculo, numero='CONT-1')
        self._agregar_item(embarque, item_repuesto, numero='CONT-2')

        # Un gasto por valor (se reparte 93.75 / 6.25) y otro por unidad (mitad y mitad).
        self._gasto(embarque, GastoImportacion.Tipo.FLETE, '100.00',
                    criterio=GastoImportacion.Criterio.POR_VALOR)
        self._gasto(embarque, GastoImportacion.Tipo.PUERTO, '60.00',
                    criterio=GastoImportacion.Criterio.POR_UNIDAD)

        prorratear_costos(embarque)

        # Vehículo: 93.75 (valor) + 30 (unidad) = 123.75
        # Repuesto: 6.25 (valor) + 30 (unidad) = 36.25
        self.assertEqual(embarque.items.get(factura_item=item_vehiculo).costo_prorrateado,
                         Decimal('123.75'))
        self.assertEqual(embarque.items.get(factura_item=item_repuesto).costo_prorrateado,
                         Decimal('36.25'))

    # ------------------------------------------------------------------
    # Vistas
    # ------------------------------------------------------------------
    def test_la_vista_de_cierre_cierra_el_embarque(self):
        user = self._login()
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        respuesta = self.client.post(
            reverse('cerrar_embarque', args=[embarque.pk]),
            {'deposito_destino': self.deposito.pk},
        )

        self.assertEqual(respuesta.status_code, 302)
        embarque.refresh_from_db()
        self.assertEqual(embarque.estado, Embarque.Estado.CERRADO)

    def test_la_vista_de_cierre_muestra_el_preview(self):
        self._login()
        factura = self._factura()
        item = FacturaItem.objects.create(
            factura=factura, vehiculo=self.vehiculo,
            descripcion='Corolla 2024', cantidad=1, precio_unitario=Decimal('1500.00'))
        embarque = self._embarque()
        self._agregar_item(embarque, item)
        self._gasto(embarque)
        prorratear_costos(embarque)

        respuesta = self.client.get(reverse('detalle_embarque', args=[embarque.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Cierre a inventario')
        # Costo unitario: (1500 FOB + 100 gastos) x 7500 = 12.000.000 PYG
        self.assertContains(respuesta, '12000000')

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _login(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(
            username='cierre_user', password='123456', is_superuser=True, is_staff=True)
        self.client.force_login(user)
        return user
