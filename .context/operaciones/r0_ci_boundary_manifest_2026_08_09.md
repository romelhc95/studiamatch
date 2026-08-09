# R0-CI-BOUNDARY-F10.9-2026-08-09

| Campo | Valor |
|---|---|
| Gate | `G0-R0-F10.9` |
| Freeze | `R0-FREEZE-F10.9-2026-08-09` |
| Estado | `CANDIDATE_LOCAL_VALIDATION_PENDING_COMMIT` |
| Autoriza merge | `NO` |

## Anchors

```text
cert_base = 2a70dd001d8ded34d5ba67c19221f7f5e291d2c8
main_source = ad89e8ab9575b37476502d6062e22c044ad6447b
main_source_tree = 54098b3ff581cc7728979afc8e6d47c9535141b5
cert_anchor = f8695f2463f5f8bf2d887bdd344f7f102afc13cd
dev_base = 8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc
dev_archive_tree = 13d3926f21b65abc73d1e8ef6e4305b2d61e0c77
dev_extraction = 2c83cde5bc6e04f01c595a629e5694bd6de3e286
```

## Boundary Surfaces

```text
.github/workflows/security-audit.yml
.github/workflows/f9-7-contract.yml
scripts/security/f109_boundary.py
tests/test_fase10_9_branch_reconciliation.py
tests/test_fase10_main_boundary.py
```

El validador candidate aplica allowlists exactas para
`F109_CERT_RECONCILIATION`, `F109_DEV_RECONCILIATION` y `F109_P1`. El modo
certificacion exige ademas Context Graph `41 files / 340 links / 0 broken`.
Los modes quedan congelados por path: `security-audit.yml=100755`; todos los
demas paths del delta R0=`100644`.
El modo P1 queda dormido hasta congelar el SHA post-#328; no se activa por nombre
de rama ni por un baseline pendiente.

## Independent Validator

```text
path = local temp outside repository
sha256 = 412aefd14e64a8f27473127a3e80a2679548c8317665b44de95addf1bdd30919
result = FROZEN_COMPILE_PASS_EXECUTION_PENDING_COMMIT
```

El validator independiente no puede ser reemplazado por el PR ni ejecutarse
desde una copia del candidate.
Los freezes previos `da55638a...` y `68c981d7...` fueron invalidados antes del
primer push al ampliar actions pinneadas y modes por path; no son evidencia
utilizable.

## Candidate

```text
head_sha = DERIVED_EXTERNAL_AFTER_COMMIT
head_tree = DERIVED_EXTERNAL_AFTER_COMMIT
delta_manifest_digest = DERIVED_EXTERNAL_AFTER_COMMIT
required_checks = PENDING_REMOTE
human_review_after_last_push = PENDING
```

Este manifest se actualiza antes del primer push con SHA/tree/digests reales.
No autoriza #328, #330, merge ni data plane.
