"""
Siembra el inventario multi-depósito (`StockRepuesto`) con el stock heredado.

Hasta ahora el stock vivía solo en `Repuesto.stock_actual` (un único
depósito implícito). A partir de esta migración `StockRepuesto` pasa a ser la
fuente de verdad, así que el saldo heredado se adopta como físico del depósito
principal y queda documentado con un movimiento de entrada.

También repara la tabla `inventario_stockrepuesto` en las bases que quedaron
con la FK apuntando a `catalogo_repuesto` (la app `catalogo` está
deshabilitada y el modelo `Repuesto` mudó a `inventario`). Sin esarepair, en
esos ambientes cualquier alta de stock falla por integridad referencial.

Es una migración de datos de ida: no se revierte (el snapshot ya es la
realidad del inventario).
"""

from decimal import Decimal

from django.db import migrations

MOTIVO_SALDO_INICIAL = 'Saldo inicial migrado desde stock_actual'
TABLA_STOCK_REPUESTO = 'inventario_stockrepuesto'
TABLA_REPUESTO = 'inventario_repuesto'


def _tabla_existe(schema_editor, tabla):
    with schema_editor.connection.cursor() as cursor:
        return tabla in schema_editor.connection.introspection.table_names(cursor)


def _fk_apunta_a_inventario(schema_editor, tabla):
    """True si la FK de `repuesto` de la tabla apunta a `inventario_repuesto`."""
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, tabla)

    for info in constraints.values():
        if not info.get('foreign_key'):
            continue
        referenciada = info.get('references')
        if not referenciada:
            # PostgreSQL: (tabla, columna). SQLite: solo 'foreign_key'.
            referenciada = info.get('foreign_key')
        if referenciada and referenciada[0] == TABLA_REPUESTO:
            return True
    return False


def reparar_tabla_stock_repuesto(apps, schema_editor):
    """
    Reconstruye `inventario_stockrepuesto` si su FK apunta a la app `catalogo`.

    Es idempotente: si la tabla no existe o ya está bien, no hace nada.
    """
    StockRepuesto = apps.get_model('inventario', 'StockRepuesto')

    if not _tabla_existe(schema_editor, TABLA_STOCK_REPUESTO):
        return
    if _fk_apunta_a_inventario(schema_editor, TABLA_STOCK_REPUESTO):
        return

    filas = list(
        StockRepuesto.objects.values(
            'id', 'creado', 'actualizado', 'cantidad', 'reservado',
            'ubicacion', 'deposito_id', 'repuesto_id',
        )
    )

    schema_editor.execute(f'DROP TABLE "{TABLA_STOCK_REPUESTO}"')
    schema_editor.create_model(StockRepuesto)

    if filas:
        StockRepuesto.objects.bulk_create([
            StockRepuesto(
                id=fila['id'],
                creado=fila['creado'],
                actualizado=fila['actualizado'],
                cantidad=fila['cantidad'],
                reservado=fila['reservado'],
                ubicacion=fila['ubicacion'],
                deposito_id=fila['deposito_id'],
                repuesto_id=fila['repuesto_id'],
            )
            for fila in filas
        ])


def obtener_deposito_principal(Deposito):
    deposito = Deposito.objects.filter(es_principal=True).first()
    if deposito is not None:
        return deposito

    codigo = 'PRINCIPAL'
    intento = 1
    while Deposito.objects.filter(codigo=codigo).exists():
        intento += 1
        codigo = f'PRINCIPAL{intento}'

    return Deposito.objects.create(
        codigo=codigo,
        nombre='Depósito Principal',
        ubicacion='Asunción',
        es_principal=True,
        activo=True,
    )


def sembrar_stock_repuesto(apps, schema_editor):
    Repuesto = apps.get_model('inventario', 'Repuesto')
    StockRepuesto = apps.get_model('inventario', 'StockRepuesto')
    MovimientoStock = apps.get_model('inventario', 'MovimientoStock')
    Deposito = apps.get_model('inventario', 'Deposito')

    repuestos = Repuesto.objects.filter(stock_actual__gt=0).order_by('id')
    if not repuestos.exists():
        # No hay stock heredado que migrar: no se crea el depósito principal
        # (se crea solo cuando haga falta, desde `inventario.services`).
        return

    deposito = obtener_deposito_principal(Deposito)

    for repuesto in repuestos:
        if StockRepuesto.objects.filter(repuesto=repuesto, deposito=deposito).exists():
            continue

        cantidad = int(repuesto.stock_actual)
        reservado = min(int(repuesto.stock_reservado or 0), cantidad)

        StockRepuesto.objects.create(
            repuesto=repuesto,
            deposito=deposito,
            cantidad=cantidad,
            reservado=reservado,
        )

        MovimientoStock.objects.create(
            repuesto=repuesto,
            deposito_destino=deposito,
            tipo='ENTRADA',
            cantidad=cantidad,
            saldo_posterior=cantidad,
            costo_unitario=repuesto.costo_unitario or Decimal('0.0000'),
            motivo=MOTIVO_SALDO_INICIAL,
            referencia='MIGRACION-SALDO-INICIAL',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0039_alter_movimientostock_cantidad_and_more'),
    ]

    operations = [
        migrations.RunPython(reparar_tabla_stock_repuesto, migrations.RunPython.noop),
        migrations.RunPython(sembrar_stock_repuesto, migrations.RunPython.noop),
    ]
