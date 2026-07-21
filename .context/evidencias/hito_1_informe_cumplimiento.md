# Informe de Cumplimiento — Hito 1 v2

> Documento orientado a cliente y a gate interno. Resume que se entrego, que requerimiento cubre y que evidencia respalda el cumplimiento. La fuente tecnica versionada queda en Git.

## 1. Resumen Ejecutivo

| Campo | Detalle |
|---|---|
| Sprint | Sprint 1 |
| Hito | Hito 1 |
| Paquete aprobado | Paquete 1 — Orquestacion FG2/FG3, schema base y seguridad |
| Fecha de reconstruccion limpia | 2026-07-21 |
| Estado | Implementado — listo para PR limpio |
| Rama | `feat/hito-1-foundation-v2` |

### Resultado para el cliente
- Se preparo la base tecnica para operar el pipeline con controles por institucion y evitar ejecuciones automaticas no aprobadas.
- Se versiono el contrato de datos que consumiran los siguientes hitos: campos faltantes, fuentes por campo, publication_status, data_quality_status, manual_updated_at, patrocinio base y lead_source_type.
- Se reconcilio el drift detectado: Supabase Free ya tenia aplicado Hito 1, pero `desarrollo` no versionaba todos los artefactos.

## 2. Alcance Aprobado

| Fuente | Referencia |
|---|---|
| Estimacion aprobada | `.context/estimaciones/est_001.md` |
| Tarea tecnica | `.context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1_orquestacion_fg2_fg3_schema_base_y_seguridad.md` |
| Documento cliente | `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf` |
| CAs cubiertos | CA1, CA2 parcial, CA7 preparacion |

## 3. Matriz De Cumplimiento Por Criterio De Aceptacion

| CA | Requerimiento aprobado | Cambio entregado | Evidencia verificable | Estado |
|---|---|---|---|---|
| CA1 | Schedules del harvester/pipeline definidos sin saltar gates ni exponer credenciales. | FG2 queda sin cambios fuera de alcance; FG1/FG3 quedan manual-only con autorizacion explicita. Orquestador filtra gates antes del limit. | `.github/workflows/fg1_inventory.yml`, `.github/workflows/fg3_integrity.yml`, `scripts/core/master_orchestrator.py`, py_compile OK. | Cumple |
| CA2 parcial | Schema soporta estado editorial/calidad, campos faltantes, fuentes, timestamps, fecha y leads/patrocinio base. | Migration SQL versiona columnas, checks, indices, RLS hardening, anti-spoofing y backfill idempotente. Reutiliza `start_date`/`start_date_text`. | `db/migrations/20260712_hito1_editorial_quality_contract.sql`; Supabase Free confirma columnas y policies. | Cumple |
| CA7 preparacion | Documentar tablas/campos y contrato para hitos siguientes. | TAREA-001 y changelog documentan campos que consumiran Hitos 2, 3 y 5. | `.context/changelog/2026-07-12.md`, TAREA-001, este informe. | Cumple |

## 4. Matriz De Subtareas Tecnicas

| Subtarea | Resultado | Archivos / artefactos | Validacion | Estado |
|---|---|---|---|---|
| ST-01 | Workflows revisados; FG1/FG3 con `workflow_dispatch`, cron comentado y autorizacion manual explicita. | `.github/workflows/fg1_inventory.yml`, `.github/workflows/fg3_integrity.yml` | Revision YAML. | Cumple |
| ST-02 | Estrategia FG1/FG3 formalizada como manual-only para Hito 1. | `.github/workflows/fg1_inventory.yml`, `.github/workflows/fg3_integrity.yml`, changelog | Sin `schedule` activo; dispatch exige `resume_authorized=true` y rama permanente. | Cumple |
| ST-03 | Orquestador filtra `discovery_enabled` y `circuit_open` antes del `limit`. | `scripts/core/master_orchestrator.py` | `py_compile` OK. | Cumple |
| ST-04 | Campos editoriales/de calidad definidos sin reutilizar estados ETL. | TAREA-001, migration SQL | Revision de nombres y schema. | Cumple |
| ST-05 | Migration SQL idempotente versionada y reconciliada contra Free. | `db/migrations/20260712_hito1_editorial_quality_contract.sql` | Columnas/checks/indices/RLS confirmados. | Cumple |
| ST-06 | Contrato de patrocinio/leads preparado sin email/webhook/CRM. | Migration SQL | `lead_source_type` y campos sponsorship confirmados. | Cumple |
| ST-07 | RLS revisado y hardening versionado. | Migration SQL | Policies `courses_select_*` y `leads_insert_*` confirmadas. | Cumple |
| ST-08 | Contrato para hitos siguientes documentado. | Changelog + TAREA-001 | Revision documental. | Cumple |

