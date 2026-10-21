# Pipeline sintético → PG17 → Admin/público — R2 — 2026-10-11

## Resultados ejecutados

1. R1 terminó exit 1 antes de ejecutar transforms: `/usr/bin/python3` no tenía
   `requests`. Se conserva en
   [`local-pipeline-walk-r1.stdout.txt`](local-pipeline-walk-r1.stdout.txt).
   No se instaló ni descargó nada.
2. R2 terminó exit 0 en `studiamatch-dev` con `/opt/venv/bin/python`, timeout
   120 s, `env -i`, adaptador PostgREST en memoria y respuesta HTTP sintética
   inyectada en la frontera de red. Log completo:
   [`local-pipeline-walk-r2.stdout.txt`](local-pipeline-walk-r2.stdout.txt);
   salida estructurada:
   [`local-pipeline-walk-r2-result.json`](local-pipeline-walk-r2-result.json).
3. La salida JSON de R2 y una proyección read-only del curso PG17 se validaron y
   compararon dentro de `studiamatch-dev`: PASS en 11 campos compartidos
   (`id`, institución, categoría, nombre, slug, URL, precio, modalidad,
   duración, proveedor, `is_mock_data`); identidad estable, procedencia pipeline
   y ruido descartado/no publicado. La consulta se hizo en transacción
   `READ ONLY` con `ROLLBACK`; proyección:
   [`local-pipeline-pg17-readonly-r1.json`](local-pipeline-pg17-readonly-r1.json).
4. El harness local
   [`h3_uat_functional_catalog_seed.sql`](../../../tests/sql/h3_uat_functional_catalog_seed.sql)
   acepta `h3_course_payload` del pipeline walk, lo carga al PG17 desechable y
   valida el contrato de ID, institución, categoría, proveedor y estado. El
   marker ejecutado se conserva en
   [`pipeline-course-seed-r12.txt`](pipeline-course-seed-r12.txt). La fila
   actual mantiene `field_sources.name=pipeline`, overrides vacíos y estado
   publicado.
5. H3-UAT-049 recorre esa misma identidad en Admin: preview, override/audit,
   retiro y alta de disponibilidad, evidencia inclusiva de 90 días,
   publicación, lector efectivo, listado, detalle y comparación. R30 añadió
   que “Solicitar Info” es un enlace interno al detalle local del mismo curso:
   3/3 viewports PASS, cero retries, PNG y vídeo en
   [`uat-functional-targeted-r30`](uat-functional-targeted-r30/).

## R3 — frontera negativa de discovery

- Antes de corregir, el runner sintético aceptó como URLs de discovery
  `ftp://`, `javascript://` y `file://` cuando el authority coincidía con el
  host configurado: 3 FAIL reproducidos; otros 6 casos negativos/presencia
  pasaron. El defecto estaba en `_is_valid_crawl_url`, que comparaba el host
  pero no restringía el esquema.
- Cambio local mínimo: `scripts/core/universal_harvester.py` rechaza esquemas
  distintos de HTTP/HTTPS antes del resto de validaciones. No cambia la
  allowlist de hosts, los gates institucionales ni los escritores.
- El runner
  [`test_h3req1_pipeline_discovery_boundaries.py`](../../../tests/test_h3req1_pipeline_discovery_boundaries.py)
  añade cobertura de HTTP/HTTPS permitidos, FTP/JavaScript/file rechazados,
  host externo, PDF y sitemap ausente, 503 o XML malformado. Revalidación R3,
  dentro de `studiamatch-dev`, ejecutó esos casos junto al pipeline walk:
  exit 0, 10 passed, 1 warning preexistente de deprecación PyPDF2, cero red y
  cero escrituras PG17. Log:
  [`local-pipeline-discovery-r3.stdout.txt`](local-pipeline-discovery-r3.stdout.txt).
- Dos colecciones previas se detuvieron con exit 2 antes de ejecutar pruebas
  porque `PYTHONPATH` no incluía el módulo histórico `integrity_ping`; se
  conservan en R1/R2. R3 fijó `/app`, `/app/scripts/core` y
  `/app/scripts/maintenance`; los hashes host/contenedor coincidieron.
