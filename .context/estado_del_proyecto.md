# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-03-F9.10-READINESS-CONTROLS-IN-PROGRESS`.

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
| `F9` | Certificacion Hito 1 CA1-only | `IN_PROGRESS` | F9.9 queda cerrada documentalmente con PR #277 en `certificacion`, desviacion `DEVIATION_ACCEPTED_FAIL_CLOSED`, controles pre-main PR #280 mergeados en `desarrollo`, PR #282 mergeado en `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b` y QA independiente `PASS`; PR #283 quedo fusionado en `desarrollo@5cfd93f626b3362c5c148b1d680ae948ce0218ea` con CI post-merge PASS. F9.10 ejecuta correccion repository-only para congelar proyeccion exacta antes de cualquier PR a `certificacion`. No hay canary Certification positivo, Production ni schedules. |
| `F10` | Produccion CA1-only | `PENDING` | Bloqueada hasta readiness F9.10; contempla PR a `main`, canary Production, habilitacion gradual de schedules y observacion. |
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
| `F9.10` | `ACTIVE_AUTHORIZED_IN_PROGRESS` | Readiness de repositorio autorizada por frase decimal exacta: gate CI `f10-main-boundary`, canary Production definido pero no ejecutado, rollback/snapshot privado, correccion `DB-SYNC` vs writers, registro sanitizado de PR #282/run `30824041542`, PR #283 mergeado en `desarrollo`, proyeccion selectiva pendiente de replay sobre `certificacion@bc227629b8df1fcabca47ea7be3ea1d5b4c7667b`, subfases F10.x y validaciones locales. `USER_PERSONAL_UAT` sigue pendiente antes de readiness F10. |

Base documental rebaseline: `desarrollo@f8b898745b7ff35949640227af0049ddde06f901` / tree `3d044210792a11b099efb102a511ee1f41e8a52c`.

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase activa: F9.10; [PLAN-H1-CA1-ONLY-001](operaciones/plan_cierre_hito1_ca1_only.md) fija la frontera CA1-only y conserva [PLAN-F9.7-CIERRE-001](operaciones/cierre_definitivo_f9_7.md), [PR-O v1 superseded](operaciones/pr_o_f9_7_v3_hold.md) y [PR-O executor privado](operaciones/pr_o_f9_7_successor_private_executor.md) como historia no ejecutable de Hito 1.
- Subfase autorizada en este paquete: readiness F9.10 de repositorio y documentacion. Permite cambios en allowlist F9.10, pruebas locales y PRs SDLC a `desarrollo`/`certificacion` para controles. No autoriza Supabase Free/Pro, Cloudflare, DDL/DML, backup/restore real, writers remotos, backfill, Edge, ejecuciones Production, merge a `main`, migraciones, habilitacion/cancelacion de schedules ni aprobacion de runs antiguos de `main`.
- Autorizacion documental anterior: `REGISTRAR_APROBACION_ADENDA_Y_REBASELINE_HITO1_CA1_ONLY`, completada y fusionada por el rebaseline PR #269 en `desarrollo@d9c7f180495c985a1e9a0ada4a42525fda60a870` / tree `7c510dfdbf90a97b97d2358596cab12a8cc4c2a3`.
- PR #268 de arquitectura y matrices fue mergeado en `desarrollo@f8b898745b7ff35949640227af0049ddde06f901` / tree `3d044210792a11b099efb102a511ee1f41e8a52c`.
- Siguiente accion futura: completar este PR correctivo F9.10 repository-only a `desarrollo`, congelar SHA/tree final post-merge, recalcular la proyeccion exacta aprobada, pedir una segunda autorizacion F9.10 antes de abrir PR a `certificacion`, ejecutar `USER_PERSONAL_UAT` sobre candidate inmutable y solo entonces readiness F10. F10 permanece bloqueada hasta readiness inequivoca.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) conserva su historia y no ejecuta operaciones remotas en este cierre documental. La adenda aprobada separa el cierre CA1 productivo del alcance CA2 pendiente: Hito 1 queda CA1-only, `H1-CA2P` y `H1-CA7P` quedan como antecedentes historicos, y su alcance pendiente pasa a `H2-CA2` y `H4-CA7` sin reutilizar evidencia historica como cierre. F6-F8, v3 y los artifacts F9.7 permanecen inmutables; Free/Pro siguen `UNCHANGED_NOT_ATTESTED`; `GO_FOR_FREE` queda superseded para Hito 1. Hitos 2 a 5 permanecen `PENDING`, sin subfase ejecutable.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