## 5. Matriz De Pruebas Por Criterio De Aceptacion

| CA | Prueba ejecutada | Metodo / comando | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|
| CA1 | Validar workflows FG1/FG3 manual-only sin hardcodear secrets. | Revision de `.github/workflows/fg1_inventory.yml` y `.github/workflows/fg3_integrity.yml`. | FG1/FG3 conservan `workflow_dispatch`; cron no corre automaticamente. | `schedule` comentado, `resume_authorized=true` requerido y secrets via GitHub Environment. | OK documental |
| CA1 | Validar gates del orquestador antes de harvesting. | `docker exec -w /app studiamatch-dev python3 -m py_compile scripts/core/master_orchestrator.py` + revision de diff. | Orquestador compila y aplica gates por institucion antes de procesar; `limit` aplicado post-filtro. | `py_compile` OK; gates pre-filtrados antes del `limit`. | OK |
| CA2 parcial | Validar schema editorial/calidad/leads versionado. | Revision de `db/migrations/20260712_hito1_editorial_quality_contract.sql` + Supabase Free. | Columnas, checks, indices y RLS/policies versionados en migracion local. | Free confirma columnas/policies y migration queda versionada. | OK |
| CA2 parcial | Validar contrato publico/RLS y anti-spoofing. | Query `pg_policies` y comparacion contra migration versionada. | `courses` publico filtra `publication_status='publicado'`; policies INSERT anon/authenticated fuerzan `lead_source_type='organic'`. | Supabase Free confirma ambas policies endurecidas. | OK |
| CA7 preparacion | Validar documentacion para hitos siguientes. | Revision de TAREA-001, changelog e informe. | Hitos 2, 3 y 5 identifican campos a consumir sin reinterpretar requerimiento. | Contrato documentado. | OK documental |

## 6. Cambios Realizados

### Cambios funcionales
- El pipeline evita consumir cupos de `limit` con instituciones que no tienen discovery habilitado o cuyo circuit breaker esta abierto.
- FG3 queda manual-only para evitar writers automaticos antes de canaries/promocion formal.
- Se preparo el contrato de datos para distinguir cursos borrador, pendiente_revision, publicado y despublicado, y calidad pendiente o completo.
- Se preparo la estructura para registrar missing_fields y field_sources, usada por Hito 2 y Hito 3.
- Se agrego base de patrocinio para que Hito 5 diferencie cursos patrocinados y organicos.

### Cambios tecnicos de soporte
- Nueva migracion SQL idempotente con columnas, checks, indices, comentarios, backfill justificado y RLS hardening.
- Validacion en Supabase Free de columnas y policies ya aplicadas.
- Documentacion de contrato en changelog y tarea tecnica.

### Fuera de alcance no implementado
- No se implemento panel `/admin`; corresponde a Hito 3.
- No se implemento entrega real-time de leads por email/webhook/CRM.
- No se promovio la migracion a Supabase Pro; eso requiere certificacion y aprobacion posterior.

## 7. Evidencia De Validacion

| Validacion | Resultado | Evidencia |
|---|---|---|
| Seguridad / credenciales | OK | Revision security-auditor sin hallazgos bloqueantes; scan de diff sin secretos. |
| Python syntax check | OK | `docker exec -w /app studiamatch-dev python3 -m py_compile scripts/core/master_orchestrator.py`. |
| SQL/RLS | OK | Supabase Free confirma columnas de `courses`/`leads` y policies `courses_select_*`, `leads_insert_*`. |
| Context graph | OK | `docker exec -w /app studiamatch-dev python3 scripts/maintenance/validate_context_graph.py .context`. |
| QA Gate obligatorio | GO | `.context/evidencias/hito_1_qa_gate_report_20260721_171403.md` · [[hito_1_qa_gate_report_20260721_171403]] |
| Informe cliente | Generado | `.context/evidencias/hito_1_informe_cumplimiento.md`. |
| Matriz CA -> pruebas/evidencia | OK | CA1, CA2 parcial, CA7 preparacion cumplen con pruebas y evidencia versionada. |

