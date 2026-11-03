# H3REQ1 G09 delta R64–R70 — 2026-10-11

## Candidato y resultado

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/base: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- R70 validó el bundle normal construido desde el candidato, Pages/workerd con Miniflare, mocks locales y PostgreSQL 17 sintético R12. Chromium 1228 corrió dentro del contenedor UAT en modo headless, sin ventana visible.
- Resultado R70: H3-UAT-049 y H3-UAT-064, 6/6 ejecuciones PASS, 96/96 aserciones, cero errores de consola, cero requests fallidos y cero retries. Se preservaron seis PNG y un vídeo desktop del recorrido H3-UAT-049.
- El Windows loopback existente `http://localhost:3336/` sigue respondiendo HTTP 200 y conserva acceso a R12/datos sintéticos. El runtime temporal R69 se mantuvo interno al contenedor durante las pruebas y no se expuso al host.

## LOCAL-05 — comparación

El estado previo cubría selección, retirada, duplicados, límite, deep link y rechazo de un curso no elegible, pero faltaba comparar dos candidatos elegibles con campos opcionales ausentes. H3-UAT-064 añadió ese caso: dos IDs y cursos sintéticos distintos, campos de precio/duración/ROI/salario ausentes en uno, valores poblados distintos en el otro y ubicación no entregada por `COURSE_PUBLIC_FIELDS`.

R61 había mostrado que la etiqueta `Ubicación` quedaba sin valor. El componente ahora presenta `Por confirmar` cuando `course.address` no está disponible. R64 y R70 comprobaron ambos cursos por separado en desktop, tablet y móvil: fallback de ubicación, precio/duración, ROI/salario, valores completos distintos y ausencia de texto crudo `null`/`undefined`. La ruta de datos del caso bloquea requests de navegador fuera del runtime y responde con fixtures sintéticos.

R63 quedó preservado como fallo del test: la captura ya mostraba `Por confirmar`, pero la assertion comparaba `Ubicación` con regex sensible a mayúsculas mientras el estilo la presenta en versales. El ajuste mínimo fue añadir el modificador `i`; R64 pasó 3/3. No fue un fallo del producto.

## Diagnóstico de los ensayos del runtime

| Ensayo | Resultado | Causa y tratamiento |
|---|---|---|
| R63 | 0/3, test FAIL | Harness: assertion sensible a mayúsculas; las tres capturas ya muestran el fallback. Se conserva rojo y se corrige la assertion para comparar sin distinguir mayúsculas. |
| R64 | H3-UAT-064 3/3 PASS | Confirmó la corrección en tres viewports; 6 aserciones por viewport, capturas guardadas. |
| R65 | H3-UAT-049 0/3, FAIL antes de assertions | Configuración de test: el build apuntaba a `127.0.0.1:3361`, runtime escuchaba en `3371`; `ERR_CONNECTION_REFUSED`. Se conserva la corrida, cero retries. |
| R66 | H3-UAT-049 0/3, FAIL antes de las assertions | Se alineó el proxy en 3361, pero el runtime todavía servía el build que solo tenía `mock/mock-course`; la navegación a `ulima/analitica-aplicada-60000000` no tenía página estática y expiró esperando el heading de detalle. |
| R68 | H3-UAT-049 0/3 en el gate global; 26/26 assertions por viewport | El recorrido funcional pasó; la corrida seguía fallando por console errors 404 al prefetchar las 14 rutas sintéticas que el build no generó. |
| R69 build + R70 | Build 33/33 páginas; 17 rutas estáticas; R70 6/6 PASS | El fixture de build aislado refleja las 16 rutas públicas sintéticas del PG17 y la ruta `mock/mock-course` de H3-UAT-064. El runtime y el proxy usan el mismo puerto sintético que quedó compilado en el bundle. |

No se atribuyeron R65/R66/R68 a defectos del producto. Se conservaron las matrices/ejecuciones de cada corrida y no se aumentaron retries. El productor del build R69 usó `env -i`, una API sintética y un fixture unido solo a `127.0.0.1`; no leyó `.env*` ni tuvo acceso a servicios remotos.

## Build y artefactos R69

- Build aislado desde la copia de fuentes/dependencias dentro de `studiamatch-dev`, sin tocar `/app/web/out` ni el runtime Windows activo.
- Next.js 16.3.8, `npm run build`, exit 0; generó 33/33 páginas y las 17 rutas del fixture sintético.
- 206 archivos exportados; manifiesto `compare-build-r69/normal-out-r69.sha256` SHA-256 `5f50efc76f69e55b71c5a853d3c42f66910145eb87a9a999c606d9a7834c5274`, todos los hashes revalidados. Bundle y manifiesto conservados bajo `compare-build-r69/normal-out-r69/` y el directorio `compare-build-r69/`.
- R67 había salido del build con éxito, pero un postflight auxiliar dio exit 127 porque `rg` no está instalado en `studiamatch-dev`. R69 reemplazó ese postflight por `test -f`, `find` y `sha256sum -c`, todo PASS. El error auxiliar se conserva separado del exit 0 del build.

## Evidencia R64/R70

- R64 matrix: `h3req1_g09_uat_2026-10-10_r4/uat-compare-missing-location-r64/h3-expanded-uat-matrix.json`.
- R70 matrix y artefactos: `h3req1_g09_uat_2026-10-10_r4/uat-compare-and-pipeline-r70/`.
- Capturas R70: H3-UAT-049 y H3-UAT-064 en desktop/tablet/mobile; hashes en `h3-expanded-uat-artifact-hashes.json`.
- Vídeo de recorrido integrado H3-UAT-049 desktop: original excluido del paquete público y preservado localmente; su ruta y SHA-256 históricos constan en [la nota de sanitización visual R19](h3req1_visual_evidence_redaction_2026-10-18_r19.md#inventario-local-de-originales).
- Las corridas R63/R65/R66/R68 permanecen preservadas y no se cuentan como PASS.

## G08 y estado de G09

El pytest completo vigente terminó **335 passed, 4 skipped, 1 warning** en `studiamatch-dev`, con el proceso iniciado mediante `env -i` y `PYTHON_DOTENV_DISABLED=1`. El log es `h3req1_g08_delta_r70/pytest-r70.log`. Los dos nuevos tests de recuperación de pipeline están incluidos; los skips siguen siendo NO-EJECUTADOS, no PASS. `CompareContent.tsx` pasó ESLint focal y `tsc --noEmit`; el build R69 recompiló el componente. Node syntax del runner/fixture y el scan focal de credenciales también pasaron. El scan no imprimió valores y quedó en `h3req1_g08_delta_r70/credential-scan-r70.log`.

Los inputs de acción/workflow, ShellCheck, H2 writer scan, npm audit y suites no afectadas no cambiaron; se reutiliza la evidencia G08 previa mientras sus pins coincidan. No se ejecutaron pruebas con credenciales, cuentas/correos reales, APIs live, CI remoto ni escrituras remotas.

LOCAL-05 pasa su pendiente específico y puede marcarse **completo para la comparación del catálogo actual**. LOCAL-04, 11, 15, 18 y 21 conservan su subalcance completo. Las demás áreas LOCAL siguen parciales; G09 no cierra y no cambia el tablero: G01–G10 80% (8/10), cierre local G01–G09 88,89% (8/9). G10 remoto permanece separado.

Los runtimes R69 temporales fueron detenidos por PID verificado; sus puertos internos quedaron libres. Se preservaron R12, PG17 sintético, `studiamatch-dev`, el proxy loopback, el checkout original y el resto de recursos preexistentes.
