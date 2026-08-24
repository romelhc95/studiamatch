# TASK-GOV-CI-012 - Evidencia Causal Promociones O2-O5

## Estado

`CANDIDATE_R1_LOCAL`

## Objetivo

Reemplazar HOM-011 por HOM-012 antes de abrir un nuevo PR, corrigiendo integralmente promociones O2-O5 con evidencia causal offline y cierre asincronico O3.

## Alcance

- Congelar PR #443 y PR #445 como `FAILED_NOT_MERGED_FROZEN`, sin editarlos, cerrarlos, reabrirlos, rerunearlos ni mergearlos.
- Registrar `R3-GOV-HOM-011-O2-REQ1=CONSUMED_BY_FAILURE` y HOM-011 O3-O5 como `SUPERSEDED_NOT_USABLE`.
- Extraer el collector GitHub REST a Python testeable en `github_promotion_snapshot.py`.
- Requerir `promotion-jit-envelope-v2` ligado a PR, run opened attempt 1, refs, SHAs, trees, WP, digest, identidades, Environment y ruleset digest.
- Usar una sola aprobacion del Environment `Promotion`, antes del merge.
- Convertir la aprobacion en evidencia inmutable pre-merge y eliminar dependencia post-merge del secret.
- Separar el cierre estructural O3 del cierre asincronico Cloudflare Pages app_id `85455` y DB Sync Detect Only `NO_DB_CHANGES`.
- Hacer que O4 consuma evidencia O3 producida por el loader real.
- Exigir cierre O5 con igualdad final de trees y ancestry.

## Fuera De Alcance R1

- Push, PR, merge, fetch, pull, ramas remotas, Certification, Main, workflow_dispatch, cambios remotos de environments, secrets, variables, rulesets o branch protections.
- Supabase, DB remoto, DDL/DML, migraciones, backfill, writers, schedules, Cloudflare remoto, deploys, produccion, lead capture y egress.

## Salida Esperada

- `WP-GOV-CI-012` congelado localmente con digest calculado, pendiente de aprobacion R2 separada por commit/tree/digest.
- Tests offline para collector, envelope v2, artifacts, replays #440/#443/#445, O3 productor/consumidor, polling con reloj falso y DAG Git O2-O5.
- Siguiente gate unico: `PREPARE_WP_GOV_CI_012_R2_APPROVAL`.
