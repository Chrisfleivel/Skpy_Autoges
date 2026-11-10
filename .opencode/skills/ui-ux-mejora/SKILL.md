---
name: ui-ux-mejora
description: Audita y mejora la interfaz (UI) y la experiencia de usuario (UX) de una aplicación web existente o nueva: jerarquía visual, usabilidad, formularios, tablas, estados vacíos/carga/error, accesibilidad, responsive y textos. Usa esta skill siempre que el usuario pida mejorar, pulir, rediseñar o revisar la interfaz, el diseño o la usabilidad, que algo "se vea mejor", sea "más fácil de usar" o "más profesional", o mencione UX, UI, accesibilidad, responsive, formularios confusos, dashboards o pantallas de un sistema de gestión, aunque no use esas palabras exactas. Also use for - improve UI, UX review, usability audit, polish the frontend, redesign a screen.
---

# Mejora de UI y UX

Objetivo: que la pantalla sea más clara, rápida y agradable de usar para personas reales, sin romper lo que ya funciona. Una buena mejora se nota en que el usuario duda menos, se equivoca menos y termina su tarea en menos pasos.

## Principios

- **Claridad antes que decoración.** Cada elemento visual debe ayudar a entender o a actuar. Si solo adorna, quítalo.
- **Consistencia con lo que ya existe.** Respeta el sistema de diseño, los componentes y las convenciones del proyecto. Un cambio coherente vale más que uno vistoso pero aislado.
- **Cambios pequeños y verificables.** Es más fácil revisar y revertir diez ajustes acotados que un rediseño completo.
- **La interfaz no toca la lógica.** No cambies reglas de negocio, URLs, nombres de campos, validaciones del backend ni modelos, salvo que el usuario lo pida.

## Flujo de trabajo

### 1. Entender el contexto

Antes de proponer nada, lee el código de la pantalla (templates, componentes, CSS) e identifica:

- Stack y librerías de UI en uso (por ejemplo Django templates, React, Bootstrap, Tailwind). Mejora con lo que ya hay; no agregues dependencias nuevas sin permiso.
- Quién usa la pantalla y cuál es su tarea principal (por ejemplo, registrar una venta, buscar un vehículo, revisar un cobro).
- Si hay variables CSS, clases utilitarias o componentes reutilizables que deban respetarse.

Si falta algo esencial, haz una sola pregunta. Si no, asume lo más razonable y dilo en una línea.

### 2. Auditar

Si tienes un navegador disponible (Browser MCP, Playwright u otro), úsalo: abre la pantalla, toma capturas en escritorio y en móvil (~375 px de ancho), revisa la consola y recorre el flujo con el teclado. Si no, audita desde el código. Revisa estos puntos:

**Jerarquía y layout**
- ¿Se entiende en 3 segundos qué es la pantalla y cuál es la acción principal?
- Una sola acción primaria por vista; las secundarias con menos peso visual.
- Espaciado consistente (usa una escala, por ejemplo 4/8/16/24/32), alineaciones limpias y agrupación por proximidad.
- Líneas de texto de menos de ~80 caracteres y buen contraste de tamaños entre títulos y cuerpo.

**Navegación y orientación**
- El usuario sabe dónde está (título, migas, ítem activo en el menú) y cómo volver.
- Los nombres del menú usan el vocabulario del usuario, no el del sistema.

**Formularios**
- Etiqueta visible por campo (no solo placeholder), agrupación lógica, campos obligatorios marcados.
- Tipo de input correcto (fecha, número, email, selector con búsqueda si hay muchas opciones) y `autocomplete` cuando aplique.
- Errores junto al campo, que digan qué pasó y cómo corregirlo; no perder lo ya escrito al fallar la validación.
- Botón de envío con verbo concreto ("Guardar cliente", no "Enviar") y estado de "guardando" para evitar doble envío.

