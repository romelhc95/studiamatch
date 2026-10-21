# Canarios de certificación y producción

## Contratos y piezas

| Pieza | Responsabilidad | Consumidor local demostrado | Estado y límite |
|---|---|---|---|
| F9.9 manifest de certificación | `scripts/core/certification_canary_manifest.py`: `_resolve_institution`, `_load_profile`, `_count_pipeline`, `build_manifest`; consulta perfil y conteos de `staging_raw`, `cleansed_programs`, `enriched_programs`, sanitiza identificadores y escribe un manifiesto/variables de GitHub. | `tests/test_fase09_9_certification_canary.py` cubre sanitización/contrato; `tests/test_supabase_credentials_contract.py` clasifica la identidad Data API. La búsqueda en `.github/workflows/` de ambos checkouts no halló caller F9 vigente. | Suite contractual local identificada; no se afirma ejecución aquí. El manifest es de lectura de datos más salida local; no prueba que un workflow corrió o que Certification lo adoptó. |
| F9.9 state de certificación | `scripts/core/certification_canary_state.py`: `capture_snapshot` guarda un snapshot privado del cohort; `restore_snapshot` comprueba marcadores y devuelve filas de las tres tablas a su estado previo, con PATCH y DELETE idempotentes. | `tests/test_fase09_9_certification_canary.py` incluye los contratos de snapshot/restore; `tests/test_supabase_credentials_contract.py` solo clasifica proveedor/key transport, no ejecuta restauración. No hay workflow local que invoque esta fuente. | La relación de suite está comprobada; no se atribuye PASS/ejecución. `restore` puede modificar/eliminar datos y necesita JIT si un operador lo dirigiera a un ambiente real. El workflow F9.9 está retirado en el corte local. |
| Workflow F10 de producción | `.github/workflows/production_canary.yml` declara `workflow_dispatch` limitado a `main`, environment `Production`, SHA fijado, preflight, manifest, snapshot, restore y revalidación. | Llama explícitamente a los tres módulos F10. `tests/test_fase10_production_canary.py` valida el contrato del YAML. | Declaración local únicamente; no prueba workflow instalado, permisos, secrets, dispatch ni schedule remoto. No lo ejecutar ni configurar en este ciclo. |
| Preflight F10 | `scripts/core/production_canary_source_preflight.py` valida host/URLs de perfil y realiza GET acotado; aborta redirects y navegación fuera del allowlist de host. | El workflow F10 y `tests/test_fase10_production_canary.py`; no es un caller del producto web. | Llamada de red de lectura hacia origen institucional cuando se ejecuta; restricciones se verifican en tests fake, no en remoto. |
| Manifest F10 | `scripts/core/production_canary_manifest.py` consulta target/perfil y conteos, aplica gates/límites y escribe resumen sanitizado y variables temporales de Actions. | El workflow F10 y `tests/test_fase10_production_canary.py`. | Data API de lectura y salida de workflow. Un manifest no prueba fin del canario ni schema remoto actual. |
| State F10 | `scripts/core/production_canary_state.py` captura snapshot privado acotado; restore compara marcador/IDs, reconstituye cohort, elimina extras y PATCH filas cambiadas, luego revalida filas fuera del cohort y repetibilidad. | El workflow F10 y `tests/test_fase10_production_canary.py` con fake DB. | Capacidad DB de escritura y borrado. Snapshot privado no se publica como artifact; tests source no equivalen a dispatch/restore remoto. |

### Manifest de certificación F99

`certification_canary_manifest.py` resuelve el `institution_slug`, carga `institution_site_profiles` y cuenta cohortes por `institution_id` en `staging_raw`, `cleansed_programs` y `enriched_programs`. `build_manifest()` valida que el contexto/target sea Certification, aplica el perfil canary permitido y emite contadores sanitizados; `_write_github_env()` escribe el ID/slug sanitizado para pasos del runner. El consumer local es la suite `tests/test_fase09_9_certification_canary.py`; `tests/test_supabase_credentials_contract.py` únicamente clasifica la identidad Data API. La búsqueda en `.github/workflows/` de ambos checkouts no encontró workflow F99 vigente. No se afirma ejecución de la suite o adopción de Certification; si se modifica el conteo o sanitización, revisar ambas suites y el contrato de `institution_site_profiles`.

### State de certificación F99

`capture_snapshot()` guarda en un archivo privado las filas previas de las tres tablas para la institución/marker acotado. `restore_snapshot()` valida el contexto y el marcador F99, elimina filas extra creadas por el canary y parchea las que cambiaron para reproducir el estado previo; la operación está diseñada para repetirse. Las funciones dependen de `scripts/shared/db_client.py` y del schema localmente descrito en [Database](../database.md). La suite offline `test_fase09_9_certification_canary.py` comprueba el contrato con fuentes/fakes; el test de credenciales no lo ejecuta. `restore_snapshot` tiene efectos DELETE/PATCH, por lo que no debe usarse contra un ambiente real sin JIT separado, snapshot privado y rollback aprobado. No hay un workflow F99 actual que lo llame.

### Workflow manual de producción F10

