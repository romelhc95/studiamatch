# Componentes legacy y deprecated

## Inventario

`scripts/deprecated/harvesters/` conserva once scrapers institucionales con contratos distintos por institución. Los once hacen `POST` directo a `courses` y evitan discovery/estados del pipeline actual; `new-horizons-peru_harvester.py` y `smartdata_harvester.py` además contienen rutas `PATCH` de registros existentes. Los otros nueve (`continental`, `idat`, `nacional`, `pucp`, `senati`, `ulima`, `upc`, `usil` y `utp`) no comparten esas rutas PATCH. La implementación de cada scraper y sus campos de salida siguen siendo la autoridad para cualquier análisis puntual. Ninguno se considera writer vigente: el flujo actual documentado es `scripts/core/sync_vector_worker.py` y el mantenimiento de disponibilidad de `scripts/maintenance/integrity_ping.py`.

Los auxiliares fuera de `harvesters/` no forman un solo módulo operativo:

| Fuente | Contrato y efectos que constan en el código | Límite actual |
|---|---|---|
| `scripts/deprecated/add_exclusion.py` | Lee instituciones y la tabla histórica `crawler_exclusions`, intenta insertar allí y contiene `_cleanup_staging()` con borrado de filas `staging_raw`. | La tabla histórica fue retirada por migration; el borrado de staging tiene efecto distinto y no se ejecuta en esta transferencia. |
| `scripts/deprecated/seed_crawler_exclusions.py` | Lee catálogo institucional y escribe patrones en `crawler_exclusions`. | Incompatible con el schema local vigente tras retirar esa tabla; no ejecutar contra ningún ambiente. |
| `scripts/deprecated/fase32b_migrate_free_to_pro.py` | Conserva lecturas/escrituras REST entre Free y Pro, incluyendo datos operativos como `courses` y `enriched_programs`, además del modelo antiguo de exclusiones. | No es promoción DB-as-Code ni una ruta actual de despliegue; requiere autorización y plan de remediación separados si alguna vez se evalúa. |

