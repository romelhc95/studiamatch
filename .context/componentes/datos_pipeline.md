# Componentes: datos y pipeline

Esta ficha agrupa los objetos DB y su relación con el pipeline. El diccionario campo-a-campo está en [database.md](../database.md); el ledger de SQL en [database_migrations.md](database_migrations.md); las estaciones/gates/writers en [pipeline.md](pipeline.md).

| Componente lógico | Fuente principal | Consumidor/contrato | Datos/estado | Prueba y límite |
|---|---|---|---|---|
| Catálogo institucional | institutions, institution_site_profiles, config/institution_sources.json | FG1, harvester, diagnostics | slug, URLs, perfil, allow/exclusion, gates | tests pipeline/discovery; no leer estado remoto. |
| Pipeline operativo | core workers y staging tables | orchestrator/workflows | raw→cleansed→enriched→courses, status/error/hash | PG17/mock y R178; no datos productivos. |
| Capa editorial | field definitions/state/audit y RPC | Admin + courses_public_effective | pipeline-owned/editorial overrides, publish/quality/availability | harness SQL/UI local; aplicación Pro no verificada. |
| Membresías e invitaciones | admin_members, invitations, membership audit | Admin/Auth/Edge | rol, actividad, onboarding, token hash y transición | UAT/harness sintéticos; identities remotas desconocidas. |
| Seguridad del DB reader | vistas/RLS/grants/gateway | frontend/BFF | campos efectivos/allowlist | tests contracts/PG17; no prueba pre-request remoto. |
| Writer excepcional | scripts/maintenance, scripts/deprecated | operación autorizada por separado | catálogo o datos operativos | no usar nombre de audit como garantía; inspeccionar script, JIT y rollback. |

## Alcance por manifest para la primera FG2 controlada

El modo local `bounded_first_run` congela las instituciones y filas mediante un
manifest ligado a run, intento y SHA de fuente. La entrada registra institución,
`staging_id`, `course_id` cuando es refresh, clasificación, SHA-256 de URL y
contenido y estado inicial. Cleansing recibe solo los `staging_id` permitidos;
enrichment y sync derivan y comprueban solo los registros relacionados con esos
IDs. No se permite que esas etapas tomen trabajo incidental de las colas globales
en este modo. El camino ordinario sin manifest conserva sus consultas actuales y
no hereda por sí solo el alcance limitado.

Una URL nueva se registra como `new_discovery` sin `course_id`. Una URL que ya
coincide con un curso de la misma institución se registra como
`refresh_existing` con el `course_id` exacto; el sync mantiene el mismo curso y
usa `course_editorial_state` para preservar overrides manuales, fuentes y
timestamps. La prueba sintética verifica `Nombre editorial vigente` con fuente
`manual_override` tras el refresh. Las filas históricas protegidas de
`staging_raw` quedan como blockers con su ID, estado y hashes; no se resetean
`processing`, no se reabren `processed` y no se limpia ni repuebla ninguna cola.
Si la unicidad por URL impide continuar una fila existente, hace falta presentar
el ID, estado y transición SQL exacta para aprobación DML separada.

La comparación usa `normalize_url` igual que FG2; `url_sha256` identifica esa
clave canónica mientras el digest del lote conserva la URL exacta y el estado de
cada fila `staging_raw`/`courses`/downstream. La verificación de alias consulta
por páginas solo columnas de metadatos (`id`, `institution_id`, `url`, estado,
hash y referencias); no trae `raw_html` ni modifica filas. El harvester vuelve a
resolver staging y courses por los IDs revisados, y conserva el URL almacenado al
promover la fila conocida. Sync recibe el `course_id` aprobado a través de
cleansed/enriched y comprueba una única identidad antes de upsert. Alias
duplicados, cambio de owner o aparición de un curso en un lote `new_discovery`
son deriva bloqueante, no dedupe automático. Esta lectura de inventario no
significa que los jobs consuman las colas globales: cleansing, enrichment y
sync siguen confinados a las relaciones incluidas en el manifest.

No se atribuye aquí frescura a los 224 cursos informados por el TL ni stale a
las 798 filas `processing` por su `created_at`. Antes de una corrida productiva
se exige lectura fresca y acotada de perfil, seed, URL, hash y estado, además de
la proyección de consumo de cada etapa. Los cursos elegibles y el backlog se
comparan por IDs; los conteos sirven como resumen, no como criterio de dedupe ni
como sustituto del manifest. La prueba local no es un snapshot de Pro.

No existe un único snapshot SQL que represente el remoto actual: restore_full_schema.sql y MASTER son fuentes locales históricas; Pro es el baseline de comparación. Los fixtures PG17 son desechables.

## Navegación relacionada

[Database](../database.md) · [Pipeline](pipeline.md) · [Migrations](database_migrations.md) · [Backend](../backend.md) · [Pruebas](../pruebas.md) · [HITO-002/003](../hitos/README.md) · [Decisiones](../decisiones/README.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#pipeline)

## Fuentes y relaciones

Los workers, modelos de estado, configuración de discovery y RPCs se asignan path por path en el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#pipeline). Los contratos de tablas y RPC que consumen están en [database](../database.md#rutinas-relevantes-por-proposito).
