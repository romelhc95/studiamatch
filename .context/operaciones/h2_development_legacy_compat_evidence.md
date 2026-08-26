# H2 Development Legacy Compatibility Evidence

Estado: `PREPARED_FOR_FREE_DEVELOPMENT_JIT`.

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
| Calidad | `GO_WITH_OBSERVATIONS` | Tests locales y evidencia remota pasan para H2 compat; quedan observaciones UI no bloqueantes: prefetch RSC 404 en rutas dinamicas y 401 manejados en ratings/reviews. |
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
| Observaciones UI | `NON_BLOCKING_FOR_H2_COMPAT`: 404 en prefetch RSC de rutas dinamicas exportadas y 401 manejados para `ratings/reviews`; deben clasificarse en deuda separada si se exige consola limpia. |

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
| `compatibilidad` | Mantener visibles los cursos legacy que ya cumplian `active + verified + production_enabled` mientras H2 editorial se estabiliza. |
| `deploy` | Validar Home, listado, detalle, comparador, build static y smoke web contra `courses_public_effective`. |
| `contract` | Retirar la cohorte legacy cuando los cursos requeridos esten publicados por el contrato H2 estricto `published + complete + available`. |
| Rollback | Mientras la cohorte exista, el frontend H2 conserva el catalogo anterior; cualquier correccion DB posterior debe ser forward-only. |
| No degradacion funcional | `courses_public_effective=0` era `NO-GO`; post-apply Free queda `227` y la web real muestra catalogo. |

## Limites

- No autoriza Supabase Pro, produccion, schedules, canaries, deploys, merge a `main` ni publicacion masiva.
- La aplicacion en Free requiere JIT separada para aplicar la migracion y verificar equivalencia real contra datos remotos.
- Si el inventario remoto no encuentra cursos elegibles, se permite un seeder condicionado de fixtures solo en Free para validar comportamiento, no como evidencia de catalogo real.
- PR #466 no debe mergearse sin revision humana, CI requerido y aceptacion explicita de las observaciones UI no bloqueantes.
