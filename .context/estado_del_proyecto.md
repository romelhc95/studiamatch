# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-13-F10.10-M3-PUBLIC-ACL-PREFLIGHT-V2-POST-MERGE`.

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
| `F10` | Produccion CA1-only | `IN_PROGRESS_REBASELINE_METADATA` | F10.10 queda `M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2_PAYLOAD_POST_MERGE_VERIFIED_CONSUMER_BINDING_REQUIRED`: payload sanitizado promovido por PR #371; PR #372 remedio el harness y ambos checks post-merge quedaron PASS. Falta adaptar/promover el consumidor canónico target/transport antes de aprobación o consumo. |
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
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | PR #323 promovio `operation=verify` read-only a `main@5c7efaf417eba7f45bed45994a6249d03f609fc2`; PR #324 corrigio el gate FG2 deferred tras verify y quedo en `main@675ade43f41a2f5d04f05a40f9837b514a8705ce` / tree `90868898778a1039006e45b870fbc03e6e65291b`. DB Sync verify `31268229878=PASS`: pending migrations `0`, apply skipped, target schema PASS y FG2 deferred PASS. PR #325 corrigio la paginacion de atestacion no-cohorte y quedo en `main@859d2f7d83f83950d10858fe27bd035febba7f68` / tree `ba7f6e74e88b2153aef1f4582bb3faa999c01a98`; DB Sync post-merge `31271765282=SUCCESS_NO_DB_CHANGES_SKIPPED` corrio solo `Detect DB changes`; Security Audit `31271765308=PASS`. Production Canary `31272290614=PASS`: target/candidate/limites/source-access preflight/snapshot PASS, FG1 PASS, FG2 harvest/cleansing/enrichment/sync PASS, FG3 PASS, restore exacto PASS, segundo restore `--expect-noop` PASS, after-cleanup PASS y artifact sanitizado `9026139906` con seis manifests y digest `sha256:1a1a0fe3df7bbd03b74217be188fd58014257a5b2a5045ce63863260b73ec6ce`. `EVID-H1-010=VERIFIED`. No reejecutar `operation=apply`; no ejecutar DDL/DML, backfill, schedules ni cambios de secrets/environments. |
| `F10.9` | `STOP_REQUIRES_REBASELINE` | R0/P1-P5 quedaron cerrados post-merge. PR #341 integro P5 mediante candidate `46fd10864af2a90e407f6867adf980daa940b075` y merge protegido `1c5d1526a1da247ca6ad0eb7b25cd5e0b0f51564` / tree `8eb146006419d93dc0a74710ca9efaaf101ab280`; Security Audit `31409222936=PASS` y F9.7 `31409222568=PASS`. [G3/P5 post-merge y G4](operaciones/g3_p5_post_merge_g4_decision_2026_08_10.md) fija `G3=PASS` y `G4=STOP_REQUIRES_REBASELINE`: no se puede demostrar metadata cero y el snapshot conocido conserva `104/224` incompletos. P7/G5+, data plane, DDL/DML, schema/migrations, providers, writers, re-enrichment/backfill, Certification, Main y schedules quedan bloqueados. Pares aceptados `0`; observacion `NOT_STARTED`. |
| `F10.10` | `M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2_PAYLOAD_POST_MERGE_VERIFIED_CONSUMER_BINDING_REQUIRED` | PR #371 promovio el payload v2 null-bound; su primer F9.7 post-merge fallo fail-closed antes de crear PostgreSQL. PR #372 remedio exclusivamente el harness y quedo fusionada en `desarrollo@89cbeda226c6e04c6c1b6e091e6b94fc36273645` / tree `da92dfa4baf89cc04bc2a67c97f678f3273e152b`; Security Audit `31720301586=PASS` y F9.7 `31720301577=PASS`. No es ejecutable: falta un consumer candidate separado que valide `target-binding-v2` y `observed-transport-v2` de la misma conexion. |

