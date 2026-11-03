## Resumen

Corrige el rótulo del filtro largo para que coincida con su límite real (`> 6 meses`) y actualiza las expectativas canónicas de los filtros corto/medio. Incluye la corrección responsive de panel/footer y el parser de duración ya presentes en #503. Cubre localmente H3-CA4.9 mediante H3-UAT-059 y H3-CA4.11 mediante H3-UAT-058. No cierra H3REQ1 ni declara aceptación de Development.

Rama `feat/h3req1-public-duration-mobile-20261024`, base `desarrollo` (`1c69b94606795e33c9fee82e8a8e803f3104c566`). R12 se construyó desde el head previo del PR `6e1bd8f5ad623a44524b11391c1385c59b9a4b70`; los fuentes exactos del candidato local son `HomeContent.tsx` SHA-256 `84af11d225b18fd52e95fb54625c7014a06e6a1a31bb413d29a6a980f516ffd7` y `tests/h3_local_uat.mjs` SHA-256 `e9c2ed3a660d2c4982c7443fd4ffed0da4ab174d2e357284d5dac0026a5719bd`. El manifiesto seleccionado contiene 44 paths; el worktree preserva 88 excluidos. GitHub PR #503 identifica la revisión actual del HEAD después de cada publicación; los check-runs se deben leer siempre para ese SHA y no se heredan entre commits.

## Evidencia De Este PR

