# Componente: pipeline FG1/FG2/FG3

## Estaciones y contratos

| Estación | Fuente → destino | Trabajo y estado |
|---|---|---|
| FG1 discovery | config/institution_sources.json → institutions e institution_site_profiles | discovery_institutions.py comprueba instituciones y puede insertar las faltantes; --no-insert detiene el caso sin catálogo. Escritura de catálogo, autorización operacional separada. |
| FG2 orchestration | perfiles y flags → tareas por institución | master_orchestrator.py decide elegibilidad/recencia/circuit breaker, ejecuta workers por subproceso y aplica time guard. |
| FG2-1 harvester | web/sitemap/config → staging_raw | universal_harvester.py descubre URLs, filtra/noise/exclusiones, canonicaliza, extrae HTML/metadata, calcula SHA-256 content_hash y omite contenido sin cambio. En el modo controlado, el GET limita el cuerpo antes de parsearlo. |
| FG2-1.5 cleansing | staging_raw → cleansed_programs | cleansing_worker.py bloquea batch, limpia texto, consolida páginas y filtra ruido; usa atomic_cleansing_promote y conserva estados/errores de origen. |
| FG2-2 enrichment | cleansed_programs → enriched_programs | enrichment_worker.py aplica prompt/campos, normaliza respuestas y usa proveedor configurado con fallback/mock; atomic_enrichment_promote guarda la unidad de trabajo. |
| FG2-3 sync | enriched_programs → courses + editorial quality | sync_vector_worker.py es writer normal de datos finales, conserva overrides y aplica guards de mock/canary/quality. El nombre no acredita embeddings activos. |
| FG3 integrity | courses → PATCH limitado de courses | integrity_ping.py revisa enlaces; la tolerancia histórica da ventana de 3 días antes de desactivar. |

## Mapa de módulos mantenidos

| Archivo/símbolo | Responsabilidad e interfaz local | Consumidor/dependencia demostrada | Datos y permiso |
|---|---|---|---|
| `config/institution_sources.json` | Lista de instituciones/hosts que lee `load_sources()`; no ejecuta requests por sí misma. | `scripts/core/discovery_institutions.py`; el workflow FG1 declara el comando. | Configuración declarativa del catálogo. Cambiar slug/host obliga a revisar el perfil y `--source-slug` del canario. |
| `scripts/core/discovery_institutions.py` | `load_sources()` selecciona config; `run_discovery(..., allow_insert)` verifica instituciones/perfiles y `--no-insert` mantiene el preflight sin insertar. | `.github/workflows/fg1_inventory.yml`; `.github/workflows/production_canary.yml` lo invoca con `--no-insert`. | `institutions`, `institution_site_profiles`; el modo normal puede insertar catálogo/perfil y requiere autorización de escritura. |
| `scripts/core/master_orchestrator.py` | `get_institutions()` resuelve cohortes/gates/recencia/circuit breaker; `run_script()` lanza workers por subprocess con timeout; `main()` aplica límites y flags. | Job FG2 en `production_pipeline.yml`; sus subprocessos y jobs siguientes son etapas separadas. | Lee perfiles/estado y lanza subprocessos; los procesos hijos pueden tocar DB/red. `--limit`, exclusiones y modo canario cambian el lote. |
| `scripts/core/universal_harvester.py` | `UniversalHarvester` obtiene sitemap/BFS, aplica hosts/gates/exclusiones, extrae HTML/metadata y calcula hash del contenido antes de registrar la URL. | Job de orquestación FG2; `cleansing_worker.py` consume `staging_raw`. | Web externa y `staging_raw`; escribe usando identidad de pipeline autorizada. `content_hash` evita repetir contenido igual, no representa identidad única de curso. |
| `scripts/core/cleansing_worker.py` | `CleansingWorker` reclama staging, limpia/consolida páginas, aplica ruido y fechas/precio, registra errores y promueve el batch con RPC atómica. | Job separado de `production_pipeline.yml`; RPC lock/promote en el ledger DB. | `staging_raw → cleansed_programs`, estados y errores; writer de pipeline. |
| `scripts/core/enrichment_worker.py` | `EnrichmentWorker` prepara prompt/contexto, aplica proveedores, normaliza la respuesta; `process_enrichment_records()` limita/agrupa intentos. | Job separado de `production_pipeline.yml`; proveedores por nombre y fallback local/mock según flag. | `cleansed_programs → enriched_programs`; variables por nombre `OPENCODE_API_KEY`, `CF_ACCOUNT_ID`, `CF_API_TOKEN`. Un proveedor real usa red/costo; ninguno se invocó aquí. |
| `scripts/core/sync_vector_worker.py` | `SyncVectorWorker` valida datos normalizados/calidad/guards y persiste cursos, respetando ownership editorial. El nombre no prueba que embeddings estén activos. | Job separado de `production_pipeline.yml`; `roi_engine.py` calcula campos ROI. | `enriched_programs → courses`; writer normal final, requiere permisos de pipeline y preflight de modo. |
| `scripts/core/integrity_ping.py` | `is_safe_public_url()`/`resolve_public_host()` validan IP pública; `request_pinned_public_url()` fija DNS para request HTTPS/HEAD; `patch_course_exact_one()` limita la mutación a una fila; `run_integrity_ping()` aplica ventana de gracia antes de desactivar. | `.github/workflows/fg3_integrity.yml` (comando desde `scripts/core`); `production_canary.yml` lo usa con límites canario. | Lee URLs de `courses`, requests externas y puede PATCH de un curso exacto; exige permiso writer y protección anti-SSRF. |

