# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `READY_FOR_DIGEST_APPROVAL` |
| Lifecycle stage | `AWAITING_DIGEST` |
| Implementation status | `PLANNED_NOT_ACTIVE` |
| Criteria status | `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` |
| Work package | `WP-H2-001` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Aprobacion digest; R3 JIT separado para DDL/DML, Supabase, backfill y RLS/grants |

## Pendiente

1. O5 de homologacion: `COMPLETED`.
2. Checkout limpio homologado: `COMPLETED`.
3. Aprobar `WP-H2-001` por digest verificable.
4. Autorizar DDL/DML Free JIT cuando corresponda.
5. Autorizar DDL/DML Pro JIT solo despues de certificacion y aprobacion separada.
6. Ejecutar migracion forward-only, pruebas RLS/grants, backfill idempotente y segundo run `NOOP`.

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

No hay ejecucion activa en F10.11. H2 no inicia hasta aprobacion humana exacta del digest y commit candidate de `WP-H2-001`. La primera aprobacion solo puede autorizar R1.
