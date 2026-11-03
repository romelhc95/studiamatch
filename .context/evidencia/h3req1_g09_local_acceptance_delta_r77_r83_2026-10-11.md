# Delta de aceptación G09 R77–R83 — 2026-10-11

## Candidato y entorno

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD baseline: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`; los resultados se atan también al WIP.
- App integrada: contenedor `h3req1-g09-uat-app-20261010-r12`, imagen `studiamatch-h3req1:20261009-v3`; Pages/workerd local en `http://localhost:3330/`, mock local `:3331`, perímetro `:3332`.
- Datos: base PG17 sintética `h3_final_uat_g09_20261010_r12`; Postgres 17.11; fixture mock local. Consultas de inventario solo lectura. R83 reseteó el fixture sintético por viewport mediante el contrato del runner.
- Browser: Playwright/Chromium 1228, headless dentro del contenedor Docker, sin ventana visible. Requests y datos de prueba locales; no se accedió a correo, cuentas, secretos ni servicios remotos.
- El test modificado `tests/h3_local_uat.mjs` quedó con SHA-256 `b66881fe0eb6883802d1fbfd7d616160c7f69607d8cf98e92c9de060c4dfa521`, igual en el checkout montado `/app` al preflight de R83.

## Resultados ejecutados

| Corte | Selección | Resultado | Evidencia y alcance |
|---|---|---|---|
| R77 | H3-UAT-056, canal de asesoría cerrado | PASS 3/3; 3 capturas; retries 0 | `uat-functional-focused-r77-t03/`; la acción de contacto permanece cerrada, no aparecen formulario/captura y no se emite escritura externa. El CTA “Solicitar Info” de R30 sigue siendo enlace interno al detalle del mismo curso. |
| R78 | H3-UAT-043/046/048/057/058/065 | PASS 18/18; 18 capturas; retries 0 | `uat-functional-focused-r78-navigation-accessibility/`; cinco rutas públicas 200, recursos/login estables, primer foco de teclado en control interactivo, nombres accesibles básicos, ruta desconocida 404 controlada, 5 rutas sintéticas de institución y sin overflow. |
| R79 | H3-UAT-063, diez muestras independientes | PASS 30/30 viewports, 10 ejecuciones del caso, retries 0 | `uat-performance-r79/sample-01..10/`; cada recorrido home→detalle→back→forward registra checkpoints; Chromium 1228 headless, R12. P50/P95 de duración del recorrido: desktop 4345/4577 ms, tablet 4017/4147 ms, móvil 3772/4033 ms. P50/P95 DCL: 240/268, 86/147 y 71/96 ms respectivamente; load: 363/402, 216/333 y 205/349 ms. Diez repeticiones descriptivas, no SLA. |
| R80 | Primera ampliación de H3-UAT-017 | FAIL; 0/3; retries 0 | Evidencia roja preservada en `uat-admin-queue-r80/`. Supuestos del test no distinguían paginación omitida en un resultado filtrado de controles deshabilitados; el conteo se actualizaba antes de que la consulta de filas terminara. |
| R81 | Corrección de espera inicial | FAIL; 0/3; retries 0 | `uat-admin-queue-r81/`; la captura muestra 9 filas Borrador/Pendiente. El viewport móvil llegó a `rate_limited` del Auth mock porque esta variante omitió el reset de fixture. El runner debe restaurar el fixture sintético por viewport para estos logins/MFA. |
| R82 | Captura de conteo/filas | FAIL; 0/3; retries 0 | `uat-admin-queue-r82/`; conteo persistido 26, filtro compuesto 9, pero la locator accesible no encontró enlaces a ese instante. Captura posterior conserva la lista filtrada visible. Se corrigió la espera/locator y se restauró el reset sintético por viewport; los tres cortes rojos permanecen. |
| R83 | H3-UAT-017, paginación/estado/filtros | PASS 3/3; 63 aserciones; 3 capturas; 1 vídeo desktop; retries 0 | `uat-admin-queue-r83/`; total 26, página inicial 20, página final 6, páginas sin solapamiento y orden inicial restaurado, estado Borrador+Pendiente devuelve 9 filas, paginación se oculta para una sola página y reset repone total/página inicial. Sin errores de consola ni requests fallidos. |