### Contrato de retirada FG3 — candidato local 2026-10-28

Una fecha de inicio antigua, disponibilidad vencida/desconocida o una falla
transitoria no desactivan el curso. La regla local conserva la gracia de más de
tres días desde `last_404_at` y requiere observaciones repetidas 404/410 para
desactivar, dejando curso y auditoría existentes. HTTP 200 solo acredita respuesta
del URL: no prueba que el programa siga listado en el catálogo institucional. La
retirada semántica de páginas 200 queda limitada y trazada a H1; no se incorpora un
crawler nuevo. Prueba sintética: `tests/test_integrity_ping_retirement_contract.py`;
resultado por corte en el [checkpoint CA4](../evidencia/h3req1_editorial_contract_2026-10-28.md).

Los YAML prueban wiring declarado. El workflow FG2 invoca `master_orchestrator.py --skip-cleansing` y mantiene jobs separados de cleansing, enrichment y sync; no asumir que el padre ejecutó todas las etapas. Horarios reales y ejecuciones quedan remotos.

## Gates y perfiles

La implementación actual usa los gates Fase 100 discovery_enabled, pipeline_enabled y production_enabled, configurados por institution_site_profiles. Los workers conservan fallback temporal a pipeline_ready cuando el gate moderno no existe o no se puede leer según su adapter. Fase 75 documenta la historia de pipeline_ready y no debe reactivarse como contrato nuevo. discovery_enabled no es lo mismo que procesar; production_enabled gobierna publicación.

## Concurrencia, idempotencia, requeue y errores

Harvester usa content_hash SHA-256 y estados para no reprocesar contenido idéntico. SQL lock_staging_records/lock_cleansed_records marca trabajo y evita que workers consuman dos veces una misma cohorte; RPC atómicas preservan estados de origen/destino. Orchestrator time guard y circuit breaker limitan un job largo; gate cerrado salta institución. Los workers registran processing_error/reason/error y no consideran output LLM como schema garantizado. La regla de retry/requeue está en RPCs y scripts; no requeue en esta transferencia.

## Primera corrida FG2 acotada — candidato local 2026-11-09

El candidato local añade `bounded_first_run` al `workflow_dispatch`, con valor
predeterminado `false`, y exige referencia, SHA-256 y bytes Base64 del lote
revisado para entrar en ese modo. El cron diario `0 5 * * *` continúa usando el
camino ordinario, que no consume estos manifests y conserva los límites vigentes.
El camino ordinario puede leer colas globales; habilitarlo o despacharlo requiere
los gates propios y una revisión separada de ese alcance.

