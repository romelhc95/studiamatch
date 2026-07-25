# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-24`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases. El estado vivo de la tarea activa pertenece a la propia tarea.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `FASE-00` | Preservacion | `COMPLETED` | Preservacion verificada. |
| `FASE-01` | Main a certificacion | `COMPLETED` | Convergencia verificada. |
| `FASE-02` | Certificacion a desarrollo | `COMPLETED` | Convergencia verificada. |
| `FASE-03` | Higiene remota | `COMPLETED` | Higiene terminada. |
| `FASE-04` | Bootstrap local | `COMPLETED` | Entorno local verificado. |
| `FASE-05` | Obsidian minimo | `COMPLETED` | Gobierno documental, PR #221 y `SRC-REQ-001` reconciliada. |
| `FASE-06` | Reconciliacion DB-as-Code | `HUMAN_GATE` | PR #223 fusionado; forward-fix de checksum LF/CRLF validado y pendiente de CI, review y merge. Ningun cambio remoto aplicado. |
| `FASE-07` a `FASE-11` | Fases posteriores | `PENDING` | Permanecen fuera de la ejecucion vigente. |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Fase autorizada: ninguna; el forward-fix F6 espera revision humana.
- Siguiente fase autorizable: ninguna hasta cerrar F6.

## Alcance Inmediato

`FASE-06` fue autorizada y produjo migrations por postcondicion, un manifest cerrado y la exclusion mecanica de `H-00`. PR #223 fue aprobado y fusionado en `desarrollo`; la validacion post-merge desde Docker sobre el bind mount Windows detecto checksums distintos por CRLF. El forward-fix canoniza LF/CRLF tanto en manifest como en ledger y pasa 74 pruebas, pero F6 no cierra antes de CI, aprobacion y merge humanos. `H1-CA7P` esta completado; `H1-CA1` y `H1-CA2P` mantienen `TASK-H1-001` en progreso. Ninguna migration F6 fue aplicada a Free o Pro.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
