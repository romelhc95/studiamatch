# Continuación H3REQ1 — V15, Docker, SQL y CI — 2026-10-09

## Corte previo a las invocaciones V7 y Docker V3 — histórico — 10% — 2026-10-09

### Reconciliación anterior a las autorizaciones V7/Docker

La rama/HEAD y WIP continúan en `feat/h3req1-sync-20261002`,
`4eb4d877a50b012bb630a129bd0c74482c33be9c`, `55/239/0`. El contenedor
`studiamatch-dev` continúa `restarting` (RestartCount 2502), usa `studiamatch-dev:local`,
el bind del checkout original y el volumen persistente `studiamatch_node_modules`.

Lecturas Docker de solo lectura copiaron únicamente el marcador de manifests, los dos
manifests desde el bind y el marcador/metadata de una dependencia a un directorio temporal,
que se eliminó al terminar. La salida conservada fue solo clasificación sanitizada:
bind=original `OK`; imagen-vs-bind `MISMATCH`; candidato-vs-imagen `MISMATCH`;
marcador-de-volumen-vs-imagen `OK`; versión instalada de `braces` distinta del pin del
candidato. Esto confirma un desfase activo del guard de inicio; el volumen coincide con la
imagen antigua. No explica por sí solo todos los reinicios anteriores ni demuestra corrupción
de Docker. No se modificó ningún contenedor, imagen, volumen o red.

El usuario concedió una aprobación adicional para el JIT V15 V2 SHA
`49243bda140af6038d3e93ed9a2d4d8b19b2206c54a7ac4648f2ab93d5904703`; quedó sin ejecutar porque
ese paquete ya tenía una invocación consumida con `PHASE_ORDER_MISMATCH` y la reducción ya
había informado el par sintético. No reintenté los 52 probes. El parser V3 corrige el prefijo
contra el orden real de llamadas y sus siete casos locales pasan; no lee F1.

Validaciones adicionales de este corte: el checker mecánico del dispatcher V3 pasó derivación,
identidad exacta del paquete, sintaxis, orden, rollback y targets (11 contenedores/5 redes).
El shell regression de `protected-path-scope` pasó; el módulo `protected_workflow_review.py`
compila en memoria. La suite oficial `pytest` no pudo iniciar (`No module named pytest`); no se
instaló dependencia ni se alteró Docker. No se ejecutó CI remoto.

En ese corte los gates eran total `10%`, delta `0`; G02 `10/10`; G01 y G03–G10 `0/10`;
D01–D14 `0/14`. Las aprobaciones e invocaciones posteriores se registran abajo.

Revisión focal CI V4: el patch aislado carga workflow y helper desde la rama default (`main`)
y no ejecuta el head del PR. El draft WIP del checkout es otro artefacto: hace checkout del
helper desde `github.event.pull_request.base.sha`. Esa diferencia se conservó; solo se añadió
`edited` al draft para reevaluar retarget explícito, mientras que el patch ya incluía ese evento.
La comparación mecánica confirmó que el resto del workflow coincide al normalizar la referencia
y el comentario. Se actualizó el paquete para distinguir ambas fuentes. La revisión estática del
patch no acredita el run/status real ni la evaluación de policy; G10 sigue abierto.

### Identidad, WIP y resultado de las autorizaciones

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
WIP actual 55 tracked modificados, 239 entradas untracked, 0 staged. Checkout original
`/home/romel/src/studiamatch`, rama `feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`, WIP 39/39/0, sin cambios.

El usuario aprobó el JIT V15 TTY V2 SHA
`49243bda140af6038d3e93ed9a2d4d8b19b2206c54a7ac4648f2ab93d5904703`; una invocación
terminó con `phase=f1-v15-output-capture|error_code=PHASE_ORDER_MISMATCH`, exit 1. El helper
valida el artefacto previo sin emitir esa secuencia; el wrapper esperaba un prefijo que no
existe. No llegó a F1 ni r9 y no se reintenta. Se conserva el resultado anterior de V15 que
redujo el error del fixture a `{NanoCpus, HostConfig.Mounts}`; no se repiten sus probes.

### Corrección mínima y pruebas parciales

V7 conserva las otras 23 expresiones juntas; lee `NanoCpus` y `HostConfig.Mounts` de forma
aislada y recompone la secuencia original en memoria. El formato y las salidas malformadas,
con controles o fuera de tamaño se rechazan de forma cerrada. No es diagnóstico de producto
ni de defecto del motor.

Resultados locales, separados de gates de runtime:

| Check | Resultado | Límite |
|---|---|---|
| Pruebas V7 del par, llamadas directamente desde el host | PASS 4/4 | Composición, mapas presentes/ausentes, negativos y restauración. No invoca Docker. |
| Parser V15 output contract V3 | PASS 7/7 | Sintéticos locales; el nuevo JIT V15 V3 no se ejecutó. |
| `bash -n` de wrapper F1 V7 y dispatcher Docker V3 | PASS | Sintaxis únicamente. |
| Checker mecánico Docker V3 | PASS | Runner byte-idéntico al paquete, derivación V2 exacta, pins, orden/condiciones/rollback, 11 IDs/5 redes exactos, WIP `55/239/0`. |
| Preflight de manifests R9 | PASS 68/68 + 3 artefactos del paquete, 0 desajustes | Integridad de inputs solamente; r9 no ejecutado. La imagen r9 fijada aún tiene el marcador de dependencias de manifests antiguos. |
| Lectura/ejecución F1 | Pendiente | No invocada. |
| Docker build/cutover/cleanup V3 | Pendiente | No invocados. |

Revisión estática directa de V7: los índices 15 y 24 y sus expresiones son exactos; el
residuo tiene 23 campos; la composición conserva el orden; errores del helper no se imprimen;
el wrapper exige rama/HEAD, hashes, usuario no-root y TTY, filtra solo fase/código y falla
antes de r9. Los temporales usan imagen local por digest, sin pull, red, rootfs writable,
privilegios, credenciales o volúmenes; IDs completos aleatorios y `--rm`, stop explícito. No
se encontraron hallazgos bloqueantes en esta revisión estática focal. No es review runtime
ni un scan completo Codex Security.

El JIT F1-only V7, SHA-256
`a602ee00fe5168cab2216c92799154801903fad84627d3e204e8461411e30cfd`, solicita una
invocación PTY no-root en Ubuntu WSL: sintéticos y una clasificación del snapshot histórico
F1 mediante tres `docker inspect` de solo lectura. No inspecciona ni manipula el contenedor
`studiamatch-dev`. No incluye r9: el dispatcher vigente fija una imagen con hashes internos
de `package.json`/lock distintos del candidato, por lo que el gate de dependencias fallaría
antes de lint/typecheck. Se preparará r9 contra el digest real de la imagen V3 luego de
rebuild y health PASS.

### Docker activo y simplificación

Lectura acotada del ID conocido de `studiamatch-dev`: `restarting`, RestartCount 2502,
imagen `studiamatch-dev:local`, restart policy `unless-stopped`; bind al checkout original
`/home/romel/src/studiamatch:/app` y volumen persistente
`studiamatch_node_modules:/app/web/node_modules`. No se hizo mutation Docker.

El rebuild/cutover V2 quedó consumido por `npm ci` exit 254: el contexto omitió el paquete
local `web/vendor/braces-3.0.4-h3.1.tgz`. V3 incluye el tarball con hash fijado en el contexto
allowlisted y en `COPY` antes de `npm ci`; el lock y package no cambian. Dispatcher V3 SHA
`de178b3621bcb89d38a7e7528bd746516fe569f2a2e659645d11932253e63b2c`; paquete V3 SHA
`62ee72e2a4d6027b360234ee48bdbe1d63ee936931ad13d9169def1bda43b98e`. Revisión mecánica
PASS. Incluye build con egress predeterminado sin allowlist; lista destinos esperados y el
riesgo de egress adicional de lifecycle scripts. Usa tag nuevo y rollback por identidad; la
limpieza queda detrás de health PASS y de 11 IDs/cinco redes exactos. Preserva volúmenes,
imágenes, runtime R4 fallido, evidencia y rollback. No se ejecutó; requiere autorización
agrupada nueva porque V2 está consumido.

### Reconciliación SQL, integrado y matriz de aceptación

- C03 SQL safe-suspend/resume v3: relectura del manifiesto y comparación actual de sus 41
  rutas, 41/41 PASS, 0 ausentes/0 cambiadas. Es evidencia del subgate SQL histórico; aquí no
  se ejecutó SQL ni se cierra el drill integrado.
- C03 integrado: el manifiesto actual declara 62 rutas; 60 coinciden y dos tienen delta:
  `tests/h3req1_c03_integrated_runtime.mjs` y `web/functions/_lib/admin-bff.ts`. Renovar
  esas coberturas después de reconstrucción y health; no repetir el conjunto intacto.
- C02 PG17 v4: el corte reconciliado vigente es 69/72. Los tres deltas son
  `tests/sql/h3_pg17_harness.sql`, `.github/workflows/security-audit.yml` y
  `web/functions/_lib/admin-bff.ts`; G01 permanece abierto.

| Ajuste | Inputs/casos vigentes | Pruebas anteriores preservadas | Resultado actual | Siguiente acción |
|---|---|---|---|---|
| Edición Admin/procedencia | `admin_update_course`, editor/BFF, recarga, origen, override, restore por `null`, conflicto de versión, límites Admin/user. | Harness editorial y contratos/UAT 2026-10-01. | Sin defecto demostrado; sin ejecución actual. | Renovar casos afectados en PG17, contrato y UAT al tener runtime. |
| Auditoría | Actor `auth.uid()`, fecha, before/after atómicos, historial protegido/append-only, denegación de acceso directo. | Assertions PG17 iniciales; el C03 SQL 41/41 no prueba la auditoría editorial. | Harness `h3_pg17_harness.sql` cambió; no ejecutado. | Incluir aserciones afectadas en PG17+C03 integrado con prueba de atomicidad y roles. |
| Disponibilidad | HTTPS/observed/valid-until, día 90 inclusivo, >90, ausente/inválida/vencida y `unknown` legacy. | Contratos y harness anteriores. | Implementación inicial PASS; sin revalidación. | Renovar únicamente bordes afectados y comprobar no regresión de legacy/publicación. |
| Correo autenticado | `auth.getUser()` vía BFF, fallback/error, rol admin/user y vista desktop/mobile sin PII. | Contrato/header y UAT iniciales. | No se corrió visual/UAT actual. | Probar ambos roles tras Pages/workerd con capturas sanitizadas. |

