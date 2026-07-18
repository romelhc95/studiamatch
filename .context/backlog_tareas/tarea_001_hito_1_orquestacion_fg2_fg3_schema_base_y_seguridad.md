---
id: TAREA-001
fase: 1
estado: completado
prioridad: critica
estimacion_ref: est_001
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
Estimacion de referencia: [[../estimaciones/est_001]]

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

## Fuentes del requerimiento
- Documento fuente: `requerimientos/30062026/Studiamatch_MVP_Requerimientos_v5.pdf`.
- Seccion 2: estado actual y pendiente critico de schedules automaticos desactivados.
- Seccion 8.3: cambios en schema Supabase (`status`, `campos_faltantes`, sources, timestamps, `proxima_fecha_inicio`).
- Seccion 10: CA1 y CA2.

## Matriz CA -> detalle implementable
| CA | Detalle exacto del requerimiento | Implicancia tecnica | Fuera de alcance |
|---|---|---|---|
| CA1 | Reactivar schedules automaticos del harvester. | Revisar/ajustar workflows FG2/FG3 sin saltar gates ni secrets por environment. | Cambiar logica de scraping fuera de gates. |
| CA2 parcial | Schema Supabase: status, source, updated_at, fecha, tabla leads y flag de datos criticos incompletos. | Agregar contrato SQL exacto para estado editorial/calidad, faltantes, fuentes, timestamps y patrocinio/leads base. | Implementar admin, pipeline completo de faltantes o entrega real-time. |

## Alcance incluido
- Definir o reactivar schedules del pipeline FG2/FG3 conforme a CA1, respetando gates por institucion y secrets por environment.
- Incorporar schema base para estado editorial, calidad de datos, campos faltantes, fuentes de datos y proxima fecha de inicio conforme a CA2 parcial.
- Preparar campos o contrato minimo para patrocinio/leads sin entrega real-time.
- Dejar evidencia tecnica para que Hito 2 y Hito 3 consuman los nuevos campos sin reinterpretar el requerimiento.

## Alcance excluido
- No implementar la deteccion completa de campos vacios del pipeline; corresponde a TAREA-002.
- No implementar panel `/admin`; corresponde a TAREA-003.
- No implementar entrega real-time de leads por email, webhook o CRM.
- No sincronizar datos operativos Free -> Pro como mecanismo normal.
- No publicar cursos incompletos automaticamente sin reglas de calidad definidas.

## Criterios de Aceptacion
- [x] Schedules del harvester/pipeline quedan definidos o reactivados sin saltarse gates ni exponer credenciales
- [x] Schema soporta estado editorial/calidad, campos faltantes, fuentes manual/scraping, timestamps y proxima fecha de inicio
- [x] Leads/flag de patrocinio quedan preparados sin implementar entrega real-time fuera de alcance
- [x] No se reutilizan estados ETL (`pending`, `processing`, `synced`) como estado editorial publico.
- [x] Cualquier cambio SQL queda versionado en `db/migrations/` y revisado por `supabase-architect`/`security-auditor`.
- [x] El resultado queda documentado para consumo de TAREA-002 y TAREA-003.

## Matriz CA -> pruebas/evidencia
| CA | Prueba obligatoria | Tipo | Metodo / comando | Resultado esperado | Evidencia requerida |
|---|---|---|---|---|---|
| CA1 | Validar workflow FG2 y decision FG3 sin hardcodear secrets. | Workflow/DevOps | Revisar `.github/workflows/production_pipeline.yml` y `.github/workflows/fg3_integrity.yml`. | FG2 con schedule/environment/secrets por GitHub Environment; FG3 documentado como manual-only o activo segun decision. | Tabla de decision en changelog e informe. |
| CA1 | Validar gates del orquestador antes de harvesting. | Pipeline Python | `docker exec studiamatch-dev python3 -m py_compile scripts/core/master_orchestrator.py` + revision de diff. | Orquestador compila y filtra gates antes de procesar instituciones. | Salida `py_compile` y diff del archivo. |
| CA2 parcial | Validar schema editorial/calidad/leads versionado. | DB migration | Revisar `db/migrations/20260712_hito1_editorial_quality_contract.sql`. | Columnas, checks, indices, RLS/policies/backfill requeridos estan versionados o explicitamente observados. | Migration diff + queries a `information_schema`, `pg_constraint`, `pg_indexes`, `pg_policies`. |
| CA2 parcial | Validar contrato publico/RLS y anti-spoofing. | RLS/security | Query `pg_policies` y comparacion contra migration versionada. | `courses` publico filtra estado aprobado y `leads_insert_public` no permite `sponsored` anon sin autorizacion. | Resultado query + fragmento versionado en migration. |
| CA7 preparacion | Validar documentacion para hitos siguientes. | Documental | Revisar TAREA-001, changelog e informe. | TAREA-002/003/005 pueden identificar que campos consumir sin reinterpretar requerimiento. | Enlaces/secciones actualizadas. |

