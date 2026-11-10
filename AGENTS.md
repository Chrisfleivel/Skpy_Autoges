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
- **Disabled apps** (commented out in `INSTALLED_APPS`): `contabilidad`, `documentos_financieros`, `reportes`, `catalogo` (which also has `MIGRATION_MODULES = {'catalogo': None}`). Their code exists; don't re-enable them without intent.
- `importaciones/` services are documented as not fully integrated with real models yet — see `FASES_VERIFICACION_IMPORTACIONES.md` for the compatibility audit checklist before extending them.
- URLs are wired per-app in `skpy_autogest_project/urls.py` with the same app-name prefix; global templates live in root `templates/`, not app dirs.

## Docs caveat

Root `.md` files (`ARQUITECTURA_DIVISAS.md`, `GUIA_DIVISAS_FASE_2.md`, `ANALISIS_ROLES_Y_SECTORES.md`, `MANUAL_USUARIOS_POR_ROLES.md`, `FASES_VERIFICACION_IMPORTACIONES.md`) mix implementation records with plans. Verify against code before trusting a claim; `settings.py`'s docstring still says Django 5.2 but the project runs Django 6.0.
