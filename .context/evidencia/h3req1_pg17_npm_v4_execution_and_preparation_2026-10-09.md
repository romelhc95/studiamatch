# Resultados PG17 V2, npm V3 y preparación del runner npm V4 — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Invocaciones recientes

| Objetivo | Aprobación y consumo | Resultado real sanitizado | Lectura del gate |
|---|---|---|---|
| Harness editorial en PG17 fijado | Aprobación recibida para `H3REQ1-EDITORIAL-ATOMICITY-PG17-VERSION-CLASSIFIER-V2-ONCE-20261009-V1`, JIT SHA `8b491649c945983e01df7b0ca8b3bee3e23cf5aad0438961ce73c1623d3f7b19`; runner SHA `0292c231da0c379312152471d5f455103d6399985c2aef0fc839f81d08294d6a`. Invocación consumida. | `preflight=OK`, `pg17-version-parser-synthetic=OK`, `pg17-start=OK`, `pg17-ready=OK`, `sql-harness=OK`, `container-cleanup=OK`. La fase del harness solo se marca OK tras el marcador exacto `h3_pg17_harness_ok`. El resultado almacenado no contiene exit numérico. | PASS parcial de versión, parser, harness fijado y cleanup. No cierra G01 completo, la integración Edge/PostgREST ni el candidato. No se suma porcentaje. |
| Auditoría npm clasificada V3 | Aprobación recibida para `H3REQ1-CANDIDATE-V3-NPM-AUDIT-CLASSIFIER-V3-ONCE-20261009-V1`, JIT SHA `d1bacad0aa0281aabb3e8bd1c04598cc99330770aadf79eb86eaf3960e55d3db`; runner SHA aprobado `fbfca9919a41ee7eda8c5d8d2574cd94d21726544c682597193d32b01ab64aa4`. Invocación consumida. | Exit 1; `capture-synthetic-tests=OK`, `image-preflight=OK`, `synthetic-tests=TESTS_FAILED`. No ocurrió request `npm audit`, no hubo egress al registry y la etapa se detuvo antes del timeout de 150 s. | FAIL del runner/sintéticos. No es un fallo del producto, registry, imagen o Docker. Sin retry ni nueva aprobación reutilizada. |

## Diagnóstico mínimo del fallo npm

El contenedor monta el directorio allowlisted como `/h3-audit`. El runner consumido invocó
`/h3-audit/test_audit_candidate_v3_v2.py` y, después, habría invocado
`/h3-audit/audit_candidate_v3_v2.py`. Ambos paths no existen. Los dos archivos presentes en el
directorio fijado se llaman `test_audit_candidate_v3_v3.py` y `audit_candidate_v3_v3.py`; el
test V3 importa por nombre el clasificador V3. El error de Python queda oculto intencionalmente
por `2>/dev/null` y el wrapper lo convierte en el código sanitizado `TESTS_FAILED`.

Esta discrepancia entre nombre de archivos y rutas invocadas explica de forma reproducible el
FAIL antes de npm. La inspección local confirmó que existen ambos nombres V3, que los nombres V2
no aparecen ya en el runner corregido, y `bash -n` pasó. Se conserva byte por byte el runner
consumido en
[`runner V3 ejecutado`](h3req1_candidate_npm_audit_classifier_v3_runner_consumed_2026-10-09.sh)
(SHA-256 `fbfca9919a41ee7eda8c5d8d2574cd94d21726544c682597193d32b01ab64aa4`). La corrección
mínima cambia solo esas dos rutas; no cambia clasificación, inputs, permisos, aislamiento,
egress, timeout o política de fallo cerrado.

## Revisión y validación de la corrección

- Rutas del clasificador y de pruebas comparadas contra el inventario allowlisted: PASS.
- El wrapper mantiene sus seis casos de captura; la invocación V3 los ejecutó con PASS.
- Los 16 sintéticos del clasificador fallaron al no poder abrir el filename V2 inexistente;
  no se afirma que sus aserciones funcionales hayan fallado.
- `bash -n` del runner corregido: PASS.
- Comprobación de existencia de ambos paths V3 y ausencia de referencias a filenames V2 en el
  runner: PASS.
- No se ejecutaron los sintéticos Python en el host ni se usó Docker fuera del JIT consumido.
  Para verificar el runner corregido en la imagen fijada hace falta una aprobación nueva.

El paquete de una invocación nueva es
[`JIT npm V4`](../operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v4_once_2026-10-09.md).
JIT SHA-256 `e2f998052709087268ff65ef971beeb6ca26dd50b18ecd4ab4b43436f57594a6`;
runner SHA-256 `2df6da2fe4617e87bc10a93f1ceb6ffd3c80b54bac918b6092aa5eac3beaa27a`. Requiere
aprobación concreta antes de ejecutar.

