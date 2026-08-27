# Matriz Hito 002

Veredicto: `IMPLEMENTED_AND_VALIDATED_IN_CERTIFICATION_NO_MAIN_YET`.

Veredicto PR: `PR_467_MERGED_TO_CERTIFICACION_CI_GREEN_DEPLOY_STABLE`.

Fuente cliente validada: `SRC-REQ-002` via `ADENDA-REQ-EST-001-001`.

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
| `H2-CA3` | Conservacion de incompletos | `PASS_IN_DEVELOPMENT` | Backfill remoto: `350` estados creados para `350` cursos; compatibilidad legacy preparada para cursos `active + verified + production_enabled`. | Ningun programa que ya debia verse desaparece por estar incompleto durante la transicion H2. |
| `H2-CA3` | Clasificacion de calidad | `PASS_IN_DEVELOPMENT` | `complete=131`, `pending=219`. | Los completos y pendientes quedan separados para accion editorial. |
| `H2-CA3` | No publicacion automatica | `PASS_IN_DEVELOPMENT_REMOTE` | Los cursos nuevos pendientes fuera de la cohorte no aparecen; la cohorte legacy solo conserva lo que ya era visible por negocio. | Nada nuevo incompleto se publica por accidente y la web real recupera los cursos elegibles. |
| `H2-COMPAT` | Transparencia funcional Desarrollo | `PASS_AFTER_FREE_MIGRATION` | Post-apply Free: `227` legacy elegibles, `227` cohorte, `227` efectivos, `0` faltantes, `0` inesperados. | La web muestra catalogo, detalle y comparador mientras se completa la editorializacion. |
| `H2-CA3` | Idempotencia de backfill | `PASS_IN_DEVELOPMENT` | Segundo run `NOOP=350`. | Reejecutar el proceso no duplica ni rompe datos. |
| `H2-CA3` | Escalabilidad de lote | `PASS_IN_DEVELOPMENT` | Tests cubren batches hasta mas de `1000` registros y escenarios de `10000`. | El proceso esta preparado para crecer sin depender de una carga manual unica. |
| `H2-CA3` | Validacion automatizada | `PASS_IN_DEVELOPMENT` | Suite H2 `91 passed`; harness PG17 `h2_pg17_harness_ok`; credential scan `PASS`. | La entrega esta respaldada por pruebas repetibles, no solo revision manual. |
| `H2-CLIENT` | Validacion contra fuente cliente | `PASS_CLIENT_SOURCE_ATTESTED` | `SRC-REQ-002` contrastado mediante `ADENDA-REQ-EST-001-001`; CA2 completo y CA3 presentes. | La entrega responde a los criterios aprobados por el cliente sin exponer el documento privado. |
| `H2-PR` | PR protegido a certificacion | `PR_467_MERGED_TO_CERTIFICACION_CI_GREEN_DEPLOY_STABLE` | PR #458, PR #459, PR #460, PR #466 y PR #467 aprobados/mergeados; checks requeridos verdes; deployment `4cc2e34c` estable. | H2 ya esta en la rama de certificacion con compatibilidad legacy validada. |
| `H2-PRO` | Preparacion productiva | `NO_GO_UNTIL_PRO_EXPAND_COMPAT_VERIFIED` | Pro read-only: `350` cursos totales, `224` activos/verificados elegibles, H2 schema ausente; plan productivo versionado. | Antes de produccion se prepara la base para que el catalogo no desaparezca. |

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
| Cursos Pro baseline elegible | 224 |
| Deployment certificacion estable | `4cc2e34c` |

## Validaciones Minimas Futuras

- `pytest` para validador/backfill cuando exista codigo.
- Pruebas SQL en PostgreSQL 17 cuando cambie `db/**`.
- Evidencia por ambiente antes de promover.
- Aprobacion JIT separada para cualquier DDL/DML, Supabase, backfill o writer.
- Pro requiere `expand + compatibilidad` verificado antes de cualquier PR efectivo a `main`.
