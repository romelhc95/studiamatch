# Matriz Hito 002

| Unidad | Estado | Evidencia requerida |
|---|---|---|
| `H2-CA2` | `PLANNED_NOT_ACTIVE` | Migracion forward-only, diccionario, RLS/grants, writer inventory, auditoria y tests por rol. |
| `H2-CA3` | `PLANNED_NOT_ACTIVE` | Registros incompletos preservados, `missing_fields`, pipeline tolerante, backfill reanudable y segundo run `NOOP`. |

## Validaciones Minimas Futuras

- `pytest` para validador/backfill cuando exista codigo.
- Pruebas SQL en PostgreSQL 17 cuando cambie `db/**`.
- Evidencia por ambiente antes de promover.
