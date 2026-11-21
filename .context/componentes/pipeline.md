# Componente: pipeline FG1/FG2/FG3

## Estaciones y contratos

| Estación | Fuente → destino | Trabajo y estado |
|---|---|---|
| FG1 discovery | config/institution_sources.json → institutions e institution_site_profiles | discovery_institutions.py comprueba instituciones y puede insertar las faltantes; --no-insert detiene el caso sin catálogo. Escritura de catálogo, autorización operacional separada. |
| FG2 orchestration | perfiles y flags → tareas por institución | master_orchestrator.py decide elegibilidad/recencia/circuit breaker, ejecuta workers por subproceso y aplica time guard. En contextos controlados conserva solo diagnósticos versionados con fase/categoría allowlistadas y metadatos DB sanitizados; nunca publica stdout/stderr ni argumentos. |
| FG2-1 harvester | web/sitemap/config → staging_raw | universal_harvester.py descubre URLs, filtra/noise/exclusiones, canonicaliza, extrae HTML/metadata, calcula SHA-256 content_hash y omite contenido sin cambio. En el modo controlado, el GET limita el cuerpo antes de parsearlo. |
| FG2-1.5 cleansing | staging_raw → cleansed_programs | cleansing_worker.py bloquea batch, limpia texto, consolida páginas y filtra ruido; usa atomic_cleansing_promote y conserva estados/errores de origen. |
| FG2-2 enrichment | cleansed_programs → enriched_programs | enrichment_worker.py aplica prompt/campos, normaliza respuestas y usa proveedor configurado con fallback/mock; atomic_enrichment_promote guarda la unidad de trabajo. |
| FG2-3 sync | enriched_programs → courses + editorial quality | sync_vector_worker.py es writer normal de datos finales, conserva overrides y aplica guards de mock/canary/quality. El nombre no acredita embeddings activos. |
| FG3 integrity | courses_public_effective → RPC atómica limitada de courses | integrity_ping.py valida con HEAD/GET y decisión conservadora; el RPC revalida elegibilidad y snapshot en la transacción y solo cambia last_404_at o is_active. |

## FG2 multiformato y onboarding de perfiles — candidato local 2026-11-20

`run_profile_onboarding()` precede al selector dentro del entrypoint del
orquestador FG2. Examina solo instituciones existentes cuyos slugs están en
`FG2_PROFILE_DIAGNOSTIC_SLUGS`; perfil inexistente no es requisito para esa
primera lectura. `FG2_PROFILE_DIAGNOSTICS_ENABLED` permite diagnosticar;
`FG2_PROFILE_DIAGNOSTIC_PERSIST_ENABLED` controla persistencia de observación;
`FG2_PROFILE_AUTO_ACTIVATE_VERIFIED` es una política separada y requiere
persistencia habilitada. Son variables declaradas por workflow, no se
confirmaron valores de GitHub ni se habilitó ningún Environment.

`scripts/shared/site_diagnostics.py` limita a 20 las solicitudes HTTP externas por
diagnóstico y cuenta aparte los intentos WebSocket bloqueados,
3 redirects por respuesta, dos detalles de curso, 2 MiB por cuerpo y cinco
segundos entre requests del origen. Usa la política común de URL/SSRF, valida
DNS público y vuelve a validar cada redirect. Para SPA y ecommerce utiliza
Chromium con sandbox: HTTP y subrecursos pasan por la ruta interceptada y el
transporte HTTP validado; WebSocket se cierra antes de conectar, WebRTC y
WebTransport se deshabilitan antes de cargar la institución, QUIC queda apagado
y service workers bloqueados. Los intentos WebSocket quedan registrados como
bloqueos requeridos y no se envían al origen; sin evidencia de control completo el perfil queda en
`review_required`. La salida se sanitiza antes de guardarse:
quita tracking, retiene solo parámetros de paginación permitidos y redacciona
URLs sanitizadas mayores a 2.048 caracteres, dejando el diagnóstico en
`review_required` en vez de truncar y habilitar una URL distinta.

El runtime de `universal_harvester.py` instala las mismas fronteras de
transporte en cada `BrowserContext`, incluidos los perfiles `spa_js_heavy` y
`ecommerce` en modo ordinario y acotado. La ruta HTTP resuelve, valida, fija y
cuenta cada navegación/subrecurso mediante `FG2RequestBudget`; service workers
quedan bloqueados. WebSocket se cierra antes de conectar y cualquier intento
detiene la institución sin persistir el detalle parcial. RTCPeerConnection,
webkitRTCPeerConnection y WebTransport se deshabilitan y verifican sobre
`about:blank` antes de navegar. Si falta la API de interceptación o la
verificación no pasa, el contexto se cierra y el harvester no continúa.

