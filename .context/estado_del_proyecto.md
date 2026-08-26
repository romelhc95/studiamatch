# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-26-F11-H2-MERGED-CERTIFICACION`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Pilares Transversales Obligatorios

Todo desarrollo futuro del producto debe preservar continuamente escalabilidad,
seguridad, mantenimiento, calidad y rendimiento. Ningun hito, task o
requerimiento puede cerrarse sin validar estas premisas frente al alcance
ejecutado.

Todo cierre de hito o task vinculado a un requerimiento debe validar criterios de aceptacion contra el documento privado del cliente mediante atestacion sanitizada versionada.
El documento privado no se versiona y no se expone en PRs;
la evidencia versionada solo registra el identificador de fuente, resultado y
trazabilidad.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Redefinicion de flujo simple | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Flujo simplificado validado en `desarrollo`, `certificacion` y `main`; preservado como historia no ejecutable. |
| `F11` | Activacion documental del nuevo pedido | `H2_MERGED_TO_CERTIFICACION_CI_GREEN` | H2 Free aplicado/verificado; PR #458 mergeado a `desarrollo`, PR #459 gate documental mergeado y PR #460 mergeado a `certificacion` con checks verdes; autoridad exclusiva en `AGENTS.md` y Obsidian `.context/**`. |

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
- Hito: [HITO-002](hitos/hito_002.md).
- Tarea: [TASK-H2-001](backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md).
- Subfase tecnica activa: `F11`.
- Work package activo: `NONE_SUPERSEDED`.
- Work package completado: `NONE_APPLICABLE`.
- Gate vigente: `H2_MERGED_TO_CERTIFICACION_CI_GREEN`.
- Proximo gate unico: `CERTIFICATION_QA_H2_READ_ONLY`.

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `REDEFINED_ACTIVE_AFTER_H2_H3` | `TASK-H1-001` |
| `HITO-002` | `MERGED_TO_CERTIFICACION_CI_GREEN` | `TASK-H2-001` |
| `HITO-003` | `NEXT_AFTER_H2_CERTIFICATION_QA` | `TASK-H3-001` |
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
| Base de datos | `FREE_H2_DDL_DML_PUBLIC_SURFACE_VALIDATED` | DDL Free inicial, forward-fix, remediacion Security Advisor, backfill editorial, seed `editorial_field_definitions` y fix `20260826_h2_public_effective_view_public_fields_fix.sql` aplicados/verificados en Supabase Free. Pro, writers, schedules y DB Sync siguen bloqueados. |
| Evidencia cliente | `GRADE_A_CLIENT_SOURCE_VALIDATED_H2_CERTIFICACION` | Acta ejecutiva y matriz H2 con veredicto, metricas verificables, validacion contra `SRC-REQ-002` via adenda sanitizada y PRs #458/#459/#460 mergeados. |

## Alcance Inmediato

El alcance inmediato es ejecutar QA read-only de H2 en `certificacion` bajo
instruccion humana separada.
`web/**`, `db/**`, `supabase/**`, `scripts/core/**`, `scripts/shared/**`,
`scripts/maintenance/**`, `config/**`, dependencias y Docker permanecen protegidos
salvo autorizacion separada. H2 fue mergeado por PR #458 a `desarrollo`, PR #459
agrego gate documental post-merge y PR #460 lo promovio a `certificacion`, todos
con CI verde. Forward-fix, remediacion Security Advisor, backfill editorial,
seed y fix de vista publica aplicados/verificados en Supabase Free. Pro, writer,
schedule o nueva accion remota requiere aprobacion JIT separada.

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

El siguiente gate es QA read-only de H2 en `certificacion` cuando exista
instruccion humana separada. Pro, writers, schedules, produccion, deploys y
cambios remotos adicionales siguen bloqueados.
