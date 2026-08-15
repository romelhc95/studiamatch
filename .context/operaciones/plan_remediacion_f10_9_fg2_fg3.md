# PLAN-REM-F10.9-001 - Remediacion FG2/FG3 Post-Activacion Programada

| Campo | Valor |
|---|---|
| ID | `PLAN-REM-F10.9-001` |
| Estado | `REBASELINED_FG2_FG3_OPERATIONAL_REMEDIATION` |
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

Ninguna seccion o gate concede ejecucion. ADR-0011 fija
`G4=PASS_CA1_FG2_FG3_ONLY_METADATA_TRANSFERRED_TO_H2` y reabre G5-G13 solo para
aprobaciones separadas. Un gate en PASS tampoco concede el siguiente.

## Estado De Ejecucion Del Plan

Snapshot documental: `2026-08-10`. Este bloque registra el estado observado;
no autoriza pushes, aprobaciones, merges ni operaciones remotas.

| Paquete | Estado | Evidencia o blocker vigente |
|---|---|---|
| `R0` | `COMPLETED_POST_MERGE_VERIFIED` | CA2 preservado en `archive/f10-9-ca2-preserve-desarrollo-20260809@8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc` / tree `13d3926f21b65abc73d1e8ef6e4305b2d61e0c77`; PR #329 fue fusionado en `certificacion@4f16f314284324c3b5e9c11c4536eef5ee04c7f3` y PR #328 en `desarrollo@4dcbb3fd792c25b16627f663fde31e40229718ce`, ambos con checks post-merge PASS. |
| `P1` | `COMPLETED_POST_MERGE_VERIFIED` | PR #331 integro el wiring fail-closed en `4f47836a8c80bbab396e30ed65f424e58e772987`; PR #332 integro el candidate estabilizado en `desarrollo@53921e3ec845f4a248e586a0ecd667c64f4c070d` / tree `0344c649772aea18314fe022d5f24898e3dc03d0`. Security Audit `31350585499=PASS` y F9.7 `31350585516=PASS` post-merge. PR #330 fue cerrado como `SUPERSEDED_NON_PROMOTABLE`. |
| Wiring `P2` | `COMPLETED_POST_MERGE_VERIFIED` | PR #333 aprobado/fusionado en `desarrollo@d5433ea9f810b0338513665bb95ba28715c6c8b5` / tree `24a270f314b46728d5ae9847dafba0ff1999be7f`; Security Audit `31354339105=PASS` y F9.7 `31354339122=PASS` post-merge. |
| `P2` | `COMPLETED_POST_MERGE_VERIFIED` | PR #335 integro los cuatro paths exactos mediante `desarrollo@0d87060837586603055ca91629b20815803b3239` / tree `9c04cd75d47654fd8cfb3058b65e8846afd3c5e5`; Security Audit `31361988478=PASS` y F9.7 `31361988498=PASS` post-merge. Ver [evidencia G1/P2](./g1_p2_post_merge_evidence_2026_08_10.md). |
| `P3`-`P4` | `COMPLETED_POST_MERGE_VERIFIED` | PR #338 integro runtime FG2/FG3 fail-closed en `desarrollo@945f17cb597dc4ae960278a1fbae86c1a2043dc9` / tree `f448ac27c8abf5f2dbbb77da0ece6c82861f0028`; Security Audit `31389283184=PASS` y F9.7 `31389282945=PASS` post-merge. Ver [evidencia G2/P3-P4](./g2_p3_p4_post_merge_evidence_2026_08_10.md). |
| `P5` | `COMPLETED_POST_MERGE_VERIFIED` | PR #341 integro el gate local read-only en `desarrollo@1c5d1526a1da247ca6ad0eb7b25cd5e0b0f51564` / tree `8eb146006419d93dc0a74710ca9efaaf101ab280`; Security Audit `31409222936=PASS` y F9.7 `31409222568=PASS` post-merge. Ver [evidencia G3/P5 y decision G4](./g3_p5_post_merge_g4_decision_2026_08_10.md). |
| `ADR-0011` | `COMPLETED_POST_MERGE_VERIFIED` | PR #375 integrado en `desarrollo@2c9d2438c5fc309d3692d1a1de1233e0fcc95afc` / tree `161a8df69bf5e527c4ba863891504551ec5f7aa7`; Security Audit `31768101859=PASS` y F9.7 `31768101887=PASS`. |
| `G5` | `REMEDIATED_REPOSITORY_ONLY_V2_3_TRUST_STOP` | PR #382 integro repository-only v2.2 mediante candidate `8a6724a5850792383456763a119c925c53961f2a` y merge protegido `58e0a0b37f7a3795e9487ab01aa558b5ecaa6ae3` / tree `13eb0465233c9e870995763630ee9e6541a45add`; Security Audit `31861308128=PASS`, F9.7 `31861308133=PASS` y focused `94955078030=159 PASS`. Su resultado exclusivo fue `MERGED_POST_MERGE_CI_PASS_ROUTING_REMEDIATION_REQUIRED`; v2.2 queda `HISTORICAL_ANTECEDENT_NOT_FIT_FOR_CONNECTED_MODE`. El [sucesor offline GET-only v2.3](./g5_get_only_adapter_contract_2026_08_14.md) es candidate local pendiente de promocion en un nuevo PR; usa `SourceAttemptResult`, decision causal en earliest valid source attempt (sin bundles, cierre snapshot 1), FILTER literal URL completa/regex text 2000, subset lineal que rechaza agrupacion/alternancia/cuantificadores no escapados, rechazo localhost/IP no global y `circuit_opened_at` dormido fingerprint-only. FG3 exige `category_counts=3` y `courses/prior_mutations/history<=50000`; `65/50001 -> STOP_G5_TARGET_BINDING_INVALID`. Conserva cooldown 24h, exact-one, redirects sin autoridad y profiles no elegibles sin probes. La divergencia NULL preflight bloquea v2.3 y preflight/workers no cambian. Valida estructura y termina `STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`; gate `NOT_CREATED_NOT_APPROVED_NOT_CONSUMED`, connected mode `STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED`. |
| `P7` | `REOPENED_AUTHORIZATION_REQUIRED` | Integracion CA1 FG2/FG3 despues de cerrar gates operativos separados. |
| `P6` | `DEFERRED_OUTSIDE_F10_9_REQUIRES_REBASELINE` | La frontera CA1-only prohibe SQL/schema/migrations/DDL/DML/backfill. |
| Data plane | `NOT_AUTHORIZED` | Cero lecturas Production, repair apply, DDL/DML, provider calls, backfill o re-enrichment autorizados por este documento. |
| Observacion | `NOT_STARTED` | Pares aceptados `0`; exige tres pares naturales consecutivos durante al menos 72 horas. |

