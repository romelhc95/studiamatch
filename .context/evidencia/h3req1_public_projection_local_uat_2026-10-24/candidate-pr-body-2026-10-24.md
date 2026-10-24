## Resumen

Corrige la interpretación de duración compuesta en el catálogo y el overflow móvil del panel de filtros/footer, y remedia de forma exacta los dos gates que bloquean #503: alcance protegido y selección de fuentes R20. Cubre H3-CA4.9 y H3-CA4.11 en validación local; no cierra H3REQ1 ni acepta Development. H3-UAT-059 sigue bloqueado: el primer runner no pudo iniciar por Chromium incompatible; la única instalación A2 autorizada falló por DNS y no se lanzó el runner.

Rama `feat/h3req1-public-duration-mobile-20261024`, base `desarrollo` en `1c69b94606795e33c9fee82e8a8e803f3104c566`; último head remoto antes de esta corrección documental `a379847f6acc410d5224823c6d5311736a5de13a`. El manifiesto conserva 44 paths exactos. El delta documental local corrige cuatro paths incluidos y este borrador de descripción; los cambios WIP ajenos se mantienen fuera del paquete. El manifiesto exacto es [`candidate-pr-scope-2026-10-24.json`](candidate-pr-scope-2026-10-24.json). No se adjunta documento privado del cliente.

## Evidencia De Este PR

- Parser del candidato exacto: 11/11 PASS en Docker; comparación determinista anterior de 10.000 inputs no mostró diferencias y la prueba de 2.000 aclaraciones cero valida recorrido acotado.
- H3-UAT-058 / H3-CA4.11: PASS canónico local anterior reutilizable para este delta, tres viewports más comprobaciones estrechas de 320 px. No se repitió.
- H3-UAT-059 / H3-CA4.9: el intento canónico inicial tuvo 0/3 viewports, 0 capturas y 0 resets porque Playwright 1.63.0 requiere Chromium 1243 y el runtime tenía 1228. Luego se consumió el JIT A2 en una única invocación del instalador, que falló con `EAI_AGAIN` al resolver `cdn.playwright.dev`; no se invocó el runner A2, no hubo resets ni escrituras PG17. El fixture sembrado permanece preservado. Resultado actual: bloqueado antes de ejecutar el caso, no PASS/FAIL funcional. No se repetirá instalación ni runner con este permiso.
- B: regresión exacta del guard PASS en Docker con los 29 paths literales cotejados contra el manifiesto; negativos de rutas PASS. R20 pasó `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`: 735/735 fuentes estructurales, 725/735 con dimensiones completas, 115/115 documentos activos, 433/433 históricos enlazados, 9.270 links y 4.630 anchors. Tras corregir la referencia al stdout excluido, R20 se volvió a ejecutar y pasó con los mismos conteos; credential scan Docker PASS en los 44 paths del manifiesto. `actionlint 1.7.12`, `ShellCheck 0.11.0`, parser 11/11, regresión del guard y `git diff --check` PASS en Docker según la evidencia local.
- Browser Chrome Windows local previo a `http://localhost:3020/`, 320 CSS px: documento, body y footer 320 px; footer x=0..320; popover x=16..304. Es evidencia local, no Deployment de Pages.

