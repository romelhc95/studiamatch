# ADR-0002 - Ciclo Recurrente De Requerimientos Privados

Estado: `ACCEPTED`

## Contexto

El proyecto recibe solicitudes nuevas de forma recurrente. Los originales pueden contener detalle comercial o privado y no deben convertirse directamente en alcance versionado.

## Decision

1. Cada solicitud se ingresa manualmente como fuente privada `SRC-REQ-*` y se registra como `INTAKE-*` sanitizado.
2. El intake genera una estimacion detallada de costo y tiempo; el detalle comercial permanece privado y la nota `EST-*` publica solo la version tecnica sanitizada.
3. La aprobacion humana convierte el intake en `REQ-*`, hitos y tareas o subtareas alineadas a criterios de aceptacion.
4. Ningun archivo nuevo modifica automaticamente alcance, esfuerzo, hitos o tareas.
5. Cada hito produce evidencia nueva al finalizar; no se reutilizan veredictos o evidence packages historicos.
6. Los schemas y el arbol de evidencia permanecen diferidos hasta que exista un candidate real.

## Aplicacion A SRC-REQ-001

- `H1-CA1` adopta cadencia automatica con gates y controles.
- `EST-001` conserva complejidad Alta y 72h.
- La intencion sin destino actual se registra como [INTAKE-002](../backlog_tareas/intake/INTAKE-002.md) para estimacion futura separada.

## Consecuencias

- El requerimiento sanitizado sigue siendo autoridad de alcance.
- La estimacion no compite con el estado vivo.
- Nuevos intakes requieren autorizacion antes de crear hitos o tareas.
- La evidencia se crea por hito y se entrega despues de su validacion.

## Enlaces

- [Flujo de requerimientos](../operaciones/flujo_requerimientos.md)
- [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
- [EST-001](../estimaciones/est_001.md)
- [Estado del proyecto](../estado_del_proyecto.md)
