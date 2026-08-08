# Paquete De Evidencia Hito 1

| Campo | Valor |
|---|---|
| ID | `EVID-PACK-H1-001` |
| Estado | `DRAFT_DB_SYNC_REMEDIATED_PRODUCTION_CANARY_PENDING` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` vigente por adenda |
| Candidate | `desarrollo@5b282461149b7319685cf090534e28051e5eb32c` (F9.8 local), `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17` (PR #277), entrega tecnica `main@64e4ed895d43121c5683e26a355993f18e528a5c` (PR #291), remediacion F10.8 `main@260900a268ab8eb194140ea7311aec2a170b6e17` (PR #297), remediacion DB Sync `main@529ca111f1fef40efb15676ad6f07d002a54ae92` (PR #307) |

Este documento define la evidencia que se entregara al cliente. No afirma que
Hito 1 este completado.

## Aprobacion Contractual Sanitizada

| Evidencia | Estado | Fecha | Rol aprobador | ID opaco | Digest |
|---|---|---|---|---|---|
| `EVID-H1-001` | `VERIFIED` | `2026-08-01` | `CLIENT_AUTHORIZED_APPROVER` | `RECORDED_PRIVATELY` | `RECORDED_OUT_OF_GIT` |

La evidencia privada permanece fuera de Git. Esta atestacion no copia contenido
comercial, firmas, datos personales, rutas privadas, hashes completos ni
credenciales.

## Resultado Ejecutivo

Candidate local F9.8 CA1-only implementado y replay-validado post-merge en
Docker/Linux. PR #277 promovio el candidate selectivo a Certification y quedo
aprobado/fusionado; los canaries Certification posteriores se aceptan solo como
evidencia fail-closed (`DEVIATION_ACCEPTED_FAIL_CLOSED`), no como PASS. QA
independiente verifico esa desviacion. PR #282 agrego controles pre-main en
Certification y F9.10 definio el gate `main`, canary Production y rollback sin
ejecutarlos. F10.6 cerro control-plane con environments programados fail-closed y
runs legacy schedule cancelados con cero pasos. F10.7 reconstruyo los controles,
promovio el paquete CA1-only por PR #291 a `main@64e4ed895d43121c5683e26a355993f18e528a5c`,
verifico boundary post-merge de 32 objetos y registro Cloudflare Pages `SUCCESS`
como publicacion tecnica del arbol promovido. F10.8 promovio por PR #297 la
remediacion de Production Canary a `main@260900a268ab8eb194140ea7311aec2a170b6e17`;
Certification Canary `31140933096=PASS`, `security-audit`, `F10 Main Boundary` y
Cloudflare Pages quedaron verificados. DB Sync `31142826000` fallo fail-closed
antes de Supabase porque el push sin cambios `db/**` ejecuto report de migraciones
incompatible con `main`; apply/schema/FG2 quedaron skipped y no hubo DDL/DML ni
mutacion DB. La remediacion DB Sync se promovio por PR #304/#305/#306/#307 hasta
`main@529ca111f1fef40efb15676ad6f07d002a54ae92`; run `31151066062` termino
`SUCCESS_NO_DB_CHANGES_SKIPPED` y `Security Audit Gate` `31151066061=PASS`.
Canary Production acreditable, schedules, produccion observada y conformidad
siguen pendientes. El resultado final debera indicar claramente que se entrego
CA1 tecnicamente y que CA2 se traslado a Hito 2.

## Alcance Entregado

| Elemento | Resultado | Evidencia |
|---|---|---|
| Schedules FG2/FG3 | `TECHNICAL_DELIVERY_MAIN_SCHEDULES_PENDING` | Workflows con kill switch y environments dedicados; gate main/canary Production definidos; observacion Production pendiente |
| Gates/circuit breaker | `FAIL_CLOSED_CERTIFICATION_QA_VERIFIED` | Runs F9.9 fallaron con salida no cero y cleanup/idempotencia cuando hubo snapshot; QA independiente `PASS` |
| Secrets solo CI | `CI_SECURITY_PASS` | PR #277 `security-audit` y credential scan PASS; no secretos en evidencia F9.9 |
| Development/Certification/Production | `TECHNICALLY_DELIVERED_FORMAL_CLOSURE_PENDING` | PR #277/#282/#285/#288/#289/#291/#297/#304/#305/#306/#307 Approved/Merged; environments programados fail-closed; `main` promovido tecnicamente; Certification Canary final PASS; DB Sync remediado y verificado en `main`; Production canary y schedules pendientes |
| Cero cambios CA2 | `MAIN_BOUNDARY_PASS_POST_MERGE` | Boundary post-merge 32 objetos digest `8fafc74e415d6875315e8584eb17705e24c40777675996cde9bf4ff0ccf7ddff`; remediacion DB Sync limitada a workflows; cero rutas prohibidas |

FG1 se valida en un anexo tecnico interno como soporte de inventario. No forma
parte del alcance entregado ni de la conformidad contractual CA1.

## Matriz CA1

| Cambio | Prueba | Ambiente | Umbral | Resultado |
|---|---|---|---|---|
| Cadencia y refs | Workflow contract | Local/CI | PASS | `LOCAL_PASS_CI_PENDING` |
| Gates antes de limites | Tests de orquestacion | Local/Development | PASS | `LOCAL_REPLAY_PASS_REMOTE_PENDING` |
| Circuit breaker | Error/recuperacion | Local/Certification | PASS | `LOCAL_REPLAY_PASS_REMOTE_PENDING` |
| FG2 | Canary y schedule | Certification/Production | Completo, sin mock | `CERTIFICATION_FAIL_CLOSED_PRODUCTION_PENDING` |
| FG3 | HTTP/SSRF/mutacion | Certification/Production | Sin falsos verdes | `PRODUCTION_PENDING` |
| Secrets | Credential scan | CI/Production | Cero exposicion | `LOCAL_SECURITY_PASS_CI_PENDING` |
| Frontera CA2 | Object/digest diff | Todos | Cero cambios | `POST_MAIN_BOUNDARY_VERIFIED` |

## Identidad Inmutable

- Base commit/tree: `d9c7f180495c985a1e9a0ada4a42525fda60a870` / `7c510dfdbf90a97b97d2358596cab12a8cc4c2a3`.
- Candidate commit/tree: `5b282461149b7319685cf090534e28051e5eb32c` / `d1fe60a403aa213e8a1beb51d49af12aba727cfd`.
- Patch-id y hashes: patch-id estable `ba0f680c09d1d91684f772e326d077676a05370e`; candidate F9.7 congelado `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
- Merge desarrollo/certificacion/main: controles pre-main PR #280 en `desarrollo@ac7d46e7a09213a10616297323e2d411b8d10954` / tree `695f5a358979a81c380641e8f800ca3ab62c9f6a`; candidate F9.9 `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`; controles F9.10 PR #282 en `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` / tree `b2edda7c538b7e74abe0bcaf59715e9d3f4b9327`; PR #283/#284 en `desarrollo`; PR #285 historico en `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760`; PR #291 aprobado/fusionado en `main@64e4ed895d43121c5683e26a355993f18e528a5c` / tree `7d43590c19ca15171d468bf8c823a5e93b47d8cc`.

## Validaciones

- Local/container: `PASS` para py_compile CA1, assertions focused F9.8 CA1 y replay post-merge Docker/Linux (53 focused + focused jobs CI + F9.7 congelado 226+7 + runners PG17).
- CI: PR #277 PASS (`security-audit`, boundary selectivo, credential scan, Python, typecheck, lint); PR #280/#283/#284 y CI post-merge PASS en `desarrollo`; PR #282/#285 y CI post-merge PASS en `certificacion`; PR #291 y PR #297 PASS hacia `main` con `security-audit` y boundary F10; PR #305/#306/#307 PASS para remediacion DB Sync y gate main incremental.
- Security: `LOCAL_PASS` sin blockers; residual SSRF DNS TOCTOU documentado como riesgo no bloqueante.
- QA independiente: `PASS` segun [QA-F9.9-DEVIATION-001-RESULT](../../operaciones/qa_desviacion_f9_9_resultado.md).
- Canary Certification F9.9: `DEVIATION_ACCEPTED_FAIL_CLOSED`, no PASS; el
  Certification Canary F10.8 posterior queda registrado aparte como PASS.
- F9.10 readiness: run `30824041542` PASS read-only/sanitizado; PR #283 CI post-merge PASS (`30856264196`, `30856264217`); PR #285 CI post-merge `30865604732` PASS; run `30865604729` cancelado con cero pasos; boundary `main -> certificacion` = 32 objetos, digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5`; `USER_PERSONAL_UAT=PASS`. No DML y no Production. El canary Production futuro queda definido con artifacts sin slug/SHA/run/digest privado.
- F10.6 control-plane: `Production-Scheduled-FG1/FG2/FG3` verificados con branch policy `main`, reviewer humano autorizado, self-review bloqueado, variables fail-closed y secrets minimos por nombre; `Production` conserva `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true`; runs `30681941694`, `29678093566` y `29677885934` quedaron `cancelled` con `steps=[]` y sin pending deployments. No se aprobaron runs, no hubo retry, dispatch, schedule ejecutado, writer, Production canary, Supabase, Cloudflare, DDL/DML ni PR/merge a `main`.
- Entrega tecnica F10.7: PR #291 aprobado/fusionado en `main@64e4ed895d43121c5683e26a355993f18e528a5c`; `Security Audit` post-main run `30969158679` PASS con `F10 Main Boundary`; Cloudflare Pages `SUCCESS`; `DB Sync to Production` run `30969158711` cancelado con jobs `steps=[]`. Boundary post-merge 32 objetos digest `8fafc74e415d6875315e8584eb17705e24c40777675996cde9bf4ff0ccf7ddff`; [ADR-0009](../../decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md) registra que esto es entrega tecnica, no cierre contractual completo.
- F10.8 post-main: PR #297 aprobado/fusionado en `main@260900a268ab8eb194140ea7311aec2a170b6e17`; Certification Canary `31140933096=PASS` sobre `certificacion@94026de77fe9c1a01c66eae78bea8b09858daf96`; artifact sanitizado con tres JSON, cohortes `redacted`, sin `institution_id`, hosts Supabase ni UUIDs en artifacts, y conteos/gates `pre == post == after_cleanup`. `security-audit` y `F10 Main Boundary` PASS. `DB Sync to Production` historico `31142826000=FAIL_CLOSED_PRE_SUPABASE`; fallo antes de Supabase por ruta sin cambios `db/**`, apply/schema/FG2 skipped y cero DDL/DML/mutacion. Remediacion DB Sync verificada por PR #307 y run `31151066062=SUCCESS_NO_DB_CHANGES_SKIPPED`; Production Canary sigue pendiente.
- Remediacion DB Sync F10.8: PR #304 mergeado a `desarrollo`; PR #305 y PR #306 mergeados a `certificacion`; PR #307 mergeado a `main@529ca111f1fef40efb15676ad6f07d002a54ae92`. `DB Sync to Production` run `31151066062=SUCCESS_NO_DB_CHANGES_SKIPPED`: solo `Detect DB changes` corrio; preflight/report/apply/schema/FG2 quedaron skipped por ausencia de cambios `db/**`. `Security Audit Gate` post-main `31151066061=PASS`. No Supabase, DDL/DML, migrations, Production Canary, schedules, writer ni mutacion DB.
- Production Canary F10.8 run `31157736479=FAIL_CLOSED_HTTP_403_RESTORE_NOOP`: aprobacion separada, snapshot privado, restore exacto y segundo restore NOOP completados; FG2 harvest fallo por HTTP 403 de fuente externa y FG3 quedo skipped. El [registro Production Canary F10.8](./registro_canary_production_f10_8_2026-08-07.md) conserva la evidencia sanitizada. Los artifacts sanitizados no expusieron cohorte, UUIDs, hosts Supabase ni credenciales, pero la auditoria posterior detecto URLs operativas en logs. `EVID-H1-010` permanece `PENDING` hasta promover remediacion de sanitizacion/source-access preflight y obtener un canary completo PASS.
- Production Canary F10.8 run `31236936740=FAIL_CLOSED_FG2_CLEANSING_PROVENANCE_RESTORE_NOOP`: aprobacion separada sobre `main@705624a8ffa2f4fae0ffd7a958baa6205a6ae088`; target/candidate/limites/source-access preflight/snapshot/FG1/FG2 harvest PASS; FG2 cleansing fallo fail-closed tras promover tres filas existentes porque `atomic_cleansing_promote` no fusionaba `cleansed_programs.metadata` durante conflicto por URL; enrichment/sync/FG3 skipped; restore exacto, segundo restore NOOP y `after-cleanup == pre` PASS. Remediacion local versiona `20260808_fase10_8_atomic_cleansing_provenance.sql`, sincroniza restore canonico y limita DB Sync con `--only`. No DDL/DML remoto, backfill, schedules, secrets ni nuevo canary. `EVID-H1-010` permanece `PENDING` hasta aplicar la migracion con autorizacion separada y obtener canary completo PASS.
- `EVID-H1-010` futuro requiere canary Production completo `run_fg1=true`, `run_fg2=true`, `run_fg3=true`, `mutable_authorized=true`, limites `5/5/3/3/3`, snapshot privado, restore y segundo restore NOOP. Runs parciales FG2-only/FG3-only seran diagnosticos, no evidencia de cierre.
- `USER_PERSONAL_UAT=PASS` historico queda registrado contra `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` / tree `419b25f69e4eef4d7277a7439ca45efc1eaac242`, sin PII, secretos ni identificadores internos; para F10.8 se registro un UAT nuevo contra `main@64e4ed895d43121c5683e26a355993f18e528a5c` / tree `7d43590c19ca15171d468bf8c823a5e93b47d8cc`.
- Definicion QA: [QA-F9.9-DEVIATION-001](../../operaciones/qa_desviacion_f9_9.md); resultado `PASS` sanitizado en [QA-F9.9-DEVIATION-001-RESULT](../../operaciones/qa_desviacion_f9_9_resultado.md).
- Canary Production: pendiente; no se ejecuto en esta remediacion.
- Schedule observado: pendiente.

## Desviacion F9.9 Certification

La decision [ADR-0007](../../decisiones/ADR-0007_desviacion_canary_certification_f9_9.md)
acepta evidencia fail-closed sin cerrar el Hito:

| Run | Estado sanitizado |
|---|---|
| `30777088545` | Cancelado esperando aprobacion; sin ejecucion ni secretos. |
| `30781870451` | FAIL por duplicado normalizado en inventario; cleanup e idempotencia exitosos. |
| `30782109395` | FAIL por source slug no configurado; cleanup e idempotencia exitosos. |
| `30782242009` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |
| `30782360475` | FG1 PASS; FG2 FAIL por HTTP 403; cleanup e idempotencia exitosos. |

Condiciones:

- No se declara resultado positivo de Certification.
- `F99_CERTIFICATION_CANARY_MUTABLE_APPROVED` quedo restaurado a `false`.
- Las cohortes intentadas quedaron documentadas como sin markers F9.9 residuales y QA verifico el bundle primario disponible.
- Los artifacts disponibles reportaron conteos no-cohorte sin cambio; no se afirma digest de contenido no-cohorte fuera del nivel demostrado por QA.
- FG2 downstream, FG3, canary Production, schedules y conformidad siguen pendientes.
- La desviacion expira con observacion Production completada en F10 o ante un fallo que descarte que el problema fuese el egress observado en Certification.

## Exclusiones Confirmadas

El paquete final debera confirmar que no se promovieron schema, RLS/RPC,
frontend, leads/email, Edge, backfill, admin, Home o Resultados CA2+.

## Riesgos Residuales

Se enlaza el [anexo CA2/RLS](./anexo_h1_ca2_seguridad_rls.md). Ningun riesgo
puede presentarse como mitigado sin evidencia.

## Aprobaciones

- Aprobacion contractual de adenda: `EVID-H1-001=VERIFIED`.
- Revision tecnica: controles pre-main de repositorio aprobados/fusionados en PR #280 con CI post-merge PASS.
- QA: `PASS` para la desviacion F9.9; no autoriza Production ni `main`.
- Readiness F9.10: completada; F10.6 control-plane completada; F10.7 entrega tecnica post-main registrada por PR #291 y [ADR-0009](../../decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md).
- UAT personal: `PASS` registrado para SHA/tree final de Certification; la promocion tecnica posterior a `main` no autoriza Production canary, schedules ni cierre contractual.
- Aprobacion de release tecnico a `main`: `VERIFIED` por PR #291 y PR #297 aprobados/fusionados.
- Conformidad cliente: pendiente.

## Ledger De Evidencias H1

| ID | Estado |
|---|---|
| `EVID-H1-001` | `VERIFIED` |
| `EVID-H1-002` | `VERIFIED` |
| `EVID-H1-003` | `VERIFIED` |
| `EVID-H1-004` | `VERIFIED` |
| `EVID-H1-005` | `VERIFIED` |
| `EVID-H1-006` | `VERIFIED` |
| `EVID-H1-007` | `VERIFIED` |
| `EVID-H1-008` | `DEVIATION_ACCEPTED_FAIL_CLOSED` |
| `EVID-H1-009` | `VERIFIED` |
| `EVID-H1-010` | `PENDING` |
| `EVID-H1-011` | `PENDING` |
| `EVID-H1-012` | `PENDING` |
| `EVID-H1-013` | `PENDING` |
| `EVID-H1-014` | `VERIFIED_POST_MERGE_BOUNDARY` |
| `EVID-H1-015` | `VERIFIED` |
| `EVID-H1-016` | `CLIENT_CONFORMITY_PENDING` |