BFF/HttpOnly, MFA, roles, gateway, cuotas y cuenta existente se conservan. No reinvitar,
resetear, usar tokens accesibles desde JS ni tomar el informe histórico como HIGH actual.
UAT 144 sin retry, onboarding 10/10 separado, seis pilares, revisión de cliente y
`expand → compatibilidad → deploy → contract`/rollback siguen pendientes.

### CI y gates

Patch Protected Workflow Integrity V4, SHA-256
`68bb4037f665c4e82c91b89faae939a20ab90cebbf85cff0b4a2f90b19682c26`; aplicación aislada,
smoke directo de 5 casos y regression shell pasan. Pytest oficial no se ejecutó porque no
está instalado. GitHub Actions Policies no tiene políticas según la captura ya revisada;
Pages Production es `main`, include `*`, exclude vacío. No se publicó, instaló, requirió ni
probó el control remoto; el YAML no acredita enforcement.

| Gate | Completo | Parcial conservado |
|---|---:|---|
| G01 SQL/wire/editorial | 0/10 | C02 69/72; cobertura nueva del harness editorial pendiente. |
| G02 suspensión SQL | 10/10 | C03 SQL v3 41/41 rutas actuales. |
| G03 tooling | 0/10 | Pruebas sintéticas locales; r9 no ejecutado. |
| G04 F1 | 0/10 | Par mínimo sintético; F1 no leído. |
| G05 copia | 0/10 | No ejecutada. |
| G06 arranque Pages/workerd | 0/10 | No ejecutado. |
| G07 Edge/PG17/PostgREST y C03 integrado | 0/10 | Manifiesto integrado 60/62; sin nuevo runtime. |
| G08 checks | 0/10 | Sin checks finales Docker. |
| G09 aceptación | 0/10 | UAT/onboarding/visual/revisión pendientes. |
| G10 CI | 0/10 | Patch estático; sin enforcement remoto. |
| **Total** | **10%** | **Delta 0 puntos**. |

No hay GO: `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL` son NO-GO; D01–D14 0/14. Publicación
CI/settings, SQL, push/PR/merge y deploy Development requieren instrucciones separadas.
Las dos aprobaciones pendientes se agrupan por objetivo: (1) diagnóstico F1 V7 único; (2)
rebuild/cutover/cleanup V3 con su rollback y gates. No se pide autorización para r9 hasta
pinnear el runtime candidato después del health PASS.

## Delta posterior — parser corregido, dispatcher exacto y revisión completada

Fecha: 2026-10-09. Candidato: rama `feat/h3req1-sync-20261002`, HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; WIP al cierre: 54 rutas tracked modificadas,
235 entradas untracked, 0 staged. No se alteró el checkout original ni se hicieron cambios de
producto, SQL, secretos o Docker.

### Aprobación y ejecución, separadas

| Objetivo | Aprobación/paquete anterior | Resultado real | Estado siguiente |
|---|---|---|---|
| Rebuild/cutover Docker | V1 SHA `0d24ff2fadf0c55ce6d9a1fd5e89e71c2eddba3f15075d2e96406c0d4a367209`, aprobado | Dos despachos rechazados por revisión automática y error JS `BUILD_CONTEXT` ocurrieron antes de Docker. Preflight directo posterior se interrumpió; one-shot considerado consumido. No se capturó exit. Inventario read-only posterior: sin tag/volumen/red/contenedor candidato y sin build/cutover/cleanup acreditados. | V1 no se reusa. Dispatcher V2 SHA `060c87cb4283ca3312746697b551de815ffc7c09b13b49f8816effee361be1ba` preparado y revisado; requiere nueva autorización agrupada. |
| Diagnóstico V15 | JIT V1 SHA `b5f98329415c613f5ab4c96b3d3721db97f56cd60749748eb7eadd56666efe4c`, aprobado | Fixture reprodujo el baseline y la reducción reportó `{nano-cpus, mounts}`. Wrapper exit 1: orden de fase esperado desalineado con el runner; no se alcanzaron F1/r9. Invocación consumida. | Parser/fixture V2 corregidos; JIT SHA `b9b44f70121be8f7ca91471fdd4410767e5c160ab943996c6dee412b40e7af95` requiere autorización nueva y sigue sin ejecutar. |

### Resultado de la nueva autorización V15 y despacho Docker V2

El usuario aprobó una invocación del JIT V15 V2 SHA
`b9b44f70121be8f7ca91471fdd4410767e5c160ab943996c6dee412b40e7af95` y una invocación del
dispatcher Docker V2 SHA `060c87cb4283ca3312746697b551de815ffc7c09b13b49f8816effee361be1ba`.
V15 se intentó primero, con el comando exacto fijado en el paquete. Resultado sanitizado:
`phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED`, exit 1. El proceso se llamó sin TTY
interactivo y el propio preflight salió antes de cualquier llamada Docker; no corrió la suite
sintética, no creó temporal, no leyó F1 ni corrió r9. La autorización V15 queda consumida por
esta invocación fallida; sin retry ni ejecución alternativa bajo el mismo permiso. Acción:
preparar un despacho que exija TTY antes de invocar el runner, comparar mecánicamente el comando
y JIT, revisar de nuevo y solicitar otra autorización.

La autorización Docker V2 se aprobó para una invocación y se consumió al ejecutar el comando
literal del paquete. El preflight confirmó WIP/hashes y construyó el contexto; el build falló.
`npm ci` terminó con exit 254 por `ENOENT` en
`/opt/node-staging/web/vendor/braces-3.0.4-h3.1.tgz`; el runner salió 1 y emitió
`phase=image-build|error_code=COMMAND_FAILED`. `web/package.json` y lockfile refieren
`file:vendor/braces-3.0.4-h3.1.tgz`, y el archivo fuente existe en el checkout con SHA-256
`a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819`. La causa concreta es que
el contexto allowlisted omitió `web/vendor` y el Dockerfile solo copió package manifests al
directorio de npm. El archivo no estaba ausente del checkout ni se ha demostrado corrupción del
lockfile.

Verificación read-only tras FAIL: el tag `studiamatch-h3req1:20261009-v1` está ausente; el
contenedor original conserva ID `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`,
nombre `/studiamatch-dev`, imagen `studiamatch-dev:local`, estado `restarting` y policy
`unless-stopped`; no se alcanzaron cutover, health, rollback ni cleanup. El contexto fallido se
preserva en `/tmp/h3req1-docker-build-v1.kAsIKK`. No hubo retry de Codex ni cambios en el lock,
servicio o Docker. El log reportó un retry interno de npm antes del `ENOENT`; la invocación no se
repitió.

Corrección a preparar para V3: agregar el único tarball `web/vendor/braces-3.0.4-h3.1.tgz` al
contexto con hash fijado y un `COPY` de esa ruta exacta antes de `npm ci`; verificar el `COPY`
con smoke offline, renovar pines y repetir la revisión automática. El nuevo rebuild/cutover/
cleanup requerirá autorización agrupada nueva porque el V2 ya está consumido.

El despacho V2 se guardó como archivo, no como bloques reensamblados en la llamada. El checker
`tests/h3req1_docker_peer_substep_diag/check_docker_candidate_dispatch_v2.py` produjo:
`static_review=PASS`, 8 bloques en orden, ejecutable byte-idéntico al body Bash del paquete,
`bash -n=PASS`, 11 IDs y cinco redes exactos, orden/gates/rollback PASS, WIP `54/235/0`.
Checker SHA `a83f4fe07dc16290d29994a37124e2a15433c4dd18f03d2f822928e1b628a384`; runner SHA
`33ac38a88d62e8f8afb09d27e0e84b2a7a695d3b5685e519f13f5190db7c7baa`.

Revisión automática Codex Security completada, scan
`6e1f513c-aa31-448c-8926-c63e82f0df52`: diff exacto de seis archivos, coverage 6/6,
0 findings reportables. Informe estático; no ejecutó Docker ni verificó rollback runtime.
El endpoint de inventario de review items devolvió cero filas a pesar del diff; se revisaron
manualmente todos los archivos del snapshot, se registraron como cobertura y se cerró el scan.
El `python3 -m pytest -q` intentado en este corte salió 1 (`No module named pytest`); no
instalé paquetes. Los seis casos sintéticos V15 y `bash -n` habían pasado en la preparación
previa; esa evidencia es parcial y no sustituye el resultado del nuevo JIT.

### Entorno y gates

La consulta read-only acotada mantuvo `studiamatch-dev` ID
`115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`, estado `restarting`,
RestartCount observado 2415, imagen `studiamatch-dev:local`, checkout original. No se hizo
build, stop, rename, limpieza, retry ni cambio de daemon. El candidato reconstruido y los
recursos propios siguen ausentes; la causa raíz del restart no se atribuye por analogía.

| Gate | Estado actual | Parcial conservado |
|---|---:|---|
| G01 SQL/wire/editorial | 0/10 | C02 69/72; renovar harness editorial modificado |
| G02 suspensión SQL | 10/10 | C03 SQL v3 41/41, aplicable a inputs revalidados |
| G03 tooling | 0/10 | checker y revisión estática PASS; V15 corregido no ejecutado |
| G04 F1 | 0/10 | `{nano-cpus, mounts}` es diagnóstico sintético; F1 no leído |
| G05 copia, G06 arranque, G07 integración | 0/30 | Sin evidencia nueva |
| G08 checks, G09 aceptación | 0/20 | Sin checks Docker, UAT 144 ni onboarding 10/10 nuevos |
| G10 CI | 0/10 | Patch aislado, no publicado ni exigido; YAML por sí solo no acredita enforcement |
| Total | **10%** | **Delta 0 puntos**; parciales no suman |

`GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL` continúan NO-GO. D01–D14=0/14. La siguiente acción
ejecutable tras aprobación es el V15 sintético corregido y el dispatcher Docker V2 dentro de
sus alcances separados. No se pide permiso por archivo/hash individual; cada pregunta agrupa
un objetivo one-shot completo. Push/PR/merge, cambios de settings, SQL, publicación CI y
despliegue Development requieren aprobación/instrucción independiente.

## Identidad y alcance

| Campo | Resultado |
|---|---|
| Candidato | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama / HEAD | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| WIP del candidato al iniciar este corte / actual | 54 tracked modificados, 232 → 233 entradas untracked, 0 staged |
| Checkout original | `/home/romel/src/studiamatch`, `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`, 39 tracked modificados, 39 untracked, 0 staged |
| Cambios de producto de este corte | Ninguno. Se preparan solo evidencia y JITs; se preservan ambos checkouts y el WIP existente. |
| Estado de cierre recalculado | G01 0/10; G02 10/10; G03–G10 0/10; **10%**. D01–D14 0/14. `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`: NO-GO. |

## V14 y paquete diagnóstico mínimo V15

V14 está consumido y no se repite. Su resultado está en
[V14](h3req1_c03_v14_template_field_interaction_failure_2026-10-09.md), SHA-256
`abf6be735583098f5a196b6d5284438aefcb8329adbd9601a73a6ed728c80940`: 25 expresiones
individuales pasaron en el mapa `present`, mientras el formato combinado dio
`INSPECT_TEMPLATE_EVALUATION_ERROR`. No se ejecutaron el mapa ausente, F1 ni r9. Esto
localiza el problema en la interacción del formato de lectura sintético; no demuestra fallo
del producto ni del motor Docker.

V15 fue aprobado y ejecutado una vez. El baseline exacto se reprodujo en el fixture y el helper
produjo el conjunto 1-minimal `{nano-cpus, mounts}`. Su paquete
[JIT V15](../operaciones/jit_h3req1_docker_desktop_wsl_f1_v15_minimal_subset_diagnostic_once_2026-10-09.md)
reproduce primero el error exacto en el mismo fixture sintético y reduce los campos por
eliminación, con máximo 52 probes únicas y 5 s por probe. Solo puede concluir un conjunto
1-minimal por eliminación si demuestra que quitar cada miembro despeja el error. No afirma
mínimo cardinal global ni selecciona una causa si el error exacto no se reproduce. Esta
invocación no lee F1 ni corre r9.

