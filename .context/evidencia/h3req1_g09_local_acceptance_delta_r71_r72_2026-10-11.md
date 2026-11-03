# H3REQ1 G09 delta R71–R72 — 2026-10-11

## Candidato, alcance y resultado

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD baseline: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Se añadió el caso canónico H3-UAT-065 a `tests/h3_local_uat.mjs` para probar
  deep links de detalle generados en el build normal para cinco instituciones.
- El caso obtiene datos solo de fixtures REST interceptados por Playwright;
  las demás solicitudes no locales se bloquean antes de llegar a la red. No
  consulta PostgreSQL ni servicios externos ni usa identidad/secretos reales.
- Pages/workerd Miniflare sirvió el export normal R69; Chromium 1228 corrió
  headless dentro del contenedor UAT, sin ventana. El runtime escuchó en
  `127.0.0.1:3370` dentro del contenedor, sin puerto publicado.
- H3-UAT-065 R72: **PASS, 3/3 ejecuciones, 69/69 aserciones, cero errores de
  consola, cero requests fallidos y cero retries**. Cada viewport visitó cinco
  rutas, produjo 20 respuestas REST sintéticas y comprobó curso/institución,
  URL y ausencia de `null`/`undefined`. No se solicitaron recursos externos no
  REST.

## Revisión y tratamiento de R71

R71 pasó 3/3, pero la revisión del runner encontró que la aserción sobre bloqueo
de requests externos usaba una condición constante. Se preservan matriz, hashes
y capturas R71 como antecedente y no se cuentan como evidencia final. El cambio
mínimo reemplazó esa condición por `blockedExternalOrigins.size === 0`; R72
repitió solo H3-UAT-065 en una carpeta distinta y pasó. Ningún fallo de R71
se atribuyó al producto.

## Fixture sintético

| Institución | Curso | Ruta verificada |
|---|---|---|
| Universidad de Lima | Programa local H3 11 | `/courses/ulima/programa-local-h3-11/` |
| Pontificia Universidad Católica del Perú | Programa local H3 12 | `/courses/pucp/programa-local-h3-12/` |
| Universidad Peruana de Ciencias Aplicadas | Programa local H3 13 | `/courses/upc/programa-local-h3-13/` |
| Universidad San Ignacio de Loyola | Programa local H3 14 | `/courses/usil/programa-local-h3-14/` |
| Universidad Tecnológica del Perú | Programa local H3 15 | `/courses/utp/programa-local-h3-15/` |

Los cursos llevan UUID, categoría, precio, modalidad, duración, descripción,
requisitos, salario y retorno sintéticos. Cada identidad de institución se
mantiene separada. R72 ejercitó las rutas desktop 1440×900, tablet 768×1024 y
móvil 390×844.

## Evidencia revisable

- Matriz: `h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/h3-expanded-uat-matrix.json`
  — SHA-256 `73f5b8be1a3f28b26447f09ad07756a1fa39cd0bb5f5241265f1396ca1932c4d`.
- Manifiesto: `h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/h3-expanded-uat-manifest.json`
  — SHA-256 `f84b6a4b5dc3b1e817b87d1b91d75f12e0eeeed0c9c18d2ca3f2aa8daf075637`.
- Hashes de artefactos:
  `h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/h3-expanded-uat-artifact-hashes.json`
  — SHA-256 `34de2b80802502d8f743b43400e3afaf6f6d92c80567fe974187c9b543f894e8`.
- [Desktop](h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/H3-UAT-065-desktop.png)
  — SHA-256 `838d8b9536d7eb17713b64948f1db5b57fe5b25696c0b959d8ef2aba3b3d9513`.
- [Tablet](h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/H3-UAT-065-tablet.png)
  — SHA-256 `507c04c83243e2d24f5fc9ef52ef5c65b1fc291119e0134c0b3a008d0417b15b`.
- [Móvil](h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/H3-UAT-065-mobile.png)
  — SHA-256 `76e119a1c11483c8638a1a709ddcacfc7e1583c7a393498ad5302fd5004bece3`.
- Exit: `h3req1_g09_uat_r72_exit.txt` = `0`; resumen: `h3req1_g09_uat_r72_stdout.json`.
- Captura auxiliar de credenciales para el runner:
  `credential-scan-r72.log` = `credential scan passed`; `node --check` pasó.

## Servidor, acceso Windows y recursos

- Ensayo R72: Pages/workerd con el export normal R69, Miniflare; datos REST
  sintéticos, sin PG17 ni escrituras. Playwright Chromium 1228, headless.
- Acceso Windows preexistente continúa en `http://localhost:3336/`, detrás del
  proxy loopback R47 hacia app/datos R12. No se recreó ni cambió para R72.
- El runtime R72 se detuvo al terminar; su directorio Durable Object temporal
  fue retirado por el manejador exacto del proceso. R12, PostgreSQL sintético,
  proxy loopback, `studiamatch-dev`, checkout original y recursos ajenos quedaron
  intactos.
- R71/R72 no cambian el resultado de G08: el full pytest 335/4 skips, TypeScript,
  ESLint, builds, scanner/writer scan y auditorías vigentes ya están registrados.
  `node --check` y el scanner focal del runner sí se renovaron tras el cambio.

## Impacto en LOCAL-01..23 y gates

R72 amplía LOCAL-02/03/16 con navegación directa por instituciones. Sigue
pendiente ampliar datos por estados/eligibilidad/assets y cotejar una identidad
única PG17 a través de build y runtime. El caso no cubre las otras brechas
funcionales de la matriz ni reemplaza las 189 selecciones previas.

El catálogo actual queda en 65 casos × 3 viewports y 195 combinaciones PASS
seleccionadas entre ejecuciones: 189 previas, R70 añade H3-UAT-064 (3/3), renueva
H3-UAT-049 en sustitución de R30 y R72 añade H3-UAT-065 (3/3). No fue una sola
corrida completa. LOCAL-05 sigue completo en su contrato; las áreas
LOCAL-01..03, 06..10, 12..14, 16..17, 19..20 y 22..23 mantienen pendientes
ejecutables en la matriz. G09 sigue parcial. Métricas sin cambio: 80% histórico
(8/10) y 88,89% cierre local (8/9); G10 remoto sigue separado.
