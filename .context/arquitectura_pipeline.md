# Arquitectura Del Pipeline

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

Si `pipeline_enabled=false`, el harvester puede operar en modo discovery-only y las estaciones posteriores omiten la institucion. El Hito 1 debe revisar que el orquestador aplique gates antes del `limit`, no solo priorizacion.

## Workflows Vigentes

| Workflow | Trigger actual |
|---|---|
| FG1 inventory | `schedule` mensual y `workflow_dispatch` |
| FG2 Golden Pipeline | `schedule` diario y `workflow_dispatch` |
| FG3 integrity | `schedule` diario y `workflow_dispatch` |

Los comentarios que dicen "desactivado" no desactivan un bloque `schedule`. La modalidad aprobada por [Hito 1](backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) es cadencia automatica con gates, circuit breakers y controles de ambiente; cualquier ajuste debe preservar esos controles.

## Limites

- `staging_raw`, `cleansed_programs`, `enriched_programs` y `courses` son datos operativos por ambiente.
- La promocion DB-as-Code incluye catalogos, perfiles, reglas y schema; no replica datos operativos Free a Pro.
- H-00 es Free-only y requiere autorizacion separada.

Ver [Sistema DB Supabase](sistema_db_supabase.md) y [Flujo de release](operaciones/flujo_release_minimo.md).
