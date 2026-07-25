# Flujo De Requerimientos

Este flujo describe la trazabilidad documental reusable desde cada solicitud privada hasta el release. No define automatizacion, componentes ejecutables ni una maquina de estados.

| Etapa | Entrada | Salida | Nota canonica | Autoridad | Transicion | Trazabilidad |
|---|---|---|---|---|---|---|
| Intake | Solicitud original ingresada manualmente en privado | `INTAKE-*` identificable | Nota canonica de intake; originales en artifact privado | Decision humana sobre incorporacion | Intake -> Estimacion | `SRC-REQ-*` -> `INTAKE-*` |
| Estimacion | Intake sanitizado | Estimacion detallada de alcance, costo y tiempo | Nota `EST-*` publica sanitizada; detalle comercial privado | Agente contractual | Estimacion -> Aprobacion | `INTAKE-*` -> `EST-*` |
| Aprobacion | Estimacion revisada | Requerimiento e hitos autorizados | Requerimiento sanitizado y ADR cuando corresponda | Aprobacion humana explicita | Aprobacion -> Tarea | `EST-*` -> `REQ-*` -> `HITO-*` |
| Tarea | Hito autorizado | Tareas o subtareas con criterios trazables | Nota `TASK-*` | Tarea para estado vivo; requerimiento para contrato | Tarea -> Validacion | `HITO-*` -> `TASK-*` -> criterios |
| Validacion | Entregables de la tarea | Resultado verificable por criterio | Tarea canonica y referencias de evidencia | Verificacion aplicable a cada criterio | Validacion -> Release | Criterio -> verificacion -> evidencia nueva |
| Release | Criterios validados y gates aprobados | Hito promovido y paquete de evidencia para entrega | [Flujo de release minimo](./flujo_release_minimo.md) | Gates tecnicos y aprobacion humana | Release -> registro historico | Requerimiento -> hito -> tareas -> evidencia -> release -> changelog |

## Reglas De Paso

- Ninguna etapa crea alcance o criterios fuera del requerimiento aceptado.
- La aprobacion humana habilita la transicion aplicable; un documento por si solo no autoriza ejecucion.
- La tarea conserva su estado vivo y enlaza la verificacion sin incrustar artifacts externos.
- El release sigue su flujo canonico y el changelog registra el resultado sin adquirir autoridad vigente.
- Los costos, terminos comerciales y originales permanecen privados; la nota publica conserva alcance tecnico, complejidad y esfuerzo sanitizados.
- Detectar un archivo privado nuevo nunca crea automaticamente requerimientos, hitos, tareas, subtareas o cambios de estimacion.
- Cada hito genera evidencia nueva al terminar su desarrollo; el arbol y schema de evidencia se implementan solo cuando exista un candidate real.
