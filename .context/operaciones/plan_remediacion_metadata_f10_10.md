# PLAN-F10.10-001 - Remediacion Acotada De Metadata

| Campo | Valor |
|---|---|
| Estado | `M3_COLLECTOR_PROMOTED_REMOTE_GATES_PENDING` |
| Subfase | `F10.10` |
| Hito | `HITO-001` |
| Criterio | `H1-CA1` con metadata cero preservada |
| Decision | [ADR-0010](../decisiones/ADR-0010_rebaseline_f10_10_metadata_remediation.md) |
| Autoriza ejecucion remota | `NO` |

## Objetivo

Corregir de forma acotada, reversible y atribuible los cursos activos que sigan
sin syllabus y/o objectives, sin reabrir F10.9, sin ampliar writers del pipeline,
sin modificar schema y sin cambios fuera de una cohorte congelada por target
fisico.

El snapshot historico `104/224` sirve solo como antecedente. La primera cohorte
operativa debe surgir de dos lecturas paginadas vigentes con la politica P5
`f10.9-metadata-v2` y fingerprint estable.

## Frontera

Permitido solo tras el gate y aprobacion correspondientes:

- lectura paginada de `courses` y lineage persistido necesario;
- generacion privada desde fuentes oficiales persistidas;
- providers con budget explicito, evidencia fuente y revision humana total;
- PATCH fill-only exact-one de `courses.syllabus`/`courses.objectives`;
- restauracion de category/category_id/category_confirmed solo ante efecto del
  trigger de syllabus en la misma fila;
- backup/restore privado y verificaciones sanitizadas.

Prohibido en toda F10.10 salvo nuevo rebaseline superior:

- live fetch, crawling o source HTTP;
- INSERT, DELETE, UPSERT, RPC, SQL ad hoc o writers masivos;
- writes en `staging_raw`, `cleansed_programs` o `enriched_programs`;
- ejecutar workers core o scripts legacy como reparacion;
- DDL, schema, RLS, grants, triggers o migrations;
- copiar datos operativos entre ambientes;
- sobrescribir metadata valida o cambiar actividad para reducir el denominador;
- schedules, observacion F10.9 o F11.1.

## Gates

| Gate | Alcance | Salida requerida | Capacidad |
|---|---|---|---|
| `M0` | Registrar ADR, plan, autoridad y tarea | `PASS`: PR #343 y checks post-merge verificados | Git/docs consumido |
| `M1` | Tooling, fixtures y tests offline | Candidate local fail-closed; cero red/DB/provider | Codigo local |
| `M2` | Promover codigo sin ejecucion | SHA/tree/digest inmutables y CI PASS | Git/CI |
| `M3` | Contencion y diagnostico read-only | Cohorte vigente doble, schema/trigger/writer fingerprints | Lectura remota |
| `M4` | Generar propuestas privadas | Candidate atribuible, budget respetado, cero DB writes | Provider sin writer |
| `M5` | Revision editorial | 100% outputs provider revisados; solo aprobados son elegibles | Humano |
| `M6` | Pilot maximo 5 | exact-one, verify, cero no-cohorte | Writer acotado |
| `M7` | Idempotencia/restore del pilot | apply NOOP, restore, restore NOOP, apply final y apply final NOOP | Writer acotado |
| `M8` | Lotes restantes maximo 10 | stop-on-drift y checkpoints; un writer secuencial | Writer acotado |
| `M9` | Verificacion cero | metadata cero, cero ETL/no-cohorte, idempotencia PASS | Lectura remota |
| `M10` | Handoff de autoridad | Decision separada sobre F10.9/G4 | Docs/Git |

Ningun gate concede el siguiente. M0 no autoriza M1. M2 no autoriza environments.
Free, Certification y Pro requieren etapas de aprobacion independientes. La
unidad de datos es el target fisico inmutable `(project_ref, host_fingerprint)`.
Si dos nombres apuntan al mismo target fisico, se ejecuta una sola cohorte/apply
y se registran dos approvals/replays; no se reportan como cohortes independientes.

## Cohorte

La politica bloqueante `metadata-remediation-v1` se aplica sobre toda la
poblacion activa y exige por cada campo syllabus/objectives:

```text
courses.is_active = true
field_non_missing_under_f10_9_metadata_v2 = true
field_same_target_official_source_attributed = true
field_mock = false
field_semantics_valid = true
```

La cohorte de reparacion es el subconjunto activo que falla completitud P5. Las
fallas de atribucion/mock/semantica fuera de ese subconjunto generan HOLD y
tambien bloquean M9; no se ocultan por no requerir PATCH.

Cada target fisico deriva su propia poblacion/cohorte, ordenada por `course.id`,
mediante dos snapshots completos identicos. El manifest privado conserva ID,
preimagen exacta, fingerprints, lineage y candidate. La proyeccion versionada
conserva solo conteos, reason codes y digests.

