"""Verificación manual de la Fase 4 contra la BD de desarrollo.

Reproduce el caso real: los tres documentos (factura, B/L y liquidación)
pertenecen a operaciones distintas. La conciliación debe informar sin bloquear.
Ejecutar con: venv64/Scripts/python scripts/verificar_fase4_conciliacion.py
"""
import os
import sys
from datetime import date
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skpy_autogest_project.settings')
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
    DocumentoAdjunto,
    Embarque,
    EmbarqueContenedor,
    EmbarqueItem,
)

MARCA = 'TMP-F4-'


def limpiar():
    for factura in FacturaComercial.objects.filter(numero__startswith=MARCA):
        for orden in factura.ordenes_pago.all():
            if orden.pago_exterior_id:
                pago = orden.pago_exterior
                orden.pago_exterior = None
                orden.save(update_fields=['pago_exterior', 'updated_at'])
                if pago.gasto_comision_id:
                    pago.gasto_comision.delete()
                pago.delete()
            orden.delete()
        EmbarqueItem.objects.filter(factura_item__factura=factura).delete()
        factura.delete()
    EmbarqueItem.objects.filter(embarque__referencia_interna__startswith=MARCA).delete()
    EmbarqueContenedor.objects.filter(
        embarque__referencia_interna__startswith=MARCA).delete()
    Embarque.objects.filter(referencia_interna__startswith=MARCA).delete()
    Proveedor.objects.filter(nombre__startswith=MARCA).delete()


def main():
    limpiar()

    cliente = Client()
    cliente.force_login(User.objects.get(username='chris'))

    proveedor = Proveedor.objects.create(
        nombre='TMP-F4 Proveedor', razon_social='TMP-F4 Proveedor SA',
        tipo_persona='JURIDICA')

    # --- Documento 1: factura comercial de 8 vehículos --------------------
    factura_bl = FacturaComercial.objects.create(
        proveedor=proveedor, numero=MARCA + 'BL', fecha=date(2026, 8, 26),
        moneda='USD', total_declarado=Decimal('25150.00'))
    item_bl = FacturaItem.objects.create(
        factura=factura_bl, descripcion='Hyundai Tucson 2011', cantidad=8,
        precio_unitario=Decimal('3143.75'), chasis='KMHJU81VBBU197503')
    factura_bl.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)

    # --- Documento 2: B/L de otra operación (4 vehículos) ------------------
    embarque = Embarque.objects.create(
        referencia_interna=MARCA + 'EMB', bl_numero=MARCA + 'MEDUKC733517',
        puerto_carga='INCHEON, KOREA', puerto_descarga='IQUIQUE, CHILE',
        destino_final='ASUNCION, PARAGUAY', fecha_embarque=date(2026, 8, 20),
        estado=Embarque.Estado.PROGRAMADO)
    contenedor = EmbarqueContenedor.objects.create(
        embarque=embarque, numero=MARCA + 'MEDUKC733517', tipo='40HC',
        peso_bruto_kg=Decimal('6030.00'))
    EmbarqueItem.objects.create(
        embarque=embarque, factura_item=item_bl, contenedor=contenedor,
        cantidad=4, chasis_bl='KMHJU81VBBU197503')
    DocumentoAdjunto.objects.create(
        embarque=embarque, tipo=DocumentoAdjunto.Tipo.BL,
        archivo=__import__('django.core.files.uploadedfile', fromlist=['SimpleUploadedFile'])
        .SimpleUploadedFile('bl.pdf', b'%PDF-1.4'), descripcion='B/L original')

    # --- Documento 3: liquidación de otra operación ------------------------
    factura_liq = FacturaComercial.objects.create(
        proveedor=proveedor, numero=MARCA + 'LIQ', fecha=date(2026, 8, 26),
        moneda='USD', total_declarado=Decimal('12000.00'))
    FacturaItem.objects.create(
        factura=factura_liq, descripcion='Kia Sportage', cantidad=4,
        precio_unitario=Decimal('3000.00'))
    factura_liq.cambiar_estado(FacturaComercial.Estado.CONFIRMADA)
    orden = OrdenPagoExterior.objects.create(
        tipo_documento_remitente='RUC', numero_documento_remitente='8001234560001',
        remitente_nombre='TMP-F4 Proveedor', forma_pago='TRANSFERENCIA',
        numero_cuenta='1234567890', moneda=Moneda.objects.get(codigo='USD'),
        importe_orden=Decimal('12000.00'), comision_orden=Decimal('85.00'),
        referencia_op='136294', numero_lote='132115',
        fecha_operacion=date(2026, 8, 26), ordenante='TMP-F4 Proveedor SA',
        beneficiario='KIA CORPORATION', pais_beneficiario='KR',
        cuenta_beneficiaria='620-123456-789',
        motivo_transferencia='INVOICE 20260826', concepto='FONDOS PROPIOS',
        cotizacion=Decimal('1'), factura=factura_liq)
    pago = PagoExterior.objects.create(
        factura=factura_liq, fecha_operacion=date(2026, 8, 26), moneda='USD',
        importe=Decimal('12000.00'), comision=Decimal('85.00'),
        forma_pago=PagoExterior.FormaPago.DEBITO_CUENTA, referencia_op='136294')
    orden.pago_exterior = pago
    orden.save(update_fields=['pago_exterior', 'updated_at'])

    # --- Documento 4: factura todavía sin nada ----------------------------
    factura_vacia = FacturaComercial.objects.create(
        proveedor=proveedor, numero=MARCA + 'VACIA', fecha=date(2026, 9, 1),
        moneda='USD', total_declarado=Decimal('5000.00'))

    # --- Pantallas --------------------------------------------------------
    r = cliente.get('/importaciones/conciliacion/')
    print('lista           ->', r.status_code,
          '| título:', b'Conciliaci' in r.content,
          '| filas:', r.content.count(b'Ver detalle'))

    r = cliente.get('/importaciones/conciliacion/?estado=DIFERENCIA')
    print('filtro dif.    ->', r.status_code)

    r = cliente.get('/importaciones/conciliacion/?q=TMP-F4-BL')
    print('filtro busq.   ->', r.status_code,
          '| encuentra la factura:', b'TMP-F4-BL' in r.content)

    r = cliente.get('/importaciones/conciliacion/exportar/')
    print('exportar CSV    ->', r.status_code, '|', r['Content-Type'])

    for factura in (factura_bl, factura_liq, factura_vacia):
        r = cliente.get(f'/importaciones/conciliacion/{factura.pk}/')
        linea = ' | '.join(
            h.concepto for h in __import__(
                'importaciones.conciliacion', fromlist=['conciliar_factura']
            ).conciliar_factura(factura).hallazgos
        )
        print(f'detalle {factura.numero:18} ->', r.status_code, '|', linea)

    # --- La conciliación no bloquea: todo se pudo guardar -------------------
    print('documentos guardados ->',
          'facturas:', FacturaComercial.objects.filter(numero__startswith=MARCA).count(),
          '| embarques:', Embarque.objects.filter(referencia_interna__startswith=MARCA).count(),
          '| liquidaciones:', OrdenPagoExterior.objects.filter(referencia_op='136294').count(),
          '| pagos:', PagoExterior.objects.filter(referencia_op='136294').count())

    limpiar()
    print('limpieza -> facturas:',
          FacturaComercial.objects.filter(numero__startswith=MARCA).count(),
          '| embarques:',
          Embarque.objects.filter(referencia_interna__startswith=MARCA).count(),
          '| pagos:', PagoExterior.objects.filter(referencia_op='136294').count())


if __name__ == '__main__':
    main()
