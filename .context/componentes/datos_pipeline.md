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

## Perfilado inicial FG2 y recorrido editorial — candidato local 2026-11-20

El diagnóstico se ancla en una fila existente de `institutions`; no requiere
`institution_site_profiles` para empezar. Si existe un perfil completo activo,
se conserva y onboarding no lo vuelve a escribir. Si falta el perfil, la fila
pendiente separa los campos efectivos (sin modo runnable) de la observación,
la sugerencia y su procedencia. Una sugerencia verificada solo puede poblar un
perfil autogenerado/incompleto bajo la política explícita; un perfil manual
validado no se sustituye. El nuevo `allowed_resource_origins` es una lista JSON
de orígenes exactos para recursos del navegador, no un permiso DNS: cada
destino sigue validándose y pinneándose.

| Paso | Lectura/escritura y transición | Evidencia local | Límite |
|---|---|---|---|
| Diagnóstico | `institutions` → observado/sugerido/procedencia en `institution_site_profiles`; `pending_review` si falta certeza | `test_fg2_profile_onboarding.py`, Browser + HTTP controlados del E2E | no coteja configuración Pro ni scrapea instituciones |
| Discovery | sitemap, catálogo paginado o enlaces → URLs detalle elegibles | SSR, SPA y ecommerce sintéticos; páginas nuevas descubiertas desde el catálogo | no garantiza que la fuente real publique URLs utilizables |
| Harvest | GET controlado / Chromium interceptado → `staging_raw.discovered/pending/processed` con identidad y hash | PostgREST inserta filas sintéticas y los runners posteriores reciben el manifest hash | no verifica secret key, permisos ni datos remotos |
| Cleansing | claim por IDs de manifest; RPC SQL atómica → `cleansed_programs` y staging processed | migrations/RPC aplicadas en PG17 efímero, handoff entre contenedores | fixture no reproduce extensiones/roles/config completos de Pro |
| Enrichment | IDs asociados a staging manifest → salida validada en `enriched_programs` | provider `local_smart_mock`, fallo RPC inyectado y recuperación | no invoca ni acredita proveedor real o coste |
| Sync/editorial | IDs asociados → `courses` + `course_editorial_state.pending_review` | postflight por ID, Admin count/list RPC; nuevos ausentes de vista pública | no prueba la sesión/Auth Admin remota ni puede aprobar editorial |

La última ejecución del fixture reportó 6 cursos sintéticos, 5 en la cola
Admin pendientes y cero en `courses_public_effective`. El curso refreshed
retuvo su ID y override editorial. El conteo de PG17 no representa filas o
permisos de Pro. `processing` histórico no se resetea, y un refresh ordinario
usa el ID/manifiesto existente; reparación de filas abandonadas sigue siendo
operación separada con IDs concretos y JIT DML.

La cola de Admin usa `admin_get_course_queue_filtered` y
`admin_count_course_queue_filtered`. El componente mantiene el requisito AAL2;
para `admin` inicia en `editorial_status=pending_review` y manda
`p_quality_status=NULL`, por lo que los cursos nuevos con calidad pendiente
son visibles para revisión. El rol `user` conserva su filtro `draft` más
`quality_status=pending`. Un admin puede filtrar calidad después de cargar la
cola. Este ajuste no publica cursos: la decisión editorial sigue bajo el
estado/override y las RPC existentes. El fixture comprueba las RPC contra
PostgreSQL 17; el contrato UI focal comprueba los filtros iniciales, sin sesión
remota de Admin.

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
son deriva bloqueante, no dedupe automático. Solo la ejecución que recibe y
verifica el manifest queda confinada a sus relaciones.

### Consumidores de schedule FG2 — baseline anterior al manifest acotado

Esta sección conserva el contrato previo de colas globales, que motivó el
scope por manifest. En el candidato local del 2026-11-20,
`production_pipeline.yml` activa `FG2_COHORT_SCOPED` para schedule en `main`,
transporta y verifica el manifest entre jobs y cada worker limita sus lecturas
a IDs/relaciones aprobados. El runtime del workflow y sus variables remotas no
se consultaron en este ciclo.

En `schedule`, el workflow ejecuta el orquestador ordinario con
`--limit 10 --skip-cleansing`; la fase de cleansing corre después en otro job y
ninguno recibe el manifest. El límite del harvesting no restringe esas colas:

- Cleansing llama `lock_staging_records(inst_id=NULL, batch_size=100)` y repite
  hasta el time guard, sin `max_records`. La RPC bloquea filas `staging_raw`
  `pending` de cualquier institución y las mueve a `processing`; si la
  institución no tiene pipeline habilitado, el worker las marca `skipped`.
  Tras fallos repetidos de RPC, el fallback consulta también `status=pending`
  global.
- Enrichment selecciona `cleansed_programs.status=pending` para todos los IDs
  de instituciones con `pipeline_enabled`, por lotes hasta su límite temporal.
  Puede invocar proveedores sobre filas que no produjo ese harvesting.
