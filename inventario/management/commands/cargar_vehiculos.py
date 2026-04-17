from django.core.management.base import BaseCommand
from inventario.models import Vehiculo
import random
import string

class Command(BaseCommand):
    help = 'Carga vehículos iniciales en la base de datos para pruebas'

    def generate_vin(self, marca):
        """Genera un VIN único basado en la marca"""
        prefix = {
            'HYUNDAI': 'KMH',
            'KIA': 'KNM',
            'SSANGYONG': 'KPT'
        }.get(marca.upper(), 'VIN')
        
        # Genera 14 caracteres aleatorios (VIN tiene 17, pero ajustamos)
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
        return f"{prefix}{random_part}"

    def handle(self, *args, **kwargs):
        vehiculos_data = [
            # Hyundai
            {
                'marca': 'HYUNDAI',
                'modelo': 'Santa Fe',
                'año': 2018,
                'motorizacion': '2.2L CRDi',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Blanco',
                'costo_compra': 120000000,  # Guaraníes
                'precio_venta': 140000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Tucson',
                'año': 2017,
                'motorizacion': '2.0L CRDi',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Gris Plata',
                'costo_compra': 100000000,
                'precio_venta': 120000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Accent',
                'año': 2016,
                'motorizacion': '1.6L VGT',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Azul',
                'costo_compra': 80000000,
                'precio_venta': 95000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Elantra',
                'año': 2019,
                'motorizacion': '1.6L GDi',
                'combustible': 'gasolina',
                'transmision': 'Automática',
                'color': 'Negro',
                'costo_compra': 90000000,
                'precio_venta': 110000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Grand Starex',
                'año': 2015,
                'motorizacion': '2.5L CRDi',
                'combustible': 'diesel',
                'transmision': 'Manual',
                'color': 'Gris',
                'costo_compra': 150000000,
                'precio_venta': 170000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Porter II',
                'año': 2017,
                'motorizacion': '2.5L CRDi',
                'combustible': 'diesel',
                'transmision': 'Manual',
                'color': 'Azul',
                'costo_compra': 130000000,
                'precio_venta': 150000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Veloster',
                'año': 2016,
                'motorizacion': '1.6L Turbo',
                'combustible': 'gasolina',
                'transmision': 'Automática',
                'color': 'Rojo',
                'costo_compra': 85000000,
                'precio_venta': 100000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Kona',
                'año': 2020,
                'motorizacion': '1.6L Turbo',
                'combustible': 'gasolina',
                'transmision': 'Automática',
                'color': 'Amarillo',
                'costo_compra': 95000000,
                'precio_venta': 115000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Palisade',
                'año': 2021,
                'motorizacion': '2.2L CRDi',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Azul Oscuro',
                'costo_compra': 180000000,
                'precio_venta': 200000000,
            },
            {
                'marca': 'HYUNDAI',
                'modelo': 'Avante',
                'año': 2018,
                'motorizacion': '1.6L LPi',
                'combustible': 'otro',  # GLP
                'transmision': 'Automática',
                'color': 'Blanco',
                'costo_compra': 75000000,
                'precio_venta': 90000000,
            },
            # Kia
            {
                'marca': 'KIA',
                'modelo': 'Sportage',
                'año': 2017,
                'motorizacion': '2.0L CRDi',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Naranja',
                'costo_compra': 110000000,
                'precio_venta': 130000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'Sorento',
                'año': 2019,
                'motorizacion': '2.2L CRDi',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Negro',
                'costo_compra': 140000000,
                'precio_venta': 160000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'Picanto',
                'año': 2016,
                'motorizacion': '1.0L',
                'combustible': 'gasolina',
                'transmision': 'Automática',
                'color': 'Rosado',
                'costo_compra': 60000000,
                'precio_venta': 75000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'Rio',
                'año': 2018,
                'motorizacion': '1.4L',
                'combustible': 'gasolina',
                'transmision': 'Manual',
                'color': 'Blanco',
                'costo_compra': 70000000,
                'precio_venta': 85000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'K5',
                'año': 2017,
                'motorizacion': '2.0L LPi',
                'combustible': 'otro',  # GLP
                'transmision': 'Automática',
                'color': 'Gris Oscuro',
                'costo_compra': 95000000,
                'precio_venta': 110000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'K7',
                'año': 2019,
                'motorizacion': '2.4L GDi',
                'combustible': 'gasolina',
                'transmision': 'Automática',
                'color': 'Perla',
                'costo_compra': 120000000,
                'precio_venta': 140000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'Bongo III',
                'año': 2018,
                'motorizacion': '2.5L CRDi',
                'combustible': 'diesel',
                'transmision': 'Manual',
                'color': 'Azul',
                'costo_compra': 135000000,
                'precio_venta': 155000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'Carnival',
                'año': 2020,
                'motorizacion': '2.2L CRDi',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Blanco',
                'costo_compra': 160000000,
                'precio_venta': 180000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'Mohave',
                'año': 2021,
                'motorizacion': '3.0L V6',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Negro Mate',
                'costo_compra': 190000000,
                'precio_venta': 210000000,
            },
            {
                'marca': 'KIA',
                'modelo': 'Cerato',
                'año': 2017,
                'motorizacion': '1.6L',
                'combustible': 'gasolina',
                'transmision': 'Automática',
                'color': 'Plata',
                'costo_compra': 78000000,
                'precio_venta': 95000000,
            },
            # SsangYong
            {
                'marca': 'SSANGYONG',
                'modelo': 'Korando',
                'año': 2018,
                'motorizacion': '2.2L',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Blanco',
                'costo_compra': 105000000,
                'precio_venta': 125000000,
            },
            {
                'marca': 'SSANGYONG',
                'modelo': 'Rexton',
                'año': 2019,
                'motorizacion': '2.2L',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Gris',
                'costo_compra': 145000000,
                'precio_venta': 165000000,
            },
            {
                'marca': 'SSANGYONG',
                'modelo': 'Tivoli',
                'año': 2017,
                'motorizacion': '1.6L',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Verde',
                'costo_compra': 85000000,
                'precio_venta': 100000000,
            },
            {
                'marca': 'SSANGYONG',
                'modelo': 'Musso',
                'año': 2018,
                'motorizacion': '2.2L',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Azul Marino',
                'costo_compra': 125000000,
                'precio_venta': 145000000,
            },
            {
                'marca': 'SSANGYONG',
                'modelo': 'Rodius',
                'año': 2016,
                'motorizacion': '2.0L',
                'combustible': 'diesel',
                'transmision': 'Automática',
                'color': 'Plata',
                'costo_compra': 115000000,
                'precio_venta': 135000000,
            },
        ]
        
        for vehiculo_data in vehiculos_data:
            vin = self.generate_vin(vehiculo_data['marca'])
            while Vehiculo.objects.filter(codigo_chasis=vin).exists():
                vin = self.generate_vin(vehiculo_data['marca'])
            
            vehiculo, created = Vehiculo.objects.get_or_create(
                marca=vehiculo_data['marca'],
                modelo=vehiculo_data['modelo'],
                año=vehiculo_data['año'],
                defaults={
                    'codigo_chasis': vin,
                    'motorizacion': vehiculo_data['motorizacion'],
                    'color': vehiculo_data['color'],
                    'combustible': vehiculo_data['combustible'],
                    'transmision': vehiculo_data['transmision'],
                    'costo_compra': vehiculo_data['costo_compra'],
                    'precio_venta': vehiculo_data['precio_venta'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Vehículo {vehiculo} creado correctamente.'))
            else:
                self.stdout.write(f'Vehículo {vehiculo} ya existe.')
        
        self.stdout.write(self.style.SUCCESS('Carga de vehículos completada.'))
