# SKPY AutoGest - Sistema de Divisas y Tasas de Cambio
## Guía de Implementación - Fase 2

---

## 📋 Estado Actual (Fase 1 - Completada)

✅ Modelos mejorados con trazabilidad de divisas
✅ Sistema de tasas de cambio diarias con auditoría  
✅ Campos USD en Vehículos y Repuestos
✅ Interfaz mejorada para gestión de tasas

---

## 🚀 Fase 2: Integración con Formularios de Vehículos y Repuestos

### Paso 1: Crear Formularios con Soporte a USD

**Archivo:** `inventario/forms.py`

```python
from django import forms
from .models import Vehiculo, Repuesto
from configuraciones_maestras.models import TasaCambio

class VehiculoFormUSD(forms.ModelForm):
    """Formulario para agregar vehículos con costo en USD"""
    class Meta:
        model = Vehiculo
        fields = [
            'nombre', 'marca', 'modelo', 'año', 'color',
            'codigo_chasis', 'transmision', 'combustible',
            'kilometraje', 'costo_usd', 'tasa_cambio', 'precio_venta',
            'precio_cif_usd', 'estado', 'ubicacion'
        ]
        widgets = {
            'costo_usd': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 25000.00',
                'step': '0.01',
                'id': 'costo-usd'
            }),
            'tasa_cambio': forms.Select(attrs={'class': 'form-control', 'id': 'tasa-selector'}),
            # ... otros widgets
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo tasas USD → PYG
        self.fields['tasa_cambio'].queryset = TasaCambio.objects.filter(
            moneda_origen='USD',
            moneda_destino='PYG'
        ).order_by('-fecha')
        
        # Preseleccionar tasa actual
        tasa_actual = TasaCambio.obtener_tasa_actual()
        if tasa_actual:
            self.fields['tasa_cambio'].initial = tasa_actual
```

### Paso 2: Actualizar Vista de Agregar Vehículo

**Archivo:** `inventario/views.py`

```python
from configuraciones_maestras.models import TasaCambio
from django.contrib import messages

@revisar_permiso('inventario.agregar_vehiculo')
def agregar_vehiculo(request):
    # Validar que exista tasa de cambio
    tasa_actual = TasaCambio.obtener_tasa_actual()
    if not tasa_actual:
        messages.warning(
            request, 
            'No hay tasa de cambio registrada. Por favor, carga la tasa del día.'
        )
        return redirect('agregar_tasa_cambio')
    
    if request.method == 'POST':
        form = VehiculoFormUSD(request.POST, request.FILES)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            # Asegurar que se usa tasa vigente
            if vehiculo.costo_usd and not vehiculo.tasa_cambio:
                vehiculo.tasa_cambio = tasa_actual
                vehiculo.tasa_aplicada = tasa_actual.valor
            vehiculo.save()
            messages.success(request, f'Vehículo {vehiculo.nombre} agregado correctamente.')
            return redirect('lista_vehiculos')
    else:
        form = VehiculoFormUSD(initial={'tasa_cambio': tasa_actual})
    
    return render(request, 'inventario/agregar_vehiculo.html', {
        'form': form,
        'tasa_actual': tasa_actual
    })
```

### Paso 3: Actualizar Plantilla de Agregar Vehículo

**Archivo:** `templates/inventario/agregar_vehiculo.html`

Agregar este código donde va el campo `costo_usd`:

```html
<div class="row g-3">
  <!-- Costo en USD -->
  <div class="col-md-6">
    <label class="form-label fw-semibold" for="{{ form.costo_usd.id_for_label }}">Costo (USD)</label>
    {{ form.costo_usd }}
    {% if form.costo_usd.errors %}
      <div class="text-danger small mt-1">{{ form.costo_usd.errors }}</div>
    {% endif %}
    <small class="text-muted d-block mt-1">Precio CIF o valor de compra en dólares</small>
  </div>

  <!-- Selector de Tasa -->
  <div class="col-md-6">
    <label class="form-label fw-semibold" for="{{ form.tasa_cambio.id_for_label }}">Tasa de Cambio</label>
    {{ form.tasa_cambio }}
    {% if form.tasa_cambio.errors %}
      <div class="text-danger small mt-1">{{ form.tasa_cambio.errors }}</div>
    {% endif %}
    <small class="text-muted d-block mt-1">
      {% if tasa_actual %}
        Vigente: 1 USD = {{ tasa_actual.valor|floatformat:4 }} Gs
      {% endif %}
    </small>
  </div>

  <!-- Previsualización de Costo en Guaraníes -->
  <div class="col-md-6">
    <label class="form-label fw-semibold">Costo (Guaraníes)</label>
    <input type="text" id="costo-guaranies-preview" class="form-control" readonly placeholder="Se calcula automáticamente">
    <small class="text-muted d-block mt-1">Cálculo: USD × Tasa = Guaraníes</small>
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const costoUsdInput = document.getElementById('costo-usd');
  const tasaSelector = document.getElementById('tasa-selector');
  const previewInput = document.getElementById('costo-guaranies-preview');

  function actualizarPreview() {
    const costoUsd = parseFloat(costoUsdInput.value) || 0;
    const tasaOption = tasaSelector.options[tasaSelector.selectedIndex];
    const tasaTexto = tasaOption.text;
    
    // Extraer valor de tasa del texto (ej: "1 USD = 6850.5000 PYG")
    const match = tasaTexto.match(/= ([\d.]+)/);
    const tasa = match ? parseFloat(match[1]) : 0;
    
    const costoGuaranies = costoUsd * tasa;
    previewInput.value = costoGuaranies.toLocaleString('es-PY', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }) + ' Gs';
  }

  costoUsdInput.addEventListener('input', actualizarPreview);
  tasaSelector.addEventListener('change', actualizarPreview);
  actualizarPreview();
});
</script>
```