La ejecución controlada mantiene el selector rotativo por
`last_harvest_at ASC NULLS FIRST`, exige que las instituciones aprobadas sigan
siendo el prefijo elegible de esa rotación, y valida perfiles, elegibilidad y
seeds antes del contacto externo. Dentro de cada institución elegible, el lote
puede fijar un subconjunto ordenado, único y de mismo origen de sus seeds
configurados; el preflight vuelve a validar ese subset contra el perfil vigente
antes de cualquier contacto. Esto no cambia el orden ni sustituye instituciones
de la rotación. El lote revisado está ligado al SHA de fuente,
referencia humana, huella de institución, hashes de perfil/seeds y cada URL
permitida con su hash y snapshot de IDs/estados en staging, courses y referencias
downstream. Relee ese snapshot antes de lanzar el harvester, antes del primer
request y antes de la primera escritura; ante deriva termina sin sustituir
instituciones ni ampliar URLs. El manifiesto de entrada tiene un máximo de 40
KiB. El transporte queda limitado a una
solicitud simultánea por origen, al menos 5 segundos entre inicios, 10 URLs
únicas incluyendo URLs de sitemap, y 20 inicios HTTP por institución; los
redirects y reintentos cuentan para el presupuesto. Solo espera `Retry-After`
válido de hasta 30 segundos; si
excede ese máximo, difiere el origen. Ante 403 o 429 detiene ese origen sin
reintentar la respuesta de bloqueo. Cada salto valida DNS público y fija la IP
validada en una sesión HTTPS directa, sin proxy de entorno, redirects ni retries
automáticos.

El GET de `UniversalHarvester` en la cohorte controlada usa streaming y acumula
los bytes en la aplicación, sin confiar en `Content-Length`. Para HTTP 403/429
consulta el estado y cierra la respuesta antes de iterar o materializar el
cuerpo; la implementación instalada de `curl_cffi` puede haber puesto el primer
chunk en su cola interna al entregar el stream, pero el harvester no lo consume,
no lo parsea y no escribe por esa respuesta. Para los demás estados acumula
hasta 2 MiB; al recibir un chunk que excedería el tope, cierra y falla antes de
parsear HTML/XML o crear staging. La prueba sintética diferencia bytes ya
encolados por el transporte de bytes consumidos/materializados por el harvester.
El GET ordinario de `UniversalHarvester` también valida y fija por DNS público
cada destino HTTP inicial y cada redirect en una sesión directa, con TLS, sin
proxy de entorno, redirects automáticos ni retries. Para preservar
canonicalizaciones institucionales, puede seguir un redirect a otro host si
ese destino también resuelve exclusivamente a IPs públicas.

El límite de cuerpo de 2 MiB se aplica al transporte controlado, incluido el
candidato de cohorte programada. El dispatch manual sin `bounded_first_run`
conserva el transporte ordinario y no hereda este límite. La ruta de Playwright
ya no continúa solicitudes HTTP(S): Chromium resolvería DNS por separado del
socket fijado por curl, por lo que el guard aborta esas solicitudes hasta contar
con un transporte de navegador que pueda fijar DNS y aplicar el mismo
presupuesto. El transporte ordinario HTTP sigue validando y fijando cada
destino inicial y redirect.

La autodetección en `site_diagnostics.py` lee en streaming hasta 2 MiB, cierra
sin consumir los cuerpos intermedios y valida/pinea cada redirect antes del
siguiente GET. Bloquea loopback, redes privadas/link-local, destinos reservados,
userinfo, puertos no soportados y respuestas DNS mixtas; conserva redirects a
otros hosts solo cuando cada salto pasa la misma validación pública.

El 403/429 de una corrida controlada se cierra antes de que el harvester lea el
body y detiene el origen sin reintento. Las URLs con filas staging en estados
protegidos tampoco consumen el máximo de URLs cosechables: se registran como
blockers con límite propio y la búsqueda continúa por el sitemap hasta reunir
hasta diez URLs nuevas o `discovered` elegibles. Los redirects, reintentos,
páginas seed y extracción HTTP se cuentan dentro del límite de la institución.
El modo controlado rechaza perfiles que necesitan Playwright antes de
contactar el origen y su guard común también falla antes de `page.goto`. La
ruta ordinaria conserva la navegación Playwright existente, incluida la
validación de forma de la URL inicial; esa navegación no comparte el pin DNS ni
los límites del transporte HTTP acotado y no acredita cobertura de E9/E10.

