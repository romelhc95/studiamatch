# Conciliación de áreas de aceptación local LOCAL-01..23 — 2026-10-11

## Candidato y regla de lectura

- Checkout candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama/HEAD: `feat/h3req1-sync-20261002` / baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`; se consideran los inputs WIP,
  no solo HEAD.
- R28/R29/R30 dan un PASS visual vigente por cada una de las 189 ejecuciones del
  catálogo. Detalle, hashes y causas:
  [reconciliación visual R28/R29/R30](h3req1_g09_uat_2026-10-10_r4/r28_r29_catalog_reconciliation_2026-10-11.md).
- `Vigente` significa que el caso indicado se ejecutó en el runtime candidato
  con inputs compatibles; `Histórica` requiere cotejo de inputs antes de
  reutilizar; `Parcial` acredita solo el subconjunto descrito; `Faltante` no
  tiene evidencia ejecutada suficiente. Ningún estado de esta tabla por sí
  solo cierra G09.

## Matriz cruzada

| Área | Pruebas/evidencia existente y estado | Cobertura y resultado actual | Falta para cerrar el área |
|---|---|---|---|
| LOCAL-01 Inventario y fixtures | UAT PG17 R12, R28/R29, pipeline R2/R18, R74, agregado R83, lectura R116 y conciliación R141/R142. **Completo para el inventario sintético actual.** | R141 concilia 31 filas PG17, 16 elegibles, lector público con exactamente las mismas 16 identidades, 16 detalles propios HTTP 200 y 15 rutas no elegibles HTTP 404. R69 artifact estático y R142 listing coinciden con las 16 rutas; UAT recorre páginas 12+4 sin duplicados. Los datos permanecen sintéticos y la lectura SQL fue `READ ONLY`/`ROLLBACK`. | No extrapolar los conteos a datos operativos o cloud; el cambio tras mutación/rebuild/cache sigue en LOCAL-03/16. Evidencia [R140–R142](h3req1_g09_local_acceptance_delta_r140_r142_2026-10-11.md). |
| LOCAL-02 Navegación pública | H3-UAT-043, 057, 063, 049, 065/R119 y H3-UAT-067/R116. **Completo para el inventario actual de producto.** | R28 conserva ruta inexistente controlada y back/forward; R116 cubre catálogo poblado, vacío y API 503 con fallback estático, 3/3 viewports; R119 visitó los 16 deep-links de producto en cinco universidades: 16/16 HTTP 200, curso/institución, canonical, JSON-LD y ruta propia, 3/3 viewports, 294/294 assertions, cero egress/errores/retries. El artefacto R69 tenía un 17.º path de mock interno que R12 responde 404; se excluyó del inventario cliente y se preserva R117. | Sin pendiente dentro del inventario público actual y estados navegacionales cubiertos. El comportamiento tras mutación→rebuild/cache se mantiene en LOCAL-03/16. Ver [manifest R117](h3req1_g09_uat_2026-10-10_r4/uat-static-details-r117/h3-expanded-uat-manifest.json) y [manifest R119](h3req1_g09_uat_2026-10-10_r4/uat-static-details-r119/h3-expanded-uat-manifest.json). |
| LOCAL-03 Muestreo y detalle | H3-UAT-051, 054, 057, 065/R119; R74; H3-UAT-067/R116; R141/R142; H3-UAT-072/R146. **Completo para el recorrido sintético local.** | R146 renovó el build normal desde el candidato y ejecutó H3-UAT-072 en 3/3 viewports: la mutación sintética del mismo UUID se refleja en listing y detalle manteniendo la ruta. En R162 se verificaron 201/201 hashes del artifact R146 y 61/61 fuentes web actuales. R119/R141/R142 conservan inventario, estados y rutas no elegibles; R116 conserva catálogo poblado/vacío/503. R149 se preserva como antecedente, pero no es la base de cierre. | No inferir invalidación CDN ni propagación remota. Evidencia: `h3req1_g09_onboarding_2026-10-11_r7/run-r7/onboarding-r146/uat072-current/` y `h3req1_g09_uat_2026-10-10_r4/uat-r148-current-normal/`; hashes de verificación R162 en `uat-r162-r146-artifact-check.log` y `uat-r162-r146-source-check.log`. |
| LOCAL-04 Filtros, búsqueda y orden | H3-UAT-052, 053, 059, 060, 061, 062; R23 rojo preservado; R24 canónico, R28 y R33. **Completo para el catálogo vigente.** | R23: H3-UAT-059 desktop/tablet FAIL al restaurar búsqueda vacía; mobile PASS; H3-UAT-062 comparador PASS 3/3. Causa: “Limpiar todo” dejaba `searchInput` obsoleto mientras limpiaba `searchTerm`; el debounce podía reaplicarlo. El delta existente añade `setSearchInput("")`. R24 canónico pasó 059 + 060 en los tres viewports (6/6). R28 pasó 052/053/059/060/061/062 en 18/18 viewports; su FAIL global se debió a 007/032/042 y se preserva. R33 volvió a ejecutar 053 en el runtime compartido: 3/3 viewports, 9/9 aserciones, tres capturas, cero errores y retries. D25/D26 corroboran sin cambio de producto. | Ningún caso del catálogo actual pendiente para filtros, búsqueda, bandas, mínimos/máximos, orden, paginación y comparación; G09 permanece parcial por las otras áreas LOCAL-01..23. Evidencia [R23–R26 y acceso Windows](h3req1_g09_filters_windows_access_r24_r26_2026-10-11.md), [R28/R29/R30](h3req1_g09_uat_2026-10-10_r4/r28_r29_catalog_reconciliation_2026-10-11.md), [acceso Windows y R31–R33](h3req1_g09_windows_access_combined_filters_r31_r33_2026-10-11.md). |
| LOCAL-05 Comparación | H3-UAT-055, 062, 049 y 064; R58/R70. **Completo para el contrato local de comparación del catálogo.** | R58 H3-UAT-055 3/3 viewports PASS: UUID sintético no elegible retorna 0 cursos y ninguna tarjeta ajena. R57 `id=eq` no soportado se conserva como fallo de test y se corrigió a `id=in.(...)`. R70 H3-UAT-049 pasa 3/3 con la misma identidad publicada; H3-UAT-064 pasa 3/3 con dos candidatos elegibles distintos, valores opcionales ausentes/poblados, fallback `Por confirmar` para ubicación y sin `null`/`undefined`. En total, seis ejecuciones y 96/96 aserciones, cero errores de consola/requests y retries 0. | No queda pendiente funcional de comparación en el catálogo vigente. R63/R65/R66/R68 conservan los rojos de harness/fixture por regex, proxy y rutas estáticas; sus causas están clasificadas en [delta R64–R70](h3req1_g09_local_acceptance_delta_r64_r70_2026-10-11.md). |
| LOCAL-06 Asesoría | H3-UAT-056 R77 y CTA público R30. **Completo para el comportamiento local vigente.** | R77 confirma canal cerrado, ausencia de formulario/captura y cero escrituras externas en desktop/tablet/móvil; R30 confirma que “Solicitar Info” navega al detalle interno del mismo curso. Capturas R77 preservadas. | Sin acción local pendiente; no se probó envío de correo ni destino externo real. |
| LOCAL-07 Descubrimiento | R2 pipeline walk + `tests/test_h3req1_pipeline_discovery_boundaries.py` R18; R58/G08, R73, R140, R147 y R161. **Completo en PG17 sintético local.** | R147 demuestra checkpoint persistido/resume y handoff discovery→staging sobre PostgREST/PG17.11; R161 renovó el harness con los inputs actuales y pasó `discovery-checkpoint-resume` y `discovery-to-staging`. | No hubo crawling exterior; la entrada fue sintética. No extrapolar a fuentes ni credenciales operativas. Evidencia `.context/evidencia/h3req1_g09_pipeline_postgrest_r161/run-r10.log` y `exit.txt`; el manifiesto R147 se conserva como antecedente. |
| LOCAL-08 Procesamiento completo | R2 pipeline walk + SQL seed PG17 + H3-UAT-049 R30; R7/R10/R12/R18, R73, R140, R147 y R161. **Completo en PG17/PostgREST sintéticos locales.** | R161 persistió staging→cleansed→enriched→courses; recovery de cleansing/enrichment tras 503 sintético y requeue/recovery de sync pasan; estado final `staging=1|cleansed=1|enriched=1|courses=1`. PostgREST HTTP PASS. R30 conserva Admin/publicación/listing/detalle/comparación. | LLM, embeddings y fuentes externas no se consultaron; no se ejecutó writer cloud. Evidencia `.context/evidencia/h3req1_g09_pipeline_postgrest_r161/run-r10.log` y `exit.txt`. |
| LOCAL-09 Sesión y MFA | H3-UAT-001..005, 028..034; G03 BFF UAT; R75/R76/R133/R139/R171–R173. **Completa para el fixture local.** | R76 conserva 96 checks: sesión A/B, actividad expirada/futura/tamper, flags HttpOnly/Secure/SameSite/Max-Age, limpieza Auth/code-verifier multi-chunk y rebind MFA. R133 prueba rechazo tras expiración, borrado de cookies y RPC 401. R139 coloca una sesión Auth sintética en refresh window, hace tres lecturas BFF paralelas y verifica AAL2, renovación de expiración y cambio de huellas SHA-256 del par access/refresh sin registrar tokens; al avanzar el reloj, las tres lecturas fallan cerradas, limpian cookies y el RPC devuelve 401. INV-008 fue reproducido como ciclo funcional con `password_pending`, corregido y revalidado por R8; R146 repitió el onboarding 10/10. R171–R173 revalidan email autenticado y fallback sin email con MFA local en admin/user; R173 exige GET del mismo origen loopback, path exacto y query vacía. Las ejecuciones R173 pasan. | Sin pendiente funcional local en el fixture; no representa llamadas Auth remotas ni garantiza semántica del proveedor. El BFF sigue server-side HttpOnly y no expone tokens. Evidencia [R75](h3req1_g09_local_acceptance_delta_r75_2026-10-11.md), [R76](h3req1_g09_local_acceptance_delta_r76_2026-10-11.md), [R8](h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md), [R130–R133](h3req1_g09_local_acceptance_delta_r130_r133_2026-10-11.md), [R135–R139](h3req1_g09_local_acceptance_delta_r135_r139_2026-10-11.md), R146 y [R170–R173](h3req1_g09_email_fallback_r170_r173_2026-10-11.md). |
| LOCAL-10 Roles y membresías | H3-UAT-003, 004, 022, 026, 035, 040, 050; suspensión R51; R41/R93/R94. **Completa para el fixture local.** | R41 pasa rol/estado/último admin/teclado. R93 suma dos solicitudes BFF simultáneas del mismo actor: 3/3 viewports, 19 aserciones por vista. R94 usa dos actores y transacciones PG17 concurrentes: una desactivación gana, la otra se rechaza por actor ya inactivo, el último admin se conserva y ambos estados originales se restauran. R92 queda como rojo de runtime R12 antiguo; R93 usó build R41. | No extrapolar concurrencia a Auth/DB remotos; no queda acción funcional local en este fixture. Evidencia [R41](h3req1_g09_uat_2026-10-11_r41_membership_keyboard.md), [R92–R93](h3req1_g09_local_acceptance_delta_r92_r93_2026-10-11.md) y [R94](h3req1_g09_local_acceptance_delta_r94_2026-10-11.md). |
| LOCAL-11 Invitaciones y onboarding | H3-UAT-036..039 y onboarding R8/R146. **Completo en el alcance local sintético.** | R6 fue intermitente; R8 reprodujo el ciclo funcional `password_pending`→Admin/login→Admin. R146 volvió a ejecutar 10/10 en Pages/workerd sobre export normal del candidato, Auth/PostgREST mock y PG17.11 sintético; Chromium 1228 headless, diez capturas y vídeo, retries 0. Los hashes actuales de Admin login/admin-page coinciden con R146. | Sin cuenta/correo real ni Auth remoto. Evidencia R146 `onboarding-summary-r146.json`, topología [R8](h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md) y aclaración de R6 en [R6](h3req1_g09_onboarding_r6_windows_access_2026-10-11.md). |
| LOCAL-12 Cola Admin | H3-UAT-013..017 R27/R28 y ampliación H3-UAT-017 R83. **Completo para el fixture local actual.** | R83 PASS 3/3 viewports, 21 aserciones por vista: 26 resultados persisted, ventanas cursor 20+6 sin solape, restauración de orden, filtro combinado `draft/pending` con 9 filas, paginación oculta para una sola página y reset completo. | Sin acción pendiente para la cola del fixture actual. No infiere volumen productivo ni rendimiento global. Evidencia [R77–R83](h3req1_g09_local_acceptance_delta_r77_r83_2026-10-11.md). |
| LOCAL-13 Edición/ownership/auditoría | H3-UAT-006..010, 018, 022..027, 049; R29 caso 007; R58 H3-UAT-050; PG17 R7; R90/R91/R108. **Completo en el fixture sintético actual.** | R108 H3-UAT-049 pasó 3/3 viewports, 129/129 aserciones: edición y persistencia de los 13 campos, valores y fuentes pipeline conservados, auditoría actor/fecha/antes/después. R58 050 cubre ownership; R90 discard/no-op; R91 conflicto de versión y restauración; R7 atomicidad PG17. | Sin pendiente funcional dentro del fixture actual; el alcance es sintético y local. Evidencia [R107–R108](h3req1_g09_local_acceptance_delta_r107_r108_2026-10-11.md), [R58](h3req1_g09_local_acceptance_delta_r58_2026-10-11.md), [R84–R90](h3req1_g09_local_acceptance_delta_r84_r90_2026-10-11.md) y [R91](h3req1_g09_local_acceptance_delta_r91_2026-10-11.md). |
| LOCAL-14 Vista previa | H3-UAT-049; R28/R30, preview R58 y R90. **Completa para el contrato local del preview Admin.** | R90 3/3 viewports confirma contenido poblado y parcial, fallback visible `Consultar` al vaciar fecha opcional, ausencia de `null`/`undefined`, ajuste al viewport, descarte/version intacta y luego save/publicación/lectura pública. 32/32 aserciones por viewport. | Sin pendiente de preview en el fixture actual; estados de carga/error del catálogo siguen en LOCAL-02/03. Evidencia [R84–R90](h3req1_g09_local_acceptance_delta_r84_r90_2026-10-11.md). |
| LOCAL-15 Disponibilidad/publicación | H3-UAT-006, 019, 025, 049/R30; SQL editorial PG17 R7; C03 integrado R51. **Completo para el contrato local de evidencia/publicación.** | Inputs del harness SQL actual cotejados con R7; `h3_pg17_harness_ok`. Caso UAT 049/R30: rechaza URL no HTTPS, observación futura, evidencia expirada y >90 días sin mutar estado/versión/auditoría; acepta límite inclusivo de 90 días; clearing/unpublish; publicar sin evidencia vigente es rechazado; lector efectivo solo contiene curso elegible. La compatibilidad legacy (fallback/ocultamiento por estado) está en PG17 harness. | Ninguna prueba funcional necesaria de esta área en el alcance sintético vigente. Mantener renovable si cambian migración, harness o caso 049. Evidencia: manifests R7, UAT R30 y [R51 integrado](h3req1_c03_integrated_run_2026-10-10_r51.txt). |
| LOCAL-16 Reflejo entre consumidores | H3-UAT-049, 051..055, 065/R119, R51, R74, R108, R141/R142 y H3-UAT-072/R146; R41 static fixture. **Completo para publicación/rebuild local.** | R108 refleja edición del mismo ID en Admin/lector/listing/detalle/compare tras reload. H3-UAT-072/R146 verifica la misma identidad en listing/detalle tras mutación y rebuild normal, en 3/3 viewports. El artifact servido tiene 201/201 hashes y las 61 fuentes web actuales coinciden (R162). R141/R142 cotejan PG17→API→detail→artifact→listing. | No acredita purga/invalidation CDN ni distribución remota. Evidencia `onboarding-r146/uat072-current/`, R162 artifact/source checks, [R107–R108](h3req1_g09_local_acceptance_delta_r107_r108_2026-10-11.md) y [R140–R142](h3req1_g09_local_acceptance_delta_r140_r142_2026-10-11.md). |
| LOCAL-17 Seguridad y contratos | G03/G08, R51, R58 H3-UAT-050, R135 H3-UAT-070 y R174–R176. **Completa para los controles locales probados.** | R174 detecta blobs transitorios en cinco escenarios de historia. R175 prueba archivo de worktree, índice staged, padre symlink rechazado, symlink final sin seguir destino externo y redacción. R176 añade 4 asignaciones opacas a variables sensibles y exige allowlist para helper/pre-push. 72 contratos Python, ShellCheck y actionlint 1.7.7 pasan. R51 prueba gateway/replay/suspensión/cuotas; R135 confirma rechazo 429 sin mutación y sesión preservada: 3/3 viewports, 24/24 assertions. | No queda prueba funcional local de esta área; la revisión final del scope se registra en LOCAL-23. YAML local no acredita enforcement remoto; CI y controles live no se ejecutaron. Evidencia [R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [R175](h3req1_g08_credential_tree_symlink_r175_2026-10-11.md), [R176](h3req1_g08_scanner_named_credentials_ci_allowlist_2026-10-11.md), R51, R58 y R135–R139. |
| LOCAL-18 Runtimes e integración | S18 snapshot, S16 Pages/workerd, R51 C03 integrado. **Completo para los gates runtime G05/G06/G07.** | Snapshot 17/17 sources + manifest; healthz real; R51 PASS integrado Pages/workerd, Edge, PG17 y PostgREST con manifiesto de 128 rutas; los inputs R51 siguen coincidiendo. | Ninguna acción de gate runtime pendiente. Revalidar solo si cambia un input runtime/integración; R2 pipeline walk no reemplaza R51 ni certifica runtime adicional. |
| LOCAL-19 Fallos/persistencia/recuperación | R51 C03, R2/R7/R10/R12/R18 pipeline, R135/R139/R140/R147 y R161. **Completo para los escenarios sintéticos declarados.** | R161 renueva discovery checkpoint/resume y 503/recovery de cleansing/enrichment, más sync 503/requeue; persiste el mismo flujo hasta courses en PG17.11/PostgREST. R51 cubre suspensión/dispatcher/finalizadores/drift/runtime recovery; R135/R139 cuota y Auth fail-closed; R140 atomicidad de cleansing. | No se probaron proveedores externos, LLM/embedding ni writes cloud. Los fallos son fixtures locales controlados. Evidencia R161 `run-r10.log`/`exit.txt`, [R51 integrado](h3req1_c03_integrated_run_2026-10-10_r51.txt), [R135–R139](h3req1_g09_local_acceptance_delta_r135_r139_2026-10-11.md) y [R140–R142](h3req1_g09_local_acceptance_delta_r140_r142_2026-10-11.md). |
| LOCAL-20 Responsive/accesibilidad | R41 H3-UAT-040; R83 H3-UAT-017; R113 H3-UAT-066; R124/R129 H3-UAT-068; R126 H3-UAT-069; R128 renovación H3-UAT-017. **Completa para las superficies de aceptación actuales.** | Teclado y desplazamiento de membresías R41; campos editoriales R113; filtros/paginación de cola R128 (26/26 por viewport); acciones/confirmaciones invocadas por teclado, feedback anunciado y contraste medido en la página de membresías R129 (15/15 por viewport); acciones del comparador R126 (6/6 por viewport). Capturas en los tres viewports y vídeo desktop en cada renovación focal. | Sin pendientes funcionales en las superficies actuales de la matriz. Las muestras de contraste cubren los elementos enumerados por H3-UAT-068, no todas las páginas ni una certificación WCAG global. Evidencia [R113–R116](h3req1_g09_local_acceptance_delta_r113_r116_2026-10-11.md), [R123–R126](h3req1_g09_local_acceptance_delta_r123_r126_2026-10-11.md) y [R127–R129](h3req1_g09_local_acceptance_delta_r127_r129_2026-10-11.md). |
| LOCAL-21 Calidad/build/dependencias | G03 y G08 completos para los checks locales aplicables. **Vigente completo con límites declarados.** | G08: pytest R160 **337 passed/4 skipped/1 warning**; contrato credenciales R159 **45/45**; scanner histórico R174 `history=5` + 70 contratos relacionados PASS; writer scan PASS; ESLint exit 0 (9 warnings conocidos); Next typegen/TypeScript PASS; 176 Python AST; npm audit full/prod sin vulnerabilidades; actionlint/ShellCheck/workflow/scope guard reutilizados con hashes compatibles. Build normal R69: 33/33 páginas, 17 rutas sintéticas y 206 archivos con manifest verificado; R146 renovó el build normal de 201 archivos verificados; builds anteriores R9/R10 17/17 páginas, 126 artefactos. Node syntax y scan de los inputs delta PASS. | Los cuatro skips y pruebas que requieren credenciales/cloud/live quedan NO-EJECUTADOS/skip, no PASS. Evidencia: [G08 reconciliation y R174](h3req1_g08_credential_history_scan_r174_2026-10-11.md), [R64–R70](h3req1_g09_local_acceptance_delta_r64_r70_2026-10-11.md), R159–R162. Esta área completa no cierra G09. |
| LOCAL-22 Rendimiento/recursos | H3-UAT-063 R79, H3-UAT-017 R83 y health S16. **Completo para medición descriptiva local.** | Diez muestras independientes del recorrido H3-UAT-063, 30/30 viewport PASS, retries 0; p50/p95 registrados por viewport para DCL, load, recursos same-origin y duración home→detail→back→forward. Comparación descriptiva contra R53–R55 n=3; R83 añade tiempos de cola, no se mezcla con latencia pública. | No se declara SLA ni se extrapola a Production; no hay otra medición local pendiente dentro del objetivo descriptivo. Evidencia [R77–R83](h3req1_g09_local_acceptance_delta_r77_r83_2026-10-11.md). |
| LOCAL-23 Evidencia/aceptación | G01–G08; catálogo R28/R29/R30 y casos posteriores; R8/R146/R161/R168/R169/R173–R178 y evidencias LOCAL-01..22. **Completa en el alcance local.** | INV-008 tiene causa funcional reproducida, corrección y onboarding R8/R146 10/10. El catálogo conserva 216 PASS caso-viewport (72×3) seleccionados, conciliados entre corridas compatibles; R28/R29/R30 acreditan 189 ejecuciones; R173 renueva email/fallback/roles (6/6 viewports, 36/36 assertions, seis capturas, cero retries). R170 sigue registrado como fallo del test. R174–R176 cierran scanner y regresiones; R177/R178 registran inventario y scan final. La revisión independiente R5 pasó sin HIGH/MEDIUM ni bloqueantes. Los cuatro criterios cliente, seis pilares, transición y rollback tienen evidencia local sintética con límites documentados. | No queda cobertura local bloqueante. G10 (enforcement/CI remoto), promoción, deploy y smoke remoto quedan fuera; no se afirma PASS remoto. |

## Resultado del corte

- Catálogo visual vigente: **216/216 resultados PASS caso-viewport seleccionados**
  (72 casos × tres viewports) entre corridas compatibles, no una corrida global
  única. R28/R29/R30 concilian los primeros 189. Las renovaciones/casos
  H3-UAT-064..072 agregan resultados hasta 72 casos; R168/169 renuevan 029/072,
  y R171–R173 reemplazan 002/003 para incluir y endurecer el fallback de email
  sin sumar casos. R173 tiene 36/36 assertions y seis capturas.
  Los rojos históricos R28/R57/R63/R65/R66/R68/R71/R121/R123/R125/R170 quedan
  preservados y no se contabilizan como PASS o retries.
- G08 permanece completo para checks locales aplicables: R160 337 passed,
 4 skipped, 1 warning; R159 45/45 credenciales; R174 renueva el scanner de
 historia (cinco regresiones), 70 contratos relacionados y ShellCheck; writer
 scan, auditorías, lint/tipos/builds y workflow checks se reutilizan solo con
 inputs compatibles. Skips y controles live/cloud son NO-EJECUTADOS.
- LOCAL-01..22 acreditan sus subalcances sintéticos documentados. LOCAL-07/08/19
  usan R161 integrado PG17.11/PostgREST y R51 C03; no hay crawling, LLM,
  embeddings o writers cloud. LOCAL-13/15 cubren los ajustes editoriales en
  PG17/UAT; LOCAL-09/10 conservan HttpOnly, MFA, roles y onboarding sintético.
- INV-008 se corrigió tras reproducir el ciclo `password_pending`; R8/R146
  onboarding 10/10, cero retries. El nuevo gap del encabezado se valida en
  R171–R173: email autenticado y fallback vacío conservando roles. R173 pasó
  6/6 ejecuciones, 36/36 assertions, seis capturas y cero retries, con la
  interceptación limitada a GET same-origin loopback y query vacía. R170 fue fallo de
  sincronización del test, documentado aparte y no atribuido al producto.
- LOCAL-23 se cierra en el alcance local: el revisor independiente aprobó el
  paquete R5 exacto, los 89 paths y la matriz/cuerpo sin HIGH/MEDIUM ni
  bloqueantes. El dictamen estático no sustituye pruebas; las ejecuciones
  locales y sus límites ya están reconciliados en LOCAL-01..22. G10 remoto,
  enforcement, despliegue y promoción siguen pendientes y no se cuentan como
  aceptación local.

## Corte R64–R70 — 2026-10-11

El catálogo actual contiene 64 casos y tres viewports. Se conserva la conciliación
de 189 ejecuciones PASS de R28/R29/R30 y se añade H3-UAT-064 en R70 (3/3);
H3-UAT-049 se revalida en R70 (3/3) y sustituye su resultado visual previo.
Así se documentan 192 combinaciones caso-viewport PASS seleccionadas entre las
corridas, no una ejecución global única. Los fallos R63/R65/R66/R68 se conservan
como diagnósticos de test/fixture; R69 generó el conjunto estático completo y R70
pasó ambos casos afectados. Las capturas, vídeo y hashes están en
[evidencia R64–R70](h3req1_g09_local_acceptance_delta_r64_r70_2026-10-11.md).
G09 permanece parcial por las demás áreas LOCAL-01..23.

## Delta vigente R71–R72 — 2026-10-11

Se añadió H3-UAT-065 al runner canónico para resolver el hueco de muestreo
estático: cinco rutas representativas (ULima, PUCP, UPC, USIL y UTP), datos
REST sintéticos, páginas de detalle y etiquetas de institución. R71 pasó 3/3,
pero una revisión detectó que su aserción de aislamiento era tautológica; se
preservó y dejó de contarse. Se cambió a comprobar cero solicitudes de recursos
externos no-REST y se revalidó solo ese caso como R72.

R72 terminó PASS en desktop/tablet/móvil: 3/3 ejecuciones, 69/69 aserciones,
cero errores de consola, cero requests fallidos, cero recursos externos
bloqueados y cero retries. El runner atendió 20 solicitudes por vista desde
fixtures sintéticos. Pages/workerd Miniflare sirvió el export normal R69; Chromium
1228 corrió headless dentro del contenedor R12. El proceso y el puerto 3370
temporales se retiraron al terminar; el R12/PG17 y el proxy Windows quedaron
intactos. Tres capturas están en
`h3req1_g09_uat_2026-10-10_r4/uat-static-details-r72/`; hashes y logs se fijan
en el manifiesto de alcance R2. R71 permanece preservado, pero no se suma al
catálogo PASS.

El catálogo vigente pasa de 64 a 65 casos y queda en 195 combinaciones
caso-viewport PASS seleccionadas (189 previas, R70 añade H3-UAT-064 3/3 y
renueva H3-UAT-049 3/3; R72 añade H3-UAT-065 3/3). Es una conciliación entre
corridas, no una ejecución única. El nuevo caso fortalece LOCAL-02/03/16, que
siguen parciales por estados/error, estratos de datos/assets y coherencia de un
mismo registro PG17 entre consumidores. G09 sigue parcial; métricas sin cambio:
80% histórico (8/10) y 88,89% local (8/9).

## Corte histórico R72 — tareas pendientes antes de R75, posteriormente conciliadas

Esta lista conserva el estado de trabajo tras R72; no representa pendientes
vigentes. Los deltas R75–R178 que siguen a esta sección documentan su resolución.
En particular, LOCAL-02/03 se completaron con R116, R119 y R146: estados
poblado/vacío/503, deep links propios de las 16 rutas en cinco instituciones,
misma identidad tras mutación y rebuild normal, y hashes del artefacto verificados.

Las referencias a casos existentes abajo son base preservable; cada tarea
renueva solo la cobertura que aún falta. Ninguna fila se marca PASS por estar
descrita. Las pruebas nuevas se agregan al runner/H3 fixtures sintéticos y se
ejecutan en Docker con cero retries.

| Tarea | Áreas | Base existente | Próxima ejecución y predicado de cierre |
|---|---|---|---|
| G09-T01 Fixture y estados | LOCAL-01 | PG17 R12, pipeline R2/R18, H3-UAT-049/065, R141/R142 | **Completa para fixture sintético actual:** 31 PG17 rows, 16 elegibles cotejadas con lector/detail/artifact/listing, 15 no elegibles excluidas/404, y listing paginado 12+4 sin duplicados. |
| G09-T02 Rutas y elegibilidad | LOCAL-02/03 | H3-UAT-043/049/054/057/065, R69/R72 | **Cerrada después de este corte:** R116 cubre catálogo poblado, vacío y API 503 con fallback; R119 recorre los 16 deep links propios en cinco instituciones y comprueba identidad/canonical/JSON-LD; R146 valida la misma identidad tras mutación y rebuild normal. Ver filas LOCAL-02/03 y evidencias R116/R119/R146. |
| G09-T03 Asesoría | LOCAL-06 | H3-UAT-056 R77 + CTA interno R30 | **Completa:** canal cerrado, sin formulario/captura ni escritura externa; CTA lleva al detalle local esperado. |
| G09-T04 Discovery y pipeline | LOCAL-07/08/19 | `tests/test_h3req1_local_pipeline_walk.py`, R18 24/24, R2, R73, R140, R147 y R161 | **Completa en PG17/PostgREST sintéticos:** checkpoint/resume, handoff, cleansing/enrichment 503 recovery, sync requeue y estado persistido de punta a punta. Sin crawling, LLM, embeddings o writers externos. |
| G09-T05 Sesión y MFA | LOCAL-09 | H3-UAT-001..005/028..034, R51, G03 BFF UAT, R75/R76/R133/R139, R8/R146 | **Completa para el fixture local:** sesión/MFA, HttpOnly y chunks, expiración, refresh paralelo sintético y ciclo INV-008 corregido; R139 y R8/R146 pasan. Auth remoto y cuenta real fuera del alcance. |
| G09-T06 Membresías concurrentes | LOCAL-10 | H3-UAT-022/026/040, R41/R93/R94 | **Completa en fixture local:** UI/BFF mantiene rol/estado; R93 prueba solicitudes paralelas del actor; R94 prueba dos actores sintéticos simultáneos, último-admin guard y restore en PG17. |
| G09-T07 Cola Admin | LOCAL-12 | H3-UAT-013..017 y R83 | **Completa para R12:** conteos, páginas persistidas, filtro combinado, cursor estable, estado final y reset en tres viewports. |
| G09-T08 Editor y auditoría | LOCAL-13 | H3-UAT-006..010/018/022..027/049/050, PG17 R7, R58/R90/R91/R108 | **Completa en el fixture actual:** R108 cubre los 13 campos, origen pipeline, persistencia/auditoría y reflejo público; R91 conflicto, R58 ownership y R7 atomicidad. |
| G09-T09 Preview | LOCAL-14 | H3-UAT-049, R28/R30, R90 | **Completa:** tres viewports, contenido parcial, fecha vacía/fallback, layout, discard sin persistir y save/recorrido público pasan en R90. |
| G09-T10 Reflejo público | LOCAL-03/16 | H3-UAT-049/051..055/065/071/072, R51, R69/R72/R119, R74, R108, R141/R142, R146 | **Completa para publicación/rebuild local:** el mismo UUID sintético mutado aparece en listing y detalle del artifact normal R146; el artifact pasó 201/201 y las fuentes 61/61. Sin claim de CDN/remoto. |
| G09-T11 Negativos de seguridad | LOCAL-17 | R51, G08 scanner/writer scan/audits, H3-UAT-050, R135, R174–R176 | **Completa para los controles locales declarados:** firma/replay/nonce, suspensión, roles, gateway, cuota y no mutación se cubren en R51/R135; historia/worktree/index, symlinks, valores opacos y allowlist se renuevan R174–R176. Revisión de scope final se registra en T15. |
| G09-T12 Fallos y recuperación | LOCAL-19 | R51, R147/R161, tests de suspensión/recovery R2, R135/R139, R140 | **Completa para escenarios locales sintéticos:** persistencia/checkpoint y recovery de discovery/cleansing/enrichment/sync en R161, además de C03/suspensión, cuota/Auth fail-closed y atomicidad. No extrapolar a proveedores externos o fallos no ensayados. |
| G09-T13 Responsive y accesibilidad | LOCAL-20 | R41, R83/R128, R113, R126, R129 | **Completa en superficies actuales:** teclado/foco en membresías, campos editoriales, filtros/paginación de cola y comparador; acciones/confirmaciones por teclado; feedback anunciado; muestras de contraste por viewport. Sin afirmación de auditoría WCAG global. |
| G09-T14 Rendimiento | LOCAL-22 | H3-UAT-063 R79 (10 muestras), health S16 | **Completa en alcance descriptivo local:** p50/p95 y baseline local documentados; sin SLA. |
| G09-T15 Aceptación final | LOCAL-23 | G01–G08, atestación sanitizada, matriz y catálogo R28/R29/R30, R8/R146/R161/R168/R169/R173–R178, review independiente R5 | **Completa para cierre local:** 23 áreas y cuatro criterios cliente reconciliados; R5 revisión independiente PASS, sin HIGH/MEDIUM ni bloqueantes. G10 CI remoto y promoción permanecen separados. |


## Delta R75 — conciliación de subcasos de sesión/MFA — 2026-10-11

La matriz anterior listaba como faltante la sesión A no renovando B, expiración
de actividad y varios flags, aunque el runner BFF de G03 ya las ejecuta. Se
comparó el SHA-256 actual de `tests/h3_admin_bff_mock_uat.mjs`
(`378f753d0de940ad5e023123d735d35429678e73498c458a5270b75da05dd3f6`) con
`h3req1_g08_candidate_final_2026-10-11_r1/source-inputs-r4.sha256`: coincide.
La nota de ejecución G03 registra 90 checks, 6 rechazos de cookie de actividad,
1 rebind tras MFA, 4 rechazos de origen y 4 de configuración de firma. Por
coincidir el input y existir resultado vigente, no se repitió la suite.

El código cubre cookie de actividad ligada a session_id, timestamps raw/tampered,
actividad expirada y futura, flags `HttpOnly`, `Secure`, `SameSite=Lax`,
`Max-Age`, limpieza y rechazo del cookie A cuando Auth devuelve la sesión B.
La sesión se valida con un Auth mock en un test Node, sin navegador ni servicio
remoto. No prueba expiración real de Auth/browser, Auth cookies multi-chunk ni
una carrera de refresh observada end-to-end. G09-T05/LOCAL-09 avanzan, pero siguen
parciales; no se ejecutó un caso nuevo y las métricas de gates no cambian.
Evidencia primaria: [cookie ligada a sesión](h3req1_activity_cookie_session_binding_2026-10-10.md).


## Delta R76 — logout de cookies Auth multi-chunk — 2026-10-11

Se amplió solo el test sintético `tests/h3_admin_bff_mock_uat.mjs` para enviar
logout con cookie Auth base, chunks `.0/.1/.2`, code-verifier base y chunks
`.0/.1`; el caso exige que los siete nombres reciban expiración. SHA del runner
`7c1fefd3f8743a1b3a898bf4a1b200b7c2f486380bc293045760435644065b40`. La
implementación bajo prueba (`web/functions/_lib/admin-bff.ts`) no cambió.

En `studiamatch-dev` (`500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`,
imagen `studiamatch-h3req1:20261009-v3`, healthy), el runner vio el mismo SHA
montado en `/app`. Se ejecutó con `env -i` (solo PATH/HOME), Node y mocks de Auth,
cuota y RPC: exit 0, **96 checks**, `authCookieNamesCleared=7`, cero retries.
No se abrió navegador, no hubo Auth/DB reales ni operaciones remotas. Log de
salida allowlisted: `h3req1_g09_local_acceptance_r76/bff-multichunk-r76.log`.

Checks afectados después del cambio: `node --check` y credential scanner del
runner pasan en Docker. `git diff --check` dentro del contenedor no pudo leer el
worktree porque el puntero Git resuelve a metadata del host (exit 128); el mismo
chequeo read-only desde el checkout WSL terminó exit 0. Un preflight anterior
con marcador literal de SHA se detuvo antes de Node; corregido el pin, source
match y ejecución pasaron.

LOCAL-09/G09-T05 avanza en cleanup multi-chunk; siguen faltando expiración
real de Auth y carrera de refresh en browser. No cambia comportamiento de
producto ni porcentaje de gate. Evidencia y límites no certifican servicios
remotos.


## Delta R77–R83 — 2026-10-11

Resultados, fallos preservados, server/browser, IDs del entorno, agregados PG17,
hashes, capturas y vídeo están en [evidencia R77–R83](h3req1_g09_local_acceptance_delta_r77_r83_2026-10-11.md). R77–R79 añadieron cobertura de asesoría, navegación/accesibilidad básica y diez muestras de rendimiento. R80–R82 quedan como rojos de test/sincronización: el componente oculta paginación para una sola página; el test anterior no esperaba el resultado de filas y la variante sin reset llegó al rate limit sintético de MFA. R83 corrige únicamente la espera y locator del runner, usa el reset de fixture requerido y pasa H3-UAT-017 en 3/3, 63 aserciones, con tres capturas y un vídeo.

LOCAL-06, LOCAL-12 y LOCAL-22 quedan completos dentro de sus alcances sintéticos/descriptivos. LOCAL-01/02/03/20 avanzan pero siguen parciales. El catálogo conserva 65 casos; la conciliación histórica 195 PASS seleccionados continúa como selección de corridas previas. R77–R83 son ejecuciones adicionales/renovaciones, no una corrida completa del catálogo. El total de gates permanece 80% histórico (8/10) y 88,89% local (8/9); G09 parcial, sin GO.

## Delta R84–R90 — preview/editor — 2026-10-11

R90 renovó H3-UAT-049 en el candidato montado en R12: 3/3 viewports, 32
aserciones por viewport, 96 total, cero retries/errores de consola/requests.
Confirma la fecha vacía con fallback visible `Consultar`, ausencia de
`null`/`undefined`, ajuste al viewport, descarte sin persistencia y sin
auditoría, botón de guardado deshabilitado con draft limpio, y el flujo de
guardar/publicar/leer el mismo registro sintético por listado/detalle/compare.
Capturas/vídeo y hashes están en
[evidencia R84–R90](h3req1_g09_local_acceptance_delta_r84_r90_2026-10-11.md).

R85/R86/R87/R89 se conservan como fallos del test con causas de selector,
observabilidad y expectativas de API visual. R87 observó `inputEmpty=true` y
`textContent=InicioConsultar`; R90 comprobó el nodo `Consultar` exacto y visible.
R89 observó el guardado presente pero deshabilitado, sin badge y sin delta de
auditoría. No se atribuye un defecto a producto.

LOCAL-14 / T09 se marca completo para el contrato del preview Admin del fixture
actual. LOCAL-13 / T08 incorpora descarte y no-op sin cambios; sigue parcial por
matriz vigente de grupos/tipos de campo y reconciliación focal de conflicto/
ownership. Los gates y métricas no varían: 80% histórico (8/10), 88,89% local
(8/9); G09 continúa parcial y G10 remoto sigue pendiente.

## Delta R91 — conflicto concurrente de editor — 2026-10-11

H3-UAT-023 pasó 3/3 viewports, 8/8 assertions cada uno. Dos escrituras sobre la
misma versión sintética produjeron un ganador y un conflicto; la recarga mostró
el override y la fuente del pipeline, y el cleanup verificó/restauró el estado
original. Capturas y hashes: [R91](h3req1_g09_local_acceptance_delta_r91_2026-10-11.md).
LOCAL-13/T08 avanza en conflicto, pero sigue parcial por la matriz de grupos y
tipos de campo. No cambian los porcentajes de gate.

## Delta R92–R93 — concurrencia de membresía — 2026-10-11

R92 no llegó al nuevo predicado porque se sirvió el export R12 anterior, que no
contenía la región accesible presente en el código y en el build R41. R93 usó
Pages/workerd R41 y PG17.11 sintético R12: 3/3 viewports, 19/19 assertions cada
uno; dos mutaciones simultáneas del mismo actor se serializaron. R94 añadió dos
actores sintéticos con transacciones PG17 independientes y concurrentes: una
desactivación ganó, la segunda fue rechazada, se mantuvo un admin activo y luego
se restauraron ambos miembros. LOCAL-10/T06 queda completo en fixture local;
ver [R92–R93](h3req1_g09_local_acceptance_delta_r92_r93_2026-10-11.md) y
[R94](h3req1_g09_local_acceptance_delta_r94_2026-10-11.md).
