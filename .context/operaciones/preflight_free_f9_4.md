# Definicion F9.4 Sustituida

## Estado

- Identidad anterior: F9.4 `REMOTE_READ_FREE`.
- Estado final: `SUPERSEDED_NON_AUTHORIZABLE`.
- Sustitucion: [PLAN-H1-SIMPLIFICADO-001](./plan_simplificado_hito1.md) y [ADR-0004](../decisiones/ADR-0004_simplificacion_contractual_hito1.md).
- Nueva identidad F9.4: reconciliacion contractual exclusivamente local y documental.
- Siguiente subfase al cierre de F9.4: F9.5 preflight Free read-only dirigido, entonces pendiente y no autorizada. El estado vigente posterior se consulta en [Estado del proyecto](../estado_del_proyecto.md).

La definicion anterior proponia un adapter remoto, OpenAPI, advisors, binding cross-plane, nonce one-shot, attestations y cinco blockers. Ese diseno queda fuera del critical path contractual y no puede implementarse ni ejecutarse con ninguna autorizacion F9.4 presente o futura.

Los artifacts y resultados historicos F9.3 no se reescriben. Su existencia no obliga a resolver los blockers de la definicion sustituida ni amplia `H1-CA1`, `H1-CA2P` o `H1-CA7P`.

## Regla De Autorizacion

La frase `Ejecuta las tareas pendientes de la Fase F9.4` solo cubrio la reconciliacion documental descrita por el estado y la tarea activos. No concede acceso Free/Pro, carga de secrets, DDL, DML, migrations, backfill, H-00, pausa de writers, workflows remotos ni operaciones productivas.

El siguiente trabajo autorizable se obtiene exclusivamente de [Estado del proyecto](../estado_del_proyecto.md), [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) y la [macrofase F9](./certificacion_hito1_f9.md). Esta nota es un tombstone historico y no una definicion ejecutable.
