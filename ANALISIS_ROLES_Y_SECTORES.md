# SKPY AutoGest - Análisis de Roles, Permisos y Sectores del Sistema

## Índice
1. [Módulos/Sectores del Sistema](#módulossectores-del-sistema)
2. [Roles Principales](#roles-principales)
3. [Matriz de Responsabilidades](#matriz-de-responsabilidades)
4. [Permisos por Rol](#permisos-por-rol)
5. [Flujos de Trabajo por Rol](#flujos-de-trabajo-por-rol)

---

## 🏗️ Módulos/Sectores del Sistema

SKPY AutoGest está compuesto por **7 módulos principales** que cubren todo el ciclo de negocio:

### 1. **Seguridad y Usuarios** 🔐
- **Gestión:** Usuarios, empleados, roles, permisos
- **Funciones:** Control de acceso, auditoría de usuarios, gestión de perfiles
- **Base de datos:** `seguridad_usuarios/`
- **Permisos:** 20+ permisos de CRUD y operacionales

### 2. **Configuraciones Maestras** ⚙️
- **Gestión:** Empresas, proveedores, agentes de transporte, despachantes, tasas de cambio
- **Funciones:** Datos de referencia del sistema, configuración de divisas
- **Base de datos:** `configuraciones_maestras/`
- **Permisos:** 30+ permisos para empresas, proveedores, transportistas

### 3. **Inventario** 📦
- **Gestión:** Vehículos (autos importados), repuestos, mantenimientos
- **Funciones:** Control de stock, categorización de productos, precios USD/PYG
- **Base de datos:** `inventario/`
- **Permisos:** 20+ permisos para vehículos, repuestos, mantenimientos
- **Características especiales:** Trazabilidad de divisas (Fase 1 completada)

### 4. **Clientes y Pedidos** 👥
- **Gestión:** Clientes, pedidos de venta, búsqueda, abastecimiento
- **Funciones:** Registro de clientes, creación de pedidos, gestión de cotizaciones
- **Tipos de Pedidos:**
  - 🔄 **Venta:** Venta directa de repuestos/vehículos
  - 🔍 **Búsqueda:** Búsqueda de productos por especificación
  - 📦 **Abastecimiento:** Reposición de stock
  - 🌍 **Importación:** Pedidos de importación a medida
- **Base de datos:** `clientes_pedidos/`
- **Permisos:** 40+ permisos complejos (crear, editar, aprobar, rechazar, transferir, etc.)

### 5. **Cobranzas** 💰
- **Gestión:** Pago de pedidos, facturas, transferencias, despacho
- **Funciones:** Registrar pagos, facturación, control de despacho
- **Estados de Pedido:**
  - En cobranzas (pendiente de pago)
  - En transferencia (proceso de envío)
  - En despacho (listo para entregar)
- **Base de datos:** `cobranzas/`
- **Permisos:** 15 permisos específicos para cobranza

### 6. **Importaciones** 🌐
- **Gestión:** Importaciones, documentos aduanales, fases de importación
- **Funciones:** Seguimiento de procesos aduanales, gestión de contenedores
- **Base de datos:** `importaciones/`
- **Permisos:** 8 permisos para manejo de importaciones

### 7. **Contabilidad** 📊
- **Gestión:** Asientos contables, movimientos, reportes
- **Funciones:** Auditoría contable, generación de reportes, análisis financiero
- **Base de datos:** `contabilidad/`
- **Permisos:** 5 permisos de lectura y análisis

**Otros módulos complementarios:**
- **Pedido Búsqueda:** Gestión específica del flujo de búsqueda de productos
- **Reposición de Stock:** Gestión de reordenamientos automáticos
- **Reportes:** Análisis general del sistema
- **Documentos Financieros:** Generación de facturas y documentos

---

## 👥 Roles Principales

### Sistema de Roles Jerárquico

El sistema cuenta con **5 roles principales** más 1 rol especial (Administrador):

### 1. **Administrador** 🔑
**Nivel:** Máxima autoridad  
**Definición:** `crear_roles.py` → `DEFAULT_ROLES[0]`

```python
{
    'nombre': 'Administrador',
    'descripcion': 'Acceso completo a todas las funcionalidades del sistema.',
    'permisos': 'all',  # Todos los permisos
}
```

**Responsabilidades:**
- ✅ Acceso TOTAL a todos los módulos
- ✅ Creación y gestión de usuarios
- ✅ Configuración del sistema
- ✅ Gestión de roles y permisos
- ✅ Generación de reportes ejecutivos
- ✅ Auditoría completa del sistema

**Funcionalidades principales:**
- Panel de administración completo
- Gestión de usuarios y empleados
- Configuración de empresas y proveedores
- Gestión de divisas y tasas de cambio
- Revisión de auditorías
- Acceso a reportes contables

---

### 2. **Rol Seguridad** 🔐
**Nivel:** Administración de acceso  
**Módulos:** `seguridad_usuarios`

```python
{
    'nombre': 'Seguridad',
    'descripcion': 'Gestiona usuarios, roles y permisos.',
    'prefijos': ['seguridad_usuarios.'],
    'sectores': ['Seguridad y Usuarios'],
}
```

**Responsabilidades:**
- ✅ Crear, editar, eliminar usuarios
- ✅ Crear, editar, eliminar empleados
- ✅ Crear y gestionar roles
- ✅ Asignar permisos a roles
- ✅ Cambiar contraseñas
- ✅ Ver auditoría de usuarios

**Funcionalidades clave:**
- Registrar nuevos usuarios
- Editar perfiles de usuario
- Crear roles predefinidos
- Asignar roles a usuarios
- Desactivar/reactivar usuarios
- Ver historial de cambios

---

### 3. **Rol Inventario** 📦
**Nivel:** Gestión de productos  
**Módulos:** `inventario`

```python
{
    'nombre': 'Inventario',
    'descripcion': 'Gestiona vehículos, repuestos y existencias.',
    'prefijos': ['inventario.'],
    'sectores': ['Inventario'],
}
```

**Responsabilidades:**
- ✅ Agregar/editar/eliminar vehículos
- ✅ Agregar/editar/eliminar repuestos
- ✅ Registrar mantenimientos
- ✅ Controlar stock (actual, reservado, disponible)
- ✅ Categorizar productos
- ✅ Establecer precios

**Funcionalidades clave:**
- Cargar vehículos importados (con divisas USD/PYG)
- Cargar repuestos con código interno
- Registrar categorías de repuestos
- Listar inventario disponible
- Ver detalles de productos
- Editar información de stock
- Registrar mantenimientos

**Datos que gestiona:**
- Vehículos: nombre, marca, modelo, color, chasis, precio, stock
- Repuestos: nombre, código, descripción, categoría, precio, stock
- Mantenimientos: tipo, descripción, costo, vehículo asociado

---

### 4. **Rol Ventas** 💼
**Nivel:** Operaciones comerciales  
**Módulos:** `clientes_pedidos`, `cobranzas`, `pedido_busqueda`

```python
{
    'nombre': 'Ventas',
    'descripcion': 'Gestiona pedidos, clientes y ventas.',
    'prefijos': ['clientes_pedidos.', 'cobranzas.', 'pedido_busqueda.'],
    'sectores': ['Clientes Pedidos', 'Cobranzas'],
}
```

**Responsabilidades:**
- ✅ Crear/editar clientes
- ✅ Crear pedidos de venta (incluye búsqueda y abastecimiento)
- ✅ Aprobar/rechazar pedidos
- ✅ Registrar pagos y cobranzas
- ✅ Gestionar despachos
- ✅ Generar facturas
- ✅ Establecer transferencias

**Funcionalidades clave:**
- **Gestión de Clientes:**
  - Registrar nuevos clientes (físicos o jurídicos)
  - Editar datos de clientes
  - Ver historial de pedidos

- **Gestión de Pedidos:**
  - Crear pedidos de VENTA (inventario disponible)
  - Crear pedidos de BÚSQUEDA (especificación personalizada)
  - Crear pedidos de ABASTECIMIENTO (reposición stock)
  - Crear pedidos de IMPORTACIÓN (a medida)
  - Agregar items a pedidos
  - Editar pedidos pendientes
  - Cancelar pedidos

- **Gestión de Flujo:**
  - Aprobar pedidos
  - Rechazar pedidos (con motivo)
  - Enviar a cobranzas
  - Programar transferencias
  - Confirmar transferencias
  - Registrar despachos

- **Cobranzas:**
  - Listar pedidos en cobranzas
  - Facturar al contado
  - Registrar pagos
  - Descargar facturas
  - Confirmar entregas

---

### 5. **Rol Configuraciones** ⚙️
**Nivel:** Datos maestros del sistema  
**Módulos:** `configuraciones_maestras`

```python
{
    'nombre': 'Configuraciones',
    'descripcion': 'Gestiona datos maestros y configuraciones del sistema.',
    'prefijos': ['configuraciones_maestras.'],
    'sectores': ['Configuraciones Maestras'],
}
```

**Responsabilidades:**
- ✅ Crear/editar empresas
- ✅ Crear/editar proveedores
- ✅ Crear/editar agentes de transporte
- ✅ Crear/editar despachantes aduanales
- ✅ Gestionar tasas de cambio (USD ↔ PYG)
- ✅ Cargar categorías de productos

**Funcionalidades clave:**
- **Empresas:** Registro central de empresa/sucursales
- **Proveedores:** Datos de proveedores, contactos, ubicación
- **Transporte:** Agentes de transporte y choferes
- **Aduana:** Despachantes aduanales
- **Divisas:** Tasas de cambio diarias (auditoría DNIT)
- **Contactos:** Gestión de contactos generales

**Datos que gestiona:**
- Razón social, RUC, teléfono, email, dirección
- Contactos por persona/empresa
- Tasas de cambio con usuario y fecha (trazabilidad)

---

## 📊 Matriz de Responsabilidades

| **Funcionalidad** | **Admin** | **Seguridad** | **Inventario** | **Ventas** | **Config** |
|---|:---:|:---:|:---:|:---:|:---:|
| **USUARIOS** | | | | | |
| Crear usuarios | ✅ | ✅ | ❌ | ❌ | ❌ |
| Editar usuarios | ✅ | ✅ | ❌ | ❌ | ❌ |
| Cambiar contraseña | ✅ | ✅ | ✅ | ✅ | ✅ |
| **INVENTARIO** | | | | | |
| Agregar vehículos | ✅ | ❌ | ✅ | ❌ | ❌ |
| Editar vehículos | ✅ | ❌ | ✅ | ❌ | ❌ |
| Listar repuestos | ✅ | ❌ | ✅ | ✅ | ❌ |
| Agregar repuestos | ✅ | ❌ | ✅ | ❌ | ❌ |
| **CLIENTES** | | | | | |
| Crear clientes | ✅ | ❌ | ❌ | ✅ | ❌ |
| Editar clientes | ✅ | ❌ | ❌ | ✅ | ❌ |
| Listar clientes | ✅ | ❌ | ❌ | ✅ | ❌ |
| **PEDIDOS** | | | | | |
| Crear pedidos | ✅ | ❌ | ❌ | ✅ | ❌ |
| Aprobar pedidos | ✅ | ❌ | ❌ | ✅ | ❌ |
| Rechazar pedidos | ✅ | ❌ | ❌ | ✅ | ❌ |
| Facturar | ✅ | ❌ | ❌ | ✅ | ❌ |
| Registrar pagos | ✅ | ❌ | ❌ | ✅ | ❌ |
| **COBRANZAS** | | | | | |
| Listar cobranzas | ✅ | ❌ | ❌ | ✅ | ❌ |
| Cobrar pedidos | ✅ | ❌ | ❌ | ✅ | ❌ |
| **CONFIGURACIÓN** | | | | | |
| Agregar empresas | ✅ | ❌ | ❌ | ❌ | ✅ |
| Agregar proveedores | ✅ | ❌ | ❌ | ❌ | ✅ |
| Cargar tasas cambio | ✅ | ❌ | ❌ | ❌ | ✅ |
| Gestionar roles | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ver reportes | ✅ | ❌ | ✅ | ✅ | ✅ |

---

## 🔑 Permisos por Rol

### ADMINISTRADOR (Todos los permisos - ~90+)

```
Acceso completo a:
- Todo en Seguridad y Usuarios (20+ permisos)
- Todo en Inventario (20+ permisos)
- Todo en Clientes y Pedidos (40+ permisos)
- Todo en Cobranzas (15+ permisos)
- Todo en Configuraciones Maestras (30+ permisos)
- Todo en Importaciones (8+ permisos)
- Todo en Contabilidad (5+ permisos)
```

### SEGURIDAD (20 permisos)

```
seguridad_usuarios.registrar_usuario
seguridad_usuarios.editar_usuario
seguridad_usuarios.eliminar_usuario
seguridad_usuarios.listar_usuarios
seguridad_usuarios.agregar_empleado
seguridad_usuarios.editar_empleado
seguridad_usuarios.eliminar_empleado
seguridad_usuarios.listar_empleados
seguridad_usuarios.agregar_rol
seguridad_usuarios.editar_rol
seguridad_usuarios.listar_rol
seguridad_usuarios.eliminar_rol
seguridad_usuarios.agregar_permiso
seguridad_usuarios.cambiar_contrasena
... (+ 6 más)
```

### INVENTARIO (20 permisos)

```
inventario.listar_inventario
inventario.agregar_vehiculo
inventario.listar_vehiculos
inventario.editar_vehiculo
inventario.eliminar_vehiculo
inventario.agregar_repuesto
inventario.listar_repuestos
inventario.editar_repuesto
inventario.eliminar_repuesto
inventario.agregar_mantenimiento
inventario.listar_mantenimientos
inventario.editar_mantenimiento
... (+ 8 más)
```

### VENTAS (55 permisos combinados)

**Clientes y Pedidos:**
```
clientes_pedidos.agregar_cliente
clientes_pedidos.editar_cliente
clientes_pedidos.listar_clientes
clientes_pedidos.detallar_cliente
clientes_pedidos.agregar_pedido
clientes_pedidos.editar_pedido
clientes_pedidos.listar_pedidos
clientes_pedidos.detallar_pedido
clientes_pedidos.realizar_pedido
clientes_pedidos.realizar_pedido_busqueda
clientes_pedidos.realizar_pedido_abastecimiento
clientes_pedidos.realizar_pedido_a_medida
clientes_pedidos.editar_pedido.aprobar
clientes_pedidos.editar_pedido.rechazar
clientes_pedidos.editar_pedido.enviar_a_cobranzas
... (+ 20 más de flujo)
```

**Cobranzas:**
```
cobranzas.lista_pedidos_cobranzas
cobranzas.cobrar_pedido
cobranzas.facturar_contado_cobranzas
cobranzas.facturar_pedido_cobranzas
cobranzas.descargar_factura_cobranzas
cobranzas.iniciar_transferencia_cobranzas
cobranzas.confirmar_transferencia_cobranzas
... (+ 8 más)
```

### CONFIGURACIONES (30 permisos)

```
configuraciones_maestras.lista_empresas
configuraciones_maestras.agregar_empresa
configuraciones_maestras.editar_empresa
configuraciones_maestras.detalles_empresa
configuraciones_maestras.agregar_proveedor
configuraciones_maestras.editar_proveedor
configuraciones_maestras.listar_proveedores
configuraciones_maestras.detallar_proveedor
configuraciones_maestras.cargar_tasas_cambio
configuraciones_maestras.editar_tasa_cambio
configuraciones_maestras.listar_tasas_cambio
... (+ 18 más de transportistas, despachantes, etc.)
```

---

## 🔄 Flujos de Trabajo por Rol

### Flujo VENDEDOR (Rol: Ventas)

```
1. INICIO DEL DÍA
   └─ Ver lista de clientes
   └─ Ver lista de pedidos pendientes
   └─ Ver inventario disponible

2. CREAR PEDIDO
   └─ Seleccionar cliente
   └─ Elegir tipo de pedido (Venta/Búsqueda/Abastecimiento)
   └─ Agregar items (vehículos/repuestos)
   └─ Establecer precios
   └─ Guardar pedido (estado: borrador)

3. PROCESO DE APROBACIÓN
   └─ Aprobar pedido (requiere permiso especial)
   └─ O rechazar con motivo

4. COBRO
   └─ Enviar a cobranzas
   └─ Registrar pago
   └─ Generar factura

5. ENTREGA
   └─ Programar transferencia
   └─ Confirmar entrega
   └─ Registrar documento
```

### Flujo ENCARGADO INVENTARIO (Rol: Inventario)

```
1. CARGA DE PRODUCTOS
   └─ Agregar nuevo vehículo importado (con tasa USD)
   └─ Agregar repuesto con stock
   └─ Categorizar productos
   └─ Establecer precios de venta

2. CONTROL DE STOCK
   └─ Ver inventario disponible
   └─ Verificar stock reservado
   └─ Listar mantenimientos

3. REPOSICIÓN
   └─ Ver pedidos de abastecimiento
   └─ Registrar llegada de repuestos
   └─ Actualizar stock
```

### Flujo ADMINISTRADOR DE CONFIGURACIÓN

```
1. DATOS MAESTROS
   └─ Registrar empresas y sucursales
   └─ Registrar proveedores
   └─ Registrar agentes de transporte

2. DIVISAS (Critical)
   └─ DIARIAMENTE: Cargar tasa de cambio USD → PYG
   └─ Histórico con auditoría (DNIT compliance)
   └─ Ver tendencia de tasas

3. SISTEMAS
   └─ Crear categorías de repuestos
   └─ Registrar despachantes aduanales
   └─ Gestionar contactos del sistema
```

### Flujo ADMINISTRADOR DE SEGURIDAD

```
1. USUARIOS
   └─ Crear nuevos usuarios
   └─ Asignar roles
   └─ Editar perfiles
   └─ Cambiar contraseñas
   └─ Desactivar/reactivar

2. ROLES Y PERMISOS
   └─ Crear nuevos roles (si se requiere)
   └─ Editar permisos de roles
   └─ Ver quién tiene qué rol

3. AUDITORÍA
   └─ Ver historial de cambios
   └─ Monitorear acceso
```

---

## 📈 Crecimiento del Sistema

### Módulos en Desarrollo (Fases 2-3):

- **Contabilidad Avanzada:** Asientos automáticos, reportes DNIT
- **Importaciones Completas:** Seguimiento aduanal, integración de fases
- **Reportes Ejecutivos:** Dashboards, análisis de ventas
- **API Externa:** Integración con sistemas terceros

### Roles Futuros (Potenciales):

- **Gerente Comercial:** Vista de reportes y analytics
- **Contador:** Acceso a reportes contables y auditoria
- **Despachante Aduanal:** Gestión de importaciones
- **Encargado de Transporte:** Control de envíos
- **Supervisor de Cobranzas:** Análisis de pagos

---

## 📝 Notas Importantes

### Trazabilidad y Auditoría
- ✅ **Sistema de divisas:** USD/PYG con histórico de tasa (DNIT)
- ✅ **Auditoría de usuarios:** Quién, cuándo, qué hizo
- ✅ **Control de roles:** No se pueden editar roles en uso
- ✅ **Historial de cambios:** Cada acción queda registrada

### Seguridad
- 🔐 Autenticación requerida para todos
- 🔐 Permisos verificados en cada vista (decorator `@revisar_permiso`)
- 🔐 No hay acceso cruzado entre roles (validación estricta)
- 🔐 Cambio de contraseña disponible para todos

### Base de Datos Física
- **Modelo de Rol:** `seguridad_usuarios.models.Rol`
- **Modelo de Permiso:** `seguridad_usuarios.models.Permiso`
- **Relación:** Rol ↔ Permiso (ManyToMany)
- **Asignación:** User → (Perfil/Empleado) → Cargo → Roles

---

## 🛠️ Comandos de Gestión

```bash
# Cargar permisos iniciales
python manage.py cargar_permisos

# Crear roles predefinidos
python manage.py crear_roles

# Forzar recreación de roles
python manage.py crear_roles --force

# Crear un rol específico
python manage.py crear_roles --role Inventario

# Cargar datos de prueba
python manage.py crear_empleados_dummy
```

---

**Versión:** 1.0  
**Última actualización:** Julio 2026  
**Mantenedor:** Sistema SKPY AutoGest
