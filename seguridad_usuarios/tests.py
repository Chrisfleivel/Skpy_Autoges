# seguridad_usuarios/tests.py

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from configuraciones_maestras.models import Cargo, Departamento, Empresa, Sucursal

from .forms import EmpleadoForm, ContactoEmpleadoForm
from .models import Empleado, Permiso, Rol, UsuarioPerfil


class ContactoEmpleadoFormTests(TestCase):
    def test_empleado_form_expone_telefono_y_sucursal(self):
        form = EmpleadoForm()

        self.assertIn('telefono', form.fields)
        self.assertIn('sucursal', form.fields)
        self.assertNotIn('direccion', form.fields)

    def test_contacto_empleado_form_expone_telefono_y_direccion(self):
        form = ContactoEmpleadoForm()

        self.assertIn('telefono', form.fields)
        self.assertIn('direccion', form.fields)


class ListaEmpleadosFilterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='pass12345',
        )
        self.empresa = Empresa.objects.create(nombre='Empresa Activa', ruc='80000001', email='empresa@test.com', telefono='123', direccion='Av. Principal 1')
        self.sucursal = Sucursal.objects.create(empresa=self.empresa, nombre='Matriz', activa=True)
        self.departamento = Departamento.objects.create(empresa=self.empresa, nombre='Ventas', estado=True)
        self.cargo = Cargo.objects.create(nombre='Vendedor', departamento=self.departamento, estado=True)
        self.otro_departamento = Departamento.objects.create(empresa=self.empresa, nombre='Tecnología', estado=True)
        self.otro_cargo = Cargo.objects.create(nombre='Analista', departamento=self.otro_departamento, estado=True)

        self.empleado = Empleado(
            tipo_persona='FISICA',
            nombre='Carlos',
            apellidos='Pérez',
            documento_identidad='12345678',
            email='carlos@example.com',
            departamento=self.departamento,
            cargo=self.cargo,
            sucursal=self.sucursal,
            tiene_usuario=True,
        )
        self.empleado_2 = Empleado(
            tipo_persona='FISICA',
            nombre='Ana',
            apellidos='Gómez',
            documento_identidad='87654321',
            email='ana@example.com',
            departamento=self.otro_departamento,
            cargo=self.otro_cargo,
            sucursal=self.sucursal,
            tiene_usuario=False,
        )
        self.empleado_3 = Empleado(
            tipo_persona='FISICA',
            nombre='Luis',
            apellidos='Martínez',
            documento_identidad='11111111',
            email='luis@example.com',
            departamento=self.departamento,
            cargo=self.cargo,
            sucursal=self.sucursal,
            tiene_usuario=False,
        )
        Empleado.objects.bulk_create([self.empleado, self.empleado_2, self.empleado_3])
        self.empleado.refresh_from_db()
        self.empleado_2.refresh_from_db()
        self.empleado_3.refresh_from_db()

    def test_lista_empleados_filtra_por_busqueda_usuario_departamento_y_cargo(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('lista_empleados'), {
            'busqueda': '87654321',
            'departamento_id': self.otro_departamento.id,
            'cargo_id': self.otro_cargo.id,
            'usuario': 'NO',
        })

        self.assertEqual(list(response.context['empleados']), [self.empleado_2])


class EmpleadoEmpresaScopeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='admin2',
            email='admin2@example.com',
            password='pass12345',
        )
        self.empresa_1 = Empresa.objects.create(nombre='Empresa 1', ruc='1', email='e1@test.com', telefono='1', direccion='Dir 1')
        self.empresa_2 = Empresa.objects.create(nombre='Empresa 2', ruc='2', email='e2@test.com', telefono='2', direccion='Dir 2')

        self.departamento_1 = Departamento.objects.create(empresa=self.empresa_1, nombre='Ventas', estado=True)
        self.departamento_2 = Departamento.objects.create(empresa=self.empresa_2, nombre='Compras', estado=True)
        self.cargo_1 = Cargo.objects.create(nombre='Vendedor', departamento=self.departamento_1, estado=True)
        self.cargo_2 = Cargo.objects.create(nombre='Comprador', departamento=self.departamento_2, estado=True)
        self.sucursal_1 = Sucursal.objects.create(empresa=self.empresa_1, nombre='Central', activa=True)
        self.sucursal_2 = Sucursal.objects.create(empresa=self.empresa_2, nombre='Sucursal 2', activa=True)

        self.empleado_1 = Empleado.objects.create(
            tipo_persona='FISICA',
            nombre='Empleado',
            apellidos='Uno',
            documento_identidad='10000001',
            email='uno@test.com',
            departamento=self.departamento_1,
            cargo=self.cargo_1,
            sucursal=self.sucursal_1,
            tiene_usuario=False,
        )
        self.empleado_2 = Empleado.objects.create(
            tipo_persona='FISICA',
            nombre='Empleado',
            apellidos='Dos',
            documento_identidad='10000002',
            email='dos@test.com',
            departamento=self.departamento_2,
            cargo=self.cargo_2,
            sucursal=self.sucursal_2,
            tiene_usuario=False,
        )

    def test_lista_empleados_filtra_por_empresa_activa(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('lista_empleados'))

        self.assertEqual(list(response.context['empleados']), [self.empleado_1])

    def test_formulario_empleado_solo_muestra_sucursales_de_empresa_activa(self):
        form = EmpleadoForm()

        self.assertEqual(list(form.fields['sucursal'].queryset), [self.sucursal_1])


class UsuarioPerfilRoleResolutionTests(TestCase):
    def test_permisos_asignados_se_obtienen_del_cargo_del_empleado(self):
        departamento = Departamento.objects.create(nombre='Operaciones', estado=True)
        cargo = Cargo.objects.create(nombre='Supervisor', departamento=departamento, estado=True)
        cargo_rol = Rol.objects.create(nombre='Rol de Cargo')
        permiso_cargo = Permiso.objects.create(codename='seguridad_usuarios.permiso_cargo', nombre='Permiso cargo')
        cargo_rol.permisos.add(permiso_cargo)
        cargo.roles.add(cargo_rol)

        empleado = Empleado(
            tipo_persona='FISICA',
            nombre='María',
            apellidos='López',
            documento_identidad='22222222',
            email='maria@example.com',
            departamento=departamento,
            cargo=cargo,
            tiene_usuario=True,
        )
        Empleado.objects.bulk_create([empleado])
        empleado.refresh_from_db()
        usuario = get_user_model().objects.create_user(username='maria_user', password='pass12345')
        usuario_perfil = usuario.perfil
        usuario_perfil.empleado = empleado
        usuario_perfil.save()

        perfil_rol = Rol.objects.create(nombre='Rol de Perfil')
        permiso_perfil = Permiso.objects.create(codename='seguridad_usuarios.permiso_perfil', nombre='Permiso perfil')
        perfil_rol.permisos.add(permiso_perfil)
        usuario_perfil.roles.add(perfil_rol)

        permisos = usuario_perfil.permisos_asignados()

        self.assertIn('seguridad_usuarios.permiso_cargo', permisos)
        self.assertIn('seguridad_usuarios.permiso_perfil', permisos)