### Paso 4: Aplicar Cambios Similares a Repuestos

Repetir los pasos 1-3 para:
- `RepuestoFormUSD` en `inventario/forms.py`
- `agregar_repuesto()` en `inventario/views.py`
- `templates/inventario/agregar_repuesto.html`

---

## 🎯 Paso 5: Dashboard - Tarjeta de Tasa Actual

**Archivo:** `configuraciones_maestras/views.py`

Actualizar la vista `home_maestras` (o la principal):

```python
def home_maestras(request):
    tasa_actual = TasaCambio.obtener_tasa_actual()
    existe_tasa_hoy = TasaCambio.existe_tasa_para_hoy()
    
    return render(request, 'configuraciones_maestras/home_maestras.html', {
        'tasa_actual': tasa_actual,
        'existe_tasa_hoy': existe_tasa_hoy
    })
```

**Archivo:** `templates/configuraciones_maestras/home_maestras.html` (o `templates/home.html`)

Agregar esta tarjeta en el dashboard:

```html
<div class="row mb-4">
  <div class="col-md-6 col-lg-3">
    <div class="card border-0 shadow-sm {% if not existe_tasa_hoy %}border-warning{% endif %}">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <small class="text-muted">Tasa de Cambio (USD → Gs)</small>
            {% if tasa_actual %}
              <h5 class="fw-bold mt-2">{{ tasa_actual.valor|floatformat:4 }} Gs</h5>
              <small class="text-success">Valida: {{ tasa_actual.fecha|date:'d/m/Y' }}</small>
            {% else %}
              <h5 class="fw-bold mt-2 text-danger">Sin registrar</h5>
            {% endif %}
          </div>
          <i class="bi bi-currency-exchange text-primary" style="font-size: 2rem;"></i>
        </div>
        {% if not existe_tasa_hoy and tasa_actual %}
        <div class="alert alert-warning mt-3 mb-0 small">
          ⚠️ Tasa desactualizada. <a href="{% url 'agregar_tasa_cambio' %}">Cargar tasa de hoy</a>
        </div>
        {% endif %}
      </div>
    </div>
  </div>
</div>
```

---

## 🔐 Validación de Integridad

### Checklist antes de usar en producción:

- [ ] Todas las tasas históricas tienen `usuario_creo` (ejecutar SQL update si es necesario)
- [ ] Los vehículos/repuestos cargados sin USD están correctamente marcados
- [ ] El sistema rechaza cargas sin tasa del día
- [ ] Las conversiones USD → PYG son consistentes en reportes
- [ ] Backup de base de datos antes de agregar tasas antiguas

### Ejemplo de SQL para auditar tasas sin usuario:

```sql
SELECT * FROM configuraciones_maestras_tasacambio WHERE usuario_creo_id IS NULL;
```

---

## 📝 Auditoría de Cambios Históricos

Para cambios posteriores (ajustes de costo), NO BORRES registros. Crea un modelo `AsientoAjuste`:

```python
class AsientoAjuste(models.Model):
    """Registro de ajustes contables sin borrar histórico"""
    tipo_cambio = models.CharField(max_length=20, choices=[
        ('vehiculo', 'Vehículo'),
        ('repuesto', 'Repuesto')
    ])
    objeto_id = models.PositiveIntegerField()
    razon = models.TextField()
    valor_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    valor_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
```

---

## ✅ Próximos Pasos

1. Implementar formularios USD para vehículos y repuestos
2. Crear validación en vistas (rechazar sin tasa)
3. Agregar tarjeta de tasa en dashboard
4. Realizar pruebas de cálculo de conversión
5. Documentar proceso en manual de usuario

---

**Última actualización:** 10/06/2026
**Responsable:** Sistema de Divisas v1.0
