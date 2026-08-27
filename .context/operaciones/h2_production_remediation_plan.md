# Plan De Remediacion Productiva H2

Estado: `PLAN_IMPLEMENTED_LOCALLY_NO_PRO_APPLY_NO_MAIN_PROMOTION`.

Alias historico preservado para trazabilidad: `PLAN_READY_NO_PRO_APPLY_NO_MAIN_PROMOTION`.

Ambiente objetivo futuro: Supabase Pro `xwhtiqmboljkshrtviyw` y rama `main`.

Este documento no autoriza DDL/DML, Supabase Pro, `main`, writers, schedules,
DB Sync, canaries ni deploys manuales. Define los cambios necesarios para
habilitar un flujo protegido posterior hacia `main` manteniendo la transicion
transparente obligatoria.

La transicion productiva obligatoria es `expand -> compatibilidad -> deploy -> contract`.

## Contexto Cerrado

| Control | Resultado |
|---|---|
| PR #466 | Aprobado y mergeado a `desarrollo` en `e8376035d8d5c3e1b7893cbb1ede14f735ccd05d`. |
| PR #467 | Aprobado y mergeado a `certificacion` en `2d499324bb21e750d9bc7c94cb80e7a193062b50`. |
| Certificacion deployment | Cloudflare Pages `4cc2e34c`, checks verdes. |
| Certificacion smoke | Home, detalle, comparador, RSC y relacionados responden `200`; snapshot navegador sin errores reportados. |
| Free H2 compat | `227` legacy elegibles, `227` cohorte, `227` efectivos, `0` faltantes, `0` inesperados. |
| Pro read-only observado | `350` cursos totales, `224` activos y verificados elegibles; H2 schema ausente. |

## Veredicto Actual

`NO_GO_FOR_MAIN_UNTIL_PRO_EXPAND_COMPAT_VERIFIED`.

Certificacion esta funcionalmente estable, pero Pro no tiene los objetos H2 que
requiere el frontend certificado. El frontend de `main` aun lee `courses`; el
frontend H2 lee `courses_public_effective`. Promover frontend antes del schema
romperia la lectura. Aplicar las migraciones H2 actuales completas antes del
frontend tambien puede romper el `main` vigente porque revocan acceso directo a
`courses` y rutas legacy.

## Brecha Productiva Read-Only

| Control | Resultado |
|---|---|
| PostgreSQL Pro | `17.6`. |
| `public.course_editorial_state` | No existe. |
| `public.courses_public_effective` | No existe. |
| `private.h2_legacy_public_course_cohort` | No existe. |
| Cursos Pro totales | `350`. |
| Cursos Pro activos/verificados elegibles | `224`. |
| Slugs duplicados Pro | `0` grupos duplicados observados. |
| `anon` SELECT directo a `courses` | `true`, requerido por el frontend actual de `main`. |
| `anon` SELECT a `institution_site_profiles` | `false`. |
| Drift `crawler_exclusions` | `public.crawler_exclusions` existe en Pro; contradice la regla canonica de retiro legacy y debe reconciliarse/documentarse antes de JIT Pro sin modificar Pro en esta remediacion. |
| `db-sync-to-pro.yml` | En esta rama local acepta `migration_manifest` cerrado para F10.8 y H2 Pro. |
| `db_migrate.py` | En esta rama local exige `--manifest` para Pro y rechaza `--only` Pro arbitrario. |

## Principio De Release

La promocion a `main` solo puede ocurrir despues de un `expand` Pro aditivo y
compatible que deje operando simultaneamente:

- frontend viejo de `main` leyendo `courses`;
- frontend H2 leyendo `courses_public_effective`;
- cohorte legacy Pro congelada con los `224` cursos elegibles actuales;
- cero revocaciones legacy hasta despues del deploy estable y ventana de rollback.

## Transicion Transparente Productiva

| Fase | Requisito |
|---|---|
| `expand` | Crear objetos H2 en Pro de forma aditiva: tablas editoriales, auditoria, diccionario, funciones privadas, vista publica y grants minimos sin revocar lectura legacy directa a `courses`. |
| `compatibilidad` | Capturar `private.h2_legacy_public_course_cohort` con los `224` cursos elegibles de Pro y verificar que `courses_public_effective` devuelve exactamente ese baseline mientras los estrictos H2 aun son `0` o el conteo esperado. |
| `deploy` | Solo despues del expand verificado, promover `certificacion -> main` por PR protegido; validar build contra Pro, Cloudflare automatico y smoke productivo. |
| `contract` | En PR/JIT posterior, revocar lectura directa a `courses`, retirar paths legacy y finalmente eliminar la cohorte cuando el catalogo requerido este `published + complete + available`. |
| Rollback | Antes de contract, rollback primario es redeploy del frontend previo; DB aditiva permanece compatible. Si se aplica contract, rollback requiere migracion forward-only de ACLs. |
| No degradacion funcional | El catalogo productivo no puede caer por debajo del baseline Pro elegible `224` sin decision humana explicita y evidencia. |