## Analisis tecnico previo obligatorio
- [x] Revisar `.context/estimaciones/est_001.md` lineas de Paquete 1, CA1, CA2 parcial y preparacion CA7.
- [x] Revisar `.context/sistema_db_supabase.md` para confirmar columnas existentes en `courses` y `leads` antes de proponer migration.
- [x] Revisar `.context/arquitectura_pipeline.md` para confirmar estado real de FG2/FG3, gates, jobs, triggers y workers.
- [x] Revisar `.github/workflows/production_pipeline.yml` y `.github/workflows/fg3_integrity.yml` para confirmar triggers, environments, secrets y dependencias actuales.
- [x] Revisar `scripts/core/master_orchestrator.py` para confirmar enforcement de `pipeline_ready`, freshness guard, circuit breaker y limites.
- [x] Confirmar si `courses.start_date` y `courses.start_date_text` existen en codigo/schema real; si existen, se reutilizan como proxima fecha de inicio y no se duplican.
- [x] Confirmar si ya existe algun equivalente a `publication_status`, `data_quality_status`, `missing_fields`, `field_sources`, `manual_updated_at`, `is_sponsored` o `lead_source_type`; si existe, documentar reutilizacion en vez de duplicar.

## Especificacion exacta del cambio

### Workflows
| Archivo | Cambio exacto esperado |
|---|---|
| `.github/workflows/production_pipeline.yml` | Verificar que el schedule de FG2 queda definido segun CA1, que usa GitHub Environment por branch (`Development`, `Certification`, `Production`) y que no hardcodea secrets. Si ya esta correcto, documentar sin modificar. |
| `.github/workflows/fg3_integrity.yml` | Formalizar decision de FG3: mantener `workflow_dispatch` y activar/desactivar schedule solo segun alcance aprobado. Si se mantiene manual-only, documentar explicitamente que el cron no corre automaticamente. |

### Orquestador
| Archivo | Cambio exacto esperado |
|---|---|
| `scripts/core/master_orchestrator.py` | No cambiar logica salvo que el analisis demuestre falta de enforcement. Si cambia, asegurar checks de `pipeline_ready`, freshness guard, circuit breaker y limite de corrida antes de lanzar workers. |

### Migracion SQL propuesta
Archivo esperado: `db/migrations/YYYYMMDD_hito1_editorial_quality_contract.sql`.

Tabla `courses`:
| Columna | Tipo | Nullability/default | Check/Notas |
|---|---|---|---|
| `publication_status` | `text` | `NOT NULL DEFAULT 'borrador'` | `chk_courses_publication_status`: valores `borrador`, `pendiente_revision`, `publicado`, `despublicado`. No reutilizar estados ETL. |
| `data_quality_status` | `text` | `NOT NULL DEFAULT 'pendiente'` | `chk_courses_data_quality_status`: valores `pendiente`, `completo`. |
| `missing_fields` | `jsonb` | `NOT NULL DEFAULT '[]'::jsonb` | `chk_courses_missing_fields_array`: `jsonb_typeof(missing_fields) = 'array'`. |
| `field_sources` | `jsonb` | `NOT NULL DEFAULT '{}'::jsonb` | `chk_courses_field_sources_object`: `jsonb_typeof(field_sources) = 'object'`. Ejemplo esperado por Hito 2/3: `{"price_pen":"scraping","duration":"manual"}`. |
| `manual_updated_at` | `timestamptz` | `NULL` | Timestamp de ultima curacion manual admin. |
| `is_sponsored` | `boolean` | `NOT NULL DEFAULT false` | Flag base para CA10 futuro; no implementa logica comercial avanzada. |
| `sponsorship_priority` | `integer` | `NOT NULL DEFAULT 0` | `chk_courses_sponsorship_priority_nonnegative`: `sponsorship_priority >= 0`. |
| `sponsorship_label` | `text` | `NULL` | `chk_courses_sponsorship_label_length`: `sponsorship_label IS NULL OR char_length(sponsorship_label) <= 80`. |

