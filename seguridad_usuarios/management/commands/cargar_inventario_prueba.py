from django.core.management.base import BaseCommand
from inventario.models import Vehiculo, Repuesto, MantenimientoVehiculo, Deposito

class Command(BaseCommand):
    help = 'Carga Vehiculos, Repuestos, Mantenimientos, Depósitos'

    def handle(self, *args, **kwargs):
        # Vehículos de prueba
        # deposito
        pass

        