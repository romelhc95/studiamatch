# DDL-H2-PRO-EXPAND-COMPAT-20260827

Status: APPROVED_FOR_PRODUCTION_DDL
Authorized manifest: h2-expand-compat
Authorized payload SHA: 3ab8f4874762ec887c5d68437035fde381027c84
Authorized base SHA: 78c00fc915bb758f907ababec01ea11df4cef118
Authorized non-auth digest SHA256: sha256:66c4ddea5515d098543ef7844bd74a2220b6d1cbd279255746d51bc08bb35f21
H2 expected eligible count: 224
H2 expected cohort digest: sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9
Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED
Pro apply gate: APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR

## Alcance

Esta autorizacion JIT humana cubre exclusivamente la ejecucion del manifiesto
`h2-expand-compat` sobre Supabase Pro `xwhtiqmboljkshrtviyw`, usando el payload
exacto autorizado y el orden cerrado del manifiesto. Incluye la reconciliacion
idempotente de la tabla legacy `public.crawler_exclusions`, observada vacia y sin
dependencias funcionales en el preflight read-only. No autoriza `contract`,
writers, schedules, canaries, FG1/FG2/FG3 ni deploy productivo.

## Gates Previos

- Pro preflight read-only: `224` cursos elegibles y visibles publicamente.
- Digest ordenado de cohorte: `sha256:c217dbffc9d50cca0e1f111fcddf1268db9a34e8671a409f3663dcfff1d735e9`.
- `public.crawler_exclusions`: `0` filas; sin funciones o constraints funcionales dependientes detectados.
- Objetos H2 objetivo: ausentes antes de la aplicacion.
- Lectura publica legacy de `public.courses`: preservada durante expand.
- Backup/PITR y aprobacion del environment `Production`: gates runtime obligatorios; esta autorizacion no los sustituye.

## Evidencia Y Cierre

La ejecucion debe ser manual mediante `workflow_dispatch` con `operation=apply`,
`migration_manifest=h2-expand-compat`, `candidate_sha` descendiente del payload,
`apply_authorized=true`, `backup_pitr_verified=true` y este `ddl_authorization_id`.
Luego debe completarse `Verify target schema`, advisors de seguridad/rendimiento y
artifact H2 antes de cualquier PR efectivo hacia `main`.
