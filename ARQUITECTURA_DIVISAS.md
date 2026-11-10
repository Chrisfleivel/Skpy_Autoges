# 🏦 SKPY AutoGest - Sistema de Gestión de Divisas

## Resumen Ejecutivo

Se ha implementado una **arquitectura completa de trazabilidad financiera** para SKPY AutoGest que garantiza:

✅ **Integridad de datos** - Cada transacción en USD registra la tasa aplicada
✅ **Auditoría completa** - Quién, cuándo y a qué tasa se registró cada compra  
✅ **Flexibilidad** - Soporte para múltiples divisas (USD, KRW, etc. → PYG)
✅ **Cumplimiento DNIT** - Histórico sin modificaciones para auditorías

---

## 📊 Arquitectura Implementada

### Capas del Sistema

```
┌─────────────────────────────────────┐
│   INTERFAZ DE USUARIO               │
│  (Formularios con cálculo en tiempo │
│   real de USD → Gs)                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   CAPA DE NEGOCIO (Views/Forms)     │
│  - Validar tasa diaria              │
│  - Calcular costo en guaraníes      │
│  - Capturar usuario y auditoría     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   MODELOS DE DATOS                  │
│  ┌─ TasaCambio (histórico)          │
│  ├─ Vehiculo (costo_usd + tasa)     │
│  └─ Repuesto (costo_usd + tasa)     │
│                                      │
│  Métodos helper:                     │
│  - obtener_tasa_actual()             │
│  - existe_tasa_para_hoy()            │
│  - costo_calculado_guaranies()       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   BASE DE DATOS (SQLite/PostgreSQL) │
└─────────────────────────────────────┘
```

### Flujo de Carga de Vehículo/Repuesto

```
1. Usuario entra a "Agregar Vehículo"
   ↓
2. Sistema valida: ¿Existe tasa del día?
   ├─ NO → Redirigir a "Cargar Tasa de Cambio"
   └─ SI → Continuar
   ↓
3. Formulario muestra:
   - Campo "Costo (USD)"
   - Selector de "Tasa de Cambio" (preselecciona actual)
   - Previsualización de costo en Gs (JavaScript)
   ↓
4. Usuario ingresa:
   - Costo en USD (ej. 25,000)
   - Selecciona tasa (ej. 6,850.50)
   ↓
5. Sistema calcula:
   - costo_usd = 25000
   - tasa_aplicada = 6850.50
   - costo_compra = 25000 × 6850.50 = 171,262,500 Gs
   - tasa_cambio_id = FK a registro de TasaCambio
   ↓
6. Guardar en BD:
   - Registro de Vehículo con todos los campos USD + Gs
   - Referencia histórica a TasaCambio del día
   - Auditoría completada (usuario, fecha, tasa)
```

---

## 📁 Archivos Modificados (Fase 1)

### Modelos
- `configuraciones_maestras/models.py` - TasaCambio mejorado
- `inventario/models.py` - Vehiculo y Repuesto con USD

### Formularios
- `configuraciones_maestras/forms.py` - TasaCambioForm con fecha

### Vistas
- `configuraciones_maestras/views.py` - Agregar/Listar tasas con auditoría

### Plantillas
- `templates/configuraciones_maestras/lista_tasas_cambio.html` - Resumen diario
- `templates/configuraciones_maestras/agregar_tasa_cambio.html` - Previsualización
- `templates/configuraciones_maestras/detalle_tasa_cambio.html` - Auditoría

### Migraciones
- `configuraciones_maestras/migrations/0010_*` - Estructura TasaCambio
- `inventario/migrations/0015_*` - Campos USD en Vehiculo/Repuesto

---

## 🔍 Consultas Útiles en la BD

### Obtener tasa vigente
```python
from configuraciones_maestras.models import TasaCambio
tasa_hoy = TasaCambio.obtener_tasa_actual()
```

### Ver histórico de vehículos con USD
```python
from inventario.models import Vehiculo
vehiculos_usd = Vehiculo.objects.filter(costo_usd__isnull=False).select_related('tasa_cambio')
```