Validacion documental local vigente de este snapshot:

- los targets de enlaces tocados por esta actualizacion existen;
- `git diff --check` y credential scan pasan;
- el Context Graph contiene `66` archivos Markdown, `403` enlaces locales y
  `0` targets rotos;
- el blocker heredado de Context Graph registrado en el snapshot inicial quedo
  superado por R0 y no permanece como accion pendiente;
- G1/P2, G2/P3-P4 y G3/P5 quedan trazados por evidencia separada. El resultado
  consumido G4=STOP permanece historico; ADR-0011 lo supersede para estado vivo.

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
| `P7` | Candidate integrado CA1 runtime, workflows, evidencia y regresion | Partes CA1 de `02`, `06`, `07` y `09`; `08` transferido a H2 | Candidate inmutable validado en `desarrollo`; promociones quedan en gates posteriores. |

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
antes de decidir si la remediacion cabe en CA1. No autorizan apply. DDL,
backfill o DML fuera de los applies cohort-bound G6 expresamente aprobados
produce `STOP_REQUIRES_REBASELINE`.

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

El planner read-only historico pertenece a F10.9. ADR-0011 reabre cualquier apply
de transicion solo bajo `G6-B`, con candidate, manifest, aprobacion y rollback
separados; no autoriza SQL ad hoc, DDL ni ejecucion desde este documento.

Antes de deduplicar, un planner debe clasificar las `798` filas stale:

| Evidencia | Estado candidato |
|---|---|
| Downstream limpio valido | `processed` |
| Payload valido sin downstream | `pending` |
| Sin payload valido | `discovered` |
| Evidencia contradictoria | `HOLD_MANUAL` |
| Dependencias incompatibles | `HOLD_DEPENDENCY_CONFLICT` |

