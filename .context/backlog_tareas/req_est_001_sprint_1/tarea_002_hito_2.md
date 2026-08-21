# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `ACTIVE_R1_PLANNED_NOT_ACTIVE` |
| Lifecycle stage | `ACTIVE` |
| Implementation status | `PLANNED_NOT_ACTIVE` |
| Criteria status | `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` |
| Work package | `WP-H2-001` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Revision Plan y subfase decimal separada para implementacion R1; R3 JIT separado para DDL/DML, Supabase, backfill y RLS/grants |

## Pendiente

1. O5 de homologacion: `COMPLETED`.
2. Checkout limpio homologado: `COMPLETED`.
3. Aprobar `WP-H2-001` por digest verificable: `COMPLETED_R1_NOT_ACTIVE`.
4. Activar `WP-H2-001` hasta R1: `COMPLETED_ACTIVE_R1`.
5. Definir revision Plan y subfase decimal de implementacion local R1.
6. Autorizar DDL/DML Free JIT cuando corresponda.
7. Autorizar DDL/DML Pro JIT solo despues de certificacion y aprobacion separada.
8. Ejecutar migracion forward-only, pruebas RLS/grants, backfill idempotente y segundo run `NOOP`.

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

No hay implementacion iniciada en F10.11. H2 no inicia trabajo funcional hasta revision Plan y autorizacion posterior exacta de una subfase decimal. La activacion vigente solo autoriza R1 local.
