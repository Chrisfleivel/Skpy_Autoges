"""
Servicios de las órdenes de pago al exterior (liquidaciones bancarias).

La liquidación es el documento bancario; el asiento contable vive en
`finanzas.PagoExterior`. Este módulo hace el puente entre ambos: registra
el pago a partir de la liquidación y deja la orden enlazada.
"""
from __future__ import annotations

import os
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction

from finanzas.services import registrar_pago_exterior

from .models import OrdenPagoExterior


def _copiar_archivo(orden: OrdenPagoExterior, pago):
    """Copia la liquidación escaneada al asiento financiero (copia propia)."""
    if not orden.archivo:
        return
    try:
        contenido = orden.archivo.read()
        extension = os.path.splitext(orden.archivo.name)[1] or '.jpg'
        nombre = f'{orden.referencia_op or "liquidacion"}_{orden.pk}{extension}'
        pago.archivo.save(nombre, ContentFile(contenido), save=False)
    except (OSError, ValueError):
        # Si el archivo no está disponible, el pago se registra igual.
        pass


@transaction.atomic
def registrar_pago_desde_orden(
    orden: OrdenPagoExterior,
    *,
    factura,
    fecha_operacion,
    importe,
    comision=Decimal('0'),
    cotizacion=None,
    embarque=None,
    forma_pago=None,
    referencia_op='',
    numero_lote='',
    usuario=None,
):
    """
    Registra el pago al exterior tomando los datos de la liquidación.

    El asiento financiero hereda del documento los datos bancarios, y la
    comisión se imputa al embarque indicado (si lo hay). La orden queda
    enlazada al pago y pasa a estado ENVIADA.
    """
    if orden.pago_exterior_id:
        raise ValidationError('La liquidación ya tiene un pago registrado.')

    if orden.moneda_id and factura.moneda != orden.moneda.codigo:
        raise ValidationError(
            f'La moneda de la factura ({factura.moneda}) no coincide con la de la liquidación '
            f'({orden.moneda.codigo}).'
        )

    datos = {
        'moneda': orden.moneda.codigo,
        'forma_pago': forma_pago or orden.forma_pago_finanzas,
        'referencia_op': referencia_op or orden.referencia_op or '',
        'nro_lote': numero_lote or orden.numero_lote or '',
        'ordenante': orden.ordenante or '',
        'cuenta_debito': orden.numero_cuenta or '',
        'banco_corresponsal': orden.banco_corresponsal.nombre if orden.banco_corresponsal else '',
        'banco_beneficiario': orden.banco_beneficiario.nombre if orden.banco_beneficiario else '',
        'pais_beneficiario': orden.pais_beneficiario or '',
        'cuenta_beneficiario': orden.cuenta_beneficiaria or '',
        'beneficiario': orden.beneficiario or '',
        'motivo_transferencia': orden.motivo_transferencia or '',
        'concepto': orden.concepto or '',
        'cotizacion': cotizacion if cotizacion else None,
    }

    pago = registrar_pago_exterior(
        factura,
        fecha_operacion=fecha_operacion,
        importe=importe,
        comision=comision,
        embarque=embarque,
        usuario=usuario,
        **datos,
    )

    _copiar_archivo(orden, pago)
    pago.save(update_fields=['archivo', 'actualizado'])

    orden.factura = factura
    orden.embarque = embarque
    orden.pago_exterior = pago
    orden.estado = OrdenPagoExterior.Estado.ENVIADA
    orden.save(update_fields=[
        'factura', 'embarque', 'pago_exterior', 'estado',
        'capital', 'comision', 'total', 'total_orden', 'updated_at',
    ])

    return pago
