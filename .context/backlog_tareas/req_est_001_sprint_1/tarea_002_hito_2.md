# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `FREE_DDL_APPLIED_BACKFILL_BLOCKED` |
| Work package | `SUPERSEDED` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Aprobacion JIT para DB, Supabase, backfill o writers |

## Pendiente

1. Abrir PR H2 separado despues del PR documental.
2. Autorizar DDL/DML Free JIT cuando corresponda.
3. Autorizar DDL/DML Pro JIT solo despues de certificacion y aprobacion separada.
4. Ejecutar migracion forward-only, pruebas RLS/grants, backfill idempotente y segundo run `NOOP`.

## Preparacion Actual

- Inventario y diseno no operativo: [H2 Editorial Layer Inventory](../../operaciones/h2_editorial_layer_inventory.md).
- Solicitud JIT Free consumida y acotada: [DDL-H2-EDITORIAL-LAYER-FREE](../../operaciones/ddl_authorizations/DDL-H2-EDITORIAL-LAYER-FREE.md).

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

H2 tiene DDL Free aplicada para la capa editorial. Backfill, Pro, writers,
schedules, canaries, deploys y cualquier DDL/DML adicional quedan bloqueados sin
aprobacion JIT separada.
