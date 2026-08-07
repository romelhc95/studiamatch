# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-07-F10.8-DB-SYNC-FAIL-CLOSED-REMEDIATION`.

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
| `F10` | Produccion CA1-only | `IN_PROGRESS` | F10.8 queda `IN_PROGRESS_DB_SYNC_FAIL_CLOSED_REMEDIATION_REQUIRED`. PR #297 fue aprobado/fusionado en `main@260900a268ab8eb194140ea7311aec2a170b6e17`; `security-audit`, `F10 Main Boundary`, Cloudflare Pages y Certification Canary `31140933096=PASS` sobre `certificacion@94026de77fe9c1a01c66eae78bea8b09858daf96` quedaron verificados con artifact sanitizado. `DB Sync to Production` `31142826000=FAIL_CLOSED_PRE_SUPABASE`: fallo antes de contactar Supabase porque el workflow invoco `db_migrate.py --manifest` en una version de `main` incompatible; `Apply pending migrations`, `Verify target schema` y `FG2 deferred` quedaron skipped. No hubo DDL/DML, migraciones, snapshot Production, writer ni mutacion DB. Hito 1 queda `TECHNICALLY_DELIVERED_FORMAL_CLOSURE_PENDING`; `EVID-H1-010..013/016` siguen pendientes. |
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
| `F10.8` | `IN_PROGRESS_DB_SYNC_FAIL_CLOSED_REMEDIATION_REQUIRED` | Remediacion Production Canary promovida por PR #297 a `main@260900a268ab8eb194140ea7311aec2a170b6e17`; Certification Canary `31140933096=PASS` sobre `certificacion@94026de77fe9c1a01c66eae78bea8b09858daf96`, manifest/artifacts sanitizados y conteos pre/post/after-cleanup sin cambio. DB Sync `31142826000` fallo fail-closed antes de Supabase por ruta sin cambios DB que no debio ejecutar report de migraciones. Tarea activa: remediar `db-sync-to-pro.yml` para omitir report/apply/verify en push a `main` sin cambios `db/**`, mantener apply manual DDL-gated y fallar antes de secrets si existe incompatibilidad DB real. `EVID-H1-010..013/016=PENDING`; Production Canary, schedules y cierre final siguen bloqueados. |
| `F10.9` | `PENDING` | Habilitacion gradual de schedules y observacion: al menos 72h y tres pares FG2 -> FG3 consecutivos completos. |

Base documental post-main: `desarrollo@077fce526876f87c93119968d4b9cba245c8cbf4`.

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase tecnica activa: F10.8 `IN_PROGRESS_DB_SYNC_FAIL_CLOSED_REMEDIATION_REQUIRED`; PR #297 promovio la remediacion F10.8 a `main@260900a268ab8eb194140ea7311aec2a170b6e17`. Certification Canary `31140933096=PASS`, `security-audit` y `F10 Main Boundary` quedaron verificados. F10.7 permanece `COMPLETED_TECHNICAL_DELIVERY` y conserva [ADR-0008](decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md) y [ADR-0009](decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md) como antecedentes.
- Incidente post-merge a resolver dentro de F10.8: `DB Sync to Production` run `31142826000=FAIL_CLOSED_PRE_SUPABASE`; fallo antes de Supabase por ejecutar report de migraciones en un push CA1-only sin cambios `db/**`, usando una ruta `--manifest` incompatible con la version de `main`. Los jobs `Apply pending migrations`, `Verify target schema` y `FG2 deferred to scheduled production window` quedaron skipped; no hubo DDL/DML ni mutacion DB.
- Tarea pendiente de F10.8: remediar exclusivamente `DB Sync to Production` fail-closed. Allowlist: `.github/workflows/db-sync-to-pro.yml`, tests especificos del contrato DB Sync y `.github/workflows/security-audit.yml` solo si el gate minimo lo requiere. Excluye `db/**`, `supabase/**`, manifests, migrations, DDL/DML, backfill, Supabase, writers, Production Canary, workflow dispatch operativo, schedules y CA2.
- Compatibilidad contractual: `F10 permanece bloqueada` para canary Production, schedules, writers, Supabase Free/Pro y DDL/DML hasta completar esta remediacion F10.8, revalidar el push a `main` sin falso rojo y recibir aprobaciones separadas para Production Canary/F10.9/F11.1. Este registro no completa Hito 1 contractual.
- Autorizacion documental anterior: `REGISTRAR_APROBACION_ADENDA_Y_REBASELINE_HITO1_CA1_ONLY`, completada y fusionada por el rebaseline PR #269 en `desarrollo@d9c7f180495c985a1e9a0ada4a42525fda60a870` / tree `7c510dfdbf90a97b97d2358596cab12a8cc4c2a3`.
- PR #268 de arquitectura y matrices fue mergeado en `desarrollo@f8b898745b7ff35949640227af0049ddde06f901` / tree `3d044210792a11b099efb102a511ee1f41e8a52c`.
- Siguiente accion futura: revisar y fusionar la remediacion documental actual a `desarrollo`; despues de mergear esta autoridad, una nueva autorizacion exacta `Ejecuta las tareas pendientes de la Fase F10.8` podra implementar la remediacion fail-closed de DB Sync por la ruta Desarrollo -> Certificacion -> Main. Production Canary y schedules siguen bloqueados hasta autorizaciones separadas.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) conserva su historia y no ejecuta operaciones remotas en este cierre documental. La adenda aprobada separa el cierre CA1 productivo del alcance CA2 pendiente: Hito 1 queda CA1-only, `H1-CA2P` y `H1-CA7P` quedan como antecedentes historicos, y su alcance pendiente pasa a `H2-CA2` y `H4-CA7` sin reutilizar evidencia historica como cierre. F6-F8, v3 y los artifacts F9.7 permanecen inmutables; Free/Pro siguen `UNCHANGED_NOT_ATTESTED`; `GO_FOR_FREE` queda superseded para Hito 1. Hitos 2 a 5 permanecen `PENDING`, sin subfase ejecutable.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
