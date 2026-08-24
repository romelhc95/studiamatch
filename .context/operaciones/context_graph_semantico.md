# Context Graph Semantico

> Este documento define la estructura reutilizable del grafo. No crea alcance ni autoriza ejecucion.

## Estructura Canonica

```text
.context/
├── 00_INDICE.md
├── estado_del_proyecto.md
├── backlog_tareas/<requerimiento>/
│   ├── _index.md
│   └── tarea_<NNN>_<hito>.md
├── hitos/
│   └── hito_<NNN>.md
├── decisiones/
│   └── ADR-<NNNN>_<decision>.md
├── operaciones/
│   └── plan_maestro_<requerimiento>.md
├── arquitectura_pipeline.md
├── sistema_db_supabase.md
├── operaciones/
│   └── matriz_adopcion_db.md
├── matrices/
│   └── matriz_hito_<NNN>.md
├── work_packages/
│   └── WP-<HITO>-<NNN>.json
├── evidencias_cliente/
│   └── req_est_001_sprint_1/
│       └── evidencia_hito_<NNN>.md
└── seguimiento/
    ├── seguimiento_<requerimiento>.md
    └── retrospectiva_<hito>.md
```

## Responsabilidades

| Documento | Responsabilidad |
|---|---|
| Estado | Unica autoridad viva de fase, tarea y WP. |
| Requerimiento | Alcance, fuentes, criterios y exclusiones. |
| Plan Maestro | Dependencias, secuencia, gates y estrategia. |
| Hito | Contrato funcional y criterio de salida. |
| TASK | Trabajo autorizable. |
| ADR | Decision irreversible o relevante. |
| Manifest | Alcance mecanizable e inmutable. |
| Arquitectura Pipeline | Topologia aplicativa, runtime, workflows, writers y despliegue. |
| Sistema DB Supabase | Modelo de datos, RLS, RPC, lectores, escritores y contrato de credenciales. |
| Matriz Adopcion DB | Estado esperado por ambiente, promocion DB-as-code y drift. |
| Matriz | Criterio, prueba, ambiente y evidencia. |
| Evidencia | Resultado observado. |
| Tracker | Dashboard operativo. |
| Retrospectiva | Tiempo, rework y mejoras. |

## Validacion Semantica Minima

- `estado_del_proyecto.md` debe declarar `F10.11` en preparacion `GOV-CI12`, `F12.1` bloqueada por homologacion y rebaseline, `active_work_package = WP-H2-001`, `WP-H2-001=ACTIVE_R1` y `PREPARE_WP_GOV_CI_012_R2_APPROVAL`.
- El Plan Maestro debe mantener O0-O5 historicos completados, Etapa 1 Obsidian como `DESARROLLO_MERGED_PENDING_HOMOLOGATION`, `WP-H2-001` activo hasta R1, PR #424, PR #425, PR #426, PR #427, PR #429, PR #430, PR #432, PR #434, PR #436, PR #438, PR #439, PR #441, PR #442 y PR #444 publicados en `desarrollo`, PR #428 como `O2_CONSUMED_BY_FAILURE`, PR #431 como `R3-GOV-HOM-003-O2-REQ1_CONSUMED_BY_FAILURE`, PR #433 como O2 mergeado con run post-merge `32615044699` fallido, PR #435 como `R3-GOV-HOM-005-O2-REQ1_CONSUMED_BY_FAILURE`, PR #437 como O2 mergeado con run post-merge `32650341464` fallido, PR #438 como run post-merge `32655520324` fallido, PR #440 como O2 mergeado con run post-merge `32662084712` fallido, PR #441 como run post-merge `32666126533` fallido con `POST_MERGE_ATTESTATION_DUPLICATE`, PR #443 y PR #445 como `FAILED_NOT_MERGED_FROZEN`, y el proximo gate unico `PREPARE_WP_GOV_CI_012_R2_APPROVAL`.
- El tracker debe contener las ocho secciones operativas y el bloque terminal `Prompt Cavernicola`.
- El indice debe enlazar Estado, Plan Maestro, tracker, retrospectiva, ADR R0-R3, matrices, evidencias y work packages H2-H5.
- El indice debe enlazar `WP-GOV-OBS-001`, `WP-GOV-INFRA-001`, `TASK-GOV-OBS-001` y `TASK-GOV-INFRA-001` como evidencia R2 ya publicada en desarrollo por PR #424.
- El indice debe enlazar `arquitectura_pipeline.md`, `sistema_db_supabase.md` y `operaciones/matriz_adopcion_db.md` como fuentes canonicas no ejecutables.
- El indice debe enlazar `WP-GOV-ARCH-001` y `TASK-GOV-ARCH-001` como artifacts consumidos por PR #425, `WP-GOV-HOM-001`/`TASK-GOV-HOM-001` como artifacts consumidos por PR #426, `WP-GOV-CI-001`/`TASK-GOV-CI-001` como artifact consumido por PR #427, `WP-GOV-CI-002`/`TASK-GOV-CI-002` como artifact consumido por PR #429, `WP-GOV-CI-003`/`TASK-GOV-CI-003` como artifact consumido por PR #430, `WP-GOV-CI-004`/`TASK-GOV-CI-004` como artifact consumido por PR #432, `WP-GOV-CI-005`/`TASK-GOV-CI-005` como artifact consumido por PR #434, `WP-GOV-CI-006`/`TASK-GOV-CI-006` como artifact consumido por PR #436, `WP-GOV-CI-007`/`TASK-GOV-CI-007` como artifact publicado por PR #438 con fallo post-merge, `WP-GOV-CI-008`/`TASK-GOV-CI-008` como artifact publicado por PR #439 con O2 #440 fallido, `WP-GOV-CI-009`/`TASK-GOV-CI-009` como artifact publicado por PR #441 con fallo post-merge, `WP-GOV-CI-010`/`TASK-GOV-CI-010` como artifact consumido por PR #442, `WP-GOV-CI-011`/`TASK-GOV-CI-011` como artifact publicado por PR #444 con O2 #445 fallido, y `WP-GOV-CI-012`/`TASK-GOV-CI-012` como candidate causal evidence; el siguiente gate unico es `PREPARE_WP_GOV_CI_012_R2_APPROVAL`.
- Cada WP Sprint 1 debe permanecer `PROPOSED` hasta aprobacion humana por digest; `WP-H2-001` es la excepcion vigente y debe permanecer `ACTIVE` solo hasta R1.
- Ninguna evidencia o tracker puede marcar H2-CA2/H2-CA3 implementado, aceptado o completado antes de evidencia funcional y cualquier R3 JIT requerido.

