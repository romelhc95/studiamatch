# PLAN-F10.10-001 - Remediacion Acotada De Metadata

| Campo | Valor |
|---|---|
| Estado | `SUPERSEDED_FOR_HITO_1_TRANSFERRED_TO_H2_CA2` |
| Subfase | `F10.10` |
| Hito | `HITO-001` |
| Criterio | `H2-CA2` pendiente de rebaseline nuevo |
| Decision | [ADR-0010](../decisiones/ADR-0010_rebaseline_f10_10_metadata_remediation.md) |
| Autoriza ejecucion remota | `NO` |

> [ADR-0011](../decisiones/ADR-0011_rebaseline_superior_hito1_ca1_f10_10_a_h2.md)
> supersede este plan para Hito 1. Se conserva como antecedente H2; no autoriza
> continuidad ni reutilizacion de capacidades.

Todo el contenido operativo posterior queda `HISTORICAL_RESEARCH_ONLY`. Las
frases en presente, gates propuestos y contratos tecnicos describen el baseline
anterior y no son vigentes ni aprobables. Hito 2 requiere documentos e
identidades nuevas.

## Objetivo

Corregir de forma acotada, reversible y atribuible los cursos activos que sigan
sin syllabus y/o objectives, sin reabrir F10.9, sin ampliar writers del pipeline,
sin modificar schema y sin cambios fuera de una cohorte congelada por target
fisico.

El [rebaseline M3 reader](./m3_reader_f10_10_rebaseline.md) introduce una
excepcion preparatoria Free-only al veto general de DDL de esta version del plan:
un package local para crear y retirar exclusivamente el rol efimero
`studiamatch_m3_reader`. Las DDL reader v1/v2 fueron consumidas y revertidas; no
existe capacidad vigente. El diagnostico ACL posterior fue read-only y termino
STOP. La excepcion no modifica schema de aplicacion, tablas, RLS, policies, triggers ni datos, y solo
podra ser operativa despues de merge protegido, CI/post-merge y gates/payload
separados. Certification y Pro quedan fuera de la excepcion.

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
- DDL, schema, RLS, grants, triggers o migrations, salvo el candidate local
  Free-only del rol M3 reader descrito en su rebaseline; su DDL remoto permanece
  prohibido hasta gate futuro;
- copiar datos operativos entre ambientes;
- sobrescribir metadata valida o cambiar actividad para reducir el denominador;
- schedules, observacion F10.9 o F11.1.

## Gates

| Gate | Alcance | Salida requerida | Capacidad |
|---|---|---|---|
| `M0` | Registrar ADR, plan, autoridad y tarea | `PASS`: PR #343 y checks post-merge verificados | Git/docs consumido |
| `M1` | Tooling, fixtures y tests offline | Candidate local fail-closed; cero red/DB/provider | Codigo local |
| `M2` | Promover codigo sin ejecucion | SHA/tree/digest inmutables y CI PASS | Git/CI |
| `M3` | Historia M3 preservada | Worktree local no promovido `HISTORICAL_NON_PROMOTABLE` | No reutilizable |
| `M4-M9` | Metadata, providers, revision, pilot, restore y lotes | `NOT_EXECUTED_TRANSFERRED_TO_H2` | Rebaseline H2 requerido |
| `M10` | Handoff de autoridad | `SUPERSEDED_BY_ADR_0011` | Consumido documentalmente |

Ningun gate concede el siguiente. Ningun gate, payload, reader, ACL, credential,
binding, manifest, cohorte o aprobacion de F10.10 puede reutilizarse en Hito 2.
Todos los gates M3 anteriormente propuestos quedan `SUPERSEDED_NON_AUTHORIZABLE`;
no existe gate sucesor F10.10. La unidad target y las secuencias anteriores son
solo investigacion historica.

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

El criterio M9 queda transferido a H2-CA2 y ya no bloquea Hito 1. ADR-0011 cambia
G4 a `PASS_CA1_FG2_FG3_ONLY_METADATA_TRANSFERRED_TO_H2`.

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

M4-M9 quedan `NOT_EXECUTED_TRANSFERRED_TO_H2`. Toda ejecucion remota y toda
continuidad M3 quedan prohibidas bajo este plan.

El [scope M3 v2 Free-only](./m3_f10_10_scope_por_ambiente_target.md)
queda preservado como contrato historico no autorizable. La
[evidencia M3](./m3_f10_10_post_merge_evidence_2026_08_11.md) registra PR #350,
merge `332706fe3ed2b525438494b50be8aad583bedd83`, tree
`91e1fc1b89ce2a2fc3aa8114ef9a0818b60dcd46` y checks post-merge PASS. El
collector v1 queda promovido solo como antecedente. Su secuencia historica
Free -> Certification -> Pro queda `SUPERSEDED_BY_M3_READER_V2_FREE_ONLY` y no es
ejecutable. Ningun gate historico concede M4.

### Investigacion Historica Del Reader - No Reutilizable

