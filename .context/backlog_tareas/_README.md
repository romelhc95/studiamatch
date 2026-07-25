# Gobierno Del Backlog

El backlog organiza requerimientos y tareas canonicas sin duplicar estado vivo. Cada tarea debe derivar de un requerimiento aceptado, usar la [plantilla minima](./_plantilla_tarea.md) y quedar enlazada desde su indice de requerimiento.

## Taxonomia Canonica

| Tipo | ID canonico | Proposito | Nota canonica |
|---|---|---|---|
| Intake | `INTAKE-*` | Registrar una solicitud privada pendiente de sanitizacion, estimacion y aprobacion. | Nota propia bajo `backlog_tareas/intake/` |
| Requerimiento | `REQ-EST-001` | Fijar el alcance aprobado y sus criterios sanitizados. | [REQ-EST-001](./req_est_001_sprint_1/_index.md) |
| Hito | `HITO-001` | Agrupar el alcance de Hito 1 sin mantener estado vivo. | [HITO-001](../hitos/hito_001.md) |
| Fase | `FASE-NN` | Identificar una etapa autorizable y su estado vigente. | [Estado del proyecto](../estado_del_proyecto.md) |
| Tarea | `TASK-H1-001` | Ejecutar y mantener el estado del paquete principal de Hito 1. | [TASK-H1-001](./req_est_001_sprint_1/tarea_001_hito_1.md) |
| Criterio | `H1-CA1` | Trazar la orquestacion aceptada dentro de `HITO-001`. | [TASK-H1-001](./req_est_001_sprint_1/tarea_001_hito_1.md#criterios-y-entregables) |
| Criterio parcial | `H1-CA2P` | Trazar el schema y seguridad base aceptados. | [TASK-H1-001](./req_est_001_sprint_1/tarea_001_hito_1.md#criterios-y-entregables) |
| Criterio preparatorio | `H1-CA7P` | Trazar el contrato documental aceptado. | [TASK-H1-001](./req_est_001_sprint_1/tarea_001_hito_1.md#criterios-y-entregables) |
| Decision | `ADR-NNNN` | Registrar una decision humana durable y su razon. | [Indice ADR](../decisiones/_index.md) |
| Snapshot | `SNAPSHOT-YYYY-MM-DD` | Identificar el corte del estado vivo vigente. | [Estado del proyecto](../estado_del_proyecto.md) |
| Changelog | `CHANGELOG-YYYY-MM-DD` | Registrar cambios historicos sin autoridad vigente. | [Changelog](../changelog/2026-07-24.md) |

## Reglas

- El estado vivo del proyecto y las fases reside solo en [Estado del proyecto](../estado_del_proyecto.md).
- El estado vivo de una tarea y sus criterios reside solo en su nota canonica.
- Los indices y los hitos enlazan alcance, pero no replican estados.
- Una tarea no crea criterios que no existan en el requerimiento aceptado.
- `TASK-H1-001` es la tarea principal de `HITO-001` y no tiene subtareas.
- Un intake no crea alcance, hito, tarea ni esfuerzo. Solo avanza con estimacion detallada, aprobacion humana y requerimiento sanitizado; los originales y terminos comerciales permanecen privados.
