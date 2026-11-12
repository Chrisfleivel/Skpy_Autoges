"""
Tests de la galería de fotos del vehículo (Tanda B).

`Vehiculo.imagen` es la portada; `VehiculoFoto` guarda las fotos
adicionales, ordenadas por `orden`, que se cargan con un formset en el
alta y la edición y se muestran en el detalle.
"""

import base64
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from inventario.models import (
    MarcaVehiculo,
    ModeloVehiculo,
    Vehiculo,
    VehiculoFoto,
)

# PNG 1x1 en blanco, válido para el validador de imágenes de Django.
PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)


def imagen(nombre='foto.png'):
    return SimpleUploadedFile(nombre, PNG_1X1, content_type='image/png')


class GaleriaVehiculoTestCase(TestCase):
    """Cada test usa un MEDIA_ROOT temporal para no ensuciar media/."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp(prefix='skpy_galeria_')
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='galeria_user', password='123456', is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

        self.marca = MarcaVehiculo.objects.create(nombre='Hyundai')
        self.modelo = ModeloVehiculo.objects.create(marca=self.marca, nombre='Tucson')

        self.vehiculo = Vehiculo.objects.create(
            nombre='Tucson',
            marca=self.marca,
            modelo=self.modelo,
            codigo_chasis='KMHJU14H9A0000001',
            **{'año': 2024},
            costo_compra=Decimal('20000000.00'),
            precio_venta=Decimal('28000000.00'),
        )

    def _datos_alta(self, **extra):
        datos = {
            'nombre': 'Tucson Sport',
            'codigo_chasis': 'KMHJU14H9A1234567',
            'combustible': 'nafta',
            'marca': str(self.marca.pk),
            'modelo': str(self.modelo.pk),
            'año': '2024',
            'kilometraje': '0',
            'costo_compra': '20000000.00',
            'precio_venta': '28000000.00',
            'descripcion': '',
            'fotos-TOTAL_FORMS': '1',
            'fotos-INITIAL_FORMS': '0',
            'fotos-MIN_NUM_FORMS': '0',
            'fotos-MAX_NUM_FORMS': '1000',
        }
        datos.update(extra)
        return datos

    # ------------------------------------------------------------------
    # Alta
    # ------------------------------------------------------------------
    def test_el_alta_registra_las_fotos_de_la_galeria(self):
        respuesta = self.client.post(reverse('registrar_vehiculo'), self._datos_alta(
            **{
                'fotos-0-imagen': imagen('frontal.png'),
                'fotos-0-descripcion': 'Frontal',
                'fotos-0-orden': '1',
            }
        ))

        self.assertEqual(respuesta.status_code, 302)
        vehiculo = Vehiculo.objects.get(codigo_chasis='KMHJU14H9A1234567')
        self.assertEqual(vehiculo.fotos.count(), 1)
        foto = vehiculo.fotos.first()
        self.assertEqual(foto.descripcion, 'Frontal')
        self.assertEqual(foto.orden, 1)
        self.assertTrue(foto.imagen.name.startswith('vehiculos/fotos/'))

    def test_el_alta_acepta_vehiculos_sin_fotos(self):
        respuesta = self.client.post(reverse('registrar_vehiculo'), self._datos_alta())

        self.assertEqual(respuesta.status_code, 302)
        vehiculo = Vehiculo.objects.get(codigo_chasis='KMHJU14H9A1234567')
        self.assertEqual(vehiculo.fotos.count(), 0)

    def test_el_alta_no_exige_la_gestion_del_formset(self):
        """Regression: un envío sin el formset debe guardar igual."""
        respuesta = self.client.post(reverse('registrar_vehiculo'), {
            'tipo': 'vehiculo',
            'marca': str(self.marca.pk),
            'modelo': str(self.modelo.pk),
            'año': '2024',
            'kilometraje': '0',
            'codigo_chasis': 'KMHJU14H9A7654321',
            'combustible': 'nafta',
        })

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Vehiculo.objects.filter(codigo_chasis='KMHJU14H9A7654321').exists())

    def test_la_edicion_no_exige_la_gestion_del_formset(self):
        respuesta = self.client.post(reverse('editar_vehiculo', args=[self.vehiculo.pk]), {
            'codigo_chasis': self.vehiculo.codigo_chasis,
            'marca': str(self.marca.pk),
            'modelo': str(self.modelo.pk),
            'año': '2024',
            'kilometraje': '0',
        })

        self.assertEqual(respuesta.status_code, 302)
        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.fotos.count(), 0)

    # ------------------------------------------------------------------
    # Edición
    # ------------------------------------------------------------------
    def test_la_edicion_agrega_fotos(self):
        self.client.post(reverse('editar_vehiculo', args=[self.vehiculo.pk]), {
            'nombre': self.vehiculo.nombre,
            'codigo_chasis': self.vehiculo.codigo_chasis,
            'marca': str(self.marca.pk),
            'modelo': str(self.modelo.pk),
            'año': '2024',
            'kilometraje': '0',
            'costo_compra': '20000000.00',
            'precio_venta': '28000000.00',
            'descripcion': '',
            'fotos-TOTAL_FORMS': '1',
            'fotos-INITIAL_FORMS': '0',
            'fotos-MIN_NUM_FORMS': '0',
            'fotos-MAX_NUM_FORMS': '1000',
            'fotos-0-imagen': imagen('lateral.png'),
            'fotos-0-descripcion': 'Lateral',
            'fotos-0-orden': '2',
        })

        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.fotos.count(), 1)
        self.assertEqual(self.vehiculo.fotos.first().descripcion, 'Lateral')

    def test_la_edicion_puede_quitar_una_foto(self):
        foto = VehiculoFoto.objects.create(
            vehiculo=self.vehiculo, imagen=imagen('frontal.png'),
            descripcion='Frontal', orden=1)

        self.client.post(reverse('editar_vehiculo', args=[self.vehiculo.pk]), {
            'nombre': self.vehiculo.nombre,
            'codigo_chasis': self.vehiculo.codigo_chasis,
            'marca': str(self.marca.pk),
            'modelo': str(self.modelo.pk),
            'año': '2024',
            'kilometraje': '0',
            'costo_compra': '20000000.00',
            'precio_venta': '28000000.00',
            'descripcion': '',
            'fotos-TOTAL_FORMS': '1',
            'fotos-INITIAL_FORMS': '1',
            'fotos-MIN_NUM_FORMS': '0',
            'fotos-MAX_NUM_FORMS': '1000',
            'fotos-0-id': str(foto.pk),
            'fotos-0-vehiculo': str(self.vehiculo.pk),
            'fotos-0-imagen': '',
            'fotos-0-descripcion': 'Frontal',
            'fotos-0-orden': '1',
            'fotos-0-DELETE': 'on',
        })

        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.fotos.count(), 0)

    # ------------------------------------------------------------------
    # Detalle
    # ------------------------------------------------------------------
    def test_el_detalle_muestra_la_galeria(self):
        VehiculoFoto.objects.create(
            vehiculo=self.vehiculo, imagen=imagen('frontal.png'),
            descripcion='Frontal', orden=1)

        respuesta = self.client.get(reverse('detalle_vehiculo', args=[self.vehiculo.pk]))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn('Galería de fotos', contenido)
        self.assertIn('Frontal', contenido)

    def test_el_detalle_no_rompe_sin_fotos(self):
        respuesta = self.client.get(reverse('detalle_vehiculo', args=[self.vehiculo.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('Galería de fotos', respuesta.content.decode())

    def test_las_fotos_se_ordenan_por_orden(self):
        VehiculoFoto.objects.create(
            vehiculo=self.vehiculo, imagen=imagen('b.png'), descripcion='Segunda', orden=5)
        VehiculoFoto.objects.create(
            vehiculo=self.vehiculo, imagen=imagen('a.png'), descripcion='Primera', orden=1)

        self.assertEqual(
            [f.descripcion for f in self.vehiculo.fotos.all()],
            ['Primera', 'Segunda'],
        )

    def test_al_borrar_el_vehiculo_se_boran_sus_fotos(self):
        VehiculoFoto.objects.create(
            vehiculo=self.vehiculo, imagen=imagen('frontal.png'), orden=1)

        self.vehiculo.delete()

        self.assertEqual(VehiculoFoto.objects.count(), 0)
