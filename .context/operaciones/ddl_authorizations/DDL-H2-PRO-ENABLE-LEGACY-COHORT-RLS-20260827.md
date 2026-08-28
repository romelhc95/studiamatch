# DDL-H2-PRO-ENABLE-LEGACY-COHORT-RLS-20260827

Status: APPROVED_FOR_PRODUCTION_DDL
Authorized manifest: h2-expand-compat
Authorized payload SHA: 257b474e1959af0f2253f9e9eaca54b43d8dfa65
Authorized base SHA: 99b17f61a950c5e65ec55e329e011ddeadf5c501
Authorized non-auth digest SHA256: sha256:37dc89e1e8221dadcf5d33a5f3c2129439541390db86fca60eb5cda673c056d7
H2 expected eligible count: 224
H2 expected cohort digest: sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9
Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED
Pro apply gate: APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR

## Alcance

Esta autorizacion JIT humana cubre exclusivamente la migracion forward-only
`20260827_h2_pro_enable_legacy_cohort_rls` dentro del manifiesto
`h2-expand-compat` sobre Supabase Pro `xwhtiqmboljkshrtviyw`. Las migraciones H2
anteriores del manifiesto ya aplicadas no deben ejecutarse nuevamente. La tabla
`private.h2_legacy_public_course_cohort` permanece privada, sin grants ni
politicas publicas.

## Gates Previos

- El expand H2 y la cohorte ya fueron aplicados y verificados en Pro.
- La cohorte contiene `224` cursos y conserva el digest esperado.
- `public.crawler_exclusions` fue retirada durante el expand y no contiene filas.
- El hallazgo critico del Advisor corresponde a RLS deshabilitado en la cohorte privada.
- Backup/PITR y aprobacion del environment `Production` siguen siendo gates runtime obligatorios.

## Evidencia Y Cierre

La ejecucion debe ser manual mediante `workflow_dispatch` con
`operation=apply`, `migration_manifest=h2-expand-compat`, `candidate_sha`
descendiente del payload, `apply_authorized=true`, `backup_pitr_verified=true` y
este `ddl_authorization_id`. Luego debe completarse `operation=verify`, advisors
sin hallazgos criticos nuevos y artifact H2 antes de abrir el PR hacia `main`.