El collector v1 promovido por PR #350 permanece antecedente. El ultimo estado
historico previo a ADR-0011 fue `M3_PUBLIC_DB_ACL_PRIVATE_PREFLIGHT_FREE_V2_PAYLOAD_POST_MERGE_VERIFIED_CONSUMER_BINDING_REQUIRED`: PR #353 promovio collector
v2, PR #354/#355 reconciliaron evidencia/rotacion y PR #356 promovio binding
passwordless; CI post-merge rerun termino PASS.
PR #371 promovio el payload v2 null-bound. Su primer F9.7 post-merge fallo
fail-closed antes de crear PostgreSQL; PR #372 remedio exclusivamente el harness
y su merge `89cbeda226c6e04c6c1b6e091e6b94fc36273645` obtuvo Security Audit
`31720301586=PASS` y F9.7 `31720301577=PASS`. El consumer binding canónico no fue
implementado por esas promociones.
El run `31513546109` preserva intento 1 `FAIL_TRANSIENT_LOCAL_SOCKET_AFTER_READY`
y un unico rerun sin cambios, intento 2 `PASS`; no se repitio ningun acceso remoto.
El package `db/free_only_migrations/` permanece fuera del glob Pro y la
compensacion sigue fail-closed.
DB Sync excluye `db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql` y el path exacto de compensacion de
su deteccion automatica Pro-relevant. El rol Free `studiamatch_m3_reader` nace con
`NOLOGIN/PASSWORD NULL/rolvaliduntil NULL`, obtiene solo
SELECT de cuatro columnas y no tiene otra relacion, mutacion o acceso efectivo a
`SECURITY DEFINER`; `BYPASSRLS=true` es obligatorio siempre para full-population.
La activacion privada Q0 fija `LOGIN` y `VALID UNTIL` exacto/finito desde
`F10_10_M3_VALID_UNTIL`, y usa solo `psql
\password` para establecer el password.

El provisioner PostgreSQL 17 aprobado por `F10_10_M3_PROVISIONER` es exactamente
el unico member/admin del reader (`roleid=reader`, `member=provisioner`) con
`admin=true/inherit=false/set=false`; el reader es member de cero roles
(`member=reader`). El fingerprint del provisioner se incorpora a
`target-binding-v2`.

Binding offline y atestacion TLS/server de la misma conexion son evidencias
separadas y sus digests no pueden ser iguales; se retiran los valores negociados
TLS/server exactos del entorno. `q0-only` es un gate independiente anterior a
Q1-Q4. `collect` exige mecanicamente su manifest/digest predecessor canonical v2
PASS con query-set y target binding identicos. El manifest sanitizado prueba
PASS/transcript/binding/query-set/counters, no publica BYPASS/expiracion raw. La
compensacion acepta estado activo con expiracion futura o expirada, o inactivo;
cuarentena primero, termina sesiones bajo gate, revoca grants/settings del package
y solo elimina al final si dependencias ajenas no bloquean el drop.

El manifest/envelope canonical, target binding, observed transport y predecessor
son v2. Los content digests `query-set-v1`, `schema-v1`, `constraints-v1`,
`triggers-v1`, `snapshot-raw-v1`, `snapshot-normalized-v1` y `cohort-v1` se
conservan intencionalmente y son validos dentro de v2; manifest/binding v1 sigue
rechazado y no existe `q0-attestation-v2`.

El gate preflight Free fue consumido una vez y termino PASS. DDL v1 y v2 fueron
consumidas una vez cada una y terminaron rollback; ambas quedan no reutilizables.
El diagnostico bound consumio una llamada `execute_sql` sin retry bajo PostgreSQL
17 `REPEATABLE READ READ ONLY` y termino
`STOP_PUBLIC_DB_ACL_REMEDIATION_REQUIRED`: TARGET y OTHER_CONNECTABLE no
conformes; NON_CONNECTABLE conforme e inmutable. Hubo cero filas de aplicacion,
DDL/DML/RPC/provider/writer/Pro. Q0 Free, lectura y teardown Free estan no
consumidos. Los CI anteriores al run `31533516407`, PostgreSQL 17 local y
rotacion atestada conservan su evidencia historica PASS. El diagnostico
`pg_catalog` counts/flags-only bajo gate separado fue consumido una vez y produjo
STOP. No hubo passwords ni lectura funcional remota. Certification, Pro, M4-M10,
F10.9/G4, schedules y F11.1 permanecen bloqueados.

La contrasena SQL usada previamente por un canary local fue rotada/revocada fuera
de banda segun [atestacion sanitizada](./m3_reader_f10_10_rotation_attestation_2026_08_11.md)
y no puede reutilizarse. Su valor no se documento. El hallazgo queda cerrado solo
para esa identidad.

El run post-merge `31533516407` de PR #358 fallo porque el harness acepto el
servidor temporal que el entrypoint PostgreSQL usa durante init; el socket
desaparecio al transicionar al servidor final. No se autoriza un rerun ciego. La
remediacion debe esperar el marcador `PostgreSQL init process complete`, comprobar
contenedor/socket y exigir tres probes consecutivos antes del contrato. DDL Free
permanece bloqueado hasta merge protegido y CI post-merge PASS de esa correccion.
