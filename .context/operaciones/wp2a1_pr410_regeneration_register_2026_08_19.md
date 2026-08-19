# WP2A.1 PR #410 Regeneration Register - F10.9

| Campo | Valor |
|---|---|
| Subfase | `F10.9` |
| Tipo | `REPOSITORY_ONLY_STATE_REGISTER` |
| PR #411 | `MERGED_POST_MERGE_VERIFIED` |
| PR #410 | `REGENERATED_ONE_DIRECT_COMMIT_CHECKS_GREEN_NOT_APPROVED_NOT_MERGED` |
| Autoriza aprobacion o merge | `NO` |
| Autoriza WP2B | `NO` |

## Autoridad

```text
desarrollo = f9108fb40dea2d59cf0ac0409626308166da2f94
pr_411_merge = f9108fb40dea2d59cf0ac0409626308166da2f94
pr_411_merge_tree = 11e06e388fe2931cb4bbd2e404d0727f061edb0d
pr_411_merge_parents = 80674393b0c40cfa10355711170f9f5842e6c2fe,13384646dae719463472e05c62fd9047bed03576
```

PR #411 fusiono en `desarrollo` el soporte repository-only para ejecutar la suite
enfocada WP2A.1 cuando el boundary emite
`mode=wp2a1_certification_control_bootstrap`. El merge quedo verificado por
checks post-merge nuevos:

```text
security-audit = 95901859737 PASS
branch_reconciliation = 95901724205 PASS
f9_7 = 95901883449 PASS
g5 = 95901723624 PASS
m3 = 95901723652 PASS
credential_scan = 95901724192 PASS
python = 95901724265 PASS
typescript = 95901724232 PASS
eslint = 95901724163 PASS
```

## PR #410 Regenerado

```text
pr = https://github.com/romelhc95/studiamatch/pull/410
old_head_superseded = 1c998989b577da27fc4b65542ef6b05fb4c5210e
new_head = 44e406936945bd05961435943e7f062ee729291f
new_tree = ce6e5d1a227ce5242200c4e5aa2974d8c1bb76a8
parent = 4f16f314284324c3b5e9c11c4536eef5ee04c7f3
commit_count = 1
base = certificacion@4f16f314284324c3b5e9c11c4536eef5ee04c7f3
base_tree = cad3f1061cbdc00b2883f7812602a4f80bda0853
```

El candidate fue reconstruido desde `certificacion@4f16f314284324c3b5e9c11c4536eef5ee04c7f3`,
no desde el head viejo. La rama `promote/f10-9-wp2a1-certification-control-bootstrap`
fue actualizada por `force-with-lease` usando como lease exacto
`1c998989b577da27fc4b65542ef6b05fb4c5210e`.

## Envelope

```text
A 100644 86101b1834d295dfc70432246205fc058f302a8c .context/operaciones/wp2a1_certification_push_manifest_continuity_fix_2026_08_18.json
M 100755 34ebe758bfe882a2bd4a10e90d97763f990c4785 .github/workflows/security-audit.yml
M 100644 0654fc0bd199145f08f85c372fdfff6c1b77c7d3 scripts/security/f109_boundary.py
M 100644 2c211b1c12c206240b4180aebb07570ba5a69013 tests/test_fase10_9_branch_reconciliation.py
```

No hay quinto path, rename, copy, delete, symlink ni submodule. Los blobs del
candidate coinciden con `desarrollo@f9108fb40dea2d59cf0ac0409626308166da2f94`.
El blob del manifest del candidate coincide con el manifest protegido
`86101b1834d295dfc70432246205fc058f302a8c`. El validator authority queda fijado
a `desarrollo@f9108fb40dea2d59cf0ac0409626308166da2f94`.

## Checks Observados Para El Nuevo SHA

```text
security-audit = 95928431910 PASS
branch_reconciliation = 95928320662 PASS
f9_7 = 95928320445 PASS
credential_scan = 95928320707 PASS
python = 95928320776 PASS
typescript = 95928320664 PASS
eslint = 95928320702 PASS
cloudflare_pages = 95928971862 PASS
```

Las aprobaciones previas y los checks del head viejo `1c998989b577da27fc4b65542ef6b05fb4c5210e`
no se reutilizan. PR #410 queda abierto, sin aprobacion, sin merge y con
`mergeability=blocked` hasta revision humana nueva.

## Evidencia Preservada De La Regeneracion PR #410

```text
py_compile = PASS
focused_wp2a1_certification_unittest = PASS
pr_simulation = PASS mode=wp2a1_certification_control_bootstrap
protected_merge_push_simulation_without_hydration = PASS
full_f10_9_suite_on_protected_desarrollo_f9108fb = PASS Ran 266 tests OK skipped=1
negative_cases = PASS via protected suite and direct non_merge_push rejection
git_diff_check = PASS
credential_scan = PASS
pre_commit_hook = PASS
pre_push_hook = PASS
security_auditor = GO
qa = GO
```

## Validacion De Este Follow-Up Documental

```text
git_diff_check = PASS
credential_scan = PASS
validate_context_graph = NOT_RUN_UNAVAILABLE_IN_THIS_BRANCH
```

El script `scripts/maintenance/validate_context_graph.py` no existe en
`desarrollo@f9108fb40dea2d59cf0ac0409626308166da2f94`; por eso no se ejecuto
validacion estructural adicional del Context Graph en este follow-up.

## Limites

WP2B permanece fail-closed y fuera de PR #410. Este registro no ejecuta ni
autoriza approval, merge, branch protection, required checks, `main`, Actions
API, Cloudflare API, GitHub App, Supabase, SQL, Production, writers, schedules,
workflow dispatch, OIDC live ni cambios remotos adicionales.
