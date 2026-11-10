from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from seguridad_usuarios.models import Rol
from .models import Cargo, Departamento, Empresa, Moneda
from seguridad_usuarios.models import Empleado


class MonedaCatalogTests(TestCase):
    def test_crea_monedas_por_defecto_y_permite_agregar_otra_en_runtime(self):
        Moneda.ensure_defaults()

        self.assertIn('USD', Moneda.objects.values_list('codigo', flat=True))
        self.assertIn('PYG', Moneda.objects.values_list('codigo', flat=True))

        Moneda.objects.create(codigo='ARS', nombre='Peso argentino')

        self.assertIn('ARS', [codigo for codigo, _ in Moneda.get_choices()])

    def test_core_moneda_usa_datos_db_y_permite_nuevas_monedas_en_runtime(self):
        from core.models import Moneda as MonedaCore

        Moneda.ensure_defaults()
        Moneda.objects.create(codigo='BOV', nombre='Bolívar')

        self.assertIn('BOV', [codigo for codigo, _ in MonedaCore.get_choices()])
        self.assertIn('USD', MonedaCore.USD)

    def test_core_tasa_cambio_usa_el_modelo_persistido_y_soporta_runtime(self):
        from decimal import Decimal
        from core.models import TasaCambio as TasaCambioCore

        tasa = TasaCambioCore.registrar(
            moneda_origen='USD',
            moneda_destino='PYG',
            valor=Decimal('7500.00'),
            fecha=None,
        )

        self.assertEqual(tasa.moneda_origen, 'USD')
        self.assertEqual(tasa.moneda_destino, 'PYG')
        self.assertEqual(TasaCambioCore.obtener_tasa_actual('USD', 'PYG').valor, Decimal('7500.00'))


class EmpresaCrudTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='empresa_user', password='testpass123')
        content_type = ContentType.objects.get(app_label='configuraciones_maestras', model='empresa')
        for codename in ['view_empresa', 'add_empresa', 'change_empresa', 'delete_empresa']:
            permission = Permission.objects.get(content_type=content_type, codename=codename)
            self.user.user_permissions.add(permission)
        self.user.save()
        self.client.force_login(self.user)

    def test_listar_empresas_muestra_empresa_registrada(self):
        Empresa.objects.create(nombre='SKPY AutoGest', direccion='Asunción, Paraguay')

        response = self.client.get(reverse('lista_empresas'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SKPY AutoGest')

    def test_crear_empresa_guarda_datos_basicos(self):
        response = self.client.post(reverse('agregar_empresa'), {
            'nombre': 'SKPY Importaciones',
            'direccion': 'Av. Dr. Francia 1234',
            'telefono': '+595 981 111 222',
            'email': 'info@skpy.com.py',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Empresa.objects.filter(nombre='SKPY Importaciones').exists())


class CargoRoleAssignmentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='cargo_user', password='testpass123')
        content_type = ContentType.objects.get(app_label='configuraciones_maestras', model='cargo')
        for codename, name in [('agregar_cargo', 'Can agregar cargo'), ('editar_cargo', 'Can editar cargo')]:
            permission, _ = Permission.objects.get_or_create(content_type=content_type, codename=codename, defaults={'name': name})
            self.user.user_permissions.add(permission)
        self.user.save()
        self.client.force_login(self.user)
        self.departamento = Departamento.objects.create(nombre='Operaciones')
        self.rol_1 = Rol.objects.create(nombre='Rol A')
        self.rol_2 = Rol.objects.create(nombre='Rol B')

    def test_crear_cargo_guarda_varios_roles(self):
        response = self.client.post(reverse('agregar_cargo'), {
            'nombre': 'Analista',
            'departamento': self.departamento.id,
            'descripcion': 'Cargo de prueba',
            'vacantes': 1,
            'salario': '2500000',
            'roles': [self.rol_1.id, self.rol_2.id],
        })

        self.assertEqual(response.status_code, 302)
        cargo = Cargo.objects.get(nombre='Analista')
        self.assertEqual(set(cargo.roles.values_list('id', flat=True)), {self.rol_1.id, self.rol_2.id})

    def test_editar_cargo_actualiza_los_roles_asignados(self):
        cargo = Cargo.objects.create(nombre='Supervisor', departamento=self.departamento, descripcion='Cargo viejo')
        cargo.roles.add(self.rol_1)

        response = self.client.post(reverse('editar_cargo', args=[cargo.id]), {
            'nombre': 'Supervisor',
            'departamento': self.departamento.id,
            'descripcion': 'Cargo actualizado',
            'vacantes': 1,
            'salario': '3000000',
            'roles': [self.rol_2.id],
        })

        self.assertEqual(response.status_code, 302)
        cargo.refresh_from_db()
        self.assertEqual(list(cargo.roles.values_list('id', flat=True)), [self.rol_2.id])

    def test_cargo_no_eliminable_si_fue_relacionado_con_un_empleado(self):
        cargo = Cargo.objects.create(nombre='Analista', departamento=self.departamento, descripcion='Cargo historial')
        empleado = Empleado(
            tipo_persona='FISICA',
            nombre='Juan',
            apellidos='Pérez',
            documento_identidad='99999999',
            email='juan.perez@example.com',
            departamento=self.departamento,
            cargo=cargo,
            tiene_usuario=False,
        )
        Empleado.objects.bulk_create([empleado])
        empleado = Empleado.objects.get(documento_identidad='99999999')

        self.assertFalse(cargo.eliminable())

        empleado.cargo = None
        empleado.save()
        cargo.refresh_from_db()

        self.assertFalse(cargo.eliminable())
