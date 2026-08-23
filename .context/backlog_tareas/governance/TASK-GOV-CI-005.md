# TASK-GOV-CI-005 - Boundary estructural post-merge de promociones

## Estado

`CANDIDATE_R1_LOCAL`

## Contexto

PR #433 completo O2 `desarrollo -> certificacion` con `Promotion Boundary` y `security-audit` verdes antes del merge. El push post-merge a `certificacion@3682d0af8c16ed0476663e6727b14f03ec14ed78` fallo el job `Canonical Path Boundary` del run `32615044699` porque el workflow trato el delta historico de promocion como scope incremental.

## Problema

Las promociones O2-O5 ya tienen boundary estructural en PR, pero el evento `push` posterior al merge vuelve a usar `event.before..after` como si fuese un WP incremental. Ese delta contiene cambios ya homologados y no debe evaluarse como scope local nuevo.

## Alcance R1

- Agregar validacion fail-closed de push post-merge de promocion O2-O5.
- Exigir evidencia de PR asociado por API, merge commit de dos padres, par exacto, attestation, checks pre-merge, merger `romelhc95` y review `romelhc95-approver`.
- Mantener boundary incremental para pushes ordinarios, directos, forks, merges no asociados y evidencia incompleta.
- Crear `WP-GOV-CI-005`, `ADR-0034` y solicitudes HOM-005 O2-O5.

## Fuera De Alcance

- Rerun del run `32615044699`.
- Push, PR, merge o promocion remota.
- O2/O3/O4/O5, Main, Supabase, DB, DDL/DML, backfill, RLS/grants, writers, schedules, deploys, workflow_dispatch, secretos o H2-H5.

## Criterios De Salida

- `WP-GOV-CI-005` valida por digest.
- Push post-merge de promocion valido produce `POST_MERGE_PROMOTION_STRUCTURAL_PASS`.
- Pushes ordinarios conservan boundary incremental.
- HOM-005 existe como `REQUESTED_JIT_SINGLE_USE` sin autorreferencia.
- Tests de gobierno pasan en Docker.
- `security-auditor` no reporta hallazgos bloqueantes.
