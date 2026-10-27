# Componente: pruebas y evidencia

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
| `tests/test_h3req1_pipeline_discovery_boundaries.py` | `test_discovery_accepts_web_schemes_for_the_configured_host`, rechazos de esquemas/host/assets, sitemap ausente/malformado, gates y circuit breaker. | `UniversalHarvester` y perfiles/respuestas sintéticos. | Handoff R18 reporta 24 passed/1 warning con hashes de suite; no acredita una institución, proveedor ni schedule remoto. |
| `tests/test_fase121_extractors.py` | Reglas declarativas de selectores, etiquetas, transforms y extracción por pilar. | Helpers/config Fase 121 y HTML fixture. | No demuestra calidad estadística del proveedor ni performance productiva. |
| `tests/h3req1_pipeline_postgrest_pg17_integration.py` | Ejercita workers actuales por HTTP local; discovery/checkpoint, staging, fallos 503 y recovery de cleansing/enrichment/sync, handoff persistido. | PostgREST + PostgreSQL 17.11 desechables, payloads sintéticos y proxy local. | R161 `run-r10.log` reporta PASS de fases y estado final 1/1/1/1. El log no conserva SHA del runner; resultado delimitado a ese corte local. No atribuirle G07 R51. |

## Canary contract suites

| Suite | Contrato/código inspeccionado | Datos/consumidor | Evidencia y límite |
|---|---|---|---|
| `tests/test_fase09_9_certification_canary.py` | Retiro de workflow F99, redacción de manifest, cohort selectivo, marca de filas y snapshot/restore | Fakes/contratos estáticos contra módulos F99 y gates locales; no conecta a Certification. | Tiene tests definidos; no hay run de esta suite acreditado en este corte. El test de credenciales clasifica identidad, no ejecuta canary. |
| `tests/test_fase09_10_pre_main_controls.py` | Fail-closed de preflight previo a main, writers pausados antes de mutaciones y protección DB sync/manual apply | Lee workflows FG1/FG2/FG3, DB sync y production canary por path/símbolos. | La búsqueda exacta en `.github/workflows/` de ambos árboles no encontró un runner de esta suite; no atribuirle PASS. |
| `tests/test_fase10_main_boundary.py` | Gate de promoción a main, no auto-aplicación DB y canary manual antes de schedules | Lee `security-audit.yml`, workflows programados y `production_canary.yml`. | Contrato estático local; no certifica branch protection/configuración remota. No se acreditó ejecución en este ciclo. |
| `tests/test_fase10_production_canary.py` | Workflow manual/SHA lock, host allowlist, sanitización, fakes de DB, snapshots/restores, idempotencia y fallos parciales | Módulos `production_canary_*` y YAML local; todos los datos de pruebas son sintéticos/fakes. | Suite amplia de contrato local, no run remoto. No se ejecutó de nuevo porque sus inputs no cambiaron en este ciclo documental. |

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
| `.context/operaciones/h2_main_production_expand_evidence.json` | Evidencia operativa histórica fuera de `.context/evidencia`; contenido no leído | Preservar en su ruta. No se presenta como estado remoto actual ni se incorpora al paquete sin revisión sanitizada. |
| `tests/h3req1-c03-edge-lock-output-r3/**` | Resolver R3 fechado, fixture `deno.json`, fuente Edge y Deno image declarada por el script | Preservar el lock y sentinel. Bytes/manifiestos no acreditan nueva ejecución ni éxito de los drills. |
| `.context/evidencia/**`, `tests/**/*.sha256`, logs y capturas | Suites/runners y ciclos fechados, según cada manifest | Preservar rutas y hashes consumidos. Cada resultado se restringe a inputs, entorno y fecha de su acta. |
| Snapshots `.context/evidencia/**/web/.next/**` | Next.js dentro de snapshots locales G08/G09; fuentes/config/lockfiles identificados por acta | 4,422 outputs no-cache preservados como build histórico; no acreditan build actual/deploy. 283 `.next/cache` se excluyen del checkpoint filtrado. |
| Copias `.context/evidencia/**/vendor/braces-3.0.4-h3.1.tgz` | Empaquetadores de contextos históricos; tarball vendorizado fijado en lock | 10 copias de dependencia excluidas del checkpoint filtrado; originales y checkpoint previo se preservan. |
| Tarballs `source-candidate-r2/r3.tar` de G08 | Captura de fuente R2/R3; cada uno contiene la dependencia braces | Dos snapshots preservados en candidato/checkpoint supersedido y excluidos del checkpoint filtrado; no modificar evidencia sellada. |

El índice por path, componente, ficha/anchor, referencias y estado está en el [registro verificable](../trazabilidad/registro_fuentes_componentes.md#asignaciones-por-fuente). La tabla de familias evita tratar miles de logs, snapshots o capturas como componentes independientes.

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