### Estados, activación y límites

| Resultado del diagnóstico | Perfil/efectivo | Efecto | Evidencia requerida |
|---|---|---|---|
| Sin perfil | `pending_review`, modos efectivos nulos | Puede persistir observado/sugerido si la puerta de persistencia está abierta | diagnóstico con transport controls, origen y detalles de curso verificados |
| Incompleto o ambiguo | `pending_review` | No activa cosecha ni escritores | causa sanitizada y revisión posterior |
| Bloqueo 403/429 | `blocked` | Corta el examen de esa institución sin fallback evasivo | estado HTTP y conteo acotado |
| Sugerencia verificada + política de autoactivación | solo perfil autogenerado incompleto puede recibir campos efectivos | `discovery_enabled`/`pipeline_enabled`; `production_enabled` permanece false | política explícita, prueba del origen, programa nuevo y dos fichas |
| Perfil efectivo activo | conserva valores manuales/validados | onboarding rutinario no los reemplaza | el harvester aplica los gates efectivos existentes |

La columna histórica `pipeline_ready` no constituye por sí sola autorización de
diagnóstico, harvesting o producción. Las puertas de examen, persistencia,
activación de discovery/pipeline y `production_enabled` son distintas. La
detección de JavaScript no habilita stealth ni bypass. Una detección pendiente
no es selección elegible; el selector regular continúa fallando cerrado.

### Ensayo PG17/PostgREST acotado

`tests/fg2_full_pipeline_pg17/run.sh` construye un entorno efímero con migraciones
versionadas, roles sintéticos y red Docker interna sin egress. Llama los mismos
entrypoints de las cuatro estaciones desde procesos separados y valida
manifiesto, staging, cleansing, enrichment y sync mediante PostgREST real contra
PG17. HTTP institucional y proveedor de enrichment son simulados; el proveedor
registrado es `local_smart_mock`. En la última ejecución, el ensayo terminó
PASS con 6 cursos sintéticos en destino, 5 pendientes de revisión en la cola
Admin y 0 en `courses_public_effective`; el refresh preservó ID y override.
También comprobó perfil ambiguo, 403/429, fallo RPC transitorio con salida
no-cero y recuperación sin duplicación. No demuestra datos/proveedores reales,
permisos remotos, deployment, ni resultado productivo.

**Transición:** `expand` incorpora schema y modo explícito de diagnóstico;
`compatibilidad` conserva el camino existente y activa defaults conservadores;
`deploy` necesita PR/promoción protegida, baseline schema y autorización DB
JIT separada; `contract` queda después de un piloto funcional autorizado.
Rollback local es descartar el diff aislado. Después de integrar, reversión por
PR; no borrar observaciones ni ejecutar DDL rollback destructivo sin aprobación.

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
| `scripts/core/integrity_ping.py` | `run_integrity_ping()` selecciona desde `courses_public_effective`, lee la base solo para esos IDs y llama `fg3_apply_public_course_transition` para revalidar y escribir en una transacción. Cada probe valida/pinea DNS público, HTTPS y redirects; aplica HEAD/GET y retry bounded. | `.github/workflows/fg3_integrity.yml` (comando desde `scripts/core`); `production_canary.yml` lo usa con límites canario. | Lee URLs efectivas públicas y snapshots base de IDs seleccionados; el RPC solo cambia `last_404_at` o `is_active`. `stale` es NO-OP. La revisión local no acredita que la migration esté aplicada en Pro. |

### Contrato de retirada FG3 — candidato local 2026-10-28

Una fecha de inicio antigua, disponibilidad vencida/desconocida o una falla
transitoria no desactivan el curso. La regla local conserva la gracia de más de
tres días desde `last_404_at` y requiere observaciones repetidas 404/410 para
desactivar, dejando curso y auditoría existentes. HTTP 200 solo acredita respuesta
del URL: no prueba que el programa siga listado en el catálogo institucional. La
retirada semántica de páginas 200 queda limitada y trazada a H1; no se incorpora un
crawler nuevo. Prueba sintética: `tests/test_integrity_ping_retirement_contract.py`;
resultado por corte en el [checkpoint CA4](../evidencia/h3req1_editorial_contract_2026-10-28.md).