Snapshots completos se repiten en M3, inmediatamente antes y despues del pilot,
antes y despues de cada lote y dos veces en M9. Cada checkpoint reconcilia
full-pagination, total row IDs/count, active IDs/count, contenido y cohorte.

Una fila entra en candidate solo si:

- permanece activa e incompleta en ambos snapshots;
- tiene lineage unico y same-target;
- la fuente oficial persistida es suficiente y no mock;
- no existe conflicto o cambio concurrente;
- solo se propone el campo que estaba missing.

Reason codes HOLD minimos:

```text
HOLD_AMBIGUOUS_LINEAGE
HOLD_SOURCE_MISSING
HOLD_SOURCE_STALE
HOLD_INSUFFICIENT_EVIDENCE
HOLD_PROVIDER_FAILED
HOLD_EDITORIAL_REVIEW
HOLD_CONCURRENT_CHANGE
```

Un solo HOLD bloquea M9 PASS.

La unidad contable es el slot `(course_id, field_name)`, con
`field_name in (syllabus, objectives)`. Todo slot incompleto congelado y todo slot
incompleto vigente deben reconciliarse:

```text
frozen_incomplete_slots = remediated_slots + pending_slots + hold_slots + conflict_slots
current_incomplete_slots = pending_slots + hold_slots + conflict_slots + newly_incomplete_slots
unclassified_incomplete_slots = 0
```

Cada source record privado incluye field, physical target, lineage/source hash,
evidence location hash, extraction method/version, mock flag, freshness rule y
reviewer decision. `official`, `sufficient`, `stale` y `attributed` no pueden ser
booleanos sin esos campos reproducibles.

Todo provider call y revision se reconcilia por target:

```text
provider_outputs_total = reviewed_approved + reviewed_rejected + review_holds
unreviewed_provider_outputs = 0
```

Outputs fallidos, descartados, superseded y revisiones nuevas permanecen en el
denominador. Solo `reviewed_approved` puede entrar al candidate. Un output
rechazado debe quedar asociado a una propuesta aprobada posterior para el mismo
slot o a un HOLD terminal; nunca desaparece del ledger.

## Apply Y Reconciliacion

Cada PATCH metadata debe:

1. enlazarse a un ID del manifest privado;
2. comprobar `is_active=true` y preimagenes exactas;
3. tocar solo `syllabus`/`objectives` que sigan missing;
4. usar return=representation y exigir exact-one;
5. releer la fila y demostrar resultado exacto;
6. comprobar todas las columnas no autorizadas;
7. detener el lote ante cualquier divergencia.

El PATCH categoria es distinto: solo puede restaurar `category`, `category_id` y
`category_confirmed` a su preimagen, mediante CAS/exact-one y despues de demostrar
el side effect del trigger en esa misma fila. La unidad metadata+categoria no es
transaccional y tiene estado intermedio.

Ante timeout/desconexion no se repite la mutacion. Read-after-write clasifica
`APPLIED`, `NOT_APPLIED`, `CONFLICT` o `HOLD_AMBIGUOUS_WRITE`. Un estado mixto
entre PATCH metadata y PATCH categoria nunca se clasifica APPLIED. Si la
invisibilidad atomica es requisito, terminar `STOP_DDL_REQUIRED`.

## Backup Y Rollback

Antes de cada apply se exige snapshot privado de filas completas, preimagenes,
lineage y digests no-cohorte; confirmacion de writers/schedules pausados y target
binding. El restore usa compare-and-swap inverso, solo toca cambios de esta fase,
no pisa ediciones posteriores y debe terminar en segundo restore NOOP.

Secuencia obligatoria del pilot:

```text
apply
second_identical_apply = NOOP
restore
second_identical_restore = NOOP
final_apply
second_identical_final_apply = NOOP
```

Los contadores separan `metadata_patch_requests`, `category_restore_patches`,
`rows_touched`, `field_mutations`, `restore_patches` y `final_apply_patches`.
`expected` y `actual` se comparan dentro de cada categoria; no se usa un unico
contador ambiguo de writes. Initial apply, restore y final apply mantienen
contadores separados; un PATCH categoria no se incluye tambien como metadata
PATCH, aunque la misma fila aparezca en ambas categorias.

Los artifacts privados se retienen hasta 30 dias despues de la decision M10 o el
plazo superior que defina el environment. Nunca se publican en Git ni artifacts
de acceso general.

## Stop Conditions

Terminar STOP ante:

- drift de SHA/tree, schema, trigger, profile, policy, cohorte o source hash;
- writers/schedules activos o target ambiguo;
- lineage cero/multiple/cross-institution;
- necesidad de live fetch, DDL o ampliar tablas/campos;
- output provider sin atribucion o revision;
- write fuera de cohorte, exact-one failure o transporte no reconciliable;
- alteracion ETL/no-cohorte;
- restore fallido o cualquier apply/restore idempotente no-NOOP;
- metadata residual, HOLD o conflicto.

