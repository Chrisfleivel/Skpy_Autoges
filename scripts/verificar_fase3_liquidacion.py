"""Verificación manual de la Fase 3 contra la BD de desarrollo.

Crea una operación temporal (factura + embarque + liquidación), recorre las
pantallas, registra el pago y deja la base como estaba.
Ejecutar con: venv64/Scripts/python scripts/verificar_fase3_liquidacion.py
"""
import os
import sys
from datetime import date, time
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skpy_autogest_project.settings')
# Asegura que la raíz del proyecto esté en sys.path para importar los settings.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
django.setup()

from django.contrib.auth.models import User
from django.test import Client

from compras.models import FacturaComercial, FacturaItem
from configuraciones_maestras.models import Moneda, OrdenPagoExterior, Proveedor
from finanzas.models import PagoExterior
from importaciones.models import (
    Embarque,
    EmbarqueContenedor,
    EmbarqueItem,
    GastoImportacion,
)

BASE = '/configuraciones_maestras/ordenes-pago-exterior/'
MARCA = 'TMP-'


def limpiar():
    OrdenPagoExterior.objects.filter(referencia_op='136294').update(pago_exterior=None)
    for pago in PagoExterior.objects.all():
        if pago.gasto_comision_id:
            pago.gasto_comision.delete()
        pago.delete()
    GastoImportacion.objects.filter(embarque__referencia_interna__startswith=MARCA).delete()
    OrdenPagoExterior.objects.filter(referencia_op='136294').delete()
    EmbarqueItem.objects.filter(embarque__referencia_interna__startswith=MARCA).delete()
    EmbarqueContenedor.objects.filter(embarque__referencia_interna__startswith=MARCA).delete()
    Embarque.objects.filter(referencia_interna__startswith=MARCA).delete()
    FacturaComercial.objects.filter(numero__startswith=MARCA).delete()
    Proveedor.objects.filter(nombre__startswith=MARCA).delete()


def main():
    limpiar()

    cliente = Client()
    cliente.force_login(User.objects.get(username='chris'))

    proveedor = Proveedor.objects.create(
        nombre='TMP Proveedor', razon_social='TMP', tipo_persona='JURIDICA')
    factura = FacturaComercial.objects.create(
        proveedor=proveedor, numero='TMP-20260826', fecha=date(2026, 8, 26),
        moneda='USD', total_declarado=Decimal('25150.00'))
    FacturaItem.objects.create(
        factura=factura, descripcion='Hyundai Tucson', cantidad=8,
        precio_unitario=Decimal('3143.75'))
    factura.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)

    embarque = Embarque.objects.create(
        referencia_interna='TMP-EMB', bl_numero='TMP-MEDUKC733517',
        fecha_embarque=date(2026, 8, 20), destino_final='ASUNCION')
    contenedor = EmbarqueContenedor.objects.create(
        embarque=embarque, numero='TMP-MEDUKC733517', tipo='40HC')
    EmbarqueItem.objects.create(
        embarque=embarque, factura_item=factura.items.first(),
        contenedor=contenedor, cantidad=4)

    orden = OrdenPagoExterior.objects.create(
        tipo_documento_remitente='RUC', numero_documento_remitente='8001234560001',
        remitente_nombre='SKPY Trading', forma_pago='TRANSFERENCIA',
        numero_cuenta='1234567890', moneda=Moneda.objects.get(codigo='USD'),
        importe_orden=Decimal('25150.00'), comision_orden=Decimal('85.00'),
        referencia_op='136294', numero_lote='132115', fecha_operacion=date(2026, 8, 26),
        hora_operacion=time(14, 30), usuario_banco='NVILLAMA',
        firmante='NERY VILLAMAYOR', ordenante='SKPY Trading S.A.',
        beneficiario='HYUNDAI MOTOR COMPANY', pais_beneficiario='KR',
        cuenta_beneficiaria='620-123456-789', motivo_transferencia='INVOICE 20260826',
        concepto='FONDOS PROPIOS', cotizacion=Decimal('1'))

    detalle = cliente.get(f'{BASE}detalle/{orden.pk}/')
    print('detalle        ->', detalle.status_code,
          '| referencia:', b'136294' in detalle.content,
          '| usuario banco:', b'NVILLAMA' in detalle.content,
          '| boton:', b'Registrar pago' in detalle.content)

    registro = cliente.get(f'{BASE}{orden.pk}/registrar-pago/')
    print('registrar GET  ->', registro.status_code,
          '| campo importe:', b'name="importe"' in registro.content)

    lista = cliente.get(BASE)
    print('lista          ->', lista.status_code,
          '| boton:', b'Registrar pago' in lista.content)

    alta = cliente.get(f'{BASE}agregar/')
    print('agregar        ->', alta.status_code,
          '| multipart:', b'multipart/form-data' in alta.content,
          '| archivo:', b'name="archivo"' in alta.content)

    respuesta = cliente.post(f'{BASE}{orden.pk}/registrar-pago/', {
        'factura': factura.pk, 'embarque': embarque.pk,
        'fecha_operacion': '2026-08-26', 'importe': '25150.00',
        'comision': '85.00', 'cotizacion': '', 'forma_pago': 'DEBITO_CUENTA',
        'referencia_op': '136294', 'numero_lote': '132115',
    })
    print('registrar POST ->', respuesta.status_code, respuesta.get('Location', ''))

    orden.refresh_from_db()
    pago = PagoExterior.objects.get()
    gasto = GastoImportacion.objects.get()
    factura.refresh_from_db()
    print('pago           ->', pago.importe, '+', pago.comision, pago.moneda,
          '| ref', pago.referencia_op, '| lote', pago.nro_lote,
          '| forma', pago.forma_pago)
    print('orden          ->', orden.estado, '| pago', orden.pago_exterior_id,
          '| factura', orden.factura_id, '| embarque', orden.embarque_id,
          '| total', orden.total_orden)
    print('gasto          ->', gasto.tipo, gasto.monto, gasto.moneda,
          '-> embarque', gasto.embarque_id)
    print('factura        ->', factura.estado, '| pagado', factura.monto_pagado,
          '| saldo', factura.saldo_pendiente)

    detalle = cliente.get(f'{BASE}detalle/{orden.pk}/')
    print('detalle tras pago ->', detalle.status_code,
          '| muestra pago:', b'Pago al exterior' in detalle.content)

    doble = cliente.post(f'{BASE}{orden.pk}/registrar-pago/', {
        'factura': factura.pk, 'embarque': embarque.pk,
        'fecha_operacion': '2026-08-26', 'importe': '1.00',
        'comision': '0.00', 'cotizacion': '', 'forma_pago': 'DEBITO_CUENTA',
        'referencia_op': '', 'numero_lote': '',
    })
    print('doble registro ->', doble.status_code, '| pagos:', PagoExterior.objects.count())

    limpiar()
    print('limpieza -> ordenes:', OrdenPagoExterior.objects.count(),
          '| pagos:', PagoExterior.objects.count(),
          '| gastos:', GastoImportacion.objects.count(),
          '| embarques:', Embarque.objects.count(),
          '| facturas:', FacturaComercial.objects.count())


if __name__ == '__main__':
    main()
