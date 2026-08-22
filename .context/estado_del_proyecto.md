# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-21-OBS-CANDIDATE-PENDING-MAIN`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Cierre contractual, homologacion canonica y Obsidian Sprint 1 | `HOMOLOGATED_OBSIDIAN_PENDING_MAIN` | O0-O5 y D0-D10 completados; documentacion Obsidian existe como candidate local pendiente de main. |
| `F11` | Cierre fisico legacy | `SUPERSEDED_BY_F10_11` | Cualquier limpieza fisica futura requiere autorizacion separada. |
| `F12` | Implementacion local Sprint 1 posterior a F10 | `BLOCKED_BY_OBSIDIAN_MAIN` | Macrofase futura H2-H5 gobernada por WP/digest; no ejecutable hasta cierre efectivo en main. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 es el cutoff contractual de Hito 1. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Evidencia tecnica historica preservada; no ejecutable. |
| `F10.9` | `SUPERSEDED_BY_O0_B` | WP2B queda superseded; PR #413 cerrado sin merge y excluido. |
| `F10.10` | `HISTORICAL_NON_PROMOTABLE` | M3 reader/DDL queda congelado; no autoriza DDL/DML ni payloads. |
| `F10.11` | `HOMOLOGATED_OBSIDIAN_PENDING_MAIN` | O0-O5 completados; paquete correctivo D0-D10 homologado; cierre Obsidian pendiente de main. |

## Subfases F12

| ID | Estado | Identidad vigente |
|---|---|---|
| `F12.1` | `BLOCKED_BY_OBSIDIAN_MAIN` | Hito 2 CA2 - contrato editorial y calidad; bloqueado hasta documentacion Obsidian en main y checkout ordinario actualizado. |
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
| Preservacion F10.10 | `VERIFIED`, manifest `e15e89d0b5abb10980cba41bf3afe6ce6d530ce00a8544d2fc3318ec4b81a689` |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-002](hitos/hito_002.md).
- Tarea: [TASK-H2-001](backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md).
- Subfase tecnica activa: `F10.11`.
- Work package activo: `WP-H2-001`.
- Work package aprobado: `WP-H2-001=ACTIVE_R1`.
- Work package de gobierno candidato: [WP-GOV-OBS-001](work_packages/WP-GOV-OBS-001.json).
- Gate homologacion completado: `O0_O5_D0_D10_COMPLETED_HOMOLOGATED`.
- Checkout limpio: `VERIFIED`.
- Lifecycle stage: `ACTIVE`.
- Gate status: `APPROVED_R1`.
- Implementation status: `BLOCKED_PENDING_OBSIDIAN_MAIN`.
- Criteria status: `H2-CA2=NOT_STARTED`, `H2-CA3=NOT_STARTED`.
- Acceptance status: `NOT_STARTED`.
- Etapa 1 Obsidian: `LOCAL_CANDIDATE_PENDING_MAIN`.
- Proximo gate unico: `PREPARE_WP_GOV_OBS_R2_APPROVAL`.

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | `TASK-H1-001` |
| `HITO-002` | `ACTIVE_R1_BLOCKED_PENDING_OBSIDIAN_MAIN` | `TASK-H2-001` |
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
| Etapa 1 Obsidian | `LOCAL_CANDIDATE_PENDING_MAIN` | Indice, evidencias, taxonomia y Context Graph existen localmente; cierre efectivo requiere main, homologacion y checkout ordinario actualizado |

## Alcance Inmediato

La homologacion canonica F10.11 esta completada. `main`, `certificacion` y
`desarrollo` comparten el tree `fcb59095e48441bb4486ccc196aee61e2e1e0fe3`.
El checkout objetivo esta limpio en `desarrollo@974f9d4bde6d79230afde5c5a86ba7a3894233c6`.
Hito 2 tiene `WP-H2-001` activo hasta R1, sin implementacion iniciada. La traza futura `F12.1` queda bloqueada hasta que la documentacion Obsidian canonica exista en main, se homologue hacia certificacion/desarrollo y el checkout ordinario StudIAMatch consuma ese estado.

## Siguiente Gate

El unico siguiente gate es `PREPARE_WP_GOV_OBS_R2_APPROVAL`. Ese gate debe emitir
una aprobacion humana por digest para `WP-GOV-OBS-001` hasta R2, limitada a push,
PR y merge a `desarrollo`. Certification, Main, DDL/DML remoto, Supabase,
backfill remoto, RLS/grants remotos, writers, schedules, produccion y cualquier
R3 requieren grants JIT separados.
