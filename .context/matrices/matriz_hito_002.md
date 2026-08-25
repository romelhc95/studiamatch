# Matriz Hito 002

| Unidad | Gate status | Implementation status | Criteria status | Evidencia requerida |
|---|---|---|---|---|
| `H2-CA2` | `FORWARD_FIX_JIT_REQUIRED` | `LOCAL_VALIDATED` | `LOCAL_PASS_REMOTE_PENDING` | Migracion forward-only, diccionario, RLS/grants, writer inventory, auditoria y tests por rol. |
| `H2-CA3` | `BACKFILL_JIT_REQUIRED` | `LOCAL_DRY_RUN_READY` | `LOCAL_PASS_REMOTE_PENDING` | Registros incompletos preservados, `missing_fields`, pipeline tolerante, backfill reanudable y segundo run `NOOP`. |

## Enlaces Canonicos

- Estado vivo: [Estado Del Proyecto](../estado_del_proyecto.md)
- Plan vinculante: [Plan Vinculante Nuevo Pedido](../operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md)
- Plan Maestro: [Plan Maestro Sprint 1 H2-H5](../operaciones/plan_maestro_sprint1_h2_h5.md)
- Hito: [HITO-002](../hitos/hito_002.md)
- TASK: [TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- Evidencia: [Evidencia Hito 002](../evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md)

## Validaciones Minimas Futuras

- `pytest` para validador/backfill cuando exista codigo.
- Pruebas SQL en PostgreSQL 17 cuando cambie `db/**`.
- Evidencia por ambiente antes de promover.
- Aprobacion JIT separada para cualquier DDL/DML, Supabase, backfill o writer.
