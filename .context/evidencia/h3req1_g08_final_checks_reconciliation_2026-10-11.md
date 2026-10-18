# H3REQ1 G08 — checks finales del candidato — 2026-10-11

## Delta vigente R159–R176 — revalidación del candidato actual

Esta sección supersede los conteos de 335/336 de los cortes anteriores. Rama y
HEAD base permanecen `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el candidato incluye su WIP
identificado. En este delta no cambió código funcional web ni dependencias; se
modificaron el harness sintético PostgREST/credenciales y el runner UAT.

| Check | Resultado vigente | Evidencia / límite |
|---|---|---|
| Pytest del proyecto | R160: **337 passed, 4 skipped, 1 warning**, exit 0. | Docker `studiamatch-dev`, imagen local fijada; selector `tests/test_*.py`, `env -i`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONPATH=/app/scripts/core`. Log `h3req1_g08_current_pytest_r160.log`, `.exit`. Los skips y warning PyPDF2 se declaran, no se cuentan como PASS. |
| Contrato de credenciales | R159: 45/45 PASS, exit 0. | `h3req1_g08_credentials_contract_r159_focused.log`, `.exit`; cliente de harness con identidad sintética explícita y AST que fija Bearer al proxy local allowlisted. |
| Credential scan | R159 y R168/R169 PASS para sus inputs; R174–R176 renuevan historia, worktree, índice, symlinks y nombres de variables sensibles. | R174 prueba `history=5`; R175 prueba archivos tracked unstaged, índice, traversal de padres symlink y redacción; R176 prueba cuatro asignaciones opacas. 72 contratos Python relacionados y ShellCheck pasan en Docker. Evidencia [R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [R175](h3req1_g08_credential_tree_symlink_r175_2026-10-11.md), [R176](h3req1_g08_scanner_named_credentials_ci_allowlist_2026-10-11.md). No se imprimen valores. |
| Pipeline PG17/PostgREST | R161: exit 0. | `.context/evidencia/h3req1_g09_pipeline_postgrest_r161/run-r10.log`; discovery checkpoint/resume, handoff, recovery sintética 503 de cleansing/enrichment/sync y fila final persistida. Se usa como G09/LOCAL-07/08/19 además del check G08 del harness. |
| Sanitizer de UAT | R162: 16/16 PASS, exit 0. | `h3req1_g09_sanitizer_r162.log`, `.exit` e `.inputs.sha256`; hashes actuales coinciden. |
| Sintaxis y scan de UAT | R168/R169: PASS para sus runners fijados. R171–R173 renovaron `node --check` y credential scan en Docker; el input actual es SHA `04d00dc0…dd60f`. | R168/R169 fijaron el runner previo `6c9fe406…`; sus hashes no se presentan como idénticos al WIP actual. R173 acredita sintaxis/scan actuales y las pruebas afectadas 002/003 después de cerrar el finding LOW de query string. Inputs R168/R169/R171/R172/R173 quedan preservados por separado; evidencia del precheck R173: [`h3req1_g08_final_r173_runner_precheck.log`](h3req1_g08_final_r173_runner_precheck.log). |
| Auditorías npm | PASS, 0 vulnerabilidades full/prod; package/lock actuales conservan sus hashes fijados. | R7 `inputs-r7.txt`, `npm-audit-r7.log`; `web/package.json` y `web/package-lock.json` coinciden con `dfdd9a7e…` y `d526163c…`. Registry restringido a npm, retries 0, sin tarballs ni instalación en esta continuación. |
| ESLint, Next typegen/TypeScript, writer scan, static build normal/mock | PASS conservado por inputs compatibles. | Evidencia histórica G08 enlazada debajo. R146 normal export verifica 201/201 y fuente web 61/61 en R162; R69/R143 registran compilación completa y sus rutas/páginas. No cambió TypeScript/JavaScript funcional ni dependencias de aplicación; no se repitieron suites intactas. |
| Workflow / actionlint | R176: **PASS**, actionlint 1.7.7, exit 0 en `security-audit.yml`, `protected-workflow-integrity.yml` y `db-sync-to-pro.yml`; pip install usa lock con hashes. | El binario oficial local se validó con `tools.sha256`; análisis en contenedor efímero `--pull=never --network=none --read-only`, workflows read-only. El comando usa `requirements-pipeline.txt` con `--require-hashes`; no se ejecutó el workflow ni CI remoto. |
| Credential scan final R6 | **PASS**, exit 0, 854 paths únicos en 11 lotes: 679 tracked, 28 untracked propuestos, 145 evidencias y manifest/cuerpo R6, deduplicados. Se repite después de la reconciliación documental R6 de la matriz; el conjunto de rutas y su conteo no cambian. La enumeración de paths UTF-8 usa `git -c core.quotePath=false ls-files -z`. | `studiamatch-dev`, imagen local `studiamatch-h3req1:20261009-v3`; scanner por paths explícitos, salida sanitizada. |

G08 continúa completo para los checks locales aplicables. Las pruebas live y
con credenciales reales están NO-EJECUTADAS; CI/G10 remoto no se usa para
declarar enforcement.

### Delta R174 — scanner de historia Git — 2026-10-11

Una revisión independiente detectó que `--diff` podía aceptar un valor
credential-like presente en un commit intermedio si había sido eliminado o
saneado antes de HEAD. El caso se reprodujo en un fixture Git sintético, el
scanner se corrigió para revisar todos los blobs cambiados de cada commit
nuevo, y el hook materializa el árbol vacío en la primera publicación.
R174 pasó cinco escenarios de historia (lineal, empty-tree, root, merge y
pre-push con OID remoto nulo), 70 contratos Python relacionados y ShellCheck
v0.11.0. Los cambios exactos pasaron credential scan sin revelar valores.
La revisión independiente posterior no encontró HIGH/MEDIUM en el delta.
El costo del primer push sin base remota se documenta como no medido; no se
limita el DAG ni se omiten commits para reducirlo. La invocación completa de
`--tree` del candidato dentro de `studiamatch-dev` no alcanzó Git porque ese
contenedor no tiene montado el `.git` administrativo del worktree; la suite
R174 prueba esos modos en un repo aislado, y el scan completo anterior R159
conserva su alcance original. Detalle y límites en
[evidencia R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md).

R170–R173 (delta del test email): R170 terminó exit 1 al simular la ausencia de
email; las aserciones previas de sesión/rol pasaron, pero `route.fetch()` en la
interceptación recibió HTTP 403 del BFF y no alcanzó el fallback. Se corrigió
solo el test para tomar primero la sesión autenticada desde el `fetch` del
navegador y servir una respuesta local sintética con `email: null`. R171 ejecutó
los dos casos afectados en 6/6 viewports, 30/30 assertions, seis capturas y
cero retries. La revisión encontró un LOW porque la intercepción admitía query
strings; R173 limitó a GET del mismo origen loopback, path exacto y query vacía,
y renovó 6/6 viewports, 36/36 assertions, seis capturas y cero retries, además
de `node --check` y credential scan en Docker. R172 se conserva pero no prueba
el hash actual. Todas las corridas, inputs y el rojo R170 están en
[R170–R173](h3req1_g09_email_fallback_r170_r171_2026-10-11.md). Ningún archivo
funcional web ni dependencia cambió por este delta.

### Delta R175–R176 — cobertura de scanner, workflow y LOCAL-17

R175 detectó y corrigió un hueco de `--tree`: el contenido unstaged del
worktree quedaba sin inspeccionar. Se añade lector seguro por componentes con
`O_NOFOLLOW`, rechazo cerrado de traversal por padres symlink y pruebas que
separan worktree, índice y enlaces finales. La suite focal reportó
`tree=6|history=5|io-failures=4|concurrent=2|redaction=PASS`.

R176 añade patrones para asignaciones opacas a nombres de credenciales,
redacción de valores y allowlist en ambas capas para el helper y
`.githooks/pre-push`. Se reprodujo en rojo el comando de instalación CI sin
pins; después el workflow usó el lock existente `requirements-pipeline.txt`
con `--require-hashes`. En Docker, `tests/test_security_flow.py`,
`tests/test_supabase_credentials_contract.py` y
`tests/test_protected_workflow_review.py` terminó **72 passed**; ShellCheck
0.11.0 y actionlint 1.7.7 pasaron. Actionlint valida tres workflows locales,
no acredita ejecución ni enforcement remoto.

El escaneo histórico cubrió 679 paths tracked. Un escaneo explícito previo
cubrió 229 paths únicos de scope/evidencia; R5 renovará esa selección tras
incluir el presente informe. El contenedor `studiamatch-dev` no tiene montado
el `.git` administrativo, así que `--tree` completo no se declara PASS allí;
los modos se prueban en repositorios sintéticos y los paths candidatos se
escanean explícitamente. Los intentos de actionlint con binario no instalado,
tmpfs no ejecutable y cwd incorrecto fallaron antes del análisis; la
invocación corregida con asset fijado terminó exit 0. No se descargaron
dependencias ni se ejecutó CI remoto.

## Corte histórico R70 — comprobaciones del candidato tras LOCAL-05

Esta sección supersede el conteo pytest 333 del corte R58 descrito más abajo.
La rama/HEAD siguen siendo `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el HEAD no identifica el WIP.

| Check del delta | Comando/inputs | Resultado y evidencia |
|---|---|---|
| Pytest del proyecto | En `studiamatch-dev`: `env -i`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONPATH=/app/scripts/core`, `/opt/venv/bin/python -m pytest -q -p no:cacheprovider tests/test_*.py`. | Exit 0: **335 passed, 4 skipped, 1 warning** (PyPDF2). Log `h3req1_g08_delta_r70/pytest-r70.log`, SHA-256 `5d0154269669cb37c95ef1319df58b5c49e7734b733831368b6f14300335ff72`. No se cargó `.env*` en el entorno de pytest; los skips quedan NO-EJECUTADOS. |
| ESLint / TypeScript | `./node_modules/.bin/eslint src/app/compare/CompareContent.tsx`; `NODE_OPTIONS=--max-old-space-size=3072 ./node_modules/.bin/tsc --noEmit --pretty false`, dentro de `/app/web` en Docker. | Ambos exit 0 con el hash vigente de `CompareContent.tsx` (`635c4a6c…ea10b3b`). El resto de ESLint/TS continúa cubierto por la corrida G08 y sus inputs compatibles. |
| Runner y credential scan | `node --check` para `tests/h3_local_uat.mjs` y el fixture estático R69; `scripts/security/scan_credentials.sh` sobre `CompareContent.tsx`, runner UAT y fixture R69. | Exit 0, `credential scan passed`; log `h3req1_g08_delta_r70/credential-scan-r70.log`, SHA-256 `c907c408226ecdd488273b9af102a9201a0efaf17a8d58788658a67652ca1396`. |
| Build normal | `npm run build` en copia aislada del candidato, Next 16.3.8; API synthetic bound a `127.0.0.1`, `env -i`, sin tocar `/app/web/out`. | Exit 0, **33/33 páginas**, 17 rutas sintéticas, 206 archivos con todos los hashes verificados. Log `h3req1_g09_uat_2026-10-10_r4/compare-build-r69/normal-build-r69.log`; manifest `normal-out-r69.sha256`, SHA-256 `5f50efc76f69e55b71c5a853d3c42f66910145eb87a9a999c606d9a7834c5274`. |
| UAT afectada | H3-UAT-049 y 064, tres viewports, Pages/workerd/Miniflare y PG17 local sintético, Chromium 1228 headless. | R70 exit 0: 6/6 viewports PASS, 96/96 assertions, cero console errors/failed requests/retries, seis PNG y un vídeo. Matriz R70 SHA-256 `c608aea62f7e50eb927893efabe0ed0c77b12d8443a40c4282427b386acc700c`. Detalle en [delta R64–R70](h3req1_g09_local_acceptance_delta_r64_r70_2026-10-11.md). |

Actionlint, ShellCheck, workflow protegido, scope guard, H2 writer scan, auditorías npm, contrato de credenciales, AST Python y builds previos se reutilizan por inputs compatibles o quedan renovados por las referencias siguientes. No se ejecutaron pruebas con credenciales, cuentas/correos reales, APIs live, CI remoto ni escrituras remotas. G08 permanece completo; este delta no cambia la métrica de gates.

## Identidad del candidato

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD base: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- El HEAD no identifica el WIP. El inventario de inputs de código probado es
  `h3req1_g08_candidate_final_2026-10-11_r1/source-inputs-r4.sha256`:
  1.067 archivos, SHA-256
  `30d1a237323c3d68049dc194a37393fc01359f8a135ec15400db4a419a4522c0`.
  La verificación de R6 cotejó snapshot y checkout contra el manifiesto sin
  diferencias. El snapshot no contiene `.env*` operativo ni symlinks.
- WIP registrado durante esta conciliación: 60 rutas tracked modificadas,
  789 entradas untracked agregadas por directorio y 0 staged. Los resultados,
  runners y artefactos de evidencia se conservan; no se ejecutó limpieza.
- Docker: imagen local `studiamatch-h3req1:20261009-v3`, ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`;
  volumen de dependencias `h3req1-g08-web-node-modules-r1`, digest
  `ea36c13c72f0b1c13f2791118b4eb7ad89c17ba9ecbce44d413b794e6837e625`.

## Resultados ejecutados o reutilizados por inputs compatibles

| Check | Resultado | Evidencia / límites |
|---|---|---|
| Pytest del proyecto | Histórico R58: 333 passed, 4 skipped, 1 warning. Delta vigente R70: 335 passed, 4 skipped, 1 warning. | R58 y R70 ejecutados con el glob vigente `tests/test_*.py` dentro de Docker; el delta R70 suma las dos pruebas de recuperación nuevas. Los skips no se cuentan como PASS. Warning PyPDF2. |
| Contrato de credenciales Supabase | PASS, 43/43 | `.../supabase-credentials-contract-r4.log`. |
| Scanner de credenciales | Sintéticos PASS; scan del candidato PASS | `.../credential-scanner-synthetic-r4.log` y `.../credential-scanner-candidate-r4.log`. No se imprimieron secretos. |
| Escritores H2 | PASS | `.../h2-writer-scan-r4.log`. |
| Python syntax | PASS, 176 archivos `.py` de `scripts/` y `tests/` parseados como AST dentro del contenedor fijado | `.../python-ast-r4.log`; comprobación de sintaxis, no ejecución de esos 176 módulos. |
| ESLint | PASS, exit 0, 0 errores y 9 warnings conocidos | `.../eslint-r4.log`. |
| Next typegen y TypeScript | PASS | `.../next-typegen-r4.log`, `.../typescript-r4.log`; 4 GiB para el contenedor y heap Node 3.072 MiB. |
| actionlint, ShellCheck, workflow protegido, scanner y scope guard | PASS reutilizado con pins de inputs coincidentes | `.context/evidencia/h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v5.txt` acredita `ALL_PENDING_CHECKS_OK`, y `.context/evidencia/h3req1_g03_r9_v7_execution_2026-10-10.txt` acredita actionlint con hashes coincidentes y ShellCheck PASS. TypeScript de V7 no se reutiliza; el resultado vigente es R4. La matriz G03 del estado registra los checks aplicables. |
| npm audit full y production | PASS, 0 vulnerabilidades en ambos alcances | `.context/evidencia/h3req1_g08_npm_audit_2026-10-10_r7/output/npm-audit-r7.log`; package `dfdd9a7e…ab2` y lock `d526163c…34db` coinciden con el checkout. Registry limitado a npm, retries 0, sin tarballs. |
| Static build mock | PASS reutilizado: rutas mock esperadas y manifest del artefacto verificado | `.context/evidencia/h3req1_g08_final_2026-10-10_r3/mock-build-r5.log`; 126 archivos. Los hashes actuales de `web/package.json` y `web/package-lock.json` coinciden con los de auditoría/build registrados. |
| Static build normal | PASS, contenedor build exit 0, 17/17 páginas, 126 archivos | `h3req1_g08_candidate_final_2026-10-11_r1/normal-build-r6-output/`. El smoke usó PostgREST sintético y generó las rutas pública y de detalle del curso `Curso Legacy Visible`. El manifest de salida tiene SHA-256 `61f0b5d50acc2f0fc65a0c1058a00b27a51c976d636ac9544413edc151f94299`. |

### Conciliación del build normal R6

El contenedor del build y el smoke terminaron con exit 0. La salida estática
fue re-verificada: home y detalle contienen el curso sintético, el fallback no
aparece y los 126 archivos pasan SHA-256. El proxy allowlist permitió 13
solicitudes, rechazó 2 y registró 0 fallos upstream; el build solo tuvo red
interna y utilizó el proxy acotado para fuentes. El preflight sintético del
montaje directo confirmó Next 16.3.8. R5 fue un fallo real del runner de
dependencias: Turbopack rechazó el symlink exterior a la raíz. R6 corrigió el
layout con el volumen montado directamente en `web/node_modules`; un build
sintético aislado reprodujo y pasó ese layout antes del build de candidato.

El wrapper R6 terminó con exit 1 únicamente en su última comprobación porque
la regex esperaba `phase=font-proxy|…`, mientras el registro emite
`phase=font-proxy-summary|…`. No afectó el exit del contenedor ni el artefacto.
La reconciliación read-only con parser correcto terminó exit 0 y acredita
salida, hash, cleanup exacto y preservación de servicios en
`normal-build-r6-postflight-reconciliation.log`. El intento inicial de esa
reconciliación se conserva como fallo de su propio selector, seguido por la
corrección de una sola línea y el PASS final.

Recursos temporales R6: build y proxy retirados por ID exacto; las dos redes
temporales quedaron vacías y fueron retiradas. `studiamatch-dev` no se tocó.
R12/R8 siguieron activos y `http://127.0.0.1:3333/` / `:3334/` devolvieron
HTTP 200 en el postflight.

## Límites

- Cuatro pruebas Python quedaron skipped; no se reclaman como aprobadas.
- No se ejecutaron pruebas que requieran credenciales, cuentas reales, servicios
  cloud, live API o writes remotos. No hubo CI remoto, PR, deploy ni promoción.
- El mock build, PostgreSQL y PostgREST sintéticos no acreditan producción.
- Esto cierra G08 del candidato local; no cierra G09 de aceptación ni G10 remoto.

## Resultado

G08 **completo** para los checks locales aplicables al inventario de candidato
indicado arriba. El tablero histórico pasa de 70% a 80% (8/10 gates completos);
el cierre local pasa de 7/9 = 77,78% a 8/9 = 88,89%. G09 permanece parcial y
no se declara GO local mientras falte aceptación funcional.

### Delta de G08 R58 — 2026-10-11

El archivo `tests/test_h3req1_local_pipeline_walk.py` añadió únicamente dos
pruebas sintéticas de recuperación para `paginated_catalog` y
`catalog_link_extraction`; ambas pasaron en Docker (2 passed) y la suite del
proyecto vigente terminó 333 passed/4 skipped. `tests/h3_local_uat.mjs` recibió
diagnóstico sanitizado del 403 en H3-UAT-050 y el filtro soportado para UUID en
H3-UAT-055; `node --check` en `studiamatch-dev`/R12 y el scanner de credenciales
en ambos runners pasaron. ESLint, TypeScript, builds, audits y workflow inputs
no cambiaron por este delta y se conservan por compatibilidad de inputs.

La invocación exploratoria `pytest /app/tests` exit 2 se detuvo en colección
por el mismo módulo `test_diagnostic_once.py` en dos carpetas JIT. No ejecutó
tests. No es el selector G08 del proyecto: el runner versionado usa
`tests/test_*.py`, que excluye paquetes one-shot anidados y terminó PASS.
