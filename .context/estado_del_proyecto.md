# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-30-F9.7-POSTMERGE-FOLLOWUP`.

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
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | Corte local F9.7 fusionado y reconciliado en `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c`; v3 sigue byte-identico, security hold `LOCAL_CANDIDATE_BLOCKED` y Free sigue sin certificar. |
| `F10` | Pro y produccion | `PENDING` | Bloqueada hasta que F9 termine en `free_certified`; incluye canary, `main`, smoke y observacion. |
| `F11` | Cierre final | `PENDING` | Bloqueada hasta completar produccion observada; incluye limpieza fisica autorizada de artifacts historicos. |

## Subfases F9

| ID | Estado | Identidad vigente |
|---|---|---|
| `F9.1` | `COMPLETED` | Precertificacion local; alias historico `FASE-09`, PR #231/#232 y cierre #233 |
| `F9.2` | `COMPLETED` | Contrato local de promocion; alias historico `FASE-10`, PR #235/#236 |
| `F9.3` | `COMPLETED` | Freeze local; PR #238, remediacion CRLF #239 y replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | `COMPLETED` | Reconciliacion contractual local; plan simplificado adoptado, definicion remota sustituida y antecedente temporal retirado |
| `F9.5` | `COMPLETED_WITH_KNOWN_FINDINGS` | Cierre contractual/documental; artifacts de PR #245 y PR #247 son `HISTORICAL_NON_PROMOTABLE`; no queda lectura Free pendiente |
| `F9.6` | `COMPLETED` | `H00_ALREADY_REMEDIATED_NO_DML`: cohorte con PII directa remediada, conservada como pseudonimizada; Gate B DELETE `SUPERSEDED_NON_AUTHORIZABLE`; Pro prohibido |
| `F9.7` | `IN_PROGRESS` | `security_cutoff_local_candidate` local cerrado y fusionado por PR #258; merge `e95eeaccc864477db587bbb13c827d0c17340d8d` conserva tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`; PR #259 reconcilio el replay y fue fusionado en `fdaac633d29476e3323a8f88741a87570ece3b7c` con tree `2fa573d878eb566dd00f6fe21939e5b6420133ed`; `CORR-WP-F9.7-04-02` y `WP-F9.7-04..06` quedan cerrados localmente; F9.7 permanece `IN_PROGRESS` hasta `GO_F9.7_COMPLETE` en Free; Free/Pro `UNCHANGED_NOT_ATTESTED`, security hold `LOCAL_CANDIDATE_BLOCKED`, Supabase previews skipped y sin Cloudflare manual |
| `F9.8` a `F9.10` | `PENDING` | Plan/ejecucion backfill/T03 y certificacion/T04; gates separados |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase activa: F9.7; [ADR-0005](decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md), [PLAN-H1-CORTE-SFE-001](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md) y [PLAN-F9.7-CIERRE-001](operaciones/cierre_definitivo_f9_7.md) fijan el corte local y su secuencia `WP-F9.7-01..06`: PR #258 tuvo `NO_GO_CI`, `NO_GO_CI_120D234` y `NO_GO_CI_D2CB32E` sobre candidates no promocionables, luego `CORR-WP-F9.7-04-02` produjo `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`; CI verde, seis auditorias finales `GO_FOR_LOCAL_PR` en [issuecomment-5133103661](https://github.com/romelhc95/studiamatch/pull/258#issuecomment-5133103661), aprobacion humana `romelhc95-approver`, merge humano `e95eeaccc864477db587bbb13c827d0c17340d8d`, replay post-merge Docker/Linux PASS y reconciliacion documental PR #259 fusionada en `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c` / tree `2fa573d878eb566dd00f6fe21939e5b6420133ed` cierran `CORR-WP-F9.7-04-02` y `WP-F9.7-04..06` localmente.
- Subfase autorizada: follow-up documental post-merge sobre `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c` mediante nueva rama `feat/*` hacia `desarrollo`; no autoriza Supabase Free/Pro, DDL/DML remoto en Free/Pro, backup/restore, writers, backfill, deploy manual, Cloudflare manual, PR-O ni merge automatico.
- Siguiente accion: `definicion de PR-O combinado v3 + hold`. No implementar ni aplicar PR-O; F9.7 sigue `IN_PROGRESS` hasta que exista autorizacion y evidencia Free especifica.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) sigue el [plan simplificado](operaciones/plan_simplificado_hito1.md) y el [plan de corte local](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md). F6-F8 y v3 permanecen byte-identicos; `TASK-H1-001` y F9.7 permanecen `IN_PROGRESS`; el nuevo security hold es package terminal separado y `LOCAL_CANDIDATE_BLOCKED`. La atribucion Free previa solo cubrio fuentes ACL y no prueba snapshot actual ni convergencia; Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`. Gate B, la atestacion ACL, `validate_wp_f9_7_04_ci_forward_fix`, PR #258 y PR #259 quedan como acciones historicas o `SUPERSEDED` por el snapshot `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c`. Backup/restore y writers solo tienen runbooks de datos sin capacidad. El corte local F9.7 ya esta fusionado y reconciliado en `desarrollo`, pero no completa Free. Los artifacts F9.5 siguen `HISTORICAL_NON_PROMOTABLE`. F9.8-F9.10, F10 Produccion y F11 Cierre siguen pendientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