El modo bounded usa solo el transporte HTTP que pasa por ese presupuesto. El
preflight admite perfiles `traditional_ssr` y rutas de discovery HTTP; perfiles
SPA/ecommerce, `catalog_link_extraction`, stealth o bypass anti-bot quedan fuera.
Una ejecución programada en `main` crea un manifiesto ligado a run, intento y
SHA y pasa al proceso hijo `--scheduled-cohort`, distinto de `--controlled` de
la primera corrida manual con lote revisado. El preflight del hijo exige evento
`schedule`, ref `refs/heads/main`, manifest y límites exactos, pero no exige ni
acepta el lote de aprobación manual. La selección limita la rotación a diez
instituciones elegibles de transporte bounded, 10 URLs y 20 solicitudes HTTP
por institución, una solicitud simultánea por origen, 5 segundos entre inicios
y `Retry-After` de hasta 30 segundos. El presupuesto incluye redirecciones y
reintentos. Los perfiles que requieren Playwright se difieren antes de contacto
y no se sustituyen dentro de la cohorte.

En este modo, `sitemap_bfs` conserva la ruta ordinaria: el preflight de
schedule fija `{website_url}/sitemap.xml`; los `seed_urls` del perfil no se
interpretan como XML cuando son páginas de catálogo o cursos. Cada destino de
redirect consume tanto una solicitud HTTP como una URL única antes de seguirlo,
por lo que un redirect fuera del presupuesto se detiene sin el siguiente GET.
El sync bounded lee una vez por invocación el inventario de alias de `courses`
y actualiza esa copia con los cursos que escribe durante la misma corrida; las
comprobaciones por ID aprobado siguen haciendo una lectura exacta y fresca.
Para `new_discovery`, el inventario solo detecta si la URL ya tiene alias y el
conjunto de cursos existentes usado como destino de escritura queda vacío; una
fila ajena del inventario nunca puede convertirse en el objetivo del upsert. Una
denegación del guard DNS antes del primer request se persiste como `deferred`
con `last_started_monotonic=null` y evita nuevos contactos a ese origen en la
corrida; `blocked` sigue requiriendo un inicio HTTP real de 403/429.
El workflow FG2 y `production_canary.yml` comparten además el grupo root
`studiamatch-fg2-${{ github.ref }}` con `cancel-in-progress: false`, para que
los callers de Actions del mismo ref no procesen en paralelo las filas del
pipeline. Esta serialización abarca workflows completos; no es una reclamación
transaccional por fila y depende de que el writer entre por esos workflows.

La primera corrida manual con lote revisado conserva sus URLs exactas: si el
perfil usa `sitemap_bfs`, cada seed aprobado de página se procesa como
candidato dentro del lote y no se intenta parsear su HTML como documento XML.
No se expande la cohorte mediante enlaces fuera del lote. Para clasificar un
refresh ordinary, el harvester aplica la misma limpieza de sufijos de URL que
cleansing (`/presentacion`, entre otros) antes de buscar el `course_id` en
`courses`; así un alias de detalle no se etiqueta como descubrimiento nuevo
cuando cleansing lo agrupa con un curso existente. El hash de URL solicitada
se conserva por separado del hash de identidad que consumen los workers.

La misma cota de diez URLs únicas por institución limita las URLs válidas
examinadas, incluidas las que ya tienen filas `staging_raw` en estados protegidos.
Esas filas se registran como bloqueos, no pasan a la cohorte downstream y nunca
se reabren. Al llegar al límite, sitemap, seeds o paginación dejan de examinar
URLs nuevas; así el manifest mantiene como máximo diez bloqueos por institución
y no intenta transportar un sitemap histórico completo entre jobs.

El manifiesto de corrida queda ligado a run, intento, SHA de fuente, IDs y hashes
de perfil, seeds, URL cruda, URL efectiva/canónica según la precedencia de
cleansing y contenido. Cleansing
consulta únicamente los IDs `staging_raw` del manifiesto; enrichment filtra por
esos `staging_id`; sync deriva los `cleansed_id` del mismo conjunto y solo filas
`enriched_programs.pending` exactas. Cada etapa revalida institución, estado,
relaciones y hashes. Las colas históricas ajenas no entran en la selección y no
se resetean ni reabren. El workflow transporta el digest entre jobs y conserva
el manifiesto como artifact por siete días. Un job `SUCCESS` no acredita que
hubiera trabajo; se revisan filas y resultados funcionales.

