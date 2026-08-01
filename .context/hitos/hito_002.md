# HITO-002 - Contrato CA2 Y Pipeline De Incompletos

`HITO-002` agrupa el alcance propuesto de CA2 completo y CA3 para
`REQ-EST-001`. Esta nota documenta alcance y trazabilidad; no mantiene estado
vivo.

## Alcance Propuesto

- `H2-CA2`: contrato integral de schema editorial/calidad, campos faltantes,
  fuentes, actualizacion manual, inicio, patrocinio/leads base y RLS.
- `H2-CA3`: pipeline que preserva datos parciales, marca faltantes y clasifica
  registros pendientes o completos sin fallar por vacios criticos.

## Secuencia Interna

1. `WP-H2-CA2` fija y certifica CA2.
2. `WP-H2-CA3` integra CA2 con CA3 en harvester, cleansing, enrichment y sync.
3. Backfill y adopcion por ambiente usan gates y autorizaciones separadas.

Estos work packages son unidades tecnicas internas; no son hitos comerciales,
subtareas, fases ni eventos de pago.

## Exclusiones

- Panel `/admin`, autenticacion y curacion manual: Hito 3.
- Home y documentacion de cierre: Hito 4.
- Resultados y filtros: Hito 5.
- Entrega real-time de leads por email/webhook: fuera de Sprint 1.
- Busqueda semantica y embeddings.

## Dependencias

- Hito 1 CA1 desplegado y estable.
- Adenda cliente aprobada.
- Candidate DB forward-only, pruebas por rol y rollback/replay.

## Trazabilidad

- [REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md)
- [TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- [Adenda sanitizada](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
- [Estado del proyecto](../estado_del_proyecto.md)
- [Matriz de pruebas Hito 2](../pruebas/02_matriz_tests_hito_2.md)