La antiguedad por si sola nunca autoriza transicion. El planner termina en
clasificacion/fingerprint. Solo un apply cohort-bound aprobado expresamente en
`G6-B` puede continuar; cualquier otro apply produce `STOP_REQUIRES_REBASELINE`.

## WP-REM-04 - Deduplicacion Determinista

La clasificacion/fingerprint read-only pertenece a F10.9. ADR-0011 reabre
repoint/archive/retire solo bajo `G6-A`, con candidate, manifest, aprobacion y
rollback separados. DELETE masivo y SQL ad hoc permanecen prohibidos.

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

## WP-REM-08 - Referencia Metadata Transferida

El snapshot `104/224` permanece visible e inmutable como
`TRANSFERRED_NON_BLOCKING_H2_CA2`. WP-REM-08 deja de ser gate bloqueante de Hito
1 y se conserva solo como referencia transferida. Re-enrichment, fill-only y
backfill siguen prohibidos en F10.9.

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

Aprobacion consumida para codigo/tests P2 local read-only/offline. No autoriza
red remota, data plane ni acciones de apply.

El wiring fail-closed fue integrado mediante PR #333 y reconoce exclusivamente
`feat/f10-9-p2-readonly-planners`, su baseline protegido y los cuatro paths
exactos de P2. El candidate debe partir del tip protegido posterior a la
reconciliacion post-merge.

Salida observada: PR #335 fue aprobado sobre
`b7ac753873e712cd35b937dd9ed1cf66015a776a` y fusionado en
`desarrollo@0d87060837586603055ca91629b20815803b3239` / tree
`9c04cd75d47654fd8cfb3058b65e8846afd3c5e5`. Security Audit
`31361988478=PASS` y F9.7 `31361988498=PASS` verificaron el merge protegido.
La [evidencia G1/P2](./g1_p2_post_merge_evidence_2026_08_10.md) registra diff,
validaciones, capacidades desactivadas y manifest fail-closed. Resultado
`G1=PASS/GO_G2_AUTHORIZATION_REQUIRED`.

La aprobacion G1 fue consumida. Este PASS no autoriza G2/P3-P4, red remota,
data plane, workers ni apply.

### G2 - P3/P4 Runtime Fail-Closed

Entrada: G1 PASS y contratos read-only congelados.

Acciones: integrar preflight FG2 fail-before-write, manifest de cohorte y
orquestacion partial-global; separar FG3 en probe/classify/aggregate/apply/verify.

Salida: suites sinteticas que demuestren cero writes ante blocker/inconcluso,
exact-one, `ALREADY_APPLIED` reconciliado y segundo run NOOP.

Aprobacion consumida para codigo/tests P3/P4 local. PR #338 fue aprobado sobre
`b0674c9fd8fb4b91f63e0b0fc32f8d93b2a4afdc` y fusionado en
`desarrollo@945f17cb597dc4ae960278a1fbae86c1a2043dc9` / tree
`f448ac27c8abf5f2dbbb77da0ece6c82861f0028`. Security Audit
`31389283184=PASS` y F9.7 `31389282945=PASS` verificaron el merge protegido. La
[evidencia G2/P3-P4](./g2_p3_p4_post_merge_evidence_2026_08_10.md) registra el
boundary exacto, validaciones y capacidades desactivadas. Resultado
`G2=PASS/GO_G3_AUTHORIZATION_REQUIRED`.

Este PASS no autoriza G3/P5, red remota, data plane, workers, providers ni apply.

### G3 - P5 Metadata Read-Only

Entrada: G2 PASS y definicion aprobada de missing = null/blank/placeholder.

Acciones: implementar planner de cohorte read-only que incluya null, blank y
placeholders y produzca conteo/digest sanitizado.

Salida: gate determinista que retorna no cero cuando exista un curso activo
incompleto y demuestra cero writer/provider calls.

Aprobacion consumida para codigo/tests P5 local. PR #341 fue aprobado sobre
`46fd10864af2a90e407f6867adf980daa940b075` y fusionado en
`desarrollo@1c5d1526a1da247ca6ad0eb7b25cd5e0b0f51564` / tree
`8eb146006419d93dc0a74710ca9efaaf101ab280`. Security Audit
`31409222936=PASS` y F9.7 `31409222568=PASS` verificaron el merge protegido. Ver
[evidencia G3/P5 y decision G4](./g3_p5_post_merge_g4_decision_2026_08_10.md).
Resultado `G3=PASS`.

