# H2 Development Legacy Compatibility Evidence

Estado: `QUALITY_CLEANUP_REMOTE_VERIFIED_PENDING_REVIEW`.

Ambiente objetivo: `desarrollo` / Supabase Free.

## Proposito

Corregir la transicion H2 para que la web de Desarrollo conserve los cursos que por contrato de negocio ya debian mostrarse antes de H2, sin reabrir lectura publica directa a `courses` ni publicar automaticamente cursos nuevos incompletos.

## Criterios De Aceptacion H2

| Criterio | Estado | Evidencia |
|---|---|---|
| `H2-CA2` Modelo editorial separado | `GO` | La superficie publica sigue siendo `courses_public_effective`; la cohorte vive en `private.h2_legacy_public_course_cohort` sin grants publicos. |
| `H2-CA3` Pipeline tolerante a incompletos | `GO` | Los cursos legacy visibles pueden permanecer pendientes sin desaparecer; los cursos nuevos pendientes fuera de cohorte no se publican. |
| Compatibilidad funcional Desarrollo local/mock | `GO` | Tests, harness PG17 y smoke web mock validan que la vista compatible renderiza catalogo cuando la API entrega cursos. |
| Compatibilidad funcional Desarrollo remoto | `GO_AFTER_FREE_MIGRATION` | Post-apply Free: `227` cursos legacy elegibles, `227` en cohorte, `227` en `courses_public_effective`, `0` faltantes y `0` inesperados. |
| Privacidad de datos editoriales | `GO` | La vista mantiene 28 columnas publicas y cero campos privados/editoriales. |
| Transparencia para futuro main | `GO_CONDICIONADO` | La misma estrategia debe validarse en Pro con JIT read-only/DDL/DML antes de cualquier merge a `main`. |

## Pilares Obligatorios

| Pilar | Estado | Justificacion |
|---|---|---|
| Funcionalidad | `GO_AFTER_FREE_MIGRATION` | Desarrollo remoto muestra `227` programas, detalle real de `Big data` y comparador con el curso seleccionado. |
| Escalabilidad | `GO` | La cohorte es una tabla indexada por `course_id`; el lector mantiene filtros por `active`, `verified` y `production_enabled`. |
| Seguridad | `GO` | No hay fallback frontend a `courses`; la cohorte queda en schema `private`, sin grants publicos, y la vista expone solo campos publicos. |
| Mantenimiento | `GO` | La compatibilidad es forward-only, versionada y separa expansion temporal de contraccion futura. |
| Calidad | `GO` | Correccion validada en Docker, CI y preview Cloudflare `be52f883`: detalle sin React #418, bundle sin llamadas legacy `ratings`/`reviews`, recursos RSC criticos `200`, rutas relacionadas `200` y comparador sin defaults fabricados. |
| Rendimiento | `GO` | La cohorte usa PK por `course_id`; el lector filtra por columnas existentes y conserva una superficie de 28 columnas. |

## Preflight Read-Only Free 2026-08-26

| Control | Resultado |
|---|---|
| Proyecto Free | `https://aqrldlmlszjtgpqiegaa.supabase.co` |
| PostgreSQL | `17.6` |
| Ledger H2 aplicado | H2 editorial, grants fix, start date fix, allowlist fix, forward fix, security advisor remediation y public fields fix. |
| Migracion compat aplicada | `NO`: `private.h2_legacy_public_course_cohort` no existe. |
| Legacy visible elegible | `227` cursos; ordered IDs md5 `b2a88ca4af2075f9796365acec1904c8`. |
| H2 estricto visible | `0` cursos; ordered IDs md5 `d41d8cd98f00b204e9800998ecf8427e`. |
| Vista efectiva actual | `0` cursos; ordered IDs md5 `d41d8cd98f00b204e9800998ecf8427e`. |
| Delta actual | `227` cursos legacy faltan en `courses_public_effective`; `0` cursos inesperados en la vista. |
| Vista columnas | `28` publicas, `0` privadas. |
| Grants actuales | `anon/authenticated` no tienen SELECT directo a `courses` ni `course_editorial_state`; si tienen SELECT a `courses_public_effective`. |
| Funcion privada | `PUBLIC` sin EXECUTE; `anon/authenticated/service_role` con EXECUTE explicito; `SECURITY DEFINER=true`. |
| Advisors | `NOT_VERIFIED`: MCP devolvio `Unauthorized` para advisors, requiere credencial/flujo alterno read-only. |
| Web real preview #466 | `NO-GO`: responde `200 []` desde `courses_public_effective` y muestra `0` programas. |

