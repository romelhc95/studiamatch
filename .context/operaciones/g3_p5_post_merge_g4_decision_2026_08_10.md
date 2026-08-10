# G3/P5 Post-Merge Y Decision G4 - F10.9

| Campo | Valor |
|---|---|
| Gate tecnico | `G3/P5` |
| Resultado G3 | `PASS` |
| Gate de autoridad | `G4` |
| Resultado G4 | `STOP_REQUIRES_REBASELINE` |
| Autoriza P7/G5 | `NO` |
| Autoriza data plane o mutacion | `NO` |

## Candidate Protegido P5

```text
baseline = 092251e50e75917378ae15bae82b741c322424fa
baseline_tree = 9b49de459278587e858e720213e86debbe66ee77
candidate = 46fd10864af2a90e407f6867adf980daa940b075
candidate_parent = 092251e50e75917378ae15bae82b741c322424fa
candidate_tree = 8eb146006419d93dc0a74710ca9efaaf101ab280
merge_commit = 1c5d1526a1da247ca6ad0eb7b25cd5e0b0f51564
merge_parents = 092251e50e75917378ae15bae82b741c322424fa,46fd10864af2a90e407f6867adf980daa940b075
merge_tree = 8eb146006419d93dc0a74710ca9efaaf101ab280
diff_sha256 = 710aa1bf66619d3fb110398d692c76e3793987d0df75d0b55de2ad795954e3bb
approval_after_last_push = true
```

El candidate contiene exactamente dos altas `100644`:

```text
A scripts/shared/f10_9_metadata_planner.py
A tests/test_fase10_9_p5_metadata_readonly.py
```

## Contrato Y Validacion G3

P5 procesa snapshots nativos locales, filtra cursos activos, normaliza null,
blank, Unicode format-only y placeholders exactos versionados, pagina
internamente, compara dos cohortes y emite solo agregados y fingerprints. La
superficie no importa ni invoca DB, HTTP, provider o writer y aplica limites de
filas, ancho y texto antes de copiar o normalizar.

```text
focused_p5 = 56 PASS
full_f10_9 = 244 PASS
python_compile = PASS
f10_9_boundary = PASS mode=p5
credential_scan = PASS
security_auditor = GO_TO_COMMIT
qa = GO_TO_COMMIT
data_quality = GO_TO_COMMIT
pr_security_audit_run = 31405441682:success
pr_f9_7_contract_run = 31405441145:success
post_merge_security_audit_run = 31409222936:success
post_merge_f9_7_contract_run = 31409222568:success
```

Los checks post-merge usaron
`headSha=1c5d1526a1da247ca6ad0eb7b25cd5e0b0f51564`. Por tanto:

```text
G3 = PASS
P5 = COMPLETED_POST_MERGE_VERIFIED
```

## Decision G4

La linea base diagnostica conserva `104/224` cursos activos incompletos, pero
ese valor no es una atestacion vigente ni sustituye un fingerprint remoto
actual. F10.9 no ha autorizado acceso al data plane para recalcularlo y no puede
demostrar el umbral obligatorio de cero.

Ademas, si el hallazgo persiste, llevarlo a cero exige re-enrichment, backfill,
writer editorial o DML. Todas esas capacidades estan fuera de F10.9 y P6 esta
expresamente diferido. Ningun resultado local P5 corrige datos operativos.

Se cumplen dos condiciones independientes de STOP:

```text
current_zero_metadata_evidence = NOT_AVAILABLE
known_diagnostic_snapshot = 104_incomplete_of_224_active
mutation_required_if_persistent = true
mutation_authorized_in_f10_9 = false
G4 = STOP_REQUIRES_REBASELINE
G5_P7 = BLOCKED_NOT_AUTHORIZED
```

La autoridad superior debe decidir fuera de F10.9 si crea una fase separada de
remediacion de metadata, traslada el hallazgo a otro hito o modifica mediante
waiver/rebaseline el umbral contractual. Hasta entonces no procede P7,
Certification, Main, diagnostico Production, schedules ni observacion de 72h.

Este documento no concede DDL/DML, SQL, Supabase, providers, writers,
re-enrichment, backfill, cambios editoriales, environments, variables, retries,
dispatches, schedules, Certification, Main ni F11.1.