`.github/workflows/production_canary.yml` declara `workflow_dispatch` para `main`, fija el SHA/ambiente `Production` y ordena preflight → manifest → snapshot → writers autorizados → restore aun ante fallo → manifest/attest posterior. El YAML contiene el contrato de job/orden; `tests/test_fase10_production_canary.py` y `tests/test_fase10_main_boundary.py` inspeccionan sus límites. Es una definición local, no prueba que exista el workflow remoto ni que se haya despachado. Revisar el test de main boundary y el workflow cuando se cambie trigger, permiso, input, orden o condición de restore; una dispatch real requiere instrucción separada.

### Preflight de origen F10

`production_canary_source_preflight.py` valida URL base/patrones del perfil de institución, exige HTTPS/host permitido, bloquea redirects y hace GET limitado antes de snapshot. Sus límites de host/status se ejercitan con respuestas sintéticas en `test_fase10_production_canary.py`; no prueba la disponibilidad actual de un proveedor. Depende del perfil de institución y del helper de datos compartido, pero no modifica las tablas. Ante cambios de URL/patrón, renovar la suite de preflight, pruebas de redirects/status y el orden del workflow antes de cualquier dispatch.

### Manifest de producción F10

`production_canary_manifest.py` combina `CANARY_INSTITUTION_SLUG`, target esperado y cohorte, valida límites y cuenta filas de pipeline con el cliente DB. Produce un JSON público sanitizado y valores temporales de Actions; no incluye snapshot privado. El workflow lo invoca antes y después del canario. La suite `test_fase10_production_canary.py` usa fake DB y comprueba límites/redacción; la suite no se ejecutó durante esta transferencia. Si cambian contadores, variables, campos o sanitización, revisar preflight, state, assertions de manifest y variables permitidas del job.

### Estado de producción F10

`production_canary_state.py` separa el snapshot privado de su resumen sanitizado, valida target/main/Production y la marca de run, pagina comprobaciones de datos ajenos al cohort, y restaura filas del cohort con PATCH/DELETE. Antes de aceptar restore comprueba igualdad de contenido, conteos/NULL semantics, rows que desaparecen, fallos parciales e idempotencia en una segunda pasada. El workflow ejecuta la compensación en salida normal o fallida. `test_fase10_production_canary.py` usa fake DB para esos casos; el resultado solo acredita un run fechado que identifique inputs y entorno. Nunca adjuntar el snapshot privado. Cualquier cambio de schema/row marker/query pagination exige revisar el SQL/diccionario, el workflow, la suite y la recuperación; el uso remoto requiere aprobación separada.

## Secuencia y protección

El workflow de producción declara únicamente `workflow_dispatch` sobre `main`, un environment `Production`, SHA/revisión fijados y límites de filas; el test `test_production_canary_workflow_is_manual_main_only_and_sha_locked` valida el YAML local. La restauración se intenta incluso tras fallo y luego se comprueba que el estado se recuperó; esa propiedad es código/test, no evidencia de ejecución en este corte.

Variables/bindings identificados por nombre: `F99_CERTIFICATION_CANARY_SUPABASE_HOST`, `F10_PRODUCTION_CANARY_SUPABASE_HOST`, `CANARY_EXPECTED_ENVIRONMENT`, `CANARY_INSTITUTION_SLUG` y credenciales Supabase por environment. No se registran valores. F9 limita el target a Certification cuando se ejecuta en Actions; F10 exige Production y `main`.

Los manifests y summaries JSON son artefactos derivados de las consultas y del estado de ejecución. La captura privada usa un directorio temporal del runner; no se debe adjuntar ni confundir con evidencia sanitizada. Preservar logs/manifiestos existentes con su input, fecha y referencia; los archivos locales presentes no prueban adopción remota.

## Modificar sin confundir preflight, manifest y estado

Para cambiar el origen/destino o gate, sigue `production_canary.yml` → `production_canary_source_preflight.py` → `production_canary_manifest.py` → `production_canary_state.py`. El preflight hace GET acotado a URLs permitidas; el manifest lee y serializa un resultado sanitizado; `snapshot` conserva el estado privado para compensación; `restore` es el único paso aquí descrito con PATCH/DELETE. Cambios de variables o schemas deben renovar `test_fase10_production_canary.py`, el harness/quota o pipeline que toca esos objetos y la revisión estática del workflow. No se corre snapshot/restore para probar documentación. F9 y F10 usan runtimes/ambientes distintos; compartir código de redacción no implica compartir workflow.

La búsqueda local de `certification_canary` en `.github/workflows/**` no encontró invocación vigente; el test F9.9 existe como suite manual/local, pero `security-audit.yml` no lo incluye en sus comandos actuales de pytest. Para Production, el YAML y test están presentes localmente; dispatch/schedules, secrets, environment y ejecución reales quedan en una comprobación remota pendiente.

## Fuentes y relaciones

La asignación por archivo, métodos, tablas, consumidores, pruebas y permisos está en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#canarios). Las pruebas de contrato están en [pruebas](../pruebas.md); la operación y sus límites en [operación](../operacion.md#pipeline-y-mantenimiento). La historia local está resumida en el [changelog](../changelog.md#historia).

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
