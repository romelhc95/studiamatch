# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-21-F10.11-O1-DESARROLLO-MERGED`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Cierre contractual y homologacion canonica Sprint 1 | `ACTIVE_O2_PENDING` | O1 desarrollo completado; pendiente homologacion a certificacion. |
| `F11` | Cierre fisico legacy | `SUPERSEDED_BY_F10_11` | Cualquier limpieza fisica futura requiere autorizacion separada. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 es el cutoff contractual de Hito 1. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Evidencia tecnica historica preservada; no ejecutable. |
| `F10.9` | `SUPERSEDED_BY_O0_B` | WP2B queda superseded; PR #413 cerrado sin merge y excluido. |
| `F10.10` | `HISTORICAL_NON_PROMOTABLE` | M3 reader/DDL queda congelado; no autoriza DDL/DML ni payloads. |
| `F10.11` | `ACTIVE_O2_PENDING` | O1 desarrollo completado; prepara PR protegido hacia certificacion. |

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
| Desarrollo canonico O1 | `desarrollo@864caa29524e2f37ab6951677b3799b1515cf969` |
| Tree canonico O1 | `ac9551128e443d5aa8a9c3401ff5f79b45d9da94` |

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

## Homologacion

| Etapa | Estado | Evidencia |
|---|---|---|
| O1 `candidate -> desarrollo` | `COMPLETED` | PR #414 mergeado con commit `864caa29524e2f37ab6951677b3799b1515cf969` |
| O2 `desarrollo -> certificacion` | `PENDING` | Requiere prompt y PR protegido separado |
| O3 `certificacion -> main` | `PENDING` | Requiere prompt y PR protegido separado |
| O4 `main -> certificacion` | `PENDING` | Requiere prompt y PR protegido separado |
| O5 `certificacion -> desarrollo` | `PENDING` | Requiere prompt y PR protegido separado |

## Alcance Inmediato

La unica ejecucion autorizable siguiente en `F10.11` es preparar O2 mediante PR
protegido hacia `certificacion`, manteniendo `web/**` y `db/**` sin cambios de
producto y sin activar Hito 2.

## Siguiente Gate

Antes de O2 se requiere decision humana separada. Hito 2 solo inicia tras O5,
checkout limpio homologado y aprobacion explicita de `WP-H2-001` por digest.
