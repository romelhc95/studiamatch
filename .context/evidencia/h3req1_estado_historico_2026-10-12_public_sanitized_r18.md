> Copia pública sanitizada R18. Se retiraron identificadores personales y valores con forma de sesión; el original R17 permanece intacto en el checkout local y no forma parte del paquete público.

# Archivo histórico del estado operativo acumulado

> Copia del contenido de `.context/estado_del_proyecto.md` anterior a la consolidación documental local, corte 2026-10-12. La copia coincide byte por byte con el checkpoint externo verificado antes de la edición. Este archivo preserva snapshots y enlaces históricos; no es autoridad operativa vigente y sus estados solo aplican a la fecha indicada en cada sección.
>
> SHA-256 del archivo de origen preservado: `51942bd6232052aeaad5391fef4f23a7ab7a80186b79ab077fb40d890b995124`.
> Backup externo completo: `/home/romel/backups/studiamatch-docs-2026-10-12/checkpoint_structure_review_pretrim_20261013T025404Z` (snapshot `snapshot`); el manifiesto de hashes está en `inventory/files.sha256.jsonl`.

---

# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-10-12-H3REQ1-G10-LOCAL-R182-COMPLETE`.

## Corte vigente — GO LOCAL — validación y preparación local completas — R181/R182, 2026-10-12

G01–G09 conservan el cierre funcional local R178. El delta R8/R181 prepara el
bootstrap CI en dos etapas sin reabrir pruebas funcionales con inputs compatibles.
Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el HEAD no identifica el WIP. El
checkout original, cambios ajenos, secretos y evidencia R6/R7 se preservan. No
hubo commit, push, PR, merge, lecturas/configuración remota ni deploy.

La revisión independiente final R8/R181 devolvió PASS, sin HIGH/CRITICAL ni
bloqueos. Confirmó el inventario de 92 paths propuestos + 158 evidencias = 250
archivos únicos, tamaños/modos/hashes y cero solapamiento; el test protegido y
la atestación sanitizada están incluidos. El cuerpo tiene las diez secciones de
la plantilla y sus enlaces resuelven. Los cinco puntos R181 se corrigieron.
R182 marca como históricos/supersedidos los encabezados antiguos R179, R178,
R144 y del 2026-10-09, sin alterar sus resultados. Como estado e índice forman
parte de los 92 paths propuestos, el scope checker y scanner se renovaron sobre
el candidato reconciliado; el resultado está en la evidencia R182 enlazada abajo.

Stage 1 conserva `security-audit` y sus gates existentes, no depende de un
workflow aún no instalado y mantiene permisos acotados. Stage 2 queda como patch
separado/inactivo; su activación requiere primero la instalación de PWI y
lecturas/comprobaciones remotas en otra etapa. En Docker, actionlint Stage 1
exacto y transición 9/9 se reutilizan de R180 porque sus inputs no cambiaron;
R182 renueva scope guard y credential scan sobre los 92 paths tras marcar los
cortes antiguos como históricos. La evidencia del snapshot final y el estado de
los contenedores está enlazada abajo.

| Gate | Estado del corte | Evidencia/límite |
|---|---|---|
| G01–G09 | Completos localmente por R178 | Matriz LOCAL-01..23, criterios cliente sanitizados, seis pilares, transición y recuperación/rollback local. Los cuatro tests live omitidos y las warnings se declaran; no se cuentan como PASS. |
| G10 — preparación local | Completa | Stage 1/Stage 2 reconciliados; actionlint y transición compatibles reutilizados; scope/scanner 92/92 tras la reconciliación R182; revisión independiente R8/R182 PASS; manifest/cuerpo íntegros. |
| G10 — remoto | Pendiente y fuera de esta sesión | No se leyeron ramas/protecciones/Actions/Pages, no hay run remoto, instalación/enforcement, PR, revisión humana GitHub ni deploy. |

**GO LOCAL — validación y preparación local completas.** Esto permite revisar el
candidato con el responsable, pero no equivale a `GO_LOCAL_PR` ni a
`GO_DEVELOPMENT_REAL`. Métricas con denominadores estables: tablero global
G01–G10 = 9/10 = 90% (delta de este corte: 0 puntos); cierre local G01–G09 =
9/9 = 100% (delta de este corte: 0 puntos). G10 remoto sigue pendiente y no se
suma al cierre local.

Evidencia vigente: [cierre del delta y revisión independiente R181/R182](evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md),
[scope/scanner Docker R182 92/92](evidencia/h3req1_g10_scope_scan_r182_2026-10-12.txt),
[cuerpo PR local R8/R182](evidencia/h3req1_pr_body_draft_local_review_2026-10-12_r8.md),
[manifest R8/R182](evidencia/h3req1_pr_scope_manifest_2026-10-12_r8.json),
[cierre funcional R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md),
[matriz LOCAL-01..23](evidencia/h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md).
No se creó PR ni se inició la etapa remota.

La siguiente sesión, separada de esta validación, reorganizaría Obsidian en este
orden: índice, arquitectura, tecnologías, backend, database (diccionario y
propósito), frontend, componentes relacionados, hitos, decisiones y changelog.
Este párrafo conserva el siguiente paso que figuraba en el snapshot R182 del
2026-10-12; el corte documental siguiente lo reemplazó.

### Actualización documental local — 2026-10-12

Se implementó la reorganización integral del corte local y quedó preparada para
revisión/reconciliación. La entrada vigente es [índice documental](indice.md);
el [inventario](h3req1_inventario_cobertura.md) conserva 28 responsabilidades
editoriales de alto nivel, no como denominador. El registro verificable enlazado
allí mantiene las asignaciones exactas por fuente y sus relaciones; en el corte
de reanudación tiene 12 componentes y 49 grupos, con relaciones semánticas aún
en investigación local. La ficha de
[reorganización](h3req1_mapa_reorganizacion.md) conserva rutas históricas y
referencias. La evidencia de checks y revisión se registra en
[corte documental](evidencia/h3req1_documentacion_integral_2026-10-12.md).

Esta actualización no cambia el GO LOCAL R181/R182, sus resultados R8, ni
convierte la preparación del paquete documental en GO para PR, merge,
Development, Supabase, Cloudflare o pruebas remotas. G10 remoto continúa
pendiente; su lectura y cualquier acción quedan para una instrucción separada.
El borrador R9 es un delta documental explícito, no la reconciliación del
paquete funcional. R8 conserva su tarball local de `braces`, excluido del delta
documental por la instrucción de no incluir dependencias; el responsable debe
resolver esa incompatibilidad en el paso 3 antes de declarar integrado el
paquete combinado. Las opciones y lecturas concretas quedan en la evidencia
documental enlazada arriba, sin abrir aquí un plan de ejecución remoto.

## Corte histórico — R180, supersedido por R181 — cierre local del delta G10 preparado; G10 remoto pendiente — 2026-10-12

G01–G09 conservan el cierre local R178; este delta no reabre pruebas funcionales cuyos
inputs siguen compatibles. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el HEAD no identifica el WIP. El checkout
original `/home/romel/src/studiamatch`, secretos, cambios ajenos y evidencia R6/R7 se
preservan. No hubo commit, push, PR, merge, lectura/configuración remota ni deploy.

R7 fue reconciliado en su delta: 91 rutas propuestas, 149 evidencias y 240 archivos únicos
siguen íntegros según la revisión independiente. Esa revisión encontró seis rutas que el
scope guard Stage 1 no admitía; R180 las agrega por coincidencia exacta. También eliminó
`checks: read` no utilizado de Stage 2 y limita sus permisos `actions: read`/
`pull-requests: read` al waiter. No se amplió la expresión de rutas ni se desactivó un gate.

| Gate | Estado R180 | Evidencia/límite |
|---|---|---|
| G01–G09 | Completos localmente por R178 | No se repiten pruebas funcionales con inputs compatibles. |
| G10 — preparación local | Parcial, validaciones ejecutadas | Stage 1 actionlint PASS en Docker, scope de 91/91 PASS; Stage 2 R8 separado/inactivo. La revisión independiente post-fix y la conciliación final R8 siguen pendientes. |
| G10 — remoto | Pendiente | No se leyeron ramas, protecciones, Actions, merge queue ni Pages; no hay workflow run, enforcement, revisión humana ni deploy acreditados. |

Stage 1 actionlintó cuatro entradas con actionlint 1.7.7 en Docker: workflow Stage 1 exacto,
variante Stage 2 sintética, PWI y DB Sync; exit 0. El primer comando con una opción inválida
terminó en exit 2 antes de analizar YAML y no se cuenta. El scope checker R180 aceptó las 91
rutas propuestas: 71 por regex, 20 exactas y cero no admitidas. El patch Stage 2 R8 aplica en
modo check al workflow activo y permanece sin aplicar.

Métrica global histórica G01–G10: 9/10 = 90%. Métrica local G01–G09: 9/9 = 100%; el porcentaje
local no acredita G10 remoto ni `GO_LOCAL_PR`/`GO_DEVELOPMENT_REAL`. No se declara todavía
“GO LOCAL” hasta cerrar la revisión independiente post-fix y el inventario R8.

Evidencia vigente: [cierre local G10 R180](evidencia/h3req1_g10_bootstrap_transition_2026-10-12_r180.md),
[scope checker R180](evidencia/h3req1_g10_scope_allowlist_check_r180.py),
[patch Stage 2 R8](evidencia/h3req1_g10_security_audit_stage2_2026-10-12_r8.patch),
[cuerpo PR R8](evidencia/h3req1_pr_body_draft_local_review_2026-10-12_r8.md) y
[manifest R8](evidencia/h3req1_pr_scope_manifest_2026-10-12_r8.json). R179/R7 y R6 quedan
preservados como cortes históricos.

## Corte histórico — G10 bootstrap local preparado en dos etapas; remoto pendiente — R179, supersedido por R181/R182 — 2026-10-12

G01–G09 conservan el cierre local R178. El candidato permanece en el checkout
`/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`; el HEAD no identifica el WIP.
No hubo commit, push, PR, merge, workflow remoto, configuración remota ni deploy.

R6 se preservó íntegro antes del delta (234/234 hashes/tamaños/modos y cuerpo/
manifest verificados). R7 agrega al inventario explícito
`tests/test_protected_workflow_review.py`, que faltaba en R6, y prepara el
cuerpo/manifiesto nuevos. El workflow local `security-audit.yml` queda en
etapa 1 sin waiter PWI: conserva el agregado/check actual y los demás gates;
la eliminación se limita a la dependencia futura que no puede existir antes
de instalar PWI. La etapa 2 queda como patch separado, no aplicado.

| Gate | Estado | Evidencia/límite |
|---|---|---|
| G01–G09 | Completos localmente por R178 | El delta R179 es preparación CI/documental; no repite ni reemplaza los resultados funcionales. |
| G10 — preparación local | Parcial preparado | R179 Stage 1/Stage 2, R7 body/manifest, transición parcheada en copia temporal. Falta actionlint exacto de Stage 1 y revisión independiente R7. |
| G10 — remoto | Pendiente | Default branch, protecciones/Rulesets, Actions efectivo, merge queue y Pages deben leerse; sin CI/enforcement remoto. |

Métrica histórica G01–G10: 9/10 = 90%; cierre local G01–G09: 9/9 = 100%.
No se declara `GO_LOCAL_PR`: G10 y la integridad/revisión R7 siguen pendientes.
R5 no se extrapola a los deltas R7.

Paquete R179: [bootstrap en dos etapas](evidencia/h3req1_g10_bootstrap_transition_2026-10-12.md),
[patch Stage 2](evidencia/h3req1_g10_security_audit_stage2_2026-10-12.patch),
[cuerpo PR R7](evidencia/h3req1_pr_body_draft_local_review_2026-10-12_r7.md) y
[manifest R7](evidencia/h3req1_pr_scope_manifest_2026-10-12_r7.json). R6 permanece
como corte histórico sin modificar.


## Corte histórico — G08–G09 locales completos; G10 remoto pendiente — R178, supersedido por R181/R182 — 2026-10-11

El candidato continúa en `/home/romel/src/studiamatch-h3req1-sync-20261002`,
rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. El HEAD no identifica el WIP. El
checkout original, cambios ajenos, evidencia histórica y recursos Docker se
preservan; no hubo commit, push, PR, merge, deploy ni escrituras remotas.

La autorización humana local del 2026-10-10 sigue limitada a H3REQ1 local:
fixtures, builds, PG17 desechable y pruebas sintéticas. No autoriza servicios
remotos, cuentas reales, secretos, checkout original ni promociones. G10 remoto
permanece fuera del ciclo.

R160 ejecutó pytest del proyecto en Docker: 337 passed, 4 skipped, una warning,
exit 0. R159 renovó el contrato de credenciales (45/45) y credential scan; R161
renovó el pipeline PostgREST/PG17 hasta persistir staging/cleansed/enriched/
courses y recovery ante 503 sintéticos. R162 pasó el sanitizer 16/16. Los checks
G08 de lint, typegen/TypeScript, audit, writer scan, actionlint/ShellCheck y
build se conservan solo donde los inputs siguen coincidiendo; el artifact
normal R146 se verificó 201/201 y sus fuentes web actuales 61/61. R173 renovó
en Docker `node --check` y credential scan del runner UAT actual, además de
H3-UAT-002/003 en 6/6 viewports y 36/36 assertions.

G09: INV-008 tiene causa reproducida (ciclo de rutas con sesión
`password_pending`), corrección y onboarding local 10/10 en R8/R146. R167 solo
validó la redirección y tomó captura mientras la cola cargaba; R168 fortaleció
el predicado del test y pasó el dashboard estable en 3/3 viewports, 9/9
aserciones. R169 volvió a ejecutar H3-UAT-072 con el artifact normal R146
verificado: 3/3 viewports, 18/18 aserciones, cero retries/errores/egress; cierra
el vínculo mutación sintética→rebuild→listing/detalle. R147/R161 cubren el
pipeline persistente sintético. R170 queda conservado como fallo de sincronía
del test; R171–R173 validan correo autenticado, fallback y roles. R173 además
limita la interceptación a GET del endpoint exacto en loopback sin query.
LOCAL-01..22 quedan completos dentro de los límites indicados en la matriz.
LOCAL-23 se cierra con la revisión independiente R5 PASS: sin findings
HIGH/MEDIUM ni bloqueantes; el cuerpo sigue la plantilla y el inventario fue
verificado. La recomendación LOW opcional de mínimo privilegio está descrita
como hardening previo a una futura promoción remota, no como waiver.
R174 corrigió un HIGH confirmado en `--diff` del scanner de
credenciales: el modo anterior omitía blobs transitorios entre commits. R175
cubre worktree, índice y symlinks con lectura segura por componentes; R176
añade detección de asignaciones opacas, allowlist CI de ambos paths y lock
hash-pinned para dependencias Python del workflow. Los sintéticos y 72 contratos
relacionados pasan en Docker; ShellCheck y actionlint 1.7.7 pasan. La revisión
independiente cerró los MEDIUM de R175/R176 y no encontró HIGH/MEDIUM nuevos en
ese delta. El manifest R6 identifica 89 paths propuestos, 145 evidencias y 234
archivos únicos hasheados. La revisión independiente R5 pasó; R178 registra la
reconciliación final. El scan R6 de 854 paths pasó en Docker, exit 0, en 11 lotes; R178 registra
el conjunto exacto y la imagen usada.

| Gate | Estado vigente | Evidencia |
|---|---|---|
| G01 SQL/editorial | Completo | Harnesses PG17 anteriores, inputs compatibles. |
| G02 suspensión SQL | Completo | C03 SQL aislado preservado; el integrado se acredita aparte en G07. |
| G03 tooling | Completo | R160/R161 y checks focales; actionlint/ShellCheck y demás solo con pins compatibles. |
| G04 F1 | Completo | Diagnóstico estructurado vigente; Docker Desktop/WSL identificado, sin repetir F1. |
| G05 snapshot | Completo | S18, 17/17 fuentes, productores/receptores/verificadores PASS. |
| G06 Pages/workerd | Completo | S16 healthz real PASS; R146/R168/R169/R173 sirven Pages/workerd local. |
| G07 C03 integrado | Completo | R51 PASS; 128/128 inputs continúan coincidiendo. |
| G08 checks finales | Completo | R160 337/4; R159 45/45; R174 5 regresiones de historia; R175 6 casos tree; R176 4 asignaciones opacas, 72 contratos focales, ShellCheck y actionlint 1.7.7; scan final R6 854 paths, exit 0; R161 PG17/PostgREST; sanitizer R162 16/16; lint/types/audits/builds vigentes por input; R173 UAT 6/6 viewports. |
| G09 aceptación local | Completo en alcance local | LOCAL-01..23 reconciliadas; INV-008, pipeline, dashboard, mutación/rebuild, correo/fallback/roles y scanner tienen evidencia local compatible. Revisión independiente R5 PASS. |
| G10 CI remoto | Pendiente | Sin workflow remoto, enforcement, revisión humana ni operaciones protegidas. |

Métricas: tablero histórico G01–G10 = 9/10 (90%); cierre local G01–G09 =
9/9 (100%). El 100% es local y no acredita G10 ni promoción remota.

Evidencia y matriz: [cierre R159–R173](evidencia/h3req1_g09_local_close_r159_r173_2026-10-11.md),
[R178 cierre local](evidencia/h3req1_g09_local_close_r178_2026-10-11.md),
[R179 bootstrap CI en dos etapas](evidencia/h3req1_g10_bootstrap_transition_2026-10-12.md),
[review independiente R5](evidencia/h3req1_g09_final_review_r5_2026-10-11.md),
[G08 final](evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md),
[R175 symlink/worktree](evidencia/h3req1_g08_credential_tree_symlink_r175_2026-10-11.md),
[R176 scanner/allowlist](evidencia/h3req1_g08_scanner_named_credentials_ci_allowlist_r176_2026-10-11.md),
[R170–R173](evidencia/h3req1_g09_email_fallback_r170_r173_2026-10-11.md),
[matriz LOCAL-01..23](evidencia/h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md),
[scanner de historia R174](evidencia/h3req1_g08_credential_history_scan_r174_2026-10-11.md).
[Cierre R178](evidencia/h3req1_g09_local_close_r178_2026-10-11.md), [revisión R5](evidencia/h3req1_g09_final_review_r5_2026-10-11.md), y [matriz LOCAL-01..23](evidencia/h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md). Borrador local sin PR: [R6](evidencia/h3req1_pr_body_draft_local_review_2026-10-11_r6.md); manifest: [R6](evidencia/h3req1_pr_scope_manifest_2026-10-11_r6.json).

### Corte histórico — G08/G09 R144, 2026-10-11

## Corte histórico — G08 checks locales completos; G09 aceptación funcional parcial — R144, supersedido por R178/R181/R182 — 2026-10-11

El último corte de cierre G01–G09 queda preservado como antecedente, no como
estado vigente del candidato. La revisión de seguridad encontró que la cookie
de actividad no estaba vinculada a la sesión Auth; el defecto se reprodujo en
rojo y se corrigió con HMAC ligado a `session_id`. También se re-firma la cookie
tras MFA si Auth devuelve una sesión nueva. La revisión independiente posterior
no encontró bloqueantes estáticos. El checkout original
`/home/romel/src/studiamatch` y los recursos remotos no se modificaron.

La autorización humana local del 2026-10-10 cubre correcciones, fixtures
aislados, SQL solo en PG17 desechable, builds y pruebas locales de H3REQ1; no
autoriza operaciones remotas, secretos, cuentas/datos reales, cambios en el
checkout original, commit/push/PR/merge/deploy, ni limpieza global. La excepción
JIT es local y específica de este ciclo.

Rama/HEAD siguen siendo `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP al corte R142: 60 rutas
tracked con cambios, 17.473 rutas untracked expandidas y 0 staged. Ese conteo
incluye caches, evidencia y WIP ajeno; no define por sí solo el candidato ni
autoriza incluir todos los paths. El set de candidato propuesto de R2 y el
cuerpo PR local permanecen como borradores que deben reconciliarse contra el
manifest final después del cierre. Ruta del draft: `evidencia/h3req1_pr_body_draft_local_review_2026-10-11_r2.md`.
Los demás paths permanecen excluidos y preservados.
Incluye S13/S14/S15/S16 ejecutados, snapshots S16/S17/S18,
R49/R50 históricos, R51 PASS, UAT R28/R29/R30 y pipeline walk R2/R73;
no se ejecutó `git reset` ni `git clean`; R83 sí usó el reset permitido del fixture sintético por viewport.
`studiamatch-dev` está healthy (`500931b0f086`), imagen local
`studiamatch-h3req1:20261009-v3`, puerto loopback `127.0.0.1:3000`; montajes de
trabajo `/app` y dependencias preservados. También siguen activos dos holders
S3/S2 preexistentes. El snapshot S18 (`48116e932a47…`) y su volumen fuente se
preservan. El runtime S15 (`d45b6f4ef1ab…`, exit 0/OOM false) se conserva porque
su supervisor dio NO-GO; está adjunto read-only al mismo volumen S18. El primer
preflight S16 no creó contenedor ni alteró esos recursos; el runtime S16
posterior pasó y fue retirado por su ID exacto.

### G03 — revalidación del delta BFF PASS

La ejecución G03 BFF registró 90 checks PASS; R76 amplió el test de logout a 96
checks sin cambio de producto. El contrato Admin queue pasó 13/13; sintaxis Node
de los mocks/runtime PASS; ESLint terminó exit 0 con nueve warnings conocidos
y cero errores; Next typegen y TypeScript PASS con contenedor 4 GiB y heap Node
3072 MiB. Resultado y límites en
[evidencia de cookie ligada a sesión](evidencia/h3req1_activity_cookie_session_binding_2026-10-10.md).
Workflow protegido, scanner, scope guard, ShellCheck y actionlint previos se
reutilizan porque sus inputs respectivos coinciden. No se suma un punto por la
revalidación: G03 ya estaba contado en el corte anterior.

### G01–G10 — estado recalibrado del mismo candidato

| Gate | Estado vigente | Evidencia / dependencia |
|---|---|---|
| G01 SQL/editorial | Completo | Inputs SQL/editorial no cambiaron en este delta; evidencia PG17 previa se conserva. |
| G02 suspensión SQL | Completo | C03 SQL aislado previo sigue aplicando; no sustituye G07 integrado. |
| G03 tooling | Completo | Revalidación BFF/TS/lint actual; suites workflow, scanner, scope guard y análisis estático siguen por hashes compatibles. |
| G04 F1 | Completo | Evidencia estructurada S12 continúa aplicando; no hubo cambio en el control de Docker/F1. |
| G05 snapshot completo | Completo | S18 renovó el snapshot para el runtime corregido: exit 0, 18 archivos (17/17 sources + manifest), productor/receptor/verificador 0, permisos exactos, sin symlinks; container y volumen preservados. Evidencia `h3req1_c03_source_snapshot_2026-10-10_s18.md`. S16/S17 permanecen intactos. |
| G06 Pages/workerd | Completo | S16 exit 0: digest de dependencias PASS, healthz real `workerd=true`/Pages root asset (22 intentos), smoke PASS, OOM false, red interna sin endpoints. Contrato 7/7, recovery 9/9; runtime temporal retirado por ID exacto; S15, S18 y S11 preservados. Evidencia `h3req1_c03_startup_smoke_2026-10-10_s16_diagnostic.md`. |
| G07 C03 integrado | Completo | R51 PASS local con Pages/workerd, Edge, PG17 y PostgREST; manifiesto verifica 128 rutas y sus inputs siguen coincidiendo para este candidato. Evidencia `h3req1_c03_integrated_r51_preparation_2026-10-10.md` y log sanitizado `h3req1_c03_integrated_run_2026-10-10_r51.txt`. R49 y R50 permanecen históricos; R50 FAIL no se reutiliza. |
| G08 checks finales | Completo | Pytest vigente 335 passed/4 skipped, contrato credenciales 43/43, scanner/writer scan, ESLint, typegen/TS, 176 Python AST, auditorías npm full/prod sin vulnerabilidades y builds previos normal/mock. R69 revalidó build normal: 33/33 páginas, 17 rutas sintéticas y 206 artefactos verificados; R72 renovó sintaxis/scanner del runner, R73 probó dos casos Python afectados (2/2), y R76 renovó BFF UAT (96 checks, confirmado también sin red); R83 renovó `node --check` y credential scan focal del runner UAT con SHA coincidente entre checkout y contenedores. Las pruebas live/credenciales no se ejecutaron. Evidencia `evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md` y deltas R70/R72/R73. |
| G09 aceptación local | Parcial | R108 conserva edición/procedencia/auditoría; R8 resolvió INV-008 con ciclo reproducible `password_pending` y pasó onboarding sintético 10/10, sin repetición. R135 H3-UAT-070 pasó cuota integrada (3/3 viewports, 24 assertions); R139 H3-UAT-034 pasó refresh/rotación/expiración (3/3, 42 assertions, sin tokens en salida). R141/R142 completan LOCAL-01: 31 filas PG17, 16 identidades elegibles conciliadas lector→artifact→listing/detalle, 15 no elegibles excluidas/404. R140 pasa atomic cleansing PG17 y amplía LOCAL-07/08/19. R142 amplía catálogo a 71 casos y suma H3-UAT-071 3/3. LOCAL-01, 09 y 17 completas en el fixture descrito; quedan parciales LOCAL-03/07/08/16/19/23. R127 se conserva como predicado de test excesivo; R134/R136/R137 y comparator R141 conservan errores del oráculo/comparador. UAT R12 Pages/workerd :3330 + mock :3331, Chromium 1228 headless. Evidencia [R140–R142](evidencia/h3req1_g09_local_acceptance_delta_r140_r142_2026-10-11.md). G09 no GO. |
| G10 CI remoto | Pendiente | Requiere integración/enforcement/revisión humana fuera de esta autorización local. |

### Delta actual R143/R144 — G08 revalidado; G09 en ejecución — 2026-10-11

R143 generó un artifact normal actual desde las 63 fuentes web verificadas del
candidato: manifiesto de contenido
`ec9001e3d26939c638e3bb7f535eeb1aae7eb7a197e94438b909ca807d82f242`, 201 archivos
y 16 rutas de detalle; build, mock build, lint, typegen y TypeScript terminan
exit 0. Writer scan PASS, prueba focal 4/4 y credential scan PASS. Los checks
G08 restantes se reutilizan por inputs coincidentes con R142; no se repitieron.
R144 añadió un ensayo PG17.11 aislado de checkpoint/resume, cleansing,
enrichment malformado/recovery y sync idempotente del mismo URL: exit 0. El
runner SQL usa migraciones versionadas y estático ShellCheck PASS.

La primera corrida UAT R143 se detuvo tras 114/213 por usar `127.0.0.1` en vez
del origen configurado `localhost`; se preservaron seis ejecuciones no-PASS de
cuatro casos y 119 capturas en `uat-r143-invalid-host-partial/`. No se cuentan
como resultado del candidato ni se atribuyen a producto. La corrida corregida
está en `uat-r143-candidate-full71/`, con Pages/workerd R12 aislado en puertos
3370/3371/3373, Chromium 1228 headless, `localhost` y cero retries. En el último
checkpoint: 12/213. El acceso Windows `127.0.0.1:3333` y R12/PG17 se conservan.

LOCAL-07/08/19 avanzan con persistencia real de PostgreSQL sintético, sumada a
R2/R18/R140; la prueba R144 no llama crawler exterior, LLM ni writers cloud.
LOCAL-03/16 aún requieren mutación→rebuild→lectura posterior con el mismo
registro; LOCAL-23 espera UAT, revisión final y aceptación. G09 sigue parcial;
tablero G01–G10 permanece en 80% y cierre local G01–G09 en 8/9 (88,89%). No
declarar GO. Detalle R143/R144:
[evidencia actual](evidencia/h3req1_g08_g09_current_candidate_r143_r144_2026-10-11.md).

### Delta vigente G09 R130–R133 — expiración Auth local — 2026-10-11

H3-UAT-034 se amplió solo en el runner existente para probar expiración sintética
Auth en navegador, rechazo de sesión BFF, borrado de cookies HttpOnly y RPC
protegido denegado. INV-008 ya está resuelto en R8; no se repitió. R130–R132
se preservan como FAIL del ensayo acoplado a la cola Admin; telemetría allowlisted
mostró `rpc_failed` 502 en solicitudes de la cola iniciadas antes del límite del
reloj virtual. R133 dejó la página Admin y ejecutó el probe en Privacidad: 3/3
viewports, 27/27 assertions, 3 capturas, vídeo desktop, cero retries/errores de
consola/requests. El resultado demuestra expiración del mock Auth, no refresh
concurrente ni Auth remoto. No cambia porcentajes: G09 sigue parcial.

R12 continuó con Pages/workerd local en `127.0.0.1:3330`, mock local en
`:3331`, PG17 sintético y Chromium 1228 headless en Docker; no se abrió ventana.
Evidencia: [delta R130–R133](evidencia/h3req1_g09_local_acceptance_delta_r130_r133_2026-10-11.md).

### Delta vigente G09 R134–R139 — cuota y refresh concurrente — 2026-10-11

R134 conservó 0/3 como error del oráculo: esperaba el código interno de cuota,
pero el contrato BFF expone `rate_limited` y el HTTP 429 era intencional. El
runner se ajustó solo para el error público esperado; R135 pasó H3-UAT-070 en
3/3 viewports, 24/24 assertions, con estado/versión/auditoría sin cambios.
R136/R137 conservaron dos expectativas incorrectas del runner (headers
`Set-Cookie` normalizados y `sessionId` interno en el DTO público), corregidas
sin cambiar producto.

R138 pasó expiración/refresh observado, pero todavía no verificaba la rotación
del par opaco. R139 añadió huellas SHA-256 calculadas en memoria y confirmó
rotación access/refresh, renovación de vencimiento, AAL2 en tres lecturas
paralelas y rechazo/cookies limpias/RPC 401 al expirar el fixture: 3/3
viewports, 42/42 assertions, tres capturas y vídeo desktop, sin retries ni
errores de consola/requests. Se preservan todos los intentos rojos.

El preflight estructural y `node --check` pasan en R12; scanner focal pasa en
`studiamatch-dev`. La primera invocación de `H3_VALIDATE_ONLY` en
`studiamatch-dev` terminó exit 1 por falta de Playwright en ese contenedor; no
se instaló nada y el preflight se completó en R12, con SHA del runner igual al
checkout y `studiamatch-dev`. R12 Pages/workerd, Auth/PostgREST mock, PG17
sintético y Chromium 1228 headless se conservaron. INV-008 no se repitió: R8
ya acredita su causa reproducida y onboarding 10/10. No cambian métricas de
gate: histórico G01–G10 80% (8/10), cierre local G01–G09 88,89% (8/9). Ver
[delta R135–R139](evidencia/h3req1_g09_local_acceptance_delta_r135_r139_2026-10-11.md).

### Delta vigente G09 R140–R142 — 2026-10-11

R140 ejecutó `tests/sql/run_fase10_8_atomic_cleansing_postgres.sh` una vez en
PG17.11 desechable, exit 0: atomicidad, upsert, metadatos, estados, idempotencia
y permisos del RPC. El contenedor exacto se retiró; log e identidad se
preservan. No acredita todo el pipeline.

R141 cotejó 31 filas sintéticas PG17: las 16 elegibles coinciden por ID,
institución y slug con el lector público; sus 16 rutas de detalle son 200 y
propias, las 15 no elegibles responden 404 y las 16 rutas aparecen en el
artifact estático R69. Un comparador inicial mezcló rutas absolutas y relativas
y produjo 32 diferencias; el rojo queda preservado. Tras corregir el formato,
el mismo artifact/PG17 dan 16 rutas y cero diferencias.

R142 agregó H3-UAT-071 al runner (71 casos) y pasó el listing 16/16 en páginas
12+4: 3/3 viewports, 18/18 assertions, tres capturas y vídeo desktop, cero
errores/retries/egress externo. `node --check`, validación estructural y
credential scanner pasan. Dos errores de despacho/ruta de evidencia quedaron
registrados; ambos ocurrieron antes de abrir el navegador. La fuente actual
del runner tiene SHA-256
`08cf76f22f211fccb325bdd6ab90eb132e238435d982d0419f36fb2b2e9a321c`.

LOCAL-01 queda completa para inventario sintético actual. LOCAL-03 continúa
parcial por mutación→rebuild/cache/reset del mismo registro; LOCAL-07/08/19
continúan parciales por checkpoint/recovery integrado de discovery, enrichment
y sync en PG17. No hubo cambio de producto. Métricas sin cambio: G01–G10
80% (8/10), G01–G09 88,89% (8/9). Detalle: [R140–R142](evidencia/h3req1_g09_local_acceptance_delta_r140_r142_2026-10-11.md).

### Corte histórico G09 R57–R58 — 2026-10-11

R49 conserva el rojo y las 189 ejecuciones visuales son una selección de PASS
compatibles entre corridas, no una corrida única. R55/R56 renovaron 063/034;
R8 ya corrigió INV-008 como defecto del ciclo login/guard y pasó 10/10. R57
ejecutó 050/055 × tres viewports y terminó exit 1, 2/6 PASS: 055 usó
`id=eq` no soportado por el mock y omitió el filtro; 050 tuvo un 403 móvil sin
código conservado. R58 corrigió solo el filtro de prueba, añadió telemetría
allowlisted y pasó 050/055 6/6, seis capturas, cero retries. El 403 no se
reprodujo y permanece sin causa atribuida.

LOCAL-07 añadió recovery de `paginated_catalog` y `catalog_link_extraction`,
2/2 PASS; el pytest de proyecto vigente queda en 333 passed/4 skipped. La
matriz identifica LOCAL-04/11/15/18/21 completos en sus subalcances y las
otras áreas pendientes por acción concreta. G09 permanece parcial y no se
declara GO. Evidencia: `evidencia/h3req1_g09_local_acceptance_delta_r58_2026-10-11.md`.
Windows: `http://localhost:3336/` (app R12 + datos PG17 sintéticos, sidecar R47
GET/HEAD en loopback); Playwright no abrió ventana. Capturas y hashes de R58
están bajo `evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-focused-r58-audit-compare-diagnostic/`.

### Corte histórico G08/G09 R64–R70 — 2026-10-11

El full pytest del proyecto terminó exit 0 con 335 passed, 4 skipped y 1
warning; ESLint focal, TypeScript, node syntax y scan focal de credenciales
pasaron. R69 normal build generó 33/33 páginas, 17 rutas de datos sintéticos y
206 artefactos verificados. Actionlint, ShellCheck, workflow protegido, scope
guard, H2 writer scan y auditorías npm se reutilizan solo por inputs compatibles.
Las pruebas live/credenciales no se ejecutaron.

LOCAL-05 quedó completo para la comparación actual: R70 pasó H3-UAT-049 y
H3-UAT-064 en desktop/tablet/móvil, 6/6 ejecuciones y 96/96 assertions. Se
verificó el fallback Por confirmar con campos opcionales ausentes, datos
poblados distintos y la ruta pipeline/Admin/publicación/público. Se guardaron
seis capturas y vídeo desktop. El catálogo vigente 64×3 se concilia con 192
combinaciones PASS seleccionadas; no fue una sola corrida global. G09 sigue
parcial por LOCAL-01..03,06..10,12..14,16..17,19..20 y 22..23. La métrica no
cambia: 80% histórico (8/10), 88,89% cierre local (8/9), delta 0 pp. G10
remoto sigue pendiente.

Se preservan R63/R65/R66/R68 con causas de harness/fixture; R69 incluyó las 17
rutas sintéticas que consume R12, y R70 pasó sin errores de consola/requests ni
retries. Chromium 1228 corrió headless dentro de Docker, sin ventana. El
runtime R69 temporal se detuvo por PID verificado y sus puertos quedaron libres;
R12, PG17 sintético y el acceso Windows `http://localhost:3336/` siguen activos.
Detalle: `evidencia/h3req1_g09_local_acceptance_delta_r64_r70_2026-10-11.md`.

### Delta vigente R71–R76 — 2026-10-11

R71 de H3-UAT-065 pasó inicialmente, pero su aserción de aislamiento era
tautológica; queda preservada y no se contabiliza. R72 corrigió esa aserción y
ejecutó solo ese caso en desktop/tablet/móvil: 3/3, 69/69 aserciones, tres
capturas, cero errores de consola/requests/retries. Chromium 1228 headless;
Pages/workerd Miniflare usó el export normal R69 y REST sintético interceptado.
No hubo acceso PG17 en R72.

R73 ejecutó en Docker solo dos pruebas antes no presentes en el resultado R18:
fallo posterior de página y de scroll, con recuperación de URLs únicas; exit 0,
2 passed, cero retries, una advertencia PyPDF2. El hash de la fuente coincidió
entre host y `studiamatch-dev`; los adaptadores fueron en memoria, no PG17. La
prueba amplía LOCAL-07/08 pero no cierra persistencia integrada. Evidencia:
`evidencia/h3req1_g09_local_acceptance_delta_r71_r72_2026-10-11.md` y
`evidencia/h3req1_g09_local_acceptance_delta_r73_2026-10-11.md`.

El catálogo queda en 65 casos × 3 viewports y 195 combinaciones PASS elegidas
entre corridas (no una sola ejecución). El total de gates no cambia: G01–G10
80% (8/10) y cierre local G01–G09 88,89% (8/9), delta 0 pp. G09 continúa
parcial; G10 remoto separado. El acceso Windows preexistente
`http://localhost:3336/` respondió 200 y no se recreó.

R74 leyó en transacción PG17 `READ ONLY` una fila sintética y comparó su
ID/institución/nombre/slug/URL con el artefacto R69 y el detalle servido por el
loopback Windows R12/R47; los tres predicados de identidad pasaron. Los campos
provider/duration eran nulos y quedaron fuera del cotejo. No se probó
invalidación de caché tras una edición; LOCAL-01/03/16 siguen parciales. Ver
`evidencia/h3req1_g09_local_acceptance_delta_r74_2026-10-11.md`.

R75 releyó la evidencia G03 de la cookie de actividad contra el SHA actual del
runner BFF (`378f753d…`), coincidente con source manifest R4. Sus 90 checks
incluyen rechazo de actividad de sesión A al presentar sesión B, expiración y
tamper, flags/limpieza de cookie y rebind MFA. Se actualiza la matriz LOCAL-09:
estos subcasos no están pendientes, pero expiración Auth/browser, cookies
multi-chunk y refresh concurrente end-to-end siguen sin prueba. No se repitió la
suite ni cambió código. G09 y las métricas permanecen parciales/sin delta. Ver
`evidencia/h3req1_g09_local_acceptance_delta_r75_2026-10-11.md`.

R76 amplió el test existente de logout para incluir cookie base, tres chunks Auth,
code-verifier base y dos chunks del verifier. El BFF UAT actual pasó 96 checks
en `studiamatch-dev` sano con `env -i`; el SHA en host y `/app` coincidió,
`node --check` y scanner focal pasaron, cero retries. La implementación BFF no
cambió. `git diff --check` dentro del contenedor falló por el puntero Git al
worktree host (exit 128); el chequeo read-only desde WSL pasó exit 0. El
preflight con marcador literal de SHA fue detenido antes de ejecutar; la
invocación corregida pasó. Quedan expiración Auth y refresh concurrente en
browser, por lo que LOCAL-09 y G09 siguen parciales. Ver
`evidencia/h3req1_g09_local_acceptance_delta_r76_2026-10-11.md`.

### Métrica vigente tras cierre G08 — 2026-10-11

G08 cierra con evidencia del candidato de 1.067 inputs, manifiesto SHA-256
`30d1a237323c3d68049dc194a37393fc01359f8a135ec15400db4a419a4522c0`, además de
las pruebas compatibles identificadas en su nota. El build normal R6 terminó
en exit 0 dentro del contenedor y verificó 126 artefactos. El wrapper marcó
exit 1 por una discrepancia de regex en el resumen del proxy; se conservó ese
resultado y un postflight read-only independiente validó build, hashes, cleanup
y servicios Windows. No se modificó producto en este delta.

El tablero G01–G10 queda en 80% (8/10 completos); G01–G09 en 8/9 = 88,89%.
Delta desde 70% / 7/9 = 77,78%: +10 pp / +11,11 pp. G09 sigue parcial por
LOCAL-01..03,06..10,12..14,16..17,19..20 y 22..23. No hay GO local ni autorización remota.
G10 remoto permanece separado.

Pruebas local G08 y salida: `evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md`.
Postflight R6: `evidencia/h3req1_g08_candidate_final_2026-10-11_r1/normal-build-r6-postflight-reconciliation.log`.

### G09 delta R6 — onboarding y acceso Windows (corte histórico) — 2026-10-11

El onboarding sintético R6 coteja los inputs actuales: 643 fuentes y build mock
de 126 archivos. La pasada diagnóstica V2 terminó exit 0, 10/10 casos PASS,
cero retries y 10 capturas verificadas; las respuestas BFF/worker observadas
fueron 200 y el callback Auth BFF 303. Browser Chromium 1228 headless dentro
del app R6; Pages/workerd, mock Auth y PostgreSQL 17.11 corrieron en red Docker
interna. Evidencia completa, capturas y hashes:
`evidencia/h3req1_g09_onboarding_r6_windows_access_2026-10-11.md`.

El resultado no cierra G09: el runner inicial quedó en
`ONBOARDING_TEST_FAILED`; una continuación diagnóstica alcanzó la captura
`FAIL-INV-008` en “Validando acceso…” y su filtro de salida anterior rechazó el
formato. La V2 pasó sin cambio funcional entre el fallo y el PASS, por lo que
la discrepancia sigue sin causa probada. Se conservan los dos intentos y no se
declara estabilidad por repetir. R6 app quedó detenido; su PG17 y red interna
se preservan.

Windows conserva el acceso existente a la app UAT R12 en
`http://127.0.0.1:3333/` y al curso sintético
`/courses/ulima/analitica-aplicada-60000000/`: proxy loopback, Pages/workerd y
PG17 R12 respondieron HTTP 200, con una fila coincidente para el curso de ID
`70000000-0000-0000-0000-000000000091`. No se recrearon servicios para
publicar el acceso. El onboarding R6 usa otra base sintética y queda sin puerto
publicado, separado de la revisión Windows. El delta no modifica las métricas:
G01–G10 70%, G01–G09 7/9=77.78%, delta 0 pp; G09 permanece parcial.

### G09 delta R8 — INV-008 y acceso Windows al mismo fixture — 2026-10-11

R6 fue diagnosticado después del PASS anterior: la sesión Auth `password_pending`
entraba en un ciclo `/admin/` ↔ `/admin/login/`. El guard Admin rechaza el rol
`authenticated` hasta terminar setup; login redirigía cualquier sesión de vuelta
a Admin. Se preserva el rojo. La corrección de `web/src/app/admin/login/page.tsx`
consulta el estado de onboarding y envía la sesión pendiente a aceptar invitación;
el caso en `tests/h3_invitation_uat.mjs` ahora verifica destino, mensaje, CTA y que
no se muestre el panel antes del password.

El runner R8, con inputs del candidato actuales y PG17.11 sintético retenido,
terminó exit 0: INV-013/008/001/002/009/007/003/004/005/012, 10/10 PASS, diez
capturas con hashes, un vídeo del flujo principal y cero retries. Chromium 1228
corrió headless. Detalle, topología, fallos de bootstrap y evidencia en
`evidencia/h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md`.

Windows verificó HTTP 200 en `http://127.0.0.1:3334/`, mismo Pages/workerd y
PostgreSQL sintético del onboarding; proxy GET/HEAD, POST 405, host binding solo
127.0.0.1. El PG17 R7 se conserva; el proxy usa una red bridge dedicada para
publicar solo loopback y conecta al runtime por su red interna. No se cargaron
credenciales reales ni hubo writes remotos. LOCAL-11 queda cerrado para esta
matriz; G09 sigue parcial, G08 sigue pendiente y las métricas permanecen
G01–G10 70%, G01–G09 7/9=77.78%, delta 0 pp.

### G08/G09 delta R9–R10/R41 — build final y membresías — 2026-10-11

R9 ejecutó el build normal del candidato en Docker: exit 0, 17/17 páginas y
126 artefactos. R9 también documentó un fallo del dispatcher mock (exit 254)
porque lanzó `npm run build:mock` desde `/app` en vez del snapshot; se preservó
como defecto del harness. R10 corrigió únicamente el cwd y el build mock pasó:
17/17 páginas, 126 artefactos. Ambos builds usaron el mismo input allowlisted
de 57 archivos, SHA-256
`3894b6c5807677736c0c963b6ff8caed24dbda701489e5960dd2f9fc007293ab`; no hubo
pull ni instalación. Reconciliación:
`evidencia/h3req1_g08_candidate_final_2026-10-11_r2/normal-mock-builds-r9-r10-reconciliation.log`.

R41 resolvió un defecto real de la tabla de membresías: con la región enfocada,
ArrowRight no desplazaba las columnas recortadas. El diagnóstico R40 había
separado ese defecto del montaje 404 de R39. La región Admin ahora anuncia su
nombre, recibe foco y recorre horizontalmente con ambas flechas; R41 verificó
H3-UAT-040 en desktop/tablet/móvil: 3/3 viewport PASS, 51/51 assertions, cero
retries, requests fallidos o errores de consola. El test cambió rol, desactivó
y reactivó un miembro sintético, confirmó la protección del último admin y
restauró el estado original en `finally`. Chromium 1228 fue headless dentro del
contenedor UAT; capturas por viewport están en
`evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-targeted-r41/`.
No se generó vídeo en R41. El mismo runtime/PG17 sintético queda accesible por
`http://localhost:3335/admin/login/` mediante el sidecar loopback
`h3req1-g09-localhost-proxy-r41` (ID `2d579168976e`), sin recrear app ni DB.
Login y Admin/users responden 200; lectura same-origin responde 200; negativos
cross-site de lectura/escritura responden 403. El viejo `:3333` sigue en R12.
Revisión y límite LOCAL-10/20:
`evidencia/h3req1_g09_uat_2026-10-11_r41_membership_keyboard.md`.

Postflight loopback del 2026-10-11: `localhost:3335/`, `/admin/login/` y
`/admin/users/` responden 200; el detalle pipeline del fixture PG17 R12 responde
404 en ese bundle R41. La misma ruta responde 200 por el runtime R12 existente
en `127.0.0.1:3333`, que usa un bundle estático distinto; la solicitud con Host
`127.0.0.1:3335` recibe 421 por la allowlist de Host `localhost:3335`. Por eso
el acceso Admin R41 y la ruta pública R12 no se presentan como una única versión
estática ni se usa el smoke de loopback para cerrar LOCAL-03/16. Evidencia
sanitizada: `evidencia/h3req1_g09_windows_loopback_r41_postflight_2026-10-11.md`.

El delta de UI se revalidó en Docker con ESLint (exit 0, nueve warnings
conocidos), Next typegen y `tsc --noEmit` PASS, scanner acotado PASS y sintaxis
del runner PASS. Los checks no afectados se reutilizan solo con sus inputs
compatibles anotados en `evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md`.
G08 sigue completo. G09 continúa parcial: R41 amplía LOCAL-10/20, pero quedan
concurrencia de membresías y las áreas funcionales parciales/faltantes de la
matriz. G01–G10 se mantiene en 80% (8/10); G01–G09, 8/9=88.89%. No hay GO local.
El total no aumenta por R41 porque G09 sigue abierto; R9/R10 son evidencia
convergente del G08 ya cerrado.

### Estado actual de ejecución y WIP

Rama/HEAD: `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. El WIP no se identifica solo por
HEAD: al final de la preparación hay 60 rutas tracked modificadas, 795 entradas
untracked visibles en `git status`, cero staged y 14.272 archivos enumerados
con `git ls-files --others --exclude-standard`. Ninguno se limpió ni se alteró
de forma indiscriminada. El borrador PR separa las 84 rutas de cambio propuestas
de evidencia, artefactos y fixtures locales excluidos. El contenido SHA-256 de
las 84 rutas seleccionadas (60 tracked modificadas y 24 untracked) está fijado
en `evidencia/h3req1_pr_scope_manifest_2026-10-11.json`; su digest se registra en
el borrador PR. El resto del WIP queda fuera del alcance propuesto, preservado y
no incluido.

### G09 — delta de discovery/pipeline R18

En `studiamatch-dev`, R7 cubrió negativos de discovery/gates, el walk y fallo/
recovery del RPC de cleansing: 13/13 PASS. Los rojos previos demostraron
aceptación de esquemas no HTTP(S) y `<loc/>` como `None`; el parser ahora omite
loc vacíos y solo acepta HTTP(S). El fallo de cleansing dejó staging `pending`
sin fallback ni fila parcial y el mismo input se recuperó con una fila.
R10 añadió fallo/recovery del RPC atómico de enrichment e idempotencia por
`cleansed_id`; R12 añadió fallo antes del upsert de curso, recuperación y
repetición idempotente por URL. El fallo de sync conserva `pending` y no crea
curso; la recuperación deja `synced` y una sola fila. R13 reprodujo que el
circuit breaker acumulaba 403/429 a través de HTTP 200 y abría fuera del
umbral consecutivo. El cambio mínimo resetea el contador al recibir una
respuesta HTTP distinta de 403/429; dos bloqueos consecutivos siguen abriendo
y persistiendo el circuito. R14 añadió la prueba del `main` con discovery gate
cerrado: sale 0, sin discovery ni writes. R15 añadió la ruta con gate activo y
fallos de discovery totales: `exit 1` antes de scraping/escrituras. Resultado
R15: 19/19 PASS, 1 warning PyPDF2, cero retries. R16 añadió pruebas del flujo
completo para `hardcoded_urls`, catálogo paginado y extracción de enlaces:
deduplica seeds equivalentes, registra solo URL interna válida y deja la página
del browser cerrada. Los transportes y navegador son sintéticos. R16 terminó
22/22 PASS, 1 warning PyPDF2, cero retries. R17 demuestra que una fila
`discovered` preexistente vuelve a la lista de resume sin nueva inserción y que
una fila `pending` permanece protegida. R18 prueba discovery-only con pipeline
apagado: `exit 0`, sin scraper ni telemetría. R18 combinado terminó 24/24 PASS,
1 warning PyPDF2, cero retries. R8/R9/R11 y el fixture
fallido de `main` en R13 quedan preservados y clasificados en el handoff; R11
fue el guard SSRF trabajando correctamente, no un defecto de producto. Resto
de LOCAL-01..23 continúa pendiente.
Evidencia:
`evidencia/h3req1_g09_uat_2026-10-10_r4/local-pipeline-walk-r2-handoff-2026-10-11.md`.
Windows PowerShell también recibe HTTP 200 para el detalle sintético
`http://127.0.0.1:3333/courses/ulima/analitica-aplicada-60000000/`.

### G09 — filtros públicos y acceso Windows; R23 rojo, R24 canónico PASS, D25/D26 suplementarios

La app UAT existente `h3req1-g09-uat-app-20261010-r12` se mantuvo activa; el
proxy `h3req1-g09-localhost-proxy-r12` conserva el binding exclusivo
`127.0.0.1:3333` al Pages/workerd interno 3330 y a la misma PG17 sintética.
Curso usado: “Analítica Aplicada”, ID
`70000000-0000-0000-0000-000000000091`; no hubo recreación ni escrituras.
R23 dejó dos fallos al limpiar búsqueda (desktop/tablet) y comparador 3/3 PASS.
R24 canónico pasó H3-UAT-059 y H3-UAT-060 en los tres viewports (6/6). La causa
de los fallos quedó identificada en el cambio WIP previo a R24: “Limpiar todo”
vaciaba `searchTerm`, pero dejaba `searchInput`; el debounce de 300 ms podía
volver a aplicar el texto obsoleto tras limpiar el URL. El handler actual
limpia ambos estados. R28 volvió a pasar H3-UAT-052/053/059/060/061/062 en los
tres viewports. D25/D26 son diagnósticos suplementarios y no incrementan gates.
Chromium 1228 corrió headless en el contenedor de la app; las capturas se
preservan en `evidencia/h3req1_g09_uat_2026-10-10_r4/uat-functional-r24/` y
`.../uat-functional-r25/`.
Detalle, SHA-256, enlaces y limitaciones en
`evidencia/h3req1_g09_filters_windows_access_r24_r26_2026-10-11.md` y
`evidencia/h3req1_g09_windows_access_combined_filters_r31_r33_2026-10-11.md`.

El corte antes de S16 era G01–G10=50% y G01–G09=5/9=55.56%. S16 cerró G06
y R51 cerró G07: estado actual G01–G10=70% y G01–G09=7/9=77.78%. Delta
acumulado desde ese corte: +20 pp en el tablero histórico y +22.22 pp en el
cierre local. R28/R29/R30 dejan la cobertura visual del catálogo en un PASS por
cada ejecución; R24 y R28 también pasan la cobertura focal de filtros, con el
rojo R23 preservado y su causa funcional identificada. G09 sigue parcial por las 23 áreas
funcionales y criterios restantes; esta cobertura no suma puntos. Revisión,
documentación, acceso localhost y pruebas focales no suman puntos por separado.

R49 PASS histórico y compatibilidad (125/127), R50 FAIL y R51 PASS quedan
registrados en sus evidencias respectivas. UAT r27 cubrió cinco casos del
focal r26; R28/R29/R30 concilian los 63 casos × tres viewports, preservando
fallos iniciales. La primera conciliación de `LOCAL-01..LOCAL-23` está en
`evidencia/h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md`;
siguiente, ejecutar las coberturas marcadas parciales/faltantes y continuar
G08/G09 según resultados. R18 conserva recovery/idempotencia de cleansing,
enrichment y sync, el circuit breaker consecutivo y 24 pruebas focales
discovery/pipeline PASS en Docker. Evidencia y logs
R1/R2/R3/R4-red/R5/R6/R7–R18:
`evidencia/h3req1_g09_uat_2026-10-10_r4/local-pipeline-discovery-r*.stdout.txt`.
G10, deploy, integración protegida y pruebas Development siguen fuera de alcance.

## Corte histórico — validación local H3REQ1 G01–G09 declarada completa — 90% — 2026-10-10

Este corte precede al hallazgo/reparación de sesión documentados arriba. Sus
resultados y recursos se conservan como evidencia histórica; su tabla y GO no
representan el candidato actual y no satisfacen los gates G05–G09 vigentes.

El usuario autorizó en esta sesión culminar la validación **local** H3REQ1 en
`/home/romel/src/studiamatch-h3req1-sync-20261002`, exceptuando para este ciclo únicamente la
solicitud documental de JIT local. La excepción no cambia AGENTS ni habilita commit, push, PR,
merge, CI remoto, workflow_dispatch, servicios remotos, secretos, cuentas/datos operativos,
checkout original, limpieza global o cambios del Docker engine. El checkout original
`/home/romel/src/studiamatch` queda preservado.

El usuario amplió explícitamente el 2026-10-10 la autorización a todas las operaciones
estrictamente locales necesarias para completar G01–G09 en este candidato, incluidos cambios de
tooling/tests, snapshots, Docker fixtures H3 aislados, PostgreSQL 17 desechable y sus migraciones,
builds/descargas fijadas y pruebas locales. Esta excepción reemplaza únicamente JIT documental
local dentro de ese alcance; no cambia las políticas del revisor ni autoriza secretos, checkout
original, datos/cuentas/correo operativos, Git/CI/PR/merge, servicios remotos, deploy, cambios de
engine o limpieza global. No se solicitarán permisos adicionales por comando/hash local dentro de
este ciclo.

Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP actual: 741 entradas con `git status --short`,
0 staged, 55 rastreados modificados y 686 untracked. Incluye evidencia, runners y contratos de
esta continuación. Se preserva todo, sin reset ni clean; el checkout original
`/home/romel/src/studiamatch` no recibió escrituras y conserva 78 entradas de estado. No se
infiere la identidad del candidato desde HEAD.

### G07 vigente — R46 C03 integrado PASS local

R46 se ejecutó una vez con timeout 2400 s y cero retries. El log sanitizado termina en
`C03 integrated drill: PASS`; SHA-256
`0fefdb22984226124a2847c8f9f4a01923a2396569b01309db8239f30b4f1a00`. El probe PostgREST
encontró exactamente una fila; request ID, actor, correo, rol y user ID coinciden; status
`PENDING`, entrega `COMPLETED`, sin reconciliación pendiente. Edge replay aceptó la misma
invitación, no llamó Auth por segunda vez y devolvió sesión AAL2/rol admin. Pasaron las
assertions de suspensión, denegaciones y nonce, finalización in-flight una vez, auditoría/cuota,
resume en nueva conexión, SQL final y smoke. Ver [resultado/inventario R46](evidencia/h3req1_c03_r46_result_inventory_2026-10-10.md),
[log](evidencia/h3req1_c03_integrated_run_2026-10-10_r46.txt) y [manifiesto archivado](evidencia/h3req1_c03_integrated_manifest_r46.sha256).

La causa de R45 fue el role sintético: `service_role` se creaba NOLOGIN sin `BYPASSRLS`; RLS estaba
activo en `admin_invitations`, SELECT era solo para ese rol y no había policy. Se corrigió solo el
setup PG17 desechable con `ALTER ROLE service_role BYPASSRLS` y aserción de `pg_roles.rolbypassrls`;
no cambian producto, migraciones ni políticas remotas. El contrato R46 fue rojo 34/35 antes del SQL
y verde 35/35 después; Bash/Node syntax, ShellCheck 0.11.0, `git diff --check` y manifiesto
126/126 PASS. El runner retiró siete contenedores y dos redes por IDs exactos; snapshot/TLS/caches
e imágenes siguen preservados. `studiamatch-dev` permanece healthy.

R45 también retiró siete contenedores detenidos y dos redes vacías tras archivar evidencia; se
preservan sus volúmenes snapshot/TLS y caches. El despacho inicial R45 terminó exit 77 antes de
Docker por un pin mal tipeado; la relectura mecánica permitió la ejecución única autorizada.
Un intento de regenerar el manifiesto que incluía `rm -f` fue rechazado automáticamente antes de
ejecutarse; se usaron temporales retenidos en `/tmp`. Detalles en la preparación e inventario R45.

### G08 vigente — checks finales locales

Pytest del proyecto: 307 passed, 4 skipped por requerir API/credenciales live y una advertencia
de deprecación PyPDF2. Builds normal y mock completaron 17 rutas; cada export tiene manifiesto
verificado de 126 archivos. r9 V5 cerró ShellCheck, ESLint, typegen, TypeScript con 4 GiB y heap
Node 3072 MiB, actionlint reutilizado por hashes idénticos, suite de workflow protegido, scanner
de credenciales y scope guard. Los audits npm full/production R7 informaron cero vulnerabilidades
con egress allowlisted, retries 0 y captura separada read-only/output. El audit R6 se invalidó tras
revisión por riesgo de solapamiento de mounts; R7 corrigió ese diseño y recibió revisión estática
independiente PASS. Véanse [cierre local G01–G09](evidencia/h3req1_validacion_local_g01_g09_2026-10-10.md),
[r9 V5](evidencia/h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v5.txt) y
[audit R7](evidencia/h3req1_g08_npm_audit_2026-10-10_r7/output/npm-audit-r7.log).

### G09 vigente — aceptación local

UAT sintético R11: 48 casos × tres viewports, 144/144 PASS y 144 capturas con hashes verificados,
retries 0. Onboarding separado R5: 10/10 PASS, retries 0, sin tocar la cuenta existente ni usar
correo real. El harness PG17 editorial actual pasó en ambos runners. Los cuatro criterios del
cliente y sus límites están reconciliados en el [cierre local](evidencia/h3req1_validacion_local_g01_g09_2026-10-10.md).

### G01–G10 y métrica actual

| Gate | Estado | Evidencia / pendiente |
|---|---|---|
| G01 SQL/editorial | Completo | Harness editorial PG17 y cierre SQL vigente; la corrección R46 afecta solo setup de integración C03. |
| G02 suspensión SQL | Completo | C03 SQL aislado v3, 41/41 inputs; G07 añade integración Pages/Edge/PG17/PostgREST. |
| G03 tooling | Completo | r9 V5 y validaciones focales aprobadas con inputs compatibles; R46 renovó contrato/ShellCheck del runner. |
| G04 F1 | Completo | Verificador/copia F1 acreditados en S12. |
| G05 snapshot completo | Completo | S12 PASS con productores/receptores/verificación y symlinks/modos. |
| G06 Pages/workerd | Completo | S9 healthz real PASS; R46 volvió a arrancar Pages/workerd integrado. |
| G07 C03 integrado | Completo | R46 PASS local: aislamiento, suspensión, finalización única, recovery/replay AAL2, SQL final y smoke. |
| G08 checks finales | Completo local | Pytest 307 passed/4 live-gated skipped; r9, escaneos, auditorías y builds normal/mock verificados. |
| G09 aceptación local | Completo local | Cuatro criterios cubiertos; UAT 144/144 y onboarding sintético 10/10, sin retries. |
| G10 CI remoto | Pendiente fuera del ciclo | Control PWI debe instalarse/exigirse por promoción protegida; no se ejecuta aquí. |
| **Histórico G01–G10** | **90%** | G01–G09 completos localmente; G10 remoto pendiente. Inicial 70%, delta +20 puntos porcentuales. |
| **Cierre local G01–G09** | **9/9 = 100%** | Inicial 7/9 = 77.78%, delta +22.22 puntos porcentuales. No significa 100% del proceso de promoción. |

**Validación local H3REQ1 completa: GO para revisión del responsable.** No se declara
`GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`. G10, integración protegida, despliegue Development,
identificación del artefacto remoto y D01–D14 requieren instrucciones separadas; Certification y
Production permanecen fuera de alcance.

#### Historial G07 R41–R44

R41 terminó exit 1 en `/control/recovery` con status Edge 409 y
`errorCodeClass=ABSENT`, tras pasar snapshot, PG17 17.11, bootstrap H2→H3, PostgREST,
Pages/workerd AAL2, reserva, suspensión, dispatcher 403/42501, finalización Auth una vez,
safe-resume y sus assertions SQL. Evidencia e inventario/retirada están en
[R41](evidencia/h3req1_c03_integrated_r41_preparation_2026-10-10.md); log SHA-256
`eaa8e006c497401d77c9f2f0fb814e565fc347c6e7a5a47086adefdadc1479c7`.

La ausencia diagnóstica se debió a un lector incorrecto del **harness**: Edge responde con
`code` de primer nivel; Pages/BFF responde con `error.code` anidado. R42 corrige solo el lector
del replay directo y prueba ambos shapes sintéticamente. No cambia producto, status 200
requerido, SQL ni reintentos. Contrato R42 32/32, Node/Bash syntax, ShellCheck 0.11.0 en imagen
local read-only/network-none y `git diff --check` PASS. El intento de `git diff` en el
contenedor no pudo resolver el puntero `.git` del worktree padre; el check se completó en el
candidato host. Manifiesto R41 archivado exactamente (115 inputs); R42 117/117 PASS, SHA-256
`45c77516393942b00709f50ff7a02578a7d33b7f4f5ef798be17f209918ff33d`. Ver [preparación R42](evidencia/h3req1_c03_integrated_r42_preparation_2026-10-10.md).

R42 se ejecutó una vez, timeout 2400 s, y terminó exit 1 en
`edge-first-pages-last-recovery-smoke`: el replay directo Edge devolvió 409 y el código
allowlisted `INVITE_EARLY_RECONCILIATION_REQUIRED`. Todos los pasos anteriores, incluido
safe-resume y SQL de recuperación, pasaron. Esto confirma el código de negocio, pero aún no
cuál predicado persistido lo produjo. Log sanitizado SHA-256
`cec6e2cd7224289e427591560a67c5948e37101ec989e02d5496ae1e665981a4`; ver [inventario R42](evidencia/h3req1_c03_r42_resource_inventory_2026-10-10.md).

Tras preservar evidencia se retiraron los siete contenedores R42 y dos redes internas vacías
con identidad exacta. Se conservan sus volúmenes etiquetados de snapshot y TLS, todas las
imágenes/caches y `studiamatch-dev`; el PGDATA tmpfs dejó de estar montado al detener PG17.

R43 se ejecutó una vez con timeout 2400 s, exit 1 en `edge-first-pages-last-recovery-smoke`.
Los pasos previos pasaron: snapshot y caches, PostgreSQL 17.11, bootstrap, PostgREST readiness,
Pages/workerd AAL2, reserva, suspensión, denegaciones, finalizador in-flight exactamente una vez,
safe-resume y assertions SQL. Replay Edge: 409 `INVITE_EARLY_RECONCILIATION_REQUIRED`.
El probe obtuvo 404 `PGRST125`, `rowCountClass=NOT_READ`. La causa demostrada es el path del
harness: pidió `/rest/v1/admin_invitations` directamente a PostgREST en `:3000`; PostgREST 13
clasifica PGRST125 como ruta inválida ([documentación](https://docs.postgrest.org/en/v13/references/errors.html#postgrest-error-codes)).
No se atribuye el 409 al producto. Log sanitizado SHA-256
`ec5d23bd171733a98de51bc86f5ba83698a01affe93843f3d903cb9d66b81`, manifiesto R43 archivado
sin cambios, 120 entradas SHA-256
`acc4b2b733998bd6f5e5be1010c7e7c9e8cc72d26f598d5bcc5c93f21443b096`; detalle e inventario en
[resultado R43](evidencia/h3req1_c03_r43_result_inventory_2026-10-10.md).

Se corrigió únicamente el probe a `/admin_invitations`; el contrato R43 y el nuevo contrato R44
pasaron 68/68. Manifiesto R44: 122 inputs, SHA-256
`e25f62b86bd99d2e20cc07e3da09f172d7b3e3dee8f9ba740135b0f3356790c6`, 122/122.
R44 se ejecutó y terminó exit 1 en el replay: probe HTTP 200, filtro JSON `ZERO`; no demostró
fallo del producto. Resultado e inventario se preservan en
[R44](evidencia/h3req1_c03_r44_result_inventory_2026-10-10.md).

`studiamatch-dev` está running/healthy con imagen `studiamatch-h3req1:20261009-v3`; `/app`
monta este candidato y conserva `node_modules`. El estado R44 es antecedente histórico; G07 cierra
por R46 como se documenta en la sección vigente.

### Antecedente inmediato G07 — R39 clasifica el primer fallo de recuperación Edge

R39 pasó snapshot, PG17 17.11, bootstrap SQL H2→H3, PostgREST, login Pages/workerd AAL2,
reserva previa, suspensión persistente, denegación del dispatcher (403/42501 con nonce
preservado), finalización de Auth exactamente una vez mientras SQL seguía suspendido,
safe-resume y assertions SQL recuperadas. Falló exit 1 en `/control/recovery`, con el primer
predicado `RECOVERY_EDGE_REPLAY_STATUS`; el runner anterior no registró status HTTP ni código
Edge. No se atribuye el fallo al producto ni al harness sin esa clasificación.

Log R39 sanitizado SHA-256
`b526908cd89b0b30c440ac184a795a14c23244f31a264258f7b0f39c30ac79d3`; véase
[resultado R39](evidencia/h3req1_c03_integrated_run_2026-10-10_r39.txt),
[preparación R39](evidencia/h3req1_c03_integrated_r39_preparation_2026-10-10.md) y
[inventario/retirada R39](evidencia/h3req1_c03_r39_resource_inventory_2026-10-10.md).
Se retiraron siete contenedores exactos y dos redes internas vacías tras el inventario;
volúmenes, imágenes y `studiamatch-dev` se conservaron. `studiamatch-dev` permanece healthy
en `studiamatch-h3req1:20261009-v3`.

R40 se ejecutó una vez y falló con exit 1 en `/control/recovery`:
`RECOVERY_EDGE_REPLAY_STATUS`, `status=409`, `INVITE_EARLY_HTTP_409`. El clasificador anterior
no incluyó aún los códigos de conflicto definidos por Edge, por lo que no se conoce cuál fue
el motivo; no se cambia producto ni se rebaja la expectativa 200. R40 pasó todos los pasos
previos de R39 y dejó documentado el inventario. Sus siete contenedores y dos redes internas
vacías se retiraron por ID exacto; volúmenes, caches, imágenes y `studiamatch-dev` se conservaron.
Ver [resultado R40](evidencia/h3req1_c03_integrated_r40_preparation_2026-10-10.md),
[log sanitizado R40](evidencia/h3req1_c03_integrated_run_2026-10-10_r40.txt) y
[inventario R40](evidencia/h3req1_c03_r40_resource_inventory_2026-10-10.md).

R41 añadió a la clasificación únicamente códigos 409 conocidos por el contrato Edge y distingue
`ALLOWLISTED`, `UNRECOGNIZED`, `ABSENT` o `STATUS_INVALID`; no emite el valor crudo. Es una
corrección diagnóstica del harness, sin cambio funcional/SQL. Preflight R41: 31/31 contratos,
Bash syntax, ShellCheck 0.11.0 y manifiesto 115/115 PASS; inputs y comando en
[preparación R41](evidencia/h3req1_c03_integrated_r41_preparation_2026-10-10.md), manifiesto
SHA-256 `c8d2f656b7cfb726ea907d336ca92dd55bef602fcda4245304b56c700fbcf4a4`. R41 terminó con
status 409 y `errorCodeClass=ABSENT`; su manifiesto quedó archivado. R42, descrito arriba,
corrige la captura diagnóstica demostrablemente incompatible.

### Antecedente G07 R21 — HTTP 403 / SQLSTATE 42501 en admin_members antes de admisión

R20 intentó copiar fuentes a un rootfs read-only y se detuvo antes del probe (`READ_ONLY_COPY_REJECTED`,
exit 1); se corrigió la inyección usando stdin hacia tmpfs. R21 detectó `TLS_UNKNOWN_ISSUER` con
`DENO_CERT`, CA montada y gateway sin solicitudes. R22 confirmó la variable y el archivo presentes,
pero el Edge main aún no confió en esa CA; R23 mostró que añadir `mozilla,system` sin incluir la CA
en el bundle de sistema tampoco bastó. R24 creó un bundle temporal con raíces del sistema más la CA
sintética y configuró `DENO_TLS_CA_STORE=system`, `DENO_CERT` y `SSL_CERT_FILE`. El userWorker hizo
GET a la ruta Auth del gateway sintético y recibió HTTP 401 esperado; gateway: `auth_user_get=1`,
`other_requests=0`. Se mantuvo TLS verificado. Esto acredita solo el transporte sintético, no la
invitación Admin ni C03 integrado.

Resultados sanitizados, causas y hashes en
[R20–R24 transporte Edge](evidencia/h3req1_c03_edge_transport_r20_r24_result_2026-10-10.md).
Los recursos R20–R24 de diagnóstico se retiraron por identidad exacta; sus CA públicas y resultados
se preservaron. `studiamatch-dev` sigue healthy con `studiamatch-h3req1:20261009-v3`. Los recursos
R19 históricos (snapshot/TLS/caches/redes) se conservan; el nuevo R20 integrado usa nombres y
volúmenes propios.

El driver integrado R20 incorporó el bundle temporal de sistema probado por R24 y usó el manifiesto
de 71 entradas, SHA-256
`fcccd29bf59bff816bd06d786144e09dabeedf67c165f5422f71a7d377ecb721`. Sintaxis, contrato,
ShellCheck y manifiesto pasaron antes del run. R20 pasó snapshot, PG17 17.11, bootstrap SQL H2→H3,
setup integrado de cuota/gateway, fixture editorial/in-flight, PostgREST readiness y login
Pages/workerd (`aal2`, cookies auth/activity). Edge completó GET Auth y consultó
`/rest/v1/admin_members`; el upstream devolvió **HTTP 403**. Los contadores allowlisted fueron
`authUserRequests=2`, `authUserAccepted=2`, `adminMemberRequests=1`,
`adminMemberCredentialRejected=0`, `adminMemberFailureResponses=1`, `adminMemberLastStatus=403`,
`functionRequests=1`, `functionCredentialRejected=0`, `functionSessionRejected=0`,
`functionCalls=1`, `requestAdmission=0`, `invitationReserve=0`. R20 no capturó código estructurado,
así que por sí solo no atribuía la causa. No se envió correo
ni se mutó una reserva. El run terminó exit 1 en
`real-edge-invite-held-after-reservation` (`INVITE_EARLY_UNAUTHORIZED`). Log sanitizado SHA-256
`54ec73abd1ecd9a5364c24875823223008c9b353f257236944137d71e1dc8efd`; detalle en
[resultado integrado R20](evidencia/h3req1_c03_integrated_r20_result_2026-10-10.md).

R21 añadió captura estricta de `code`, ejecutó el candidato en PG17 17.11 y obtuvo **SQLSTATE
42501** con HTTP 403 en la misma consulta. Esto demuestra insuficiencia de privilegio, pero aún no
determina relación, columna, vista o rol efectivo. No permite concluir que la policy RLS sea causa.
`requestAdmission=0` e `invitationReserve=0`; no hubo correo ni mutación de invitación. El run
terminó exit 1 en `real-edge-invite-held-after-reservation`; su log sanitizado tiene SHA-256
`37b590faf64a46a56321e4eeb2294efb0029eb347724b3f782febaf0cfd2d9f2`, con detalle en
[resultado R21](evidencia/h3req1_c03_integrated_r21_result_2026-10-10.md).

Los servicios exactos R20 y R21 quedaron detenidos; cada PGDATA era tmpfs y no se conserva. Se
preservan contenedores, volúmenes de snapshot/TLS, cachés, imágenes y redes internos etiquetados;
no se retiró nada ni se modificó `studiamatch-dev` o el checkout original. El helper de
diagnóstico limita datos a 8 KiB y permite solo `PGRSTddd`, SQLSTATE o `UNCLASSIFIED`; contrato
22/22, sintaxis Bash/Node, manifiesto 74/74 y `git diff --check` pasan. Ver [preparación R21](evidencia/h3req1_c03_integrated_r21_preparation_2026-10-10.md).

Siguiente acción de aquel corte: contrastar el SQLSTATE con la consulta Edge
`admin_members(user_id,role,is_active,account_status)` y verificar grants efectivos de relación,
columnas y rol en el mismo PG17 desechable. Ese bloqueo fue atendido antes de R39; el siguiente
trabajo vigente es la clasificación de replay indicada arriba. No repetir R21 intacto.

G07 sigue parcial. Métricas sin cambio: histórico G01–G10 **60%**; cierre local G01–G09 **6/9 =
66.67%**. G01–G06 completos; G07 parcial; G08–G09 pendientes; G10 remoto pendiente.

### Antecedente G07 — preparación R19 tras el fallo R18

R18 quedó preservado y la CA sintética v3 del harness fue corregida en el único componente
demostrado: `tests/h3req1_c03_integrated_runtime.mjs`. La CA declara `CA:TRUE`, uso de firma
de certificados y SKI; el leaf conserva `CA:FALSE`, EKU de servidor y SAN interno. El runner
verifica esos predicados y la cadena con OpenSSL antes de crear el runtime. El diff contra el
runtime R18 archivado se limita a ese generador/verificador; el runner R19 normalizado es
idéntico a R18.

El contrato R19 pasó 21/21, sintaxis de Node/Bash y `git diff --check` pasaron, y el manifiesto
de snapshot actual pasó 69/69 con SHA-256
`6bed68f48085fa69992f4fecd32f6c6014ac8fe6c12809d4ce8688535a987d1a`. Evidencia de preparación,
pins y comando exacto en
[R19](evidencia/h3req1_c03_integrated_r19_preparation_2026-10-10.md). G07 sigue parcial.

La ejecución R19 pasó manifest/snapshot/cache, PG17 17.11, tres SQL fixtures, PostgREST
readiness y login Pages/workerd. Se detuvo con exit 1 en `real-edge-invite-held-after-reservation`
(`INVITE_EARLY_UNAUTHORIZED`): `functionCalls=1`, pero `adminMemberRequests=0`,
`requestAdmission=0` y `invitationReserve=0`. El contador Auth compartido (`authUserAccepted=1`)
no distingue el login previo de la validación Edge. La CA v3 pasó sus aserciones; esto no
demuestra el handshake Edge/Auth. Log sanitizado SHA-256
`48a58c1f312bfc99505afef57a567cfd33b86858d18799521f68219f90b6ca28` y alcance en
[R19 resultado](evidencia/h3req1_c03_integrated_r19_result_2026-10-10.md). Los cuatro servicios
fueron detenidos; snapshot, TLS, caches y redes R19 permanecen. Sigue un GET Auth Deno acotado
en red interna con resultado TLS/DNS/connect/HTTP cerrado, antes de revisar el método/path de
`supabase-js`. Un reinicio del contenedor mock R19 salió 1 antes de iniciar el probe (`OOM=false`,
sin error de daemon); es un fixture one-shot sin logs y no localiza causa. Evidencia en
`evidencia/h3req1_c03_edge_auth_transport_probe_r19_restart_failure_2026-10-10.txt`; el siguiente
método será un gateway TLS sintético nuevo y una red interna aislada. G07 permanece parcial.

### G07 — delta R18: transporte TLS bloquea Edge antes de Auth

R18 pasó manifiesto 69/69, contrato 19/19 y comprobaciones estáticas. La integración completa
terminó exit 1 en `real-edge-invite-held-after-reservation` con `INVITE_EARLY_UNAUTHORIZED`;
no acreditó reserva. Sus counters marcan `adminMemberRequests=0`, `requestAdmission=0` y
`invitationReserve=0`. Una solicitud Edge sintética y un fixture Edge Runtime separado
confirmaron `TLS_UNKNOWN_ISSUER` antes de que el mock gateway recibiera tráfico. La causa
probable está en el CA del harness: OpenSSL muestra `ca.pem` sin extensiones, mientras Deno
rechaza su issuer; falta revalidar con CA v3 `CA:TRUE`/`keyCertSign`. No se atribuye el defecto
a código funcional.

Resultado, límites y scripts V1/V2 preservados en
[R18 y clasificación TLS](evidencia/h3req1_c03_integrated_r18_result_2026-10-10.md). Log R18:
SHA-256 `7601cf6b955dbf73fdbfe6906e6489c9d63f0bb756a03094623963dc5932f188`. Los siete
contenedores R18 (runtime, Edge, fixture diagnóstico, PG17, PostgREST y dos auxiliares) se
retiraron por ID exacto después de preservar la evidencia; las dos redes internas se retiraron
con cero adjuntos. No se borraron imágenes ni volúmenes TLS/snapshot o cachés. El cambio al
generador/verificador TLS está preparado y R19 espera ejecución. G07 continúa parcial y no suma
puntos.

Métrica vigente: tablero histórico G01–G10 **60%**; cierre local G01–G09 **6/9 = 66.67%**.
G01–G06 completos; G07 parcial; G08–G09 pendientes; G10 remoto pendiente.

### G03 — tooling y suites focales completos

El snapshot aislado r6 verifica 77 filas de paquete, 68 fuentes actuales coincidentes y cero
paths `.env*`; los tres hashes de workflow siguen idénticos y actionlint se reutilizó. ShellCheck,
ESLint y Next typegen previos se conservaron al confirmar esos mismos inputs. La primera ejecución
de esta continuación pasó typegen y TSC, pero el test protegido no comenzó: el runner usaba
`/usr/bin/python3`, que no tiene pytest. Se comprobó en la imagen fijada que el runtime del
Dockerfile es `/opt/venv/bin/python` con pytest 9.1.1. El runner ahora selecciona explícitamente
ese intérprete y detiene con código cerrado si falta; no se instaló ni descargó nada.

La revalidación aislada pasó `next typegen`, `tsc --noEmit` con heap Node 3072 MiB dentro de
4 GiB/2 CPU, `tests/test_protected_workflow_review.py`, `tests/test_scan_credentials.sh` y
`tests/test_protected_path_scope_guard.sh`. Acción, scanner y suites finalizaron exit 0; red
`none`, mounts read-only y cleanup del ID exacto PASS. El runner de esta continuación también
pasó `bash -n` y ShellCheck. La revisión independiente de los cambios de runner quedó sin
hallazgos. Resultados V4 (fallo del intérprete del sistema) y V5 (PASS) están preservados en
[evidencia V4](evidencia/h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v4.txt) y
[evidencia V5](evidencia/h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v5.txt); contexto y
reproducción en la [nota de recuperación local H3REQ1](evidencia/h3req1_ciclo_validacion_local_2026-10-10.md).

### G01 — SQL/editorial reconciliado y harness afectado PASS

El manifiesto del harness editorial PG17 fijó 36 inputs y pasó 36/36 antes de la ejecución.
Se ejecutó el harness una vez en PostgreSQL 17.11 desechable: `network=none`, rootfs
read-only, mounts SQL read-only, PGDATA en tmpfs, sin puertos ni volúmenes. Evidencia
[PG17 editorial V3](evidencia/h3req1_editorial_atomicity_pg17_v3_once_2026-10-10.txt), SHA-256
`e85fcbfcf983c3bd2bf96417632259a872094bc956985336ba98c399fa0e630a`. Resultado: readiness,
versión 17.11, marcador del harness, `EXIT_0`, exit final 0 y cleanup del contenedor exacto.

El C03 SQL safe-suspend/resume v3 se reconcilió por separado: 41/41 hashes actuales,
0 ausentes, 0 deltas. Se conserva ese PASS para los bytes actuales; no se reejecutó ese SQL
ni se confunde con C03 integrado. C02 queda en 69/72 para su alcance histórico. El harness
editorial afectado obtuvo ahora su prueba PG17; los deltas BFF/workflow continúan en G08/G10
y no se presentan como cobertura C02 completa. Se retienen sus suites históricas aplicables.

### G04 — verificador de proyección Docker corregido y controles F1 PASS

V14 identificó que los 25 campos funcionaban separados y fallaba su composición. El helper
`tests/h3req1_c03_source_snapshot_projection_v2.sh` consulta 21 campos base y cuatro expresiones
aisladas (`NanoCpus`, Tmpfs path/length y `Mounts`), y recompone la proyección original en orden.
No elimina campos ni relaja predicados. El parser acepta solo el LF terminal emitido por Docker y
falla cerrado ante LF interno/repetido, CR, NUL, pipe, exceso de bytes, timeout fuera de 1–15 o
fallo en cualquiera de las lecturas; limpia metadata parcial.

La suite sintética pasó mapas presentes/ausentes, orden/composición 25 campos y 11 negativos,
incluidos timeout `16` y entero de longitud arbitraria rechazados antes de llamar a Docker.
ShellCheck 0.11.0 y `bash -n` pasaron en un contenedor efímero `network=none`. La revisión
independiente confirmó PASS sin hallazgos: el LF final de `docker inspect` queda eliminado por
command substitution de Bash y el mock lo reproduce. El primer intento sintético no inició porque
el rootfs read-only carecía de `/tmp`; se añadió un tmpfs de 16 MiB al contenedor de prueba y la
revalidación pasó. No fue un ensayo Docker del producto.

El runner F1 V2 pasó para sus inputs de entonces y se conserva como evidencia histórica. Luego se
actualizó `tests/h3req1_c03_integrated_runtime.mjs` para usar el manifiesto de fuentes V3 solo en
modo `startupOnly`, sin cambiar el manifiesto del modo C03 integrado. Esa modificación invalidó
la actualidad del snapshot V2; por eso se repitió únicamente la captura afectada, no las pruebas
sintéticas ni tooling intactos. La revisión independiente detectó que S2/F1 no fijaban el daemon
ni, en S2, el path del checkout. Ambos runners quedaron fijados al checkout esperado cuando aplica,
contexto `default`, endpoint `/var/run/docker.sock` e identidad mínima observada del engine
Docker Desktop. Revisión independiente final: sin hallazgos concretos.

La revalidación F1 V3 pasó con manifiesto y pins actuales. Evidencia:
[snapshot F1 V3](evidencia/h3req1_c03_source_snapshot_2026-10-10_v3.md), runner SHA-256
`9b9d010787836c9c317fe3e451ff63d17b94b48ba154421306bff6c305f64211`, sidecar SHA-256
`6377c544113c302cef3ee91be821e83675e794c62b5e1e132f16ff2c755ad3c9`, projection helper SHA-256
`7be1caec879e7e22db6da8c10a0623f254ec329e101ed675b7928803cba005f6`, source manifest SHA-256
`4b6e99fb6feb85eb8b4ea8e899e69c2d3c497657b507b03004d45981b97417c8`. El daemon comprobado es
Docker Desktop `docker-desktop`, contexto `default`, engine ID
`[UUID redactado]`, versión 29.8.2; no se cambió el engine. Rama/HEAD
fijados; productor tar, receptor Docker, filtro y verificador exit 0; estado antes/después PASS,
sin OOM, `network=none`, rootfs read-only, usuario 1001, sin mounts persistentes, logs ni puertos.
Snapshot: 14 archivos allowlisted, manifiesto 13/13, 540831 bytes, sin symlinks, extracción
`--no-same-owner`. El contenedor exacto terminado y cidfile/evidencia se conservan.
La antigua [evidencia F1 V2](evidencia/h3req1_c03_source_snapshot_2026-10-10_v2.md) permanece
intacta. V3 sigue siendo evidencia aplicable a G04; la copia vigente de G05 es S12 con el
manifiesto V4 actual y su volumen íntegro read-only.

### G06 — Pages/workerd y `healthz` acreditados localmente; G07 pendiente

Las primeras dos revalidaciones S9 se detuvieron en preflight por filas V3 históricas en los
manifiestos S3 y S4; la tercera falló exit 127 porque el helper de compatibilidad se invocaba antes
de su definición. Los tres resultados y correcciones quedan preservados en [preflight S9](evidencia/h3req1_c03_startup_smoke_2026-10-10_s9_preflight1.md) y [dispatch S9](evidencia/h3req1_c03_startup_smoke_2026-10-10_s9_dispatch_failure.md). Ninguno alcanzó el runtime.

Tras mover ambas definiciones auxiliares antes de la llamada pre-Docker, actualizar el sidecar,
pasar Bash, `diff --check`, ShellCheck y revisión independiente, S9 terminó exit 0. Evidencia
[S9 Pages/workerd](evidencia/h3req1_c03_startup_smoke_2026-10-10_s9.md), SHA-256
`5703e866bd09b0ef654478bf23a2e3842921ec008069c9552d56712ad1ee4bc3`: snapshot S12 verificado
14/14 archivos, hashes 13/13, cero symlinks y permisos exactos; S3 resources/network PASS;
pruebas sintéticas del filtro y diagnóstico PASS; runtime Pages/workerd real `healthz=PASS`
en 5 intentos internos fijados, exit 0, OOM false, red interna S3 sin egress. Edge y database
no se iniciaron. El runtime S9 queda preservado como exited 0; no se limpió ningún recurso.

Pins S9: runner `9e8019f686b50835cf3c14f6d29cbdf8c45db305eb3c95fe5365103f2da2d19f`, sidecar
`d9e51fd2487edcff096ee630de2ed9d1f30b7de323a79cbfae9d60516c3d3bf4`. La revisión independiente
final no encontró bloqueantes. Esto completa G06 únicamente; G07 integrado aún no ha comenzado.

### G07 — integración C03 parcial; R17 devuelve `INVITE_EARLY_UNAUTHORIZED` antes de reservar

La revisión estática previa detectó pulls implícitos posibles, `docker exec` sin deadline,
cleanup por nombre tras validar ID y servicios activos que podían quedar tras FAIL/señal. R5
quedó corregido y tiene prueba de contrato incluida en su snapshot: imágenes solo locales
(`--pull=never`), endpoint local fijado luego de comprobar daemon, deadlines de host/contenedor,
stop limitado a IDs etiquetados por el run y cleanup por ID inmutable tras una sola inspección.
Validación local del delta corregido: Bash `-n`, 6/6 pruebas Node contractuales, ShellCheck
0.11.0 warning-level, `git diff --check` y manifiesto 63/63 PASS. Revisión independiente de
bytes previos encontró hashes de manifiesto obsoletos y que los helpers bajo `timeout` omitían
el endpoint fijado; el binario `/usr/bin/docker` y `--host unix:///var/run/docker.sock` ahora
se aplican también en `bounded_docker` y `bounded_exec`, con asserts específicos. Runner SHA-256
`7e2d4c018852d0bdb702ed198deb9b679838293dc3a9129a000b36d9fff74a2d`; test SHA-256
`dd3b6fed570d0c1dd396317144e7c7e75ec1b6f83ec9b4ce5619d57fc346e40c`; manifiesto SHA-256
`4e12f52b113881d264421e555c6c1dd56ae7868a738a70124f11f809e9125393`. Las revisiones
independientes de seguridad y protocolo dieron PASS estático. R5 se ejecutó una vez: exit 1 en
`isolated-postgrest`, luego de que PG17 H2→Pro→H3, setup C03/fixtures y Pages/workerd `healthz`
pasaran. PostgREST siguió `running`, pero 60 sondeos `GET /` desde Pages/workerd no obtuvieron
2xx; el probe no distinguió status HTTP, DNS, conexión o timeout. No hay logs crudos
(`log-driver none`), OOM ni evidencia de causa de producto/Docker. El stop por fallo alcanzó solo
los tres servicios R5 etiquetados y conservó redes, snapshot/TLS y cachés.
R6 terminó exit 1 en `healthz` (OOM false). La causa exacta fue el manifiesto
integrado ausente del snapshot: `integrated_runtime.mjs:734–736` lee
`tests/h3req1-c03-integrated.sha256`, pero el snapshot R6 solo contenía el archivo
renombrado `tests/h3req1-c03-integrated-r6.sha256`. El probe read-only del volumen
confirmó `runtime-manifest=missing|r6-manifest=present`. R6 no llegó a PG17/Edge.
R7 corrigió la ruta, pero no se ejecutó: revisión independiente detectó que el
bootstrap de snapshot y el verificador de caches carecían de deadline individual.
R8 añade canonical-manifest coverage y deadlines (60 s Docker directo, 300 s
snapshot, 180 s cache). Sus pruebas contractuales pasan 10/10; ShellCheck,
`bash -n`, diff y 64/64 hashes pasan. Ambas revisiones independientes de R8 dieron
PASS estático. Su ejecución pasó snapshot/cache, Pages/workerd healthz, PG17 17.11,
bootstrap SQL y fixture sintético, y terminó exit 1 en `isolated-postgrest`: 60 sondeos
reportaron `HTTP_503`. No se leyó el body ni hay logs crudos; los servicios se detuvieron
por ownership exacto y Edge no se inició. Los exits post-stop (runtime 143, PG17 0,
PostgREST 255) no explican el 503. No se atribuye causa a PostgREST, SQL o Docker.

R9 preserva el resultado anterior, agrega extracción JSON estrictamente acotada: Fetch BYOB
solicita máximo 8192 bytes, cancela al alcanzar el límite y solo emite `PGRST###` o SQLSTATE
allowlisted; demás casos conservan `HTTP_<status>`. RED de contrato reprodujo que R8 perdía
`PGRST000`; GREEN pasó 11/11 en Node aislado con network none y mount read-only, incluida la
prueba de `Response` real y cuerpo de 8193 bytes con exactamente 8192 consumidos. Bash syntax,
ShellCheck 0.11.0 y manifiesto 64/64 pasan. Revisión independiente final seguridad + protocolo/SQL:
PASS sin blockers. Pins runner `905398c9964b2182726d97ffca0788b176198b3ecdce3ca0492d948f82084840`,
contrato `8d8e5c9fa26731479a05fcacb2d2cc4f632a7ee8a261ca95de03e501aed34ba7`, probe
`92d419157a8669b889edf5cf78a5d54e31040076788d8a39ddf4123b501f69d7`, manifiesto
`6b0a469325b466a59211b3f6e50f16bce49910d78cad994068daa51caba13de9`. R9 se ejecutó una vez
con timeout 1800 s y terminó exit 1 en `isolated-postgrest`: los 60 sondeos devolvieron
`HTTP_503_PGRST002`. El failure-stop detuvo los tres contenedores R9 propios (runtime 143,
PG17 0, PostgREST 255 después del stop), OOM false; Edge no inició. La respuesta clasifica una
falla en la consulta/construcción del schema cache, pero no da el SQLSTATE subyacente. R9 no
registró stdout/stderr del contenedor PostgREST (`log-driver none`) ni comprobó acceso TCP
autenticado por el alias de red después del fallo. Los contenedores, redes, snapshot y evidencia
R9 se conservan; los recursos detenidos no acreditan causa ni reparación. Diagnóstico R10 debe
recrear solo PG17/PostgREST con los mismos SQL/fixtures y límites, registrar logs efímeros acotados
con salida cerrada/sanitizada, comprobar alias TCP y autenticación con credencial aleatoria y no
iniciar Edge. G07 sigue parcial, sin cambio de métrica: histórico 60%, local 6/9 = 66.67%.

R10 V1 terminó exit 1 antes de crear red o servicios: el snapshot R9 contiene dos archivos no
manifestados además de los 64 esperados; no hay faltantes ni symlinks. Se clasificaron como
artefactos históricos fuera del candidato y se conservaron. Evidencia sanitizada
[R10 V1](evidencia/h3req1_c03_integrated_diagnostic_r10.txt), SHA-256
`f066662b844fc74f78a3272f1fd0ff800653f29c4974f448dead88df35ad6ef7`. El verificador V2 acepta
solo los 64 archivos/hashes del manifest y dos extras históricos fijados; rechaza otro extra,
symlink o drift. El volumen R9 pasó `VERIFIED_64_2`. R10 V2 terminó exit 1 antes de crear red o
servicios porque comparaba literalmente el banner PG17.11; el digest local sí reportó release
17.11 con metadata Debian. La evidencia [R10 V2](evidencia/h3req1_c03_integrated_diagnostic_r10_v2.txt),
SHA-256 `e390ba35d4452762ea7c9cca6fb90b63a8a13b8e2778b1aeddc213b75a63d8ce`, preserva el FAIL.
El comparador se corrigió y se fijó junto con sus sintéticos. Revisión independiente final de
seguridad y protocolo: PASS. R10 V3 completó exit 0, pero `HTTP_503_PGRST002` solo aparecía en la
respuesta; el clasificador de log antiguo no conocía todos los marcadores PostgREST 13.
[R10 V3](evidencia/h3req1_c03_integrated_diagnostic_r10_v3.txt), SHA-256
`06963c9db4674e8cf73275a4f49f1ef1e435dc693282235d339174bf4cbd550a`, se conserva.
R10 V4 confirmó exit 0 del diagnóstico, inputs 7/7 y snapshot 64+2; PG17 readiness, los tres
fixtures SQL y TCP/auth antes/después pasaron. PostgREST permaneció `running`, exit 0 y OOM false,
pero el probe volvió a dar `HTTP_503_PGRST002`; el clasificador emitió
`NO_SCHEMA_CACHE_MARKER` para sus logs y `NO_SCHEMA_CACHE_SQLSTATE` para PG. Evidencia
[R10 V4](evidencia/h3req1_c03_integrated_diagnostic_r10_v4.txt), SHA-256
`e932748d438d77e876005ae56c5d3fb602f76f4367e56dc36b7d4485250e6925`. Se retiraron únicamente
los dos contenedores y la red interna R10 exactos. El resultado no demuestra causa de SQL, Docker
ni producto; no se inició Edge ni se guardaron logs crudos.

R10 V5 se ejecutó una vez y terminó exit 0 como diagnóstico, sin cerrar G07. Los inputs fueron
7/7, el snapshot R9 64/64 + dos extras históricos fijados, PG17.11 readiness y los tres SQL
fixtures exit 0; TCP/auth PG17 pasó antes y después del servicio. PostgREST siguió running, exit 0,
OOM false, pero respondió `HTTP_503_PGRST002`. El clasificador acotado devolvió
`NO_SCHEMA_CACHE_SQLSTATE` en PostgreSQL y `NO_JSON_RECORD` en logs PostgREST. Se retiraron por
ID exacto los dos contenedores y la red interna R10; no se inició Edge ni se guardaron logs crudos.
Evidencia [R10 V5](evidencia/h3req1_c03_integrated_diagnostic_r10_v5.txt), SHA-256
`9ad4794b11102cb4c834a62996318195da4fed283542736992789bb62e30be5c`.

La imagen candidata se verificó en contenedor sin red como PostgREST 13.0.7. La imagen oficial
v14.0 separada se preparó y revisó para comprobar si exponía la categoría/código subyacente, sin
alterar el pin candidato. Su ejecución R11 terminó exit 0 como diagnóstico: manifiesto R11 8/8,
R9 64/64, snapshot 64+2, PG17.11, los tres SQL fixtures y TCP/autenticación antes/después PASS.
PostgREST 14.0 quedó running, exit 0/OOM false; la consulta luego de cinco segundos devolvió
`HTTP_503_PGRST002`. Los logs filtrados dieron `NO_SCHEMA_CACHE_SQLSTATE` y `NO_JSON_RECORD`.
Evidencia [R11 V14](evidencia/h3req1_c03_integrated_diagnostic_r11_v14.txt), SHA-256
`b5a10e5a6973d76d488b9bdd6a05e52b4a3276664389846872459e6b5a9aaef5`; limpieza solo por IDs
exactos, sin Edge ni logs crudos. Esto no identifica causa ni valida el runtime candidato.

R12 V2 se ejecutó y terminó como diagnóstico con exit 0; evidencia
[R12 V2](evidencia/h3req1_c03_integrated_diagnostic_r12_schema_dump_v2.txt), SHA-256
`d3136b0fad548608f5dc755f75bdea9b3fa5041ebd5624d073ed436acfd981b7`. Inputs 4/4, R9 manifest
64/64 y snapshot 64 + 2 extras históricos; PG17.11 readiness, tres fixtures SQL y TCP/auth antes
y después PASS. La comprobación allowlisted identificó `EXTENSIONS_SCHEMA_ABSENT`; el dump
reprodujo `SQLSTATE_3F000`, exit 1, hasta 8192 bytes. Solo se retiraron por ID los dos contenedores
y la red interna R12 exactos. No hubo Edge ni logs crudos. Esto demuestra el prerrequisito faltante
en el fixture, no un defecto de producto/PostgreSQL/Docker.

Corrección local mínima: un fixture R10 separado crea `extensions` en PG17 desechable antes de
las migraciones C03; los fixtures R9/R6 y el snapshot R9 se conservan sin cambios. El runner,
contrato y SQL R10 sustituyen solo esas tres entradas del manifiesto integrado: 61/61 entradas
restantes conservaron sus hashes; manifiesto R10 64/64. Contrato/sintaxis Node 12/12 en Docker
aislado y ShellCheck 0.11.0 PASS. Revisión independiente estática PASS sin blockers. Evidencia
[preflight R10](evidencia/h3req1_c03_integrated_r10_static_validation.txt), SHA-256
`ccdab4645bc187729f3ec8001fa2443e54f11f55ffc64e551aef46e849d45664`; ShellCheck
[R10](evidencia/h3req1_c03_integrated_r10_shellcheck.txt), SHA-256
`dc39e8e043b102865371a5a2245f3a8340a6605255c08bb4e44b31da2414c17a`.

R10 integrado se ejecutó una vez con el arreglo de `extensions`: snapshot y caches PASS, Pages/workerd
`healthz` PASS, PG17 17.11 y los tres fixtures SQL PASS, y PostgREST readiness PASS. Se inició Edge
activo y el control falló en `/control/login` con `AssertionError`, exit 1, fase
`real-edge-invite-held-after-reservation`. El handler R10 ocultaba el predicado y no hay base para
atribuir la causa a Auth, BFF, cookies, Edge, SQL o Docker. El failure-stop detuvo cuatro servicios
R10 etiquetados; contenedores, snapshots, volúmenes y redes se conservaron. Evidencia
[R10 integrado](evidencia/h3req1_c03_integrated_run_2026-10-10_r10.log), SHA-256
`67957f6f5006f668a31ea7fc70f2bbf14c37e62f79b50c10b45cc033198d153b`.

R11 agrega diagnóstico cerrado de los cuatro predicados de login. Corrió exit 1 en
`real-edge-invite-held-after-reservation` con `LOGIN_HTTP_STATUS_NOT_200`; AAL y cookies no se
evaluaron después de fallar status. Esa versión no guardó el número HTTP, por lo que no se infiere
si la causa está en validación, cuota, Auth o sesión. Evidencia R11:
[log](evidencia/h3req1_c03_integrated_run_2026-10-10_r11.log), SHA-256
`c960ee86ae60a9bdbea1560c43ac2f543de057f61379060cf4c613b880f7f296`.

R12 preflight falló 13/14 antes de Docker: un offset del clasificador etiquetaba AAL como cookie.
El log se preserva en [R12 preflight](evidencia/h3req1_c03_integrated_r12_static_validation.txt),
SHA-256 `2c51bb6054d651dc6b4dafa2f7d8c3d04382bc77ca3edf389199be854097356a`. Se corrigió con índices
explícitos y R13 pasa Bash `-n`, ShellCheck 0.11.0, `git diff --check`, 14/14 pruebas de contrato y
manifest 65/65. R13 registra únicamente códigos `LOGIN_HTTP_STATUS_NNN` (status entero 100–599),
`LOGIN_HTTP_STATUS_INVALID`, AAL/cookie allowlisted; el BFF, Auth, cookies y sus políticas no se
modificaron. La revisión independiente R13 concluyó PASS sin blockers; no ejecutó runtime.

R13 integrado llegó a `/control/login` y emitió status 403; no identificó el origen del rechazo. R14, con snapshot/cache, PG17/H2-Pro-H3, setup de cuotas/dispatcher, fixtures, PostgREST readiness y Edge activo en PASS, falló antes de la reserva: `/control/login`, `TypeError`, exit 1. El adaptador usó el `Request` global de Node, incompatible con `worker.fetch()` de Miniflare 4.20260730.0. Probe aislado reprodujo TypeError; `undici.Request` más ruta explícita `admin.local.test/*` devolvió 200 con URL/Origin same-origin. La corrección está limitada al harness, no al BFF/producto.

R15 incorporó el Request/route fix y pasó login (`aal2`, ambas cookies), pero terminó exit 124 esperando 60 s el hold de Auth. No hubo aserción de reserva ni suspensión/recuperación; el resultado temprano quedó oculto por el harness. R16 compite el evento Auth con early response/rejection y timeout interno de 30 s; solo emite códigos allowlisted y detiene ante early result. El drill pasó manifest 65/65, contratos/cache y preflight; se detuvo antes de servicios porque el daemon agotó el pool IPv4 al crear la segunda red (`all predefined address pools have been fully subnetted`). No se alcanzó el clasificador temprano. Inventarié 19 redes H3 internas con `attached=0`; se retiraron esas redes selectivamente y se preservaron contenedores, imágenes y 27 volúmenes. Evidencias: [R16 resultado](evidencia/h3req1_c03_integrated_r16_result_2026-10-10.md), [inventario previo](evidencia/h3req1_c03_integrated_network_inventory_precleanup_2026-10-10.txt), [limpieza](evidencia/h3req1_c03_integrated_network_cleanup_2026-10-10.md), [log R16](evidencia/h3req1_c03_integrated_run_2026-10-10_r16.log), [R14 resultado](evidencia/h3req1_c03_integrated_r14_result_2026-10-10.md), [probe Request/Origin](evidencia/h3req1_c03_miniflare_request_compatibility_2026-10-10.txt), [R15 resultado](evidencia/h3req1_c03_integrated_r15_result_2026-10-10.md), [R16 estática](evidencia/h3req1_c03_integrated_r16_static_validation_2026-10-10.md) y [R16 preparación](evidencia/h3req1_c03_integrated_r16_preparation_2026-10-10.md).

R17 usó nombres nuevos y un manifiesto de 67 entradas. Docker, snapshot completo, contrato 18/18,
caches fijadas, Pages/workerd `healthz`, PG17 17.11, PostgREST readiness y login (`aal2`, cookies)
pasaron. La fase de invitación in-flight recibió `INVITE_EARLY_UNAUTHORIZED`, exit 1, antes de
confirmar reserva. El failure-stop detuvo los cuatro servicios R17 propios. El código Edge
`unauthorized` puede provenir de rechazo del Auth mock o de un fallo leyendo `admin_members` que
el handler transforma a `unauthorized`; el log no discrimina esos subpasos. Se preservaron log,
manifiesto y runtime exactos; siguiente R18 agrega solo contadores sintéticos de etapa/status,
sin exponer tokens, headers, cuerpos ni errores crudos. [R17 resultado](evidencia/h3req1_c03_integrated_r17_result_2026-10-10.md), [preparación](evidencia/h3req1_c03_integrated_r17_preparation_2026-10-10.md), [log](evidencia/h3req1_c03_integrated_run_2026-10-10_r17.log), [manifiesto](evidencia/h3req1_c03_integrated_manifest_r17.sha256) y [runtime exacto](evidencia/h3req1_c03_integrated_runtime_r17.mjs).

G07 sigue parcial y sin puntos nuevos: tablero G01–G10 60%; cierre local G01–G09 6/9 = 66.67%.
Próxima etapa: diagnosticar la fuente de `INVITE_EARLY_UNAUTHORIZED` con contadores sintéticos
en R18 y corregir únicamente el componente demostrado. La limpieza selectiva de R16 preservó
27 volúmenes H3, imágenes y `studiamatch-dev` healthy; véase [network cleanup](evidencia/h3req1_c03_integrated_network_cleanup_2026-10-10.md). Detalle de R13 y del resultado R11 en
[preparación R13](evidencia/h3req1_c03_integrated_r13_preparation_2026-10-10.md), historial R11
en [R11/R12](evidencia/h3req1_c03_integrated_r11_preparation_2026-10-10.md) y diagnóstico SQL/
fixture en [R10/R12](evidencia/h3req1_c03_integrated_r10_preparation_2026-10-10.md).

Evidencia por iteración: [R5](evidencia/h3req1_c03_integrated_r5_preparation_2026-10-10.md),
[R6](evidencia/h3req1_c03_integrated_r6_preparation_2026-10-10.md),
[R7](evidencia/h3req1_c03_integrated_r7_preparation_2026-10-10.md) y
[R8](evidencia/h3req1_c03_integrated_r8_preparation_2026-10-10.md),
[R9](evidencia/h3req1_c03_integrated_r9_preparation_2026-10-10.md).

El diagnóstico S6 histórico identificó `MiniflareCoreError`, sin atribuirlo a producto o Docker.

S5 pasó pins, verificación de recursos S3, red por ID y sintéticos. Emitió `dependency-roots-present`,
`runtime.mjs:800:3`, healthz NO-GO tras 3 intentos y exit 1 sin OOM. S6 corrigió el filtro y agregó
clasificación de tipo/código cerrada; su revisión independiente no halló findings. Los sintéticos,
Node/Bash syntax, ShellCheck oficial 0.11.0, manifiesto y `git diff --check` pasaron. El preflight
S6 verificó nuevamente S3 y el self-test del filtro; el runtime emitió `MiniflareCoreError`,
`runtime.mjs:800:3`, healthz NO-GO tras 4 intentos, exit 1 sin OOM. Su contenedor permanece
preservado en la red interna S3; la evidencia no contiene mensaje ni código crudo.

El resultado acredita una excepción del tipo Miniflare durante la ruta de startup después de
`dependency-roots-present`, pero no el subpaso exacto. Según el flujo fijado, quedan por delante
directorios/TLS sintético, builds esbuild, constructor Miniflare y `getWorker`; no se atribuye la
causa a producto ni a Docker. El siguiente diagnóstico debe emitir eventos de fase cerrados y
clase/código allowlisted en cada frontera de esa secuencia, manteniendo output sanitizado,
dependencias read-only, red interna sin egress y no ejecución de Edge/DB.

Pins S6: runner `74d7ae4285a27741cc698caa55ff47363e8fd26efbed4c577ca6464bcd40e354`, manifiesto
`6590fee0612153c22e902b00c378c48803424b56277a1fd1db841e20f10be8ad`, probe
`b1c92a574bc24d7bed812079c508bfaca921935442fe056da65c661ad4f90b81`, filtro
`cd55b200391906d79bb347486d2201b4cf968a8a5445e193b11135883d133405`. Resultado sanitizado
[`S6`](evidencia/h3req1_c03_startup_smoke_2026-10-10_s6.md), SHA-256
`38f5ff8c466886ae405db19bc26ad498accacf14e9de95218d1f7816bcde9b74`; contenedor
`h3req1-c03-startup-runtime-20261010-s6` ID
`e7dcb0e20e47fd8d1c26ab6e5ce6674b10fb480bcc67dabcaf24cbe2e7cf1f36`, exit 1, OOM false,
red interna S3 ID `ffc476c62637ef44316255202a6b08a170df514685bb6d16efcf7976fd79a13f`. No hubo egress,
DB/Edge/SQL, secretos, remotos ni cleanup. Este resultado S6 es histórico y queda supersedido
para G06 por S9; no se borra ni se reinterpreta.

Para ShellCheck, `studiamatch-dev` no contiene el binario; el primer preflight estático se detuvo
antes de analizar scripts (exit 1, causa demostrada: `shellcheck=missing`). Se usó la imagen oficial
`koalaman/shellcheck:v0.11.0` con digest
`sha256:61862eba1fcf09a484ebcc6feea46f1782532571a34ed51fedf90dd25f925a8d`; análisis en contenedor
efímero `network=none`, mounts solo lectura, severity warning y sources habilitados pasó. Un
primer uso con severidad por defecto mostró únicamente avisos `info` SC2016/SC2015/SC1091; no son
warnings ni findings funcionales y se preservó el resultado, sin alterar el código por esos avisos.

El ensayo S2 se ejecutó una vez y falló en `create-new-source-snapshot`: el `docker run` receptor
terminó con exit 2 y el runner con exit 1. No se alcanzaron npm bootstrap, red interna, Pages/
workerd ni healthz. La reproducción mínima aislada demostró que el receptor intentaba conservar
UID/GID del tar dentro de un contenedor `cap-drop=ALL`; tar devolvió `OWNER_RESTORE_DENIED` (exit
2). El mismo archivo terminó exit 0 al añadir `--no-same-owner`. Esto identifica una incompatibilidad
del extractor bajo las capabilities fijadas; no atribuye el fallo a producto ni a Docker Desktop.
El S2 completo y la reproducción sanitizada quedan preservados en
[diagnóstico S2](evidencia/h3req1_c03_startup_smoke_2026-10-10_s2_diagnosis.md). Holder, snapshot
fallido y tres volúmenes S2 permanecen preservados; no hubo cleanup.

El S3 corrigió la extracción: snapshot exit 0 con 14 archivos, cero symlinks y hashes verificados;
los contenedores bootstrap tools y Pages terminaron exit 0. El runner se detuvo en
`create-new-egress-blocked-internal-network`, exit 1, antes de iniciar Pages/workerd. La causa
demostrada fue el predicado incorrecto `docker network create stdout == nombre`: el CLI devuelve
el ID. La red exacta existe y la metadata read-only confirma `bridge`, `Internal=true` y etiquetas
S3 correctas. No hubo fallo del engine ni prueba de healthz. La [reconciliación S3](evidencia/h3req1_c03_startup_smoke_2026-10-10_s3_diagnosis.md)
conserva resultado y recursos; no hubo cleanup.

## S4 — G06 aún incompleto: fallo de runtime y del predicado post-exit — 2026-10-10

S4 fijó candidato, Docker Desktop, manifiestos S3 y red interna por ID. Sus preflight de
ownership, red, snapshot, dependencias e inputs pasaron; no repitió `npm ci` ni usó egress. El
contenedor Pages/workerd terminó exit 1, `OOMKilled=false`; healthz observó `ECONNREFUSED` y no
hubo marcador `runtime-ready`. El output crudo se descartó. La evidencia solo acota la falla a
después de `dependency-roots-present` y antes del runtime listo; la causa exacta todavía no está
determinada.

También se confirmó un defecto del verificador: después del exit, Docker mantuvo el
`HostConfig.NetworkMode`/`NetworkID` exacto de la red S3 pero dejó `EndpointID` vacío. Exigir
EndpointID post-exit produjo `S4 runtime did not attach...` aunque la identidad de red persistente
coincide. La nota
[diagnóstico S4](evidencia/h3req1_c03_startup_smoke_2026-10-10_s4_diagnosis.md) preserva los
estados y la evidencia sanitizada. Runner S4 y contenedor fallido quedan conservados; S2/S3,
holder, tres volúmenes y red interna S3 siguen preservados.

No se marca G06 completo ni se inicia G07. La siguiente ejecución usará un runner revisado que
verifica la red por ID y añade un diagnóstico sanitizado de la etapa/tipo de error anterior a
`runtime-ready`; continuará usando los volúmenes S3 read-only y sin egress. El porcentaje sigue
en G01–G05 completos: tablero histórico 50%, cierre local 5/9 = 55.56%.

El detalle del resultado histórico F1 V2, sus pins y el contenedor preservado permanece en
[evidencia F1 V2](evidencia/h3req1_c03_source_snapshot_2026-10-10_v2.md); no se confunde con la
captura V3 vigente.

### Gates y métricas al corte vigente

| Gate | Estado | Evidencia / pendiente |
|---|---:|---|
| G01 SQL/wire/editorial | 10/10 | Harness PG17 V3 exit 0 y 36/36 inputs; C03 SQL 41/41 sin reejecución. C02 histórico 69/72; deltas BFF/workflow reservados a G08/G10. |
| G02 suspensión SQL | 10/10 | C03 SQL aislado v3 41/41, sujeto a compatibilidad de inputs. |
| G03 tooling | 10/10 | actionlint por hashes vigentes; ShellCheck/ESLint/typegen previos con inputs idénticos; TSC 3072 MiB y tres suites focales PASS en V5. |
| G04 F1 | 10/10 | Proyección 21+4, negativos sintéticos y controles del contenedor F1 V3 verificados antes/después; evidencia snapshot F1 V3. |
| G05 snapshot completo | 10/10 | S12 PASS: 14 archivos allowlisted, source manifest 13/13, symlinks 0, modos exactos, productor/limitador/receptor/verificador exit 0; red none y montaje independiente read-only. Evidencia `h3req1_c03_source_snapshot_2026-10-10_s12.md`. S9/S10/S11 conservados como fallos anteriores. |
| G06 Pages/workerd healthz | 10/10 | S9 real, `healthz=PASS`, exit 0, OOM false, red interna sin egress; evidencia S9 fijada arriba. |
| G07 Edge/PG17/PostgREST/C03 integrado | 0/10 | No acreditado. |
| G08 checks finales | 0/10 | Reconciliar por impacto después de G03/G07. |
| G09 aceptación local | 0/10 | UAT 144/cero retries, onboarding 10/10, pilares y revisión pendientes. |
| G10 CI remoto | 0/10 | Fuera de la autorización; requiere evidencia/decisión remota separada. |
| **Tablero G01–G10** | **60%** | **60 puntos completos de 100; G01–G06 completos.** |
| **Cierre local G01–G09** | **6/9 = 66.67%** | **G01–G06 completos; G07–G09 pendientes.** |

### Snapshot actual y próximo runtime

El source manifest V4 actual se capturó con S12 en un volumen local persistente, tras probar la
cota de bytes exacta y limit+1. S12 terminó exit 0 en productor, limitador (9 MiB máximo),
receptor y verificador independiente read-only: 14 archivos, 13/13 hashes, cero symlinks, modos
exactos, extracción sin restaurar ownership, red none. La evidencia
[`S12`](evidencia/h3req1_c03_source_snapshot_2026-10-10_s12.md) identifica contenedor/volumen y
preserva la cota real; el volumen local no dispone de cuota Docker. S9, S10 y S11 permanecen
como intentos fallidos conservados; S11 falló en su sintético antes de Docker.

G06 ya pasó con Pages/workerd S9. El siguiente ensayo G07 ejecutará `postgrest --dump-schema`
una sola vez con el pin candidato 13.0.7, capturando solo códigos allowlisted y descartando el
schema/error crudo. Si sigue sin ser concluyente, el diagnóstico siguiente medirá `/ready`,
métricas del cache y actividad PG sin volver a sondear el API. Edge y C03 integrado esperan
readiness. No se conectará a datos operativos ni a `.env*`.

No se declara GO. G07–G09 permanecen pendientes. Implementación, pruebas,
integración local y despliegue se reportan por separado; no se ha ejecutado operación remota.

## Corte anterior — V1 retenido por revisión; diagnóstico V2 preparado — 10% — 2026-10-10

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`, WIP actual
55 tracked/287 untracked/0 staged. El checkout original se preservó; no se leyeron `.env*` ni
secretos.

### r9 TSC diagnostic continuation V1 — una ejecución, FAIL

Se ejecutó una vez el JIT SHA-256
`1847596f63eafb4f0bb1074d581bc058a602b6d065e60f7324112de66aa17eff` con TTY Ubuntu WSL,
`romel` no-root, `require_escalated`, sin `sudo`, timeout 180 s y cero retries. La salida durable
está en [evidencia TSC V1](evidencia/h3req1_g03_r9_tsc_v1_execution_2026-10-10.txt):

```text
phase=r9-reused-web-inputs|error_code=HASHES_MATCH
phase=r9-image-read-classifier-synthetics|error_code=OK
phase=r9-continuation-preflight|error_code=OK
phase=r9-candidate-copy|error_code=OK
phase=r9-continuation-preflight|error_code=OK
phase=r9-actionlint-reuse|error_code=INPUT_HASHES_MATCH
phase=r9-typescript-classifier-synthetics|error_code=OK
phase=r9-typescript|error_code=NODE_HEAP_LIMIT
exit=134
```

El clasificador confirma el mensaje de límite de heap de Node; no se atribuye a un tipo/fichero
concreto ni a un defecto funcional. Runtime: el mismo contenedor aislado de 512 MiB y el mismo
snapshot del candidato. No se elevó el límite. La captura de 64 KiB se conservó solo en memoria;
la evidencia no contiene stderr crudo. El stop-on-failure dejó sin correr las suites restantes de
workflow protegido, credential scan y path scope guard. El permiso V1 está consumido y no se
repite. No hay corrección local demostrada todavía.

Revisión estática posterior, sin editar fuentes: `web/tsconfig.json` declara strict/noEmit,
`skipLibCheck` e `incremental`; `web/src` contiene 45 rutas TS/TSX. El patrón
`.next/types/**/*.ts` aparece dos veces en `include`, mientras el proyecto también incluye
generados Next. No hay evidencia de que esa duplicación cause el heap limit; no se modificó ni se
usa para atribuir causa.

### G01–G10 y métrica

| Gate | Estado | Evidencia vigente |
|---|---:|---|
| G01 SQL/wire/editorial | 0/10 | C02 69/72; exit del harness editorial no acreditado. |
| G02 suspensión SQL | 10/10 | C03 SQL aislado v3, 41/41 inputs; no acredita integración. |
| G03 tooling | 0/10 | Actionlint, ShellCheck, typegen y ESLint PASS; TypeScript NODE_HEAP_LIMIT; tres suites pendientes. |
| G04 F1 | 0/10 | Reducción sintética parcial; F1 no leído. |
| G05 copia | 0/10 | No ejecutada. |
| G06 Pages/workerd | 0/10 | No hay arranque/healthz acreditado. |
| G07 Edge/PG17/PostgREST/C03 integrado | 0/10 | No ejecutado. |
| G08 checks | 0/10 | Checks finales pendientes. |
| G09 aceptación | 0/10 | UAT 144 sin retry, onboarding 10/10, revisión/pilares pendientes. |
| G10 CI | 0/10 | Patch local preparado; enforcement remoto no acreditado. |
| **Total** | **10%** | **Inicial 10%; final 10%; delta 0 puntos. NO-GO.** |

`GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` y D01–D14 siguen NO-GO. La aprobación humana del JIT
[inventario TypeScript V1](operaciones/jit_h3req1_g03_r9_tsc_project_config_v1_once_2026-10-10.md),
SHA-256 `d70a5dc8f3061fac4d48ac57d6a57fcb99f21e0e637fcfa01b8581e41d3304cb`, se recibió, pero la
invocación se detuvo antes de ejecutar el runner por hallazgos de revisión independiente: el
manejo de error de stdin podía dejar exit 0; UTF-8 inválido se reemplazaba; y categorías de paths
se clasificaban por subcadena. V1 no leyó Docker ni escribió evidencia; no se considera ejecutado
ni consumido.

Se preparó el [diagnóstico TypeScript V2](operaciones/jit_h3req1_g03_r9_tsc_project_config_v2_once_2026-10-10.md),
SHA-256 `c7ee6073c31af1101ece522605389b586c7f0cda9dfba871b63d1bd73b90631a`, con helper
`r9_tsc_config_filter_v2.js`, SHA-256 `d60133e9c431e6a9fe176a70950b56aebdf25e540801551c4006feaaebabdccd`.
V2 agrega error de stdin con exit no cero, decodificación UTF-8 fatal, clasificación de raíces
anclada y secuencia PASS exacta obligatoria. Pasaron `bash -n` del bloque y la revisión de
whitespace; revisión independiente de seguridad no encontró hallazgos restantes y confirmó pins
y WIP `55/287/0`. El entorno y snapshot local están presentes, el path de evidencia está libre,
pero el helper no se ejecutó en Docker y `tsc --showConfig` no se repitió. V2 requiere aprobación
independiente; V1 no autoriza V2. G03 sigue abierto; F1 y etapas dependientes permanecen detenidas.

## Corte anterior — r9 V7 consumido en TypeScript sin diagnóstico — 10% — 2026-10-10

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`, WIP actual
55 tracked/284 untracked/0 staged. El checkout original `/home/romel/src/studiamatch` se
preservó; no se leyeron `.env*` ni secretos.

### Resultado de r9 V7

El JIT preparado [r9 image-read classified V7](operaciones/jit_h3req1_g03_r9_image_read_classified_v7_once_2026-10-10.md),
SHA-256 `ccbedbf6b9a830a247e61a65e408ef6246b1adac4d74ab8dca0719b31b102868`, se ejecutó una
vez mediante TTY Ubuntu WSL, como romel no-root, con el permiso de sandbox escalado solicitado;
sin `sudo`. La evidencia sanitizada es
[h3req1_g03_r9_v7_execution_2026-10-10.txt](evidencia/h3req1_g03_r9_v7_execution_2026-10-10.txt).
Rama, HEAD, WIP `55/282/0`, hash del runner, manifests y fuentes fijadas coincidieron. Resultado:

```text
phase=r9-reused-web-inputs|error_code=HASHES_MATCH
phase=r9-image-read-classifier-synthetics|error_code=OK
phase=r9-continuation-preflight|error_code=OK
phase=r9-continuation-preflight|error_code=OK
phase=r9-actionlint-reuse|error_code=INPUT_HASHES_MATCH
phase=r9-tool-extraction|error_code=OK
phase=r9-shellcheck|error_code=OK
phase=r9-candidate-copy|error_code=OK
phase=r9-npm-dependency-manifest|error_code=OK
phase=r9-node-and-typescript-versions|error_code=OK
phase=r9-next-typegen|error_code=OK
phase=r9-eslint|error_code=OK
phase=r9-typescript|error_code=CHECK_FAILED
exit=134
```

Los cuatro casos sintéticos del clasificador, los pins, actionlint reutilizado por hashes
idénticos, extracción de herramientas, ShellCheck, copia, manifest de dependencias, versiones,
typegen y ESLint pasaron. TypeScript terminó con exit 134; el runner redirigió su diagnóstico
crudo y solo conserva fase/exit. La causa exacta no está demostrada (no inferir OOM, defecto de
producto ni señal concreta). Stop-on-failure dejó sin ejecutar las suites de workflow protegido,
credential scan y path guard. V7 está consumido; no se repite intacto.

G03 continúa 0/10 porque r9 no completó todos sus checks. G01=0/10, G02=10/10 y G04–G10=0/10;
total inicial 10%, final 10%, delta 0 puntos. No hay GO. No se hicieron cambios funcionales ni
operaciones DB/SQL, publicación, push/PR/merge, configuración remota o deploy.

El siguiente paquete agrupado [diagnóstico TypeScript y continuación r9 V1](operaciones/jit_h3req1_g03_r9_tsc_diagnostic_continuation_v1_once_2026-10-10.md)
está preparado, JIT SHA-256 `1847596f63eafb4f0bb1074d581bc058a602b6d065e60f7324112de66aa17eff`.
Sus runners/classifier tienen hashes fijados en el paquete; sintaxis Bash y `git diff --check`
pasaron. Los siete sintéticos del clasificador se ejecutarán dentro del contenedor solo tras
aprobar el JIT. Hubo una comprobación `py_compile` del helper temporal en el host durante su
preparación; no ejecutó la aplicación ni suites y no sustituye validación dentro de Docker.
El nuevo paquete captura el fallo TypeScript en forma sanitizada y, solo tras PASS, corre las tres
suites restantes no alcanzadas. No reejecuta actionlint, ShellCheck, ESLint ni typegen con inputs
idénticos; no aumenta recursos/retries. Requiere aprobación independiente; V7 no la cubre.

## Corte anterior — r9 V6 consumido en lectura de imagen; causa no clasificada — 10% — 2026-10-10

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`, WIP actual
55 tracked/282 untracked/0 staged. El checkout original `/home/romel/src/studiamatch` no fue
modificado en este ciclo. No se leyeron `.env*` ni secretos.

### Resultado de r9 V6

El usuario aprobó `H3REQ1-G03-R9-OUTPUT-CAPTURE-V6-ONCE-20261010-V1`, JIT SHA-256
`7592aaa6d29a3aa70513780087ecb2ae65b89076c772afe8667fdca3ebf17e95`. Se comprobó antes del
despacho rama, HEAD, WSL, usuario no-root, WIP `55/280/0`, SHA del JIT y runner; todos
coincidieron. El bloque exacto corrió una vez con TTY, timeout 180 s y cero retries. Resultado
sanitizado durable en [evidencia V6](evidencia/h3req1_g03_r9_v6_execution_2026-10-10.txt):

```text
phase=r9-reused-web-inputs|error_code=HASHES_MATCH
phase=r9-context|error_code=IMAGE_READ_FAILED
exit=1
```

La comparación del endpoint `default` pasó antes de intentar leer la imagen. La lectura
`docker image inspect` fijada para `studiamatch-h3req1:20261009-v3` devolvió error; V6 descartó
stderr, así que no se atribuye la causa al socket, la imagen ni Docker Desktop. Se detuvo antes de
validar el contenedor/volumen, crear el contenedor efímero, ejecutar ShellCheck, ESLint, typegen,
TypeScript o suites. No hubo cambios de Docker ni recursos nuevos. V6 queda consumido y no se
repite.

### Estado de autorización, gates y siguiente acción

Se preparó una autorización nueva y agrupada, [r9 image-read classified V7](operaciones/jit_h3req1_g03_r9_image_read_classified_v7_once_2026-10-10.md),
JIT SHA-256 `ccbedbf6b9a830a247e61a65e408ef6246b1adac4d74ab8dca0719b31b102868`. Su runner V7
SHA-256 es `a388d9264e68579161e7631002933ce5e6e0615fba12106c02ae098a0ed68614`. Requiere una
invocación nueva en TTY Ubuntu WSL como romel no-root, sin sudo, con `sandbox_permissions=require_escalated`.
Clasifica en memoria el error de la lectura única; solo si la imagen/digest
coincide continúa r9. La solicitud sigue pendiente; V6 no la autoriza.

V15 conserva evidencia de reducción sintética `{NanoCpus, HostConfig.Mounts}`; no demuestra causa
del producto. V7 falló al renderizar el residual y V8 de tmpfs fue aprobado/consumido sin salida
recuperable. No se repiten. No hay control F1 acreditado ni corrección adicional demostrada.
Se conserva la preparación del CI independiente, pero no hay publicación, required check ni
enforcement remoto.

| Gate | Estado | Evidencia vigente |
|---|---:|---|
| G01 SQL/wire/editorial | 0/10 | C02 reconciliado 69/72; el harness editorial PG17 no conserva exit acreditable. |
| G02 suspensión SQL | 10/10 | C03 SQL aislado v3, 41/41 inputs; no acredita integración. |
| G03 tooling | 0/10 | Actionlint PASS histórico con hashes fijados; V6 se detuvo antes de ShellCheck y checks restantes. |
| G04 F1 | 0/10 | Reducción sintética parcial; F1 no leído por esta ejecución. |
| G05 copia | 0/10 | No ejecutada. |
| G06 Pages/workerd | 0/10 | No hay arranque/healthz vigente. |
| G07 Edge/PG17/PostgREST/C03 integrado | 0/10 | Sin ejecución integrada. |
| G08 checks | 0/10 | Checks finales Docker pendientes. |
| G09 aceptación | 0/10 | UAT 144 sin retry, onboarding 10/10, revisión/pilares pendientes. |
| G10 CI | 0/10 | Patch local preparado; enforcement no acreditado. |
| **Total** | **10%** | **Inicial 10%; final 10%; delta 0 puntos. No GO.** |

La preparación y la evidencia parcial no suman puntos. `GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` y
D01–D14 siguen NO-GO. No se ejecutaron operaciones DB/SQL nuevas, publicación, push/PR/merge,
configuración remota ni deploy.

## Corte anterior — r9 V5 aprobado y despachado una vez; salida no recuperable — 10% — 2026-10-10

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`, WIP
55 tracked/279 untracked/0 staged. Checkout original preservado en `/home/romel/src/studiamatch`,
rama `feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`,
último WIP registrado 39/39/0. No se leyeron `.env*` ni valores secretos.

Inventario Docker read-only 2026-10-10: `studiamatch-dev` ID
`500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, imagen local
`studiamatch-h3req1:20261009-v3` (`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`),
`running|healthy`, labels Compose `studiamatch-h3req1/app`; bind mount en `/app` y volumen
`studiamatch_h3req1_node_modules` en `/app/web/node_modules`, ambos RW. No se consultó `Env` ni
contenido de mounts. El checkout original sigue preservado para rollback. Cleanup V6 se consumió
antes de eliminar recursos: no retiró los IDs ni redes fijados. El JIT r9 V5 se despachó después,
pero su salida no es recuperable; este inventario no acredita qué fase alcanzó ni sustituye sus
resultados de tooling.

### Tareas y gates concretos

1. **r9/G03:** r9 V4 fue aprobado/consumido. Preflight, entorno aislado, sintéticos y actionlint
   pasaron. ShellCheck detuvo el runner antes de ESLint, TypeScript y suites focales.
2. **Diagnóstico ShellCheck V1:** aprobado/consumido una vez; sintéticos pasaron, el parser
   rechazó el formato y devolvió `OUTPUT_INVALID`. La salida JSON cruda se descartó. La revisión
   del manual oficial confirma que `json1` es un objeto con `comments`, mientras `json` legado es
   un arreglo; el V1 esperaba la raíz equivocada, compatible con su fallo, pero no se afirma que la
   respuesta real descartada haya sido capturada.
3. **Diagnóstico ShellCheck V2:** aprobado/consumido una vez, JIT SHA
   `21453beda3f35d82cb4091d5b5c7a164837f583ff275381065479f340fde20bb`. Preflight, extracción y
   34 sintéticos pasaron. La única pasada ShellCheck clasificó el defecto real y paró con exit 1:

   ```text
   phase=shellcheck-diagnostic-preflight|error_code=OK
   phase=shellcheck-diagnostic-preflight|error_code=OK
   phase=shellcheck-diagnostic-tool-extraction|error_code=OK
   phase=shellcheck-diagnostic-synthetics|error_code=OK
   phase=shellcheck-diagnostic|error_code=CHECK_FAILED
   diagnostic=script=scripts/security/scan_credentials.sh|line=195|column=5|rule=SC2209
   exit=1
   ```

   No se conserva texto crudo. SC2209 corresponde a asignar el literal `diff` sin comillas en
   `mode=diff`; ShellCheck exige citar el literal que no representa un nombre de comando. Se
   corrigió únicamente esa asignación a `mode="diff"` en el candidato. La cita no cambia el valor
   de la variable. `bash -n` y `git diff --check` focal dieron PASS.
4. **Snapshot r9 V5:** el paquete r5 del diagnóstico tenía una versión anterior del único archivo
   fuente `scripts/security/scan_credentials.sh`; r6 refresca ese archivo desde el candidato y
   regenera sus manifiestos. El archivo actual contiene WIP previo además del quote fix; no se
   atribuyen al arreglo de SC2209. Los demás archivos del paquete permanecen idénticos. El r9 V5
   verifica 68/68 fuentes actuales, hashes completos del paquete, los inputs web y conserva los
   hashes de los tres workflows del actionlint PASS de V4. Así reutiliza actionlint sin repetirlo;
   después revisa el marcador Node/dependencies, regenera `next typegen` en el scratch temporal y
   corre ShellCheck, ESLint, `tsc --noEmit` y las tres suites que V4 no alcanzó.
5. **JIT r9 V5:** el usuario aprobó el JIT SHA-256
   `0cdd62518f924693c0c05b45a69ecaf8a2bf4b4b0d96001f1bde75a39f403eb6`; runner host SHA
   `1aa13c054482eecfb78f586913a0a9d60e437606c1a432c72400c86d040da862`; helper de contenedor SHA
   `b4835a286ef036ca733efe6a49be9cc37b19d16bb5ddbfb4a6ea90065461ab71`, clasificador json1 SHA
   `07a8401aa6a89275362e2456655ad79ec00ff6d3629da5059e851a2520cc38a4`. Se despachó una sola vez
   como `romel` no-root en Ubuntu WSL interactiva. La salida del ejecutor no quedó recuperable;
   no hay fases, exit ni diagnóstico verificables. La invocación se considera consumida y no se
   repite. No se atribuye PASS/FAIL a ShellCheck, lint, typegen, TypeScript ni suites. Detalle y
   comando: [JIT r9 ShellCheck continuation V5](operaciones/jit_h3req1_g03_r9_shellcheck_continuation_v5_once_2026-10-09.md),
   con el registro de ejecución en [evidencia V15/Docker/SQL/CI](evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md).
6. **CI independiente:** patch PWI local SHA-256
   `033fe1263ceb86b1f609613de52de41b071153f7e8eabb6a11848b5b69c1a450`; aplicación aislada,
   `diff --check` y coincidencia de cuatro rutas pasan. Sin publicación, check requerido ni
   enforcement remoto; G10 sigue 0/10. Revisión focal adicional: el patch toca cuatro rutas de
   control; el workflow PWI nuevo se activa por `pull_request_target`/`pull_request_review`, sin
   `push`, schedule, `workflow_dispatch` ni job de despliegue. Pages sigue con include `*`, por lo
   que una integración futura puede generar Preview; no se observó run ni deployment y no se
   modifica configuración remota. GitHub MCP confirma `main` como default; el paquete ya registra
   que `pull_request_target` solo queda disponible tras instalar el workflow en esa rama. La
   instalación inicial sigue bajo las protecciones existentes y revisión humana; no se declara
   efectivo el control nuevo durante ese bootstrap.
7. **Etapas siguientes:** luego de completar r9 se evalúa F1 según su JIT vigente; después copia,
   Pages/workerd hasta `healthz`, Edge/PG17/PostgREST/C03 integrado, aceptación, UAT 144 sin retry,
   onboarding separado 10/10, revisión y seis pilares. No se avanzó ni se autorizan operaciones
   remotas con este JIT.

### Gates y métrica

| Gate | Estado vigente | Evidencia / bloqueo |
|---|---:|---|
| G01 SQL/wire/editorial | 0/10 | C02 reconciliado 69/72; harness editorial pendiente de renovar en PG17. |
| G02 suspensión SQL | 10/10 | C03 SQL v3 41/41 inputs exactos; runtime integrado pendiente. |
| G03 tooling | 0/10 | actionlint PASS previo en inputs fijados; SC2209 corregido localmente. El resultado de r9 V5 no es recuperable; ShellCheck/lint/typegen/tsc/suites actuales carecen de evidencia verificable. |
| G04 F1 | 0/10 | V15 parcial; controles F1 no acreditados en este corte. |
| G05 copia | 0/10 | No ejecutada. |
| G06 Pages/workerd | 0/10 | Arranque y `healthz` no acreditados. |
| G07 Edge/PG17/PostgREST/C03 integrado | 0/10 | Sin runtime integrado; conservación y recuperación no acreditadas. |
| G08 checks | 0/10 | Checks finales Docker pendientes. |
| G09 aceptación | 0/10 | Cuatro ajustes, UAT 144, onboarding 10/10, revisión y pilares pendientes. |
| G10 CI | 0/10 | Patch PWI local; sin required check ni enforcement. |
| **Total** | **10%** | Solo G02 completa; no hay GO. |

La aprobación y el despacho de V5, igual que el diagnóstico, el arreglo local, manifests y
preparación, no completan un gate: total **10%**, delta **0 puntos**. `GO_LOCAL_PR`,
`GO_DEVELOPMENT_REAL` y D01–D14 siguen NO-GO.

### Revisión estática y paquete siguiente — aceptación UI/V6 pendiente — 2026-10-10

Después del despacho V5, revisión focal de los cuatro ajustes: no se demostró defecto de
producto. Migration/PG17 ya expresan actor, fecha, before/after, atomicidad, límite inclusivo
de 90 días, rechazo de exceso, ausencia y compatibilidad legacy; esa cobertura SQL actual no
se ejecutó en este corte. Sí faltaba en la UAT existente una comprobación de que la UI Admin
rechaza >90 días antes del RPC y mantiene el formulario de disponibilidad oculto para `user`.
Se ampliaron esos dos casos H3-CA4.2 ya existentes, sin sumar casos: siguen siendo 48 × 3.
El contrato estático también comprueba que el guard de UI preceda a `admin_set_course_availability`.
Hashes actuales: `tests/h3_local_uat.mjs` `6db4d61def41dba7f932c1f59278a52ec1162945c57b847ace8cbec1ccf730a1`;
`tests/test_h3_admin_queue_ux_contract.py` `4cf3f2841dfaac14178e1331ac03cd6bee6046a6ec1a8ce750c03fd3732295b1`.
`git diff --check` y `bash -n` del comando de paquete pasaron. Además, cinco sintéticos
aislados del filtro de salida V6 pasaron: acepta fase/exit/diagnóstico allowlisted y rechaza
texto crudo y una ruta diagnóstica no permitida. No se ejecutaron suites de producto, DB, Docker
ni browser UAT. Los cambios solo añaden cobertura y no alteran runtime/producto.

V5 continúa consumido con salida no recuperable; no se repite. Se preparó para aprobación nueva
el JIT G03 V6 de captura durable, SHA-256
`7592aaa6d29a3aa70513780087ecb2ae65b89076c772afe8667fdca3ebf17e95`, ejecutable solo si
coinciden WIP `55/280/0`, branch/HEAD, snapshot r6, tools e imagen/contendor fijados. No se
despachó. El registro focal está en
[reconciliación V15/Docker/SQL/CI](evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md)
y el [paquete G03 V6](operaciones/jit_h3req1_g03_r9_output_capture_v6_once_2026-10-10.md).
El total sigue **10%**, delta **0 puntos**; G03=0/10 y G09=0/10 hasta ejecución/evidencia.
Lectura read-only GitHub MCP 2026-10-10: `.github/workflows/protected-workflow-integrity.yml`
no existe en `main`; búsqueda de PRs para `romelhc95:feat/h3req1-sync-20261002` hacia
`desarrollo` devolvió `[]`. No se publicó ni abrió PR; G10 continúa 0/10 y la promoción sigue
pendiente de autorización separada.

## Corte anterior — PG17 editorial parcial; candidato Docker saludable; limpieza V6 consumida sin cambios — 10% — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
WIP: 55 rutas tracked modificadas, 270 entradas untracked, 0 staged. Checkout original
`/home/romel/src/studiamatch`: rama `feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`, WIP 39 tracked/39 untracked, 0 staged.
Ambos se preservan; no se leyeron `.env*` ni valores de secretos.

### Tareas concretas, gates y ficha de impacto

1. **SQL/editorial:** C03 safe-suspend/resume v3 se reconcilió contra sus 41 rutas exactas:
   41/41 coinciden, 0 ausentes/deltas, sin ejecutar SQL. La aprobación PG17 editorial V2 se
   consumió y dejó `preflight`, parser/sintéticos de versión, start, ready, harness y cleanup en
   `OK`; el marcador `h3_pg17_harness_ok` fue observado, pero el exit numérico no se conservó.
   Ese harness editorial no pertenece a las 41 rutas C03. G01 sigue 0/10; G02 permanece 10/10
   solo para el subgate SQL C03 exacto. Sin crédito para integración C03.
2. **Tooling/V15:** la reducción sintética acreditó `{NanoCpus, HostConfig.Mounts}`; no atribuye
   causa al producto. V15 output-contract V2 se consumió con `PHASE_ORDER_MISMATCH`, antes de F1.
   El split-pair V7 pasó cuatro sintéticos y falló en `INSPECT_TEMPLATE_TMPFS_EVALUATION_ERROR`
   para el residual; V8 se aprobó y consumió sin phase/exit recuperable. No se repiten esas
   invocaciones. La composición final, lectura F1 y r9 requieren paquete y autorización nuevos.
3. **Auditoría npm:** JIT V3 aprobado y consumido; exit 1 en sintéticos porque dos rutas del
   wrapper apuntaban a archivos `_v2.py` ausentes mientras el mount contiene `_v3.py`. No hubo
   solicitud al registry. npm V4 fue aprobado y consumido: las seis pruebas de captura y 16
   sintéticos dieron `OK`; `npm-audit` terminó en `EMPTY_STDOUT_STDERR_PRESENT` (stdout vacío,
   stderr presente sin código allowlisted). No se obtuvo JSON ni se puede concluir si el registry
   recibió o respondió. No se repite.
4. **Docker/entorno:** la invocación V5 recibió aprobación y terminó exit 1 después de activar el
   candidato. La lectura puntual confirma `studiamatch-dev`, ID
   `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`, imagen
   `studiamatch-h3req1:20261009-v3` (ID `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`),
   estado healthy, checkout candidato bind-mounted en `/app` y volumen
   `studiamatch_h3req1_node_modules` en `/app/web/node_modules`. `studiamatch-h3req1-node-deps`
   terminó exit 0. El contenedor original ID `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`
   quedó preservado como `studiamatch-original-dev-20261009`, exited 1; conserva el checkout
   original y `studiamatch_node_modules` para rollback. Sin `.env*` leído ni valores expuestos.
   V6 fue aprobado y consumido una vez: `candidate-wip|OK`,
   `cleanup-preflight|CONTAINER_MISMATCH`, `runner-exit|EXIT_1`. Falló dentro de
   `verify_container`, antes de `cleanup-preflight|OK` y antes de toda llamada `docker rm` o
   `docker network rm`; no se retiró ningún contenedor ni red. La rutina no emitió ordinal/campo
   para la tupla discrepante. Una consulta read-only posterior, limitada a los 11 IDs fijados y a
   nombre/imagen/estado/exit/restart, encontró sus tuplas iguales a las esperadas; esto no recupera
   el valor que observó el JIT ni identifica cuál discrepó entonces. No se atribuye causa ni se
   repite la limpieza. JIT SHA `efcce4f8e762264a41b766904c0e4f1aaa3d4d4023ff3a289a80d761d62acdd9`
   y runner SHA `37386e4a640618356f7cea8ac630ae298e8537380680255e4a4105e127214e63` están
   consumidos. El preflight había acreditado candidato/rollback antes de cleanup. No avanzó r9 ni
   ningún gate local.
5. **CI independiente:** se revalidó r4 en `/tmp/h3req1-g03-validation-29d8fff9-r4`: manifests
   internos 71/71; 68/71 hashes de fuentes actuales coinciden, tres auxiliares son package-only y
   hay cero drift. El wrapper fija rama/HEAD/WIP y compara esos hashes antes de Docker. Paquete
   SHA `ca30a43c990e45e634412219c9a28d964b410068671c499048e80f2ff8c9068b`, inputs
   `b57603e8e75eb456a71e10ca45326c13e281ecb9e99b056ed163757c2292e2be`, tools
   `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`, runner
   `5197e0f8be7583394903fbac629bee94ff55cd084130d8f1a8c78c0c958721ba`. Bash, manifests, source
   gate, límites y aislamiento estático PASS; las suites no se ejecutaron. JIT r9 SHA
   `d0a99744cf964d4a55fc3e104d74a4913093d394379e89351584dcb209c5c931` está preparado y espera
   aprobación para una invocación. Patch PWI V4 SHA
   `68bb4037f665c4e82c91b89faae939a20ab90cebbf85cff0b4a2f90b19682c26`: aplica en snapshot limpio
   de HEAD y el helper/tests coincide con el candidato. No se ejecutó pytest/actionlint/Docker r9,
   ni se publicó, instaló o configuró CI remotamente; G10 sigue 0/10.
6. **Aceptación y cierre local:** r9, copia íntegra, Pages/workerd hasta healthz, integración
   Edge/PG17/PostgREST, C03 integrado, cuatro ajustes, revisión independiente, UAT 144 sin
   retries, onboarding separado 10/10, atestación cliente y seis pilares siguen pendientes.
   La matriz de los cuatro ajustes permanece en
   [la aclaración de origen BFF y ruta de ajustes](evidencia/h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente).

### Evidencia vigente y métrica

- [Ejecución PG17 y corrección npm V4](evidencia/h3req1_pg17_npm_v4_execution_and_preparation_2026-10-09.md).
- [Preparación y resultado Docker cutover V4/V5/V6; candidato saludable, cleanup V6 consumido sin cambios](evidencia/h3req1_docker_candidate_cutover_v4_preparation_2026-10-09.md).
- [Preparación CI PWI y r9; patch V4 aislado PASS, r9 JIT pendiente](evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md).
- [JIT npm V4](operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v4_once_2026-10-09.md),
  [JIT Docker V4 consumido](operaciones/jit_h3req1_docker_candidate_cutover_v4_once_2026-10-09.md)
  y [JIT Docker V5](operaciones/jit_h3req1_docker_candidate_cutover_v5_once_2026-10-09.md): npm
  V4 terminó con salida incompleta; Docker V4 se consumió antes de Docker por desajuste de WIP;
  Docker V5 se aprobó y consumió, dejó health PASS, pero se detuvo antes de retirar recursos por
  `VOLUME_MAP_MISMATCH`. No se reintenta; V6 corrige el predicado y espera autorización para la
  limpieza exacta.
- [JIT Docker cleanup V6](operaciones/jit_h3req1_docker_candidate_cleanup_v6_once_2026-10-09.md),
  SHA `efcce4f8e762264a41b766904c0e4f1aaa3d4d4023ff3a289a80d761d62acdd9`: aprobado y
  consumido; preflight falló con `CONTAINER_MISMATCH`, sin cleanup. No se reintenta ni suma puntos.
- [JIT r9 candidate V4](operaciones/jit_h3req1_g03_r9_candidate_v4_once_2026-10-09.md),
  SHA `d0a99744cf964d4a55fc3e104d74a4913093d394379e89351584dcb209c5c931`: preparado con gate
  de hashes del candidato; pendiente de aprobación para una invocación. No suma puntos.
- G01 0/10; G02 10/10 solo por el SQL C03 v3 exacto; G03–G10 0/10. Total
  **10%**, delta **0 puntos**. No se suman documentación, hashes, sintéticos aislados ni
  preparaciones.
- No hay `GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` ni D01–D14. No se modificaron ramas remotas,
  GitHub, Cloudflare, Certification o Production.

La siguiente actualización se hará después de resultados reales o un gate completado.

## Corte previo — PG17 VERSION_MISMATCH; parser npm corregido, nueva invocación pendiente — 10% — 2026-10-09 (conservado)

### Detalle preservado del corte anterior — PG17 VERSION_MISMATCH; parser npm corregido — 10% — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
WIP observado al cierre de esta nota: 55 rutas tracked modificadas, 252 entradas untracked,
0 staged. Checkout original `/home/romel/src/studiamatch`: rama
`feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`, WIP 39/39/0. No se leyó `.env*`, no se
modificaron secretos y no se alteró el checkout original.

### Tareas, gates y resultados reales

1. Ejecutar el JIT PG17 editorial aprobado una vez. Resultado exit 1:
   `preflight=OK`, `pg17-start=OK`, `pg17-version=VERSION_MISMATCH`,
   `container-cleanup=OK`. La invocación está consumida. El runner no revela la versión real
   que observó; no se atribuye el mismatch a imagen ni a Docker y no se reintenta. La cobertura
   editorial no pasa y G01 permanece 0/10.
2. Ejecutar el JIT npm audit clasificador V2 aprobado una vez. Resultado exit 1 en
   `capture-synthetic-tests=SUMMARY_CASE_INVALID`, antes de Docker. La invocación está
   consumida; no hubo lectura de imagen, contenedor de auditoría ni egress npm.
3. Corregir el defecto mínimo demostrado del wrapper: su patrón JSON omitía las comillas de
   la clave raíz (`auditCommandExit`/`counts`). El runner anterior se conservó byte por byte en
   `evidencia/h3req1_npm_audit_capture_runner_v2_pre_fix_2026-10-09.sh`; el corregido tiene
   SHA-256 `0c48f12b818c8611c1187fa402f92bb502ed6ea45cb17cc13270db28a51a58f5`.
   `bash -n` y la revisión de whitespace del runner pasaron. No se ejecutaron los sintéticos
   fuera del JIT.
4. Preparar una nueva solicitud concreta, sin usar la autorización consumida:
   `operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v2_fixed_capture_once_2026-10-09.md`.
   SHA-256 `f06d497bfcc26cd321b6a2b96ebc8c2d2bc8fedfecf187df9eb00cdd601c9aea`; falta aprobación
   humana para una nueva invocación.
5. Preparar un diagnóstico estrictamente read-only para conocer `postgres --version` real del
   digest que falló, sin repetir harness ni SQL:
   `operaciones/jit_h3req1_pg17_pinned_image_version_once_2026-10-09.md`, SHA-256
   `a7787182737186ae43cb4e82f6f88a4fb7a71bdf52e2de7e1f9967672c2835b1`. Está pendiente de
   aprobación, no ejecutado. No hay otra operación Docker autorizada ejecutable en este corte.

### Estado de cierre y evidencia

- Evidencia conjunta y matriz de resultados: [PG17 y parser npm V2](evidencia/h3req1_pg17_and_npm_capture_execution_2026-10-09.md).
- Evidencia PG17 sanitizada: [resultado de la invocación](evidencia/h3req1_editorial_atomicity_pg17_once_2026-10-09.md).
- Evidencia de preservación del runner fallido: [runner V2 previo a la corrección](evidencia/h3req1_npm_audit_capture_runner_v2_pre_fix_2026-10-09.sh).
- Solicitudes concretas pendientes: [lectura PG17 fijada](operaciones/jit_h3req1_pg17_pinned_image_version_once_2026-10-09.md) y
  [npm V2 con captura corregida](operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v2_fixed_capture_once_2026-10-09.md).
- G01 0/10; G02 10/10 (C03 SQL v3 41/41, manifest separado); G03 0/10; G04–G10 0/10.
  Total 10%, delta 0 puntos. Hashes, sintaxis, limpieza o documentación no suman controles.
- No hay GO_LOCAL_PR ni GO_DEVELOPMENT_REAL. F1/r9, copia, Pages/workerd, integración
  Edge/PG17/PostgREST, C03 integrado, checks finales, UAT 144, onboarding separado 10/10 y
  enforcement CI efectivo siguen sin acreditarse.

## Corte anterior — auditoría npm V3 REPORT_INVALID; cobertura atomicidad editorial preparada, PG17 pendiente — 10% — 2026-10-09 (conservado)

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
WIP preservado: 55 tracked modificados, 247 entradas untracked, 0 staged. Checkout original
`/home/romel/src/studiamatch`: rama `feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`, WIP 39/39/0. No se modificó.

### Tareas, gates y ficha de impacto

1. Reconciliar resultado V15 y comprobar que no hubiera ejecución posterior: completado.
2. Corregir/reconciliar el parser de salida V15 V2 contra el orden real del helper; validar
   V3 con sintéticos y preservar la reducción ya obtenida: completado localmente; no se leyó F1.
3. Ejecutar V8 bajo la autorización recibida: Codex intentó la invocación PTY única, pero la
   salida de herramienta quedó truncada y no se recuperó por terminal. Resultado/exit no
   verificables; no se declara PASS/FAIL, no se reejecuta y no se afirma acceso F1/r9.
4. Ejecutar auditoría read-only de los advisories `npm ci` reportados por V3, fijada a su
   digest/manifests: aprobación recibida y JIT consumido; imagen y sintéticos alcanzados, pero
   npm no produjo un reporte JSON aceptado (`REPORT_INVALID`, exit 1). El detalle crudo fue
   descartado por diseño. Sin retry ni remediación de dependencias. Preparado un clasificador
   sanitizado v2 con pruebas sintéticas. Su JIT nuevo
   `operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v2_once_2026-10-09.md`, SHA-256
   `1a70db5a61e9fdf63660b296404c8ec188014b0d1b08bb8f9148975e6902ac2e`, requiere autorización
   nueva para una invocación; no se ha ejecutado.
5. Reparar y revisar mecánicamente el dispatcher Docker V3, conservando el rebuild/cutover
   reversible y la limpieza exacta: checker mecánico PASS; JIT aprobado y consumido; build y
   smoke PASS; cutover FAIL por `.env.local` ausente en el candidato; rollback PASS.
6. Alinear el helper/tests PWI al requisito documentado de tipo humano y refrescar patch V4:
   aplicación aislada y pruebas locales focales PASS; pytest oficial y revisión independiente
   V4 pendientes.
7. Continuar r9, copia, arranque Pages/workerd, Edge/PG17/PostgREST, C03 y aceptación tras sus
   gates y JIT aplicables.
8. Corregir la falta de cobertura de atomicidad de auditoría editorial: test-only añadido al
   harness PG17, revisión estática PASS, 36/36 inputs fijados; SQL no ejecutado. El JIT nuevo
   `operaciones/jit_h3req1_editorial_atomicity_pg17_once_2026-10-09.md`, SHA-256
   `a795528ec0376ac64a88344a03380644eed5122da9f52ffd44cf19cd3b923ef7`, está preparado y
   requiere autorización antes de crear el PG17 efímero.
9. La aprobación recibida nuevamente para npm audit SHA `d14b4f8…` corresponde al JIT ya
   consumido con `REPORT_INVALID`; no autoriza retry. El clasificador V2 separado requiere
   autorización nueva.

### Cobertura editorial atómica: implementada en harness, runtime pendiente

La matriz vigente tenía evidencia de actualización exitosa, conflicto de versión,
actor/fecha/antes/después, reset de override y acceso de auditoría protegido, pero no
provocaba un fallo del append ni demostraba rollback de la mutación. Se añadió una inyección
de `CHECK NOT VALID` de alcance exclusivo `action='update'`, verificación exacta de
`CONSTRAINT_NAME`, comparación del registro completo `course_editorial_state` y conteo de
auditoría, y retirada del constraint antes del camino positivo. No se alteró la migración de
producto. Revisión estática, `bash -n`, `git diff --check` del harness, whitespace check de los
archivos nuevos y cierre de hashes 36/36 PASS; ningún SQL/PG17/Docker se ejecutó.

Ficha: solo `tests/sql/h3_pg17_harness.sql` cambió por el test; dependencias directas son la
migración editorial y la secuencia H2/H3 más tres harnesses incluidos. Manifest
`operaciones/manifest_h3req1_editorial_atomicity_pg17_2026-10-09.sha256` fija los 36 inputs.
El runner `tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_once.sh` usa la imagen
PG17 fijada, un contenedor `network none`, bind mounts SQL read-only y PGDATA tmpfs; no monta
`.env*`, no hace pull, egress, ni writes remotos. Se eliminará el contenedor exacto tras
preservar fases sanitizadas. La ejecución necesita aprobación nueva por el cambio de hash.
G01/G09 siguen parciales; total **10%**, delta **0**. G02 safe-suspend C03 v3 41/41 conserva
su manifest independiente y no cubre esta propiedad editorial.

Evidencia de preparación: `evidencia/h3req1_editorial_atomicity_pg17_preparation_2026-10-09.md`.

### V8 Tmpfs: aprobación recibida; resultado de invocación no recuperable

Se preparó el JIT [V8 Tmpfs pair diagnostic](operaciones/jit_h3req1_docker_desktop_wsl_f1_tmpfs_pair_diagnostic_v8_once_2026-10-09.md),
SHA-256 `f286b7c916fb434d7f55afa6d8bb0104df4d9bd52d382e061fe2570f1438477d`. La corrección
esperada es segmentar el campo exacto solo si el matrix lo confirma. Una invocación buscaría
hasta 43 pares alrededor de los dos campos Tmpfs, revalidaría la contraparte del primer fallo y
probaría los 25 campos compuestos con mapas presentes/ausentes. Sin F1, r9, `studiamatch-dev`,
pull/build o cambios de Docker. La prueba sintética focal pasó 4/4, AST y `bash -n` pasaron, y
el checker estático confirmó pins, comando, límites y scope. La herramienta Codex Security
rechazó el scope focal y exigió `scope='.'`; no inició un scan ni produjo scan ID porque eso
abarcaría todo el WIP. La revisión estática local sigue siendo parcial e independiente pendiente.
La aprobación V7 SHA `a602ee00fe5168cab2216c92799154801903fad84627d3e204e8461411e30cfd` está
consumida; no se repite. El usuario aprobó V8 SHA
`f286b7c916fb434d7f55afa6d8bb0104df4d9bd52d382e061fe2570f1438477d`. Codex emitió el comando
fijado con PTY, pero la llamada de herramienta quedó sin salida recuperable; el lector del
terminal tampoco devolvió salida y una comprobación de procesos no encontró el runner activo.
Se trata la autorización como consumida para impedir replay. No hay fase ni exit verificables:
no se asigna PASS/FAIL ni se afirma que Docker/F1/r9 fueran alcanzados. Evidencia y límite en
`evidencia/h3req1_v8_execution_capture_and_npm_audit_preparation_2026-10-09.md`.

### Auditoría de advisories de imagen V3: invocación consumida, reporte inválido

`npm ci` durante V3 informó un advisory `high` y uno `critical`; el detalle no quedó guardado.
El paquete `operaciones/jit_h3req1_candidate_v3_npm_audit_once_2026-10-09.md`, SHA-256
`d14b4f8c6bec307c401b0ddda4fa73e249fc6d7e3058178a10525dc2ca4293fd`, fija imagen
`sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`, manifests, tests y
salida. Ejecuta seis pruebas y una auditoría npm en un único contenedor read-only efímero;
envía el árbol de dependencias al registry público, sin tarball/pull/build. Bash `-n` pasó,
los hashes de package/lock coinciden y los pines de fuentes están fijados. El usuario aprobó
una invocación; el runner se ejecutó una vez en PTY como `romel` no-root y terminó exit 1 con
`phase=image-preflight|error_code=OK` y `phase=npm-audit|error_code=REPORT_INVALID`. El runner
emite esa segunda fase solo después de validar el marcador exacto
`V3_NPM_AUDIT_SYNTHETIC_PASS:6/6`, así que los sintéticos dentro de la imagen pasaron y se
alcanzó el parser del stdout de npm. `REPORT_INVALID` corresponde a fallo de `json.loads`;
el detalle crudo fue descartado, por lo que no se distingue entre salida no JSON del cliente,
respuesta de red u otra causa. La autorización está consumida; no se repite ni se corrigen
dependencias. Evidencia en
`evidencia/h3req1_v8_execution_capture_and_npm_audit_preparation_2026-10-09.md`.

Preparé una segunda solicitud independiente para que una eventual nueva ejecución clasifique
solo la forma de stdout/stderr, sin mostrar texto crudo: JIT
`operaciones/jit_h3req1_candidate_v3_npm_audit_classifier_v2_once_2026-10-09.md`, SHA-256
`1a70db5a61e9fdf63660b296404c8ec188014b0d1b08bb8f9148975e6902ac2e`. El runner tiene
`bash -n` PASS y pines fijados. Quedan sin ejecutar seis casos sintéticos del parser Bash y
14 aserciones del clasificador dentro de la imagen; el paquete fija ambas etapas. La invocación
anterior no se repite ni se interpreta esta nueva solicitud como aprobada.

Este corte actualiza runners diagnósticos, helper/tests PWI, patch V4, evidencia e índices. No
cambia producto, SQL/wire, BFF/HttpOnly, MFA, roles, gateway, cuotas ni secretos. HEAD no se usa
como resumen del WIP. Se preservan evidencia y ambos checkouts.

### V15 y clasificación F1

V14 probó individualmente las 25 expresiones y falló con el formato completo. La reducción
V15 ya había acreditado el conjunto 1-minimal sintético `{NanoCpus, HostConfig.Mounts}`;
no atribuye causa al producto ni al daemon. La autorización V15 TTY V2, JIT SHA
`49243bda140af6038d3e93ed9a2d4d8b19b2206c54a7ac4648f2ab93d5904703`, se consumió con
`phase=f1-v15-output-capture|error_code=PHASE_ORDER_MISMATCH`, exit 1. El parser esperaba un
prefijo que el helper no emite; no alcanzó F1 ni r9. No se repiten los probes.

V7 conserva el bloque restante de 23 campos y lee las dos expresiones del par por separado;
después recompone los 25 valores en memoria y aplica el parser fail-closed existente. Las
pruebas sintéticas directas pasan 4/4: composición, mapas presentes/ausentes, rechazo de
salida malformada/sobredimensionada y restauración del formato. El parser de salida V15 V3
pasa 7/7. `bash -n` del wrapper F1 pasa. La invocación única V7 se consumió con la fase
`f1-template-synthetic-inspect` y código `INSPECT_TEMPLATE_TMPFS_EVALUATION_ERROR`, exit 1.
Pasaron endpoint, lectura de metadata de volúmenes/imagen sintética y casos unitarios. La
clasificación corresponde al residual de 23 expresiones tras separar NanoCpus/Mounts; no
identifica todavía si falla tmpfs aislado o su composición con ese residual. No se alcanzó el
smoke de mapas ausentes, no se leyó F1 y no corrió r9. La limpieza no informó fallo. Se conserva
evidencia sanitaria en la
[actualización V7 tmpfs](evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md#v7-split-pair-fallo-sintético-tmpfs--actualización-posterior).

El usuario aprobó otra invocación del mismo JIT V15 V2 SHA
`49243bda140af6038d3e93ed9a2d4d8b19b2206c54a7ac4648f2ab93d5904703`. La reconciliación
confirma que ese JIT ya se ejecutó y consumió con `PHASE_ORDER_MISMATCH`; la reducción
sintética ya acreditó `{nano-cpus, mounts}`. No inicié una repetición que volvería a ejecutar
los probes. El defecto exacto estaba en el prefijo esperado del parser V2: el código fuente
emite reducer-tests y luego el bloque anidado; V2 esperaba un bloque de clasificadores
duplicado y fuera de orden. El parser V3 ajusta únicamente ese contrato y sus pruebas locales
lo validan; no cambia el resultado del diagnóstico ni lee F1.

JIT F1 V7 [SHA-256 `a602ee00fe5168cab2216c92799154801903fad84627d3e204e8461411e30cfd`]
está consumido y no se repite. La revisión del código localiza la fase en el template sintético
que conserva `.HostConfig.Tmpfs`; la lectura del error crudo no se guardó. El siguiente paso es
aislar de forma sintética esa expresión de las demás antes de pedir autorización nueva.
El R9 se preparará contra el digest real del candidato una vez reconstruido y sano.

### Docker activo y dispatcher V3

La consulta previa de solo lectura del contenedor conocido reportó ID
`115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`, nombre
`studiamatch-dev`, imagen `studiamatch-dev:local`, estado `restarting`, RestartCount observado
2502, política `unless-stopped`; bind al checkout original
`/home/romel/src/studiamatch:/app` y volumen persistente
`studiamatch_node_modules:/app/web/node_modules`. En esa consulta no se había hecho build,
stop, rename, cleanup ni retry. La lectura read-only de los hashes allowlisted confirmó que el bind coincide con el
checkout original, los manifests de la imagen no coinciden con ese bind ni con el candidato,
el marcador del volumen coincide con la imagen y la versión instalada de `braces` no coincide
con el pin del candidato. Esto concuerda con el guard de init y demuestra un desfase activo
imagen/source/dependencia; no determina una causa única para todos los reinicios históricos.

El JIT Docker V2 ya está consumido: `npm ci` falló porque su contexto omitió el tarball local
`web/vendor/braces-3.0.4-h3.1.tgz`. El paquete V3 lo incorpora al contexto allowlisted y al
`COPY` antes de `npm ci`; no cambia package/lock. JIT V3
[SHA-256 `62ee72e2a4d6027b360234ee48bdbe1d63ee936931ad13d9169def1bda43b98e`]
(operaciones/jit_h3req1_docker_candidate_rebuild_cutover_dispatch_v3_2026-10-09.md), runner
`de178b3621bcb89d38a7e7528bd746516fe569f2a2e659645d11932253e63b2c`. La revisión mecánica
pasó: runner byte-idéntico al bloque del JIT; derivación exacta del V2 con deltas listados;
hashes/tarball, sintaxis, orden/gates, rollback, 11 IDs y cinco redes exactos. El build usa
egress de red Docker predeterminado sin allowlist de dominios; el JIT identifica descargas
previstas y posibles egress adicionales de lifecycle scripts. La aprobación V2 consumida no
se reutiliza. El usuario aprobó una invocación V3; checker, pines y preflight 55/239/0 pasaron.
Build y smoke PASS. `npm ci` instaló 627 paquetes y reportó 2 advisories (1 high, 1 critical);
no se conservó detalle de paquete. Cutover FAIL: `env file .../.env.local not found`, exit 1.
El trap reportó `RESTORED_ORIGINAL`; lectura acotada confirma el ID original como
`studiamatch-dev`, imagen `studiamatch-dev:local`, estado `restarting`, política
`unless-stopped`. El env-file del candidato está ausente; el de `/home/romel/src/studiamatch`
existe pero no se leyó ni usó. La imagen candidata quedó presente; red, volumen, provisionador
y nombre de fallo V3 están ausentes. El contexto temporal allowlisted permanece. No se alcanzó
health PASS ni la limpieza histórica; no se retiraron los 11 contenedores ni cinco redes. La
autorización V3 está consumida y no se reintenta. Resolver la fuente del env-file requiere un
paquete/JIT nuevo antes de otro cutover. No hay GO ni puntos sumados.

### SQL, C03 integrado, CI y aceptación

- C03 safe-suspend/resume SQL v3: comparación actual de las 41 rutas del manifiesto,
  41/41 coinciden, 0 ausentes/cambiadas. El PASS SQL histórico se conserva; no se ejecutó
  SQL en este corte. No acredita el drill integrado.
- C03 integrado R4: comparación actual del manifiesto de 62 entradas, 60 coinciden y dos
  cambiaron: `tests/h3req1_c03_integrated_runtime.mjs` y
  `web/functions/_lib/admin-bff.ts`. Renovar únicamente esas coberturas después del runtime.
- C02 PG17 v4: último cruce vigente 69/72; los deltas restantes son el harness editorial
  `tests/sql/h3_pg17_harness.sql`, `security-audit.yml` y `admin-bff.ts`. G01 sigue abierto.
- Bootstrap CI Protected Workflow Integrity: patch V4 de cuatro rutas preservado,
  SHA `68bb4037f665c4e82c91b89faae939a20ab90cebbf85cff0b4a2f90b19682c26`; aplica en copia
  temporal. Smoke directo 5 casos y regression shell de protected-path pasan; helper y tests
  compilan. `pytest -q tests/test_protected_workflow_review.py` no pudo correr
  (`No module named pytest`) y no se instaló nada. No está publicado, instalado ni requerido. El usuario
  informó que Actions Policies no tiene políticas; Pages conserva `main` Production con
  include `*`, exclude vacío. No se atribuye enforcement al YAML.
- Revisión focal estática PWI V4: el patch aislado obtiene workflow y helper de la rama default
  `main`; no ejecuta el head del PR. El workflow draft WIP del checkout es distinto: checkout
  del helper desde `base.sha`. Se conserva esa fuente local sin sustituir el artefacto; se añadió
  `edited` al draft para reevaluar cambios explícitos de base. El patch ya incluía ese evento.
  La comparación mecánica confirma que, normalizadas la referencia y su comentario, no hay más
  diferencias de contenido en ese workflow.
  Ninguno de estos hechos estáticos acredita el run real, la evaluación de policy ni la
  emisión/asociación del check.
  La lectura acotada del workflow/helper confirma checkout de `base.sha`, token de solo lectura,
  clasificación fail-closed de los archivos API, revisión humana no autora con asociación
  permitida y `commit_id` igual al head actual, más revalidación de head al final. Sin hallazgo
  nuevo en esta revisión estática; no se reejecutaron tests locales ni existe run remoto.
- La matriz vigente de los cuatro ajustes queda en
  [origen BFF y ruta de aceptación](evidencia/h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente).
  Sus pruebas iniciales del 2026-10-01 se preservan como parciales; no hubo revalidación
  actual de editor, auditoría, disponibilidad ni encabezado. UAT 144 sin retries, onboarding
  10/10 separado, revisión final, seis pilares y transición/rollback siguen pendientes.

| Gate | Estado | Evidencia parcial vigente |
|---|---:|---|
| G01 SQL/wire/editorial | 0/10 | C02 69/72; cobertura editorial actual pendiente. |
| G02 suspensión SQL | 10/10 | C03 SQL v3, manifiesto 41/41 actual. |
| G03 tooling | 0/10 | V7 4/4, V15 parser V3 7/7 y dispatchers estáticos PASS; V8 sin salida recuperable; npm audit V3 sintéticos 6/6, reporte `REPORT_INVALID`; G03 abierto. |
| G04 F1 | 0/10 | V15 identificó el par mínimo sintético; ejecución V8 sin resultado verificable; F1 pendiente. |
| G05 copia | 0/10 | No iniciada. |
| G06 Pages/workerd | 0/10 | No iniciado. |
| G07 Edge/PG17/PostgREST y C03 | 0/10 | R4 falló healthz; delta actual 60/62. |
| G08 checks | 0/10 | Checks finales en Docker pendientes. |
| G09 aceptación | 0/10 | Cuatro ajustes/UAT/onboarding/revisión pendientes. |
| G10 CI | 0/10 | Patch preparado; pytest no disponible, control remoto no instalado/requerido. |
| **Total** | **10%** | **Delta 0 puntos**; documentación y sintéticos no suman cierre. |

`D01–D14=0/14`; `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`: NO-GO. Publicación/configuración
CI, SQL, push/PR/merge y despliegues mantienen sus instrucciones/JIT separados. Ver la
[reconciliación vigente](evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md).

## Historial de cortes anteriores

### Corte previo — V15 V2 y Docker V2 consumidos en preflight/build FAIL — 10% — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP preservado:
54 rutas tracked modificadas, 235 entradas untracked, 0 staged. Checkout original
`/home/romel/src/studiamatch`: rama `feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`; no se modificó en este corte.

- **Tareas/gates del ciclo:** (1) reconciliar aprobaciones y consumos; (2) corregir y revisar
  V15/dispatcher; (3) preservar evidencia y gates; (4) reanudar tooling, F1, copia, health,
  integración y aceptación tras las autorizaciones puntuales pendientes. Impacto limitado a
  runners/JIT/evidencia: no cambian producto, SQL/wire, BFF/HttpOnly, MFA, roles, gateway,
  cuotas ni secretos. Los PASS previos se clasifican por sus inputs; el resultado de la suite
  editorial C02 sigue pendiente.
- **V15 anterior:** la autorización de una invocación (JIT SHA
  `b5f98329415c613f5ab4c96b3d3721db97f56cd60749748eb7eadd56666efe4c`) se consumió. El fixture
  reprodujo el error y la reducción halló el conjunto 1-minimal `{nano-cpus, mounts}`; F1/r9 no
  se alcanzaron. El FAIL del wrapper fue una discrepancia del orden esperado: el parser situaba
  `f1-v15-reducer-tests` antes de las fases de clasificador anidadas, mientras el runner las
  emite primero. Se corrigió el parser de salida y su fixture negativo/positivo. Los seis casos
  sintéticos V2 habían pasado directamente en la preparación previa; `bash -n` y compilación
  Python en memoria también pasaron allí. La nueva invocación no se ha ejecutado. El intento
  aprobado del JIT corregido SHA `b9b44f70121be8f7ca91471fdd4410767e5c160ab943996c6dee412b40e7af95`
  se consumió con `phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED`, exit 1. El despacho
  se ejecutó sin TTY interactivo; el runner se detuvo antes de Docker, tests, F1 y r9. Sin
  reintento. El intento `python3 -m pytest` de este corte terminó exit 1 porque `pytest` no
  está instalado; no se instaló nada. JIT corregido
  [V15 parser contract V2](operaciones/jit_h3req1_docker_desktop_wsl_f1_v15_output_contract_v2_once_2026-10-09.md),
  SHA `b9b44f70121be8f7ca91471fdd4410767e5c160ab943996c6dee412b40e7af95`, ahora requiere una
  invocación nueva preparada para TTY después de corregir el despacho.
- **Dispatcher Docker:** la aprobación V1 SHA
  `0d24ff2fadf0c55ce6d9a1fd5e89e71c2eddba3f15075d2e96406c0d4a367209` ya no está disponible
  para reuso. Dos despachos fueron rechazados por la revisión automática; ninguno ejecutó
  Docker. Luego hubo `ReferenceError: BUILD_CONTEXT is not defined`, también antes de Docker.
  El preflight directo posterior se interrumpió y consume conservadoramente el one-shot, aunque
  no se capturó exit; la consulta read-only posterior no halló build/cutover/cleanup ni recursos
  candidatos. No se atribuye el fallo al producto ni a `package-lock` por el error JavaScript.
  El despacho V2 queda como archivo estático y byte-idéntico a su JIT; el checker confirma los
  ocho bloques fuente en orden, hash del ejecutable, sintaxis, 11 IDs y cinco redes exactos,
  orden de etapas, gates y rollback con identidad. Resultado `static_review=PASS`, WIP
  `54/235/0`. Revisión de seguridad Codex Security completada (scan
  `[UUID redactado]`): seis archivos cubiertos, 0 findings reportables;
  revisión estática únicamente, sin runtime Docker. Nuevo paquete
  [dispatcher Docker V2](operaciones/jit_h3req1_docker_candidate_rebuild_cutover_dispatch_v2_2026-10-09.md),
  SHA `060c87cb4283ca3312746697b551de815ffc7c09b13b49f8816effee361be1ba`, fue aprobado y
  consumido en una invocación. Pasó preflight y build context; luego `npm ci` falló con exit 254
  dentro del build, runner exit 1 y `phase=image-build|error_code=COMMAND_FAILED`. La lectura
  read-only posterior confirmó que el tag candidato no existe, el contenedor original conserva
  identidad/policy y no hubo cutover/health/cleanup. El lock/package declaran
  `file:vendor/braces-3.0.4-h3.1.tgz`; el tarball fuente existe con SHA
  `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819`, pero quedó fuera del
  contexto allowlisted y del `COPY` a la carpeta de npm. Causa demostrada: contexto/COPY
  incompletos para una dependencia local; no corrupción del lockfile ni defecto del daemon.
  El contexto fallido queda preservado en `/tmp/h3req1-docker-build-v1.kAsIKK`. No reintentar.
  Preparar V3 con el tarball como input pinneado, `COPY` acotado y validación de `npm ci`; luego
  revisión automática y autorización agrupada nueva para rebuild/cutover/cleanup.
- **Entorno Docker observado:** el contenedor conocido `studiamatch-dev`, ID
  `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`, seguía `restarting`
  (RestartCount 2415 en consulta read-only); usa `studiamatch-dev:local` y el checkout original.
  No se ejecutó build, stop, rename, limpieza ni retry. Causa del estado y compatibilidad del
  contenedor con checks no están demostradas. El paquete nuevo preserva el rollback y solo
  contempla cleanup de IDs/redes exactos después de health PASS.
- **Pruebas/resultados:** checker mecánico y `bash -n` del dispatcher PASS; el test runner V15
  no se volvió a correr en esta sesión porque el host no tiene pytest y no se autorizó instalarlo.
  No hay ejecución nueva Docker, F1, r9, copia, Pages/workerd, Edge/PG17/PostgREST, C03 integrado,
  UAT 144, onboarding 10/10 ni promoción CI. CI sigue preparado localmente, no publicado ni
  efectivo.
- **G01–G10 vigentes:** G01=0/10 (harness editorial/C02 afectado pendiente); G02=10/10
  (C03 SQL v3 41/41 sigue aplicando a inputs comprobados); G03–G10=0/10. Total **10%**, delta
  **0 puntos**. El scan estático, la documentación y la preparación no suman cierre. D01–D14=0/14.
  `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`: NO-GO.
- **Siguiente acción:** V15 requiere un dispatcher que garantice TTY antes de otra solicitud.
  Docker requiere V3 con el tarball local, `COPY`, hashes y pruebas exactos; su autorización V2
  quedó consumida durante `npm ci`. Solicitar nuevos permisos después de la revisión automática.
  Luego seguir etapas autorizadas y renovables sin suites intactas; detener etapas dependientes
  ante FAIL. Publicación/settings de
  CI, PR/merge, SQL y despliegue Development mantienen autorización separada. Ver
  [evidencia del corte](evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md).

## Corte anterior — V15 ejecutado; par mínimo observado; wrapper FAIL; Docker preflight drift; 10% — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
WIP preservado: 54 tracked modificados, 233 entradas untracked, 0 staged. Checkout original
`/home/romel/src/studiamatch`: rama `feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`, 39 tracked modificados, 39 untracked, 0 staged.

- **V15:** aprobación registrada y consumida; JIT SHA
  `b5f98329415c613f5ab4c96b3d3721db97f56cd60749748eb7eadd56666efe4c`. El baseline exacto se
  reprodujo en fixture sintético y el helper informó el conjunto 1-minimal
  `{nano-cpus, mounts}`. El wrapper terminó exit 1 en su validación del prefijo de salida y no
  emitió el resumen final; por ello el JIT global queda FAIL, aunque el conjunto aparece en la
  salida sanitizada. El contenedor temporal no quedó presente. No leyó F1 ni ejecutó r9, y no
  acredita runtime ni gate. Se prepara un parser corregido y validación que separa esas dos
  expresiones sin atribuir causa al producto o al daemon.
- **Docker:** `studiamatch-dev` actual ID `115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a`,
  estado `restarting`, contador observado 2397, imagen `studiamatch-dev:local` ID
  `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, checkout montado
  `/home/romel/src/studiamatch`; conserva volumen `studiamatch_node_modules`. Los hashes staged
  de la imagen no coinciden con el checkout original ni con el candidato, y `init-container.sh`
  termina ante esa discrepancia. El usuario ya compartió el mensaje exacto de rechazo; el filtro
  actual de logs no encontró coincidencia en los últimos 1500. Esto demuestra el rechazo de
  manifests observado, no todo el historial de reinicios. El JIT Docker aprobado, SHA
  `0d24ff2fadf0c55ce6d9a1fd5e89e71c2eddba3f15075d2e96406c0d4a367209`, tuvo dos rechazos de
  revisión automática del despacho anterior y un error JS previo a ejecutar. La última llamada
  directa fue interrumpida durante el preflight; el conteo vigente es 54/233/0 frente al pin
  54/232/0. Se trata como invocación consumida y no se reintenta. La salida/exit de esa llamada
  no quedó capturada, pero la inspección posterior confirma el ID/nombre/policy originales y
  ausencia de tag, volumen, red y contenedor candidatos: no hay evidencia de build, cutover,
  cleanup ni cambios Docker. El paquete vigente no puede ejecutarse con ese drift; se prepara
  un despacho estático verificable y una autorización nueva con baseline actualizado.
- El inventario histórico de Node/PG17/PostgREST registra seis contenedores detenidos y tres
  redes internas vacías; sus resultados permanecen en evidencia/manifiestos y no tienen
  volúmenes persistentes. Se suman cinco auxiliares R4 con seis volúmenes recuperables y dos
  redes R4 vacías; el runtime R4 fallido y sus montajes se preservan por diagnóstico healthz no
  resuelto. El JIT agrupado de simplificación
  [rebuild/cutover y cleanup selectivo](operaciones/jit_h3req1_docker_candidate_rebuild_cutover_2026-10-09.md),
  SHA `0d24ff2fadf0c55ce6d9a1fd5e89e71c2eddba3f15075d2e96406c0d4a367209`, propone contexto de
  build allowlisted, tag nuevo `studiamatch-h3req1:20261009-v1`, volumen/red candidatos y cutover
  reversible. Tras health PASS y preflight íntegro, retira 11 IDs y cinco redes exactos; preserva
  imágenes, volúmenes R4/R5, runtime fallido y rollback. El hash del paquete sigue igual, pero la
  invocación única ya no se reutiliza por el intento interrumpido y el WIP drift. El override
  limita `node-deps` a manifests read-only y volumen, sin montar secrets. `studiamatch-dev`
  habitual no será runtime de pruebas aisladas ni reemplaza el runtime C03 fijado.
- **SQL recalculado:** C03 SQL v3 coincide 41/41 y 0 faltan. El PASS PG17 histórico del JIT
  C03 v3 (harness safe-suspend/resume exit 0) sigue aplicando a esos inputs exactos; no acredita
  el C03 integrado ni incluye el harness editorial actual. C02 v4 no-C03 coincide 69/72
  (0 faltantes): deltas en
  `tests/sql/h3_pg17_harness.sql`, `.github/workflows/security-audit.yml` y
  `web/functions/_lib/admin-bff.ts`. Esto corrige el corte anterior incompleto 70/72; se
  preservan resultados para bytes intactos y se renueva solo cobertura afectada. El harness
  editorial añade pruebas de los cuatro ajustes y no se ha ejecutado: G01 se reabre hasta
  validarlo en PG17; el delta BFF corresponde a G08 y el workflow a G10. No se ejecutó SQL en
  este corte.
- **CI independiente:** patch PWI V3 SHA `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`:
  aplicación aislada al base y whitespace check scoped de cuatro rutas PASS. Actionlint/pytest/
 Docker pendientes; no publicado, instalado, configurado ni efectivo. Sin acciones remotas.
- **Aceptación cliente:** matriz vigente de los cuatro ajustes iniciales sigue aplicable; no hay
  defecto funcional demostrado ni revalidación del candidato. Se preservan BFF/HttpOnly, MFA,
  roles, gateway, cuotas y cuenta existente. UAT 144, onboarding separado 10/10, seis pilares,
  rollback y transición siguen sin cierre. [Evidencia del corte](evidencia/h3req1_v15_docker_sql_ci_reconciliation_2026-10-09.md).
- **Gates recalculados:** G01=0/10 (harness C02 editorial modificado pendiente); G02=10/10
  (C03 SQL v3 PASS aplicable a sus 41 inputs actuales); G03–G10=0/10. Total **10%**. Los
  PASS parciales se conservan por separado: V15 sintéticos, C02 69/72, C03 SQL 41/41 y patch
  CI aislado. D01–D14=0/14.
  `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`: NO-GO.
- **Siguiente acción:** corregir y probar localmente el parser V15 y la composición de las dos
  lecturas; preparar el dispatcher Docker como archivo estático y comparar mecánicamente el body
  con los bloques de un JIT actualizado, incluido el rollback. Pedir una autorización nueva solo
  para esos paquetes consumidos o con precondiciones cambiadas. En paralelo, continuar CI local
  permitido. Después de los PASS y autorizaciones vigentes, seguir tooling → copia → health →
  integración Edge/PG17/PostgREST/C03 → aceptación; detenerse ante FAIL. Publicación CI,
  PR/merge/settings y despliegue Development requieren instrucciones separadas.

## Corte anterior — V14 consumido; smoke de template combinado FAIL; F1/r9 detenidos; 20% — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP preservado:
54 tracked modificados (54 unstaged), 227 entradas untracked de `git status --short` y 0 staged. Checkout original
`/home/romel/src/studiamatch`: `feat/h3req1-development-remote-tests`, HEAD
`7650093b05a820e8e6faf9ec711e12fab8b50398`, 39 tracked modificados, 39 untracked y 0 staged.

- **JIT V12 consumido, FAIL antes de contenedores/F1/r9:** aprobación de una invocación del JIT
  `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-V12-TEMPLATE-VARIANT-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`,
  SHA-256 `b06bd50b6bea6c63d0fcec63ffef6fc47527f506e13ca840777bfa652bce16cf`. El resultado fue
  endpoint/V10/V11 previos `OK`, luego
  `f1-template-synthetic-label-map/SYNTHETIC_IMAGE_LABELS_PRESENT`, exit 1. Solo demuestra que
  `Config.Labels` no es vacío; no revela si contiene claves snapshot H3. No se crearon contenedores,
  no se leyó F1 ni se ejecutó r9. Sin retry, pull/build/install, cambios Docker ni acceso a
  `studiamatch-dev`. [Resultado V12](evidencia/h3req1_c03_v12_synthetic_image_label_map_failure_2026-10-09.md).
- **JIT V13 consumido, salida de fases rechazada:** JIT SHA-256
  `5019c8cd6aab75d18d3f4e369744470fee16ad91398855f6d3c18c781250aa25`, aprobado para una
  invocación escalada. Salida: `f1-v11-output/OUTPUT_REJECTED`, exit 1. r9 no se alcanzó. La salida
  no distingue límite de bytes frente a línea no permitida; tampoco permite saber si F1 fue leído
  ni acreditar cleanup. No hay retry. [Resultado V13](evidencia/h3req1_c03_v13_output_rejected_2026-10-09.md).
- **V13/V14 consumidos:** V13 terminó `OUTPUT_REJECTED`, sin determinar si alcanzó F1. V14 fue
  aprobado una vez y revisado sin hallazgos antes de ejecución; su JIT SHA-256 fue
  `60ba16f2b29919ef89869625360416cb87470a7e4ad374f7c1d4b763d9686f48`. Confirmó endpoint, siete
  fixtures, ausencia de residuales V12 y mapa de labels sintético (`OK`). En el primer smoke
  `present`, el template completo devolvió `INSPECT_TEMPLATE_EVALUATION_ERROR`; los 25 campos
  aislados dieron `OK` y el runner clasificó `FIELD_INTERACTION_ERROR`, exit 1. Detuvo el segundo
  smoke, ambas lecturas F1 y r9. El cleanup temporal no reportó error. Evidencia sanitizada SHA-256
  `abf6be735583098f5a196b6d5284438aefcb8329adbd9601a73a6ed728c80940`:
  [resultado V14](evidencia/h3req1_c03_v14_template_field_interaction_failure_2026-10-09.md).
  No se infiere defecto del Docker daemon ni del producto. No hay retry. Siguiente acción: aislar
  la composición del template sintético, corregir únicamente el defecto demostrado y preparar una
  nueva autorización agrupada antes de otra invocación Docker. Ver también
  [prep V13](evidencia/h3req1_c03_v13_label_classifier_preparation_2026-10-09.md),
  [resultado V13](evidencia/h3req1_c03_v13_output_rejected_2026-10-09.md) y
  [prep V14](evidencia/h3req1_c03_v14_output_capture_preparation_2026-10-09.md).

- **JIT V8 consumido:** el usuario aprobó una invocación de
  `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-FIELD-ISOLATION-V8-ONCE-20261009-V1`, SHA-256
  `b63ad5cf046625af7f2fff26e65343b54068e40f1489d8f2df6c2f883bd005a5`. `require_escalated`,
  romel no-root en Ubuntu WSL interactiva, sin sudo. Salida: endpoint atestado previamente `OK`;
  `synthetic-image-read` terminó `SYNTHETIC_IMAGE_UNAVAILABLE`, exit 1.
- **Fallo y clasificación:** no se obtuvo el resultado esperado de `docker image inspect` sobre
  la imagen sintética fijada. El helper mapea cualquier non-zero a un mismo código, así que no
  distingue imagen ausente, acceso denegado, Engine u otro fallo. No inferir una causa Docker.
  V7 había leído `OK` el mismo digest sintético en su corte histórico; no se reutiliza como PASS
  actual ni explica la diferencia.
  Se detuvo antes de sintéticos, container probe y 25 expresiones. F1, r9 y etapas posteriores
  no se alcanzaron. Sin pull/build/install, retry, cambios Docker ni acceso a `studiamatch-dev`.
  [Evidencia V8](evidencia/h3req1_c03_v8_synthetic_image_read_failure_2026-10-09.md).
- **JIT V9 original consumido en despacho incorrecto:** el bloque de Codex pasó el `.sh` a Python,
  exit 1 sin fases; el wrapper no corrió ni inició Docker. La aprobación se consumió y no se
  reutilizó. [Evidencia](evidencia/h3req1_c03_v9_python_dispatch_failure_2026-10-09.md).
- **JIT V9 Bash corregido consumido en diagnóstico real:** SHA-256
  `a1b28cb9b3a2bc40bc9d4150dc2ffd8d90371e78672920ba75028c064abf8c43`. Resultado
  `prior-endpoint-attestation|OK`, `synthetic-image-read|IMAGE_INSPECT_TEMPLATE_ERROR`, exit 1.
  Se detuvo antes de las 14 pruebas y los probes; no creó contenedor ni accedió a F1/r9/
  `studiamatch-dev`. No repetir el template combinado. [Evidencia V9](evidencia/h3req1_c03_v9_image_template_error_2026-10-09.md).
- **JIT V10 consumido, diagnóstico sintético PASS:** el JIT
  [aislamiento de campos de imagen y probes sintéticos](operaciones/jit_h3req1_docker_desktop_wsl_f1_image_template_field_isolation_v10_once_2026-10-09.md),
  SHA-256 `08ced8865cffae2c46319897c98d368f45621dbe6650ff445ab701d55f546d7c`, separa `{{.Id}}`
  y `{{json .Config.Volumes}}`. Una invocación autorizada con `require_escalated`, como romel
  no-root en Ubuntu WSL, exit 0. Resultado: atestación previa endpoint OK; ID aislado OK; bloque
  focal exacto 17/17 OK; Volumes aislado OK; imagen sintética OK; las 25 expresiones allowlisted
  OK y cleanup del contenedor temporal OK. La salida sanitaria completa está en
  [resultado V10](evidencia/h3req1_c03_v10_image_template_field_isolation_result_2026-10-09.md).
  No leyó F1, no ejecutó r9, no accedió a `studiamatch-dev` ni hizo pull/build/install/retry o
  cambios Docker. No repitió V8/V9. La revisión previa confirmó seis pins, orden stop-on-failure,
  `bash -n` y `git diff --check`, sin hallazgos; no ejecutó pruebas Python/pytest en preparación.
  Ver [preparación V10](evidencia/h3req1_c03_v10_image_field_isolation_prep_2026-10-09.md).
- **JIT V11 consumido; smoke combinado FAIL:** el usuario aprobó una invocación agrupada F1/r9,
  SHA-256 `7775d8df1a71fe00f27e78e6a4e73599eab0a62bc064b438932adfb2dcd660b7`. Reusó el PASS V10;
  el smoke emitió `f1-template-synthetic-inspect/INSPECT_TEMPLATE_EVALUATION_ERROR`, exit 1.
  Fail-closed: no leyó F1 ni corrió r9. No hubo retry, pull/build/install, cambios Docker o
  acceso a `studiamatch-dev`. [Resultado V11](evidencia/h3req1_c03_v11_combined_template_failure_2026-10-09.md).
- **Autorizaciones Docker consumidas no se reusan:** las preparaciones previas se conservan en
  [V12 prep](evidencia/h3req1_c03_v12_template_variant_preparation_2026-10-09.md) y
  [V13 prep](evidencia/h3req1_c03_v13_label_classifier_preparation_2026-10-09.md). La etapa
  siguiente invocación requiere aprobación nueva para el comando exacto del JIT. Ante cualquier FAIL/timeout,
  se preserva fase/código sanitizados y se detiene. Solo smoke, F1 y r9 PASS habilitan evaluar copia
  íntegra, Pages/workerd, Edge/PG17/PostgREST y C03 integrado. G03/G04 siguen 0/10; total 20%.
- **Matriz de cuatro ajustes:** permanece en la
  [nota de alcance](evidencia/h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente).
  No se demostró defecto funcional; BFF/HttpOnly, MFA, roles, gateway y cuotas preservados.
- **CI independiente:** patch Protected Workflow Integrity V3 SHA-256
  `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b` sigue aislado; no tests
  Docker, publicación, instalación, required status o enforcement. Revisión read-only del patch
  en copia temporal de la base: impacto HIGH por el límite privilegiado `pull_request_target`,
  probabilidad MODERATE, protección parcial, recuperación fácil; recomendación
  `hold_for_evidence`, sin defecto fuente demostrado. `git apply --check` PASS; pytest,
  actionlint y ejecución GitHub no ejecutados. Antes de requerirlo faltan pruebas locales exactas,
  observar el check real y confirmar merge queue por rama. V3 no se aplicó al checkout compartido;
  el plan de publicación y configuración sigue con autorización separada.
- **G01–G10:** G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. Parciales anteriores
  no se suman. D01–D14=0/14. Sin `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Corte anterior — V7 inspect sintético FAIL; V8 preparado antes de autorización — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`; WIP actual:
54 tracked unstaged, 206 untracked paths y 0 staged. Checkout original `/home/romel/src/studiamatch`:
`feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`,
39 tracked unstaged, 39 untracked y 0 staged. Se preservan ambos checkouts y todo su trabajo.

- **Último JIT consumido:** V7 template smoke clasificado + F1/r9 condicional, SHA-256
  `d83ae63a49ce94be4672822758fb294c5a951af1a060ddfcb63f59d764808f2f`, aprobado para una
  invocación y ejecutado con `require_escalated` como `romel` no-root en Ubuntu WSL interactiva.
  Atestación previa, imagen sintética, volúmenes y cuatro focused tests dieron `OK`; el primer
  `f1-template-synthetic-inspect` devolvió `INSPECT_TEMPLATE_EVALUATION_ERROR`, exit 1. La
  expresión no quedó localizada por la allowlist. El cleanup no emitió fallo. No se alcanzaron
  mapas ausentes, F1 ni r9. Sin retry, pull/build/install, cambio Docker ni acceso a
  `studiamatch-dev`. Evidencia: [resultado V7](evidencia/h3req1_c03_v7_template_smoke_evaluation_failure_2026-10-09.md).
- **Preparación y revisión V6:** el paquete
  [smoke Go-template y clasificación F1](operaciones/jit_h3req1_docker_desktop_wsl_f1_template_smoke_v6_r9_once_2026-10-09.md)
  pasó revisión independiente final sin hallazgos. La salida genérica del smoke muestra que
  falta aplicar el clasificador allowlisted al stderr sintético, no que falte corregir el
  template ni que Docker sea defectuoso. La
  [evidencia de preparación](evidencia/h3req1_c03_v6_template_smoke_f1_reclassification_prep_2026-10-09.md)
  conserva los cambios, pines y revisiones.
- **Revisión independiente del paquete V5 ejecutado:** sin hallazgos; confirmó el SHA, los pins,
  las operaciones Docker, el límite r9 y la salida sanitaria. La frase `exit=<n>` quedó
  precisada: solo se imprime para un fallo de r9; errores anteriores pueden omitirla.
- **Siguiente paso/gate:** no repetir V7 ni ningún JIT consumido. Preparar aislamiento sintético
  por expresión del formato allowlisted con códigos sanitizados, revisión independiente y una
  autorización agrupada nueva antes de otra llamada Docker.
- **Preparación y revisión V7:** el paquete
  [clasificación del template sintético V7 + F1/r9 condicional](operaciones/jit_h3req1_docker_desktop_wsl_f1_template_smoke_classified_v7_r9_once_2026-10-09.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-SMOKE-CLASSIFIED-V7-R9-ONCE-20261009-V1`,
  SHA-256 `d83ae63a49ce94be4672822758fb294c5a951af1a060ddfcb63f59d764808f2f`, pasó revisión
  independiente final sin hallazgos. Una revisión previa detectó un digest de test desalineado;
  se corrigió antes de ejecución, se repineó la cadena completa y se revisó de nuevo. El helper
  comprobó hashes/evidencia, ejecutó cuatro casos focales y llegó al primer smoke temporal, que
  falló con evaluación Go-template genérica y detuvo el segundo smoke y F1/r9. Ver
  [preparación V7](evidencia/h3req1_c03_v7_classified_template_smoke_prep_2026-10-09.md).
- **V8 preparado para localizar la expresión:** el JIT
  [aislamiento de las 25 columnas del template](operaciones/jit_h3req1_docker_desktop_wsl_f1_template_expression_probe_v8_once_2026-10-09.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-FIELD-ISOLATION-V8-ONCE-20261009-V1`, SHA-256
  `b63ad5cf046625af7f2fff26e65343b54068e40f1489d8f2df6c2f883bd005a5`, está preparado para una
  invocación agrupada y pasó revisión independiente final sin hallazgos. Ejecuta cinco sintéticos
  y, si pasan, 25 probes read-only sobre un contenedor temporal con imagen fijada. No repite el
  template completo ni lee F1/r9. Queda pendiente la autorización humana de una invocación. La
  [preparación V8](evidencia/h3req1_c03_v8_template_expression_probe_prep_2026-10-09.md) conserva
  impacto, límites y pins.
- **Matriz de los cuatro ajustes cliente:** incorporada en la
  [nota de alcance vigente](evidencia/h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente).
  Conserva la evidencia inicial como parcial. El contrato Python coincide con el corte 2026-10-04,
  pero el `h3_pg17_harness.sql` actual difiere de su hash histórico; los fuentes del corte 2026-10-01
  no tenían digests por archivo. Se requiere manifest actual y runtime Docker para la cobertura
  afectada. No se encontró defecto funcional demostrado; no se modificó producto.
- **Paquete JIT V5 consumido; no autoriza reintento:**
  [V5 nil-safe + F1/r9 condicional](operaciones/jit_h3req1_docker_desktop_wsl_f1_template_nil_safe_v5_r9_once_2026-10-09.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-TEMPLATE-NIL-SAFE-V5-R9-ONCE-20261009-V1`. La invocación
  está consumida.
- **CI independiente:** patch Protected Workflow Integrity V3 conserva SHA
  `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`, 4 rutas, aplicación
  aislada y `git diff --check` PASS previo. No se ejecutaron pytest/actionlint/Docker ni se
  publicó, instaló o activó. Rulesets/capturas administrativas existentes no se repiten.
- **Parciales separados, no sumables:** atestación endpoint/identidad previa PASS; V4-FIX
  sintéticos 7/7 PASS; V5 sintéticos 11/11 PASS; V6 sintéticos 15/15 PASS; V7 focused 4/4 PASS;
  imagen sintética sin volúmenes PASS; V7 primer template smoke FAIL con
  `INSPECT_TEMPLATE_EVALUATION_ERROR`; segundo smoke, F1 y r9 no alcanzados. Históricos de otro
  corte/candidato: C03 SQL 41/41, C02
  70/72, UAT 144/144, onboarding 10/10 y scanner r7 PASS.
- **Validación:** wrapper V8 `bash -n`, `git diff --check` y búsqueda de whitespace final PASS;
  tests V8 esperan el JIT agrupado. La ejecución autorizada V7 dio focused tests PASS y primer
  smoke FAIL. No se ejecutaron F1, r9, copia, Pages/workerd, integración C03 ni aceptación. El diff-scan formal no
  aceptó scope parcial; no se lanzó scan amplio.
- **CI independiente:** Protected Workflow Integrity sigue aislado; validación Docker,
  publicación, required status y enforcement siguen pendientes. No se activó ni publicó.
- **Aceptación:** se preservan BFF/HttpOnly, MFA, roles, gateway, cuotas y la cuenta existente.
  sessionStorage sigue siendo evidencia histórica; no se afirma XSS ni HIGH actual. Los cuatro
  ajustes no se revalidaron en este corte; su matriz y casos están en
  [la nota de desarrollo existente](evidencia/h3req1_desarrollo_existente_y_cierre_delta_2026-10-08.md#matriz-de-aceptación-sobre-el-candidato-vigente).
- **G01–G10:** G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14.
  Parciales históricos siguen separados; no hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Corte histórico — endpoint acreditado; reporter sintético V4 preparado — supersedido por R181 — 2026-10-09

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`: rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP por
`git status --porcelain --untracked-files=normal`: 54 entradas tracked modificadas, 190
untracked y 0 staged. Checkout original `/home/romel/src/studiamatch`: rama
`feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`,
39 tracked, 39 untracked, 0 staged. Ambos se preservan.

- **Último JIT consumido:**
  `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V3-ESCALATED-AND-R9-ONCE-20261009-V1`,
  SHA-256 `aac075df511b0982b12e5414db75dcfb792c46d022a6bdf8ba0c3b6c8afad994`; ejecución única
  escalada como usuario no-root, sin `sudo`. Socket path/create/connect, lectura HTTP e
  identidad Linux dieron `OK`; la imagen sintética pasó lectura; el caso sintético de `main()`
  terminó `V2_MAIN_EXIT_ASSERT_FAILED`, exit 1. Stop-on-failure detuvo F1 y r9. No hubo retry,
  consulta/rebuild de `studiamatch-dev`, pull, instalación ni cambio Docker.
- **Corrección demostrada del reporter:**
  [evidencia y matriz](evidencia/h3req1_c03_socket_classifier_v3_assertion_reporter_failure_2026-10-09.md).
  V3 buscaba tokens por subcadena en el traceback completo, ambiguo entre aserciones cercanas.
  El harness V4 separa retorno, secuencia sanitaria y ausencia del sentinel; clasifica por
  nombre allowlisted y no inspecciona traceback. Solo cambió tooling/test, no producto.
- **Siguiente ejecución preparada:**
  [JIT V4 sintético + F1/r9 condicional](operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v4_and_r9_once_2026-10-09.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V4-R9-ONCE-20261009-V1`, SHA-256
  `86c7475574fef2d60eb62aef21d75d6a8948f3ee196fc97ae7ed89105bb94884`. Reusa la atestación
  exacta del endpoint, no repite socket/HTTP. Una aprobación nueva cubre solo un run; pruebas
  sintéticas primero, F1 una vez y r9 una vez únicamente tras sus predicados `OK`.
- **Tooling estático:** `bash -n` del runner V4 y `git diff --check` PASS. No se ejecutó código
  Python del proyecto, pytest, actionlint ni Docker en este corte; reviewer independiente del
  delta V4 pendiente.
- **CI independiente:** bootstrap Protected Workflow Integrity V3 sigue aislado, SHA-256
  `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`; aplica en copia limpia
  y `git diff --check` pasó históricamente. `git apply --check` sobre el WIP compartido falla
  por solapamiento con rutas ya existentes; no se aplicó. No hay pytest/actionlint runtime,
  run remoto, check requerido ni enforcement. Reglas/capturas recibidas no se vuelven a pedir.
- **Aceptación:** la matriz de los cuatro ajustes permanece en la evidencia enlazada. No se
  revalidó funcionalidad del WIP actual ni se modificó código de producto. Se preservan
  BFF/HttpOnly, MFA, roles, gateway, cuotas, cuenta existente y evidencia histórica. El informe
  de sessionStorage continúa histórico; no se declara XSS ni HIGH actual.
- **Parciales históricos separados:** C03 SQL 41/41; r4 20/20; scanner r7 PASS; BFF r2 60
  checks/10 cuotas; UAT 144/144 y onboarding 10/10 de candidato anterior; C02 70/72.
- **G01–G10:** G01=10/10, G02=10/10; G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14.
  No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Corte previo — socket connect devolvió EPERM; probe fuera del sandbox preparado — 2026-10-09

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP actual:
54 rutas tracked modificadas, 190 untracked y 0 staged. El checkout original conserva 39
tracked, 39 untracked y 0 staged; no se modificó.

- **Último JIT consumido:**
  `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V2-AND-R9-ONCE-20261009-V1`, SHA-256
  `edecb9534187fc522cd7b97851fe1cfaa6ab0473e7d975585aeff3f12074476a`. Salida: sintéticos
  in-memory `OK`, socket path `OK`, socket-create `OK`, socket-connect `EPERM`, exit 1. El runner
  detuvo HTTP/identidad, sintéticos Docker, F1 y r9; no hubo retry.
- **Predicado y causa:** el `connect()` al socket fijo devolvió `EPERM`. La ruta existe y crear
  un socket pasó. El comando corrió bajo sandbox normal; que el sandbox haya bloqueado el syscall
  es una hipótesis pendiente, no se atribuye aún a Codex ni a Docker Desktop.
- **Próximo JIT:** [reconciliación socket EPERM fuera del sandbox + F1/r9 condicional](operaciones/jit_h3req1_docker_desktop_wsl_f1_socket_classifier_v3_escalated_and_r9_once_2026-10-09.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V3-ESCALATED-AND-R9-ONCE-20261009-V1`,
  SHA-256 `aac075df511b0982b12e5414db75dcfb792c46d022a6bdf8ba0c3b6c8afad994`. Requiere nueva
  aprobación de una invocación `require_escalated`; sigue sin usar sudo. Reutiliza los sintéticos
  in-memory PASS con el mismo SHA, prueba el socket una vez fuera del sandbox y solo si la
  identidad pasa continúa a sintéticos Docker, F1 y r9. Si el auto-review niega la escalación,
  no se ejecuta.
- **CI independiente:** bootstrap Protected Workflow Integrity V3 SHA-256
  `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b` pasó aplicación aislada
  desde HEAD y `git diff --check`; no se aplicó al WIP, instaló ni publicó. Checks/runtime y
  enforcement remoto siguen pendientes.
- **Aceptación y preservación:** la [matriz de los cuatro ajustes](evidencia/h3req1_c03_engine_unavailable_and_socket_classifier_prep_2026-10-09.md)
  sigue vigente, sin nueva revalidación. Se preservan BFF/HttpOnly, MFA, roles, gateway, cuotas,
  cuenta existente, WIP y evidencia histórica; el informe sessionStorage permanece histórico.
- **Parciales anteriores separados:** SQL C03 41/41; pytest focal r4 20/20; scanner r7 PASS;
  UAT BFF r2 60 checks/10 cuotas; UAT anterior 144/144 y onboarding anterior 10/10; C02 70/72.
  No se suman a la aceptación del WIP actual.
- **G01–G10:** G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14.
  No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Corte anterior — wrapper de diagnóstico V1 corregido; JIT V2 pendiente — 2026-10-09

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP actual:
54 rutas tracked modificadas, 188 untracked y 0 staged. El checkout original conserva 39
tracked, 39 untracked y 0 staged; no se modificó.

- **Último JIT consumido:**
  `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V1-AND-R9-ONCE-20261009-V1`, SHA-256
  `da21f8c7853769f7f5cefe5155b45bcb3c192e228244a756d415205f4733cd2e`. Resultado sanitizado:
  `socket-probe-synthetic-tests/OK`, seguido por
  `f1-classification-v2/F1_CLASSIFICATION_FAILED`, exit 1. No hubo retry ni se alcanzó el
  socket real, F1 o r9.
- **Causa corregida:** el wrapper intentó leer `projection.EXPECTED_ENDPOINT`, pero el módulo
  projection allowlisted no tiene ese atributo. La excepción quedó clasificada como genérica.
  El helper V1 consumido se preservó intacto; el helper V2 nuevo toma el endpoint fijo de
  `probe.EXPECTED_ENDPOINT`. Revisión estática, `bash -n` y `git diff --check` pasaron; Python
  y pruebas Docker del cambio siguen pendientes.
- **Próxima invocación concreta:** [JIT socket classifier V2 + F1/r9 condicional](operaciones/jit_h3req1_docker_desktop_wsl_f1_socket_classifier_v2_and_r9_once_2026-10-09.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V2-AND-R9-ONCE-20261009-V1`, SHA-256
  `edecb9534187fc522cd7b97851fe1cfaa6ab0473e7d975585aeff3f12074476a`. Requiere aprobación
  nueva porque la invocación anterior fue consumida. Incluye sintéticos, socket, F1 y r9
  condicionales; cualquier fallo detiene, sin retry ni cambios Docker.
- **CI independiente:** bootstrap Protected Workflow Integrity V3 SHA-256
  `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b` pasó aplicación
  aislada desde HEAD y `git diff --check`; no se aplicó al WIP, publicó ni instaló. Status
  remoto requerido y enforcement siguen pendientes.
- **Aceptación y preservación:** la [matriz de los cuatro ajustes](evidencia/h3req1_c03_engine_unavailable_and_socket_classifier_prep_2026-10-09.md)
  sigue vigente y los asserts actuales no se revalidaron. Se preservan BFF/HttpOnly, MFA, roles,
  gateway, cuotas, la cuenta existente, WIP y evidencia histórica. El informe sessionStorage es
  histórico; no se declara ataque ni HIGH actual.
- **Parciales anteriores separados:** SQL C03 41/41; pytest focal r4 20/20; scanner r7 PASS;
  UAT BFF r2 60 checks/10 casos de cuota; UAT anterior 144/144 y onboarding anterior 10/10;
  C02 70/72. No se suman a la aceptación del WIP actual.
- **G01–G10:** G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14.
  No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Corte anterior — Engine WSL no respondió; socket diagnostic preparado — 2026-10-09

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El HEAD no
representa todo el candidato: al cierre de este corte había 54 rutas tracked con cambios, 186
untracked y cero staged. El checkout original `/home/romel/src/studiamatch` tenía 39 tracked,
39 untracked y cero staged. Ambos se preservaron.

- **Última invocación consumida:** JIT V3 `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V3-ASSERTIONS-AND-R9-ONCE-20261009-V1`, SHA-256
  `1aa957146fbe98b6bec2e04c9d9cbc67414cbb4a9dbe3af138d53b592f8af178`. Salida sanitizada
  `phase=desktop-wsl-engine|error_code=DOCKER_ENGINE_UNAVAILABLE`, exit 1. No hubo retry.
- **Predicado discrepante:** el runner alcanzó `docker version --format '{{.Server.Os}}'` en el
  endpoint fijo; el CLI devolvió status no cero y el clasificador lo resumió. No se preservó
  stderr y no se conoce si fue socket ausente, permiso o conexión/repuesta del Engine. No se
  infiere que Docker Desktop esté mal. F1, sintéticos V3 y r9 no se alcanzaron.
- **Diagnóstico correctivo preparado:** [socket probe V1](operaciones/jit_h3req1_docker_desktop_wsl_f1_socket_classifier_v1_and_r9_once_2026-10-09.md)
  separa ruta, creación, conexión, respuesta HTTP y decodificación; evita repetir el comando
  `docker version`. Incluye F1 y r9 condicionales en una única invocación, pendiente de
  aprobación exacta. No se ejecutó ni tocó Docker.
- **CI independiente:** el patch [Protected Workflow Integrity V3](evidencia/h3req1_ci_bootstrap_minimal.patch),
  SHA-256 `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`, pasó aplicación y
  `git diff --check` en copia temporal limpia de HEAD. Aplicación contra el checkout WIP fue
  rechazada por rutas/hunks solapados; no se alteró el WIP. No hay ejecución Docker, instalación,
  check remoto, required status ni enforcement.
- **Aceptación:** los cuatro cambios y los resultados previos se organizan en la
  [matriz del corte](evidencia/h3req1_c03_engine_unavailable_and_socket_classifier_prep_2026-10-09.md).
  Los casos actuales siguen sin revalidarse; la cuenta Auth, MFA y onboarding no se reinvitan ni
  resetean. Se preserva BFF/HttpOnly, roles, gateway y cuotas. El informe sessionStorage es
  histórico y no se declara HIGH actual.
- **Parciales previos, separados:** SQL C03 41/41; pytest focal r4 20/20; scanner r7 PASS; UAT
  BFF r2 60 checks/10 cuotas; UAT anterior 144/144 y onboarding anterior 10/10; C02 70/72.
  Son candidatos/inputs previos y no se suman como validación actual.
- **G01–G10:** G01=10/10, G02=10/10, G03–G10=0/10; total **20%**. D01–D14=0/14. El detalle
  está en la evidencia enlazada. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Corte anterior — aserción sintética V2 falló; diagnóstico V3 preparado — 2026-10-09

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP amplio
preservado (238 entradas: 54 cambios unstaged y 184 untracked, sin staged; había 236 antes de
preparar el diagnóstico V3. El checkout original conserva 78 entradas).

- **Último JIT consumido:**
  `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-SYNTHETIC-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`,
  SHA-256 `708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`, aprobado y
  ejecutado una vez como `romel` en Ubuntu WSL interactiva, sin sudo. Endpoint y digest de la
  imagen sintética `OK`; el runner reportó
  `phase=classifier-synthetic-tests|error_code=V2_MAIN_SANITIZATION_FAILED`, exit 1.
- **Predicado fallido:** el caso `test_v2_main_emits_only_sanitized_template_error` reportó
  `V2_MAIN_SANITIZATION_FAILED`. La invocación conservó solo ese código genérico: no distingue
  entre exit, secuencia sanitizada, marcador sensible, excepción o problema de clasificación.
  F1 y r9 no se alcanzaron. No se atribuye a Docker, pytest ni al código funcional y no se
  alteran las expectativas a ciegas.
- **Corrección de diagnóstico preparada, no ejecutada:** se etiquetaron esos tres predicados
  con marcadores constantes y el runner nuevo traduce únicamente dichos marcadores a códigos
  cerrados. El paquete
  [JIT diagnóstico V3 + F1/r9 condicional](operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v3_main_assertion_and_r9_once_2026-10-09.md),
  SHA-256 `1aa957146fbe98b6bec2e04c9d9cbc67414cbb4a9dbe3af138d53b592f8af178`, requiere aprobación
  exacta y una sola invocación. Una revisión estática encontró y corrigió en el runner preparado
  una ruta fija al entrypoint V2; la solicitud anterior con SHA `a7fe73ac…` quedó obsoleta antes
  de ejecutarse. No se ejecutaron los nuevos tests localmente.
- **Revisión de seguridad:** la revisión manual fue acotada a estos runners. El conector
  `security_diff_scan` solo admite `scope="."`; su intento de scope local fue rechazado antes
  de crear scanId. Se respetó el pedido de no lanzar un scan completo. No hay reporte
  automatizado de seguridad para el paquete.
- **Reporte de `studiamatch-dev`:** el usuario informó mismatch entre los manifests fuente y
  la imagen staged. `init-container.sh` confirma estáticamente que compara esos hashes con el
  marcador de la imagen y falla con ese mensaje; no se leyó el marcador ni se consultó Docker.
  No se inició/reconstruyó el contenedor; es un asunto separado del pin y el JIT lo excluía.
- **Evidencia:** [falla de aserción V2 y paquete diagnóstico V3](evidencia/h3req1_c03_classifier_v2_assertion_failure_2026-10-09.md),
  [falla sintética genérica anterior](evidencia/h3req1_c03_classifier_v2_synthetic_runtime_failure_2026-10-09.md),
  [pin discordante](evidencia/h3req1_c03_f1_classifier_v2_pin_mismatch_2026-10-09.md) y
  [primer synthetic FAIL](evidencia/h3req1_c03_f1_classifier_v2_synthetic_failure_2026-10-09.md).
- **Gates:** G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta cero; D01–D14=0/14.
  La lectura F1 previa conserva `INSPECT_TEMPLATE_ERROR`; las invocaciones posteriores no
  alcanzaron F1. Los parciales previos permanecen separados. No hay `GO_LOCAL_PR` ni
  `GO_DEVELOPMENT_REAL`.

## Corte anterior — F1 inspección detenida por error de template — 2026-10-08

Candidato confirmado: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El checkout
conserva WIP amplio; HEAD no lo representa por completo. El checkout original
`/home/romel/src/studiamatch` se preservó sin cambios.

- **Docker/F1 — intento previo:** antes de aprobar el JIT de clasificación, el usuario había
  reportado `phase=f1-container-read|error_code=DOCKER_READ_FAILED` desde el bloque
  output-capture. Ese evento histórico no queda autorizado ni cierra el gate; su JIT de SHA
  `bbaa2242bf026f252864b4e476a60e9de2a8e327c0456d2b343b612402c61c92` no se repite.
  El resultado actual es el de la invocación aprobada descrita a continuación.
- El [JIT F1](operaciones/jit_h3req1_docker_desktop_wsl_f1_error_classification_once_2026-10-08.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-READ-ERROR-CLASSIFICATION-ONCE-20261008-V1`, SHA-256
  `ce424f43901752cab76d9bcad88ceca05eb94a65790e4750a3b5f71f4b417395`, fue aprobado y consumido
  por `romel` una vez en Ubuntu WSL, sin sudo. Salida: endpoint `OK`, imagen F1 `OK`, lectura
  F1 `INSPECT_TEMPLATE_ERROR`. El runner diagnóstico termina exit 1 por esa rama; el código de
  salida numérico del CLI no se expuso. El predicado discrepante es el `docker inspect` del ID
  F1 fijado con el formato allowlisted; el clasificador reconoció un marcador de error de
  template. No se conoce si falló el parseo o la evaluación de un campo ni qué token/atributo
  lo produjo. No se repite este JIT ni se cambia Docker.
  Sin los tres resultados `OK`, r9 y runtime local no están habilitados por el JIT.
- **Aceptación:** se añadieron aserciones de procedencia y auditoría por actor/fecha/antes/después,
  también al limpiar un override, y disponibilidad a `tests/sql/h3_pg17_harness.sql`; se amplió
  `tests/h3_local_uat.mjs` dentro de los mismos
  48 casos × 3 viewports (144 ejecuciones, cero retries): email sintético Admin/User y saves
  simultáneos con versión común. Sintéticos y suites no se ejecutaron al faltar el gate de
  Docker. La matriz y ficha están en
  [corte de aceptación y F1](evidencia/h3req1_corte_matriz_aceptacion_f1_2026-10-08.md).
  No se demostró defecto funcional; los cambios fueron de cobertura y herramienta.
- **CI:** el patch bootstrap V3 continúa preparado, sin aplicar ni publicar; SHA
  `4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b`. No hay run real del
  check, status requerido, autorización de PR/merge/settings ni confirmación de aislamiento
  Pages. Production `main`, auto-deploy y watch `*` permanecen como riesgo de promoción.
  Cloudflare documenta el prefijo `[CF-Pages-Skip]` para omitir un deployment, pero falta
  comprobarlo en este PR y con el squash; un check de Pages ausente no es PASS
  ([integración GitHub](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/)).
  Capturas Branches previas se conservan y no se vuelven a pedir.
- **Parciales:** C03 SQL v3 41/41 inputs; pytest focal r4 20/20 y scanner r7 PASS; UAT BFF r2
  60 checks/10 casos de cuota; UAT histórico anterior 144/144 y onboarding 10/10 separado.
  Son resultados de sus candidatos, no de este WIP. C02 sigue 70/72 por BFF/workflow; revalidar
  esos deltas, no repetir SQL/wire con inputs intactos.
- **Gates:** G01=10/10, G02=10/10, G03–G10=0/10; total **20%**, delta 0. D01–D14=0/14.
  No hay `GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` ni permiso para integrar, desplegar, publicar,
  cambiar reglas o activar producto. BFF/HttpOnly, roles, MFA, gateway y cuotas se preservan.
  El informe de sessionStorage es histórico: este corte no afirma ataque ni HIGH actual.

Stop actual: no existe una corrección del formato demostrada por el código sanitizado
`INSPECT_TEMPLATE_ERROR`; el texto crudo fue descartado por diseño. Se preparó una revisión
diagnóstica V2 que separa parseo, evaluación y marcador ambiguo sin exponer stderr; amplía los
casos sintéticos del runner existente en
`tests/h3req1_docker_peer_substep_diag/test_f1_read_failure_classification_once.py`. Helper
V2 SHA-256 `3b5f7c6dd00ba6b690fcaadbc0c018f7d2e0dc11079ac0991cd0ffd06926f706`, runner combinado
SHA-256 `385f94732d8f93420533284cd1f4ceee36d82b742ba7ab519c3af0749c6c88df`; ni helper ni
pruebas se ejecutaron. El [JIT V2](operaciones/jit_h3req1_docker_desktop_wsl_f1_classifier_v2_and_r9_once_2026-10-08.md),
ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-AND-R9-ONCE-20261008-V1`, SHA-256
`c2f9414cea67402af76727b3c240982d1c264252569ab94aea9dedc47c687a66`, está preparado y espera
aprobación. El runner realiza prueba sintética primero; solo si pasa lee F1 una vez y, solo con
las cuatro fases `OK` y controles F1 conformes, ejecuta r9. No volver a leer F1 ni invocar
Docker con un template alternativo por conjetura. Solo una causa concreta habilita una
corrección del formato y su fixture tipado de 25 campos/orden.
Ninguna prueba sintética acredita el objeto real de F1 ni autoriza otra lectura. Una
invocación nueva requiere su propio JIT. El trabajo independiente de aceptación y CI sigue
preparado en la evidencia enlazada. No repetir F2d, scans completos ni planes generales.

## Corte previo — invocación WSL consumida, salida pendiente antes del reporte — 2026-10-08

Se prepararon el diagnóstico alternativo de Docker Desktop WSL y el bootstrap CI. El usuario
aprobó una invocación del diagnóstico alternativo y aceptó su residual MEDIUM; informó que lo
ejecutó, pero la terminal se cerró antes de que enviara las líneas sanitizadas. La invocación
se considera consumida; no hay resultado utilizable ni aumento de porcentaje.

- **Docker:** F2d y el diagnóstico de fase terminaron
  `phase=peer-identity|error_code=EACCES` y están consumidos. El JIT peer-substep
  [H3REQ1-C03-PEER-SUBSTEP-DIAGNOSTIC-F1-READ-ONCE-20261008-V1](operaciones/jit_h3req1_peer_substep_diag_once_2026-10-08.md),
  SHA-256 e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173, separa
  socket, SO_PEERCRED, cada lectura de /proc y revalidación. Exige una única ejecución
  desde el Linux que ve el proceso y `/proc` del daemon; incluye lectura F1 allowlisted solo
  tras identidad PASS. El usuario confirmó Docker Desktop de Windows con WSL integration.
  Docker documenta que el Engine corre en su distro interna `docker-desktop`, aislada de Ubuntu;
  `sudo` en Ubuntu no da acceso root a ese `/proc`. No ejecutar ese JIT en Ubuntu, en
  `studiamatch-dev`, otro contenedor ni entrando a la distro interna. El usuario ejecutó una
  vez su runner fijado desde Ubuntu WSL como root; devolvió
  `phase=peer-identity|error_code=IDENTITY_MISMATCH`, y `uname` confirmó WSL2. La invocación
  queda consumida, no se reintenta. El predicado de identidad no pasó; por el orden del runner
  las lecturas allowlisted de metadata y la revalidación del socket precedieron a la
  discrepancia, pero el código no dice cuál condición concreta difirió. F1 no se consultó y
  no hubo lectura de metadata de contenedor por Docker API. Esto no demuestra que Docker esté
  mal. Se preparó la
  [alternativa Docker Desktop WSL](operaciones/jit_h3req1_docker_desktop_wsl_attestation_once_2026-10-08.md),
  SHA-256 `9327c0ea163e47aa35c798442fec4230341b97fda1c19dfa811c492e3416fe4d`, que verifica el
  socket integrado y respuesta Linux y lee F1 solo después; no prueba
  PID/UID/ejecutable/namespace del daemon y conserva el residual MEDIUM que el usuario
  aceptó para una invocación. El usuario informó que ejecutó su bloque y la ventana se cerró;
  no proporcionó ninguna línea `phase=…|error_code=…`. Runner/helper emiten el resultado solo
  por stdout y no escriben un registro local. La invocación se considera consumida; no se
  reintenta. Sin esas líneas no se puede evaluar endpoint/Linux ni F1 y r9 no está habilitado.
  La aprobación no incluye rebuild/pull ni limpieza de imágenes o contenedores; el paquete usa
  digests fijados y copia aislada del candidato.
  El usuario expresó preferencia por reconstruir imágenes para un entorno limpio; hacerlo
  cambiaría los pins y no es necesario para validar el WIP, que se monta/copia sobre runtimes
  fijados. No se reconstruye ni retira ningún recurso preexistente bajo la aprobación actual.
  El usuario confirmó que no puede recuperar el scrollback. Se preparó una nueva solicitud
  agrupada de una repetición read-only con captura validada en la shell y pausa visible:
  [JIT output-capture](operaciones/jit_h3req1_docker_desktop_wsl_output_capture_once_2026-10-08.md),
  ID `H3REQ1-C03-DOCKER-DESKTOP-WSL-OUTPUT-CAPTURE-ONCE-20261008-V1`, SHA-256
  `bbaa2242bf026f252864b4e476a60e9de2a8e327c0456d2b343b612402c61c92`. Requiere aprobación
  nueva; no se ejecutó. Esta solicitud repite como máximo las lecturas allowlisted del endpoint,
  imagen y F1, no escribe salida local, y si sus tres fases pasan enlaza r9 con la autorización
  consolidada ya vigente. Hasta entonces G04=0/10, G03=0/10 y total 20%; no hay GO.
- **CI:** el patch bootstrap [V3](evidencia/h3req1_ci_bootstrap_minimal.patch) está aislado
  de cuatro rutas y parte de 4eb4d877a50b012bb630a129bd0c74482c33be9. SHA-256
  4f5c7a946886d1df9cb866bdc057276db9eb5aa47e997be403b092ba6f704d1b.
  git apply --check y git diff --check pasaron en snapshot aislado, según su evidencia;
  pytest, actionlint, Docker y workflow remoto no se ejecutaron. Revisión independiente:
  hold_for_evidence, sin bypass de código confirmado. La policy GitHub predeterminada para
  pull_request_target en repo público está en evaluate hoy; no requiere policy manual para
  correr ahora, pero enforcement se anuncia para 2026-11-02. Faltan emisión/asociación real
  del check al SHA vigente, comportamiento al avanzar la base con head estable y confirmar
  si hay merge queue. El repo permite squash; se preparó como vía candidata el prefijo
  `[CF-Pages-Skip]` en el título del commit para omitir deployment, pendiente de comprobar el
  efecto real en el commit de rama y su squash. El modo Preview branch control sigue desconocido.
  No se modificaron reglas, no se publicó ni aplicó el patch al checkout compartido, que
  conserva el WIP preexistente.
- **Configuración administrativa recibida:** GitHub MCP reporta el owner como `type=User`; el
  repo está bajo la cuenta personal `romelhc95`, no una organización/Enterprise. El usuario
  confirmó que Settings → Actions → Policies no tiene policies; Policy insights indica que la
  supervisión de reglas requiere Enterprise, y el usuario confirmó que no es una cuenta
  Enterprise. No existe scope de organización porque el owner es una cuenta User. Para el repo
  público, la policy predeterminada de `pull_request_target` está en evaluate hoy y GitHub
  anuncia enforcement el 2026-11-02; no se repiten consultas/capturas.
  Cloudflare Pages tiene Production branch `main`, automatic deployments enabled, root `web`,
  `npm install && npm run build`, output `out`, Build watch include `*` y exclude vacío,
  build comments enabled, cache disabled, build system v3 y sin deploy hooks. `*` coincide con
  cualquier archivo y un match dispara build; el patch entra en el flujo Production. El usuario
  compartió Deployments con un Preview histórico de
  `feat/h3req1-development-remote-tests`; esto prueba que existió un Preview para esa rama, no
  el modo exacto (None/All/Custom) ni el efecto sobre el bootstrap. No se comprobó el build
  del bootstrap. El usuario indica que existe un MCP cf-builds, pero no está expuesto en las
  herramientas de esta sesión.
- **GitHub ya confirmado por las capturas:** las tres reglas requieren PR, una aprobación,
  descartan approvals obsoletas, exigen rama actualizada y requieren solo security-audit.
  No se repiden esas capturas. El ruleset activo conserva su bypass redactado. El workflow
  independiente aún no está instalado ni requerido.
- **Pruebas parciales aprobadas, separadas:** G02 conserva SQL C03 v3 PASS e inputs 41/41;
  G03 conserva pytest r4 20/20, proyector/scope PASS y regresión del scanner r7 PASS; G08
  conserva UAT BFF r2 PASS con 60 checks y 10 casos de cuota. r8 acabó exit 126 antes de
  ejecutar checks. Ninguno de estos resultados cierra por sí solo el gate indicado. Las
  144 ejecuciones visuales, onboarding 10/10 y revisión de aceptación final siguen pendientes.
- **Gates:** G01=10/10, G02=10/10 y G03–G10=0/10. Total 20%, delta 0; D01–D14 0/14.
  No hay GO. Código preparado, revisión, hashes y documentos no suman puntos.

El JIT peer-substep está consumido por `IDENTITY_MISMATCH` desde Ubuntu WSL y no se repite.
La invocación del JIT alternativo V1 también se informó ejecutada y queda consumida, pero su
salida no está disponible. No inferir PASS/FAIL ni continuar r9 con esa invocación. No relanzar
el bloque V1; la solicitud V2 de captura permanece pendiente de aprobación. Su autorización no
incluye rebuild/pull ni limpieza de
recursos. Los runtimes del ciclo usan digests fijados y reciben una copia aislada del candidato;
no se requiere reconstruirlos para incluir los cambios fuente. Si se solicita cambiar esos
pins, preparar otra autorización agrupada. El bootstrap CI permanece
como patch revisable; Policy Insights no es accesible en cuenta personal y no bloquea el run en
evaluate actual. El Preview histórico está acreditado, pero branch control y merge queue por rama
siguen desconocidos. No cambiar ni reinstalar Docker sin causa demostrada.

Si la alternativa aprobada devuelve endpoint/Linux PASS más F1 PASS, r9 sigue condicionado a ese
resultado. La solicitud deja explícita la reconciliación del
manifiesto “NO AUTORIZADO” con la excepción iterativa ya aprobada, agrupando la decisión en un
objetivo. No se ejecuta r9 antes de la evidencia ni se aumenta el 20% por esta preparación.

## Estrategia de cierre tras revisión — 2026-10-08

El [tablero y estrategia vigentes](operaciones/h3req1_avance_por_gates_y_prompt_luna_2026-10-08.md)
se actualizaron para dos frentes: diagnóstico de subpasos peer-identity con permiso real
de lectura, y preparación bootstrap CI de controles desde base confiable. No repetir
capturas ya aportadas, métodos consumidos ni scans completos sin delta. Validaciones A/B
no consumidas mantienen su alcance condicionado; diagnóstico nuevo y writes CI requieren
decisión concreta. Actualización solo documental; total sigue 20%, sin runtime nuevo.

## Corte histórico — continuación desde sesión 01a11de1

El F2d anterior continúa consumido. El diagnóstico nuevo, aprobado para una sola invocación
elevada, devolvió `phase=peer-identity|error_code=EACCES` (exit 1). El flujo llegó a la
validación del peer; por ello creación/configuración del socket, conexión, lectura
`SO_PEERCRED` y decodificación no fueron las fases que fallaron. El código permite que EACCES
en `peer-identity` venga de lectura de metadata del proceso o de la revalidación del socket;
no discrimina cuál. No se repitió, no se cambió Docker y no se acreditó identidad. Ver
[solicitud JIT y hashes](operaciones/jit_h3req1_peer_phase_diagnostic_once_2026-10-08.md) y
[evidencia](evidencia/h3req1_diagnostic_ci_prep_2026-10-08.md).

Revisión estática @security-auditor: la ruta de importación sintética detectada inicialmente se
corrigió; el segundo pase no encontró findings en los dos archivos nuevos. Las pruebas no se
ejecutaron ni se declara runtime PASS. La herramienta Codex Security diff-scan no aceptó el scope
de subdirectorio y exigía revisar la raíz completa; no se inició para preservar WIP y no repetir
un scan completo.

GitHub: las capturas del usuario muestran reglas clásicas para `desarrollo`, `certificacion`
y `main`: PR requerido, 1 aprobación, dismiss de reviews stale, branch up-to-date y solo el
check `security-audit`; no permiten bypass de la regla clásica, force-push ni deletion. La
aprobación del último push está activa en las dos primeras, pero no en `main`. El ruleset
`owner-only-protected-branch-updates` (21255108) está Active sobre las tres; solo restringe
updates y muestra un actor User con `Always allow`, cuya identidad se conserva redactada. No
se infiere cómo interactúa ese bypass con las reglas clásicas.

La lectura GitHub MCP confirmó que las tres ramas ejecutan el workflow remoto
`.github/workflows/security-audit.yml` en `pull_request`, que su agregado no depende de
`Protected Workflow Integrity`, y que ninguna contiene el workflow independiente
`.github/workflows/protected-workflow-integrity.yml`. El candidato diferido de CI queda
confirmado como brecha de control MEDIUM: un PR aprobado puede cambiar el workflow que emite
el único status requerido. No se probó un bypass directo ni se modificaron ramas/configuración.
La validación complementaria está en el artefacto Codex Security
`candidate-500f085f897ba6f7`; ver [evidencia y remediación agrupada](evidencia/h3req1_diagnostic_ci_prep_2026-10-08.md).

G01–G02 siguen en 10/10; G03–G10 siguen en 0/10. Total **20%**, sin incremento por código
preparado, hashes o revisión documental. Las pruebas parciales previas se mantienen separadas
por alcance en el tablero; GO sigue sin acreditarse.

## Revisión histórica de la detención 01a11de1 — 2026-10-08

[Análisis de la llamada y helper](evidencia/h3req1_revision_sesion_01a11de1_bloqueos_2026-10-08.md):
F2d se invocó sin `require_escalated` explícito, y el helper descarta fase/errno al capturar
errores de socket/connect/credenciales. No se ha demostrado que el sandbox causara el fallo
ni que el motor sea inválido. Siguiente diagnóstico debe distinguir esos errores y usar
acceso del entorno expresamente aprobado antes de decidir cambiar motor. F2d anterior
permanece consumido; ninguna ejecución nueva autorizada por esa nota. El estado de CI era
desconocido por 403 y quedó actualizado en el encabezado vigente con las capturas posteriores.

## Resultado del paquete local iterativo aprobado — 2026-10-08

Se aprobó y ejecutó una vez `H3REQ1-CLOSE-LOCAL-ITERATIVE-20261008-V1`, SHA-256
`4b2649342395f8bb14fb43958d660d3588f1f6ca55bce4a6516858b395cfb4f8`, incluidas A/B/C,
la excepción iterativa y los dos residuales MEDIUM de A. F2d terminó **NO-GO** porque no
se pudo acreditar la identidad del peer (`api-requests=0`). Ese método queda consumido:
no se leyó F1, no se ejecutó r9 ni otra fase Docker. El bloque GitHub fue read-only; required
checks/reviews no se pudieron verificar porque la API de branch protection devolvió 403.

La revisión estática de seguridad terminó con 51/51 filas, cero hallazgos reportables
confirmados y dos candidatos condicionales diferidos. No hubo pruebas de aplicación/SQL ni
runtime. Se preservó el WIP y no se modificó código de producto. El estado sigue **20%**
(G01–G02 completos; G03–G10 abiertos), D01–D14 0/14 y `GO_LOCAL_PR` **NO-GO**. La ficha,
resultados y dependencias concretas están en
[evidencia del ciclo](evidencia/h3req1_cierre_local_iterativo_2026-10-08.md).

## Preparación de paquete consolidado para nueva sesión — 2026-10-08

Se preparó [propuesta local iterativa y lectura CI](operaciones/h3req1_paquete_consolidado_cierre_local_luna_2026-10-08.md)
para Luna 6 Max, con límites, recursos, preflight de permisos, excepción de revisión de
hashes y prompt único. No es autorización, no consumió JIT ni ejecutó runtime/remotos.
La aprobación consolidada propuesta cubre ciclo local y lecturas GitHub; cualquier
bootstrap protegido faltante aún debe concretarse contra reglas reales antes de writes.
Review humano final y CI efectivo siguen siendo prerrequisitos de GO_LOCAL_PR. Se conserva
el snapshot factual y 20%; no se acredita cierre por preparar este paquete.

## Revisión estática y ejecución G03 r8 — 2026-10-08

El scan de Codex Security `[UUID redactado]` terminó con inventario
51/51, cero hallazgos reportables confirmados y cobertura parcial. Dejó un candidato medio
condicional sobre el required check de Protected Workflow Integrity, pendiente de lectura
autorizada de las reglas GitHub; la observación CORS se suprimió porque no se encontró un
flujo de navegador que exponga el JWT requerido. El informe es estático, corresponde al
snapshot `codex-security-snapshot/v1:sha256:2f6b7c1204f9a7e3beb22543f02263a994ce304017705fb350526335179ace58`
y advierte que el árbol cambió durante su revisión documental. No acredita GO ni estado
remoto.

La ejecución r8 fue autorizada explícitamente y consumió una sola invocación de
`/tmp/h3req1-g03-validation-29d8fff9-r1/run-r8.sh` (límite 180 s, sin retry). El manifiesto
`inputs.sha256` coincidió en sus 71 entradas y su SHA-256 fue
`6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee`. Las descargas fijadas
pasaron sus hashes: actionlint 1.7.7 `023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757`
y ShellCheck 0.11.0 `b7af85e41cc99489dcc21d66c6d5f3685138f06d34651e6d34b42ec6d54fe6f6`.
El contenedor fijado arrancó, pero la etapa interior terminó antes de ejecutar los checks:
exit 126, `bash: run-in-container.sh: Permission denied`. Causa demostrada por metadata:
la raíz del bind mount era modo 0700, UID/GID 1000; el proceso interior era 1001:1001 y no
podía atravesar/leer el paquete. El archivo interior era 0755. No se ejecutaron actionlint,
ShellCheck, ESLint, TypeScript, pytest ni regresiones scanner/scope. `--rm` retiró solo el
contenedor de esta invocación; no se limpió ni inspeccionó ningún recurso existente.

Se preparó la revisión r9 en `/tmp/h3req1-g03-validation-29d8fff9-r2`, preservando los 71
inputs y dejando su raíz 0755; el manifiesto de paquete SHA-256 es
`b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`, el wrapper
`run-r9.sh` `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`. Los mismos
dos archivos de herramientas ya autorizados se copiaron y sus hashes se revalidaron; r9
no descarga nada. El paquete y wrapper pasan validación de hashes/sintaxis, pero r9 no se
ejecutó y requiere permiso nuevo. Además, la condición `unix://` del runner no demuestra
la identidad del peer dockerd; F2c quedó NO-GO y esa dependencia debe resolverse antes de
otra ejecución Docker, por F2d aprobado o alternativa local autorizada. No se reutilizan
aprobaciones de r4–r8. El JIT r9 propuesto tiene SHA-256
`49502617f2bb788b2e9664e659c3f9dd4fe3dc84188ee0b5d86e2909c3dadedf`.

G03 sigue abierto: **20% -> 20%**, sin gate cerrado. G01–G02 continúan en 20%; G03–G10
valen 0. Permisos r4–r7, BFF r2 y r8 están consumidos. Development remoto permanece 0/14.
No se ejecutó F2d/F1, SQL ni operación remota. Ver
[ciclo r7/r8 y corrección r9 preparada](evidencia/h3req1_helper_docker_fixture_2026-10-08.md)
y [JIT r9 propuesto](operaciones/manifiesto_jit_h3_g03_local_validation_r9_2026-10-08.md).

## Ejecuciones r4/r5/r6/r7 y siguiente gate — 2026-10-08

La aprobación r7 exacta se verificó contra el paquete congelado y se consumió en una única
ejecución Docker aislada. `inputs.sha256` coincidió con
`c374f2d25a6faea9343b560bc27d400cd9ef82d2bc90e202327b54ccba1df95b`; manifiesto 3/3 y
regresión scanner PASS, exit 0, sin retry. El falso `grep` corrió en el tmpfs acotado
`/exec-fixture`, separado del scratch `/tmp noexec`. r4/r5/r6 permanecen como evidencia
histórica; sus permisos siguen consumidos. G03 aún vale 0 porque faltan linters/revisión.
G01–G02 se mantienen en 20%; G03–G10 abiertos. Development remoto 0/14. No se ejecutó
F2d/F1, SQL ni operación remota. Ver
[resultados r4–r7](evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

## Renovación de F2d y revisión de pins — 2026-10-08

El manifiesto F2d se renovó tras r4: ahora verifica 17/17, con SHA-256
`18101dd492dd894d5c5692c204f1a47d3727fb609f75b83ffdbc854bcf0f657a`. El helper
`SO_PEERCRED` y sus fixtures sintéticos pasaron dentro de Docker como parte de pytest
20/20 de r4; esto no identifica el daemon real ni autoriza consultar F1. La revisión
estática r2 quedó en
[evidencia](evidencia/h3req1_c03_f2d_diagnostic_static_review_r2_2026-10-08.md), con límites
de alcance y reconciliación explícita con AGENTS. El JIT r2 requiere aprobación fresca,
aprobación expresa para ejecutar el auxiliar Python en el host Linux y aceptación de dos
riesgos MEDIUM; no se ejecutó F2d. El JIT actual tiene SHA-256
`deb429e38070174b7f179ed2c178bf4c5598ef04c0de4b92ba2f87d624b54078`. El scanner r7 está
consumido con PASS; G03 requiere lint/review separados. G01–G02 permanecen en 20%; G03–G10 abiertos;
Development remoto 0/14.

## Continuación de validación BFF y acceso Docker — 2026-10-08

El paquete BFF r1 fue aprobado, pero el intento terminó con `permission denied` al acceder
a `unix:///var/run/docker.sock`, antes de imprimir Node o ejecutar la UAT. Su permiso quedó
consumido y no se reintentó. El reemplazo r2 se autorizó aparte y pasó una única ejecución:
manifiesto SHA-256 `c2c62c156d4fec0dcdecaee6db4af9077b680ca9bc1aee74a4abde61d8f49f58`, Node
`v20.20.2`, TypeScript `5.9.3`, sintaxis válida y UAT `PASS` (60 verificaciones, 10 casos
de cuota), exit 0. Esta evidencia parcial de BFF no cierra G08. r4 se ejecutó después y
terminó NO-GO por la regresión scanner. r5 también quedó consumido al revelar que el fixture
no ejecutaba su `grep` falso; en ese corte, r6 esperaba aprobación. El resultado posterior
r6 y paquete r7 se registran al inicio del estado. G01–G02
continúan en 20%; G03–G10 siguen abiertos y Development remoto en 0/14. Ver
[evidencia del intento y reemplazo](evidencia/h3req1_bff_validation_access_2026-10-08.md).

## Seguimiento de cierre acreditado — análisis de sesión 01a11c04 — 2026-10-08

[Tablero fijo G01–G10 y prompt actualizado](operaciones/h3req1_avance_por_gates_y_prompt_luna_2026-10-08.md):
comparación retrospectiva con la misma regla, 20% -> 20%, delta 0 puntos porcentuales.
Mide gates completos, no implementación ni esfuerzo. Hay nueva evidencia/correcciones
de ingeniería, pero ningún gate completo adicional en ese corte. r4 coincidía 13/13 antes
de ejecutarse; su resultado posterior fue NO-GO por una regresión del scanner. Se detectó
En ese corte, F2d inputs coincidían 16/17 por cambio del helper; la renovación posterior
17/17 y revisión/JIT r2 se describen en la sección vigente al inicio de este estado.
C03 SQL se revalidó 41/41 sin SQL.
Esta actualización es documental, sin Docker/remotos ni permiso consumido. Los
resultados funcionales y restricciones de las secciones siguientes se conservan.

## Continuación H3REQ1 — control HMAC y revisión del snapshot actual — 2026-10-08

Se agregó en `web/functions/_lib/admin-bff.ts` una barrera fail-closed: cuando la clave
HMAC de cuota y la del gateway RPC son iguales, las rutas Admin devuelven 503 genérico
antes de admitir cuota o llamar RPC. El logout local sigue limpiando cookies. La UAT
sintética del BFF pasó en el paquete r2 (60 verificaciones, 10 casos de cuota); no acredita
bindings remotos ni cierra G08. La ficha de componente/consumidores/contrato/impacto está en la
[evidencia del ciclo](evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

La revisión formal del snapshot actual quedó completada como Codex Security scan
`[UUID redactado]`, snapshot
`codex-security-snapshot/v1:sha256:e20b46145f4fed6119fe2475ec0c6571bf4206d835c6c467ea2766716298c0cb`, baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`: 51/51 rutas revisadas, cero hallazgos
reportables confirmados, cuatro candidatos diferidos y cobertura parcial. Es revisión
estática; no acredita runtime ni la ausencia global de riesgos. Sigue sin comprobarse la
configuración Auth, los rulesets/required checks y costos de GitHub, el host efectivo del
mock ni los bindings/valores HMAC desplegados.

El paquete r4 conservó 13/13 hashes y luego se ejecutó una vez bajo autorización; pasó
pytest 20/20, proyector y scope guard, pero falló la regresión scanner y terminó NO-GO.
Esa autorización está consumida. En ese corte, el paquete r6 preparado requería autorización;
su ejecución posterior y el r7 pendiente están registrados en la sección vigente inicial. No
se ejecutó F2d sobre F1, runtime integrado, SQL/DB, GitHub, Supabase ni Cloudflare. Se
mantienen **NO-GO** F2d/F1, snapshot integrado, C03 integrado, `GO_LOCAL_PR` y
`GO_DEVELOPMENT_REAL`.

Revalidación de inputs: C02 v4 no-C03 **70/72**, ahora con dos deltas identificados:
`.github/workflows/security-audit.yml` y el BFF modificado para rechazar claves HMAC
iguales. C03 SQL v3 conserva **41/41**. Los resultados SQL/wire no se repiten; antes de
cierre se debe revalidar la cobertura BFF afectada y los controles de workflow. Detalle y
hashes en [revalidación vigente](evidencia/h3req1_revalidacion_hashes_2026-10-08.md).
El paquete r4 cubre helpers, scanner, scope guard y parser de workflow; no incluye la UAT
del BFF. Por eso, aun si r4 pasa, esa regresión requerirá otra ejecución Docker acotada y
aprobación propia antes de cerrar el cambio HMAC.

## Ciclo de validación de cierre — actualización 2026-10-08

La revisión formal del diff quedó sellada como Codex Security scan
`[UUID redactado]`, snapshot
`codex-security-snapshot/v1:sha256:5429d4eeecd0cc1a5cb33f29abbfd7772b33eb07d3b249a5014bdf05b713c6e0`,
baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`: inventario 51/51, cero hallazgos
reportables confirmados, cuatro candidatos diferidos y cobertura parcial. El cierre
advierte que el árbol cambió durante el scan; sus conclusiones aplican a ese snapshot
y no acreditan que el candidato actual esté libre de HIGH/CRITICAL. Ver
[evidencia del ciclo](evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

El paquete r4 de validación aislada tuvo sus 13 hashes confirmados; la aprobación exacta
se consumió en una ejecución y el resultado global fue NO-GO por la regresión scanner.
En ese corte, r6 validaba la corrección del fixture y esperaba aprobación; luego falló por
el montaje `noexec` y se preparó r7. No reutilizar
ninguna autorización consumida.
Se mantienen NO-GO F2d/F1, snapshot, smoke Pages/workerd, C03 integrado, CI efectivo,
UAT final, `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`; no hay operación DB ni remota autorizada.

## Actualización documental de continuación — 2026-10-08

Se analizó la sesión `[UUID redactado]` y se documentaron
[hallazgos y decisiones por objetivo](evidencia/h3req1_analisis_sesion_01a11a7e_2026-10-08.md).
El [prompt único Luna 6 Max](operaciones/h3req1_prompt_luna_6_max_cierre_local_2026-10-08.md)
exige ciclos hasta GO acreditado y preguntas ante decisiones/permisos faltantes, sin
convertir el objetivo en PASS anticipado. Antes de ejecutar F2d debe resolverse su
dependencia de validación helper/parser en Docker y el contexto host de su auxiliar;
después corresponde aprobación fresca del diagnóstico revisado. Sidecar 1/1 e inputs
F2d 17/17 coinciden; esto solo prueba integridad de archivos. En aquella actualización
documental no se ejecutó runtime ni se consumió JIT. La ejecución posterior y su NO-GO
de fixtures se registran en la sección vigente siguiente.

## Resultado de fixtures y correcciones de seguridad — 2026-10-08

La primera ejecución aislada quedó como historia: el paquete de seis archivos produjo
12 PASS/1 FAIL porque no incluía la corrección del fixture de socket. Después se aprobó y
consumió una única ejecución r3, con 13 archivos verificados por hash. Pytest terminó
**19 PASS/1 FAIL**; falló la expectativa del helper F2d para una ruta seleccionada distinta.
También fallaron dos regresiones shell: el fixture del comparador pegó el duplicado al
registro anterior sin separador, y el scanner no redactó porque pasó `--` a `awk`. El
scope guard pasó (`ordinary=3|newline=1|controls=1|malformed=3`). Resultado r3 global
**NO-GO**, exit 1; no hubo retry. El contenedor `--rm` se retiró; no se inspeccionaron ni
limpiaron otros recursos y no se llamó Docker API desde dentro. Ver
[evidencia de fixtures](evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

Se corrigió el helper para reportar una ruta seleccionada distinta antes de consultar al
peer; el fixture duplica ahora un registro completo. El scanner ahora examina los blobs
binarios del índice y de cada revisión cambiada, sin omitir `.lock` ni parsear líneas de
diff; las nuevas regresiones cubren NUL, `.lock`, contenido que empieza `++` y diff de
blobs binarios. Son correcciones de código revisadas estáticamente y siguen sin revalidar
en Docker. Requieren manifiesto nuevo y aprobación JIT nueva antes de una ejecución.

La revisión independiente identificó además una condición pendiente en el control de CI:
el texto versionado de reglas enumera `security-audit` como check obligatorio, mientras
`Protected Workflow Integrity` corre desde `pull_request_target` y su condición requerida
por separado no está acreditada. Si el único check obligatorio es el workflow que define
el propio PR, este puede sustituirlo por un job de éxito. La revisión es estática y no
consultó las reglas activas de GitHub. Se requiere verificar y, si falta, añadir
`Protected Workflow Integrity` como check requerido en `desarrollo`, `certificacion` y
`main`; eso necesita aprobación remota independiente. Ningún HIGH/CRITICAL se da por
descartado hasta terminar la revisión final del diff.

C02 v4 no-C03 quedó 71/72 en el corte anterior por el cambio del workflow; tras el nuevo
guard HMAC del BFF la revalidación vigente es 70/72. C03 SQL v3 continúa 41/41; no se repitieron
suites ni SQL. ShellCheck/actionlint no corrieron en esta etapa y su presencia en la imagen
sigue sin verificarse. Snapshot completo, smoke Pages/workerd, C03 integrado, CI efectivo,
UAT final, `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL` siguen NO-GO.

## Entrada técnica vigente del proyecto completo — 2026-10-08

[Capa de trazabilidad](trazabilidad/00_entrada_tecnica.md): mapa de componentes
producto/DB/pipeline/runtime/CI/tooling/historia, contratos y consumidores, matriz de
impacto, cobertura/evidencia y protocolo constructor. Es documentación local solicitada
para todo el proyecto; cualquier PR/remoto requiere instrucción humana separada.
[Revisión y límites](evidencia/trazabilidad_tecnica_proyecto_2026-10-07.md) conserva el
corte anterior. No crea autoridad ni GO funcional. Preservar snapshot/NO-GO: S1 falló antes de npm/workerd;
D3 falló antes de tar por una configuración inválida del logging `local` (`max-file=1`
con compresión habilitada), demostrada por J2. Esto no prueba ownership ni causa S1, cuyo
runner usa `log-driver none`. D4 se aprobó/consumió una vez; su harness terminó exit 1 por
una expectativa incorrecta sobre `.Mounts`, aunque el proceso sintético devolvió exit 0.
J3 (SHA-256 `1ce8f345b4b8c92559228d5cc6d5b46ae198d2febbef486efb1f9111a61676f1`) confirmó
que solo esa expectativa difería: `HostConfig.Tmpfs[/diag]` y los demás controles
allowlisted coincidieron. El fixture sintético demuestra el mecanismo, no la causa S1.
Ver [reconciliación D4](evidencia/h3req1_c03_d4_metadata_mismatch_reconciliation_2026-10-07.md)
y [resultado J3](evidencia/h3req1_c03_d4_metadata_read_2026-10-07_j3.md). El contenedor
D4 `d52d606bdc809eb7bfd13c6e16c4e0a7bc29db2bf3e71e7941b75a84de868650` quedó exited y
preservado, sin stop/cleanup/retry. F1 quedó preparado con runner/sidecar/JIT propios; la
auditoría estática final encontró 0 HIGH/LOW y un MEDIUM de bypass same-user, que el humano
aceptó expresamente junto con el JIT F1. El JIT F1 fue ejecutado una sola vez y quedó
consumido. `docker create` tuvo éxito, pero la inspección pre-start rechazó controles; el
runner no llamó a `start` y no hizo stop/remove/retry. ID preservado
`54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`; el campo discrepante no
está en el reporte y no se infiere. F1 no es PASS del snapshot y no demuestra causa S1 ni
ownership. Ver [reconciliación F1](evidencia/h3req1_c03_source_snapshot_f1_prestart_failure_reconciliation_2026-10-07.md)
y [reporte F1](evidencia/h3req1_c03_source_snapshot_2026-10-07_f1.md), además de la
[atestación de aprobación F1](evidencia/h3req1_c03_source_snapshot_f1_approval_2026-10-07.md).
F2b fue aprobado una vez con aceptación expresa de sus dos residuales MEDIUM y terminó
**NO-GO**, exit 1 en `context-config`: el path Unix seleccionado no pasó la comparación de
canonicalidad con `realpath`. El valor se descartó; no se consultó `/proc`, imagen, contenedor
ni daemon API. No se hizo retry y el permiso está consumido. Esto no demuestra proxy, symlink
ni causa de F1. El ID F1 permanece intacto y su control discrepante sigue desconocido.
[Resultado F2b](evidencia/h3req1_c03_f1_daemon_diagnostic_f2b_2026-10-08.md).
F2c recibió aprobación nueva para una invocación y aceptación expresa de sus dos residuales
MEDIUM. Terminó **NO-GO**, exit 1 en `daemon-identity-proof`: confirmó endpoint Unix local,
socket y ruta canónica, pero no pudo probar la identidad del peer. El reporte no conserva el
submotivo interno. Por el gate, hubo cero Docker API calls, cero lecturas de imagen y cero
inspect de F1; el ID F1 no cambió y la discrepancia histórica sigue desconocida. El permiso
F2c está consumido; no se reintenta. Ver [resultado F2c](evidencia/h3req1_c03_f1_daemon_diagnostic_f2c_2026-10-08.md).
Se preparó y revisó estáticamente F2d como alternativa de identidad directa con `SO_PEERCRED`,
con códigos de fallo sanitizados y sin enumerar todos los descriptores `/proc`. `bash -n`,
sidecar e inputs hash-bound pasaron; el helper Python, parser y runtime no se han probado en
Docker. Está pendiente de aprobación JIT independiente y aceptación fresca de ambos
residuales MEDIUM. Ver [revisión F2d](evidencia/h3req1_c03_f2d_diagnostic_static_review_2026-10-08.md)
y [manifiesto F2d](operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md).

El scanner canónico y el scope guard H3 se corrigieron localmente. La revisión halló y cerró
dos salidas fail-open del guard (`git diff` fallido y errores de filtro `grep`); los registros
de path vacíos también fallan. Aún faltan regresiones de paths positivos/negativos, actionlint
y review dentro de Docker. En el corte anterior a la guardia HMAC, C02 v4 no-C03 estaba
71/72 por el workflow; la revalidación vigente es 70/72 tras el cambio de `admin-bff.ts`.
C03 SQL v3 41/41 coincide. No se repitieron suites ni se ejecutó SQL. Ver
[revalidación de hashes](evidencia/h3req1_revalidacion_hashes_2026-10-08.md).
Snapshot completo, smoke Pages/workerd, C03 integrado, `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`
siguen NO-GO.
D4 runner/sidecar/JIT:
`785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107`,
`84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c`,
`fcec517023f4a85e1381ad4b1b2be949fba933596e469293fed28315397a4fba`.
Antes de editar un componente, registrar consumidores, contrato, impactos, pruebas y
evidencia a preservar/renovar. El scope guard quedó con una lista explícita de paths H3 y
documentales; actionlint, revisión Docker e inventario final siguen pendientes. Ninguna
protección CI se desactiva.

En el corte anterior: 21 tests docs/cliente PASS en Docker y grafo 115/115 notas alcanzables,
0 sin entrada/rotos. Esos resultados no validan los cambios actuales.
[Evidencia y límites](evidencia/trazabilidad_tecnica_proyecto_2026-10-07.md).
La evidencia previa confirma que el scanner oficial no era válido: el temporal falló pese
a imprimir PASS. La corrección local ahora falla cerrado y tiene regresiones preparadas;
requiere ejecución real dentro del stack local aprobado antes de GO_LOCAL_PR. NO-GO global
permanece.

## Preparación pre-ejecución D3 — corte histórico — 2026-10-07

Se reconcilió la [ruta y prompt](operaciones/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md):
D2/S1 consumidos, no pendientes; no repetir D2, bootstrap npm o drill. Ownership tar
1000 con cap-drop ALL sigue siendo una hipótesis; exit 2 sin stderr no demuestra la
causa histórica. En este corte se había preparado localmente el runner D3 y su manifiesto
para un fixture sintético, antes de que el JIT D3 se aprobara y ejecutara.
`bash -n` del runner, `sh -n` del payload, sintaxis del launcher y verificación SHA-256
del runner/manifiesto pasaron en la preparación. El manifiesto JIT D3 se conserva sin
editar como snapshot aprobado pre-ejecución; su encabezado ya no representa el estado
actual. Los resultados reales constan en la reconciliación D3 enlazada abajo.
La última alerta estática de stderr crudo se verificó como falso positivo: ambos
wrappers Docker redirigen `stderr` de `timeout` y su hijo a `/dev/null`; los streams
de creación/logs que sí se capturan pasan por sanitización acotada.
La revisión estática final no confirmó hallazgos HIGH/MEDIUM de ejecución; dejó un
residual LOW documentado en el JIT: stdout estructurado de comandos Docker está sujeto
a timeout, pero no a límite explícito de bytes, bajo el supuesto de daemon local confiable.

La revisión de `.github/workflows/security-audit.yml` confirma que la allowlist de
Protected Path Integrity aún no incluye el runner/manifiesto D3 ni este JIT; por ello
estos artefactos no pueden entrar en un PR protegido hasta revisión/aprobación humana
separada del ajuste de scope guard. No se modificó ningún workflow ni se abrió PR.

## Resultado de la ejecución autorizada D3 — 2026-10-07

El JIT `H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D3` fue aprobado y consumido
una sola vez con JIT SHA-256
`cd90d783b7ec5a65a5ccc4e57fe6f737681d7aa4f8ed46a4d9c7e8c786f3ae7c`, runner
`a64fa5743372d5ff39fb9a009d89beb68a9afec756b32455066db06f84c41796` y manifiesto
`560ea87e661acd95406ea749358b060d0132dcc97300682db1b101ef1f4ca0e1`. Docker devolvió
el ID exacto `81c57f0e70538d7430e46a61d745a3b6296fb943980342f2caeead19c0658ebf`; el runner
terminó `NO-GO`, exit 1, durante `one-new-offline-synthetic-diagnostic-container`. Su
inspección acotada de manejo de fallo registró estado `created`, por lo que no hizo stop;
el recurso queda preservado sin cleanup.

D3 no ejecutó el script sintético dentro del contenedor: no llegó a tar productor/receptor,
snapshot, npm, Pages/workerd ni a la comparación de ownership. Al cierre de la ejecución
D3, el runner descartó stderr del daemon y `.State.Error` aún no se había consultado; en
ese corte la causa del fallo D3 y la hipótesis histórica de ownership seguían sin demostrar.
J2 posterior recuperó la causa D3, como se registra abajo. Se conserva intacto el reporte
original [D3](evidencia/h3req1_c03_snapshot_diagnostic_2026-10-07_d3.md), SHA-256
`76e4c7c4182bcb30156f7a12eea87376aa68f6667c21a203ef8a7ddcc9f43a23`, y el manifiesto JIT
aprobado, SHA-256 indicado arriba. La actualización factual y el siguiente JIT están en
la [reconciliación D3](evidencia/h3req1_c03_d3_create_start_failure_reconciliation_2026-10-07.md).

J1 fue aprobado/consumido y su parser falló cerrado, sin exponer salida; no se repitió.
J2, lectura nueva solo de `.State.Error`, fue aprobado/consumido una vez y devolvió
`failed to initialize logging driver: compression cannot be enabled when max file count is 1`.
Ver [evidencia J1](evidencia/h3req1_c03_snapshot_d3_create_failure_inspect_2026-10-07.md)
y [J2](evidencia/h3req1_c03_snapshot_d3_state_error_read_2026-10-07_j2.md). La causa del
fallo de arranque de D3 queda demostrada; ownership sigue sin probarse por D3. D4 y su
resultado posterior se reconcilian arriba y en evidencia propia. No repetir D3/D2/S1 ni
acceder a otros recursos.
No hay snapshot PASS, smoke Pages/workerd PASS ni C03 integrado PASS; C02 v4 y C03 SQL v3
se conservan por alcance/hash y no se reejecutaron.

## Resultado D2 y S1 NO-GO — 2026-10-07

El JIT exacto `H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D2` se aprobó y consumió una vez
con manifiesto SHA-256 `6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c` y runner
`f337ed07de258c632c1cfcfa9f6292f8b1f19389bb06112fc5f8bec192e96447`. El único `docker inspect`
fue del contenedor R4 exacto y leyó nombre/estado/exit/OOM/log-driver: `exited`, exit 1,
`OOMKilled=false`, `log-driver=none`. No se consultó imagen, logs, exec, redes ni volúmenes; no
se cambió ni limpió recurso. Reporte sanitizado local, ignorado por `*.log`:
`.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log`, SHA-256
`a62865e09cf409a81047999e438f45aa0c1abdb1b4e4d4b2b9c8532679c9dda6`. D2 no explica por qué no
levantó `healthz`; el log histórico es irrecuperable (`log-driver none`, stdout/stderr suprimidos).

Se preparó una reproducción S1 en [JIT](operaciones/manifiesto_jit_h3_close03_startup_smoke_2026-10-06_s1.md),
que ejercita el mismo bootstrap hasta Pages/workerd healthz en modo dedicado. El JIT fue aprobado
y consumido una vez. Manifiesto de 13 inputs SHA-256
`67fdea215c289cec028dae46172ba431814c598211561c17e6846d24e1c9ca7f`; runner
`c5fd272fdd18ef5a84d19bd1de229c421eb7dcccef7c2f1817460bcd9cc1a0d0`; supervisor
`6a5e14271ad4795ccbfff8e2e7049a702cca9c9bcdc060b24df5798a2a8e3fcd`; runtime actualizado
`637990b49e585d9772b62e8f5eeac0aa3708f082d9106228d62caf3859776e3a`. Manifiesto source S1
13/13 PASS (`ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d`); manifiesto JIT
13/13 PASS; Bash/Node syntax y `git diff --check` PASS. La auditoría independiente estática final
del 2026-10-07 devolvió 0 hallazgos. Se cerraron hallazgos de buffers/retry, TOCTOU del snapshot
y capacidad tmpfs mediante filtrado incremental binario, `--fetch-retries=0`, verificación del
source manifest dentro del snapshot antes de npm y cota simultánea corregida. Artefactos/JIT
actualizados el 2026-10-07; gates estáticos y auditoría final permanecen PASS/0.

Ejecución autorizada S1 2026-10-07: **NO-GO** en `phase=create-new-source-snapshot`, exit 2,
antes de ambos npm ci y del arranque workerd. Evidencia sanitaria
`.context/evidencia/h3req1_c03_startup_smoke_2026-10-07_s1.md`, SHA-256
`46b5d62efc1a557ed4a6833ffaf62b2ae290ae15c4761b33601702524876436b`. La evidencia confirma el
holder `h3req1-c03-startup-volume-holder-20261006-s1` running en red none y stop acotado del
snapshot por ownership verificado. Los tres volúmenes se crearon antes de la fase fallida y se
preservan; no hubo inspección posterior, cleanup ni retry. La red de runtime y los bootstraps no
se alcanzaron. El output no identifica causa más específica. No hay smoke PASS; C03 integrado
continúa bloqueado y cualquier diagnóstico/retry/cleanup requiere JIT independiente.

El cambio del runtime solo añade un modo diagnóstico `--startup-smoke` con Auth mock apagado,
fixture gateway sin rutas Auth/PostgREST y cero solicitudes; el modo integrado normal conserva
su digest completo. El manifiesto R4 permanece intacto como evidencia histórica, pero ya no es
el cierre transitivo del runtime actualizado. El futuro C03 integrado requiere manifiesto full
nuevo y su JIT independiente. S1 no usa fixture SQL, `.env*`, secretos de operador, caches ni
recursos R1–R4.

H3-CLOSE-02 v4 (72/72 no-C03) y C03 SQL v3 (41/41) se conservan por alcance/hash históricos;
no se reejecutaron ni se modificaron sus inputs SQL. El checkout original y el WIP completo del
candidato siguen preservados.

## Ruta de cierre solicitada — 2026-10-06

[Ruta ejecutable y prompt actualizado](operaciones/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md):
diagnóstico suficiente -> smoke real de arranque -> C03 integrado -> gates finales ->
GO_LOCAL_PR acotado -> PR/integración/deploy autorizados -> D01–D14 y GO Development real.
Evitar nuevos drills completos sin diagnóstico. D2 se consumió una vez y no garantiza causa raíz;
S1 fue aprobado/consumido una vez y terminó NO-GO antes de npm/workerd, sin causa detallada.
C03 integrado sigue bloqueado. Cualquier nuevo diagnóstico, retry o cleanup necesita JIT separado;
no se harán consultas a los recursos preservados bajo la autorización S1 consumida.

## Preparación estática del diagnóstico D2 — corte pre-ejecución

Tras el NO-GO del guard de imagen D1, se preparó un runner nuevo e independiente. JIT propuesto
`H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D2`; manifiesto de 5 inputs SHA-256
`6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c`; runner
`tests/h3req1_c03_integrated_runtime_diag_d2.sh` SHA-256
`f337ed07de258c632c1cfcfa9f6292f8b1f19389bb06112fc5f8bec192e96447`. Fija el manifiesto R4
(`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`), runner R4
(`28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474`), log R4
(`208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34`) y reporte D1
(`82cda545f327eb721fb1442ba91f962b5b3eb4b4e50a2a86e0c2e175f5a85347`). El único acceso Docker
propuesto es un `inspect --format` al nombre exacto del runtime R4 para leer nombre/estado/
exit/OOM/log-driver; D2 excluye deliberadamente `.Config.Image`, no infiere identidad de imagen
y no pretende explicar el timeout. No ejecuta logs/exec/list/inspect de redes o volúmenes; no
monta caches ni crea/detiene/reinicia/limpia recursos. El runtime `log-driver none` impide
recuperar stdout/stderr. El reporte sanitizado nuevo, si se aprueba, sería
`.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log`.

Gates estáticos de ese corte: `bash -n`, `git diff --check`, `sha256sum -c` 5/5; rama/HEAD
esperados `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`. El resultado
D2 aún no existía al preparar este runner; su única ejecución y resultado están arriba.
La primera auditoría detectó un LOW por falta de guard de symlink en `tests/`; se añadió el
guard antes de leer inputs. La reauditoría cerró ese hallazgo del runner y encontró un LOW
documental (estado aún decía “pendiente”); esta actualización lo remedia. No hay hallazgos
técnicos HIGH/CRITICAL/MEDIUM. Gates finales `bash -n`, `git diff --check`, `sha256sum -c` 5/5
pasan. No se ejecutó Docker/inspect, runtime, SQL ni acceso remoto.
JIT D1 y R4 consumidos: D2 necesita aprobación humana independiente, y no autoriza otro inspect,
lectura de logs, limpieza, resume, retry, recursos R1/R2/R3, PG17/PostgREST, SQL, Supabase,
push/PR/merge/deploy. Comando propuesto, solo tras auditoría y aprobación:

```bash
bash tests/h3req1_c03_integrated_runtime_diag_d2.sh \
  --jit H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D2 \
  --manifest-sha256 6f6f4e451e45dec30c8145b2bb328286786aaf36d887635ae0be14f5e4547e6c
```

Rollback: no ejecutar o detenerse antes de cualquier futura autorización; preservar recursos y
evidencias. Esta operación diagnóstica es metadata-only y no cambia contrato de producto, por
lo que expand/deploy/contract no aplican.

## Resultado de ejecución autorizada del diagnóstico D1 — 2026-10-06

JIT `H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D1` aprobado/consumido con manifiesto
SHA-256 `19618493b6ecc5148dd6320a8c915f97563b3d79eea57507950b08928c38a914`; el runner verificó
4/4 inputs. La única llamada Docker fue `inspect --format` al runtime R4 exacto. La metadata
recibida no pasó la igualdad literal de `.Config.Image` con el string pinned, por lo que el
runner suprimió metadata y salió `NO-GO: R4 runtime image does not match the pinned digest`
(fase `read-only-inspect-exact-r4-runtime`, exit 1). Esto puede ser una diferencia de forma
entre referencia/tag y metadata Docker; **no confirma** que la imagen ejecutada fuera distinta.
No se emitió estado/exit/OOM/log-driver ni se obtuvo causa del timeout.

No se ejecutaron `docker logs/exec`, no se inspeccionaron redes/volúmenes/caches ni se detuvo,
reinició o modificó el contenedor. No hubo acceso remoto ni DDL/DML. Solo se creó el reporte
sanitizado `.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log`, SHA-256
`82cda545f327eb721fb1442ba91f962b5b3eb4b4e50a2a86e0c2e175f5a85347`. D1 está consumido:
cualquier nuevo inspect, logs, cambio al guard o retry necesita un JIT/ciclo nuevo. Recursos
R4 permanecen preservados; R1/R2/R3 no fueron consultados.

## Preparación estática del diagnóstico D1 para runtime R4 — corte pre-JIT

Preparé un runner estrictamente read-only con JIT propuesto
`H3-CLOSE-03-INTEGRATED-DIAGNOSTIC-2026-10-06-D1` y manifiesto de 4 inputs SHA-256
`19618493b6ecc5148dd6320a8c915f97563b3d79eea57507950b08928c38a914`. Runner SHA-256
`e77be4ef49976dab09ccbb0a6c78934eade5ad3f8514fe8d4bab82078ea48239`; fija el manifiesto R4
`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7` y el log R4
`208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34`, además del runner R4
SHA `28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474`. Solo llamaría
`docker inspect` al nombre exacto `h3req1-c03-integrated-runtime-20261006-r4`, emitiendo campos
allowlisted image/state/exit/OOM/log-driver. El runtime usa `log-driver none`; D1 no ejecuta
`docker logs`, `docker exec`, ni inspecciona redes, volúmenes o caches. No arranca, detiene,
reinicia ni altera contenedores; no crea recursos. Resultado previsto, si JIT se aprueba:
`.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d1.log`.

Gates estáticos D1 finales antes del JIT: `bash -n`, `git diff --check`, `sha256sum -c` 4/4.
Auditoría final sin HIGH/CRITICAL/MEDIUM ni LOW bloqueantes; LOW de log-driver mitigado con
allowlist exacta `none`. Rama/HEAD `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. No se ejecutó diagnóstico post-fallo; inspección
adicional del runtime requería JIT D1 humano nuevo. La ejecución y su NO-GO se registran arriba.
Aunque se apruebe, si metadata no explica el timeout, recuperar logs de runtime o retry necesita otro plan/JIT. No autoriza R1/R2,
caches o volúmenes R3/R4, Postgres, servicios, SQL, red, stop/restart, cleanup, Supabase remoto,
push, PR, merge o deploy.

## Resultado de ejecución autorizada del drill integrado R4 — 2026-10-06

JIT `H3-CLOSE-03-INTEGRATED-2026-10-06-R4` aprobado y consumido con manifiesto SHA-256
`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`. El runner verificó
62/62 inputs. Los tres bootstraps terminaron y el verificador registró los digests de los
volúmenes de dependencias; por tanto, el bootstrap Deno con config explícita y `--frozen`
superó esa fase. En `isolated-workerd-bootstrap`, tras iniciar el runtime, el control `healthz`
agotó el timeout de 60 intentos: `NO-GO: runtime state timeout: healthz`; exit 1. El log R4
registra tres `bootstrap-diagnostic-class=no-recognized-safe-category`, pero no ofrece una
causa raíz del timeout.

No se alcanzaron la fase de creación de PG17/PostgREST, las pruebas del user worker ni SQL.
No hubo acceso remoto, Auth externo ni correo. Quedaron preservados sin cleanup los recursos R4
creados hasta esta fase (bootstraps, verificador, runtime, redes edge/data y volúmenes); en el
JIT R4 no se inspeccionaron servicios después del fallo. Más tarde D1 hizo solo el `inspect`
acotado descrito arriba; no leyó logs de servicio. Los nombres de PG17, PostgREST,
Edge active/suspended y sus fases posteriores solo fueron preflight-checked, no creados. No se
montaron caches/volúmenes R1/R2/R3; el único input R3 fue el lock file fijado por hash. C02 v4
y C03 SQL v3 permanecen PASS y no se repitieron.

Los JIT R4 y D1 están consumidos. **No hay retry, nueva inspección, cleanup ni resume autorizado**;
diagnosticar el runtime o hacer otro intento requiere un JIT independiente y un ciclo nuevo.
Evidencia: [log R4](evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log) y
[protocolo](evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

## Preparación estática del candidato integrado R4 — corte pre-JIT, 2026-10-06

Se incorporó el lock R3 aprobado al candidato del drill integrado. El manifiesto
`tests/h3req1-c03-integrated.sha256` fija **62 inputs**, SHA-256
`e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7`; el runner tiene SHA-256
`28c417bee4bd0f3c0d9d1e576397c8be1af9e7d0309b81a58c1fcc4f3639f474`. El lock R3 incluido es
`tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock`, SHA-256
`ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428`. El snapshot copia el
`deno.json` limpio del resolver y el lock a `admin-invite/deno.json`/`deno.lock`, verifica ambos
con `cmp`, excluye `package.json`, y hace bootstrap fresco Deno con `--config` explícito y
`--frozen`; luego el Edge Runtime usa ese mismo snapshot y cachés nuevas.

Gates estáticos finales: `bash -n`, `git diff --check`, `sha256sum -c` 62/62; rama/HEAD
esperados `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`. Auditoría
final: cero HIGH/CRITICAL/bloqueantes; un LOW de señales se mitigó con traps HUP/INT/TERM y se
reevaluó. Persiste MEDIUM aceptable solo con aprobación JIT explícita (egress bridge general,
lifecycle scripts Miniflare, sin límites cgroup, cuota de disco ni timeout global). **No se
ejecutó Docker/Deno/runtime/SQL durante esta fase de preparación. Después se aprobó y consumió
el JIT R4; su resultado se registra arriba. El drill integrado queda **NO-GO**.

Nombres previstos del runner R4, todos nuevos; no todos llegaron a crearse:
contenedores `h3req1-c03-source-snapshot-20261006-r4`,
`h3req1-c03-bootstrap-miniflare-20261006-r4`, `h3req1-c03-bootstrap-pages-deps-20261006-r4`,
`h3req1-c03-bootstrap-edge-deps-20261006-r5`, `h3req1-c03-dependency-cache-verify-20261006-r4`,
`h3req1-c03-integrated-runtime-20261006-r4`, `h3req1-c03-integrated-pg17-20261006-r4`,
`h3req1-c03-integrated-postgrest-20261006-r4`, `h3req1-c03-integrated-edge-active-20261006-r4`,
`h3req1-c03-integrated-edge-suspended-20261006-r4`; redes `h3req1-c03-integrated-edge-20261006-r4`
y `h3req1-c03-integrated-data-20261006-r4`; volúmenes `h3req1-c03-integrated-source-snapshot-20261006-r4`,
`h3req1-c03-integrated-tls-20261006-r4`, `h3req1-c03-integrated-miniflare-node-modules-20261006-r4`,
`h3req1-c03-integrated-pages-node-modules-20261006-r4`, `h3req1-c03-integrated-edge-deno-cache-20261006-r5`
y `h3req1-c03-integrated-edge-node-modules-20261006-r5`; log
`.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log`. El JIT debe reconocer que no
hay cuota de disco para named volumes ni timeout global, CPU/RAM sin límites cgroup, y que un
fallo preserva el estado sin cleanup/resume. Los 6 volúmenes llevan labels con nonce R4 nuevo y
se verifica el nombre exacto para impedir reutilización/carreras; el runner no consulta nombres
ni monta recursos R1/R2. Solo consume como archivo el lock R3 ya aprobado; no inspecciona el
cache/volumen R3.

Transición: **expand** añade lock/config al fixture inmutable; **compatibilidad** conserva el
contrato del Edge y no cambia archivos de producto ni producción; **deploy** no se autoriza ni
ocurre en este ciclo; **contract** queda para una futura promoción protegida. Rollback local:
ante fallo detener el ciclo, no auto-limpiar ni reanudar, preservar contenedores/volúmenes/log;
no retroceder silenciosamente al lock R2 fallido. El único PG17 es descartable, local y tmpfs;
no hay Supabase remoto, correo, push, PR, merge o deploy.

## Resultado de ejecución autorizada — resolver Deno Edge R3 — 2026-10-06

JIT `H3-CLOSE-03-EDGE-LOCK-RESOLVER-2026-10-06-R3` aprobado y consumido con manifiesto
SHA-256 `60805a1aca0dd3fbd96aeabe2f18a3a6c3efa6df8cafccaf184a66cfb92334f0`. El resolver
verificó los 4/4 inputs y completó exit 0. Lock v4 generado:
`tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock`, SHA-256
`ccb3d17f01947e679fb530ba7cbc9d252263ab1051d1d9ab21429eecde7ba428`. Su sección `specifiers`
contiene solo `jsr:@supabase/functions-js`, `npm:@supabase/supabase-js` y el transitivo
`npm:openai`; no aparecen `miniflare`, `esbuild` ni `typescript`. Es resultado del resolver,
no todavía validación integrated/frozen de Edge Runtime.

Contenedor y volúmenes R3 quedan preservados; no hubo cleanup. El log está en
`evidencia/h3req1_c03_edge_lock_resolver_2026-10-06_r3.log`. No se inspeccionaron ni montaron
caches/volúmenes Docker R1/R2. El lock ya se incorporó al candidato/manifiesto R4, que requirió
auditoría/JIT; posteriormente R4 se aprobó/consumió pero falló antes de alcanzar Edge user
worker (ver resultado R4 arriba). El drill sigue **NO-GO**. En la ejecución R3 no se inició Edge Runtime,
Pages/workerd, PostgREST ni PG17, no se ejecutó SQL ni hubo acceso remoto.

## Resultado de ejecución autorizada C03 R1 — 2026-10-06

El JIT exacto `H3-CLOSE-03-INTEGRATED-2026-10-06-R1` fue aprobado para el manifiesto
`a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101`. El runner verificó
62/62 hashes; `bash -n` y `git diff --check` pasaron. El snapshot de fuentes y los dos
bootstrap npm completaron; el bootstrap Deno Edge terminó con exit 1. El contenedor
`h3req1-c03-bootstrap-edge-deps-20261006-r3` quedó `exited|1|false`. La salida del bootstrap
fue suprimida y `log-driver none` impide recuperar la causa desde logs; causa raíz no
determinada.

No se alcanzaron Edge Runtime, Pages/workerd integrado, PostgREST, PG17 ni SQL; no hubo
operaciones remotas. No se ejecutó cleanup ni resume. Los contenedores y volúmenes creados,
incluidos los caches Edge r3 potencialmente parciales, quedan preservados y no deben
reutilizarse ni eliminarse sin instrucción/aprobación separada. C02 v4 y C03 SQL v3 siguen
preservados sin repetición. C03 integrado continúa **NO-GO**; el resultado del intento R2 se
registra a continuación.

## Resultado de ejecución autorizada C03 R2 — 2026-10-06

El JIT exacto `H3-CLOSE-03-INTEGRATED-2026-10-06-R2` fue aprobado para el manifiesto SHA-256
`0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11`; el runner verificó
62/62. Snapshot y los dos bootstrap npm terminaron; el bootstrap Deno Edge falló con exit 1.
El log registró dos `no-recognized-safe-category` y uno `lockfile-resolution-failure`; este
resumen no contiene suficiente detalle para determinar la causa raíz.

No se alcanzaron Edge Runtime, Pages/workerd integrado, PostgREST, PG17 ni SQL; no hubo
operaciones remotas. No se ejecutó cleanup ni resume. Los contenedores y volúmenes R2,
incluidos los caches Edge r4 potencialmente parciales, quedan preservados y no deben
reutilizarse ni eliminarse sin instrucción/aprobación separada. Los caches R1 r3 tampoco se
inspeccionaron ni alteraron. C02 v4 y C03 SQL v3 siguen preservados sin repetición. C03
integrado continúa **NO-GO**; otro intento requiere nuevo ciclo/JIT.
Evidencia: [log R2](evidencia/h3req1_c03_integrated_run_2026-10-06_r2.log) y
[protocolo](evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).

## Preparación estática del resolver Deno R3 — corte pre-JIT, 2026-10-06

El log R2 solo permite asociar el fallo a `lockfile-resolution-failure`; no confirma causa
raíz. La inspección estática encontró una hipótesis: el lock actual se generó desde
`tests/h3req1-c03-bootstrap`, cuyo `package.json` mezcla el grafo Edge con dependencias de
Miniflare (`esbuild`, `miniflare`, `typescript`); ese lock se copia luego al directorio
`admin-invite`, que no tiene ese package manifest. Se preparó un resolver independiente que
monta solo el `index.ts` de Edge y un `deno.json` limpio (`nodeModulesDir: auto`), sin
`package.json`; esto es una hipótesis a probar, no causa confirmada.

JIT propuesto `H3-CLOSE-03-EDGE-LOCK-RESOLVER-2026-10-06-R3`, aún **pendiente**, manifiesto de
cuatro inputs SHA-256 `60805a1aca0dd3fbd96aeabe2f18a3a6c3efa6df8cafccaf184a66cfb92334f0`.
`bash -n`, `git diff --check`, `sha256sum -c` 4/4 y auditoría estática cerraron sin HIGH/
CRITICAL ni blockers. Rama/HEAD esperados: `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

La ejecución R3, si se aprueba, sería solo `deno cache` con la imagen Deno 2.1.4 fijada y
egress Docker bridge general (sin allowlist FQDN), sin npm ni lifecycle scripts. Crea el
contenedor `h3req1-c03-edge-lock-resolver-20261006-r3`, volúmenes nuevos
`h3req1-c03-edge-lock-deno-cache-20261006-r5` y
`h3req1-c03-edge-lock-workspace-20261006-r3`, log
`.context/evidencia/h3req1_c03_edge_lock_resolver_2026-10-06_r3.log` y lock nuevo
`tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock`. El resolver no
monta directorios host escribibles; source/config son read-only. Solo tras exit 0 y validación
en contenedor se copia el lock a `.context/evidencia/h3req1_c03_edge_lock_r3_candidate.tmp`,
se valida otra vez y se promueve atómicamente al path final. Ejecuta como UID 0 dentro del
contenedor, con rootfs read-only, `--cap-drop=ALL`, `no-new-privileges`, 2 CPUs, RAM/swap total
2 GiB, 256 procesos y `/tmp` de 512 MiB. Los volúmenes se verifican por nombre exacto y llevan
labels con nonce de esta invocación para rechazar carreras/reuso. Docker no fija cuota de disco
para named volumes ni timeout de pared; el posible consumo del Docker data-root y duración no
acotada deben aceptarse expresamente en el JIT. Los contenedores/volúmenes Docker R1/R2 y
caches r3/r4 no fueron inspeccionados, montados, reutilizados ni limpiados. **Salvedad de
auditoría:** una búsqueda estática incidentalmente leyó archivos generados bajo
`tests/h3req1-c03-bootstrap/node_modules/.deno`; no los modificó ni incorporó las coincidencias
a la evidencia, y
no confirmó su relación con esos volúmenes. No acceder, reutilizar ni limpiar esa ruta sin
instrucción separada. El resolver no autoriza el drill integrado, PG17, SQL,
Supabase remoto, correo ni operaciones Git.

Comando propuesto exclusivamente tras JIT humano separado:

```bash
bash tests/h3req1_c03_edge_lock_resolver_r3.sh \
  --jit H3-CLOSE-03-EDGE-LOCK-RESOLVER-2026-10-06-R3 \
  --manifest-sha256 60805a1aca0dd3fbd96aeabe2f18a3a6c3efa6df8cafccaf184a66cfb92334f0
```

Esta es tooling local para el drill: no altera comportamiento de producto ni criterios de
aceptación. La atestación sanitizada H3 mantiene autorización local hasta GO local, pero no
sustituye este JIT de egress ni el JIT independiente que necesitará un futuro drill integrado.

## Preparación estática R2 pre-JIT — 2026-10-06 (histórico)

R2 exige el nuevo JIT exacto `H3-CLOSE-03-INTEGRATED-2026-10-06-R2` y el manifiesto SHA-256
`0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11`. El runner ahora resume
los tres bootstrap mediante clases diagnósticas allowlisted; las respuestas dinámicas de
control se filtran por redactor y el digest de dependencias se valida contra un esquema fijo
de cuatro SHA-256 antes de escribirlo al log. R2 usa nombres nuevos y volúmenes Deno/Edge r4; no monta,
reutiliza, inspecciona ni elimina caches R1 r3. Los recursos R1, incluidos los que pueden
contener dependencias parciales, quedan preservados.

`bash -n`, `git diff --check` y `sha256sum -c` (62/62) pasaron; rama `feat/h3req1-sync-20261002`
y HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c` coinciden. En el corte pre-JIT R2 aún no
se había ejecutado Docker, npm, SQL ni servicios. El egress general Docker bridge de los tres bootstraps y los
efectos destructivos limitados al nuevo PG17 tmpfs deben aceptarse expresamente en el JIT R2.
Comando propuesto solo tras aprobación humana separada:

```bash
bash tests/h3req1_c03_integrated_drill.sh --jit H3-CLOSE-03-INTEGRATED-2026-10-06-R2 \
  --manifest-sha256 0e1634876956d8031ac99057dfc14936f65896b7a0d4626b642bfe8c4239aa11
```

## Bootstrap Edge y preparación del runner — corte pre-JIT, 2026-10-06

Los cierres SQL se preservan: **H3-CLOSE-02 v4 72/72 inputs no-C03** y **C03 SQL v3
41/41** siguen coincidiendo; no se repitieron. El Edge Runtime v1.74.3 ya está descargado
y verificado. `package-lock.json` npm quedó generado (solo metadata, sin instalar paquetes).
Lock v5 generado con Deno 2.9.7 se conserva como histórico, no compatible con Edge
Runtime v1.74.3, que fija Deno 2.1.4. El primer resolver 2.1.4 falló antes del lock por
falta de `nodeModulesDir: auto`; contenedor y cache parcial quedan preservados. Un JIT
retry aprobado generó el lock v4 compatible `deno-edge-runtime-v1.74.3-r2.lock` (SHA-256
`ce8a4a433e58cc9a4cee0e908cb7b629305b58a790666e107d56f53a6a3548b1`) y llenó dos
volúmenes cache nuevos. El postinstall de workerd aún no se ejecutó y Miniflare/workerd
no están instalados. Ya se prepararon y revisaron estáticamente el runner y fixtures
integrados; el runner incluye snapshot source-only verificado, tres fases de bootstrap con
egress Docker bridge general (no FQDN-allowlisted; JIT pendiente) y después dos redes
internas segmentadas; el gateway HTTPS escucha solo en EDGE y runtime verifica el volumen
Edge `node_modules` desde `/edge-node-modules`. El manifiesto de 62 inputs verificó 62/62
(SHA-256 `a1073d93d22b8c01ed0e41031e4c1f41df33848eac1ff31935b223c80f47e101`);
bash syntax y `git diff --check` terminaron con exit 0. Ninguna fase funcional se ejecutó. No se
iniciaron runtime, Pages/workerd, Edge, PostgREST ni PG17; tampoco se ejecutó SQL. C02 v4 y
C03 SQL v3 siguen preservados sin repetición. En ese corte C03 integrado quedaba **NO-GO** a
la espera de aprobación humana del JIT R1. Ver el
[protocolo y resultado](evidencia/h3req1_c03_integrated_protocol_preflight_2026-10-05.md).
El estado continúa **NO-GO**.

## Síntesis vigente y amarre documental — 2026-10-05

Revisión de continuación: [avance comprobado, PR/remoto y prompt nuevo](seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md).
La última sesión principal confirma C03 SQL v3 PASS; 41/41 hashes coinciden en esta
revisión read-only. C03 integrado sigue pendiente, candidato sin PR hacia desarrollo
en la consulta actual; Development real NO-GO. El encabezado «no aprobado» del manifiesto
v3 es el corte de propuesta preservado, no una instrucción vigente de repetirlo.

Estado **`NO-GO_H3REQ1_DEVELOPMENT_FREE`**. El
[traspaso ejecutable](seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md)
consolida H3-CLOSE-01–08; el [manifiesto v1](operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05.md)
registra el primer bootstrap fallido; el [v2](operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v2.md)
registra el primer fallo SQL; el [v3](operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v3.md)
registra los PASS parciales y el fallo de replay por headers residuales; y el [v4](operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md)
registra el PASS del runtime local cubierto por H3-CLOSE-02.
Leerlo junto al [plan único](operaciones/plan_cierre_integral_h3req1_2026-10-04.md),
[evidencia actual](evidencia/h3req1_development_candidate_cycle_2026-10-04.md),
[hito](hitos/hito_003.md),
[tarea](backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md) y
[seguimiento Sprint](seguimiento/seguimiento_sprint_1_h2_h5.md) y
[propuesta JIT safe-resume v3](operaciones/manifiesto_jit_h3_close03_safe_resume_pg17_2026-10-05_v3.md).

### Preflight integrado H3-CLOSE-03 — 2026-10-05

El preflight confirmó rama/HEAD y Docker en el worktree correcto. H3-CLOSE-02 v4 conserva
72/72 inputs no C03 intactos. La autoría local de tres fuentes SQL terminó; el PASS
safe-suspend v2 queda histórico para hashes anteriores. Bajo el JIT C03 v3 exacto y el
prompt `continua`, el subgate SQL safe-suspend/resume pasó en un PG17 nuevo con 4/4 procesos
`psql` exit 0 (los primeros tres solo bootstrap). El recurso nuevo se preserva sin cleanup;
el PG17 previo sigue intacto. C03 integrado y H3-CLOSE-01/04–08 siguen NO-GO. Ver
[evidencia del preflight](evidencia/h3req1_h3_close03_integrated_preflight_2026-10-05.md).

### Addendum H3-CLOSE-03 — remediación estática safe-suspend — 2026-10-05

Continuación documental posterior: se corrigieron tabla, procedimiento y prompt del
[traspaso](seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md), y el prompt
del [plan único](operaciones/plan_cierre_integral_h3req1_2026-10-04.md). Ambos comienzan
en H3-CLOSE-03 integrado, conservando H3-CLOSE-02 PASS v4 y safe-suspend SQL PASS v2.
La tabla de hashes del 2026-10-04 queda rotulada histórica/no ejecutable; no hay
instrucción vigente de repetir el runtime inicial ni JIT consumidos. Solo cambios con
impacto demostrado requieren revalidación y nuevo permiso. Gobierno general y recuperación
de conocimiento histórico se difieren; CI obligatorio de H3 sí debe completarse.
Ese ciclo documental previo editó solo documentación, sin código/SQL/tests funcionales ni
operaciones remotas, y mantuvo el NO-GO.
Validación documental: los prompts de plan/traspaso son idénticos; 68 enlaces locales
de las tres notas verificadas existen; Markdown/fences/newline PASS en Docker por stdin;
`git diff --check` PASS. El corte de grafo registrado en ese ciclo fue **100/100 notas
alcanzables, 0 sin entrada y 0 destinos locales rotos** (incluía seis manifiestos nuevos).
No se validaron URLs externas, anchors ni render Obsidian; no se repitieron suites del producto.

Validación documental de este ciclo: **102/102 notas `.context` alcanzables desde el índice,
0 sin entrada**. Cuatro referencias a assets fuera del checkout se excluyeron del grafo y
siguen anotadas en el mapa; los enlaces locales de las siete notas tocadas resolvieron.

La revisión de solo lectura detectó que `db/rollback/h3req1_safe_suspend.sql` revocaba
las RPC mutadoras internas, pero no el dispatcher autenticado `admin_signed_rpc`
(`SECURITY DEFINER`); el harness tampoco comprobaba una llamada firmada por esa ruta.
Con `continua` acotado se actualizaron localmente el rollback y
`tests/sql/h3_safe_suspend_harness.sql`: el dispatcher se incluye en revocación y
snapshot/restauración de ACL; el fixture prepara una prueba payload-bound y exige que
pre-request admita el destino pero la ACL suspendida rechace su ejecución y no consuma
el nonce.

Después se aprobó y ejecutó un JIT PG17 local nuevo: baseline H2→H3, cuotas, gateway
firmado y el harness actualizado safe-suspend pasaron. La salida anterior del gateway
incluyó firmas sintéticas de fixture; no se copiaron sus valores a evidencia ni hubo
claves/JWT/secretos de producto. La continuación safe-suspend pasó con `psql -q -o
/dev/null`, exit code 0 y sin output. Una consulta opcional de versión había fallado por
quoting sin alterar datos; `pg_config` confirmó PostgreSQL 17.11. El JIT v4 no cubre estos
bytes. La evidencia y aprobación consumida están en el [manifiesto JIT v2](operaciones/manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md).
La atestación H3-CA4/H3 local se revisó; no se amplió negocio ni permisos remotos.
H3-CLOSE-03 sigue pendiente del drill integrado workerd+Edge+SQL y de recuperación real;
el restore del harness es TEST-only. El contenedor PG17 permanece preservado sin cleanup.
El estado global permanece NO-GO.

Gateway payload-bound y guard NULL continúan implementados localmente. Se remediaron
además el HIGH de cardinalidad de Durable Objects (partición IP compartida, una cuenta
por solicitud y GC transaccional), el LOW del harness que no aislaba el shard y la
premisa incorrecta de que MFA `listFactors()` requiere GET `/auth/v1/factors`. El SDK
2.109.0 usa GET `/auth/v1/user`, ya permitido; la aprobación humana para el GET adicional
quedó sin consumir y la allowlist factors permanece POST-only.

Docker: pytest **287 PASS/4 skips** (1 warning deprecación PyPDF2); TypeScript PASS;
ESLint 0 errores/9 warnings existentes; npm audits 0 vulnerabilidades; cuotas UAT y
Miniflare, SDK/Auth, BFF mock, Edge, safe-suspend fixture y smoke web mock PASS. Credential
scan y `git diff --check` PASS. El JIT v1 falló antes de instalar por config npm duplicada;
el JIT v2 fue aprobado y su bootstrap terminó (90 paquetes, 0 vulnerabilidades), con Node
`v22.23.2` y SDK `2.109.0`. PG17 v2 encontró `key_id` ambiguo; se renombró localmente a
`v_key_id` con autorización separada. PG17 v3 pasó H2/H3/baseline/cadena/cuotas, pero el
replay falló por headers residuales del escenario non-editor. Se movió el replay exacto
inmediatamente tras la llamada positiva; en PG17 v4 pasaron los harnesses SQL, incluido el
replay 409, safe-suspend y baseline futuro contraído. PostgREST HTTP/SDK, SQL assert y
concurrencia también PASS. Se preservan redes, runners y bases PG17 tmpfs sin cleanup.
El PostgREST CI se restringió a loopback de forma estática, pero el workflow no se ejecutó. Detalles en la
[evidencia actualizada](evidencia/h3req1_development_candidate_cycle_2026-10-04.md).

**Sí se ejecutó SQL/PostgREST únicamente en PG17/Docker local desechable** bajo aprobación
v4; la suite indicada pasó, incluido el replay exacto y el wire. Los JIT v2/v3/v4 están
consumidos y no se repetirán. No hubo Auth/correo remoto, grants remotos, Git/CI remoto,
Cloudflare ni deploy. No se eliminó ningún recurso; cualquier cleanup requiere JIT separado.

Siguiente: planificar y validar localmente H3-CLOSE-03 (rollback integrado workerd+Edge+PG17,
sin activar ni limpiar recursos remotos) -> H3-CLOSE-04–06 -> autorizaciones separadas para
CI protegido e integración/despliegue -> D01–D14 reales -> GO Development. El PASS v4 no
cierra otros gates ni declara GO.
Auth+MFA remoto histórico se conserva sin reset/repetición; Romel/2026-11-03 para
braces/facetas y el objetivo 2026-10-11 del cierre backend siguen vigentes, no son
waivers. Certification/Production requieren autorización posterior separada.

El [mapa documental](seguimiento/mapa_documental_obsidian_2026-10-04.md) conecta notas
antes inaccesibles y explica historia, referencias retiradas y assets preservados fuera
del worktree. Este ciclo implementó cambios locales BFF/cuotas/transporte/tests y
actualizó documentación; no ejecutó DB/config remota ni acciones Git/remotas. Los cortes inferiores son
históricos donde contradigan esta síntesis y el traspaso; no recrean pendientes resueltos.

Validación anterior del ciclo documental: grafo `.context` del candidato **94/94 notas
alcanzables, 0 sin entrada, 0 destinos locales rotos**; 14 documentos con formato/fences
y newline verificados por Python dentro de `h3req1-candidate-docker-20261004` (contenido
enviado por stdin, sin modificar el snapshot), PASS después de reparar un fence histórico
faltante. `git diff --check` PASS. No se validaron URLs externas, anchors ni render Obsidian.
No se repitió pytest ni SQL/wire; sus PASS/runtime pendientes conservan el alcance previo.

## Estado vigente tras remediación local de límite NULL — 2026-10-04

Estado: **`NO-GO_H3REQ1_DEVELOPMENT_FREE`**. Tras el `continua` del 2026-10-04 se cerró
localmente el LOW de `p_first: null`: la RPC original rechaza SQL `NULL` antes de los
`LIMIT`; una migración forward-only actualiza la función ya aplicada o el snapshot
privado si está instalado el wrapper de cuotas, fallando cerrada ante drift. El
dispatcher signed detecta JSON `null` y lo convierte en el sentinel acotado `0` por la
RPC pública, para preservar el wrapper de cuota, AAL2, RBAC y el error legacy sin pasar
SQL `NULL` a `LIMIT`. Se conservan HMAC payload-bound, allowlist, `auth.uid()`, RLS,
grants y la ruta `service_role`.

La revisión estática final de `security-auditor` encontró **0 hallazgos LOW+** en este
alcance; no se concede waiver. Los harnesses SQL cubren RPC directa, reparación del
snapshot privado de cuota, AAL1, editor AAL2, no-editor y consumo de cuota, pero **no se
han ejecutado**. PG17/PostgREST requieren un JIT separado con los hashes actuales; el
wire, UAT/rollback integrado, gates remotos y aceptación D01–D14 siguen pendientes.
Owner del cierre: Romel; implementadores: Backend/DB Security; fecha objetivo:
2026-10-11. No se ejecutó SQL, PostgREST, Auth, Supabase remoto, Git remoto, PR, deploy,
promoción ni cambios de rama protegida.

Validación en Docker `h3req1-candidate-docker-20261004`, snapshot independiente en
`/workspace` y `.env*` excluidos: `/opt/venv/bin/python -m pytest tests -q`
**287 passed, 4 skipped**, 1 warning deprecación PyPDF2; credential scan explícito de los
archivos tocados y `git diff --check` PASS. También pasan las validaciones previas de
SDK/BFF/Auth/Edge UAT, TypeScript, lint y smoke build registradas abajo; no se repitieron
en este ciclo. Los cuatro skips siguen requiriendo `RUN_SUPABASE_INTEGRATION_TESTS=1` y
Supabase live. No se cargaron credenciales.

Se preservan el candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c` (baseline,
no identifica el WIP) y el checkout original `/home/romel/src/studiamatch`; no se
stageó ni creó commit. La evidencia ampliada está en
[el ciclo de candidato 2026-10-04](evidencia/h3req1_development_candidate_cycle_2026-10-04.md).

## Corte pre-remediación de firma — histórico 2026-10-04

Estado vigente: **`NO-GO_H3REQ1_DEVELOPMENT_FREE`**. El trabajo continúa en el
candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, sobre `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c`;
el HEAD identifica el baseline, no los bytes del WIP. No se stageó ni se creó commit.
El checkout `/home/romel/src/studiamatch` no se editó; conserva su propio WIP y no es
el candidato. Las validaciones se ejecutaron en `h3req1-candidate-docker-20261004`, con
bind de solo lectura al worktree y snapshot de trabajo separado bajo `/workspace`;
`studiamatch-dev` quedó intacto aunque estuviera reiniciándose.

Auth+MFA remoto PASS del 2026-09-27 y la cuenta existente acreditada se conservan como
evidencia; no se repite reset, re-enrolamiento ni operación Auth remota. Se implementó
localmente la compatibilidad BFF/cuotas y la firma HMAC separada por RPC: proyecto,
método, nombre allowlisted, actor, tiempo, nonce y key-id; Durable Object admite antes
de PostgREST. Con JIT humano acotado pasaron baseline, cuotas, migración, harness firmado
y safe-suspend en PG17 desechable. PostgREST 13 detectó 500/PGRST121 para un RPC Admin
sin firma: faltaba `headers` en `DETAIL`. Tras `continua`, se corrigieron localmente los
10 bloques PGRST y se preservó `Retry-After` en 503; contrato dirigido 43 passed, pytest
285 passed/4 skips, TypeScript, credential scan y diff check PASS. El quinto JIT confirmó
HTTP 403; discrepó el payload requerido/invalid. Tras `continua`, hook/harness/runner/
test distinguen firma ausente de firma parcial; pytest 285/4, TypeScript, Node syntax,
credential scan y diff-check PASS. El sexto JIT es requisito antes de DB runtime con los
nuevos hashes. Security review: un LOW de Retry-After fue cerrado; revisión actual no
encontró HIGH/CRITICAL, pero dejó LOW preexistente del HMAC sin vincular parámetros; su
disposición/owner están pendientes y no hay waiver. No hubo SQL/grants remotos ni se
tocaron contenedores históricos.

La revisión aceptó mantener `braces@3.0.4-h3.1` como snapshot temporal con Romel como
owner de revisión/reemplazo al `2026-11-03`. Las nueve advertencias ESLint y la
deprecación PyPDF2 quedan registradas; el defecto de facetas `priceMin` sigue fuera de
H3, separado para seguimiento con Romel al `2026-11-03`. No son waivers de calidad.

La evidencia de este ciclo está en
[H3REQ1 candidato local 2026-10-04](evidencia/h3req1_development_candidate_cycle_2026-10-04.md).
Resumen: TypeScript PASS; ESLint 0 errores/9 warnings; pytest 285 passed/4 skips
(todos live Supabase opt-in); npm audit dev/prod 0; H2 writer scan PASS; build normal
con fixture local PASS para ruta elegible y build mock PASS; BFF/SDK/cuotas/auth-error/invitación
Edge/safe-suspend y workerd PASS. YAML de `security-audit.yml` parsea (11 jobs), pero
actionlint/shellcheck no están disponibles en este contenedor y no se marcan PASS.
El SQL PG17 local pasó baseline/cuotas/migración/harness firmado/safe-suspend. El quinto
wire confirmó HTTP 403 con `DETAIL.headers`, pero recibió código `rpc_signature_invalid`
frente a la expectativa `rpc_signature_required`; el contrato se corrigió después sin
repetir SQL. No se hizo UAT E2E completa con PG17, reset/correo/Auth,
lectura/escritura remota, revisión/CI GitHub efectiva, push/PR/merge, deploy, rollback
remoto ni promoción.

Bloqueos para GO Development real: JIT nuevo para ejecutar bytes actuales y completar
wire; decisión owner/riesgo de LOW sobre firma no ligada al cuerpo; UAT/rollback integrado;
revisión
CI independiente y protecciones efectivas
aún no acreditadas; operaciones remotas Free,
Auth y Pages/Worker/Edge requieren permisos exactos separados; faltan aceptación D01–D14
remota, revisión final y compatibilidad/deploy. Certification/Production no ejecutadas.
No se declara GO por los PASS locales.

## Traspaso documental integral — corte inicial 2026-10-04 (histórico)

## Contenido del traspaso documental — corte inicial (histórico)

El responsable solicitó únicamente documentación Obsidian detallada para completar
H3REQ1 hasta Development real y después Certification/Production. El
[plan único de cierre](operaciones/plan_cierre_integral_h3req1_2026-10-04.md) es la
referencia operativa de continuación: consolida H3-CLOSE-01 a H3-CLOSE-08, aceptación
D01–D14, gates Ready/Development/Certification/Production, matriz JIT, transición y
prompt desarrollador. Sustituye como checklist activo al plan 2026-10-02; conserva
sus decisiones y evidencias históricas. La autoridad viva sigue en esta nota.

La revisión read-only confirmó `desarrollo@4eb4d877a50b012bb630a129bd0c74482c33be9c`,
PR #500 mergeado y checks consultados verdes en su head. Auth+MFA remoto del
2026-09-27, incluyendo challenge/verify y RPC protegidas, ya tiene evidencia PASS:
no se reabre como implementación pendiente. Deben validarse no regresión y transición
de la misma cuenta al BFF/HttpOnly, refresh/logout y los demás criterios reales.

En ese corte inicial, el candidato estaba en `/home/romel/src/studiamatch-h3req1-sync-20261002`,
`feat/h3req1-sync-20261002`, HEAD baseline `4eb4d87`, con WIP sin commit. Se preserva
`/home/romel/src/studiamatch` como checkout original, no como candidato de integración.
Los PASS locales r17/onboarding y 283 tests del corte 2026-10-03 se conservan, pero no
se reejecutaron en este traspaso ni constituyen aceptación del candidato final.

Ese traspaso inicial conserva el historial documental, los gates y las decisiones
remotas read-only acreditadas antes del presente ciclo. Su descripción de «solo
documentación» y sus resultados históricos no sustituyen la evidencia técnica actual
enlazada arriba ni representan el candidato final.

Historical gates preserved: `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED`, `PRODUCTION_REMEDIATION_PRO_EXPAND_COMPAT_BEFORE_MAIN`, `H2_CLOSED_H3_READY_FOR_PROMPT_CONTINUA`, `H3_READY_FOR_PROMPT_CONTINUA`, `H3_GO_LOCAL_CLOSED_READY_FOR_SUPABASE_FREE_JIT`, `H3_SUPABASE_FREE_AUTH_JIT_VALIDATION`, `H3_LOCAL_EXPANDED_NO_GO` (histórico del ciclo anterior, fechado 2026-08-30), `H3_PR_DEVELOPMENT_NO_GO` (readiness, resuelto por el ciclo de corrección local del 2026-09-02).

## Ciclo local BFF/HttpOnly H3REQ1 — 2026-10-02 UTC

El responsable exige un [plan de GO integral para PR y pruebas Development](operaciones/plan_go_h3req1_local_development_2026-10-02.md).
El entregable es readiness completo del candidato y del proceso de pruebas, no
entregas por hallazgo ni GO parciales. Incluye preparación local, CI independiente,
PR protegido, integración Development, Free/Preview, UAT y rollback planificados;
excluye Certificación/Producción. Los resultados remotos se obtienen durante la
ejecución autorizada, no se exigen como condición circular para iniciar las pruebas.
Readiness no equivale a pruebas remotas aprobadas ni sustituye sus JIT separados.
Las remediaciones de esta sesión pueden formar parte del PR si aportan al producto,
respetan el alcance cliente y tienen evidencia. Se planifica onboarding desde cero
de la cuenta designada con reinicio Free acotado tras inventario, preservando otro
admin activo y auditoría; la compatibilidad BFF se prueba con otra cuenta existente
sin reinvitarla. Estas decisiones no autorizan reset, writes, Git remoto ni deploy.

La evidencia más reciente es
[el ciclo local BFF/HttpOnly](evidencia/h3req1_bff_local_cycle_2026-10-02.md).
El candidato actual es el worktree aislado `/home/romel/src/studiamatch-h3req1-sync-20261002`,
branch `feat/h3req1-sync-20261002`, `HEAD=4eb4d877a50b012bb630a129bd0c74482c33be9c` y
árbol local sin commit. Su manifiesto y hash están en la evidencia; `HEAD` identifica
el baseline, no los bytes del candidato. El estado permanece
**`NO-GO_H3REQ1_DEVELOPMENT_FREE`**.

### Corte de readiness local — 2026-10-02, actualización posterior

**NO-GO** para congelar candidato, abrir PR funcional o iniciar pruebas remotas.
En la continuación posterior, el responsable ratificó exclusivamente el límite
Edge independiente **120 peticiones/actor/minuto** y aprobó por JIT únicamente el
drill SQL local en la base desechable PG17 `h3_final_uat_go_r14`. Tras verificar
identidad PG17, schema H3 y cero conexiones activas ajenas, el harness
`tests/sql/h3_safe_suspend_harness.sql` cerró `h3_safe_suspend_harness_ok`: suspensión
SQL idempotente, preservación de datos/auditoría/visibilidad, finalizadores in-flight
y restauración exacta de permisos solo en el test. Pages workerd y Edge fixture de
suspensión también PASS por separado. **No** acredita aún la combinación integrada
Pages/Edge/cookies/bindings/SQL; no se autorizó SQL remoto ni despliegue.
El inventario estático de 94 migraciones `2026*.sql` solo localizó `RAISE SQLSTATE
'PGRST'` en los dos archivos de cuota H3, no en los originales versionados. Eso no
garantiza el comportamiento del baseline Pro remoto ni cuenta abortos transaccionales;
el riesgo de RPC cancelada sigue abierto, sin waiver.
Inventario GitHub **solo lectura** autorizado en la misma continuación:
`desarrollo@4eb4d877a50b012bb630a129bd0c74482c33be9c` aparece protegida; el
directorio remoto `.github/workflows/` NO contiene aún
`protected-workflow-integrity.yml` (solo el YAML local WIP), y no hay PR abierto con
base `desarrollo` al consultar. Figuran `romelhc95` (admin) y
`romelhc95-approver` (write), dos identidades que pueden asumir roles distintos de
merge/review si sus permisos efectivos se verifican al abrir PR. El MCP no expone
configuración de required checks/rulesets: **no está acreditado** enforcement del
check independiente. No se hizo push, PR ni configuración GitHub.
La suite visual r17 cerró **PASS: 48/48 casos, 144/144 ejecuciones y 144 capturas,
cero retries** (`generatedAt=2026-10-03T02:15:53.295Z`); artefactos preservados en
`/tmp/h3req1-go-candidate-20261002-r14/evidence-expanded-uat-r17` dentro de
`studiamatch-h3req1-check`. Las fallas r13–r16 siguen conservadas, no se sustituyen.

El primer onboarding UAT no observó respuesta HTTP en la primera invitación. La
inspección read-only confirmó cero invitaciones/identidades nuevas. Se localizó una
carrera del test helper: esperaba el heading, no la sesión server-side AAL2. Se
añadió espera explícita por `/api/admin/session` AAL2, aserción de botón habilitado y
matcher same-origin/path. La repetición paced cerró **PASS 10/10** con intervalo
mínimo 20.1 s. Resumen sanitizado y checksums en
`/tmp/h3req1-go-candidate-20261002-r14/evidence-onboarding-uat-r1` del contenedor;
el primer fallo se conserva, no se atribuye a una invitación enviada.

El triage previo reclasificó `shadcn@4.21.1` de `dependencies` a `devDependencies`:
su CSS se consume al compilar el static export y los 151 assets fueron idénticos a
UAT r14. En el corte anterior, `npm audit --omit=dev` era 0 y
`npm audit --include=dev` seguía en 9 HIGH/0 CRITICAL por `braces <=3.0.3`. La
continuación 2026-10-03 integró localmente el snapshot fijado `braces@3.0.4-h3.1`;
una instalación limpia del WIP ahora reporta **0 HIGH/0 CRITICAL** en audit completo
y de producción. El upstream no publicó aún un release: responsable y fecha de
revisión del snapshot quedan abiertos, sin waiver.

Gates locales repetidos: pytest **283 passed/4 skipped** (los cuatro son tests live
Supabase opt-in), TypeScript PASS, ESLint 0 errores/9 warnings existentes,
actionlint/shellcheck/credential scan/`git diff --check` PASS; BFF 52, Edge invite,
SDK 26 y suspensión directa/workerd (8 aliases Admin, 3 rutas públicas) PASS.
`workflow_dispatch` sin baseline ahora falla cerrado localmente; push inicial usa
empty-tree para los gates de rutas/DB/credenciales. Esto no acredita enforcement CI
remoto. También se confirmó en PG17 que cancelar la transacción de una RPC revierte
su evento SQL de cuota: riesgo MEDIUM abierto, no waiver.

HEAD sigue siendo baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el árbol
continúa sin commit ni candidato congelado. Hubo lectura autorizada GitHub descrita
abajo, pero ninguna escritura GitHub/Supabase/Cloudflare, push, PR, merge o deploy.
Los dos artefactos untracked con nombres literales de plantilla siguen en 0 bytes,
intactos y excluidos; la captura de reglas GitHub también se excluye del candidato.

### Continuación de readiness — 2026-10-03

La matriz única de readiness quedó confirmada por el responsable, sin agregar
criterios fuera del plan vinculante y los pilares transversales. El veredicto sigue
**NO-GO** para PR funcional e inicio de pruebas Development.

- Tooling: el responsable aprobó integrar localmente un snapshot fijado del arreglo
  upstream `micromatch/braces` PR #72, commit
  `28d440b5dd449dbf1fe6f3506cf94ecca4d02660`. `web/vendor/braces-3.0.4-h3.1.tgz`
  identifica explícitamente que no es release oficial; su SHA-256 es
  `a8c0b0223dc788781252f9b056207b5b053b8dd0896da861c305769b472f0819`. En una copia
  limpia Docker del WIP: `npm ci`, audit completo/prod **0 vulnerabilidades**, TSC,
  lint y build PASS; los 151 assets coinciden byte a byte con la referencia.
  Pasaron además 904 tests del snapshot upstream. El PR continúa abierto y sin release;
  responsable y fecha de revisión del backport siguen pendientes de confirmación.
- Calidad sobre el WIP: pytest **283 passed/4 skipped** (los cuatro requieren
  `RUN_SUPABASE_INTEGRATION_TESTS=1` contra Supabase live), TypeScript/actionlint/
  shellcheck, credential scan y `git diff --check` PASS; ESLint 0 errores/9 warnings
  existentes. Pytest reporta una deprecación de `PyPDF2`. Estos resultados no congelan
  el candidato ni sustituyen UAT/build final del último byte.
- Cuotas: el responsable eligió avanzar con gateway firmado local. La firma debe
  proteger los RPC Data API directos y el Durable Object debe admitir antes de RPC,
  conservando el JWT del usuario, `auth.uid()`, RLS, RBAC y MFA. No se han creado ni
  ejecutado migraciones, grants o SQL para el gate; requiere JIT exacto separado.
  La admisión Edge de 120/actor/min sigue ratificada; reserve-before-Auth y
  finalizadores in-flight no se debilitan.
- GitHub, lectura autorizada: `desarrollo` está protegida y apunta a
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; colaboradores observados:
  `romelhc95` (admin) y `romelhc95-approver` (write). El único ruleset visible está
  activo, solo restringe updates y da bypass `Always allow` a `romelhc95`; sus
  controles de PR y status checks aparecen desmarcados. La vista clásica queda en
  `Loading...` y el REST de protección responde 401; por tanto, los required checks
  efectivos siguen **sin acreditar**. No se cambió GitHub.
- La suspensión SQL ya aprobada pasó, igual que Pages/workerd y Edge por separado;
  sigue faltando el ensayo integrado Pages + Edge + cookies + bindings + SQL, con JIT
  propio. Los dos artefactos literales de plantilla continúan intactos y excluidos.

Evidencia y tareas/gates de este corte:
[continuación de readiness 2026-10-03](evidencia/h3req1_readiness_continuation_2026-10-03.md)
y [plan integral](operaciones/plan_go_h3req1_local_development_2026-10-02.md). El
WIP sigue sin commit/push/PR; no existe hash final de fuentes/build/resultados. No se
ejecutó ninguna operación Supabase, Cloudflare o GitHub de escritura.

### Corte histórico — remediaciones locales posteriores al acuerdo de baseline

**Último pedido: solo documentación para GO.** El
[plan vinculante](operaciones/plan_go_h3req1_local_development_2026-10-02.md)
En ese corte histórico el plan consolidaba seis gates: UAT final/onboarding (ambos
cerrados localmente en la actualización superior); riesgos y decisión de cuotas;
rollback integrado/recuperación segura; candidato reproducible/atestación/pilares;
CI independiente protegido; paquete exacto PR/pruebas/JIT. Se exige evidencia real,
no PASS históricos ni intención. Clasificar archivos antes de stagear y usar la
estructura de plantilla PR con resultados actuales, sin copiar su evidencia antigua.

**NO-GO integral permanece.** UAT r8 fallida y r10 inconclusa, CI HIGH sin
enforcement acreditado y demás pendientes no se cierran por documentarlos. No se
exigen resultados remotos anticipados para iniciar pruebas: checks del PR son gate
posterior de merge y UAT remota es gate posterior de aceptación Development.
Este pedido no autoriza código, pruebas, commit/push/PR/merge, inventario remoto,
SQL/Auth, secretos/bindings/deploy/rollback ni Certificación/Producción. Siguiente
ciclo funcional requiere `continua` y conserva JIT separado por operación.

**Actualización autoritativa del cierre:** arquitectura/umbrales de cuotas aprobados
localmente; ya implementados y probados en Docker/PG17/workerd/PostgREST, sin writes
remotos. El plan registra transición por expand separado, activación tras Edge
compatible, bindings/secrets por nombre (sin valores) y matriz JIT remota.
Reauditoría focalizada final `ses_f0118bf9cffeK47ubskTUvcYSB`: cero nuevos
HIGH/MEDIUM verificados, sin cierre integral ni cierre del HIGH funcional runtime.

**NO-GO vigente por validación concreta:** UAT workerd r8 FAIL (26/48 casos,
80/144 ejecuciones PASS, 143 capturas, cero retries); r10 sin resultado final,
runner detenido tras exceder dos timeouts de 20 min, staging/capturas preservados.
Se corrigieron manual+rechazo redirects3xx/opaqueredirect, query perdida en slash,
snapshot incompleto y reemisión de cookies request que competía con MFA; estos
cambios no están acreditados por una nueva suite 144/144. Solo SDK escribe cambios
Auth, logout limpia cookies localmente con CSRF sin ampliar Bearer. Smoke no cierra
intermitencia AAL2. Driver ahora conserva progreso/errores/backup y captura acotada.
Siguiente tarea bloqueante: diagnosticar UAT con progreso, remediar/revalidar suite
completa y onboarding; no congelar candidato ni avanzar PR/deploy con UAT fallida.

Últimos checks focalizados: pytest282/4skips/1warning PASS; typecheck web/Edge PASS;
BFF52+6cuotas, SDK26+7redirect, Edge UAT, middleware suspensión y cuotas unitarias
PASS; runtime real DO SQLite25/10admit+restart PASS; PG17r3 ambos modos cadena,
expand/compatibilidad/activación/cuotas/suspensión PASS; actionlint y credential scan
PASS. CI independiente HIGH, ensayo integrado rollback, atestación/pilares del
candidato final, hashes separados y UAT remota siguen pendientes. Sin waiver.

**Cierre integral en ejecución:** cuotas implementadas localmente tras aprobación;
revisión detectó cuatro MEDIUM remediados (legacy RPC, admisión Edge, configuración
antes de writes, contador de excepciones). PG17 r2 ambos modos y wire PostgREST13.0.7
+SDK reales PASS, incluyendo 403 que conserva admisión y 429/Retry-After legacy.
UAT workerd reveló HIGH funcional nuevo: `redirect:error` no soportado en Cloudflare;
Auth falla. Remediar con `manual` y rechazo explícito 3xx/opaqueredirect, sin seguir
Location ni ampliar destinos. Evidencia fallida r4 y parcial r5 preservada; no GO.
Driver de UAT requiere aislamiento de cuotas por ejecución, no solo viewport;
límites permanecen activos dentro de cada caso. Estos cortes no son aceptación final.

**Corrección de objetivo solicitada por el responsable:** terminar un paquete
integral listo para PR y pruebas remotas, en vez de detener la entrega en cierres
focalizados. Pendientes consolidados: arquitectura/cuotas aprobadas e implementadas,
gates Docker completos y UAT del candidato final, revisión/atestación/pilares,
hashes de fuentes/artefacto/evidencia, rollback Pages/Edge seguro ensayado localmente,
bootstrap CI con enforcement acreditado y matriz operativa de pruebas/JIT.
Si el bootstrap requiere PR previo, es prerrequisito protegido de la misma entrega,
no cierre funcional separado. Solo se detiene por aprobación humana requerida,
drift o gate fallido; un PASS aislado no termina el objetivo.
Este pedido autoriza actualización documental, no push/PR/merge/deploy/writes.

**Continuación solicitada:** tareas/gates integrales listados; inspección BFF/Edge
identifica necesidad de cubrir llamadas directas fuera de Pages. Propuesta de cuotas
con Durable Objects interno BFF + controles privados transaccionales de iniciadores
Supabase y umbrales concretos registrada en el plan para aprobación humana local.
Sin implementación de cuotas ni aprobación inferida; no DB ni infraestructura remota.
La decisión de arquitectura/umbrales es el bloqueo inmediato, no un cierre parcial.

El responsable eligió **Aprobar diseño local**: Durable Objects interno BFF +
controles privados Supabase y umbrales presentados. Se autoriza implementación y
pruebas Docker/PG17 del diseño, no operaciones/secretos/infraestructura remotos.
Se continúa cuotas -> rollback artefacto -> validación/UAT/evidencia/revisión integral;
bootstrap y operaciones remotas mantienen JIT. NO-GO integral hasta acreditar gates.

**Actualización del ciclo `Continúa`:** LOW replay recovery y MEDIUM cobertura
in-flight cerrados por reauditoría READ-ONLY `ses_f01f31258ffeIQxqU1tGp9N4xX`.
Metadata aditiva `delivery_method` elegida por servidor antes de Auth; replay
completado conserva respuesta completa y legacy sin metadata mantiene false.
Drill ejecuta completion/failure/reconciliation como service_role tras suspender,
con reservas previas reales, rechazo de nuevos iniciadores y estado/auditoría
verificados. PASS Docker: Edge, typecheck semántico, ambos drills PG17 y pytest
282/4 skipped; diff check PASS. Auditor reejecutó Edge, revisó SQL estáticamente.
Hallazgos cerrados como evidencia interna, no GO entregable parcial;
**NO-GO integral/local/remoto** conservado.
Cuotas, UAT final, artefacto congelado y gates remotos siguen pendientes.

Resultados locales: pytest **282 passed/4 skipped**, SDK interceptado **26**,
BFF **52**, Auth error **7**, Edge happy paths normal/reenvío confirmado/reenvío
no confirmado y replay **3 PASS**, typecheck semántico Edge con SDK **2.109.0 PASS**.
La respuesta exitosa ahora permanece dentro del scope de `reserved`.

PG17: cadena H2 Pro actual -> H3 **PASS** conservando cohorte; cadena de contracción
futura -> H3 **PASS** por separado. Se incorporaron únicamente campos de metadata
Pro acreditada; el fixture reducido no es un dump completo del schema remoto.
No se eliminan roles globales referenciados por otras bases de los gates.

Static Build local completo **PASS** en snapshot Docker aislado
`/tmp/h3req1-ci-approved-pro-20261002` dentro de `studiamatch-h3req1-build`:
`npm ci`, pruebas BFF/Auth/Edge/transporte, typecheck Edge y smoke/build fixture.
Esto no acredita ejecución ni enforcement del CI remoto ni todo el workflow DB.
Allowlists reconciliadas por rutas exactas; inventario JWT y overrides Request/init
ampliados, sujetos a reauditoría independiente.

Rollback compensatorio `db/rollback/h3req1_safe_suspend.sql`: **suspensión segura**,
no restauración de funciones/vistas antiguas. Drills PG17 **PASS** en ambos modos:
idempotencia, permisos, preservación de estado/auditoría/cohorte, exclusión de curso
con evidencia vigente unavailable y completion de invitaciones en curso.
La suspensión degrada temporalmente mutaciones Admin de forma deliberada; no es
prueba de rollback transparente del artefacto remoto ni autoriza aplicación remota.

Reauditoría anterior READ-ONLY: `ses_f01fa8673ffeytyjgOYvnMSYta` (hallazgos
posteriormente cerrados por el ciclo `Continúa` descrito arriba).
Confirma cierre del HIGH Edge por scope y allowlist reconciliada; no nuevos
HIGH/CRITICAL en el delta focalizado. Dos hallazgos abiertos: LOW replay de recovery
devuelve `recovery_sent=false` aunque el envío inicial respondió true; MEDIUM drill
no ejecuta finalización in-flight ni verifica failure/reconciliation tras suspensión.
Los 26 casos de transporte son interceptados: tres usan SDK real, los restantes
helper directo. Typecheck SDK local no acredita runtime Deno/version resuelta Edge.
Rollback remoto NO aprobado: Edge de HEAD enviaba Auth antes de reservar y puede
producir efectos antes de fallar con reserva revocada. No usar ese downgrade como
rollback seguro. Pruebas build/SQL fueron reportadas por sesión principal, no
reejecutadas por auditor. Siguiente ciclo: corregir replay, ampliar drill y verificar
sus gates; requiere `continua`, sin autorización remota implícita.
NO-GO local/remoto preservado: cuotas sin arquitectura aprobada/implementación,
UAT final sobre bytes nuevos, congelación de manifiesto/artefacto, revisión y CI
independiente remoto siguen pendientes. No hubo nuevas operaciones remotas.

### Corte anterior — histórico, supersedido por los resultados anteriores

Último corte funcional parcial: pytest **282 passed/4 skipped**, SDK interceptado
23 escenarios, BFF 52, Edge focalizado y TypeScript PASS. UAT Pages r14 (48/48 casos,
144/144 ejecuciones/capturas) e invitaciones 10/10 son evidencia histórica anterior
al transporte nuevo; no cierran su UAT final. PG17 H3 independiente pasa, pero la
prueba H2 Pro -> H3 encadenada falla. actionlint/shellcheck pasan; el build CI completo
modificado no fue ejecutado. Cualquier PASS de pruebas no cierra los hallazgos de
la reauditoría más reciente.

Bloqueadores de ese corte histórico (no lista vigente):

- **HIGH CI:** no se acreditó un workflow mantenedor instalado/requerido fuera del PR
  modificable. No se consultó GitHub en esta continuación.
- **HIGH Edge éxito:** reauditoría reprodujo HTTP 409/reconciliation_required tras
  Auth y completion exitosos; `reserved` fuera de su scope al construir respuesta.
  Corregir y cubrir happy paths normal/reenvío/replay y typecheck semántico Edge.
- **MEDIUM allowlist CI:** rutas propias del candidato fuera del gate protegido:
  harness encadenado, ESLint config y sistema_db_supabase; reconciliar explícitamente.
- **MEDIUM rate limiting:** sin cuotas propias para BFF/RPC/invitaciones. El
  responsable decidió incluir su remediación en el cierre actual; ya no se difiere.
  Arquitectura propuesta pendiente de aprobación; no existe waiver.
- **LOW inventario JWT:** excepción acotada aprobada e implementada; revisión no
  encontró bypass de origen/ruta/método/redirect. Inventario aún incompleto como
  matriz explícita de identidad/origen/destino/método y falta cobertura Request/init.
- **Baseline drift:** fixture H2 Pro carece de provider_used requerido por H3;
  detenerse para decisión humana, sin columnas ad hoc ni schema remoto inferido.
- **Rollback DB:** falta rollback SQL compensatorio ejecutable y drill; bloquea todo
  deploy/migración remota. El LOW de autorización por `account_status` se corrigió y
  sus dos regresiones PG17 pasan. Reauditoría local read-only encontró los hallazgos
  actuales anteriores; no autoriza ni sustituye gates remotos.

La UAT visual r14 corresponde a un build anterior al cambio de transporte web. No hubo consulta a
GitHub/Supabase, DDL/DML/Auth remoto, push, PR, merge, workflow dispatch, deploy o
promoción. El NO-GO local y remoto se conserva.

### Inicio de continuación Build — decisiones al iniciar, supersedidas por el corte posterior

El responsable solicitó actualizar Obsidian primero y continuar el plan de cierre.
Se preservan Auth/MFA/invitaciones y dos colaboradores: uno aprueba y otro mergea;
no se agrega personal, autoaprobación ni bypass de protección. El WIP original y
evidencias históricas permanecen intactos.

| Tarea | Gate / estado al iniciar este ciclo |
|---|---|
| Actualizar Obsidian y trazabilidad | Plan, estado y evidencia consistentes; no atribuir PASS a trabajo pendiente |
| Excepción JWT acotada | Presentar proyecto/rutas/métodos para aprobación; actualizar atestación solo después. No reimplementar Auth/MFA/invitaciones |
| Rate limiting compartido | Incluido en cierre. Servicio interno Cloudflare/Durable Objects mediante binding es propuesta, no arquitectura aprobada ni infraestructura desplegada |
| Build CI reproducible | Sustituir dependencia de `example.invalid` por fixture local explícito; ejecutar el job completo en Docker y probar ruta estática elegible |
| H2 Pro -> H3 encadenado | Misma base PG17 limpia, sin reset/recreación del schema entre fases. Los harnesses separados no acreditan ese gate |
| Rollback SQL compensatorio | Restaurar funciones/vistas previas sin descartar datos/columnas/auditoría nuevos; drill local, sin reinstalar cohortes retiradas ni reabrir exposición de tokens JS |
| Bootstrap CI independiente | Manifiesto y revisión local; instalación/check requerido efectivos solo con aprobaciones y evidencia remotas separadas. HIGH sigue abierto |
| GO local | Fuentes/artefacto identificados, gates afectados PASS, criterios/pilares/atestación, reauditoría exacta, sin bloqueos pendientes |
| GO Development | Integración protegida y Free/Pages/Auth/Edge/cuotas/UAT/rollback real con JIT por operación; no Certificación/Producción |

La continuación no concede lectura remota, push, PR, merge, deploy, workflow dispatch,
writes DB/Auth, resets ni configuración de protecciones. Ante drift se detiene y
consulta. La aprobación JWT sigue pendiente: no se interpreta este prompt como
ampliación implícita del contrato. El manifiesto anterior precede a esta edición
documental y debe regenerarse al congelar el siguiente candidato.

### Corte posterior — aprobación JWT y bloqueo del baseline encadenado

El responsable aprobó explícitamente `Aprobar cierre` para la excepción JWT acotada
de proyecto/ruta/método presentada. La atestación, AGENTS e inventario se actualizaron;
el transporte local ahora permite solo RPCs allowlisted POST, Auth user GET/PUT,
MFA factors/challenge/verify POST y baja DELETE con UUID, Edge admin-invite POST;
Edge reenvía identidad solo a Auth user GET. API key solo en apikey, redirects
bloqueados, Supabase verifica identidad (forma JWT no autentica). No se rediseñó
Auth/MFA/invitaciones. SDK interceptado 23 escenarios, BFF 52, Edge, TypeScript y
pytest **282 passed/4 skipped** pasan. Falta UAT visual sobre estos bytes y revisión
independiente; el LOW no se declara cerrado por pruebas interceptadas.

CI: se retiró el build previo contra example.invalid; smoke local inicia fixture
verificado y ejecuta build. actionlint y shellcheck pasan, pero el job/build completo
modificado aún no se ejecutó; no declarar PASS funcional CI.

La nueva prueba `tests/sql/h3_from_h2_pro_pg17_harness.sql` encadena H2 Pro -> H3
sin reset intermedio del schema. Se ejecutó en servidor PG17 nuevo aislado porque
el harness H2 elimina roles a nivel servidor. **FAIL confirmado:**
`20260828_h3_admin_course_queue_view.sql` requiere `courses.provider_used` ausente
en el fixture H2 Pro. Existe `20260505_add_provider_tracking.sql`, pero no se ha
acreditado el schema/ledger remoto actual. Se detiene el ciclo ante drift; no añadir
columnas ni inferir que el modelo local equivale a Pro. Pedir decisión de lectura
remota acotada o reconstrucción exclusivamente versionada con límite explícito.

Rollback compensatorio y cuotas no implementados/ensayados. NO-GO local/remoto;
ninguna operación remota ejecutada, WIP y evidencia previa preservados.

Reauditoría READ-ONLY `ses_f02149ccbffeOndfPb8FmeEHoT`: transporte acotado correcto
sin bypass confirmado; HIGH Edge éxito reproducido, MEDIUM allowlist CI, LOW
inventario JWT y LOW contradicciones documentales. Se consolida este corte como
actual; cortes previos quedan históricos. El ciclo está detenido por baseline drift
y por esos hallazgos pendientes; no hubo remediación adicional de código en auditoría.

### Lectura Pro autorizada — baseline remoto actual difiere del modelo contraído

El responsable aprobó lectura exclusiva de metadatos/schema/grants/constraints y
ledger de Pro. Se confirmó primero URL `https://xwhtiqmboljkshrtviyw.supabase.co`.
Sin credenciales ni datos operativos, sin DDL/DML/Auth/deploy:

- `courses.provider_used`: existe, text nullable, default mock.
- `courses.is_mock_data`: boolean nullable default true; `seniority_level`: varchar
  nullable default Mid. Metadatos actuales no equivalen al fixture reducido.
- `private.h2_legacy_public_course_cohort`: **existe** en Pro. El baseline local
  `h2_pro_pg17_harness.sql` que retira cohorte representa contracción ensayada,
  no acredita el estado actual remoto. No retirar ni reconstruir datos de Pro.
- Ledger nativo list_migrations leído; por sí solo no acredita la totalidad de
  SQL aplicado fuera de ese ledger. No inferir ausencia de H2 por nombres no listados.

Nueva discrepancia de baseline: detener antes de cambiar fixture/secuencia. Proponer
prueba encadenada desde modelo fiel al Pro actual (cohorte presente) y conservar
separadamente ensayo de contracción (cohorte ausente). Requiere decisión humana de
baseline, no DDL remoto. Rollback y cuotas pendientes; HIGH Edge/CI abiertos; NO-GO.
Toda mención anterior de ausencia de consultas remotas describe su corte histórico;
esta lectura acotada es la única operación remota de esta continuación.

### Decisión de baseline — continuación aprobada

El responsable confirmó usar Pro actual como autoridad y corregir el fixture local:
cohorte presente y provider_used text nullable default mock. Conservar aparte el
ensayo de contracción futura sin cohorte. No modificar Pro ni retirar cohortes por
el hecho de que el harness anterior las retiraba. Este acuerdo desbloquea corrección
local del modelo y revalidación encadenada; no concede nuevas operaciones remotas.
Se continúa remediación Edge happy paths, inventario/CI/build/rollback locales;
cuotas y bootstrap siguen pendientes, NO-GO preservado.

## Historial de preparación del worktree — el corte actual está arriba

### Ciclo autorizado `Continúa` — remediación focalizada

Tareas: persistir el método de entrega antes de Auth y recuperarlo solo en replay
completado; ampliar drill con reservas previas a suspensión y llamadas completion,
failure y reconciliation bajo service_role después. Gates Docker: Edge UAT/typecheck,
PG17 ambos modos, contratos y reauditoría. Sin operaciones remotas.
Compatibilidad: metadata aditiva, registros anteriores sin método conservan false;
no inferir recovery por estado Auth actual. Rollback del artefacto remoto pendiente;
suspensión segura vigente y NO-GO preservado.

Los párrafos siguientes preservan el preflight y el traslado inicial, no describen
el estado vigente. Sus pendientes locales de UAT/PG17/lint fueron actualizados por
la evidencia más reciente de las líneas 20-51; los gates remotos siguen abiertos.

La lectura de GitHub confirmó `origin/desarrollo@4eb4d877a50b012bb630a129bd0c74482c33be9c`
(protegida). El checkout WIP comparte base `97168646b2a6bbd8e59f6d704446759303e11e64`
y estaba 27 commits detrás/5 delante; solo se actualizó el ref local mediante fetch
read-only. El snapshot externo `verified5` registró 1.707 entradas locales, ninguna
staged. El WIP permanece en el checkout original y no se alteró durante el port.

La revisión del plan fue incorporada documentalmente: respaldo recuperable con
hashes previo al traslado, reconciliación por deltas/merge-base sin sobrescribir
archivos completos, revisión del baseline Pro y migraciones, bootstrap de CI
externamente protegido sin circularidad y validación del candidato exacto. Las 24
rutas son solapamientos, no conflictos confirmados. El HIGH conserva su estado
abierto hasta revisión/evidencia; un defecto local confirmado bloquea GO local y la
configuración remota pendiente se registra aparte, sin reclasificación automática.
El MEDIUM diferido no tiene waiver. Se creó y verificó un respaldo local externo;
credential scan del árbol y archivos nuevos candidatos y `git diff --check` pasaron.
Con autorización exacta se creó `/home/romel/src/studiamatch-h3req1-sync-20261002`,
branch local `feat/h3req1-sync-20261002`, desde `origin/desarrollo@4eb4d877…`. En el
corte de creación, el worktree estaba limpio y no había recibido deltas del WIP.

La revisión read-only encontró 43 rutas tracked divergentes y 1.652 archivos nuevos
en el WIP; 1.488 son evidencia histórica/visual. Los artefactos/capturas masivas y
16 rutas locales/configuración se excluyeron del candidato. El reporte UAT y el
documento histórico que el WIP borraba se conservaron desde `origin/desarrollo`; el
PR template remoto también se preservó. Las cuatro migraciones se portaron, pero su
compatibilidad con el baseline Pro no se ha validado.

Se portaron deltas revisados al worktree aislado mediante merges de tres vías y
selecciones manuales BFF/editoriales. Se retiró el fallback de Preview compilado en
la Edge Function: invitación, recuperación y CORS dependen ahora de URLs/allowlists
configuradas explícitamente, con fallo cerrado. Falta validar la matriz local. El
check `Protected Workflow Integrity` propuesto no está acreditado como requerido en
remoto; HIGH CI sigue abierto. Aún no se ejecutaron validaciones funcionales sobre
el candidato integrado. Las cinco entradas antiguas stale/prunable siguen intactas;
el estado permanece **NO-GO**.

La transición permanece: `expand` implementado y UAT mock Pages local PASS;
compatibilidad real de cuentas legacy en producción pendiente; `deploy` requiere JIT separado;
`contract` solo tras estabilidad productiva; rollback remoto debe verificarse antes
de promoción y nunca vuelve a tokens accesibles por JavaScript.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Remediación editorial y auditoría — 2026-10-01

El [plan de remediación de ingreso, corrección y auditoría](operaciones/plan_remediacion_ingesta_editorial_auditoria_2026-10-01.md)
registra el diagnóstico de nuevos cursos, overrides manuales, disponibilidad,
historial Admin y rutas estáticas. El usuario comunicó conformidad explícita del
cliente sin crear un contrato nuevo; quedó registrada en la atestación sanitizada
[CLIENT_PLAN_ACCEPTED_LOCAL_EXECUTION](evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md),
que habilitó implementación/validación local en Docker/PG17. La evidencia
[del ciclo local](evidencia/h3_course_editorial_local_cycle_2026-10-01.md) registra
PG17, contratos, typecheck, lint, static smoke y credential scan en PASS. El
estado del subciclo es `NO-GO_LOCAL_ACCEPTANCE_GAPS_PENDING`: faltan UAT
visual/autenticada del editor nuevo con MFA y una ruta estática de curso nuevo con
datos elegibles. El responsable decidió no requerir clasificador automático en este
ciclo; se mantiene revisión Admin de faltantes/diferencias. La UAT H3 global
permanece `NO-GO`. No se aplicó DDL/DML remoto, no se ejecutaron writers ni se hizo
deploy, push, PR, merge o promoción. Cualquier paso remoto necesita aprobación/JIT
independiente; la identidad visible en el encabezado se registra abajo como cambio
UI local separado.

## Decisiones de diseño BFF y disponibilidad — 2026-10-01

El responsable atestó que el alcance BFF/HttpOnly está alineado con la fuente
privada del cliente y confirmó que se registre en la atestación sanitizada. Para
sesiones legacy se requiere expirar/limpiar el token del navegador y volver a
autenticar la **misma cuenta** con MFA; no canjear tokens legacy, crear otra cuenta,
reinvitar ni repetir onboarding. También autorizó la excepción estrecha para que el
BFF envíe el JWT de usuario como Bearer solo a RPCs allowlisted de Supabase Data API;
publishable key permanece en `apikey`, y no se usa service role como identidad.
La regla HTTP quedó actualizada localmente; el inventario y sus contratos de prueba
se completarán junto con el BFF.
La evidencia de disponibilidad tendrá vigencia
máxima **global de 90 días calendario desde `observed_at`**; `valid_until` no puede
exceder ese límite y evidencia ausente, inválida o vencida permanece `unknown`.
Este ciclo no requiere clasificador semántico automático: Admin revisa faltantes y
diferencias pipeline/override y decide según su rol. La adenda quedó incorporada
al archivo sanitizado local, todavía sin commit Git, en
[la atestación sanitizada](evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md)
y el [borrador BFF/HttpOnly](operaciones/borrador_bff_httponly_admin_h3req1_2026-10-01.md).
Estas decisiones habilitan diseño e implementación locales, no operaciones remotas.

## Identidad visible en encabezado Admin — 2026-10-01

El responsable aceptó que el panel muestre el correo de la sesión Auth en vez del
distintivo de rol; la atestación sanitizada se actualizó sin agregar username ni
modificar RBAC. La comprobación read-only en Supabase Free confirmó una cuenta Auth
única, correo confirmado, contraseña configurada, creación en la fecha UTC,
inicio de sesión registrado, invitación aceptada, TOTP verificado y membresía
`admin` activa/`ready`, sin guardar PII en la evidencia.

La implementación local obtiene el correo con Supabase Auth; el rol sigue
controlando autorización. Tras la autorización puntual se actualizó Next a `16.3.8`,
se retiró la opción ESLint obsoleta de `next.config.js` y se fijó `shadcn@4.21.1`;
el contenedor `studiamatch-dev` está `running/healthy` y ambas rutas `/admin/login/`
y `/admin/` responden HTTP 200. La vista pública de login pasó inspección visual
aislada a 1440×900 y 390×844, sin errores de consola ni overflow horizontal; no se
inició sesión ni se probó el encabezado autenticado. TypeScript y 11 contratos
focalizados pasan; ESLint no tiene errores y conserva 9 warnings; credential scan
(561 archivos) y `git diff --check` pasan. Evidencia:
[ciclo de identidad Admin](evidencia/h3_admin_email_header_local_cycle_2026-10-01.md).

La remediación local de dependencias completó 15 overrides acotados por rango/major
en `web/package.json` y su lockfile, incluyendo los paquetes con advisories previos.
El rebuild local autorizado instaló 625 paquetes y reportó 0 vulnerabilidades.
`npm audit --include=dev` y `npm audit --omit=dev` reportan ambos 0 (0 HIGH/CRITICAL).
TypeScript pasa; ESLint tiene 0 errores y 9 warnings; pasan 28 contratos/pruebas
focalizados, credential scan y `git diff --check`. El `@security-auditor` read-only
no identificó hallazgos confirmados con la evidencia disponible y advierte riesgo
residual de compatibilidad por overrides transitivos; un audit limpio no garantiza
seguridad absoluta. No se ejecutó `npm audit fix`.

Docker está `running/healthy`, reinicios 0; Next `16.3.8`, shadcn `4.21.1`, marcador
de dependencias alineado con los hashes de ambos manifests, y `/admin/login/` y
`/admin/` responden HTTP 200. No se hizo build estático durante esta remediación.
`web/out` permaneció idéntico: 180 archivos, 2,461,143 bytes, SHA-256 del árbol
`0dab4eef13500534ba07c7ccae0eb475bf08a548574f6d45d8e83d60bbcbbe98`. El build
estático aislado anterior compiló Next y generó 17/17 páginas, pero usó
`example.invalid`, cayó al default `/courses/pucp/estudios-generales` y no acredita
el catálogo remoto Free; sus 124 archivos se preservaron fuera del repo.

El NO-GO de aceptación visual/autenticada sigue vigente porque no se probó el header
con sesión ni el editor con MFA. No se aplicaron writes Supabase/Auth, migración,
deploy, push, PR, merge ni promoción; H3REQ1 remoto/Free continúa `NO-GO` y requiere
aprobación independiente para cada gate restante.

## Preflight local para PR H3REQ1 — 2026-10-01

Se ejecutó una batería offline en snapshot Docker temporal, excluyendo secretos de
entorno (solo se incluyó `.env.example` como fixture contractual), artefactos
personales y `web/out`; el checkout no se montó escribible. Pasaron 184
tests Python seleccionados, sintaxis/compilación Python, Node UAT syntax, H2 writer
scan, TypeScript, ESLint (0 errores/9 warnings), npm audit full y `--omit=dev` (0
hallazgos), build normal con placeholders y H2 mock smoke. El build de placeholder
falló el fetch esperado a `example.invalid`, generó 17/17 páginas y cayó al fallback
`/courses/pucp/estudios-generales`; no acredita ruta para curso nuevo elegible.
Actionlint y shellcheck no estaban disponibles en la imagen y quedan pendientes de
CI. Con autorización JIT local acotada pasaron los harnesses `h2_pg17_harness.sql`,
`h2_pro_pg17_harness.sql` y `h3_pg17_harness.sql` en PostgreSQL 17.11 efímero; el
error del guard de rollback en H2-Pro fue el rechazo negativo esperado. El
contenedor temporal fue retirado. `studiamatch-dev` sigue saludable y `web/out`
conserva 180 archivos/2,461,143 bytes y el hash ya registrado arriba. Evidencia
detallada: [preflight H3REQ1 de este ciclo](evidencia/h3req1_development_remote_cycle_2026-09-26.md#continuacion-del-ciclo-preflight-y-revalidacion-2026-09-26).

El PR queda **BLOQUEADO**: las referencias locales muestran 22 commits detrás y 4
delante de `origin/desarrollo` (sin fetch/rebase), y el árbol combina 24 archivos
versionados modificados más WIP sin seguimiento; no se stageó ni descartó nada.
La revisión de seguridad read-only encontró 1 HIGH, 3 MEDIUM y 2 LOW. El HIGH es el
cambio candidato de sesión de `sessionStorage` a `localStorage`; el usuario eligió
usar BFF con cookie HttpOnly. El alcance ya está atestado, pero la implementación y
revisión de seguridad siguen pendientes y no hay waiver. El workflow permite que
el PR modifique su propio gate de paths; además quedan hallazgos de concurrencia de
invitaciones y el control de vigencia aún no aplicado para evidencia de
disponibilidad. No hay waiver formal; la política ya definida es 90 días globales
desde `observed_at`.

Resultado: `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. No se abrió PR ni hubo push,
Free/Preview, Auth, DDL/DML remoto, deploy o promoción. La atestación sanitizada
acepta el alcance BFF para trabajo local; el borrador técnico sigue sujeto a validar
adapter/runtime. Próximo gate: implementar y revisar localmente BFF/HttpOnly, cerrar
controles del workflow/invitación/redirect/body y aplicar la política de 90 días;
después completar UAT y ruta estática elegible, reducir/acotar WIP y actualizar el
baseline sin alterar trabajo ajeno. Push/PR y cada operación remota requieren
aprobaciones separadas.

## Ciclo Development/Free 2026-09-26

La evidencia canónica de este ciclo es
[h3req1_development_remote_cycle_2026-09-26.md](evidencia/h3req1_development_remote_cycle_2026-09-26.md).
El PR #499 está mergeado en `desarrollo` en
`c56f1cb5a0dac722a92e7ef3a6000a9bb2d6b4a9`. Las acciones remotas autorizadas de
este ciclo se limitaron a Free/Development.

El estado continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. La autorización
JIT Free/Development para los dos deltas exactos `20260925` fue consumida: ambos
quedaron registrados y validados en Free, por lo que el drift específico de
H3-001 queda corregido. El 2026-10-01 se acreditó un escenario completo de alta
Admin/invitación/onboarding en Free mediante reporte del usuario y comprobación
read-only; ese escenario H3-002 queda `PASS`, aunque el gate integral sigue
`PARTIAL` hasta reconciliar evidencia de ejecución/correo. H3-003/H3-004 siguen
`BLOCKED` hasta ejecutar sus autorizaciones y pruebas remotas separadas. En el
ciclo previo se aplicó la plantilla Auth de recovery, se publicó el Preview
actualizado y se ejecutó el recovery real del admin existente; no se ejecutaron usuarios adicionales,
cleanup, rollback, push, merge ni promoción. La autorización JIT Edge permitió
desplegar el artefacto aprobado como `admin-invite` versión 4, `ACTIVE` y
`verify_jwt=true`. El smoke autenticado de invitaciones, RBAC y onboarding sigue
pendiente de su autorización y UAT separadas.

## Resumen H3 En Lenguaje Simple

### Qué se intenta construir

H3 agrega una zona privada para que personas autorizadas revisen y corrijan la
información de los cursos. Hay dos tipos de personas: `user`, que completa datos
faltantes, y `admin`, que además aprueba cambios y administra usuarios. El acceso
debe usar una segunda comprobación de seguridad y la zona privada no debe aparecer
en la dirección pública normal.

### Qué significa el estado actual

`H3_PR_DEVELOPMENT_READY_LOCAL` acredita **GO técnico local**, no cierre
contractual. El ciclo read-only 2 del 2026-09-24 mantiene
`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`: Free ahora registra las
migraciones 03A/03B y los hardenings 20260924, pero Pro sigue sin migraciones H3,
tablas ni RPCs consultables. También faltan UAT
remota completa, hostnames por ambiente, Certification y la transición
`deploy -> contract`. La UAT canónica local conserva 47/47 casos y 141/141
ejecuciones PASS con cero reintentos.

### Qué se corrigió desde la prueba fallida anterior

La corrida inicial falló porque las páginas privadas no aparecían en la copia
servida. El programa de pruebas se corrigió para esperar a que la página terminara
de cargar antes de interactuar (espera de hidratación), se validó el bloqueo
público `studiamatch.com/admin/ → 404` sobre un servidor de perímetro real
(`static-server.js`) y se corrigió un selector de prueba.

### Qué acredita la evidencia actual

- UAT canónica `h3_local_uat.mjs` regenerada el 2026-09-02: **`47/47` casos y
  `141/141` ejecuciones PASS, 141 screenshots, 0 retries**, evidencia en
  `.context/evidencia/h3-expanded/`.
- Build normal y `build:mock` ejecutados en Docker el 2026-09-03: compilación
  exitosa y rutas `web/out/admin/{index,login,edit,users}/index.html` presentes.
  El waiver de static export queda superseded para este candidato.
- Suite CI-local seleccionada: 142 tests PASS; TypeScript PASS; lint sin errores
  (9 warnings históricos); `py_compile`, credential scan, actionlint, shellcheck,
  mock smoke y `git diff --check` PASS. H2/H2-Pro/H3 PG17 PASS; el harness H3
  termina en `h3_pg17_harness_ok` e incluye regresión A6/A13.
- La corrida completa indiscriminada `pytest -q` no es un gate válido en este
  checkout porque recolecta worktrees históricos montados bajo `local/worktrees/`
  y tests de integración que requieren entorno; produjo 540 errores de colección.
  El PR usa el conjunto versionado del job `python-check` y documenta esta
  exclusión.

### Qué resolvió el ciclo de corrección local (2026-09-02) y la sincronización documental (2026-09-03)

El ciclo descrito en [Siguiente Gate](#siguiente-gate) eliminó los bloqueadores
locales que la auditoría de readiness había identificado en CI, contratos DB, MFA
local, UAT/evidencia y rollback; la sincronización del 2026-09-03 incorporó el
delta A6/A13 y separó explícitamente la evidencia remota parcial:

1. `security-audit.yml` corregido (YAML válido), allowlist H3 explícita y
   `db-gate` con harness H3 en PG17; gate emulado localmente `GATE_OK`.
2. Migración `20260902_h3_pr_contract.sql`: lector efectivo de valores y gate de
   publicabilidad; seed idempotente con categorías para los 30 cursos.
3. MFA: `admin-auth.ts` y login muestran secreto/QR y resuelven `aal` real sin
   forzarlo; retirado el spec UAT duplicado.
4. Perímetro 3002 con `Host` mapping correcto (`/admin/login` 200 en admin
   origin, `/admin/` 404 en `studiamatch.com`).

### Qué sigue ahora

Commit + push + PR protegido a `desarrollo` quedaron **autorizados por
instrucción humana separada** y se ejecutan con la plantilla
`.github/pull_request_template.md` llena con resultados reales del ciclo.
Permanecen como gates remotos posteriores y separados: `security-audit` en
GitHub y revisión del PR, aplicación/revalidación de `20260903` en Free,
configuración Auth, Cloudflare restante, promoción a `certificacion`, merge y
deploy. No se ejecuta ninguna de esas acciones sin su aprobación.

### Auditoría Final De Cierre H3REQ1 (2026-09-23)

El documento canónico es
[H3REQ1 Closure Review Final](hitos/h3req1_closure_review_final_2026-09-23.md).
La decisión es `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`.

- MFA fue retirado del gate de aceptación por decisión de alcance: la prueba es
  compleja y no bloquea autenticación administrativa existente, RBAC,
  invitaciones, onboarding, edición, ownership ni perímetro. El MFA/`aal2`
  existente se conserva como compatibilidad y mejora evolutiva.
- La evidencia local permanece PASS: core H3 47/47 y 141/141, builds,
  contratos, PG17, Edge 03A, DB 03B y Mock UAT-02.
- La evidencia remota permanece parcial: `admin-invite` está ACTIVE con
  `verify_jwt=true`, pero las migraciones 03A/03B no aparecen en los inventarios
  remotos revisados; el preview de Development devuelve 404 para callback,
  aceptación y setup de password.
- No se autoriza promoción `desarrollo -> certificacion -> main`, deploy, merge,
  push ni writes adicionales con la evidencia actual.

### Diccionario mínimo

- `GO`: evidencia suficiente para pasar al siguiente control; no significa publicar.
- `NO_GO`: hay fallas o evidencia insuficiente; se debe corregir y volver a probar.
- `build`: proceso que convierte el código en las páginas que se pueden servir.
- `UAT`: prueba que usa la interfaz como lo haría una persona.
- `PASS` / `FAIL`: comprobación aprobada / comprobación fallida.
- `mock`: imitación local de un servicio real, usada para probar sin tocar internet.
- `JIT`: autorización humana puntual para una acción concreta y sensible.
- `PR`: solicitud para revisar cambios antes de integrarlos.

## Pilares Transversales Obligatorios

Todo desarrollo futuro del producto debe preservar continuamente funcionalidad,
escalabilidad, seguridad, mantenimiento, calidad y rendimiento. Ningun hito, task o
requerimiento puede cerrarse sin validar estas premisas frente al alcance
ejecutado.

Para cualquier nuevo desarrollo con requerimiento cliente, antes de iniciar y al cerrar un hito o task vinculado a un requerimiento se debe validar criterios de aceptacion contra el documento privado del cliente mediante atestacion sanitizada versionada.
El documento privado no se versiona y no se expone en PRs;
la evidencia versionada solo registra el identificador de fuente, resultado y
trazabilidad.
Si este gate documental falla, no se puede ejecutar codigo, DB, UI, pipeline ni
PR del hito siguiente hasta corregir la atestacion sanitizada.

Todo cambio funcional, DB, UI, pipeline o despliegue debe incluir una transicion
transparente obligatoria: `expand -> compatibilidad -> deploy -> contract`.
Durante construccion y promocion se debe preservar el comportamiento legacy
necesario para que la aplicacion siga funcionando; luego de estabilizar en
produccion se debe retirar la funcionalidad legacy y dejar activo el nuevo
contrato solicitado. Ningun hito, task o PR puede cerrarse ni promoverse sin
documentar compatibilidad, contraccion, rollback y evidencia de no degradacion
funcional.

Todo prompt futuro de desarrollo queda bajo `PROMPT_RETROALIMENTADO_REQUIRED`
segun [Estandar De Prompts Retroalimentados](operaciones/estandar_prompts_retroalimentados.md).
Un prompt retroalimentado mantiene un ciclo de analizar, implementar, validar,
revisar, convertir cada fallo, hallazgo, drift o gate incompleto en tareas,
corregir y revalidar hasta cumplir sus criterios de GO. No se declara GO por
intencion, implementacion parcial o pruebas locales cuando el alcance exige
evidencia remota. Si se requiere JIT, push, PR, merge, deploy,
workflow_dispatch, Supabase writes, ramas protegidas o acciones destructivas,
la ejecucion se detiene y se pide aprobacion humana separada con opciones
concretas, recomendacion y consecuencias. Cada aprobacion recibida obliga a
reevaluar estado, actualizar el plan y continuar desde el gate detenido. El
cierre exige evidencia canonica, criterios cliente, pruebas completas,
revisiones especializadas y ausencia de hallazgos HIGH/CRITICAL. No se pueden
ocultar fallos como historicos o fuera de alcance sin demostrar baseline; cada
waiver requiere causa, evidencia reproducible, owner, riesgo, vencimiento y
aprobacion humana.

Todo PR debe usar la plantilla versionada `.github/pull_request_template.md`.
Antes de abrir o actualizar un PR se deben ejecutar las validaciones necesarias
para completar sus secciones con resultados reales. La plantilla no se llena con
intenciones, placeholders ni omisiones silenciosas; toda validacion no aplicable
o pendiente debe indicar causa, riesgo residual y owner.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Redefinicion de flujo simple | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Flujo simplificado validado en `desarrollo`, `certificacion` y `main`; preservado como historia no ejecutable. |
| `F11` | H3REQ1 ampliado: campos, invitaciones y hostname; MFA evolutivo fuera del gate | `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` | GO técnico local preservado; UAT remota, 03A/03B remoto, hostnames por ambiente, Certification y contract pendientes. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 es el cutoff contractual de Hito 1. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Evidencia tecnica historica preservada; no ejecutable. |
| `F10.9` | `SUPERSEDED_BY_O0_B` | WP2B queda superseded; PR #413 cerrado sin merge y excluido. |
| `F10.10` | `HISTORICAL_NON_PROMOTABLE` | M3 reader/DDL queda congelado; no autoriza DDL/DML ni payloads. |
| `F10.11` | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Reemplaza WP/digest/Context Graph por flujo simple protegido; el soporte temporal fue retirado al recibir GO documental. |

## Bases Vinculantes

| Concepto | Valor |
|---|---|
| Requerimiento | `REQ-EST-001` |
| Cutoff contractual Hito 1 | PR #291 / `64e4ed895d43121c5683e26a355993f18e528a5c` |
| Baseline tecnico | PR #327 / `main@ad89e8ab9575b37476502d6062e22c044ad6447b` |
| Tree tecnico | `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| Autoridad funcional | `desarrollo@9f163c2c5f8dc54b4986ce75ef1d5c69a740bedf` |
| Certificacion preservada | `certificacion@33b1c9ec3c49117c2020860d5850d9d67988f836` |
| PR #413 | `CLOSED_NOT_MERGED_EXCLUDED`, head `4461f13c79ac893cb428074a729d75140056557b` |
| Archives Etapa 1 | `archive/post-h1-desarrollo-20260820-9f163c2`, `archive/post-h1-certificacion-20260820-33b1c9e` |
| Desarrollo canonico O2 | `desarrollo@a2c97ec17aabc790b656d6db1b16bdc95f0af1b2` |
| Certificacion canonica O2 | `certificacion@4e7e41a9fac08e657308849701b4b1f70b994e3b` |
| Tree canonico O2 | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-003](hitos/hito_003.md).
- Tarea H3: `TASK-H3-001` en el backlog canónico versionado: `backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md`.
- Subfase tecnica activa: `F11`.
- Work package activo: `NONE_SUPERSEDED`.
- Work package completado: `NONE_APPLICABLE`.
- Gate técnico local: `H3_PR_DEVELOPMENT_READY_LOCAL`; gate de cierre vigente: `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`.
- UAT canónica histórica: `47/47` casos y `141/141` ejecuciones PASS con 141
  screenshots y 0 retries, evidencia en `.context/evidencia/h3-expanded/`. La
  regresión A6/A13 del delta `20260903` fue revalidada separadamente en PG17.
- Build normal/mock revalidado en Docker: PASS; rutas admin exportadas presentes.
  El waiver de static export queda superseded para el candidato actual.
- Gates reejecutados en Docker: suite CI-local 142 PASS; TypeScript PASS; lint 0
  errores y 9 warnings históricos; py_compile PASS; credential scan PASS;
  `git diff --check` limpio; actionlint/shellcheck PASS; H2/H2-Pro/H3 PG17
  `h3_pg17_harness_ok` (incluye regresión A6/A13);
  gate `protected-paths` emulado `GATE_OK`. `pytest -q` global indiscriminado no es
  válido por recolectar worktrees históricos y tests de integración fuera del gate,
  y produjo 540 errores de colección.
- Auditorías especializadas del ciclo previo quedaron resueltas para el alcance
  local. JIT-A remoto tiene `20260903` aplicado en Free y A6/A13 corregidos; JIT-DEV
  dejó el ambiente limpio después de probar usuarios/factores temporales. JIT-B
  valida el perímetro y membresía Cloudflare, pero la UAT administrativa completa
  debe usar el deployment/preview correcto por ambiente; E2/E5/E6/E7 no se cierran
  contra `admin.studiamatch.com` mientras este siga asociado al proyecto productivo.
- Commit + push + PR protegido a `desarrollo` quedaron **autorizados por
  instrucción humana separada** y se ejecutan con la plantilla de PR.
- Gates remotos posteriores y separados: UAT administrativa por ambiente, proyecto/
  artefacto Pages admin separado, políticas Access por ambiente, 404 público estable,
  promoción a `certificacion`, merge y deploy. No se ejecutan sin su aprobación.

### Matriz de avance H3REQ1 ampliado

Los porcentajes son estimaciones separadas: implementación no equivale a aceptación; validación exigida solo por evidencia ejecutada y reproducible. La UAT local acredita el cierre local. Development remoto sobre Free valida actualmente el contrato A6/A13 y el entorno de datos; la UAT administrativa/Pages/Access debe ejecutarse contra el deployment correcto de la rama antes de certificar.

| Criterio | Implementación | Validación verificable | Bloqueo principal |
|---|---:|---:|---|
| H3-CA4 local | 78.7% provisional | GO técnico local | `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`; porcentajes previos conservados solo como estimación, no cierre contractual. |
| H3-CA4.1 Auth/RBAC | 90% | 85% | UAT local cubre RBAC y negativos; Auth real pendiente de JIT. |
| H3-CA4.2 Ownership | 85% | 75% | 13 campos y `missing_fields` cubiertos por UAT; falta entorno real. |
| H3-CA4.3 Transporte independiente | 60% | 40% | Fixture E2E diferenciando cuatro campos validado local; falta entorno real. |
| H3-CA4.4 Cola | 85% | 70% | Paginación, cursor y filtros cubiertos por UAT; falta entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | Mutaciones admin y locking cubiertos por UAT; falta entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Auditoría append-only cubierta por UAT; falta entorno real. |
| H3-CA4.7 MFA/`aal2` (fuera del gate) | Evolutivo | No bloqueante | Implementación existente conservada como compatibilidad/mejora evolutiva; no se requiere Auth real para cerrar H3REQ1. |
| H3-CA4.8 Membresías/invitaciones | 85% | 55% | Gestión, último admin, Edge 03A y DB onboarding 03B cubiertos localmente; falta Auth/frontend real y UAT remota. |
| H3-CA4.9 Hostname/perímetro | 60% | 40% | Perímetro Access y 404 público parcial; falta separar el deployment admin por ambiente y validar cada hostname contra su SHA. |
| H3-CA4.10 Convergencia Pro/Free/local | 55% | 35% | PG17 y Free validados; falta diff completo/remoto con Pro como baseline y configuración por ambiente. |
| H3-CA4.11 UAT/artifacts | 100% estructural | 55% contractual | UAT canónica 47/47 y 141/141 PASS con 0 retries regenerada el 2026-09-02; evidencia autocontenida en `.context/evidencia/h3-expanded/`; falta UAT real en Free/Certification. |
| **Promedio simple** | **78.7% provisional** | **No aplica como cierre** | **`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`; UAT administrativa por ambiente, 03A/03B remoto, separación Pages/Access y Certification pendientes.** |

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `REDEFINED_ACTIVE_AFTER_H2_H3` | `TASK-H1-001` |
| `HITO-002` | `CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN` | `TASK-H2-001` |
| `HITO-003` | `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` | `TASK-H3-001` |
| `HITO-004` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | `TASK-H4-001` |
| `HITO-005` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | `TASK-H5-001` |

## Activacion Documental

| Etapa | Estado | Evidencia |
|---|---|---|
| Baseline local | `COMPLETED` | `origin/main@9b486146962bd2a092acfd649fdcf716e922de89` |
| WIP previo | `DISCARDED_BY_AUTHORIZATION` | No se preserva WIP fuera del baseline. |
| Flujo simple | `DEPLOYED_TO_MAIN` | PR #451 a `desarrollo`, PR #452 a `certificacion`, PR #453 a `main`. |
| GO documental | `RECEIVED` | Pedido humano: aplicar actualizacion documental completa y retirar soporte temporal. |
| Soporte temporal raiz | `REMOVED` | `REDEFINICION.md` eliminado definitivamente; no debe recrearse. |
| Plan vinculante | `MOVED_TO_OBSIDIAN` | [Plan vinculante nuevo pedido](operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md). |
| Acciones remotas | `FLOW_NORMALIZED` | Nuevos cambios siguen PR protegido `desarrollo -> certificacion -> main`. |
| CI/CD DB Sync Pro | `H2_VERIFY_NO_OP_APPLY_GATE_FIXED` | Workflow `db-sync-to-pro.yml` ajustado en PRs #480/#481 para que el job `Apply pending migrations` tenga exito como no-op bajo `operation=verify` cuando no hay migraciones pendientes, permitiendo generar el artifact H2 requerido por `security-audit`. |
| Base de datos | `PRO_EXPAND_APPLIED_AND_VERIFIED` | DDL Free inicial, forward-fix, remediacion Security Advisor, backfill editorial, seed, fix de vista y compatibilidad legacy aplicados/verificados en Supabase Free. El manifiesto `h2-expand-compat` fue aplicado y verificado en Pro con backup/PITR verificado; baseline elegible productivo `224`, evidence canonico del run `33143730910` y rerun `33188932351` success, advisors sin hallazgos HIGH/CRITICAL. |
| Evidencia cliente | `GRADE_A_CLIENT_SOURCE_VALIDATED_H2_CERTIFICACION` | Acta ejecutiva y matriz H2 con veredicto, metricas verificables, validacion contra `SRC-REQ-002` via adenda sanitizada, PRs #458/#459/#460 mergeados y QA read-only definida. |
| QA certificacion previa | `PASS_CERTIFICATION_READ_ONLY_QA` | [QA H2/H3 read-only](operaciones/h2_h3_certification_readonly_qa.md) ejecutada antes de la compatibilidad legacy: suite `108 passed`, build/static smoke PASS, vista publica sin privados y advisors sin bloqueantes H2. |
| Compatibilidad Desarrollo | `MERGED_TO_DESARROLLO_READY_FOR_CERTIFICATION_PROMOTION` | PR #466 mergeado a `desarrollo` en `e8376035d8d5c3e1b7893cbb1ede14f735ccd05d`; post-apply Free: `227` cursos legacy elegibles, `227` en cohorte, `227` en `courses_public_effective`, `0` faltantes y `0` inesperados. Preview final `af2ac376` valida Home, detalle, comparador, HTML inicial correcto, bundle sin `ratings`/`reviews` y rutas relacionadas `200`. |
| Compatibilidad Certificacion | `MERGED_AND_DEPLOYED_STABLE` | PR #467 mergeado a `certificacion` en `2d499324bb21e750d9bc7c94cb80e7a193062b50`; deployment `4cc2e34c`; checks verdes; host `https://certificacion.studiamatch-aty.pages.dev/` con Home, detalle y comparador `200`. |
| Remediacion productiva | `H2_EXPAND_VERIFIED_AND_PROMOTED_MAIN` | [Plan De Remediacion Productiva H2](operaciones/h2_production_remediation_plan.md), evidence canonico del run `33143730910`, rerun `33188932351` success y PR #486 mergeado a `main`. |

## H3-BUILD-03B DB Implementation (2026-09-21)

El checkpoint `H3-BUILD-03B-DB-IMPLEMENTATION` fue implementado y validado
localmente en Docker PostgreSQL 17. La evidencia canonica del ciclo es
`.context/evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_db_implementation_local_2026-09-21.md` y el reporte detallado es
`STUDIAMATCH-INFORME-IMPLEMENTACION-H3-BUILD-03B-DB-2026-09-21.md`.

### Cambios validados

- Nueva migracion expand-only `db/migrations/20260921_h3_invitation_onboarding_rpc.sql`.
- TTL server-side de 24 horas desde `last_sent_at`/`sent_at` interno.
- RPCs `admin_accept_current_invitation`, `admin_complete_password_setup` y
  `admin_get_onboarding_status`.
- Locks por email/usuario/invitacion/membresia, expiracion lazy e idempotencia.
- Auditoria `accept`, `expire` y `password_set` sin duplicados efectivos.
- ACL minima, `SECURITY DEFINER`, search path explicito y sin exposicion de
  token, password o secretos.
- Harness nuevo integrado en `tests/sql/h3_pg17_harness.sql`.

### Validacion

- `h3_invitation_onboarding_harness_ok`.
- `h3_pg17_harness_ok`.
- `h3_invitation_edge_runtime_harness_ok`.
- Credential scan PASS.
- `git diff --check` PASS.

### Estado y limites

Estado: `H3-BUILD-03B-DB_LOCAL_VALIDATED`.

No se ejecutaron migraciones remotas, writes Supabase, Auth remoto, deploy,
schedules, workflow dispatch, commit, push, PR ni merge. Las migraciones
`20260918`, `20260919` y `20260920` permanecen intactas. Las invitaciones
anteriores al nuevo contrato no recibieron backfill DML.

### Expand -> compatibilidad -> deploy -> contract

- `expand`: nueva migracion y RPCs, conservando columnas/firmas legacy.
- `compatibilidad`: runtime Edge 03A, Auth-owned token y usuarios legacy `ready`
  permanecen soportados.
- `deploy`: pendiente de aprobacion JIT y validacion Free/Certification/Pro.
- `contract`: pendiente de callback/frontend validado y retiro controlado de
  compatibilidad.
- Rollback: futura migracion aprobada; no editar historicos ni aplicar rollback
  remoto implícito.

## Alcance Inmediato

El alcance inmediato es versionar la remediacion productiva H2 y habilitar el
flujo protegido hacia `main` sin ejecutarlo. Pro, `main`, writers, schedules,
deploys manuales o DML adicional requieren aprobacion JIT separada. La secuencia
obligatoria para produccion es expandir y verificar Pro antes del deploy frontend.
`web/**`, `db/**`, `supabase/**`, `scripts/core/**`, `scripts/shared/**`,
`scripts/maintenance/**`, `config/**`, dependencias y Docker permanecen protegidos
salvo autorizacion separada. H2 fue mergeado por PR #458 a `desarrollo`, PR #459
agrego gate documental post-merge y PR #460 lo promovio a `certificacion`, todos
con CI verde. Forward-fix, remediacion Security Advisor, backfill editorial,
seed, fix de vista publica y compatibilidad legacy aplicados/verificados en
Supabase Free. La web real de Certificacion muestra cursos reales; la limpieza de
calidad quedo validada remotamente en preview Cloudflare `4cc2e34c`. Pro, writer,
schedule o nueva accion remota requiere aprobacion JIT separada.

## H3-BUILD-03B Frontend Auth (2026-09-22)

El checkpoint frontend quedó implementado y validado localmente en Docker como
`H3-BUILD-03B-FRONTEND_AUTH_LOCAL_VALIDATED_WITH_RESIDUALS`. La evidencia
canonica es `.context/evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_frontend_auth_local_2026-09-22.md`.

- Cliente browser oficial Supabase con PKCE, persistencia de sesión compatible y
  `detectSessionInUrl = false`.
- Callback `/admin/auth/callback/` con exchange único, limpieza de URL,
  aceptación RPC y destinos internos fijos.
- Pantallas `/admin/accept-invite/` y `/admin/setup-password/` consumiendo las
  tres RPCs de onboarding; password enviada solo a Auth, nunca al RPC.
- Login/MFA legacy preservado como compatibilidad; MFA queda fuera del gate de
  aceptación por decisión de alcance.
- Mock local extendido para grant PKCE one-shot, actualización de password y
  RPCs de onboarding.
- `tsc`, lint sin errores, build normal, build mock, contratos focalizados,
  credential scan y `git diff --check` PASS. Lint mantiene 9 warnings históricos
  fuera del delta.
- `npm audit --omit=dev --audit-level=high` conserva 16 hallazgos HIGH y 1
  CRITICAL de dependencias transitorias; no se aplicó `npm audit fix` fuera del
  alcance.

No se ejecutaron Auth remoto, writes Supabase, migraciones remotas, deploy,
workflow dispatch, commit, push, PR, merge ni promoción protegida. Mock UAT-02
validó localmente callback, aceptación y password setup; el siguiente gate es UAT
remota por ambiente.

## Orden Vinculante Nuevo Pedido

```text
Intake documental
-> H2 Modelo editorial y pipeline tolerante a incompletos
-> H3 Administracion editorial autenticada
-> H1 Automatizacion segura y reactivacion gradual
-> H4 Home publica y documentacion tecnica
-> H5 Resultados publicos, filtros y cards
```

## Siguiente Gate

El checkpoint local `H3-BUILD-03B-FRONTEND-AUTH` y Mock UAT-02 quedaron validados.
El siguiente gate es UAT remota por ambiente, validación 03A/03B, Certification y
`contract/cleanup`. Supabase remoto, deploy, workflow dispatch, commit, push, PR,
merge y contract/cleanup requieren aprobaciones separadas.

H2REQ1 esta cerrado: `h2-expand-compat` fue aplicado y verificado en Pro,
la evidencia canonica esta en `.context/operaciones/h2_main_production_expand_evidence.json`
y la promocion `certificacion -> main` fue completada por PR #486.

La UAT ampliada de H3REQ1 alcanzó dos corridas estructurales 47/47 y 141/141 PASS,
pero la auditoría de readiness posterior revocó el GO para PR y dejó el estado
`H3_PR_DEVELOPMENT_NO_GO` (histórico). El build normal y mock ya pasaban en Docker
y las rutas admin se exportaban, por lo que el waiver de static export quedó
superseded; persistían bloqueadores reproducibles en CI, invariantes DB, MFA
real, cobertura E2E, rollback y vinculación de evidencia al candidato. La
atestación sanitizada
`.context/evidencias_cliente/sprint_1/atestado_h3_ampliacion_prompt_humano_sanitizado.md`
autorizó la corrección local hasta GO verificable. El ciclo siguiente resolvió esos
bloqueadores y dejó el estado `H3_PR_DEVELOPMENT_READY_LOCAL`.

### Ciclo de corrección local (2026-09-02) — bloqueadores HIGH/CRITICAL resueltos

Correcciones aplicadas y revalidadas en Docker (sin push/PR/remoto):

1. `security-audit.yml`: eliminada la línea corrupta bajo `h2-main-production-expand-gate:`
   (YAML parse OK) y reescrita la allowlist de `protected-paths` con el contrato H3
   explícito (`20260828_h3_admin_*`, `20260829_h3_rbac_users`, `20260830_h3_expanded_contract`,
   `20260902_h3_pr_contract`, `20260903_h3_rbac_contract_fix`, seed, harnesses,
   archivos admin web, workflows). El job
   `db-gate` ahora también crea la DB `h3_gate` y ejecuta `h3_pg17_harness.sql`.
   Gate replicado localmente con el diff real de `protected-paths` vs baseline
   `9b486146…`: `GATE_OK` (57 archivos en scope, todos allowlisted, incluida la
   restauración del sufijo `\.sql` compartido de migraciones H2/H3).
2. Migración `20260902_h3_pr_contract.sql`: `admin_get_course_editorial` devuelve valores
   efectivos consistentes (`current_values` + `current_value` por field) y
   `admin_publish_course` aplica gate de publicabilidad (rechaza `pending`/missing con
   error `Course is not publishable: pending quality or missing fields`).
3. Seed `h3_admin_seed_local.sql` idempotente (`ON CONFLICT DO NOTHING`) y con categorías
   asignadas a los 30 cursos fixture; el recompute de calidad tras ediciones ya no
   degrada cursos completos (30/30 con `category_id`).
4. Harness `h3_pg17_harness.sql` (CI, destructivo): re-run de seed idempotente, lector
   efectivo, rechazo de publish en draft incompleto y publish exitoso con auditoría;
   desde el candidato actual también cubre la regresión A6/A13 del delta `20260903`.
   Verificado en PG17 (`h3_gate3`): `h3_pg17_harness_ok`.
5. Harness `h3_pg17_harness_local.sql` (local, rollback): guard de idempotencia de seed +
   gate de publish + lector efectivo. Verificado en `studiamatch_h3`:
   `h3_pg17_harness_local_ok` (baseline DB restaurado a la seed canónica).
6. MFA: `admin-auth.ts` normaliza `enrollTotp` (shape anidada real y top-level mock),
   resuelve `aal` (top-level → decode JWT → `aal1`) sin forzar `aal2`, y el login
   (`web/src/app/admin/login/page.tsx`) muestra el panel “Registra tu autenticador”
   (QR `data:image`, secreto agrupado, `otpauth URI`) cuando el factor no está verificado.
7. Harness local spec `tests/h3_local_uat.spec.mjs` retirado (duplicado del runner canónico).
8. `.gitignore` actualizado (evidencia stale, `.worktrees/`, logs y node_modules del mock).

Validaciones del ciclo (local, Docker): TypeScript `tsc --noEmit` 0 errores; `npm run lint`
0 errores; build normal y `build:mock` estáticos PASS (rutas admin presentes);
`scripts/security/h2_web_mock_smoke.sh` PASS; actionlint y shellcheck PASS; suite CI-local
142 tests PASS; `py_compile`, credential scan y `git diff --check` PASS; H2/H2-Pro/H3
PG17 PASS con `h3_pg17_harness_ok` y regresión A6/A13.

Estado resultante: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR a `desarrollo`). El PR
incluye el delta `20260903` y documentación JIT sincronizada, sin afirmar aplicación
remota posterior. JIT-A mantiene A6/A13 históricos FAIL hasta revalidación; JIT-B
mantiene E1/E3/E4/E8 PASS y E2/E5/E6/E7 pendientes. Commit + push + PR protegido a
`desarrollo` siguen la plantilla `.github/pull_request_template.md`; la aplicación
remota del delta, configuración Auth, dependencia build, certificación y deploy
requieren aprobaciones separadas.

### Remediación local de cierre H3REQ1 (2026-09-23)

Con autorización humana `continua` se ejecutó únicamente el ciclo local. Se corrigió
el runner `tests/h3_local_uat.mjs` para consumir la sesión persistida por el cliente
oficial PKCE (`*-auth-token`, `access_token`, `refresh_token`), se hizo configurable
el Chromium instalado en Docker y el mock reconstruye sus identidades RBAC estables
antes de cada corrida. No se modificaron ambientes Supabase ni se ejecutaron
deploy, workflow dispatch, commit, push, PR, merge o promoción protegida.

Evidencia nueva y reproducible:

- `.context/evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_remediation_local_2026-09-23.md`.
- `.context/evidencia/h3req1_uat_matrix_local_2026-09-23.md`.
- `.context/evidencia/h3req1_remediation_report_2026-09-23.md`.
- `.context/evidencia/h3-expanded/h3-expanded-uat-matrix.json`: 47/47 casos y
  141/141 ejecuciones PASS, 141 screenshots y 0 retries.
- `tests/h3_invitation_uat.mjs`: 9/9 casos de invitación PASS, incluyendo user/admin,
  aceptación, password setup, expiración, revocación, resend/supersede, redirect y replay.
- Harness PG17 limpio: `h3_invitation_onboarding_harness_ok` y
  `h3_pg17_harness_ok`.

La matriz UAT local registra `PASS` únicamente para la evidencia local. El estado
contractual vivo permanece `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` porque
siguen pendientes Auth/PKCE y correo real, aplicación y validación remota 03A/03B,
UAT por ambiente, hostnames Development/Certification, Certification, Pro H3,
deploy y `contract/cleanup`. No se declara cierre definitivo. MFA/`aal2` permanece
fuera del gate H3REQ1 y como mejora evolutiva; su compatibilidad existente no fue
retirada.

### Ciclo 3 — afinación documental del plan y baseline local

El 2026-09-24 se afinó únicamente `.context/operaciones/h3req1_remediation_plan_2026-09-24.md`
y la ficha read-only del ciclo 2. No se modificó código, SQL, Edge, frontend ni
pruebas; tampoco se ejecutaron DDL, writes, Auth, correo, deploy, push, PR,
merge, cleanup, rollback o promoción. R1 queda clasificado como `PASS` por la
captura read-only, mientras H3-001 sigue `FAIL` por drift Pro y H3-002/H3-003/
H3-004 siguen `BLOCKED`. El siguiente paso autorizado es preparar el delta
exacto y solicitar los paquetes JIT separados; no aplicar migraciones ni iniciar
UAT con la evidencia actual.

La validación Docker/PG17 del ciclo 3 cerró `LOCAL-VAL-001` y `LOCAL-VAL-002`
como `PASS`: harness canónico limpio en `h3_cycle3_clean`, con resultados
`h3_pg17_harness_ok` y `h3_invitation_onboarding_harness_ok`. Los contratos H3
focalizados quedaron 8/8 `PASS`, la UAT mock de invitación 9/9 `PASS`, build
mock, TypeScript, credential scan, sintaxis y perímetro local `PASS`. `pytest`
continúa `BLOCKED` porque no está instalado en la imagen Docker y no se infiere
PASS por otra herramienta.

La revalidación remota read-only del ciclo 3 confirma: Free con 15 migraciones
H3 relacionadas y `admin-invite` v3 `ACTIVE`/`verify_jwt=true`; Pro con 0
migraciones H3, sin `admin_members`, `admin_membership_audit` ni
`admin_invitations`, y sin `admin-invite`. En aquel snapshot el hardening
registrado en Free no tenía archivo correspondiente en el checkout. El ciclo 4
lo recuperó y lo validó localmente; queda pendiente únicamente su
reconciliación after-apply remota. Estado contractual: H3-001 `FAIL`;
H3-002/H3-003/H3-004 `BLOCKED`; no se solicita Certification.

### Ciclo 4 — hardening local H3REQ1

Se corrigió el bloqueador local de SQL no reproducible: las migraciones de
hardening 20260924 fueron reincorporadas al checkout principal desde el
worktree de remediación y validadas en PG17 limpio. El nuevo harness acredita
protección de onboarding incompleto, RBAC de admin/user/inactivo, último admin,
auditoría append-only compatible y preservación legacy. Resultado local:
`h3_onboarding_rbac_hardening_harness_ok` y `h3_pg17_harness_ok`.

También quedaron `PASS` los 60 tests focalizados con pytest, TypeScript,
build normal, build mock, credential scan, sintaxis y UAT mock 9/9. Las
dependencias de pytest quedaron versionadas con hashes en
`requirements-pipeline.txt`. Los 9
warnings ESLint históricos permanecen sin errores.

Esto no cierra el gate remoto. H3-001 sigue `FAIL` porque Pro no tiene el
baseline H3; H3-002/H3-003/H3-004 siguen `BLOCKED` por falta de DDL, Auth/correo,
Edge/Pages, contract, cleanup y rollback autorizados. Estado: `NO-GO`.

El ciclo 5 corrigió los dos hallazgos locales HIGH/MEDIUM del auditor: la ruta
legacy `admin_create_member` ahora rechaza creación directa y el harness PG17
comprueba ACL/RLS de roles PostgREST. Los tests focalizados siguen 60/60
`PASS`; esto mantiene GO técnico local, pero no convierte evidencia local en
GO contractual remoto.

El ciclo 6 cerró la brecha de visibilidad operativa: se añadió el lector
aditivo `admin_list_members_onboarding` y la pantalla de miembros lo consume,
sin retirar el RPC legacy. TypeScript, build mock, lint sin errores, credential
scan, harness PG17 y tests focalizados permanecen `PASS`.

El ciclo 6 también alineó el mock server con ese RPC aditivo y limpió el lock
de Pygments para que `requirements-pipeline.txt` mantenga un único bloque con
hash reproducible. El gate remoto continúa `NO-GO` hasta las autorizaciones JIT
y la convergencia Free/Pro.

La reauditoría del ciclo 7 cerró los hallazgos locales restantes: mock reader
protegido por RPC, fixture PG17 coherente, legacy guard probado contra un user
`ready` real, lock pytest/Pygments reproducible y sin HIGH/MEDIUM local abierto.
H3REQ1 queda en `GO técnico local`, pero sigue `NO-GO contractual remoto` por
Pro sin baseline H3 y por falta de DDL/Auth/Edge/Pages/contract/rollback con
autorización JIT.

## Continuación del ciclo Development/Free — 2026-09-26

El preflight y la revalidación posterior a `continua` conservaron el estado
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. No se crearon usuarios,
invitaciones ni datos temporales y no se ejecutaron writes remotos.

- Free mantiene las dos migraciones `20260925`, las tablas H3 con RLS, las RPCs
  hardenizadas y `admin-invite` versión 4 `ACTIVE` con `verify_jwt=true`.
- El baseline final read-only permanece en 3 miembros activos, 0 invitaciones,
  0 huérfanas, 1 auditoría y 4 usuarios Auth.
- H3-001 Free queda `PASS`; H3-002, H3-003 y H3-004 permanecen `BLOCKED` por
  falta de sesión admin AAL2, buzón accesible, hostname/artefacto Pages de
  Development y rollback autorizado.
- La validación Docker local quedó `PASS` para 60 contratos focalizados,
  `h3_pg17_harness_ok`, TypeScript, lint sin errores, credential scan, sintaxis
  y `git diff --check`. El build pasó con `NEXT_PUBLIC_H3_MOCK_URL` vacío; el
  intento con `.env.local` cargado fue bloqueado correctamente por el guard de
  producción contra variables de mock.
- Los smokes Edge sin autorización devolvieron HTTP 401 y el conteo final
  confirmó ausencia de mutaciones.

El siguiente gate exacto es materializar fuera del chat la sesión admin
ready/AAL2 y el buzón temporal, y obtener el hostname/artefacto Development
correcto. Si se necesita frontend remoto, debe recibirse la autorización JIT
Pages/preview separada. Hasta entonces no se ejecuta UAT Auth, cleanup,
rollback, Certification, Pro, Production, push, PR o promoción.

La revalidación de intake de las 13:12 UTC recibió la opción humana
`A+B+C + continua`, pero la sesión admin, el buzón y el artefacto/hostname no
quedaron materializados en las herramientas disponibles. La autorización no se
consumió y el estado continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`, sin
usuarios temporales, invitaciones ni writes remotos.

### Revalidación coordinada y cierre del ciclo — 2026-09-26T14:40:25Z

Ambiente único: Free/Development, project ref `aqrldlmlszjtgpqiegaa`, URL
`https://aqrldlmlszjtgpqiegaa.supabase.co`. Checkout local evaluado:
`97168646b2a6bbd8e59f6d704446759303e11e64`; Edge Development `admin-invite`
remoto: versión `4`, `ACTIVE`, `verify_jwt=true`, bundle SHA
`fc6e0c3dfdb337f4fcd38cdc75a74c0a73392673d78e169bc0125f8ca655a313`.

Se consumió la autorización JIT consolidada para corregir únicamente el drift
ACL de `public.admin_members`. El artefacto fuera del repositorio fue
`h3req1_admin_members_acl_delta_20260926.sql`, SHA-256
`39d5a2e852cebad117f7292591d0658255281804915ad7fdfec968f3366636ef`; la
migración remota quedó registrada como
`h3req1_admin_members_acl_delta_20260926` en la versión
`20260926143836`. No se aplicó otro DDL.

La revalidación after-apply quedó `PASS`: `anon` y `authenticated` ya no tienen
ningún privilegio directo sobre `public.admin_members`; RLS continúa habilitado
en las tres tablas H3; el guard legacy y
`admin_list_members_onboarding()` permanecen presentes; los conteos no cambiaron
(3 membresías, 2 admins activos/ready, 4 usuarios Auth, 0 invitaciones, 0
huérfanas, 1 auditoría, 0 temporales, 0 filas de auditoría con marcadores de
secretos). H3-001 Free queda `PASS`.

La validación Docker quedó `PASS`: 60 contratos focalizados, 142 regresiones
offline, TypeScript, credential scan, sintaxis Python/Node, `git diff --check`,
build normal con `NEXT_PUBLIC_H3_MOCK_URL` vacío, build mock, UAT mock de
invitación 9/9, `h3_pg17_harness_ok`,
`h3_invitation_onboarding_harness_ok`,
`h3_onboarding_rbac_hardening_harness_ok`,
`h3_invitation_edge_runtime_harness_ok`, `h3_pg17_harness_local_ok`,
`h2_pg17_harness_ok` y regresiones A6/A13. Los DB/containers temporales creados
para esta ejecución fueron eliminados; no se modificaron otros datos locales.

La auditoría de dependencias se ejecutó en Docker y queda `FAIL` residual:
`npm audit --omit=dev --audit-level=high` reportó 36 vulnerabilidades, incluidas
16 HIGH y 1 CRITICAL. No se ejecutó `npm audit fix` porque cambiar dependencias
queda fuera de este ciclo; este hallazgo por sí solo impide cualquier GO.

La selección humana de sesión admin, buzón y Pages no pudo materializarse en el
entorno: el navegador disponible continúa fuera del hostname administrativo, no
hay buzón/API conectado y el preview conocido mantiene 404 en callback,
aceptación y setup de password. No se generó `run_id` ni se ejecutaron Auth,
correo, PKCE, callback real, RBAC remoto por actor, cleanup remoto, rollback o
Pages. H3-002, H3-003 y H3-004 permanecen `BLOCKED`.

Rollback previsto del delta ACL: restaurar, solo con autorización separada, los
privilegios previos de `anon` y `authenticated`; no se ejecutó rollback. Riesgo
residual: falta evidencia remota de correo/Auth/PKCE, UAT por rol, hostname y
artefacto Pages Development, y drill de rollback. El estado vigente permanece
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`; siguiente acción exacta: conectar
la sesión admin `active/ready/aal2`, el buzón temporal y el hostname/artefacto
Development desde el entorno seguro, sin compartir secretos.

### Verificación posterior a `continua` — 2026-09-26T14:49:35Z

La materialización se volvió a comprobar en modo read-only: no hay páginas
Chrome DevTools abiertas y el navegador accesible continúa en una API de GitHub,
no en el hostname administrativo Free/Development. Tampoco se expuso un buzón o
API temporal al entorno de ejecución. No se generó `run_id`, no hubo Auth,
correo, UAT remota, cleanup ni nuevos writes. El estado permanece
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`; siguiente acción: conectar esos
inputs reales sin compartir secretos.

### Pages/preview H3 recovery — 2026-09-26T17:38:49Z

Se consumió la autorización JIT Pages/preview exclusivamente para
Free/Development. El artefacto local incluye la nueva ruta separada
`/admin/reset-password/`, además de `/admin/auth/callback/`,
`/admin/accept-invite/` y `/admin/setup-password/`; la recuperación actualiza
password únicamente mediante Supabase Auth y no invoca RPC de onboarding.

Validación Docker: 165 pruebas contractuales/regresiones `PASS`, TypeScript
`PASS`, credential scan `PASS`, Python compile `PASS`, build normal `PASS` (243
páginas), build mock `PASS` (17 páginas), smoke Playwright de recovery `PASS` y
`git diff --check` `PASS`. Las siete rutas administrativas se generaron y
respondieron `200` en el servidor estático local; el callback de recovery limpia
la URL y rechaza tipos de enlace no `recovery`.

Preview Pages publicado en el proyecto `studiamatch`, ambiente `preview`, rama
`feat/h3req1-development-remote-tests`: deployment `946d11cc`, URL canónica
`https://946d11cc.studiamatch-aty.pages.dev` y alias operativo
`https://feat-h3req1-development-remo.studiamatch-aty.pages.dev`. El deployment
quedó `success` y asociado al commit base
`97168646b2a6bbd8e59f6d704446759303e11e64` con cambios locales marcados como
dirty. El smoke remoto del alias respondió `200` para `/admin/`, login,
callback, aceptación, setup, recovery y users; recovery no expuso marcadores de
token en el HTML.

Para hacer operativo el preview se añadió únicamente el alias real a
`ADMIN_ALLOWED_HOSTS` del entorno Preview de Pages, preservando el host anterior;
no se alteró la configuración Production. No se ejecutaron Auth, correo, DDL,
Edge, usuarios, MFA, cleanup, rollback, push, PR, merge ni promoción.

El estado contractual sigue
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`: en el snapshot previo faltaba
configurar el redirect de recuperación; ese punto quedó resuelto por el JIT de
Auth registrado abajo. Continúan pendientes recuperar la sesión admin, ejecutar
correo/PKCE/UAT real, RBAC, cleanup y rollback; además permanece el hallazgo
`npm audit` de 16 HIGH y 1 CRITICAL.

### Auth recovery redirect Free/Development — 2026-09-26T18:02:31Z

Se consumió la autorización JIT exclusiva de configuración Auth en Free/
Development, project ref `aqrldlmlszjtgpqiegaa`. Mediante Supabase Dashboard se
establecieron y verificaron después de recargar:

```text
Site URL:
https://feat-h3req1-development-remo.studiamatch-aty.pages.dev/admin/reset-password/

Redirect URL permitido:
https://feat-h3req1-development-remo.studiamatch-aty.pages.dev/admin/reset-password/
```

La configuración quedó persistida. No se modificaron usuarios, MFA, DDL, Edge,
Certification, Pro, Production, cleanup, rollback ni promoción. Aún no se envió
un correo de recovery ni se ejecutó Auth UAT; el siguiente paso humano es
solicitar un correo nuevo desde el usuario Auth existente sin compartir su URL o
token.

### Password policy, live validation and recovery TTL — 2026-09-26T18:54:19Z

Se consumió el ciclo autorizado `continua + Free Auth`, exclusivamente en
Free/Development (`aqrldlmlszjtgpqiegaa`). La configuración Auth se verificó en
el Dashboard antes y después de guardar:

```text
PASSWORD_MIN_LENGTH: 12
Password requirements: lowercase, uppercase, digits and symbols
MAILER_OTP_EXP: 86400 seconds (24 hours)
```

Se implementó una política compartida en recovery y setup inicial con validación
en tiempo real de longitud, mayúscula, minúscula, número, símbolo y coincidencia.
La contraseña continúa viajando únicamente a Supabase Auth; no se envía a RPC de
onboarding. La plantilla HTML versionada quedó en
`supabase/templates/password-recovery.html`; todavía no se aplicó al Dashboard
remoto.

Validación local: 23 contratos `PASS`, TypeScript `PASS`, lint `PASS` con 9
warnings históricos, build normal `PASS` (243 páginas), build mock `PASS` (17
páginas), `git diff --check` `PASS` y credential scan `PASS`. El Dashboard
reporta la recomendación de seguridad esperable por configurar la expiración Auth
por encima de una hora; el valor de 24 horas fue solicitado para alinear el
correo de recuperación y queda pendiente observar el comportamiento real con un
buzón autorizado.

Transición: `expand` (política compartida y plantilla) y compatibilidad recovery /
setup validadas localmente; `deploy` no ejecutado por alcance autorizado; el
contrato remoto de correo/UAT aún está pendiente. Certification, Production,
usuarios, MFA, cleanup, rollback, push, PR, merge y promoción no fueron tocados.
El estado general continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` hasta
completar plantilla remota autorizada, correo real, PKCE/UAT, RBAC, cleanup,
rollback y resolver o aprobar el waiver de `npm audit` (16 HIGH, 1 CRITICAL).

### Smoke UI live password validation — 2026-09-26T18:57Z

Se verificó en navegador local contra `/admin/reset-password/` con una sesión
local sintética aislada: valor incompleto mantiene el botón deshabilitado y marca
los requisitos pendientes; coincidencia incorrecta muestra el estado de mismatch
y mantiene el botón deshabilitado; valor completo marca las cinco reglas, muestra
`Lista para guardar` y habilita el botón. No se realizó submit ni se enviaron
credenciales a ningún backend; la sesión sintética y el contexto aislado fueron
eliminados al terminar.

### Security remediation and traceability — 2026-09-26T20:18:46Z

La reauditoría corrigió la exposición incompleta de estados para accesibilidad:
cada regla anuncia `cumplido/pendiente`, los inputs exponen `aria-invalid`, los
mensajes de error solo se referencian cuando existen y setup anuncia errores
generales con `role=alert`. Smoke final local: entrada incompleta deshabilitada,
mismatch deshabilitado y cinco reglas coincidentes habilitan el submit sin enviar
datos.

Se registraron hashes del checkout actual en la evidencia canónica. El deployment
histórico `946d11cc` mantiene sus hashes separados; no se atribuye el candidato
actual a Pages porque no se ejecutó deploy. La expiración de 24 horas queda como
riesgo autorizado y el Dashboard conserva su recomendación de usar un TTL menor a
una hora. No hay hallazgos CRITICAL/HIGH en el código auditado; permanecen
pendientes correo/UAT real, aplicación de plantilla remota, deploy, `npm audit`
(16 HIGH, 1 CRITICAL) y promoción.

Auditoría final de seguridad de la remediación: `GO técnico local`, 0 HIGH y 0
MEDIUM nuevos. El `NO-GO` contractual global se mantiene por el TTL autorizado de
24 horas, plantilla remota/UAT/correo/deploy pendientes y `npm audit` existente.

### Recovery real y Preview actualizado — 2026-09-26T21:42:07Z

Se consumió la autorización JIT exclusiva de Free/Development para aplicar la
plantilla de recovery, publicar el artefacto actual y probar el recovery del
usuario admin existente. La plantilla quedó persistida en Auth con asunto en
español, `{{ .ConfirmationURL }}`, uso único, vigencia de 24 horas y requisitos
de contraseña alineados con `PASSWORD_MIN_LENGTH=12` y las cuatro categorías
fuertes. El endpoint Auth `/recover` devolvió `200`; los logs sanitizados del
intervalo registraron `/verify` `303`, `/user` `200` y `/logout` `204`. La persona
operadora confirmó que el correo real llegó, que el Preview mostró el formulario
y el checklist en vivo, y que la edición de contraseña terminó correctamente.
No se registraron enlaces, tokens ni passwords.

Pages Preview `studiamatch` quedó en deployment `5fb35afa` (`success`), branch
`feat/h3req1-development-remote-tests`, commit base
`97168646b2a6bbd8e59f6d704446759303e11e64` con `commit-dirty=true`, y alias
`https://feat-h3req1-development-remo.studiamatch-aty.pages.dev`. El HTML remoto
de `/admin/reset-password/index.html` respondió `200` y coincidió con el export
local: 21,321 bytes y SHA-256
`c38d65166996cee5aed95b32764ff44eb8d7bd21fcb6eae53c2a6f6806488abe`.

La indicación relacionada con MFA se conserva intencionalmente: no se ocultó ni
se afirmó que el usuario tenga un factor habilitado. El Preview remoto vigente
continúa siendo el deployment anterior, donde el login guiaba el enrolamiento
cuando no existía un TOTP verificado y exigía AAL2 después de la verificación.
No se habilitaron, revocaron ni modificaron factores MFA remotos en este ciclo.

La transición `expand -> compatibilidad -> deploy -> contract` queda trazada en
la evidencia canónica. `expand` incorporó la política compartida y la plantilla;
`compatibilidad` conservó las rutas legacy y el callback existente;
`deploy` corresponde al Preview `5fb35afa`; `contract` permanece limitado a
Development hasta cerrar la UAT de invitaciones, RBAC, onboarding y MFA/AAL2.
Rollback documentado: restaurar la plantilla Auth previa y reasignar el alias al
deployment anterior, solo con autorización JIT separada; no se ejecutó rollback.

El estado global continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` por los
gates H3-002/H3-003/H3-004 todavía pendientes, `npm audit` con 16 HIGH y 1
CRITICAL, y la falta de promoción protegida. Certification y Production no se
modificaron.

### Continuación local — MFA de compatibilidad — 2026-09-27

El árbol local Docker incorpora la política MFA de compatibilidad: `aal1` permite
autenticar y llegar al panel; las operaciones sensibles mantienen
`admin_require_aal2()` y muestran una configuración/verificación TOTP explícita
cuando la RPC devuelve `MFA aal2 required`. El login ya no consulta factores ni
enrola silenciosamente. La integración usa el cliente MFA oficial de Supabase y
el mock local expone los factores a través de `auth/v1/user`, contrato que evita
el `GET /auth/v1/factors` remoto que devolvía `405`.

La validación local ejecutada dentro de Docker pasó TypeScript, build normal,
build mock, contratos MFA, sintaxis UAT, credential scan y `git diff --check`;
lint pasó sin errores y conserva nueve warnings históricos. El static smoke
confirmó password-only, configuración explícita, verify TOTP y sesión `aal2`.
El UAT canónico fue relanzado contra el static export/mock server después de
iniciar el PostgreSQL local detenido; el resultado final queda pendiente de su
terminación y no se afirma como PASS antes de contar con la matriz completa.

Este cambio permanece local: no se ejecutaron writes Supabase, DDL, cambios de
factores remotos, deploy, push, PR, merge ni promoción. La transición queda
`expand -> compatibilidad -> deploy pendiente -> contract pendiente`; rollback:
restaurar el login/MFA previo y reasignar el alias al deployment estable, con JIT
separado. Certification y Production no se modificaron.

### Diagnóstico Auth recovery rate-limit — 2026-09-27T03:17:11Z

La comprobación read-only de `auth_logs` en Free/Development confirmó que el
error del Dashboard corresponde a `POST /recover` con HTTP `429` y
`error_code=over_email_send_rate_limit`. Es la protección antiabuso de Supabase
Auth: debe transcurrir una espera mínima de 9 segundos desde la solicitud
anterior y el envío debe ejecutarse una sola vez. El evento no indica un fallo
de MFA, redirect, RPC, Preview ni DDL; no se realizaron cambios remotos durante
el diagnóstico.

El login observado antes del diagnóstico terminó en `Invalid login credentials`
antes de crear sesión, sin llegar a `aal1` autenticado, MFA o `aal2`. El Preview
Development vigente es el deployment `10205113`, publicado en el alias
`https://feat-h3req1-development-remo.studiamatch-aty.pages.dev`; el resto de
ambientes permanece intacto.

La credencial compartida en el intercambio y la expuesta durante la inspección
previa deben considerarse comprometidas. No se conserva su valor ni se usará
para una nueva validación. La rotación debe ocurrir antes de continuar la UAT
autenticada; después se podrá comprobar login, enrolamiento/verificación MFA y
una operación sensible. El estado global continúa
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### UAT remota read-only con sesión MFA — 2026-09-27

Con el usuario autenticado en OpenChamber Web, el Preview actualizado acreditó:
redirección de `/admin/login/` a `/admin/` con sesión existente, acceso en una
segunda pestaña, dashboard admin, gestión de usuarios, opciones `User`/`Admin`,
editor con institución protegida y navegación manual `Ver impacto`. El preview
compartido continúa mostrando `Hibrido` para el curso observado, consistente con
el diagnóstico remoto de disponibilidad `unknown` y cohorte legacy.

No se ejecutó el POST de invitación, correo, guardado, publicación, archivado,
calidad, cambio de rol ni logout. La invitación real y el cleanup requieren JIT
separado; el timeout remoto completo de 30 minutos queda representado por el
smoke local Docker. El estado sigue `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### MFA `aal2` y operación sensible confirmadas — 2026-09-27T03:55:45Z

OpenChamber confirmó que el código TOTP fue aceptado: el endpoint de verify
respondió HTTP `200`, desapareció la tarjeta MFA y la cola editorial cargó 131
cursos. Los RPCs `admin_get_course_queue` y `admin_count_course_queue` también
respondieron HTTP `200`, demostrando que la sesión elevada fue aceptada por el
enforcement server-side.

No se registraron códigos ni secretos MFA. El gate remoto de login, MFA explícita
y operación sensible queda `PASS`. Logout, refresh, regresión posterior al
refresh y reconciliación final de transición continúan pendientes; el estado
global sigue `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### MFA existente presenta challenge directo — 2026-09-27T03:48:54Z

Los logs Auth sanitizados confirmaron creación de factor, challenge y verify con
HTTP `200`, sin exponer secreto ni código. El login password-only continúa
entrando en `aal1`; las operaciones sensibles elevan a `aal2` según el contrato.

Se corrigió la tarjeta MFA para consultar los factores al montarse: si encuentra
uno `verified`, inicia el challenge existente y muestra directamente el campo de
6 dígitos. OpenChamber en el Preview `ea787a8a` ahora muestra `Verifica MFA para
continuar`, `Tu autenticador ya está configurado`, `Código de 6 dígitos` y
`Verificar MFA`, sin mostrar QR ni solicitar nuevo enrolamiento.

El gate de detección del factor verificado y presentación del challenge queda
`PASS`. Falta verificar el código actual y ejecutar la operación sensible con
`aal2`; el estado global continúa
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### Remediación de redirección posterior al login — 2026-09-27T03:37:18Z

La evidencia remota separó el rechazo de credenciales del problema posterior de
autorización: Supabase Auth registró `POST /token` `200`, el RPC
`admin_current_user_role` respondió `200`, y la membresía del usuario existente
es `admin`, activa y `ready`. La función remota declara `RETURNS text`; el cliente
solo extraía roles desde objeto/array, por lo que el valor escalar `admin` se
convertía en `anon` y `AdminDashboardPage` redirigía a `/admin/login/`.

Se corrigió `web/src/lib/admin-auth.ts` para aceptar respuesta escalar, objeto o
array sin romper el contrato mock. Validación Docker: TypeScript `PASS`, 12
contratos focalizados `PASS`, build normal de 243 páginas `PASS`, credential scan
`PASS`, `git diff --check` `PASS`; lint sin errores y nueve warnings históricos.

El candidato corregido se publicó exclusivamente en Pages Preview Free/
Development como deployment `e6948d54`, con el alias operativo
`https://feat-h3req1-development-remo.studiamatch-aty.pages.dev`. Las rutas
`/admin/login/` y `/admin/` responden `200`. No se ejecutaron DDL, writes de datos,
cambios de factores MFA, push, PR, merge ni promoción. Falta confirmar el login
posterior al deployment y continuar la UAT MFA; el estado global permanece
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### Login confirmado después de la remediación — 2026-09-27T03:41:43Z

OpenChamber confirmó sobre el alias Preview corregido que la sesión permanece en
`/admin/`, muestra `StudIAMatch Admin`, el rol visible `Admin`, `Cola editorial` y
el enlace `Usuarios`. Auth registró `POST /auth/v1/token` con HTTP `200`.

La tarjeta `Configura MFA para continuar` aparece como acción explícita y muestra
que la contraseña es válida. No se enroló ni modificó ningún factor MFA durante
esta comprobación. El gate de login/compatibilidad queda `PASS`; la verificación
TOTP, la sesión `aal2` y la operación sensible continúan pendientes. El estado
global permanece `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### UX editorial y renderer compartido — 2026-09-27

La mejora evolutiva de cola/editor/previsualización quedó implementada en el
candidato local Docker. Free/Development conserva el delta DDL aditivo registrado
como `20260927044751` (`20260927_h3_admin_queue_facets_filter`), con funciones
server-side para filtro institucional, conteo filtrado y facets de estados. Las
RPCs exigen `aal2`, editor activo y grants explícitos a `authenticated`/
`service_role`; los contratos legacy permanecen.

La cola ahora muestra estados con color y explicación, contadores de editorial y
calidad, selector de institución catalogado y paginación server-side. El editor
expone copy en español, ayuda contextual, impacto del campo y acciones con color
semántico. `CoursePublicRenderer` es compartido por el detalle público y la
previsualización inferior; los valores sin guardar actualizan el renderer, el
cambio de campo desplaza/resalta automáticamente el bloque afectado y `Ver
impacto` repite el salto manual.

Validación local Docker del ciclo: TypeScript `PASS`, lint `PASS` con 9 warnings
históricos y 0 errors, build normal `PASS` con 243 páginas, contratos focalizados
`16 passed`, UAT `47/47` casos y `141/141` ejecuciones `PASS`, PG17 harness `PASS`,
credential scan `PASS` y `git diff --check` `PASS`.

El candidato UX no fue desplegado en Pages durante esta continuación. Se conserva
la transición `expand -> compatibilidad -> deploy -> contract`, con rollback al
artefacto Preview anterior pendiente de autorización separada. No se ejecutaron
push, PR, merge, Certification, Production ni promoción. El estado contractual
global sigue `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` por los gates remotos y
documentales restantes, `npm audit` con 16 HIGH/1 CRITICAL y promoción protegida
pendiente.

### Validación remota del candidato UX — 2026-09-27T16:18Z

El candidato UX se publicó y validó únicamente en Free/Development. El PR `#500`
continúa abierto hacia `desarrollo`, sin merge. El head del PR es
`9d367f2f8ff487ec77080592946c4dfbdb2f34e1`; `security-audit`, protected paths,
credential scan, Python, ESLint, TypeScript, build, actionlint y PostgreSQL DB
gate quedaron `PASS`. CodeQL y sus tres jobs Analyze (`python`, `actions`,
`javascript-typescript`) quedaron `success`.

El branch preview hash del PR no está autorizado por `ADMIN_ALLOWED_HOSTS`, por
lo que la rama que conserva el alias Preview autorizado se sincronizó con el
frontend candidato mediante commit
`5a9aeace32b14df4ff73b47918f7212d1fb985e2`. Pages generó el deployment
`[UUID redactado]` (`success`) en:
`https://feat-h3req1-development-remo.studiamatch-aty.pages.dev`.

La validación remota read-only del alias confirmó `HTTP 200` para home, login,
dashboard, callback, aceptación, setup, recovery, users y un detalle público.
Chrome DevTools observó recursos `200/304`, cero errores de consola y solo dos
warnings de preload de fuentes. Con la sesión admin existente se observaron el
rol `Admin`, la cola con `131` filas visibles, facets `350/219/131`, el filtro
catalogado `Certus` con `16` filas, la búsqueda `Marketing` con `2` filas y el
filtro de calidad pendiente con `219` filas. El editor mostró copy español,
previsualización compartida, actualización en vivo del título, resaltado y
desplazamiento `Ver impacto`; responsive móvil a `390px` quedó utilizable.

No se ejecutaron guardar, publicar, archivar, actualizar calidad, cambios de rol,
Auth/MFA, cleanup, rollback, merge ni promoción. La continuidad de login,
challenge TOTP y operación sensible `aal2` queda referenciada a la evidencia
remota `ea787a8a`; no se reingresó ni registró un código MFA en esta pasada.
El gate de candidato UX Preview queda `PASS`, pero el estado contractual global
permanece `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` por `npm audit` con 16 HIGH
y 1 CRITICAL, invitación/cleanup/rollback y promoción protegida pendientes.

### Continuación local: invitación, sesión y publicación — 2026-09-27

La investigación read-only del ciclo posterior aisló tres hallazgos funcionales
sin tocar Certification ni Production:

1. `admin-invite` responde el preflight, pero `Access-Control-Allow-Origin` es
   `null` para el alias Preview. El runtime remoto requiere materializar el alias
   exacto en `ADMIN_INVITE_ALLOWED_ORIGINS`; no se ejecutó esa configuración ni
   un POST de invitación. El candidato local conserva fail-closed y presenta un
   error operativo en español.
2. La sesión Auth administrativa pasó a almacenamiento compartido entre pestañas
   con migración legacy desde `sessionStorage`. `AdminSessionGuard` cierra tras
   `30 * 60 * 1000 ms` sin actividad y sincroniza actividad/logout mediante
   `localStorage`. El editor conserva `Ver impacto` como único desplazamiento
   manual; editar o enfocar un campo ya no lleva la ventana a la previsualización.
3. La lectura del curso IDAT `[UUID redactado]` confirmó
   `published/complete`, override `mode=Remoto`, pero `availability_status=unknown`.
   La vista `courses_public_effective` conserva entonces el valor legacy
   `Hibrido`; no es un fallo de caché ni de mapeo del detalle. Se versionó el
   delta local `20260927_h3_publication_visibility_contract.sql` para impedir
   futuras publicaciones que no cumplan `availability=available`; no se aplicó
   remotamente ni se forzó DML sobre disponibilidad.

Validación Docker del checkout: TypeScript, build normal/mock, 12 contratos focales,
PG17 H3 harness, credential scan, sintaxis Node y `git diff --check` `PASS`; lint
`PASS` con 9 warnings históricos; UAT editorial `47/47` y `141/141` screenshots;
UAT de invitación `9/9`, incluyendo rol `user`; smoke de actividad, logout
cross-tab y no auto-scroll `PASS`. La ausencia de `pytest` en la imagen se dejó
registrada y los contratos se ejecutaron directamente con Python.

La transición sigue `expand -> compatibilidad -> deploy -> contract`: el deploy,
la configuración CORS remota, la contracción legacy, cleanup y rollback requieren
autorización separada. El estado global continúa
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` por la UAT remota pendiente,
`npm audit` con 16 HIGH y 1 CRITICAL y la promoción protegida no solicitada.

### After-apply CORS de `admin-invite` — 2026-09-27T18:41Z

Se consumió la autorización JIT exclusiva de allowlist + deploy en Free/Development.
`admin-invite` quedó en versión `7`, `ACTIVE`, `verify_jwt=true`, bundle
`0b2cffede1333b2ffa2a5c0acd1814233caf7c4ef6d06af74b8aae32cc1ce478`. El alias
Preview autorizado `https://feat-h3req1-development-remo.studiamatch-aty.pages.dev`
recibe ahora `Access-Control-Allow-Origin` exacto en el preflight `OPTIONS`; un
origen externo recibe `null`. El `GET` sin autorización continúa en `401`, por lo
que el perímetro JWT no se debilitó.

La implementación conserva las variables de allowlist, normaliza orígenes y
aplica el fallback del alias solo si `SUPABASE_URL` corresponde al proyecto Free
autorizado; Pro/Production no lo heredan. No se ejecutó invitación, correo,
Auth/MFA, usuario temporal, POST autenticado ni cleanup. El estado global sigue
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` por la UAT remota de invitación y
rol `user`, disponibilidad pública pendiente, `npm audit` con 16 HIGH y 1
CRITICAL, cleanup/rollback y promoción protegida.

### Corrección local de redirección de login — 2026-09-27

La página `/admin/login/` ahora consulta la sesión Auth antes de mostrar el
formulario. Con sesión válida redirige automáticamente a `/admin/`; sin sesión
mantiene el login disponible. TypeScript, lint, build normal/mock, 13 contratos,
smoke de sesión y UAT local `48/48` (`144/144`) quedaron `PASS` en Docker.

El frontend candidato ya se desplegó con autorización únicamente al Preview
Free/Development: `https://cbc299f7.studiamatch-aty.pages.dev`, alias operativo
`https://feat-h3req1-development-remo.studiamatch-aty.pages.dev`. Login, panel y
usuarios responden `HTTP 200`; el preflight de invitaciones desde el alias
devuelve el origen permitido exacto. Todavía se requiere la sesión del usuario
con MFA para ejecutar las pruebas autenticadas; no se envió invitación/correo ni
se realizó una mutación remota. El estado contractual continúa
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### Diagnóstico Edge `admin-invite` v8 — 2026-09-27

Con autorización JIT se desplegó únicamente en Free/Development la versión `8`
de `admin-invite`, `ACTIVE`, `verify_jwt=true`, bundle
`3a195d795fbfa355fa55573d0913e9fc0d9b055323fde8b75abc243f07ae10f3`. El
preflight del alias autorizado quedó `HTTP 200` con origen exacto y el origen
externo recibió `null`.

El único reintento Admin autorizado recibió `HTTP 500` con `Server configuration
incomplete`. La auditoría agregada posterior confirmó `0` invitaciones, `0`
membresías y `0` usuarios Auth nuevos. El runtime Edge no tiene disponible
`NEXT_SUPABASE_SECRET_KEY` (o `SUPABASE_URL`) bajo el nombre esperado. No se
expuso ningún secreto y no se repitió el POST.

Se mantiene `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. Se requiere una
aprobación JIT específica para materializar el secreto en Free/Development y
otra autorización para un nuevo POST controlado; no se debe tocar
Certification/Production.

### Drift SQL del callback de invitación — 2026-09-28

El primer clic de la invitación confirmó Auth y alcanzó el RPC de aceptación,
pero no cambió la invitación ni la membresía. La definición remota de
`admin_accept_current_invitation` tenía dos backslashes en la regex del correo;
rechazó el email normalizado antes de la transición y devolvió una respuesta RPC
HTTP 200 con error de negocio. El segundo clic falló por el uso único del enlace.

Se preparó localmente
`db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql` y se añadió al
PG17 harness; el harness terminó `h3_pg17_harness_ok`, contratos/credential scan
y diff check pasaron. El delta no se aplicó al proyecto Free. La invitación
existente sigue `pending`/`invited` aunque la identidad Auth ya está confirmada.

El estado continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. Se necesita JIT
para aplicar el DDL y una autorización posterior para cleanup/reemisión, sin
Certification/Production.

### Delta SQL aplicado en Free — 2026-09-28

Con autorización JIT se aplicó únicamente
`h3_invitation_accept_email_regex_fix` en Free/Development; Supabase registró la
migración `20260928002407`. La definición remota ahora contiene una sola barra
escapada en la regex y no contiene la variante doble. La invitación fallida no
fue modificada: permanece `pending`/`invited`, con Auth confirmado.

Se mantiene `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. Cleanup/reemisión y
otra prueba de correo requieren autorización JIT separada.

### Fallback de callback preparado — 2026-09-28

Se implementó y validó localmente un fallback seguro en
`/admin/auth/callback/`: una sesión Auth válida sin `code` ni fragmento puede
reintentar `admin_accept_current_invitation`; una sesión anónima sigue siendo
rechazada. TypeScript, lint, builds normal/mock, 20 contratos, credential scan,
diff check y PG17 harness (`h3_pg17_harness_ok`) pasaron.

El cambio no está publicado en Pages. La invitación existente sigue
`pending`/`invited` y su enlace ya fue consumido. Para completar la UAT se
requiere publicar este fallback y que el usuario establezca una contraseña por
recovery, inicie sesión y vuelva al callback; cleanup/reemisión sigue pendiente.

La telemetría confirma que el primer clic sí alcanzó la RPC de aceptación con
sesión Auth; el diagnóstico previo de ausencia de `code`/sesión fue incorrecto.
La causa probada fue la regex doble del RPC. El segundo clic sí fue rechazado por
token de un solo uso.

### Fallback de callback desplegado en Preview — 2026-09-28

Con autorización separada se publicó únicamente el frontend normal en el alias
Preview. Deployment `8d64a66f.studiamatch-aty.pages.dev`; `/admin/login/`,
`/admin/auth/callback/` y `/admin/accept-invite/` respondieron `HTTP 200`.
No se envió correo ni se tocaron datos. La sesión actual del administrador no se
navegó al callback para evitar logout accidental.

### Revalidación de secreto y sesión — 2026-09-27

La sesión MFA del usuario volvió a confirmarse en el Preview: `/admin/` carga,
el rol `Admin` es visible y el logout está disponible. `NEXT_SUPABASE_SECRET_KEY`
existe localmente en Docker y `/app/.env.local`, con formato `sb_secret_...`;
los workflows GitHub también la referencian mediante el secreto del environment
`Development`.

Eso no prueba su disponibilidad en el runtime aislado de Supabase Edge. El CLI
no pudo listar los secretos remotos porque el contenedor no tiene
`SUPABASE_ACCESS_TOKEN`, y el POST v8 continúa devolviendo `Server configuration
incomplete`. No se repitió la invitación. Los 14 contratos focalizados,
credential scan y `git diff --check` pasaron.

Se requiere aprobación JIT separada para materializar el secreto en Free → Edge
Function secrets y otra autorización para un nuevo POST controlado. El estado
continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### Runtime corregido e invitación Admin — 2026-09-27

El usuario configuró `NEXT_SUPABASE_SECRET_KEY` en los secrets de Edge de
Free/Development. `admin-invite` quedó en versión `9`, `ACTIVE`,
`verify_jwt=true`, bundle `3a195d795fbfa355fa55573d0913e9fc0d9b055323fde8b75abc243f07ae10f3`.
La prueba no mutante con correo inválido devolvió `HTTP 400 Invalid email`, por
lo que desapareció el `Server configuration incomplete`.

Con autorización JIT se ejecutó un único POST Admin. La UI confirmó estado
`pending`, cuenta `invited` y correo enviado; logs registraron `POST | 200`.
La auditoría agregada confirmó `1` invitación pending, `1` membresía admin
invited y `1` usuario Auth nuevo, sin duplicados. No se abrió correo ni se
aceptó el enlace. El usuario debe completar onboarding/MFA manualmente; cleanup
requiere autorización JIT separada. El estado sigue
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### Reenvío seguro y plantilla de invitación — validación local 2026-09-28

Se implementó localmente el botón `Reenviar invitación`, limitado a filas
`pending`/`invited` y protegido por administrador activo y MFA/AAL2. El Edge
mantiene el camino de invitación para identidades Auth no confirmadas y usa
`resetPasswordForEmail` con redirect allowlisted para identidades confirmadas;
no elimina usuarios ni requiere cleanup. La respuesta distingue
`recovery_sent=true` y conserva la invitación pendiente si Auth no puede
entregar recovery.

Se añadió `supabase/templates/invite.html`, alineado visualmente con
`password-recovery.html`, con un único `{{ .ConfirmationURL }}` y sin manejo de
tokens. El template y el cambio Edge siguen locales; no se aplicaron al
Dashboard ni se desplegaron.

Validación local actual: 26 contratos con runner Python directo, TypeScript,
lint sin errores (9 warnings históricos), build normal de 243 páginas, build
mock de 17 páginas, Node syntax checks, credential scan, `git diff --check` y
PG17 `h3_pg17_harness_ok` en PASS. `pytest` no está instalado en el contenedor.

La última publicación Preview (`8d64a66f`) contiene el fallback anterior, no
este botón ni el nuevo Edge. Para continuar se requieren autorizaciones JIT
separadas para deployment Preview, despliegue de Edge y aplicación/configuración
remota del template Auth, además de un único envío controlado. El estado sigue
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`; Certification/Production no fueron
tocadas.

### Preview y Edge actualizados — 2026-09-28

Con autorizaciones separadas se publicó el frontend Free/Development en
`82d2f852.studiamatch-aty.pages.dev` y se actualizó el alias autorizado
`feat-h3req1-development-remo.studiamatch-aty.pages.dev`. Las rutas login,
callback y users respondieron `HTTP 200`; la UI autenticada mostró
`Reenviar invitación` únicamente para la fila `pending`/`invited`.

`admin-invite` quedó en versión `10`, `ACTIVE`, `verify_jwt=true`, bundle
`f051a0a25aafbd3cb0910dd810b45a884537ac2653fee3e6cb41c4169f0dd16e`. No se
ejecutó ningún POST de reenvío.

La verificación del Dashboard mostró que el cuerpo del template Invite todavía
era el default; `supabase/templates/invite.html` aún no se considera aplicado.
El usuario debe pegarlo y guardarlo manualmente en Free/Development. Recovery,
Certification y Production no fueron tocados. El estado sigue
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` hasta completar template, envío
único, aceptación, MFA, RBAC, cleanup/rollback y evidencia contractual.

### Reenvío recovery ejecutado — 2026-09-28

El usuario confirmó el guardado manual del template Invite Free/Development.
Con JIT específico se ejecutó una sola vez `Reenviar invitación` para la
identidad Auth existente. La UI confirmó `Correo de recuperación reenviado`;
Edge registró `POST | 200` a las `02:22:02Z`, Auth registró un recovery y un
mail send, y la auditoría agregada confirmó una invitación admin pending de
reenvío, una membresía admin invited, cero usuarios Auth nuevos y cero
duplicados. La fila permaneció `pending`/`invited`.

El agente no abrió el correo ni aceptó el enlace. El usuario debe completar
manualmente recovery/contraseña, login, MFA y `/admin/auth/callback/`; la UAT
post-onboarding, RBAC por actor y cleanup/rollback siguen pendientes. El estado
continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### Re-invite del mismo correo: preparación huérfana — 2026-09-28

La evaluación read-only confirmó una identidad Auth confirmada, una sesión, un
refresh token, un one-time token, tres invitaciones y tres auditorías para
`[cuenta de prueba protegida]`. No se ejecutó eliminación.

Las invitaciones y auditorías son append-only por contrato; no se permite borrar
esas filas para liberar el correo. Se preparó localmente el caso seguro en el
Edge: cuando no existen Auth ni membresía viva, pero queda una invitación
histórica pendiente, `Agregar usuario` puede enviar una invitación Auth nueva y
la reserva supersede la pendiente, conservando toda la trazabilidad. Se
mantienen cooldown, RBAC, role checks y el camino recovery para identidades
confirmadas.

Los gates posteriores pasaron: 27 contratos directos, TypeScript, lint sin
errores (9 warnings históricos), builds normal/mock de 243/17 páginas, PG17
`h3_pg17_harness_ok`, Node syntax, credential scan y diff check. El Edge remoto
sigue en v10; el ajuste huérfano es local. No se eliminó Auth ni se envió una
nueva invitación. Para continuar se requieren JIT separados para eliminar solo
la identidad Auth/tokens y desplegar Edge; el histórico de invitaciones/auditoría
se conservará. El estado sigue
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### POST huérfano bloqueado por rate limit — 2026-09-28

Tras desplegar Edge v11 y eliminar la identidad Auth anterior, se ejecutó el
único POST autorizado de `Agregar usuario` con el mismo correo. Auth respondió
HTTP 429 `over_email_send_rate_limit`; no se creó usuario Auth ni membresía.
Edge devolvió `Auth invitation failed` y, por un defecto de compensación de v11,
registró dos `send_failed` para un solo intento. Las filas y auditorías se
conservaron por el contrato append-only.

Localmente se corrigió el doble registro y se añadió el mapeo `auth_rate_limited`
→ HTTP 429; también se mantuvo el caso orphaned y la FK
`admin_members.user_id -> auth.users(id) ON DELETE CASCADE`. Los gates pasan con
28 contratos, TypeScript, lint sin errores (9 warnings históricos), builds
normal/mock 243/17, PG17 `h3_pg17_harness_ok`, Node syntax, credential scan y
diff check. Edge remoto permanece v11, por lo que no se reintentará mientras el
rate limit siga activo ni sin una nueva autorización JIT para desplegar v12.
El estado continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

### Edge v12 y rate limit del proveedor — 2026-09-28

Con autorización JIT se desplegó `admin-invite` v12 en Free/Development sin
POST. Quedó `ACTIVE`, `verify_jwt=true`, bundle
`87329d8f47ff36917d13e237c09b39763d0088a114fd67acd351cc6642da2111`. Incluye el
caso orphaned, mapea Auth 429 a `auth_rate_limited`/HTTP 429 y elimina la
compensación externa duplicada.

Supabase documenta un límite aproximado de 2 envíos por hora con el proveedor
integrado; no se repetirá el POST durante la ventana ni se sorteará el límite.
El estado objetivo actual es `0` Auth users, `0` memberships, `1` pending, `2`
superseded, `2` send_failed y `5` auditorías, todo el histórico conservado.
El estado continúa `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` hasta completar
un reintento permitido por el proveedor, invitación/aceptación/MFA/RBAC y UAT.

### Preflight de invitación Auth normal — 2026-10-01

La comprobación remota read-only más reciente queda registrada en la evidencia
[de preflight del 2026-10-01](evidencia/h3_invite_normal_preflight_2026-10-01.md).
Free confirma `admin-invite` v12 `ACTIVE`,
`verify_jwt=true` y el SHA esperado; sus marcadores de reinvitación huérfana y
`auth_rate_limited` están presentes, con una única llamada a `failInvitation`.

El agregado actual confirma cero usuarios Auth, identidades, sesiones, refresh
tokens, one-time tokens, factores MFA y membresías; se preservan 1 invitación
`pending` (vencida en el timestamp observado), 2 `superseded`, 2 `send_failed` y
5 auditorías. No hubo writes ni se abrió el buzón.

Los logs de Auth/Edge de las últimas 24 horas no muestran
`over_email_send_rate_limit`; esto no demuestra que el proveedor haya liberado el
límite y no se hizo un envío de prueba. La pestaña Preview muestra el formulario
de login, no una sesión Admin/AAL2. El Dashboard abrió la sección de templates,
pero no expuso el subject ni el cuerpo Invite en una vista verificable. Por ello
no se solicitó JIT nuevo ni se ejecutó el POST. Estado: `NO-GO`; quedan pendientes
la inspección manual del template remoto, sesión Admin/AAL2 y un preflight
read-only actualizado antes de considerar una nueva JIT de un solo envío.

Transición: `expand` conserva Edge v12; `compatibilidad` preserva invitaciones y
auditorías append-only; `deploy` no se repitió; `contract` y rollback no se
ejecutaron. No hay cleanup ni promoción autorizados.

### Resultado del único clic de invitación normal — 2026-10-01

Se recibió una autorización JIT nueva y acotada para un único clic de
`Agregar usuario` en Free/Development; el clic se ejecutó una vez. La lectura
read-only posterior encontró una identidad Auth, sesión, refresh token, factor
MFA y membresía, y la invitación nueva figura `accepted` con auditorías `accept`
y `password_set`. No se verificó el estado final/rol de la membresía ni el
`aal2`; no se atribuye quién realizó esas transiciones.

La consulta agregada de logs posterior falló con error de backend, así que no se
confirmaron `POST 200` ni el evento Auth de invitación. No se abrió el buzón, no
se aceptó el enlace desde el agente y no hubo retry, segundo clic ni cleanup.
Resultado inesperado frente al estado `pending`/`invited` esperado: detener UAT y
pedir confirmación humana antes de cualquier otra validación. El estado global
continúa `NO-GO`; no se declara invitación normal comprobada ni UAT completada.

### Post-check de onboarding confirmado por el usuario — 2026-10-01

El usuario confirmó que completó la autenticación manualmente. La consulta
read-only posterior confirma una sola identidad Auth y membresía; la membresía
está `admin`, activa y `ready`. La invitación más reciente figura `accepted`,
con `accepted_at` y `password_set_at`; hay un factor TOTP `verified` y una sesión
actual con `aal2`. Se reconciliaron 8 auditorías y no hay identidad duplicada.

El caso funcional de invitación/onboarding queda validado, pero la consulta de
logs del envío falló y no acredita el HTTP `POST 200`; se conserva esa brecha de
telemetría y no se atribuye la aceptación a una acción del agente. El usuario
reporta que el panel identifica el rol `Admin`, pero no quién inició sesión; se
registra como mejora UX aparte. UAT H3 global continúa `NO-GO`, sin cierre ni
promoción. No se hizo cleanup: invitaciones/auditorías son append-only; cualquier
cleanup de Auth/membresía requerirá una JIT destructiva nueva y específica.


### Delta vigente R77–R83 — 2026-10-11

R77 cerró el canal local de asesoría (3/3); R78 pasó navegación pública/404,
recursos, nombres de control, rutas de cinco instituciones y fit de viewport
(18/18, screenshots, Chromium 1228 headless en R12). R79 midió H3-UAT-063 en
diez muestras independientes, 30/30 viewports, cero retries; no establece SLA.
R80–R82 conservan rojos del test de cola: controles de paginación se ocultan
cuando el filtro produce una sola página, las lecturas de conteo y filas se
sincronizaron incorrectamente y el mock MFA alcanzó rate limit al omitir el
reset sintético por viewport. R83 repara solo el runner, restablece el fixture
local aislado y pasa H3-UAT-017 3/3, 63/63 aserciones, tres capturas y vídeo
desktop. La base sintética PG17 conserva 31 cursos, 31 estados editoriales,
406 auditorías editoriales, 15 membresías, 58 auditorías de membresía y 24
invitaciones; la cola expone 26 filas, incluida la combinación `draft/pending`
de 9 resultados.

G08 sigue completo; G09 sigue parcial. LOCAL-06, LOCAL-12 y LOCAL-22 cierran en
su alcance local; R90 cierra además LOCAL-14 para preview Admin. El total
histórico permanece en 80% (8/10) y el cierre local en 88,89% (8/9). No se
declara GO. G10 sigue remoto y fuera de autorización. Detalle/hashes:
`evidencia/h3req1_g09_local_acceptance_delta_r77_r83_2026-10-11.md` y
`evidencia/h3req1_g09_local_acceptance_delta_r84_r90_2026-10-11.md`.

### Delta vigente R84–R90 — preview/editor Admin — 2026-10-11

R90 ejecutó H3-UAT-049 en desktop/tablet/móvil: 32/32 aserciones por viewport,
96 total, cero errores de consola/requests y cero retries. Chromium 1228 corrió
headless en Docker; Pages/workerd R12, Auth/PostgREST mock y PG17 sintético
permanecieron aislados. Se guardaron tres capturas y vídeo desktop. El caso
acredita fallback visible `Consultar` con fecha opcional vacía, preview parcial,
límite responsive, descarte sin persistencia, guardado deshabilitado sin cambios
y auditoría, y el recorrido save/publicación/listado/detalle/comparación. El
renderer/editor/preview funcional no cambió en este delta.

R85, R86, R87 y R89 son rojos preservados del oráculo: selector `Inicio`
ambiguo; lectura inicial sin observabilidad; `innerText` no concordó con
`textContent=InicioConsultar`; y expectativa incorrecta de que el botón de
guardado desapareciera. R90 usa texto exacto visible y verifica el botón
deshabilitado; el badge no aparece y auditoría/versión quedan intactas al
descartar. Evidencia primaria, capturas, vídeo, hashes y límites:
`evidencia/h3req1_g09_local_acceptance_delta_r84_r90_2026-10-11.md`.

LOCAL-14 queda completo para preview Admin. LOCAL-13 avanza, pero mantiene
pendientes la matriz vigente de tipos/campos y reconciliación focal de
conflicto/ownership. G09 no cierra y las métricas no cambian: 80% histórico
(8/10), 88,89% local (8/9). El WIP sigue 60 tracked, 808 untracked visibles,
16.706 paths expandidos, 0 staged; no se alteró el checkout original ni se
hicieron operaciones remotas.

### G09 delta R91 — conflicto de versión y procedencia — 2026-10-11

H3-UAT-023 pasó 3/3 viewports y 24/24 aserciones; por cada carrera sintética
hubo un ganador y un conflicto, la procedencia se recuperó tras reload y se
restauró el override inicial. Capturas/evidencia:
`evidencia/h3req1_g09_local_acceptance_delta_r91_2026-10-11.md`. LOCAL-13/T08
avanza, pero sigue parcial por cobertura vigente de grupos y tipos de campo.
Las métricas continúan 80% histórico y 88,89% local; G09 parcial, G10 remoto.

### G09 delta R92–R94 — concurrencia de membresías — 2026-10-11

R92 falló antes de las mutaciones porque `site-out-r12` no contenía la región
accesible actual; R93 ejecutó H3-UAT-040 contra el build R41 y pasó 57/57
aserciones en tres viewports. Dos RPC simultáneas del mismo actor se
serializaron, el último-admin guard se mantuvo y el fixture se restauró. R94
añadió dos transacciones PG17 con actores sintéticos distintos: la primera
desactivó al otro admin; la segunda fue rechazada al quedar su actor inactivo.
El último admin permaneció activo; ambos miembros se restauraron y el conteo
regresó a 2. Evidencia: `evidencia/h3req1_g09_local_acceptance_delta_r92_r93_2026-10-11.md`
y `evidencia/h3req1_g09_local_acceptance_delta_r94_2026-10-11.md`.
LOCAL-10/T06 queda completo en el fixture local; no cierra G09 ni cambia las
métricas. Las auditorías de prueba sintéticas son append-only y se conservaron.

### G09 delta R109–R116 — estados públicos y teclado editorial — 2026-10-11

R113 ejecutó H3-UAT-066: los 13 campos editoriales tienen nombre accesible y
Tab/Shift+Tab recorre el formulario sin guardar; 3/3 viewports, 9/9 aserciones,
tres capturas y vídeo desktop. R114 conservó el timeout causado por la caché
local no vacía; R115 conservó el FAIL del runner por prefetch 404 de una ruta de
fixture ausente. Se corrigió solo el runner: invalidar la caché sintética entre
estados y usar un slug ya generado por el export estático. R116 pasó
H3-UAT-067 en 3/3 viewports y 15/15 aserciones: catálogo poblado, vacío, API
503 con fallback y cero egress/errores de consola. El runner terminó con cero
retries; no cambió producto.

R109–R112 también se conservan como fallos de preflight/endpoint/locator y reset
de fixture, ya clasificados en la evidencia de este delta. `node --check`,
`git diff --check`, credential scan Docker, coincidencia de fuente montada y
preflight estructural pasan. El scanner se ejecutó con entorno limpio y solo
sobre el runner UAT.

Una consulta `BEGIN READ ONLY ... ROLLBACK` en PG17 sintético R12 contó 31 cursos,
0 estados ausentes, 16 filas públicas efectivas, 27 precios positivos/2 cero/2
nulos y 15 evidencias de disponibilidad dentro de 90 días/16 ausentes. El
resultado es agregado y no cierra LOCAL-01 ni se atribuye a la respuesta
REST sintética de R116. INV-008 no se repitió: el análisis R8 ya identificó el
ciclo de guard para `password_pending`, y onboarding R8 pasó 10/10.

La matriz visual actual es 67 casos × 3 viewports = 201 ejecuciones PASS
seleccionadas a través de corridas compatibles; no hubo una corrida global
única. R113/R116 añaden 6 ejecuciones PASS y 24 assertions. G08 permanece
completo; LOCAL-02 y LOCAL-20 avanzan, LOCAL-01 sigue parcial. G09 conserva
LOCAL-07/08 (checkpoint/persistencia pipeline PG17), LOCAL-09 (expiry/refresh en
navegador), LOCAL-16 (rebuild/estratos), LOCAL-17/19 (negativos y recovery
integrados), y revisión LOCAL-23. No cambian las métricas: histórico G01–G10
80% (8/10), cierre local G01–G09 88,89% (8/9). No GO.

Estado de trabajo al cierre de esta fase: rama `feat/h3req1-sync-20261002`,
HEAD base `4eb4d877a50b012bb630a129bd0c74482c33be9c`, 60 tracked modificados,
814 entradas untracked visibles (16.927 paths al expandir), 0 staged. Recursos
R12 y `studiamatch-dev` se preservan; no se tocó el checkout original, no hubo
cleanup, commit, push, PR, merge, deploy ni operación remota. Evidencia y hashes
completos en `evidencia/h3req1_g09_local_acceptance_delta_r113_r116_2026-10-11.md`.
