# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-29`.

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
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | Corte local F9.7 de seguridad/funcionalidad/estabilidad en definicion; v3 sigue byte-identico y el security hold queda candidate bloqueado; Free sigue sin certificar. |
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
| `F9.7` | `IN_PROGRESS` | `security_cutoff_local_candidate`; PR #258 tuvo `NO_GO_CI` inicial y luego `NO_GO_CI_120D234`; candidates `b711e0b`/`249295` y `120d234`/`bf68ed` quedan no promocionables; `CORR-WP-F9.7-04-02` esta `IN_PROGRESS`, `WP-F9.7-05` queda `INVALIDATED_BY_CI_PARITY_GAP` y auditorias previas quedan `INVALIDATED_STALE_ORACLE`; v3 byte-identico, security hold bloqueado para Free/Pro, Free/Pro `UNCHANGED_NOT_ATTESTED`, Supabase previews skipped y `AUTOMATIC_PR_PREVIEW_ACCEPTED` sin Cloudflare manual |
| `F9.8` a `F9.10` | `PENDING` | Plan/ejecucion backfill/T03 y certificacion/T04; gates separados |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase activa: F9.7; [ADR-0005](decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md), [PLAN-H1-CORTE-SFE-001](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md) y [PLAN-F9.7-CIERRE-001](operaciones/cierre_definitivo_f9_7.md) fijan el corte local y su secuencia `WP-F9.7-01..06`: PR #258 descubrio `BLOCKING_IN_SCOPE` de CI/release gates propiedad de `WP-F9.7-04`; el primer forward-fix `120d234` corrigio la evidencia local pero fallo en CI por paridad actionlint/env-i/frontend cold-cache, por lo que `CORR-WP-F9.7-04-01=NO_GO_CI_PARTIAL`, `CORR-WP-F9.7-04-02=IN_PROGRESS`, `WP-F9.7-05=INVALIDATED_BY_CI_PARITY_GAP`, `WP-F9.7-06=NO_GO_CI_120D234` y las auditorias previas quedan `INVALIDATED_STALE_ORACLE`.
- Subfase autorizada: forward-fix local acotado de `WP-F9.7-04` mediante `CORR-WP-F9.7-04-02`, validaciones, commit hijo normal, push a `feat/f9-7-security-cutoff` y actualizacion de PR #258. Supabase Free/Pro, DDL/DML, backup/restore, writers, backfill, deploy manual, Cloudflare manual y merge siguen prohibidos; se acepta solo preview automatico del PR como `AUTOMATIC_PR_PREVIEW_ACCEPTED`.
- Siguiente accion: `validate_wp_f9_7_04_ci_forward_fix`; la secuencia obligatoria es `READY_FOR_CI` -> CI verde -> seis auditorias finales nuevas -> `GO_FOR_HUMAN_REVIEW`, sin merge automatico.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) sigue el [plan simplificado](operaciones/plan_simplificado_hito1.md) y el [plan de corte local](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md). F6-F8 y v3 permanecen byte-identicos; `TASK-H1-001` y F9.7 permanecen `IN_PROGRESS`; el nuevo security hold es package terminal separado y bloqueado. La atribucion Free previa solo cubrio fuentes ACL y no prueba snapshot actual ni convergencia; Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`. Gate B y la atestacion ACL quedan consumidos; backup/restore y writers solo tienen runbooks de datos sin capacidad. Los artifacts F9.5 siguen `HISTORICAL_NON_PROMOTABLE`. F9.8-F9.10, F10 Produccion y F11 Cierre siguen pendientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