La búsqueda local acotada no encontró un caller automatizado de estos paths. `tests/test_supabase_credentials_contract.py` inventaría algunas identidades/transporte para la auditoría de credenciales; no importa ni ejecuta los scrapers/helpers. Los resultados y el alcance de búsqueda están en [la revisión local de relaciones](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md#relaciones-legacy-2026-10-13). No se descarta una invocación manual o privada fuera de los dos checkouts.

`scripts/legacy/`, cuando contiene material de desarrollo archivado, no forma parte del runtime; el registro clasifica fuentes ejecutables presentes y el mapa de reorganización conserva rutas históricas sin moverlas.

Los informes fechados de `docs/**` se preservan como historia. Los planes de remediación/infraestructura que ya contradecían el candidato fueron retirados del árbol activo después de respaldarlos y revisar referencias; sus reemplazos, SHA y tratamiento están en la [evidencia de consolidación documental](../evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md#rutas-consolidadas). No se convierte ninguna propuesta histórica en comportamiento actual.

## Contratos, datos y pruebas

| Familia | Datos/efectos | Consumidor/prueba | Estado y límite |
|---|---|---|---|
| Harvesters directos | Once `POST` a `courses`; dos (`new-horizons-peru`, `smartdata`) incluyen además `PATCH`. Pueden marcar datos verificados sin pasar por estaciones/gates actuales. | Sin caller automatizado hallado en los árboles locales; el test de credenciales solo enumera transporte. No se encontró suite funcional por scraper. | Legacy/deprecated. Los commits locales de 2026-09-10 prueban presencia histórica, no ejecución ni vigencia. |
| `add_exclusion.py` | GET/POST del contrato `crawler_exclusions` y DELETE acotado sobre `staging_raw` en su helper de limpieza. | Sin import/invocación en tests/workflows/código buscado; no se encontró suite funcional. | Dos efectos distintos; no asumir que el path de exclusiones controla también el borrado staging. |
| `seed_crawler_exclusions.py` | GET de catálogo/tabla vieja y POST a `crawler_exclusions`. | Sin caller automatizado ni prueba de comportamiento hallados; el test de credenciales no ejecuta el seed. | Legacy; incompatible con la tabla retirada. |
| `fase32b_migrate_free_to_pro.py` | Lectura/escritura cross-environment de tablas de catálogo y operativas, con mapeos históricos. | No se encontró caller o caso de prueba de comportamiento en los árboles locales. | Legacy; no usar como sync normal ni como DB-as-Code. |

Las coincidencias de consumo se revisaron como texto/rutas en 920 archivos del candidato y 529 del original, en los árboles locales de `tests`, `scripts`, `.github`, `.githooks`, `web`, `workers` (solo donde existe), `supabase`, `db`, `config` y `mock-server`. Se excluyeron `.env*`, dependencias y caches. Coincidencias de logs `.github/log/` se clasificaron como registro histórico; no como caller. La historia de Git local para los once harvesters apunta a `4b29d771625d6231c5875c9276eb1303a970ef02` (2026-09-10); los helpers de exclusiones a `3b27640c13a0b8a74aab24d205801a51fdc57772` (2026-07-24), y fase 32B a `d8f1ea0b210f2a1cf95e73751621cf8b4fcf0f93` (2026-07-24). Estos commits no acreditan test, ejecución o adopción.

La relación por path, estado, operación, consumidor, test/evidencia y fuente histórica está en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#legacy-y-deprecated). La evidencia de un commit no demuestra test, deploy ni adopción remota; la ausencia de un caller en los árboles locales no demuestra que no exista un consumidor externo.

## Exclusion migration

[`scripts/maintenance/merge_exclusions_to_profiles.py`](../../scripts/maintenance/merge_exclusions_to_profiles.py) define `merge()` como migrador de una sola vez entre la tabla retirada `crawler_exclusions` y `institution_site_profiles.exclusion_patterns`. Lee instituciones/perfiles, agrega patrones y hace `upsert` del perfil. La fuente SQL local [`20260503_FASE74_drop_crawler_exclusions.sql`](../../db/migrations/20260503_FASE74_drop_crawler_exclusions.sql) retira la tabla vieja; por ello el helper no es compatible con el contrato local vigente sin una fuente `crawler_exclusions` separada.

La búsqueda literal de `merge_exclusions_to_profiles`, `merge()` y `crawler_exclusions` en `scripts/**`, `.github/workflows/**` y `tests/**` de ambos checkouts halló solo: comentario de `fase74_seed_pro.py`, texto de ayuda de `seed_crawler_exclusions.py` y entrada de identidad de transporte en `test_supabase_credentials_contract.py`. La revisión de esos tres hits no encontró import ni invocación de `merge()`; el test de credenciales enumera el endpoint/identidad, no ejecuta el helper. Este alcance no descarta un wrapper privado o trigger remoto. No aparece una prueba funcional dedicada del helper en `tests/**`; la evidencia disponible demuestra su código y la migration de retiro, no que el helper haya corrido ni que los datos se hayan migrado. No ejecutarlo. Reactivarlo exigiría confirmar fuente/schema y ambiente, definir dry-run/idempotencia/rollback, añadir fixture y test, y autorización DB write. La búsqueda bilateral y el límite de relación están en [resolución R11](../evidencia/h3req1_sem_resolucion_relaciones_locales_2026-10-13_r11.md#mantenimiento-legacy-de-exclusiones).

## Documentación histórica por dominio

Los Markdown conservados bajo `docs/` son lecturas históricas agrupadas por responsabilidad; no son rutas de runtime ni una segunda fuente de estado. La asignación exacta de cada archivo y sus anclas de registro están en `legacy-docs-*` del registro verificable.

| Ruta/familia | Propósito histórico | Tratamiento vigente |
|---|---|---|
| `STUDIAMATCH-H3-UAT-MOCK-02-REPORT.md` | Informe UAT mock de un corte previo | Evidencia histórica; no acredita el candidato actual. |
| `docs/architecture/` | Diagramas y descripciones de arquitectura/pipeline de cortes anteriores | Contrastar con `.context/arquitectura.md` y fichas actuales. `sdlc_global_workflow.md` mantiene menciones históricas al plan raíz retirado. |
| `docs/deployment/` y `docs/devops-engineer/` | Guías e informes de ambientes/deploy | No usar como runbook actual sin cotejar con `.context/operacion.md`, workflows locales y estado. |
| `docs/operations/` | Taxonomía y hardening de URLs | Historia; no sustituye operación/pipeline actuales. |
| `docs/data-analyst/` | Análisis y propuestas de catálogo, taxonomía y calidad | No son resultados actuales ni autorización de writes. |
| `docs/frontend-architect/` y `docs/code-cleaner/` | Revisiones visuales/refactor de una fecha concreta | No gobiernan UI ni código presentes. |
| `docs/health-monitor/`, `docs/tech-evaluator/` y `docs/orquestador-sdlc/` | Reportes de revisión técnica, calidad y coordinación | Conservar como historia; propuestas, test reports y recomendaciones no se elevan a PASS actual. |
| `docs/qa-engineer/` | Reportes de QA y cortes de prueba | Los informes existentes permanecen por su evidencia histórica; ningún resultado se atribuye al estado actual sin input/run fechado. Dos rutas que son destinos de writers mantenidos se clasifican como artefactos generados en la ficha de mantenimiento. |
| `docs/security/` y `docs/security-auditor/` | Reportes y resolución histórica de seguridad | No son waivers vigentes ni reemplazan el tooling/evidencia actual. |

Para estos documentos no aplica una suite funcional del producto: son fuentes de consulta histórica. El informe puede servir como evidencia de su propio corte solo si identifica input/fecha; su presencia no equivale a PASS. La búsqueda de consumidores automatizados y los cuatro escritores de reportes se registran en la evidencia local citada arriba y en [mantenimiento](mantenimiento.md#reportes-generados-y-conservados).

## Navegación

[Pipeline vigente](pipeline.md) · [Datos y pipeline](datos_pipeline.md) · [Operación](../operacion.md#pipeline-y-mantenimiento) · [Base de datos](../database.md#baseline-fixtures-y-rollback) · [Registro de fuentes](../trazabilidad/registro_fuentes_componentes.md#legacy-y-deprecated)

## Fuentes y relaciones

Este registro no reemplaza la documentación del comportamiento fuente: agrega asignaciones exactas y permite verificar paths, anchors y exclusiones.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
- [Documentación DB sustituida](../catalogos_historicos/database_legacy.md#documentos-preservados)
