# G1/P2 Post-Merge Evidence - F10.9

| Campo | Valor |
|---|---|
| Gate | `G1/P2` planners offline |
| Estado | `G1_PASS_GO_G2_AUTHORIZATION_REQUIRED` |
| PR | `#335` |
| Autoriza G2/P3-P4 | `NO` |
| Autoriza data plane | `NO` |

## Candidate Protegido

```text
baseline = 2ad4e28ef261cb6c9ad013fe270cd7c48a52d8e0
candidate = b7ac753873e712cd35b937dd9ed1cf66015a776a
candidate_parent = 2ad4e28ef261cb6c9ad013fe270cd7c48a52d8e0
candidate_tree = 9c04cd75d47654fd8cfb3058b65e8846afd3c5e5
merge_commit = 0d87060837586603055ca91629b20815803b3239
merge_parents = 2ad4e28ef261cb6c9ad013fe270cd7c48a52d8e0,b7ac753873e712cd35b937dd9ed1cf66015a776a
merge_tree = 9c04cd75d47654fd8cfb3058b65e8846afd3c5e5
approval_after_last_push = true
```

El diff candidate contiene exactamente cuatro altas `100644`:

```text
A scripts/maintenance/f10_9_readonly_audit.py
A scripts/shared/f10_9_readonly_planner.py
A tests/fixtures/f10_9_p2_synthetic.json
A tests/test_fase10_9_p2_readonly_planners.py
```

No incluye workflows, DB, SQL, migrations, providers, schedules, runtime remoto
ni modo apply.

## Validacion Del Candidate

```text
focused_p2 = 38/38 PASS
focused_p2_without_environment = 38/38 PASS
p1_regression = 36/36 PASS
f10_9_boundary = 42/42 PASS
main_boundary = 6/6 PASS
py_compile = PASS
credential_scan = PASS
security_auditor = GO_TO_COMMIT
qa = GO_TO_COMMIT
delta_manifest_sha256 = df1aad972bb0bd2b091a445632c9fb1367c425d4204e63869fef01a321fef154
validator_file_sha256 = 989cd6f552f826aab0b962cbff6bb5948da3fc2045761eade441611b0ffcf265
```

El validador externo calculo `delta_manifest_sha256` sobre el UTF-8 del manifest
canonico ordenado `status<TAB>mode<TAB>path<TAB>blob`, unido por LF. El
`validator_file_sha256` corresponde a los bytes del propio script validador. El
resultado preservado registra ambos valores junto con base, tree, paths y tests.

El fixture sintetico termina deliberadamente en `STOP_REQUIRES_REBASELINE`.
Ese resultado prueba el fail-closed del planner y no diagnostica Production. El
manifest conserva `next_gate_eligible=false`, cero writes y capacidades DB,
HTTP, providers y apply desactivadas.

## CI Y Post-Merge

PR #335 fue aprobado sobre el candidate exacto y fusionado mediante merge commit
en `desarrollo` el `2026-08-10`.

```text
pr_security_audit_run = 31361405257:success
pr_f9_7_contract_run = 31361405329:success
post_merge_security_audit_run = 31361988478:success
post_merge_f9_7_contract_run = 31361988498:success
```

## Decision G1

Los planners P2 quedaron integrados, reproducibles, read-only, offline y sin
modo apply. Los criterios de salida G1 estan satisfechos:

```text
G1 = PASS
next_gate = GO_G2_AUTHORIZATION_REQUIRED
P3_P4 = NOT_STARTED_REQUIRES_SEPARATE_AUTHORIZATION
data_plane = NOT_AUTHORIZED
```

Este registro no autoriza implementar P3/P4, ejecutar workers, acceder a
Supabase o Production, emitir llamadas de proveedor, aplicar DDL/DML, ejecutar
backfill/re-enrichment, habilitar schedules ni promover a Certification/Main.
