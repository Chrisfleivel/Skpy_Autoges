from django.core.management.base import BaseCommand
from inventario.models import Repuesto, UnidadMedida
import random

class Command(BaseCommand):
    help = 'Carga repuestos iniciales en la base de datos para pruebas'

    def handle(self, *args, **kwargs):
        # Obtener o crear la unidad de medida "Unidad"
        unidad, created = UnidadMedida.objects.get_or_create(
            nombre='Unidad',
            defaults={'abreviatura': 'u'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Unidad de medida "Unidad" creada.'))

        repuestos_data = [
            # I. Sistema de Motor y Mantenimiento
            {
                'nombre': 'Filtro de Aceite CRDi (Eco)',
                'codigo_repuesto': '26320-2F000',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Santa Fe, Tucson / Kia Sorento, Sportage',
            },
            {
                'nombre': 'Filtro de Aire Motor',
                'codigo_repuesto': '28113-1R000',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Accent, Kona / Kia Rio, Stonic',
            },
            {
                'nombre': 'Filtro de Combustible Diésel',
                'codigo_repuesto': '31922-4H001',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Porter II / Kia Bongo III',
            },
            {
                'nombre': 'Bujía de Precalentamiento',
                'codigo_repuesto': '36710-2F001',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Motores CRDi 2.0/2.2',
            },
            {
                'nombre': 'Bujía de Iridium GDi',
                'codigo_repuesto': '18846-10060',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Elantra, Veloster / Kia K5',
            },
            {
                'nombre': 'Correa de Accesorios (Poliv)',
                'codigo_repuesto': '25212-2F000',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Santa Fe / Kia Sorento',
            },
            {
                'nombre': 'Bomba de Agua',
                'codigo_repuesto': '25100-2E000',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Tucson / Kia Sportage 2.0',
            },
            {
                'nombre': 'Termostato de Motor',
                'codigo_repuesto': '25500-4A010',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Grand Starex / H1',
            },
            {
                'nombre': 'Junta de Tapa de Cilindros',
                'codigo_repuesto': '67201-60120',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'SsangYong Korando, Rexton 2.2',
            },
            {
                'nombre': 'Kit de Distribución (Cadena)',
                'codigo_repuesto': '24321-2B000',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Accent / Kia Rio 1.4/1.6',
            },
            {
                'nombre': 'Filtro de Combustible GLP (LPi)',
                'codigo_repuesto': '33095-3K000',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Avante / Kia K5 LPi',
            },
            {
                'nombre': 'Inyector Diésel Delphi',
                'codigo_repuesto': '28231-4600',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'SsangYong Actyon, Kyron',
            },
            {
                'nombre': 'Válvula EGR',
                'codigo_repuesto': '28410-2F000',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Santa Fe / Kia Sorento',
            },
            {
                'nombre': 'Enfriador de Aceite',
                'codigo_repuesto': '26410-4A450',
                'categoria': 'Sistema de Motor y Mantenimiento',
                'compatibilidad': 'Hyundai Porter II / Kia Bongo III',
            },
            # II. Sistema de Frenos y Seguridad
            {
                'nombre': 'Pastillas de Freno Delanteras',
                'codigo_repuesto': '58101-2WA00',
                'categoria': 'Sistema de Frenos y Seguridad',
                'compatibilidad': 'Hyundai Santa Fe / Kia Sorento',
            },
            {
                'nombre': 'Pastillas de Freno Traseras',
                'codigo_repuesto': '58302-D3A00',
                'categoria': 'Sistema de Frenos y Seguridad',
                'compatibilidad': 'Hyundai Tucson / Kia Sportage',
            },
            {
                'nombre': 'Disco de Freno Delantero',
                'codigo_repuesto': '51712-1W200',
                'categoria': 'Sistema de Frenos y Seguridad',
                'compatibilidad': 'Hyundai Accent / Kia Rio',
            },
            {
                'nombre': 'Sensor de ABS Delantero',
                'codigo_repuesto': '59810-F2000',
                'categoria': 'Sistema de Frenos y Seguridad',
                'compatibilidad': 'Hyundai Elantra / Kia Cerato',
            },
            {
                'nombre': 'Bomba Central de Freno',
                'codigo_repuesto': '58510-4H000',
                'categoria': 'Sistema de Frenos y Seguridad',
                'compatibilidad': 'Hyundai Grand Starex',
            },
            {
                'nombre': 'Maza de Rueda Trasera (con Rulemán)',
                'codigo_repuesto': '52730-Q0000',
                'categoria': 'Sistema de Frenos y Seguridad',
                'compatibilidad': 'Hyundai Kona / Kia Seltos',
            },
            {
                'nombre': 'Pastillas de Freno de Estacionamiento',
                'codigo_repuesto': '48330-08010',
                'categoria': 'Sistema de Frenos y Seguridad',
                'compatibilidad': 'SsangYong Rexton / Musso',
            },
            # III. Suspensión y Dirección
            {
                'nombre': 'Amortiguador Delantero Izquierdo',
                'codigo_repuesto': '54651-D3000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Tucson / Kia Sportage',
            },
            {
                'nombre': 'Amortiguador Delantero Derecho',
                'codigo_repuesto': '54661-D3000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Tucson / Kia Sportage',
            },
            {
                'nombre': 'Amortiguador Trasero',
                'codigo_repuesto': '55311-2W000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Santa Fe / Kia Sorento',
            },
            {
                'nombre': 'Bieleta de Barra Estabilizadora',
                'codigo_repuesto': '54830-0U000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Accent / Kia Rio',
            },
            {
                'nombre': 'Rótula de Suspensión',
                'codigo_repuesto': '54530-4H000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Grand Starex / Porter II',
            },
            {
                'nombre': 'Buje de Parrilla Inferior',
                'codigo_repuesto': '54551-F2000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Elantra / Kia Cerato',
            },
            {
                'nombre': 'Terminal de Dirección',
                'codigo_repuesto': '44510-35000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'SsangYong Tivoli / Korando',
            },
            {
                'nombre': 'Cremallera de Dirección Hidráulica',
                'codigo_repuesto': '57700-4E000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Kia Bongo III',
            },
            {
                'nombre': 'Homocinética Lado Rueda',
                'codigo_repuesto': '49500-2V000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Veloster / Kia Forte',
            },
            {
                'nombre': 'Brazo Pitman',
                'codigo_repuesto': '56820-44000',
                'categoria': 'Suspensión y Dirección',
                'compatibilidad': 'Hyundai Porter II',
            },
            # IV. Sistema Eléctrico y Sensores
            {
                'nombre': 'Alternador (120A)',
                'codigo_repuesto': '37300-2F000',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Hyundai Santa Fe / Kia Sorento CRDi',
            },
            {
                'nombre': 'Motor de Arranque',
                'codigo_repuesto': '36100-2E000',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Hyundai Tucson / Kia Sportage',
            },
            {
                'nombre': 'Bobina de Encendido',
                'codigo_repuesto': '27301-2B010',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Hyundai Accent, Elantra / Kia Rio, Soul',
            },
            {
                'nombre': 'Sensor de Oxígeno (Lambda)',
                'codigo_repuesto': '39210-2B000',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Hyundai Veloster / Kia Picanto',
            },
            {
                'nombre': 'Sensor de Posición de Cigüeñal (CKP)',
                'codigo_repuesto': '39180-2F000',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Motores CRDi',
            },
            {
                'nombre': 'Batería 90Ah (AGM)',
                'codigo_repuesto': '37110-C5902',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Hyundai Palisade / Kia Carnival',
            },
            {
                'nombre': 'Compresor de Aire Acondicionado',
                'codigo_repuesto': '97701-4H000',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Hyundai Grand Starex',
            },
            {
                'nombre': 'Faro Delantero Izquierdo (LED)',
                'codigo_repuesto': '92101-J9000',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Hyundai Kona 2020',
            },
            {
                'nombre': 'Faro Trasero Derecho',
                'codigo_repuesto': '92402-D9000',
                'categoria': 'Sistema Eléctrico y Sensores',
                'compatibilidad': 'Kia Sportage 2017',
            },
            # V. Transmisión y Otros
            {
                'nombre': 'Filtro de Caja Automática',
                'codigo_repuesto': '46321-3B000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai/Kia 6 Velocidades',
            },
            {
                'nombre': 'Kit de Embrague (Disco y Plato)',
                'codigo_repuesto': '41100-4A000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai Porter II / Kia Bongo III',
            },
            {
                'nombre': 'Crapodina Hidráulica',
                'codigo_repuesto': '41421-24300',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai Accent / Kia Rio Manual',
            },
            {
                'nombre': 'Cruceta de Cardán',
                'codigo_repuesto': '34025-05001',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'SsangYong Musso / Rexton',
            },
            {
                'nombre': 'Soporte de Motor Delantero',
                'codigo_repuesto': '21810-D3000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai Tucson / Kia Sportage',
            },
            {
                'nombre': 'Espejo Retrovisor Eléctrico',
                'codigo_repuesto': '87610-G6000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Kia Picanto / Morning',
            },
            {
                'nombre': 'Manija Exterior de Puerta',
                'codigo_repuesto': '82651-4H000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai Grand Starex',
            },
            {
                'nombre': 'Radiador de Agua',
                'codigo_repuesto': '25310-F2000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai Elantra / Kia Cerato',
            },
            {
                'nombre': 'Intercooler',
                'codigo_repuesto': '28270-2F000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai Santa Fe / Kia Sorento Turbo',
            },
            {
                'nombre': 'Válvula de Control de Aire (IAC)',
                'codigo_repuesto': '35102-02000',
                'categoria': 'Transmisión y Otros',
                'compatibilidad': 'Hyundai I10 / Kia Picanto',
            },
        ]
        
        for repuesto_data in repuestos_data:
            stock_actual = random.randint(10, 50)
            costo_compra = random.randint(50000, 500000)
            precio_venta = round(costo_compra * 1.2, 2)
            
            repuesto, created = Repuesto.objects.get_or_create(
                codigo_repuesto=repuesto_data['codigo_repuesto'],
                defaults={
                    'nombre': repuesto_data['nombre'],
                    'categoria': repuesto_data['categoria'],
                    'compatibilidad': repuesto_data['compatibilidad'],
                    'unidad_medida': unidad,
                    'stock_actual': stock_actual,
                    'stock_minimo': 5,
                    'costo_compra': costo_compra,
                    'precio_venta': precio_venta,
                    'costo_unitario': costo_compra,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Repuesto {repuesto} creado correctamente.'))
            else:
                self.stdout.write(f'Repuesto {repuesto} ya existe.')
        
        self.stdout.write(self.style.SUCCESS('Carga de repuestos completada.'))