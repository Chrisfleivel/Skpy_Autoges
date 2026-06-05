from django.core.management.base import BaseCommand
from inventario.models import TipoTransmision

import random
import string

class Command(BaseCommand):
    help = 'Cargar tipos de transmisión de vehículos de prueba'

    def handle(self, *args, **kwargs):
        tipos_transmision = [
            ("Manual", "Transmisión manual con una palanca de cambios y embrague."),
            ("Automática", "Transmisión automática que cambia de marcha sin intervención del conductor."),
            ("CVT (Transmisión Variable Continua)", "Transmisión que ofrece cambios de marcha suaves y eficientes sin pasos definidos."),
            ("Doble Embrague (DCT)", "Transmisión que utiliza dos embragues para cambios de marcha rápidos y sin interrupciones."),
            ("Semi-Automática", "Transmisión que combina características de manual y automática, permitiendo cambios manuales sin pedal de embrague."),
            ("Automática de 8 velocidades", "Transmisión automática avanzada con 8 velocidades para mejorar la eficiencia y el rendimiento."),
            ("Automática de 9 velocidades", "Transmisión automática con 9 velocidades que ofrece una amplia gama de relaciones para optimizar el consumo de combustible."),
            ("Automática de 10 velocidades", "Transmisión automática de última generación con 10 velocidades para un rendimiento excepcional y eficiencia máxima."),
            ("Automática de 7 velocidades", "Transmisión automática con 7 velocidades que proporciona un equilibrio entre rendimiento y eficiencia."),
            ("Automática de 6 velocidades", "Transmisión automática con 6 velocidades que ofrece cambios suaves y una buena respuesta."),
            ("Automática de 5 velocidades", "Transmisión automática básica con 5 velocidades, común en vehículos más antiguos o económicos."),
            ("Automática de 4 velocidades", "Transmisión automática con 4 velocidades, común en vehículos más antiguos."),
            ("Automática de 3 velocidades", "Transmisión automática básica con 3 velocidades, común en vehículos muy antiguos."),
            ("Automática de 2 velocidades", "Transmisión automática muy básica con solo 2 velocidades, rara en vehículos modernos."),
            ("Automática de 1 velocidad", "Transmisión automática extremadamente básica con solo 1 velocidad, rara en vehículos modernos."),
        ]
        for nombre, descripcion in tipos_transmision:
            TipoTransmision.objects.get_or_create(nombre=nombre, defaults={'descripcion': descripcion})
        self.stdout.write(self.style.SUCCESS('Tipos de transmisión cargados exitosamente.'))