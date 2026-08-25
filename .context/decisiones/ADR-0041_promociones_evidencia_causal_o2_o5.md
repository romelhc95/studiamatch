# ADR-0041 - Promociones Con Evidencia Causal O2-O5

## Estado

Aceptada localmente como candidate CI12; REQ5 en remediacion local con contrato V3 congelado.

## Contexto

PR #445 fallo sin merge durante HOM-011 O2. HOM-011 dependia de un secret mutable post-merge y de observabilidad incompleta del collector inline. Eso permitia confundir campos no observables con listas vacias y no demostraba offline la cadena O2-O5 completa.

Durante REQ4, el contrato V1 de readiness quedo rechazado antes de implementacion por asumir un timestamp de approval no expuesto por el endpoint REST. El contrato V2 queda preservado sin editar como `FROZEN_SUPERSEDED_CONTRACT_DIGEST_NONREPRODUCIBLE`. El contrato local vigente es `GOV-CI12-R2-READINESS-V3`, digest detached `7f4d14665039e05d1cb952f5f51aa6111f70d52188bf6762b2964961e451ca14`.

## Decision

Las promociones futuras usan HOM-012. `promotion-jit-envelope-v3` liga la aprobacion humana a PR, run `pull_request/opened`, `run_attempt=1`, refs, SHAs, trees, WP, digest, identidades, side effects, Environment `Promotion` y digest del ruleset owner-only observado.

La aprobacion del Environment `Promotion` ocurre una sola vez antes del merge. El job pre-merge genera `promotion-approval-evidence.json`; el post-merge consume esa evidencia inmutable y no vuelve a leer `R3_JIT_APPROVAL_ENVELOPE` ni solicita Environment.

La causalidad V3 no depende de inventar un timestamp de approval. Se prueba por identidad del run `pull_request/opened`, intento 1, job `Promotion Boundary` con Environment `Promotion`, artifact producido en ese mismo job y bindings de endpoints approvals/run/jobs al mismo `run_id`.

La evidencia no inventa campos no observables. El historial REST de approvals se procesa desde `environments[]`, `user`, `state` y `comment`; `environment.created_at` es metadata del Environment y no decision time. `approval_id` dentro del envelope es solo referencia humana/JIT. El comentario libre no se persiste: se conserva solo `comment_present` y, si aplica, `comment_sha256`.

El collector GitHub REST vive en `scripts/security/github_promotion_snapshot.py`. `bypass_actors` ausente es `UNOBSERVABLE` y falla cerrado. Los reviewers se obtienen desde `protection_rules[type=required_reviewers].reviewers`; `prevent_self_review=true`, `can_admins_bypass=false` y `deployment_branch_policy=null` son obligatorios.

O3 se cierra de forma asincronica: Cloudflare Pages debe terminar success con app_id `85455` sobre el merge SHA exacto y DB Sync Detect Only debe producir artifact `NO_DB_CHANGES`, `db_changed=false`, `apply_executed=false`. Report/apply/verify, DDL/DML, Supabase y credenciales Production quedan prohibidos en ruta no-change.

O4 consume `o3-closure-evidence.json` mediante el loader real; O5 demuestra `tree(main) == tree(certificacion) == tree(desarrollo)` y ancestry final.

## Consecuencias

- PR #443 y PR #445 quedan congelados.
- HOM-011 queda superseded; no se reutilizan grants, ramas, runs ni secrets.
- HOM-012 O2-O5 requieren R3 JIT separados y single-use.
- R1 solo prepara codigo, documentos y pruebas offline; no autoriza operaciones remotas.
- Candidate `1034193d48f820bcc37f8c03aa57aca777a037ba` queda superseded localmente por mismatch del contrato REST de approvals antes de solicitar R2.
- Los GET historicos V2 usados para congelar el contrato ya fueron consumidos y no deben repetirse sin autorizacion nueva.
