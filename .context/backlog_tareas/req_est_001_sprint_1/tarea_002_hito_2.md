# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `ACTIVE_R1_BLOCKED_PENDING_OBSIDIAN_MAIN` |
| Lifecycle stage | `ACTIVE` |
| Implementation status | `BLOCKED_PENDING_OBSIDIAN_MAIN` |
| Criteria status | `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` |
| Work package | `WP-H2-001` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Etapa 1 Obsidian pendiente de main; H2-CA2/H2-CA3, R2 y R3 separados; DDL/DML, Supabase, backfill y RLS/grants remotos requieren JIT |

## Enlaces Canonicos

- Estado vivo: [Estado Del Proyecto](../../estado_del_proyecto.md)
- Plan Maestro: [Plan Maestro Sprint 1 H2-H5](../../operaciones/plan_maestro_sprint1_h2_h5.md)
- Hito: [HITO-002](../../hitos/hito_002.md)
- Matriz: [Matriz Hito 002](../../matrices/matriz_hito_002.md)
- Evidencia: [Evidencia Hito 002](../../evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md)
- Work package: [WP-H2-001](../../work_packages/WP-H2-001.json)

## Pendiente

1. O5 de homologacion: `COMPLETED`.
2. Checkout limpio homologado: `COMPLETED`.
3. Aprobar `WP-H2-001` por digest verificable: `COMPLETED_R1_NOT_ACTIVE`.
4. Activar `WP-H2-001` hasta R1: `COMPLETED_ACTIVE_R1`.
5. Definir revision Plan y subfase decimal de implementacion local R1: `LOCAL_CANDIDATE_PENDING_MAIN`.
6. Publicar y homologar documentacion Obsidian en `main`: `LOCAL_CANDIDATE_PENDING_MAIN`.
7. Rebasar/reactivar WP de Hito 2 desde checkout ordinario actualizado: `BLOCKED_PENDING_OBSIDIAN_MAIN`.
8. Autorizar DDL/DML Free JIT cuando corresponda.
9. Autorizar DDL/DML Pro JIT solo despues de certificacion y aprobacion separada.
10. Ejecutar migracion forward-only, pruebas RLS/grants, backfill idempotente y segundo run `NOOP`.

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

No hay implementacion funcional iniciada antes de `F12.1`. La siguiente ejecucion de Hito 2 queda bloqueada hasta cierre efectivo de Etapa 1 en main y nueva/rebasada aprobacion WP. H2-CA3, R2 y cualquier R3 requieren gates posteriores separados.