**Tablas y datos (comunes en sistemas de gestión)**
- Búsqueda, filtros y orden en las columnas que de verdad se consultan; paginación o scroll claro.
- Números alineados a la derecha, formato local de moneda y fechas, estados con etiqueta de color **y** texto.
- Acciones por fila visibles pero discretas; confirmación clara en las destructivas, indicando qué se va a borrar.

**Feedback y estados**
- Cada acción confirma su resultado (mensaje de éxito o error) con el mismo vocabulario que usó el botón.
- Estados de carga, vacío y error diseñados: un estado vacío explica qué falta y ofrece la acción para resolverlo.

**Accesibilidad (mínimo AA)**
- Contraste de texto de al menos 4.5:1 (3:1 en texto grande); el color nunca es la única señal.
- Foco de teclado visible y orden de tabulación lógico; todo es operable sin mouse.
- Imágenes con `alt`, botones con texto o `aria-label`, HTML semántico (`button`, `nav`, `main`, `label for`).
- Áreas táctiles de al menos ~44 px y respeto de `prefers-reduced-motion`.

**Responsive**
- Sin scroll horizontal en móvil; las tablas anchas se adaptan (contenedor con scroll o vista en tarjetas).
- Los controles críticos siguen accesibles en pantallas pequeñas.

**Textos (microcopy)**
- Voz activa, frases cortas, sentence case, sin jerga técnica. Los errores no se disculpan ni son vagos.
- Un mismo concepto se llama igual en todas las pantallas.

### 3. Priorizar

Ordena los hallazgos por impacto en el usuario frente a esfuerzo de implementación. Empieza por lo que más ayuda con menos riesgo (bugs de usabilidad, errores de formulario, contraste, estados faltantes). Trabaja en rondas de 5 a 8 cambios como máximo para que el usuario pueda revisarlos.

### 4. Implementar

- Reutiliza clases y componentes existentes. Si ves valores repetidos (colores, espaciados, radios), centralízalos en variables CSS en lugar de duplicarlos.
- Mantén intactos los elementos funcionales: nombres de campos, `name`/`id` que usa el backend, tokens CSRF, atributos de HTMX/JS y URLs.
- Haz los cambios por partes y explica brevemente cada uno. No reescribas archivos completos si basta con editar unas líneas.

### 5. Verificar

- Si hay navegador: vuelve a capturar (escritorio y móvil), revisa que no haya errores nuevos en consola y repite el flujo principal con teclado.
- Si no: revisa el código resultante y, si hay tests o `check` del framework, ejecútalos.
- Comprueba que lo que funcionaba sigue funcionando (envío de formularios, filtros, enlaces).

### 6. Reportar

Cierra con un resumen breve:

1. **Qué cambió** y por qué (una línea por cambio, orientada al usuario).
2. **Archivos tocados.**
3. **Cómo verificarlo** (qué pantalla abrir y qué probar).
4. **Pendientes recomendados**, con su prioridad, que no se hicieron en esta ronda.

## Si hay libertad de diseño (pantalla nueva o rediseño pedido)

Antes de escribir código, define un plan corto y compruébalo contra el contexto del producto:

- **Color:** 4 a 6 valores con nombre (base, superficie, texto, acento, estados éxito/error/aviso).
- **Tipografía:** una o dos familias con roles claros y una escala consistente.
- **Layout:** una frase o un wireframe ASCII por pantalla, indicando la alineación.

Evita los "defaults genéricos" (mismas tarjetas redondeadas con sombra suave en todo, degradados decorativos, etiquetas en mayúsculas sobre cada título, animaciones de entrada en cada sección). Elige una sola cosa para que sea la memorable y mantén el resto sobrio. El movimiento se usa solo para mostrar un cambio de estado tras una acción del usuario.

## Qué evitar

- Rediseñar todo cuando piden un ajuste puntual.
- Cambiar la lógica de negocio, el backend o los datos para "arreglar" un problema visual.
- Añadir librerías, fuentes externas o animaciones sin necesidad ni permiso.
- Inventar datos o textos legales; si hace falta contenido de ejemplo, márcalo como provisional.
- Usar el color como único indicador de estado o de error.