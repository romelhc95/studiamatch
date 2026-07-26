# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-07-25`.

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
| `F9` | Certificacion Hito 1 en Free | `IN_PROGRESS` | F9.1/F9.2 locales completadas; Free sigue `reconciled_not_certified`. Candidate local F9.3 verificado, pendiente de CI/review/merge y replay post-merge. |
| `F10` | Pro y produccion | `PENDING` | Bloqueada hasta que F9 termine en `free_certified`; incluye canary, `main`, smoke y observacion. |
| `F11` | Cierre final | `PENDING` | Bloqueada hasta completar produccion observada; retira el plan temporal mediante PR. |

## Subfases F9

| ID | Estado | Identidad vigente |
|---|---|---|
| `F9.1` | `COMPLETED` | Precertificacion local; alias historico `FASE-09`, PR #231/#232 y cierre #233 |
| `F9.2` | `COMPLETED` | Contrato local de promocion; alias historico `FASE-10`, PR #235/#236 |
| `F9.3` | `IN_PROGRESS` | Freeze local autorizado; candidate verificado sin red/secrets, pendiente de CI/review/merge y replay post-merge |
| `F9.4` a `F9.10` | `PENDING` | Lectura Free, T01, schema/T02, H-00, plan/ejecucion backfill/T03 y certificacion/T04; solo reservas |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase autorizada: `F9.3` local mediante `Ejecuta las tareas pendientes de la Fase F9.3`; no autoriza F9.4 ni operaciones remotas.
- Siguiente subfase autorizable: ninguna hasta cerrar F9.3 mediante CI, review, merge, replay post-merge y cierre documental. F9.4 permanece reservada.

## Alcance Inmediato

La [macrofase F9](operaciones/certificacion_hito1_f9.md) restaura el plan inicial. Los packages historicos `FASE-09` y `FASE-10` se preservan como F9.1/F9.2 completadas, sin renombrar artifacts. F8 permanece byte-identico, `reconciled_not_certified`, con Free/Pro bloqueados y cero attestations. `H1-CA2P` y `TASK-H1-001` siguen en progreso. El candidate F9.3 congela localmente el contrato read-only y paso 55 pruebas focused, 253 de regresion, replay sintetico y auditorias security/QA; aun no esta cerrado. F9.4 sera la primera lectura Free bajo otro gate. F10 Produccion y F11 Cierre permanecen pendientes.

Los cambios funcionales posteriores deben seguir [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), [Matriz DB](operaciones/matriz_adopcion_db.md) y [Release minimo](operaciones/flujo_release_minimo.md).
