# TASK-GOV-CI-012 - Evidencia Causal Promociones O2-O5

## Estado

`LOCAL_REMEDIATION_IN_PROGRESS`

Candidate `1034193d48f820bcc37f8c03aa57aca777a037ba` queda `NO_GO_R2_SUPERSEDED_BY_LOCAL_REMEDIATION` por `GITHUB_ENVIRONMENT_APPROVAL_API_CONTRACT_MISMATCH`.

Candidate `50a853ac4e32e60280213489d347070d79cf2580` de PR #446 queda `NO_GO_R2_CODEQL_CACHE_POISONING`: `security-audit` run `32785885240` paso, pero CodeQL check `97617739354` fallo por `security/code-scanning/19` en `.github/workflows/db-sync-to-pro.yml`, job `db-sync-detect-only`, al hacer checkout dinamico de `needs.detect-db-changes.outputs.candidate_sha` y ejecutar codigo del candidate. REQ6 corrige localmente ese patron; el R2 anterior no se reutiliza.

REQ4 congelo `GOV-CI12-R2-READINESS-V2`, pero REQ5 lo preserva como `FROZEN_SUPERSEDED_CONTRACT_DIGEST_NONREPRODUCIBLE` sin editarlo. El contrato vigente local es `GOV-CI12-R2-READINESS-V3`, digest detached `7f4d14665039e05d1cb952f5f51aa6111f70d52188bf6762b2964961e451ca14`. V1 queda preservado como `FROZEN_REJECTED_PREIMPLEMENTATION`; V3 separa observado vs derivado, no inventa timestamp de approval y ata causalidad por run/job/Environment gate. Los tres GET V2 historicos ya fueron consumidos y no deben repetirse.

## Objetivo

Reemplazar HOM-011 por HOM-012 antes de abrir un nuevo PR, corrigiendo integralmente promociones O2-O5 con evidencia causal offline y cierre asincronico O3.

## Alcance

- Congelar PR #443 y PR #445 como `FAILED_NOT_MERGED_FROZEN`, sin editarlos, cerrarlos, reabrirlos, rerunearlos ni mergearlos.
- Registrar `R3-GOV-HOM-011-O2-REQ1=CONSUMED_BY_FAILURE` y HOM-011 O3-O5 como `SUPERSEDED_NOT_USABLE`.
- Extraer el collector GitHub REST a Python testeable en `github_promotion_snapshot.py`.
- Requerir `promotion-jit-envelope-v3` ligado a PR, run opened attempt 1, refs, SHAs, trees, WP, digest, identidades, Environment y ruleset digest.
- Usar una sola aprobacion del Environment `Promotion`, antes del merge.
- Convertir la aprobacion en evidencia inmutable pre-merge y eliminar dependencia post-merge del secret.
- Procesar el contrato raw real de GitHub Environment approvals: `environments[]`, `user`, `state` y `comment`; `approval_id` queda solo como referencia humana/JIT, no como ID REST observado. `environment.created_at` es metadata del Environment y no timestamp de decision.
- Separar el cierre estructural O3 del cierre asincronico Cloudflare Pages app_id `85455` y DB Sync Detect Only `NO_DB_CHANGES`.
- Hacer que O4 consuma evidencia O3 producida por el loader real.
- Exigir cierre O5 con igualdad final de trees y ancestry.

## Fuera De Alcance R1

- Push, PR, merge, fetch, pull, ramas remotas, Certification, Main, workflow_dispatch, cambios remotos de environments, secrets, variables, rulesets o branch protections.
- Supabase, DB remoto, DDL/DML, migraciones, backfill, writers, schedules, Cloudflare remoto, deploys, produccion, lead capture y egress.

## Salida Esperada

- `WP-GOV-CI-012` congelado localmente con digest calculado, pendiente de aprobacion R2 separada por commit/tree/digest.
- Tests offline para collector, envelope v3 sanitizado, artifacts, replays #440/#443/#445, O3 productor/consumidor, polling con reloj falso y DAG Git O2-O5.
- Tests offline para normalizador raw de approvals y `approval_record_digest` derivado.
- Tests offline para `db-sync-detect-only` sin checkout ni ejecucion de codigo del candidate, preservando artifact `db-sync-detect-only-v1`.
- Siguiente gate unico: `PREPARE_WP_GOV_CI_012_R2_APPROVAL`.

## Validacion Local REQ5

- `tests/test_promotion_evidence.py`: 24 passed en Docker sin red.
- Suite governance focal `tests/test_promotion_evidence.py tests/test_promotion_readiness.py tests/test_release_workflow_matrix.py tests/test_work_package_manifest.py`: 129 passed en Docker sin red.
- REQ5 suite ampliada `tests/test_gov_ci12_r2_readiness_contract_v3.py tests/test_promotion_api_adapter.py tests/test_promotion_evidence.py tests/test_promotion_readiness.py tests/test_promotion_o2_o5_e2e.py tests/test_release_workflow_matrix.py tests/test_work_package_manifest.py tests/test_context_graph_semantics.py`: 200 passed en Docker sin red.

## Validacion Local REQ6

- Focales `tests/test_fase10_8_db_sync.py tests/test_release_workflow_matrix.py tests/test_promotion_evidence.py tests/test_work_package_manifest.py tests/test_context_graph_semantics.py`: 177 passed en Docker sin red.
- Suite governance completa: 260 passed en Docker sin red.
- Python compile, `validate_work_package.py`, `validate_context_graph.py`, Markdown links, hashes V1/V2/V3, DB gate no-change, secret scan, lint, typecheck y static build offline: PASS.
- PR #446 no fue editado, cerrado, reruneado, sincronizado ni mergeado durante REQ6 local.