Si el schedule termina sin filas nuevas o modificadas después de una lectura
exitosa, el manifest registra `no_op` y se actualiza `institutions.last_harvest_at`
como marcador de intento para avanzar la rotación. Ese marcador no significa
refresh ni ejecución funcional; una corrida que solo descubre o que queda
`blocked`/`skipped` tampoco acredita actualización de cursos.

El evento `schedule` usa este camino bounded y por manifiesto; el
`workflow_dispatch` manual sin la opción bounded conserva el camino ordinario
con aprobación de `Production`. Desarrollo y Certificación siguen bloqueados
antes de Environments y credenciales. Este wiring es local y no activa el cron,
los flags ni los writers remotos.

La clasificación distingue `new_discovery` (sin fila de curso conocida) de
`refresh_existing` (misma URL asociada a un `course_id` de esa institución).
Un refresh sintético conserva el ID de curso y `course_editorial_state`; el
contrato editorial mantiene `manual_override` y su timestamp en sync. La
unicidad histórica de `staging_raw.url` impide reciclar silenciosamente una fila
`processing`, `processed`, `discarded` o `skipped`: se registra el bloqueo en el
manifest y no se reabre ni se resetea. Cualquier transición manual de esos
estados exige un dry-run con IDs exactos y DML aprobada fuera de este ciclo.

La identidad del lote usa la misma función `normalize_url` que el harvester
(quita query/fragment y slash final, baja scheme/host y retira `/en/`). El
`url_sha256` del scope aprobado identifica esa URL normalizada; el `url_sha256`
de cada entrada del manifest de corrida coincide con el URL exacto que el writer
deja en `staging_raw`, pues cleansing valida la fila almacenada. El digest del
lote también vincula las URLs exactas de los snapshots de `staging_raw`,
`courses` y filas downstream. Para no leer/paginar tablas completas, la
revalidación agrupa
por institución únicamente las URLs aprobadas y construye un filtro regex
PostgREST anclado a su identidad normalizada. El patrón contempla scheme/host
con mayúsculas, `/en/` antes de segmentos, el slash final y query/fragment que
`normalize_url` elimina, manteniendo sensible a mayúsculas el path. Cada lectura
usa `limit=URLs_del_grupo+1` (o `IDs_de_referencia+1`); más filas que URLs
aprobadas detienen el lote y las duplicidades dentro del límite se detectan al
comparar por identidad. Por institución se hacen como máximo seis lecturas
metadata acotadas: cuatro relaciones por alias y hasta dos por `staging_id` /
`cleansed_id`; con diez instituciones son hasta sesenta requests de base de
datos y cada respuesta se limita a once filas. Un owner o estado/hash distinto
detiene el lote antes del harvester. El harvester vuelve a leer las filas
aprobadas por ID, y la primera promoción conserva el URL exacto existente de
staging; el hash de la entrada se calcula sobre ese mismo URL. Cuando un nuevo
scope no tenía fila `staging_raw` al preflight, la comprobación después del
contacto filtra por la institución aprobada y los aliases de una sola URL, con
`limit=2`, en vez de paginar la tabla completa o cruzar instituciones; cualquier
alias nuevo o ambiguo de esa institución detiene antes de escribir. El sync recibe el `course_id` del manifest por la cadena
staging→cleansed→enriched, confirma que solo una fila de courses conserva esa
identidad y escribe sobre su URL exacta. Para `new_discovery`, un curso que
aparezca con cualquier alias después del preflight detiene el writer. Estas
lecturas son de metadatos y no reinician ni consumen las colas.

Si el presupuesto se agota durante un sitemap controlado, `_fetch_sitemap`
devuelve los enlaces de los documentos que ya leyó y no inicia otra solicitud.
El schedule puede guardar esos enlaces permitidos como `staging_raw.discovered`
y `manifest.discovery_rows`; marca la institución `deferred` y no añade esos
IDs a `manifest.entries`, por lo que cleansing/enrichment/sync no los consumen
en ese run. Un schedule posterior los retoma si aún aparecen en el sitemap.
El lote manual conserva su manifest exacto y no persiste candidatos parciales
fuera de las entradas que puede procesar. Seeds `.xml.gz` se rechazan en el
preflight controlado; si un sitemap ya leído anuncia uno, se difiere el origen
antes de solicitar el cuerpo comprimido. No se descomprime contenido sin un
límite de salida probado.
La identidad usada para resolver `course_id` es `normalize_url` aplicada a la
URL de cleansing (`cleanse_course_url`); se usa tanto en schedule como en el
lote revisado, incluidos detalles `/presentacion` y variantes `/en/`. El
snapshot conserva el URL crudo/staging y el URL almacenado del curso por
separado, y el lote se rechaza si dos entradas derivan al mismo curso. Los
queries de cursos siguen limitados a aliases de la cohorte aprobada.

