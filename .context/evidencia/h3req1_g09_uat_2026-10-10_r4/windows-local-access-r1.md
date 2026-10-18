# Acceso Windows localhost — UAT H3REQ1 — 2026-10-11

## Resultado

- URL verificada desde Windows: `http://127.0.0.1:3333/`.
- `curl.exe -4` ejecutado en Windows contra esa URL respondió HTTP 200; `curl` desde Ubuntu WSL también respondió HTTP 200 (34 500 bytes).
- Ruta directa del curso usada en el recorrido R30: `http://127.0.0.1:3333/courses/ulima/analitica-aplicada-60000000/`; `Invoke-WebRequest` lanzado desde Windows respondió HTTP 200 y el HTML contenía “Analítica Aplicada”.
- En esta configuración, `http://localhost:3333/` resolvió primero a `::1` y expiró porque solo se publica IPv4. Usa `127.0.0.1`; no se amplió el binding.
- Docker publica únicamente `127.0.0.1:3333 -> h3req1-g09-localhost-proxy-r12:3330`.
- Docker Desktop es el engine activo. Se confirmó el acceso HTTP desde el proceso Windows; no se abrió una ventana del navegador Windows en esta sesión. La URL queda limitada a loopback.

## Entorno preservado

- App existente: `h3req1-g09-uat-app-20261010-r12`, imagen local `studiamatch-h3req1:20261009-v3`, sigue `running`.
- PostgreSQL sintético existente: `h3req1-g09-uat-pg17-20261010-r12`, sigue `running`.
- Red de pruebas existente: `h3req1-g09-uat-20261010-r12`, `internal=true`.
- No se recrearon ni reiniciaron la app o PostgreSQL, y no se modificaron los datos del fixture.
- El servidor Pages/workerd existente escucha en `127.0.0.1:3330` dentro de la app. Un puente de solo TCP en el puerto interno `3334` permite al proxy llegar a ese listener sin reemplazarlo.

## Auxiliares de acceso

- `h3req1-g09-localhost-proxy-r12` usa la misma imagen local (`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`), usuario `65532:65532`, root filesystem read-only, sin capabilities, sin mounts y con límites de 256 MiB, 0.25 CPU y 64 procesos.
- Red auxiliar `h3req1-g09-localhost-access-r12`: bridge sin masquerade saliente y con inter-container communication desactivada. Solo el proxy está conectado allí; también está conectado a la red UAT interna.
- No se pasaron `.env`, credenciales, secretos ni valores de configuración al proxy.
- El mapeo inicial desde la red UAT no publicaba el puerto porque esa red es interna (`docker port` no mostraba binding). El proxy se conectó a la red auxiliar; el binding efectivo quedó en `127.0.0.1:3333`.
- El primer proxy apuntaba al puerto 3330 de la IP del contenedor. La prueba estructurada acreditó que Pages/workerd solo escucha en loopback. Se corrigió el trayecto con el puente interno 3334 y un proxy auxiliar de reemplazo; no se alteró el runtime.

## Datos sintéticos visibles

- Curso: `Analítica Aplicada`.
- ID: `70000000-0000-0000-0000-000000000091`.
- Slug: `analitica-aplicada-60000000`.
- Identidades de prueba en UAT: `admin@local.test` y `user@local.test`; esta nota no contiene contraseñas ni códigos MFA.
- El acceso muestra la misma app/fixture usado por UAT, no datos operativos.

## Capturas relacionadas

- [Cola Admin con el filtro predeterminado vacío](uat-functional-final-r25/H3-UAT-006-desktop.png).
- [Listado público con el curso sintético y dos enlaces en su tarjeta](uat-functional-final-r25/H3-UAT-053-desktop.png).

La primera captura respalda que cero resultados es el estado correcto para el filtro predeterminado; el fallo r25 provino de una expectativa del runner que asumía una fila. La segunda respalda que el contador del runner debe contar la tarjeta y validar sus enlaces, no exigir un único enlace.

