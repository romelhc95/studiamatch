# TASK-GOV-CI-006 - Promociones target-aware y retiro de gates legacy

## Estado

`CANDIDATE_R1_LOCAL`

## Contexto

PR #434 publico CI5 en `desarrollo`, pero PR #435 fallo O2 antes de mergear porque el contrato legacy F9.7 se ejecuto sobre una promocion moderna. El grant `R3-GOV-HOM-005-O2-REQ1` quedo consumido por fallo y no se debe reintentar.

## Problema

Las promociones directas entre ramas protegidas no son compatibles con `strict=true` cuando `desarrollo`, `certificacion` y `main` tienen historia divergente. Ademas, los gates legacy congelados no deben dispararse en PRs de homologacion moderna.

## Alcance R1

- Convertir `.github/workflows/f9-7-contract.yml` a `workflow_dispatch` manual frozen-only.
- Introducir validacion target-aware para ramas `promote/gov-hom-006-oN`.
- Exigir attestation con `Base-Ref`, `Source-Ref`, `Source-SHA` y `Candidate-Tree`.
- Crear `WP-GOV-CI-006`, `ADR-0035` y solicitudes HOM-006 O2-O5.
- Reconciliar tests y documentos vivos para el nuevo cierre no recursivo.

## Fuera De Alcance

- Push, PR, merge o promocion remota.
- Cerrar, editar o reintentar PR #435.
- O2/O3/O4/O5, Main, Certification, Supabase, DB, DDL/DML, backfill, RLS/grants, writers, schedules, deploys, workflow_dispatch, secretos o H2-H5.

## Criterios De Salida

- `WP-GOV-CI-006` valida por digest.
- F9.7 queda sin triggers automaticos `pull_request`/`push`.
- Promotions HOM-006 validan branch target-aware y padres exactos.
- O3 queda documentado como R3 con rebuild Production automatico, DB sync detect-only y resultado `NO_DB_CHANGES` obligatorio.
- Tests de gobierno pasan en Docker.
- `security-auditor` no reporta hallazgos bloqueantes.
