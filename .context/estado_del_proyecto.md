# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-22-GOV-CI2-R2-PENDING`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Cierre contractual, homologacion canonica y Obsidian Sprint 1 | `GOV_CI2_PROMOTION_BOUNDARY_PENDING_R2` | PR #427 esta publicado en `desarrollo`; PR #428 fallo en O2 por `Canonical Path Boundary` y el grant O2 quedo `O2_CONSUMED_BY_FAILURE`. Falta `WP-GOV-CI-002` antes de solicitar nuevo O2 JIT. |
| `F11` | Cierre fisico legacy | `SUPERSEDED_BY_F10_11` | Cualquier limpieza fisica futura requiere autorizacion separada. |
| `F12` | Implementacion local Sprint 1 posterior a F10 | `BLOCKED_PENDING_HOMOLOGATION_AND_REBASE` | Macrofase futura H2-H5 gobernada por WP/digest; no ejecutable hasta cierre efectivo F10.11 y rebaseline de `WP-H2-001`. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 es el cutoff contractual de Hito 1. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Evidencia tecnica historica preservada; no ejecutable. |
| `F10.9` | `SUPERSEDED_BY_O0_B` | WP2B queda superseded; PR #413 cerrado sin merge y excluido. |
| `F10.10` | `HISTORICAL_NON_PROMOTABLE` | M3 reader/DDL queda congelado; no autoriza DDL/DML ni payloads. |
| `F10.11` | `GOV_CI2_PROMOTION_BOUNDARY_PENDING_R2` | PR #427 quedo mergeado a `desarrollo`; PR #428 fallo sin merge. Falta candidate `WP-GOV-CI-002`, R2 a `desarrollo` y luego nuevo O2 R3 JIT separado. |

## Subfases F12

| ID | Estado | Identidad vigente |
|---|---|---|
| `F12.1` | `BLOCKED_PENDING_HOMOLOGATION_AND_REBASE` | Hito 2 CA2 - contrato editorial y calidad; bloqueado hasta cierre F10.11, convergencia de trees y rebaseline de `WP-H2-001`. |
| `F12.2` | `BLOCKED_BY_F12_1_CA2` | Hito 2 CA3 - integracion de registros incompletos, bloqueada hasta cierre local de CA2. |

## Bases Vinculantes