## Métrica y siguiente etapa

G01 continúa 0/10; G02 conserva 10/10 por el corte separado C03 SQL v3 41/41; G03 continúa 0/10;
G04–G10 continúan 0/10. Total **10%**, delta **0 puntos**. PG17/npm audit, corrección del runner,
sintaxis y evidencia no cierran por sí solos un gate. No hay `GO_LOCAL_PR` ni
`GO_DEVELOPMENT_REAL`.

Siguientes acciones concretas: solicitar una única autorización para el JIT npm V4; mientras
tanto, terminar la revisión estática del dispatcher Docker de cutover reversible ya aprobado en
objetivo pero consumido con rollback; continuar la preparación CI independiente. La integración
de producto, aceptación, UAT 144, onboarding separado 10/10 y enforcement remoto siguen sin
acreditarse.

## Resultado de la autorización npm V4 — 2026-10-09

El usuario aprobó una invocación de `H3REQ1-CANDIDATE-V3-NPM-AUDIT-CLASSIFIER-V3-FIXED-PATHS-V4-ONCE-20261009-V1`,
JIT SHA-256 `e2f998052709087268ff65ef971beeb6ca26dd50b18ecd4ab4b43436f57594a6`; runner SHA
`2df6da2fe4617e87bc10a93f1ceb6ffd3c80b54bac918b6092aa5eac3beaa27a`. Se ejecutó una sola vez
en PTY Ubuntu WSL como `romel` no-root. Exit 1:

```text
phase=capture-synthetic-tests|error_code=OK
phase=image-preflight|error_code=OK
phase=synthetic-tests|error_code=OK
phase=npm-audit|error_code=EMPTY_STDOUT_STDERR_PRESENT
```

Las seis pruebas Bash y los 16 sintéticos de la imagen pasaron. La fase final solo se emite
después de invocar el clasificador de `npm audit --json`. El clasificador detectó stdout vacío,
stderr no vacío y ninguna línea de código npm reconocida por su allowlist. El stderr crudo se
descartó. No se obtuvo JSON de auditoría. Esta salida no determina si el registry recibió la
solicitud o respondió, ni clasifica causa de red/servicio. La autorización quedó consumida; no
se repite ni se cambian dependencias o lockfile.

El fallo no detiene el cutover Docker V4 aprobado, que es una operación local separada; no
equivale a aprobar un release ni cierra CI. El JIT npm V4 no tocó `studiamatch-dev` ni alteró
recursos Docker persistentes.

# Resultado cutover Docker V4 — detenido por preflight WIP — 2026-10-09

La aprobación humana del JIT `H3REQ1-DOCKER-CANDIDATE-CUTOVER-V4-ONCE-20261009-V1`, SHA-256
`4753244a0eacc25714455c9d0053e58de05b7d9bad64c7cb8c97a60ce39ac56f`, se consumió en una
invocación PTY única como usuario WSL no-root. Runner SHA
`1ed4151492ebf0b599ce7644d89a9fe1031f116a3351a5c3823c556bd43be6a6`; override SHA
`b05df1ada0dae130284e9f97ddb1c9c4780276140e1d7d0dafe31bf0931e8290`.

Resultado real: exit 1, solo `phase=candidate-wip|error_code=STATUS_DRIFT`. El estado antes del
runner fue 55 rutas tracked, 267 untracked, 0 staged. El runner creó el log sanitizado
`.context/evidencia/h3req1_docker_candidate_cutover_v4_once_2026-10-09.log` antes de contar;
`.gitignore` excluye `*.log`, así que el conteo no subió. El preflight exigía 55/268/0 y se detuvo.
La secuencia del ejecutable confirma que esta salida ocurre antes de comprobar pins o llamar
Docker; no hubo build, cutover, cleanup, ni cambio a contenedores, redes, imágenes o volúmenes.

La autorización está consumida y no se repite. El siguiente paquete debe fijar el WIP real y
separar su log ignorado del conteo; se pedirá autorización nueva para la misma operación
protegida. G01–G10 no cambian: total 10%, delta 0.

## Preparación cutover Docker V5 — corrección de WIP ignorado — 2026-10-09

V15 y sus continuaciones no tienen JIT vigente: el diagnóstico V1 se consumió por
`PHASE_ORDER_MISMATCH`; la continuación V2 se consumió por `INTERACTIVE_TTY_REQUIRED`; V8 no dejó
salida recuperable. No se repiten.

