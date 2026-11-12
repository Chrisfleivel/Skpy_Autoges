"""
Cierre de un embarque de importación contra el inventario.

El cierre es el momento en que la importación deja de ser un documento y pasa
a ser **inventario real**:

- Los **vehículos** quedan con su costo landed desglosado por tipo de gasto
  (flete, aduana, extras...), con la tasa de cambio aplicada y su referencia
  auditables.
- Los **repuestos** ingresan al depósito destino con su costo unitario en
  guaraníes y generan el movimiento de stock correspondiente.

Todo se calcula en la moneda base del sistema (USD, ver
`ARQUITECTURA_DIVISAS.md`) y se convierte a guaraníes con la tasa del día,
que queda registrada en el producto.

Dos funciones:

- `previsualizar_cierre()`: devuelve los números **sin** tocar nada, para
  mostrarlos en pantalla antes de confirmar.
- `ejecutar_cierre()`: aplica el cierre (en una sola transacción) y deja el
  embarque en estado CERRADO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from configuraciones_maestras.models import Moneda, TasaCambio
from importaciones.calculos import lineas_de_prorrateo, repartir_gastos_por_tipo
from inventario.models import MovimientoStock
from inventario.services import registrar_entrada

MONEDA_BASE = 'USD'
MONEDA_LOCAL = 'PYG'

# Mapeo del tipo de gasto al campo de costo del producto (ver `Producto`).
# Los dos primeros valores son el campo de monto y el de su moneda.
MAPEO_COSTOS = {
    'FLETE': 'costo_flete1',
    'ARANCEL': 'costo_aduana_paraguaya',
    'DESPACHANTE': 'costo_aduana_paraguaya',
    'PUERTO': 'costo_aduana_extrangera',
    'TRANSPORTE_INTERNO': 'costo_flete2',
    'SEGURO': 'costo_extra',
    'COMISION_BANCARIA': 'costo_extra',
    'OTRO': 'costo_extra',
}

# Campo de moneda que acompaña a cada campo de costo.
MONEDA_DE_COSTO = {
    'costo_flete1': 'moneda_flete1',
    'costo_aduana_paraguaya': 'moneda_costo_aduana_paraguaya',
    'costo_aduana_extrangera': 'moneda_aduana_extrangera',
    'costo_flete2': 'moneda_costo_flete2',
    'costo_extra': 'moneda_costo_extra',
}

TIPO_VEHICULO = 'vehiculo'
TIPO_REPUESTO = 'repuesto'
TIPO_SIN_PRODUCTO = 'sin_producto'


@dataclass
class LineaCierre:
    """Costo de cierre de un ítem del embarque."""

    item_id: int
    descripcion: str
    tipo: str
    producto: object
    cantidad: int
    item: object = None
    fob_usd: Decimal = Decimal('0')
    gastos: dict = field(default_factory=dict)
    gastos_usd: Decimal = Decimal('0')
    landed_usd: Decimal = Decimal('0')
    landed_usd_unitario: Decimal = Decimal('0')
    costo_unitario_pyg: Decimal = Decimal('0')
    avisos: list = field(default_factory=list)


@dataclass
class ResultadoCierre:
    """Resultado del análisis (y de la ejecución) del cierre."""

    ok: bool = True
    mensaje: str = ''
    bloqueos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    lineas: list = field(default_factory=list)
    tasa: object = None
    fecha_tasa: object = None
    deposito: object = None
    total_fob_usd: Decimal = Decimal('0')
    total_landed_usd: Decimal = Decimal('0')
    total_costo_pyg: Decimal = Decimal('0')

    @property
    def puede_cerrarse(self) -> bool:
        return self.ok and not self.bloqueos


def fecha_de_cierre(embarque):
    """Fecha que define la tasa a aplicar: la de recepción, o la de hoy."""
    return embarque.fecha_recepcion or timezone.localdate()


def tasa_aplicable(fecha):
    """Tasa USD→PYG vigente a la fecha indicada (la más reciente que no la supere)."""
    return TasaCambio.objects.filter(
        moneda_origen=MONEDA_BASE,
        moneda_destino=MONEDA_LOCAL,
        fecha__lte=fecha,
    ).order_by('-fecha').first()


def _resolver_tasa(fecha, tasa, usuario):
    """
    Devuelve `(tasa, error)`.

    `tasa` puede ser:
    - `None`: se busca la tasa vigente.
    - una instancia de `TasaCambio`: se usa tal cual.
    - un número: se registra como la tasa del día (y queda auditada).
    """
    if isinstance(tasa, TasaCambio):
        return tasa, None

    if tasa not in (None, ''):
        try:
            valor = Decimal(str(tasa))
        except (TypeError, ValueError):
            return None, 'La tasa de cambio no es un número válido.'
        if valor <= 0:
            return None, 'La tasa de cambio debe ser mayor que cero.'

        existente = TasaCambio.objects.filter(
            moneda_origen=MONEDA_BASE,
            moneda_destino=MONEDA_LOCAL,
            fecha=fecha,
        ).first()
        if existente is not None:
            if existente.valor != valor:
                # Las tasas históricas no se tocan: hacen falta para la
                # auditoría de DNIT (ver ARQUITECTURA_DIVISAS.md).
                return None, (
                    f'Ya hay una tasa registrada para el {fecha} ({existente.valor}) y las '
                    'tasas históricas no se pueden modificar. Cargá la tasa correcta en '
                    'Configuraciones maestras.'
                )
            return existente, None

        try:
            return TasaCambio.registrar(
                moneda_origen=MONEDA_BASE,
                moneda_destino=MONEDA_LOCAL,
                valor=valor,
                fecha=fecha,
                usuario=usuario,
            ), None
        except IntegrityError:
            return None, (
                f'Ya existe una tasa registrada para el {fecha}. '
                'Revise Configuraciones maestras.'
            )

    encontrada = tasa_aplicable(fecha)
    if encontrada is None:
        return None, (
            f'No hay tasa de cambio {MONEDA_BASE}→{MONEDA_LOCAL} vigente al {fecha}. '
            'Carguela en Configuraciones maestras antes de cerrar el embarque.'
        )
    return encontrada, None


def _moneda_base():
    """Instancia de la moneda base (USD), creándola si falta."""
    Moneda.ensure_defaults()
    return Moneda.objects.get(codigo=MONEDA_BASE)


def previsualizar_cierre(embarque, *, fecha=None, tasa=None, usuario=None) -> ResultadoCierre:
    """
    Calcula el cierre del embarque **sin** modificar nada.

    Devuelve un `ResultadoCierre` con los números por ítem y la lista de
    `bloqueos` (lo que impide cerrarlo) y `avisos` (lo que conviene revisar).
    """
    from importaciones.models import Embarque

    fecha = fecha or fecha_de_cierre(embarque)
    resultado = ResultadoCierre()
    resultado.deposito = embarque.deposito_destino

    # --- Estado del embarque -------------------------------------------
    if not embarque.puede_pasar_a(Embarque.Estado.CERRADO):
        resultado.bloqueos.append(
            f'El embarque está en estado {embarque.get_estado_display()}: '
            f'solo se puede cerrar desde {Embarque.Estado.RECIBIDO}.'
        )

    # --- Prorrateo ------------------------------------------------------
    if not embarque.gastos_prorrateados:
        resultado.bloqueos.append('Los gastos todavía no fueron prorrateados entre los ítems.')
    if embarque.items.filter(costo_prorrateado__isnull=True).exists():
        resultado.bloqueos.append('Hay ítems sin costo landed asignado.')

    # --- Moneda de la factura -------------------------------------------
    monedas = set(
        embarque.items.exclude(factura_item__isnull=True)
        .values_list('factura_item__factura__moneda', flat=True)
    )
    monedas.discard(None)
    if monedas - {MONEDA_BASE}:
        resultado.bloqueos.append(
            'La factura del embarque debe estar en USD (moneda base del sistema) '
            'para poder cerrar a inventario.'
        )

    # --- Tasa de cambio --------------------------------------------------
    tasa_obj, error_tasa = _resolver_tasa(fecha, tasa, usuario)
    if error_tasa:
        resultado.bloqueos.append(error_tasa)
    else:
        resultado.tasa = tasa_obj
        resultado.fecha_tasa = tasa_obj.fecha

    # --- Depósito destino ------------------------------------------------
    tiene_repuestos = embarque.items.filter(factura_item__repuesto__isnull=False).exists()
    if tiene_repuestos and not embarque.deposito_destino_id:
        resultado.bloqueos.append(
            'Indique el depósito de destino: el embarque tiene repuestos para ingresar a stock.'
        )

    # --- Cálculo ----------------------------------------------------------
    if tasa_obj is not None and embarque.gastos_prorrateados:
        _calcular_lineas(embarque, tasa_obj, resultado)

    resultado.ok = not resultado.bloqueos
    if resultado.ok:
        resultado.mensaje = 'El embarque se puede cerrar a inventario.'
    else:
        resultado.mensaje = ' '.join(resultado.bloqueos)
    return resultado


def _calcular_lineas(embarque, tasa, resultado: ResultadoCierre) -> None:
    """Arma las líneas de costo del cierre."""
    items = list(
        embarque.items.select_related(
            'factura_item__factura',
            'factura_item__vehiculo',
            'factura_item__repuesto',
        )
    )
    gastos = list(embarque.gastos.filter(es_costeable=True))
    bases = lineas_de_prorrateo(items)
    reparto = repartir_gastos_por_tipo(gastos, bases)

    for item, base in zip(items, bases):
        factura_item = item.factura_item
        cantidad = base['cantidad'] or 1
        fob = base['base']
        detalle = reparto['detalle'].get(item.pk, {})

        # El total prorrateado guardado es el aprobado por el usuario: es el
        # que se muestra en pantalla y el que se usa para el costo landed.
        gastos_usd = item.costo_prorrateado or Decimal('0')
        desglose = reparto['totales'].get(item.pk, Decimal('0'))
        if desglose != gastos_usd:
            resultado.avisos.append(
                f'{base["descripcion"]}: el desglose por tipo de gasto ({desglose}) '
                f'no coincide con el costo prorrateado guardado ({gastos_usd}). '
                'Volvé a prorratear los gastos.'
            )

        landed = fob + gastos_usd
        unitario = (landed / Decimal(cantidad)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        costo_pyg = (unitario * Decimal(str(tasa.valor))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if factura_item.vehiculo_id:
            tipo = TIPO_VEHICULO
            producto = factura_item.vehiculo
            if cantidad != 1:
                resultado.avisos.append(
                    f'{base["descripcion"]}: el ítem agrupa {cantidad} unidades '
                    'pero es un vehículo (cada vehículo es único).'
                )
        elif factura_item.repuesto_id:
            tipo = TIPO_REPUESTO
            producto = factura_item.repuesto
        else:
            tipo = TIPO_SIN_PRODUCTO
            producto = None
            resultado.avisos.append(
                f'{base["descripcion"]}: el ítem no tiene vehículo ni repuesto '
                'asociado, así que no ingressa al inventario.'
            )

        linea = LineaCierre(
            item_id=item.pk,
            descripcion=base['descripcion'],
            tipo=tipo,
            producto=producto,
            cantidad=cantidad,
            item=item,
            fob_usd=fob,
            gastos={tipo_gasto: monto for tipo_gasto, monto in detalle.items()},
            gastos_usd=gastos_usd,
            landed_usd=landed,
            landed_usd_unitario=unitario,
            costo_unitario_pyg=costo_pyg,
        )
        resultado.lineas.append(linea)
        resultado.total_fob_usd += fob
        resultado.total_landed_usd += landed
        resultado.total_costo_pyg += costo_pyg * cantidad


def _aplicar_costos_vehiculo(linea: LineaCierre, tasa, moneda_usd) -> None:
    """Carga el costo landed del vehículo, desglosado por tipo de gasto."""
    vehiculo = linea.producto

    vehiculo.costo_compra_provedor_total = linea.fob_usd
    vehiculo.moneda_compra_proveedor = moneda_usd

    por_campo = {}
    for tipo_gasto, monto in linea.gastos.items():
        campo = MAPEO_COSTOS.get(tipo_gasto, 'costo_extra')
        por_campo[campo] = por_campo.get(campo, Decimal('0')) + monto

    for campo, monto in por_campo.items():
        setattr(vehiculo, campo, monto)
        setattr(vehiculo, MONEDA_DE_COSTO[campo], moneda_usd)

    # Campos informativos (editable=False): costo FOB y costo landed, en USD.
    vehiculo.costo_fob = linea.fob_usd
    vehiculo.costo_total = linea.landed_usd

    vehiculo.tasa_aplicada = tasa.valor
    vehiculo.tasa_cambio = tasa
    vehiculo.save()


def _aplicar_entrada_repuesto(linea: LineaCierre, tasa, moneda_usd, deposito, usuario, embarque) -> None:
    """Ingresa el repuesto al depósito destino con su costo en guaraníes."""
    repuesto = linea.producto

    registrar_entrada(
        repuesto,
        deposito,
        linea.cantidad,
        linea.costo_unitario_pyg,
        tipo=MovimientoStock.Tipo.ENTRADA_COMPRA,
        embarque_item=linea.item,
        usuario=usuario,
        referencia=f'Embarque {embarque.pk}',
        motivo=f'Recepción de embarque {embarque.bl_numero or embarque.pk}',
    )

    repuesto.refresh_from_db()
    repuesto.costo_unitario_proveedor = linea.landed_usd_unitario
    repuesto.moneda_compra_proveedor = moneda_usd
    repuesto.tasa_aplicada = tasa.valor
    repuesto.tasa_cambio = tasa
    repuesto.save()


@transaction.atomic
def ejecutar_cierre(embarque, *, usuario=None, fecha=None, tasa=None) -> ResultadoCierre:
    """
    Cierra el embarque a inventario.

    Escribe los costos de los vehículos, ingresa los repuestos al depósito
    destino y deja el embarque en estado CERRADO. Todo en una sola
    transacción: si algo falla, no queda nada a medias.
    """
    resultado = previsualizar_cierre(embarque, fecha=fecha, tasa=tasa, usuario=usuario)
    if not resultado.ok:
        raise ValidationError(resultado.mensaje or 'No se puede cerrar el embarque a inventario.')

    if MovimientoStock.objects.filter(embarque_item__embarque=embarque).exists():
        raise ValidationError(
            'Este embarque ya tiene movimientos de stock: no se puede cerrar a inventario dos veces.'
        )

    moneda_usd = _moneda_base()

    for linea in resultado.lineas:
        if linea.tipo == TIPO_VEHICULO:
            _aplicar_costos_vehiculo(linea, resultado.tasa, moneda_usd)
        elif linea.tipo == TIPO_REPUESTO:
            _aplicar_entrada_repuesto(
                linea, resultado.tasa, moneda_usd, resultado.deposito, usuario, embarque
            )

    embarque.cambiar_estado(
        embarque.Estado.CERRADO,
        usuario=usuario,
        nota='Cierre a inventario',
    )
    return resultado
