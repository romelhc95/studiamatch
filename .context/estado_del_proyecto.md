# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-08-27-F11-H2-PRO-APPLY-DONE-VERIFY-PENDING`.

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Pilares Transversales Obligatorios

Todo desarrollo futuro del producto debe preservar continuamente funcionalidad,
escalabilidad, seguridad, mantenimiento, calidad y rendimiento. Ningun hito, task o
requerimiento puede cerrarse sin validar estas premisas frente al alcance
ejecutado.

Para cualquier nuevo desarrollo con requerimiento cliente, antes de iniciar y al cerrar un hito o task vinculado a un requerimiento se debe validar criterios de aceptacion contra el documento privado del cliente mediante atestacion sanitizada versionada.
El documento privado no se versiona y no se expone en PRs;
la evidencia versionada solo registra el identificador de fuente, resultado y
trazabilidad.
Si este gate documental falla, no se puede ejecutar codigo, DB, UI, pipeline ni
PR del hito siguiente hasta corregir la atestacion sanitizada.

Todo cambio funcional, DB, UI, pipeline o despliegue debe incluir una transicion
transparente obligatoria: `expand -> compatibilidad -> deploy -> contract`.
Durante construccion y promocion se debe preservar el comportamiento legacy
necesario para que la aplicacion siga funcionando; luego de estabilizar en
produccion se debe retirar la funcionalidad legacy y dejar activo el nuevo
contrato solicitado. Ningun hito, task o PR puede cerrarse ni promoverse sin
documentar compatibilidad, contraccion, rollback y evidencia de no degradacion
funcional.

Todo prompt futuro de desarrollo queda bajo `PROMPT_RETROALIMENTADO_REQUIRED`
segun [Estandar De Prompts Retroalimentados](operaciones/estandar_prompts_retroalimentados.md).
Un prompt retroalimentado mantiene un ciclo de analizar, implementar, validar,
revisar, convertir cada fallo, hallazgo, drift o gate incompleto en tareas,
corregir y revalidar hasta cumplir sus criterios de GO. No se declara GO por
intencion, implementacion parcial o pruebas locales cuando el alcance exige
evidencia remota. Si se requiere JIT, push, PR, merge, deploy,
workflow_dispatch, Supabase writes, ramas protegidas o acciones destructivas,
la ejecucion se detiene y se pide aprobacion humana separada con opciones
concretas, recomendacion y consecuencias. Cada aprobacion recibida obliga a
reevaluar estado, actualizar el plan y continuar desde el gate detenido. El
cierre exige evidencia canonica, criterios cliente, pruebas completas,
revisiones especializadas y ausencia de hallazgos HIGH/CRITICAL. No se pueden
ocultar fallos como historicos o fuera de alcance sin demostrar baseline; cada
waiver requiere causa, evidencia reproducible, owner, riesgo, vencimiento y
aprobacion humana.