### Selección pública y PATCH condicional FG3 — candidato previo, supersedido

La selección y el contador de calidad leen `courses_public_effective`, que
proyecta valores editoriales efectivos y limita los cursos a la cohorte pública.
Después de seleccionar, FG3 consulta `courses` únicamente por bloques de IDs ya
seleccionados y obtiene `institution_id`, `url`, `is_active`, `is_verified` y
`last_404_at`. Si la fila ya no existe, cambió institución/URL o no está
activa/verificada, la omite antes del request. No se consulta `last_404_at` para
cursos ajenos a la vista.

Antes de escribir vuelve a consultar la vista para ese ID y compara su
`institution_id` y URL con la selección; si ya no aparece o difiere, omite el
PATCH. Cada escritura solo modifica `last_404_at` o `is_active` y compara en el
mismo PATCH el ID, `institution_id`, URL, `is_active=true`, `is_verified=true` y
el `last_404_at` observados en la fila base. Si el PATCH devuelve cero filas,
otra operación cambió el snapshot: se registra como stale NO-OP y no se
sobrescribe ese cambio. Una respuesta con
más de una fila, ID distinto o error HTTP sigue siendo error. La validación de
HTTPS/host público, DNS fijado, redirects, gracia 404/410 de tres días, errores
transitorios sin desactivación y ausencia de caducidad por fecha no cambian.

La vista también depende de estado ajeno a `courses`: `production_enabled` y la
exclusión canary del perfil institucional, el estado editorial publicado y la
membresía/availability de la cohorte legacy. La relectura detecta cambios ya
visibles antes de la segunda consulta; el PATCH sobre `courses` no puede incluir
esas condiciones en una comparación atómica PostgREST. Si una condición cambia
después de la relectura de la vista y antes del PATCH, el CAS base todavía podría
actualizar la fila aunque ya no pertenezca a la vista. Una corrida funcional
requiere resolver ese riesgo con una decisión explícita o una operación atómica
DB que vuelva a comprobar la vista y los campos base; esto último requiere
diseño, gate DB/JIT y validación independiente.

Transición: `expand` mantiene el lector legacy existente; `compatibilidad` limita
FG3 al conjunto que ya sirve la vista pública y conserva los mismos campos de
retirada; `deploy` queda pendiente del flujo protegido; `contract` solo se
considera después de verificar la corrida autorizada. Rollback: revertir por PR
la selección/CAS de aplicación después de detener el flujo bajo su autorización;
no restaurar cursos ni editar `courses` manualmente. La prueba Docker sintética
no demuestra despliegue, elegibilidad remota ni cierre de la carrera sobre las
tablas relacionadas.

El resultado CAS anterior conserva sus pruebas históricas, pero su ventana
lectura/PATCH queda supersedida por el candidato atómico siguiente. No es base
para ejecutar FG3.

### Transición pública atómica FG3 — candidato local 2026-11-15

`fg3_apply_public_course_transition` vuelve a consultar
`courses_public_effective` dentro de la misma transacción que actualiza una sola
fila de `courses`. La función valida ID, institución, URL, activo, verificado y
`last_404_at` observados; bloquea perfil, estado editorial, membresía legacy y
curso en ese orden; y devuelve `stale` sin escritura si perdió elegibilidad o
detectó deriva. El lock de la tabla H2 de membresías es dinámico y opcional:
H2 puede haber retirado esa tabla, en cuyo caso la vista H3 conserva cero
miembros legacy y las filas publicadas estrictas siguen operando. Para
`deactivate_after_grace` calcula tres días completos con el reloj de la base,
no con el reloj del proceso.

El cliente llama una vez a la RPC con `service_role`; no sigue redirects ni
reintenta writes ambiguos o rechazados y detiene el lote ante esos errores. La
RPC fija `search_path` vacío y concede `EXECUTE` únicamente a `service_role`.
El harness PG17 confirma ACL, idempotencia, gracia y una retirada `unpublish`
concurrente: el RPC espera el lock, reevalúa la vista tras el commit y devuelve
`stale` con cero cambios a `courses`. Las pruebas locales usan fixtures; no
acreditan permisos, advisors, schema o ejecución de Pro.