## Post-Apply Free 2026-08-26

| Control | Resultado |
|---|---|
| Migracion aplicada | `20260826164745/h2_development_legacy_public_compat` |
| Legacy visible elegible | `227` cursos; ordered IDs md5 `b2a88ca4af2075f9796365acec1904c8`. |
| Cohorte legacy | `227` cursos; ordered IDs md5 `b2a88ca4af2075f9796365acec1904c8`. |
| H2 estricto visible | `0` cursos; esperado hasta publicacion editorial real. |
| Vista efectiva actual | `227` cursos; ordered IDs md5 `b2a88ca4af2075f9796365acec1904c8`. |
| Missing legacy IDs | `0` |
| Unexpected effective IDs | `0` |
| Vista columnas | `28` publicas, `0` privadas. |
| Grants | `anon/authenticated` sin SELECT directo a `courses` ni `course_editorial_state`; con SELECT a `courses_public_effective`. |
| Funcion privada | `PUBLIC` sin EXECUTE; `anon/authenticated/service_role` con EXECUTE explicito; `SECURITY DEFINER=true`. |
| Security Advisor | Solo `INFO rls_enabled_no_policy` legacy/no-H2 para `_view_count_dedup`, `schema_repair_audit`, `supabase_migrations`. |
| Performance Advisor | Solo `INFO` legacy/uso reciente; sin bloqueantes H2 compat. |
| Build local contra Free real | `PASS`: static export genera `235` paginas y `227` rutas de cursos. |
| Web real preview #466 Home/listado | `PASS`: muestra `227` resultados, `227` programas y `14` instituciones. |
| Web real preview #466 detalle | `PASS`: `/courses/dmc/big-data-12b2f4dc/` carga `Big data`. |
| Web real preview #466 comparador | `PASS`: `/compare/?ids=cafd93b2-4a2b-403e-b289-d7fd135316c7` carga `Big data`. |
| Observaciones UI | `ROOT_CAUSE_IDENTIFIED_AND_FIXED_LOCALLY_PENDING_REMOTE`: `_redirects` servia `/courses/` para detalles estaticos existentes, causando hydration #418; llamadas legacy `ratings`/`reviews` retiradas porque reviews reales estan fuera de Sprint 1; comparador deja de inventar precio, salario o ROI. |

## Limpieza Calidad Local 2026-08-26

| Control | Resultado |
|---|---|
| Causa raiz hydration | `web/public/_redirects` reescribia `/courses/:institution/:slug` hacia `/courses/` con 200, entregando HTML fallback aunque existiera el asset estatico del detalle. |
| Correccion detalle | `_redirects` eliminado; `/courses/` queda como pagina propia, no como rewrite para rutas de detalle. |
| Social proof | GET/POST frontend a `ratings` y `reviews` retirados; no se amplian grants, RLS ni superficie publica porque reviews reales estan excluidas de Sprint 1. |
| Relacionados | Carga desacoplada de social proof y filtrada por `category_id` + `institution_id`, para que los href usen el `institution_slug` real del curso actual. |
| Comparador | Precio, salario y ROI desconocidos se muestran como `Consultar`/`No disponible`; no se fabrican `Gratis`, `S/ 4,500` ni `12.0` meses. |
| Pruebas | Regresiones estaticas agregadas para rewrites, social proof, relacionados y defaults fabricados; smoke mock falla ante endpoints REST inesperados. |
| Estado calidad | `GO`: preview Cloudflare `be52f883` validado sin React #418, sin 401 de `ratings`/`reviews` y sin 404 de rutas exportadas criticas. |

