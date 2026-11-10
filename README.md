# Skpy_Autoges

ERP de gestión para concesionaria de vehículos (Paraguay), desarrollado en Django con módulos de inventario, ventas, compras, cobranzas, importaciones y más.

## Requisitos

- Python 3.14 (64 bits)
- Dependencias en `requirements.txt`

## Levantar la aplicación

Desde la raíz del proyecto:

```sh
venv64\Scripts\python manage.py runserver
```

- Aplicación: http://127.0.0.1:8000/
- Administrador de Django: http://127.0.0.1:8000/admin/
- El autoreloader recarga el código automáticamente al guardar cambios.

> **Nota:** usar siempre `venv64\Scripts\python` (es el entorno completo, según `requirements.txt`). El entorno `venv\` solo tiene Django y falla con generación de PDFs y máquinas de estados.

### Primera vez (si no existe el entorno)

```sh
python -m venv venv64
venv64\Scripts\pip install -r requirements.txt
venv64\Scripts\python manage.py migrate
```

## Bajar la aplicación

Presionar `Ctrl+C` en la terminal donde corre el servidor.

Si el puerto 8000 quedó ocupado por un proceso colgado:

```sh
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

## Pruebas

```sh
venv64\Scripts\python manage.py test                            # todas
venv64\Scripts\python manage.py test inventario.test_fase1     # un módulo
```

## Documentación adicional

- `ARQUITECTURA_DIVISAS.md` — arquitectura de divisas y tasas de cambio (USD → PYG)
- `ANALISIS_ROLES_Y_SECTORES.md` — roles, permisos y módulos del sistema
- `MANUAL_USUARIOS_POR_ROLES.md` — manual de uso por rol
- `FASES_VERIFICACION_IMPORTACIONES.md` — estado de integración del módulo de importaciones