### Auditar cambios de tasas
```python
from django.contrib.auth.models import User
from configuraciones_maestras.models import TasaCambio

# Quién cargó cada tasa
for tasa in TasaCambio.objects.all():
    print(f"{tasa.fecha}: {tasa.valor} Gs (por {tasa.usuario_creo})")
```

### Verificar integridad (si existe tasa para cada vehículo USD)
```python
sin_tasa = Vehiculo.objects.filter(costo_usd__isnull=False, tasa_cambio__isnull=True)
print(f"Vehículos USD sin tasa registrada: {sin_tasa.count()}")
```

---

## ⚠️ Consideraciones de Auditoría (DNIT)

### Validación ante auditoría:
1. **No modificar tasas históricas** - Usar asientos de ajuste
2. **Mantener separación USD/PYG** - Ambos campos en BD
3. **Trazabilidad de usuario** - `usuario_creo` en cada tasa
4. **Justificación de cambios** - Logs en tabla `AsientoAjuste` (implementar en Fase 2)

### Ejemplo de pregunta DNIT:
> "¿Cuál fue la tasa de cambio aplicada al vehículo importado el 15/03/2026?"

**Respuesta:**
```python
vehiculo = Vehiculo.objects.get(id=123)
print(f"Tasa aplicada: {vehiculo.tasa_aplicada}")  # 6850.50
print(f"Tasa histórica: {vehiculo.tasa_cambio.fecha}")  # 2026-03-15
print(f"Costo calculado: {vehiculo.costo_calculado_guaranies} Gs")  # 171,262,500
```

---

## 📌 Próximas Fases

### Fase 2 (Recomendado hacer siguiente)
- Formularios USD para agregar Vehículos y Repuestos
- Validación: rechazar cargas sin tasa del día
- Dashboard con tarjeta de tasa vigente

Ver: `GUIA_DIVISAS_FASE_2.md`

### Fase 3 (Futuro)
- API de tasas automáticas (Banco Central del Paraguay)
- Modelo `AsientoAjuste` para cambios históricos
- Reportes de análisis de tasas y márgenes

### Fase 4 (Opcional)
- Conversión a otras divisas (EUR, CNY, etc.)
- Cálculo de Costo Landed (USD + flete + despacho)

---

## 🚀 Cómo Usar en Desarrollo

### Cargar una tasa diaria
1. Ir a `Configuraciones → Tasas de Cambio`
2. Click en "Cargar Tasa de Hoy"
3. Ingresar:
   - Moneda Origen: USD
   - Moneda Destino: PYG
   - Tasa: 6850.50 (valor actual)
   - Fecha: 2026-06-10
4. Guardar

### Verificar en consola de Django
```bash
python manage.py shell
```

```python
from configuraciones_maestras.models import TasaCambio
print(TasaCambio.obtener_tasa_actual())
# Output: 1 USD = 6850.5000 PYG (al 2026-06-10)
```

---

## 📚 Documentación Adicional

- **Modelos:** Ver docstrings en `models.py`
- **Formularios:** Ver `forms.py` con validaciones personalizadas
- **Vistas:** Ver métodos helper en `views.py`
- **Templates:** Plantillas responsivas con Bootstrap 5

---

## ✨ Características Destacadas

### 1. Cálculo Automático
```python
@property
def costo_calculado_guaranies(self):
    if self.costo_usd and self.tasa_aplicada:
        return self.costo_usd * self.tasa_aplicada
    return self.costo_compra
```

### 2. Validación de Fecha Única por Tasa
```python
class Meta:
    unique_together = [['moneda_origen', 'moneda_destino', 'fecha']]
```

### 3. Previsualización en Tiempo Real
```javascript
function actualizarPreview() {
  const tasa = parseFloat(inputTasa.value) || 0;
  document.getElementById('preview-resultado').textContent = 
    (100 * tasa).toLocaleString('es-PY');
}
```

---

**Versión:** 1.0  
**Última actualización:** 10/06/2026  
**Estado:** ✅ Fase 1 Completada - Listo para Fase 2
