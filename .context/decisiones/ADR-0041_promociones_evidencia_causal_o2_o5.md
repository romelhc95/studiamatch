# ADR-0041 - Promociones Con Evidencia Causal O2-O5

## Estado

Aceptada localmente como candidate CI12.

## Contexto

PR #445 fallo sin merge durante HOM-011 O2. HOM-011 dependia de un secret mutable post-merge y de observabilidad incompleta del collector inline. Eso permitia confundir campos no observables con listas vacias y no demostraba offline la cadena O2-O5 completa.

## Decision

Las promociones futuras usan HOM-012. `promotion-jit-envelope-v2` liga la aprobacion humana a PR, run `pull_request/opened`, `run_attempt=1`, refs, SHAs, trees, WP, digest, identidades, side effects, Environment `Promotion` y digest del ruleset owner-only observado.

La aprobacion del Environment `Promotion` ocurre una sola vez antes del merge. El job pre-merge genera `promotion-approval-evidence.json`; el post-merge consume esa evidencia inmutable y no vuelve a leer `R3_JIT_APPROVAL_ENVELOPE` ni solicita Environment.

El collector GitHub REST vive en `scripts/security/github_promotion_snapshot.py`. `bypass_actors` ausente es `UNOBSERVABLE` y falla cerrado. Los reviewers se obtienen desde `protection_rules[type=required_reviewers].reviewers`; `prevent_self_review=true`, `can_admins_bypass=false` y `deployment_branch_policy=null` son obligatorios.

O3 se cierra de forma asincronica: Cloudflare Pages debe terminar success con app_id `85455` sobre el merge SHA exacto y DB Sync Detect Only debe producir artifact `NO_DB_CHANGES`, `db_changed=false`, `apply_executed=false`. Report/apply/verify, DDL/DML, Supabase y credenciales Production quedan prohibidos en ruta no-change.

O4 consume `o3-closure-evidence.json` mediante el loader real; O5 demuestra `tree(main) == tree(certificacion) == tree(desarrollo)` y ancestry final.

## Consecuencias

- PR #443 y PR #445 quedan congelados.
- HOM-011 queda superseded; no se reutilizan grants, ramas, runs ni secrets.
- HOM-012 O2-O5 requieren R3 JIT separados y single-use.
- R1 solo prepara codigo, documentos y pruebas offline; no autoriza operaciones remotas.
