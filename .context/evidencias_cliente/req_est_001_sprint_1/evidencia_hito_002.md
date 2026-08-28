# Acta Ejecutiva Canonica Hito 002

Estado: `CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN`.

Veredicto: `IMPLEMENTED_AND_VALIDATED_IN_CERTIFICATION_NO_MAIN_YET`.

Veredicto PR: `PR_467_MERGED_TO_CERTIFICACION_CI_GREEN_DEPLOY_STABLE`.

Grado de evidencia: `A`.

Esta acta acredita que H2, compuesto por `H2-CA2` y `H2-CA3`, esta implementado y validado tecnicamente en el ambiente Supabase Free de desarrollo, mergeado a `desarrollo` por PR #458, promovido a `certificacion` por PR #460, corregido por compatibilidad/calidad en PR #466 y promovido nuevamente a `certificacion` por PR #467 con checks verdes y deployment estable. No acredita produccion ni aceptacion contractual final sin remediacion Pro `expand + compatibilidad`, validaciones CI, aprobacion JIT y PR protegido posterior a `main`.

## Validacion Contra Fuente Cliente

La validacion de cierre de `H2-CA2` y `H2-CA3` se contrasto contra la fuente privada cliente `SRC-REQ-002` usando la atestacion sanitizada versionada [ADENDA-REQ-EST-001-001](../../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md). La fuente privada no se versiona y no se expone en PRs. La adenda exige que Hito 2 contenga CA2 completo y CA3: schema editorial/calidad, faltantes, fuentes, actualizacion manual, constraints, indices, RLS, contratos de acceso, pipeline tolerante a datos parciales, marcado pendiente/completo, persistencia, backfill y pruebas por ambiente.

## Resumen Para Cliente

Hito 002 entrega la capa que evita que programas incompletos o no revisados se publiquen automaticamente. El sistema ahora conserva los programas descubiertos, calcula su estado de calidad, identifica datos faltantes, protege correcciones manuales y expone al publico solo campos seguros.

En terminos practicos, StudIAMatch ya puede distinguir entre informacion capturada por el pipeline, informacion pendiente de revision e informacion lista para publicarse. Los registros incompletos no bloquean el proceso ni desaparecen; quedan pendientes con una razon verificable.

## Resultado Por Criterio

| Criterio | Veredicto | Resultado comprensible | Evidencia verificable |
|---|---|---|---|
| `H2-CA2` Modelo editorial y calidad | `PASS_IN_DEVELOPMENT` | Cada programa tiene estado editorial, calidad, faltantes, fuentes, auditoria y reglas de exposicion publica. | DDL/RLS/RPC/vista aplicados en Free; `0` campos privados expuestos; advisors sin hallazgos H2 criticos/warn. |
| `H2-CA3` Pipeline tolerante a incompletos | `PASS_IN_DEVELOPMENT` | Los programas incompletos se conservan como pendientes, no detienen el flujo y los que ya eran visibles por negocio no desaparecen durante la transicion H2. | Backfill Free de `350` estados; `131` completos, `219` pendientes, segundo run `NOOP=350`; compatibilidad legacy preparada en `private.h2_legacy_public_course_cohort`. |

## Metricas Verificadas

| Metrica | Valor | Lectura Para Cliente |
|---|---:|---|
| Programas existentes en desarrollo | 350 | Universo inicial procesado por H2. |
| Estados editoriales creados | 350 | Todos los programas tienen control editorial. |
| Programas completos | 131 | Pueden avanzar a revision/publicacion cuando el editor lo autorice. |
| Programas pendientes | 219 | Se conservan y muestran que informacion falta. |
| Faltante dominante | `duration=219` | La duracion es el principal dato a completar. |
| Segundo backfill | `NOOP=350` | La ejecucion es idempotente: no duplica ni reescribe sin necesidad. |
| Definiciones editoriales | 41 | Diccionario de campos y reglas disponible. |
| Definiciones publicas | 25 | Campos permitidos para interfaces publicas. |
| Definiciones privadas | 16 | Campos internos protegidos. |
| Columnas de vista publica | 28 | Superficie publica acotada. |
| Campos privados expuestos | 0 | No se publica estado interno ni auditoria. |
| Compatibilidad visual Desarrollo | `GO_AFTER_FREE_MIGRATION` | Post-apply Free: `227` cursos legacy elegibles, `227` en cohorte y `227` visibles en `courses_public_effective`; preview #466 muestra catalogo, detalle y comparador. |
| Compatibilidad Certificacion | `GO_AFTER_PR_467` | PR #467 mergeado a `certificacion` en `2d499324bb21e750d9bc7c94cb80e7a193062b50`; Cloudflare `4cc2e34c`; host de certificacion muestra Home, detalle y comparador. |
| Baseline Pro pre-main | `NO_GO_UNTIL_PRO_EXPAND` | Pro read-only: `350` cursos totales, `224` activos/verificados elegibles; H2 schema ausente. |

## Evidencia Tecnica Resumida

| Control | Resultado |
|---|---|
| Ambiente validado | Supabase Free `aqrldlmlszjtgpqiegaa`. |
| Migraciones H2 aplicadas | Capa editorial, forward-fix, remediacion Security Advisor, seed y fix de vista publica. |
| Ledger remoto final | `20260826020441/h2_public_effective_view_public_fields_fix`. |
| Vista publica | `public.courses_public_effective` con `security_invoker=true`. |
| Cohorte legacy | `private.h2_legacy_public_course_cohort` preserva el catalogo publico anterior elegible sin fallback frontend a `courses`. |
| Privacidad | `private_column_count=0`, `total_columns=28`. |
| Roles publicos | `anon` y `authenticated` sin lectura directa de tablas internas H2. |
| Funcion privada | `PUBLIC` sin `EXECUTE`; grants explicitos a roles esperados. |
| Publicacion automatica | Bloqueada: el pipeline no marca programas como publicados. |
| Cursos archivados | Protegidos contra sobrescritura automatica del pipeline. |
| Security Advisor | Sin hallazgos H2 criticos/warn; solo infos legacy no-H2. |
| Performance Advisor | Solo infos legacy/uso reciente; sin bloqueo H2. |

