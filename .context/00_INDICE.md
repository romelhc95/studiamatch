# StudIAMatch - Contexto Canonico

`.context/` es la unica fuente documental de verdad del proyecto. Toda nota canonica debe ser breve, usar enlaces relativos y ser alcanzable desde este indice.

## Entrada Al Contexto

- Prompt base
- [Estado vigente](estado_del_proyecto.md)
- Taxonomia y backlog
- Flujo de requerimientos

## Producto Y Arquitectura

- Mapa canonico de arquitectura
- [Sistema DB Supabase](sistema_db_supabase.md)
- [Arquitectura del pipeline](arquitectura_pipeline.md)
- Estructura frontend
- Estrategia de pruebas Sprint 1
- Gobierno de hallazgos
- [Estimacion EST-001](estimaciones/est_001.md)
- Hitos Sprint 1
- [Adenda cliente 001 sanitizada](backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md)
- [Plan de cierre Hito 1 CA1-only](operaciones/plan_cierre_hito1_ca1_only.md)
- Evidencia cliente Sprint 1
- Registro de entrega tecnica Hito 1
- [Matriz de adopcion DB](operaciones/matriz_adopcion_db.md)
- Reconciliacion DB-as-Code F6
- Certificacion G1b F7
- Certificacion local Hito 1 F8
- Certificacion Hito 1 - macrofase F9
- [Resultado QA F9.9](operaciones/qa_desviacion_f9_9_resultado.md)
- [Plan simplificado de Hito 1 - historico superseded](operaciones/plan_simplificado_hito1.md)
- [Plan de corte seguridad/funcionalidad/estabilidad Hito 1](operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- Cierre definitivo F9.7 por work packages
- Preservacion y retiro del plan temporal F9.4
- [Evidencia historica F9.1 - package FASE-09](operaciones/precertificacion_hito1_f9.md)
- [Evidencia historica F9.2 - package FASE-10](operaciones/promocion_hito1_f10.md)
- [Definicion remota F9.4 sustituida y no autorizable](operaciones/preflight_free_f9_4.md)
- [Registro historico F9.5](operaciones/preflight_free_f9_5.md)
- Cierre H-00 F9.6
- Evidencia Gate B F9.7
- Definicion de remediacion Gate B F9.7
- Atestacion de origen ACL F9.7
- Remediacion local del trigger F9.7
- [Contrato PR-O F9.7 v1 superseded](operaciones/pr_o_f9_7_v3_hold.md)
- [Contrato PR-O F9.7 executor privado](operaciones/pr_o_f9_7_successor_private_executor.md)
- Pg Net queue drain F9.7
- [Flujo de release minimo](operaciones/flujo_release_minimo.md)

## Alcance Y Trabajo

- [HITO-001](hitos/hito_001.md)
- [HITO-002](hitos/hito_002.md)
- HITO-003
- HITO-004
- HITO-005
- [Backlog REQ-EST-001](backlog_tareas/req_est_001_sprint_1/_index.md)
- [TASK-H1-001](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [Seguimiento detallado de Hito 1](backlog_tareas/req_est_001_sprint_1/seguimiento_detallado_hito_1.md)
- [TASK-H2-001](backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- TASK-H3-001
- TASK-H4-001
- TASK-H5-001
- Anexo cliente CA2/RLS
- [Backlog diferido F9.5](backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md)
- [Backlog diferido leads/email](backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md)
- INTAKE-002 pendiente de estimacion
- Plantilla de tarea

## Decisiones E Historial

- Indice de decisiones
- ADR-0001
- ADR-0002
- [ADR-0003](decisiones/ADR-0003_taxonomia_macrofases_subfases.md)
- [ADR-0004](decisiones/ADR-0004_simplificacion_contractual_hito1.md)
- [ADR-0005](decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- ADR-0006
- [ADR-0007](decisiones/ADR-0007_desviacion_canary_certification_f9_9.md)
- [ADR-0008](decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md)
- [ADR-0009](decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md)
- [ADR-0010](decisiones/ADR-0010_rebaseline_f10_10_metadata_remediation.md)
- [ADR-0011](decisiones/ADR-0011_rebaseline_superior_hito1_ca1_f10_10_a_h2.md)
- [ADR-0012](decisiones/ADR-0012_trust_plane_g5_repository_only.md)
- [ADR-0013](decisiones/ADR-0013_trust_broker_durable_object_ledger.md)
- [ADR-0014](decisiones/ADR-0014_g5_manual_workflow_connected_adapter_disabled.md)
- [ADR-0015](decisiones/ADR-0015_g5_deployment_ready_disabled.md)
- [ADR-0016](decisiones/ADR-0016_g5_operational_activation_gates.md)
- [ADR-0017](decisiones/ADR-0017_g5_e1_cloudflare_deployment_hardening.md)
- [ADR-0018](decisiones/ADR-0018_g5_trust_live_remediation_repository_only.md)
- [ADR-0019](decisiones/ADR-0019_github_runtime_schema_lifecycle.md)
- [ADR-0020](decisiones/ADR-0020_g5_runtime_binding_snapshot_cas.md)
- [ADR-0021](decisiones/ADR-0021_g5_terminal_confirmation_token_scope.md)
- [ADR-0022](decisiones/ADR-0022_g5_followup_security_remediation.md)
- Changelog 2026-08-01
- Changelog 2026-08-03
- Changelog 2026-08-04
- Changelog 2026-08-07
- Plantilla ADR
- Changelog 2026-07-24
- Changelog 2026-07-25
- Changelog 2026-07-26
- Changelog 2026-07-27
- Changelog 2026-07-28
- Changelog 2026-07-29
- Changelog 2026-07-30
- Plantilla de changelog

## Matriz De Autoridad

| Informacion | Fuente autorizada | Regla de precedencia |
|---|---|---|
| Alcance aprobado | [Requerimiento sanitizado REQ-EST-001](backlog_tareas/req_est_001_sprint_1/_index.md) | Ninguna estimacion, tarea o nota operativa puede ampliarlo. |
| Arquitectura decidida | ADR aceptada | La decision vigente debe estar aceptada y enlazada desde el vault. |
| Vistas de arquitectura | Mapa canonico | Son vistas derivadas; no sustituyen REQ, TASK, Git ni evidencia remota. |
| Cobertura y hallazgos | Estrategia de pruebas | Los tests prueban CA aprobados; ningun hallazgo amplia alcance sin `INTAKE -> EST -> REQ -> TASK`. |
| Comportamiento implementado | Git y migrations, referenciados desde las notas de `.context/` | El codigo y las migrations son autoridad tecnica, no fuentes documentales paralelas. |
| Estado DB aplicado | [Snapshot canonico vivo](estado_del_proyecto.md); [sistema DB](sistema_db_supabase.md) y [matriz DB](operaciones/matriz_adopcion_db.md) quedan como referencias historicas pre-F10.8 | Ninguna nota historica puede sustituir la DDL Pro F10.8 aplicada/verificada ni autorizar adopcion nueva. |
| Estado de tareas | TASK canonica de cada Hito, enlazada desde [REQ-EST-001](backlog_tareas/req_est_001_sprint_1/_index.md) | Cada tarea es la unica autoridad de su avance y criterios; solo una puede estar activa. |
| Estado del proyecto | [Snapshot canonico](estado_del_proyecto.md) | Sustituye cualquier resumen vivo en hitos, estimaciones, indices o changelogs. |
| Taxonomia de fases | [ADR-0003](decisiones/ADR-0003_taxonomia_macrofases_subfases.md), ADR-0004/0005, ADR-0006, [ADR-0008](decisiones/ADR-0008_rebaseline_f10_7_gate_reconstruction.md), [ADR-0009](decisiones/ADR-0009_reconciliacion_entrega_tecnica_post_main_f10_7.md), [ADR-0011](decisiones/ADR-0011_rebaseline_superior_hito1_ca1_f10_10_a_h2.md) y macrofase F9 | F0-F11 son macrofases; ADR-0011 supersede F10.10/ADR-0010 solo para Hito 1, transfiere metadata a H2-CA2 y reactiva F10.9 solo para FG2/FG3. |
| Readiness de release | Candidate y gates registrados en `.context/` segun el [flujo de release](operaciones/flujo_release_minimo.md) | Se deriva de evidencia verificable y aprobacion humana; no existe candidate en F5. |
| Historia | Changelog no autoritativo | Registra eventos y nunca determina vigencia. |
| Plan de implementacion legacy `../IMPLEMENTATION_PLAN.md` | Ninguna | Es antecedente no canonico, no es dependencia y esta fuera del flujo vigente. |

[EST-001](estimaciones/est_001.md) fija solo complejidad Alta y una estimacion tecnica original de 72h; no acredita saldo real ni es autoridad para alcance o estado vivo.

## Reglas Minimas

- No duplicar estado vivo fuera de [Estado del proyecto](estado_del_proyecto.md) y la tarea correspondiente.
- No crear criterios, subtareas o decisiones implicitas para completar vacios.
- No registrar secretos, credenciales, datos personales ni identificadores sensibles.
- Git y las migraciones forward-only conservan la verdad ejecutable; `.context/` conserva la verdad documental.
- Una afirmacion de validacion o release requiere una verificacion enlazada desde la nota autoritativa aplicable.
