# Requerimientos sanitizados y aceptación

> Corte: 2026-10-12. Esta nota resume criterios versionados y atestados; no reproduce el documento privado del cliente ni crea alcance o autoridad operativa.

## Fuente y precedencia

La fuente canónica accesible en el repositorio es [REQ-EST-001 Sprint 1 sanitizado](../backlog_tareas/req_est_001_sprint_1/_index.md), con su [adenda cliente](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md) y la [atestación de aceptación del plan editorial](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md). La fuente privada no se leyó ni se copia a PR. Los archivos y referencias visuales privados enumerados por el índice pueden no estar disponibles en este checkout; su ausencia no amplía ni cancela criterios.

La atestación del 2026-10-01 autoriza implementación/validación local en Docker y PG17 desechable hasta GO local. Excluye accesos/escrituras Supabase, Auth/Cloudflare reales, deploy, schedules, workflow_dispatch, push, PR, merge, Certification, Production y promoción. La autorización no se extiende a esta etapa futura.

## Criterios trazados

| Criterio sanitizado | Implementación candidata observada | Validación local acreditada | Estado y límite |
|---|---|---|---|
| Pipeline admite datos parciales y deja el curso pendiente de revisión, sin publicación automática | Workers FG2, estados editoriales y gates; ver [pipeline](../componentes/pipeline.md) y [database](../database.md) | Cierre R178 y matriz LOCAL-01..23; fixtures locales | Validado localmente en el alcance declarado. No acredita escrituras ni estado de datos remotos. |
| Admin puede completar/corregir campos, conserva ownership/procedencia y rechaza una edición con versión obsoleta | Editor Admin, RPC allowlisted, manual_overrides, field_sources y control optimistic version | R178: criterios editoriales y conflicto de versión en fixture sintético | Validado localmente. Usuario estándar no gana permisos por inferencia. |
| Cada mutación editorial registra actor, fecha y valores anteriores/nuevos en auditoría protegida, sin auditoría parcial ante rechazo/no-op | course_editorial_audit, funciones editoriales y acceso protegido | Harness PG17/C03 declarados por R178 | Validado localmente en SQL sintético; no prueba tabla/grants remotos. |
| Disponibilidad exige evidencia trazable vigente; límite inclusivo de 90 días; faltante/futuro/vencido/exceso falla cerrado y conserva compatibilidad legacy | availability override/evidence y vista pública efectiva | R178: aceptación sintética de fechas, evidencias y compatibility | Validado localmente. Ningún backfill o publicación remota autorizados. |
| Vista efectiva y rutas estáticas muestran únicamente un curso elegible sin retirar compatibilidad necesaria | courses_public_effective, export Next estático y estado editorial | R178 G06/G07/G09 dentro de fixtures y artefacto normal identificado | Validación local; rebuild y cache remoto pendientes. |
| El encabezado de Admin muestra el correo de sesión autenticada y conserva el rol como autoridad de permisos | Session context y encabezado Admin | R173: seis viewports, 36 aserciones; R178 lo incorpora al cierre | Validado localmente con identidad sintética; no cuenta real. |

La referencia normativa de estos criterios es la atestación sanitizada y el índice de requerimientos, no esta tabla. Para los datos de resultados, consultar [R178](../evidencia/h3req1_g09_local_close_r178_2026-10-11.md). R178 acredita G01–G09 locales para el candidato y las limitaciones allí declaradas; R181/R182 no vuelve a ejecutar aceptación funcional.

## Tasks, owners y dependencias

| Task / hito | Owner documentado | Estado en la fuente vigente local | Dependencias / siguiente lectura |
|---|---|---|---|
| TASK-H1-001 / HITO-001 | No se declara owner actual en la ficha | REDEFINED_ACTIVE_AFTER_H2_H3; H1-CA1 requiere evidencia nueva; waivers históricos no cierran CA1 nuevo | [HITO-001](../hitos/hito_001.md), luego estado operativo y permiso del ciclo. |
| TASK-H2-001 / HITO-002 | No se declara owner actual en la ficha | CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN según la ficha histórica; pendientes adicionales de producción se mantienen sujetos a JIT | [HITO-002](../hitos/hito_002.md), [TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md). No inferir estado actual remoto por el nombre del estado. |
| TASK-H3-001 / HITO-003 / H3REQ1 | Romel figura como owner backend en una nota histórica de la tarea | G01–G09 GO local por R178; G10 local preparado R181/R182; G10 remoto pendiente. Cierre contractual remoto sigue incompleto | [HITO-003](../hitos/hito_003.md), [estado operativo](../estado_del_proyecto.md), [R178](../evidencia/h3req1_g09_local_close_r178_2026-10-11.md). Owner actual no se infiere de la nota antigua. |
| TASK-H4-001 / HITO-004 | No declarado | PLANNED_AFTER_H2_CONTRACT_STABLE | [HITO-004](../hitos/hito_004.md); contrato visual y fuente de referencia necesitan verificación dentro de un ciclo autorizado. |
| TASK-H5-001 / HITO-005 | No declarado | PLANNED_AFTER_H2_CONTRACT_STABLE | [HITO-005](../hitos/hito_005.md); alcance de búsqueda/filtros necesita cotejo antes de iniciar. |

Las precedencias completas permanecen en el [índice de REQ-EST-001](../backlog_tareas/req_est_001_sprint_1/_index.md) y el [plan vinculante Obsidian](../operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md). Esta navegación no reinicia, cierra ni autoriza tareas.

## Clasificación de afirmaciones

- **Implementación candidata**: comprobada en fuentes del checkout del 2026-10-12; puede contener WIP no representado por HEAD.
- **Validación local acreditada**: resultado fechado de R178/R181/R182 con inputs/entorno descritos en su evidencia.
- **Adopción remota verificada en este corte**: ninguna. No hubo consultas remotas en esta sesión.
- **Historia**: hitos, PRs, ejecuciones y decisiones documentados con fecha/hash en sus notas originales; una nota o commit no acredita el estado actual.
- **Propuesta/desconocido**: H4/H5 planificados; rutas, campos, schema aplicado y estado remoto requieren cotejo en un ciclo posterior.

## Navegación

[Hitos](../hitos/README.md) · [Arquitectura](../arquitectura.md) · [Pruebas](../pruebas.md) · [Changelog](../changelog.md) · [Índice principal](../indice.md)
