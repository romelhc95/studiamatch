# Gobierno Del Backlog

El backlog organiza requerimientos y tareas canonicas sin duplicar estado vivo. Cada tarea debe derivar de un requerimiento aceptado, usar la [plantilla minima](./_plantilla_tarea.md) y quedar enlazada desde su indice de requerimiento.

## Taxonomia Canonica

| Tipo | ID canonico | Proposito | Nota canonica |
|---|---|---|---|
| Intake | `INTAKE-*` | Registrar una solicitud privada pendiente de sanitizacion, estimacion y aprobacion. | Nota propia bajo `backlog_tareas/intake/` |
| Requerimiento | `REQ-EST-001` | Fijar el alcance aprobado y sus criterios sanitizados. | [REQ-EST-001](./req_est_001_sprint_1/_index.md) |
| Hito | `HITO-001..005` | Agrupar el alcance de cada hito sin mantener estado vivo. | [Indice de hitos](../hitos/_index.md) |
| Macrofase | `FNN` | Conservar una etapa F0-F11 del plan `main -> Hito 1`; agrupa resultados, no autoriza por si sola. | [Estado del proyecto](../estado_del_proyecto.md) |
| Subfase | `FNN.n` | Identificar una unidad ejecutable con alcance, allowlist, gates y autorizacion exactos. | Nota operativa enlazada desde [Estado](../estado_del_proyecto.md) |
| Alias historico | `FASE-NN` | Preservar identidad de artifacts/PR cerrados sin determinar la macrofase vigente. | Nota de evidencia correspondiente |
| Tarea | `TASK-HN-001` | Mantener el estado vivo del paquete de cada hito. | [REQ-EST-001](./req_est_001_sprint_1/_index.md) |
| Adenda | `ADENDA-REQ-EST-001-NNN` | Registrar un delta sanitizado pendiente o aprobado sin duplicar el contrato completo. | [Adenda 001](./req_est_001_sprint_1/adenda_cliente_001_sanitizada.md) |
| Evidencia cliente | `EVID-PACK-HN-NNN` | Presentar resultado sanitizado de un candidate real. | [Indice de evidencia](../evidencias_cliente/sprint_1/_index.md) |
| Backlog diferido | `BK-F9.5-*` | Registrar hallazgos sin implementar, autorizar ni crear subtareas. | [Hallazgos F9.5](./req_est_001_sprint_1/backlog_f9_5_known_findings.md), [BK-F9.5-05](./req_est_001_sprint_1/backlog_seguridad_leads_email.md) |
| Criterio | `H1-CA1` | Trazar la orquestacion aceptada dentro de `HITO-001`. | [TASK-H1-001](./req_est_001_sprint_1/tarea_001_hito_1.md#criterios-y-entregables) |
| Criterio parcial | `H1-CA2P` | Trazar el schema y seguridad base aceptados. | [TASK-H1-001](./req_est_001_sprint_1/tarea_001_hito_1.md#criterios-y-entregables) |
| Criterio preparatorio | `H1-CA7P` | Trazar el contrato documental aceptado. | [TASK-H1-001](./req_est_001_sprint_1/tarea_001_hito_1.md#criterios-y-entregables) |
| Criterio futuro | `HN-CA*` | Trazar un CA aprobado dentro del Hito correspondiente. | [REQ-EST-001](./req_est_001_sprint_1/_index.md) y su TASK |
| Decision | `ADR-NNNN` | Registrar una decision humana durable y su razon. | [Indice ADR](../decisiones/_index.md) |
| Snapshot | `SNAPSHOT-YYYY-MM-DD` | Identificar el corte del estado vivo vigente. | [Estado del proyecto](../estado_del_proyecto.md) |
| Changelog | `CHANGELOG-YYYY-MM-DD` | Registrar cambios historicos sin autoridad vigente. | [Changelog](../changelog/2026-07-24.md) |

## Reglas

- El estado vivo del proyecto y las fases reside solo en [Estado del proyecto](../estado_del_proyecto.md).
- Solo una subfase decimal definida y activa autoriza ejecucion; una macrofase o alias historico no agrega permisos.
- El estado vivo de una tarea y sus criterios reside solo en su nota canonica.
- Los indices y los hitos enlazan alcance, pero no replican estados.
- Una tarea no crea criterios que no existan en el requerimiento aceptado.
- Cada Hito tiene una unica TASK principal. Las TASK futuras permanecen
  `PENDING` sin subfase ejecutable hasta que el Estado las active.
- Una adenda draft no cambia alcance. Solo una aprobacion externa registrada y
  una ADR aceptada permiten normalizar el nuevo mapa en el requerimiento.
- Un backlog diferido no crea una tarea, subtarea, criterio, candidate, package ni autorizacion de ejecucion.
- Un intake no crea alcance, hito, tarea ni esfuerzo. Solo avanza con estimacion detallada, aprobacion humana y requerimiento sanitizado; los originales y terminos comerciales permanecen privados.
