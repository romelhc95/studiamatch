# Arquitectura Del Pipeline

Esta nota conserva el resumen operativo del pipeline. Las vistas Mermaid y las
fronteras completas viven en el [Mapa canonico de arquitectura](arquitectura/00_mapa.md),
especialmente [Pipeline y estados](arquitectura/03_pipeline_estados.md). Las
vistas son derivadas y no acreditan adopcion remota.

## Flujo Actual

El Golden Pipeline mueve datos por cuatro estaciones persistentes:

| Estacion | Worker | Entrada | Salida | Funcion |
|---|---|---|---|---|
| 1 | `universal_harvester.py` | Sitemap y crawl | `staging_raw` | Descubre URLs y captura contenido. |
| 2 | `cleansing_worker.py` | `staging_raw` | `cleansed_programs` | Limpia, consolida y descarta ruido. |
| 3 | `enrichment_worker.py` | `cleansed_programs` | `enriched_programs` | Extrae los pilares del programa. |
| 4 | `sync_vector_worker.py` | `enriched_programs` | `courses` | Valida, normaliza y publica el registro final. |

`master_orchestrator.py` coordina harvesting y puede delegar cleansing. El workflow FG2 encadena harvesting, cleansing, enrichment, sync y luego auditorias QA.

## Enrichment Y Vectores

El orden real de providers es DeepSeek mediante OpenCode, Cloudflare Workers AI y, si ambos fallan o se degradan, smart mock. El smart mock queda marcado como dato mock. La generacion de embeddings en sync sigue comentada como placeholder; no se debe afirmar busqueda vectorial operativa desde ese worker.

## Gates Reales

- `discovery_enabled`: permite o bloquea la entrada del harvester.
- `pipeline_enabled`: permite procesamiento ETL; los workers conservan fallback temporal a `pipeline_ready` cuando el campo nuevo no esta presente.
- `production_enabled`: permite publicar activo; sync conserva inactivo lo que no esta habilitado para produccion.
- `allowed_url_patterns`: allowlist positiva de URLs de programas.
- `exclusion_patterns`: exclusiones por institucion, incluyendo regex controladas.
- Validaciones de ruido adicionales operan en cleansing, enrichment y sync.

Si `pipeline_enabled=false`, el harvester puede operar en modo discovery-only:
persiste `discovered` y no entrega esas filas a cleansing. De forma independiente,
las estaciones posteriores materializan `skipped` con razon canonica
`pipeline_gate=false` solo para filas pendientes que llegan a inspeccionar.
Perfiles y colas se leen fail-closed. El orquestador aplica perfil,
`discovery_enabled`, exclusiones, circuit breaker y freshness antes del `limit`.
Los fallos detectados por el orquestador producen salida no cero sin descartar
trabajo persistido; algunos fallos internos del harvester y FG3 aun se absorben
o terminan en cero y requieren cobertura/remediacion en CA1.

## Workflows Vigentes

| Workflow | Trigger actual |
|---|---|
| FG1 inventory | `schedule` mensual y `workflow_dispatch` |
| FG2 Golden Pipeline | `schedule` diario y `workflow_dispatch` |
| FG3 integrity | `schedule` diario posterior a FG2 y `workflow_dispatch` |

FG2 y FG3 comparten grupo de concurrencia y no se cancelan entre si; FG3 queda en cola si FG2 sigue activo. Los tres workflows rechazan refs que no sean ramas permanentes antes de acceder a environments. La modalidad aprobada por [Hito 1](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) es cadencia automatica con gates, circuit breakers y controles de ambiente.

## Limites

- `staging_raw`, `cleansed_programs`, `enriched_programs` y `courses` son datos operativos por ambiente.
- La promocion DB-as-Code incluye catalogos, perfiles, reglas y schema; no replica datos operativos Free a Pro.
- H-00 es Free-only y requiere autorizacion separada.

## Invariante De Preservacion Completa Del Corte

El corte de [ADR-0005](decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md) preserva harvester completo y Golden Pipeline: `universal_harvester.py`, `master_orchestrator.py`, sitemap discovery, crawl/BFS, catalog-link discovery, extraccion HTTP, extraccion browser/Playwright cuando el perfil lo requiere, persistencia `discovered/pending` en `staging_raw`, deduplicacion, hashing, `allowed_url_patterns`, `exclusion_patterns`, `discovery_enabled`, `pipeline_enabled`, fallback temporal `pipeline_ready`, `production_enabled`, circuit breaker, cooldown, freshness, timeouts, persistencia parcial, `cleansing_worker.py`, `enrichment_worker.py`, `sync_vector_worker.py`, `integrity_ping.py`, FG1 mensual, FG2 diario, FG3 diario posterior a FG2, branch guards y environments.

No significa activar globalmente instituciones, saltar `pipeline_enabled`, saltar `production_enabled`, restaurar harvesters deprecated, afirmar que todas las instituciones fueron cosechadas ni ejecutar remote smoke en este corte.

## Separacion Respecto De Leads Y Email

Leads/email no son una estacion del Golden Pipeline. La arquitectura completa de captura, outbox, proveedor, secretos, observabilidad y reintentos queda `DEFERRED_NO_IMPLEMENTATION` en [BK-F9.5-05](backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md). El security hold DB-as-Code no toca `staging_raw`, `cleansed_programs`, `enriched_programs`, `courses`, RPCs del pipeline ni workflows FG.

Ver [Sistema DB Supabase](sistema_db_supabase.md),
[Flujo de release](operaciones/flujo_release_minimo.md) y
[Estrategia de pruebas](pruebas/00_estrategia_pruebas_sprint_1.md).
