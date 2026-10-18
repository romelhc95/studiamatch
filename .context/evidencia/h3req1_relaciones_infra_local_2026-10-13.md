# Relaciones locales de infraestructura y guías — 2026-10-13 UTC

> Evidencia de búsqueda de consumidores para el corte local. No afirma adopción de GitHub, Cloudflare, agentes editoriales ni resultados de ejecución remota.

## Alcance de búsqueda

Se compararon los paths de las 19 guías `.github/agents/*.md`, los 5 comandos `.github/commands/*.toml`, `README.md` y `.github/pull_request_template.md` mediante búsqueda literal (`rg -l --fixed-strings --hidden`). En candidato y original se inspeccionaron estos roots cuando existían: `.github/workflows`, `.github/scripts`, `scripts`, `tests`, `web`, `workers`, `supabase`, `db` y `config`. Se excluyeron `.git`, `node_modules`, `.next` y `.context/evidencia`. La búsqueda no interpretó prompts ni ejecutó runners.

Resultado del candidato: no hubo path-literal caller para ninguna guía `.github/agents/*.md` ni comando `.github/commands/*.toml`. `README.md` aparece en el checker documental, en `tests/test_protected_path_scope_guard.sh`, `tests/test_protected_workflow_review.py` y `.github/workflows/security-audit.yml`. `.github/pull_request_template.md` aparece en `security-audit.yml`, `tests/test_requirement_client_source_validation.py` y `tests/test_obsidian_context_state.py`.

Resultado del checkout original: no hubo path-literal caller de las guías de agente ni de comandos TOML; la plantilla PR aparece en los dos tests de requisito/estado. No se encontró un consumidor fuera de esos roots locales mediante esta búsqueda. Esto acredita ausencia de referencias literales en el alcance enumerado, no ausencia de lectura manual, plugin externo o integración remota.

## Contratos de workflows

Los cuatro YAML se leyeron estáticamente para identificar eventos, comandos directos y consumidores; no se despachó un workflow.

| Path | Consumidor directo | Datos/efectos definidos en código | Suite que lee el contrato |
|---|---|---|---|
| `.github/workflows/fg1_inventory.yml` | Preflight FG1 y `scripts/core/discovery_institutions.py`; `requirements-fg1.txt` | El script toma `config/institution_sources.json`, consulta `institutions` e inserta faltantes salvo `--no-insert`. El YAML declara un horario mensual y despacho manual. | `tests/test_fase09_10_pre_main_controls.py::test_scheduled_workflows_use_environment_bound_preflight_outputs`; `::test_fg1_and_fg3_check_writer_pause_before_mutation`; `tests/test_fase10_main_boundary.py`; `tests/test_supabase_credentials_contract.py`. |
| `.github/workflows/fg3_integrity.yml` | Preflight FG3 y `scripts/core/integrity_ping.py`; `requirements-fg3.txt` | El worker lee `courses`, prueba URLs y parchea campos de vigencia/gracia 404. El YAML declara horario diario y despacho manual. | Mismos tests FG1/FG3 y límites; test de credenciales Supabase. |
| `.github/workflows/production_pipeline.yml` | Preflights por estación; `master_orchestrator.py`, `cleansing_worker.py`, `enrichment_worker.py`, `sync_vector_worker.py`; `requirements-pipeline.txt` | Cadena local declarada de `staging_raw` → `cleansed_programs` → `enriched_programs` → `courses`; cada estación tiene gate enforced. Horario diario y despacho manual están en YAML. | `tests/test_fase09_10_pre_main_controls.py::test_scheduled_workflows_use_environment_bound_preflight_outputs`; `::test_fg2_checks_writer_pause_before_every_mutating_station`; `tests/test_fase10_main_boundary.py`; `tests/test_supabase_credentials_contract.py`. |
| `.github/workflows/opencode.yml` | Evento de comentario → acción `anomalyco/opencode/github@latest`, en el mismo YAML | Recibe evento de comentario de issue/PR; no accede a tablas del producto por una ruta local observada. | No se halló test local de ejecución/evento; solo se valida sintaxis YAML. |

Que un test lea una fuente demuestra una relación de contrato. No se marca el test como ejecutado ni el horario como activo por esta tabla.

## Configuración y dependencias

La búsqueda de consumidores ejecutables vinculó los requirements así: `Dockerfile` consume `requirements.txt` y `requirements-pipeline.txt`; `fg1_inventory.yml` consume `requirements-fg1.txt`; `fg3_integrity.yml` consume `requirements-fg3.txt`; `production_pipeline.yml` y `production_canary.yml` consumen `requirements-pipeline.txt`; `db-sync-to-pro.yml` consume `requirements-db-migrate.txt`. La relación de `web/package.json`/lock con npm, Next, ESLint y TypeScript está documentada desde `AGENTS.md` y los tests UAT que cargan el SDK mediante `createRequire`. Esta evidencia no instala paquetes ni prueba build actual.

`.editorconfig`, `.gitattributes`, `.gitignore`, `web/.gitignore` y `.actrc` se clasifican como configuración de herramientas locales; no se les atribuye caller de producto. El contenido de `.actrc` no fue leído. `.env.example` no fue usado como entorno operativo y no se inspeccionaron valores `.env`.

## Límites

- La evidencia describe relaciones encontradas en dos árboles locales al 2026-10-13 UTC; original permaneció en solo lectura.
- No se consultó GitHub, Cloudflare ni Supabase. Instalación/ejecución de la acción OpenCode, schedules, environments, secrets, required checks y deploys siguen separados como verificaciones remotas.
- No se ejecutaron FG1, FG2, FG3, OpenCode, `act`, Docker compose ni pruebas funcionales por el solo hecho de documentar estas relaciones.

[Infra/release](../componentes/infra_release.md) · [Índice](../indice.md) · [Estado operativo](../estado_del_proyecto.md)
