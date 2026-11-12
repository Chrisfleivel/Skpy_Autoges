from django.core.management.base import BaseCommand
from configuraciones_maestras.models import Departamento, Cargo


class Command(BaseCommand):
    help = 'Carga y repara departamentos y cargos iniciales en la base de datos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina los departamentos y cargos base y los vuelve a crear desde cero.',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)

        departamentos_cargos_iniciales = [
            {
                'departamento': {
                    'nombre': 'Recursos Humanos',
                    'descripcion': 'Departamento encargado de la gestión del personal.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Recursos Humanos', 'descripcion': 'Responsable de la gestión del departamento.'},
                    {'nombre': 'Analista de Nómina', 'descripcion': 'Encargado de procesar la nómina del personal.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Tecnología de la Información',
                    'descripcion': 'Departamento encargado de la infraestructura tecnológica.'
                },
                'cargos': [
                    {'nombre': 'Administrador de Sistemas', 'descripcion': 'Responsable de la administración de servidores y redes.'},
                    {'nombre': 'Desarrollador de Software', 'descripcion': 'Encargado del desarrollo y mantenimiento de aplicaciones.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Ventas',
                    'descripcion': 'Departamento encargado de la comercialización de productos y servicios.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Ventas', 'descripcion': 'Responsable de la estrategia y gestión del equipo de ventas.'},
                    {'nombre': 'Representante de Ventas', 'descripcion': 'Encargado de interactuar con clientes y cerrar ventas.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Marketing',
                    'descripcion': 'Departamento encargado de la promoción y publicidad de productos y servicios.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Marketing', 'descripcion': 'Responsable de la estrategia de marketing.'},
                    {'nombre': 'Especialista en Marketing Digital', 'descripcion': 'Encargado de las campañas en línea y redes sociales.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Finanzas',
                    'descripcion': 'Departamento encargado de la gestión financiera y contable.'
                },
                'cargos': [
                    {'nombre': 'CFO (Director Financiero)', 'descripcion': 'Responsable de la planificación financiera y gestión de riesgos.'},
                    {'nombre': 'Contador', 'descripcion': 'Encargado de llevar los registros contables y preparar informes financieros.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Operaciones',
                    'descripcion': 'Departamento encargado de la gestión diaria y logística.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Operaciones', 'descripcion': 'Responsable de supervisar las operaciones diarias.'},
                    {'nombre': 'Coordinador Logístico', 'descripcion': 'Encargado de gestionar la cadena de suministro y distribución.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Atención al Cliente',
                    'descripcion': 'Departamento encargado de gestionar las relaciones con los clientes.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Atención al Cliente', 'descripcion': 'Responsable de la estrategia y gestión del equipo de atención al cliente.'},
                    {'nombre': 'Representante de Servicio al Cliente', 'descripcion': 'Encargado de interactuar con clientes para resolver sus consultas y problemas.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Inventario',
                    'descripcion': 'Departamento encargado de la gestión de inventarios y almacenes.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Inventario', 'descripcion': 'Responsable de la gestión y control del inventario.'},
                    {'nombre': 'Encargado de Almacén', 'descripcion': 'Encargado de supervisar las operaciones del almacén y la recepción de mercancías.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Calidad',
                    'descripcion': 'Departamento encargado de asegurar la calidad de productos y servicios.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Calidad', 'descripcion': 'Responsable de la implementación y supervisión de los estándares de calidad.'},
                    {'nombre': 'Inspector de Calidad', 'descripcion': 'Encargado de realizar inspecciones y pruebas para asegurar la calidad.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Investigación y Desarrollo',
                    'descripcion': 'Departamento encargado de la innovación y desarrollo de nuevos productos.'
                },
                'cargos': [
                    {'nombre': 'Director de I+D', 'descripcion': 'Responsable de la estrategia y gestión del departamento de investigación y desarrollo.'},
                    {'nombre': 'Científico de Investigación', 'descripcion': 'Encargado de llevar a cabo investigaciones para el desarrollo de nuevos productos.'},
                ]
            },
            {
                'departamento': {
                    'nombre': 'Importaciones y Exportaciones',
                    'descripcion': 'Departamento encargado de gestionar las operaciones de comercio internacional.'
                },
                'cargos': [
                    {'nombre': 'Gerente de Importaciones y Exportaciones', 'descripcion': 'Responsable de la estrategia y gestión del comercio internacional.'},
                    {'nombre': 'Coordinador de Logística Internacional', 'descripcion': 'Encargado de coordinar el transporte y la logística de importaciones y exportaciones.'},
                ]
            },
        ]

        if reset:
            nombres_departamentos = [item['departamento']['nombre'] for item in departamentos_cargos_iniciales]
            nombres_cargos = [cargo['nombre'] for item in departamentos_cargos_iniciales for cargo in item['cargos']]
            Cargo.objects.filter(nombre__in=nombres_cargos).delete()
            Departamento.objects.filter(nombre__in=nombres_departamentos).delete()
            self.stdout.write(self.style.WARNING('Se reiniciaron los departamentos y cargos base.'))

        for item in departamentos_cargos_iniciales:
            departamento_data = item['departamento']
            departamento = Departamento.objects.filter(nombre=departamento_data['nombre']).first()

            if departamento is None:
                departamento = Departamento.objects.create(
                    nombre=departamento_data['nombre'],
                    descripcion=departamento_data['descripcion'],
                    estado=True,
                )
                self.stdout.write(self.style.SUCCESS(f'Departamento "{departamento.nombre}" creado.'))
            else:
                departamento.descripcion = departamento_data['descripcion']
                departamento.estado = True
                departamento.save(update_fields=['descripcion', 'estado'])
                self.stdout.write(f'Departamento "{departamento.nombre}" restaurado/actualizado.')

            for cargo_data in item['cargos']:
                cargo = Cargo.objects.filter(nombre=cargo_data['nombre']).first()

                if cargo is None:
                    cargo = Cargo.objects.create(
                        nombre=cargo_data['nombre'],
                        descripcion=cargo_data['descripcion'],
                        departamento=departamento,
                        estado=True,
                    )
                    self.stdout.write(self.style.SUCCESS(f'  Cargo "{cargo.nombre}" creado en el departamento "{departamento.nombre}".'))
                else:
                    cargo.descripcion = cargo_data['descripcion']
                    cargo.departamento = departamento
                    cargo.estado = True
                    cargo.save(update_fields=['descripcion', 'departamento', 'estado'])
                    self.stdout.write(f'  Cargo "{cargo.nombre}" restaurado/actualizado para el departamento "{departamento.nombre}".')

        self.stdout.write(self.style.SUCCESS('Departamentos y cargos cargados correctamente.'))