# R0 Post-Merge Evidence - F10.9

| Campo | Valor |
|---|---|
| Gate | [G0-R0-F10.9](./g0_r0_reconciliacion_f10_9.md) |
| Estado | `PROTECTED_RECONCILIATION_PASS_P1_WIRING_IN_PROGRESS` |
| Autoriza G0 PASS | `NO` |
| Autoriza P1 runtime | `NO` |
| Autoriza data plane | `NO` |

## Protected Heads

| Ref | Commit | Tree |
|---|---|---|
| `main` | `ad89e8ab9575b37476502d6062e22c044ad6447b` | `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| `certificacion` | `4f16f314284324c3b5e9c11c4536eef5ee04c7f3` | `cad3f1061cbdc00b2883f7812602a4f80bda0853` |
| `desarrollo` | `4dcbb3fd792c25b16627f663fde31e40229718ce` | `cad3f1061cbdc00b2883f7812602a4f80bda0853` |

`main` es ancestro de `certificacion`; `certificacion` es ancestro de
`desarrollo`. Los trees protegidos de `certificacion` y `desarrollo` son
identicos.

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
replacement = NOT_CREATED
close_authorized = NO
```

PR #330 no se fusiona, rebasa ni force-pushea. Solo puede consultarse como
referencia semantica. Se cierra como `SUPERSEDED_NON_PROMOTABLE` despues de
abrir el reemplazo P1 desde el tip protegido post-wiring.

## P1 Boundary Wiring

El package `ci/f10-9-p1-boundary` habilita el boundary fail-closed previo a P1.
No modifica los cinco paths runtime P1 y requiere aprobacion/merge humano antes
de crear `fix/f10-9-p1-rebuilt`.

G0 permanece abierto hasta integrar P1, verificar checks post-merge y registrar
`R0-P1`. Este documento no autoriza P2, DDL/DML, Supabase, schedules,
dispatches, backfill, re-enrichment ni data plane.
