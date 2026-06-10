from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Corrige valores inconsistentes en inventario_vehiculo.marca / .modelo convirtiendo nombres en FK.'

    def handle(self, *args, **options):
        from inventario.models import MarcaVehiculo, ModeloVehiculo

        cursor = connection.cursor()
        cursor.execute('SELECT id, marca, modelo FROM inventario_vehiculo')
        rows = cursor.fetchall()
        updated = 0
        created_marcas = 0
        created_modelos = 0

        with transaction.atomic():
            for pk, marca_val, modelo_val in rows:
                marca_obj = None
                modelo_obj = None

                # Procesar marca
                if marca_val is None:
                    marca_id = None
                else:
                    try:
                        marca_id_candidate = int(marca_val)
                        marca_obj = MarcaVehiculo.objects.filter(id=marca_id_candidate).first()
                    except Exception:
                        marca_obj = MarcaVehiculo.objects.filter(nombre=str(marca_val)).first()
                        if not marca_obj:
                            nombre_marca = str(marca_val).strip() or 'Marca Desconocida'
                            marca_obj = MarcaVehiculo.objects.create(nombre=nombre_marca)
                            created_marcas += 1

                # Procesar modelo
                if modelo_val is None:
                    modelo_id = None
                else:
                    try:
                        modelo_id_candidate = int(modelo_val)
                        modelo_obj = ModeloVehiculo.objects.filter(id=modelo_id_candidate).first()
                    except Exception:
                        nombre_modelo = str(modelo_val).strip()
                        if marca_obj:
                            modelo_obj = ModeloVehiculo.objects.filter(nombre=nombre_modelo, marca=marca_obj).first()
                        else:
                            modelo_obj = ModeloVehiculo.objects.filter(nombre=nombre_modelo).first()

                        if not modelo_obj and nombre_modelo:
                            # Asegurar que existe una marca para crear el modelo
                            if not marca_obj:
                                marca_obj = MarcaVehiculo.objects.filter(nombre='Marca Desconocida').first()
                                if not marca_obj:
                                    marca_obj = MarcaVehiculo.objects.create(nombre='Marca Desconocida')
                                    created_marcas += 1
                            modelo_obj = ModeloVehiculo.objects.create(marca=marca_obj, nombre=nombre_modelo)
                            created_modelos += 1

                # Obtener ids finales
                marca_id = marca_obj.id if marca_obj else None
                modelo_id = modelo_obj.id if modelo_obj else None

                # Actualizar fila si es necesario (usar SQL sin parámetros para evitar problemas de formateo con sqlite)
                cursor.execute(f"SELECT marca, modelo FROM inventario_vehiculo WHERE id = {pk}")
                current = cursor.fetchone()
                cur_marca, cur_modelo = current[0], current[1]
                if (cur_marca != marca_id) or (cur_modelo != modelo_id):
                    marca_sql = 'NULL' if marca_id is None else str(int(marca_id))
                    modelo_sql = 'NULL' if modelo_id is None else str(int(modelo_id))
                    sql = f"UPDATE inventario_vehiculo SET marca = {marca_sql}, modelo = {modelo_sql} WHERE id = {pk}"
                    cursor.execute(sql)
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f'Operación finalizada: filas actualizadas={updated}, marcas creadas={created_marcas}, modelos creados={created_modelos}'))