**Ficha de impacto:** helper, wrapper y pruebas sintéticas bajo
`tests/h3req1_docker_peer_substep_diag/`; consumidores: diagnóstico C03; sin cambios en
producto, SQL/wire, BFF/HttpOnly, MFA, roles, gateway o cuotas. Evidencia V14 y pruebas
históricas preservadas. El fixture nuevo es efímero, sin mounts, volúmenes, red o variables
del host; cleanup se verifica por ID. El JIT usa la imagen existente
`sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, compartida con
`studiamatch-dev:local`, sin inspect/start/stop/rename del contenedor habitual. No equivale
a sustituir el runtime candidato por esa imagen.

Validación local ya ejecutada en la preparación V15:

- `python3 -B f1_template_minimal_failure_v15_once.py --synthetic-only`: PASS, exit 0.
- Cinco casos del test V15 ejecutados directamente, sin pytest: PASS. Cubren reproducción
  exacta del baseline, reducción/minimalidad por eliminación, entrada vacía/sobredimensionada,
  caché de probes y límite de probes.
- `bash -n run_wsl_f1_v15_minimal_subset_diagnostic_once.sh`: PASS.
- Revisión estática independiente final: sin hallazgos bloqueantes; confirmó gates, pines,
  límites de probes/tiempo, sandbox Docker y formato/exit. No ejecutó Docker ni las pruebas.
- Pytest, actionlint y shellcheck no están instalados en el host; no se instalaron.

Pines actuales: helper `05947152fcfb356c1ea8bc0a283eda3c3aad0c94f31e9844083fac2678a0f764`,
test `460a18aef0f391e1a479fbb4ce1cf41f387ea9266c5938e09087904741ddecf4`, wrapper
`765d1abefe11afad133bd7a2b4497c3f084e3cff3cdb7bea06b69b0551e6662d`, JIT
`b5f98329415c613f5ab4c96b3d3721db97f56cd60749748eb7eadd56666efe4c`.

## Docker activo y desfase de manifests

Inventario read-only mínimo del contenedor `studiamatch-dev`:

| Recurso | Identidad / función / persistencia |
|---|---|
| Contenedor | `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`, nombre `studiamatch-dev`; estado `restarting`, RestartCount 2397 al consultar; restart policy `unless-stopped`; Compose project/service `studiamatch/app`; working dir `/app`. |
| Imagen activa | tag `studiamatch-dev:local`, ID `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`. |
| Checkout montado | bind `/home/romel/src/studiamatch` → `/app`; no sirve al candidato actual. |
| Dependencias persistentes | volumen `studiamatch_node_modules` → `/app/web/node_modules`; se preserva. |
| Candidato | No tiene contenedor/volumen propio al consultar. El tag propuesto `studiamatch-h3req1:20261009-v1`, el contenedor `studiamatch-h3req1-node-deps` y volumen `studiamatch_h3req1_node_modules` no existían. |

Runtimes históricos consultados por nombre/ID conocido, no mediante un scan global:

| Recurso | Estado/función | Checkout y persistencia |
|---|---|---|
| `h3req1-node22-jit-20261005` (`8e0a4df5…`) | Exited; imagen Node 22 fijada al digest histórico; runner viejo. | Cuatro binds read-only al candidato, sin volumen; red `bridge`. |
| `h3req1-node22-jit-v2-20261005` (`544616a0…`) | Exited; runner SQL/wire v4. | Cuatro binds read-only al candidato, sin volumen; red interna v4. |
| `h3req1-pg17-jit-v3-20261005` (`51b1967b…`) | Exited; PG17 de intento histórico. | Cuatro binds read-only a SQL/migrations/rollback/seeds; sin volumen, red interna v3. |
| `h3req1-pg17-jit-v4-20261005` (`4e26f117…`) | Exited; PG17 de C02 v4. | Cuatro binds read-only al candidato; sin volumen, red interna v4. |
| `h3req1-postgrest-jit-20261005` (`4cbde5db…`) | Exited; PostgREST v13.0.7 fijado al digest histórico. | Sin mounts/volúmenes; red interna v4. |
| `h3req1-c03-safe-suspend-pg17-20261005` (`88aa68bc…`) | Exited; PG17 de subgate C03. | Tres binds read-only al candidato; sin volumen, network mode `none`. |

El inventario read-only de los nombres exactos del runner C03 integrado R4 encontró cinco
contenedores auxiliares `exited/0` con volúmenes persistentes de esa ejecución: bootstrap
Miniflare `dec76d0a…` (Node 22), bootstrap Pages `8cf1e627…` (Node 22), bootstrap Edge
`d6a26afb…` (Deno 2.1.4), verificador de caches `94ef3d0b…` (Node 22) y snapshot bootstrap
`e5e9cf70…` (Node 22). Sus mounts nombran solo los volúmenes C03 R4/R5 enumerados abajo.
Los contenedores PG17, PostgREST y Edge active/suspended de R4 no existen. El runtime R4
`b8aff877…` terminó `exited/1`, montó esos caches/snapshot y no llegó a PG17: se preserva
porque el healthz no tiene causa raíz demostrada y el contenedor puede contener diagnóstico
recuperable. Las redes `h3req1-c03-integrated-edge-20261006-r4` (`b1f633b4…`) y
`h3req1-c03-integrated-data-20261006-r4` (`da562797…`) están internas y sin endpoints.
El log R4 se conserva en archivo, SHA-256
`208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34`; registra el FAIL de
healthz, no una causa raíz.

Se preservan los seis volúmenes R4: `h3req1-c03-integrated-source-snapshot-20261006-r4`,
`h3req1-c03-integrated-tls-20261006-r4`,
`h3req1-c03-integrated-miniflare-node-modules-20261006-r4`,
`h3req1-c03-integrated-pages-node-modules-20261006-r4`,
`h3req1-c03-integrated-edge-deno-cache-20261006-r5` y
`h3req1-c03-integrated-edge-node-modules-20261006-r5`. Sus etiquetas coinciden con JIT R4 y
manifiesto `e5d72e06…`; no se inspeccionó su contenido. En el grupo histórico anterior, los
PG usaron tmpfs y los runners usaron binds read-only, sin volúmenes persistentes.

Las redes históricas v2, v3 y v4 están `Internal=true` y vacías; el contenedor PG17 v2 no
existe. Los reportes SQL permanecen en sus manifiestos/evidencias. Los contenedores no son
runtime del candidato actual. El JIT Docker SHA-256
`0d24ff2fadf0c55ce6d9a1fd5e89e71c2eddba3f15075d2e96406c0d4a367209` agrupa el rebuild
allowlisted y cutover reversible del studiamatch-dev del candidato con cleanup selectivo.
Tras health PASS valida primero los 11 contenedores y cinco redes completos; compara ID, nombre,
imagen, estado, exit/restart y ausencia de volúmenes de los seis anteriores, además de los mapas
exactos de seis mounts persistentes R4/R5. Solo entonces retira los 11 contenedores sin -v y
las cinco redes exactas. Preserva el runtime R4 fallido y sus seis volúmenes, el rollback,
imágenes/tags, fuentes y evidencia en archivos. El cleanup es condicional al health PASS y no
elimina resultados persistentes.

La revisión de la versión final del JIT confirmó `bash -n` PASS en sus ocho bloques ejecutables y checks estáticos de alcance:
11 IDs únicos de contenedores, cinco redes únicas, los seis mapas completos de mounts R4/R5,
preflight de todos los objetos antes del primer `rm`, errores limitados a fase/código y cero
borrado de volúmenes. El usuario aprobó el JIT (`0d24ff2f…`). Dos despachos anteriores fueron
rechazados por auto-review (bloques transformados e ID mal copiado), y otro falló en JavaScript
antes de ejecutar. La última llamada literal quedó interrumpida durante el preflight; el WIP
actual es `54/233/0`, frente al pin `54/232/0`. Se considera consumida la invocación única y no
se reintenta. No se capturó exit/fase de esa llamada. La lectura posterior confirma que el
contenedor original permanece bajo el ID/nombre/policy esperados, el tag/volumen/red/candidato
siguen ausentes, y no hay contexto de build temporal. No existe evidencia de build, cutover ni
cleanup; no hubo mutación Docker observada. Se requiere un dispatcher estático verificable y
un JIT actualizado con nueva autorización para volver a intentar.


El manifiesto dentro de la imagen fija `web/package.json` en
`7f42e397a859d7d5108f1f17a613e8722493ecfb368c25dd4a12b0e414e7e7bb` y
`web/package-lock.json` en `a6f707e516fbb0d4dc3067b809573b9ac64d8543c54dfe28998cd13901bf4ccf`.
El checkout original contiene respectivamente `ee907a16780a8327fb118cd612bbc47826eed24fc792a202fffb773c58367267`
y `952fb25ffa499e64c7d6811fea4ea1d9d83e7a482c0916da918f7c881ed7ad29`; el candidato,
`4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a` y
`8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc`. Ambos checkouts
difieren de la imagen staged. El marcador anterior del volumen coincide con la imagen, por
lo que el desfase probado está entre fuente bind-mounted e imagen, no entre volumen e imagen.

`init-container.sh` líneas 23–33 compara esos manifests y sale ante diferencia. El usuario
compartió la salida exacta `Node dependency manifests differ from image` /
`source web/package.json or web/package-lock.json hash != staged image hash`; esto demuestra
la condición que causa ese rechazo de init. La consulta actual sigue mostrando Restarting,
pero un filtro de los últimos 1500 logs por esas tres líneas fijas no encontró coincidencia;
no se atribuyen todas las reiniciadas actuales solo a ese texto de log. No hay evidencia de
Docker defectuoso ni motivo para reinstalar.

Base `node:20-bookworm` disponible localmente con ID
`sha256:8f693eaa7e0a8e71560c9a82b55fd54c2ae920a2ba5d2cde28bac7d1c01c9ba5`; Compose 5.5.1.
La validación anterior del override candidate parseó y mostró los nombres/puerto/red sin
resolver env: `studiamatch-dev` (host loopback `127.0.0.1:3000`), servicio one-shot
`studiamatch-h3req1-node-deps`, volumen `studiamatch_h3req1_node_modules` y red
`studiamatch-h3req1_default`. El override limita el one-shot a los dos manifests como binds
read-only y el volumen de deps; no monta el checkout ni `.env.local`. No se construyó, inició,
paró ni modificó ningún recurso. Override SHA-256 actual
`32997839538f071219fe6174f3d20f2a0481ecb25b25e1cc3816f53d19fd48c0`.

Se preparará un rebuild de un tag candidato, con contexto de build allowlisted compuesto solo
por `Dockerfile`, `init-container.sh`, `requirements-pipeline.txt`, `web/package.json` y
`web/package-lock.json`; no se enviará el worktree completo ni `.env*`. El set normal de
`studiamatch-dev` y el stack aislado de integración tendrán usos distintos: no se usarán las
credenciales `.env.local` del contenedor habitual en pruebas aisladas. La reconstrucción,
provisión de volumen, renombre reversible del contenedor original y arranque requieren JIT
agrupado; siguen pendientes.

## Reconciliación SQL contra los manifiestos

Se recalcularon SHA-256 actuales sin ejecutar SQL:

- C03 SQL v3: **41/41** coinciden con el cierre transitivo v3; 0 ausentes, 0 deltas. El
  preflight del 2026-10-05 registra que el harness safe-suspend/resume del JIT C03 v3 terminó
  exit 0. Ese PASS sigue aplicando a esas 41 rutas exactas; no incluye el harness editorial
  `tests/sql/h3_pg17_harness.sql` ni acredita el drill integrado.
- C02 v4 no-C03: **69/72** coinciden, 0 ausentes, 3 deltas. Se excluyeron los dos inputs
  propios de C03 que ya excluía el manifiesto; se aceptaron los dos hashes actualizados por
  v4 para el wrapper payload-bound y su harness. Deltas restantes:
  `tests/sql/h3_pg17_harness.sql` (`e1525daa…` → `8d4ea8d0…`),
  `.github/workflows/security-audit.yml` (`1221ecc1…` → `b285eb49…`) y
  `web/functions/_lib/admin-bff.ts` (`1cb1ad95…` → `829cd9cd…`).

La afirmación previa de C02 **70/72** era incompleta para el harness editorial actual; se
reemplaza por 69/72. El `h3_pg17_harness.sql` actual añade casos para procedencia/overrides,
auditoría, disponibilidad y publicación; esos casos no se ejecutaron. Por tanto **G01 se
reabre (0/10)** hasta ejecutar la cobertura C02 afectada en PG17. El PASS histórico C02 se
conserva para los inputs/runtime intactos; no repetir las suites intactas. El delta BFF se
renueva dentro de G08 y el workflow dentro de G10. **G02 permanece 10/10** por el PASS C03 v3
exacto y sus 41 inputs actuales; esto no cierra C03 integrado. Así, el total recalculado es
**10%**, delta −10 puntos respecto al corte anterior, sin crédito por documentación ni hashes.

## Cuatro criterios, atestación, pilares y aceptación

La matriz ejecutable y los casos de aceptación permanecen en
[la aclaración de origen BFF y ajustes](h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente).
El estado actual de los cuatro es implementación con evidencia inicial del 2026-10-01,
sin defecto funcional demostrado y sin revalidación actual:

1. Edición: procedencia tras recarga, override, restauración por `null`, conflicto obsoleto y
   roles admin/user.
2. Auditoría: actor real, fecha, before/after atómicos, historial protegido/append-only.
3. Disponibilidad: evidencia vigente, límite inclusivo de 90 días, rechazo `>90`, ausencia/
   invalidez/vencimiento fail-closed y compatibilidad `unknown` legacy.
4. Encabezado: correo de `auth.getUser()`, fallback, legibilidad mobile/desktop, roles y sin
   PII en evidencia.

Los runners anteriores se preservan: tests contractuales de editor/cola/MFA, BFF mock, UAT
de invitación, `tests/h3_local_uat.mjs` y harnesses SQL/C03. No hay ejecución UAT actual del
candidato. Se mantienen BFF/HttpOnly, MFA, roles, gateway, cuotas y cuenta existente; no
reinvitar ni resetear. La atestación sanitizada de cliente sigue vigente para ejecución local.
Los seis pilares y `expand → compatibilidad → deploy → contract`/rollback no tienen evidencia
de cierre de este candidato; documentarlos no suma gate. UAT 144/144 sin retries y onboarding
10/10 separado quedan pendientes.

## CI independiente y siguientes gates

El patch Protected Workflow Integrity V3 sigue en artefacto, SHA-256
`4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`, cuatro rutas, revisión
estática `hold_for_evidence`. En una copia temporal del base `4eb4d877…`, `git apply --check`,
aplicación y `git diff --cached --check` acotado a las cuatro rutas del patch dieron PASS. Una
primera comprobación global incluyó whitespace heredado de cientos de archivos ajenos del
base; se descartó ese resultado global y se repitió el check solo sobre las rutas modificadas.
No se ejecutaron actionlint/pytest/Docker para CI; no se publicó, instaló ni configuró y no
existe check remoto efectivo acreditado. Rulesets/capturas recibidos no se repiten.
Preparación local y revisión pueden avanzar; publicación/PR/merge/settings y deploy requieren
instrucción separada. Pages Production `main`, include `*`, exclude vacío; el skip del bootstrap
no se probó en este repo.

| Gate | Estado | Evidencia parcial por separado |
|---|---:|---|
| G01 | 0/10 | C02 histórico se conserva para inputs intactos; harness editorial nuevo pendiente de PG17. |
| G02 | 10/10 | C03 v3 SQL PASS para 41/41 inputs exactos; integrado sigue pendiente. |
| G03–G10 | 0/10 cada uno | V15 sintéticos, C02 69/72, inventory Docker y patch CI son parciales, no cierre. |
| Total | **10%** | Recalculado; G01 reabierto por cobertura SQL/harness nueva aún no ejecutada. |
| D01–D14 | 0/14 | No hubo promoción/despliegue Development. |

Siguiente acción inmediata: aprobación de una sola invocación V15 descrita en su JIT para
obtener la reducción mínima. En paralelo, revisar el JIT de rebuild/cutover local. Tras V15,
corregir solo el predicado demostrado, revisión independiente y pruebas sintéticas de
composición, mapas presente/ausente y negativos. No avanzar a F1/r9/copia/arranque/integración
si una fase falla.

## V7 split-pair: fallo sintético tmpfs — actualización posterior

El usuario aprobó una invocación de `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SPLIT-PAIR-V7-ONCE`,
JIT SHA-256 `a602ee00fe5168cab2216c92799154801903fad84627d3e204e8461411e30cfd`. Se ejecutó
una vez con el comando fijado en PTY Ubuntu WSL como `romel` UID 1000, sin `sudo`:

```text
phase=prior-desktop-wsl-endpoint-attestation|error_code=OK
phase=classifier-synthetic-image-volumes-read|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-unit-tests|error_code=OK
phase=f1-template-synthetic-inspect|error_code=INSPECT_TEMPLATE_TMPFS_EVALUATION_ERROR
exit=1
```

La autorización queda consumida. El runner se detuvo en la primera inspección sintética del
template residual; no ejecutó el caso “maps absent”, no leyó F1, no ejecutó r9 y no tocó
`studiamatch-dev`. La fase de limpieza no reportó error. No se conservó metadata ni stderr
crudos.

El código cerrado atribuye el fallo a la familia `.HostConfig.Tmpfs` del template Go. La
plantilla conservada incluye el lookup protegido de tmpfs y su longitud, dentro de las 23
expresiones que permanecen juntas después de aislar `NanoCpus` y `HostConfig.Mounts`. El
resultado no prueba si falla esa expresión aislada, el valor de tmpfs o su interacción con otra
expresión residual; no se atribuye al producto ni a Docker defectuoso. El próximo diagnóstico
debe aislar sintéticamente esa expresión/combinación, mantener salida cerrada y tener pruebas
sintéticas/revisión antes de un JIT nuevo. V7 no se repite.

En forma independiente, el usuario aprobó una invocación del dispatcher Docker V3, JIT SHA-256
`62ee72e2a4d6027b360234ee48bdbe1d63ee936931ad13d9169def1bda43b98e`. El checker, pins y WIP
55/239/0 pasaron antes de ejecutar. El resultado real se registra en la actualización siguiente.

Gates actuales: G01=0/10; G02=10/10; G03–G10=0/10; total 10%, delta 0; D01–D14=0/14. Los
PASS parciales V7 se conservan separados y no cierran tooling ni aceptación.

## Resultado Docker V3 — build/smoke PASS, cutover FAIL, rollback PASS

El usuario aprobó una invocación del JIT Docker V3 SHA-256
`62ee72e2a4d6027b360234ee48bdbe1d63ee936931ad13d9169def1bda43b98e`. Checker mecánico,
runner byte-idéntico, hashes, bash syntax, orden/condiciones, rollback, targets exactos
11 containers/5 networks y preflight WIP 55/239/0 pasaron. El comando ejecutó una vez con
timeout de 2700 s.

| Fase | Resultado | Evidencia sanitizada |
|---|---|---|
| Preflight y contexto allowlisted | PASS | Los ocho pins y seis archivos de contexto pasaron. |
| Image build | PASS | Tag `studiamatch-h3req1:20261009-v3`; base local fijada, sin pull. |
| Image smoke | PASS | Manifests/tarball, `braces`, Node/npm, Python y Playwright. |
| Cutover | FAIL, exit 1 | Compose no encontró `.env.local` en el checkout candidato. |
| Rollback | PASS | `RESTORED_ORIGINAL`; el ID original vuelve bajo `studiamatch-dev`, `studiamatch-dev:local`, estado `restarting`, política `unless-stopped`. |
| Cleanup histórico | No alcanzado | No hubo health PASS; no se retiró ninguno de los 11 containers ni cinco networks. |

`npm ci` instaló 627 paquetes y su salida reportó 2 advisories: 1 high, 1 critical. No se
capturaron nombres ni detalles. La lectura read-only posterior confirma que `.env.local` no
existe en el candidato y sí existe en `/home/romel/src/studiamatch`; no se leyó ni usó el
archivo del checkout original. La imagen candidata quedó local. Los nombres V3 de network,
volume, `node-deps` y contenedor fallido no existen; el contexto allowlisted permanece en
`/tmp` para preservar evidencia.

La autorización V3 queda consumida y no se repite. El fallo no habilita una segunda build ni
un cutover con un env-file distinto. Preparar una modificación puntual del paquete, definir
la fuente de configuración sin leer ni copiar valores y pedir un JIT nuevo antes de otro
cutover. No se acreditó health, tooling/r9, startup, integración, C03 ni aceptación. G01=0/10,
G02=10/10, G03–G10=0/10; total `10%`, delta `0`; D01–D14=0/14.

## V8 preparado — reducción focal de Tmpfs, pendiente de invocación

El usuario aprobó y consumió la invocación V7 descrita arriba; su fallo residual fue
`INSPECT_TEMPLATE_TMPFS_EVALUATION_ERROR`, antes de F1/r9. No se repite V7. Se preparó el
paquete [JIT V8](../operaciones/jit_h3req1_docker_desktop_wsl_f1_tmpfs_pair_diagnostic_v8_once_2026-10-09.md),
SHA-256 `f286b7c916fb434d7f55afa6d8bb0104df4d9bd52d382e061fe2570f1438477d`, con runner
`ad4214a2f2998c486e1aa5c3d01478e4389f9f0cf162cb20670e57975904c14e`, helper
`bf99e3414c6aad157371ad2decdb338a9f07c5587d422d41a0e13ed17147f121` y pruebas focales
`b9050f5d2f960beb0a25b0fd239f6e717cf5fe0061c747256255e8bdad51dfdd`. El matrix se limita a
los dos campos Tmpfs (índices 18/19) contra las otras 21 expresiones del residual, se detiene
en el primer par fallido y relee la contraparte para demostrar minimalidad. Después valida la
proyección segmentada de 25 campos con mapas presentes/ausentes. No lee F1 ni ejecuta r9.

Validación previa: pruebas sintéticas focales `4/4`; `bash -n`; AST Python; checker mecánico de
pines, comando exacto, orden, límites y scope: PASS. Revisión manual focal no encuentra una
lectura de F1/secretos ni operación sobre `studiamatch-dev`. Intenté el scan Codex Security
diff limitado a `tests/h3req1_docker_peer_substep_diag/v8_tmpfs_pair`; la herramienta rechazó
el scope y pidió `scope='.'`. No se inició scan ni se generó scan ID para no abarcar el WIP
completo. No se declara revisión automática independiente.

El JIT V8 aún requiere aprobación humana. No suma controles: G01=0/10, G02=10/10,
G03–G10=0/10, total `10%`, delta `0`; D01–D14=0/14.

## Actualización posterior — cleanup V6 y revalidación independiente r9/CI — 2026-10-09

El JIT Docker cleanup V6 aprobado se consumió una vez con
`cleanup-preflight|CONTAINER_MISMATCH`, exit 1, antes de cualquier `docker rm` o
`docker network rm`. La salida no conserva el ordinal/campo discrepante. Una consulta read-only
posterior de los 11 IDs fijados mostró sus tuplas actuales iguales a las esperadas, sin recuperar
el estado observado durante la ejecución ni demostrar una causa. No hubo cleanup/retry. Ver
[evidencia V6](h3req1_docker_candidate_cutover_v4_preparation_2026-10-09.md).

En paralelo, el paquete r9 r4 se revalidó contra las entradas actuales: 71 manifiestadas, 68
archivos fuente con hash coincidente, tres helpers package-only exactos y cero drift. Se reforzó
el wrapper host para fijar rama/HEAD/WIP y realizar esa comparación antes de Docker. Bash syntax,
manifests, source gate, límites, mounts read-only y `network=none` pasan; no se ejecutaron las
suites. El JIT [r9 candidate V4](../operaciones/jit_h3req1_g03_r9_candidate_v4_once_2026-10-09.md),
SHA-256 `d0a99744cf964d4a55fc3e104d74a4913093d394379e89351584dcb209c5c931`, espera aprobación.

El patch CI PWI V4 conserva SHA-256
`68bb4037f665c4e82c91b89faae939a20ab90cebbf85cff0b4a2f90b19682c26`; `git apply --check` en
snapshot limpio del HEAD baseline pasa, la aplicación aislada pasa y las dos fuentes helper/test
son byte-idénticas al candidato. El patch afecta cuatro rutas de control. No se publicó,
configuró ni probó en GitHub; G10 y el enforcement remoto continúan abiertos. El total permanece
10%, delta 0.

## r9 ejecución real: actionlint FAIL

El usuario aprobó una sola invocación de
`H3REQ1-G03-R9-CANDIDATE-V4-ONCE-20261009-V1`, JIT SHA-256
`d0a99744cf964d4a55fc3e104d74a4913093d394379e89351584dcb209c5c931`, runner SHA-256
`5197e0f8be7583394903fbac629bee94ff55cd084130d8f1a8c78c0c958721ba`. El preflight fijó la
rama/HEAD, WIP `55/270/0`, fuente 68/71 con tres auxiliares package-only exactas; todos pasaron.
La invocación ejecutada como `romel` no-root en Ubuntu WSL interactiva terminó exit 1:

```text
phase=r9-preflight|error_code=OK
phase=r9-candidate-source|error_code=OK
phase=r9-context|error_code=OK
phase=r9-input-hashes|error_code=OK
phase=r9-tool-hashes|error_code=OK
phase=r9-tool-extraction|error_code=OK
phase=r9-tool-versions|error_code=OK
phase=r9-candidate-copy|error_code=OK
phase=r9-npm-dependency-manifest|error_code=OK
phase=r9-node-and-typescript-versions|error_code=OK
phase=r9-next-typegen|error_code=OK
phase=r9-actionlint|error_code=CHECK_FAILED
exit=1
```

`actionlint` recibió exactamente `.github/workflows/security-audit.yml`,
`.github/workflows/protected-workflow-integrity.yml` y
`.github/workflows/db-sync-to-pro.yml`. El wrapper redirigió stdout/stderr a `/dev/null`; por
ello no quedó ubicación ni regla del diagnóstico. No se atribuye el fallo a un archivo o al
producto por inferencia. La autorización quedó consumida y no se repite. ShellCheck, ESLint,
TypeScript y `tests/test_protected_workflow_review.py`, `tests/test_scan_credentials.sh` y
`tests/test_protected_path_scope_guard.sh` no se alcanzaron.

El contenedor único de validación fue `--rm`, `network=none`, read-only, usuario 1001, cap-drop,
sin checkout writable, sin `.env*` ni credenciales, y sin socket Docker. El preflight encontró
saludable el `studiamatch-dev` fijado y el volumen de dependencias; no se modificaron. El JIT
r9 anterior no autoriza diagnóstico/reintento; G03 sigue 0/10 y el total sigue 10% (delta 0).

## Continuación r9 preparada: diagnóstico de actionlint, pendiente JIT

Se preparó una invocación nueva y acotada porque el resultado anterior perdió el diagnóstico:
[JIT r9 actionlint diagnostic/continuation](../operaciones/jit_h3req1_g03_r9_actionlint_continuation_v1_once_2026-10-09.md),
SHA-256 `63c9cc7facec5233c46f9f7967847d851e56f7e1ba03f8ea74515ffd3f3185b1`. Ejecutaría
`actionlint` una vez en los mismos tres workflows y solo si pasa continuaría los checks r9 que
no se alcanzaron. Sus dos helpers tienen SHA `53114a41…` y `65b5feae…`; `bash -n` pasa para
ambos. El parser tiene cinco casos sintéticos dentro del JIT, limita tamaño/cantidad y solo
emite workflow, línea, columna y regla allowlisted. La revisión estática confirma ejecución
`--pull=never --network=none --read-only`, montajes read-only, stop-on-failure y no acceso a
F1, `.env*`, secretos, SQL/DB ni operaciones de `studiamatch-dev`. No se ejecutaron los
sintéticos ni se volvió a invocar Docker/actionlint. Durante la revisión de despacho se detectó
y corrigió el filtro externo que omitía `r9-tool-extraction` y `r9-candidate-copy`, y ajustó el
código de salida sanitizado para formato inesperado; los runners fueron repineados antes de
pedir autorización. El JIT requiere aprobación humana nueva; G03 sigue 0/10 y total 10%.

## CI bootstrap: patch sincronizado con el candidato

La revisión estática encontró un delta entre el patch previo y el workflow candidato: el patch
hacía checkout del default branch del repositorio, mientras que el workflow candidato fija el
`pull_request.base.sha`. Se actualizó el patch para igualar exactamente el workflow candidato;
la versión anterior se preservó en
`h3req1_ci_bootstrap_minimal_v4_pre_sync.patch`, SHA `68bb4037…`. Patch actual
`h3req1_ci_bootstrap_minimal.patch`, SHA `033fe1263ceb86b1f609613de52de41b071153f7e8eabb6a11848b5b69c1a450`.

En un snapshot limpio creado desde HEAD baseline, `git apply --check`, aplicación, `git diff
--check`, igualdad byte a byte del workflow PWI/helper/test con el candidato y presencia de los
dos enlaces del workflow `security-audit` dieron PASS. El cambio sigue acotado a cuatro rutas.
La validación es de patch/estructura local: el actionlint de los tres workflows candidatos
falló en r9 sin conservar diagnóstico, no hubo ejecución GitHub ni check remoto. No se declara
enforcement ni se avanza a publicación/PR/settings sin instrucción separada.

## Continuación r9: preflight documental detiene JIT aprobado V1

La aprobación V1 (`63c9cc7facec5233c46f9f7967847d851e56f7e1ba03f8ea74515ffd3f3185b1`)
no se ejecutó: la comparación previa encontró que la ficha JIT esperaba SHA de helper interno
`8c13d00a2ce5e58636b155e17bfcd09ecee0030e339507767f8580f2591acea5`, pero el runner V1 fija y
el archivo actual tiene `65b5feae6661b868cb62ee8e23c28caaf862faa508f091cee3b2d81d6b109557`.
Se comprobó rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`,
WIP 55/272/0 antes de preparar V2, EUID no-root, kernel Ubuntu WSL y `bash -n` PASS. No se
invocó el runner V1, Docker ni actionlint; no se consumió la autorización y no hubo cambios de
contenedor.

