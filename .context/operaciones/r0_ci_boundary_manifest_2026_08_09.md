# R0-CI-BOUNDARY-F10.9-2026-08-09

| Campo | Valor |
|---|---|
| Gate | `G0-R0-F10.9` |
| Freeze | `R0-FREEZE-F10.9-2026-08-09` |
| Estado | `G0_PASS_P2_WIRING_COMPLETED_G1_AUTHORIZED` |
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
cert_merge = 4f16f314284324c3b5e9c11c4536eef5ee04c7f3
post_r0_dev_base = 4dcbb3fd792c25b16627f663fde31e40229718ce
post_r0_dev_tree = cad3f1061cbdc00b2883f7812602a4f80bda0853
post_p1_dev_base = 53921e3ec845f4a248e586a0ecd667c64f4c070d
post_p1_dev_tree = 0344c649772aea18314fe022d5f24898e3dc03d0
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
El wiring activa P1 solo para `fix/f10-9-p1-rebuilt` desde el tip protegido
vigente de `desarrollo`, o para su push merge protegido cuando el delta coincide
exactamente con cinco paths. El PR de wiring usa baseline literal post-R0 y
allowlist propia de doce paths. Todo PR y push de `desarrollo` ejecuta F10.9:
cualquier interseccion parcial, expandida, renombrada o con mode drift sobre P1
falla; solo un delta sin paths P1 emite `skip_non_p1`, conserva activo el
boundary legacy y no se convierte en autorizacion P1.

```text
M AGENTS.md
M .context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md
M .context/estado_del_proyecto.md
M .context/operaciones/g0_r0_reconciliacion_f10_9.md
M .context/operaciones/plan_remediacion_f10_9_fg2_fg3.md
M .context/operaciones/r0_ci_boundary_manifest_2026_08_09.md
A .context/operaciones/r0_post_merge_evidence_2026_08_09.md
M .github/workflows/f9-7-contract.yml
M .github/workflows/security-audit.yml
M scripts/security/f109_boundary.py
M tests/test_fase10_9_branch_reconciliation.py
M tests/test_fase10_main_boundary.py
```

## P2 Wiring Boundary

El candidate `ci/f10-9-p2-boundary` parte exactamente de `post_p1_dev_base` y
debe ser un unico commit directo, same-repository, con modes exactos. Su delta
contiene exclusivamente diez paths existentes:

```text
M .context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md
M .context/estado_del_proyecto.md
M .context/operaciones/g0_r0_reconciliacion_f10_9.md
M .context/operaciones/plan_remediacion_f10_9_fg2_fg3.md
M .context/operaciones/r0_ci_boundary_manifest_2026_08_09.md
M .context/operaciones/r0_post_merge_evidence_2026_08_09.md
M .github/workflows/f9-7-contract.yml
M .github/workflows/security-audit.yml
M scripts/security/f109_boundary.py
M tests/test_fase10_9_branch_reconciliation.py
```

El wiring reconoce P2 funcional solo en
`feat/f10-9-p2-readonly-planners`, desde el tip protegido post-wiring y con
exactamente cuatro altas mode `100644`:

```text
A scripts/shared/f10_9_readonly_planner.py
A scripts/maintenance/f10_9_readonly_audit.py
A tests/fixtures/f10_9_p2_synthetic.json
A tests/test_fase10_9_p2_readonly_planners.py
```

Intersecciones parciales, deltas expandidos, otro branch, otro baseline, forks,
renames, deletes o mode drift fallan. El wiring no implementa P2.

## Independent Validator

```text
path = local temp outside repository
sha256 = 733da0452549c05a2983d15112eb13dd59240ebe01beaf35874218f060a1e9a2
result = PASS_FINAL_STAGED_INDEX
```

El validator independiente no puede ser reemplazado por el PR ni ejecutarse
desde una copia del candidate.
Los freezes previos `da55638a...` y `68c981d7...` fueron invalidados antes del
primer push al ampliar actions pinneadas y modes por path; no son evidencia
utilizable. Este bloque corresponde al package P1 ya integrado; el validator
independiente P2 wiring se congela despues del stage final de sus diez paths.

## P1 Integrado

```text
candidate_sha = e9fb19a217cf1ad3bd9924afb0d3bdbebed7a694
merge_sha = 53921e3ec845f4a248e586a0ecd667c64f4c070d
merge_tree = 0344c649772aea18314fe022d5f24898e3dc03d0
security_audit = 31350585499:success
f9_7_contract = 31350585516:success
human_review_after_last_push = true
```

## Candidate P2 Wiring

```text
head_sha = c9dd940c8beb74b48979a86b6a91f5bdc1225cbc
head_tree = 24a270f314b46728d5ae9847dafba0ff1999be7f
delta_manifest_digest = 0ac5438fc4a7b5ee15c7e9a02f3671b164c7aacc8a74d3b9e0e8dda82d5fdbde
merge_sha = d5433ea9f810b0338513665bb95ba28715c6c8b5
merge_tree = 24a270f314b46728d5ae9847dafba0ff1999be7f
security_audit = 31354339105:success
f9_7_contract = 31354339122:success
human_review_after_last_push = true
independent_validator_sha256 = 1c7a767e37ccd4d549dbe6face36baff160e23dd314a5c0fdab50e8f81015919
independent_validator_result = PASS
```

El output sanitizado externo conserva tree y digest reales del indice final; el
head SHA se deriva despues del commit. No se incrustan esos valores en el mismo
tree porque producirian una referencia criptografica autorreferente. Este
manifest registra el wiring ya integrado. La autorizacion posterior de P2 se
limita a codigo/tests locales read-only/offline y no concede data plane.
