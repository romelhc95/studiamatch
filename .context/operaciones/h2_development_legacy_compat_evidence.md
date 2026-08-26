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
| Compatibilidad funcional Desarrollo | `GO` | La vista conserva cursos `is_active=true`, `is_verified=true` y `production_enabled=true` capturados en la cohorte. |
| Privacidad de datos editoriales | `GO` | La vista mantiene 28 columnas publicas y cero campos privados/editoriales. |
| Transparencia para futuro main | `GO_CONDICIONADO` | La misma estrategia debe validarse en Pro con JIT read-only/DDL/DML antes de cualquier merge a `main`. |

## Pilares Obligatorios

| Pilar | Estado | Justificacion |
|---|---|---|
| Funcionalidad | `GO` | El catalogo publico previo se preserva mediante cohorte legacy congelada y la web no queda vacia si existen cursos elegibles. |
| Escalabilidad | `GO` | La cohorte es una tabla indexada por `course_id`; el lector mantiene filtros por `active`, `verified` y `production_enabled`. |
| Seguridad | `GO` | No hay fallback frontend a `courses`; la cohorte queda en schema `private`, sin grants publicos, y la vista expone solo campos publicos. |
| Mantenimiento | `GO` | La compatibilidad es forward-only, versionada y separa expansion temporal de contraccion futura. |
| Calidad | `GO` | Harness PG17 y tests estaticos validan estricto H2, legacy visible, nuevos pendientes excluidos y no-productivos excluidos. |
| Rendimiento | `GO` | La cohorte usa PK por `course_id`; el lector filtra por columnas existentes y conserva una superficie de 28 columnas. |

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
| No degradacion funcional | `courses_public_effective=0` es `NO-GO` si existen cursos legacy elegibles. |

## Limites

- No autoriza Supabase Pro, produccion, schedules, canaries, deploys, merge a `main` ni publicacion masiva.
- La aplicacion en Free requiere JIT separada para aplicar la migracion y verificar equivalencia real contra datos remotos.
- Si el inventario remoto no encuentra cursos elegibles, se permite un seeder condicionado de fixtures solo en Free para validar comportamiento, no como evidencia de catalogo real.
