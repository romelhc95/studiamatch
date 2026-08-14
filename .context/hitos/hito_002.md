# HITO-002 - Calidad Editorial Y Pipeline De Campos Vacios

`HITO-002` recibe el alcance `H2-CA2` y `H2-CA3` definido por la adenda. Su
estado es `PENDING_REBASELINE`; esta nota no activa una subfase ni autoriza
ejecucion.

## Alcance Recibido H2-CA2

- Los `104/224` cursos activos con syllabus/objectives incompletos del snapshot
  historico F10.9 (`102` sin syllabus y `2` sin syllabus ni objectives),
  reclasificados `TRANSFERRED_NON_BLOCKING_H2_CA2`.
- Metadata incompleta, fuentes y lineage por campo.
- Providers y revision editorial humana.
- Fill-only/backfill y reconciliacion de calidad.
- Cohortes por target, pilot, lotes, restore e idempotencia.
- Cualquier reader/ACL futuro bajo un rebaseline nuevo.

La deuda permanece visible y no bloquea Hito 1. Los conteos historicos no son una
cohorte vigente ni una allowlist.

## No Herencia Operativa

[ADR-0011](../decisiones/ADR-0011_rebaseline_superior_hito1_ca1_f10_10_a_h2.md)
prohibe reutilizar gates, payloads, readers, roles, ACL, credentials, bindings,
cohortes o aprobaciones F10.10/M3. ADR-0010 y sus planes son antecedentes de
investigacion, no autoridad de ejecucion H2.

El estado y los criterios de Hito 2 se consultan en
[TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md).
