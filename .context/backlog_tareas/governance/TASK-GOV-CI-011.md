# TASK-GOV-CI-011 - Promotion Envelope And O3 Closure

## Estado

`CANDIDATE_R1_LOCAL`

## Objetivo

Remediar durablemente el fallo no mergeado de PR #443 y reemplazar HOM-010 por HOM-011 con aprobacion transaccional ligada al run `opened` valido.

## Alcance

- Congelar PR #443 como `FAILED_NOT_MERGED`, sin editarlo, cerrarlo, reabrirlo, rerunearlo ni mergearlo.
- Marcar `R3-GOV-HOM-010-O2-REQ1` como consumido y HOM-010 O3-O5 como superseded.
- Requerir `R3_JIT_APPROVAL_ENVELOPE` con schema `promotion-jit-envelope-v1` para HOM-011.
- Ligar el envelope a PR, run `opened`, `run_attempt=1`, refs, SHAs, tree, WP, digest, identidades, side effects y expiry.
- Evitar cancelacion del run `opened` valido en promociones.
- Invalidar `edited`, `reopened`, `synchronize`, `ready_for_review` y rerun.
- Crear readiness preflight local/remoto read-only.
- Endurecer el contrato deseado de `Promotion` con `can_admins_bypass=false`.
- Preparar HOM-011 O2-O5 sin consumir R3.
- Cerrar O3 solo con Cloudflare Pages app_id `85455` y `DB Sync Detect Only=NO_DB_CHANGES`.
- Bloquear O4 hasta cierre O3.

## Fuera De Alcance R1

- Push, PR, merge, Certification, Main, O2/O3/O4/O5, workflow_dispatch, cambios remotos de environments, secrets, variables, rulesets o branch protections.
- Supabase, DB remoto, DDL/DML, migraciones, backfill, writers, schedules, Cloudflare remoto, deploys, produccion y Hito 2 funcional.

## Salida Esperada

- `WP-GOV-CI-011` congelado localmente con digest calculado `1b14d76273ef82a4889cdee8edea46815a88efaf66a8a16a180241f4b6e8cc88`, pendiente de aprobacion R2 separada por commit/tree/digest.
- Tests positivos/negativos de envelope, eventos, drift, expiry, identidades, O3 Cloudflare/DB Sync y O4 bloqueado.
- Siguiente gate unico: `PREPARE_WP_GOV_CI_011_R2_APPROVAL`.
