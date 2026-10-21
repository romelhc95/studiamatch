# Borrador del cuerpo PR H3REQ1 — preparado con plantilla versionada — 2026-10-11 R4

Documento local para revisión del responsable; **no se creó PR**. El cuerpo sigue la plantilla versionada `.github/pull_request_template.md`. R4 incorpora el hallazgo y la corrección R174 del scanner de historia; la revisión independiente del alcance completo actual y la reconciliación final del manifest/cuerpo siguen pendientes.

## Resumen

Implementación H3REQ1 para edición y procedencia editorial, auditoría, publicación por evidencia de disponibilidad, membresías/invitaciones, BFF HttpOnly, MFA/RBAC, gateway RPC firmado y cuotas. Este cuerpo resume evidencia local sintética; no representa aceptación remota.

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`; HEAD no identifica el WIP.
- Manifiesto de contenido: `.context/evidencia/h3req1_pr_scope_manifest_2026-10-11_r4.json`, SHA-256 `388805ade46ca1c6d393cf5c0f92282e44ce0e6413fe288d38922a756a1d3fcd`. El manifiesto no se hashea a sí mismo ni al cuerpo; sus listas y el WIP excluyen esos paths generados.
- Propuesta de alcance: lista explícita de 88 paths de cambio (61 tracked + 27 untracked); 138 paths de evidencia seleccionada por separado, no son inclusión automática. Digest de entries de cambio: `f18f136a5f27bb04217c445e30736810abaf58d49d0fd0c7fa73a24228e8856b`; WIP expandido: 20.363 paths untracked, 61 tracked modificados, 869 entradas untracked visibles y 0 staged; status digest `229e3dd3032e58f8f5e3a8a48a229f28130012c6f1bc2cba092a5d6292e704d1`; diff digest `2a930bbb3ec5fefde1cbb1b1520af0b644a12b08d755c864e8eee5e24b70e2da`; no hay paths staged. Se excluyen los demás untracked, cachés, `node_modules`, `.next`, `out`, builds temporales, secretos/`.env*` operativos, datos reales, contenedores/volúmenes, checkout original y recursos ajenos.
- Resultado actual de revisión de alcance: la revisión independiente del alcance de código actual y del manifest/cuerpo R4 está pendiente. Estado de gates al preparar esta versión: G01–G08 completos; G09/LOCAL-23 en revisión final; G10 remoto pendiente. No se declara GO en esta versión preliminar.

## Evidencia De Este PR

| Resultado | Comandos/casos e inputs | Ambiente y grado | Evidencia y límites |
|---|---|---|---|
| G08 — pruebas Python | R160: `pytest tests/test_*.py`, 337 passed, 4 skipped, 1 warning, exit 0; R159 contrato de credenciales 45/45. | Docker local, `studiamatch-dev` e imagen fijada; variables operativas no cargadas en pytest. | [G08 vigente](h3req1_g08_final_checks_reconciliation_2026-10-11.md); los cuatro skips y la advertencia PyPDF2 se conservan y no cuentan como PASS. |
| G08 — seguridad/tooling | Credential scan, H2 writer scan, ESLint (exit 0, nueve warnings conocidos), Next typegen/TypeScript, actionlint y ShellCheck PASS o reutilizados con inputs coincidentes. R173 renueva `node --check` del runner UAT actual; R174 corrige el scan de historia con cinco regresiones (lineal/root/merge/árbol vacío/primer push), 70 contratos relacionados y ShellCheck PASS en Docker. | Docker local; hashes fijados por los registros de ejecución. | [G08 vigente](h3req1_g08_final_checks_reconciliation_2026-10-11.md), [R173 precheck](h3req1_g08_final_r173_runner_precheck.log) y [R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md). El intento `--tree` actual no llegó a enumerar porque el gitdir del worktree no está accesible en `studiamatch-dev`; no se afirma un nuevo scan completo de ese modo ni enforcement CI remoto. |
| G08 — dependencias y build | npm audit full/prod: cero vulnerabilidades con `package.json`/lock fijados. Build normal R69: 33/33 páginas y 206 archivos con hashes; artifact normal R146: 201/201 y sus fuentes actuales 61/61. Build mock y otros checks se reutilizan solo con pins compatibles. | Contenedores locales aislados; servicios y REST sintéticos. | Evidencia de auditoría/build enlazada desde [G08](h3req1_g08_final_checks_reconciliation_2026-10-11.md). R69 y R146 son artefactos distintos; no se mezclan sus conteos. |
| G07 — C03 integrado | R51 PASS, 128/128 inputs; R161 verifica discovery, persistencia y recuperación ante 503 sintéticos. | Pages/workerd + Edge + PostgreSQL 17.11 + PostgREST locales; fixtures desechables y sintéticos. | [R51](h3req1_c03_integrated_run_2026-10-10_r51.txt), [R161](h3req1_g09_pipeline_postgrest_r161/run-r10.log). No es DB/servicio remoto. |
| G09 — catálogo visual | 216/216 resultados PASS caso-viewport seleccionados para 72 casos × 3 viewports, reconciliados entre ejecuciones compatibles; R28/R29/R30 aportan 189. R170 permanece como FAIL de harness y queda excluido. | Chromium 1228 headless, Pages/workerd local y datos sintéticos. | [Matriz LOCAL-01..23](h3req1_g09_local_acceptance_matrix_reconciliation_2026-10-11.md) y [catálogo R28/R29/R30](h3req1_g09_uat_2026-10-10_r4/r28_r29_catalog_reconciliation_2026-10-11.md). No fue una sola corrida global. |
| G09 — INV-008 / onboarding | INV-008 reproducido como ciclo de rutas para sesión `password_pending`, corregido; R8 y R146 onboarding 10/10, cero retries. | Pages/workerd, Auth/PostgREST y PG17 locales sintéticos; Chromium headless. | [Topología INV-008/R8](h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md); no se usó cuenta/correo real. |
| G09 — correo, fallback y roles | R173: H3-UAT-002/003, 2/2 casos, 6/6 viewports, 36/36 assertions, seis capturas, cero retries; helper limitado a GET de loopback, path exacto y query vacía. | Pages/workerd R146 en contenedor preservado; Chromium 1228 headless, sin ventana; fixture Auth/PostgREST y PG17.11 sintéticos; puertos publicados solo en loopback. | [R170–R173](h3req1_g09_email_fallback_r170_r173_2026-10-11.md) y [R174 scanner](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [revisión de seguridad R173](h3req1_g09_security_review_r173_2026-10-11.md). R170 sigue preservado como FAIL y no se cuenta como retry ni PASS. |
| Live/remoto | NO-EJECUTADO: CI remoto/enforcement, CodeQL remoto, Pages Preview, Auth/Supabase live, correos reales, cuentas reales, deploys y pruebas de producción. | Fuera de esta autorización local. | G10 y la aceptación remota permanecen pendientes; no se abrió PR ni se hicieron escrituras remotas. |

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Admin/editoría | Edición conserva procedencia, overrides, ownership y control de versión; auditoría transaccional registra actor, fecha y before/after; publicación aplica evidencia válida de disponibilidad con límite inclusivo de 90 días y compatibilidad legacy. | Admin, RPC editorial, pipeline y lector público. | R7/R30/R51/R58/R90/R91/R108; cruzado en la matriz LOCAL-01..23. |
| Sesión, membresías e invitación | BFF usa cookies HttpOnly, preserva MFA/RBAC/último admin, y dirige el estado de invitación `password_pending` al setup de contraseña. | Auth UI/BFF, Admin, invitaciones y membresías. | R8/R41/R51/R94/R146 y contratos locales; correo/roles renovados R173. |
| Gateway y cuota | RPC Admin allowlisted con gateway firmado y cuota fail-closed. | BFF, gateway de RPC y binding local de cuota. | R51/R135 y revisiones G08/G09; sin claims de configuración remota. |
| Pipeline y runtime público | Pages/workerd, Edge y PostgreSQL/PostgREST locales comprueban suspensión/recovery y persistencia; artefacto normal cotejado con el catálogo sintético. | Publicación, listado/detalle público y pipeline. | R51/R69/R146/R161. |
| CI independiente | Controles locales y workflow están en la propuesta de 88 paths. | Futuro PR y ramas protegidas. | YAML local no demuestra instalación ni enforcement; G10 sigue pendiente y no se tocó GitHub. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | PASS local acotado | G01–G08 completos; la matriz reconcilia las áreas LOCAL-01..22, y LOCAL-23 permanece abierto hasta revisión independiente del scope; no equivale a aceptación de usuarios reales. |
| Escalabilidad | Medición descriptiva | R79 usa diez muestras; R135 admite 30 probes de escritura y rechaza el 31 con 429. Sin carga masiva ni SLA. |
| Seguridad | Sin bloqueantes en revisiones locales citadas | Scanner/contratos/auditorías locales; revisión R173 no encontró HIGH/MEDIUM en su alcance. No es auditoría remota/global ni cierra revisión final del scope. |
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
| UAT/runtime/integración | R51 128/128; catálogo 216/216 resultados caso-viewport seleccionados; R8 onboarding 10/10; R161 recuperación pipeline; R173 6/6 viewports. | Docker/Pages/workerd/Edge/PG17/PostgREST locales, Chromium 1228 headless. | Matriz, R51, R8/R146, R161 y [R170–R173](h3req1_g09_email_fallback_r170_r173_2026-10-11.md). No es una ejecución global única. |
| security-audit / CI independiente efectivo | YAML/control local propuesto; enforcement y workflow remoto NO-EJECUTADOS. | GitHub remoto fuera de alcance. Owner: responsable de integración. | G10 pendiente; requiere autorización remota posterior. |
| CodeQL si aplica | NO-EJECUTADO. | Sin CI remoto. Owner: responsable del PR. | Aplicabilidad se confirma al preparar la revisión remota; no se cuenta como PASS. |
| Cloudflare Pages / smoke preview | NO-EJECUTADO. | Ningún preview/deploy remoto. Owner: responsable del despliegue. | Certification/Production intactos. |
| Browser snapshot si aplica | R173 seis PNG verificados; onboarding R8 conserva capturas/vídeo; el catálogo mantiene capturas por caso en sus manifiestos. | Chromium 1228 headless; sin ventana visible. | Manifiestos R8/R173 y catálogo; R173 no incluye vídeo. |
| security-auditor | R147 revisó el fix del scanner R174 sin HIGH/MEDIUM en ese delta; R173 tuvo revisión focal sin HIGH/MEDIUM en su alcance. La revisión independiente del scope completo actualizado queda pendiente. | Revisión estática local. | [Evidencia R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [dictamen R173](h3req1_g09_security_review_r173_2026-10-11.md); no extrapolar más allá de cada alcance. |
| Documentación / trazabilidad / fuente cliente | Matriz, estado, atestación sanitizada, seis pilares, transición/rollback y manifest actualizados. | Evidencia local. | La revisión independiente del alcance de código y del manifest/body R4 está pendiente; owner: responsable H3. |

## Seguridad Y Datos

- [x] Scanner y contratos de credenciales locales pasan en los inputs identificados; R174 renueva historia Git con cinco regresiones y 70 contratos relacionados; el escaneo explícito de archivos modificados pasa en Docker. La revisión global del alcance de 88 paths queda pendiente de esta versión.
- [x] BFF HttpOnly, API key por `apikey`, RBAC, MFA y último administrador preservados en pruebas locales citadas; no se usaron cuentas reales.
- [ ] Revisión independiente HIGH/CRITICAL ausentes para el conjunto de 88 paths: pendiente; no se interpreta el dictamen focal R173 como revisión completa.
- [x] Sin DB remota, secretos, producción, restore, schedules, writers cloud, PR, merge, push o deploy.

## Alcance Y Limites

- [x] Requerimiento vinculado con la atestación sanitizada y la matriz LOCAL-01..23.
- [ ] Rama/base/inventario final para la revisión del PR: manifest R4 con 88 paths de cambio; revisión independiente pendiente; no existe PR.
- [x] Evidencia actual, histórica, fallida y reutilizada está separada; R170 se preserva como FAIL y no se cuenta como PASS/retry.
- [x] Operaciones remotas, despliegues, credenciales y cuentas reales quedan fuera; su aprobación sería separada.

## Checklist Tecnico

- [x] Checks locales G08 ejecutados/reutilizados con inputs compatibles en Docker; resultados y skips/warnings reales documentados.
- [x] Ficha de impacto, consumidores, contratos, matriz funcional y capa técnica actualizados.
- [x] Atestación sanitizada, seis pilares, `expand -> compatibilidad -> deploy -> contract`, rollback y límites revisados.
- [ ] Review independiente del manifest R4 y de este cuerpo: pendiente en esta versión. G10 CI remoto no se presenta como efectivo.
- [x] GO local, GO_LOCAL_PR y GO_DEVELOPMENT_REAL se mantienen separados; no se crea PR ni se inicia promoción.

**Estado de esta versión:** borrador local R4, sin PR. G01–G08 completos; G09/LOCAL-23 pendiente de revisión independiente del alcance de código actualizado y reconciliación final; G10 CI remoto NO-EJECUTADO. Este archivo prepara el cuerpo con la plantilla versionada, no abre un PR ni declara GO.
