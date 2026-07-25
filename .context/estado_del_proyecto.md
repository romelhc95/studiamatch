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
| `FASE-09` | Precertificacion local H1-CA2P | `PENDING` | Alcance local/offline definido; requiere merge del PR de definicion y nueva autorizacion exacta posterior. |
| `FASE-10` a `FASE-11` | Fases posteriores | `PENDING` | Permanecen sin alcance ejecutable definido. |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Fase autorizada: ninguna; F8 esta cerrada.
- Siguiente fase autorizable: `FASE-09` solo despues de fusionar su definicion y emitir una nueva autorizacion exacta.

## Alcance Inmediato

`FASE-08` produjo un contrato funcional local con verifier fuerte, PostgreSQL 17 efimero, persistencia fail-closed y un manifest F8 cerrado. PR #228 recibio CI verde, aprobacion y merge humano; `desarrollo@dbda29e` conserva el tree exacto y repite 121 pruebas, Python compile, Context Graph y PostgreSQL 17 en PASS. La evidencia vive en [Certificacion local Hito 1 F8](operaciones/certificacion_hito1_f8.md). No se aplico DDL/DML en Free o Pro y el package conserva status `reconciled_not_certified`. `H1-CA1` y `H1-CA7P` estan completados; `H1-CA2P` y `TASK-H1-001` siguen en progreso. [F9](operaciones/precertificacion_hito1_f9.md) queda definida solo para precertificacion local; no hereda la autorizacion emitida antes de esta definicion ni habilita Free/Pro.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
