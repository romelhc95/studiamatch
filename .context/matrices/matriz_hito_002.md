# Matriz Hito 002

| Unidad | Gate status | Implementation status | Criteria status | Evidencia requerida |
|---|---|---|---|---|
| `H2-CA2` | `BLOCKED_NEW_REQUEST_REQUIRED` | `PLANNED_NOT_ACTIVE` | `NOT_STARTED` | Migracion forward-only, diccionario, RLS/grants, writer inventory, auditoria y tests por rol. |
| `H2-CA3` | `BLOCKED_NEW_REQUEST_REQUIRED` | `PLANNED_NOT_ACTIVE` | `NOT_STARTED` | Registros incompletos preservados, `missing_fields`, pipeline tolerante, backfill reanudable y segundo run `NOOP`. |

## Enlaces Canonicos

- Estado vivo: [Estado Del Proyecto](../estado_del_proyecto.md)
- Plan Maestro: [Plan Maestro Sprint 1 H2-H5](../operaciones/plan_maestro_sprint1_h2_h5.md)
- Hito: [HITO-002](../hitos/hito_002.md)
- TASK: [TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- Evidencia: [Evidencia Hito 002](../evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md)

## Validaciones Minimas Futuras

- `pytest` para validador/backfill cuando exista codigo.
- Pruebas SQL en PostgreSQL 17 cuando cambie `db/**`.
- Evidencia por ambiente antes de promover.
- Nuevo pedido explicito y aprobacion JIT separada para cualquier DDL/DML.
