from django.core.management.base import BaseCommand

from clientes_pedidos.models import Cliente, ContactoCliente


class Command(BaseCommand):
    help = 'Genera clientes de prueba físicos y jurídicos con un contacto asociado.'

    def handle(self, *args, **options):
        personas = [
            ('Hugo Ramón Martínez', '1.234.567', 'Av. Mcal. López 4500, Asunción', '+595981000001'),
            ('Sandra Lorena Ortiz', '2.345.678', 'Calle Palma 123, Asunción', '+595981000002'),
            ('Javier Ignacio Sosa', '3.456.789', 'Av. España 980, Asunción', '+595981000003'),
            ('Elena María Duarte', '4.567.890', 'Calle Iturbe 456, San Lorenzo', '+595981000004'),
            ('Ricardo Fabián Ruiz', '5.678.901', 'Av. Aviadores del Chaco 2500, Asunción', '+595981000005'),
            ('Natalia Beatriz Ríos', '6.789.012', 'Calle Herrera 789, Lambaré', '+595981000006'),
            ('Carlos Daniel Giménez', '7.890.123', 'Av. Fernando de la Mora 4400, Asunción', '+595981000007'),
            ('Patricia Inés Silva', '8.901.234', 'Calle Cerro Corá 1110, Asunción', '+595981000008'),
            ('Jorge Alberto Ayala', '9.012.345', 'Av. Sacramento 890, Asunción', '+595981000009'),
            ('María José Benítez', '1.123.456', 'Calle Brasil 333, Luque', '+595981000010'),
            ('Víctor Hugo Paredes', '2.234.567', 'Av. Eusebio Ayala 5500, Asunción', '+595981000011'),
            ('Sonia Raquel Franco', '3.345.678', 'Calle Eligio Ayala 670, Asunción', '+595981000012'),
            ('Gustavo Adolfo Vera', '4.456.789', 'Av. Primer Presidente 1200, Asunción', '+595981000013'),
            ('Fátima Luján Zárate', '5.567.890', 'Calle Antequera 990, Asunción', '+595981000014'),
            ('Diego Armando Escobar', '6.678.901', 'Av. Molas López 450, Asunción', '+595981000015'),
            ('Carmen Rosa Villalba', '7.789.012', 'Calle Azara 1500, Asunción', '+595981000016'),
            ('Rubén Darío Espínola', '8.890.123', 'Av. Santa Teresa 3200, Asunción', '+595981000017'),
            ('Teresa Beatriz Portillo', '9.901.234', 'Calle Tacuary 880, Asunción', '+595981000018'),
            ('Luis Fernando Aquino', '1.012.345', 'Av. Artigas 2100, Asunción', '+595981000019'),
            ('Gabriela Alejandra Franco', '2.123.456', 'Calle Estados Unidos 410, Lambaré', '+595981000020'),
        ]

        empresas = [
            ('Logística del Este S.A.', '80012345-6', 'Av. Mcal. López 1200, Asunción', 'Transporte', '+595981000021'),
            ('Agroganadera El Norte SRL', '80098765-4', 'Ruta Transchaco Km 15, Mariano R. Alonso', 'Agrícola', '+595981000022'),
            ('Construcciones del Sur S.A.', '80022334-1', 'Av. Cacique Lambaré 850, Lambaré', 'Construcción', '+595981000023'),
            ('TecnoShop Paraguay S.A.', '80055667-9', 'Av. Eusebio Ayala 4300, Asunción', 'Electrónica', '+595981000024'),
            ('Servicios Contables Integrales SRL', '80044556-2', 'Calle Palma 500, Asunción', 'Consultoría', '+595981000025'),
            ('Inmobiliaria Horizonte S.A.', '80066778-0', 'Av. Santa Teresa 2800, Asunción', 'Bienes Raíces', '+595981000026'),
            ('Importadora Global Motor SRL', '80077889-3', 'Av. Aviadores del Chaco 3100, Asunción', 'Automotriz', '+595981000027'),
            ('Alimentos del Paraguay S.A.', '80011223-5', 'Ruta 2 Km 18, Capiatá', 'Distribución', '+595981000028'),
            ('Soluciones Energéticas PY S.A.', '80033445-7', 'Av. Mcal. Estigarribia 900, San Lorenzo', 'Energía', '+595981000029'),
            ('Publicidad Creativa SRL', '80088990-1', 'Calle Herrera 120, Asunción', 'Marketing', '+595981000030'),
        ]

        self._crear_personas(personas)
        self._crear_empresas(empresas)

        self.stdout.write(self.style.SUCCESS('Clientes de prueba creados correctamente.'))

    def _crear_personas(self, personas):
        for nombre_completo, documento, direccion, telefono in personas:
            partes = nombre_completo.split()
            nombre = partes[0]
            apellidos = ' '.join(partes[1:]) if len(partes) > 1 else ''
            documento_limpio = ''.join(char for char in documento if char.isdigit())
            ruc = f'{documento_limpio}-0' if documento_limpio else ''

            cliente, created = Cliente.objects.get_or_create(
                documento_identidad=documento_limpio,
                defaults={
                    'tipo_persona': 'FISICA',
                    'nombre': nombre,
                    'apellidos': apellidos,
                    'ruc': ruc,
                    'telefono': '',
                    'direccion': '',
                    'estado': True,
                },
            )
            if not created:
                cliente.nombre = nombre
                cliente.apellidos = apellidos
                cliente.ruc = ruc
                cliente.telefono = ''
                cliente.direccion = ''
                cliente.save(update_fields=['nombre', 'apellidos', 'ruc', 'telefono', 'direccion'])

            self._crear_contacto(
                cliente=cliente,
                nombre=nombre,
                apellidos=apellidos,
                telefono=telefono,
                direccion=direccion,
            )

    def _crear_empresas(self, empresas):
        for razon_social, ruc, direccion, rubro, telefono in empresas:
            cliente, created = Cliente.objects.get_or_create(
                ruc=ruc,
                defaults={
                    'tipo_persona': 'JURIDICA',
                    'razon_social': razon_social,
                    'nombre': '',
                    'apellidos': '',
                    'documento_identidad': '',
                    'telefono': '',
                    'direccion': '',
                    'estado': True,
                },
            )
            if not created:
                cliente.razon_social = razon_social
                cliente.documento_identidad = ''
                cliente.telefono = ''
                cliente.direccion = ''
                cliente.save(update_fields=['razon_social', 'documento_identidad', 'telefono', 'direccion'])

            self._crear_contacto(
                cliente=cliente,
                nombre=razon_social.split()[0],
                apellidos=' '.join(razon_social.split()[1:]) if len(razon_social.split()) > 1 else '',
                telefono=telefono,
                direccion=direccion,
            )

    def _crear_contacto(self, cliente, nombre, apellidos, telefono, direccion):
        contacto, created = ContactoCliente.objects.get_or_create(
            cliente=cliente,
            defaults={
                'tipo_persona': 'FISICA',
                'nombre': nombre,
                'apellidos': apellidos,
                'telefono': telefono,
                'email': '',
                'direccion': direccion,
                'estado': True,
            },
        )
        if not created:
            contacto.nombre = nombre
            contacto.apellidos = apellidos
            contacto.telefono = telefono
            contacto.direccion = direccion
            contacto.save(update_fields=['nombre', 'apellidos', 'telefono', 'direccion'])