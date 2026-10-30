# Herramientas de mantenimiento

> Corte local 2026-10-13. Fuentes revisadas estáticamente; ningún script, import, writer, SQL, test o workflow se ejecutó. No se consultó Supabase ni se leyeron `.env`, secretos o documentos privados. Cada path tiene sección propia y asignación exacta en el registro.

## Clasificación de operaciones

| Clase observada | Riesgo y regla de operación |
|---|---|
| Lectura local | No importar herramientas como método de inspección; algunas ejecutan lógica en top-level. Reportes son salidas generadas, no evidencia de un run. |
| Red/lectura DB | Puede contactar sitios o Supabase con identidades del entorno. Esta ficha no autoriza solicitudes remotas ni registra valores. |
| Writer/delete | `insert/upsert/patch/rpc/delete` requiere autorización JIT al target exacto, alcance de filtros y recuperación revisados. |
| Cross-environment | No es promoción normal. Requiere credenciales explícitas y distintas por Free/Pro, mapeo por slug y autorización de remediación. |
| DDL | `db_migrate.py` y `migrate_rpcs_to_pro.py` necesitan JIT DDL, baseline Pro, manifest cerrado y rollback. |
| Artefacto local | `generate_sitemap.py` escribe `web/public/sitemap.xml`; revisar inputs y diff. |

