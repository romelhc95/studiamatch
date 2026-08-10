# R0 Post-Merge Evidence - F10.9

| Campo | Valor |
|---|---|
| Gate | [G0-R0-F10.9](./g0_r0_reconciliacion_f10_9.md) |
| Estado | `G0_PASS_GO_G1_P2` |
| Autoriza G0 PASS | `YES_RECORDED` |
| Autoriza P2 runtime | `NO` |
| Autoriza data plane | `NO` |

## Protected Heads

| Ref | Commit | Tree |
|---|---|---|
| `main` | `ad89e8ab9575b37476502d6062e22c044ad6447b` | `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| `certificacion` | `4f16f314284324c3b5e9c11c4536eef5ee04c7f3` | `cad3f1061cbdc00b2883f7812602a4f80bda0853` |
| `desarrollo` | `d5433ea9f810b0338513665bb95ba28715c6c8b5` | `24a270f314b46728d5ae9847dafba0ff1999be7f` |

`main` es ancestro de `certificacion`; `certificacion` es ancestro de
`desarrollo`. La igualdad de trees de `certificacion` y `desarrollo` fue
verificada al cerrar R0; los cambios posteriores corresponden exclusivamente al
wiring P1, P1 integrado y wiring P2 protegido.

## PR 329 - Certificacion

```text
approved_head = 809afbdb7ba875db1feef0b8688bbb0cd40e0724
merge_commit = 4f16f314284324c3b5e9c11c4536eef5ee04c7f3
merge_parents = 2a70dd001d8ded34d5ba67c19221f7f5e291d2c8,809afbdb7ba875db1feef0b8688bbb0cd40e0724
merge_tree = cad3f1061cbdc00b2883f7812602a4f80bda0853
approval_after_last_push = true
security_audit_run = 31340356606:success
certification_canary_run = 31340356597:success
```

## PR 328 - Desarrollo

```text
approved_head = c287e5b17e555aefe606e710a20e1ee73a5ca0dd
merge_commit = 4dcbb3fd792c25b16627f663fde31e40229718ce
merge_parents = 8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc,c287e5b17e555aefe606e710a20e1ee73a5ca0dd
merge_tree = cad3f1061cbdc00b2883f7812602a4f80bda0853
approval_after_last_push = true
security_audit_run = 31342154494:success
f9_7_contract_run = 31342154499:success
```

## CA2 Archive

```text
ref = archive/f10-9-ca2-preserve-desarrollo-20260809
commit = 8f4b4b0cbd8fd8ed096a34d8fa826f39ba6ec3fc
tree = 13d3926f21b65abc73d1e8ef6e4305b2d61e0c77
status = PRESERVED_FOR_HITO_2
```

## PR 330

```text
head = 8333102c44ea3278a05c3dad82763d55706b7e4f
tree = fab0ca1bbad12fd633b7574a44ab0a52ea00a1ac
status = REFERENCE_ONLY_NON_PROMOTABLE
replacement = PR_332
status_final = CLOSED_SUPERSEDED_NON_PROMOTABLE
```

PR #330 no fue fusionado, rebasado ni force-pusheado. Queda solo como referencia
semantica; fue cerrado como `SUPERSEDED_NON_PROMOTABLE` despues de abrir #332.

## PR 331 - P1 Boundary Wiring

```text
merge_commit = 4f47836a8c80bbab396e30ed65f424e58e772987
approval_after_last_push = true
post_merge_checks = success
```

El package habilito el boundary fail-closed previo a P1 sin modificar sus cinco
paths runtime.

## PR 332 - P1 Integrado

```text
candidate = e9fb19a217cf1ad3bd9924afb0d3bdbebed7a694
merge_commit = 53921e3ec845f4a248e586a0ecd667c64f4c070d
merge_tree = 0344c649772aea18314fe022d5f24898e3dc03d0
approval_after_last_push = true
security_audit_run = 31350585499:success
f9_7_contract_run = 31350585516:success
p1_diff_paths = exact_five_path_allowlist
```

P1 paso 36 pruebas focused, 121 regresiones relacionadas, credential scan y
security-auditor sin blockers. El ancestry de #330 no fue reutilizado.

## Decision G0

Todos los predicados de salida G0 quedaron satisfechos. Resultado:
`G0=PASS/GO_G1_P2`. La siguiente actividad es integrar el wiring fail-closed P2;
P2 funcional permanece `NOT_STARTED_REQUIRES_SEPARATE_AUTHORIZATION`.

Este documento no autoriza P2, DDL/DML, Supabase, schedules, dispatches,
backfill, re-enrichment ni data plane.

## PR 333 - P2 Boundary Wiring

```text
candidate = c9dd940c8beb74b48979a86b6a91f5bdc1225cbc
merge_commit = d5433ea9f810b0338513665bb95ba28715c6c8b5
merge_tree = 24a270f314b46728d5ae9847dafba0ff1999be7f
approval_after_last_push = true
security_audit_run = 31354339105:success
f9_7_contract_run = 31354339122:success
p2_wiring_diff_paths = exact_ten_path_allowlist
```

El wiring P2 quedo protegido y verificado post-merge. La autorizacion posterior
de G1/P2 se limita a cuatro altas locales read-only/offline; no habilita red,
data plane ni apply.
