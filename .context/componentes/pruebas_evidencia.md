# Componente: pruebas y evidencia

## Corte local H3REQ1 — contrato editorial CA4, 2026-10-28

El [checkpoint del contrato editorial](../evidencia/h3req1_editorial_contract_2026-10-28.md)
conserva baseline, evidencia separada, resultados E1–E6 y límites. En el candidato
local E1–E5 pasan con harnesses PG17 sintéticos y prueba FG3 aislada. E6 tiene
assertions añadidas al UAT y el build/TypeScript/contratos source-level pasan, pero
queda pendiente la ejecución real en navegador para teclado, preview y medidas de
overflow desktop/móvil; por eso el paquete aún no es publicable. No hubo CI porque
no se abrió PR. Los resultados no acreditan ambiente remoto ni aceptación funcional
remota.

Esta ficha conecta suites con dominios; los conteos son locales y fechados, no una medición acumulativa de calidad.

| Familia | Ruta/runner | Componentes | Evidencia principal | Límite |
|---|---|---|---|---|
| Python contratos | tests/test_*.py | web/BFF/DB/pipeline/seguridad | R178 G03 337 passed, 4 skipped, 1 warning | Skips/warning no son PASS. |
| SQL | tests/sql/*.sql | pipeline, editorial, RBAC, invitation, cuota, gateway | R178 G01/G07 | PostgreSQL 17 synthetic. |
| Browser/UAT | tests/*.mjs, fixtures/mock-server | público/Admin/onboarding | R178 G09 y R173 | Mock/synthetic, viewports seleccionados. |
| Pages/workerd integrated | tests/h3req1_c03* | BFF/Edge/PostgREST | R178 G07 R51 128/128 | Local/isolated; no remote environment. |
| Build/source snapshot | tests/h3req1_c03_source_snapshot* | worker and static artifact | R178 G05/G06 | Hashes solo identifican el input. |
| Security/scope | scripts/security, hooks, YAML workflow | secretos, rutas, CI | La nota de resolución R11 registra los checks documentales y scanner locales de este corte; el shell guard no acredita branch protection remota. | Scanner estático, no garantía remota. |
| Diagnóstico transferencia C03 | `tests/h3req1_docker_peer_substep_diag/**` | Diagnósticos de Docker Desktop/WSL, probes y clasificadores locales | No se atribuye un PASS por presencia de herramientas; revisar por runner y evidencia fechada | No es suite funcional del producto; algunos wrappers pueden cambiar o eliminar recursos Docker. |
| Integración/fixtures C03 | `tests/h3req1-c03-*`, `tests/h3req1_c03_*` | Contratos sintéticos, lock resolver y runners aislados | R178 R51 es histórico; no acredita cambios posteriores del WIP | Incluye herramientas one-off: leer su manifiesto/efectos antes de cualquier ejecución. |

Fuente de resultados por fecha: [R178](../evidencia/h3req1_g09_local_close_r178_2026-10-11.md), [R181/R182](../evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md). Los artefactos de fallos/retries/capturas se preservan en .context/evidencia y no deben sobrescribirse.

Corte local público R11 — 2026-10-25: el catálogo de `tests/h3_local_uat.mjs` asigna H3-UAT-058 a H3-CA4.11 (responsive de listado/detalle) y H3-UAT-059 a H3-CA4.9 (filtros independientes y objetivo “Actualizarme”). H3-UAT-058 pasó 3/3 viewports en la corrida canónica combinada. H3-UAT-059 falló primero por una expectativa de test desactualizada; el filtro “corta” no debe incluir la duración compuesta de seis meses. Se actualizó la expectativa manteniendo la banda corta vacía con este fixture, la banda media de 3–6 meses inclusiva y la larga por encima de seis meses. La ejecución focal posterior pasó 1/1 caso, 3/3 viewports y 38/38 aserciones por viewport; retries 0, resets 0 porque el caso no los requiere. PostgreSQL 17 desechable se reutilizó sin SQL, resets ni cleanup; el postflight read-only confirmó 13 relaciones públicas, 31 cursos, 31 filas editoriales, 16 cursos efectivos y 26 filas de cola. Build local del producto SHA `6e1bd8f5ad623a44524b11391c1385c59b9a4b70`; runner probado SHA-256 `5246b6473bc78dae70595668530a05545b811e7fce9d6e54df08a42716b95f32`. Las salidas brutas y capturas de R11 se conservan localmente fuera del PR; el resumen sanitizado, hashes y límites están en el [ciclo de aceptación local](../evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-acceptance-cycle-2026-10-24.md). Es evidencia sintética local, no aceptación del Preview, Development ni D06/Admin.

Corte local público R12 — 2026-10-25: el runner vuelve a confirmar H3-UAT-058→H3-CA4.11 y H3-UAT-059→H3-CA4.9; ambos declaran cero resets. En Docker, el build estático del candidato pasó y ambas rutas públicas devolvieron 200 con contenido esperado. La ejecución conjunta pasó 2/2 casos, 6/6 viewports y 6 capturas; 058 verificó responsive listado/detalle/footer y panel a 320 px (17/17 assertions), y 059 verificó filtros y “Actualizarme” (39/39 assertions por viewport; 117/117). Cero retries, cero resets. El fixture PG17 completo se reutilizó con lecturas read-only antes/después; conteos sin cambio. Chrome Windows MCP observó el build local por el forwarder GET/HEAD a 390 px y confirmó el nombre accesible `Largos (>6m)` con contador; la medición de 320 px se atribuye al runner. Ver [R12 y artefactos locales](../evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-acceptance-cycle-2026-10-24.md#r12-build-local-filtros-responsive-y-verificacion-visible-2026-10-25). Es evidencia sintética local, no aceptación del Preview ni de Development.

## Candidato local R21: correcciones públicas y Admin

R21 reúne la normalización de modalidad/duración consumida por ambos recorridos “Actualizarme”, el wrapping de “Limpiar todo”, la cabecera Admin móvil y la protección contra respuestas tardías de la cola. La regresión de duración y H3-UAT-059 son los casos para repetir tras el deployment nuevo; el subcaso de cabecera se valida en un viewport móvil Admin, y la cola necesita dos filtros con respuestas deliberadamente fuera de orden. Los tests `admin_header_responsive.test.mjs` y `admin_queue_request_guard.test.mjs` son unitarios/source-level: por sí solos no prueban runtime remoto ni sustituyen esas comprobaciones UI.

## Navegación relacionada

[Pruebas](../pruebas.md) · [Seguridad](../seguridad.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#pruebas-y-evidencia) · [Requerimientos](../requerimientos/README.md) · [Hitos](../hitos/README.md) · [R178](../evidencia/h3req1_g09_local_close_r178_2026-10-11.md) · [R181/R182](../evidencia/h3req1_g10_r8_review_corrections_r181_2026-10-12.md) · [Resolución de relaciones R11](../evidencia/h3req1_sem_resolucion_relaciones_locales_2026-10-13_r11.md)

## Fuentes y relaciones

Suites funcionales, contratos, SQL harnesses, mocks, runners y diagnósticos locales están asignados por path en el [registro fuente-componente](../trazabilidad/registro_fuentes_componentes.md#pruebas-y-evidencia). Los archivos `.sha256`, logs, capturas y salidas C03 son familias de evidencia/artefactos, no módulos funcionales ni suites activas por sí solos.

## Mock runtime y fixtures

| Fuente | Responsabilidad observable | Consumidor/entrada local | Datos y efectos | Evidencia disponible |
|---|---|---|---|---|
| `mock-server/package.json`, `package-lock.json` | Fija comandos y dependencias del mock HTTP local. | Los runners UAT usan `node`/el servidor mock según sus comandos y spawn sites; no es un workflow de producto. | Dependencias de test solamente; no copiar `node_modules` al paquete. | Manifest/lock identifican dependencias, no ejecución. |
| `mock-server/server.js` | Emula Auth, Data API/RPC y rutas de test; conserva state sintético y comportamiento protegido por `NODE_ENV=test`. La ruta de reset acepta solo el token local de test y devuelve una época monotónica del fixture tras cada reset autorizado. | `tests/h3_local_runtime_server.mjs` y `tests/h3_local_uat.mjs` consumen rutas configuradas en su código; el UAT exige que la época aumente antes de aislar cada ejecución. El alcance de consumidores es `tests/**`, `mock-server/**` y `.github/workflows/**`; no se afirma un consumidor externo. | Usuarios/factores/cursos/invitaciones sintéticos y estado en memoria; puede escuchar un puerto y persistir fixture temporal según configuración. El encabezado de época no contiene credenciales ni estado Auth. | Contratos estáticos `tests/test_h3_mock_invitation_contract.py` y UATs asociadas; el resultado vigente de 058/059 está en [ciclo de aceptación local 2026-10-24](../evidencia/h3req1_public_projection_local_uat_2026-10-24/candidate-acceptance-cycle-2026-10-24.md). |
| `mock-server/static-server.js` | Sirve el export estático para UAT navegador/Pages simulado. | Runners UAT que declaran el static server; revisar `tests/h3_local_uat.mjs` y sus helpers antes de cambiar rutas. | Lectura de `web/out` y salida HTTP local; no es despliegue Pages. | R178 G06/G09 solo acredita los inputs y viewports explicitados allí. |
| `tests/fixtures/h3/admin_auth_local_mock.sql` | Instala funciones/roles/tablas sintéticas que permiten ejecutar contrato Auth/RPC sin Supabase real. | Harnesses PG17 y mock Admin que incluyen el fixture. | Schema desechable y filas sintéticas; no se conecta al proyecto remoto. | Los harnesses identifican qué bloques incluyen el fixture; cada resultado queda en su reporte fechado. |

Para cambiar un comportamiento del mock, localiza primero su ruta exacta, su invocación desde un runner y las pruebas que afirman el contrato. El mock no demuestra equivalencia de Auth, PostgREST, Edge, correo o cuotas remotas. No lo ejecutes contra credenciales reales ni reutilices estado entre tests.

## Admin BFF UAT local

El grupo `functional-admin-uat` tiene 18 fuentes separadas por los casos que operan: `h3_admin_auth_error_uat.mjs` verifica respuestas de autenticación; `h3_admin_bff_mock_uat.mjs` recorre UI/BFF/RPC mock; `h3_admin_invite_edge_typecheck.mjs` compila el contrato TypeScript de Edge; `h3_admin_invite_edge_uat.mjs` recorre invitación/entrega simulada; `h3_admin_quota_{postgrest,runtime,uat}.mjs` separan transporte, runtime y flujo de cuota; `h3_admin_safe_suspend_{runtime,}.mjs` cubren suspensión/reanudación controlada; `h3_invitation_uat.mjs` recorre inbox/aceptación/onboarding; `h3_local_uat.mjs` es el UAT integrado; `h3_local_runtime_{quota_fixture,server}.mjs` prepara dependencias locales; `h3_supabase_sdk_headers_uat.mjs` observa cabeceras SDK; y `h3_local_uat_http_diagnostics.test.mjs` más `h3_local_uat_sanitizer.test.mjs` cubren clasificación/redacción de logs HTTP. `h3_uat_http_diagnostics.mjs` y `h3_uat_sanitizer.mjs` son utilidades llamadas por esos tests, no resultados.

El mapa de símbolo/caso y el fixture exacto se mantiene en cada fuente y en la [trazabilidad local](../evidencia/h3req1_relaciones_semanticas_locales_2026-10-12.md). Estos UAT son mock/local; los tests de contrato Python y harnesses SQL vinculados están en las secciones siguientes. En R10 se renovaron solo los inputs con cambios posteriores a R178: BFF UAT actual (96 checks), middleware safe-suspend y los tests estáticos Admin Invite/DB sync (24 passed en conjunto). La relación de plantillas reutiliza R178 por hashes R8 idénticos. El [reporte R10 Admin](../evidencia/h3req1_sem_admin_validacion_local_2026-10-13_r10.md) contiene hashes, comandos, salidas y límites. Los demás resultados R178 se reutilizan únicamente cuando el input exacto no cambió; un resultado agregado no se presenta como salida individual.

**Delta D04, 2026-10-25:** el mock BFF del candidato local ejecutó 127 checks y añadió el caso HTTP 403 de autorización con payload sanitizado; conserva MFA y el error genérico para otros fallos RPC. Esto es mock, no denegación remota. Las tres funciones del contrato Python exacto del candidato y la función afectada de `test_security_flow.py` pasaron en Docker. El contrato se limita a fuentes incluidas: durante revisión se retiró una aserción que dependía de los dos archivos PostgREST WIP excluidos; no se presentan esos cambios como parte del candidato. El harness `tests/sql/h3_admin_quota_harness.sql` pasó dentro del paquete JIT de dos bases PG17 sintéticas; no hubo HTTP PostgREST ni escritura remota. Detalle, hashes y límites en [evidencia D04](../evidencia/h3req1_d04_onboarding_forbidden_2026-10-25.md).

## Suites Python de contrato

| Suite | Afirmaciones centrales leídas en el código | Componente y fixtures | Límite de resultado |
|---|---|---|---|
| `tests/test_admin_invite_edge_contract.py` | Allowlist de redirects/CORS, validación de proyecto y `apikey`, autorización antes del body, reserva antes de efecto de correo, lifecycle y gate protegido. | Edge `admin-invite`, RPC de invitación/gateway y workflow protegido; inspección estática y harnesses aparte. | No envía correo; el archivo de test demuestra aserciones, no el estado del deployment. |
| `tests/test_editorial_contract.py` | Cálculo de calidad, precedence de overrides, required fields, defaults, fallos cerrados y hash estable. | `scripts/shared/editorial_contract.py` y valores sintéticos. | Unit tests no prueban datos actuales de Pro. |
| `tests/test_h2_backfill_editorial_state.py` | Mapeo de payload, preservación de timestamps, dry-run, idempotencia, límite de proyecto y batching. | `h2_backfill_editorial_state.py`; fake DB/client. | No ejecuta el writer remoto durante esta documentación. |
| `tests/test_h2_client_evidence_docs.py` | Atestación privada sanitizada, mapeo a cliente y lenguaje de alcance. | Evidencia versionada sanitizada, matrices y estado. | No lee el documento privado del cliente. |
| `tests/test_h2_development_legacy_compat.py`, `test_h2_editorial_migration.py` | Compatibilidad pública legacy, publication/quality gates, RLS/grants, expand/contract y rollback guardado. | Migrations H2, documentos, fixtures SQL y rutas públicas. | Las aserciones estáticas/harnesses no prueban aplicación remota. |
| `tests/test_h3_admin_queue_ux_contract.py` | Filtros/facetas/paginación, publicación/availability, auditoría, preview y sesión/miembros. | UI Admin, BFF allowlist, RPC/migrations y navegación sintética. | No constituye una ejecución de PostgREST real. |
| `tests/test_h3_admin_onboarding_denial_contract.py` | Guard exacto de onboarding, mapeo `42501 -> 403`, harness Admin permitido/user denegado y sanitización BFF 403. | Migration candidata, wrapper de cuota, BFF y harness PG17. | Cuatro funciones pasaron en Docker. El harness PG17 se ejecutó en DB sintética separada; no acredita PostgREST ni Development. |
| `tests/test_h3_invitation_callback_contract.py`, `test_h3_mock_invitation_contract.py`, `test_h3_password_recovery_contract.py` | PKCE/callback server-side, token de un solo uso, fake inbox, idempotencia, recuperación y no exposición de link privado. | Pages BFF, Auth mock, templates y rutas onboarding. | El correo y Auth real no se ejercitan. |
| `tests/test_mfa_compatibility_contract.py`, `test_password_policy_contract.py` | Reglas de password, MFA server-mediated, assurance/AAL y normalización de error. | UI, BFF, SDK y fixtures Auth. | No verifica factores/cuentas remotas. |
| `tests/test_obsidian_context_state.py`, `test_requirement_client_source_validation.py` | Estado/versionado de autoridad, enlaces, plantilla y gate de fuente cliente/criterios. | `.context`, `.github/pull_request_template.md`, atestación sanitizada y `AGENTS.md`. | Test documental local; no crea aceptación cliente ni autorización remota. |

El cierre R178 declara 337 passed, 4 skipped y 1 warning en su suite de proyecto; no ofrece una correspondencia por test method a menos que el reporte de ese run la especifique. No presentar la cifra como resultado individual de cada fila. Durante este ciclo solo se ejecutan gates documentales/scanner/scope que reciban cambios, no estas suites funcionales.

## Suites de navegador

`tests/mobile_usability.spec.ts` y `tests/quality_audit.spec.ts` importan `@playwright/test`; el primero enfoca uso móvil y el segundo una auditoría de UI/calidad. La búsqueda en manifiestos raíz/web, rutas `playwright.config.*`, scripts y workflows de ambos checkouts no encontró configuración ni comando que los descubra. La ausencia queda comprobada dentro de ese alcance; no se infiere uso manual, externo o remoto ni ejecución. R178 G09 acredita solo los casos y viewports nombrados en su evidencia, no se atribuye por defecto a estos dos paths. Para ejecutarlos en el futuro, el responsable debe decidir un runner reproducible y revisar su permiso/entorno; no es evidencia de cobertura actual ni una brecha local sin investigar.

## Contrato unitario del catálogo público

`tests/h3_duration_parser.test.mjs` ejecuta once contratos sintéticos del parser compartido, incluidas equivalencias entre el texto y la aclaración parentética, suma de periodos distintos, fallback parentético, paréntesis incompleto y complejidad acotada. Pasó 11/11 en Docker; el stdout bruto de una corrida histórica 7/7 se conserva localmente fuera del PR y el resumen sanitizado está en el acta del ciclo H3REQ1. El test está incluido en #503; no reemplaza H3-UAT-059 ni valida filtros en un navegador real.

## Pipeline cases

| Suite | Contrato | Consumidor/datos | Resultado delimitado |
|---|---|---|---|
| `tests/test_harvester.py` | Cuatro checks de API live: precio, duplicados, instituciones piloto y salud PostgREST. El fixture requiere `RUN_SUPABASE_INTEGRATION_TESTS=1` y URL/key. | Consulta `/rest/v1/courses` e `/institutions`; no importa ni prueba `UniversalHarvester`. | R160: los cuatro casos quedaron skipped por no habilitar integración/credenciales. No es parser unitario ni resultado runtime; no se consultó Supabase live. |
| `tests/test_h2_pipeline_contract.py` | Gates, transiciones, persistencia/recuperación y seguridad entre workers. | Config/perfiles, código pipeline y SQL helpers. | Ver casos/assertions en la fuente; resultado histórico se limita a G03 R178. |
| `tests/test_h3req1_local_pipeline_walk.py` | Recorrido local FG1→workers y salidas/estados del flujo. | Fixture local y workers aislados por sus helpers. | No es un schedule ni run de proveedores reales. |
| `tests/test_fg2_bounded_run.py` | Validación de perfil/seeds, manifest, pacing, concurrencia, presupuesto, Retry-After, redirects/reintentos y parada 403/429. | `fg2_bounded_run.py`; transportes sintéticos. | Incluida en Docker focal 73/73 y regresión 145 passed; no abre red. |
| `tests/test_fg2_bounded_orchestration.py` | Rotación, preflight antes del origen, alcance de selección y resultados de institución. | Orquestador, perfiles y fixtures sintéticos. | Incluida en Docker focal 73/73 y regresión 145 passed; no consulta perfiles reales. |
| `tests/test_fg2_bounded_workers.py` | Rechazo de IDs ajenos al manifest y exclusión de las colas globales por cleansing, enrichment y sync. | Adaptadores sintéticos; IDs de tres estaciones. | Incluida en Docker focal 73/73 y regresión 145 passed; no ejecuta RPC remoto. |
| `tests/test_fg2_bounded_workflow.py` | Contrato YAML del input manual, default false, outputs, transmisión del manifest/digest y dependencia del guard main-only. | `.github/workflows/production_pipeline.yml`. | Suite local incluida en la regresión Docker de 172 casos; no ejecuta Actions ni habilita workflows. |
| `tests/test_h3req1_pipeline_discovery_boundaries.py` (R18 histórico; ausente en c0) | Suite de boundaries de discovery: esquemas/host/assets, sitemap, gates y circuit breaker. | `UniversalHarvester` y perfiles/respuestas sintéticos en el handoff R18. | Los 24 passed/1 warning son salida archivada; el módulo no existe en este checkout y no es ejecutable aquí. No acredita fuente, proveedor ni schedule remoto. |
| `tests/test_fase121_extractors.py` | Reglas declarativas de selectores, etiquetas, transforms y extracción por pilar. | Helpers/config Fase 121 y HTML fixture. | No demuestra calidad estadística del proveedor ni performance productiva. |
| `tests/h3req1_pipeline_postgrest_pg17_integration.py` | Ejercita workers actuales por HTTP local; discovery/checkpoint, staging, fallos 503 y recovery de cleansing/enrichment/sync, handoff persistido. | PostgREST + PostgreSQL 17.11 desechables, payloads sintéticos y proxy local. | R161 `run-r10.log` reporta PASS de fases y estado final 1/1/1/1. El log no conserva SHA del runner; resultado delimitado a ese corte local. No atribuirle G07 R51. |

### Corrida local FG2 acotada — 2026-11-09

El candidato `/tmp/h1req1-fg2-bounded-harvest-20261109`, base
`646f14afa845ea3200f40ce919e273f090059c63`, se validó en Docker con la imagen
local fijada `sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1`,
`--network none` y checkout read-only. Los tests focales pasaron **73/73** con
dos warnings. La regresión ampliada pasó **145 tests**, con un test deselected y
dos warnings. El excluido fue
`tests/test_fase09_10_pre_main_controls.py::test_db_sync_main_push_is_report_only_and_manual_apply_is_guarded`;
una ejecución anterior de ese caso falló por una expectativa de texto H2 ausente
en `.github/workflows/db-sync-to-pro.yml`, que permanece igual a HEAD y no forma
parte del diff FG2. No se convierte ese resultado en fallo del candidato FG2.

`scripts/security/scan_credentials.sh --tree`, compilación Python en memoria,
parseo YAML y `git diff --check` pasaron. La advertencia restante es deprecación
upstream PyPDF2 y cache pytest deshabilitada por montaje read-only. El dry-run
funcional usa solo IDs sintéticos: institución
`00000000-0000-0000-0000-000000000001`; staging
`40000000-0000-0000-0000-000000000091`; cleansed
`50000000-0000-0000-0000-000000000091`; enriched
`60000000-0000-0000-0000-000000000091`; course
`70000000-0000-0000-0000-000000000091`. URL:
`https://synthetic.h3.example/programs/analitica-aplicada`, SHA-256
`cc741735bd878822d09ac0756132ae2e4da1a50ef7b7b503467f2c5a3e26672d`; HTML
sintético SHA-256
`82d0ed446d6756f761c437105a1767338c45d35f793dba201221fb519f9d98c2`. El refresh mantiene el
mismo `course_id`, staging pasa a `pending` y luego `processed`, cleansing y
enrichment producen las filas fixture asociadas, sync termina `synced` y
conserva `Nombre editorial vigente` como `manual_override`. Todo es sintético;
no es el dry-run de la cohorte productiva ni una prueba de escrituras Pro.

No hubo llamadas a instituciones, DNS productivo, proveedores AI, Supabase,
Pro, GitHub ni Actions. Un error previo de referencia Docker y una invocación
que no localizó el test correcto no ejecutaron pruebas ni afectaron datos; los
resultados que se acreditan aquí son solo las corridas completadas con la
imagen local verificada.

El scope del checker local está fijado en
`.context/evidencia/h1req1_fg2_bounded_local_scope_2026-11-09.json`; identifica
las fuentes de este paquete y no es el manifest exacto de un PR ni concede
autoridad de ejecución.

#### Reanudación desde el clon íntegro del TL — 2026-11-09

Se retomó desde `/tmp/h1-tl-fg2-historial-20261109.IpjVdE/repo`,
`HEAD=c0f19bcec33ec84a82dfc06581311ec37452fc23`, base `desarrollo`
`c736336819bc0a927cc7224a053429e27433a748`. Docker con `--network none`:
suite FG2 focal **68 passed, 1 warning** en la imagen fijada
`sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1`,
con red deshabilitada y copia sanitaria read-only. La regresión exacta
(orquestación, límites, workers, workflow, pipeline walk, credenciales y
controles fase 09/10) dio **148 passed, 1 deselected, 1 warning**. Sin filtro
fue 148 passed/1 failed por
`test_db_sync_main_push_is_report_only_and_manual_apply_is_guarded`, cuya
aserción H2 no coincide con el workflow y test idénticos a HEAD c0f19b. Warning:
deprecación upstream de PyPDF2. La suite no incluye el módulo R18 ausente
`tests/test_h3req1_pipeline_discovery_boundaries.py`; sus 24 passed/1 warning
son solo evidencia histórica. El credential scan y el checker documental de
esta huella se repiten después de consolidar estas notas; no se afirma aquí un
resultado nuevo. No hubo conexión a fuentes, DB ni Pro.

La prueba nueva verifica que Playwright no recibe `page.goto` cuando el
harvester está en modo controlado y que todos los `page.goto` directos están
centralizados tras esa barrera. La suite sigue usando perfiles y respuestas
sintéticas; no es un run, un lote ni una prueba de URLs de Pro. FG3 y CA4
permanecen sin tocar.

#### Revalidación de identidad URL — 2026-11-09 17:16 Lima

Tras corregir la coincidencia canónica de URLs y el transporte del `course_id`
aprobado, Docker con `--network none`, imagen fijada
`sha256:bb30d6237846f120d39b7c9794f8eb0c938c69e8cc15e0e93d2ca03641a7ade1` y
checkout read-only dio **106 passed** en las seis suites FG2/pipeline/H2 que
cubren el delta. La regresión ampliada con credenciales y controles de fase
09/10 dio **169 passed, 1 deselected, 1 warning**. El deselected es la aserción
H2 antigua `test_db_sync_main_push_is_report_only_and_manual_apply_is_guarded`
(fallo ajeno reproducido contra archivos sin cambios); el warning es
deprecación PyPDF2. `scripts/security/scan_credentials.sh --tree` pasó en el
mismo Docker offline. Se reejecutó el self-test candidate-aware con
`.context/evidencia/h1req1_fg2_bounded_local_scope_2026-11-09.json`: PASS,
769/769 fuentes asignadas, 122/122 documentos activos alcanzables y 433/433
históricos enlazados. Estos resultados son locales/sintéticos y no sustituyen
una corrida, lote o preflight actual de Pro.

El self-test candidate-aware con manifest terminó PASS (769/769 fuentes
asignadas; 122/122 documentos activos; 433/433 históricos). La comparación
integral actual, desde git-archive c0 hasta este candidato, permanece FAIL
**349→349**, listas idénticas, SHA-256 ordenado
`7775152137258a7709396217c4e521d64a9f185f4dfc7ebfc513f8564ab64434`. Este
conteo corrige el 201→201 anterior, que no coincide con la salida íntegra
reproducible. El corte FG3 histórico **348→348** se conserva por separado.

#### Revisión de seguridad del diff FG2 — 2026-11-09 17:38 Lima

Codex Security scan `faa63933-92e9-495a-89e2-acc089e60bf7` revisó el diff del
clon TL desde `c0f19bcec33ec84a82dfc06581311ec37452fc23`, huella
`codex-security-snapshot/v1:sha256:1e7f6642443ed74216c03dff0899fa64327f6fcd608a3a63b775a8c00c1781b9`:
**0 hallazgos**, cobertura `complete`. Se revisaron las 18 rutas del diff: las
seis fuentes runtime del inventario y las doce restantes de workflow, suites y
fichas documentales. La disponibilidad de delegación fue `fail`; el parent
realizó la revisión completa. El informe está en
`/home/romel/.codex/state/plugins/codex-security/scans/repo/c0f19bcec33ec84a82dfc06581311ec37452fc23_20261109T222419Z_t3qfc9rb/report.md`.

La cobertura no incluyó producción, fuentes, credenciales, Environment efectivo
ni ejecución hosted. La revisión observó que las revalidaciones antialias leen
inventarios completos paginados varias veces; es un posible costo de lectura y
latencia cuya medida depende del lote y del tamaño real, no un finding de
seguridad de este scan. Las pruebas Docker/red-none **106 passed** y la
regresión ampliada **169 passed, 1 deselected, 1 warning** son evidencia local
separada. El checker candidate-aware PASS no elimina el **FAIL integral
349→349**; FG3 **348→348** permanece histórico. Sin push, PR, merge, promoción,
dispatch o escrituras Pro.

#### Revalidacion local FG2 CWE-400 — 2026-11-10

Sobre el candidato de FG2 en `/tmp/h1req1-fg2-approved-seed-selection-20261109`,
el transporte del GET controlado limita la respuesta acumulada a 2 MiB. La
prueba valida un cuerpo dentro del limite y una respuesta superior al tope sin
`Content-Length` confiable; el callback aborta y cierra el stream, evita
materializar/parsing del cuerpo completo y difiere el origen. La prueba de
orquestacion verifica que el exceso no crea filas staging. Una respuesta
chunked contra un servidor loopback sintetico comprueba que el receptor corta
la transferencia antes de que el servidor finalice. No se contactaron fuentes.

Docker Desktop, imagen fijada
`sha256:ebbf777792ee636179660638264c3d7b501f79e8efec731296d5ef41d07d18e6`,
`--network none`, checkout montado read-only: los casos focales dieron **6
passed, 27 deselected, 1 warning PyPDF2**; incluyen hardcoded y sitemap, con
respuesta oversized sin alta de staging. La regresion de nueve suites FG2,
gates main-only, pipeline walk y contrato de credenciales dio **223 passed, 1
warning**. El credential scanner reporto PASS; el test del protected-path
scope guard reporto PASS para las 1.196 rutas, 13 catalogos/1.173 destinos,
rechazo de vecinos y alcance invalido fail-closed. `bash -n` y `git diff
--check` tambien pasaron. El checker candidate-aware, tras renderizar las
vistas desde el JSON canonico, dio `DOC_GATE_PASS`: 769/769 fuentes, 122/122
documentos activos y 433/433 historicos. `actionlint` no esta disponible en
la imagen; los contratos YAML de los workflows se cubren por las suites
locales, sin afirmar un check de GitHub Actions.

Este resultado local no acredita un run, el control en main ni la ausencia de
hallazgos de seguridad del diff final. El FAIL integral **348→348, listas
identicas** permanece separado del PASS candidate-aware. Sin trafico a
instituciones, Pro writes, RPC, Actions mutativos, flags, Environment,
dispatch, schedules, push o PR.

#### Revisión por impacto FG2 ordinario y lote controlado — 2026-11-11

El dictamen sanitizado del revisor confirmó la base `c736336819bc0a927cc7224a053429e27433a748` y revisó estáticamente el candidato anterior de 35 rutas, SHA-256 `7bb2f49199e1e2d986c079fa342145a1869fd85dd96a611aac7eb51d57a8f0ba`. El scan reutilizado `371e1513-379a-4d05-820e-4d97da8ada21` fue standard sobre 1.847 archivos y cerró con cobertura general parcial de 6/9 unidades; cinco registros se deduplican en tres familias (SSRF, XSS y activación OpenCode por comentario). El dictamen fue **NO-GO** para FG2 ordinario/readiness H1. El diff local cambió después de esa revisión; no se atribuye al SHA actual su aprobación ni cobertura 35/35 del scanner.

El delta evaluado por pruebas atiende los tres bloqueos de implementación H1: (1) la ruta HTTP ordinaria valida/pinea destinos iniciales y cada redirect antes de la siguiente solicitud, y los sitemaps anidados y seeds de diagnóstico pasan por el mismo control; (2) `--controlled-first-run` exige `--skip-cleansing` y la delegación del manifest antes de seleccionar DB o workers; (3) enrichment y sync revalidan la URL y sus referencias contra el manifest antes del proveedor/writer. Los casos negativos de deriva URL conservan IDs/institución y demuestran parada anterior a efectos.

Revalidación del candidato actual: Docker `studiamatch-dev:local`, red `none`, filesystem del repo montado read-only. Cuatro suites FG2 y cuatro casos adicionales de harvester/diagnóstico dieron **94 passed, 1 warning** de deprecación PyPDF2. Incluye redirects privados sin segundo request, límites de presupuesto/rotación controlada, rechazo de lote derivado antes del worker, URLs downstream sustituidas, diagnóstico con cuerpo excesivo y redirects. No hubo solicitudes institucionales, llamadas a proveedores ni escrituras Pro. `test_noncontrolled_sitemap_does_not_apply_controlled_body_cap` confirma también un residual: el transporte HTTP ordinario aún recibe cuerpos sin el cap de 2 MiB; páginas Playwright tampoco tienen ese cap ni DNS pin de curl.

Lectura estática del YAML y selectores actuales (no evidencia remota): schedule FG2 cosecha hasta diez instituciones, pero no transmite el manifest. Cleansing reclama `staging_raw.pending` global en lotes de 100, `inst_id=NULL`, hasta el time guard y puede mover filas de instituciones no habilitadas a `skipped`; tras fallos RPC su fallback también consulta pending global. Enrichment y sync recorren sus propias filas `pending` de instituciones `pipeline_enabled`, no limitadas al lote cosechado. `discovered`, `processing` y `processed` no se reencolan automáticamente. Sin IDs no se infiere qué filas concretas consumiría una corrida. E10 permanece bloqueado hasta limitar y verificar ese recorrido; no se resetearon estados.

El scan general conserva dos hallazgos fuera del delta: XSS JSON-LD puede afectar una publicación H1 posterior y está fuera del allowlist CA1 (`web/**` prohibido); el hallazgo bajo del workflow OpenCode no es parte de FG2. No se modificaron esas rutas. La foto previa de UTEC es histórica: el prefijo vigente de rotación ofrece discovery-only; una excepción para refrescar las tres URLs observadas requiere decisión humana y una lectura Pro fresca antes de cualquier contacto. FG3 no se cambia: el owner conserva pendiente la decisión sobre la ventana lectura/PATCH TOCTOU. El FAIL integral FG3 **348→348, listas idénticas** sigue separado.

#### Corrección de P2 de Code Reviewer sobre lote manual y refresh ordinary — 2026-11-11

Code Reviewer evaluó el diff `f7aa2472…` y emitió NO-GO con dos P2: en `sitemap_bfs`, un seed manual de página podía enviarse al parser XML; y un alias de detalle como `/presentacion` podía clasificarse `new_discovery` aunque cleansing lo agrupa con un curso existente. Se agregaron pruebas RED para ambos casos. La primera regresión también detectó que un seed `.xml` real dentro de un lote no debía perder su parseo; se preservó ese camino separando los seeds de página de los de sitemap.

El candidato corregido pasó **167 pruebas** en Docker Desktop, imagen `studiamatch-dev:local` (`sha256:ebbf777792ee636179660638264c3d7b501f79e8efec731296d5ef41d07d18e6`), `--network none`, repo montado read-only. Incluye las seis suites de FG2, manifest/workers, workflow, controles main/manual y recorrido local del pipeline. Una advertencia de deprecación PyPDF2. No hubo red institucional, llamadas a proveedores ni escrituras Pro. El checker candidate-aware, ejecutado después de consolidar las adiciones documentales, dio `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`: 769/769 fuentes asignadas, 122/122 documentos activos y 433/433 históricos. El FAIL integral histórico `348→348`, listas idénticas, se conserva aparte; no se convierte en PASS. El Code Reviewer debe dictaminar todavía la huella final.

#### Regresión Code Reviewer FG2 — 2026-11-11

Sobre el NO-GO del diff `e22455c0…` se añadieron tres reproducciones: upsert de
`new_discovery` con inventario no vacío, deferral DNS antes de HTTP persistido
en manifest y presencia de las cuatro suites FG2 en el pytest efectivo de CI.
Las tres fallaron primero en Docker sin red y pasaron tras el arreglo local.
Luego seis suites de `fg2_bounded_run`, orquestación, workers, workflow,
controles pre-main y recorrido de pipeline dieron **169 passed, 1 warning** de
deprecación PyPDF2. El candidato se montó read-only y el contenedor usó
`--network none`; esto no acredita el CI remoto, las colas Pro ni ejecución
funcional. El checker documental candidate-aware pasó `DOC_SELF_TEST_PASS` y
`DOC_GATE_PASS` (769/769 fuentes, 122/122 documentos activos, 433/433
históricos), y el credential scan exacto de las 35 rutas pasó. El FAIL integral
`348→348` sigue separado.

#### Concurrencia de cleansing en FG2 — 2026-11-11

El Code Reviewer encontró que FG2 schedule y el caller cleansing de Production
Canary podían solaparse. Se añadió un test que compara el grupo root y la
política de cancelación de ambos YAML; falló con los grupos distintos y pasó al
asignar a los dos `studiamatch-fg2-${{ github.ref }}` y mantener
`cancel-in-progress: false`. Con esa corrección, las seis suites completas pasan
**170 passed, 1 warning** en Docker `--network none` y checkout read-only. Es un
contrato estático más regresiones sintéticas, no una simulación de scheduler
remoto ni un claim DB atómico. Tras las notas nuevas, `DOC_SELF_TEST_PASS`,
`DOC_GATE_PASS` (769/769 fuentes asignadas, 122/122 docs activos y 433/433
históricos), credential scan de 35 rutas y `git diff --check` pasaron. CI remoto,
colas actuales y E9 siguen pendientes.

#### Regresión Code Reviewer FG2 — 2026-11-11

Sobre el NO-GO del diff `e22455c0…` se añadieron tres reproducciones: upsert de
`new_discovery` con inventario no vacío, deferral DNS antes de HTTP persistido
en manifest y presencia de las cuatro suites FG2 en el pytest efectivo de CI.
Las tres fallaron primero en Docker sin red y pasaron tras el arreglo local.
Luego seis suites de `fg2_bounded_run`, orquestación, workers, workflow,
controles pre-main y recorrido de pipeline dieron **169 passed, 1 warning** de
deprecación PyPDF2. El candidato se montó read-only y el contenedor usó
`--network none`; esto no acredita el CI remoto, las colas Pro ni ejecución
funcional. Checker documental y credential scan del diff final quedan pendientes
tras consolidar el paquete; el FAIL integral `348→348` sigue separado.

### FG3 — candidato aislado y evidencia de seguridad

Se conserva sin edición el candidato
`/tmp/studiamatch-h1req1-20261108-source`, HEAD
`c736336819bc0a927cc7224a053429e27433a748`, diff SHA-256
`0252e5c96caf72881c8ccac7bcccf8ed2674d6a3c9fee401bb228b37b0aa7c7e`. Mientras
esa huella coincida, se reutilizan la suite focal **36 passed, 9 subtests** y la
regresión **90 passed, 1 deselected, 9 subtests**; el excluido
`test_f99_certification_canary_workflow_was_retired_for_h2_main_gate` no se
declara PASS. El candidato selecciona desde `courses_public_effective`, lee
`last_404_at` en `courses` solo por IDs seleccionados y mantiene las escrituras
permitidas exactas en `courses`. La evidencia no autoriza una corrida FG3.

El chequeo de seguridad del paquete conserva tres resultados separados: la
revisión manual identificó y corrigió el redirect privado/log sensible, y dejó
documentada la ventana de elegibilidad/PATCH; el credential scan local fue
PASS; el scanner gestionado de diff no emitió `scanId`, por lo que no hay un
resultado PASS que atribuirle. El gate versionado de promoción requiere PR con
una aprobación humana y check obligatorio `security-audit`; ese CI todavía debe correr
contra el PR exacto. No se sustituye por la revisión manual ni por el credential
scan local.

Antes de cada PATCH FG3 se vuelve a leer la vista pública para el ID y se hace
PATCH condicional por ID/estado activo/`last_404_at` esperado. Si el ID ya no
aparece en `courses_public_effective`, se omite; si el estado base cambió, el
PATCH condicional/reconciliación no acepta una fila distinta. Como consulta de
vista y PATCH no son atómicos, persiste una ventana TOCTOU estrecha entre ambas
llamadas. La limitación queda abierta y visible; cerrarla con garantía
transaccional requiere diseño/DDL/JIT separado, no inferible del test local.

El registro previo de comparación integral FG3 se corrige como
**FAIL 348→348, listas idénticas**, cero nuevos/cero resueltos, lista SHA-256
`738e442d6b13b3f604376a3f274747b8208f389fa3c2712e535d5fa015527a92`. Ese
resultado pertenece a la comparación documental registrada en el changelog;
no es PASS integral ni resultado del checkout FG2 actual.

## Canary contract suites

| Suite | Contrato/código inspeccionado | Datos/consumidor | Evidencia y límite |
|---|---|---|---|
| `tests/test_fase09_9_certification_canary.py` | Retiro de workflow F99, redacción de manifest, cohort selectivo, marca de filas y snapshot/restore | Fakes/contratos estáticos contra módulos F99 y gates locales; no conecta a Certification. | Tiene tests definidos; no hay run de esta suite acreditado en este corte. El test de credenciales clasifica identidad, no ejecuta canary. |
| `tests/test_fase09_10_pre_main_controls.py` | Ref exacta main-only, preflight fail-closed, guard antes de Environment/credenciales, dependencias de jobs y preservación de DB Sync | Lee workflows FG1/FG2/FG3, DB Sync y Production Canary; ejecuta los bloques shell del guard y preflight. | Incluida en Docker `--network none`: regresión agregada 172 passed con una advertencia PyPDF2. No es run de Actions ni prueba de adopción remota. |
| `tests/test_fase10_main_boundary.py` | Gate de promoción a main, no auto-aplicación DB y canary manual antes de schedules | Lee `security-audit.yml`, workflows programados y `production_canary.yml`. | Incluida en la regresión Docker de 172 tests; no certifica branch protection/configuración remota. |
| `tests/test_fase10_production_canary.py` | Workflow manual/SHA lock, host allowlist, sanitización, fakes de DB, snapshots/restores, idempotencia, fallos parciales y condición exacta main antes de Environment | Módulos `production_canary_*` y YAML local; datos sintéticos/fakes. | Incluida en la regresión Docker de 172 tests; no es canary remoto. |

Los cuatro paths son relaciones distintas y sus callers se listan en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#pruebas-y-evidencia). Una prueba definida confirma una relación test→contrato, no que la suite se haya ejecutado o pasado. Ninguno se ejecutó solo para documentar la ausencia de resultados.

## SQL harnesses, runners y fixtures

Los archivos SQL de pruebas están separados por el contrato que preparan o afirman; el workflow no ejecuta todos ellos automáticamente en cada evento. Las referencias siguientes se leyeron estáticamente en los runners, workflow y harnesses locales de ambos checkouts. En [Database](../database.md#baseline-fixtures-y-rollback) se detallan schema, datos sintéticos y límites frente a Pro. Un `psql -f`, `\ir` o `run_sql` es una relación de consumo, no prueba de que haya corrido en este corte.

### SQL harnesses H2

| Path | Contrato/consumidor | Datos y resultado | Cambio por impacto |
|---|---|---|---|
| `tests/sql/h2_pg17_harness.sql` | Fixture H2 para schema/compatibilidad y suite SQL; `.github/workflows/security-audit.yml` lo invoca con `psql -f` cuando el gate de DB detecta cambios `db/`. | PostgreSQL 17 local con roles/claims/tablas sintéticos; no replica permisos efectivos remotos. El resultado se toma de acta fechada, no del workflow YAML. | Si cambia el contrato H2, revisar migrations H2, el workflow del gate y `tests/test_h2_editorial_migration.py`. |
| `tests/sql/h2_pro_pg17_harness.sql` | Fixture de baseline H2-Pro; invocado en el mismo gate local de DB de `security-audit.yml`. | Fixtures Postgres desechables; no aplica SQL a Pro ni demuestra promoción. | Revisar su secuencia de `\ir`, la allowlist de migrations y la evidencia PG17 vinculada al cambio. |

### SQL harnesses H3 schema

| Path | Contrato/consumidor | Datos y resultado | Cambio por impacto |
|---|---|---|---|
| `tests/sql/h3_pg17_harness.sql` | Crea el schema H3 sintético. El workflow `security-audit.yml` lo invoca para los escenarios H3; `tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_once.sh` y sus variantes R2–R6 lo fijan como harness. | Emula `auth.uid()`/`auth.jwt()` y carga sub-harnesses de invitación/onboarding; no conecta a Auth/PostgREST remoto. R178 o el acta de la variante acreditan solo sus propios inputs. | Revisar migrations cargadas, seed local, fixtures incluidos y las cuatro rutas H3/Admin que dependen del schema. |
| `tests/sql/h3_from_h2_pro_pg17_harness.sql` | Bootstrap H2→H3 ejecutado desde `security-audit.yml` y vía `run_sql` en drills C03 integrados. | Estado sintético que prueba compatibilidad de secuencia; no prueba schema aplicado en Pro. | Renovar si cambia baseline, migraciones H2/H3, fixtures de cohorte o RPC consumidas por los drills. |
| `tests/sql/h3_pg17_harness_local.sql` | Variante local distinta del harness CI; la búsqueda del path en `tests/`, `.github/workflows/`, `scripts/` y sus callers no localizó runner automático en ninguno de los dos checkouts. | Define fixtures locales y transacción de prueba. No se encontró resultado fechado ligado a esta variante; no inferir ejecución por similitud con `h3_pg17_harness.sql`. | Mantener pendiente la identificación de su runner/uso manual antes de atribuirle cobertura; si cambia, revisar por separado de CI. |

### SQL Admin

| Path | Contrato/consumidor | Datos y resultado | Cambio por impacto |
|---|---|---|---|
| `tests/sql/h3_admin_quota_harness.sql` | Crea y comprueba funciones/tablas de cuota; invocado por `security-audit.yml` en escenarios de chain/contract y citado por C03. | Actores, límites y nonce sintéticos; no representa tráfico/estado remoto. | Revisar migraciones de cuota, BFF/DO y UAT PostgREST; renovar el harness PG17 asociado. |
| `db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql` | Ajusta únicamente la excepción de rol del lector onboarding para que el wrapper de cuota la convierta en HTTP 403; el harness verifica Admin permitido/user denegado. | Función SQL en bases sintéticas PG17; no consulta identidades remotas. | Aplicada y validada solo en el paquete JIT local consumido; Free/Development/PostgREST siguen sin ejecutar. Ver [evidencia D04](../evidencia/h3req1_d04_onboarding_forbidden_2026-10-25.md). |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | Comprueba wrapper allowlisted, firma y dispatch; lo consume `security-audit.yml` y los drills C03. | Claves/firma de prueba locales y SQL aislado; no provisiona el gateway remoto. | Cambios en wrapper, argumentos tipados, pre-request, HMAC o RPC requieren actualizar fixtures y casos de BFF. |
| `tests/sql/h3_invitation_edge_runtime_harness.sql` | Incluido con `\ir` desde `h3_pg17_harness.sql`; también enumerado por `tests/test_admin_invite_edge_contract.py`. | Schema/estados sintéticos de Edge y membresía; no envía email ni despliega Edge. | Mantenerlo alineado con reservation/compensation, contrato Edge y tests de invitación. |
| `tests/sql/h3_invitation_onboarding_harness.sql` | Incluido por `h3_pg17_harness.sql` y enumerado por el contrato Python de invitación. | Claims, invitación y onboarding sintéticos; no confirma Auth/correo reales. | Revisar migration de invitación, callback, política de password y RPC de miembros. |
| `tests/sql/h3_onboarding_rbac_hardening_harness.sql` | Incluido por `h3_pg17_harness.sql`; caso separado listado en el test de contrato Edge. | Estados/roles Admin locales; no verifica usuarios o grants remotos. | Renovar junto con migrations de RBAC/onboarding y sus assertions. |
| `tests/sql/h3_safe_suspend_harness.sql` | Invocado por `security-audit.yml` en ambos chains; contiene `\ir` de los rollbacks locales; C03 llama rollback por `run_sql`. | Prueba estado de suspensión/reanudación en fixture desechable; la capacidad de restauración requiere JIT si se dirige a servicio operativo. | Revisar forward migration + `db/rollback/*` + BFF, semántica de pausa y recuperación; el fixture no ejecuta restore remoto. |

### Primer Admin — candidato local 2026-11-05

| Path/runner | Contrato y entradas | Resultado en este corte | Límite y próximo gate |
|---|---|---|---|
| `tests/h3_first_admin_bootstrap_pg17.sh` + `tests/sql/h3_first_admin_bootstrap_pg17_harness.sql` + `tests/sql/h3_first_admin_bootstrap_harness.sql` | Fixture H2→H3 local, capas de cuotas y gateway firmado, migration bootstrap candidata; prueba callback firmado, cuota por solicitud, reserva ordinaria con token NULL y lifecycle de contraseña. | **PASS local PG17 sintético** para árbol de ejecución `20ca1593822c2d7e887877b5d1fffa103d2aceb0`, patch SHA-256 `bb8bb7af3fcbf94410e477bc44ee544abe374477654f51c7cc32e3b058f4a916`; marcador PASS, log SHA-256 `2002c6ee56ec19ba4b2377a4b9973b1993f6a47d389e363be6f028f2f4af75c2`, limpieza comprobada. | Una ejecución local autorizada; cubrió la DB sintética y no Pro, Auth real ni correo. Identidad del SQL/runner/harness se conserva tras la reconciliación documental. |
| `tests/test_h3_first_admin_bootstrap_contract.py` + `tests/test_h3_pro_migration_manifest.py` | Contrato estático del identity gate, callback existente, safe-suspend, cuotas/gateway, manifest y wiring del harness. | **PASS 9/9 en Docker** después de calificar las lecturas ambiguas del harness; un warning de pytest cache proviene del mount read-only. | Static/source tests only; no acredita PostgreSQL, Auth ni Pages runtime. |

El TL confirmó que `20260919_h3_invitation_auth_token_delta` permite `token_hash=NULL` en reservas ordinarias antes de la entrega Auth. El primer borrador que exigía hash fue corregido; el candidato no altera esa columna. La reserva ordinaria con token NULL y el rechazo de creador nulo sin provenance se probaron en el harness local. También se eliminó la doble entrada local al lifecycle: una solicitud externa alcanza una sola llamada envuelta por cuota. El runner usa imagen fijada por digest, red `none`, fuente read-only y datos efímeros. El contrato estático + manifest pasó 9/9 y la suite completa del guard pasó en Docker; allowlist y workflow permanecieron intactos. La ejecución PG17 autorizada para árbol `20ca1593822c2d7e887877b5d1fffa103d2aceb0`/patch `bb8bb7af3fcbf94410e477bc44ee544abe374477654f51c7cc32e3b058f4a916` terminó PASS y se limpió el contenedor. Los intentos fallidos anteriores quedan como historia; no prueban fallo de producto. Este fixture no acredita Pro, Auth real, invitación/correo ni runtime remoto.

### SQL PostgREST wire

| Path | Contrato/consumidor | Datos y resultado | Cambio por impacto |
|---|---|---|---|
| `tests/sql/h3_quota_postgrest_fixture.sql` | Cargado por `security-audit.yml` antes de la prueba wire de cuota. | Funciones, roles y claves locales en `h3_pro_chain_gate`; no son secretos de ambiente. | Revisar dependencia `h3_admin_rpc_signed_gateway_harness.sql` y el cliente UAT PostgREST. |
| `tests/sql/h3_quota_postgrest_assert.sql` | Ejecutado por el workflow después de `tests/h3_admin_quota_postgrest.mjs`. | Assertions sobre filas/resultado de PostgREST local; los éxitos se acreditan por log fechado, no por YAML. | Cambiar junto con respuesta wire, RPC, fixtures y prueba JS. |
| `tests/sql/h3_invitation_reservation_concurrency.sh` | El workflow lo ejecuta con `PGHOST/PGDATABASE` locales y lo pasa también por ShellCheck. | Test de concurrencia/locks con datos sintéticos en `h3_gate`; nunca supone Auth/correo reales. | Renovar si cambia reserva, índice único, compensación o código de retry; preservar el resultado del run específico. |

### Fixtures UAT

| Path | Contrato/consumidor | Datos y resultado | Cambio por impacto |
|---|---|---|---|
| `tests/sql/h3_uat_functional_catalog_seed.sql` | Seed sintético de catálogo/curso ejecutado manualmente en el PostgreSQL 17 desechable del ciclo local para `H3-UAT-058/059`; no hay inclusión automática en workflows ni invocación del seed desde el runner. | Escribe exclusivamente fixtures de prueba al ejecutarse. El curso sintético 13 usa duración `6 meses (24 semanas)` y modo Híbrido; el fixture de pipeline se publica solo con evidencia sintética vigente dentro del máximo de 90 días. | El seed requiere schema en el PostgreSQL 17 desechable `h3_final_uat_20261024_058059`; la ejecución registrada se detuvo en la guarda de elegibilidad de pipeline antes del cierre del seed. No se ejecutó en Supabase ni en otra base de producto. Los resultados históricos 058/059 no cubren el delta actual del parser. |
| `tests/sql/h3_uat_pipeline_course_seed.sql` | Seed de curso/pipeline sintético; no se localizó caller exacto en los mismos scopes locales. | Define salida de fixture, no resultado de pipeline. | Mantenerlo aislado del writer y del catálogo reales; resolver runner antes de cambiarlo. |
| `tests/sql/h3_uat_synthetic_identity_fixup.sql` | Ajusta identidades sintéticas de fixture; no se localizó caller exacto en los scopes locales. | Efecto DML sobre filas de test; no ejecutar fuera de fixture desechable. | Revisar el fixture que lo prepara, identidad referenciada y evidencia antes de modificar. |

La búsqueda de callers automáticos cubre los dos árboles locales, workflows y scripts: los otros dos seeds de esta tabla no tuvieron runner identificado en este ciclo. El catálogo se cargó manualmente solo en el PG17 desechable indicado; no infiere ejecución remota ni uso por una ruta productiva.

### SQL C03 integrado

| Path | Contrato/consumidor | Datos y resultado | Cambio por impacto |
|---|---|---|---|
| `tests/sql/h3req1_c03_integrated_setup.sql` | Preparación de estado sintético; `tests/h3req1_c03_integrated_runtime.mjs` carga su contenido y los drills llaman `run_sql`. | Cohorte aislada de C03; no acredita comportamiento actual sin acta del run. | Cambios de schema/estado requieren renovar setup, snapshot y asserts conectados. |
| `tests/sql/h3req1_c03_integrated_extension_setup.sql` | Setup inicial del gateway/cuota, consumido por el drill base y diagnóstico R10. | DDL local de fixture; no activar el hook remoto. | Revisar migraciones EXPAND y la versión del contrato que el drill reproduce. |
| `tests/sql/h3req1_c03_integrated_extension_setup_r10.sql` | Variante R10 del setup; solo consumidores que citan explícitamente `r10`. | Setup de fixture fechado; no equivale a la configuración vigente. | Mantener como historial del drill y actualizar su manifiesto junto con el runner. |
| `tests/sql/h3req1_c03_integrated_extension_setup_r11.sql` | Variante R11 invocada por su drill; distinta de R10/R12/R13. | DDL de fixture y estado sintético versionado. | No mezclar con el setup más reciente al reconstruir un run antiguo. |
| `tests/sql/h3req1_c03_integrated_extension_setup_r12.sql` | Setup R12 consumido por el drill R12. | Fixture de una iteración histórica. | Reproducir solo desde su manifest/acta, no como setup general vigente. |
| `tests/sql/h3req1_c03_integrated_extension_setup_r13.sql` | Setup R13 consumido por variantes C03 posteriores que lo nombran. | Fixture versionado, no prueba de despliegue. | Cambiarlo exige actualizar los drills vinculados y sus digests nuevos; no editar hashes sellados. |
| `tests/sql/h3req1_c03_integrated_assert_inflight.sql` | `run_sql` antes del hold de Auth en drills integrados. | Verifica reserva/estado sintético previo a suspensión. | Mantener las invariantes transaccionales con la fuente del estado y su informe. |
| `tests/sql/h3req1_c03_integrated_assert_suspended.sql` | Assertion de ACL/datos/cuota/auditoría desde drills. | Test local de estado pausado; no mide grant remoto. | Renovar al cambiar pausa, ACL, ledger o cuota. |
| `tests/sql/h3req1_c03_integrated_assert_completed_suspended.sql` | Assertion de finalización concurrente durante suspensión. | Caso sintético para carrera de finalizer; requiere salida del run para acreditar. | Revisar finalizer, transición idempotente y locks. |
| `tests/sql/h3req1_c03_integrated_assert_recovered.sql` | Assertion de recuperación posterior a reanudación. | Datos de fixture; no acredita recovery remoto. | Revisar rollback, acceso restaurado y auditoría. |
| `tests/sql/h3req1_c03_integrated_assert_final.sql` | Assertion final de idempotencia, cuota y auditoría. | Resultado local del último paso del drill. | Revisar el conjunto completo de assert previos y manifest del drill. |

Los callers de las variantes se registran por path en el [registro canónico](../trazabilidad/registro_fuentes_componentes.md#pruebas-y-evidencia). Los logs/manifiestos de cada R permanecen en sus directorios fijados y solo acreditan los paths/digests que contienen. La revisión R11 separa, por grupo, imports/llamadas, datasets, permisos, assertions definidas y outputs localizados o ausentes en [resolución de relaciones](../evidencia/h3req1_sem_resolucion_relaciones_locales_2026-10-13_r11.md#diagnosticos-c03-inputs-y-retencion); una mención en un manifest no se trata como ejecución.

### SQL pipeline PG17

| Path | Contrato/consumidor | Datos y resultado | Cambio por impacto |
|---|---|---|---|
| `tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql` | Montado read-only como `/fixture/setup.sql` por `run_h3req1_pipeline_postgrest_pg17_r1.sh`. | Crea fixture local para PostgREST/PG17; nunca apunta a Pro. | Cambiar junto con su runner, imagen fijada y suite Python de persistencia. |
| `tests/sql/run_h3req1_pipeline_postgrest_pg17_r1.sh` | Crea el runtime PG17/PostgREST desechable y monta el setup anterior; one-off por nombre. | El runner puede crear/parar un contenedor; no se ejecuta para documentar. Resultado solo con acta/manifiesto R1. | Antes de tocar, revisar Docker target, mounts, red, manifest SHA y recuperación. |
| `tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql` | Montado read-only como `/fixture/pipeline.sql` por el runner de persistencia. | Fixture de estado y fallos sintéticos para requeue/recovery. | Relacionar con locks y estado por worker, no con datos operativos. |
| `tests/sql/run_h3req1_pipeline_persistence_recovery_pg17_r1.sh` | Runner PG17 desechable que monta la fuente anterior. | Puede crear/parar recursos Docker; no se ejecuta en esta transferencia. | Revisar JIT Docker, image digest, mounts y manifest antes de invocar. |
| `tests/sql/run_fase10_8_atomic_cleansing_postgres.sh` | Runner aislado de atomic cleansing y provenance, consumido por las actas PG17 de esa fase. | Crea el entorno/fixture indicado por el script; no se afirma resultado aquí sin el acta coincidente. | Renovar junto con atomic promotion, schema y evidencia por input. |

Antes de cambiar un objeto SQL, recorre migration → harness/setup → assertion/runner → RPC y consumidor UI/Edge. Los harnesses nombrados como inputs no prueban que se hayan ejecutado en este corte; los resultados PG17 requieren su evidencia fechada exacta.

## Diagnósticos de transferencia C03

Los 124 paths de transferencia se asignan por responsabilidad en el [registro](../trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente): diagnóstico de fase Docker/WSL (2), despacho/cutover y cleanup Docker (7), auditoría npm y sus clasificadores (9), par tmpfs (4), wrappers actionlint (6), wrappers ShellCheck (6), wrappers TypeScript (5), runners WSL/otros (28), clasificadores/probes de salida (26), tests de contrato sintéticos (14) y helpers de lectura/clasificación (17). Los paths exactos de cada grupo viven en el JSON canónico; esta ficha explica el contrato compartido sin sustituir esa asignación.

Los runners de actionlint, ShellCheck, TypeScript y los probes WSL consumen los clasificadores o scripts del mismo subárbol según las rutas declaradas en cada wrapper. La relación de llamada se sigue comprobando por path: los hallazgos por nombre también incluyen referencias de hash, allowlist, test y log, que no cuentan automáticamente como caller. No se atribuye PASS por la existencia de un runner o un artefacto.

Los `docker_candidate_dispatch_v2/v3.sh` leen las fuentes fijadas, crean un contexto temporal bajo `/tmp`, generan un manifiesto de entrada, preparan una imagen y ejecutan Compose; al terminar pueden borrar el contexto/manifiesto temporales y retirar `node-deps`. Los wrappers `docker_candidate_cutover_v4/v5.sh` validan la configuración Compose antes de modificar el entorno local. `docker_candidate_cleanup_v6.sh` tiene rutas de eliminación de recursos protegidas por checks de propiedad/hash. Ninguno se ejecutó en esta transferencia. Revisar inputs, mounts, identidad del daemon, recursos existentes y alcance de borrado antes de una autorización separada.

Los clasificadores y tests sintéticos validan salidas acotadas de diagnóstico. No prueban la aplicación StudIAMatch, no sustituyen los contratos funcionales R178/R181/R182 y no acreditan que un servicio remoto o runtime local estuviera disponible. La investigación por path y sus alcances están en la [resolución local R11](../evidencia/h3req1_sem_resolucion_relaciones_locales_2026-10-13_r11.md); los resultados de cada intento C03 conservan su propio input-manifest y no se consolidan en un PASS nuevo.

## Diagnósticos y fixtures C03

Los 196 paths de diagnóstico se desglosan en ocho capacidades: configuración bootstrap/dependencias (3), identidad/proyección Docker (6), transporte Edge y lock resolver (12), launchers del drill integrado (53), tests de contrato integrados (48), helpers runtime integrados (5), helpers diagnósticos auxiliares (12), atomicidad editorial PG17 desechable (7), snapshots de fuentes (19) y probes de startup/recuperación (31). La ficha no eleva estos scripts a rutas de producto ni a jobs CI. Dos locks y dos overrides Compose se registran en grupos propios; el subtotal completo de estas familias es 324 paths.

El drill integrado enlaza runners `.sh`, tests de contrato `.test.mjs`, helpers Pages/Worker/PostgREST y harnesses SQL sintéticos. Para un cambio, localizar en el registro el path exacto, su pareja runner/test si existe, el manifest de inputs y el resultado fechado. Un log o hash suelto no prueba que el test pasara; el resultado R178 R51 128/128 solo se atribuye al conjunto nombrado en su acta. La familia no debe ejecutarse contra credenciales operativas.

El bootstrap Node/Deno tiene `package.json` y lock NPM sin scripts publicados, más `deno.json`, que selecciona `./deno.lock`. El archivo `deno-edge-runtime-v1.74.3-r2.lock` no tiene referencia en la configuración ni consumidor local demostrado en el alcance de búsqueda de ambos checkouts; queda preservado como snapshot de dependencias sin uso acreditado, no se borra ni se presenta como lock activo. Los locks identifican dependencias, no instalación ni resultado de runtime.

## Configuración de entornos diagnósticos

Los dos YAML bajo `.context/operaciones/h3req1_docker_candidate_*override_2026-10-09.yml` tienen consumidores estáticos en `docker_candidate_dispatch_v2/v3.sh` y `docker_candidate_cutover_v4/v5.sh`. La forma declarada incluye servicios `node-deps` y `app`, mounts/volúmenes y configuración de puertos; el checker y esta revisión no muestran valores operativos. Los wrappers pueden crear/reconstruir contenedores y borrar recursos temporales o servicios del proyecto local; por ello la relación de datos/configuración se limita a sus claves/estructura, sin afirmar hosts efectivos, mounts resueltos ni ejecución. Se preservan los recursos Docker existentes y no se lanza Compose.

El alcance histórico de búsquedas, las limitaciones de callers y los paths sin historia local se detallan en [evidencia semántica C03](../evidencia/h3req1_relaciones_semanticas_c03_2026-10-13.md). La adopción del runtime, de bindings o de cualquier destino remoto es exclusivamente verificable en una lectura futura autorizada; no se infiere de los YAML, scripts o logs locales.

Los archivos `.context/operaciones/h3req1_docker_candidate*_override_2026-10-09.yml` están relacionados como `c03-docker-overrides`. Las referencias estáticas los conectan con los wrappers `docker_candidate_dispatch_v2/v3.sh` y `docker_candidate_cutover_v4/v5.sh`; esos wrappers pueden crear, reconstruir o sustituir recursos Docker. Se inspeccionó la estructura YAML declarada (servicios, imágenes, puertos, override de env-file y mounts/volúmenes), pero no se copiaron valores, resolvieron interpolaciones/mounts ni aplicaron los Compose. Por eso los valores efectivos y bindings del daemon no están verificados y los overrides no se ejecutaron. La evidencia y el manifiesto fijados por cada wrapper se preservan como historia, sin copiar sus hashes a esta ficha.

El lock `tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock` y `.gitkeep` son salida/sentinel del resolver R3, no fuentes mantenidas. Los integrated drills los consumen al construir snapshots; su retención, inputs y límite probatorio están en la tabla de artefactos del [registro](../trazabilidad/registro_fuentes_componentes.md#artefactos-generados-fixtures-y-evidencia). El script productor contiene preflight Docker/JIT y no se ejecutó. Las versiones R2/R3 no se mezclan ni una reemplaza a la otra por nombre.

## Artefactos y evidencia generada

| Familia | Productor/inputs acreditados | Retención y límite |
|---|---|---|
| `web/tsconfig.tsbuildinfo` | Cache incremental de TypeScript según `web/tsconfig.json`; usa config y fuentes TS | Preservar durante la transferencia. Se puede recrear con typecheck/build; su presencia no acredita ninguno. |
| `.context/operaciones/h2_main_production_expand_evidence.json` | DB Sync to Production #99 (`42170267471`), evidencia autenticada para C `17d2d9b57fe9e5f32430a83ec843a3c3df9baa3b`, manifest `h2-expand-compat` | JSON auténtico del artifact `13481325792`, SHA-256 `7082bb5a19f08a10f56cfb0d1198bb38021d575d05e18c144f81e799aed252f9`; dispatch real `verify`, aunque el esquema conserva `operation=apply`; Report 90 aplicadas/0 pendientes, Apply NO-OP, migraciones SKIPPED y Verify SUCCESS | Artefacto exacto que consume `h2-main-production-expand-gate` | Preservar byte por byte en la ruta exacta. No editar el label histórico ni incluir ZIP/advisor bodies. Renovar solo mediante workflow autenticado y decisión/JIT propios. | El gate valida run/ref/SHA, jobs, manifest, cohorte y advisors; esta evidencia acredita H2, no el ledger/Apply/Verify H3 ni runtime Admin. |
| `tests/h3req1-c03-edge-lock-output-r3/**` | Resolver R3 fechado, fixture `deno.json`, fuente Edge y Deno image declarada por el script | Preservar el lock y sentinel. Bytes/manifiestos no acreditan nueva ejecución ni éxito de los drills. |
| `.context/evidencia/**`, `tests/**/*.sha256`, logs y capturas | Suites/runners y ciclos fechados, según cada manifest | Preservar rutas y hashes consumidos. Cada resultado se restringe a inputs, entorno y fecha de su acta. |
| Snapshots `.context/evidencia/**/web/.next/**` | Next.js dentro de snapshots locales G08/G09; fuentes/config/lockfiles identificados por acta | 4,422 outputs no-cache preservados como build histórico; no acreditan build actual/deploy. 283 `.next/cache` se excluyen del checkpoint filtrado. |
| Copias `.context/evidencia/**/vendor/braces-3.0.4-h3.1.tgz` | Empaquetadores de contextos históricos; tarball vendorizado fijado en lock | 10 copias de dependencia excluidas del checkpoint filtrado; originales y checkpoint previo se preservan. |
| Tarballs `source-candidate-r2/r3.tar` de G08 | Captura de fuente R2/R3; cada uno contiene la dependencia braces | Dos snapshots preservados en candidato/checkpoint supersedido y excluidos del checkpoint filtrado; no modificar evidencia sellada. |

El índice por path, componente, ficha/anchor, referencias y estado está en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente). La tabla de familias evita tratar miles de logs, snapshots o capturas como componentes independientes.

### Guardia de modo del lote manual FG2 — 2026-11-11

El Code Reviewer del diff previo 3d66cb01… encontró que el validador
controlled_first_run aceptaba un evento schedule en main cuando recibía la
huella del lote manual. La regresión
tests/test_fg2_bounded_run.py::test_controlled_first_run_requires_manual_dispatch_on_main
reprodujo el fallo en Docker --network none; tras la guarda, confirma que solo
workflow_dispatch en refs/heads/main entra en ese modo y que schedule y
refs/heads/desarrollo se rechazan. El modo scheduled_cohort conserva su
contrato schedule/main.

La regresión focal final de siete suites en Docker --network none dio
181 passed, 10 subtests passed y 1 warning de deprecación PyPDF2. Es evidencia
local offline, no una corrida de Actions ni una lectura de Pro. El Code Reviewer
y el checker documental candidate-aware deben cerrar sobre la huella final.

### Presupuesto y alias de identidad FG2 — 2026-11-11

El Code Reviewer del diff anterior c603b3fd… identificó tres P2: sitemap
partial persistido como discovered sin poder entrar al manifest; URL `/en/`
equivalente no encontrada por el lookup schedule; y un seed `/presentacion`
del lote manual sin enlace al course_id del padre.

Cada regresión se ejecutó primero contra el candidato anterior en Docker
`--network none` y falló; tras el cambio pasa: el crawler no crea candidatos
descubiertos cuando ya está deferred/blocked por presupuesto, el schedule
resuelve aliases de URL al mismo course_id, y el snapshot revisado permite
guardar la URL detail junto con el URL/id/estado real del curso padre. También
se rechaza un lote con dos entradas que derivan a la misma identidad. Las siete
suites focales dieron 185 passed, 10 subtests passed y una advertencia de
deprecación PyPDF2. El número de hijos downstream no se infiere de las 100
entradas máximas: requiere el manifest y las relaciones del run Pro.

Resultado local offline; no acredita Pro, fuentes, E9, E10 ni ejecución
funcional. El candidato actualizado requiere checker candidate-aware y nuevo
Code Reviewer sobre la huella completa.

### Alias almacenado y resultados parciales FG2 — 2026-11-11

El Code Reviewer del SHA `03d52e43…` detectó que el lookup no incluía cursos
almacenados con sufijo de detalle y que una falla no bloqueante posterior a una
URL exitosa podía saltarse downstream. Las nuevas regresiones reprodujeron
ambos casos en Docker sin red. La búsqueda incluye URL solicitada, identidad
normalizada y sufijos de detalle conocidos, y falla si el regex encuentra más
de una fila. Una corrida con resultados mixtos registra `partial` y permite a
los tres workers continuar únicamente con entradas exitosas del manifest; cada
worker mantiene los filtros por staging IDs/foreign keys, estado e institución.
Una corrida sin entradas exitosas sigue fallando. El marcador de harvest solo
avanza la rotación; no prueba refresh.

Seis suites FG2/pre-main/pipeline: **187 passed, 1 warning** de deprecación
PyPDF2 en Docker `--network none`, candidato read-only. Los 10 casos focales
nuevos pasan; antes, cuatro configuraciones de alias/partial fallaban con
fixtures. El snapshot de IDs Pro no forma parte de esta evidencia y la cantidad
de filas downstream depende de las relaciones del manifest real. El Code
Reviewer, checker documental y escaneo de credenciales del SHA nuevo siguen
pendientes.

## Navegación histórica local

Evidencia preservada por proceso; cada catálogo enlaza sus documentos históricos individualmente y no es una autoridad operativa.

- [C03 integrado: sesiones, invitación y recuperación](../catalogos_historicos/c03_integrado.md#documentos-preservados)
- [Admin, autenticación e historia editorial](../catalogos_historicos/admin_auth_editorial.md#documentos-preservados)
- [Frontend público y UAT](../catalogos_historicos/frontend_publico_uat.md#documentos-preservados)
- [Pipeline, datos y base de datos](../catalogos_historicos/pipeline_base_datos.md#documentos-preservados)
- [Infraestructura, seguridad y CI](../catalogos_historicos/infra_seguridad_ci.md#documentos-preservados)
- [Documentación, trazabilidad y transferencia](../catalogos_historicos/documentacion_trazabilidad.md#documentos-preservados)
- [Registros operativos históricos y JIT](../catalogos_historicos/operacion_jit.md#documentos-preservados)
- [Evidencia histórica de requerimientos e hitos](../catalogos_historicos/requerimientos_hitos.md#documentos-preservados)
- [Seguimiento y handoffs históricos](../catalogos_historicos/seguimiento_historico.md#documentos-preservados)
- [C03 — diagnóstico de arranque de runtimes locales](../catalogos_historicos/c03_inicio_runtime.md#documentos-preservados)
- [C03 — snapshots y preflight de fuentes](../catalogos_historicos/c03_snapshot_fuentes.md#documentos-preservados)
- [C03 — diagnósticos Docker, F1 y clasificadores](../catalogos_historicos/c03_diagnosticos_runtime.md#documentos-preservados)
