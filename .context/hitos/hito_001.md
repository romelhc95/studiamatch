# HITO-001 - Orquestacion Y Candidate CA1-Only

`HITO-001` agrupa el alcance original de Hito 1 para `REQ-EST-001` y la
redistribucion propuesta por la adenda. Esta nota documenta alcance y
trazabilidad; no mantiene estado vivo.

## Alcance

- `H1-CA1`: orquestacion automatica FG2/FG3, schedules y gates aplicables.
- `H1-CA2P`: soporte parcial de schema editorial, calidad y seguridad base.
- `H1-CA7P`: preparacion documental para tablas, campos, RLS, pipeline y decisiones operativas.

## Redistribucion Propuesta

[ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
propone cerrar Hito 1 exclusivamente con `H1-CA1` en produccion. `H1-CA2P`
pasa a `H2-CA2` y `H1-CA7P` a `H4-CA7` despues de aprobacion cliente. Hasta
entonces, el alcance original anterior permanece vigente.

El candidate CA1-only no puede incluir cambios de schema/RLS/RPC, frontend,
leads/email, backfill ni artifacts terminales CA2. Ver
[PLAN-H1-CA1-ONLY-001](../operaciones/plan_cierre_hito1_ca1_only.md).

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
- Adenda propuesta: [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
- Plan CA1-only: [PLAN-H1-CA1-ONLY-001](../operaciones/plan_cierre_hito1_ca1_only.md)
- Evidencia cliente draft: [EVID-PACK-H1-001](../evidencias_cliente/sprint_1/paquete_hito_001.md)
