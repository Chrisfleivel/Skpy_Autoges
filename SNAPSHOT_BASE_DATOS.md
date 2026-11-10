# Snapshots de la base de datos

Guía para crear y restaurar copias puntuales de la base de datos de desarrollo
(`db.sqlite3`). La base de datos vive en la raíz del proyecto y está ignorada
por git; los snapshots sirven como punto de restauración manual.

> **Convención del proyecto:** `db.sqlite3` (gitignored) es la base de desarrollo
> activa; las migraciones corren directamente sobre ella. `db.sqlite3.bak` SÍ
> está trackeado en git — no lo confundir con los snapshots descriptos acá.

---

## Snapshot actual

| Campo | Valor |
|---|---|
| Archivo | `db_snapshot_20261110_2149.sqlite3` |
| Fecha | 10/11/2026 21:49 (America/Asuncion) |
| Tamaño | 1,9 MB |
| Contenido | 114+ tablas · 213 permisos · 5 roles · 30 empleados dummy · inventario de prueba (25 vehículos, 50 repuestos) · CRUD de Sucursales y Cajas |

### Leyenda de Sucursales y Cajas cargadas

| Sucursal | Cajas | Estado |
|---|---|---|
| Limpio | 3 | activa |
| Mariano Roque Alonso | 2 | activa |
| Matriz | 1 | activa |
| **Total** | **6 cajas en 3 sucursales** | |

> Este es el primer snapshot que incluye el maestro de Sucursales y Cajas
> (modelo `cobranzas.Caja` con el campo `tipo` y la restricción de unicidad
> `sucursal + nombre` de la migración `0003`).

### Historial de snapshots

| Archivo | Fecha | Notas |
|---|---|---|
| `db_snapshot_20261110_2024.sqlite3` | 10/11 20:24 | Estado inicial tras cargas de seguridad (roles, permisos, empleados dummy) |
| `db_snapshot_20261110_2101.sqlite3` | 10/11 21:01 | Tras cargas de inventario (25 vehículos, 50 repuestos, marcas/modelos) |
| `db_snapshot_20261110_2149.sqlite3` | 10/11 21:49 | Actual — con Sucursales y Cajas cargadas |

⚠️ **Los snapshots anteriores incluyen los 30 empleados dummy** que creó
`crear_empleados_dummy` (el comando se ejecutó dos veces y no es idempotente).
Capturan el estado de su momento, no el previo a esas corridas.

---

## Cómo crear un snapshot manualmente

### 1. Detener el servidor (recomendado)

Si `runserver` está corriendo, bajalo con `Ctrl+C` en su terminal antes de
copiar: SQLite no bloquea la copia, pero un pedido en curso podría dejar la
copia en un estado intermedio de transacción.

### 2. Copiar el archivo con marca de tiempo

Desde la raíz del proyecto, en Git Bash:

```sh
cp db.sqlite3 "db_snapshot_$(date +%Y%m%d_%H%M).sqlite3"
```

Genera por ejemplo `db_snapshot_20261110_2024.sqlite3`.

### 3. Verificar el snapshot (opcional pero recomendado)

Abrir la copia con Python y contar tablas / registros clave:

```sh
venv64/Scripts/python -c "import sqlite3; c = sqlite3.connect('db_snapshot_YYYYMMDD_HHMM.sqlite3'); cur = c.cursor(); cur.execute(\"SELECT count(*) FROM sqlite_master WHERE type='table'\"); print('tablas:', cur.fetchone()[0]); c.close()"
```

Si la cantidad de tablas coincide con lo esperado (~114), la copia es legible.

### Alternativa: dump lógico con Django

Para copiar solo *datos* (no el archivo binario), útil si querés importarlos a
otra base:

```sh
venv64/Scripts/python manage.py dumpdata --output dump_YYYYMMDD.json --exclude contenttypes --exclude auth.permission
```

Y para recargarlos en otra base:

```sh
venv64/Scripts/python manage.py loaddata dump_YYYYMMDD.json
```

---

## Cómo restaurar un snapshot

1. **Detener el `runserver`** (`Ctrl+C`, o matar el proceso `python.exe` de
   `venv64` que ocupa el puerto 8000).
2. **(Opcional)** Guardar el estado actual antes de pisarlo, por si hay que volver:

   ```sh
   cp db.sqlite3 "db_pre_restore_$(date +%Y%m%d_%H%M).sqlite3"
   ```

3. **Reemplazar la base activa con el snapshot:**

   ```sh
   cp db_snapshot_20261110_2149.sqlite3 db.sqlite3
   ```

4. Levantar el servidor y verificar:

   ```sh
   venv64/Scripts/python manage.py runserver
   ```

   El admin (`/admin/`) y los datos (roles, permisos, empleados) deberían
   reflejar el estado del snapshot.

---

## Estado en git

Los archivos `db_snapshot_*.sqlite3` **no están ignorados**: aparecen como
sin trackear (`??`) en `git status`. Si no querés que se suban al repo,
agregar a `.gitignore`:

```gitignore
db_snapshot_*.sqlite3
db_pre_restore_*.sqlite3
dump_*.json
```

(No agregar `db.sqlite3.bak` a esa regla: ese archivo SÍ está trackeado.)