El único delta ejecutable Docker V5 frente al V4 consumido es el nombre de su archivo de salida
sanitizada. Mantiene el conteo `55/268/0`: el JIT V5 nuevo es untracked en
`.context/operaciones` y eleva el estado de 267 a 268; el log `*.log` está ignorado y no cambia
el conteo. Runner SHA `a36a06f976c835a38796fb68e165e24ede3ed2de583443ad79d0f1644d775ba0`;
JIT SHA `b5c38e3e149402ab46dec17b1c49ff5b18d5a5a6495a631ed79a229148209b73`. La sintaxis,
alineación de hashes, identidad, orden rollback/health/cleanup y scope de 11 contenedores/3 redes
pasan revisión mecánica. La aprobación V4 no se reutiliza; V5 requiere aprobación nueva.

En CI, el patch PWI V4 conserva su SHA `68bb4037f665c4e82c91b89faae939a20ab90cebbf85cff0b4a2f90b19682c26` y sigue siendo de 4 rutas, 485 inserciones y 1 eliminación. Smoke directo 5/5, regresión shell y compilación de fuentes permanecen como evidencia previa porque el patch/input no cambió. La suite oficial pytest no corre sin esa dependencia; no se instala en host. `actionlint` y `shellcheck` no están disponibles en la sesión. No se ejecutaron pruebas en Docker ni se publicó/configuró el control. G10 permanece 0/10.

# H3REQ1 — actualización viva de resultados y entorno — 2026-10-09

## Identidad, WIP y alcance

Checkout candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
Estado Git resumido: 55 rutas tracked modificadas, 268 entradas untracked, 0 staged.
Checkout original `/home/romel/src/studiamatch`, rama
`feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`;
39 tracked modificados, 39 entradas untracked, 0 staged. Ambos WIP quedan preservados.
No se leyeron ni imprimieron secretos.

## Invocaciones recientes

| Objetivo | Aprobación y consumo | Resultado real | Consecuencia |
|---|---|---|---|
| Harness editorial PG17 | Aprobación recibida para `H3REQ1-EDITORIAL-ATOMICITY-PG17-VERSION-CLASSIFIER-V2-ONCE-20261009-V1`, JIT SHA `8b491649c945983e01df7b0ca8b3bee3e23cf5aad0438961ce73c1623d3f7b19`; runner SHA `0292c231da0c379312152471d5f455103d6399985c2aef0fc839f81d08294d6a`. Consumida. | `preflight`, sintéticos de versión, inicio PG17, readiness, `sql-harness` y cleanup: `OK`. El marcador exacto `h3_pg17_harness_ok` fue observado. No se conservó el exit numérico. | PASS parcial del harness editorial fijado. No cierra G01, G07 ni C03 integrado. No suma porcentaje. |
| npm audit classifier V3 | Aprobación recibida para `H3REQ1-CANDIDATE-V3-NPM-AUDIT-CLASSIFIER-V3-ONCE-20261009-V1`, JIT SHA `d1bacad0aa0281aabb3e8bd1c04598cc99330770aadf79eb86eaf3960e55d3db`; runner aprobado SHA `fbfca9919a41ee7eda8c5d8d2574cd94d21726544c682597193d32b01ab64aa4`. Consumida. | Exit 1: captura sintética y preflight de imagen `OK`; sintéticos Python `TESTS_FAILED`. No hubo acceso al registry. | Causa demostrada: el wrapper llamaba nombres `_v2.py`; el mount allowlisted contiene archivos `_v3.py`. Se conserva el ejecutable consumido byte por byte; la corrección cambia solo esos dos paths. |
| V15 / lectura Tmpfs sintética | Las invocaciones V15 y split-pair V7 ya están consumidas. JIT de reducción V8 `f286b7c916fb434d7f55afa6d8bb0104df4d9bd52d382e061fe2570f1438477d` aprobado y consumido administrativamente. | V15 registró `{NanoCpus, HostConfig.Mounts}`; V7 pasó cuatro sintéticos y falló en `INSPECT_TEMPLATE_TMPFS_EVALUATION_ERROR`. De V8 no quedó phase/exit observable ni se pudo recuperar salida. | No repetir V7/V8. El residual Tmpfs y la composición final siguen sin diagnóstico verificable. No se leyó F1 ni se ejecutó r9. Una continuación necesita paquete y aprobación nuevos. |
| Docker candidate V3 | JIT `62ee72e2a4d6027b360234ee48bdbe1d63ee936931ad13d9169def1bda43b98e` aprobado y consumido. | Build/smoke de imagen V3 `PASS`; cutover `FAIL` por `.env.local` ausente en candidato; rollback del contenedor original `PASS`; cleanup histórico no alcanzado. | Imagen local preservada; no afirmar que exista runtime candidato activo. V4 reutiliza la imagen y referencia el `.env.local` existente del checkout original sin leer/copiar/imprimir sus valores. |

