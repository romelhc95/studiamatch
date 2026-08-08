# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-08-F10.8-FREE-DDL-APPLIED`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases. El estado vivo de la tarea activa pertenece a la propia tarea.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0` | Preservacion | `COMPLETED` | Preservacion verificada. |
| `F1` | Main a certificacion | `COMPLETED` | Convergencia verificada. |
| `F2` | Certificacion a desarrollo | `COMPLETED` | Convergencia verificada. |
| `F3` | Higiene remota | `COMPLETED` | Higiene terminada. |
| `F4` | Bootstrap local | `COMPLETED` | Entorno local verificado. |
| `F5` | Obsidian minimo | `COMPLETED` | Gobierno documental, PR #221 y `SRC-REQ-001` reconciliada. |
| `F6` | Reconciliacion DB-as-Code | `COMPLETED` | Base funcional contractual Hito 1, forward-only y validada localmente; ningun cambio remoto aplicado. |
| `F7` | G1b minimo | `COMPLETED` | Base funcional contractual Hito 1; gates y postcondiciones locales validados. |
| `F8` | Hito 1 funcional | `COMPLETED` | Base funcional contractual Hito 1 y PostgreSQL 17 validados; sin aplicacion DB remota. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED` | F9.10 cerro readiness de repositorio y certificacion final CA1-only: PR #285 aprobado/fusionado en `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760` / tree `419b25f69e4eef4d7277a7439ca45efc1eaac242`, CI post-merge `Security Audit Gate` run `30865604732` PASS, run automatico `30865604729` cancelado con cero pasos, boundary final `main -> certificacion` de 32 objetos digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5`, `USER_PERSONAL_UAT=PASS`, `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`; sin Production, schedules, DDL/DML, Supabase ni Cloudflare. |
| `F10` | Produccion CA1-only | `IN_PROGRESS` | F10.8 queda `DDL_FREE_APPLIED_VALIDATED`. Remediacion fail-closed de DB Sync promovida hasta `main@529ca111f1fef40efb15676ad6f07d002a54ae92`; source-preflight/sanitizacion y FG1 source slug promovidos hasta `main@705624a8ffa2f4fae0ffd7a958baa6205a6ae088`; Production Canary `31236936740=FAIL_CLOSED_FG2_CLEANSING_PROVENANCE_RESTORE_NOOP`. PR #317 quedo mergeado en `desarrollo@cd4297b88c48847b26157f4c57aced588eb09b9e` y el DDL Free/Desarrollo autorizado aplico exclusivamente `20260808_fase10_8_atomic_cleansing_provenance`. Verificacion read-only: registro tecnico en `supabase_migrations.schema_migrations`, `SECURITY DEFINER`, `search_path=pg_catalog`, merge de metadata, transicion `pending/processing`, `anon/authenticated` sin execute y `service_role` con execute. No hubo Pro, Production Canary, schedules, backfill, secrets ni cambios de environments. Hito 1 queda `TECHNICALLY_DELIVERED_FORMAL_CLOSURE_PENDING`; `EVID-H1-010..013/016` siguen pendientes. |
| `F11` | Cierre final | `PENDING` | Bloqueada hasta completar produccion observada; incluye cierre documental final y limpieza fisica solo si se autoriza expresamente. |

## Subfases F9