| Concepto | Valor |
|---|---|
| Requerimiento | `REQ-EST-001` |
| Cutoff contractual Hito 1 | PR #291 / `64e4ed895d43121c5683e26a355993f18e528a5c` |
| Baseline tecnico | PR #327 / `main@ad89e8ab9575b37476502d6062e22c044ad6447b` |
| Tree tecnico | `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| Autoridad funcional | `desarrollo@9f163c2c5f8dc54b4986ce75ef1d5c69a740bedf` |
| Certificacion preservada | `certificacion@33b1c9ec3c49117c2020860d5850d9d67988f836` |
| PR #413 | `CLOSED_NOT_MERGED_EXCLUDED`, head `4461f13c79ac893cb428074a729d75140056557b` |
| Archives Etapa 1 | `archive/post-h1-desarrollo-20260820-9f163c2`, `archive/post-h1-certificacion-20260820-33b1c9e` |
| Desarrollo canonico O2 | `desarrollo@a2c97ec17aabc790b656d6db1b16bdc95f0af1b2` |
| Certificacion canonica O2 | `certificacion@4e7e41a9fac08e657308849701b4b1f70b994e3b` |
| Tree canonico O2 | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` |
| Main homologado O3 | `main@9b486146962bd2a092acfd649fdcf716e922de89` |
| Certificacion homologada O4 | `certificacion@fe7b27abf18c096f674948b4f30f815aea4aef08` |
| Desarrollo homologado O5 | `desarrollo@974f9d4bde6d79230afde5c5a86ba7a3894233c6` |
| Tree homologado O5 | `fcb59095e48441bb4486ccc196aee61e2e1e0fe3` |
| PR #424 gobierno OBS/INFRA | `MERGED_TO_DESARROLLO@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9` |
| Tree PR #424 | `530b0a95dda9f81f408ebcb8c177a1ed73afe3e3` |
| PR #425 gobierno ARCH | `MERGED_TO_DESARROLLO@4cce43a743de5860c4da86eecf1782efab91d26b` |
| Tree PR #425 | `ac16b545b74a03b149aac538062def20101187fb` |
| Digest WP-GOV-ARCH-001 consumido | `df48d75129cfe2ba8971f55573a597ca47fb0e3c20e11a3a6a63377349be44e1` |
| PR #426 gobierno HOM | `MERGED_TO_DESARROLLO@fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1` |
| Tree PR #426 | `5e7d087ac45457264ea29dfc1aa7373efd909290` |
| Digest WP-GOV-HOM-001 consumido | `aa9d19408c2750925f5824cdfcc3793e7aca1f38f8d95b8f9c57426139989e7e` |
| PR #427 gobierno CI/review | `MERGED_TO_DESARROLLO@b878c5764e55cb2646b60c4777e363489fe48e8b` |
| Tree PR #427 | `174c18efd840fff6ce27fce9fe1dc4edcd65abe8` |
| PR #428 O2 GOV-HOM | `FAILED_NOT_MERGED`, `O2_CONSUMED_BY_FAILURE` |
| Certificacion pendiente GOV-HOM | `certificacion@fe7b27abf18c096f674948b4f30f815aea4aef08` |
| Main pendiente GOV-HOM | `main@9b486146962bd2a092acfd649fdcf716e922de89` |
| Preservacion F10.10 | `VERIFIED`, manifest `e15e89d0b5abb10980cba41bf3afe6ce6d530ce00a8544d2fc3318ec4b81a689` |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-002](hitos/hito_002.md).
- Tarea: [TASK-H2-001](backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md).
- Subfase tecnica activa: `F10.11`.
- Work package activo: `WP-H2-001`.
- Work package aprobado: `WP-H2-001=ACTIVE_R1`.
- Work packages de gobierno ejecutados R2: [WP-GOV-OBS-001](work_packages/WP-GOV-OBS-001.json), [WP-GOV-INFRA-001](work_packages/WP-GOV-INFRA-001.json).
- Work package de arquitectura consumido externamente: [WP-GOV-ARCH-001](work_packages/WP-GOV-ARCH-001.json), digest `df48d75129cfe2ba8971f55573a597ca47fb0e3c20e11a3a6a63377349be44e1`, PR #425.
- Work package de homologacion consumido: [WP-GOV-HOM-001](work_packages/WP-GOV-HOM-001.json), digest `aa9d19408c2750925f5824cdfcc3793e7aca1f38f8d95b8f9c57426139989e7e`, PR #426.
- Work package de CI/review consumido: [WP-GOV-CI-001](work_packages/WP-GOV-CI-001.json), PR #427.
- Work package de boundary promocion candidate: [WP-GOV-CI-002](work_packages/WP-GOV-CI-002.json).
- Gate homologacion completado: `O0_O5_D0_D10_COMPLETED_HOMOLOGATED`.
- Checkout limpio: `VERIFIED`.
- Lifecycle stage: `ACTIVE`.
- Gate status: `APPROVED_R1`.
- Implementation status: `BLOCKED_PENDING_HOMOLOGATION_AND_REBASE`.
- Criteria status: `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED`.
- Acceptance status: `NOT_STARTED`.
- Etapa 1 Obsidian: `DESARROLLO_MERGED_PENDING_HOMOLOGATION`.
- Proximo gate unico: `PREPARE_WP_GOV_CI_002_R2_APPROVAL`.

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | `TASK-H1-001` |
| `HITO-002` | `ACTIVE_R1_BLOCKED_PENDING_HOMOLOGATION_AND_REBASE` | `TASK-H2-001` |
| `HITO-003` | `PENDING` | `TASK-H3-001` |
| `HITO-004` | `PENDING` | `TASK-H4-001` |
| `HITO-005` | `PENDING` | `TASK-H5-001` |

## Homologacion