El lookup de cursos también contempla que `courses.url` haya conservado uno de
los sufijos de detalle que cleansing elimina, como `/presentacion`. El filtro
regex anclado incluye la identidad normalizada, el URL solicitado y solo los
sufijos conocidos; dos filas que coincidan siguen causando rechazo por
ambigüedad. Así el schedule no puede convertir una URL ya persistida como
detalle en una alta duplicada.

Al sincronizar un `course_id` aprobado, el writer vuelve a comprobar el
inventario y la fila leída por ID con `course_identity_url`, la misma función
que aplica limpieza de sufijos conocidos y normalización `/en/`. Exige una sola
fila, el ID aprobado, la misma institución y la misma identidad; cualquier
ambigüedad o deriva se rechaza antes del upsert. Si valida, conserva el URL
exacto ya almacenado como destino de conflicto.

Si una institución bounded obtiene al menos una URL correcta y otra falla por
un error no bloqueante, el harvester registra `partial` y sale con código que
permite ejecutar las etapas downstream sobre las entradas exitosas del manifest.
El parser acepta `partial` solo cuando hay entradas; cleansing, enrichment y
sync mantienen los mismos filtros de ID/relación/estado y no consultan colas
globales. Con cero filas exitosas el harvester conserva el fallo y no lanza las
etapas siguientes. En schedule, `no_op`, `partial`, `blocked` y `deferred`
registran `last_harvest_at` como marcador de intento para mantener la rotación.
Para `blocked`/`deferred`, el registro ocurre al cerrar el manifest aunque el
origen se haya detenido por 403/429 o por un Retry-After fuera del presupuesto.
El resultado y el marcador no acreditan refresh ni reemplazan la evaluación de
resultados por fila.

La ventana entre lecturas y writes sigue sin transacción compartida: el sync
revalida la identidad canónica inmediatamente antes del upsert y falla si detecta
deriva, pero la base no impone unicidad sobre esta normalización. El control
reduce la ventana funcionalmente y conserva evidencia exacta; no equivale a un
lock/constraint DB ni resuelve duplicados históricos fuera del lote.

El `CurlOpt.RESOLVE` de `curl_cffi` recibe una lista de entradas, aun cuando el
pin calculado corresponda a un solo salto. El harvester y el diagnóstico
comparten ese formato en GETs y en cada redirect validado; el binding se prueba
localmente sin abrir sockets. La ruta browser ordinaria no usa `curl_cffi`; el
modo acotado la rechaza antes de navegar. Por ello los perfiles Playwright no
tienen refresh en esta cohorte hasta validar un transporte browser bounded
compatible. La navegación ordinaria existente aplica solo a corridas no acotadas
con aprobación Production y no se considera una alternativa para el schedule.

La transición es aditiva: `expand` añade el modo opt-in y el manifest;
`compatibilidad` conserva default false y el camino ordinario; `deploy` pasa por
promoción protegida; `contract` queda pendiente de evidencia funcional y gates
posteriores. Rollback local: descartar el diff aislado. Tras una eventual
integración, revertir por el mismo flujo protegido; ninguna etapa de este
contrato activa schedules o cambia flags.

## Proveedores, simulación y discrepancia documental

El código actual construye dos proveedores: DeepSeek v4 Flash por endpoint OpenCode-compatible, seguido de Cloudflare Workers AI Meta Llama 3.1 8B. Si proveedores fallan, el worker puede usar mock/smart-mock y marcar provider_used/is_mock_data. Variables por nombre: OPENCODE_API_KEY, CF_ACCOUNT_ID, CF_API_TOKEN. No se leyeron valores ni se invocaron servicios.

