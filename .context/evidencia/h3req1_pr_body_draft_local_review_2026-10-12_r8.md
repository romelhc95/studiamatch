# Borrador del cuerpo PR H3REQ1 — plantilla versionada — 2026-10-12 R8/R182

Documento local para revisión del responsable; **no se creó PR**. Sigue las diez secciones de `.github/pull_request_template.md`. R8/R182 preserva R7/R6, conserva el test protegido y cierra la preparación local del bootstrap CI en dos etapas. R7 encontró seis rutas fuera del allowlist y permisos innecesarios en Stage 2; R180 corrige las rutas con entradas exactas y limita el waiter a bases protegidas tras instalar PWI. La revisión independiente de contenido R8/R181 y la verificación read-only de pins R8/R182 devolvieron PASS, sin HIGH/CRITICAL ni bloqueos, y confirmaron los 250 archivos del paquete. G10 remoto no se presenta como ejecutado; este borrador no es un PR.

## Resumen

Implementación H3REQ1 para edición y procedencia editorial, auditoría, publicación por evidencia de disponibilidad, membresías/invitaciones, BFF HttpOnly, MFA/RBAC, gateway RPC firmado y cuotas. Este cuerpo resume evidencia local sintética; no representa aceptación remota.

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`; HEAD no identifica el WIP.
- Estado vigente: [cierre local H3REQ1 R181/R182](../estado_del_proyecto.md), con G10 remoto explícitamente pendiente.
- Manifiesto de contenido R8: [manifest de alcance](h3req1_pr_scope_manifest_2026-10-12_r8.json), SHA-256 `b3dbc3e7c1e2702d06100fb52b1c4c6663d2444b1a76ed456de1a07caaed6d87`; scope digest `c507a3708d854904419ddb55bee9198d45a5bf1fad17a8c9d09a92c737a514e9`; evidencia digest `4134fd9fcd6f3fd1cc6e2178dfc867f73e4bd39c770662dc5ff564d18aa81163`. El manifest no hashea su propio archivo ni este cuerpo.
- Inventario R8/R182: 92 paths propuestos (61 tracked + 31 untracked), 158 evidencias separadas y 250 archivos únicos hasheados, sin solapamiento. WIP observado: 61 tracked modificados, 895 entradas untracked visibles, 20.389 paths untracked expandidos y 0 staged; status digest `f3fad33ccdb019384e026266cc8a156f3f358a70772e36eba706767194eb9ccd`; diff digest `84df0c3a954ae85cc02cd12ce45646fc2a9f5e9451abd9dd9017a4490e3c00b4`. El inventario incluye `tests/test_protected_workflow_review.py` y la atestación sanitizada [atestación cliente](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md); los artefactos R7 se conservan como evidencia. Caches, dependencias, `.next`, `out`, `.env*` operativos, secretos, temporales y untracked no listados están excluidos; `.env.example` se incluye explícitamente como ejemplo versionable. R181, R180 y R6 son scopes anteriores y no se extienden automáticamente a R182.
- Resultado de revisión: R5 PASS permanece histórico y acotado. R7 detectó seis paths sin admitir y el permiso Stage 2 `checks: read` innecesario; una pasada semántica independiente posterior encontró el edge de review en bases no protegidas. R180 corrigió el flujo. La revisión independiente de contenido R8/R181 confirmó los cinco fixes y no encontró HIGH/CRITICAL ni hallazgos bloqueantes; el re-chequeo R8/R182 confirmó pins e inventario actuales sin discrepancias. Scope checker y scanner R182 validaron 92/92 en Docker. No hay enforcement remoto ni `GO_LOCAL_PR`.

## Evidencia De Este PR

| Resultado | Comandos/casos e inputs | Ambiente y grado | Evidencia y límites |
|---|---|---|---|
| G08 — pruebas Python | R160: `pytest tests/test_*.py`, 337 passed, 4 skipped, 1 warning, exit 0; R159 contrato de credenciales 45/45. Los cuatro skips son `test_no_null_prices`, `test_no_duplicate_courses`, `test_pilot_institutions_exist` y `test_rest_api_is_healthy` de `tests/test_harvester.py`; el fixture los omite si `RUN_SUPABASE_INTEGRATION_TESTS` no es `1` o faltan credenciales. Quedan NO-EJECUTADOS y no se consultó Supabase live. | Docker local, `studiamatch-dev` e imagen fijada; variables operativas no cargadas en pytest. | [G08 vigente](h3req1_g08_final_checks_reconciliation_2026-10-11.md); los cuatro skips y la advertencia PyPDF2 se conservan y no cuentan como PASS. |
| G08 — seguridad/tooling | R174–R176 renuevan el scanner: history=5, tree=6, cuatro nombres de credenciales opacos detectados/redactados; 72 contratos relacionados PASS. ShellCheck 0.11.0 y actionlint 1.7.7 PASS; `security-audit.yml` allowlists helper/pre-push y fija pip con `requirements-pipeline.txt --require-hashes`. Scan final R6: 854 paths PASS sobre su inventario; este resultado no se extiende a R7. | Docker local, assets fijados y sintéticos. | [G08 vigente](h3req1_g08_final_checks_reconciliation_2026-10-11.md), [R175](h3req1_g08_credential_tree_symlink_r175_2026-10-11.md), [R176](h3req1_g08_scanner_named_credentials_ci_allowlist_r176_2026-10-11.md), [R178](h3req1_g09_local_close_r178_2026-10-11.md). G10/CI remoto no ejecutado; `--tree` en el checkout Docker no se reclama porque no está montado el gitdir administrativo. |
| G08 — dependencias y build | npm audit full/prod: cero vulnerabilidades con `package.json`/lock fijados. Build normal R69: 33/33 páginas y 206 archivos con hashes; artifact normal R146: 201/201 y sus fuentes actuales 61/61. Build mock y otros checks se reutilizan solo con pins compatibles. | Contenedores locales aislados; servicios y REST sintéticos. | Evidencia de auditoría/build enlazada desde [G08](h3req1_g08_final_checks_reconciliation_2026-10-11.md). R69 y R146 son artefactos distintos; no se mezclan sus conteos. |
| G07 — C03 integrado | R51 PASS, 128/128 inputs; R161 verifica discovery, persistencia y recuperación ante 503 sintéticos. | Pages/workerd + Edge + PostgreSQL 17.11 + PostgREST locales; fixtures desechables y sintéticos. | [R51](h3req1_c03_integrated_run_2026-10-10_r51.txt), [R161](h3req1_g09_pipeline_postgrest_r161/run-r10.log). No es DB/servicio remoto. |
| G09 — catálogo visual | 216/216 resultados PASS caso-viewport seleccionados para 72 casos × 3 viewports; R28/R29/R30 suman 189 ejecuciones preservadas. R173 renueva email/fallback/roles 6/6 viewports, 36/36 assertions, seis capturas, cero retries; R170 queda como FAIL de harness. | Chromium 1228 headless, Pages/workerd local y datos sintéticos; R8/R146 onboarding 10/10. | [Matriz LOCAL-01..23](h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md), [R178](h3req1_g09_local_close_r178_2026-10-11.md), [catálogo R28/R29/R30](h3req1_g09_uat_2026-10-10_r4/r28_r29_catalog_reconciliation_2026-10-11.md). Los resultados son conciliados entre ejecuciones compatibles, no una sola corrida global. |
| G09 — INV-008 / onboarding | INV-008 reproducido como ciclo de rutas para sesión `password_pending`, corregido; R8 y R146 onboarding 10/10, cero retries. | Pages/workerd, Auth/PostgREST y PG17 locales sintéticos; Chromium headless. | [Topología INV-008/R8](h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md); no se usó cuenta/correo real. |
| G09 — correo, fallback y roles | R173: H3-UAT-002/003, 2/2 casos, 6/6 viewports, 36/36 assertions, seis capturas, cero retries; helper limitado a GET de loopback, path exacto y query vacía. | Pages/workerd R146 en contenedor preservado; Chromium 1228 headless, sin ventana; fixture Auth/PostgREST y PG17.11 sintéticos; puertos publicados solo en loopback. | [R170–R173](h3req1_g09_email_fallback_r170_r173_2026-10-11.md), [R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [R175](h3req1_g08_credential_tree_symlink_r175_2026-10-11.md), [R176](h3req1_g08_scanner_named_credentials_ci_allowlist_r176_2026-10-11.md) y [revisión de seguridad R173](h3req1_g09_security_review_r173_2026-10-11.md). R170 sigue preservado como FAIL y no se cuenta como retry ni PASS. |
| G10 — bootstrap Stage 1/2 | R180 conserva `security-audit` y sus gates; Stage 2 R8 permanece separado/inactivo hasta instalar PWI. | actionlint 1.7.7 en Stage 1 exacto y derivados; transición 9/9; scope checker y credential scan R182 92/92 en Docker. Revisión independiente R8/R181 y re-chequeo de pins R8/R182 PASS. Ningún workflow remoto. | [Paquete R180](h3req1_g10_bootstrap_transition_2026-10-12_r180.md), [patch Stage 2 R8](h3req1_g10_security_audit_stage2_2026-10-12_r8.patch), [scope checker](h3req1_g10_scope_allowlist_check_r180.py), [transition checker](h3req1_g10_transition_check_r180.py), [scope/scanner R182](h3req1_g10_scope_scan_r182_2026-10-12.txt), [revisión R181/R182](h3req1_g10_r8_review_corrections_r181_2026-10-12.md). G10 remoto sigue pendiente. |
| Live/remoto | NO-EJECUTADO: CI remoto/enforcement, CodeQL remoto, Pages Preview, Auth/Supabase live, correos reales, cuentas reales, deploys y pruebas de producción. | Fuera de esta autorización local. | G10 y la aceptación remota permanecen pendientes; no se abrió PR ni se hicieron escrituras remotas. |

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Admin/editoría | Edición conserva procedencia, overrides, ownership y control de versión; auditoría transaccional registra actor, fecha y before/after; publicación aplica evidencia válida de disponibilidad con límite inclusivo de 90 días y compatibilidad legacy. | Admin, RPC editorial, pipeline y lector público. | R7/R30/R51/R58/R90/R91/R108; cruzado en la matriz LOCAL-01..23. |
| Sesión, membresías e invitación | BFF usa cookies HttpOnly, preserva MFA/RBAC/último admin, y dirige el estado de invitación `password_pending` al setup de contraseña. | Auth UI/BFF, Admin, invitaciones y membresías. | R8/R41/R51/R94/R146 y contratos locales; correo/roles renovados R173. |
| Gateway y cuota | RPC Admin allowlisted con gateway firmado y cuota fail-closed. | BFF, gateway de RPC y binding local de cuota. | R51/R135 y revisiones G08/G09; sin claims de configuración remota. |
| Pipeline y runtime público | Pages/workerd, Edge y PostgreSQL/PostgREST locales comprueban suspensión/recovery y persistencia; artefacto normal cotejado con el catálogo sintético. | Publicación, listado/detalle público y pipeline. | R51/R69/R146/R161. |
| CI independiente | Stage 1 añade PWI/helper/test, pero no depende del waiter; conserva el agregado `security-audit`. Stage 2 R8 exige el waiter solo para las bases protegidas y únicamente después de instalar PWI y verificar el run del SHA/evento. | Ramas protegidas y Actions; ningún cambio remoto. | La suite con `tests/test_protected_workflow_review.py` tuvo 72 passed en R176 y sus inputs siguen iguales; no se repitió. R180 actionlint valida Stage 1 y variante Stage 2 localmente; el checker cubre que reviews de otras bases queden skipped. La revisión independiente final R8/R181 obtuvo PASS para el paquete local; la instalación/enforcement remoto sigue pendiente. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | PASS local acotado | G01–G09 completos en el alcance local; LOCAL-01..23 completas dentro de sus fixtures y límites. G10 remoto sigue pendiente y no se afirma enforcement ni aceptación remota. No equivale a aceptación remota o de usuarios reales. |
| Escalabilidad | Medición descriptiva | R79 usa diez muestras; R135 admite 30 probes de escritura y rechaza el 31 con 429. Sin carga masiva ni SLA. |
| Seguridad | Sin HIGH/CRITICAL/bloqueantes en la revisión independiente R8/R181; LOW de pip resuelto | Scanner, allowlists, lock hashes y pruebas focales PASS. La revisión de contenido R8/R181 y el re-chequeo de pins R8/R182 son locales y acotados al inventario/delta; la recomendación LOW opcional de grants por columna queda para revisar antes de promoción remota. No es auditoría remota/global. |
| Mantenimiento | PASS con seguimiento abierto | Manifiestos y recuperación versionados; se conserva `braces@3.0.4-h3.1` y seguimiento `priceMin` asignado a Romel al 2026-11-03, no como waiver. |
| Calidad | PASS con límites declarados | G08: 337 passed, cuatro skipped y una warning PyPDF2; ESLint con nueve warnings conocidos; TypeScript y builds pasan. Skips/warnings no se ocultan. |
| Rendimiento | Medición descriptiva | R79 p50/p95 local por viewport y S16 health; no se reclama SLA o rendimiento global. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Esquema/migraciones y fixtures probados en PostgreSQL 17.11 desechable; rollback de transacción probado. | G01/G02/R7/R51; sin DB operativa. |
| compatibilidad | BFF HttpOnly, MFA, roles, gateway/cuota, procedencia y fallback legacy cubiertos en los recorridos locales descritos. | R51/R108/R135/R173 y matriz. |
| deploy | Build normal servido por Pages/workerd local y check de healthz PASS. | R69/R146/S16; no hubo despliegue Cloudflare/GitHub. |
| contract | Contrato nuevo ensayado en el candidato local; no se retiró compatibilidad legacy en servicios remotos. | Contracción remota NO-EJECUTADA. |
| Rollback/recuperación | Rollback SQL local, suspensión/resume y recuperación sintética C03/pipeline comprobados; artefactos previos preservados. | G01/G02/R51/R161; rollback de deploy remoto NO-EJECUTADO. |
| No degradacion funcional | Catálogo visual conciliado, pipeline, aceptación editorial, onboarding y correo/roles en los límites de sus pruebas. | Matriz LOCAL-01..23, R8/R51/R108/R161/R173; no extrapolar a cloud/Production. |

## Evidencia Para Cliente

La fuente se representa mediante la [atestación sanitizada versionada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md); no se incluye contenido privado ni datos/cuentas reales.

| Criterio | Resultado local | Límite |
|---|---|---|
| Admin completa/corrige cursos conservando origen | PASS en fixtures: campos editoriales, procedencia/override, conflicto de versión y ownership. | No contiene datos operativos. |
| Auditoría actor/fecha/antes/después | PASS en SQL PG17 y C03: atomicidad, ownership y ausencia de auditoría parcial en rechazo/no-op. | No es escritura remota. |
| Disponibilidad válida, máximo 90 días y legacy | PASS para URL HTTPS, límite inclusivo, rechazo de futura/vencida/exceso/faltante sin mutación y compatibilidad legacy. | No implica despliegue remoto. |
| Encabezado con correo y roles | PASS R173 para email autenticado y fallback sin email; admin conserva capacidad, user no la recibe. | Sesión/MFA sintéticos; no cuenta real. |

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS R159 y renovado R168–R173 para sus inputs; R182: 92/92 paths del inventario R8, exit 0, cero hallazgos. | Docker local; sin valores ni secretos montados. | G08 y [scope/scanner R182](h3req1_g10_scope_scan_r182_2026-10-12.txt); no sustituye los scans históricos de otros scopes. |
| Python tests | R160 exit 0: 337 passed, 4 skipped, 1 warning. Los cuatro skips son los tests live del fixture de `tests/test_harvester.py` y no se ejecutaron por ausencia de `RUN_SUPABASE_INTEGRATION_TESTS=1`/credenciales; no fueron PASS. | Docker `studiamatch-dev`; pruebas locales/sintéticas. | [G08](h3req1_g08_final_checks_reconciliation_2026-10-11.md); warning PyPDF2 y skips permanecen declarados. |
| Python compile | AST de 176 fuentes PASS reutilizado por hash compatible. | Docker local; sintaxis. | G08; no implica ejecutar los 176 módulos. |
| PostgreSQL DB Change Gate | Harness PG17.11 desechable y C03 R51 PASS; R51 128/128 inputs. | PostgreSQL local sintético, transaccional. | G01/G02/R51; no DB remota. |
| ESLint | Exit 0, cero errores, nueve warnings conocidos. | Docker local. | Evidencia G08 por inputs compatibles. |
| TypeScript | Next typegen y `tsc --noEmit` PASS con heap acotado. | Docker local. | G08; sin reejecución porque inputs compatibles. |
| Static build | R69 33/33 páginas, 206 hashes; R146 artifact 201/201 y fuentes 61/61. | Next/Pages local con fixtures sintéticos. | G08/R69/R146; artefactos distintos. |
| actionlint / ShellCheck | actionlint 1.7.7: Stage 1 exacto, Stage 2 sintético, PWI y DB Sync PASS en Docker; ShellCheck 0.11.0 pasa el bloque nuevo de clasificación de base/evento. | Docker local, no CI. | [R180](h3req1_g10_bootstrap_transition_2026-10-12_r180.md); G03/G08 preservados. El intento ShellCheck sobre la extracción completa sin expandir expresiones GitHub no cuenta como PASS y se conserva explicado. |
| UAT/runtime/integración | R51 128/128; catálogo 216/216 resultados caso-viewport seleccionados; R8/R146 onboarding 10/10; R161 recovery pipeline; R173 6/6 viewports; R175/R176 checks de seguridad PASS. | Docker/Pages/workerd/Edge/PG17/PostgREST locales, Chromium 1228 headless. | Matriz, R51, R8/R146, R161, R173 y [R178](h3req1_g09_local_close_r178_2026-10-11.md). No es una ejecución global única. |
| security-audit / CI independiente efectivo | Stage 1 conserva el agregado y está validado localmente; Stage 2 R8 pasa actionlint/aplicación en copia, pero sigue separado e inactivo. | GitHub remoto no leído en esta sesión. Owner: responsable de integración. | G10 remoto pendiente. Ningún YAML local demuestra instalación, required check o enforcement. |
| CodeQL si aplica | NO-EJECUTADO. | Sin CI remoto. Owner: responsable del PR. | Aplicabilidad se confirma al preparar la revisión remota; no se cuenta como PASS. |
| Cloudflare Pages / smoke preview | NO-EJECUTADO. | Ningún preview/deploy remoto. Owner: responsable del despliegue. | Certification/Production intactos. |
| Browser snapshot si aplica | R173 seis PNG verificados; onboarding R8 conserva capturas/vídeo; el catálogo mantiene capturas por caso en sus manifiestos. | Chromium 1228 headless; sin ventana visible. | Manifiestos R8/R173 y catálogo; R173 no incluye vídeo. |
| security-auditor | Revisión independiente de contenido R8/R181 y re-chequeo final de pins/inventario R8/R182 PASS, sin HIGH/CRITICAL ni bloqueantes; revisiones focales R147 y R175/R176 mantienen sus límites. | Revisión estática local del delta e inventario. | [Revisión R181/R182](h3req1_g10_r8_review_corrections_r181_2026-10-12.md); no extrapolar a remoto ni a paths fuera del inventario. |
| Documentación / trazabilidad / fuente cliente | Matriz, estado, atestación sanitizada, seis pilares, transición/rollback y manifest R8/R182 conciliados; revisión independiente PASS. | Evidencia local. | R178 y [revisión R181/R182](h3req1_g10_r8_review_corrections_r181_2026-10-12.md). |

## Seguridad Y Datos

- [x] Scanner/contratos R174–R176 PASS para sus inputs; R182 escanea en Docker los 92 paths propuestos del inventario actualizado, con snapshot/hash fijados y sin montar secretos. R181/R180/R6 son snapshots históricos; no se extrapolan al inventario actual.
- [x] BFF HttpOnly, API key por `apikey`, RBAC, MFA y último administrador preservados en pruebas locales citadas; no se usaron cuentas reales.
- [x] Revisión independiente R5 es histórica y acotada a su scope. R7 detectó seis paths y un permiso sobrante; la pasada semántica posterior halló el edge de bases no protegidas. R180 corrigió esos puntos. La revisión de contenido R8/R181 confirmó las cinco correcciones y no encontró HIGH/CRITICAL ni bloqueantes; R182 renovó el scanner tras reconciliar encabezados.
- [x] Sin DB remota, secretos, producción, restore, schedules, writers cloud, PR, merge, push o deploy.

## Alcance Y Limites

- [x] Requerimiento vinculado con la atestación sanitizada y la matriz LOCAL-01..23.
- [x] Rama/base/inventario local: manifest R8 conserva el test protegido, separa cambios/evidencias y fija los paths, tamaños, modos y hashes actuales. Caches/dependencias/untracked no listados excluidos. No existe PR.
- [x] Inclusión R8: `tests/test_protected_workflow_review.py` sigue en scope; la nota/checkers, scanner y patch Stage 2 R8 se registran como evidencia, no como cambios activos Stage 1.
- [x] Exclusiones R8: caches, `node_modules`, `.next`, `out`, `.env*` operativos, secretos, temporales y WIP no listados siguen fuera de `scope.entries`; `.env.example` está incluido de forma explícita y el manifest distingue evidencia de cambios propuestos.
- [x] Evidencia actual, histórica, fallida y reutilizada está separada; R170 se preserva como FAIL y no se cuenta como PASS/retry.
- [x] Operaciones remotas, despliegues, credenciales y cuentas reales quedan fuera; su aprobación sería separada.

## Checklist Tecnico

- [x] Checks locales G08 ejecutados/reutilizados con inputs compatibles en Docker; resultados y skips/warnings reales documentados.
- [x] Ficha de impacto, consumidores, contratos, matriz funcional y capa técnica actualizados.
- [x] Atestación sanitizada, seis pilares, `expand -> compatibilidad -> deploy -> contract`, rollback y límites revisados.
- [x] R8/R182 conserva diez encabezados de plantilla, links, pins, exclusiones e inventario; actionlint y transición se reutilizan por inputs idénticos; scope guard y credential scan 92/92 pasan en Docker. Revisión independiente de contenido y pins PASS. G10 remoto no se presenta como efectivo.
- [x] GO local, GO_LOCAL_PR y GO_DEVELOPMENT_REAL se mantienen separados; no se crea PR ni se inicia promoción.

**Estado de esta versión:** borrador local R8/R182, sin PR. G01–G09 continúan completos por R178 y el cierre local está acreditado. Stage 1 conserva los controles actuales; Stage 2 sigue separado/inactivo. G10 remoto NO-EJECUTADO. Veredicto local: **GO LOCAL — validación y preparación local completas**. No es `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
