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
| `FASE-10` | Contrato local de promocion H1-CA2P | `COMPLETED` | PR #235 fusionado; contrato local, aislamiento y replay post-merge validados. Sin acceso remoto ni cambio de status. |
| `FASE-11` | Preflight Free read-only | `PENDING` | Capacidad reservada; requiere definicion posterior independiente. |
| `FASE-12` | Aceptacion local de readiness Free | `PENDING` | Capacidad reservada para validar evidencia F11 y crear T01; requiere definicion independiente. |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Fase autorizada: ninguna; F10 esta cerrada.
- Siguiente fase autorizable: ninguna hasta definir canonicamente el alcance ejecutable de F11.

## Alcance Inmediato

`FASE-10` agrego descriptor v2 inmutable, requisitos por transicion, attestations fail-closed, canonicalizacion y aislamiento sin egress. PR #235 recibio CI verde, aprobacion independiente y merge humano. `desarrollo@d67fa31` conserva el tree exacto `861aaa1c` del candidate y repitio F10/F9, compile, Context Graph y gates frontend en PASS. F8 permanece byte-identico y bloqueado; acceso Free/Pro, mutacion remota y cambios de status fueron `0`. La trazabilidad conserva pendientes las antiguas F9-F11 del plan temporal. `H1-CA2P` y `TASK-H1-001` siguen en progreso; F11 requiere definicion y autorizacion independientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
