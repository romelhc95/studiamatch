---
id: TAREA-001
fase: 1
estado: completado
prioridad: critica
estimacion_ref: est_001
requerimiento: req_est_001_sprint_1
hito: Hito 1
paquete: Paquete 1 - Orquestacion FG2/FG3, schema base y seguridad
cas: "CA1, CA2 parcial, CA7 preparacion"
fecha_inicio: 2026-07-11
fecha_limite: 2026-07-25
despliegue: "2026-07-27 09:00 PET"
responsable: IA implementadora
revisor: security-auditor
aprobador: Usuario/PM
skill_principal: devops-release-manager
subespecialidad: DevOps GitHub Actions + Supabase schema/RLS
skills_apoyo: "supabase-architect, security-auditor, pipeline-engineer"
gate_obligatorio: security-auditor
entregable: "PR a desarrollo con schema/workflows seguros y evidencia de validacion"
creado: 2026-07-11
tags: []
---

# Tarea 001: Hito 1 - Orquestacion FG2 FG3 schema base y seguridad

## Contexto
Estimacion de referencia: [[../../estimaciones/est_001]]

- **Requerimiento:** req_est_001_sprint_1
- **Hito:** Hito 1
- **Paquete:** Paquete 1 - Orquestacion FG2/FG3, schema base y seguridad
- **CAs cubiertos:** CA1, CA2 parcial, CA7 preparacion
- **Responsable de ejecucion:** IA implementadora
- **Revisor obligatorio:** security-auditor
- **Aprobador:** Usuario/PM
- **Entregable:** PR a desarrollo con schema/workflows seguros y evidencia de validacion

## Skills y sub-especialidad
- **Skill principal:** devops-release-manager
- **Sub-especialidad tecnica:** DevOps GitHub Actions + Supabase schema/RLS
- **Skills de apoyo:** supabase-architect, security-auditor, pipeline-engineer
- **Gate obligatorio:** security-auditor

## Plazos
- **Inicio comprometido:** 2026-07-11
- **Fecha limite de construccion:** 2026-07-25
- **Despliegue objetivo:** 2026-07-27 09:00 PET

## Dependencias
- Aprobacion de EST-001 y activacion del Sprint 1

## Criterios de Aceptacion
- [x] Schedules del harvester/pipeline quedan definidos o reactivados sin saltarse gates ni exponer credenciales
- [x] Schema soporta estado editorial/calidad, campos faltantes, fuentes manual/scraping, timestamps y proxima fecha de inicio
- [x] Leads/flag de patrocinio quedan preparados sin implementar entrega real-time fuera de alcance
- [x] No se reutilizan estados ETL como estado editorial publico.
- [x] El cambio SQL queda versionado en `db/migrations/` y reconciliado contra Supabase Free.
- [x] El resultado queda documentado para consumo de Hitos 2, 3 y 5.

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
| CA1 | Validar workflows FG2 y decision FG1/FG3 sin hardcodear secrets. | Workflow/DevOps | Revisar `.github/workflows/production_pipeline.yml`, `.github/workflows/fg1_inventory.yml` y `.github/workflows/fg3_integrity.yml`. | FG2 conserva environment/secrets por GitHub Environment; FG1/FG3 quedan manual-only con autorizacion explicita. | Tabla de decision en changelog e informe. |
| CA1 | Validar gates del orquestador antes de harvesting. | Pipeline Python | `docker exec -w /app studiamatch-dev python3 -m py_compile scripts/core/master_orchestrator.py` + revision de diff. | Orquestador compila y filtra gates antes de procesar instituciones. | Salida `py_compile` y diff del archivo. |
| CA2 parcial | Validar schema editorial/calidad/leads versionado. | DB migration | Revisar `db/migrations/20260712_hito1_editorial_quality_contract.sql` y consultar Supabase Free. | Columnas, checks, indices y RLS/policies estan versionados o documentados como ya aplicados. | Migration diff + queries a `information_schema`, `pg_constraint`, `pg_indexes`, `pg_policies`. |
| CA2 parcial | Validar contrato publico/RLS y anti-spoofing. | RLS/security | Query `pg_policies` y comparacion contra migration versionada. | `courses` publico filtra por estado editorial aprobado; `leads_insert_public` no permite patrocinio anonimo ni `course_id` no publico. | Resultado query + fragmento versionado en migration. |
| CA7 preparacion | Validar documentacion para hitos siguientes. | Documental | Revisar TAREA-001, changelog e informe. | Hitos 2, 3 y 5 identifican campos a consumir sin reinterpretar requerimiento. | Enlaces/secciones actualizadas. |

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `.github/workflows/production_pipeline.yml` | Validacion/ajuste de schedules y environment gating |
| `.github/workflows/fg3_integrity.yml` | Formalizacion de estado activo/inactivo segun alcance aprobado |
| `db/migrations/` | Nueva migracion para campos editoriales/calidad/leads si aplica |
| `scripts/core/master_orchestrator.py` | Validacion de gates, limites y circuit breaker |

