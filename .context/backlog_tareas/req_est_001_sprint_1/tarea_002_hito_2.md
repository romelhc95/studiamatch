# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `PLANNED_NOT_ACTIVE` |
| Work package | `SUPERSEDED` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Nuevo pedido explicito y aprobacion JIT para DB |

## Pendiente

1. Recibir nuevo pedido explicito posterior a F10.11.
2. Autorizar DDL/DML Free JIT cuando corresponda.
3. Autorizar DDL/DML Pro JIT solo despues de certificacion y aprobacion separada.
4. Ejecutar migracion forward-only, pruebas RLS/grants, backfill idempotente y segundo run `NOOP`.

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

No hay ejecucion activa en F10.11.
