from django.core.management.base import BaseCommand

from configuraciones_maestras.models import AgenteTransporte, DespachanteAduana
from importaciones.models import Importacion


class Command(BaseCommand):
    help = 'Crea agentes de transporte y despachantes de aduana base para las importaciones de prueba'

    def handle(self, *args, **options):
        agente_origen, created_origen = AgenteTransporte.objects.get_or_create(
            nombre='Agente Transporte Corea Test',
            defaults={
                'razon_social': 'Agente Transporte Corea Test',
                'pais_operacion': 'KR',
                'tipo_servicio': 'MARITIMO',
                'tipo_carga_especialidad': 'REPUESTOS',
                'contacto': 'Contacto Test',
                'telefono': '0981-000000',
                'direccion': 'Seul, Corea del Sur',
                'estado': True,
            },
        )

        agente_destino, created_destino = AgenteTransporte.objects.get_or_create(
            nombre='Agente Transporte Paraguay Test',
            defaults={
                'razon_social': 'Agente Transporte Paraguay Test',
                'pais_operacion': 'PY',
                'tipo_servicio': 'TERRESTRE',
                'tipo_carga_especialidad': 'REPUESTOS',
                'contacto': 'Contacto Test',
                'telefono': '021-000000',
                'direccion': 'Asunción, Paraguay',
                'estado': True,
            },
        )

        despachante_aduana, created_despachante = DespachanteAduana.objects.get_or_create(
            nombre='Despachante Aduana Test',
            defaults={
                'razon_social': 'Despachante Aduana Test',
                'registro': 'TEST-0001',
                'contacto': 'Despachante Test',
                'telefono': '0981-111111',
                'direccion': 'Asunción, Paraguay',
                'estado': True,
            },
        )

        importaciones = Importacion.objects.all()
        actualizadas = 0

        for importacion in importaciones:
            updated = False
            if not importacion.agente_transporte_origen_id:
                importacion.agente_transporte_origen = agente_origen
                updated = True
            if not importacion.agente_transporte_destino_id:
                importacion.agente_transporte_destino = agente_destino
                updated = True
            if not importacion.despachante_aduana_id:
                importacion.despachante_aduana = despachante_aduana
                updated = True
            if not importacion.agente_transporte_id:
                importacion.agente_transporte = agente_origen
                updated = True
            if updated:
                importacion.save(update_fields=[
                    'agente_transporte',
                    'agente_transporte_origen',
                    'agente_transporte_destino',
                    'despachante_aduana',
                ])
                actualizadas += 1

        self.stdout.write(self.style.SUCCESS(
            f'Agentes creados: origen={created_origen}, destino={created_destino}, despachante={created_despachante}'
        ))
        self.stdout.write(self.style.SUCCESS(f'Importaciones actualizadas: {actualizadas}'))