### G4 - Decision De Autoridad Por Hallazgos Mutantes

Entrada: G1-G3 PASS y planners sin apply con conteos/fingerprints vigentes.

Acciones: determinar si duplicados, stale lifecycle o metadata pueden resolverse
solo con runtime CA1 y sin modificar schema/datos. No se redacta SQL ni se
ejecutan providers.

Resultado historico consumido: `STOP_REQUIRES_REBASELINE`; permanece inmutable.
Decision superior efectiva ADR-0011:
`PASS_CA1_FG2_FG3_ONLY_METADATA_TRANSFERRED_TO_H2`. El snapshot `104/224` queda
visible como deuda H2 no bloqueante. G5-G13 se reabren bajo aprobaciones
separadas; no se autorizan P6, metadata, SQL ad hoc, DDL, backfill,
re-enrichment ni cambios editoriales.

### G5 - Diagnostico Production Read-Only

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Ejecuta solo conteos/reason codes y
fingerprints sanitizados. Debe identificar blockers CA1 de duplicados,
lifecycle, perfiles/fuentes, FG3 inconcluso, 404 y desactivacion. No incluye gate
metadata ni writers.

PR #376 integro v1 y queda `COMPLETED_POST_MERGE_VERIFIED`. El
[candidate repository-only G5 v2](./g5_v2_repository_only_candidate_2026_08_14.md)
versiona schema/algoritmo y corrige atribucion antes de cualquier adapter. Acepta
solo una fachada `select`/`count`, exige el orden
`snapshot_1 -> observations -> snapshot_2`, dos snapshots completos identicos,
evidencia privada por perfil/fuente/lifecycle/curso/run/cohorte y unidades con
denominadores publicos. La cohorte principal FG3 son cursos activos al inicio;
solo antecedentes privados atribuibles agregan inactivos. Historicos inactivos
no relacionados quedan fuera. El gate permanece
`NOT_CREATED_NOT_APPROVED_NOT_CONSUMED` y el entrypoint conectado termina
`STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` aun con precondiciones simuladas.

PR #380 fue fusionado y verificado, pero su contrato v2 queda
`MERGED_POST_MERGE_CI_PASS_REMEDIATION_REQUIRED`: no ligaba la duracion completa
de cada intento source y conservaba hallazgos strict Boolean/dataclass incompleta.
V2 se congela como antecedente no apto para connected mode, sin reinterpretacion silenciosa. El
[contrato offline GET-only](./g5_get_only_adapter_contract_2026_08_14.md) sucesor
versiona contrato/schema/algoritmo v2.1, consume solo datos pre-materializados,
liga cada HEAD/GET al intervalo completo, rechaza enteros en `is_active` y
estabiliza errores de dataclasses exactas incompletas. Despues de validar estructura,
termina
`STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`. Connected mode y gate permanecen
`STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED` y
`NOT_CREATED_NOT_APPROVED_NOT_CONSUMED`.

PR #381 fue fusionado mediante candidate
`51c24af3664a5d03ad16e16fa8793862cdb7fec1` en
`desarrollo@c998b0293b364b1c59d9c52824178927977f0b56`, tree
`d93843d4e08dfd9c45571b72040994926dffc221`; Security Audit
`31852148318=PASS` y F9.7 `31852148322=PASS`. V2.1 queda
`MERGED_POST_MERGE_CI_PASS_REMEDIATION_REQUIRED` y congelado como antecedente no
apto para connected mode. V2.2 deriva exact-one desde mutaciones inmutables,
impone causalidad `observations <= manifest <= anchor < snapshot_1`, aplica
`pipeline_enabled` con fallback explicito, deriva cobertura profile/source desde
configuracion y ejecuta su suite focused en candidate y post-merge antes del
checkout historico F9.7. No implementa transporte ni connected mode.

