# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-26`.

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
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | F9.5 cerro `COMPLETED_WITH_KNOWN_FINDINGS`; Free sigue sin certificar y F9.6 P0 H-00 es la subfase activa, pendiente de autorizacion. |
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
| `F9.6` | `ACTIVE_AWAITING_AUTHORIZATION` | P0 H-00 Free-only definido: la autorizacion futura debe ligar target, backup, predicado, verificador y allowlist privada antes de la revalidacion counts-only; Pro prohibido |
| `F9.7` a `F9.10` | `PENDING` | Schema/T02, plan/ejecucion backfill/T03 y certificacion/T04; gates separados |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase activa: F9.6, definida y enlazada; no hay capacidad de ejecucion heredada.
- Subfase autorizada: ninguna. F9.5 esta cerrada y T01 fue aceptada solo como decision documental condicionada para definir F9.6.
- Siguiente accion: F9.6 requiere una autorizacion decimal exacta nueva y no hereda capacidad de F9.5 ni de T01.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) sigue el [plan simplificado](operaciones/plan_simplificado_hito1.md). F6-F8 son la unica base funcional contractual de Hito 1. Los artifacts F9.5 de PR #245 y PR #247 se conservan sin eliminarlos como `HISTORICAL_NON_PROMOTABLE`: no son candidate, package contractual ni autorizacion para F9.7. `H1-CA1`, `H1-CA2P` y `H1-CA7P` se reconcilian en [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md); los hallazgos diferidos viven en el [backlog F9.5](backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md). F10 Produccion y F11 Cierre siguen pendientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
