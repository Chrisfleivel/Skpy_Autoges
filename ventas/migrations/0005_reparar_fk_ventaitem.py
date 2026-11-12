"""
Repara la FK de `ventas_ventaitem` que quedó apuntando a `catalogo_repuesto`.

La app `catalogo` estuvo deshabilitada hace tiempo y el modelo `Repuesto` mudó
a `inventario`, pero en las bases que ya existían la FK quedó apuntando a la
tabla vieja (`catalogo_repuesto`). Como esa tabla quedó vacía y sin mantener,
cualquier alta de línea de venta fallaba por integridad referencial.

Esta migración reconstruye la tabla si el problema está presente. Es
idempotente: si la FK ya apunta a `inventario_repuesto`, no hace nada.
"""

from django.db import migrations

TABLA_VENTA_ITEM = 'ventas_ventaitem'
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


def reparar_fk_venta_item(apps, schema_editor):
    """Reconstruye `ventas_ventaitem` si su FK apunta a `catalogo_repuesto`."""
    VentaItem = apps.get_model('ventas', 'VentaItem')

    if not _tabla_existe(schema_editor, TABLA_VENTA_ITEM):
        return
    if _fk_apunta_a_inventario(schema_editor, TABLA_VENTA_ITEM):
        return

    campos = [campo.name for campo in VentaItem._meta.concrete_fields]
    filas = list(VentaItem.objects.values(*campos))

    # `inventario_reservastock` apunta a esta tabla: sin desactivar la
    # verificación de FKs, el DROP fallaría si tuviera filas.
    with schema_editor.connection.constraint_checks_disabled():
        schema_editor.execute(f'DROP TABLE "{TABLA_VENTA_ITEM}"')
        schema_editor.create_model(VentaItem)

    if filas:
        VentaItem.objects.bulk_create([
            VentaItem(**fila) for fila in filas
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0004_alter_venta_moneda'),
        # La tabla hija se repara antes que la padre.
        ('inventario', '0046_reparar_fk_reservastock'),
    ]

    operations = [
        migrations.RunPython(reparar_fk_venta_item, migrations.RunPython.noop),
    ]