Transición: `expand` añade la función sin modificar el caller desplegado;
`compatibilidad` conserva el contrato anterior mientras la función no esté
instalada y mantiene writers/schedules cerrados durante el cambio; `deploy`
requiere revisión y promoción protegida, además de JIT DDL independiente por DB;
la función debe instalarse en Pro antes de promover el caller a `main`.
`contract` se acredita después de una corrida autorizada y lectura de resultado,
sin borrar la función. Recuperación: detener FG3 y mantener E10 cerrado; si ya
se promovió el caller, revertirlo mediante PR protegido con el writer pausado.
Dejar la función aditiva sin uso: no reactivar el PATCH directo por defecto ni
modificar cursos como rollback.

Los YAML prueban wiring declarado. El workflow FG2 invoca `master_orchestrator.py --skip-cleansing` y mantiene jobs separados de cleansing, enrichment y sync; no asumir que el padre ejecutó todas las etapas. Horarios reales y ejecuciones quedan remotos.

### Probe y decisión FG3 — candidato local WP-REM-07, 2026-11-19

El candidato mantiene el probe HTTP separado de la clasificación y de la RPC:
HEAD `2xx` termina saludable sin GET; HEAD `403`, `405` o `501` hace un GET
acotado; HEAD `404/410` exige GET antes de decidir cualquier transición. Un
resultado final que no confirma salud ni retiro queda inconcluso y no cambia
`last_404_at` ni `is_active`. La gracia existente de tres días y la mutación
atómica `fg3_apply_public_course_transition` permanecen vigentes.
Los estados `408/425/429` y `5xx` se reintentan acotadamente; `HEAD 501` usa
primero el GET de fallback y un `GET 501` entra al retry de servidor.

Cada curso comparte una cota total de tres intentos entre HEAD, GET, redirects y
retries, timeout HTTP de 10 segundos por intento, hasta 30 segundos acumulados
de espera y guard local de 60 segundos antes de cada request, después de DNS y
antes de clasificar la respuesta. `socket.getaddrinfo` no ofrece cancelación
portable al alcanzar ese guard: si tarda más de 60 segundos, el worker aborta al
recibir el resultado y no inicia conexión HTTP. Los `Retry-After` delta o
HTTP-date se aceptan solo dentro del presupuesto acumulado. Timeout, DNS, TLS y
errores de transporte usan reintentos acotados; `RuntimeError` conserva fase y
categoría sanitizadas (`time_budget` para el reloj, `retry_backoff` para la
espera). Cada redirect vuelve a validar el destino y resuelve/pinea
solo IPs públicas antes de abrir HTTPS; no se registran títulos, URLs ni texto
crudo de excepciones. Resultado incierto de una RPC detiene el lote y no se
repite.

La confirmación GET comienza en el `response.url` final validado por HEAD, por
lo que no vuelve a consumir intentos repitiendo redirects ya recorridos. El GET
vuelve a resolver y fijar por DNS público cada destino bajo el mismo presupuesto
`ProbeTrace`. El helper público `is_safe_public_url()` conserva resolución DNS
pública para el consumidor `SyncVectorWorker` antes de persistir un curso; el
probe usa `_is_syntactically_safe_public_url()` para validar formato y delega la
resolución acotada y el pinning a cada request HTTPS.

Los logs por ID registran método, estados HTTP, fase/categoría, acción y campos
FG3 resultantes. Sirven para reconciliar transiciones por ID sin depender del
título; no contienen cuerpos de respuesta ni errores completos. La suite
`tests/test_integrity_ping_retirement_contract.py` usa fixtures sintéticos y se
ejecuta en Docker `--network none`; incluye redirects HEAD→GET al destino final
y mocks DNS para Sync (rechazo de resolución privada o inexistente y aceptación
de una dirección pública). No demuestra acceso a las instituciones,
estado Pro ni aceptación funcional remota. Expansión: agregar el probe y los
logs conservando la RPC/contrato existente. Compatibilidad: mantener los
writers pausados mientras se publica y se observa. Deploy: requiere promoción
protegida y habilitación operativa separada. Contracción: solo tras corrida
aceptada y postflight autorizado. Rollback: pausar y revertir el caller por PR
protegido; no restaurar automáticamente los efectos de #129 ni escribir cursos.

## Gates y perfiles