- Sync selecciona `enriched_programs.status=pending` para las instituciones
  habilitadas y procesa esa selección hasta su time guard; no recibe un límite
  de cohorte desde el cron.

Los estados `discovered`, `processing` y `processed` no son seleccionados por
esas consultas normales de cleansing; activar cron no los reencola ni refresca.
Los agregados `processing` observados no permiten concluir qué IDs se moverán.
Antes de E10 se requiere un alcance de consumo por IDs y el control programado
que preserve filas históricas; no se reabre `processed`, no se resetea
`processing` y no se deduplican filas por conteos.

## FG3: cohorte pública y transición atómica — candidato local 2026-11-15

El candidato selecciona IDs y valores efectivos desde `courses_public_effective`.
Luego consulta `courses` solo para esos IDs para obtener `institution_id`, URL,
activo, verificado y `last_404_at`. Una diferencia o una fila que ya no esté
activa/verificada se omite antes del request. La comprobación y escritura final
se ejecutan juntas en `fg3_apply_public_course_transition`: la función vuelve a
validar la vista efectiva y los valores base observados dentro de la misma
transacción, con locks sobre el perfil, estado editorial, membresía legacy y
curso. Si la elegibilidad o el snapshot cambió, devuelve `stale` y no escribe.

La función solo puede cambiar `courses.last_404_at` o `courses.is_active`.
404/410 inicia la gracia y solo desactiva después de tres días completos; 2xx
puede limpiar el marcador y los errores transitorios no llaman la función. No
hay caducidad por fecha. La RPC es `SECURITY DEFINER`, fija `search_path` vacío,
califica las relaciones y retira `EXECUTE` de `PUBLIC`, `anon` y
`authenticated`; solo `service_role` la puede invocar. El cliente hace un único
POST, deshabilita redirects y detiene el lote ante un resultado ambiguo o
rechazado, sin repetir una posible escritura.

La validación local en Docker/PG17 usa filas sintéticas, incluida una retirada
editorial concurrente que hace esperar al RPC: tras el commit concurrente la
función devuelve `stale` y conserva la fila sin escritura. Esto no demuestra
schema ni ejecución remotos. La migración es local, forward-only y no se aplicó
a Pro; requiere revisión y autorización DDL exacta antes de desplegar el caller.

No se atribuye aquí frescura a los 224 cursos informados por el TL ni stale a
las 798 filas `processing` por su `created_at`. Antes de una corrida productiva
se exige lectura fresca y acotada de perfil, seed, URL, hash y estado, además de
la proyección de consumo de cada etapa. Los cursos elegibles y el backlog se
comparan por IDs; los conteos sirven como resumen, no como criterio de dedupe ni
como sustituto del manifest. La prueba local no es un snapshot de Pro.

El GET controlado usa `stream=False` y `content_callback` con un máximo
acumulado de 2 MiB antes de crear `response.content` o parsear HTML/XML. Al
detectar que el próximo chunk excedería el tope, el callback devuelve
`CURL_WRITEFUNC_ERROR` para abortar la transferencia; no usa
`Content-Length` como autoridad ni depende de devolver una escritura parcial.
El contexto de la sesión cierra el transporte al terminar o abortar la llamada.
Un exceso en HTTP 200 difiere el origen y no crea staging. Para 403/429 conserva
la clasificación de bloqueo sin reintento; para otros estados HTTP conserva
cabeceras necesarias para procesar redirects o `Retry-After`, sin parsear el
cuerpo parcial. El transporte ordinario no usa este callback y no tiene este
límite de bytes; tampoco lo tiene el cuerpo renderizado por Playwright. Este
riesgo no se resuelve al acotar las colas de workers.

Las URLs descubiertas nuevas quedan en memoria y solo crean staging tras un
body válido y parseable. Las filas históricas preexistentes quedan intactas.
Docker `--network none` valida cuerpo válido, respuesta chunked sin longitud,
desconexión temprana, cero staging writes por exceso y creación de staging tras
un parseo válido. No es una consulta a fuentes institucionales ni un resultado
productivo.

No existe un único snapshot SQL que represente el remoto actual: restore_full_schema.sql y MASTER son fuentes locales históricas; Pro es el baseline de comparación. Los fixtures PG17 son desechables.

## Navegación relacionada

[Database](../database.md) · [Pipeline](pipeline.md) · [Migrations](database_migrations.md) · [Backend](../backend.md) · [Pruebas](../pruebas.md) · [HITO-002/003](../hitos/README.md) · [Decisiones](../decisiones/README.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#pipeline)

## Fuentes y relaciones

Los workers, modelos de estado, configuración de discovery y RPCs se asignan path por path en el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#pipeline). Los contratos de tablas y RPC que consumen están en [database](../database.md#rutinas-relevantes-por-proposito).
