# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `NEXT_ACTIVE_SCOPE_PENDING_PR_AND_JIT_DB` |
| Work package | `SUPERSEDED` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Aprobacion JIT para DB, Supabase, backfill o writers |

## Pendiente

1. Abrir PR H2 separado despues del PR documental.
2. Autorizar DDL/DML Free JIT cuando corresponda.
3. Autorizar DDL/DML Pro JIT solo despues de certificacion y aprobacion separada.
4. Ejecutar migracion forward-only, pruebas RLS/grants, backfill idempotente y segundo run `NOOP`.

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

H2 es el siguiente alcance tecnico, pero cualquier DB/Supabase/backfill/writer queda bloqueado sin aprobacion JIT separada.
