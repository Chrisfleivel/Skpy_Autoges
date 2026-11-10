# 📘 Manual de Usuarios - SKPY AutoGest
## Guías por Roles y Responsabilidades

**Versión:** 1.0 | **Última actualización:** Julio 2026

---

## 📑 Tabla de Contenidos

1. [Roles Principales](#roles-principales)
2. [Administrador](#-rol-administrador)
3. [Seguridad y Usuarios](#-rol-seguridad-y-usuarios)
4. [Inventario](#-rol-inventario)
5. [Ventas](#-rol-ventas)
6. [Configuraciones Maestras](#-rol-configuraciones-maestras)
7. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🎯 Roles Principales

| # | Rol | Responsabilidad | Usuarios |
|---|-----|-----------------|----------|
| 1 | **Administrador** | Acceso total al sistema | Gerentes, supervisores |
| 2 | **Seguridad** | Usuarios, roles, auditoría | Administradores de seguridad |
| 3 | **Inventario** | Vehículos, repuestos, stock | Almaceneros, técnicos |
| 4 | **Ventas** | Clientes, pedidos, cobranzas | Vendedores, ejecutivos |
| 5 | **Configuraciones** | Datos maestros, tasas cambio | Administradores, contadores |

---

## 🔑 Rol: Administrador

**Acceso:** Total a todos los módulos  
**Responsabilidad:** Supervisar todo el sistema  
**Usuarios Típicos:** Gerente General, Supervisor

### ✅ Tareas Principales

#### 1. **Crear un nuevo usuario**
```
1. Ir a [Seguridad] → [Empleados] → [Crear Empleado]
2. Completar datos: Nombre, Email, Departamento
3. Asignar uno o más ROLES
4. Guardar
5. El sistema enviará contraseña temporal al email
```

#### 2. **Asignar Roles a un Usuario**
```
1. Ir a [Seguridad] → [Usuarios]
2. Buscar el usuario
3. Hacer clic en [Editar Perfil]
4. Seleccionar ROLES requeridos:
   ☐ Inventario (para almaceneros)
   ☐ Ventas (para vendedores)
   ☐ Configuraciones (para contadores)
5. Guardar cambios
```

#### 3. **Ver Auditoría del Sistema**
```
[Seguridad] → [Auditoría]
Filtrar por:
- Fecha
- Usuario
- Tipo de acción (Creación/Modificación/Eliminación)
- Tabla afectada
```

#### 4. **Crear un Rol Personalizado**
```
1. [Seguridad] → [Roles] → [Crear Rol]
2. Nombre: Ej: "Vendedor Senior"
3. Descripción: Explicar responsabilidades
4. Seleccionar permisos específicos (CheckBox)
5. Guardar
```

#### 5. **Generar Reporte de Usuarios**
```
[Reportes] → [Usuarios Activos]
Información disponible:
- Nombre completo
- Email
- Roles asignados
- Último acceso
- Estado (activo/inactivo)
```

---

## 🔐 Rol: Seguridad y Usuarios

**Acceso:** Módulo de Seguridad  
**Responsabilidad:** Gestionar usuarios, roles y permisos  
**Usuarios Típicos:** Administrador de sistemas, Recursos Humanos

### ✅ Tareas Principales

#### 1. **Crear Nuevo Empleado en el Sistema**
```
1. [Seguridad] → [Empleados] → [+ Crear Empleado]
2. Completar:
   - Nombre completo
   - Documento (Cédula/Pasaporte)
   - Email
   - Teléfono
   - Departamento
3. Guardar
```

#### 2. **Crear Usuario para un Empleado**
```
1. [Seguridad] → [Empleados]
2. Seleccionar empleado
3. Botón [Crear Usuario]
4. Asignar:
   - Username (ej: jperez)
   - Roles de acceso
   - Contraseña temporal
5. Guardar
6. Email con credenciales se envía automáticamente
```

#### 3. **Desactivar Usuario**
```
1. [Seguridad] → [Usuarios]
2. Buscar usuario
3. Clic en [Desactivar]
4. El usuario NO podrá iniciar sesión
5. La auditoría registrará la acción
```

#### 4. **Resetear Contraseña de Usuario**
```
1. [Seguridad] → [Usuarios]
2. Buscar usuario
3. [Generar Nueva Contraseña Temporal]
4. Email con nueva contraseña se envía
5. Usuario debe cambiarla en primer login
```

#### 5. **Auditar Cambios en el Sistema**
```
[Seguridad] → [Auditoría]
Información registrada:
✓ Quién hizo el cambio
✓ Cuándo lo hizo (fecha/hora exacta)
✓ Qué cambió
✓ En qué tabla
Para cumplimiento legal y análisis de seguridad
```

#### 6. **Gestionar Permisos**
```
[Seguridad] → [Permisos]
- Crear permiso: [+ Crear Permiso]
- Editar permiso: Seleccionar → [Editar]
- Visualizar por sector
- Solo administrador puede eliminar
```

---

## 📦 Rol: Inventario

**Acceso:** Módulo de Inventario, configuraciones  
**Responsabilidad:** Gestionar vehículos, repuestos y stock  
**Usuarios Típicos:** Almaceneros, Técnicos, Encargados de bodega

### ✅ Tareas Principales

#### 1. **Registrar Nuevo Vehículo**
```
1. [Inventario] → [Vehículos] → [+ Nuevo Vehículo]
2. Datos requeridos:
   - Tipo (Auto/Moto/Bus)
   - Marca
   - Modelo
   - Año
   - Placa (único)
   - VIN (número de serie)
3. Guardar
```

#### 2. **Agregar Repuesto al Stock**
```
1. [Inventario] → [Repuestos] → [+ Agregar Repuesto]
2. Completar:
   - Código (único)
   - Descripción
   - Categoría
   - Cantidad disponible
   - Precio unitario
   - Proveedor
3. Cargar foto (opcional)
4. Guardar
```

#### 3. **Ajustar Stock por Inventario Físico**
```
1. [Inventario] → [Stock] → [Ajustar Stock]
2. Seleccionar repuesto
3. Cantidad actual en sistema: ___
4. Cantidad real (contada): ___
5. DIFERENCIA = Pérdida/Ganancia registrada
6. Guardar (quedaría en auditoría)
```

#### 4. **Buscar Repuestos por Vehículo**
```
[Pedido Búsqueda] → [Buscar Repuestos]
Ingresar:
- Marca
- Modelo
- Año
Resultado: Lista de repuestos compatibles
```

#### 5. **Ver Repuestos con Bajo Stock**
```
[Inventario] → [Alertas de Stock]
Muestra:
✓ Repuestos bajo mínimo
✓ Cantidad actual
✓ Cantidad mínima
✓ Botón para crear orden de reposición
```

#### 6. **Crear Orden de Reposición de Stock**
```
1. [Reposición Stock] → [+ Nueva Orden]
2. Seleccionar repuestos a reponer
3. Cantidad a solicitar
4. Proveedor
5. Guardar
6. Sistema notifica a gerencia
```

---

## 💼 Rol: Ventas

**Acceso:** Módulos Clientes, Pedidos, Cobranzas  
**Responsabilidad:** Gestionar clientes, pedidos y cobros  
**Usuarios Típicos:** Vendedores, Ejecutivos de ventas, Cobradores

### ✅ Tareas Principales

#### 1. **Crear un Cliente**
```
1. [Clientes y Pedidos] → [Clientes] → [+ Nuevo Cliente]
2. Datos requeridos:
   - Nombre/Razón Social
   - Documento (RUC/Cédula)
   - Email
   - Teléfono
   - Dirección
   - Tipo: Persona/Empresa
3. Guardar
```

#### 2. **Crear Pedido - Venta Directa**
```
1. [Clientes y Pedidos] → [Pedidos] → [+ Nuevo Pedido]
2. Tipo: VENTA (inventario disponible)
3. Seleccionar Cliente
4. Agregar items:
   - Seleccionar repuesto
   - Cantidad disponible
   - Precio
5. Total se calcula automáticamente
6. Guardar
7. Generar factura
```

#### 3. **Crear Pedido - Búsqueda Personalizada**
```
1. [Clientes y Pedidos] → [Pedidos] → [+ Nuevo Pedido]
2. Tipo: BÚSQUEDA (repuesto no disponible)
3. Seleccionar Cliente
4. Ingresar datos del repuesto buscado:
   - Descripción
   - Marca/Modelo (si aplica)
   - Cantidad
   - Precio estimado
5. Estado: En búsqueda → A confirmar → Entregado
6. Guardar
```

#### 4. **Crear Pedido - Importación**
```
1. [Clientes y Pedidos] → [Pedidos] → [+ Nuevo Pedido]
2. Tipo: IMPORTACIÓN (pedido internacional)
3. Seleccionar Cliente
4. Agregar items con datos detallados
5. Ingresar datos aduanales (si es DNIT)
6. Registrar conversión de divisas (USD ↔ PYG)
7. Guardar
8. Seguimiento: Aduanas → En tránsito → Entregado
```

#### 5. **Registrar Pago/Cobro**
```
1. [Cobranzas] → [Pagos] → [+ Registrar Pago]
2. Seleccionar Cliente
3. Búsqueda de facturas pendientes:
   - Factura #
   - Monto debido
   - Fecha vencimiento
4. Seleccionar facturas a cobrar
5. Método de pago:
   - Contado (efectivo)
   - Transferencia
   - Cheque
6. Guardar
7. Recibo se genera automáticamente
```

#### 6. **Ver Estado de Cobranza**
```
[Cobranzas] → [Estado de Cuentas]
Filtrar por:
- Cliente
- Rango de fechas
Información:
✓ Factura #
✓ Fecha
✓ Monto
✓ Pagado
✓ Saldo pendiente
✓ Días de atraso
```

#### 7. **Generar Factura**
```
1. [Pedidos] → [Facturación]
2. Seleccionar Pedido
3. Revisa datos:
   - Cliente
   - Items
   - Cantidades
   - Precios
4. Ingresar número de factura (secuencial)
5. [Generar PDF]
6. Guardar
7. Email con factura se envía a cliente (opcional)
```

---

## ⚙️ Rol: Configuraciones Maestras

**Acceso:** Datos maestros, divisas, tasas cambio  
**Responsabilidad:** Mantener datos de referencia del sistema  
**Usuarios Típicos:** Contadores, Administradores, Gerentes administrativos

### ✅ Tareas Principales

#### 1. **Crear Empresa**
```
1. [Configuraciones] → [Empresas] → [+ Nueva Empresa]
2. Datos:
   - Razón Social
   - RUC (único)
   - Dirección
   - Teléfono
   - Email
   - Logo (opcional)
3. Guardar
```

#### 2. **Crear Proveedor**
```
1. [Configuraciones] → [Proveedores] → [+ Nuevo Proveedor]
2. Datos:
   - Nombre/Razón Social
   - Documento (RUC)
   - Email
   - Teléfono
   - País
   - Especialidad (Repuestos/Vehículos/etc)
3. Guardar
```

#### 3. **Actualizar Tasa de Cambio USD/PYG**
```
1. [Configuraciones] → [Divisas] → [Tasa de Cambio]
2. Fecha actual se carga automáticamente
3. Tasa vigente:
   - Compra (USD): ___ PYG
   - Venta (USD): ___ PYG
4. Cambio respecto a día anterior se calcula automáticamente
5. Guardar
6. Se aplica automáticamente a nuevos pedidos con USD
```

#### 4. **Crear Categoría de Repuesto**
```
1. [Configuraciones] → [Categorías] → [+ Nueva Categoría]
2. Nombre: Ej: "Motor", "Suspensión", "Frenos"
3. Descripción
4. Activo: ☑ Sí
5. Guardar
```

#### 5. **Crear Marca de Vehículo**
```
1. [Configuraciones] → [Marcas] → [+ Nueva Marca]
2. Nombre: Ej: "Toyota", "Ford"
3. País de origen
4. Guardar
```

#### 6. **Ver Auditoria de Cambios Maestros**
```
[Configuraciones] → [Auditoría]
Rastrea:
✓ Quién modificó la tasa de cambio
✓ Cuándo
✓ De qué valor a qué valor
✓ Razón (en observaciones)
```

---

## 🎬 Flujos Principales del Sistema

### Flujo 1: **Venta de Repuesto (Inventario Disponible)**
```
1. Cliente llama/visita
2. Vendedor busca repuesto [Inventario] → [Stock]
3. Si está disponible:
   - Crea Pedido tipo VENTA
   - Ingresa cantidad
   - Genera Factura
   - Descuenta automáticamente del stock
4. Cliente recibe repuesto
5. Registra pago [Cobranzas]
```

### Flujo 2: **Búsqueda de Repuesto No Disponible**
```
1. Vendedor crea Pedido tipo BÚSQUEDA
2. Describe repuesto solicitado
3. Almacenero ve alertas de búsquedas activas
4. Localiza proveedor
5. Cuando llega:
   - Registra en inventario
   - Notifica a vendedor
   - Vendedor confirma pedido
6. Genera factura y recibe pago
```

### Flujo 3: **Importación (Pedido Internacional)**
```
1. Vendedor crea Pedido tipo IMPORTACIÓN
2. Registra datos aduanales
3. Gerencia autoriza
4. Gerente aduanal:
   - Tramita aduanas
   - Registra estado
5. Cuando llega:
   - Ingresa a inventario
   - Costo se convierte a PYG usando tasa vigente
6. Factura al cliente
```

### Flujo 4: **Reposición de Stock Bajo**
```
1. Sistema detecta stock bajo [Alertas]
2. Almacenero crea Orden de Reposición
3. Selecciona proveedor
4. Envía orden automáticamente
5. Cuando llega:
   - Recibe mercadería
   - Registra en inventario
   - Actualiza stock automático
```

---

## ❓ Preguntas Frecuentes

### **¿Cómo cambiar mi contraseña?**
```
1. Clic en tu avatar (arriba a la derecha)
2. [Mi Perfil] → [Cambiar Contraseña]
3. Ingresa contraseña actual
4. Ingresa nueva contraseña (2 veces)
5. Guardar
6. Próximo login: usa nueva contraseña
```

### **¿Olvidé mi contraseña, qué hago?**
```
1. En pantalla de login: [¿Olvidó su contraseña?]
2. Ingresa tu email
3. Recibís link de reset en email (válido 24 hs)
4. Haz clic en link y establece nueva contraseña
Si no funciona → contacta Administrador
```

### **¿Cómo buscar un pedido anterior?**
```
1. [Clientes y Pedidos] → [Pedidos]
2. Usa filtros:
   - Cliente
   - Fecha (desde/hasta)
   - Estado
   - Tipo de pedido
3. Haz clic en [Buscar]
4. Resultado: lista con opciones de ver/editar/facturar
```

### **¿Cómo se registran los cambios de datos?**
```
Todos los cambios se guardan automáticamente:
✓ Usuario que lo hizo
✓ Fecha y hora exacta
✓ Qué se modificó
✓ Valor anterior vs Valor nuevo
Verlos: [Seguridad] → [Auditoría]
```

### **¿Qué significa cada TIPO DE PEDIDO?**

| Tipo | Cuando usarlo | Stock | Tasa cambio |
|------|:-------------|:-----:|:-----------:|
| **VENTA** | Repuesto está disponible en inventario | Se descuenta | PYG |
| **BÚSQUEDA** | No disponible, se busca con proveedores | No se descuenta | PYG |
| **ABASTECIMIENTO** | Reorden interna de stock bajo | Se reserva | PYG |
| **IMPORTACIÓN** | Pedido del extranjero (en dólares) | Se reserva | USD→PYG |

### **¿Cómo funciona la conversión de divisas?**
```
Sistema mantiene tasa USD/PYG vigente:
1. [Configuraciones] → [Divisas]
2. Contador actualiza tasa diaria
3. Al crear factura con USD:
   - Monto USD × Tasa = Monto PYG
   - Se guarda ambas divisas
   - Reporte muestra conversión
4. Cada transacción queda registrada con su tasa
```

### **¿Qué hago si hice error en una factura?**
```
1. [Clientes y Pedidos] → [Facturas]
2. Buscar factura
3. Si no está pagada:
   - Opción [Anular] → Registra como cancelada
   - Crea nueva factura correcta
4. Si está pagada:
   - Contactar administrador
   - Se hace nota de crédito
5. Auditoría registra todo
```

### **¿Quién puede ver mis auditorías?**
```
- Tú ves tus propios cambios: [Mi Perfil] → [Mi Actividad]
- Gerentes/Administradores: [Seguridad] → [Auditoría] (todos)
- Rol Contable: [Configuraciones] → [Auditoría] (datos maestros)
```

### **¿Cómo sé qué permisos tengo?**
```
1. Clic en tu avatar → [Mi Perfil]
2. Sección "Roles Asignados": ves tus roles
3. Cada rol tiene permisos específicos
4. Si necesitas más acceso: solicita a tu supervisor
```

---

## 📞 Contactos de Soporte

| Área | Contacto | Ext |
|------|----------|-----|
| **Seguridad/Usuarios** | sistemas@skpyautogest.com | 101 |
| **Inventario** | almacen@skpyautogest.com | 102 |
| **Ventas** | ventas@skpyautogest.com | 103 |
| **Configuraciones** | contabilidad@skpyautogest.com | 104 |
| **Soporte Técnico** | soporte@skpyautogest.com | 0 |

---

## 📋 Checklist para Nuevos Usuarios

- [ ] Cuenta creada y credenciales recibidas
- [ ] Primer login realizado exitosamente
- [ ] Contraseña temporal cambiada
- [ ] Tema preferido configurado
- [ ] Foto de perfil cargada (opcional)
- [ ] Leído el manual correspondiente a su rol
- [ ] Entrenamiento con supervisor completado
- [ ] Acceso a módulos verificado

---

**Última actualización:** Julio 2026  
**Versión:** 1.0  
**Siguiente revisión:** Enero 2027
