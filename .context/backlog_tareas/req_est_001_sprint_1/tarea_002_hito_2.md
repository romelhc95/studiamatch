# TASK-H2-001 - HITO-002

| Campo | Valor |
|---|---|
| Estado | `QUALITY_CLEANUP_REMOTE_VERIFIED_PENDING_REVIEW` |
| Work package | `SUPERSEDED` |
| Criterios | `H2-CA2`, `H2-CA3` |
| Bloqueo | PR #466 pendiente de revision humana antes de merge; Pro/writers siguen bloqueados |

## Pendiente

1. Revisar/mergear PR #466 solo tras revision humana.
2. Mantener evidencia Free aplicada/verificada como anexo de certificacion.
3. Autorizar DDL/DML Pro JIT solo despues de merge protegido a Desarrollo, promocion a certificacion y QA equivalente.
4. Preservar veredicto `MERGED_TO_CERTIFICACION_CI_GREEN`, grado documental `A` y validacion contra fuente cliente sanitizada en CI.

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
toca DB y queda validada en preview Cloudflare `be52f883` sin React #418, 401 ni
404 de rutas exportadas criticas.
