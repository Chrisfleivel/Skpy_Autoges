# Fases de verificación y validación para importaciones

## Estado actual

La lógica pura para verificación de VIN y prorrateo es viable y está separada de la base de datos. Sin embargo, la integración con el proyecto real requiere revisar compatibilidad con los modelos concretos del proyecto y registrar los hooks de Django para invalidar estados stale.

**Cierre a inventario implementado.** El embarque dejó de cerrar "en el papel": `importaciones/cierre.py` calcula el costo landed de cada ítem, lo desglosa por tipo de gasto en el vehículo y ingresa los repuestos al depósito destino con su costo en guaraníes. El inventario multi-depósito (`StockRepuesto`) pasó a ser la fuente de verdad y el stock heredado (`Repuesto.stock_actual`) quedó sembrado por la migración de datos `inventario/0040_sembrar_stock_repuesto.py`.

## Evidencias del proyecto actual

- El vehículo real de la app usa `inventario.models.Vehiculo` y el campo `codigo_chasis`.
- El proyecto no tiene campos `costo_fob` ni `costo_total` en `Vehiculo`; por lo tanto, la lógica de costo debe mapearse con los campos existentes del modelo real.
  - **Actualizado:** `Vehiculo` sí tiene `costo_fob` y `costo_total` (`editable=False`, en USD) y el desglose por tipo de gasto (`costo_flete1`, `costo_aduana_extrangera`, `costo_aduana_paraguaya`, `costo_flete2`, `costo_extra`).
- La app `importaciones` ya está preparada para registrar señales en `apps.py`, pero debe ejecutarse a través del `AppConfig` y con `ready()` importando `signals`.
- El flujo de prorrateo requiere invalidar `gastos_prorrateados` cuando cambian `GastoImportacion` o `EmbarqueItem`.
- El prorrateo respeta el `criterio_prorrateo` de **cada** gasto (`POR_VALOR`, `POR_UNIDAD`, `POR_PESO`), no un único criterio forzado.

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
✅ El cierre a inventario (`importaciones/cierre.py`) funciona sobre los modelos reales: costos del vehículo, stock de repuestos y estado CERRADO del embarque.
✅ `manage.py auditar_stock` da 0 errores sobre el stock migrado (50 repuestos, 1 depósito principal).

## Cierre a inventario (implementado)

| Pieza | Ubicación | Qué hace |
|---|---|---|
| `Embarque.deposito_destino` | `importaciones/models.py` | Depósito donde ingresan los repuestos al cerrar |
| `repartir_gastos_por_tipo()` | `importaciones/calculos.py` | Reparte cada gasto con **su** criterio y devuelve el detalle por tipo |
| `previsualizar_cierre()` | `importaciones/cierre.py` | Calcula FOB + gastos + landed (USD) y el costo unitario en PYG, sin tocar nada |
| `ejecutar_cierre()` | `importaciones/cierre.py` | Escribe los costos del vehículo, ingresa los repuestos y cierra el embarque |
| `MAPEO_COSTOS` | `importaciones/cierre.py` | Gasto → campo de costo: `FLETE`→`costo_flete1`, `ARANCEL`/`DESPACHANTE`→`costo_aduana_paraguaya`, `PUERTO`→`costo_aduana_extrangera`, `TRANSPORTE_INTERNO`→`costo_flete2`, `SEGURO`/`COMISION_BANCARIA`/`OTRO`→`costo_extra` |

Requisitos del cierre (si falta alguno, se explica en pantalla y no se escribe nada):

1. El embarque debe estar en estado `RECIBIDO`.
2. Los gastos deben estar prorrateados y todos los ítems con costo landed.
3. La factura debe estar en USD (moneda base del sistema).
4. Tiene que existir una `TasaCambio` USD→PYG vigente a la fecha de recepción (o se puede informar la del día, que queda registrada).
5. Si hay repuestos, tiene que estar informado el depósito de destino.

## Conclusión

Sí es viable implementarlo, pero con una diferencia importante: la lógica pura sí está lista, mientras que la integración real con Django requiere verificación de campos y señalización. El proyecto actual ya quedó preparado para registrar la invalidación automática del prorrateo; lo siguiente es ejecutar la validación definitiva en el entorno real con los modelos existentes.

**Pendiente para la etapa siguiente (taller):** los repuestos que consume un mantenimiento todavía no descuentan stock; eso usa `inventario.services.registrar_salida()`, que ya está disponible.