- La reproducción de la forma XML `<loc/>` (R4) encontró `[None]` en vez de
  omitir la entrada: 1 FAIL, 9 PASS. La causa era aceptar `.text` nulo dentro
  del parser de sitemap. `_fetch_sitemap` ahora extrae y recorta solo valores
  no vacíos y omite nodos sin loc; un loc defectuoso no descarta los demás.
- R5 ejecutó la forma XML vacía y el sitemap completo con URLs HTTP(S), URL
  externa y PDF, junto al pipeline walk: PASS. R6 añadió contrato de gates
  `discovery_enabled`, `pipeline_enabled` explícito y fallback legacy
  `pipeline_ready` en UniversalHarvester, Cleansing, Enrichment y Sync; total
  R6: exit 0, 12 passed, 1 warning PyPDF2, cero retries. Log:
  [`local-pipeline-discovery-r6.stdout.txt`](local-pipeline-discovery-r6.stdout.txt).
- R7 añade un fallo sintético de transporte en `atomic_cleansing_promote`:
  la excepción se propaga, la fila staging sigue `pending`, no se crea la fila
  cleansed y el fallback no atómico no se invoca. Al restablecer el RPC
  sintético, el mismo input se procesa una vez y queda `processed` con una
  fila cleansed. R7, que incluye R6 y el walk pipeline, terminó exit 0:
  13 passed, 1 warning PyPDF2, cero retries. Log:
  [`local-pipeline-discovery-r7.stdout.txt`](local-pipeline-discovery-r7.stdout.txt).
- R8/R9/R11 son intentos fallidos del harness y se conservan sin atribuirlos
  al producto. R8 exit 1: `EnrichmentWorker` no acepta `db_client=`; se cambió
  la inyección al `get_db_client` ya usado por el walk. R9 exit 1: el registro
  sintético no declaraba estado inicial `pending`; el fixture lo declara y
  ahora verifica la transición atómica. R11 exit 1 antes del upsert: el guard
  SSRF rechazó correctamente `synthetic.h3.example`; se inyectó en el test el
  resolver público ya usado por el walk, conservando el control URL.
- R10 ejecutó discovery + walk y fallo/recovery/idempotencia del RPC de
  enrichment: exit 0, 14 passed, 1 warning PyPDF2. El fallo deja cero filas
  enriquecidas y conserva `cleansed.status=pending`; al recuperar, una fila se
  promueve y la repetición del RPC no duplica por `cleansed_id`.
- R12 añadió fallo/recovery/idempotencia del upsert de sync: exit 0, 15 passed,
  1 warning PyPDF2, cero retries. Ante el upsert fallido, la fila enriquecida
  sigue `pending` y no hay curso; recuperación deja `synced` y un solo curso.
  Una segunda sync conserva el mismo ID y no duplica la URL. El fixture usa un
  resolver sintético para el host reservado, sin DNS externo. Se ejecutó dentro
  de `studiamatch-dev` (`1000:1000`, `env -i`), junto
  a discovery y el walk; no recreó Docker ni modificó la fila UAT/PG17.
- Resultado vigente R12: [`local-pipeline-discovery-r12.stdout.txt`](local-pipeline-discovery-r12.stdout.txt).
- R13 añadió dos pruebas rojas: 403→200→429 abrió el circuito en vez de
  resetear el contador; la prueba del `main()` tenía un perfil incompleto y
  activó auto-diagnóstico. Salida: 15 passed, 2 failed. R14 corrigió el fixture
  de `main()` y el defecto probado del contador: toda respuesta HTTP distinta
  de 403/429 reinicia la secuencia, pero dos respuestas bloqueantes consecutivas
  abren/persisten el circuito según el perfil. También demuestra que el comando
  `main()` con `discovery_enabled=false` sale 0 sin discovery ni writes.
  Revalidación R14: exit 0, 18 passed, 1 warning PyPDF2, cero retries; HTTP/DNS
  se inyectan, sin egress. Logs R13 rojo y R14 verde preservados. Cambio de
  producto limitado a `scripts/core/universal_harvester.py`; el otro cambio es
  cobertura sintética.
- R15 prueba el orquestador cuando discovery está habilitado y todos los
  fetches fallan: `main()` devuelve `exit 1` antes del scraping y no escribe
  telemetría. Con gate cerrado ya se había probado salida `exit 0`, sin
  discovery ni writes. Revalidación del conjunto: exit 0, 19 passed, 1 warning
  PyPDF2, cero retries; requests/DNS se inyectan. Log:
  [`local-pipeline-discovery-r15.stdout.txt`](local-pipeline-discovery-r15.stdout.txt).