## Taxonomia De Lifecycle H2 Bloqueado Por Obsidian Main

| Campo | Valor preaprobacion H2 | Regla |
|---|---|---|
| `lifecycle_stage` | `ACTIVE` | La activacion R1 fue registrada; el siguiente gate es revision Plan de implementacion. |
| `gate_status` | `APPROVED_R1` | O5, checkout limpio, aprobacion digest+commit y activacion R1 estan completos. |
| `implementation_status` | `BLOCKED_PENDING_HOMOLOGATION_AND_REBASE` | F12.1 es traza futura; H2-CA2 no inicia hasta que Etapa 1 cierre por predicado externo y `WP-H2-001` sea rebasado. |
| `work_package_status` | `ACTIVE` | Tiene metadata de aprobacion y activacion; no hay implementacion iniciada. |
| `criteria_status` | `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED` | Ningun criterio puede estar PASS/ACCEPTED antes de implementacion. |
| `acceptance_status` | `NOT_STARTED` | No existe evidencia de aceptacion H2. |
| `approval_target_lifecycle_stage` | `APPROVED_NOT_ACTIVE` | Resultado permitido por aprobacion futura; no es estado actual. |
| `approval_target_gate_status` | `APPROVED_R1` | Techo autorizado por la primera aprobacion; no concede activacion. |
| `approval_target_level` | `R1` | La primera aprobacion de H2 no puede conceder R2 ni R3. |

Los campos `approval_target_*` forman parte del payload firmado del manifest. El
estado mutable actual (`status`, `lifecycle_stage`, `gate_status`, progreso,
metadata de aprobacion y activacion) queda fuera de esa proyeccion para que una
aprobacion futura pueda registrar evidencia humana sin cambiar el digest firmado.
Un `PROPOSED` con estado actual `APPROVED_NOT_ACTIVE` o `APPROVED_R1` es una
pseudo-aprobacion y debe fallar. Un `ACTIVE` sin `activated_at` o sin
`active_work_package = WP-H2-001` es una activacion incompleta y debe fallar.

## Transiciones WP Permitidas

```text
PROPOSED -> APPROVED -> ACTIVE -> COMPLETED
PROPOSED/APPROVED/ACTIVE -> REVOKED
PROPOSED/APPROVED/ACTIVE -> EXPIRED
```

`PROPOSED` no puede contener `approval_digest`, `approved_by`, `approved_at`,
`approval_reference` ni `activated_at`. `APPROVED` requiere digest coincidente,
aprobador humano, referencia de aprobacion, timestamp UTC y vigencia. `ACTIVE`
requiere ademas `activated_at` y que `active_work_package` coincida con el WP.
`APPROVED` no desbloquea paths funcionales. Solo un `ACTIVE` estructuralmente
valido y vigente puede usar `allowed_paths`, y aun asi no autoriza R2/R3 ni
operaciones remotas.