Reutilizacion obligatoria:
- Reutilizar `courses.start_date` como fecha estructurada de proximo inicio si existe.
- Reutilizar `courses.start_date_text` como texto original de fecha si existe.
- No crear `next_start_date` salvo que el analisis confirme que `start_date` no existe en el schema real.

Tabla `leads`:
| Columna | Tipo | Nullability/default | Check/Notas |
|---|---|---|---|
| `lead_source_type` | `text` | `NOT NULL DEFAULT 'organic'` | `chk_leads_source_type`: valores `organic`, `sponsored`. Solo clasificacion base, sin email/webhook/CRM. |

Indices esperados:
| Indice | Tabla | Definicion |
|---|---|---|
| `idx_courses_publication_quality` | `courses` | B-tree `(publication_status, data_quality_status)` con `WHERE is_active = true`. |
| `idx_courses_missing_fields_gin` | `courses` | GIN sobre `missing_fields`. |
| `idx_courses_sponsored_priority` | `courses` | B-tree `(is_sponsored, sponsorship_priority DESC)` con `WHERE is_active = true`. |
| `idx_leads_source_type_created_at` | `leads` | B-tree `(lead_source_type, created_at DESC)`. |

Idempotencia SQL:
- Usar `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` para columnas.
- Usar `CREATE INDEX IF NOT EXISTS` para indices.
- Para checks, usar bloque `DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '...') THEN ALTER TABLE ... ADD CONSTRAINT ...; END IF; END $$;`.
- No insertar datos operativos.
- No hardcodear UUIDs.
- No tocar datos de `staging_raw`, `cleansed_programs`, `enriched_programs` ni `courses` salvo DDL.

RLS/RPC/grants:
- No abrir `UPDATE` anon sobre `courses`.
- No abrir lectura publica de PII en `leads`.
- Si se crea RPC para Hito 3, solo dejar contrato documentado en este hito; implementacion de RPC admin queda para TAREA-003 salvo que sea indispensable para CA2.
- Mantener anon SELECT publico condicionado por politicas existentes (`is_active`/`is_verified`) hasta que una tarea posterior ajuste consumo frontend.

## Subtareas tecnicas
- [x] **ST-01 — Auditar estado real de workflows**
  - Analisis previo: revisar triggers `schedule`, `workflow_dispatch`, branch/environment mapping, secrets usados y dependencias de jobs.
  - Objetivo: comparar `production_pipeline.yml` y `fg3_integrity.yml` contra CA1 y `.context/arquitectura_pipeline.md`.
  - Cambio exacto: documentar si FG2 ya cumple; si no cumple, ajustar schedule/environment sin cambiar comandos de workers fuera de alcance.
  - Archivos esperados: `.github/workflows/production_pipeline.yml`, `.github/workflows/fg3_integrity.yml`.
  - CAs relacionados: CA1.
  - Validacion: resumen de discrepancias y decision documentada antes de editar.
- [x] **ST-02 — Definir estrategia segura para FG3**
  - Analisis previo: contrastar PDF/EST-001 con `.context/estado_del_proyecto.md`, donde FG3 figura desactivado aunque existe workflow.
  - Objetivo: decidir si FG3 queda activo, manual-only o formalmente desactivado dentro del hito.
  - Cambio exacto: dejar `workflow_dispatch`; activar cron solo si el alcance aprobado lo exige, o comentar/documentar modo manual-only sin ambiguedad.
  - Archivos esperados: `.github/workflows/fg3_integrity.yml`, changelog.
  - CAs relacionados: CA1, CA7 preparacion.
  - Validacion: workflow no ejecuta acciones destructivas inesperadas y conserva `workflow_dispatch` si aplica.
- [x] **ST-03 — Verificar gates y limites de orquestacion**
  - Analisis previo: ubicar en `master_orchestrator.py` los checks de `pipeline_ready`, freshness guard, circuit breaker y limites de corrida antes de modificar.
  - Objetivo: asegurar que `master_orchestrator.py` respeta `pipeline_ready`, freshness guard, circuit breaker y limites de corrida.
  - Cambio exacto: si falta algun check, agregarlo antes de iniciar harvesting por institucion; si ya existe, documentar evidencia y no modificar.
  - Archivos esperados: `scripts/core/master_orchestrator.py` si requiere ajuste.
  - CAs relacionados: CA1.
  - Validacion: `python3 -m py_compile scripts/core/master_orchestrator.py`.