Los contratos de credenciales por nombre están en [Operación](../operacion.md#ambientes-y-datos) y [Seguridad](../seguridad.md#modelo-de-confianza-y-permisos).

## Fichas exactas por fuente

Las búsquedas de consumidores y su alcance constan en [evidencia local](../evidencia/h3req1_maintenance_consumer_search_2026-10-12.md); los símbolos/flags/efectos AST, en [inventario estático](../evidencia/h3req1_maintenance_static_inventory_2026-10-12.md). La [historia por path](../evidencia/h3req1_historia_paths_local_2026-10-12.md) registra resultados de `git log --all --follow` en ambos checkouts, sin inferir runtime/adopción.

## herramienta-analyze-url-interest-artifact

**Path y propósito:** `scripts/maintenance/analyze_url_interest_artifact.py` — Offline helper to inspect temporary URL interest artifacts. This script only prints candidate patterns. Persist reviewed configuration through version.

**Símbolos/entrada:** Offline helper to inspect temporary URL interest artifacts. This script only prints candidate patterns. Persist reviewed configuration through version; load_urls, path_family, is_noise_family, regex_for_family, main. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: local read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## Reportes generados y conservados

Estos cuatro scripts escriben destinos fijos dentro de `docs/`; la clasificación describe capacidad por lectura estática. Ningún writer se ejecutó durante la transferencia. Las rutas de salida pueden sobrescribir el reporte anterior. Su presencia no prueba fecha, input, ambiente ni resultado vigente; no hay un manifiesto de ejecución asociado en este corte.

| Productor/símbolo | Inputs/lectura observados | Destino fijo | Efecto, retención y evidencia |
|---|---|---|---|
| `scripts/maintenance/dedup_integrity_audit.py:run_audit` | `courses` activos y `institutions(slug)` por REST; solicita páginas públicas de detalle para una muestra. | `docs/qa-engineer/reporte_duplicidad_integridad.md` | GET externo/DB y escritura local del reporte; la salida no es un writer DB. El archivo existente se preserva como reporte histórico y no se atribuye a esta sesión. |
| `scripts/maintenance/taxonomy_roi_audit.py:run_taxonomy_roi_audit` | `market_salaries` y campos de `courses`; importa `shared.roi_engine.adjust_salary_for_course_type`. | `docs/qa-engineer/reporte_coherencia_taxonomica_v1.md` | Lectura DB y escritura local; relación ROI→auditoría comprobada por import. El archivo existente queda como salida histórica, no como suite ni PASS actual. |
| `scripts/maintenance/metadata_quality_report.py:analyze_metadata` | GET a `courses` para revisar descripción, audiencia y syllabus, usando nombres de configuración por ambiente. | `docs/metadata_quality_report.md` | Lectura remota/DB y escritura local con ruta fija. No ejecutar durante documentación: puede contactar el endpoint configurado y sobrescribir la salida. |
| `scripts/maintenance/quality_assurance_audit.py:run_audit` | `select_all('courses', filters='is_active=eq.true')`, con `institutions(slug)` embebido. | `docs/qa_coherence_report.md` | Lectura DB y escritura local; el destino es definido por código, pero no se acredita presente en este corte. |

Los dos reportes de `docs/qa-engineer/` que son destinos actuales de writers se preservan byte por byte, pero se clasifican en el registro como artefactos generados, no como fuentes mantenidas del componente legacy. El reporte `docs/metadata_quality_report.md` ya se clasifica por separado; `docs/qa_coherence_report.md` queda registrado como destino futuro. La ejecución de estos scripts requiere revisar ambiente, inputs y posible sobrescritura; no se leen ni se copian valores de credenciales. Un reporte histórico puede conservar hallazgos de su fecha, pero solo una salida fechada con inputs/evidencia asociados acredita un resultado.

## Navegación relacionada

[Índice integral](../indice.md) · [Operación](../operacion.md#pipeline-y-mantenimiento) · [Pipeline](pipeline.md) · [Base de datos](../database.md) · [Seguridad](../seguridad.md#modelo-de-confianza-y-permisos) · [Pruebas](../pruebas.md) · [Legacy/deprecated](legacy.md#exclusion-migration) · [Evidencia de relaciones](../evidencia/h3req1_maintenance_consumer_search_2026-10-12.md) · [Inventario AST](../evidencia/h3req1_maintenance_static_inventory_2026-10-12.md)

## Fuentes y relaciones

La asignación canónica por path, grupo, ancla y seis dimensiones está en el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#mantenimiento). Cada `## herramienta-…` es el ancla exacta del path listado en el registro. `merge_exclusions_to_profiles.py` queda en [legacy de exclusiones](legacy.md#exclusion-migration): su dependencia `crawler_exclusions` fue retirada y no se presenta como herramienta vigente.

## herramienta-apply-noise-exclusions

**Path y propósito:** `scripts/maintenance/apply_noise_exclusions.py` — Maintenance CLI `apply_noise_exclusions.py`; AST entry symbols: load_from_json, load_manual_patterns, apply_exclusions, cleanup_retroactive, main.

**Símbolos/entrada:** (sin docstring de módulo); load_from_json, load_manual_patterns, apply_exclusions, cleanup_retroactive, main. **Flags detectados por AST:** `--cleanup, --confidence, --dry-run, --institution, --json, --pattern`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: count(staging_raw); delete(staging_raw); select(institution_site_profiles); select(institutions); upsert(institution_site_profiles); red/archivo: DB read; DB write/capable RPC; DB delete; local read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Write/delete capability; JIT for the exact target/data, reviewed filters and recovery plan are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-audit-url-slugs

**Path y propósito:** `scripts/maintenance/audit_url_slugs.py` — Maintenance CLI `audit_url_slugs.py`; AST entry symbols: clean_slug_python, audit_slugs.

**Símbolos/entrada:** (sin docstring de módulo); clean_slug_python, audit_slugs. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Network read capability; do not run without explicit endpoint/environment review; no credential values belong in logs/docs.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-batch-enrich-courses

**Path y propósito:** `scripts/maintenance/batch_enrich_courses.py` — Maintenance CLI `batch_enrich_courses.py`; AST entry symbols: list_to_str, apply_validations, enrich_course, main.

**Símbolos/entrada:** (sin docstring de módulo); list_to_str, apply_validations, enrich_course, main. **Flags detectados por AST:** `--institution-id, --limit, --null-name-only`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: patch(courses); select(courses); red/archivo: DB read; DB write/capable RPC; network requests.get. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-category-audit-report

**Path y propósito:** `scripts/maintenance/category_audit_report.py` — Maintenance CLI `category_audit_report.py`; AST entry symbols: get_general_courses, get_stopwords, generate_report.

**Símbolos/entrada:** (sin docstring de módulo); get_general_courses, get_stopwords, generate_report. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Network read capability; do not run without explicit endpoint/environment review; no credential values belong in logs/docs.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-category-coverage-audit

**Path y propósito:** `scripts/maintenance/category_coverage_audit.py` — Maintenance CLI `category_coverage_audit.py`; AST entry symbols: tokenize, audit.

**Símbolos/entrada:** (sin docstring de módulo); tokenize, audit. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: select_all(category_rules); select_all(courses); red/archivo: DB read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-check-db-parity

**Path y propósito:** `scripts/maintenance/check_db_parity.py` — check_db_parity.py - Configuration-oriented parity check Free vs target. Exit codes: 0 = OK 1 = non-blocking warnings 2 = blocking parity error Fase 1.

**Símbolos/entrada:** check_db_parity.py - Configuration-oriented parity check Free vs target. Exit codes: 0 = OK 1 = non-blocking warnings 2 = blocking parity error Fase 1; migration_is_applied, load_environment, assert_environment, try_rpc, service_select, public_get, service_get, rest_select_all, ordered_ids_digest, service_post_rpc. **Flags detectados por AST:** `--env, --h2-manifest, --strict, --target-only`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: rpc(exec_sql); red/archivo: DB write/capable RPC; network requests.get,requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-check-pro-data

**Path y propósito:** `scripts/maintenance/check_pro_data.py` — Check data in Pro database from yesterday's harvest using urllib.

**Símbolos/entrada:** Check data in Pro database from yesterday's harvest using urllib.; req. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: no direct effect parsed; review helper/import wrappers. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-db-migrate

**Path y propósito:** `scripts/maintenance/db_migrate.py` — db_migrate.py — Aplicador universal de migrations SQL para StudIAMatch. Uso: python3 scripts/maintenance/db_migrate.py --env free [--dry-run] python3.

**Símbolos/entrada:** db_migrate.py — Aplicador universal de migrations SQL para StudIAMatch. Uso: python3 scripts/maintenance/db_migrate.py --env free [--dry-run] python3 ; load_environment, assert_environment, get_applied_migrations, extract_name, resolve_requested_migrations, _exec_sql_with_retry, _ensure_migration_table, _try_register_migration, _sql_literal, render_migration_sql. **Flags detectados por AST:** `--dry-run, --env, --manifest, --only`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: insert(dynamic); rpc(exec_sql); red/archivo: DB write/capable RPC; local read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DDL/RPC SQL capability; separate JIT DDL, closed manifest, Pro baseline and rollback are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-dedup-integrity-audit

**Path y propósito:** `scripts/maintenance/dedup_integrity_audit.py` — Maintenance CLI `dedup_integrity_audit.py`; AST entry symbols: clean_slug, run_audit.

**Símbolos/entrada:** (sin docstring de módulo); clean_slug, run_audit. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get; local write. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Network read capability; do not run without explicit endpoint/environment review; no credential values belong in logs/docs.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-diag-pro

**Path y propósito:** `scripts/maintenance/diag_pro.py` — Maintenance CLI `diag_pro.py`; AST entry symbols: (sin def/class detectado).

**Símbolos/entrada:** (sin docstring de módulo); (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Network read capability; do not run without explicit endpoint/environment review; no credential values belong in logs/docs.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-diag-schema-diff

**Path y propósito:** `scripts/maintenance/diag_schema_diff.py` — Diagnose schema differences between Free and Pro for all tables.

**Símbolos/entrada:** Diagnose schema differences between Free and Pro for all tables; (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get,requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Network read capability; do not run without explicit endpoint/environment review; no credential values belong in logs/docs.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-diagnose-institution

**Path y propósito:** `scripts/maintenance/diagnose_institution.py` — Fase 119: Diagnostico pre-onboarding para instituciones nuevas. Dada 1 URL de muestra, visita la pagina en modo read-only y genera un borrador de inst.

**Símbolos/entrada:** Fase 119: Diagnostico pre-onboarding para instituciones nuevas. Dada 1 URL de muestra, visita la pagina en modo read-only y genera un borrador de inst; diagnose. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: no direct effect parsed; review helper/import wrappers. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-diagnose-pro-db

**Path y propósito:** `scripts/maintenance/diagnose_pro_db.py` — Diagnóstico rápido de Supabase Pro para validar estado pre-ejecución.

**Símbolos/entrada:** Diagnóstico rápido de Supabase Pro para validar estado pre-ejecución.; (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: no direct effect parsed; review helper/import wrappers. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-fase62-update-profiles

**Path y propósito:** `scripts/maintenance/fase62_update_profiles.py` — Maintenance CLI `fase62_update_profiles.py`; AST entry symbols: get_inst_id, update_profile.

**Símbolos/entrada:** (sin docstring de módulo); get_inst_id, update_profile. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: patch(institution_site_profiles); select(institution_site_profiles); select(institutions); red/archivo: DB read; DB write/capable RPC. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-fase62b-create-pucp-and-sync-pro

**Path y propósito:** `scripts/maintenance/fase62b_create_pucp_and_sync_pro.py` — Maintenance CLI `fase62b_create_pucp_and_sync_pro.py`; AST entry symbols: sync_profiles_to_pro.

**Símbolos/entrada:** (sin docstring de módulo); sync_profiles_to_pro. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: insert(institution_site_profiles); insert(institutions); patch(institution_site_profiles); red/archivo: DB write/capable RPC; network requests.get,requests.patch,requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Cross-environment write; explicit, distinct per-environment credential pairs and separate remediation authorization are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-fase74-seed-pro

**Path y propósito:** `scripts/maintenance/fase74_seed_pro.py` — Fase 74: Seed institution_site_profiles in Pro (merge CE + full seed).

**Símbolos/entrada:** Fase 74: Seed institution_site_profiles in Pro (merge CE + full seed); (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: upsert(institution_site_profiles); red/archivo: DB write/capable RPC. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-fix-taxonomy-roi

**Path y propósito:** `scripts/maintenance/fix_taxonomy_roi.py` — Maintenance CLI `fix_taxonomy_roi.py`; AST entry symbols: duration_text_to_hours, fix_taxonomy_roi.

**Símbolos/entrada:** (sin docstring de módulo); duration_text_to_hours, fix_taxonomy_roi. **Flags detectados por AST:** `--apply`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: patch(courses); select_all(courses); red/archivo: DB read; DB write/capable RPC. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-force-harvest-up

**Path y propósito:** `scripts/maintenance/force_harvest_up.py` — Maintenance CLI `force_harvest_up.py`; AST entry symbols: force_harvest_institutions.

**Símbolos/entrada:** (sin docstring de módulo); force_harvest_institutions. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: select(staging_raw); upsert(staging_raw); red/archivo: DB read; DB write/capable RPC. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-generate-sitemap

**Path y propósito:** `scripts/maintenance/generate_sitemap.py` — Maintenance CLI `generate_sitemap.py`; AST entry symbols: generate_sitemap.

**Símbolos/entrada:** (sin docstring de módulo); generate_sitemap. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: select_all(courses); red/archivo: DB read; local write. Produce/reemplaza `web/public/sitemap.xml`; clasifícalo como artefacto regenerable, no evidencia vigente. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Reads DB and overwrites a local generated artifact; review its diff before adding it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-h2-backfill-editorial-state

**Path y propósito:** `scripts/maintenance/h2_backfill_editorial_state.py` — Maintenance CLI `h2_backfill_editorial_state.py`; AST entry symbols: parse_args, run_backfill, build_quality_payload, _load_states, _quality_equal, _assert_expected_project, _processed_count, _dict, _string_or_none, main.

**Símbolos/entrada:** (sin docstring de módulo); parse_args, run_backfill, build_quality_payload, _load_states, _quality_equal, _assert_expected_project, _processed_count, _dict, _string_or_none, main. **Flags detectados por AST:** `--after-id, --apply, --batch-size, --dry-run, --limit, --project-ref`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: no direct effect parsed; review helper/import wrappers. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-h2-pro-preflight-report

**Path y propósito:** `scripts/maintenance/h2_pro_preflight_report.py` — reporte de solo lectura para diagnosticar el contrato H2 Pro y preparar agregados del manifiesto `h2-expand-compat`. Distingue baseline, objetos parciales fuera del ledger, contrato público compatible e inconsistencias. No autoriza aplicación ni invoca RPC.

**Símbolos/entrada:** `load_pro_environment`, `service_get`, `public_get`, `select_all`, `select_service_all`, `select_public_all`, `table_exists`, `table_has_rows`, `classify_h2_state`, `build_report`, `main`. **Flags detectados por AST:** `(sin flags argparse detectados)`.

**I/O, datos y efectos:** GET a Pro fijado por host y origen HTTPS canónico. Las lecturas REST no siguen redirects y un 3xx se conserva como error HTTP sanitizado, sin reenviar `apikey` a otro origen. Con publishable key lee `courses.id` visible por RLS. Con la identidad server-side de Production (service key, bypass RLS) pagina todas las filas de `courses(id,institution_id,slug,is_active,is_verified,url)`, `institution_site_profiles(institution_id,production_enabled,notes)` y `supabase_migrations.name`. Hace probes `limit=0` para tres tablas y una vista públicas H2; no consulta endpoints RPC ni esquemas privados. Solo si `crawler_exclusions` existe, lee como máximo su columna `id` de una fila. El proceso compara IDs, slugs y URLs en memoria para conteos y digest de IDs elegibles ordenados; stdout contiene únicamente JSON agregado y los mensajes de import se redirigen a stderr. La salida omite filas, IDs, slugs, URLs, notas, valores de exclusión, cuerpos HTTP y credenciales. El service key lee datos operativos y necesita JIT aunque el reporte no escriba. No ejecuta DDL, DML, RPC ni backfill; el workflow captura el JSON por 30 días y ejecuta un dry-run posterior.

**Consumidores:** `.github/workflows/db-sync-to-pro.yml` lo invoca solo para `h2-expand-compat` cuando `operation != verify`; el resultado se conserva como artefacto de 30 días. El siguiente paso del job ejecuta el reporte dry-run del migrador. Los guards de apply/verify están en el workflow y `db_migrate.py`, no en esta salida.

**Pruebas/evidencia:** `tests/test_h2_pro_preflight_report.py` cubre baseline, H2 parcial fuera de ledger, superficie pública compatible solo como diagnóstico, ledger/schema inconsistente, discrepancia de visibilidad, errores HTTP/red/JSON/forma sanitizados, query mínima de existencia de exclusiones, pin HTTPS Pro, agregación de duplicados, bloqueo de redirects y stdout JSON limpio. En Docker/red deshabilitada: 29/29 casos del reporte más quince controles focales de lectura/paridad/migrador, 44/44 PASS. Las pruebas añaden regresión para GET/RPC sin redirects, incluidas cinco llamadas directas de la ruta de paridad de schema, y probes de privacidad H3 que fallan cerrado ante HTTP 302/500. Log SHA-256 `2bd78775f382ddb2b7640e87a241317b320cbe2badaea3ff041c0eb404ee7ae8`; `py_compile` separado SHA-256 `70dfa6a2bf0032db1311a455aa076b1fd8cefc461c31853a91323661f6f9dfd9`. La lógica previa de duplicados era correcta.

**Operación/permisos:** El workflow futuro `DB Sync to Production` en ref `certificacion` usa secrets del environment Production; el service key permite lectura con bypass de RLS y requiere JIT aunque no escriba. El paso adicional `db_migrate.py --dry-run --manifest h2-expand-compat` lee el ledger y reporta nombres/conteo de pendientes; la operación `report` no cumple la condición del job `apply`. Payload que se presentará: `candidate_sha` igual al HEAD inmutable de `certificacion`, `payload_sha` igual a ese SHA porque no hay payload de apply, `operation=report`, `migration_manifest=h2-expand-compat`, `apply_authorized=false`, `backup_pitr_verified=false`, `ddl_authorization_id` vacío, `h2_expected_eligible_count=0` (inert, reemplaza el default peligroso 224), digest vacío y `h2_advisors_reviewed=false`. El artifact JSON agregado permanece 30 días. No imprime secretos, filas ni cuerpos HTTP y no produce escritura de base de datos. No se ejecutó contra Pro.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-h2-scan-unauthorized-writers

**Path y propósito:** `scripts/maintenance/h2_scan_unauthorized_writers.py` — Maintenance CLI `h2_scan_unauthorized_writers.py`; AST entry symbols: scan, main.

**Símbolos/entrada:** (sin docstring de módulo); scan, main. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: local read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-lightweight-ping

**Path y propósito:** `scripts/maintenance/lightweight_ping.py` — Maintenance CLI `lightweight_ping.py`; AST entry symbols: check_course_url, run_ping.

**Símbolos/entrada:** (sin docstring de módulo); check_course_url, run_ping. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get,requests.patch. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-metadata-quality-report

**Path y propósito:** `scripts/maintenance/metadata_quality_report.py` — Maintenance CLI `metadata_quality_report.py`; AST entry symbols: analyze_metadata.

**Símbolos/entrada:** (sin docstring de módulo); analyze_metadata. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get; local write. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Network read capability; do not run without explicit endpoint/environment review; no credential values belong in logs/docs.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-migrate-data-to-pro

**Path y propósito:** `scripts/maintenance/migrate_data_to_pro.py` — Migrate ALL data from Supabase Free (Dev) to Supabase Pro (Production).

**Símbolos/entrada:** Migrate ALL data from Supabase Free (Dev) to Supabase Pro (Production).; run_mgmt_sql, upsert_pro, load_free_snapshot, delete_pro_data, execute_migration, main. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Cross-environment write; explicit, distinct per-environment credential pairs and separate remediation authorization are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-migrate-rpcs-to-pro

**Path y propósito:** `scripts/maintenance/migrate_rpcs_to_pro.py` — Maintenance CLI `migrate_rpcs_to_pro.py`; AST entry symbols: (sin def/class detectado).

**Símbolos/entrada:** (sin docstring de módulo); (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.post; local read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DDL/RPC SQL capability; separate JIT DDL, closed manifest, Pro baseline and rollback are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-noise-discovery-engine

**Path y propósito:** `scripts/maintenance/noise_discovery_engine.py` — Maintenance CLI `noise_discovery_engine.py`; AST entry symbols: tokenize_paths, is_noise_candidate, score_confidence, build_exclusion_pattern, analyze_institution, generate_report, run_discovery.

**Símbolos/entrada:** (sin docstring de módulo); tokenize_paths, is_noise_candidate, score_confidence, build_exclusion_pattern, analyze_institution, generate_report, run_discovery. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: select_all(courses); select_all(institutions); select_all(staging_raw); red/archivo: DB read; local write. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-preventive-cleanup

**Path y propósito:** `scripts/maintenance/preventive_cleanup.py` — Fase 74: Preventive cleanup — now writes to institution_site_profiles.exclusion_patterns (JSONB).

**Símbolos/entrada:** Fase 74: Preventive cleanup — now writes to institution_site_profiles.exclusion_patterns (JSONB); (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: delete(courses); patch(institution_site_profiles); select(courses); select(institution_site_profiles); select(institutions); red/archivo: DB read; DB write/capable RPC; DB delete. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Write/delete capability; JIT for the exact target/data, reviewed filters and recovery plan are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-pucp-sync-to-pro

**Path y propósito:** `scripts/maintenance/pucp_sync_to_pro.py` — Maintenance CLI `pucp_sync_to_pro.py`; AST entry symbols: (sin def/class detectado).

**Símbolos/entrada:** (sin docstring de módulo); (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get,requests.patch,requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Cross-environment write; explicit, distinct per-environment credential pairs and separate remediation authorization are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-quality-assurance-audit

**Path y propósito:** `scripts/maintenance/quality_assurance_audit.py` — Maintenance CLI `quality_assurance_audit.py`; AST entry symbols: run_audit.

**Símbolos/entrada:** (sin docstring de módulo); run_audit. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: select_all(courses); red/archivo: DB read; local write. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-review-autogen-profiles

**Path y propósito:** `scripts/maintenance/review_autogen_profiles.py` — Fase 121: Script de revision de perfiles auto-generados. Lista instituciones con perfil auto_generated=true y pipeline_ready=false para que un humano.

**Símbolos/entrada:** Fase 121: Script de revision de perfiles auto-generados. Lista instituciones con perfil auto_generated=true y pipeline_ready=false para que un humano ; list_autogen, approve. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: patch(institution_site_profiles); select(institutions); red/archivo: DB read; DB write/capable RPC. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-seed-institutions

**Path y propósito:** `scripts/maintenance/seed_institutions.py` — Maintenance CLI `seed_institutions.py`; AST entry symbols: make_slug, get_type.

**Símbolos/entrada:** (sin docstring de módulo); make_slug, get_type. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.post; local read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-seed-pro-profiles

**Path y propósito:** `scripts/maintenance/seed_pro_profiles.py` — Fase 74: Seed institution_site_profiles in Pro — reads profiles from Free via db_client, upserts to Pro via raw requests.

**Símbolos/entrada:** Fase 74: Seed institution_site_profiles in Pro — reads profiles from Free via db_client, upserts to Pro via raw requests; (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get,requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-seed-site-profiles

**Path y propósito:** `scripts/maintenance/seed_site_profiles.py` — Maintenance CLI `seed_site_profiles.py`; AST entry symbols: seed.

**Símbolos/entrada:** (sin docstring de módulo); seed. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: select(institutions); upsert(institution_site_profiles); red/archivo: DB read; DB write/capable RPC. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-sync-pro-to-free

**Path y propósito:** `scripts/maintenance/sync_pro_to_free.py` — Fase 71: Sincronizar Pro → Free con identidades explícitas y distintas.

**Símbolos/entrada:** Fase 71: Sincronizar Pro → Free con identidades explícitas y distintas.; _paginate_get, _build_uuid_map, _pro_to_free_map, _translate_field, _clean_row, count_free, sync_table, dry_run_table, main. **Flags detectados por AST:** `--dry-run, --table, --truncate-staging`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: delete(staging_raw); insert(dynamic); upsert(dynamic); red/archivo: DB write/capable RPC; DB delete; network requests.get. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Cross-environment write; explicit, distinct per-environment credential pairs and separate remediation authorization are required.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-taxonomy-roi-audit

**Path y propósito:** `scripts/maintenance/taxonomy_roi_audit.py` — Maintenance CLI `taxonomy_roi_audit.py`; AST entry symbols: run_taxonomy_roi_audit.

**Símbolos/entrada:** (sin docstring de módulo); run_taxonomy_roi_audit. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: select_all(courses); select_all(market_salaries); red/archivo: DB read; local write. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-test-inst-insert

**Path y propósito:** `scripts/maintenance/test_inst_insert.py` — Maintenance CLI `test_inst_insert.py`; AST entry symbols: (sin def/class detectado).

**Símbolos/entrada:** (sin docstring de módulo); (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.get,requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** DB write capability; separate JIT, explicit target and reviewed scope are required; dry-run only where the code exposes it.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-validate-dmc-pro-coverage

**Path y propósito:** `scripts/maintenance/validate_dmc_pro_coverage.py` — Validar que los cursos en Pro coincidan con el artifact dmc.txt.

**Símbolos/entrada:** Validar que los cursos en Pro coincidan con el artifact dmc.txt.; (sin def/class detectado). **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: local read. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-validate-profile-extraction-config

**Path y propósito:** `scripts/maintenance/validate_profile_extraction_config.py` — Fase 121 — valida configuracion JSONB de extraccion por perfil. No ejecuta selectores contra sitios externos. Solo valida estructura, allowlist de tra.

**Símbolos/entrada:** Fase 121 — valida configuracion JSONB de extraccion por perfil. No ejecuta selectores contra sitios externos. Solo valida estructura, allowlist de tra; _as_dict, _as_list, _validate_selector_spec, validate_profile, main. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: no direct effect parsed; review helper/import wrappers. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Read/report capability based on the reviewed source; inspect imports/wrappers and output destinations before running.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## herramienta-verify-pro-schema

**Path y propósito:** `scripts/maintenance/verify_pro_schema.py` — Maintenance CLI `verify_pro_schema.py`; AST entry symbols: run_sql.

**Símbolos/entrada:** (sin docstring de módulo); run_sql. **Flags detectados por AST:** `(sin flags argparse detectados)`. Que no aparezca `argparse` no descarta argumentos posicionales o configuración implícita.

**I/O, datos y efectos:** DB/HTTP observado: (sin llamada DB directa parseada); red/archivo: network requests.post. Se documenta capacidad estática; no se ejecutó.

**Consumidores:** El alcance de búsqueda en ambos checkouts no encontró invocación directa de producto/workflow/test fuera de la identidad de credenciales que enumera `tests/test_supabase_credentials_contract.py`; ese test no ejercita comportamiento. Puede existir invocación manual o indirecta fuera del alcance.

**Pruebas/evidencia:** No se encontró suite de comportamiento específica en el alcance. `test_supabase_credentials_contract.py` solo inventaría identidades/path y no prueba la funcionalidad. Impacto: si se cambia el contrato, agregar una prueba local apropiada y documentar su input/result.

**Operación/permisos:** Network read capability; do not run without explicit endpoint/environment review; no credential values belong in logs/docs.

**Historia y estado:** resultado por ruta en [índice de Git local](../evidencia/h3req1_historia_paths_local_2026-10-12.md). Una ruta sin commit local queda identificada como tal; el índice no prueba la motivación original. Los motivos solo se atribuyen donde hay decisión versionada; no se inventan para estas herramientas.

**Cómo cambiarlo:** leer el cuerpo y helper completos; mantener target y contrato de identidad; actualizar el caller o handoff documentado, este registro y la suite específica (o crear una si la ausencia está acreditada); revisar artifact diff, filtros, rate/timeouts y rollback. Para writer/delete/DDL/cross-env conseguir JIT separado antes de cualquier ejecución.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
