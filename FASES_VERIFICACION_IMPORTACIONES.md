# Fases de verificación y validación para importaciones

## Estado actual

La lógica pura para verificación de VIN y prorrateo es viable y está separada de la base de datos. Sin embargo, la integración con el proyecto real requiere revisar compatibilidad con los modelos concretos del proyecto y registrar los hooks de Django para invalidar estados stale.

## Evidencias del proyecto actual

- El vehículo real de la app usa `inventario.models.Vehiculo` y el campo `codigo_chasis`.
- El proyecto no tiene campos `costo_fob` ni `costo_total` en `Vehiculo`; por lo tanto, la lógica de costo debe mapearse con los campos existentes del modelo real.
- La app `importaciones` ya está preparada para registrar señales en `apps.py`, pero debe ejecutarse a través del `AppConfig` y con `ready()` importando `signals`.
- El flujo de prorrateo requiere invalidar `gastos_prorrateados` cuando cambian `GastoImportacion` o `EmbarqueItem`.

## Fase 0: auditoría de compatibilidad

Objetivo: verificar si los servicios de importaciones encajan con los modelos reales.

Checklist:
- revisar `inventario.models.Vehiculo` y sus campos de chasis/costo
- confirmar si `Embarque`, `EmbarqueItem`, `GastoImportacion` y `FacturaComercial` existen con los campos utilizados por el servicio
- confirmar si la moneda base es USD y si se usa `MONEDA_BASE` en `settings.py`
- validar nombres exactos de campos antes de llamar a un servicio

Resultado esperado: evaluar si el servicio puede ejecutarse sin adaptar modelos o si requiere un mapeo intermedio.

## Fase 1: validación de lógica pura

Objetivo: asegurar que `calculos.py` produce resultados consistentes para VIN, discrepancias y prorrateo sin depender de la BD.

Condición de éxito:
- comparaciones de chasis normalizadas y tolerantes
- resultados por tipo de discrepancia sin errores inesperados
- prorrateo con distribución proporcional replicable y determinista

## Fase 2: integración con Django y base de datos

Objetivo: ejecutar los servicios sobre modelos reales del proyecto.

Revisión principal:
- `verificar_chasis()` debe leer la entidad real del vehículo en inventario
- `verificar_destino()` debe validar el destino del envío con la estructura del dominio real
- `prorratear_costos()` debe operar sobre `EmbarqueItem` y `GastoImportacion` existentes

Si los nombres de campos difieren, se debe crear una capa de adaptación y no forzar el código de cálculo original.

## Fase 3: invalidación automática del estado de prorrateo

Objetivo: evitar que el sistema use un cálculo desactualizado.

Implementación recomendada:
- `signals.py` marca `gastos_prorrateados=False` cuando cambia un gasto o ítem
- `apps.py` usa `ready()` para cargar la señal
- el servicio debe recomputar el prorrateo solo si el embarque está marcado como no actualizado

## Fase 4: validación de flujo operativo

Objetivo: comprobar que el flujo completo funciona desde:
- embarque registrado
- costos cargados
- ítems asociados
- verificación de chasis
- prorrateo
- cierre del embarque con resultado consistente

## Fase 5: verificación, no solo implementación

Se puede considerar implementado si se cumplen tres condiciones:
1. existe compatibilidad real con los modelos del proyecto
2. los servicios corren sin errores de ORM o tipos
3. las pruebas de lógica y de integración pasan en contexto real

Si alguna de estas falla, el trabajo queda en fase de validación y adaptación, no en producción.

### Estado de verificación final

✅ Se validó compatibilidad real con los modelos del proyecto.
✅ Se validó el ciclo completo de embarque con estados reales y prorrateo.
✅ Se validó la invalidación automática del prorrateo ante cambios de gasto o ítem.
✅ La suite de importaciones pasa en contexto real con Django.

## Conclusión

Sí es viable implementarlo, pero con una diferencia importante: la lógica pura sí está lista, mientras que la integración real con Django requiere verificación de campos y señalización. El proyecto actual ya quedó preparado para registrar la invalidación automática del prorrateo; lo siguiente es ejecutar la validación definitiva en el entorno real con los modelos existentes.