## Criterio De Salida M9

```text
current_active_incomplete = 0
frozen_cohort_incomplete = 0
frozen_incomplete_slots = remediated_slots + pending_slots + hold_slots + conflict_slots
current_incomplete_slots = pending_slots + hold_slots + conflict_slots + newly_incomplete_slots
pending_slots = 0
hold_slots = 0
conflict_slots = 0
newly_incomplete_slots = 0
unclassified_incomplete_slots = 0
full_population_quality_failures := quality_failure_slots
full_population_quality_failures = 0
quality_failure_slots = 0
accepted_mock_or_unattributed = 0
unresolved_holds_or_conflicts = 0
active_field_slots = 2 * active_count
active_field_slots = validated_source_slots + quality_failure_slots
unclassified_source_slots = 0
duplicate_source_slots = 0
provider_outputs_total = reviewed_approved + reviewed_rejected + review_holds
unreviewed_provider_outputs = 0
total_course_ids_before_digest = total_course_ids_after_digest
total_course_count_before = total_course_count_after
active_ids_before_digest = active_ids_after_digest
active_count_before = active_count_after
full_pagination_reconciled = true
metadata_patch_requests_expected = metadata_patch_requests_actual
initial_category_restore_patches_expected = initial_category_restore_patches_actual
restore_patches_expected = restore_patches_actual
final_apply_patches_expected = final_apply_patches_actual
final_category_restore_patches_expected = final_category_restore_patches_actual
initial_rows_touched_expected = initial_rows_touched_actual
restore_rows_touched_expected = restore_rows_touched_actual
final_rows_touched_expected = final_rows_touched_actual
initial_field_mutations_expected = initial_field_mutations_actual
restore_field_mutations_expected = restore_field_mutations_actual
final_field_mutations_expected = final_field_mutations_actual
exact_one_failures = 0
non_cohort_changed_rows = 0
etl_table_writes = 0
etl_table_write_attempts = 0
unexpected_column_changes = 0
restore_test = PASS
second_restore = NOOP
second_initial_apply = NOOP
second_final_apply = NOOP
security_audit = PASS
data_quality_review = PASS
writers_and_schedules = PAUSED
```

`non_cohort_changed_rows=0` compara todas las columnas de todos los IDs fuera del
manifest entre snapshots completos. Las tablas ETL comparan row counts y digests
completos before/after; adicionalmente el writer tiene allowlist mecanica de
tabla/metodos, tests AST, request ledger y auditoria de intentos. La igualdad
before/after no se usa sola para afirmar cero writes transitorios.

M9 PASS no reactiva F10.9. M10 requiere una nueva decision superior que cambie
formalmente G4 a `PASS_CA1_RUNTIME_ONLY` o mantenga STOP.

## Estado M0-M3

[EVID-M0-F10.10](./m0_f10_10_post_merge_evidence_2026_08_10.md) registra PR #343,
merge `f59c35272ccec930434b3ceeb1aee8eac732d4b9`, Security Audit
`31419218575=PASS` y F9.7 `31419218779=PASS`. M0=`PASS`.

La autorizacion M1 fue consumida para tooling, fixtures y pruebas offline. La
[evidencia M2](./m2_f10_10_post_merge_evidence_2026_08_10.md) registra PR #345 y
PR #346, candidate final `a234fecb9c750a28cd290882919be972f1408467`, merge
`a7a032c5f35b2cb4e4e8a152a03947b3d7d60a7c`, tree
`306d606ac42a791e8efc98af81730db2e58cb146` y checks post-merge PASS. M1 queda
`COMPLETED_POST_MERGE_VERIFIED` y M2=`PASS`.

La ejecucion remota M3 y M4-M10 permanecen sin autorizar. M2 no autoriza red,
DB, Supabase, providers, environments, writers, workflows operativos,
backup/restore, SQL ni DDL.

El [scope M3 por ambiente/target](./m3_f10_10_scope_por_ambiente_target.md)
queda aprobado como contrato y registra la adenda `verify-full` soportada. La
[evidencia M3](./m3_f10_10_post_merge_evidence_2026_08_11.md) registra PR #350,
merge `332706fe3ed2b525438494b50be8aad583bedd83`, tree
`91e1fc1b89ce2a2fc3aa8114ef9a0818b60dcd46` y checks post-merge PASS. El
collector queda promovido, pero la ejecucion sigue bloqueada hasta consumir, en
orden, `APPROVE_M3_FREE_READONLY`,
`APPROVE_M3_CERTIFICATION_REPLAY`, `APPROVE_SDLC_M3_PRO`,
`APPROVE_PRODUCTION_M3_READONLY_WINDOW` y `APPROVE_M3_PRO_READONLY`. Ningun gate
concede M4.