Base tecnica post-cierre documental F10.8: `main@38314170197a907ac5c4c815a9bb18b3d5f29b06` / tree `741627eda4b4fbcf76503b8e353abb08ac0eb1c4`.

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase tecnica activa: F10.10 `M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2_PAYLOAD_POST_MERGE_VERIFIED_CONSUMER_BINDING_REQUIRED`. La promocion y remediacion del harness no consumieron el gate ni abrieron red; el siguiente candidate debe implementar/promover exclusivamente el consumer binding canónico.
- Incidente post-merge resuelto dentro de F10.8: `DB Sync to Production` run historico `31142826000=FAIL_CLOSED_PRE_SUPABASE`; fallo antes de Supabase por ejecutar report de migraciones en un push CA1-only sin cambios `db/**`, usando una ruta `--manifest` incompatible con la version de `main`. La remediacion fue promovida por PR #304/#305/#306/#307 hasta `main@529ca111f1fef40efb15676ad6f07d002a54ae92`.
- Evidencia de remediacion DB Sync: run post-main `31151066062=SUCCESS_NO_DB_CHANGES_SKIPPED`; solo corrio `Detect DB changes`. `DB contract preflight`, `Report pending migrations`, `Apply pending migrations`, `Verify target schema` y `FG2 deferred to scheduled production window` quedaron skipped porque no hubo cambios `db/**`. `Security Audit Gate` post-main `31151066061=PASS`.
- Compatibilidad contractual: la remediacion funcional ya aplico DDL en Free/Desarrollo y el run Pro `31263024890` aplico `20260808_fase10_8_atomic_cleansing_provenance` bajo autorizacion separada consumida. Production Canary F10.8 `31272290614=PASS` verifica `EVID-H1-010`. Este registro no autoriza nuevo DDL/DML Pro, schedules, writers programados, backfill, cambios de secrets/environments ni CA2. `EVID-H1-011..013` no pueden avanzar dentro del baseline F10.9 detenido; requieren primero rebaseline superior. `EVID-H1-016` y F11.1 conservan su aprobacion separada posterior. Este registro no completa Hito 1 contractual.
- Autorizacion documental anterior: `REGISTRAR_APROBACION_ADENDA_Y_REBASELINE_HITO1_CA1_ONLY`, completada y fusionada por el rebaseline PR #269 en `desarrollo@d9c7f180495c985a1e9a0ada4a42525fda60a870` / tree `7c510dfdbf90a97b97d2358596cab12a8cc4c2a3`.
- PR #268 de arquitectura y matrices fue mergeado en `desarrollo@f8b898745b7ff35949640227af0049ddde06f901` / tree `3d044210792a11b099efb102a511ee1f41e8a52c`.
- Siguiente accion: implementar y promover un consumer candidate separado que genere `target-binding-v2` y exija `observed-transport-v2` de la misma conexion. Solo despues se reponen fuera de Git `F10_10_M3_API_URL`, `F10_10_M3_PROJECT_REF`, `F10_10_M3_SQL_HOST`, `F10_10_M3_CA_SHA256`, provisioner y ventana. El gate sigue no aprobado y no consumido.
- Seguridad local: `ROTATION_ATTESTATION: FREE_DB_DATABASE_PASSWORD_ROTATED; OLD_CREDENTIAL_REVOKED` fue recibida sin valor sensible. La credencial canary anterior queda prohibida y el hallazgo `ROTATION_REQUIRED_OUT_OF_BAND` se cierra solo para esa identidad.

## Alcance Inmediato

La macrofase F9 conserva su historia y no ejecuta operaciones remotas en este cierre documental. La adenda aprobada separa el cierre CA1 productivo del alcance CA2 pendiente: Hito 1 queda CA1-only, `H1-CA2P` y `H1-CA7P` quedan como antecedentes historicos, y su alcance pendiente pasa a `H2-CA2` y `H4-CA7` sin reutilizar evidencia historica como cierre. F6-F8, v3 y los artifacts F9.7 permanecen inmutables como antecedentes; las attestations historicas Free/Pro de esas rutas siguen `UNCHANGED_NOT_ATTESTED` para CA2 y no contradicen la DDL Pro F10.8 aplicada ni el canary Production CA1 verificado. `GO_FOR_FREE` queda superseded para Hito 1. Hitos 2 a 5 permanecen `PENDING`, sin subfase ejecutable.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), esta autoridad viva y [Release minimo](operaciones/flujo_release_minimo.md). La [Matriz DB](operaciones/matriz_adopcion_db.md) restaurada es solo referencia historica pre-F10.8.