La implementación actual usa los gates Fase 100 discovery_enabled, pipeline_enabled y production_enabled, configurados por institution_site_profiles. Los workers conservan fallback temporal a pipeline_ready cuando el gate moderno no existe o no se puede leer según su adapter. Fase 75 documenta la historia de pipeline_ready y no debe reactivarse como contrato nuevo. discovery_enabled no es lo mismo que procesar; production_enabled gobierna publicación.

## Concurrencia, idempotencia, requeue y errores

Harvester usa content_hash SHA-256 y estados para no reprocesar contenido idéntico. SQL lock_staging_records/lock_cleansed_records marca trabajo y evita que workers consuman dos veces una misma cohorte; RPC atómicas preservan estados de origen/destino. Orchestrator time guard y circuit breaker limitan un job largo; gate cerrado salta institución. Los workers registran processing_error/reason/error y no consideran output LLM como schema garantizado. La regla de retry/requeue está en RPCs y scripts; no requeue en esta transferencia.

En modo controlado, el harvester emite `[FG2_DIAGNOSTIC]` solo con `version`,
`phase` y `category` de vocabulario fijo, más tabla/HTTP status cuando provienen
de un error DB y pasan su allowlist. Las fases incluyen la carga de módulos,
la inicialización de runtime, la validación de modo,
decodificación, inicialización, gate de perfil, arranque de Playwright,
discovery, detalle, escritura,
telemetría o cierre. `master_orchestrator.py` valida el evento y conserva esos
campos; si el hijo no lo produjo, registra `phase=unknown` y
`failure_class=child_process_exit`. El texto de errores, stdout/stderr,
argumentos, secretos, cuerpos y URLs no se exponen. La categoría identifica
una clase operativa observable, no demuestra por sí sola la causa histórica de
un run cuyos logs no conservaron ese evento. Los eventos solo se emiten cuando
el proceso tiene el marcador de canary o de cohorte/controlado.

## Primera corrida FG2 acotada — candidato local 2026-11-09

El candidato local añade `bounded_first_run` al `workflow_dispatch`, con valor
predeterminado `false`, y exige referencia, SHA-256 y bytes Base64 del lote
revisado para entrar en ese modo. El cron diario `0 5 * * *` continúa usando el
camino ordinario, que no consume estos manifests y conserva los límites vigentes.
El camino ordinario puede leer colas globales; habilitarlo o despacharlo requiere
los gates propios y una revisión separada de ese alcance.

### Identidad de staging por alcance — corrección local 2026-11-19

El harvester de un `approved_lot` carga las identidades de `staging_raw` solo
para las URLs incluidas en el lote: revalida por ID las filas del snapshot y
comprueba por alias las identidades que el snapshot declara vacías. El alcance
vacío falla cerrado. Filas históricas fuera de esas URLs, aunque tengan aliases
normalizados duplicados, no bloquean el lote ni se modifican.

El `scheduled_cohort` no barre `staging_raw` antes del discovery. Una vez que el
selector del orquestador congela instituciones y seeds elegibles en el manifest,
el harvester consulta la identidad de staging por alias para cada URL descubierta
de esa cohorte, con límite de dos filas. Exige una única fila con URL normalizada,
institución propietaria y estado conocidos; una colisión dentro de la identidad
seleccionada, una respuesta malformada o un propietario distinto falla antes de
escribir y sin escoger una fila arbitraria. Si no existe fila, conserva el flujo
de discovery actual. El staging histórico ajeno a las URLs seleccionadas no
amplía el lote ni lo bloquea.

### Admisión de semillas alineada con runtime — corrección local 2026-11-19

El preflight de `approved_lot` y la validación de candidatos del harvester usan
`profile_url_policy_rejection()` en `fg2_bounded_run.py`. Para
`hardcoded_urls`, toma como máximo diez semillas que pasen la misma regla de
origen, pertenencia al lote, extensiones, exclusiones y `allowed_url_patterns`
que se aplica en runtime, después de la misma normalización de `normalize_url`
(query, fragmento y barra final), conservando el orden del perfil. Una selección
explícita revisada no se sustituye: si una de sus URLs queda bloqueada por el
perfil, el preflight termina antes del contacto. Si ninguna semilla configurada
es procesable, termina con error y no genera una cohorte vacía.

