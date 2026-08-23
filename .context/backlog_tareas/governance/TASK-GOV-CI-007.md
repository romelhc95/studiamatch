# TASK-GOV-CI-007 - Evidencia post-merge fail-closed y HOM-007

## Estado

`CANDIDATE_R1_LOCAL`

## Contexto

PR #436 publico CI6 en `desarrollo`, pero PR #437 fue mergeado a `certificacion` y fallo en el push post-merge run `32650341464` con `POST_MERGE_REQUIRED_CHECK_MISSING`. La causa primaria fue que los check-runs de GitHub Actions sobre commits sinteticos pueden exponer `pull_requests: []`. La causa secundaria detectada fue identidad invalida: `merged_by=romelhc95-approver`, cuando el contrato exige merge por `romelhc95` y approval por `romelhc95-approver`.

## Problema

El boundary post-merge de CI5/CI6 permitia fallback incremental cuando faltaba evidencia y no distinguia inequívocamente entre push ordinario, promocion verificada y promocion invalida. Tambien faltaban retries, paginacion, freshness, workflow-run validation y review identity estricta.

## Alcance R1

- Implementar clasificacion `VERIFIED_PROMOTION`, `NOT_APPLICABLE` y `BLOCKED`.
- Permitir fallback `--changed-from` solo para `NOT_APPLICABLE`.
- Validar check-runs por nombre exacto, SHA exacto, `app.id=15368`, ultimo estado, ventana temporal, PR association y workflow run comun.
- Aceptar `pull_requests: []` solo con asociacion merge -> PR unica y validada.
- Exigir review efectiva final de `romelhc95-approver` sobre Candidate-SHA y merge por `romelhc95`.
- Reemplazar HOM-006 por HOM-007 y bloquear PR #437/HOM-006 como historia consumida o superseded.
- Crear `WP-GOV-CI-007`, `ADR-0036` y solicitudes HOM-007 O2-O5.

## Fuera De Alcance

- Push, PR, merge o promocion remota.
- Editar, reintentar o rerun de PR #437/run `32650341464`.
- O2/O3/O4/O5, Certification, Main, Supabase, DB, DDL/DML, backfill, RLS/grants, writers, schedules, deploys, workflow_dispatch, secretos o H2-H5.

## Criterios De Salida

- `WP-GOV-CI-007` valida por digest.
- Post-merge promotion invalid/ambigua queda `BLOCKED` y no ejecuta boundary incremental.
- Push ordinario queda `NOT_APPLICABLE` con exit code 2.
- Promocion valida queda `VERIFIED_PROMOTION` con exit code 0 y activa Post-Merge Promotion Approval.
- Tests de gobierno pasan en Docker.
- `security-auditor` no reporta hallazgos bloqueantes.