## Taxonomia De Fases Posteriores A F10.11

F10.11 queda como cierre contractual y homologacion local. La documentacion
Obsidian solo cierra cuando el bundle canonico este convergido como `T_HOM` en
`main`, `certificacion` y `desarrollo`, con ancestry validada y consumido por el
checkout ordinario. F12 es la macrofase futura posterior a ese cierre. `F12.1`
corresponde a H2-CA2 local R1, pero permanece
`BLOCKED_PENDING_HOMOLOGATION_AND_REBASE`; `F12.2` queda bloqueada para H2-CA3
hasta que CA2 tenga evidencia local. La fase decimal selecciona tareas y
trazabilidad; la autorizacion se deriva del WP/digest vigente. R2 y R3 siempre
requieren gates separados.

## Homologacion No Recursiva GOV-HOM

`WP-GOV-HOM-001` define el candidate `T_HOM` posterior a PR #425. El cierre de
F10.11 es un predicado externo: trees iguales a `T_HOM`, ancestry `main ->
certificacion -> desarrollo`, grants R3 `O2`/`O3`/`O4`/`O5` consumidos por
separado, DB Sync sin cambios, ningun writer/schedule/DDL/DML/Supabase y checkout
ordinario actualizado. El grafo debe fallar si reaparece el gate literal de
arquitectura ya consumido, si se agrupan grants o si H2 inicia antes de ese
predicado.

## Separacion CI Y Review GOV-CI

`WP-GOV-CI-001` desacopla `security-audit` del gate nativo de review. El
workflow valida attestation, manifest, digest, `Base-SHA`, `Candidate-SHA`, head
real, ancestry, paths y co-change solo en PR hacia `desarrollo`. La review
humana obligatoria queda en GitHub branch protection; no dispara CI, no consulta
Reviews API y no requiere rerun manual. `certificacion`, `main` y cualquier R3
siguen requiriendo grants JIT separados.

## Boundary Estructural De Promocion GOV-CI2

`WP-GOV-CI-002` corrige el fallo de PR #428, donde O2 fue evaluado como diff
incremental y quedo `O2_CONSUMED_BY_FAILURE`. Las promociones O2-O5 entre ramas
protegidas usan boundary estructural: validan repositorio same-repo, `Operation`,
`Grant-ID`, par base/head, `Base-SHA`, `Candidate-SHA`, ancestry, tree sintetico,
`Final-WP`, `D_FINAL`, `T_FINAL`, `Approval-Level=R3 JIT single-use`,
`Approval-Reference` y expiry. PR #428 y `R3-GOV-HOM-001-O2` quedan bloqueados
como consumidos. El modo estructural solo acepta accion `opened` con
`GITHUB_RUN_ATTEMPT=1`; ediciones, synchronize, reopen, ready-for-review y reruns
fallan cerrados. Los PR normales siguen usando boundary incremental por WP y
allowlist/denylist. Sin ledger persistente, CI valida precondiciones stateless y
el consumo definitivo del grant se registra externamente bajo el gate posterior.

GOV-CI3 reemplaza grants versionados aprobados por solicitudes estaticas
`REQUESTED_JIT_SINGLE_USE` con bindings simbolicos a `pull_request.base.sha`,
`pull_request.head.sha`, `tree(pull_request.head.sha)` y `manifest.candidate_digest`.
Las solicitudes no contienen `candidate_sha`, `t_final`, approvals, expiry ni
`consumed=false`; los valores exactos viven en la Promotion Attestation del PR.

GOV-CI4 corrige el fallo pre-run de PR #431: `Promotion Boundary` no debe usar
el Environment `Certification`, porque GitHub evalua deployment branch policies
contra `refs/pull/<n>/merge` en eventos `pull_request`. Las promociones O2-O5
usan un Environment dedicado `Promotion`, con reviewer requerido y sin branch
policy remota. Crear/configurar ese Environment es R3 separado; CI4 solo versiona
el cambio local y bloquea PR #431 y `R3-GOV-HOM-003-O2-REQ1` como consumidos.

GOV-CI5 corrige el fallo post-merge de PR #433: un push generado por merge de
promocion protegida no debe evaluarse exclusivamente como diff incremental si
existe evidencia read-only de PR O2-O5 asociado, checks pre-merge verdes,
attestation, review humano y merger esperado. La validacion post-merge es
estructural y fail-closed; si falta evidencia, el workflow vuelve al boundary
incremental. PR #433 y `R3-GOV-HOM-004-O2-REQ1` quedan consumidos y O3 sigue
bloqueado hasta publicar CI5 y ejecutar nuevo re-O2 con grant JIT separado.