Todo PR debe usar la plantilla versionada `.github/pull_request_template.md`.
Antes de abrir o actualizar un PR se deben ejecutar las validaciones necesarias
para completar sus secciones con resultados reales. La plantilla no se llena con
intenciones, placeholders ni omisiones silenciosas; toda validacion no aplicable
o pendiente debe indicar causa, riesgo residual y owner.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Redefinicion de flujo simple | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Flujo simplificado validado en `desarrollo`, `certificacion` y `main`; preservado como historia no ejecutable. |
| `F11` | Activacion documental del nuevo pedido | `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED` | H2 compat fue aprobado y mergeado a `certificacion` por PR #467 en `2d499324bb21e750d9bc7c94cb80e7a193062b50`; Cloudflare `4cc2e34c`, CI verde y smoke post-merge estable. Forward-fix de endpoint Security Advisor (PR #477), ajuste de RLS para cohorte privada (PR #478) y correccion del workflow `DB Sync to Production` para verificacion post-apply (PRs #480/#481) ya estan integrados. El apply de `h2-expand-compat` en Pro fue completado de forma aditiva con backup/PITR verificado; promocion a `main` queda en `NO-GO` hasta generar el artifact de verificacion H2 (`DB Sync to Production` con `operation=verify` sobre `certificacion`) y validar `expand + compatibilidad`. |

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
- Gate vigente: `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED`.
- Proximo gate unico: `PRODUCTION_REMEDIATION_PRO_EXPAND_COMPAT_BEFORE_MAIN`.

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `REDEFINED_ACTIVE_AFTER_H2_H3` | `TASK-H1-001` |
| `HITO-002` | `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED` | `TASK-H2-001` |
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
| CI/CD DB Sync Pro | `H2_VERIFY_NO_OP_APPLY_GATE_FIXED` | Workflow `db-sync-to-pro.yml` ajustado en PRs #480/#481 para que el job `Apply pending migrations` tenga exito como no-op bajo `operation=verify` cuando no hay migraciones pendientes, permitiendo generar el artifact H2 requerido por `security-audit`. |
| Base de datos | `PRO_EXPAND_APPLIED_VERIFY_PENDING` | DDL Free inicial, forward-fix, remediacion Security Advisor, backfill editorial, seed, fix de vista y compatibilidad legacy aplicados/verificados en Supabase Free. El apply del manifiesto `h2-expand-compat` fue ejecutado en Pro de forma aditiva con backup/PITR verificado; baseline elegible productivo `224`. Pendiente ejecutar `DB Sync to Production` con `operation=verify` sobre `certificacion` para generar el artifact H2 y validar advisors sin hallazgos HIGH/CRITICAL. |
| Evidencia cliente | `GRADE_A_CLIENT_SOURCE_VALIDATED_H2_CERTIFICACION` | Acta ejecutiva y matriz H2 con veredicto, metricas verificables, validacion contra `SRC-REQ-002` via adenda sanitizada, PRs #458/#459/#460 mergeados y QA read-only definida. |
| QA certificacion previa | `PASS_CERTIFICATION_READ_ONLY_QA` | [QA H2/H3 read-only](operaciones/h2_h3_certification_readonly_qa.md) ejecutada antes de la compatibilidad legacy: suite `108 passed`, build/static smoke PASS, vista publica sin privados y advisors sin bloqueantes H2. |
| Compatibilidad Desarrollo | `MERGED_TO_DESARROLLO_READY_FOR_CERTIFICATION_PROMOTION` | PR #466 mergeado a `desarrollo` en `e8376035d8d5c3e1b7893cbb1ede14f735ccd05d`; post-apply Free: `227` cursos legacy elegibles, `227` en cohorte, `227` en `courses_public_effective`, `0` faltantes y `0` inesperados. Preview final `af2ac376` valida Home, detalle, comparador, HTML inicial correcto, bundle sin `ratings`/`reviews` y rutas relacionadas `200`. |
| Compatibilidad Certificacion | `MERGED_AND_DEPLOYED_STABLE` | PR #467 mergeado a `certificacion` en `2d499324bb21e750d9bc7c94cb80e7a193062b50`; deployment `4cc2e34c`; checks verdes; host `https://certificacion.studiamatch-aty.pages.dev/` con Home, detalle y comparador `200`. |
| Remediacion productiva | `PLAN_IMPLEMENTED_LOCALLY_NO_PRO_APPLY_NO_MAIN_PROMOTION` | [Plan De Remediacion Productiva H2](operaciones/h2_production_remediation_plan.md) define `expand -> compatibilidad -> deploy -> contract`, baseline Pro `224`, migraciones Pro separadas, manifiestos cerrados en DB Sync y gates previos a `main`. |

## Alcance Inmediato

El alcance inmediato es versionar la remediacion productiva H2 y habilitar el
flujo protegido hacia `main` sin ejecutarlo. Pro, `main`, writers, schedules,
deploys manuales o DML adicional requieren aprobacion JIT separada. La secuencia
obligatoria para produccion es expandir y verificar Pro antes del deploy frontend.
`web/**`, `db/**`, `supabase/**`, `scripts/core/**`, `scripts/shared/**`,
`scripts/maintenance/**`, `config/**`, dependencias y Docker permanecen protegidos
salvo autorizacion separada. H2 fue mergeado por PR #458 a `desarrollo`, PR #459
agrego gate documental post-merge y PR #460 lo promovio a `certificacion`, todos
con CI verde. Forward-fix, remediacion Security Advisor, backfill editorial,
seed, fix de vista publica y compatibilidad legacy aplicados/verificados en
Supabase Free. La web real de Certificacion muestra cursos reales; la limpieza de
calidad quedo validada remotamente en preview Cloudflare `4cc2e34c`. Pro, writer,
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

El siguiente gate es `PRODUCTION_REMEDIATION_PRO_EXPAND_COMPAT_BEFORE_MAIN`:
generar la evidencia canonica de verificacion H2 en Pro ejecutando
`DB Sync to Production` con `operation=verify` sobre `certificacion`,
confirmar advisors sin hallazgos HIGH/CRITICAL, versionar
`.context/operaciones/h2_main_production_expand_evidence.json` y abrir el PR
`certificacion -> main`. Solo con el gate `H2 Main Production Expand Gate`
verde se autoriza el merge a `main`. Pro, writers, schedules, produccion,
deploys manuales y cambios remotos adicionales siguen bloqueados sin JIT
separada.