## Cambios Necesarios Para Habilitar El Flujo Protegido A Main

1. Reconciliar autoridad documental post-PR #467.
2. Agregar migraciones productivas separadas y ordenadas:
   - `20260827_h2_pro_expand_schema_compat.sql`: objetos H2 aditivos y vista, sin revocar `courses` legacy.
   - `20260827_h2_pro_seed_editorial_field_definitions.sql`: seed idempotente del diccionario editorial.
   - `20260827_h2_pro_backfill_editorial_state.sql`: backfill idempotente de estados editoriales no publicados.
   - `20260827_h2_pro_capture_legacy_cohort.sql`: DML controlado que captura los `224` elegibles de Pro.
   - `20260827_h2_pro_contract_public_reader.sql`: revoca lectura directa a `courses` solo despues del deploy estable.
   - `20260827_h2_pro_contract_legacy_cohort.sql`: retira cohorte solo con paridad strict H2.
3. Extender `scripts/maintenance/db_migrate.py` para aceptar manifiestos H2 Pro allowlisted, no orden alfabetico libre:
   - `h2-expand-compat`.
   - `h2-contract-public-reader`.
   - `h2-contract-legacy-cohort`.
   - `f10-8-atomic-cleansing-provenance` preservado como manifiesto historico explicito.
4. Extender `.github/workflows/db-sync-to-pro.yml` con gates H2:
   - `report` read-only de migraciones H2 pendientes;
   - `apply` manual con `Production` environment, backup/PITR y `ddl_authorization_id` H2;
   - `verify` target-only de objetos H2, counts, grants, RLS, advisors y cohort hash.
5. Agregar una autorizacion DDL/DML versionada en `.context/operaciones/ddl_authorizations/` para Pro solo cuando exista JIT humana separada, ligada a SHA, manifest, candidato y PITR.
6. Ampliar harness PostgreSQL 17 para ejecutar el stack H2 productivo en orden real.
7. Actualizar CI para bloquear PR a `main` si falta evidencia de Pro expand verificado.
8. Reconciliar `certificacion` con `main@80204bfd5018a9dbf9e5c10ace537cfe51ef05a0` antes del PR final.
9. Ejecutar build/smoke contra Pro expandido antes de mergear a `main`.
10. Mantener writers, schedules, FG1/FG2/FG3, canaries y DB Sync apply bloqueados salvo JIT separada.

## Manifiestos Ejecutables Versionados

| Manifest | Migrations | Gate operacional |
|---|---|---|
| `h2-expand-compat` | `20260827_h2_pro_expand_schema_compat`, `20260827_h2_pro_seed_editorial_field_definitions`, `20260827_h2_pro_backfill_editorial_state`, `20260827_h2_pro_capture_legacy_cohort` | Requiere `workflow_dispatch`, environment `Production`, `apply_authorized=true`, `backup_pitr_verified=true`, `ddl_authorization_id`, archivo de autorizacion con `Authorized manifest` y `Authorized candidate SHA`. |
| `h2-contract-public-reader` | `20260827_h2_pro_contract_public_reader` | Solo despues de deploy estable H2 en `main` y ventana de rollback validada. |
| `h2-contract-legacy-cohort` | `20260827_h2_pro_contract_legacy_cohort` | Solo cuando todo el catalogo requerido este `published + complete + available`; la migracion aborta si queda fila legacy-only. |
| `h2-rollback-public-reader-contract` | `20260827_h2_pro_rollback_public_reader_contract` | Rollback forward-only de ACLs tras `contract-public-reader`; aborta si la cohorte legacy ya fue retirada. |

La verificacion `target-only --h2-manifest` ajusta el contrato esperado: `h2-expand-compat` exige que `courses` siga disponible publicamente para el frontend legacy; los manifiestos `contract` exigen que la lectura publica directa a `courses` ya este retirada y que `courses_public_effective` sea la unica superficie publica de cursos.

## Ruta DB-First No Circular

El orden obligatorio requiere que Pro tenga `h2-expand-compat` verificado antes de
promover el frontend H2 a `main`. Para evitar el ciclo anterior (`DB Sync` solo en
`main` pero frontend no puede ir a `main` antes del expand), esta remediacion deja
preparadas dos rutas operativas; cualquiera requiere aprobacion humana separada y
JIT Pro antes de usarse:

| Alternativa | Mecanismo | Riesgo | Decision requerida |
|---|---|---|---|
| A - DB-first desde `certificacion` | Ejecutar `db-sync-to-pro.yml` por `workflow_dispatch` en rama `certificacion`, con `candidate_sha` igual a `origin/certificacion`, `Production` environment, `ddl_authorization_id`, backup/PITR y digest de cohorte. | Excepcion controlada al flujo normal porque aplica DB Pro antes de que el commit exista en `main`. Mantiene transparencia porque el expand es aditivo y conserva `courses`. | Requiere aprobacion humana explicita para usar `certificacion` como fuente DB-first. |
| B - PR DB/control-only a `main` | Promover primero solo migraciones/workflow/verificadores a `main`, sin frontend H2 si se puede separar limpiamente. Luego aplicar Pro y despues promover frontend. | Menor excepcion operacional, pero puede requerir separar commits/rutas y evitar activar frontend H2 antes del expand. | Requiere decision humana si se acepta PR tecnico DB-only previo. |

La implementacion local habilita la alternativa A sin ejecutarla: el workflow acepta
`certificacion` o `main`, verifica que el SHA candidato sea exactamente el head
remoto de la rama disparada y mantiene `workflow_dispatch` manual. Si el equipo no
aprueba esta excepcion DB-first, debe usarse la alternativa B.

## Preflight JIT Read-Only

Antes de solicitar JIT Pro, ejecutar solo en modo read-only el reporte
`scripts/maintenance/h2_pro_preflight_report.py`. El reporte produce las lineas que
deben copiarse a la autorizacion:

- `H2 expected eligible count: <n>`.
- `H2 expected cohort digest: sha256:<digest>`.

El workflow exige esas lineas en el archivo JIT cuando `migration_manifest` es
`h2-expand-compat` y `check_db_parity.py --h2-manifest h2-expand-compat` llama al
RPC service-only `h2_verify_expand_compat` para validar count, identidad de cohorte,
vista publica, RLS y preservacion legacy.

## Gates Medibles Antes De PR A Main

| Gate | GO |
|---|---|
| Autoridad | Estado vivo, hito, task, seguimiento, evidencia y matriz registran PR #467, `2d499324` y `4cc2e34c`. |
| Pro preflight | `course_editorial_state`, `courses_public_effective` y cohorte ausentes antes de expand; baseline Pro `224`; duplicate slug groups `0`. |
| Expand Pro | Objetos H2 existen, vista tiene `28` columnas publicas, `0` privadas, `security_invoker=true`, RLS activo en tablas H2 y RPCs mutadores H2 denegados a roles publicos. |
| Compat Pro | Cohorte `224`, vista efectiva `224`, missing baseline `0`, unexpected `0` y digest `sha256` igual al preflight aprobado en JIT. |
| Legacy Pro | Direct read legacy a `courses` sigue funcional hasta contract. |
| Seguridad | Advisors sin hallazgos H2 criticos/warn nuevos; warnings legacy baselineados. |
| Build | Static build con env Pro genera catalogo y rutas esperadas, no solo fallback tolerado. |
| Smoke | Home, listado, detalle, comparador, RSC, legales, consola y red pasan en preview/main. |
| Rollback | Deployment anterior identificado y DB aditiva compatible con frontend viejo. |

## Riesgos Residuales Baselineados

- Pro tiene warnings legacy de `function_search_path_mutable` y `increment_view_count` SECURITY DEFINER ejecutable por roles publicos; no son creados por H2, pero deben baselinearse y no empeorar.
- Pro tiene indice duplicado en `courses` reportado por Performance Advisor; no bloquea H2 expand, pero no debe mezclarse con esta remediacion.
- Pro conserva `public.crawler_exclusions`; esta remediacion no lo modifica, pero la discrepancia debe quedar reconciliada como drift antes de pedir JIT Pro.
- La cohorte legacy es temporal; mantenerla indefinidamente viola el `contract` de H2.

## Secuencia Operativa Futura

1. PR documental/remediacion a `desarrollo` con este plan y tests.
2. PR protegido `desarrollo -> certificacion` para la remediacion.
3. JIT DDL/DML Pro separada para `expand + compatibilidad`, con backup/PITR.
4. Ejecutar DB Sync H2 report/apply/verify contra Pro.
5. PR protegido `certificacion -> main` solo si Pro expand queda verificado.
6. Smoke productivo post-merge.
7. PR/JIT posterior para `contract-public-reader`.
8. PR/JIT posterior para `contract-legacy-cohort`.

## Stop Conditions

- Pro no devuelve baseline `224` o cambia sin explicacion aprobada.
- `courses_public_effective` expone campos editoriales/privados.
- Se intenta revocar `courses` antes de deploy estable y rollback window.
- DB Sync intenta ordenar H2 por nombre de archivo en vez de manifest.
- Se activa writer, schedule, canary o FG sin aprobacion separada.
- Un PR a `main` se abre sin expand Pro verificado.