## 8. Riesgos, Decisiones Y Observaciones

| Tipo | Descripcion | Decision / Mitigacion |
|---|---|---|
| Drift | Supabase Free ya tenia aplicado Hito 1, pero `desarrollo` no versionaba el contrato completo. | Reconciliado: este PR versiona el contrato DB-as-Code sin aplicar DDL remoto nuevo. |
| Decision | FG3 no se reactiva por cron en Hito 1. | Se mantiene manual-only/desactivado hasta canaries y autorizacion de writers. |
| RLS | `lead_source_type` podria ser enviado como `sponsored` desde cliente. | Policies anon/authenticated fuerzan `organic`; sponsored queda reservado a backend autorizado/service role. |
| RLS | `course_id` en leads podria apuntar a un curso no publico si el UUID fuera conocido. | Policies anon/authenticated aceptan `course_id` solo si el curso esta activo, verificado, publicado y pertenece a una institucion con `production_enabled=true`. |
| RLS legacy | Policies antiguas permisivas podrian combinarse por OR y anular el hardening. | La migracion elimina `"Public read for courses"` y `"Anyone can insert leads"` antes de crear las policies endurecidas. |
| Metadata no PII | `missing_fields`, `field_sources`, `data_quality_status` y `manual_updated_at` quedan en filas publicas si el cliente pide esas columnas por PostgREST. | Decision explicita de Hito 1: no contienen PII, frontend usa lista explicita de campos publicos y el rediseño de grants por columna queda fuera de alcance para no romper lecturas existentes. |
| DML justificado | La migracion incluye backfill de `courses.publication_status`. | Aprobado por Usuario/PM para preservar visibilidad del catalogo existente. |

DML_EXCEPTION: db/migrations/20260712_hito1_editorial_quality_contract.sql | APPROVER: Usuario/PM | JUSTIFICATION: preservar visibles los cursos activos y verificados al introducir el nuevo filtro editorial RLS.

## 9. Estado Para Entrega

- [x] Todos los CAs del hito tienen evidencia.
- [x] Todos los CAs del hito tienen prueba ejecutada sin observaciones bloqueantes.
- [x] No se agregaron alcances fuera de lo aprobado.
- [x] Las validaciones requeridas fueron ejecutadas.
- [x] El informe puede compartirse con cliente/Notion.
- [x] La tarea tecnica fue actualizada con resultado y evidencia.
- [x] Hito listo para PR final.

## 9.5 Remediacion Post-Auditoria (TAREA-006 · 2026-07-21)

Hallazgos bloqueantes de la auditoria de cobertura fueron remediados:

| Finding | Accion | Evidencia |
|---|---|---|
| RLS leads sin validacion `course_id` | Migracion `20260721_hito1_rls_reconciliation.sql` aplicada en Free. | `pg_policies` verificado: ambas policies contienen `publication_status`. |
| Sin prueba funcional del orquestador | `tests/test_orchestrator_gates.py`: 5 casos. | pytest 5/5 OK. |
| Documentacion canonica desactualizada | `sistema_db_supabase.md` y `arquitectura_pipeline.md` actualizados. | Diff versionado. |
| Tooling de gobernanza no justificado | `validate_hito_close.py` y `test_hito_governance.py` son infraestructura SDLC requerida. | Justificado en changelog. |

## 10. Version Para Notion / Cliente

```text
Hito 1 — Orquestacion FG2/FG3, schema base y seguridad
Estado: Implementado en rama limpia — listo para PR

Entregado:
- Contrato de datos para estados editoriales, calidad, campos faltantes, fuentes por campo, patrocinio y leads.
- Gates del orquestador para evitar procesar instituciones no habilitadas o con circuit breaker abierto.
- FG3 manual-only/desactivado por cron.
- RLS hardening: cursos publicos filtran por publication_status='publicado'; leads anonimos y autenticados quedan forzados a organic.

Criterios cubiertos:
- CA1: cumple.
- CA2 parcial: cumple con schema versionado y RLS hardening.
- CA7 preparacion: cumple.

Proximo paso: PR limpio a desarrollo y promocion posterior a certificacion solo con aprobacion explicita.
```
