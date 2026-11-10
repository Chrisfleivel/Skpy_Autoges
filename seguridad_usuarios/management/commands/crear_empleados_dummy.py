from django.core.management.base import BaseCommand

from configuraciones_maestras.models import Cargo, Departamento
from seguridad_usuarios.models import Empleado, ContactoEmpleado


EMPLEADOS_DE_PRUEBA = [
    {"nombre": "Juan Carlos", "apellidos": "Benítez", "direccion": "Av. Mariscal López 1234, Asunción"},
    {"nombre": "María Elena", "apellidos": "González", "direccion": "Calle Palma 567, Asunción"},
    {"nombre": "Pedro Antonio", "apellidos": "Duarte", "direccion": "Av. España 987, Asunción"},
    {"nombre": "Laura Beatriz", "apellidos": "Rojas", "direccion": "Calle Cerro Corá 432, Asunción"},
    {"nombre": "Carlos Alberto", "apellidos": "Silva", "direccion": "Calle Antequera 789, Luque"},
    {"nombre": "Ana María", "apellidos": "Fernández", "direccion": "Av. Aviadores del Chaco 210, Asunción"},
    {"nombre": "Jorge Luis", "apellidos": "Medina", "direccion": "Calle Iturbe 654, San Lorenzo"},
    {"nombre": "Silvia Patricia", "apellidos": "Giménez", "direccion": "Av. Fernando de la Mora 321, Asunción"},
    {"nombre": "Roberto Daniel", "apellidos": "Ayala", "direccion": "Calle Brasil 456, Fernando de la Mora"},
    {"nombre": "Carmen Rosa", "apellidos": "Villalba", "direccion": "Av. Primer Presidente 890, Asunción"},
    {"nombre": "Víctor Hugo", "apellidos": "Ortiz", "direccion": "Calle Herrera 112, Lambaré"},
    {"nombre": "Patricia Beatriz", "apellidos": "Ríos", "direccion": "Av. Sacramento 543, Asunción"},
    {"nombre": "Gustavo Adolfo", "apellidos": "Vera", "direccion": "Calle Colón 678, Asunción"},
    {"nombre": "Natalia Soledad", "apellidos": "Cáceres", "direccion": "Av. Defensores del Chaco 901, Fernando de la Mora"},
    {"nombre": "Francisco Javier", "apellidos": "Paredes", "direccion": "Calle Eligio Ayala 234, Asunción"},
    {"nombre": "Claudia Marcela", "apellidos": "Mendoza", "direccion": "Av. Eusebio Ayala 345, Asunción"},
    {"nombre": "Diego Armando", "apellidos": "Escobar", "direccion": "Calle General Díaz 456, Luque"},
    {"nombre": "Sonia Raquel", "apellidos": "Marecos", "direccion": "Av. Molas López 789, Asunción"},
    {"nombre": "Rubén Darío", "apellidos": "Espínola", "direccion": "Calle Tacuary 123, Asunción"},
    {"nombre": "Teresa Beatriz", "apellidos": "Portillo", "direccion": "Av. Artigas 567, Asunción"},
    {"nombre": "Luis Fernando", "apellidos": "Aquino", "direccion": "Calle Estados Unidos 890, Lambaré"},
    {"nombre": "Gabriela Alejandra", "apellidos": "Franco", "direccion": "Av. Santa Teresa 210, Asunción"},
    {"nombre": "Hugo César", "apellidos": "Bogado", "direccion": "Calle Azara 432, Asunción"},
    {"nombre": "María José", "apellidos": "Pereira", "direccion": "Av. Félix Bogado 654, Asunción"},
    {"nombre": "Ricardo Manuel", "apellidos": "Ovelar", "direccion": "Calle 14 de Mayo 987, San Lorenzo"},
    {"nombre": "Fátima Luján", "apellidos": "Zárate", "direccion": "Av. República Argentina 112, Asunción"},
    {"nombre": "Cristian David", "apellidos": "Ramírez", "direccion": "Calle Caballero 321, Asunción"},
    {"nombre": "Elena Beatriz", "apellidos": "Valdez", "direccion": "Av. Cacique Lambaré 543, Lambaré"},
    {"nombre": "Alberto Ramón", "apellidos": "Salinas", "direccion": "Calle Gral. Santos 789, Asunción"},
    {"nombre": "Rosa María", "apellidos": "Acosta", "direccion": "Av. España 234, Asunción"},
]


class Command(BaseCommand):
    help = 'Crea empleados de prueba usando los nombres, apellidos y direcciones proporcionados.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=30, help='Cantidad de empleados a crear')

    def handle(self, *args, **options):
        count = min(options.get('count', 30) or 30, len(EMPLEADOS_DE_PRUEBA))
        empleados_a_crear = []
        contactos_a_crear = []
        documentos = []

        Empleado.objects.filter(email__endswith='@example.com').delete()

        departamentos_disponibles = list(Departamento.objects.filter(estado=True).order_by('id'))
        if not departamentos_disponibles:
            departamentos_disponibles = list(Departamento.objects.order_by('id'))

        cargos_por_departamento = {}
        for departamento in departamentos_disponibles:
            cargos = list(Cargo.objects.filter(departamento=departamento, estado=True).order_by('id'))
            if not cargos:
                cargos = list(Cargo.objects.filter(departamento=departamento).order_by('id'))
            cargos_por_departamento[departamento.id] = cargos

        datos_empleados = []

        for index, data in enumerate(EMPLEADOS_DE_PRUEBA[:count], start=1):
            documento = str(50000000 + index)
            email = f"{data['nombre'].replace(' ', '').lower()}.{data['apellidos'].replace(' ', '').lower()}@example.com"
            documentos.append(documento)

            departamento_asignado = None
            cargo_asignado = None
            if departamentos_disponibles:
                departamento_asignado = departamentos_disponibles[(index - 1) % len(departamentos_disponibles)]
                cargos_departamento = cargos_por_departamento.get(departamento_asignado.id, [])
                if cargos_departamento:
                    cargo_asignado = cargos_departamento[(index - 1) % len(cargos_departamento)]

            empleado = Empleado(
                tipo_persona='FISICA',
                nombre=data['nombre'],
                apellidos=data['apellidos'],
                documento_identidad=documento,
                ruc=f"{documento}-0",
                email=email,
                cargo=cargo_asignado,
                departamento=departamento_asignado,
            )
            empleados_a_crear.append(empleado)
            datos_empleados.append(data)

        Empleado.objects.bulk_create(empleados_a_crear)
        empleados_creados = list(Empleado.objects.filter(documento_identidad__in=documentos))

        for index, empleado in enumerate(empleados_creados):
            datos = datos_empleados[index]
            contactos_a_crear.append(
                ContactoEmpleado(
                    empleado=empleado,
                    categoria='PERSONAL',
                    tipo_persona='FISICA',
                    nombre=empleado.nombre,
                    apellidos=empleado.apellidos,
                    telefono=f'09{index + 1:08d}',
                    direccion=datos['direccion'],
                    email=empleado.email,
                    es_principal=True,
                )
            )

        ContactoEmpleado.objects.bulk_create(contactos_a_crear)

        self.stdout.write(self.style.SUCCESS(f'Creados {len(empleados_creados)} empleados con sus contactos.'))