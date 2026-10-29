# Componente: pipeline FG1/FG2/FG3

## Estaciones y contratos

| Estación | Fuente → destino | Trabajo y estado |
|---|---|---|
| FG1 discovery | config/institution_sources.json → institutions e institution_site_profiles | discovery_institutions.py comprueba instituciones y puede insertar las faltantes; --no-insert detiene el caso sin catálogo. Escritura de catálogo, autorización operacional separada. |
| FG2 orchestration | perfiles y flags → tareas por institución | master_orchestrator.py decide elegibilidad/recencia/circuit breaker, ejecuta workers por subproceso y aplica time guard. |
| FG2-1 harvester | web/sitemap/config → staging_raw | universal_harvester.py descubre URLs, filtra/noise/exclusiones, canonicaliza, extrae HTML/metadata, calcula SHA-256 content_hash y omite contenido sin cambio. |
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

## Proveedores, simulación y discrepancia documental

El código actual construye dos proveedores: DeepSeek v4 Flash por endpoint OpenCode-compatible, seguido de Cloudflare Workers AI Meta Llama 3.1 8B. Si proveedores fallan, el worker puede usar mock/smart-mock y marcar provider_used/is_mock_data. Variables por nombre: OPENCODE_API_KEY, CF_ACCOUNT_ID, CF_API_TOKEN. No se leyeron valores ni se invocaron servicios.

AGENTS.md y notas históricas describen CF → GitHub → Gemini. Ese orden no coincide con scripts/core/enrichment_worker.py en este candidato. Se registra la diferencia como conflicto documental y runtime remoto desconocido; no se infiere disponibilidad ni se altera funcionalidad.

## Writers, schedules y límites

Workflow YAML programa FG1 mensual, FG2 diario y FG3 diario UTC y deja workflow_dispatch; los schedules reales/ejecuciones no se consultaron. Los writer jobs requieren preflight allow_writer. Los writers habituales de courses son sync_vector_worker.py y maintenance integrity_ping.py; 11 harvesters dedicados están bajo scripts/deprecated/harvesters y permanecen históricos/legacy según AGENTS.md. scripts/maintenance incluye bypasses, migraciones, semillas, deletes y cross-env; revisar cada archivo/callgraph y obtener JIT antes de ejecutar.

## Pruebas, evidencia y cómo modificar

Tablas/RPC están descritas en [database.md](../database.md). `tests/test_fase121_extractors.py` cubre extractores/selectores declarativos; `tests/test_h2_pipeline_contract.py` comprueba contratos de campos y estados entre workers; `tests/test_h3req1_local_pipeline_walk.py` cubre el recorrido sintético y recuperación; `tests/test_h3req1_pipeline_discovery_boundaries.py` limita URL/esquema/host/gates; `tests/h3req1_pipeline_postgrest_pg17_integration.py` y `tests/sql/h3req1_pipeline_*_r1.*` recorren persistencia en fixture local. `tests/test_harvester.py` es una suite distinta de cuatro consultas Supabase live, con opt-in y credenciales, no un parser unitario; en R160 sus cuatro casos quedaron skipped y no se consultó servicio live. El mapa fuente→caso→resultado, límites de hash y alcance de búsqueda está en [relaciones locales del pipeline](../evidencia/h3req1_sem_pipeline_relaciones_locales_2026-10-13_r11.md). R178 conserva resultados funcionales locales históricos; no se repitió suite funcional porque las fuentes de producto no cambiaron durante esta documentación.

Al cambiar filtros/config de discovery, renovar `test_h3req1_pipeline_discovery_boundaries.py` y revisar tests de canario por path; extracción, `test_fase121_extractors.py`/pipeline walk (no `test_harvester.py`, que es live); locking/estados/promoción, harnesses de persistencia y atomicidad; proveedor, validación sintética de prompt/fallback sin credenciales reales; sync/publicación, consumidores ROI/editoriales y el contrato efectivo H2/H3. Schema nuevo: migration expand, compatibilidad mientras se promociona, contracción con rollback verificable y permiso SQL separado.

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