PR #382 integro v2.2 mediante candidate
`8a6724a5850792383456763a119c925c53961f2a` y merge protegido
`58e0a0b37f7a3795e9487ab01aa558b5ecaa6ae3`, tree
`13eb0465233c9e870995763630ee9e6541a45add`. Security Audit
`31861308128=PASS`, F9.7 `31861308133=PASS` y focused
`94955078030=159 PASS`. Resultado exacto
`MERGED_POST_MERGE_CI_PASS_ROUTING_REMEDIATION_REQUIRED`; v2.2 queda congelado
como `HISTORICAL_ANTECEDENT_NOT_FIT_FOR_CONNECTED_MODE`. El candidate local
sucesor v2.3 queda `REMEDIATED_REPOSITORY_ONLY_V2_3_TRUST_STOP`, pendiente de
promocion en un nuevo PR.

V2.3 deriva `EffectiveProfileRouting` mediante joins exact-one y bloquea la
divergencia de presencia/null de `pipeline_enabled`; solo la ausencia real usa
`pipeline_ready`. Distingue roles `PROBE_TARGET`, `TEMPLATE` y `FILTER`, y
materializa los entry targets estaticos reales de hardcoded, paginated catalog,
catalog-link y sitemap_bfs, incluidos website, sitemap, BFS y warmup cuando
corresponde. Configuracion dormida cambia fingerprints sin convertirse en target.
Nested sitemaps, catalog links extraidos y BFS children permanecen en la frontera
dinamica FG2. No modifica preflight ni workers.

V2.3 usa `SourceAttemptResult`; la decision causal de routing toma el earliest
valid source attempt y, sin bundles, el cierre de snapshot 1. Canonicaliza URL con
la identidad compartida, deduplica targets por
`(kind, canonical_url)`, valida regex fail-closed y deriva el circuito efectivo:
antes de 24h abierto, exactamente a 24h auto-closed. Profiles no elegibles ligan
configuracion/fingerprint sin probes; `circuit_opened_at` dormido es
fingerprint-only. FILTER literal compara URL completa y regex usa text 2000 bajo
un subset lineal que rechaza agrupacion, alternancia y cuantificadores no
escapados; localhost e IP no global se rechazan. `65` sources por profile o
`50001` pares termina `STOP_G5_TARGET_BINDING_INVALID`. FG3 exige
`category_counts=3` y acota temprano `courses/prior_mutations/history<=50000`.
Toda observacion
deactivation/prior participa en exact-one con su prior mutation. La clasificacion
cerrada `NO_REDIRECT_WITHOUT_DERIVATION_EVIDENCE` no concede autoridad ni trust.

El preflight legacy usa `pipeline_ready` cuando `pipeline_enabled` es NULL; v2.3
considera la presencia NULL un blocker. Esa divergencia y las demas reglas
preflight no reemplazan el routing efectivo del harvester. Preflight y workers no
cambian. Los budgets permanecen coherentes en 15 segundos: por snapshot para la
capability y por intento HEAD/GET para source evidence.

Los outcomes source se recomputan desde HEAD o HEAD-GET compatibles con
`safe_source_probe`, status y errores cerrados; solo accessible es GO-compatible.
Los blockers source y lifecycle permanecen separados. Lifecycle usa 24h exactas:
24h es `NOT_STALE`, 24h mas un microsegundo es `STALE`, y toda fila `processing`
debe ser `NOT_STALE`. Causalidad FG3, exact-one derivado y conteos `24/2/1`
siguen vinculantes. Trust conserva
`STOP_G5_TRUST_VERIFICATION_NOT_IMPLEMENTED`; gate
`NOT_CREATED_NOT_APPROVED_NOT_CONSUMED`; connected mode
`STOP_G5_CONNECTED_MODE_NOT_IMPLEMENTED`.

### G6 - Remediaciones Operativas CA1 Separadas

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Cada subgate requiere manifest,
aprobacion y rollback propios; ninguno concede el siguiente:

- `G6-A`: deduplicacion, repoint y archive; cero DELETE masivo.
- `G6-B`: transiciones lifecycle justificadas por evidencia.
- `G6-C`: correcciones de perfiles y fuentes sin debilitar SSRF.
- `G6-D`: revalidacion GET y restauracion FG3 de flags/404/desactivacion.

### G7 - Integracion P7 En Desarrollo

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Integra exclusivamente runtime CA1,
tests y evidencia por PR protegido a `desarrollo`; exige candidate inmutable, CI,
credential scan y security review PASS.

### G8 - Certification

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Reconstruye el patch CA1 sobre el tip
protegido de `certificacion`; exige equivalencia, CI y QA. No ejecuta metadata.

