# Backlog — req_hito_1_rework_20260721

## Contexto
- **Estimacion de referencia:** [[../../estimaciones/est_001]]
- **Evaluacion origen:** [[../../operaciones/evaluacion_prs_cancelados_hito1_20260721]]
- **Decision:** Hito 1 se reimplementa desde `origin/desarrollo` vigente; no se mergean PRs antiguos.

## Hitos
| Hito | Paquete | CAs | Tarea | Ventana | Despliegue |
|---|---|---|---|---|---|
| Hito 1 Rework | Gobernanza y alcance | CA1, CA2 parcial, CA7 preparacion | [[tarea_001_rescatar_gobernanza_hito_1]] | Por definir | Por definir |
| Hito 1 Rework | Pipeline/orquestacion | CA1, CA2 parcial | [[tarea_002_reimplementar_controles_pipeline_hito_1]] | Por definir | Por definir |
| Hito 1 Rework | DB/RLS/contrato editorial | CA1, CA7 preparacion | [[tarea_003_reimplementar_contrato_db_rls_hito_1]] | Por definir | Por definir |
| Hito 1 Rework | QA/evidencia/cierre | CA1, CA2 parcial, CA7 preparacion | [[tarea_004_regenerar_evidencia_y_gate_hito_1]] | Por definir | Por definir |
| Post-Hito 1 | Promocion a certificacion | Gate SDLC | [[tarea_005_regenerar_promocion_certificacion_hito_1]] | Posterior a merge en desarrollo | Por definir |

## Advertencia De Gate
Los valores `Por definir` no satisfacen gates de cierre/release; deben reemplazarse por metadata aprobada antes de cierre.

## Tareas
- [[tarea_001_rescatar_gobernanza_hito_1]]
- [[tarea_002_reimplementar_controles_pipeline_hito_1]]
- [[tarea_003_reimplementar_contrato_db_rls_hito_1]]
- [[tarea_004_regenerar_evidencia_y_gate_hito_1]]
- [[tarea_005_regenerar_promocion_certificacion_hito_1]]

## PRs Cerrados Relacionados
- #202 — No mergear; usar solo como referencia historica de gobernanza.
- #203 — No mergear; reimplementar funcionalidad en tareas nuevas.
- #207 — No mergear; regenerar promocion al final.
- #47 — Cerrado y excluido del remapeo.

## Reglas
- Este directorio contiene solo tareas del requerimiento `req_hito_1_rework_20260721`.
- No mezclar cambios funcionales con promocion a `certificacion`.
- Cada tarea debe ejecutarse en rama nueva desde `origin/desarrollo` vigente.
- Ejecutar `validate_context_graph.py` si se modifica `.context`.