## Validaciones Locales Y Remotas

| Validacion | Resultado |
|---|---|
| Suite H2 focalizada | `91 passed`. |
| Harness PostgreSQL 17 | `h2_pg17_harness_ok`. |
| Python compile H2 | `PASS`. |
| Frontend lint | `PASS` con 10 warnings preexistentes. |
| TypeScript | `PASS`. |
| Static build | `PASS`. |
| Credential scan | `PASS`. |
| Security-auditor pre-merge | `GO emitido antes de abrir PR #458`. |
| Compatibilidad desarrollo | `REMOTE_COMPAT_VERIFIED_PENDING_REVIEW`: `courses_public_effective=0` queda NO-GO si existen legacy elegibles; post-apply Free queda `227`. |
| PR #458 | `APPROVED_AND_MERGED_TO_DESARROLLO@0c9e40f81f2a38141c9c2af170e26ab594b7533d`. |
| PR #459 | `APPROVED_AND_MERGED_CONTEXT_GATE@4f7061585202301760d8068e13edc5c93b0f94e2`. |
| PR #460 | `APPROVED_AND_MERGED_TO_CERTIFICACION@0ed6afeec741c698f1111c2ea27357160fa77279`. |
| PR #466 | `APPROVED_AND_MERGED_TO_DESARROLLO@e8376035d8d5c3e1b7893cbb1ede14f735ccd05d`. |
| PR #467 | `APPROVED_AND_MERGED_TO_CERTIFICACION@2d499324bb21e750d9bc7c94cb80e7a193062b50`; deployment `4cc2e34c` estable. |
| Fuente cliente | `SRC-REQ-002` validada via `ADENDA-REQ-EST-001-001`. |
| Gate fuente privada | `tests/test_requirement_client_source_validation.py` con `STUDIAMATCH_PRIVATE_SOURCE_DIR`: `6 passed`. |
| Veredicto PR | `PR_467_MERGED_TO_CERTIFICACION_CI_GREEN_DEPLOY_STABLE`. |
| Remediacion productiva | `PLAN_READY_NO_PRO_APPLY_NO_MAIN_PROMOTION`: ver [Plan De Remediacion Productiva H2](../../operaciones/h2_production_remediation_plan.md). |
| PR #477 Security Advisor endpoint | `MERGED_TO_DESARROLLO_AND_CERTIFICATION`: forward-fix del endpoint de advisors soportado por Supabase. |
| PR #478 RLS cohorte privada | `MERGED_TO_CERTIFICATION`: proteccion RLS sobre `private.h2_legacy_public_course_cohort`. |
| PR #480/#481 DB Sync verify | `MERGED_TO_DESARROLLO_AND_CERTIFICATION`: workflow `db-sync-to-pro.yml` permite no-op apply success bajo `operation=verify` para generar artifact H2. |
| Pro apply `h2-expand-compat` | `APPLIED_ADITIVE_WITH_BACKUP_PITR`: baseline elegible `224`; writers/schedules/deploys siguen pausados. |
| Pro verify pendiente | `PENDING_DB_SYNC_VERIFY_ARTIFACT`: se requiere `operation=verify` sobre `certificacion` para validar advisors y versionar evidencia. |

## Alcance No Incluido

Este hito no despliega produccion, no habilita schedules, no ejecuta writers productivos, no sincroniza Supabase Pro y no abre capturas reales de leads. Pro y `main` quedan bloqueados hasta remediacion productiva con aprobacion separada.

## Enlaces Canonicos

- Estado vivo: [Estado Del Proyecto](../../estado_del_proyecto.md)
- Plan vinculante: [Plan Vinculante Nuevo Pedido](../../operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md)
- Plan Maestro: [Plan Maestro Sprint 1 H2-H5](../../operaciones/plan_maestro_sprint1_h2_h5.md)
- Hito: [HITO-002](../../hitos/hito_002.md)
- TASK: [TASK-H2-001](../../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- Matriz: [Matriz Hito 002](../../matrices/matriz_hito_002.md)
- Evidencia tecnica: [H2 Local Acceptance Evidence](../../operaciones/h2_local_acceptance_evidence.md)
- Remediacion productiva: [Plan De Remediacion Productiva H2](../../operaciones/h2_production_remediation_plan.md)
- JIT Security Advisor: [DDL-H2-SECURITY-ADVISOR-REMEDIATION-FREE](../../operaciones/ddl_authorizations/DDL-H2-SECURITY-ADVISOR-REMEDIATION-FREE.md)
- JIT Vista Publica: [DDL-H2-PUBLIC-EFFECTIVE-VIEW-FIELDS-FIX-FREE](../../operaciones/ddl_authorizations/DDL-H2-PUBLIC-EFFECTIVE-VIEW-FIELDS-FIX-FREE.md)

## Decision Solicitada

Con esta evidencia, el siguiente paso es versionar y aprobar la remediacion productiva H2. La promocion a `main` sigue en `NO-GO` hasta ejecutar y verificar Pro `expand + compatibilidad` bajo JIT separada.
