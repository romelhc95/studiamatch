# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-25-F11-DOC-AUTHORITY-ACTIVE`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Redefinicion de flujo simple | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Flujo simplificado validado en `desarrollo`, `certificacion` y `main`; preservado como historia no ejecutable. |
| `F11` | Activacion documental del nuevo pedido | `DOCUMENTATION_AUTHORITY_ACTIVE_DB_BLOCKED` | GO documental recibido; `REDEFINICION.md` eliminado; autoridad exclusiva en `AGENTS.md` y Obsidian `.context/**`. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 es el cutoff contractual de Hito 1. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Evidencia tecnica historica preservada; no ejecutable. |
| `F10.9` | `SUPERSEDED_BY_O0_B` | WP2B queda superseded; PR #413 cerrado sin merge y excluido. |
| `F10.10` | `HISTORICAL_NON_PROMOTABLE` | M3 reader/DDL queda congelado; no autoriza DDL/DML ni payloads. |
| `F10.11` | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Reemplaza WP/digest/Context Graph por flujo simple protegido; el soporte temporal fue retirado al recibir GO documental. |

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

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-001](hitos/hito_001.md).
- Tarea: [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).
- Subfase tecnica activa: `F11`.
- Work package activo: `NONE_SUPERSEDED`.
- Work package completado: `NONE_APPLICABLE`.
- Gate vigente: `DOCUMENTATION_AUTHORITY_ACTIVE_DB_BLOCKED`.
- Proximo gate unico: `PR_DOCUMENTAL_A_DESARROLLO`.

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `REDEFINED_ACTIVE_AFTER_H2_H3` | `TASK-H1-001` |
| `HITO-002` | `NEXT_ACTIVE_SCOPE_PENDING_PR_AND_JIT_DB` | `TASK-H2-001` |
| `HITO-003` | `PLANNED_AFTER_H2_ACCEPTED` | `TASK-H3-001` |
| `HITO-004` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | `TASK-H4-001` |
| `HITO-005` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | `TASK-H5-001` |

## Activacion Documental

| Etapa | Estado | Evidencia |
|---|---|---|
| Baseline local | `COMPLETED` | `origin/main@9b486146962bd2a092acfd649fdcf716e922de89` |
| WIP previo | `DISCARDED_BY_AUTHORIZATION` | No se preserva WIP fuera del baseline. |
| Flujo simple | `DEPLOYED_TO_MAIN` | PR #451 a `desarrollo`, PR #452 a `certificacion`, PR #453 a `main`. |
| GO documental | `RECEIVED` | Pedido humano: aplicar actualizacion documental completa y retirar soporte temporal. |
| Soporte temporal raiz | `REMOVED` | `REDEFINICION.md` eliminado definitivamente; no debe recrearse. |
| Plan vinculante | `MOVED_TO_OBSIDIAN` | [Plan vinculante nuevo pedido](operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md). |
| Acciones remotas | `FLOW_NORMALIZED` | Nuevos cambios siguen PR protegido `desarrollo -> certificacion -> main`. |
| Base de datos | `BLOCKED` | Sin DDL, DML, Supabase MCP ni DB Sync apply. |

## Alcance Inmediato

El alcance inmediato es documental: consolidar autoridad en `AGENTS.md` y Obsidian,
eliminar el soporte temporal raiz y preparar el PR documental hacia `desarrollo`.
`web/**`, `db/**`, `supabase/**`, `scripts/core/**`, `scripts/shared/**`,
`scripts/maintenance/**`, `config/**`, dependencias y Docker permanecen protegidos
salvo autorizacion separada. H2 queda como siguiente alcance tecnico, pero cualquier
DDL/DML, Supabase, writer o backfill requiere aprobacion JIT separada.

## Orden Vinculante Nuevo Pedido

```text
Intake documental
-> H2 Modelo editorial y pipeline tolerante a incompletos
-> H3 Administracion editorial autenticada
-> H1 Automatizacion segura y reactivacion gradual
-> H4 Home publica y documentacion tecnica
-> H5 Resultados publicos, filtros y cards
```

## Siguiente Gate

El siguiente gate es abrir PR documental protegido hacia `desarrollo` con las
validaciones de seguridad aplicables. Despues, H2 puede planificarse como PR
separado, pero DB, Supabase, writers, schedules, produccion, deploys y cambios
remotos siguen bloqueados hasta aprobacion JIT separada.
