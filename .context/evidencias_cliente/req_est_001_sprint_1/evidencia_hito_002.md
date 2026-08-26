# Acta Ejecutiva Canonica Hito 002

Estado: `MERGED_TO_CERTIFICACION_CI_GREEN`.

Veredicto: `IMPLEMENTED_AND_VALIDATED_IN_DEVELOPMENT`.

Veredicto PR: `MERGED_TO_CERTIFICACION_CI_GREEN`.

Grado de evidencia: `A`.

Esta acta acredita que H2, compuesto por `H2-CA2` y `H2-CA3`, esta implementado y validado tecnicamente en el ambiente Supabase Free de desarrollo, mergeado a `desarrollo` por PR #458 y promovido a `certificacion` por PR #460 con checks verdes. No acredita produccion ni aceptacion contractual final sin QA de certificacion, validaciones CI y aprobacion humana posterior.

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
| Fuente cliente | `SRC-REQ-002` validada via `ADENDA-REQ-EST-001-001`. |
| Gate fuente privada | `tests/test_requirement_client_source_validation.py` con `STUDIAMATCH_PRIVATE_SOURCE_DIR`: `6 passed`. |
| Veredicto PR | `MERGED_TO_CERTIFICACION_CI_GREEN`. |

## Alcance No Incluido

Este hito no despliega produccion, no habilita schedules, no ejecuta writers productivos, no sincroniza Supabase Pro y no abre capturas reales de leads. Esas acciones requieren aprobacion separada.

## Enlaces Canonicos

- Estado vivo: [Estado Del Proyecto](../../estado_del_proyecto.md)
- Plan vinculante: [Plan Vinculante Nuevo Pedido](../../operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md)
- Plan Maestro: [Plan Maestro Sprint 1 H2-H5](../../operaciones/plan_maestro_sprint1_h2_h5.md)
- Hito: [HITO-002](../../hitos/hito_002.md)
- TASK: [TASK-H2-001](../../backlog_tareas/req_est_001_sprint_1/tarea_002_hito_2.md)
- Matriz: [Matriz Hito 002](../../matrices/matriz_hito_002.md)
- Evidencia tecnica: [H2 Local Acceptance Evidence](../../operaciones/h2_local_acceptance_evidence.md)
- JIT Security Advisor: [DDL-H2-SECURITY-ADVISOR-REMEDIATION-FREE](../../operaciones/ddl_authorizations/DDL-H2-SECURITY-ADVISOR-REMEDIATION-FREE.md)
- JIT Vista Publica: [DDL-H2-PUBLIC-EFFECTIVE-VIEW-FIELDS-FIX-FREE](../../operaciones/ddl_authorizations/DDL-H2-PUBLIC-EFFECTIVE-VIEW-FIELDS-FIX-FREE.md)

## Decision Solicitada

Con esta evidencia, el siguiente paso es autorizar QA read-only de H2 en `certificacion`. La promocion a `certificacion` no autoriza Supabase Pro, produccion, writers, schedules, canaries, deploys ni DDL/DML adicional.