### G9 - Main

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Promueve solo el patch CA1 certificado
por PR protegido a `main`, con writers/schedules pausados. La salida exige CI
post-merge PASS y cero paths CA2/editoriales; metadata cero no es umbral.

### G10 - Freeze Operacional Pre-Schedules

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Congela SHA/tree/runtime/config y
revalida kill switches, branch policy, cron main-only y ausencia de runs activos.

### G11 - GO_SCHEDULES

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Confirma cero blockers CA1 de
duplicados, lifecycle, perfiles/fuentes, inconclusos FG3, 404 y desactivacion.
Salida: `GO_SCHEDULES` o STOP. Metadata cero no participa.

### G12 - Habilitacion Gradual Y Primer Par Natural

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Habilita FG2 y, solo despues de su run
natural completo, FG3. Salida: primer par natural valido. Dispatches y reruns no
cuentan.

### G13 - Observacion Natural Y Cierre F10.9

Estado: `REOPENED_AUTHORIZATION_REQUIRED`. Registra tres pares naturales FG2 ->
FG3 consecutivos durante al menos 72 horas, medidos desde el inicio del primer
FG2 aceptado hasta el cierre del tercer FG3 aceptado, sin drift.

`EVID-H1-011/012=VERIFIED` exige los tres pares. `EVID-H1-013` exige ademas FG1
Production PASS y cron mensual activo/main-only. `EVID-H1-016` y F11.1 son
posteriores y separados. Dispatches, reruns y ejecuciones manuales acreditan cero
evidencia natural.

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
- SQL ad hoc, DDL, metadata/backfill o DML fuera de los applies cohort-bound
  aprobados expresamente en `G6-A`, `G6-B` o `G6-D` produce
  `STOP_REQUIRES_REBASELINE`; no se improvisa una ruta de apply.
- Cualquier cambio runtime/config durante observacion reinicia la secuencia.

## Aprobaciones Separadas

| Accion | Gate requerido |
|---|---|
| Boundaries/reconciliacion R0 | F10.9 Git/CI y review humano por PR |
| P1-P5 codigo/tests/docs | Consumido por packages y PRs protegidos ya verificados |
| Diagnostico Production read-only G5 | Reabierto; aprobacion separada pendiente |
| Deduplicacion/repoint/archive G6-A | Reabierto; aprobacion separada pendiente |
| Lifecycle G6-B | Reabierto; aprobacion separada pendiente |
| Perfiles/fuentes G6-C | Reabierto; aprobacion separada pendiente |
| Revalidacion/restauracion FG3 G6-D | Reabierto; aprobacion separada pendiente |
| Integracion P7 G7 | Reabierta; PR protegido separado |
| Certification G8 | Reabierta; aprobacion separada pendiente |
| Main G9 | Reabierta; aprobacion separada pendiente |
| GO_SCHEDULES G11 | Reabierto; aprobacion separada pendiente |
| Observacion natural 72h G13 | Reabierta despues de G12; aprobacion separada pendiente |
| Conformidad y cierre | F11.1 y aprobacion cliente separadas |

DDL, DML de reparacion ad hoc, SQL/migrations y re-enrichment/backfill no tienen
gate aprobable dentro de F10.9. Requieren rebaseline de autoridad superior o
traslado a otro hito. Esta prohibicion no convierte en ad hoc las mutaciones
ordinarias y cohort-bound de FG2/FG3 posteriores a `GO_SCHEDULES`.

## Criterio De Salida

- Cero duplicados normalizados y cero stale `processing`.
- Cero perfiles invalidos habilitados.
- FG2 completo SUCCESS/NOOP en todas sus estaciones.
- FG3 cohorte completa, cero inconclusos y mutaciones confirmadas.
- Tres pares naturales FG2 -> FG3 consecutivos durante al menos 72h.
- `EVID-H1-011..013=VERIFIED` solo despues de cumplir todos los umbrales.
- `EVID-H1-016` posterior a la observacion.
- Metadata `104/224` visible como `TRANSFERRED_NON_BLOCKING_H2_CA2`.

## Evidencia

El ledger append-only es
[EVID-H1-OBS-F10.9-001](../evidencias_cliente/sprint_1/registro_observacion_production_f10_9_2026-08-09.md).

Este plan no autoriza ejecucion, DDL/DML, backfill, schedules ni merge.
