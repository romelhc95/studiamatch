# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-25`.

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
| `FASE-07` | G1b minimo | `COMPLETED` | PR #226 fusionado; G1b y postcondiciones F7 validadas post-merge. Package bloqueado. |
| `FASE-08` | Hito 1 funcional | `COMPLETED` | PR #228 fusionado; contrato funcional local y PostgreSQL 17 validados post-merge. Sin aplicacion DB remota. |
| `FASE-09` | Precertificacion local H1-CA2P | `COMPLETED` | PR #231 y remediacion #232 fusionados; replay local Windows/Linux validado post-merge. F8 permanece bloqueado e inmutable. |
| `FASE-10` | Contrato local de promocion H1-CA2P | `PENDING` | Alcance local/offline definido; requiere merge de esta definicion y nueva autorizacion exacta. |
| `FASE-11` | Preflight Free read-only | `PENDING` | Capacidad reservada; requiere definicion posterior independiente. |
| `FASE-12` | Aceptacion local de readiness Free | `PENDING` | Capacidad reservada para validar evidencia F11 y crear T01; requiere definicion independiente. |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Fase autorizada: ninguna; F9 esta cerrada.
- Siguiente fase autorizable: `FASE-10` solo despues de fusionar esta definicion y emitir una nueva autorizacion exacta.

## Alcance Inmediato

`FASE-09` quedo cerrada en `desarrollo@b9053ab`. El siguiente bloqueo es el ciclo de promocion entre schema, postcondiciones Free y backfill. [F10](operaciones/promocion_hito1_f10.md) queda definida para repararlo solo en Git/local, sin acceso Free/Pro ni cambio de status. `H1-CA2P` y `TASK-H1-001` siguen en progreso.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
