# Evaluacion De PRs Cancelados Para Rehacer Hito 1

## Decision
Se cerraron los PRs abiertos que no deben usarse como base directa de merge y se remapearon sus aprendizajes a un backlog nuevo contra `origin/desarrollo` vigente.

## Alcance
- Incluidos en evaluacion: PR #202, PR #203 y PR #207.
- Excluido por instruccion: PR #47. Cerrado y no considerado para remapeo.
- Fuente de verdad posterior: [[../backlog_tareas/req_hito_1_rework_20260721/_index]].
- Base de reconstruccion: `origin/desarrollo` posterior a PR #212 y PR #211.

## Resultado Por PR
| PR | Estado aplicado | Evaluacion | Decision |
|---|---|---|---|
| #202 `docs: add governed hito close workflow` | Cerrado | Aporta conceptos de gate mecanico, matrices CA y reporte QA, pero esta contaminado por normalizacion masiva y cambios ya superseded por PR #208 a #212. | No mergear. Rescatar solo requisitos de gobernanza en [[../backlog_tareas/req_hito_1_rework_20260721/tarea_001_rescatar_gobernanza_hito_1]]. |
| #203 `feat: implement HITO 1 foundation controls` | Cerrado | Contiene la mayor parte funcional de Hito 1: FG3 manual-only, discovery-only, elegibilidad/circuit breaker, contrato editorial/calidad/patrocinio, RLS y evidencias. Estaba apilado sobre #202 y no debe mergearse directo. | Rehacer desde `desarrollo` actual dividido en tareas tecnicas. |
| #207 `chore(release): promote pre-hito1 package to certification` | Cerrado | Promocion a `certificacion` generada desde paquete anterior. Quedo invalida tras cambios en `desarrollo`. | No reutilizar. Regenerar promocion solo cuando el nuevo Hito 1 este en `desarrollo`. |
| #47 `Fase 92: Filter Cascading + Counters` | Cerrado | Excluido por instruccion. PR antiguo sin merge base limpio. | No considerar en este remapeo. |

## Hallazgos De Riesgo
| Riesgo | Impacto | Mitigacion |
|---|---|---|
| PRs antiguos arrastran cambios masivos no relacionados | Merge riesgoso y dificil de auditar | Rehacer tareas en rama nueva desde `origin/desarrollo` |
| Hito 1 estaba apilado sobre #202 | Dependencias obsoletas y conflictos probables | Separar gobernanza, pipeline, DB/RLS, QA y promocion |
| Evidencia anterior no esta ligada al commit nuevo | Gate SDLC no puede certificar un cambio reconstruido | Regenerar evidencias JSON/Markdown y checks desde el nuevo PR |
| Promocion #207 apunta a paquete anterior | Certificacion quedaria desalineada con desarrollo | Crear nueva promocion posterior al merge del nuevo Hito 1 |

## Mapeo A Backlog
| Tema rescatado | Origen | Tarea nueva |
|---|---|---|
| Gate mecanico de cierre, matriz CA y reporte QA | #202 | [[../backlog_tareas/req_hito_1_rework_20260721/tarea_001_rescatar_gobernanza_hito_1]] |
| FG3 manual-only, discovery-only y controles de orquestacion | #203 | [[../backlog_tareas/req_hito_1_rework_20260721/tarea_002_reimplementar_controles_pipeline_hito_1]] |
| Contrato editorial/calidad/patrocinio y hardening RLS | #203 | [[../backlog_tareas/req_hito_1_rework_20260721/tarea_003_reimplementar_contrato_db_rls_hito_1]] |
| Evidencia SHA-bound, validaciones y cierre de Hito 1 | #203 | [[../backlog_tareas/req_hito_1_rework_20260721/tarea_004_regenerar_evidencia_y_gate_hito_1]] |
| Promocion a certificacion | #207 | [[../backlog_tareas/req_hito_1_rework_20260721/tarea_005_regenerar_promocion_certificacion_hito_1]] |

## Regla Operativa
No reabrir ni mergear #202, #203, #207 o #47. Cualquier implementacion de Hito 1 debe partir de una rama nueva desde `origin/desarrollo` y usar las tareas del backlog nuevo.
