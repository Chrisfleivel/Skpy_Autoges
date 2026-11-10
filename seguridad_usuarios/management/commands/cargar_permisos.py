import sys

from django.core.management.base import BaseCommand
from seguridad_usuarios.models import Permiso
#from clientes_pedidos.views import permisos_iniciales_clientes_pedidos
#from configuraciones_maestras.views import permisos_iniciales_configuraciones_maestras
#from seguridad_usuarios.views import permisos_iniciales_seguridad_usuarios
#from inventario.views import permisos_iniciales_inventario
from configuraciones_maestras.permisos import generar_permisos_iniciales_configuraciones_maestras
from seguridad_usuarios.permisos import generar_permisos_iniciales_seguridad_usuarios
from inventario.permisos import generar_permisos_iniciales_inventario
from cobranzas.permisos import generar_permisos_iniciales_cobranzas
from clientes_pedidos.permisos import generar_permisos_iniciales_clientes_pedidos
from importaciones.permisos import generar_permisos_iniciales_importaciones


class Command(BaseCommand):
    help = 'Carga permisos iniciales en la base de datos'

    def handle(self, *args, **kwargs):
        # La consola de Windows usa cp1252, que no soporta caracteres como '✓'.
        # Forzamos UTF-8 en la salida (con reemplazo como último recurso) para
        # evitar UnicodeEncodeError al imprimir el mensaje final.
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(errors='replace')

        permisos_iniciales = buscar_permisos()
        creados = 0
        existentes = 0
        
        for permiso in permisos_iniciales:
            sector = permiso.get('sector') or derive_sector_from_codename(permiso.get('codename', ''))
            _, created = Permiso.objects.get_or_create(
                codename=permiso['codename'],
                defaults={
                    'nombre': permiso['nombre'],
                    'descripcion': permiso.get('descripcion', ''),
                    'sector': sector,
                }
            )
            if created:
                creados += 1
            else:
                existentes += 1
        
        mensaje = f'✓ Permisos cargados: {creados} creados, {existentes} ya existían.'
        self.stdout.write(self.style.SUCCESS(mensaje))

def derive_sector_from_codename(codename):
    if not codename:
        return ''
    if '.' in codename:
        sector = codename.split('.', 1)[0]
        return sector.replace('_', ' ').title()
    return ''


def buscar_permisos():
    """Función para buscar y combinar permisos iniciales de diferentes módulos."""
    permisos = []
    permisos.extend(generar_permisos_iniciales_clientes_pedidos())
    permisos.extend(generar_permisos_iniciales_configuraciones_maestras())
    permisos.extend(generar_permisos_iniciales_seguridad_usuarios())
    permisos.extend(generar_permisos_iniciales_inventario())
    permisos.extend(generar_permisos_iniciales_cobranzas())
    permisos.extend(generar_permisos_iniciales_importaciones())
    
    return permisos