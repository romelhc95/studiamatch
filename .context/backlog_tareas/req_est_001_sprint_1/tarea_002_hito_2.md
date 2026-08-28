# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED` |
| Work package | `SUPERSEDED` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Main queda NO-GO hasta remediacion Pro expand+compat verificada; Pro/writers siguen bloqueados sin JIT |

## Pendiente

1. Ejecutar `DB Sync to Production` con `operation=verify` sobre `certificacion` para generar el artifact H2 y validar advisors Pro sin hallazgos HIGH/CRITICAL.
2. Versionar `.context/operaciones/h2_main_production_expand_evidence.json` y abrir PR `certificacion -> main`.
3. Mantener evidencia Free aplicada/verificada como anexo de certificacion.
4. Preservar veredicto de certificacion estable, grado documental `A` y validacion contra fuente cliente sanitizada en CI.
5. Cualquier DDL/DML Pro adicional, writer, schedule o deploy requiere aprobacion JIT separada.

## Preparacion Actual

- Inventario y diseno no operativo: [H2 Editorial Layer Inventory](../../operaciones/h2_editorial_layer_inventory.md).
- Solicitud JIT Free consumida y acotada: [DDL-H2-EDITORIAL-LAYER-FREE](../../operaciones/ddl_authorizations/DDL-H2-EDITORIAL-LAYER-FREE.md).

## Criterios De Implementacion Futura

- CA2 debe entregar contrato editorial, diccionario, estados, `missing_fields`, `field_sources`, ownership, writers, RLS/grants, migracion y backfill.
- CA3 debe probar que registros incompletos se conservan, quedan pendientes y no detienen pipeline.
- Leads se limitan a schema/flags y CTA visual; cero captura, almacenamiento o egress.
- Schedules y writers continuan pausados hasta JIT R3 posterior a H2.

H2 tiene DDL Free aplicada para la capa editorial, forward-fix, remediacion
Security Advisor, backfill editorial Free con segundo `NOOP` validado y seed
`editorial_field_definitions` aplicado/verificado y fix de vista publica Free
aplicado/verificado con `0` campos privados expuestos. La correccion de compatibilidad
prepara `private.h2_legacy_public_course_cohort` para que los cursos legacy
`active + verified + production_enabled` sigan visibles en Desarrollo sin fallback
frontend a `courses`. Post-apply Free detecto `227` cursos legacy elegibles,
`227` en cohorte, `227` efectivos, `0` faltantes y `0` inesperados; preview #466
muestra catalogo, detalle y comparador reales. PR #458 fue aprobado y
mergeado a `desarrollo` con CI verde; PR #459 y PR #460 tambien fueron mergeados
con CI verde, dejando H2 en `certificacion`. Post-certificacion se integraron:
forward-fix del endpoint Security Advisor (PR #477), proteccion RLS sobre la
cohorte privada (PR #478) y correccion del workflow `DB Sync to Production` para
verificacion post-apply (PRs #480/#481). El apply del manifiesto Pro
`h2-expand-compat` fue ejecutado de forma aditiva con backup/PITR verificado y
baseline elegible `224`. El cierre se valida contra `SRC-REQ-002` mediante
`ADENDA-REQ-EST-001-001`. Pro, writers, schedules, canaries, deploys y cualquier
DDL/DML adicional quedan bloqueados sin aprobacion JIT separada. El siguiente paso
no es main directo: primero debe ejecutarse `DB Sync to Production` con
`operation=verify` sobre `certificacion`, versionar
`.context/operaciones/h2_main_production_expand_evidence.json` y abrir el PR
`certificacion -> main`, segun [H2 Production Remediation](../../operaciones/h2_production_remediation_plan.md).
