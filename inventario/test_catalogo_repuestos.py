"""
Tests del catálogo de repuestos (Tanda A).

Cubre lo que se agregó al repuesto y el CRUD de categorías con jerarquía:

- `Repuesto`: fabricante, código OEM y modelos compatibles (M2M).
- `CategoriaRepuesto`: categoría superior, nombre único por nivel, control
  de ciclos, CRUD completo y activación/inactivación.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from inventario.models import (
    CategoriaRepuesto,
    MarcaVehiculo,
    ModeloVehiculo,
    Repuesto,
)


class CatalogoRepuestosTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='catalogo_user', password='123456', is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

        self.marca = MarcaVehiculo.objects.create(nombre='Hyundai')
        self.modelo_tucson = ModeloVehiculo.objects.create(
            marca=self.marca, nombre='Tucson')
        self.modelo_santa_fe = ModeloVehiculo.objects.create(
            marca=self.marca, nombre='Santa Fe')

        self.categoria_raiz = CategoriaRepuesto.objects.create(nombre='Motor')
        self.categoria_hija = CategoriaRepuesto.objects.create(
            nombre='Filtros', padre=self.categoria_raiz)

    def _repuesto(self, **campos):
        datos = dict(
            nombre='Filtro de aceite',
            codigo_repuesto='OEM-001',
            costo_compra=Decimal('50000.00'),
        )
        datos.update(campos)
        return Repuesto.objects.create(**datos)

    # ------------------------------------------------------------------
    # Repuesto: fabricante, código OEM y modelos compatibles
    # ------------------------------------------------------------------
    def test_el_repuesto_guarda_fabricante_y_codigo_oem(self):
        repuesto = self._repuesto(fabricante='Hyundai', codigo_oem='27110-2F000')

        repuesto.refresh_from_db()

        self.assertEqual(repuesto.fabricante, 'Hyundai')
        self.assertEqual(repuesto.codigo_oem, '27110-2F000')

    def test_los_modelos_compatibles_se_asignan(self):
        repuesto = self._repuesto()
        repuesto.modelos_compatibles.set([self.modelo_tucson, self.modelo_santa_fe])

        repuesto.refresh_from_db()

        self.assertEqual(repuesto.modelos_compatibles.count(), 2)
        # El acceso inverso también funciona.
        self.assertEqual(list(self.modelo_tucson.repuestos_compatibles.all()), [repuesto])

    def test_el_m2m_arranca_vacio(self):
        repuesto = self._repuesto()

        self.assertEqual(repuesto.modelos_compatibles.count(), 0)

    def test_el_formulario_acepta_los_campos_nuevos(self):
        """Se envían solo los campos que la pantalla muestra."""
        respuesta = self.client.post(reverse('agregar_repuesto'), {
            'nombre': 'Filtro de aire',
            'codigo_repuesto': 'OEM-002',
            'categoria': str(self.categoria_raiz.pk),
            'stock_actual': '5',
            'stock_minimo': '2',
            'precio_venta': '120000.00',
            'costo_compra': '75000.00',
            'compatibilidad': '',
            'descripcion': '',
            'fabricante': 'Hyundai',
            'codigo_oem': '28113-2S000',
            'modelos_compatibles': [str(self.modelo_tucson.pk)],
        })

        self.assertEqual(respuesta.status_code, 302)
        repuesto = Repuesto.objects.get(codigo_repuesto='OEM-002')
        self.assertEqual(repuesto.fabricante, 'Hyundai')
        self.assertEqual(repuesto.codigo_oem, '28113-2S000')
        self.assertEqual(list(repuesto.modelos_compatibles.all()), [self.modelo_tucson])

    def test_el_alta_de_repuesto_no_exige_campos_que_no_se_muestran(self):
        """Regression: el formulario no debe pedir campos invisibles."""
        from inventario.forms import RepuestoForm

        form = RepuestoForm(data={
            'nombre': 'Filtro de aire',
            'codigo_repuesto': 'OEM-003',
            'costo_compra': '75000.00',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_editar_un_repuesto_no_pisa_el_stock_reservado(self):
        """`stock_reservado` es el espejo de StockRepuesto: no se edita a mano."""
        repuesto = self._repuesto(stock_actual=8, stock_reservado=3)

        respuesta = self.client.post(
            reverse('editar_repuesto', args=[repuesto.pk]), {
                'nombre': repuesto.nombre,
                'codigo_repuesto': repuesto.codigo_repuesto,
                'stock_actual': '9',
                'stock_minimo': '0',
                'precio_venta': '0',
                'costo_compra': '50000.00',
                'compatibilidad': '',
                'descripcion': '',
            })

        self.assertEqual(respuesta.status_code, 302)
        repuesto.refresh_from_db()
        self.assertEqual(repuesto.stock_actual, 9)
        self.assertEqual(repuesto.stock_reservado, 3)

    def test_el_detalle_muestra_los_modelos_compatibles(self):
        repuesto = self._repuesto(fabricante='Hyundai', codigo_oem='27110-2F000')
        repuesto.modelos_compatibles.add(self.modelo_tucson)

        respuesta = self.client.get(reverse('detalle_repuesto', args=[repuesto.pk]))
        contenido = respuesta.content.decode()

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('Hyundai', contenido)
        self.assertIn('27110-2F000', contenido)
        self.assertIn('Tucson', contenido)

    # ------------------------------------------------------------------
    # Categorías: jerarquía
    # ------------------------------------------------------------------
    def test_la_categoria_admite_una_categoria_superior(self):
        self.assertEqual(self.categoria_hija.padre, self.categoria_raiz)
        self.assertEqual(self.categoria_hija.ruta_completa, 'Motor › Filtros')
        self.assertEqual(self.categoria_raiz.ruta_completa, 'Motor')

    def test_no_se_puede_repetir_nombre_en_el_mismo_nivel(self):
        duplicado = CategoriaRepuesto(nombre='Filtros', padre=self.categoria_raiz)

        with self.assertRaises(ValidationError):
            duplicado.full_clean()

        # La base de datos también lo rechaza.
        with self.assertRaises(IntegrityError), transaction.atomic():
            CategoriaRepuesto.objects.create(nombre='Filtros', padre=self.categoria_raiz)

    def test_dos_RAICES_no_pueden_repetir_nombre(self):
        duplicado = CategoriaRepuesto(nombre='Motor')

        with self.assertRaises(ValidationError):
            duplicado.full_clean()

        with self.assertRaises(IntegrityError), transaction.atomic():
            CategoriaRepuesto.objects.create(nombre='Motor')

    def test_se_puede_repetir_nombre_en_niveles_distintos(self):
        """Una subcategoría puede llamarse igual que otra de otra rama."""
        otra_raiz = CategoriaRepuesto.objects.create(nombre='Frenos')
        categoria = CategoriaRepuesto(nombre='Filtros', padre=otra_raiz)

        categoria.full_clean()  # no debe lanzar
        categoria.save()

        self.assertEqual(CategoriaRepuesto.objects.filter(nombre='Filtros').count(), 2)

    def test_no_se_puede_colgar_de_un_descendiente(self):
        """Un ciclo (raíz → hija → raíz) está prohibido."""
        self.categoria_raiz.padre = self.categoria_hija

        with self.assertRaises(ValidationError):
            self.categoria_raiz.full_clean()

    def test_no_se_puede_ser_propia_categoria_superior(self):
        categoria = CategoriaRepuesto.objects.create(nombre='Frenos')
        categoria.padre = categoria

        with self.assertRaises(ValidationError):
            categoria.full_clean()

    def test_el_formulario_no_ofrece_descendientes_como_padre(self):
        """Al editar, la categoría no puede colgar de una de sus descendientes."""
        nietos = CategoriaRepuesto.objects.create(nombre='Aceites', padre=self.categoria_hija)

        from inventario.forms import CategoriaRepuestoForm
        form = CategoriaRepuestoForm(instance=self.categoria_raiz)

        disponibles = list(form.fields['padre'].queryset)
        self.assertNotIn(self.categoria_raiz, disponibles)
        self.assertNotIn(self.categoria_hija, disponibles)
        self.assertNotIn(nietos, disponibles)

    # ------------------------------------------------------------------
    # Categorías: CRUD
    # ------------------------------------------------------------------
    def test_la_vista_crea_una_categoria(self):
        respuesta = self.client.post(reverse('agregar_categoria_repuesto'), {
            'nombre': 'Transmisión',
            'descripcion': 'Cajas y diferenciales',
            'padre': '',
            'estado': 'on',
        })

        self.assertEqual(respuesta.status_code, 302)
        categoria = CategoriaRepuesto.objects.get(nombre='Transmisión')
        self.assertIsNone(categoria.padre)
        self.assertTrue(categoria.estado)

    def test_la_vista_crea_una_subcategoria(self):
        respuesta = self.client.post(reverse('agregar_categoria_repuesto'), {
            'nombre': 'Cajas',
            'descripcion': '',
            'padre': str(self.categoria_raiz.pk),
            'estado': 'on',
        })

        self.assertEqual(respuesta.status_code, 302)
        categoria = CategoriaRepuesto.objects.get(nombre='Cajas')
        self.assertEqual(categoria.padre, self.categoria_raiz)

    def test_la_vista_rechaza_un_nombre_repetido_en_el_mismo_nivel(self):
        respuesta = self.client.post(reverse('agregar_categoria_repuesto'), {
            'nombre': 'Filtros',
            'descripcion': '',
            'padre': str(self.categoria_raiz.pk),
            'estado': 'on',
        })

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(CategoriaRepuesto.objects.filter(nombre='Filtros').count(), 1)

    def test_la_vista_rechaza_un_ciclo(self):
        respuesta = self.client.post(
            reverse('editar_categoria_repuesto', args=[self.categoria_raiz.pk]),
            {
                'nombre': 'Motor',
                'descripcion': '',
                'padre': str(self.categoria_hija.pk),
                'estado': 'on',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.categoria_raiz.refresh_from_db()
        self.assertIsNone(self.categoria_raiz.padre)

    def test_el_listado_filtra_por_categoria_superior(self):
        respuesta = self.client.get(reverse('lista_categorias_repuestos'), {
            'padre': str(self.categoria_raiz.pk),
        })

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn('Filtros', contenido)
        self.assertNotIn('>Motor<', contenido)

    def test_el_listado_filtra_por_busqueda(self):
        respuesta = self.client.get(reverse('lista_categorias_repuestos'), {
            'search_query': 'Filtros',
        })

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('Filtros', respuesta.content.decode())

    def test_el_toggle_activa_e_inactiva(self):
        url = reverse('cambiar_estado_categoria_repuesto', args=[self.categoria_hija.pk])

        self.client.post(url)
        self.categoria_hija.refresh_from_db()
        self.assertFalse(self.categoria_hija.estado)

        self.client.post(url)
        self.categoria_hija.refresh_from_db()
        self.assertTrue(self.categoria_hija.estado)

    def test_una_categoria_con_repuestos_no_se_elimina(self):
        self._repuesto(categoria=self.categoria_raiz)

        respuesta = self.client.post(
            reverse('eliminar_categoria_repuesto', args=[self.categoria_raiz.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(CategoriaRepuesto.objects.filter(pk=self.categoria_raiz.pk).exists())

    def test_una_categoria_con_subcategorias_no_se_elimina(self):
        respuesta = self.client.post(
            reverse('eliminar_categoria_repuesto', args=[self.categoria_raiz.pk]))

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(CategoriaRepuesto.objects.filter(pk=self.categoria_raiz.pk).exists())

    def test_una_categoria_sin_uso_se_elimina(self):
        categoria = CategoriaRepuesto.objects.create(nombre='Temporal')

        self.client.post(reverse('eliminar_categoria_repuesto', args=[categoria.pk]))

        self.assertFalse(CategoriaRepuesto.objects.filter(pk=categoria.pk).exists())

    def test_el_detalle_muestra_las_subcategorias(self):
        respuesta = self.client.get(
            reverse('detalle_categoria_repuesto', args=[self.categoria_raiz.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('Filtros', respuesta.content.decode())

    def test_el_navbar_tiene_la_entrada_de_categorias(self):
        respuesta = self.client.get(reverse('lista_categorias_repuestos'))

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn(reverse('lista_categorias_repuestos'), contenido)
        self.assertIn('Categor', contenido)
