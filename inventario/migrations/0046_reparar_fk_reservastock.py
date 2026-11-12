"""
Repara la FK de `inventario_reservastock` que quedó apuntando a `catalogo_repuesto`.

La app `catalogo` estuvo deshabilitada hace tiempo y el modelo `Repuesto` mudó
a `inventario`, pero en las bases que ya existían la FK quedó apuntando a la
tabla vieja (`catalogo_repuesto`). Como esa tabla quedó vacía y sin mantener,
cualquier alta de reserva fallaba por integridad referencial.

Esta migración reconstruye la tabla si el problema está presente. Es
idempotente: si la FK ya apunta a `inventario_repuesto`, no hace nada.
"""

from django.db import migrations

TABLA_RESERVA_STOCK = 'inventario_reservastock'
TABLA_REPUESTO = 'inventario_repuesto'


def _tabla_existe(schema_editor, tabla):
    with schema_editor.connection.cursor() as cursor:
        return tabla in schema_editor.connection.introspection.table_names(cursor)


def _fk_apunta_a_inventario(schema_editor, tabla):
    """True si alguna FK de la tabla apunta a `inventario_repuesto`."""
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


def reparar_fk_reserva_stock(apps, schema_editor):
    """Reconstruye `inventario_reservastock` si su FK apunta a `catalogo_repuesto`."""
    ReservaStock = apps.get_model('inventario', 'ReservaStock')

    if not _tabla_existe(schema_editor, TABLA_RESERVA_STOCK):
        return
    if _fk_apunta_a_inventario(schema_editor, TABLA_RESERVA_STOCK):
        return

    campos = [campo.name for campo in ReservaStock._meta.concrete_fields]
    filas = list(ReservaStock.objects.values(*campos))

    with schema_editor.connection.constraint_checks_disabled():
        schema_editor.execute(f'DROP TABLE "{TABLA_RESERVA_STOCK}"')
        schema_editor.create_model(ReservaStock)

    if filas:
        ReservaStock.objects.bulk_create([
            ReservaStock(**fila) for fila in filas
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0045_alter_vehiculo_combustible'),
    ]

    operations = [
        migrations.RunPython(reparar_fk_reserva_stock, migrations.RunPython.noop),
    ]
