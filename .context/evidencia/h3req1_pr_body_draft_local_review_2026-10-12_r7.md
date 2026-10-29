# Borrador del cuerpo PR H3REQ1 — plantilla versionada — 2026-10-12 R7

Documento local para revisión del responsable; **no se creó PR**. Sigue las diez secciones de `.github/pull_request_template.md`. R7 preserva R6, incorpora el test protegido omitido del scope anterior y separa el bootstrap CI en dos etapas. La revisión R5 PASS y sus pins cubren su scope anterior, no los deltas R7. El cambio Stage 1 y el nuevo inventario requieren revisión independiente R7; G10 sigue pendiente y no se declara `GO_LOCAL_PR`.

## Resumen

Implementación H3REQ1 para edición y procedencia editorial, auditoría, publicación por evidencia de disponibilidad, membresías/invitaciones, BFF HttpOnly, MFA/RBAC, gateway RPC firmado y cuotas. Este cuerpo resume evidencia local sintética; no representa aceptación remota.

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`; HEAD no identifica el WIP.
- Manifiesto de contenido: `.context/evidencia/h3req1_pr_scope_manifest_2026-10-12_r7.json`, SHA-256 `01814dbff299986653f85b2c5a2b292170ec7680f1d1dafa16a101bd44f72770`; scope digest `73f2b9d66ee17b302a9e38d36d17fd14996b246009ea03fbb5432dd2dc59c93a`; evidencia digest `874cd6030646e90c4db1e1f859b8f86ea0acdca621d42298300b4449671fdab3`. El manifest no se hashea a sí mismo ni al cuerpo R7.
- Inventario R7: 91 paths propuestos (61 tracked + 30 untracked), 149 evidencias separadas y 240 archivos únicos hasheados, sin solapamiento. WIP: `61` tracked modificados, `880` entradas untracked visibles, `20374` paths untracked expandidos, `0` staged; status digest `a5001b4ad74b21043f229d4e45155edf26e9459679cc9f64cdaad4145ea295e7`; diff digest `eca21ca864980c4326c3f54e502277a32681dd9eaff4cd39e84b98f5ad9fbdf0`. Incluye explícitamente `tests/test_protected_workflow_review.py` y la nota R179. Excluye caches, `node_modules`, `.next`, `out`, dependencias no listadas, `.env*`, secretos, datos temporales y todos los untracked no incluidos expresamente. El scan de 854 paths es evidencia R6 histórica, no un scan del inventario R7.
- Resultado de revisión: R5 PASS permanece histórico para el alcance revisado; no cubre el test recién incluido ni el delta Stage 1. No se atribuye revisión independiente R7 ni enforcement remoto. G10 remoto permanece NO-EJECUTADO; no hay GO_LOCAL_PR.

## Evidencia De Este PR

| Resultado | Comandos/casos e inputs | Ambiente y grado | Evidencia y límites |
|---|---|---|---|
| G08 — pruebas Python | R160: `pytest tests/test_*.py`, 337 passed, 4 skipped, 1 warning, exit 0; R159 contrato de credenciales 45/45. | Docker local, `studiamatch-dev` e imagen fijada; variables operativas no cargadas en pytest. | [G08 vigente](h3req1_g08_final_checks_reconciliation_2026-10-11.md); los cuatro skips y la advertencia PyPDF2 se conservan y no cuentan como PASS. |
| G08 — seguridad/tooling | R174–R176 renuevan el scanner: history=5, tree=6, cuatro nombres de credenciales opacos detectados/redactados; 72 contratos relacionados PASS. ShellCheck 0.11.0 y actionlint 1.7.7 PASS; `security-audit.yml` allowlists helper/pre-push y fija pip con `requirements-pipeline.txt --require-hashes`. Scan final R6: 854 paths PASS sobre su inventario; este resultado no se extiende a R7. | Docker local, assets fijados y sintéticos. | [G08 vigente](h3req1_g08_final_checks_reconciliation_2026-10-11.md), [R175](h3req1_g08_credential_tree_symlink_r175_2026-10-11.md), [R176](h3req1_g08_scanner_named_credentials_ci_allowlist_r176_2026-10-11.md), [R178](h3req1_g09_local_close_r178_2026-10-11.md). G10/CI remoto no ejecutado; `--tree` en el checkout Docker no se reclama porque no está montado el gitdir administrativo. |
| G08 — dependencias y build | npm audit full/prod: cero vulnerabilidades con `package.json`/lock fijados. Build normal R69: 33/33 páginas y 206 archivos con hashes; artifact normal R146: 201/201 y sus fuentes actuales 61/61. Build mock y otros checks se reutilizan solo con pins compatibles. | Contenedores locales aislados; servicios y REST sintéticos. | Evidencia de auditoría/build enlazada desde [G08](h3req1_g08_final_checks_reconciliation_2026-10-11.md). R69 y R146 son artefactos distintos; no se mezclan sus conteos. |
| G07 — C03 integrado | R51 PASS, 128/128 inputs; R161 verifica discovery, persistencia y recuperación ante 503 sintéticos. | Pages/workerd + Edge + PostgreSQL 17.11 + PostgREST locales; fixtures desechables y sintéticos. | [R51](h3req1_c03_integrated_run_2026-10-10_r51.txt), [R161](h3req1_g09_pipeline_postgrest_r161/run-r10.log). No es DB/servicio remoto. |
| G09 — catálogo visual | 216/216 resultados PASS caso-viewport seleccionados para 72 casos × 3 viewports; R28/R29/R30 suman 189 ejecuciones preservadas. R173 renueva email/fallback/roles 6/6 viewports, 36/36 assertions, seis capturas, cero retries; R170 queda como FAIL de harness. | Chromium 1228 headless, Pages/workerd local y datos sintéticos; R8/R146 onboarding 10/10. | [Matriz LOCAL-01..23](h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md), [R178](h3req1_g09_local_close_r178_2026-10-11.md), [catálogo R28/R29/R30](h3req1_g09_uat_2026-10-10_r4/r28_r29_catalog_reconciliation_2026-10-11.md). Los resultados son conciliados entre ejecuciones compatibles, no una sola corrida global. |
| G09 — INV-008 / onboarding | INV-008 reproducido como ciclo de rutas para sesión `password_pending`, corregido; R8 y R146 onboarding 10/10, cero retries. | Pages/workerd, Auth/PostgREST y PG17 locales sintéticos; Chromium headless. | [Topología INV-008/R8](h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md); no se usó cuenta/correo real. |
| G09 — correo, fallback y roles | R173: H3-UAT-002/003, 2/2 casos, 6/6 viewports, 36/36 assertions, seis capturas, cero retries; helper limitado a GET de loopback, path exacto y query vacía. | Pages/workerd R146 en contenedor preservado; Chromium 1228 headless, sin ventana; fixture Auth/PostgREST y PG17.11 sintéticos; puertos publicados solo en loopback. | [R170–R173](h3req1_g09_email_fallback_r170_r173_2026-10-11.md), [R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [R175](h3req1_g08_credential_tree_symlink_r175_2026-10-11.md), [R176](h3req1_g08_scanner_named_credentials_ci_allowlist_r176_2026-10-11.md) y [revisión de seguridad R173](h3req1_g09_security_review_r173_2026-10-11.md). R170 sigue preservado como FAIL y no se cuenta como retry ni PASS. |
| G10 — bootstrap Stage 1/2 | R179: Stage 1 sin waiter; agregador `security-audit` y sus demás gates conservados. Stage 2 patch con dry-run/aplicación en copia temporal PASS y restore exacto del SHA R6. | Validación estructural local, sin workflow run remoto. | [Paquete R179](h3req1_g10_bootstrap_transition_2026-10-12.md) y patch Stage 2 local. R176 actionlint PASS corresponde a Stage 2/R6; Stage 1 actionlint y review R7 pendientes. |
| Live/remoto | NO-EJECUTADO: CI remoto/enforcement, CodeQL remoto, Pages Preview, Auth/Supabase live, correos reales, cuentas reales, deploys y pruebas de producción. | Fuera de esta autorización local. | G10 y la aceptación remota permanecen pendientes; no se abrió PR ni se hicieron escrituras remotas. |

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Admin/editoría | Edición conserva procedencia, overrides, ownership y control de versión; auditoría transaccional registra actor, fecha y before/after; publicación aplica evidencia válida de disponibilidad con límite inclusivo de 90 días y compatibilidad legacy. | Admin, RPC editorial, pipeline y lector público. | R7/R30/R51/R58/R90/R91/R108; cruzado en la matriz LOCAL-01..23. |
| Sesión, membresías e invitación | BFF usa cookies HttpOnly, preserva MFA/RBAC/último admin, y dirige el estado de invitación `password_pending` al setup de contraseña. | Auth UI/BFF, Admin, invitaciones y membresías. | R8/R41/R51/R94/R146 y contratos locales; correo/roles renovados R173. |
| Gateway y cuota | RPC Admin allowlisted con gateway firmado y cuota fail-closed. | BFF, gateway de RPC y binding local de cuota. | R51/R135 y revisiones G08/G09; sin claims de configuración remota. |
| Pipeline y runtime público | Pages/workerd, Edge y PostgreSQL/PostgREST locales comprueban suspensión/recovery y persistencia; artefacto normal cotejado con el catálogo sintético. | Publicación, listado/detalle público y pipeline. | R51/R69/R146/R161. |
| CI independiente | Stage 1 añade workflow PWI/helper/test, deja `security-audit` existente como agregado sin waiter. Stage 2 queda en patch separado para requerir PWI solo después de instalarlo en la rama predeterminada. | Ramas protegidas y Actions; no se modifican remotamente. | La nueva suite con `tests/test_protected_workflow_review.py` tuvo 72 passed en la pasada focal R176 (junto a otros dos archivos); no se repitió. Stage 1 R179 requiere actionlint exacto, revisión R7 y confirmación remota. G10 no está efectivo. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | PASS local acotado | G01–G09 completos en el alcance local; LOCAL-01..23 completas dentro de sus fixtures y límites. G10 remoto sigue pendiente y no se afirma enforcement ni aceptación remota. No equivale a aceptación remota o de usuarios reales. |
| Escalabilidad | Medición descriptiva | R79 usa diez muestras; R135 admite 30 probes de escritura y rechaza el 31 con 429. Sin carga masiva ni SLA. |
| Seguridad | Sin HIGH/MEDIUM conocidos en revisiones locales actuales; LOW de pip resuelto | Scanner, allowlists, lock hashes y pruebas focales PASS. Revisión independiente R5 PASS, sin HIGH/MEDIUM ni bloqueantes; la recomendación LOW opcional de grants por columna queda registrada para una revisión previa a promoción remota. No es auditoría remota/global. |
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

La fuente se representa mediante la atestación sanitizada versionada; no se incluye contenido privado ni datos/cuentas reales.

| Criterio | Resultado local | Límite |
|---|---|---|
| Admin completa/corrige cursos conservando origen | PASS en fixtures: campos editoriales, procedencia/override, conflicto de versión y ownership. | No contiene datos operativos. |
| Auditoría actor/fecha/antes/después | PASS en SQL PG17 y C03: atomicidad, ownership y ausencia de auditoría parcial en rechazo/no-op. | No es escritura remota. |
| Disponibilidad válida, máximo 90 días y legacy | PASS para URL HTTPS, límite inclusivo, rechazo de futura/vencida/exceso/faltante sin mutación y compatibilidad legacy. | No implica despliegue remoto. |
| Encabezado con correo y roles | PASS R173 para email autenticado y fallback sin email; admin conserva capacidad, user no la recibe. | Sesión/MFA sintéticos; no cuenta real. |

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS R159 y renovado R168–R173 en runners afectados; R173 exit 0. | Docker local; salida sin valores. | G08 y [precheck R173](h3req1_g08_final_r173_runner_precheck.log). |
| Python tests | R160 exit 0: 337 passed, 4 skipped, 1 warning. | Docker `studiamatch-dev`; local/sintético. | [G08](h3req1_g08_final_checks_reconciliation_2026-10-11.md); skips y warning no son PASS. |
| Python compile | AST de 176 fuentes PASS reutilizado por hash compatible. | Docker local; sintaxis. | G08; no implica ejecutar los 176 módulos. |
| PostgreSQL DB Change Gate | Harness PG17.11 desechable y C03 R51 PASS; R51 128/128 inputs. | PostgreSQL local sintético, transaccional. | G01/G02/R51; no DB remota. |
| ESLint | Exit 0, cero errores, nueve warnings conocidos. | Docker local. | Evidencia G08 por inputs compatibles. |
| TypeScript | Next typegen y `tsc --noEmit` PASS con heap acotado. | Docker local. | G08; sin reejecución porque inputs compatibles. |
| Static build | R69 33/33 páginas, 206 hashes; R146 artifact 201/201 y fuentes 61/61. | Next/Pages local con fixtures sintéticos. | G08/R69/R146; artefactos distintos. |
| actionlint / ShellCheck | PASS o reutilizados al coincidir los inputs fijados. | Local, no CI. | G03/G08; evidence paths en conciliación G08. |
| UAT/runtime/integración | R51 128/128; catálogo 216/216 resultados caso-viewport seleccionados; R8/R146 onboarding 10/10; R161 recovery pipeline; R173 6/6 viewports; R175/R176 checks de seguridad PASS. | Docker/Pages/workerd/Edge/PG17/PostgREST locales, Chromium 1228 headless. | Matriz, R51, R8/R146, R161, R173 y [R178](h3req1_g09_local_close_r178_2026-10-11.md). No es una ejecución global única. |
| security-audit / CI independiente efectivo | Stage 1 YAML local; el `security-audit` agregado sigue sin waiter PWI. Stage 2 patch validado estructuralmente y aplicable, aún no aplicado ni ejecutado remoto. | GitHub remoto, configuración actual sin revalidar. Owner: responsable de integración. | G10 pendiente; R176 actionlint cubre la variante R6/Stage 2 exacta; acción lint de Stage 1 pendiente. |
| CodeQL si aplica | NO-EJECUTADO. | Sin CI remoto. Owner: responsable del PR. | Aplicabilidad se confirma al preparar la revisión remota; no se cuenta como PASS. |
| Cloudflare Pages / smoke preview | NO-EJECUTADO. | Ningún preview/deploy remoto. Owner: responsable del despliegue. | Certification/Production intactos. |
| Browser snapshot si aplica | R173 seis PNG verificados; onboarding R8 conserva capturas/vídeo; el catálogo mantiene capturas por caso en sus manifiestos. | Chromium 1228 headless; sin ventana visible. | Manifiestos R8/R173 y catálogo; R173 no incluye vídeo. |
| security-auditor | Revisiones focales R147 y R175/R176 no hallaron HIGH/MEDIUM en sus deltas. Revisión independiente R5 del conjunto local PASS, sin HIGH/MEDIUM ni bloqueantes; el dictamen es estático y acotado al scope. | Revisión estática local. | [R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [R176](h3req1_g08_scanner_named_credentials_ci_allowlist_r176_2026-10-11.md); no extrapolar más allá de sus alcances. |
| Documentación / trazabilidad / fuente cliente | Matriz, estado, atestación sanitizada, seis pilares, transición/rollback y manifest R7 actualizados. | Evidencia local. | R5 histórico para scope anterior; R7 requiere nueva revisión independiente y sus pins se verifican mecánicamente. |

## Seguridad Y Datos

- [x] Scanner/contratos R174–R176 PASS para sus inputs. El scan final R6 de 854 paths se conserva como evidencia histórica y no se extiende al inventario R7 sin revalidar inputs.
- [x] BFF HttpOnly, API key por `apikey`, RBAC, MFA y último administrador preservados en pruebas locales citadas; no se usaron cuentas reales.
- [x] Revisión independiente R5: PASS para el scope anterior de 89 paths; no cubre el delta del test protegido ni el cambio Stage 1 R7. Revisión R7 pendiente antes del PR.
- [x] Sin DB remota, secretos, producción, restore, schedules, writers cloud, PR, merge, push o deploy.

## Alcance Y Limites

- [x] Requerimiento vinculado con la atestación sanitizada y la matriz LOCAL-01..23.
- [x] Rama/base/inventario local: manifest R7 con inclusión explícita del test protegido y nota R179; entradas de evidencia separadas; caches/dependencias/untracked no listados excluidos. No existe PR.
- [x] Inclusión R7: `tests/test_protected_workflow_review.py` y nota de transición R179 aparecen explícitamente en `scope.entries`; stage2 patch queda como evidencia local, no como fuente activa de etapa 1.
- [x] Exclusiones R7: caches, `node_modules`, `.next`, `out`, `.env*`, secretos, temporales y todos los untracked no listados están fuera de `scope.entries`; el manifest distingue evidencia de cambio propuesto.
- [x] Evidencia actual, histórica, fallida y reutilizada está separada; R170 se preserva como FAIL y no se cuenta como PASS/retry.
- [x] Operaciones remotas, despliegues, credenciales y cuentas reales quedan fuera; su aprobación sería separada.

## Checklist Tecnico

- [x] Checks locales G08 ejecutados/reutilizados con inputs compatibles en Docker; resultados y skips/warnings reales documentados.
- [x] Ficha de impacto, consumidores, contratos, matriz funcional y capa técnica actualizados.
- [x] Atestación sanitizada, seis pilares, `expand -> compatibilidad -> deploy -> contract`, rollback y límites revisados.
- [x] Revisión independiente R5 conservada para su scope. R7 valida plantilla, references, pins, exclusiones y transición Stage1/Stage2; revisión independiente R7 y actionlint exacto de Stage1 quedan pendientes. G10 no se presenta como efectivo.
- [x] GO local, GO_LOCAL_PR y GO_DEVELOPMENT_REAL se mantienen separados; no se crea PR ni se inicia promoción.

**Estado de esta versión:** borrador local R7, sin PR. G01–G09 continúan completos por R178 para el alcance local. Stage 1 evita depender del control aún no instalado; Stage 2 está preparado como patch pero requiere instalación y una instrucción posterior. G10 remoto NO-EJECUTADO; R7 necesita revisión independiente y actionlint exacto de Stage 1. No se afirma `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