La evidencia estructurada del intento 059 se conserva sanitizada en el worktree, bajo `run-canonical-058-059-footer-20261024/h3-uat-059-canonical-20261024-run01/evidence/`; artefactos/logs completos de ejecución están excluidos del paquete. El PASS anterior en `run-canonical-058-059-footer-20261024/h3-expanded/` se preserva y no se atribuye al parser actual.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Duración pública | Normaliza unidades españolas/inglesas, excluye números sin unidad de duración, suma unidades explícitas y toma el límite inferior del rango; evita recorrido cuadrático por aclaraciones repetidas. | Filtros, facetas y “Actualizarme”. | Parser 11/11 Docker; H3-UAT-059 canónico fallido antes de viewport, requiere nueva ejecución. |
| Panel y footer | Ancla “Más filtros” a la fila primaria, centra/restringe el panel móvil y permite wrapping del footer. | Catálogo, detalle estático y layout compartido. | H3-UAT-058 PASS previo reutilizable; DOM local medido a 320 px. |
| Alcance/documentación CI | Añade solo 29 literales exactos al guard, aserción de igualdad de la lista, workflow R20 y parser test en static-build. R19 queda intacto. | Control protegido, gate documental y parser en CI. | Guard, actionlint y ShellCheck PASS en Docker; R20/credential scan con resultado final a consignar al finalizar los gates. |
| UAT/fixtures | Conserva correcciones de aserción de paginación y fixture mixto híbrido; no cambia el endpoint de reset. | Runner público local y seeds sintéticos. | 059 permanece bloqueado antes de viewport: instalación de Chromium falló por DNS; runner A2 no invocado, cero resets adicionales. Fixture PG17 preservado. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | Parcial local | 058 conserva PASS reutilizable; 059 no ejecutó assertions por el fallo de Chromium. Aceptación Development pendiente. |
| Escalabilidad | Parcial local | Parser de recorrido acotado; no se ejecutó benchmark del catálogo remoto. |
| Seguridad | Revisión de código completa, alcance local | Codex Security `85681fc2-8e7d-4da5-875f-fa0395676069`: 0 findings, 4 superficies. El snapshot no incluye el assertion exacto añadido posteriormente; se revisó manualmente y pasó Docker. No acredita runtime remoto. |
| Mantenimiento | Parcial local | Relación fuente–prueba y enlace corregidos; gate documental R20 renovado. |
| Calidad | Parcial local | Parser, guard, YAML/shell y builds previos; 059 canónico incompleto por fallo de browser launch. |
| Rendimiento | Parcial de algoritmo | Se eliminó caso cuadrático comprobado; no se midieron métricas de usuario o catálogo remoto. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Mantiene formatos de duración existentes y acepta unidades compuestas; añade literals de path compatibles. | Parser focal y guard regression local. |
| compatibilidad | Mismo parser para filtros, facetas y “Actualizarme”; mantiene layout compartido y R19 histórico. | 058 reutilizable; 059 pendiente de run válido. |
| deploy | No existe despliegue de este delta en Development. | Publicación de sucesor #503 requiere autorización humana; push podría producir Preview automático. Merge y deploy manual separados. |
| contract | Repetir 059 tras una corrida local válida; tras integración/despliegue exacto, repetir los casos afectados y smoke general. | Pendiente SHA/deployment final. |
| Rollback/recuperación | Revertir como unidad parser/consumers, panel/footer y los literales/workflow; preservar la DB UAT sembrada. | No limpiar DB ni revertir datos sin JIT separado. |
| No degradación funcional | Parcial: parser focal y UI local; caso canónico 059 incompleto y acceptance Development pendiente. | No se transfiere PASS local a remoto. |

## Evidencia Para Cliente

