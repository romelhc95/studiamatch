# HITO-001 - Orquestacion Y Candidate CA1-Only

`HITO-001` agrupa el alcance vigente de Hito 1 para `REQ-EST-001` despues de la
adenda aprobada. Esta nota documenta alcance y
trazabilidad; no mantiene estado vivo.

## Alcance

- `H1-CA1`: orquestacion automatica FG2/FG3, schedules y gates aplicables.
- FG1: soporte operativo de inventario, sin crear criterio adicional.

## Antecedentes Historicos Preservados

[ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
cierra Hito 1 exclusivamente con `H1-CA1` en produccion. `H1-CA2P` pasa a
`H2-CA2` y `H1-CA7P` a `H4-CA7`; ambos se preservan solo como antecedentes y no
acreditan cierre de Hito 1.

El candidate CA1-only no puede incluir cambios de schema/RLS/RPC, frontend,
leads/email, backfill ni artifacts terminales CA2. Ver
[PLAN-H1-CA1-ONLY-001](../operaciones/plan_cierre_hito1_ca1_only.md).

## Alineacion Contractual Cerrada En F9.5

F6-F8 son la base funcional contractual de Hito 1. Los artifacts tecnicos de F9.5 de PR #245 y PR #247 son `HISTORICAL_NON_PROMOTABLE`: se preservan para trazabilidad, pero no son parte del package contractual ni una ruta de aplicacion.

- `H1-CA1` cubre los workflows y gates implementados; la compatibilidad backend y una ejecucion efectiva por ambiente permanecen como evidencia de certificacion.
- `H1-CA2P` acepta `missing_fields` JSONB, `field_sources` JSONB, `manual_updated_at` y `start_date` como equivalencias historicas del alcance editorial. La aplicacion, backfill y pruebas por rol pasan a Hito 2 y requieren evidencia nueva.
- `H1-CA7P` conserva su alcance documental historico; Hito 4 debe producir documentacion y evidencia nueva para `H4-CA7`.
- `H-00` fue un P0 Free-only de la ruta sustituida; no es prerrequisito del Hito 1 CA1-only ni de F9.8.
- [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) fija que leads/email no pertenecen al perfil funcional habilitado de Hito 1; su arquitectura integral queda diferida sin crear criterios nuevos.

Los estados vivos, dependencias y pendientes se consultan exclusivamente en [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md).

## Nota De Cierre Tecnico F10.8

La remediacion cleansing provenance F10.8 quedo promovida a `main@1885806f0d9f189600d410d353fcf13fb8dd4676` por PR #320. La DDL Pro `20260808_fase10_8_atomic_cleansing_provenance` fue aplicada una sola vez por DB Sync `31263024890` bajo autorizacion consumida, y DB Sync verify `31268229878=PASS` confirmo pending `0`, apply skipped, target schema PASS y FG2 deferred PASS sobre `main@675ade43f41a2f5d04f05a40f9837b514a8705ce`. El Production Canary `31269277219` paso FG1/FG2/FG3 y primer restore, pero fallo fail-closed en el segundo restore por JSON truncado durante atestacion no-cohorte; por tanto `EVID-H1-010` sigue pendiente. Esta nota no declara `COMPLETED_PRODUCTION`: Production Canary PASS, observacion de schedules y conformidad cliente siguen pendientes segun el estado vivo.

## Trazabilidad

- Complejidad y estimacion tecnica original: [EST-001](../estimaciones/est_001.md)
- Backlog: [REQ-EST-001 Sprint 1](../backlog_tareas/req_est_001_sprint_1/_index.md)
- Tarea principal: [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- Estado vigente: [Estado del proyecto](../estado_del_proyecto.md)
- Arquitectura: [Pipeline](../arquitectura_pipeline.md)
- Datos: [Sistema DB](../sistema_db_supabase.md) y [Matriz DB](../operaciones/matriz_adopcion_db.md)
- Release: [Flujo de release minimo](../operaciones/flujo_release_minimo.md)
- Corte seguridad/funcionalidad/estabilidad: [PLAN-H1-CORTE-SFE-001](../operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- Adenda vigente: [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
- Plan CA1-only: [PLAN-H1-CA1-ONLY-001](../operaciones/plan_cierre_hito1_ca1_only.md)
- Evidencia cliente: [EVID-PACK-H1-001](../evidencias_cliente/sprint_1/paquete_hito_001.md)
- Registro Production Canary F10.8: [EVID-H1-CANARY-F10.8-001](../evidencias_cliente/sprint_1/registro_canary_production_f10_8_2026-08-07.md)
- Autorizacion DDL F10.8: [DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO](../operaciones/ddl_authorizations/DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO.md)
- Matriz de pruebas: [Tests Hito 1](../pruebas/01_matriz_tests_hito_1.md)
