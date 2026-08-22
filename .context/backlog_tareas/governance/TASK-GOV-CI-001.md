# TASK-GOV-CI-001 - Desacoplar Security Audit Del Gate Nativo De Review

## Estado

`PROPOSED_R2_PENDING_DIGEST_APPROVAL`

## Identidad

| Campo | Valor |
|---|---|
| TASK | `TASK-GOV-CI-001` |
| WP | `WP-GOV-CI-001` |
| phase_trace | `F10.11` |
| risk_level | `GOVERNANCE_CI_REVIEW_GATE_DECOUPLING` |
| target_level | `R2` |

## Objetivo

Preparar un candidate local que elimine la necesidad de rerun manual del workflow `security-audit` cuando una review humana se emite despues del primer run del PR hacia `desarrollo`.

## Alcance

- `security-audit` valida attestation tecnica, manifest, digest, `Base-SHA`, `Candidate-SHA`, paths y co-change.
- GitHub branch protection queda como unica autoridad mecanica de review humana.
- Las reviews no disparan la suite completa ni son consultadas por el preflight.
- `certificacion`, `main`, DB, Supabase, writers, schedules, deploys y cualquier R3 siguen fuera de alcance.

## Baseline

| Rama | Commit | Tree |
|---|---|---|
| `desarrollo` | `fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1` | `5e7d087ac45457264ea29dfc1aa7373efd909290` |
| `certificacion` | `fe7b27abf18c096f674948b4f30f815aea4aef08` | `fcb59095e48441bb4486ccc196aee61e2e1e0fe3` |
| `main` | `9b486146962bd2a092acfd649fdcf716e922de89` | `fcb59095e48441bb4486ccc196aee61e2e1e0fe3` |

PR #426 queda registrado como `MERGED_TO_DESARROLLO@fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1` con tree `5e7d087ac45457264ea29dfc1aa7373efd909290`.

## Criterios De Salida

- Workflow sin trigger `pull_request_review`.
- Governance Preflight corre solo en `pull_request` hacia `desarrollo`.
- Preflight no usa `GITHUB_TOKEN`, flag de review ni Reviews API.
- Attestation requiere `Candidate-SHA` y lo compara contra el PR head SHA real.
- Agregador exige preflight `success` solo para `pull_request:desarrollo` y `skipped` para `certificacion`, `main` y `push`.
- Branch protection mantiene review humana obligatoria con `security-audit` como unico required status check.
- H2-CA2/H2-CA3 permanecen `NOT_STARTED` y H3-H5 `PLANNED_NOT_ACTIVE`.

## Prohibiciones

- No modificar `WP-GOV-ARCH-001.json` ni `WP-GOV-HOM-001.json`.
- No push, PR, merge, branch protection write, R3, Certification, Main, Supabase, DDL/DML, migraciones, backfill, writers, schedules, deploys, secrets, PII ni `workflow_dispatch`.
