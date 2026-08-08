# DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO

Status: APPROVED_FOR_PRODUCTION_DDL
Authorized migration: 20260808_fase10_8_atomic_cleansing_provenance
Authorized base SHA: 1885806f0d9f189600d410d353fcf13fb8dd4676
Authorized non-auth digest SHA256: sha256:efca1ea5daeb45bb6239669dc28823915da12d6c703e6b900c8416396ddc77d9
Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED
Pro apply gate: APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR

## Alcance

Este registro autoriza exclusivamente la futura evaluacion de apply Pro de la
migracion forward-only `20260808_fase10_8_atomic_cleansing_provenance`, ya
aplicada y verificada en Free/Desarrollo dentro de F10.8. No autoriza DDL/DML
por si solo: el workflow debe ejecutarse manualmente sobre `main`, con
`candidate_sha` exacto igual a `origin/main`, aprobacion del environment
`Production`, `apply_authorized=true`, `backup_pitr_verified=true` y
`PRODUCTION_WRITERS_PAUSED=true`.

## Cambio Autorizado Del Repositorio

El deadlock SHA-bound se resuelve atando este registro al base SHA anterior a la
remediacion documental, no al SHA final que contiene este mismo archivo. El gate
de apply debe validar que el `candidate_sha` sea descendiente de
`1885806f0d9f189600d410d353fcf13fb8dd4676` y que el diff desde ese base contenga
solo las rutas de gobierno F10.8 allowlisted. El digest no-auth cubre contenido de
blobs Git normalizados, status y modo de todas esas rutas excepto este propio
registro DDL.

Rutas permitidas desde el base autorizado:

- `.context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md`
- `.context/estado_del_proyecto.md`
- `.context/evidencias_cliente/sprint_1/paquete_hito_001.md`
- `.context/hitos/hito_001.md`
- `.context/operaciones/ddl_authorizations/DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO.md`
- `.context/operaciones/flujo_release_minimo.md`
- `.context/operaciones/plan_cierre_hito1_ca1_only.md`
- `.github/workflows/db-sync-to-pro.yml`
- `.github/workflows/security-audit.yml`
- `tests/test_fase10_8_db_sync.py`
- `tests/test_fase10_main_boundary.py`

## Exclusiones

Este registro no autoriza Production Canary, schedules, writers, backfill,
secrets/environments, Cloudflare, Edge, CA2 ni cambios en `db/**`, `supabase/**`,
`web/**`, `scripts/core/**` o `scripts/maintenance/**`.

## Evidencia Sanitizada

- PR #320 quedo mergeado en `main@1885806f0d9f189600d410d353fcf13fb8dd4676`.
- DB Sync to Production run `31243797695=SUCCESS_REPORT_ONLY` fue report-only.
- El report-only observo exactamente una migracion pendiente en Pro:
  `20260808_fase10_8_atomic_cleansing_provenance`.
- `Apply pending migrations`, `Verify target schema` y FG2 deferred quedaron
  skipped; no aplico DDL y no hubo DML Pro.
- PR #321 quedo mergeado en `main@49c5b6c490982b4572ec39f577bf9468b0bfd136`.
- DB Sync to Production run `31246525845=SUCCESS_REPORT_ONLY` observo solo la
  migracion autorizada pendiente.
- DB Sync to Production run `31258101516=FAIL_CLOSED_NON_AUTH_DIGEST` fallo antes
  de aplicar porque el digest anterior fue calculado sobre CRLF del working tree
  Windows; `Apply pending migrations`, `Verify target schema` y Production Canary
  quedaron skipped.
- Backup fisico programado restaurable `2026-08-08T05:54:02Z` verificado sin
  ejecutar restore; PITR no habilitado por compute Micro; RPO aceptado para cambios
  posteriores al timestamp del backup con writers y FG1/FG2/FG3 pausados antes de
  cualquier apply futuro.
- `EVID-H1-010..013/016` permanecen pendientes.
