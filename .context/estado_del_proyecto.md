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
| `FASE-06` | Reconciliacion DB-as-Code | `COMPLETED` | PR #223 y #224 fusionados; package forward-only y checksum LF/CRLF validados post-merge. Ningun cambio remoto aplicado. |
| `FASE-07` | G1b minimo | `HUMAN_GATE` | Candidate validado con auditoria GO; pendiente CI, review y merge. Package bloqueado. |
| `FASE-08` a `FASE-11` | Fases posteriores | `PENDING` | Permanecen fuera de la ejecucion vigente. |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Fase autorizada: ninguna; F7 espera revision humana.
- Siguiente fase autorizable: ninguna hasta cerrar F7.

## Alcance Inmediato

`FASE-07` fue autorizada y produjo compatibilidad frontend G1b, writers alineados con `pipeline_gate=false`, gates del orquestador antes del limite, gobierno FG1/FG3 y una migration closure forward-only. El package conserva status `reconciled_not_certified`: no se aplico DDL/DML en Free o Pro. La evidencia por postcondicion vive en [Certificacion G1b F7](operaciones/certificacion_g1b_f7.md). `H1-CA7P` esta completado; `H1-CA1` y `H1-CA2P` siguen en progreso hasta certificacion remota y fases posteriores.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