Las semillas de `sitemap_bfs` y `paginated_catalog` representan páginas de
discovery: deben conservar origen y pertenecer al lote aprobado, pero no son
URLs de detalle y no se filtran por exclusiones de cursos, extensiones de
detalle ni `allowed_url_patterns`. Los enlaces extraídos sí pasan por la regla
completa de detalle antes de incorporarse a la cohorte. En `scheduled_cohort`,
`hardcoded_urls` mantiene esta misma selección; `sitemap_bfs` conserva su
semilla programada `/sitemap.xml`. Los sitemaps `.xml.gz` continúan rechazados
en la ruta controlada. El parser del lote aprobado rechaza query y fragmento
tanto en las semillas como en sus URLs de detalle revisadas. En runtime, el
presupuesto controlado rechaza una query en la solicitud revisada y en sus
redirects; la canonicalización quita fragmentos antes de emitir HTTP. Una
fuente `paginated_catalog` cuya página solo exista como `?page=1` se rechaza en
preflight; usa una ruta de página sin query. La política compartida clasifica la
fuente sin aplicar reglas de detalle y conserva su query; el parser del lote
impide aprobar esa semilla con query. Los contratos locales están en
`tests/test_fg2_bounded_run.py`, `tests/test_fg2_bounded_orchestration.py` y
`tests/test_fg2_bounded_workflow.py`; sus fixtures no prueban la selección
actual de Pro ni una corrida institucional.

En este candidato local, un patrón regex de exclusión inválido/inseguro, una
allowlist inválida, la ausencia de `regex`, un timeout o un error de evaluación
rechazan la URL con una categoría sanitizada; no se ignora el patrón para
continuar. Este comportamiento es más estricto que la regla histórica de
ignorar algunos patrones inseguros y puede reducir la cohorte elegible. No se
retiran reglas de perfiles para conseguir candidatos. La validación de este
delta y su compatibilidad con perfiles de los tres modos siguen pendientes;
el texto no acredita ejecución Docker ni configuración remota.

Un HTTP 403 o 429 bloquea el origen después de una sola solicitud y no reintenta
esa respuesta, incluso cuando 429 incluye `Retry-After`. El hijo controlado lo
registra como `blocked`; detiene la discovery de la institución y no encola
enlaces parciales de un sitemap después del bloqueo. El orquestador puede
continuar solo con las otras instituciones que ya quedaron congeladas en el
manifest, nunca seleccionar una fuente de reemplazo. Un error de base, drift o
identidad ambigua sigue siendo fatal y no se convierte en `blocked`.

Transición: `expand` aplica la lectura acotada solo a `approved_lot` y
`scheduled_cohort`; `compatibilidad` mantiene sin cambios el camino ordinario y
los demás modos legacy; `deploy` requiere las promociones protegidas y su gate
operativo independiente; `contract` solo se evalúa después de una corrida
funcional autorizada y su postflight. Rollback: pausar los writers conforme a su
autorización y revertir el código por la ruta protegida; no borrar ni reclasificar
filas históricas. Las regresiones de este cambio usan mocks y datos sintéticos en
Docker sin red; no acreditan schedule funcional, estado de Pro ni otro piloto.

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

La búsqueda de sitemaps no puede consumir la reserva de detalle: con los
límites vigentes usa como máximo 8 URLs únicas y 14 inicios HTTP para la fase
sitemap, dejando hasta 2 URLs únicas y 6 inicios HTTP para consultar un detalle
y seguir un redirect del mismo origen con hasta 3 intentos por salto. Los
redirects y retries siguen contando en los totales globales 10/20. Si la cuota
de sitemap se agota antes, se detiene esa recursión sin abrir el circuit
breaker; se conservan los enlaces ya leídos, se procesa el detalle permitido y
el manifest registra `partial`, nunca `complete`. La cuota y el detalle siguen
dentro de la institución ya elegible y de la misma cohorte; 403/429,
transitorios agotados, `Retry-After` fuera del máximo y los límites globales
mantienen sus paradas existentes.

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