Se preservan los artefactos V1. La V2 preparada fija la huella real del helper (`65b5feae…`),
separa runner/JIT, espera WIP 55/273/0 y fija branch/HEAD, manifests, imagen, contenedor y
volumen sin ampliar alcance. SHA-256 JIT V2 `a5fa34d31015440fcf3f3c0f164f6491702764c33f4a494a253c230a904c06e8`,
runner V2 `a3171b16e29eddfade63b1369f11d5e924e08a490709d5f9277835a9dc58438f`; ambos scripts y el
bloque de comando copiable pasan `bash -n`. Sin invocar Docker se releen los manifests fijados:
package, inputs y tools `OK`; 68/71 fuentes actuales coinciden y los tres helpers package-only
están ausentes según contrato. El comando V2 fija WIP 55/273/0 y runner/helper actuales. Aún no
se ejecutó V2 ni se solicita crédito G03. G03 0/10; total 10%, delta 0.

## R9 continuación V2: diagnóstico actionlint no clasificado

El usuario aprobó una invocación del JIT V2 SHA-256
`a5fa34d31015440fcf3f3c0f164f6491702764c33f4a494a253c230a904c06e8`; runner SHA-256
`a3171b16e29eddfade63b1369f11d5e924e08a490709d5f9277835a9dc58438f`, helper interior
`65b5feae6661b868cb62ee8e23c28caaf862faa508f091cee3b2d81d6b109557`. Antes del despacho se
confirmó rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`,
WIP `55/273/0`, usuario no-root en WSL, hashes y `bash -n`.

Resultado real, invocación única consumida, exit 1:

```text
phase=r9-continuation-preflight|error_code=OK
phase=r9-tool-extraction|error_code=OK
phase=r9-candidate-copy|error_code=OK
phase=r9-actionlint-classifier|error_code=OK
phase=r9-actionlint-diagnostic|error_code=OUTPUT_UNCLASSIFIED
exit=1
```

`actionlint` se invocó una vez sobre los tres workflows fijados. El parser interior descartó
el texto crudo y el mensaje no revela si el motivo fue salida vacía, ruta/formato no reconocido,
coordenadas/regla no conformes u otra condición del contrato. Por tanto no se atribuye el fallo
a un workflow ni se inventa regla. La parada impidió ShellCheck, ESLint, `tsc --noEmit` y las tres
suites focales. El contenedor fue `--rm --pull=never --network=none --read-only`, sin checkout
writable, `.env*`, secretos, volumen candidato ni socket Docker; no se mutaron `studiamatch-dev`,
rollback, volúmenes ni redes. La autorización V2 está consumida; no hay retry autorizado.
G03 0/10, total 10%, delta 0.

## Preparación r9 V3: clasificador de diagnóstico ampliado, pendiente de JIT

La invocación V2 terminó con `r9-actionlint-diagnostic|OUTPUT_UNCLASSIFIED`, exit 1. La causa
subyacente sigue sin conocerse porque el raw se descartó, según alcance. V3 conserva el stop-on-
failure y solo modifica el helper del clasificador: reconoce prefijos antes de la ruta allowlisted,
coordenadas acotadas de hasta seis dígitos incluido cero, y token de regla opcional que se
normaliza a una etiqueta segura o `unknown`. Distingue salida vacía, formato no reconocido,
límite excedido, discrepancia exit/diagnóstico, error del clasificador y resultado desconocido;
jamás imprime mensaje crudo. Nueve aserciones sintéticas se prepararon dentro del contenedor r9.

Revisión estática: `bash -n` PASS para runner, helper y comando; AST de los dos heredocs Python
válido sin ejecutar sus pruebas; hashes runner/helper/JIT fijados; WIP actual y esperado
`55/274/0`; flujo conserva imagen, paquete, volumen, allowlist de workflows, mounts read-only,
`network=none`, `--pull=never`, límite de salida y stop-on-failure. No se ejecutaron los nueve
sintéticos, actionlint ni Docker para V3. El paquete requiere una autorización única nueva porque
V2 está consumido. G03 0/10; total 10%, delta 0.

## R9 continuación V3: syntax-check localizado en security-audit.yml

El usuario aprobó una invocación del JIT V3 SHA-256
`7780410607782898dfe01481c79520891c0b55bcf66f337e462632c3b1ba4efe`. Se ejecutó como `romel`
no-root en Ubuntu WSL interactiva, timeout 180 s. Rama/HEAD/WIP fijados a
`feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `55/274/0`;
runner `64ec3666e944b8a88e79542dadd964eced42a4c40439662d32de6956f5fc83a4`, helper
`eaacd68e4a7d5ec9ec66f36f730f8c6ab0a308aa5962f1282ddaaf21506ae8cb`.

