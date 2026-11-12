"""
Unificación de marcas y modelos duplicados.

En la base de desarrollo conviven marcas repetidas por diferencia de
mayúsculas/minúsculas (`Hyundai`/`HYUNDAI`, `Kia`/`KIA`) y por cambio de
razón social (`KG Mobility`/`SSANGYONG`). Cada juego trae sus propios
modelos, así que un mismo modelo aparece dos veces (Hyundai Tucson y
HYUNDAI Tucson) y los filtros por marca muestran entradas repetidas.

La migración deja una sola marca por familia (la canónica), traslada los
modelos que no tienen equivalente y fusiona los que coinciden por nombre,
reescribiendo los vehículos que apuntan a ellos.

Es idempotente: si la marca vieja ya no existe, no hace nada.
"""

from django.db import migrations


# Marca canónica -> nombres alternativos EXACTOS que se deben fusionar.
CANONICOS = {
    'Hyundai': ['HYUNDAI'],
    'Kia': ['KIA'],
    'KG Mobility': ['SSANGYONG', 'SsangYong'],
}


def _clave(nombre):
    """Clave de comparación de nombres (ignora mayúsculas y espacios sobrantes)."""
    return (nombre or '').strip().lower()


def unificar_marcas_modelos(apps, schema_editor=None):
    """
    Fusiona marcas duplicadas y sus modelos.

    Para cada familia:
      1. Los vehículos pasan a la marca canónica.
      2. Cada modelo viejo se fusiona con su gemelo (mismo nombre) o, si no
         tiene equivalente, se traslada a la marca canónica.
      3. La marca vieja se elimina.
    """
    MarcaVehiculo = apps.get_model('inventario', 'MarcaVehiculo')
    ModeloVehiculo = apps.get_model('inventario', 'ModeloVehiculo')
    Vehiculo = apps.get_model('inventario', 'Vehiculo')

    for nombre_canonico, alias in CANONICOS.items():
        canonica = MarcaVehiculo.objects.filter(nombre=nombre_canonico).first()
        if canonica is None:
            # Sin marca canónica no hay nada que fusionar.
            continue

        for nombre_alias in alias:
            # Coincidencia EXACTA a propósito: `nombre__iexact` también
            # traería la canónica, porque 'HYUNDAI' y 'Hyundai' son la misma
            # palabra sin distinguir mayúsculas.
            vieja = MarcaVehiculo.objects.filter(nombre=nombre_alias).first()
            if vieja is None or vieja.pk == canonica.pk:
                continue

            # 1. Los vehículos pasan a la marca canónica.
            Vehiculo.objects.filter(marca=vieja).update(marca=canonica)

            # 2. Cada modelo viejo se fusiona con su gemelo o se traslada.
            for modelo in list(vieja.modelos.all()):
                gemelo = canonica.modelos.filter(
                    nombre__iexact=modelo.nombre.strip()).first()
                if gemelo is not None and gemelo.pk != modelo.pk:
                    Vehiculo.objects.filter(modelo=modelo).update(modelo=gemelo)
                    modelo.delete()
                else:
                    modelo.marca = canonica
                    modelo.save(update_fields=['marca'])

            # 3. La marca vieja desaparece (sus modelos ya están resueltos).
            vieja.delete()

    _eliminar_modelos_duplicados(MarcaVehiculo, Vehiculo)


def _eliminar_modelos_duplicados(MarcaVehiculo, Vehiculo):
    """
    Quita modelos repetidos dentro de la misma marca (mismo nombre).

    Se conserva el primero y los vehículos del que sobra pasan a él.
    """
    for marca in MarcaVehiculo.objects.all():
        vistos = {}
        for modelo in marca.modelos.order_by('pk'):
            clave = _clave(modelo.nombre)
            if clave not in vistos:
                vistos[clave] = modelo
                continue
            keeper = vistos[clave]
            Vehiculo.objects.filter(modelo=modelo).update(modelo=keeper)
            modelo.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0041_remove_mantenimientovehiculo_estado_mantenimiento_and_more'),
    ]

    operations = [
        migrations.RunPython(unificar_marcas_modelos, migrations.RunPython.noop),
    ]
