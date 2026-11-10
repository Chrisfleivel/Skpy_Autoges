# seguridad_usuarios/tests.py

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from configuraciones_maestras.models import Cargo, Departamento

from .forms import EmpleadoForm, ContactoEmpleadoForm
from .models import Empleado, Permiso, Rol, UsuarioPerfil


class ContactoEmpleadoFormTests(TestCase):
    def test_empleado_form_no_expone_telefono_ni_direccion(self):
        form = EmpleadoForm()

        self.assertNotIn('telefono', form.fields)
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
        self.departamento = Departamento.objects.create(nombre='Ventas', estado=True)
        self.cargo = Cargo.objects.create(nombre='Vendedor', departamento=self.departamento, estado=True)
        self.otro_departamento = Departamento.objects.create(nombre='Tecnología', estado=True)
        self.otro_cargo = Cargo.objects.create(nombre='Analista', departamento=self.otro_departamento, estado=True)

        self.empleado = Empleado(
            tipo_persona='FISICA',
            nombre='Carlos',
            apellidos='Pérez',
            documento_identidad='12345678',
            email='carlos@example.com',
            departamento=self.departamento,
            cargo=self.cargo,
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
        self.assertNotIn('seguridad_usuarios.permiso_perfil', permisos)