Salida sanitizada exacta; exit 1:

```text
phase=r9-continuation-preflight|error_code=OK
phase=r9-continuation-preflight|error_code=OK
phase=r9-tool-extraction|error_code=OK
phase=r9-candidate-copy|error_code=OK
phase=r9-actionlint-classifier|error_code=OK
phase=r9-actionlint|error_code=CHECK_FAILED
diagnostic=workflow=security-audit.yml|line=330|column=0|rule=syntax-check
exit=1
```

Las pruebas sintéticas del clasificador pasaron. `actionlint` se invocó una sola vez sobre los
tres workflows autorizados y reportó la línea 330 de `security-audit.yml`. En el candidato,
las líneas 330–331 estaban literalmente en columna cero: `H3_LOCAL_PATHS` y `)`. Ambas pertenecen
a una sección `run: |`; por eso el delimitador del heredoc y el cierre de la sustitución quedaban
fuera del literal YAML y originaban `syntax-check`. La causa se limita a esas dos indentaciones;
no se infiere ningún defecto funcional del producto.

Corrección local mínima: se añadieron diez espacios a ambas líneas, suficientes para mantenerlas
dentro del literal YAML y que, tras la dedentación YAML común, el shell reciba `H3_LOCAL_PATHS` y
`)` en la columna correcta. El diff entre el paquete r4 preservado y r5 actualizado contiene
exclusivamente esas dos líneas. `git diff --check`, `bash -n` de runner/helper y manifests del
package/inputs pasan. Estos son checks estáticos y no sustituyen la revalidación actionlint.