- R16 amplía los modos restantes sin red: `hardcoded_urls` deduplica semillas
  normalizadas y filtra esquema no web; `paginated_catalog` parsea enlaces de
  respuesta HTML sintética; `catalog_link_extraction` usa browser/page falso,
  cierra la página y filtra host/asset. Los tres persisten solo la URL interna
  permitida. La suite combinada terminó exit 0, 22 passed, 1 warning PyPDF2,
  cero retries. Log:
  [`local-pipeline-discovery-r16.stdout.txt`](local-pipeline-discovery-r16.stdout.txt).
- R17 prueba resume en modo `hardcoded_urls`: devuelve la fila preexistente
  `discovered` y la semilla nueva, no duplica URL, y no incorpora la fila
  `pending` protegida. R18 prueba `main()` con `pipeline_enabled=false`: después
  de discovery no ejecuta scraper ni telemetría y devuelve `exit 0`. El conjunto
  discovery + pipeline terminó exit 0, 24 passed, 1 warning PyPDF2, cero
  retries. Log:
  [`local-pipeline-discovery-r18.stdout.txt`](local-pipeline-discovery-r18.stdout.txt).
- Resultado vigente: [`local-pipeline-discovery-r14.stdout.txt`](local-pipeline-discovery-r14.stdout.txt);
  R13 rojo: [`local-pipeline-discovery-r13-red.stdout.txt`](local-pipeline-discovery-r13-red.stdout.txt).
- El curso directo fue verificado de nuevo desde el proceso Windows con
  HTTP 200 y contenido sintético; URL y recursos en
  [`acceso Windows localhost`](windows-local-access-r1.md).
