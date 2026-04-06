from django.core.management.base import BaseCommand
from configuraciones_maestras.models import ConfiguracionApariencia


class Command(BaseCommand):
    help = 'Crea una configuración de apariencia por defecto si no existe'

    def handle(self, *args, **options):
        if ConfiguracionApariencia.objects.exists():
            self.stdout.write(
                self.style.WARNING('Ya existe una configuración de apariencia')
            )
            return

        config = ConfiguracionApariencia.objects.create(
            tema=ConfiguracionApariencia.THEME_DEFAULT,
            tipografia=ConfiguracionApariencia.FONT_ROBOTO,
            tamanio=16,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Configuración de apariencia creada exitosamente: {config}'
            )
        )