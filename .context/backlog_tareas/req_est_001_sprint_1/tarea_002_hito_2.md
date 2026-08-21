# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `PLANNED_NOT_ACTIVE` |
| Work package | `WP-H2-001` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | O5, checkout limpio y aprobacion digest |

## Pendiente

1. Completar O5 de homologacion.
2. Aprobar `WP-H2-001` por digest verificable.
3. Autorizar DDL/DML Free JIT cuando corresponda.
4. Autorizar DDL/DML Pro JIT solo despues de certificacion y aprobacion separada.
5. Ejecutar migracion forward-only, pruebas RLS/grants, backfill idempotente y segundo run `NOOP`.

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

No hay ejecucion activa en F10.11.
