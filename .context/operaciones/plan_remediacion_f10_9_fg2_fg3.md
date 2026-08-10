# PLAN-REM-F10.9-001 - Remediacion FG2/FG3 Post-Activacion Programada

| Campo | Valor |
|---|---|
| ID | `PLAN-REM-F10.9-001` |
| Estado | `G0_PASS_P2_WIRING_IN_PROGRESS` |
| Incidente | [INC-F10.9-001](./incidente_f10_9_fg2_fg3_2026-08-09.md) |
| Subfase | `F10.9` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` |
| Autoriza ejecucion | `NO` |

## Objetivo

Restaurar la operacion global segura de FG2 y FG3 sin ocultar parciales, sin
inventar datos y sin debilitar controles SSRF. F10.9 se limita a runtime CA1,
promocion protegida, schedules y observacion; no incluye schema, DDL, DML de
reparacion ad hoc, re-enrichment ni backfill.

Este plan es subordinado a
[PLAN-H1-CA1-ONLY-001](./plan_cierre_hito1_ca1_only.md). No crea tarea,
criterio, subfase ni autorizacion paralela.

Ninguna seccion, estado, gate o fila denominada `Aprobacion pendiente` concede
capacidad de ejecucion. Cada gate requiere una autorizacion humana futura que
incluya la frase decimal exacta `Ejecuta las tareas pendientes de la Fase F10.9`
y el alcance adicional indicado. Un gate en `PASS` tampoco concede el siguiente.

## Estado De Ejecucion Del Plan

Snapshot documental: `2026-08-09`. Este bloque registra el estado observado;
no autoriza pushes, aprobaciones, merges ni operaciones remotas.

| Paquete | Estado | Evidencia o blocker vigente |
|---|---|---|
| `R0` | `COMPLETED_POST_MERGE_VERIFIED` | CA2 preservado en `archive/f10-9-ca2-preserve-desarrollo-20260809@8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc` / tree `13d3926f21b65abc73d1e8ef6e4305b2d61e0c77`; PR #329 fue fusionado en `certificacion@4f16f314284324c3b5e9c11c4536eef5ee04c7f3` y PR #328 en `desarrollo@4dcbb3fd792c25b16627f663fde31e40229718ce`, ambos con checks post-merge PASS. |
| `P1` | `COMPLETED_POST_MERGE_VERIFIED` | PR #331 integro el wiring fail-closed en `4f47836a8c80bbab396e30ed65f424e58e772987`; PR #332 integro el candidate estabilizado en `desarrollo@53921e3ec845f4a248e586a0ecd667c64f4c070d` / tree `0344c649772aea18314fe022d5f24898e3dc03d0`. Security Audit `31350585499=PASS` y F9.7 `31350585516=PASS` post-merge. PR #330 fue cerrado como `SUPERSEDED_NON_PROMOTABLE`. |
| Wiring `P2` | `IN_PROGRESS_LOCAL_VALIDATION_PENDING` | Rama `ci/f10-9-p2-boundary` desde el tip protegido post-P1; solo boundaries, workflows, tests y reconciliacion documental. No contiene los cuatro paths funcionales P2. |
| `P2`-`P5`/`P7` | `NOT_STARTED_REQUIRES_SEPARATE_AUTHORIZATION` | G0 queda `PASS/GO_G1_P2`, pero el resultado del gate no autoriza implementar estos paquetes. |
| `P6` | `DEFERRED_OUTSIDE_F10_9_REQUIRES_REBASELINE` | La frontera CA1-only prohibe SQL/schema/migrations/DDL/DML/backfill. |
| Data plane | `NOT_AUTHORIZED` | Cero lecturas Production, repair apply, DDL/DML, provider calls, backfill o re-enrichment autorizados por este documento. |
| Observacion | `NOT_STARTED` | Pares aceptados `0`; cualquier secuencia empieza despues de remediacion promovida y habilitacion operacional nueva. |

Validacion documental local de este snapshot:

- los seis targets de enlaces tocados por esta actualizacion existen;
- `git diff --check` y credential scan pasan;
- el Context Graph global de `origin/main` queda
  `BLOCKED_INHERITED_CONTEXT_GRAPH`: el tree selectivo contiene `11` archivos
  Markdown bajo `.context`, `135` enlaces locales observados y `78` targets
  ausentes heredados;
- este paquete no restaura esos documentos ni puede declarar Context Graph PASS;
  R0 debe reconciliar el graph desde el ancestry protegido sin importar CA2 ni
  inventar contenido.

### R0 - Reconciliacion De Repositorio Y Boundaries

`R0` es un prerrequisito de gobierno y release; no reemplaza ningun `WP-REM`.
Su objetivo es recuperar `main <= certificacion <= desarrollo`, preservar CA2 y
obtener un baseline protegido desde el cual implementar la remediacion.
El runbook operativo no ejecutable es
[G0-R0-F10.9](./g0_r0_reconciliacion_f10_9.md).

Secuencia obligatoria:

1. Estabilizar un boundary CI F10.9 fail-closed para reconocer por baseline,
   parentage, tree, manifest y paths exactos la reconciliacion autorizada.
2. Validar PR #329 `main -> certificacion`; exigir CI verde y aprobacion humana
   posterior al ultimo push; fusionar solo mediante merge commit humano.
3. Incorporar el tip protegido resultante de `certificacion` a la rama de PR
   #328 mediante merge normal, sin rebase ni force-push.
4. Verificar que el archive CA2 conserva commit/tree y que el tree final de la
   reconciliacion coincide con el tip certificado; exigir CI y review nuevos.
5. Despues del merge humano de #328, integrar primero el wiring fail-closed P1
   desde `ci/f10-9-p1-boundary`, con validator independiente, CI y review humano.
6. Solo despues de ese merge y sus checks post-merge, reconstruir P1 desde el
   nuevo tip protegido de `desarrollo`, sin arrastrar ancestry de #330. El diff
   P1 aislado debe contener exactamente:

```text
M scripts/shared/db_client.py
A scripts/shared/safe_http.py
A scripts/shared/url_identity.py
M scripts/shared/utils.py
A tests/test_fase10_9_p1_safety_contracts.py
```

7. Ningun PR se aprueba o fusiona automaticamente. Un push posterior invalida
   reviews previas y exige nueva aprobacion conforme a branch protection.

Gate de salida `R0`:

```text
main_is_ancestor_of_certificacion = true
certificacion_is_ancestor_of_desarrollo = true
ca2_archive_commit_tree_match = true
p1_diff_paths = exact_allowlist
context_graph_broken_links = 0
required_checks = success
human_review_after_last_push = approved
post_merge_desarrollo_checks = success
```

### P1 - Contratos Compartidos De Seguridad

P1 cubre identidad URL versionada, transporte HTTP seguro y separacion de
retries DB. Antes de integrarlo debe cerrar estos controles:

- pinning en el transporte real sin monkey-patch process-global de DNS;
- TLS/SNI y hostname verification preservados;
- userinfo, puertos no autorizados, destinos no publicos y proxies implicitos
  rechazados;
- redirects limitados y revalidados en cada salto;
- timeout total y bytes de respuesta acotados;
- logs con reason codes sanitizados, sin URL, host, query, UUID o payload;
- mutaciones DB sin replay ciego despues de resultados ambiguos.

Gate de salida P1: diez pruebas focused y nuevos casos SSRF PASS, `py_compile`
PASS, diff exacto, credential scan PASS, security-auditor sin blockers, PR
protegido aprobado/fusionado y checks post-merge de `desarrollo` PASS.

## Mapeo P1-P7 A Work Packages

Los paquetes `P1`-`P7` son cortes de implementacion. Los `WP-REM-01..09`
siguen siendo la taxonomia funcional del plan y no cambian de identidad.

| Paquete | Alcance de implementacion | WP-REM cubiertos | Salida requerida |
|---|---|---|---|
| `P1` | URL identity, transporte seguro y retries DB | Fundacion transversal para `02`, `04`, `06`, `07` y `09` | Contratos compartidos integrados y tests offline PASS. |
| `P2` | Auditor y planners read-only de duplicados, lifecycle, referencias, perfiles y metadata | `02`, `03`, `04`, `08`, `09` | Conteos/reason codes sanitizados, fingerprints y manifests sin apply. |
| `P3` | Preflight FG2 y contrato fail-before-write/global-partial | `02`, `06` | Cero writer calls ante blocker; NOOP diferenciado de source failure; cohorte/run manifest. |
| `P4` | FG3 `probe -> classify -> aggregate -> apply -> verify` | `07`, `09` | Cero mutaciones ante inconcluso; GET confirmatorio; exact-one y segundo NOOP. |
| `P5` | Gate metadata exclusivamente read-only/fail-closed | Parte no mutante de `08` | Cohorte/digest exactos y salida no cero; sin provider, writer, re-enrichment ni backfill. |
| `P6` | `DEFERRED_OUTSIDE_F10_9_REQUIRES_REBASELINE` | Propuestas mutantes de `03`, `04`, `05` y `08` | No produce SQL, migrations, DDL/DML ni tooling dentro de F10.9. |
| `P7` | Candidate integrado CA1 runtime, workflows, evidencia y regresion | Partes no mutantes/runtime de `02`, `06`, `07`, `08` y `09` | Candidate inmutable validado en `desarrollo`; promociones quedan en gates posteriores. |

`WP-REM-01` es contencion operacional y no se considera completado por codigo
local. Requiere una atestacion remota separada antes de cualquier lectura o
writer contra ambientes.

## Linea Base Read-Only

| Hallazgo | Valor observado |
|---|---:|
| Grupos URL normalizados duplicados | `38` |
| Filas staging excedentes | `281` |
| Filas globales stale en `processing` | `798` |
| Resultados FG3 inconclusos | `24` |
| Cursos activos incompletos post-run | `104` |
| Cursos activos totales post-run | `224` |

Las cantidades son un snapshot diagnostico y deben recalcularse con fingerprint
antes de decidir si la remediacion cabe en CA1. No autorizan apply. Si alcanzar
los umbrales exige DDL/DML/backfill, F10.9 produce `STOP_REQUIRES_REBASELINE`.

## Frontera De Este Plan

Permitido tras autorizacion especifica:

- Contencion mediante kill switches.
- Codigo y tests CA1 para preflight, clasificacion y observabilidad.
- Planners read-only sin modo apply.
- Correcciones runtime/perfil que no modifiquen schema ni datos operativos y
  permanezcan dentro de la frontera CA1.

Prohibido sin aprobacion adicional:

- DDL y DML de reparacion ad hoc Free o Pro, incluso con la frase F10.9.
- Deletes o repointing masivos.
- Re-enrichment/backfill.
- SQL, migrations, RLS, RPC, grants o tooling capaz de aplicar packages DB.
- Schedules, retries y dispatches.
- Bypass de WAF/CAPTCHA o terminos de fuentes externas.
- Debilitar SSRF, exact-one, kill switch o salida no cero.
- Cualquier alcance CA2.

Las mutaciones ordinarias de los writers CA1 FG2/FG3 no son una remediacion DML
ad hoc. Solo pueden ocurrir por los workflows aprobados despues de
G11=`GO_SCHEDULES`, con kill switches revalidados, en G12/G13. No habilitan SQL,
repair apply, updates manuales, backfill ni escritura fuera de la cohorte natural.

## WP-REM-01 - Contencion

1. Aplicar `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true` a
   `Production-Scheduled-FG2` y `Production-Scheduled-FG3`.
2. Confirmar cero runs queued, waiting o in-progress.
3. Congelar SHA/tree y metadata de environments sin leer secret values.
4. Preservar logs sanitizados y conteos de mutaciones parciales.
5. No reintentar automaticamente.

La contencion requiere atestacion operacional separada; este documento no afirma
que ya fue ejecutada.

## WP-REM-02 - Preflight Read-Only FG2

Implementar un preflight anterior a cualquier writer que detecte:

- identidad URL normalizada duplicada;
- estados desconocidos o stale `processing`;
- payload/hash conflictivo;
- referencias downstream;
- perfil `hardcoded_urls` sin seeds;
- perfil habilitado sin discovery valido;
- fuente inaccesible bajo transportes autorizados.

El preflight debe emitir solo reason codes y conteos sanitizados. Cualquier
hallazgo bloqueante impide harvesting completo y garantiza cero mutaciones.

Reason codes minimos:

```text
DUPLICATE_NORMALIZED_URL
STALE_PROCESSING
CONFLICTING_CONTENT_HASH
DOWNSTREAM_REFERENCE_CONFLICT
INVALID_EMPTY_HARDCODED_PROFILE
SOURCE_ACCESS_403
SOURCE_TIMEOUT
```

## WP-REM-03 - Recuperacion De Lifecycle

El planner read-only pertenece a F10.9. Cualquier apply de transicion de estado
queda `DEFERRED_OUTSIDE_F10_9_REQUIRES_REBASELINE`.

Antes de deduplicar, un planner debe clasificar las `798` filas stale:

| Evidencia | Estado candidato |
|---|---|
| Downstream limpio valido | `processed` |
| Payload valido sin downstream | `pending` |
| Sin payload valido | `discovered` |
| Evidencia contradictoria | `HOLD_MANUAL` |
| Dependencias incompatibles | `HOLD_DEPENDENCY_CONFLICT` |

La antiguedad por si sola nunca autoriza transicion. El planner termina en
clasificacion/fingerprint; cualquier apply produce `STOP_REQUIRES_REBASELINE`.

## WP-REM-04 - Deduplicacion Determinista

La clasificacion/fingerprint read-only pertenece a F10.9. Repoint, archive,
retire o DELETE quedan `DEFERRED_OUTSIDE_F10_9_REQUIRES_REBASELINE`.

La unidad de reparacion es `normalization_version + normalized_url`. La
seleccion de survivor prioriza:

1. referencia downstream unica;
2. payload y content hash validos;
3. `processed` demostrado;
4. `pending` valido;
5. `discovered`;
6. timestamp atribuible;
7. UUID como desempate final.

Grupos con hashes distintos, multiples linajes o contradicciones quedan HOLD.
El planner puede describir survivor/losers/referencias esperados, pero no genera
ni ejecuta transacciones, repoint, archive, retire o DELETE dentro de F10.9.

Postcondiciones:

```text
pre_rows - retired_rows = post_rows
retired_rows = archived_rows
orphan_references = 0
normalized_duplicate_groups = 0
second_apply = NOOP
```

## WP-REM-05 - Prevencion De Duplicados

Propuesta historica no ejecutable en Hito 1 CA1-only. Requiere rebaseline de la
autoridad superior o traslado a otro hito antes de redactar ADR/SQL/migration:

- funcion SQL immutable de normalizacion versionada;
- columna generada `normalized_url`;
- indice diagnostico antes del repair;
- unicidad global despues de cero colisiones;
- FK fisica `cleansed_programs.staging_id -> staging_raw.id` con delete
  restrictivo, despues de resolver orphans;
- claim/upsert atomico por identidad normalizada;
- tests de paridad Python/PostgreSQL y concurrencia.

No se crea ADR ni migracion dentro de F10.9.

## WP-REM-06 - Source Access Y Perfiles

Los perfiles live afectados no pueden permanecer como `hardcoded_urls` con seeds
vacios y fallback silencioso. La remediacion debe:

1. fallar configuracion invalida antes de red;
2. diagnosticar sitemap/robots/GET/Playwright desde runner;
3. usar browser/stealth solo cuando el perfil lo autorice;
4. versionar seeds oficiales o flags demostrados;
5. mantener `discovery_enabled=false` si ninguna ruta autorizada funciona;
6. requerir waiver explicito si la fuente no puede operar globalmente.

No se permite proxy, CAPTCHA bypass ni evasion no autorizada.

## WP-REM-07 - Hardening FG3

Separar probe HTTP, clasificacion, decision y persistencia. Contrato:

| HEAD | Accion final |
|---|---|
| `2xx` | Saludable sin GET. |
| `403` | GET acotado; persistente queda inconcluso. |
| `405/501` | GET acotado. |
| `404/410` | GET obligatorio antes de mutar. |
| `408/425/429/5xx` | Retry acotado con backoff. |
| Timeout/DNS/TLS | Retry acotado y taxonomia explicita. |

Maximo tres intentos por URL, presupuesto temporal, `Retry-After` limitado y
validacion SSRF/pinning en cada redirect. Un inconcluso nunca cambia
`last_404_at` ni `is_active` y produce salida no cero.

Las mutaciones deben ser condicionales, exact-one, idempotentes y capaces de
reconciliar `ALREADY_APPLIED` sin aceptar conflicto.

## WP-REM-08 - Gate De Metadata

La decision humana vigente establece gate cero para cursos activos con syllabus
u objectives faltantes. El conteo incluye null, blank y placeholders.

Los `104` registros tienen texto limpio atribuible, pero no campos enriquecidos
utiles para backfill directo. F10.9 solo puede medir y bloquear. Re-enrichment,
fill-only o cualquier writer/backfill estan prohibidos por la frontera CA1-only.
Si el conteo no puede llegar a cero sin mutacion editorial, el resultado es
`STOP_REQUIRES_REBASELINE`, no una autorizacion de writer.

## WP-REM-09 - Verificacion De Mutaciones Previas

Los dos flags y una desactivacion del run FG3 deben revalidarse mediante GET. Si
GET confirma `404/410`, se preserva el estado. Si demuestra `2xx`, cualquier
restauracion queda `STOP_REQUIRES_REBASELINE`. No ejecutar limpieza masiva de
`last_404_at`.

## Matriz De Pruebas

FG2 debe cubrir:

- preflight cero mutaciones;
- duplicados, hashes, stale states y referencias;
- perfil hardcoded vacio;
- NOOP valido vs source failure;
- planner read-only determinista y segundo planner NOOP semantico;
- corpus URL Python versionado sin SQL;
- dos planners concurrentes sin writes;
- source access sintetico.

FG3 debe cubrir:

- HEAD/GET `2xx`, `403`, `405`, `404`, `410`;
- retries `429/5xx/timeout`;
- redirect SSRF y DNS pinning;
- first flag, grace, deactivate y recovery;
- inconcluso cero mutaciones;
- exact-one, idempotencia y conflicto;
- paginacion mayor a 1000 y TimeGuard;
- gate metadata `0`.

## Rollout

La remediacion se ejecuta en los siguientes gates. Un gate no concede el
siguiente y cada operacion remota requiere la autorizacion indicada.

### G0 - Baseline Protegido R0/P1

Entrada: F10.9 activa, ramas protegidas identificadas y archive CA2 congelado.

Runbook: [G0-R0-F10.9](./g0_r0_reconciliacion_f10_9.md).

Acciones completadas: R0 y P1 fueron integrados mediante PR protegidos, con
review humano y checks post-merge verdes en `desarrollo`.

Salida observada: `desarrollo@53921e3ec845f4a248e586a0ecd667c64f4c070d`,
tree `0344c649772aea18314fe022d5f24898e3dc03d0`, manifest exacto P1 y ancestry
protegido. Resultado `G0=PASS/GO_G1_P2`.

Aprobacion consumida solo para G0. El resultado no habilita merge automatico,
P2 funcional ni red remota.

### G1 - P2 Planners Offline

Entrada: G0 PASS.

Acciones: implementar auditor paginado y planners read-only para URL identity,
stale lifecycle, dedup, referencias, perfiles, metadata y mutaciones previas.
Todos deben operar sobre fixtures sinteticos por defecto y no incluir modo apply.

Salida: reason codes, fingerprints, clasificaciones HOLD y manifests
sanitizados reproducibles.

Aprobacion pendiente: frase decimal F10.9 mas codigo/tests P2 local. No autoriza
red remota.

Antes de implementar G1/P2 debe integrarse un wiring fail-closed separado que
reconozca exclusivamente `feat/f10-9-p2-readonly-planners`, su baseline
protegido post-wiring y los cuatro paths exactos de P2. Ese wiring no cuenta como
inicio de P2 ni concede su autorizacion.

### G2 - P3/P4 Runtime Fail-Closed

Entrada: G1 PASS y contratos read-only congelados.

Acciones: integrar preflight FG2 fail-before-write, manifest de cohorte y
orquestacion partial-global; separar FG3 en probe/classify/aggregate/apply/verify.

Salida: suites sinteticas que demuestren cero writes ante blocker/inconcluso,
exact-one, `ALREADY_APPLIED` reconciliado y segundo run NOOP.

Aprobacion pendiente: frase decimal F10.9 mas codigo/tests P3/P4 local. No
autoriza ejecucion de workers remotos.

### G3 - P5 Metadata Read-Only

Entrada: G2 PASS y definicion aprobada de missing = null/blank/placeholder.

Acciones: implementar planner de cohorte read-only que incluya null, blank y
placeholders y produzca conteo/digest sanitizado.

Salida: gate determinista que retorna no cero cuando exista un curso activo
incompleto y demuestra cero writer/provider calls.

Aprobacion pendiente: frase decimal F10.9 mas codigo/tests P5 local. No autoriza
provider remoto, writer, re-enrichment ni backfill.

### G4 - Decision De Autoridad Por Hallazgos Mutantes

Entrada: G1-G3 PASS y planners sin apply con conteos/fingerprints vigentes.

Acciones: determinar si duplicados, stale lifecycle o metadata pueden resolverse
solo con runtime CA1 y sin modificar schema/datos. No se redacta SQL ni se
ejecutan providers.

Salida: `PASS_CA1_RUNTIME_ONLY` o `STOP_REQUIRES_REBASELINE`. El segundo resultado
bloquea G5 y exige una decision de la autoridad superior fuera de F10.9.

Aprobacion pendiente: frase decimal F10.9 para registrar la decision. No autoriza
P6, SQL, DDL/DML, backfill ni cambios editoriales.

### G5 - P7 Candidate Integrado

Entrada: G1-G3 PASS y G4=`PASS_CA1_RUNTIME_ONLY`.

Acciones: integrar P2-P5 dentro de la frontera CA1, workflows en estado pausado,
tests y evidencia; abrir PR protegido a `desarrollo` y ejecutar security-auditor.

Salida: candidate commit/tree/digest inmutable y CI de `desarrollo` PASS. No
promueve a `certificacion` ni exige QA Certification en este gate.

Aprobacion pendiente: frase decimal F10.9 mas codigo/tests/PR P7. Cada promocion
requiere alcance remoto y review humano separados.

### G6 - Contencion Operacional Atestada

Entrada: antes del primer acceso remoto a environments o data plane. Los pushes,
CI, reviews y merges Git de G0/G5 no cuentan como acceso data plane.

Acciones: verificar kill switches de FG2/FG3, cero runs activos y metadata de
environments sin leer valores secretos.

Salida: atestacion sanitizada con SHA/tree y estado fail-closed.

Aprobacion pendiente: frase decimal F10.9 mas operacion GitHub de contencion.

### G7 - Promocion Certification

Entrada: G5 y G6 PASS.

Acciones: reconstruir el patch CA1 sobre el tip protegido de `certificacion`,
ejecutar CI, canary acotado permitido y QA independiente.

Salida: equivalencia patch/tree/digest, CI PASS, canary sin mutacion fuera de la
frontera y QA PASS.

Aprobacion pendiente: frase decimal F10.9 mas promocion/canary Certification.

### G8 - Promocion Main

Entrada: G7 PASS y candidate certificado inmutable.

Acciones: promover exclusivamente el patch CA1 certificado mediante PR protegido
a `main`; observar checks y deployment sin ejecutar schedules.

Salida: main SHA/tree/digest, CI post-merge PASS, cero paths CA2/DB/editoriales y
writers programados aun pausados.

Aprobacion pendiente: frase decimal F10.9 mas promocion main/release SDLC.

### G9 - Diagnostico Production Read-Only

Entrada: G8 PASS y contencion G6 revalidada.

Acciones: ejecutar preflight FG2, source probes autorizados, FG3 probe-only y
gate metadata sin writers. No se usa Free como ruta de aplicacion.

Salida: cero blockers runtime CA1, cero inconclusos, cero perfiles invalidos y
cero cursos activos incompletos. Cualquier necesidad de mutacion produce STOP.

Aprobacion pendiente: frase decimal F10.9 mas diagnostico Production read-only.

### G10 - Gate Final Antes De Schedules

Entrada: G9 PASS.

Acciones: congelar candidate/runtime/config, revalidar kill switches, branch
policy, cron main-only y ausencia de runs activos.

Salida: autorizacion-ready manifest para habilitacion gradual, sin cambiar
variables ni schedules en este gate.

Aprobacion pendiente: frase decimal F10.9 para preparar el manifest; no habilita
schedules.

### G11 - Decision GO/NO-GO De Habilitacion

Entrada: G10 PASS y manifests vigentes.

Acciones: confirmar que todos los hallazgos estan en cero sin DDL/DML/backfill y
que la remediacion permanece CA1-only.

Salida: `GO_SCHEDULES` o `STOP_REQUIRES_REBASELINE`.

Aprobacion pendiente: decision humana F10.9. No autoriza DDL/DML/backfill.

### G12 - Diagnostico Y Habilitacion Gradual

Entrada: G11=`GO_SCHEDULES`.

Acciones: FG2 preflight global, source probes autorizados, FG3 probe-only y gate
metadata; despues habilitar FG2 y, solo tras su primer natural completo, FG3.

Salida: primer par natural valido. Dispatches y reruns no cuentan.

Aprobaciones pendientes: frase decimal F10.9 mas diagnosticos, variables y
schedules, todas separadas.

### G13 - Observacion Y Cierre F10.9

Entrada: primer FG2 natural valido posterior a remediacion.

Acciones: registrar tres pares naturales FG2 -> FG3 consecutivos durante al
menos 72 horas, sin drift de SHA, config, profile, secrets o runtime.

Salida: `EVID-H1-011/012=VERIFIED` solo si se cumplen todos los umbrales. Para
`EVID-H1-013` tambien se exige Production Canary FG1 PASS y cron mensual FG1
activo/main-only; cualquier waiver requiere decision separada. `EVID-H1-016` y
F11.1 permanecen como aprobacion/cierre posterior separado.

Aprobacion pendiente: frase decimal F10.9 mas habilitacion de observacion. F11.1
no queda autorizada.

## Manifest Minimo Por Gate

Cada gate genera un manifest privado y una proyeccion sanitizada. Git conserva
solo la proyeccion sin URLs, UUID, hosts, payloads ni secretos.

| Campo | Requisito |
|---|---|
| Identidad | `plan_id`, gate, ambiente, run/PR y timestamp UTC. |
| Codigo | base SHA/tree, candidate SHA/tree, parents y digest del diff. |
| Alcance | allowlist/denylist de paths, cohort fingerprint y normalization version. |
| Datos | schema fingerprint, conteos before/after, HOLD, writes esperados/reales y non-cohort counts. |
| Seguridad | reason codes, credential scan, SSRF tests y secrets presentes solo por nombre. |
| Operacion | kill switches, writer pause, backup/restore, exact-one y segundo NOOP. |
| Decision | resultado `PASS`, `FAIL` o `STOP`, approver requerido y expiracion del manifest. |

Un manifest expira ante cambio de SHA/tree, schema, cantidades, profile,
dependencias, environment o normalization version.

## Validaciones Por Candidate

Todo comando Python/npm/pip corre dentro de Docker conforme a `AGENTS.md`.

Validaciones minimas:

```text
focused_unit_integration = PASS
python_compile = PASS
postgresql_17_replay_rollback = PASS cuando aplique
actionlint = PASS cuando cambien workflows
shellcheck = PASS cuando cambie shell
credential_scan = PASS
security_auditor = NO_BLOCKERS
context_graph = PASS
markdown_links = PASS
git_diff_check = PASS
```

P2-P5/P7 deben agregar pruebas para paginacion mayor a 1000, concurrencia,
fingerprint drift, exact-one, segundo NOOP, redirects SSRF, DNS rebinding,
timeouts, `403/404/410/429/5xx`, profiles invalidos, provider no invocado y cero
mutaciones ante blocker.

## Rollback Y Stop

- Drift de cantidades, schema, SHA, profile o dependency produce STOP.
- Fallo de backup/restore, exact-one, segundo NOOP o non-cohort attestation
  produce STOP.
- Cualquier necesidad de SQL, DDL/DML o mutacion editorial produce
  `STOP_REQUIRES_REBASELINE`; no se improvisa una ruta de apply.
- Cualquier cambio runtime/config durante observacion reinicia la secuencia.

## Aprobaciones Separadas

| Accion | Gate requerido |
|---|---|
| Boundaries/reconciliacion R0 | F10.9 Git/CI y review humano por PR |
| P1-P7 codigo/tests/docs | F10.9 y PR protegido por package |
| Kill switch | Operacion F10.9 |
| Promocion/canary Certification | Aprobacion Certification |
| Promocion a main | Aprobacion release/SDLC |
| Diagnostico Production read-only | Aprobacion read-only F10.9 |
| Schedules/retries/dispatches | Aprobacion F10.9 posterior; no acreditan observacion si son manuales |
| Observacion natural 72h | Aprobacion de habilitacion F10.9 |
| Conformidad y cierre | F11.1 y aprobacion cliente separadas |

DDL, DML de reparacion ad hoc, SQL/migrations y re-enrichment/backfill no tienen
gate aprobable dentro de F10.9. Requieren rebaseline de autoridad superior o
traslado a otro hito. Esta prohibicion no convierte en ad hoc las mutaciones
ordinarias y cohort-bound de FG2/FG3 posteriores a `GO_SCHEDULES`.

## Criterio De Salida

- Cero duplicados normalizados y cero stale `processing`.
- Cero perfiles invalidos habilitados.
- FG2 completo SUCCESS/NOOP en todas sus estaciones.
- Cero cursos activos incompletos.
- FG3 cohorte completa, cero inconclusos y mutaciones confirmadas.
- Tres pares naturales FG2 -> FG3 consecutivos durante al menos 72h.
- `EVID-H1-011..013=VERIFIED` solo despues de cumplir todos los umbrales.

## Evidencia

El ledger append-only es
[EVID-H1-OBS-F10.9-001](../evidencias_cliente/sprint_1/registro_observacion_production_f10_9_2026-08-09.md).

Este plan no autoriza ejecucion, DDL/DML, backfill, schedules ni merge.