| Etapa | Estado | Evidencia |
|---|---|---|
| O1 `candidate -> desarrollo` | `COMPLETED` | PR #414 mergeado; luego PR #415 reconciliacion post-O1 |
| O2 `desarrollo -> certificacion` | `COMPLETED` | PR #416 mergeado con commit `4e7e41a9fac08e657308849701b4b1f70b994e3b` |
| D0-D10 conformidad documental y gobierno | `COMPLETED` | PR #417 mergeado a `desarrollo`; PR #418/#420 re-O2 a `certificacion` |
| O3 `certificacion -> main` | `COMPLETED` | PR #421 mergeado a `main` |
| O4 `main -> certificacion` | `COMPLETED` | PR #422 mergeado a `certificacion` |
| O5 `certificacion -> desarrollo` | `COMPLETED` | PR #423 mergeado a `desarrollo`; checkout limpio verificado |
| R2 GOV OBS/INFRA | `MERGED_TO_DESARROLLO` | PR #424 mergeado a `desarrollo@96c6e7e97a1a6c703eb3b5a3a22f6f6d21aa28e9`; CI verde y review humano |
| R2 GOV ARCH | `MERGED_TO_DESARROLLO` | PR #425 mergeado a `desarrollo@4cce43a743de5860c4da86eecf1782efab91d26b`; tree `ac16b545b74a03b149aac538062def20101187fb`, Governance Preflight PASS, security-audit PASS y review humano por digest |
| R2 GOV HOM | `MERGED_TO_DESARROLLO` | PR #426 mergeado a `desarrollo@fddb9cea6ac44a1f7f7b31e93a7b2f2cc0eeacd1`; tree `5e7d087ac45457264ea29dfc1aa7373efd909290`, Governance Preflight PASS, security-audit PASS y review humano por digest |
| R2 GOV CI/review | `MERGED_TO_DESARROLLO` | PR #427 mergeado a `desarrollo@b878c5764e55cb2646b60c4777e363489fe48e8b`; tree `174c18efd840fff6ce27fce9fe1dc4edcd65abe8`, security-audit PASS y review humano por digest |
| O2 GOV-HOM retry | `FAILED_NOT_MERGED` | PR #428 fallo `Canonical Path Boundary`; `O2_CONSUMED_BY_FAILURE`, sin retry autorizado |
| Etapa 1 Obsidian | `DESARROLLO_MERGED_PENDING_HOMOLOGATION` | El bundle documental existe en `desarrollo`; cierre efectivo requiere candidate `WP-GOV-CI-002`, R2 a `desarrollo`, nuevo O2 R3 JIT y convergencia de trees |

## Alcance Inmediato

PR #427 publico GOV-CI en `desarrollo@b878c5764e55cb2646b60c4777e363489fe48e8b` con tree `174c18efd840fff6ce27fce9fe1dc4edcd65abe8`. PR #428 intento O2 pero fallo `Canonical Path Boundary`; el grant O2 quedo `O2_CONSUMED_BY_FAILURE`, sin retry autorizado. `WP-GOV-ARCH-001`, `WP-GOV-HOM-001` y `WP-GOV-CI-001` quedan consumidos externamente; no deben mutarse como artifacts firmados. Antes de solicitar nuevo O2, `WP-GOV-CI-002` debe separar boundary incremental y boundary estructural de promocion. Hito 2 conserva `WP-H2-001` activo hasta R1, sin implementacion iniciada.

## Siguiente Gate

El unico siguiente gate es `PREPARE_WP_GOV_CI_002_R2_APPROVAL`. Ese gate debe emitir una aprobacion humana por digest para `WP-GOV-CI-002` hasta R2, limitada a push, PR y merge a `desarrollo` del candidate local que agrega boundary estructural para promociones O2-O5. Certification, Main, DDL/DML remoto, Supabase, backfill remoto, RLS/grants remotos, writers, schedules, produccion y cualquier R3 requieren grants JIT single-use separados.

## Predicado Externo De Cierre F10.11

F10.11 queda cerrada solo cuando todos estos predicados sean verdaderos:

1. `WP-GOV-HOM-001`, `WP-GOV-CI-001` y `WP-GOV-CI-002` fueron aprobados y consumidos hasta R2 en `desarrollo`.
2. Los grants R3 `O2`, `O3`, `O4` y `O5` fueron emitidos JIT, consumidos una sola vez y registrados.
3. `tree(main) == tree(certificacion) == tree(desarrollo) == T_HOM`.
4. `main` es ancestro de `certificacion`.
5. `certificacion` es ancestro de `desarrollo`.
6. DB Sync reporto cero cambios y cero apply.
7. No hubo writers, schedules, DDL/DML, Supabase, backfill, RLS/grants ni deploy manual no autorizado.
8. El checkout ordinario consumio el `desarrollo` final homologado.
