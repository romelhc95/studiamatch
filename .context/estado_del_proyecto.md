# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-30-F9.7-PR-O-DEFINED`.

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
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | Corte local F9.7 fusionado y PR-O combinado v3 + hold definido localmente en `desarrollo@e2721a0ec4581e422246dfabfa2048297f537025`; v3 sigue byte-identico, security hold `LOCAL_CANDIDATE_BLOCKED` y Free sigue sin certificar. |
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
| `F9.7` | `IN_PROGRESS` | `security_cutoff_local_candidate` local cerrado y fusionado por PR #258; PR #260 fue mergeado por humano en `e2721a0ec4581e422246dfabfa2048297f537025` y contiene `779001c5a63b59bcd902928d1db333e82e6f1d3b`; [PR-O F9.7 v3 + hold](operaciones/pr_o_f9_7_v3_hold.md) queda `DEFINED_LOCAL_NOT_AUTHORIZED`, Free-only futuro, `application_authorized=false`, boundaries `0/3/4/5/6/7`, sin capacidad remota ejecutable; F9.7 permanece `IN_PROGRESS` hasta `GO_F9.7_COMPLETE` en Free; Free/Pro `UNCHANGED_NOT_ATTESTED`, security hold `LOCAL_CANDIDATE_BLOCKED`, Supabase previews skipped y sin Cloudflare manual |
| `F9.8` a `F9.10` | `PENDING` | Plan/ejecucion backfill/T03 y certificacion/T04; gates separados |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase activa: F9.7; [ADR-0005](decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md), [PLAN-H1-CORTE-SFE-001](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md), [PLAN-F9.7-CIERRE-001](operaciones/cierre_definitivo_f9_7.md) y [PR-O F9.7 v3 + hold](operaciones/pr_o_f9_7_v3_hold.md) fijan el corte local y la definicion operacional sucesora: PR #258 cerro `WP-F9.7-04..06`, PR #259 reconcilio el replay, PR #260 fue mergeado por humano en `desarrollo@e2721a0ec4581e422246dfabfa2048297f537025` / tree `0bc0d4b806117fb1b6a2a9fc4d618daa367829ee` y contiene `779001c5a63b59bcd902928d1db333e82e6f1d3b`.
- Subfase autorizada: definicion local de PR-O combinado v3 + security hold mediante nueva rama `feat/*` hacia `desarrollo`; no autoriza Supabase Free/Pro, DDL/DML remoto en Free/Pro, backup/restore, writers, backfill, deploy manual, Cloudflare manual, aplicacion PR-O ni merge automatico.
- Siguiente accion: `aprobacion independiente de GO_FOR_FREE para PR-O combinado v3 + hold`. No aplicar PR-O; F9.7 sigue `IN_PROGRESS` hasta que exista autorizacion y evidencia Free especifica.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) sigue el [plan simplificado](operaciones/plan_simplificado_hito1.md) y el [plan de corte local](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md). F6-F8 y v3 permanecen byte-identicos; `TASK-H1-001` y F9.7 permanecen `IN_PROGRESS`; el nuevo security hold es package terminal separado y `LOCAL_CANDIDATE_BLOCKED`. La atribucion Free previa solo cubrio fuentes ACL y no prueba snapshot actual ni convergencia; Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`. PR-O esta definido localmente como Free-only, `application_authorized=false`, `capabilities=[]`, boundaries `0/3/4/5/6/7` y cero capacidad remota ejecutable; backup/restore, writers/drain y maintenance window quedan `PENDING`. El corte local F9.7 no completa Free. Los artifacts F9.5 siguen `HISTORICAL_NON_PROMOTABLE`. F9.8-F9.10, F10 Produccion y F11 Cierre siguen pendientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