- El curso sintético también responde directamente en
  [`http://127.0.0.1:3333/courses/ulima/analitica-aplicada-60000000/`](http://127.0.0.1:3333/courses/ulima/analitica-aplicada-60000000/)
  (HTTP 200, HTML contiene el nombre/slug); es la misma app y fila PG17 de R30.

## Aislamiento y límites

- Harvest, cleansing, enrichment y sync ejecutan transforms reales con
  adaptador determinista; LLM/embeddings simulados, sin crawling exterior.
  La carga al PG17 es un fixture sintético local; no se ejecuta ningún writer
  cloud.
- El contenedor UAT y PG17 no se recrearon. R30 restauró la fila por su
  `finally`; la lectura actual confirma `manual_overrides={}`.
- `/app/.env`, `/app/.env.local` y `/app/.env.gitdesa` no existen. R2 usa
  `env -i`; no carga secretos ni imprime credenciales.
- Los casos de sitemap ausente/503/XML malformado y filtro de host/esquema/PDF
  están ahora cubiertos por R3; faltan comprobar el efecto de estos filtros
  dentro del recorrido completo de discovery/gates, fallos controlados de
  cleansing/enrichment/sync y recuperación/idempotencia. G09 permanece
  parcial.

## SHA-256 de inputs y outputs

| Ruta | SHA-256 |
|---|---|
| `tests/test_h3req1_local_pipeline_walk.py` (R2) | `a49f8894befa7b4fcc659432d76a51bfd3e4847a1b4657a3b569618143e12738` |
| `tests/test_h3req1_local_pipeline_walk.py` (R6) | `55e1adaa8ad21249b13803bbcf20e4950c0ea41ceadc2e2e78df92d5b57ca6b4` |
| `tests/test_h3req1_local_pipeline_walk.py` (R7) | `92295b4cf3812b61801aba82d28cd816adae8d7857595a6d5742adc6f9e70a48` |
| `tests/test_h3req1_local_pipeline_walk.py` (R12) | `f82f9e45446746c25b75de4c91e1ee7fbccf0e554e4490613166d8371c2c6f3f` |
| `tests/test_h3req1_local_pipeline_walk.py` (R16) | `b3f99026ba710b8a65e7c614445171357470d350e60444a99998a1a079044576` |
| `tests/test_h3req1_local_pipeline_walk.py` (R18) | `717e68bfd9ceb599a4ebc584ad60bff2268e48506046158b3f2dce3900b50379` |
| `tests/test_h3req1_pipeline_discovery_boundaries.py` (R6) | `efa553eb5fb635be8f691cc25167e78a9941642c92845ce730f29861e2cc391c` |
| `tests/test_h3req1_pipeline_discovery_boundaries.py` (R14) | `439c9dde63e137171e7bec9d64807705f32daafd0969eb877b73b9901e328b8e` |
| `tests/test_h3req1_pipeline_discovery_boundaries.py` (R15) | `b77a42ef056b1fc7141dc36eabf0b1b1c4ec49381938f726d02a78e0249ab3e3` |
| `tests/test_h3req1_pipeline_discovery_boundaries.py` (R18) | `51a30d1aa3860d8d2ed9691dc107ea9bede6cce46e9e69d85491d7a89782dd58` |
| `scripts/core/universal_harvester.py` (R2) | `26759b87f1f98971edbe13621272db17a66811faf6ca431888479ac60cac0c84` |
| `scripts/core/universal_harvester.py` (R6) | `ba28f748146e72b7c87e853a8a211fd435b76513ad50cff0a2313af99b0f3089` |
| `scripts/core/universal_harvester.py` (R14) | `8080093cdc8e04c824e173c0e917622dd43ec10d61f5c0204ac0dbedb8835f67` |
| `scripts/core/cleansing_worker.py` | `b81a7379a085f07e508bceae043528052c3d9c7e64ff1edea52177fae69dd3cf` |
| `scripts/core/enrichment_worker.py` | `b76747d33095c26ad0250bf41ca13f005d6f446d76af6f8d4413f6c070a74fc7` |
| `scripts/core/sync_vector_worker.py` | `8b5c7b75535a1320610848a7c718ddb59b0d04c4cc5256b97349b1e8a22d0149` |
| `scripts/core/integrity_ping.py` | `03a831bce519cbc7267faff093530e395b0264bd22efe862e9a4ebeb001b6a90` |
| `scripts/shared/utils.py` | `839f60158e6130c0151436463283b2b609cf824a2bc0771e68bbfc09e41a92cb` |
| R2 structured result | `ee6691491b0fde2f1cb09198cef8176fba319798446450a264523448b785bd78` |
| PG17 read-only projection | `0e530df5e97cd63adb3eb1e090159624490a98f93305d9919b221aa7deac0b77` |
| R6 focused runner output | `0c8558d4c07e578d4c130aa945bfc17bd33771637995f558b352a0557d7dc604` |
| R7 focused runner output | `fa02c719bbceb899cd072de864db8a11a8d307f871679907104beecfce4c0d05` |
| R8 focused runner output (fixture constructor FAIL) | `5a9837292430f54015290a9ba7e1576fcb679be88d913ec1a9356cff2fdb9424` |
| R9 focused runner output (initial status assertion FAIL) | `abdfbdd6de888ca9fc4376ab4868446968b084f7d0f64618df3b7ccbcf357750` |
| R10 focused runner output | `ae796a56b2a7aed25cb6ac347e20d9537702f25da492dbed4b166273bb665569` |
| R11 focused runner output (SSRF guard before injection) | `7b37eadbc1d4018663b8e724f15f3dec15754b2a9d00226f4d64fffde9dcc5ac` |
| R12 focused runner output | `24911f6d15db6a8a8e9f8224a4e07a89a12271a6aa36a2620e9e4189c73bd10e` |
| R13 red focused runner output | `e48c62550fd122a1bc23aaac134fd7bafeb49fc21375c70ae38242bacf1747c7` |
| R14 focused runner output | `e74c2e577291e26aba0bc6b8a77a85c652d5e4f09b20283a72760f0ef2fcd4ff` |
| R15 focused runner output | `133b55f61d8333d63faf50d303f783b63bd90a0a186b13f01753562149013d3a` |
| R16 focused runner output | `db29d3cc912a5f9a430d796d13386a771ea4a0a64105899fe75760b64831bfe2` |
| R17 focused runner output | `5ef25f3136ea031a0024ab5eec54b2e65854f4f5162405f14a00fe34e374cadd` |
| R18 focused runner output | `78faa2895c8d1dfa708b82ad5b12b19bd1ab9a41297f0ff50614dfe26ca5ad0a` |
