# StudIAMatch - Contexto Canonico

`.context/` es la unica fuente documental de verdad del proyecto. Toda nota canonica debe ser breve, usar enlaces relativos y ser alcanzable desde este indice.

## Entrada Al Contexto

- [Prompt base](prompts/system_prompt_base.md)
- [Estado vigente](estado_del_proyecto.md)
- [Taxonomia y backlog](backlog_tareas/_README.md)
- [Flujo de requerimientos](operaciones/flujo_requerimientos.md)

## Producto Y Arquitectura

- [Sistema DB Supabase](sistema_db_supabase.md)
- [Arquitectura del pipeline](arquitectura_pipeline.md)
- [Estructura frontend](estructura_frontend.md)
- [Estimacion EST-001](estimaciones/est_001.md)
- [Matriz de adopcion DB](operaciones/matriz_adopcion_db.md)
- [Reconciliacion DB-as-Code F6](operaciones/reconciliacion_db_as_code_f6.md)
- [Certificacion G1b F7](operaciones/certificacion_g1b_f7.md)
- [Certificacion local Hito 1 F8](operaciones/certificacion_hito1_f8.md)
- [Flujo de release minimo](operaciones/flujo_release_minimo.md)

## Alcance Y Trabajo

- [HITO-001](hitos/hito_001.md)
- [Backlog REQ-EST-001](backlog_tareas/req_est_001_sprint_1/_index.md)
- [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [INTAKE-002 pendiente de estimacion](backlog_tareas/intake/INTAKE-002.md)
- [Plantilla de tarea](backlog_tareas/_plantilla_tarea.md)

## Decisiones E Historial

- [Indice de decisiones](decisiones/_index.md)
- [ADR-0001](decisiones/ADR-0001_autoridad_fuentes_context_graph.md)
- [ADR-0002](decisiones/ADR-0002_ciclo_requerimientos_privados.md)
- [Plantilla ADR](decisiones/_plantilla_adr.md)
- [Changelog 2026-07-24](changelog/2026-07-24.md)
- [Changelog 2026-07-25](changelog/2026-07-25.md)
- [Plantilla de changelog](changelog/_plantilla_changelog.md)

## Matriz De Autoridad

| Informacion | Fuente autorizada | Regla de precedencia |
|---|---|---|
| Alcance aprobado | [Requerimiento sanitizado REQ-EST-001](backlog_tareas/req_est_001_sprint_1/_index.md) | Ninguna estimacion, tarea o nota operativa puede ampliarlo. |
| Arquitectura decidida | [ADR aceptada](decisiones/_index.md) | La decision vigente debe estar aceptada y enlazada desde el vault. |
| Comportamiento implementado | Git y migrations, referenciados desde las notas de `.context/` | El codigo y las migrations son autoridad tecnica, no fuentes documentales paralelas. |
| Estado DB aplicado | [Observacion remota, ledger y postcondicion](sistema_db_supabase.md), registrados en la [matriz DB](operaciones/matriz_adopcion_db.md) | La adopcion se decide por evidencia aplicada, no por narrativa ni stems aislados. |
| Estado de tareas | [Nota canonica TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) | La tarea es la unica autoridad de su avance y criterios. |
| Estado del proyecto | [Snapshot canonico](estado_del_proyecto.md) | Sustituye cualquier resumen vivo en hitos, estimaciones, indices o changelogs. |
| Readiness de release | Candidate y gates registrados en `.context/` segun el [flujo de release](operaciones/flujo_release_minimo.md) | Se deriva de evidencia verificable y aprobacion humana; no existe candidate en F5. |
| Historia | [Changelog no autoritativo](changelog/2026-07-24.md) | Registra eventos y nunca determina vigencia. |
| Plan de implementacion legacy `../IMPLEMENTATION_PLAN.md` | Ninguna | Es antecedente no canonico, no es dependencia y esta fuera del flujo vigente. |

[EST-001](estimaciones/est_001.md) fija solo complejidad Alta y 72h pendientes; no es autoridad para alcance ni estado vivo.

## Reglas Minimas

- No duplicar estado vivo fuera de [Estado del proyecto](estado_del_proyecto.md) y la tarea correspondiente.
- No crear criterios, subtareas o decisiones implicitas para completar vacios.
- No registrar secretos, credenciales, datos personales ni identificadores sensibles.
- Git y las migraciones forward-only conservan la verdad ejecutable; `.context/` conserva la verdad documental.
- Una afirmacion de validacion o release requiere una verificacion enlazada desde la nota autoritativa aplicable.
