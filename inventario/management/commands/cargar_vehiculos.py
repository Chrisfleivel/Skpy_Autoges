from decimal import Decimal
import random
import string

from django.core.management.base import BaseCommand

from inventario.models import MarcaVehiculo, ModeloVehiculo, TipoTransmision, Vehiculo


class Command(BaseCommand):
    help = 'Carga vehículos iniciales en la base de datos para pruebas'

    def generate_vin(self, marca):
        """Genera un VIN válido y único basado en la marca."""
        prefix = {
            'HYUNDAI': 'KMH',
            'KIA': 'KNM',
            'SSANGYONG': 'KPT',
        }.get(marca.upper(), 'VIN')
        allowed_chars = ''.join(ch for ch in string.ascii_uppercase + string.digits if ch not in 'IOQ')
        random_part = ''.join(random.choices(allowed_chars, k=14))
        return f"{prefix}{random_part}"

    def _normalizar_color(self, color_name):
        colores = {
            'Blanco': '#FFFFFF',
            'Gris Plata': '#C0C0C0',
            'Azul': '#1E40AF',
            'Negro': '#111111',
            'Gris': '#6B7280',
            'Rojo': '#DC2626',
            'Amarillo': '#FACC15',
            'Azul Oscuro': '#1D4ED8',
            'Naranja': '#F97316',
            'Rosado': '#EC4899',
            'Perla': '#F5F5F5',
            'Plata': '#E5E7EB',
            'Verde': '#16A34A',
            'Azul Marino': '#1E3A8A',
            'Negro Mate': '#111827',
        }
        return colores.get(color_name, '#FFFFFF')

    def _normalizar_combustible(self, combustible):
        mapa = {
            'gasolina': 'nafta',
            'gas': 'nafta',
            'nafta': 'nafta',
            'diesel': 'diesel',
            'electrico': 'electrico',
            'hibrido': 'hibrido',
            'otro': 'otro',
        }
        return mapa.get(combustible, 'otro')

    def _obtener_relaciones(self, marca_nombre, modelo_nombre, transmision_nombre):
        marca, _ = MarcaVehiculo.objects.get_or_create(
            nombre=marca_nombre,
            defaults={'descripcion': 'Creada por el comando de carga inicial', 'estado': True},
        )
        modelo, _ = ModeloVehiculo.objects.get_or_create(
            marca=marca,
            nombre=modelo_nombre,
            defaults={'estado': True},
        )
        transmision, _ = TipoTransmision.objects.get_or_create(
            nombre=transmision_nombre,
            defaults={'estado': True},
        )
        return marca, modelo, transmision

    def handle(self, *args, **kwargs):
        vehiculos_data = [
            {'marca': 'HYUNDAI', 'modelo': 'Santa Fe', 'año': 2018, 'motorizacion': '2.2L CRDi', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Blanco', 'costo_compra': 120000000, 'precio_venta': 140000000},
            {'marca': 'HYUNDAI', 'modelo': 'Tucson', 'año': 2017, 'motorizacion': '2.0L CRDi', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Gris Plata', 'costo_compra': 100000000, 'precio_venta': 120000000},
            {'marca': 'HYUNDAI', 'modelo': 'Accent', 'año': 2016, 'motorizacion': '1.6L VGT', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Azul', 'costo_compra': 80000000, 'precio_venta': 95000000},
            {'marca': 'HYUNDAI', 'modelo': 'Elantra', 'año': 2019, 'motorizacion': '1.6L GDi', 'combustible': 'gasolina', 'transmision': 'Automática', 'color': 'Negro', 'costo_compra': 90000000, 'precio_venta': 110000000},
            {'marca': 'HYUNDAI', 'modelo': 'Grand Starex', 'año': 2015, 'motorizacion': '2.5L CRDi', 'combustible': 'diesel', 'transmision': 'Manual', 'color': 'Gris', 'costo_compra': 150000000, 'precio_venta': 170000000},
            {'marca': 'HYUNDAI', 'modelo': 'Porter II', 'año': 2017, 'motorizacion': '2.5L CRDi', 'combustible': 'diesel', 'transmision': 'Manual', 'color': 'Azul', 'costo_compra': 130000000, 'precio_venta': 150000000},
            {'marca': 'HYUNDAI', 'modelo': 'Veloster', 'año': 2016, 'motorizacion': '1.6L Turbo', 'combustible': 'gasolina', 'transmision': 'Automática', 'color': 'Rojo', 'costo_compra': 85000000, 'precio_venta': 100000000},
            {'marca': 'HYUNDAI', 'modelo': 'Kona', 'año': 2020, 'motorizacion': '1.6L Turbo', 'combustible': 'gasolina', 'transmision': 'Automática', 'color': 'Amarillo', 'costo_compra': 95000000, 'precio_venta': 115000000},
            {'marca': 'HYUNDAI', 'modelo': 'Palisade', 'año': 2021, 'motorizacion': '2.2L CRDi', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Azul Oscuro', 'costo_compra': 180000000, 'precio_venta': 200000000},
            {'marca': 'HYUNDAI', 'modelo': 'Avante', 'año': 2018, 'motorizacion': '1.6L LPi', 'combustible': 'otro', 'transmision': 'Automática', 'color': 'Blanco', 'costo_compra': 75000000, 'precio_venta': 90000000},
            {'marca': 'KIA', 'modelo': 'Sportage', 'año': 2017, 'motorizacion': '2.0L CRDi', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Naranja', 'costo_compra': 110000000, 'precio_venta': 130000000},
            {'marca': 'KIA', 'modelo': 'Sorento', 'año': 2019, 'motorizacion': '2.2L CRDi', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Negro', 'costo_compra': 140000000, 'precio_venta': 160000000},
            {'marca': 'KIA', 'modelo': 'Picanto', 'año': 2016, 'motorizacion': '1.0L', 'combustible': 'gasolina', 'transmision': 'Automática', 'color': 'Rosado', 'costo_compra': 60000000, 'precio_venta': 75000000},
            {'marca': 'KIA', 'modelo': 'Rio', 'año': 2018, 'motorizacion': '1.4L', 'combustible': 'gasolina', 'transmision': 'Manual', 'color': 'Blanco', 'costo_compra': 70000000, 'precio_venta': 85000000},
            {'marca': 'KIA', 'modelo': 'K5', 'año': 2017, 'motorizacion': '2.0L LPi', 'combustible': 'otro', 'transmision': 'Automática', 'color': 'Gris Oscuro', 'costo_compra': 95000000, 'precio_venta': 110000000},
            {'marca': 'KIA', 'modelo': 'K7', 'año': 2019, 'motorizacion': '2.4L GDi', 'combustible': 'gasolina', 'transmision': 'Automática', 'color': 'Perla', 'costo_compra': 120000000, 'precio_venta': 140000000},
            {'marca': 'KIA', 'modelo': 'Bongo III', 'año': 2018, 'motorizacion': '2.5L CRDi', 'combustible': 'diesel', 'transmision': 'Manual', 'color': 'Azul', 'costo_compra': 135000000, 'precio_venta': 155000000},
            {'marca': 'KIA', 'modelo': 'Carnival', 'año': 2020, 'motorizacion': '2.2L CRDi', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Blanco', 'costo_compra': 160000000, 'precio_venta': 180000000},
            {'marca': 'KIA', 'modelo': 'Mohave', 'año': 2021, 'motorizacion': '3.0L V6', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Negro Mate', 'costo_compra': 190000000, 'precio_venta': 210000000},
            {'marca': 'KIA', 'modelo': 'Cerato', 'año': 2017, 'motorizacion': '1.6L', 'combustible': 'gasolina', 'transmision': 'Automática', 'color': 'Plata', 'costo_compra': 78000000, 'precio_venta': 95000000},
            {'marca': 'SSANGYONG', 'modelo': 'Korando', 'año': 2018, 'motorizacion': '2.2L', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Blanco', 'costo_compra': 105000000, 'precio_venta': 125000000},
            {'marca': 'SSANGYONG', 'modelo': 'Rexton', 'año': 2019, 'motorizacion': '2.2L', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Gris', 'costo_compra': 145000000, 'precio_venta': 165000000},
            {'marca': 'SSANGYONG', 'modelo': 'Tivoli', 'año': 2017, 'motorizacion': '1.6L', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Verde', 'costo_compra': 85000000, 'precio_venta': 100000000},
            {'marca': 'SSANGYONG', 'modelo': 'Musso', 'año': 2018, 'motorizacion': '2.2L', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Azul Marino', 'costo_compra': 125000000, 'precio_venta': 145000000},
            {'marca': 'SSANGYONG', 'modelo': 'Rodius', 'año': 2016, 'motorizacion': '2.0L', 'combustible': 'diesel', 'transmision': 'Automática', 'color': 'Plata', 'costo_compra': 115000000, 'precio_venta': 135000000},
        ]

        for vehiculo_data in vehiculos_data:
            marca, modelo, transmision = self._obtener_relaciones(
                vehiculo_data['marca'],
                vehiculo_data['modelo'],
                vehiculo_data['transmision'],
            )
            vin = self.generate_vin(vehiculo_data['marca'])
            for _ in range(100):
                vin = self.generate_vin(vehiculo_data['marca'])
                if not Vehiculo.objects.filter(codigo_chasis=vin).exists():
                    break
            else:
                raise RuntimeError('No se pudo generar un VIN único para el vehículo.')

            nombre = f"{marca.nombre} {modelo.nombre}"
            defaults = {
                'nombre': nombre,
                'marca': marca,
                'modelo': modelo,
                'año': vehiculo_data['año'],
                'kilometraje': vehiculo_data.get('kilometraje', 0),
                'codigo_chasis': vin,
                'estado': 'disponible',
                'costo_compra': Decimal(str(vehiculo_data['costo_compra'])),
                'precio_venta': Decimal(str(vehiculo_data['precio_venta'])),
                'color': self._normalizar_color(vehiculo_data['color']),
                'combustible': self._normalizar_combustible(vehiculo_data['combustible']),
                'transmision': transmision,
                'descripcion': vehiculo_data.get('motorizacion', ''),
            }

            vehiculo, created = Vehiculo.objects.get_or_create(
                nombre=nombre,
                marca=marca,
                modelo=modelo,
                año=vehiculo_data['año'],
                defaults=defaults,
            )
            if not created:
                for field, value in defaults.items():
                    if field == 'codigo_chasis' and vehiculo.codigo_chasis:
                        continue
                    setattr(vehiculo, field, value)
                vehiculo.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f'Vehículo {vehiculo} creado correctamente.'))
            else:
                self.stdout.write(f'Vehículo {vehiculo} actualizado correctamente.')

        self.stdout.write(self.style.SUCCESS('Carga de vehículos completada.'))