## Validacion Remota Calidad 2026-08-26

| Control | Resultado |
|---|---|
| Commit validado | `4b66837dd238a048980fbc81a3e8cf9b8a07709f` |
| Preview Cloudflare | `https://be52f883.studiamatch-aty.pages.dev/` |
| CI requerido | `security-audit` y CodeQL `PASS`; Cloudflare Pages `PASS`. |
| Home/listado | `PASS`: `227` resultados y `14` instituciones. |
| Detalle directo | `PASS`: `/courses/dmc/big-data-12b2f4dc/` carga `Big data`; HTML inicial contiene JSON-LD y no contiene `Ruta de programa no válida`. |
| Recursos RSC detalle | `PASS`: `index.txt`, `__next._tree.txt` y `__next._full.txt` responden `200`. |
| Bundle publicado | `PASS`: no contiene `/rest/v1/ratings` ni `/rest/v1/reviews`. |
| Comparador | `PASS`: `/compare/?ids=cafd93b2-4a2b-403e-b289-d7fd135316c7` carga `Big data`. |
| Relacionados | `PASS`: `databricks-associate-cf7986c4`, `diploma-devops-engineer-9ff7e7ea` y `azure-data-engineering-13efdc78` responden `200` sin fallback. |
| Consola navegador | `PASS_WITH_FONT_WARNINGS`: sin React #418 ni 401; solo warnings de preload de fonts no bloqueantes. |

## Reglas De Cohorte

- La cohorte se captura una sola vez desde cursos que cumplen `courses.is_active=true`, `courses.is_verified=true` e institucion con `production_enabled=true`.
- La cohorte no incluye automaticamente cursos futuros.
- Un curso H2 estrictamente publicado aparece por su estado editorial aunque tambien este en la cohorte.
- Un curso inactivo, no verificado o de institucion no productiva no aparece aunque tenga estado editorial.
- Un curso pendiente fuera de cohorte no aparece.

## Transicion Transparente

| Fase | Plan |
|---|---|
| `expand` | Crear `private.h2_legacy_public_course_cohort` y reemplazar el lector acotado sin reabrir lectura publica directa a `courses`. |
| `compatibilidad` | Mantener visibles los cursos legacy que ya cumplian `active + verified + production_enabled`; retirar solo social proof roto/fuera de alcance sin tocar DB ni datos existentes. |
| `deploy` | Home, listado, detalle, comparador, build static y smoke web validados contra `courses_public_effective`; preview `be52f883` queda sin React #418, 401 de `ratings`/`reviews` ni 404 de rutas exportadas criticas. |
| `contract` | Retirar la cohorte legacy cuando los cursos requeridos esten publicados por el contrato H2 estricto `published + complete + available`; social proof real futuro debe entrar como modulo autenticado/moderado separado. |
| Rollback | Frontend-only para limpieza de calidad; revertir commit restauraria UI previa sin DDL, sin perdida de datos y sin modificar Supabase. |
| No degradacion funcional | `courses_public_effective=0` era `NO-GO`; post-apply Free queda `227`; limpieza local preserva catalogo, detalle y comparador sin llamadas fuera del contrato publico H2. |

## Limites

- No autoriza Supabase Pro, produccion, schedules, canaries, deploys, merge a `main` ni publicacion masiva.
- La aplicacion en Free requiere JIT separada para aplicar la migracion y verificar equivalencia real contra datos remotos.
- Si el inventario remoto no encuentra cursos elegibles, se permite un seeder condicionado de fixtures solo en Free para validar comportamiento, no como evidencia de catalogo real.
- PR #466 no debe mergearse sin revision humana. CI requerido, Cloudflare Pages y calidad remota ya estan verificados para `4b66837`.