## Plan de ejecucion
1. Confirmar alcance contra la estimacion aprobada.
2. Implementar el cambio minimo que satisfaga los criterios.
3. Ejecutar validaciones aplicables en el contenedor Docker.
4. Invocar revision de seguridad antes de commit/PR.
5. Registrar resultado en changelog.

## Validaciones requeridas
- [x] `docker exec -w /app studiamatch-dev python3 -m py_compile scripts/core/master_orchestrator.py`.
- [x] Revision YAML de `.github/workflows/fg3_integrity.yml` para confirmar que `schedule` queda comentado y solo opera `workflow_dispatch`.
- [x] Revision YAML de `.github/workflows/fg1_inventory.yml` para confirmar que `schedule` queda comentado y solo opera `workflow_dispatch`.
- [x] Revision YAML de `.github/workflows/fg3_integrity.yml` para confirmar que `workflow_dispatch` exige `resume_authorized=true` y rama permanente.
- [x] Revision SQL/RLS de `db/migrations/20260712_hito1_editorial_quality_contract.sql` contra Supabase Free.
- [x] Ejecucion de `docker exec -w /app studiamatch-dev python3 scripts/maintenance/validate_context_graph.py .context` tras cambios en `.context`.
- [x] Ejecucion de `docker exec -w /app studiamatch-dev python3 scripts/maintenance/validate_hito_close.py --hito 1` con reporte GO versionado.
- [x] Revision de seguridad sin hallazgos bloqueantes.

## Evidencia requerida
- [x] Tabla de workflows revisados y decision aplicada.
- [x] Lista exacta de tablas/columnas/tipos/checks/indices agregados y razon por CA.
- [x] Resumen de impacto RLS/RPC sin hallazgos bloqueantes.
- [x] Confirmacion de reutilizacion de `start_date`/`start_date_text`.
- [x] Salida de validaciones ejecutadas.
- [x] Informe de cumplimiento en `.context/evidencias/hito_1_informe_cumplimiento.md`.
- [x] Resultado de cada prueba por CA en informe: OK / no aplica justificado.

## Checklist de cierre
- [x] CA1 cubierto con FG3 manual-only y gates del orquestador.
- [x] CA2 parcial cubierto con schema versionado y contrato publico/RLS resuelto.
- [x] CA7 preparacion cubierto con contrato documentado para Hitos 2, 3 y 5.
- [x] No se implementa entrega real-time de leads.
- [x] No quedan credenciales ni secrets.
- [x] Changelog actualizado.
- [x] Informe de cumplimiento generado antes de marcar PR listo para entrega interna.
- [x] Ningun CA queda sin prueba y evidencia.

## Notas de implementacion
- Port limpio desde `origin/desarrollo` en rama `feat/hito-1-foundation-v2`.
- Se tomo `#203` solo como fuente tecnica; no se hizo merge ni cherry-pick de la cadena antigua `#202` -> `#203`.
- Supabase Free ya tenia aplicada la migracion `20260712221039 hito1_editorial_quality_contract` y hardenings posteriores; este PR reconcilia el contrato como DB-as-Code en `desarrollo`.
- `courses.start_date` y `courses.start_date_text` se reutilizan como proxima fecha estructurada/textual; no se crea `next_start_date`.
- DML_EXCEPTION: db/migrations/20260712_hito1_editorial_quality_contract.sql | APPROVER: Usuario/PM | JUSTIFICATION: preservar visibles los cursos activos y verificados al introducir el nuevo filtro editorial RLS.

## Resultado
**Fecha**: 2026-07-21 | **Estado**: Implementado en rama limpia | **Ambiente validado**: Supabase Free

### Cambios asociados a Hito 1
| Archivo | Cambio |
|---|---|
| `.github/workflows/fg3_integrity.yml` | Cron comentado; queda manual-only con `workflow_dispatch`, `resume_authorized=true` y rama permanente. |
| `.github/workflows/fg1_inventory.yml` | Cron comentado; queda manual-only con `workflow_dispatch`, `resume_authorized=true` y rama permanente. |
| `scripts/core/master_orchestrator.py` | Filtra `discovery_enabled` y `circuit_open` antes de aplicar `limit`; conserva metadata de gates para workers posteriores. |
| `db/migrations/20260712_hito1_editorial_quality_contract.sql` | Versiona contrato editorial/calidad/patrocinio/leads, checks, indices, backfill idempotente y RLS hardening. |
| `.context/evidencias/hito_1_informe_cumplimiento.md` | Evidencia actualizada para la version limpia v2. |
| `scripts/maintenance/validate_hito_close.py` | Gate mecanico adaptado al backlog por requerimiento. |

### Evidencias vinculadas
- [[../../changelog/2026-07-12]]
- [[../../evidencias/hito_1_informe_cumplimiento]]

### Pendiente para promocion
- La promocion a `certificacion` y luego a Supabase Pro debe hacerse en PRs separados tras aprobacion explicita y con evidencia nueva de cada ambiente.