## Recorrido y evidencia actualizada

- El runner usa Playwright Chromium headless dentro de `h3req1-g09-uat-app-20261010-r12`; Pages/workerd sirve en el mismo contenedor. Cada caso se ejecuta en desktop, tablet y móvil, sin ventana visible y sin retries.
- r26 fue focal (15 casos × 3): 31/45 PASS, 14 FAIL. Sus capturas se preservan en `uat-functional-targeted-r26/`; el vídeo del flujo integrado es `uat-functional-targeted-r26/H3-UAT-049-desktop.webm`.
- r27 revalidó los cinco casos afectados (013, 017, 023, 049 y 054): 15/15 PASS, 15 capturas, un vídeo y cero retries. La matriz, manifiesto, ejecución y hashes están en `uat-functional-targeted-r27/`.
- En r27 se sincronizaron las respuestas de cola con los filtros solicitados; la fecha base se compara con `field_timestamps` presente; el comparador espera el título y precio cargados; la URL oficial se valida en JSON-LD, donde la página la publica. No se cambió código funcional del producto.
- Capturas actuales: [comparador integrado tablet](uat-functional-targeted-r27/H3-UAT-049-tablet.png), [Admin/procedencia y disponibilidad desktop](uat-functional-targeted-r27/H3-UAT-023-desktop.png), [detalle público desktop](uat-functional-targeted-r27/H3-UAT-054-desktop.png). [Vídeo integrado r27](uat-functional-targeted-r27/H3-UAT-049-desktop.webm).
- R28 ejecutó el catálogo vigente completo: 189 ejecuciones, 180 PASS y 9 FAIL, cero retries, 189 capturas y el vídeo del caso integrado 049. R29 ejecutó solo 007, 032 y 042 × tres viewports después de corregir selección del runner y los endpoints/host del ensayo: 9/9 PASS, nueve capturas, cero retries.
- R28 + R29 + R30 quedan conciliados con un PASS vigente para cada una de las 189 ejecuciones; no se presenta como una sola corrida 189/189. R30 revalidó 049 × tres viewports tras añadir una assertion del enlace interno “Solicitar Info”. Los fallos originales se preservan; los 201 PNG y dos vídeos siguen disponibles. Matriz, causas y hashes en [reconciliación R28/R29/R30](r28_r29_catalog_reconciliation_2026-10-11.md). La matriz funcional de 23 áreas sigue parcial, por lo que G09 continúa parcial.
- En Windows usa `http://127.0.0.1:3333/`. Se validó HTTP 200 con PowerShell; no se abrió navegador Windows GUI. Chromium headless se usa en los ensayos automatizados.

## Continuación de filtros y acceso — 2026-10-11

Se preservó la misma app Pages/workerd, el mismo proxy loopback y la misma
base PG17 sintética para R24–D26. URL Windows: `http://127.0.0.1:3333/`;
fixture: `Analítica Aplicada` (`70000000-0000-0000-0000-000000000091`). El
runner Chromium 1228 continuó headless. R24 canónico pasó H3-UAT-059/060 en
6/6 viewports; R28 pasó los filtros, bandas, orden/paginación y comparación
052/053/059/060/061/062 en 18/18. Se conserva el rojo R23. La causa fue el
estado `searchInput` obsoleto que el debounce podía reaplicar después de que
“Limpiar todo” solo vaciara `searchTerm`; el delta WIP antes de R24 limpia ambos.
Las capturas canónicas y el vídeo diagnóstico están enlazados en
[el análisis de filtros](h3req1_g09_filters_windows_access_r24_r26_2026-10-11.md).
La continuación R31–R33 ejecutó H3-UAT-053 en el mismo runtime: 3/3 viewports,
9/9 aserciones, tres capturas y cero retries. El acceso Windows continúa en
`http://127.0.0.1:3333/`; ver
[capturas, hashes y resultado](../h3req1_g09_windows_access_combined_filters_r31_r33_2026-10-11.md).
