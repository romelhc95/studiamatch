# Búsqueda local de consumidores de mantenimiento

> Corte: 2026-10-12. Búsqueda de solo lectura en el candidato (`feat/h3req1-sync-20261002`, HEAD base `4eb4d877a50b012bb630a129bd0c74482c33be9c`) y el original (`feat/h3req1-development-remote-tests`, HEAD `7650093b05a820e8e6faf9ec711e12fab8b50398`). No se modificó el original, no se importó ni ejecutó ninguna herramienta, writer, workflow o test y no se leyó `.env`, secretos ni documentos privados.

## Método y alcance de ausencia

Para los 42 paths `scripts/maintenance/*.py` del registro se buscaron path relativo, basename, stem de módulo e import Python en ambos árboles, dentro de `scripts/`, `tests/`, `.github/workflows/`, `.github/scripts/`, `.githooks/`, `web/`, `workers/`, `supabase/functions/` y `config/`. Se excluyeron el mismo archivo, `.context/`, dependencias/caches, archivos de entorno y nombres sensibles. La búsqueda es textual; no resuelve construcción dinámica de comandos, alias externos ni invocaciones manuales. “No encontrado” limita el resultado a ese alcance y no declara que el script sea imposible de invocar.

El escaneo AST complementario está en [`h3req1_maintenance_static_inventory_2026-10-12.md`](h3req1_maintenance_static_inventory_2026-10-12.md). Describe símbolos, flags, llamadas a DB/red y operaciones locales sin evaluar imports. La salida sin procesar de referencias se conservó temporalmente fuera del checkout y no es un resultado runtime.

## Relaciones encontradas

| Fuente | Consumidor o prueba local acreditada | Alcance de la relación |
|---|---|---|
| `scripts/maintenance/db_migrate.py` | `.github/workflows/db-sync-to-pro.yml:216,227,281,458`; `scripts/security/run_h2_r1_tests.sh:5`; `tests/test_h2_pro_migration_controls.py`, `tests/test_fase09_9_certification_canary.py`, `tests/test_fase09_10_pre_main_controls.py`, `tests/test_obsidian_context_state.py` | Workflow declara modos/paths de chequeo y aplicación; las suites inspeccionan controles/manifest. No prueba ejecución remota ni aplicación de migration. |
| `scripts/maintenance/check_db_parity.py` | `.github/workflows/db-sync-to-pro.yml:513`; `scripts/security/run_h2_r1_tests.sh:6`; `tests/test_h2_pro_migration_controls.py`, `tests/test_fase09_9_certification_canary.py` | El workflow declara el preflight de target; puede invocar `exec_sql`, por lo que el diagnóstico no se clasifica como operación inocua sin leer input/target y obtener JIT. |
| `scripts/maintenance/h2_pro_preflight_report.py` | `.github/workflows/db-sync-to-pro.yml:271`; `scripts/security/run_h2_r1_tests.sh:7`; `tests/test_h2_pro_migration_controls.py`, `tests/test_fase09_9_certification_canary.py` | Produce el preflight/cohort esperado para el workflow. Fuente de contrato y test estática; no lee Pro en esta transferencia. |
| `scripts/maintenance/h2_scan_unauthorized_writers.py` | `.github/workflows/security-audit.yml:334`; import directo en `tests/test_h2_writer_scan.py` | El workflow declara ejecución del scanner y pytest importa su `scan`; la definición no acredita una corrida de GitHub. |
| `scripts/maintenance/h2_backfill_editorial_state.py` | Import directo en `tests/test_h2_backfill_editorial_state.py`; la suite figura en `.github/workflows/security-audit.yml:343` | El test usa fake DB para dry-run/batching/idempotencia y límites; no se ejecutó durante esta documentación ni prueba un writer remoto. |
| `scripts/maintenance/diagnose_institution.py` | Importa funciones de `scripts/shared/site_diagnostics.py`; el consumer aguas arriba `scripts/core/universal_harvester.py:250,266` importa y llama `diagnose_site` de esa utilidad compartida | El script de mantenimiento es una CLI de diagnóstico; el harvester usa la utilidad compartida, no se demuestra que invoque la CLI. |
| `scripts/maintenance/noise_discovery_engine.py` → `scripts/maintenance/apply_noise_exclusions.py` | Handoff documentado por archivo JSON (`--json`); ambos son CLIs separadas | Es un contrato de artefacto escrito/leído, no import/call directo. El apply actual puede además escribir `institution_site_profiles` y, con `--cleanup`, borrar `staging_raw`; revisar modelo vigente antes de cualquier ejecución. |
| `scripts/maintenance/merge_exclusions_to_profiles.py` | `scripts/deprecated/seed_crawler_exclusions.py` nombra la herramienta como alternativa; `scripts/maintenance/fase74_seed_pro.py` contiene referencias en comentarios históricos | No se encontró una llamada ejecutable. Lee la tabla retirada `crawler_exclusions`; se clasifica legacy y no es un consumer vigente del schema actual. |
| `scripts/maintenance/seed_site_profiles.py` | `scripts/deprecated/add_exclusion.py` lo menciona como instrucción; `fase74_seed_pro.py` lo cita en comentario de contexto | No se encontró una llamada ejecutable. Referencia textual y guía no demuestran ejecución ni adopción. |
| Resto de `scripts/maintenance/*.py` | `tests/test_supabase_credentials_contract.py` enumera path/origen de credenciales para scripts específicos | Ese inventario valida identidades de credenciales y contratos HTTP; no importa ni ejercita la funcionalidad de cada herramienta. Para esos paths no se encontró llamada directa de producto, runner o workflow dentro del alcance descrito; queda posible invocación manual. |

## Consecuencias para mantenimiento

- El único ejecutor DB multi-stage hallado es el workflow declarado `db-sync-to-pro.yml`; su existencia versionada no prueba que corra ni que esté habilitado en GitHub.
- El resto de herramientas se expone como CLI manual o artefacto de handoff solo cuando el propio código lo declara. No se infiere un caller por compartir carpeta, nombre de fase o variable.
- Las suites de contrato identificadas prueban la relación estática o el comportamiento fake/local indicado; no deben presentarse como ejecución actual. Los resultados R178 se mantienen delimitados por su acta.
- Para cambiar una herramienta, revisar el script exacto, `db_client.py`/credenciales si aplica, sus callers listados, la prueba específica si existe, y la familia de salida. Cualquier write/delete/DDL/cross-environment requiere la autorización separada indicada por `AGENTS.md`.

## Historia y límites

El índice [`h3req1_historia_paths_local_2026-10-12.md`](h3req1_historia_paths_local_2026-10-12.md) registra `git log --all --follow` por path en ambos checkouts, incluyendo paths sin historia local. Ese resultado prueba únicamente que la búsqueda local fue completada; un commit no prueba test, runtime o despliegue. No se consultaron refs remotas. Los orígenes no recuperables localmente y cualquier instalación/adopción fuera de estos árboles quedan delimitados para la etapa posterior.
