# AGENTS.md

SKPY AutoGest: ERP Django 6.0 (Monolithic, not a monorepo) for an auto dealership in Paraguay. Project package: `skpy_autogest_project/`; each business module is a Django app at the repo root.

## Environment

- **Two venvs exist; they are not interchangeable.** `venv/` has only Django+pillow. `venv64/` is the complete one (`django-fsm`, `xhtml2pdf`, `numpy`) and matches `requirements.txt`. `.vscode/settings.json` points at `venv64`.
- Run everything with `venv64\Scripts\python manage.py <cmd>` from the repo root. Scripts that touch PDFs (clientes_pedidos, cobranzas, seguridad_usuarios) or state machines fail under `venv/`.
- **Language convention: everything in Spanish** — code comments, model fields, UI strings, docs. `LANGUAGE_CODE='es-py'`, `TIME_ZONE='America/Asuncion'`. Match this in new code.
- `db.sqlite3` (gitignored) is the live dev database; migrations run against it directly. `db.sqlite3.bak` IS tracked in git — don't edit it casually. There is no separate test database config; Django's test runner creates its own.
- `settings.py` contains a hardcoded Gmail app password. Don't copy this pattern or commit additional secrets.

## Commands

```sh
venv64\Scripts\python manage.py runserver       # levanta: http://127.0.0.1:8000/ (admin en /admin/)
venv64\Scripts\python manage.py test                          # all tests
venv64\Scripts\python manage.py test inventario.test_fase1    # single test module
venv64\Scripts\python manage.py makemigrations && venv64\Scripts\python manage.py migrate
venv64\Scripts\python scripts\prueba_factura_compra.py        # scripts call django.setup() themselves and write directly to the dev DB
```

Tests follow a per-phase convention: standalone modules like `inventario/test_fase1.py` … `test_fase5.py` (they match Django's `test*.py` discovery pattern).

**Levantar / bajar el aplicativo:** `runserver` corre en primer plano con autoreloader (`StatReloader`) — se baja con `Ctrl+C` en su terminal. No hay servicio ni daemon: si quedó colgado, matá el proceso `python.exe` de `venv64` (o liberá el puerto 8000 con `netstat -ano | findstr :8000` + `taskkill /PID <pid> /F`) antes de reintentar, o dará `port already in use`.

## Architecture & domain constraints

- **Currency architecture is the core rule** (see `ARQUITECTURA_DIVISAS.md`): `settings.MONEDA_BASE = 'USD'`. USD costs on `Vehiculo`/`Repuesto` must be stored with the applied `TasaCambio` (daily exchange rate from `configuraciones_maestras`) plus audit fields (who/when/rate). Never mutate historical rates — needed for DNIT (Paraguayan tax authority) audits. Convert to PYG at capture time, not at read time.
- **State machines:** `Pedido.estado` in `clientes_pedidos` uses `django-fsm` transitions. Change order status through its transition methods, not by assigning `.estado` directly.
- **System checks must never write to the database.** Django evaluates callable `choices` during `manage.py check` (which runs in `runserver`, `test`, `migrate` and `makemigrations`). `Moneda.get_choices()` is therefore **read-only**: it only lists rows. Seeding lives in `Moneda.ensure_defaults()` and in the data migration `configuraciones_maestras/0023_seed_monedas_iniciales.py`. Don't reintroduce writes into a `choices` callable.
- **Disabled apps** (commented out in `INSTALLED_APPS`): `contabilidad`, `documentos_financieros`, `reportes`, `catalogo` (which also has `MIGRATION_MODULES = {'catalogo': None}`). Their code exists; don't re-enable them without intent. Their test modules (`contabilidad/tests.py`, `documentos_financieros/tests.py`) raise `unittest.SkipTest` when the app is missing, so they report as *skipped* instead of failing the suite.
- **Stock lives in `StockRepuesto`** (one row per repuesto + depósito). `inventario/services.py` works on that model; the `Repuesto.stock_actual` / `stock_reservado` fields are kept as a **mirror** of `StockRepuesto` (updated by `sincronizar_espejo()` inside the same transaction), because `clientes_pedidos` still reads them. Movement amounts are always **positive**: direction is carried by `deposito_destino` (entrada) and `deposito_origen` (salida), which is what the `movimiento_signo_coherente_con_tipo` check constraint allows.
- **Stock movements:** write them through `inventario/services.py` (`registrar_entrada`, `registrar_salida`, `confirmar_venta`, `transferir`, `ajustar_stock`, `reservar_unidades`, `liberar_unidades`), never with `MovimientoStock.objects.create()` from app code — the services keep `StockRepuesto` and the ledger in sync. `MovimientoStock` is immutable: `save()` on an existing row and `delete()` both raise `ValidationError` (so test data has to be cleaned with raw SQL).
- **Stock audit:** `manage.py auditar_stock` checks the ledger against the physical stock (direction per type, complete transfer pairs by `grupo`, `saldo_posterior` vs physical, legacy `stock_actual` without `StockRepuesto`). Exit code 1 means errors; `--strict` also fails on warnings. The logic lives in `inventario/auditoria.py` so it can be reused and tested.
- **Import close to inventory** (`importaciones/cierre.py`): `previsualizar_cierre()` computes the landed cost per item (USD) and its PYG equivalent without touching anything; `ejecutar_cierre()` writes the vehicle's cost breakdown (per `MAPEO_COSTOS`), enters repuestos into `Embarque.deposito_destino` and closes the shipment. Requires a prorrateo, a USD invoice and a `TasaCambio` for the closing date; the rate is stored on the product (`tasa_aplicada` + `tasa_cambio`) for the DNIT audit.
- **Taller (mantenimientos):** lives in `inventario`, not in a separate app. `MantenimientoVehiculo` uses `EstadoMixin` with a single `estado` field (`pendiente` → `en_proceso` → `finalizado`, plus `cancelado`); change it with `cambiar_estado()`, never by assignment. Repuestos are in `MantenimientoRepuesto` (with `cantidad` and a `costo_unitario` snapshot) and discount stock when the maintenance is finalized (`registrar_salida()`), guarded by `stock_descontado`. `costo` is computed (`costo_mano_obra` + `costo_repuestos`); a maintenance whose stock was already discounted cannot be deleted.
- `importaciones/` services are documented as not fully integrated with real models yet — see `FASES_VERIFICACION_IMPORTACIONES.md` for the compatibility audit checklist before extending them.
- URLs are wired per-app in `skpy_autogest_project/urls.py` with the same app-name prefix; global templates live in root `templates/`, not app dirs.

## Docs caveat

Root `.md` files (`ARQUITECTURA_DIVISAS.md`, `GUIA_DIVISAS_FASE_2.md`, `ANALISIS_ROLES_Y_SECTORES.md`, `MANUAL_USUARIOS_POR_ROLES.md`, `FASES_VERIFICACION_IMPORTACIONES.md`) mix implementation records with plans. Verify against code before trusting a claim; `settings.py`'s docstring still says Django 5.2 but the project runs Django 6.0.
