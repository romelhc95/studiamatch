# ADR-0001 - Autoridad De Fuentes Del Context Graph

| Campo | Valor |
|---|---|
| ID | `ADR-0001` |
| Estado | `ACCEPTED` |
| Decision humana | Aceptada explicitamente |
| Contexto relacionado | [Indice canonico](../00_INDICE.md) |

## Contexto

La documentacion necesita una precedencia unica para evitar que indices, historial o antecedentes contradigan el estado y el contrato vigentes. El plan legacy `../../IMPLEMENTATION_PLAN.md` puede explicar antecedentes, pero esta fuera de la fuente documental canonica.

## Decision

1. `.context/` es la unica fuente documental de verdad.
2. La [matriz de autoridad](../00_INDICE.md#matriz-de-autoridad) asigna una nota canonica a cada materia.
3. El estado vivo se mantiene solo en [Estado del proyecto](../estado_del_proyecto.md) y en la tarea activa.
4. Los hitos e indices no duplican estado; los changelogs no tienen autoridad vigente.
5. El antecedente legacy no es dependencia, no autoriza ejecucion y no resuelve conflictos.
6. Las contradicciones que requieran cambiar autoridad, contrato o alcance exigen una nueva decision humana registrada como ADR.

## Fuentes Autorizadas

| Informacion | Fuente autorizada |
|---|---|
| Alcance aprobado | [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md) |
| Arquitectura decidida | ADR aceptada enlazada desde el [indice de decisiones](./_index.md) |
| Estado de tarea | [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) |
| Estado de proyecto | [Snapshot canonico](../estado_del_proyecto.md) |
| Estado DB aplicado | [Snapshot DB](../sistema_db_supabase.md) y [matriz de adopcion](../operaciones/matriz_adopcion_db.md) |
| Readiness de release | Candidate y gates futuros registrados en `.context/` segun el [flujo minimo](../operaciones/flujo_release_minimo.md) |

## Relacion Con Autoridad Tecnica

Git y las migrations determinan el comportamiento versionado. La observacion remota, el ledger y las postcondiciones determinan el estado DB aplicado. Estas autoridades tecnicas alimentan las notas canonicas del Context Graph y no crean una fuente documental paralela.

## Consecuencias

- El Context Graph tiene un punto de entrada y reglas de precedencia explicitas.
- `REQ-EST-001`, `HITO-001` y `TASK-H1-001` conservan trazabilidad sin ampliar criterios.
- La historia permanece consultable sin competir con el estado vigente.