R83 es una sola corrida del caso en desktop/tablet/móvil. R79 son diez muestras independientes solicitadas para describir variación; cada corrida tuvo cero retries. R80–R82 no se mezclan con PASS.

## Inventario sintético PG17 leído después de R83

Consultas agregadas no identificantes, read-only:

| Relación | Filas |
|---|---:|
| `courses` | 31 |
| `course_editorial_state` | 31 |
| `course_editorial_audit` | 406 |
| `admin_members` | 15 |
| `admin_membership_audit` | 58 |
| `admin_invitations` | 24 |
| Cola por estado/calidad | `draft/complete=1`, `draft/pending=9`, `published/complete=16` |

La primera consulta de desglose usó una expresión agregada mal puesta en `GROUP BY` y terminó con error SQL de lectura; no mutó datos. La consulta corregida y los conteos base terminaron correctamente. Esto no es una falla del producto. R83 corrobora la combinación de 9 filas en UI, pero LOCAL-01 sigue parcial: falta conciliar cada estrato con consumidores/detalle y estados elegibles.

## INV-008 y navegación del browser

La investigación y R8 demostraron un defecto del guard de aplicación tras aceptar invitación: la sesión `password_pending` enviaba `/admin/` a `/admin/login/`, y el login devolvía la sesión a `/admin/`. El fix en `web/src/app/admin/login/page.tsx` deriva a setup de contraseña y el caso de invitación comprueba que el panel no quede accesible antes de completarla. R8 pasa onboarding 10/10, sin retries, con diez capturas y vídeo; el rojo R6 permanece. R8 no se repitió en este delta porque su runner ejecuta el conjunto completo y sus inputs no cambiaron.

Esto es distinto al rojo R49 de back/forward: el navegador regresó a la ruta `/`, respuesta 200, pero el test esperaba el título antes de restaurarse el catálogo. La ruta incorporó `networkidle` y checkpoints. R53/R54/R55 previos y las diez muestras R79 pasaron; el rojo R49 se conserva como sincronización del test y no se atribuye al producto.

## Reconciliación de áreas

- LOCAL-06 queda completo para el comportamiento vigente: captura asesoría cerrada, CTA interno R30 y cero escrituras externas R77.
- LOCAL-12/G09-T07 queda completo para el fixture actual: R83 valida conteo, ventana ordenada, cursor sin duplicados, filtro combinado, reset y presentación en tres viewports.
- LOCAL-22/G09-T14 queda completo para medición descriptiva local: diez muestras por recorrido con p50/p95, baseline R53–R55 n=3 preservado y sin declarar SLA. Los resultados no generalizan a producción.
- LOCAL-01 avanza con conteos/estratos; queda parcial por la conciliación completa entre filas PG17, assets y consumidores.
- LOCAL-02/03/20 avanzan por R78, pero siguen parciales: aún faltan los estados de error/vacío sistemáticos, teclado/dialog/foco y contraste.
- LOCAL-09, 13, 14, 16, 17 y 19 permanecen parciales por expiración/refresh browser, matriz editor/auditoría, contenido-preview, cache/rebuild público, negativos integrados/revisión y recuperación de fallos.

G08 continúa completo; G09 sigue parcial. Las métricas no cambian: histórico G01–G10 8/10 = 80%; cierre local G01–G09 8/9 = 88,89%. No hay GO local. No se ejecutó test live/cloud, promoción, PR, merge o deploy.

## Evidencia visual

- Capturas R77: `uat-functional-focused-r77-t03/H3-UAT-056-{desktop,tablet,mobile}.png`.
- Capturas R78: `uat-functional-focused-r78-navigation-accessibility/H3-UAT-{043,046,048,057,058,065}-{desktop,tablet,mobile}.png`.
- R79: `uat-performance-r79/sample-01..10/H3-UAT-063-{desktop,tablet,mobile}.png`.
- R83: `uat-admin-queue-r83/H3-UAT-017-{desktop,tablet,mobile}.png`; vídeo revisable `uat-admin-queue-r83/H3-UAT-017-desktop.webm` (SHA-256 `240fef273389164c283fe06fcc55ab4162fc426508f489c40bd047121eca31d2`).
- Resúmenes R83: `uat-admin-queue-r83/h3-expanded-uat-matrix.json` y `uat-admin-queue-r83/h3-expanded-uat-executions.json`.
