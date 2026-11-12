from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from seguridad_usuarios.models import Rol, Permiso

DEFAULT_ROLES = [
    {
        'nombre': 'Administrador',
        'descripcion': 'Acceso completo a todas las funcionalidades del sistema.',
        'permisos': 'all',
    },
    {
        'nombre': 'Seguridad',
        'descripcion': 'Gestiona usuarios, roles y permisos.',
        'prefijos': ['seguridad_usuarios.'],
        'sectores': ['Seguridad y Usuarios'],
    },
    {
        'nombre': 'Inventario',
        'descripcion': 'Gestiona vehículos, repuestos y existencias.',
        'prefijos': ['inventario.'],
        'sectores': ['Inventario'],
    },
    {
        'nombre': 'Ventas',
        'descripcion': 'Gestiona pedidos, clientes y ventas.',
        'prefijos': ['clientes_pedidos.', 'cobranzas.', 'pedido_busqueda.'],
        'sectores': ['Clientes Pedidos', 'Cobranzas'],
    },
    {
        'nombre': 'Configuraciones',
        'descripcion': 'Gestiona datos maestros y configuraciones del sistema.',
        'prefijos': ['configuraciones_maestras.'],
        'sectores': ['Configuraciones Maestras'],
    },
    {
        'nombre': 'Compras',
        'descripcion': 'Gestiona facturas comerciales y compras a proveedores.',
        'prefijos': ['compras.'],
        'sectores': ['Compras'],
    },
    {
        'nombre': 'Importaciones',
        'descripcion': 'Gestiona embarques, documentos y conciliación de importación.',
        'prefijos': ['importaciones.'],
        'sectores': ['Importaciones'],
    },
]


class Command(BaseCommand):
    help = 'Crea roles predeterminados y asigna permisos basados en los permisos cargados.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recrear roles existentes y actualizar sus permisos con la definición predeterminada.',
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Crear o actualizar solamente un rol específico por nombre.',
        )

    def handle(self, *args, **options):
        if not Permiso.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    'No hay permisos cargados. Ejecute "python manage.py cargar_permisos" antes de crear roles.'
                )
            )
            return

        roles_a_crear = DEFAULT_ROLES
        role_name = options.get('role')
        if role_name:
            roles_a_crear = [
                rol for rol in DEFAULT_ROLES if rol['nombre'].lower() == role_name.strip().lower()
            ]
            if not roles_a_crear:
                self.stdout.write(
                    self.style.ERROR(f'No se encontró una definición de rol predeterminado con nombre "{role_name}".')
                )
                return

        for role_def in roles_a_crear:
            with transaction.atomic():
                rol, creado = Rol.objects.get_or_create(
                    nombre=role_def['nombre'],
                    defaults={'descripcion': role_def['descripcion']},
                )

                if creado:
                    self.stdout.write(self.style.SUCCESS(f'Rol "{rol.nombre}" creado.'))
                else:
                    if options.get('force'):
                        rol.descripcion = role_def['descripcion']
                        rol.estado = True
                        rol.fecha_vigencia = None
                        rol.save()
                        self.stdout.write(
                            self.style.WARNING(f'Rol "{rol.nombre}" existente actualizado con la configuración predeterminada.')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Rol "{rol.nombre}" ya existe. Use --force para actualizar su descripción y permisos.'
                            )
                        )

                permisos = self._buscar_permisos(role_def)
                if permisos.exists():
                    if rol.utilizado and not options.get('force'):
                        self.stdout.write(
                            self.style.WARNING(
                                f'El rol "{rol.nombre}" está asignado a usuarios. No se actualizaron sus permisos.'
                            )
                        )
                    else:
                        rol.permisos.set(permisos)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Se asignaron {permisos.count()} permisos al rol "{rol.nombre}".'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'No se encontraron permisos para el rol "{rol.nombre}" con la definición actual.'
                        )
                    )

        self.stdout.write(self.style.SUCCESS('Proceso de creación/actualización de roles finalizado.'))

    def _buscar_permisos(self, role_def):
        permisos = Permiso.objects.none()
        if role_def.get('permisos') == 'all':
            return Permiso.objects.all()

        query = Q()
        for prefijo in role_def.get('prefijos', []):
            query |= Q(codename__startswith=prefijo)
        for sector in role_def.get('sectores', []):
            query |= Q(sector__iexact=sector)

        if query:
            permisos = Permiso.objects.filter(query)

        return permisos.order_by('codename')