GOV-CI6 corrige el fallo de PR #435: F9.7 queda `MANUAL_FROZEN_ONLY` sin triggers
automaticos `pull_request`/`push`, y O2-O5 usan ramas target-aware
`promote/gov-hom-006-oN`. El candidate debe tener parent 1 igual al target SHA,
parent 2 igual al source SHA y `tree(candidate)=tree(source)=T_FINAL`. PR #435 y
`R3-GOV-HOM-005-O2-REQ1` quedan consumidos por fallo; no se editan ni reintentan.
O3 posterior requiere R3 JIT que reconozca Cloudflare Pages Production rebuild y
DB Sync detect-only con resultado obligatorio `NO_DB_CHANGES`.

GOV-CI7 corrige el fallo de PR #437: los pushes post-merge se clasifican como
`VERIFIED_PROMOTION`, `NOT_APPLICABLE` o `BLOCKED`. Solo `NOT_APPLICABLE` usa
fallback incremental; toda promocion invalida, ambigua o con evidencia no
confiable falla cerrada. Check-runs con `pull_requests: []` son aceptables solo
si la asociacion merge -> PR es unica y valida. PR #437 y
`R3-GOV-HOM-006-O2-REQ1` quedan consumidos; HOM-006 O3-O5 quedan superseded y
HOM-007 reemplaza la familia.

GOV-CI8 corrige el fallo post-merge de PR #438: un PR ordinario y unico hacia
`desarrollo` se clasifica como `NOT_APPLICABLE`, sin aplicar reglas de par de
promocion; direct pushes, evidencia ausente, ramas superiores no promocionales y
familias HOM-006/HOM-007 quedan `BLOCKED`; solo rutas exactas HOM-008 pueden ser
`VERIFIED_PROMOTION`. PR #438 queda como fallo post-merge consumido y HOM-008
reemplaza la familia runtime futura.

GOV-CI9 corrige el fallo post-merge de PR #440: `romelhc95-approver` conserva
su rol de reviewer/aprobador, pero no debe actualizar ni mergear `desarrollo`,
`certificacion` ni `main`. El desired state es un ruleset permanente
`owner-only-protected-branch-updates` con `Restrict updates`, bypass exclusivo de
`romelhc95` (`actor_id=18040405`) y exclusion de `romelhc95-approver`
(`actor_id=306979205`). HOM-008 queda superseded y HOM-009 reemplaza la familia
runtime futura.

GOV-CI10 corrige el fallo post-merge de PR #441: las attestations se parsean por
seccion exacta y no por body completo. PR ordinarios hacia `desarrollo` usan solo
`## Governance Attestation`; promociones O2-O5 usan solo
`## Promotion Attestation`. PR #441 y run `32666126533` no se editan ni se
rerunean. HOM-009 queda superseded y HOM-010 reemplaza la familia runtime futura.

GOV-CI11 congela PR #443 como `FAILED_NOT_MERGED`, marca `R3-GOV-HOM-010-O2-REQ1` consumido y supersede HOM-010 O3-O5. HOM-011 requiere `R3_JIT_APPROVAL_ENVELOPE` con schema `promotion-jit-envelope-v1`, `opened` attempt 1, `Promotion.can_admins_bypass=false`, Cloudflare Pages app_id `85455`, `DB Sync Detect Only=NO_DB_CHANGES` para O3 y O4 bloqueado hasta cierre O3.

GOV-CI12 congela PR #443 y PR #445 como `FAILED_NOT_MERGED_FROZEN`, marca `R3-GOV-HOM-011-O2-REQ1` consumido y supersede HOM-011 O3-O5. HOM-012 requiere `promotion-jit-envelope-v2`, una sola aprobacion Environment `Promotion` pre-merge, evidencia `promotion-approval-evidence.json`, post-merge sin secret ni Environment, collector REST Python testeable, `bypass_actors=UNOBSERVABLE` fail-closed, O3 asincronico con `o3-closure-evidence.json`, O4 consumidor real y O5 trees/ancestry.

## Semantica De Paths

Los patrones de `allowed_paths` son POSIX relativos al root del repositorio. Se
rechazan paths absolutos, backslashes, `..`, segmentos `.`, patrones vacios,
wildcards globales y solapamientos allow/deny. Renames y copias validan origen y
destino.

## Binding De Aprobacion

La aprobacion humana posterior a F10.11 debe vincular externamente el digest del
manifest y el commit candidate que lo contiene. No se introduce el SHA del mismo
commit dentro del manifest para evitar dependencia circular. La primera
aprobacion de `WP-H2-001` solo puede autorizar R1; R2 y R3 requieren gates
posteriores separados.