- [x] **ST-04 — Disenar campos editoriales y de calidad**
  - Analisis previo: verificar columnas actuales de `courses` y `leads`; confirmar inexistencia o reutilizacion de campos equivalentes.
  - Objetivo: definir nombres no ambiguos para estado editorial/calidad, faltantes, fuentes y timestamp manual.
  - Cambio exacto: aprobar los nombres `publication_status`, `data_quality_status`, `missing_fields`, `field_sources`, `manual_updated_at`, `is_sponsored`, `sponsorship_priority`, `sponsorship_label`, `lead_source_type` segun especificacion exacta.
  - Archivos esperados: migration nueva en `db/migrations/`.
  - CAs relacionados: CA2 parcial.
  - Validacion: revision de nombres contra schema actual y ausencia de colision con tablas ETL.
- [x] **ST-05 — Implementar migracion SQL idempotente**
  - Analisis previo: confirmar schema real antes de escribir DDL; si una columna ya existe, no duplicarla y documentar reutilizacion.
  - Objetivo: agregar el contrato SQL minimo para estado editorial/calidad, faltantes, fuente manual/scraping y patrocinio base.
  - Cambio exacto: crear `db/migrations/YYYYMMDD_hito1_editorial_quality_contract.sql` con las columnas, checks e indices listados en `Especificacion exacta del cambio`.
  - Archivos esperados: `db/migrations/YYYYMMDD_*.sql`.
  - CAs relacionados: CA2 parcial.
  - Validacion: SQL idempotente con `ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, checks protegidos por `pg_constraint`, sin IDs hardcodeados ni datos operativos.
- [x] **ST-06 — Preparar contrato de patrocinio/leads**
  - Analisis previo: revisar uso actual de `leads.source_page`, CTAs y posibles campos existentes de patrocinio.
  - Objetivo: agregar flag/campo minimo para distinguir patrocinio o preparar leads sin automatizacion comercial.
  - Cambio exacto: agregar `courses.is_sponsored`, `courses.sponsorship_priority`, `courses.sponsorship_label` y `leads.lead_source_type` segun tipos/checks definidos; no agregar webhook/email/CRM.
  - Archivos esperados: `db/migrations/`, documentacion/changelog.
  - CAs relacionados: CA2 parcial, preparacion CA10.
  - Validacion: no se expone PII adicional ni se abre lectura publica insegura.
- [x] **ST-07 — Revisar RLS/RPC y permisos**
  - Analisis previo: revisar policies/grants actuales de `courses` y `leads`; confirmar que los nuevos campos no requieren abrir permisos nuevos para publico.
  - Objetivo: conservar anon SELECT solo para catalogo publico y evitar escrituras privilegiadas desde browser.
  - Cambio exacto: no agregar `UPDATE` anon; no cambiar lectura publica de `leads`; documentar que RPC admin se implementara en TAREA-003 si hace falta.
  - Archivos esperados: migration si requiere grants/policies/RPC.
  - CAs relacionados: CA2 parcial.
  - Validacion: revision `security-auditor`; no secret key en frontend/workflows.
- [x] **ST-08 — Documentar contrato para hitos siguientes**
  - Analisis previo: mapear cada campo nuevo al hito que lo consume: TAREA-002 escribe/calcula, TAREA-003 edita/publica, TAREA-005 muestra patrocinio.
  - Objetivo: dejar claro que campos debe llenar TAREA-002 y que consumira TAREA-003.
  - Cambio exacto: actualizar changelog/resultado con contrato de datos: `missing_fields`, `field_sources`, `publication_status`, `data_quality_status`, `manual_updated_at`, campos sponsorship y `lead_source_type`.
  - Archivos esperados: `.context/changelog/`, seccion Resultado de esta tarea.
  - CAs relacionados: CA7 preparacion.
  - Validacion: checklist de cierre completo.

## Archivos afectados
| Archivo | Tipo de cambio |
|---|---|
| `.github/workflows/production_pipeline.yml` | Validacion/ajuste de schedules y environment gating |
| `.github/workflows/fg3_integrity.yml` | Formalizacion de estado activo/inactivo segun alcance aprobado |
| `db/migrations/` | Nueva migracion para campos editoriales/calidad/leads si aplica |
| `scripts/core/master_orchestrator.py` | Validacion de gates, limites y circuit breaker |

## Plan de ejecucion
1. Leer EST-001, CA1/CA2 parcial y esta tarea antes de tocar codigo.
2. Ejecutar y documentar el analisis tecnico previo completo.
3. Resolver la decision FG3 activo/manual-only/desactivado antes de editar workflows.
4. Confirmar/reutilizar columnas existentes antes de escribir migration.
5. Ejecutar subtareas en orden, priorizando cambios minimos e idempotentes.
6. Validar workflow/schema/RLS segun cada subtarea.
7. Ejecutar validaciones finales dentro del contenedor Docker.
8. Invocar revision de seguridad antes de commit/PR.
9. Registrar resultado en changelog y en esta tarea.

## Validaciones requeridas
- [x] `docker exec studiamatch-dev python3 -m py_compile scripts/core/master_orchestrator.py` si se modifica el orquestador.
- [x] Validacion manual de YAML si se modifican workflows.
- [x] Revision SQL/RLS por `supabase-architect` si se agregan migraciones.
- [x] Revision obligatoria de `security-auditor` antes de commit/PR.
- [x] Ejecucion completa de matriz `CA -> pruebas/evidencia` sin contradicciones entre DB aplicada y migration versionada.

## Evidencia requerida
- [x] Tabla de workflows revisados y decision aplicada.
- [x] Lista exacta de tablas/columnas/tipos/checks/indices agregados y razon por CA.
- [x] Resumen de impacto RLS/RPC sin hallazgos bloqueantes.
- [x] Confirmacion de reutilizacion o no de `start_date`/`start_date_text`.
- [x] Salida de validaciones ejecutadas.
- [x] Rama `feat/hito-1-foundation` preparada; PR se crea despues del gate final.
- [x] Informe de cumplimiento para cliente en `.context/evidencias/hito_1_informe_cumplimiento.md` con matriz CA -> cambio -> evidencia.
- [x] Resultado de cada prueba por CA en informe: OK / observado / no aplica justificado.

## Checklist de cierre
- [x] CA1 cubierto o excepcion aprobada documentada.
- [x] CA2 parcial cubierto con schema versionado y contrato publico/RLS resuelto.
- [x] Analisis previo y especificacion exacta completados antes de implementar.
- [x] TAREA-002 puede saber que campos llenar.
- [x] TAREA-003 puede saber que campos mostrar/editar.
- [x] No se implementa entrega real-time de leads.
- [x] No quedan credenciales ni secrets.
- [x] Changelog actualizado.
- [x] Informe de cumplimiento generado antes de marcar PR listo para entrega interna.
- [x] Ningun CA queda sin prueba y evidencia.

## Notas de implementacion
<!-- Detalles tecnicos aqui -->

## Resultado
**Fecha**: 2026-07-12 | **Estado**: Implementado | **Ambiente**: Supabase Free

### Subtareas completadas
- [x] ST-01 — Auditoria workflows: FG2 correcto (schedule diario + environment mapping). FG3 desactivado (cron con comentario `⛔ DESACTIVADO`).
- [x] ST-02 — FG3 manual-only formalizado. Cron permanece desactivado. `workflow_dispatch` activo.
- [x] ST-03 — Seleccion corregida en `master_orchestrator.py`: `discovery_enabled` y `circuit_open` filtran antes del limit; `pipeline_enabled=false` conserva discovery-only y el harvester omite scraping detallado/ETL.
- [x] ST-04 — Campos editoriales disenados: `publication_status`, `data_quality_status`, `missing_fields`, `field_sources`, `manual_updated_at`, `is_sponsored`, `sponsorship_priority`, `sponsorship_label`, `lead_source_type`. Nombres sin colision.
- [x] ST-05 — Migracion SQL idempotente creada y aplicada. Columnas, checks (con `conrelid`), indices versionados.
- [x] ST-06 — Contrato patrocinio/leads implementado: sponsorship fields en courses + `lead_source_type` en leads con RLS anti-spoofing. Analisis previo: `leads.source_page` (text, nullable) captura URL de origen del lead. No existen columnas CTA en leads. Campos de patrocinio no existian antes de HITO 1; los 3 nuevos son los unicos.
- [x] ST-07 — RLS revisado. No se abre UPDATE anon ni SELECT publico de PII. Hardening aplicado.
- [x] ST-08 — Changelog + contrato documentado para TAREA-002/003/005.
- [x] ST-09 — Contrato publico RLS versionado en migration: `courses_select_public` y `courses_select_authenticated` filtran `publication_status='publicado'`. Backfill de cursos existentes activos+verificados a `publicado` incluido en migration (lineas 119-122).
- [x] ST-10 — Anti-spoofing versionado en migration: `leads_insert_public` y `leads_insert_authenticated` fuerzan `lead_source_type='organic'`; patrocinio queda reservado a backend autorizado/service role.
- [x] ST-11 — Evidencia reconciliada: migration local (181 lineas) contiene DDL + backfill + RLS hardening de 4 policies. Supabase Free, migration local, informe y changelog coinciden.
- [x] ST-12 — `limit` corregido y versionado: `get_institutions()` filtra elegibilidad de discovery/circuit breaker antes de aplicar `limit`, sin consumir el contrato discovery-only. `py_compile` OK.

### Archivos modificados
| Archivo | Cambio |
|---|---|
| `scripts/core/master_orchestrator.py` | Elegibilidad discovery/circuit breaker pre-filtrada antes del `limit`; discovery-only preservado |
| `db/migrations/20260712_hito1_editorial_quality_contract.sql` | Migracion completa (181 lineas): +8 columnas courses, +1 leads, +7 checks (con `conrelid`), +4 indices, backfill cursos existentes a `publicado`, RLS hardening (4 policies) |
| `.context/changelog/2026-07-12.md` | Documentacion Hito 1 agregada |
| `.context/backlog_tareas/tarea_001_*.md` | Resultado actualizado (12/12 subtareas) |
| `.context/evidencias/hito_1_informe_cumplimiento.md` | Informe de cumplimiento cliente (CA1/CA2/CA7 con pruebas y evidencia) |
| Supabase Free | Migration + RLS hardening aplicado y verificado via `information_schema`, `pg_constraint`, `pg_indexes`, `pg_policies` |

### Validaciones ejecutadas
- [x] `docker exec studiamatch-dev python3 -m py_compile scripts/core/master_orchestrator.py` — sin errores
- [x] Migracion aplicada en Supabase Free — 8 columnas courses, 1 leads, 7 constraints, 4 indices y RLS/backfill confirmados; migration versionada endurece tambien authenticated.
- [x] Security audit: 0 hallazgos (3/3 archivos limpios, sin credenciales hardcodeadas). RLS hardening versionado en migration local.
- [x] RLS/contrato publico resuelto y versionado: `publication_status='publicado'` en filtro SELECT, `lead_source_type='organic'` en WITH CHECK INSERT
- [x] Idempotencia SQL confirmada: migracion reaplicable sin errores, constraints con `conrelid`

### Reutilizaciones confirmadas
- `courses.start_date` (DATE) — existe, se reutiliza como fecha estructurada
- `courses.start_date_text` (varchar) — existe, se reutiliza como texto original
- NO se creo `next_start_date`

### Pendiente para promocion a Pro
- Migracion `db/migrations/20260712_hito1_editorial_quality_contract.sql` debe aplicarse en Supabase Pro tras aprobacion de certificacion.

### Observaciones y desviaciones documentadas
- DML_EXCEPTION: db/migrations/20260712_hito1_editorial_quality_contract.sql | APPROVER: Usuario/PM | JUSTIFICATION: preservar visibles los cursos activos y verificados al introducir el nuevo filtro editorial RLS.
- [x] **Justificado**: Backfill DML (lineas 119-122 migration) actualiza `courses.publication_status` de `borrador` a `publicado` para 227 cursos activos+verificados. Desviacion de "no tocar datos salvo DDL" (linea 155). **Justificacion**: sin este backfill, el filtro RLS `publication_status='publicado'` ocultaria todo el catalogo existente. El UPDATE es idempotente (`WHERE publication_status = 'borrador'`) y solo afecta cursos que ya eran publicos antes de que existiera el campo.
- [x] **Baja**: Checks SQL con `conrelid` — resuelto en migration local: 7 verificaciones incluyen `conrelid = 'public.<tabla>'::regclass`.
- [x] **Baja**: `limit` antes de gates — resuelto en `get_institutions()`. Filtra gates (L55-62), luego sort (L69), luego `eligible[:limit]` (L70).
