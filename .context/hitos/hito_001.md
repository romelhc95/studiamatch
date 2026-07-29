# HITO-001 - Orquestacion, Schema Y Seguridad Base

`HITO-001` agrupa el alcance aceptado de Hito 1 para `REQ-EST-001`. Esta nota documenta alcance y trazabilidad; no mantiene estado vivo.

## Alcance

- `H1-CA1`: orquestacion automatica FG2/FG3, schedules y gates aplicables.
- `H1-CA2P`: soporte parcial de schema editorial, calidad y seguridad base.
- `H1-CA7P`: preparacion documental para tablas, campos, RLS, pipeline y decisiones operativas.

No se agregan criterios ni se modifica el contrato, el esfuerzo o el alcance de los Hitos 2 a 5.

## Alineacion Contractual Cerrada En F9.5

F6-F8 son la base funcional contractual de Hito 1. Los artifacts tecnicos de F9.5 de PR #245 y PR #247 son `HISTORICAL_NON_PROMOTABLE`: se preservan para trazabilidad, pero no son parte del package contractual ni una ruta de aplicacion.

- `H1-CA1` cubre los workflows y gates implementados; la compatibilidad backend y una ejecucion efectiva por ambiente permanecen como evidencia de certificacion.
- `H1-CA2P` acepta `missing_fields` JSONB, `field_sources` JSONB, `manual_updated_at` y `start_date` como equivalencias del alcance editorial. La aplicacion Free/Pro, identidad backend de servicio, backfill editorial y pruebas por rol permanecen fuera de este cierre.
- `H1-CA7P` conserva su alcance documental completado; falta el anexo final por ambiente para certificacion sin crear un criterio nuevo.
- `H-00` es un P0 Free-only separado, obligatorio antes de `FREE_CERTIFIED` y excluido de los criterios contractuales de este hito.
- [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) fija que leads/email no pertenecen al perfil funcional habilitado de Hito 1; su arquitectura integral queda diferida sin crear criterios nuevos.

Los estados vivos, dependencias y pendientes se consultan exclusivamente en [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).

## Trazabilidad

- Complejidad y estimacion tecnica original: [EST-001](../estimaciones/est_001.md)
- Backlog: [REQ-EST-001 Sprint 1](../backlog_tareas/req_est_001_sprint_1/_index.md)
- Tarea principal: [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- Estado vigente: [Estado del proyecto](../estado_del_proyecto.md)
- Arquitectura: [Pipeline](../arquitectura_pipeline.md)
- Datos: [Sistema DB](../sistema_db_supabase.md) y [Matriz DB](../operaciones/matriz_adopcion_db.md)
- Release: [Flujo de release minimo](../operaciones/flujo_release_minimo.md)
- Corte seguridad/funcionalidad/estabilidad: [PLAN-H1-CORTE-SFE-001](../operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
