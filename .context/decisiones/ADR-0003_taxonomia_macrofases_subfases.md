# ADR-0003 - Taxonomia Macrofases Y Subfases

## Estado

`SUPERSEDED_TOMBSTONE`

## Decision

La taxonomia legacy de macrofases/subfases queda sustituida para la operacion
vigente por [ADR-0027](ADR-0027_work_packages_y_convergencia.md) y
[ADR-0028](ADR-0028_context_graph_semantico_y_autorizacion_r0_r3.md).

## Regla Vigente

- La autoridad viva permanece en [Estado Del Proyecto](../estado_del_proyecto.md).
- La fase decimal identifica trazabilidad y seleccion de tareas.
- La autorizacion operativa R1 posterior a F10.11 requiere WP/digest vigente.
- R2 y R3 requieren gates separados; ninguna fase decimal concede push, PR,
  Supabase, DDL/DML, backfill, writers, schedules, deploys ni produccion.

## Motivo

F10.11 cerro la homologacion canonica y la Etapa 1 de documentacion Obsidian.
F12 inicia la implementacion local Sprint 1 posterior a ese cierre, empezando por
`F12.1` para Hito 2 CA2 bajo `WP-H2-001`.