## SQL reconciliado

Se volvió a comparar directamente cada ruta de la tabla “Cierre transitivo del candidato —
SHA-256” de `manifiesto_jit_h3_close03_safe_resume_pg17_2026-10-05_v3.md` contra el
checkout: **41/41 coinciden, 0 ausentes y 0 deltas**. No se ejecutó SQL en esta comparación.
El PASS histórico C03 safe-suspend/resume continúa aplicando a esos bytes exactos; no acredita
el drill integrado. `tests/sql/h3_pg17_harness.sql` no pertenece a esas 41 rutas. Su ejecución
PG17 recién consumida queda registrada aparte y no se usa para ampliar ese PASS.

El corte C02 v4 no-C03 previo era 69/72: entre los tres deltas se encuentran el harness
editorial, `.github/workflows/security-audit.yml` y `web/functions/_lib/admin-bff.ts`. El
harness editorial tiene ahora el PASS parcial PG17 descrito arriba. Los otros dos deltas y la
cobertura afectada siguen pendientes; no se repiten suites SQL/wire cuyos inputs coinciden.

## Entorno Docker, lectura puntual

- `studiamatch-dev`, ID
  `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`: estado
  `restarting`, exit 1, restart count 91 en esta lectura, imagen `studiamatch-dev:local`,
  image ID `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`,
  política `unless-stopped`. Mounts: bind del checkout original a `/app` y volumen
  `studiamatch_node_modules` en `/app/web/node_modules`.
- `studiamatch-node-deps`, ID
  `20f9f5a75ebce7fb7f890f50577a00edb8fb29f0c15b928bffd3f08414c21e16`, `exited`, imagen
  `studiamatch-dev:local`.
- La imagen candidata local `studiamatch-h3req1:20261009-v3` sigue presente con ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
  `studiamatch_h3req1_node_modules`, `studiamatch-h3req1_default` y el provisionador candidato
  no existen en la lectura actual. El volumen original existe y se preserva.
- La causa observada anteriormente para el guard de manifests sigue demostrada para aquel
  startup, pero no se atribuyen los reinicios actuales solo a ella; tampoco se concluye que
  Docker esté defectuoso. No se cambió configuración Docker ni se hizo rebuild en esta lectura.

## Correcciones y paquetes listos

- Runner npm corregido: solo las dos rutas `_v2.py` cambiaron a `_v3.py`; SHA actual
  `2df6da2fe4617e87bc10a93f1ceb6ffd3c80b54bac918b6092aa5eac3beaa27a`. `bash -n`, existencia
  de archivos y pins de package/lock: PASS. No se repitieron sus sintéticos ni se llamó npm.
  JIT nuevo para una ejecución: SHA
  `e2f998052709087268ff65ef971beeb6ca26dd50b18ecd4ab4b43436f57594a6`.
- Cutover Docker V4: imagen V3 local, sin build/pull; healthcheck y rollback fijados; cleanup
  condicionado a health PASS de 11 IDs y tres redes vacías exactas. Conserva contenedor original
  de rollback, runtime R4, seis volúmenes, imágenes y dos redes R4; no usa prune ni borra
  volúmenes. `bash -n`, `git diff --check` y revisión mecánica de orden, identidad, condiciones,
  rollback y targets exactos: PASS. Runner SHA
  `1ed4151492ebf0b599ce7644d89a9fe1031f116a3351a5c3823c556bd43be6a6`; JIT SHA
  `4753244a0eacc25714455c9d0053e58de05b7d9bad64c7cb8c97a60ce39ac56f`. No se ejecutó el
  cutover V4.
- El patch CI independiente sigue preparado, sin publicación/configuración remota ni prueba de
  enforcement. La evidencia del patch y su revisión permanecen en sus archivos vigentes.

## Gates y siguiente acción

G01 0/10; G02 10/10 por el subgate SQL C03 exacto; G03–G10 0/10. Total **10%**, delta
0 puntos. PG17, sintéticos, manifests, revisión estática y preparación documental no se suman
como gates adicionales. No hay `GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` ni D01–D14.

En ese corte se debía pedir autorización agrupada para npm V4 y cutover Docker V4. Ambas se
recibieron: npm terminó consumido con `EMPTY_STDOUT_STDERR_PRESENT`; Docker V4 se consumió antes
de Docker con `candidate-wip/STATUS_DRIFT`. El estado vigente y el paquete V5 corregido se
registran arriba. CI continúa en preparación local. Las invocaciones V7/V8 del residual Tmpfs no
se reutilizan. r9, copia íntegra, Pages/workerd, Edge/PG17/PostgREST, C03 integrado, cuatro
ajustes, UAT 144 y onboarding separado 10/10 siguen pendientes.