| ID | Estado | Identidad vigente |
|---|---|---|
| `F9.1` | `COMPLETED` | Precertificacion local; alias historico `FASE-09`, PR #231/#232 y cierre #233 |
| `F9.2` | `COMPLETED` | Contrato local de promocion; alias historico `FASE-10`, PR #235/#236 |
| `F9.3` | `COMPLETED` | Freeze local; PR #238, remediacion CRLF #239 y replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | `COMPLETED` | Reconciliacion contractual local; plan simplificado adoptado, definicion remota sustituida y antecedente temporal retirado |
| `F9.5` | `COMPLETED_WITH_KNOWN_FINDINGS` | Cierre contractual/documental; artifacts de PR #245 y PR #247 son `HISTORICAL_NON_PROMOTABLE`; no queda lectura Free pendiente |
| `F9.6` | `COMPLETED` | `H00_ALREADY_REMEDIATED_NO_DML`: cohorte con PII directa remediada, conservada como pseudonimizada; Gate B DELETE `SUPERSEDED_NON_AUTHORIZABLE`; Pro prohibido |
| `F9.7` | `COMPLETED_BY_CONTRACT_REBASELINE` | Adenda `ADENDA-REQ-EST-001-001` aprobada y efectiva; `EVID-H1-001` registra atestacion sanitizada. Cierra solo el paquete documental de rebaseline; preserva los artifacts terminales F9.7 como WIP CA2 no promocionable y antecedente historico. Cero aplicacion remota, DDL/DML, backfill, Certification o Production. |
| `F9.8` | `COMPLETED_VERIFIED_POST_MERGE` | Candidate local CA1-only implementado (PR #270/#271) y validado por replay post-merge en Docker/Linux sobre `desarrollo@5b282461149b7319685cf090534e28051e5eb32c`: 53 pruebas focused PASS, focused FG1/FG2/FG3 y jobs CI PASS, F9.7 congelado 226+7 PASS, runners PostgreSQL 17 PASS, actionlint/ShellCheck 0 issues, LF y credential scan PASS. `EVID-H1-002..005` quedan `VERIFIED`; `EVID-H1-006..016` permanecen `PLANNED`. No hubo red remota, DDL/DML, backfill, Certification ni Production. |
| `F9.9` | `COMPLETED_QA_VERIFIED` | Candidate selectivo PR #277 aprobado/fusionado en `certificacion@920ac9c7514f2e5f2e0315bf4cccb95940f3de17`; `EVID-H1-006/007=VERIFIED`; `EVID-H1-008=DEVIATION_ACCEPTED_FAIL_CLOSED`; controles pre-main PR #280 aprobados/fusionados en `desarrollo@ac7d46e7a09213a10616297323e2d411b8d10954` / tree `695f5a358979a81c380641e8f800ca3ab62c9f6a`; QA independiente `PASS` y `EVID-H1-015=VERIFIED`. No valida success path, FG3, Production ni schedules. |
| `F9.10` | `COMPLETED_READINESS_F10` | PR #285 aprobado/fusionado en `certificacion@5cd27c6f6c35808865b7084673a83f9f690d3760`; tree `419b25f69e4eef4d7277a7439ca45efc1eaac242`; CI post-merge `30865604732=PASS`; run `30865604729=CANCELLED_ZERO_STEPS`; boundary `main@d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93 -> certificacion` = 32 objetos, digest `34f3789d597bf4012378d6e509a03ee6e9ef37edaee95713023421538cab1aa5`; `USER_PERSONAL_UAT=PASS`. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.1`-`F10.5` | `SUPERSEDED_HISTORY` | Historia documental sustituida; no autorizable. |
| `F10.6` | `COMPLETED_CONTROL_PLANE` | Environments `Production-Scheduled-FG1`, `Production-Scheduled-FG2` y `Production-Scheduled-FG3` verificados con branch policy `main`, reviewer humano autorizado, self-review bloqueado, `AUTOMATION_ENABLED=false`, `PRODUCTION_WRITERS_PAUSED=true` y secrets minimos por nombre. `Production` conserva `AUTOMATION_ENABLED=false` y `PRODUCTION_WRITERS_PAUSED=true`. Runs antiguos `30681941694`, `29678093566` y `29677885934` quedaron `cancelled` con `steps=[]` y sin pending deployments. No hubo aprobacion, retry, dispatch, schedule ejecutado, writer, Supabase, Cloudflare, DDL/DML ni PR/merge a `main`. |
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | [ADR-0008](decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md) documento el rebaseline inicial; [ADR-0009](decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md) registra la entrega tecnica post-main. PR #291 promovio `certificacion@1edc65aa848d32dabfa62aa60b53f4bff9b5716e` a `main@64e4ed895d43121c5683e26a355993f18e528a5c`; tree `7d43590c19ca15171d468bf8c823a5e93b47d8cc`; boundary 32 objetos digest `8fafc74e415d6875315e8584eb17705e24c40777675996cde9bf4ff0ccf7ddff`; Cloudflare Pages `SUCCESS`; DB Sync `30969158711` cancelado con `steps=[]`. Remediacion local PR #292: `tests/test_fase10_main_boundary.py` acepta topologias pre-main y post-main sin cambiar workflows ni producto; 36 focused tests PASS en Docker. |
| `F10.8` | `DDL_FREE_APPLIED_VALIDATED` | Remediacion Production Canary promovida por PR #297 a `main@260900a268ab8eb194140ea7311aec2a170b6e17`; Certification Canary `31140933096=PASS`; DB Sync fail-closed `31142826000` remediado por PR #304/#305/#306/#307 hasta `main@529ca111f1fef40efb15676ad6f07d002a54ae92`; source-preflight/sanitizacion y FG1 source slug promovidos por flujo protegido hasta `main@705624a8ffa2f4fae0ffd7a958baa6205a6ae088`. Production Canary `31236936740=FAIL_CLOSED_FG2_CLEANSING_PROVENANCE_RESTORE_NOOP`: target/candidate/limites/source-access preflight/snapshot/FG1/FG2 harvest PASS; FG2 cleansing promovio 3 filas y fallo fail-closed por marker ausente en metadata sobre conflicto por URL; restore exacto, segundo restore NOOP y `after-cleanup == pre` PASS. PR #317 mergeado a `desarrollo@cd4297b88c48847b26157f4c57aced588eb09b9e`; DDL Free/Desarrollo autorizado aplico exclusivamente `20260808_fase10_8_atomic_cleansing_provenance` y verificacion read-only confirmo registro tecnico, metadata merge, `SECURITY DEFINER`, `search_path=pg_catalog`, ACL `service_role` y advisors solo informativos no atribuibles a la remediacion. `EVID-H1-010..013/016=PENDING`; Pro, Production Canary, schedules y cierre final requieren autorizaciones separadas. |
| `F10.9` | `PENDING` | Habilitacion gradual de schedules y observacion: al menos 72h y tres pares FG2 -> FG3 consecutivos completos. |

Base tecnica post-FG1-source-remediation: `main@705624a8ffa2f4fae0ffd7a958baa6205a6ae088`.

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase tecnica activa: F10.8 `DDL_FREE_APPLIED_VALIDATED`; el Production Canary `31236936740` sobre `main@705624a8ffa2f4fae0ffd7a958baa6205a6ae088` paso target/candidate/limites/source-access preflight/snapshot/FG1/FG2 harvest, fallo fail-closed en FG2 cleansing por no refrescar metadata de procedencia en `atomic_cleansing_promote` al resolver conflicto por URL, y completo restore exacto, segundo restore NOOP y manifest `after-cleanup` equivalente al pre-canary. La remediacion forward-only quedo mergeada en `desarrollo@cd4297b88c48847b26157f4c57aced588eb09b9e` y aplicada en Free/Desarrollo con autorizacion DDL separada; Pro, Production Canary y cierre contractual siguen pendientes. F10.7 permanece `COMPLETED_TECHNICAL_DELIVERY` y conserva [ADR-0008](decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md) y [ADR-0009](decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md) como antecedentes.
- Incidente post-merge resuelto dentro de F10.8: `DB Sync to Production` run historico `31142826000=FAIL_CLOSED_PRE_SUPABASE`; fallo antes de Supabase por ejecutar report de migraciones en un push CA1-only sin cambios `db/**`, usando una ruta `--manifest` incompatible con la version de `main`. La remediacion fue promovida por PR #304/#305/#306/#307 hasta `main@529ca111f1fef40efb15676ad6f07d002a54ae92`.
- Evidencia de remediacion DB Sync: run post-main `31151066062=SUCCESS_NO_DB_CHANGES_SKIPPED`; solo corrio `Detect DB changes`. `DB contract preflight`, `Report pending migrations`, `Apply pending migrations`, `Verify target schema` y `FG2 deferred to scheduled production window` quedaron skipped porque no hubo cambios `db/**`. `Security Audit Gate` post-main `31151066061=PASS`.
- Compatibilidad contractual: esta remediacion ya aplico DDL exclusivamente en Free/Desarrollo para `20260808_fase10_8_atomic_cleansing_provenance` bajo autorizacion separada. No autoriza ni ejecuto Pro, Production Canary, schedules, writers programados, backfill, DML operativo, cambios de secrets/environments ni CA2. `EVID-H1-010..013/016` siguen pendientes y requieren autorizaciones separadas para promocion, Pro, reintentar Production Canary, F10.9 y F11.1. Este registro no completa Hito 1 contractual.
- Autorizacion documental anterior: `REGISTRAR_APROBACION_ADENDA_Y_REBASELINE_HITO1_CA1_ONLY`, completada y fusionada por el rebaseline PR #269 en `desarrollo@d9c7f180495c985a1e9a0ada4a42525fda60a870` / tree `7c510dfdbf90a97b97d2358596cab12a8cc4c2a3`.
- PR #268 de arquitectura y matrices fue mergeado en `desarrollo@f8b898745b7ff35949640227af0049ddde06f901` / tree `3d044210792a11b099efb102a511ee1f41e8a52c`.
- Siguiente accion futura: promover la remediacion de `desarrollo` a `certificacion`, validar, promover a `main`, aplicar Pro solo con autorizacion DDL separada y Backup/PITR verificado, y repetir el Production Canary F10.8 completo sobre un nuevo SHA exacto de `main`; F10.9 schedules y F11.1 cierre/conformidad siguen bloqueados hasta completar ese canary y sus evidencias.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) conserva su historia y no ejecuta operaciones remotas en este cierre documental. La adenda aprobada separa el cierre CA1 productivo del alcance CA2 pendiente: Hito 1 queda CA1-only, `H1-CA2P` y `H1-CA7P` quedan como antecedentes historicos, y su alcance pendiente pasa a `H2-CA2` y `H4-CA7` sin reutilizar evidencia historica como cierre. F6-F8, v3 y los artifacts F9.7 permanecen inmutables; Free/Pro siguen `UNCHANGED_NOT_ATTESTED`; `GO_FOR_FREE` queda superseded para Hito 1. Hitos 2 a 5 permanecen `PENDING`, sin subfase ejecutable.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
