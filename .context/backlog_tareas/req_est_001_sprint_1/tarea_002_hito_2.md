# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED` |
| Work package | `SUPERSEDED` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | Main queda NO-GO hasta remediacion Pro expand+compat verificada; Pro/writers siguen bloqueados sin JIT |

## Pendiente

1. Versionar remediacion productiva H2 y gates para Pro/main.
2. Mantener evidencia Free aplicada/verificada como anexo de certificacion.
3. Autorizar DDL/DML Pro JIT solo despues de PR protegido de remediacion, backup/PITR y manifest H2 aprobado.
4. Preservar veredicto de certificacion estable, grado documental `A` y validacion contra fuente cliente sanitizada en CI.

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
con CI verde, dejando H2 en `certificacion`. El cierre se valida contra
`SRC-REQ-002` mediante `ADENDA-REQ-EST-001-001`. Pro, writers, schedules,
canaries, deploys y cualquier DDL/DML adicional quedan bloqueados sin aprobacion
JIT separada. La limpieza de calidad de PR #466 retira rewrites de detalle,
social proof anonimo fuera de Sprint 1 y defaults fabricados del comparador; no
toca DB y queda validada en preview Cloudflare final `af2ac376` sin React #418,
sin llamadas legacy `ratings`/`reviews` y sin 404 de rutas exportadas criticas.
PR #467 promovio la compatibilidad a `certificacion` en
`2d499324bb21e750d9bc7c94cb80e7a193062b50`; deployment Cloudflare `4cc2e34c`
estable. El siguiente paso no es main directo: primero debe ejecutarse el plan
productivo [H2 Production Remediation](../../operaciones/h2_production_remediation_plan.md),
con `expand + compatibilidad` Pro aditivo, DB Sync H2 por manifest y verificacion
del baseline Pro `224` antes del deploy frontend.