H3-CA4.9/H3-CA4.11 en la atestación/matriz sanitizada y relaciones de `.context/trazabilidad/`. 058 conserva su evidencia previa; 059 falló antes de los asserts y queda pendiente de runtime compatible. No hay resultado remoto para este delta, waiver ni GO contractual.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS, exit 0, 44/44 paths del manifiesto exacto | Docker local | Se escaneó la inclusión del paquete; no se abrió `.env` ni se leyeron valores secretos. |
| Python tests | N/A | No cambió Python | Sin efecto en runtime Python. |
| Python compile | N/A | No cambió Python | Sin efecto en runtime Python. |
| PostgreSQL DB Change Gate | No se modificó schema de producto. Los seeds autorizados sí se aplicaron al PG17 de UAT; postflight read-only: public 13 relaciones, auth/private presentes, pipeline 30, editorial 31, public effective 16. | Docker, fixture descartable local | Sin cleanup. El runner falló antes del viewport. No es Supabase remoto ni gate del workflow. |
| ESLint | PASS previo, exit 0, 0 errores y 9 warnings en líneas no modificadas | Docker local | Cambio B no modifica JS/TS de producto. |
| TypeScript | PASS previo, exit 0 | Docker local | Parser/UI actuales del candidato; cambios posteriores limitados a guard/docs/workflow/tests. |
| Static build | PASS previo con `npm run build:mock` | Docker local | Build usado en las pruebas previas; UAT 059 no alcanzó el browser. |
| actionlint / ShellCheck | PASS, exit 0 | Docker local | actionlint 1.7.12; ShellCheck 0.11.0 sobre guard y regresión. Parser 11/11 y git diff --check también PASS. |
| UAT/runtime/integración | 058 PASS reutilizado; 059 bloqueado antes de viewport | PG17 y runner Docker local | Intento inicial sin Chromium 1243; el instalador del JIT A2 falló con DNS `EAI_AGAIN`. El runner A2 no se ejecutó: 0/3 viewports, 0 capturas, 0 resets del runner, 0 retries del runner. JIT consumido; no reapply SQL. |
| security-audit / CI independiente efectivo | Run `40138547422`: 14 success, 2 failure, 2 skipped. `Protected Path Integrity` pasó; fallaron `Documentation Source Registry` y el agregado `security-audit` en el HEAD previo a esta corrección documental. | GitHub Actions, SHA remoto `a379847f6acc410d5224823c6d5311736a5de13a` | El registry reportó como faltante un stdout local excluido del paquete. El registro ahora enlaza el test fuente y el resumen versionado. Falta el run nuevo tras publicar el delta. `PWI Worker Contract` es un check de Actions y no demuestra el check del GitHub App. |
| CodeQL si aplica | PASS | GitHub Actions, SHA remoto `a379847f6acc410d5224823c6d5311736a5de13a` | Check CodeQL success en el HEAD consultado; no acredita runtime remoto. |
| Cloudflare Pages / smoke preview | Preview automático anterior PASS, deployment `2ede8537-e9d1-4202-80a1-1feee6ec9350` (`https://2ede8537.studiamatch-aty.pages.dev`) | Pages Preview, SHA remoto `a379847f6acc410d5224823c6d5311736a5de13a` | No es Development y no incluye las correcciones documentales locales; no se realizó smoke en este Preview. |
| Browser snapshot si aplica | PASS local previo | Chrome Windows MCP / `http://localhost:3020/` | 320 CSS px, footer y popover medidos; no es Development. |
| security-auditor | 0 findings para snapshot local; follow-up del assertion exacto revisado a mano | Codex Security | Scan `85681fc2-8e7d-4da5-875f-fa0395676069`; digest `6f2fe32f…f87bf0da`. No es runtime remoto. |
| Documentación / trazabilidad / fuente cliente | PASS R20 local; R19 histórico preservado. | Docker local | DOC_SELF_TEST_PASS/DOC_GATE_PASS; 735/735 fuentes, 725/735 dimensiones completas, 115/115 docs activos, 433/433 históricos enlazados, 9.270 links y 4.630 anchors. Seis verificaciones remotas del inventario siguen pendientes. |

## Seguridad Y Datos

- [x] No se añadieron credenciales, firmas, JWT, cookies, tokens ni datos personales en código/evidencia. El token sintético de reset no se leyó ni imprimió.
- [x] Auth/RLS/roles/MFA/último administrador y configuración remota no cambian en este paquete.
- [x] Codex Security reporta 0 hallazgos en el snapshot y alcance indicados; la revisión del assertion agregado post-snapshot se documenta por separado.
- [x] Sin escrituras Supabase remotas, Production, restore, schedules o writers.

## Alcance Y Limites

- [x] Vincula H3REQ1 y H3-CA4.9/H3-CA4.11; no incluye el documento cliente privado.
- [x] Scope de 44 paths exactos; 63 paths WIP ajenos preservados fuera del paquete y un archivo `.links` parcial generado por la instalación A2 también queda preservado/excluido.
- [x] Fallos históricos y el intento actual fallido se conservan; el detalle actual queda en el addendum A/B.
- [x] Sin merge/deploy/promoción ni cambios fuera de Development. La aprobación A/B fue solo local y está consumida.

## Checklist Tecnico

- [x] Guard regression, actionlint, ShellCheck, parser 11/11, R20 y credential scan 44/44 ejecutados en Docker; resultados reales registrados en el addendum.
- [x] Fichas, fuentes/consumidores y transición/rollback enlazados.
- [x] Seguridad revisada localmente con el límite del snapshot declarado.
- [ ] H3-UAT-059 válido: el JIT A2 quedó consumido al fallar la descarga CDN por DNS; falta resolver el acceso al artefacto Chromium mediante un alcance aprobado nuevo antes de un único runner.
- [ ] Renovar los checks remotos sobre el commit que incluya este delta; el último run citado pertenece al head previo. H3-UAT-059 sigue bloqueado antes de los asserts y requiere una decisión separada sobre el artefacto Chromium compatible.
- [ ] NO-GO Development; falta aceptación remota completa.