AGENTS.md y notas históricas describen CF → GitHub → Gemini. Ese orden no coincide con scripts/core/enrichment_worker.py en este candidato. Se registra la diferencia como conflicto documental y runtime remoto desconocido; no se infiere disponibilidad ni se altera funcionalidad.

## Writers, schedules y límites

Los YAML declaran FG1 mensual, FG2 diario y FG3 diario UTC y dejan
`workflow_dispatch`; la existencia del trigger no prueba activación o ejecución
remota. El candidato local 2026-11-09 agrega un `main_ref_guard` sin credenciales
antes de los Environments y jobs de FG1/FG2/FG3, limita el preflight de cada
estación a `refs/heads/main` aun con flags permisivos y conserva el mismo límite
en el job de Production Canary antes de asignar `Production`. Los demás jobs
funcionales dependen del guard; DB Sync conserva su control separado. La prueba
Docker de YAML y shell es contrato local, no adopción de GitHub. Los writers
habituales de courses son `sync_vector_worker.py` y `integrity_ping.py`; los
harvesters dedicados siguen históricos/legacy según AGENTS.md. Los scripts de
`maintenance` incluyen bypasses, migraciones, seeds, deletes y cross-env;
revisar cada callgraph y obtener JIT antes de ejecutar.

## Pruebas, evidencia y cómo modificar

Tablas/RPC están descritas en [database.md](../database.md). `tests/test_fase121_extractors.py` cubre extractores/selectores declarativos; `tests/test_h2_pipeline_contract.py` comprueba contratos de campos y estados entre workers; `tests/test_h3req1_local_pipeline_walk.py` cubre el recorrido sintético y recuperación; R18 conserva una suite histórica de URL/esquema/host/gates, pero su fuente `tests/test_h3req1_pipeline_discovery_boundaries.py` no existe en este checkout; el modo acotado actual se cubre con `tests/test_fg2_bounded_orchestration.py` y `tests/test_fg2_bounded_run.py`; `tests/h3req1_pipeline_postgrest_pg17_integration.py` y `tests/sql/h3req1_pipeline_*_r1.*` recorren persistencia en fixture local. `tests/test_harvester.py` es una suite distinta de cuatro consultas Supabase live, con opt-in y credenciales, no un parser unitario; en R160 sus cuatro casos quedaron skipped y no se consultó servicio live. El mapa fuente→caso→resultado, límites de hash y alcance de búsqueda está en [relaciones locales del pipeline](../evidencia/h3req1_sem_pipeline_relaciones_locales_2026-10-13_r11.md). R178 conserva resultados funcionales locales históricos; no se repitió suite funcional porque las fuentes de producto no cambiaron durante esta documentación.

Al cambiar filtros/config de discovery, renovar `test_fg2_bounded_orchestration.py` y `test_fg2_bounded_run.py`, revisar tests de canario por path y conservar R18 solo como evidencia histórica mientras falte su fuente; extracción, `test_fase121_extractors.py`/pipeline walk (no `test_harvester.py`, que es live); locking/estados/promoción, harnesses de persistencia y atomicidad; proveedor, validación sintética de prompt/fallback sin credenciales reales; sync/publicación, consumidores ROI/editoriales y el contrato efectivo H2/H3. Schema nuevo: migration expand, compatibilidad mientras se promociona, contracción con rollback verificable y permiso SQL separado.

## Navegación relacionada

[Datos del pipeline](datos_pipeline.md) · [Database](../database.md) · [Operación](../operacion.md) · [CI/CD](../ci_cd.md) · [Seguridad](../seguridad.md) · [Pruebas](../pruebas.md) · [HITO-001/002](../hitos/README.md) · [Requerimientos](../requerimientos/README.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#pipeline)

## Fuentes y relaciones

El [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#pipeline) asigna cada estación y configuración a su contrato, consumidores demostrados, datos, pruebas y modo de operación. Los scripts de mantenimiento y harvesters legacy tienen fichas separadas y no se autorizan por su presencia en el repositorio. Las fuentes retenidas como [legacy/deprecated](../trazabilidad/registro_fuentes_componentes.md#legacy-y-deprecated) conservan operación e historia clasificadas, no una autorización de uso.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Evidencia histórica de requerimientos e hitos](../catalogos_historicos/requerimientos_hitos.md#documentos-preservados)