- H3-UAT-058 → H3-CA4.11, “public listing and detail fit the active viewport”: PASS local Docker, desktop/tablet/mobile, 17 assertions, incluye catálogo, detalle, panel/footer y viewport de 320 px.
- H3-UAT-059 → H3-CA4.9, “public filters apply independently and career goal matches eligible courses”: PASS local Docker, desktop/tablet/mobile, 39 assertions por viewport (117 total), cero resets y cero retries. Verifica filtros de categoría, institución, modalidad, tipo, duración, objetivo “Actualizarme”, búsqueda, estado vacío, limpieza y paginación.
- Corrida conjunta R12: 2/2 casos, 6/6 ejecuciones, 6/6 capturas, 134 assertions, cero resets, cero retries. El fixture sintético PG17 exacto estaba completo y se reutilizó; no hubo SQL ni escrituras.
- Build estático `build:mock` local y smoke de `/` y `/courses/ulima/analitica-aplicada-60000000/`: HTTP 200/200; contenido de detalle esperado.
- Chrome Windows MCP observó el candidato local por forwarder GET/HEAD a 390 px: botón accesible `Largos (>6m)` con contador, documento 390/390 y panel dentro del viewport. La comprobación exacta a 320 px procede del runner Playwright, no de esa lectura MCP.
- Resumen, hashes, fixture y límites: [acta R12](candidate-acceptance-cycle-2026-10-24.md#r12-build-local-filtros-responsive-y-verificacion-visible-2026-10-25). Los logs y capturas completas se preservan en el checkout de evidencia; el PR incluye el resumen sanitizado, no los artefactos brutos.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Duración pública | Mantiene el parser de unidades compuestas y aclara el límite visual largo como `> 6 meses`. | Facetas, filtro de duración y “Actualizarme”. | Parser 11/11 Docker anterior al delta R12; H3-UAT-059 39/39 por viewport. |
| Filtros públicos | La aserción corta espera estado vacío con este fixture; la media espera cursos de 3–6 meses; la larga excluye 6 meses. | Catálogo, filtros independientes, query/reset y paginación. | H3-UAT-059 3/3 viewports, 117 assertions. |
| Responsive público | Conserva el anclaje del panel y el wrapping del footer ya corregidos. | Catálogo, detalle y footer compartido. | H3-UAT-058 3/3 viewports, con assertions a 320 px. |
| Trazabilidad | Actualiza ficha, índice, relaciones, evidencia R12 y manifiesto R20; R19 permanece histórico. | Gate documental y relaciones fuente–componente–consumidor–prueba. | Docker `DOC_SELF_TEST_PASS` y `DOC_GATE_PASS`, con el manifiesto de selección documental exacto. |

El gate documental válido pasó con `candidate-scope-manifest.json`. Una invocación diagnóstica con el manifiesto de paths del PR imprimió `DOC_GATE_FAIL` pero devolvió exit 0 por la rama de argumentos inválidos del checker; no se contó como PASS y no se modificó ese checker, que queda fuera del diff público de este PR.

Paths: 44 incluidos, 88 excluidos en `candidate-pr-scope-2026-10-24.json`. El delta R12 tuvo 10 paths modificados; R13 actualiza dos documentos ya incluidos para registrar la recuperación de publicación. No hay paths fuera del paquete. Quedan excluidos WIP Admin/MFA/BFF/FG3/C/Auth, capturas con información personal, artefactos intermedios y `.env*`.

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | Validada local para CA4.9/CA4.11 | 058 y 059 PASS en Docker con mock y fixture sintético; Development sigue pendiente. |
| Escalabilidad | Parcial | Parser reutiliza análisis lineal por curso; no se ejecutó benchmark de catálogo. |
| Seguridad | Revisión focal local | Escaneo de credenciales 44/44 y revisión manual del delta sin hallazgos; no se modifican Auth/roles/red. CodeQL fresco depende del SHA posterior al push. |
| Mantenimiento | Validado local | Registro fuente–componente y enlaces generados reconciliados; R20 describe el candidato y R19 se conserva. |
| Calidad | Validada local | Lint, TypeScript, build, parser y UAT local; 9 warnings ESLint heredados sin errores. CI del nuevo SHA aún requiere lectura posterior a la publicación. |
| Rendimiento | No medido | No se midieron Web Vitals ni tiempos del deployment final. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Mantiene formatos de duración previos y acepta unidades explícitas/compuestas. | Parser y consumidores versionados en la rama de #503. |
| compatibilidad | Filtros, facetas y “Actualizarme” usan el mismo contrato; el rótulo expresa el límite del filtro largo. | H3-UAT-059 local; el helper anterior pasa 11/11 Docker. |
| deploy | El push puede generar Preview automático. No es integración ni Development. | Autorización humana vigente cubre push no forzado y actualización de #503; no autoriza merge ni deploy manual. |
| contract | Pendiente de integración autorizada y despliegue Development identificado; luego repetir 058/059 y smoke. | Requiere instrucción humana de merge independiente y comprobar deployment/SHA reales. |
| Rollback/recuperación | Revertir como unidad parser/filtros/rótulo y ajustes responsive; conservar evidencia local y fixture. | Sin rollback de datos/configuración remotos porque no se modificaron. |
| No degradacion funcional | PASS acotado en filtros y geometría con fixtures y viewports locales. | No implica aceptación de los otros CA ni de H3REQ1. |

## Evidencia Para Cliente

H3-CA4.9 se cubre localmente con H3-UAT-059; H3-CA4.11 con H3-UAT-058, según la matriz y la atestación sanitizada de `.context/requerimientos/` y `.context/trazabilidad/`. No se incluye documento privado ni waiver. Aceptación remota Development: pendiente. D03 acredita solo el onboarding observado; D01/D02/D04/D06 permanecen parciales, D05/D07–D14 pendientes y grupos adicionales 0/11.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS, 44/44 includedPaths | Docker, local | Ningún `.env` fue abierto; manifiesto R20. Owner: Codex. |
| Python tests | N/A | No cambió Python | Sin efecto en este paquete. |
| Python compile | N/A | No cambió Python | Sin efecto en este paquete. |
| PostgreSQL DB Change Gate | N/A como migración de producto | PG17 sintético local, solo lectura | Fixture completo reutilizado; cero SQL/reset/cleanup y cero escrituras remotas. |
| ESLint | PASS exit 0; 0 errores, 9 warnings heredados | Docker, fuente local | Ejecutado con dependencias existentes montadas read-only; evidencia R12. |
| TypeScript | PASS exit 0 (`npx tsc --noEmit --incremental false`) | Docker | Sin cambios de configuración. |
| Static build | PASS `build:mock`; rutas públicas 200/200 | Docker, build local | `index.html` y detalle tienen hashes registrados en acta R12. |
| actionlint / ShellCheck | No cambian en el delta R12; en head previo CI ambos PASS | GitHub Actions, head previo `6e1bd8f5…` | El workflow no cambia en este delta; los jobs se ejecutan nuevamente para el nuevo SHA. |
| UAT/runtime/integración | PASS local, 2/2, 6/6 viewports, 134 assertions, 6 capturas, 0 retries, 0 resets | Docker + mock local | Fixtures sintéticos. No es Preview, Development ni aceptación total. |
| security-audit / CI independiente | Leer el estado de la pestaña Checks para el HEAD exacto de #503 al revisar | GitHub PR #503 | Los resultados de SHAs anteriores no se transfieren. |
| CodeQL si aplica | Leer el resultado del HEAD exacto de #503 antes de revisión | GitHub PR #503 | El resultado histórico de `213fb3b` está en R13, no sustituye el del HEAD vigente. |
| Cloudflare Pages / smoke preview | Verificar el check/Preview del HEAD exacto de #503 | GitHub / Cloudflare Pages | Cada push puede crear Preview; no es Development. |
| Browser snapshot si aplica | PASS local a 390 px; 320 px PASS en runner | Chrome Windows MCP + Playwright Docker | Chrome vio `http://127.0.0.1:3342/` por forwarder GET/HEAD, no una URL remota. |
| security-auditor | Revisión manual focal PASS; escaneo de secretos PASS | Diff funcional R12 y dos documentos R13 | Sin cambio a Auth, roles, API keys, transporte ni datos personales; CodeQL se verifica contra el HEAD actual. |
| Documentación / trazabilidad / fuente cliente | PASS R20: 735/735 fuentes asignadas; gate y autoprueba verdes | Docker, manifiesto R20 | 725/735 con dimensiones completas, 115/115 activos alcanzables, 433/433 históricos, 9.267 enlaces, 4.632 anchors. No prueba estado remoto. |

## Seguridad Y Datos

- [x] Scanner de credenciales y revisión manual del delta sin credenciales/PII/firmas/JWT; `.env*` no se abrió.
- [x] API keys, identidad, RLS, roles, MFA y membresías no cambiaron en este paquete.
- [x] Los checks se atribuyen por SHA y deben cotejarse contra el HEAD actual antes de revisión; no se heredan resultados de otros commits.
- [x] Sin SQL remoto, cambios de secretos, datos operativos, Production, restores, schedules ni writers.

## Alcance Y Limites

- [x] H3-CA4.9/H3-CA4.11 enlazados con evidencia sintética local y límite remoto declarado.
- [x] Rama `feat/h3req1-public-duration-mobile-20261024`, base `desarrollo`; paths cotejados contra el scope exacto de 44.
- [x] Evidencia histórica y resultados RED preservados; raw R12 permanece en checkout local y el resumen sanitizado está seleccionado.
- [x] WIP Admin/MFA/BFF/FG3/C/Auth fuera del paquete; no se autoriza merge, deploy manual ni cambio de protección.
- El primer upload truncado `18c9586` se conserva como historia y sus checks no se aceptan. El commit correctivo aditivo `213fb3b` restauró únicamente los dos registros de trazabilidad; sus blob SHA remotos coinciden con los locales y el diff remoto quedó en 42 paths, 11.737 adiciones y 60 eliminaciones. Detalle: [R13](candidate-acceptance-cycle-2026-10-24.md#r13-recuperacion-de-publicacion-y-verificacion-del-pr-2026-10-25).
- En el HEAD `213fb3b`, la última lectura terminó con 18 check-runs: 16 `success` y 2 `skipped`; H2 Main Production Expand Gate se omite porque el PR apunta a `desarrollo`, y Supabase Preview se reporta `skipped` con enlace al panel Pro. La siguiente publicación documental requiere releer el HEAD y checks nuevos. El PR sigue abierto, sin aprobación ni merge.

## Checklist Tecnico

- [x] H3-UAT-058 y H3-UAT-059 canónicos ejecutados juntos sobre build local Docker y fixture PG17 exacto.
- [x] R20, credential scan, lint, TypeScript, build, scope y `git diff --check` validados localmente.
- [x] Ficha, índice, relaciones, acta y esta descripción reconciliados con R12.
- [x] Expand/compatibilidad/rollback documentados; Development permanece pendiente.
- [x] Autorización vigente cubre los commits/push aditivos del paquete y el Preview automático; no incluye merge, deploy manual ni cambios de protección.
- [ ] Revisión/aprobación humana e integración: decisión humana independiente; merge no autorizado por este ciclo.
- [ ] Aceptación Development: pendiente de merge autorizado, deployment identificado y revalidación remota.