El stop-on-failure impidió ShellCheck, ESLint, `tsc --noEmit` y las tres suites focales; quedan
pendientes y no se copiaron resultados previos. El contenedor efímero se ejecutó
`--rm --pull=never --network=none --read-only`, sin checkout writable, secretos, `.env*`, volumen
candidato ni socket Docker. No se mutó `studiamatch-dev`, imágenes, volúmenes, redes o recursos
remotos. El JIT V3 está consumido; no se repite.

### V4 preparado para revalidar la corrección

El package r5 preserva el r4 anterior y fija el workflow corregido: package-manifest SHA-256
`5363610a5fd28558f3e2168dd926aaf1c26037d01b2645de815da7201c00b0ae`, inputs
`290905c8c88f56ce8c17aaf112e6536185068ea644008c685f299beeaeb1c57b`, tools
`4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`. La fuente corregida tiene
SHA `276641005c0bc1dc64b26e479b9ef197137a69b3dc4b08be8e56246fdb75df23`; el runner V4 SHA
`405f587a759fbc4f0d646c3b045db05949743cf3548d4dd33792a0a3dbf6d32a` fija WIP
`55/275/0` y mantiene el helper V2 sin cambios. El [JIT V4](../operaciones/jit_h3req1_g03_r9_actionlint_continuation_v4_once_2026-10-09.md), SHA-256
`28f3e47cfb22b409a565c19aa1a83a4cf509b5db8f5b99ab56e674e4164d6b43`, requiere una nueva
aprobación por el FAIL consumido de V3. Una sola invocación corre los sintéticos y actionlint;
ShellCheck, lint, TypeScript y suites focales quedan condicionados a actionlint PASS. Aún no se
ejecutó V4. G03 0/10; total 10%, delta 0; no hay GO.

## Resultado r9 V4: ShellCheck falla tras actionlint PASS

El usuario aprobó una invocación del JIT V4 SHA-256
`28f3e47cfb22b409a565c19aa1a83a4cf509b5db8f5b99ab56e674e4164d6b43`; runner SHA-256
`405f587a759fbc4f0d646c3b045db05949743cf3548d4dd33792a0a3dbf6d32a`, helper interior
`eaacd68e4a7d5ec9ec66f36f730f8c6ab0a308aa5962f1282ddaaf21506ae8cb`. Se ejecutó una vez en
Ubuntu WSL interactiva como `romel` no-root, con branch/HEAD/WIP fijados a
`feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `55/275/0`.

Salida sanitizada exacta, exit 1:

```text
phase=r9-continuation-preflight|error_code=OK
phase=r9-continuation-preflight|error_code=OK
phase=r9-tool-extraction|error_code=OK
phase=r9-candidate-copy|error_code=OK
phase=r9-actionlint-classifier|error_code=OK
phase=r9-actionlint|error_code=OK
phase=r9-shellcheck|error_code=CHECK_FAILED
exit=1
```

El stop-on-failure impidió ESLint, `tsc --noEmit` y las tres suites focales. El wrapper V4
descartó salida cruda y no conservó script, línea o regla de ShellCheck; no se atribuye el FAIL a
un archivo ni se repite V4. El JIT fue consumido. No hubo cambio de Docker, contenedor habitual,
SQL/DB, secreto o servicio remoto. G03 permanece 0/10; el total permanece 10%, delta 0.

### Preparación previa del diagnóstico sanitizado V1 — resultado posterior registrado abajo

Se preparó el [JIT ShellCheck diagnóstico V1](../operaciones/jit_h3req1_g03_r9_shellcheck_diagnostic_v1_once_2026-10-09.md),
SHA-256 `138629c2b2a94bbd5207c764909a2a5909749e0965a5ac5a0b5169cab7ded8b2`, con runner
`c9097daea8535a82a779fe39d3751e0078593e7b03c1b15026e3991a0771b5cd` y helper interior
`4d5ded37449829a364f9c6655107e0e1af5ebbd3b62f79a1b41c24cdbdffe47d`. Su salida admite solo
fase/código, path allowlisted, línea, columna y `SC####`; el texto del diagnóstico permanece
descartado. El helper añade pruebas sintéticas de límite de bytes, límite de hallazgos, formato
JSON y valores inválidos, para un total de trece casos. `bash -n` de ambos scripts y el parseo
estático de los dos heredocs Python dieron PASS; los trece casos todavía no se ejecutaron. Los
manifests del package r5 y tools r2 dieron PASS. La aprobación anterior de V4 no cubría ese JIT;
en el corte de preparación faltaba autorización. El resultado de la invocación aprobada se registra
abajo. El alcance se limita a los siete scripts indicados
en el JIT dentro de un contenedor efímero `--pull=never --network=none --read-only`; no lee F1,
no ejecuta r9 posterior, no toca `studiamatch-dev` y no hace cambios remotos.

## Resultado del diagnóstico ShellCheck V1 y preparación V2 — 2026-10-09

El usuario aprobó el JIT ShellCheck diagnóstico V1, SHA-256
`138629c2b2a94bbd5207c764909a2a5909749e0965a5ac5a0b5169cab7ded8b2`, con runner SHA
`c9097daea8535a82a779fe39d3751e0078593e7b03c1b15026e3991a0771b5cd` y helper SHA
`4d5ded37449829a364f9c6655107e0e1af5ebbd3b62f79a1b41c24cdbdffe47d`. Se ejecutó una sola vez
como `romel` no-root en Ubuntu WSL interactiva, timeout 120 s. Rama/HEAD/WIP:
`feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `55/276/0`.

Salida sanitizada exacta; exit 1:

```text
phase=shellcheck-diagnostic-preflight|error_code=OK
phase=shellcheck-diagnostic-preflight|error_code=OK
phase=shellcheck-diagnostic-tool-extraction|error_code=OK
phase=shellcheck-diagnostic-synthetics|error_code=OK
phase=shellcheck-diagnostic|error_code=OUTPUT_INVALID
exit=1
```

Preflight, extracción y sintéticos pasaron. ShellCheck se invocó una vez; stdout JSON y stderr
crudos se descartaron conforme al JIT. La autorización está consumida y no se repite. La respuesta
real no quedó capturada, por lo que no se inventa su forma ni sus diagnósticos.

El JIT V1 describía erróneamente `json1` como arreglo y probaba que un objeto
`{"comments":[]}` era inválido. El [manual oficial de ShellCheck](https://github.com/koalaman/shellcheck/blob/master/shellcheck.1.md)
define `json1` como objeto con propiedad `comments` y `json` como arreglo legado. Esto demuestra
que el parser y el sintético V1 estaban invertidos; la salida real perdida hace que el vínculo con
`OUTPUT_INVALID` sea una causa compatible con especificación, no una observación directa.

Se preparó V2 sin alterar los scripts/producto inspeccionados: parser separado que requiere raíz
`{"comments":[...]}`, 34 sintéticos declarados, salida limitada a script allowlisted/línea/columna/
`SC####`, descartando mensajes; un solo ShellCheck y mismos siete archivos. Revisión estática
confirma que root/list/status/schema/rutas/límites y cap de salida fallan cerrados; copy JSON y
artefactos viven solo dentro de contenedor efímero. `bash -n` de runner/helper V2 dio PASS. No se
ejecutó código Python/sintéticos fuera del JIT. No se hizo pull/build/egress, no se tocó
`studiamatch-dev`, F1, SQL/DB, secretos, GitHub o Cloudflare.

JIT V2 SHA-256 `21453beda3f35d82cb4091d5b5c7a164837f583ff275381065479f340fde20bb`, runner SHA
`af9a9293248822778b69195f70c42db72fb919080e8cc8cd5e6e6345db0b7557`, helper SHA
`6392599b1271ee47ce89ed3c79dfc44522d31f98a41b0d844ae78b0d89ac2c32`, classifier SHA
`07a8401aa6a89275362e2456655ad79ec00ff6d3629da5059e851a2520cc38a4`. Requiere aprobación nueva;
no se reutiliza la del V1. G03 permanece 0/10, total 10%, delta 0.

## Resultado ShellCheck V2, corrección SC2209 y r9 V5 preparado — 2026-10-09

El usuario aprobó una ejecución del JIT ShellCheck diagnóstico V2 SHA-256
`21453beda3f35d82cb4091d5b5c7a164837f583ff275381065479f340fde20bb`. Se ejecutó una sola vez
como `romel` no-root en Ubuntu WSL interactiva. Preflight, extracción de ShellCheck y 34 sintéticos
pasaron; ShellCheck terminó `CHECK_FAILED`, exit 1. La salida sanitaria exacta fue:

```text
phase=shellcheck-diagnostic-preflight|error_code=OK
phase=shellcheck-diagnostic-preflight|error_code=OK
phase=shellcheck-diagnostic-tool-extraction|error_code=OK
phase=shellcheck-diagnostic-synthetics|error_code=OK
phase=shellcheck-diagnostic|error_code=CHECK_FAILED
diagnostic=script=scripts/security/scan_credentials.sh|line=195|column=5|rule=SC2209
exit=1
```

