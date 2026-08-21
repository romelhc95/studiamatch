# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-20-F10.11-CANONICAL-REBASELINE`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Cierre contractual y homologacion canonica Sprint 1 | `ACTIVE_CANONICAL_REBASELINE` | Etapa 1 documental/canonica en ejecucion local sobre `TECH_BASE`. |
| `F11` | Cierre fisico legacy | `SUPERSEDED_BY_F10_11` | Cualquier limpieza fisica futura requiere autorizacion separada. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 es el cutoff contractual de Hito 1. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Evidencia tecnica historica preservada; no ejecutable. |
| `F10.9` | `SUPERSEDED_BY_O0_B` | WP2B queda superseded; PR #413 cerrado sin merge y excluido. |
| `F10.10` | `HISTORICAL_NON_PROMOTABLE` | M3 reader/DDL queda congelado; no autoriza DDL/DML ni payloads. |
| `F10.11` | `ACTIVE_CANONICAL_REBASELINE` | Work package `WP-O0-A` completado read-only; prepara `T_CANONICO`. |

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

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase tecnica activa: `F10.11`.
- Work package activo: `NONE`.
- Work package completado: `WP-O0-A=COMPLETED_READ_ONLY`.

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | `TASK-H1-001` |
| `HITO-002` | `READY_AWAITING_WP_APPROVAL` | `TASK-H2-001` |
| `HITO-003` | `PENDING` | `TASK-H3-001` |
| `HITO-004` | `PENDING` | `TASK-H4-001` |
| `HITO-005` | `PENDING` | `TASK-H5-001` |

## Alcance Inmediato

La unica ejecucion autorizada en `F10.11` es la Etapa 1 documental y canonica:
crear `T_CANONICO = TECH_BASE + PATCH_CANONICO`, sin activar Hito 2, sin PR, sin
push del candidate y sin cambios en `web/**` ni `db/**`.

## Siguiente Gate

Despues de la Etapa 1 local se requiere decision humana separada para crear PR de
homologacion hacia `desarrollo`. Hito 2 solo inicia tras homologacion y aprobacion
explicita de `WP-H2-001` por digest.