**Corte local anterior, supersedido por el candidato del 2026-11-20:** entonces
bounded aceptaba solo SSR y difería SPA/ecommerce porque el transporte de
Chromium no pasaba por el socket HTTP pinneado. Se conserva el estado histórico
para explicar el gap; no describe este candidato. Ver
[FG2 multiformato y onboarding](#fg2-multiformato-y-onboarding-de-perfiles--candidato-local-2026-11-20).

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

En ese corte, `sitemap_bfs` conservaba la ruta ordinaria: el preflight de
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
por institución únicamente las URLs aprobadas y construye filtros regex
PostgREST anclados a su identidad normalizada. El patrón contempla scheme/host
con mayúsculas, `/en/` antes de segmentos, el slash final y query/fragment que
`normalize_url` elimina, manteniendo sensible a mayúsculas el path. Las lecturas
por aliases de `staging_raw`, `courses`, `cleansed_programs` y
`enriched_programs` se particionan cuando el URL completo que `DatabaseClient`
enviaría supera el presupuesto local de 8.000 caracteres. La medición incluye
endpoint/base URL, tabla, columnas, filtro, orden y límite. Este valor es una
cota conservadora del candidato, no un límite garantizado por PostgREST. Si un
alias individual excede la cota, el preflight falla cerrado. Para bajar el
tamaño del filtro, los aliases se agrupan por origen y un trie factoriza
prefijos/sufijos de path y comparte ramas solo cuando sus subárboles tienen la
misma forma; la expresión permanece anclada y conserva la semántica de la
referencia por alias. La construcción del trie es iterativa para tolerar URLs
válidas cercanas al máximo de 2.048 caracteres y paths con muchos segmentos.
Cada fragmento usa
`limit=URLs_del_grupo+1`; sus filas se agregan por ID normalizado y cualquier
ambigüedad o conflicto se detecta sobre el conjunto completo, incluso si las
filas aparecen en fragmentos distintos. Las lecturas por
`staging_id`/`cleansed_id` permanecen como consultas por IDs con
`limit=IDs_de_referencia+1`. No se leen ni paginan tablas completas. Un owner o
estado/hash distinto detiene el lote antes del harvester. El harvester vuelve a
leer las filas
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

En fixtures sintéticos válidos, un barrido de 1–10 URLs sin filas downstream
observó como máximo 9 GET por alias en un lote de 7 URLs de 1.776 caracteres
(2 `staging_raw`, 3 `courses`, 2 `cleansed_programs`, 2 `enriched_programs`);
no tenía IDs aprobados y añadió 0 GET por ID. Otra fixture válida de 40.550
bytes, con 3 URLs de 2.048 caracteres y una fila por URL en cada tabla, midió
4 GET por alias más 2 GET por ID (`staging_id` y `cleansed_id`): 6 GET de
snapshot, 0 escrituras. Son resultados medidos localmente, no máximos de todos
los lotes ni observaciones de Pro. La cota local de 8.000 caracteres cubre el
URL completo de cada alias GET; no limita el volumen total ni expresa un límite
del servidor.

Si la cuota suave de sitemaps se agota durante la extracción controlada,
`_fetch_sitemap` devuelve los enlaces ya leídos y no inicia otra solicitud
sitemap. Con los límites por defecto, sitemap consume como máximo 8 URLs únicas
y 14 inicios HTTP; reserva las otras 2 URLs y hasta 6 inicios HTTP para una
página de detalle y un redirect, con sus reintentos incluidos en los totales
10/20. La institución queda `partial`, no se abre el circuit breaker ni se
declara agotado el presupuesto global. Los detalles completados continúan por
el flujo normal y solo sus IDs aprobados entran en el manifest de la corrida;
cleansing/enrichment/sync siguen restringidos a ese manifest.

En un lote manual con seeds mezcladas, cuando esa cuota se alcanza se omiten
las seeds sitemap que resten pero se siguen examinando las seeds de página ya
aprobadas que vengan después. No se agregan enlaces ni URLs fuera del scope del
lote. Los topes globales, 403/429, transitorios agotados y Retry-After excesivo
conservan sus paradas existentes. Seeds `.xml.gz` se rechazan en el preflight
controlado; si un sitemap ya leído anuncia uno, se difiere el origen antes de
solicitar el cuerpo comprimido. No se descomprime contenido sin un límite de
salida probado.
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
localmente sin abrir sockets. El browser no abre su propio HTTP, DNS ni socket
WebSocket hacia la institución: la ruta intercepta HTTP y entrega al navegador
la respuesta obtenida por el transporte fijado; WebSocket se bloquea antes de
conectar. Los perfiles SPA/ecommerce pueden recorrer este mismo camino tanto en
modo ordinario como acotado, sujeto al perfil, alcance y presupuesto efectivos.
La regresión Chromium sintética prueba el guard y la detención por WebSocket; no
acredita disponibilidad, permisos ni comportamiento de una institución real.

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