La invocación V2 queda consumida. El defecto demostrado es la asignación no citada `mode=diff`
para el literal asociado a `--diff`. Se corrigió únicamente esa asignación en el candidato a
`mode="diff"`; `bash -n scripts/security/scan_credentials.sh` y
`git diff --check -- scripts/security/scan_credentials.sh` pasan. El cambio mantiene el mismo
valor de la variable; el enlace a la regla se documenta en la
[guía oficial SC2209](https://github.com/koalaman/shellcheck/wiki/SC2209).

La comparación entre paquete r5 y el candidato encontró que r5 llevaba un snapshot anterior del
único archivo fuente `scripts/security/scan_credentials.sh`. r6 refresca ese archivo desde el
candidato y sus manifiestos; incluye WIP previo del archivo además del quote fix. No se atribuye
ese WIP previo a este arreglo ni se afirma que el diagnóstico V2 ejecutara el archivo completo
actual. El nuevo paquete permite validar los bytes actuales.

Verificaciones de preparación realizadas sin invocar Docker:

| Check | Resultado | Alcance |
|---|---|---|
| Paquete r6 `r4-package.sha256` e `inputs.sha256` | PASS | Manifiestos completos. |
| Herramientas locales `tools.sha256` | PASS | Sin descarga. |
| r6 contra fuentes actuales | PASS 68/68 | 71 filas; 3 artefactos package-only ausentes del checkout de forma esperada. |
| Workflows frente a r9 V4 actionlint PASS | PASS, hashes idénticos | security-audit, protected-workflow-integrity y db-sync-to-pro. |
| Bash syntax de runners r9 V5 | PASS | Solo sintaxis. |
| WIP fijado para próximo JIT | PASS `55/278/0` | Rama/HEAD continúan en el baseline esperado. |

El r9 V5 omite solo el actionlint ya aprobado con los mismos tres hashes. Dentro de un contenedor
temporal aislado corre ShellCheck sobre los mismos siete scripts con salida json1 filtrada; después
revalida el marcador de package/lock, versiones Node/TypeScript, regenera `next typegen` en el
scratch y ejecuta ESLint, `tsc --noEmit`, la suite `test_protected_workflow_review.py`,
`test_scan_credentials.sh` y `test_protected_path_scope_guard.sh`, deteniéndose al primer fallo.
`test_scan_credentials.sh` recibe un tmpfs `/exec-fixture` con ejecución habilitada; `/tmp` sigue
`noexec`. El proceso parte de `env -i`, sin heredar variables de imagen. Usa imagen local por
digest, `--pull=never --network=none --read-only` y dependencias montadas read-only. No lee F1,
no ejecuta SQL/DB ni accede a recursos remotos o credenciales.

En el corte de preparación previo a la aprobación: [r9 ShellCheck continuation V5](../operaciones/jit_h3req1_g03_r9_shellcheck_continuation_v5_once_2026-10-09.md),
SHA-256 `0cdd62518f924693c0c05b45a69ecaf8a2bf4b4b0d96001f1bde75a39f403eb6`; runner host SHA
`1aa13c054482eecfb78f586913a0a9d60e437606c1a432c72400c86d040da862`, runner interior SHA
`b4835a286ef036ca733efe6a49be9cc37b19d16bb5ddbfb4a6ea90065461ab71`, classifier SHA
`07a8401aa6a89275362e2456655ad79ec00ff6d3629da5059e851a2520cc38a4`. En ese corte, la aprobación
V2 estaba consumida y V5 esperaba aprobación. El estado posterior se registra abajo.

## Revisión focal CI bootstrap en paralelo — 2026-10-10

Se releyó el patch PWI vigente, SHA-256
`033fe1263ceb86b1f609613de52de41b071153f7e8eabb6a11848b5b69c1a450`. Mantiene cuatro rutas de
control; el workflow PWI usa `pull_request_target` y `pull_request_review`, y el delta no añade
`push`, schedule, `workflow_dispatch` ni pasos de deploy de producto. La revisión es estática:
no se aplicó ni publicó el patch y no se observó un check remoto. Cloudflare Pages tiene
Production branch `main` e include `*`; la integración puede producir una Preview y su resultado
real sigue pendiente. No se alteraron Actions Policies ni Build watch paths. G10 continúa 0/10,
sin cambio de porcentaje.

## Ejecución aprobada r9 V5 — salida no recuperable — 2026-10-10

El usuario aprobó una sola ejecución de `H3REQ1-G03-R9-SHELLCHECK-CONTINUATION-V5-ONCE-20261009-V1`,
JIT SHA-256 `0cdd62518f924693c0c05b45a69ecaf8a2bf4b4b0d96001f1bde75a39f403eb6`. Se despachó el
bloque exacto documentado con terminal interactiva (`tty=true`), como requería el paquete. La
respuesta del ejecutor no quedó disponible en el contexto recuperable; el lector de terminal de
la app indicó que no había una sesión adjunta, el proceso del runner ya no aparecía y no se halló
un archivo de salida dedicado. Por ello no se conservan fases, exit, diagnóstico ni predicado de
éxito/fallo. No se infiere el resultado a partir de ausencia del proceso o de temporales.

La autorización one-shot se considera consumida al despacharse. No se reejecutó el JIT, no se
consultó de nuevo Docker ni se inspeccionaron contenedores temporales después de perder la salida.
No hay evidencia verificable de que ShellCheck, ESLint, typegen, TypeScript o las suites focales
hayan pasado o fallado en esta invocación. El actionlint PASS reutilizado sigue limitado a los tres
workflow hashes exactos del corte anterior. G03 permanece 0/10; total 10%, delta 0. El resultado
operativo de esta invocación es indeterminado y no permite avanzar a F1 ni a etapas dependientes.
Antes de otra ejecución G03, debe existir un paquete nuevo que no repita V5 y que conserve la
salida sanitizada del runner en una evidencia recuperable según su contrato. No hay permiso para
reintentar un check de V5; F1 y las etapas dependientes siguen sin autorización por este JIT.

## Inventario Docker read-only posterior — 2026-10-10

El objetivo de esta lectura fue refrescar únicamente la metadata del servicio habitual, sin abrir
su filesystem ni consultar `Env`. La primera llamada dentro del sandbox devolvió `permission denied`
al conectar a `/var/run/docker.sock`; la lectura fue read-only y se repitió con acceso de Docker
API aprobado por el revisor. Un primer formato de salida intentó leer `.Name` en un mount bind y
falló con exit 1 (`template parsing error: map has no entry for key "Name"`); se corrigió el
formato para pedir el nombre solo a mounts tipo volume. No hubo cambios a recursos.

Resultado sanitizado de `docker inspect` del único contenedor allowlisted:

```text
500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049|sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63|studiamatch-h3req1:20261009-v3|running|healthy|studiamatch-h3req1|app|mount=bind,bind,/app,rw=true|mount=volume,studiamatch_h3req1_node_modules,/app/web/node_modules,rw=true
```

Esto confirma que el mismo `studiamatch-dev` sigue activo, usa la imagen V3 fijada, monta el
checkout en `/app` y mantiene el volumen de dependencias nombrado en `/app/web/node_modules`.
La lectura de metadata no acredita r9, F1, Pages/workerd ni C03 integrado, y no recupera la salida
perdida de V5. G03 sigue 0/10, G02 10/10; total 10%, delta 0. No se inspeccionaron logs, otros
contenedores, redes, valores de entorno ni contenido/estado interno de los mounts.

## Revisión estática de aceptación UI — 2026-10-10

La inspección focal del candidato y del harness no encontró un defecto funcional demostrado en
los cuatro ajustes. El SQL actual conserva assertions para auditoría editorial atómica (actor,
fecha, before/after y rollback si falla el append), evidencia de disponibilidad válida al día
90 inclusivo, rechazo de >90 fuera del límite, evidencia ausente/inválida/vencida y retorno al
comportamiento legacy. El harness y sus inputs editoriales cambiaron respecto al corte anterior;
no se reutiliza 41/41 para ellos y no se ejecutó SQL en esta revisión.

La UAT actual tenía 48 casos y no ejercitaba el guard >90 días del formulario antes del RPC ni
la ausencia del formulario de disponibilidad para el rol `user`. Se añadieron aserciones a los
dos casos H3-CA4.2 existentes, sin aumentar el total: 48 casos × 3 viewports. El contrato
estático `tests/test_h3_admin_queue_ux_contract.py` también fija que la validación de UI preceda
la llamada `admin_set_course_availability`. La UAT rellena solo URL/fechas/nota sintéticas,
espera el error local y cuenta que no se emita POST `/api/admin/rpc`; no persiste cambios.
No se ejecutaron UAT, pytest, ESLint, TypeScript, SQL ni Docker en esta revisión.

Verificación realizada: revisión estática del fragmento y consumidores, `rg` confirma 48
declaraciones `defineCase`, `git diff --check` PASS, `bash -n` PASS del bloque del JIT V6 y cinco
sintéticos del filtro de captura PASS. El fixture en `/tmp/h3req1-g03-r9-v6-output-filter-synthetics-20261010.sh`
(SHA-256 `265b91a6a20f20c682d94466557b73e92fec0413a6a0f9a52049124bced48814`) acepta fase, exit
numérico y diagnóstico allowlisted, y rechaza texto crudo y ruta no allowlisted.
Hashes posteriores al cambio: `tests/h3_local_uat.mjs`
`6db4d61def41dba7f932c1f59278a52ec1162945c57b847ace8cbec1ccf730a1` y
`tests/test_h3_admin_queue_ux_contract.py`
`4cf3f2841dfaac14178e1331ac03cd6bee6046a6ec1a8ce750c03fd3732295b1`. Son cambios de cobertura,
no resultados de ejecución; no suman G01/G03/G09 ni el 10% total.

El siguiente permiso local requerido es el nuevo JIT G03 r9 V6, no el V5 consumido: [paquete
de captura durable](../operaciones/jit_h3req1_g03_r9_output_capture_v6_once_2026-10-10.md),
SHA-256 `7592aaa6d29a3aa70513780087ecb2ae65b89076c772afe8667fdca3ebf17e95`. Su runner host
temporal cambia únicamente el preflight WIP de `55/279/0` a `55/280/0`; la revisión mecánica
del diff confirmó esa línea como único cambio. Aún no se ejecutó. La salida se validará y
persistirá en un archivo de evidencia nuevo antes de mostrarse.

## Verificación remota read-only de CI — 2026-10-10

GitHub MCP leyó `romelhc95/studiamatch` en `refs/heads/main`: la ruta
`.github/workflows/protected-workflow-integrity.yml` no existe (respuesta del conector: ruta
ausente). El listado read-only de PRs con head `romelhc95:feat/h3req1-sync-20261002`, base
`desarrollo` y estado `all` devolvió `[]`. No hubo escritura remota. La preparación local PWI no
está instalada en la rama default ni hay PR de esta rama; G10 permanece 0/10. Instalación,
enforcement y promoción siguen requiriendo su aprobación separada.
