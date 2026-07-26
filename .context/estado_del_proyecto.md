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
| `F6` | Reconciliacion DB-as-Code | `COMPLETED` | PR #223 y #224 fusionados; package forward-only y checksum LF/CRLF validados post-merge. Ningun cambio remoto aplicado. |
| `F7` | G1b minimo | `COMPLETED` | PR #226 fusionado; G1b y postcondiciones F7 validadas post-merge. Package bloqueado. |
| `F8` | Hito 1 funcional | `COMPLETED` | PR #228 fusionado; contrato funcional local y PostgreSQL 17 validados post-merge. Sin aplicacion DB remota. |
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | La remediacion local v2 cierra el inventario de 21 policies; Free sigue `reconciled_not_certified` hasta repetir F9.5 read-only. |
| `F10` | Pro y produccion | `PENDING` | Bloqueada hasta que F9 termine en `free_certified`; incluye canary, `main`, smoke y observacion. |
| `F11` | Cierre final | `PENDING` | Bloqueada hasta completar produccion observada; consolida evidencia final y limpieza autorizada. |

## Subfases F9

| ID | Estado | Identidad vigente |
|---|---|---|
| `F9.1` | `COMPLETED` | Precertificacion local; alias historico `FASE-09`, PR #231/#232 y cierre #233 |
| `F9.2` | `COMPLETED` | Contrato local de promocion; alias historico `FASE-10`, PR #235/#236 |
| `F9.3` | `COMPLETED` | Freeze local; PR #238, remediacion CRLF #239 y replay post-merge Docker sobre checkout Linux limpio |
| `F9.4` | `COMPLETED` | Reconciliacion contractual local; plan simplificado adoptado, definicion remota sustituida y antecedente temporal retirado |
| `F9.5` | `BLOCKED` | [Preflight Free dirigido](operaciones/preflight_free_f9_5.md); remediacion v2 local de seis entradas pendiente de repeticion read-only |
| `F9.6` a `F9.10` | `PENDING` | H-00, schema/T02, plan/ejecucion backfill/T03 y certificacion/T04; gates separados |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase autorizada: ninguna. La autorizacion local F9.5 para la remediacion v2 se consume con su merge y validacion post-merge.
- Siguiente accion: repetir F9.5 exclusivamente read-only contra el overlay v2 mediante una autorizacion nueva. F9.6 permanece bloqueada.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) sigue el [plan simplificado](operaciones/plan_simplificado_hito1.md). Los packages historicos `FASE-09`, `FASE-10`, F8 y el overlay F9.5 de cinco entradas permanecen byte-identicos. El overlay v2 agrega una sexta migration forward-only, cierra exactamente 21 policies y permanece `reconciled_not_certified`, bloqueado para Free/Pro. `H1-CA2P` y `TASK-H1-001` siguen en progreso; T01 no existe y F9.6 permanece bloqueada. F10 Produccion y F11 Cierre siguen pendientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
