# Matriz Hito 002

Veredicto: `IMPLEMENTED_AND_VALIDATED_IN_DEVELOPMENT`.

Veredicto PR: `GO_TECHNICAL_FOR_PROTECTED_PR`.

Grado de evidencia: `A`.

| Unidad | Control | Estado | Evidencia verificable | Traduccion para cliente |
|---|---|---|---|---|
| `H2-CA2` | Modelo editorial separado | `PASS_IN_DEVELOPMENT` | `course_editorial_state`, `editorial_field_definitions`, `course_editorial_audit` y `courses_public_effective` aplicados en Free. | El negocio puede revisar y controlar cada programa antes de publicarlo. |
| `H2-CA2` | Estados editoriales y de calidad | `PASS_IN_DEVELOPMENT` | Estados `draft`, `pending_review`, `published`, `archived`; calidad `complete`, `pending`, `blocked`. | Hay una cola clara entre pendiente, revisado y publicado. |
| `H2-CA2` | Campos faltantes | `PASS_IN_DEVELOPMENT` | `missing_fields` calculado por contrato H2; `duration=219` detectado en Free. | Se sabe exactamente que dato falta para completar cada programa. |
| `H2-CA2` | Fuentes y trazabilidad | `PASS_IN_DEVELOPMENT` | `field_sources` y `field_timestamps` preservados en `350/350` estados. | Se puede distinguir informacion automatica de informacion revisada. |
| `H2-CA2` | Proteccion de datos manuales | `PASS_IN_DEVELOPMENT` | Tests de precedencia manual y guard de `archived` antes de `upsert`. | El pipeline no borra decisiones editoriales ni programas archivados. |
| `H2-CA2` | Auditoria append-only | `PASS_IN_DEVELOPMENT` | `course_editorial_audit`; triggers bloquean update/delete; pruebas PG17 pasan. | Los cambios editoriales quedan trazables. |
| `H2-CA2` | Privacidad de superficie publica | `PASS_IN_DEVELOPMENT` | `courses_public_effective` remoto: `28` columnas, `private_column_count=0`, `security_invoker=true`. | El publico no ve estados internos, auditoria ni reglas privadas. |
| `H2-CA2` | Grants y RLS | `PASS_IN_DEVELOPMENT` | `anon/authenticated` sin SELECT directo a tablas internas; grants explicitos sobre vista/funcion. | El acceso publico esta limitado a informacion segura. |
| `H2-CA2` | Advisors de seguridad | `PASS_IN_DEVELOPMENT` | Security Advisor sin hallazgos H2 criticos/warn. | No quedan alertas H2 de seguridad conocidas en desarrollo. |
| `H2-CA3` | Conservacion de incompletos | `PASS_IN_DEVELOPMENT` | Backfill remoto: `350` estados creados para `350` cursos. | Ningun programa se pierde por estar incompleto. |
| `H2-CA3` | Clasificacion de calidad | `PASS_IN_DEVELOPMENT` | `complete=131`, `pending=219`. | Los completos y pendientes quedan separados para accion editorial. |
| `H2-CA3` | No publicacion automatica | `PASS_IN_DEVELOPMENT` | `courses_public_effective=0` esperado por gate editorial sin publicacion masiva. | Nada incompleto se publica por accidente. |
| `H2-CA3` | Idempotencia de backfill | `PASS_IN_DEVELOPMENT` | Segundo run `NOOP=350`. | Reejecutar el proceso no duplica ni rompe datos. |
| `H2-CA3` | Escalabilidad de lote | `PASS_IN_DEVELOPMENT` | Tests cubren batches hasta mas de `1000` registros y escenarios de `10000`. | El proceso esta preparado para crecer sin depender de una carga manual unica. |
| `H2-CA3` | Validacion automatizada | `PASS_IN_DEVELOPMENT` | Suite H2 `91 passed`; harness PG17 `h2_pg17_harness_ok`; credential scan `PASS`. | La entrega esta respaldada por pruebas repetibles, no solo revision manual. |
| `H2-PR` | Aprobacion tecnica para PR | `GO_TECHNICAL_FOR_PROTECTED_PR` | Security-auditor final sin bloqueantes; test documental grado `A`; workflow ejecuta el gate documental. | El PR puede ser aprobado por el usuario para iniciar el flujo protegido. |

## Enlaces Canonicos

- Estado vivo: [Estado Del Proyecto](../estado_del_proyecto.md)
- Plan vinculante: [Plan Vinculante Nuevo Pedido](../operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md)
- Plan Maestro: [Plan Maestro Sprint 1 H2-H5](../operaciones/plan_maestro_sprint1_h2_h5.md)
- Hito: [HITO-002](../hitos/hito_002.md)
- TASK: [TASK-H2-001](../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- Evidencia: [Evidencia Hito 002](../evidencias_cliente/req_est_001_sprint_1/evidencia_hito_002.md)

## Resumen De Metricas

| Metrica | Valor |
|---|---:|
| Cursos procesados en Free | 350 |
| Estados editoriales creados | 350 |
| Programas completos | 131 |
| Programas pendientes | 219 |
| Segundo run sin cambios | 350 |
| Definiciones editoriales | 41 |
| Definiciones publicas visibles | 25 |
| Definiciones privadas protegidas | 16 |
| Columnas publicas efectivas | 28 |
| Campos privados expuestos | 0 |

## Validaciones Minimas Futuras

- `pytest` para validador/backfill cuando exista codigo.
- Pruebas SQL en PostgreSQL 17 cuando cambie `db/**`.
- Evidencia por ambiente antes de promover.
- Aprobacion JIT separada para cualquier DDL/DML, Supabase, backfill o writer.
