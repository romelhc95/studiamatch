# Flujo De Requerimientos

Este flujo describe la trazabilidad documental minima desde la solicitud hasta el release. No define automatizacion, componentes ejecutables ni una maquina de estados.

| Etapa | Entrada | Salida | Nota canonica | Autoridad | Transicion | Trazabilidad |
|---|---|---|---|---|---|---|
| Intake | Necesidad expresada | Requerimiento identificable | [Indice canonico](../00_INDICE.md) | Decision humana sobre incorporacion | Intake -> Estimacion | ID `REQ-*` |
| Estimacion | Requerimiento identificable | Contrato, alcance y esfuerzo estimados | [EST-001](../estimaciones/est_001.md) | Estimacion aceptada del requerimiento | Estimacion -> Aprobacion | `REQ-EST-001` |
| Aprobacion | Estimacion revisada | Alcance autorizado | [EST-001](../estimaciones/est_001.md) y ADR cuando corresponda | Aprobacion humana explicita | Aprobacion -> Tarea | `REQ-EST-001` -> `HITO-001` |
| Tarea | Alcance autorizado | Tarea y criterios trazables | [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) | Tarea para estado vivo; requerimiento para contrato | Tarea -> Validacion | `HITO-001` -> `TASK-H1-001` -> `H1-CA*` |
| Validacion | Entregables de la tarea | Resultado verificable por criterio | Tarea canonica y documentos tecnicos enlazados | Verificacion aplicable a cada criterio | Validacion -> Release | Criterio -> verificacion -> evidencia enlazada |
| Release | Criterios validados y gates aprobados | Promocion autorizada | [Flujo de release minimo](./flujo_release_minimo.md) | Gates tecnicos y aprobacion humana | Release -> registro historico | Requerimiento -> tarea -> validacion -> release -> changelog |

## Reglas De Paso

- Ninguna etapa crea alcance o criterios fuera del requerimiento aceptado.
- La aprobacion humana habilita la transicion aplicable; un documento por si solo no autoriza ejecucion.
- La tarea conserva su estado vivo y enlaza la verificacion sin incrustar artifacts externos.
- El release sigue su flujo canonico y el changelog registra el resultado sin adquirir autoridad vigente.
