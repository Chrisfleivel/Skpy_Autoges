import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skpy_autogest_project.settings')
django.setup()

from django.db import connection
from contabilidad.models import Asiento, MovimientoContable
from contabilidad.services import registrar_asiento_apertura

print('Tablas iniciales:', [t for t in connection.introspection.table_names() if 'contabilidad_' in t])

from django.db import connection as conn

def ensure_table(model):
    with conn.schema_editor() as schema_editor:
        if model._meta.db_table not in conn.introspection.table_names():
            schema_editor.create_model(model)
        else:
            print('Tabla ya existe:', model._meta.db_table)

ensure_table(Asiento)
ensure_table(MovimientoContable)
print('Tablas tras ensure:', [t for t in connection.introspection.table_names() if 'contabilidad_' in t])

asiento = registrar_asiento_apertura([
    {'codigo_cuenta': '1.1.02', 'monto': 100000, 'tipo': 'debe'},
    {'codigo_cuenta': '3.1.01', 'monto': 100000, 'tipo': 'haber'},
], descripcion='ASIENTO DE APERTURA PRUEBA')

print('Asiento creado:', asiento.id, asiento.descripcion, asiento.fecha)
print('Movimientos:')
for mov in asiento.movimientos.all():
    print('   ', mov.cuenta.codigo, mov.cuenta.nombre, mov.debe, mov.haber)
