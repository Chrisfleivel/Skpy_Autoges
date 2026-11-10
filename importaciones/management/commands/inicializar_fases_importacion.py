from django.core.management.base import BaseCommand
from importaciones.models import Importacion, FaseImportacion


class Command(BaseCommand):
    """
    Management command para inicializar automáticamente las fases de importación
    para todas las importaciones que no las tengan aún.
    
    Uso: python manage.py inicializar_fases_importacion
    """
    help = 'Inicializa las fases de importación para importaciones existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--importacion-id',
            type=int,
            help='ID específico de una importación para inicializar',
        )

    def handle(self, *args, **options):
        importacion_id = options.get('importacion_id')
        
        if importacion_id:
            importaciones = Importacion.objects.filter(id=importacion_id)
        else:
            importaciones = Importacion.objects.all()
        
        fases_creadas = 0
        fases_existentes = 0
        
        # Definición de fases en orden
        FASES = [
            ('baja_vehiculo', 'Baja de Vehículo en Corea'),
            ('facturas_flete', 'Facturas de Flete'),
            ('documentos_aduana_origen', 'Documentos Aduanales (Origen)'),
            ('documentos_aduana_py', 'Documentos Aduana Paraguay'),
            ('flete_paraguay', 'Flete en Paraguay'),
            ('entrega_depositos', 'Entrega a Depósitos'),
        ]
        
        for importacion in importaciones:
            self.stdout.write(f'\nProcesando importación: {importacion.codigo_seguimiento}')
            
            for fase_code, fase_desc in FASES:
                fase_existe = FaseImportacion.objects.filter(
                    importacion=importacion,
                    fase=fase_code
                ).exists()
                
                if not fase_existe:
                    FaseImportacion.objects.create(
                        importacion=importacion,
                        fase=fase_code,
                        descripcion=fase_desc
                    )
                    fases_creadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Fase creada: {fase_desc}')
                    )
                else:
                    fases_existentes += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ℹ Fase ya existe: {fase_desc}')
                    )
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Fases creadas: {fases_creadas}'))
        self.stdout.write(self.style.WARNING(f'Fases que ya existían: {fases_existentes}'))
        self.stdout.write('='*60)
