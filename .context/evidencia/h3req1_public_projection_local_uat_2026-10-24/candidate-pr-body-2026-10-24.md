## Resumen

Corrige la interpretación de duración compuesta en el catálogo y el overflow móvil del panel de filtros/footer. Cubre H3-CA4.9 (filtros y objetivo “Actualizarme”) y H3-CA4.11 (listado/detalle responsive) con H3-UAT-058/059 canónicos en fixtures sintéticos locales. No cierra H3REQ1 ni acepta Development.

Rama `feat/h3req1-public-duration-mobile-20261024`, base `desarrollo` en `1c69b94606795e33c9fee82e8a8e803f3104c566`; el PR identificará el SHA del commit candidato publicado. El scope exacto está en [`candidate-pr-scope-2026-10-24.json`](candidate-pr-scope-2026-10-24.json) y la evidencia por caso en [`candidate-acceptance-cycle-2026-10-24.md`](candidate-acceptance-cycle-2026-10-24.md). La atestación cliente y matriz canónica siguen en `.context/requerimientos/` y `.context/trazabilidad/`; no se adjunta material privado.

## Evidencia De Este PR

Validación ejecutada el 2026-10-24 en Docker con Node/Next.js 16.3.8, static export local, mock y PostgreSQL 17 desechable: `H3-UAT-058` y `H3-UAT-059` PASS (2/2; 6/6 ejecuciones desktop/tablet/mobile; 0 retries). Chrome Windows MCP comprobó aparte el candidato local `http://localhost:3020/` a 320 CSS px: documento/body/footer 320 px, footer x=0..320 con `scrollWidth=clientWidth=320`, y popover x=16..304. Una fila de filtros mantiene `scrollWidth=280` y `clientWidth=272`, aunque todos sus controles siguen dentro del viewport y la página no desborda. No es deployment Development; repetir el criterio en el deployment que incluya este candidato.

Artefactos: carpeta `run-canonical-058-059-footer-20261024/h3-expanded/` y `run-final-docker-checks-2026-10-24/`. Los RED históricos permanecen y sus causas corregidas están resumidas en la evidencia del ciclo. El último Development acreditado antes del candidato es SHA `1c69b94606795e33c9fee82e8a8e803f3104c566`, deployment `c8a57950-2e93-461f-80c3-50217f64576c`; el commit candidato ya está creado; Preview y deployment siguen pendientes. Push y apertura del PR están autorizados para los 39 paths del manifiesto.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Duración pública | Normaliza unidades españolas/inglesas, ignora números sin unidad de duración, suma unidades explícitas y toma el límite inferior del rango. | Filtros, facetas y ambos usos de “Actualizarme”. | H3-UAT-059; test focal de parser preservado; matriz canónica. |
| Panel y footer | Ancla “Más filtros” a la fila primaria; centra/restringe el panel en móvil; permite wrapping de columnas del footer. | Catálogo público, detalle estático y layout compartido. | H3-UAT-058, medición Chrome Windows local a 320 px. |
| UAT/fixtures | Corrige la aserción de paginación/reset y pone el fixture mixto en modalidad Híbrido; conserva el guard de reset con epoch monotónico. | Runner público local y sus helpers sanitizados. | H3-UAT-058/059 canónicos y tests de helpers 18/18. |

Incluye únicamente los paths de `candidate-pr-scope-2026-10-24.json`: tres fuentes de producto, runner/fixtures/helpers, ficha pública/índice y evidencia sintética seleccionada. La conciliación contra Git registró 87 paths modificados/no versionados: 37 modificados incluidos, 50 modificados preservados fuera del PR, dos tests de dependencia ya existentes incluidos solo para trazabilidad y 39 artefactos preservados no modificados; cero paths modificados quedaron sin clasificar. Excluye el WIP Admin/MFA/BFF/FG3/C/Auth de otro worktree, capturas personales, artefactos intermedios y `.env*`.

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | Parcial local | Ambos CA locales afectados pasan; falta Development. |
| Escalabilidad | Parcial | Parsing lineal sobre duración por curso y render existente; no se ejecutó benchmark de catálogo. |
| Seguridad | Validado local con alcance acotado | Codex Security diff scan completo: 0 hallazgos reportables, 0 HIGH/CRITICAL; el código no cambió después del snapshot. Tras el delta documental final, el credential scan pasó de nuevo sobre los 39 paths incluidos. No es revisión del runtime remoto. |
| Mantenimiento | Validado local | Relaciones componente y prueba actualizadas; paths exactos en manifiesto. |
| Calidad | Validado local | ESLint 0 errores/9 warnings heredados; TypeScript, static export, helper unit tests y UAT canónicos PASS. |
| Rendimiento | No medido | No se cambió transporte ni consulta; no se ejecutó medición de rendimiento. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Mantiene formatos de duración existentes y acepta unidades compuestas. | Parser previo reemplazado por interpretación por unidad. |
| compatibilidad | Mismo helper para filtros/facetas y “Actualizarme”; UI y footer continúan compartiendo layout público. | H3-UAT-058/059 local. |
| deploy | Pendiente. El push autorizado puede generar Preview automático; merge y deploy manual no están autorizados. | Autorizados commit, push y PR protegido a desarrollo para los 39 paths; esta autorización no cubre merge ni deploy manual. |
| contract | Repetir H3-UAT-058, H3-UAT-059 y smoke general tras identificar SHA/deployment Development. | Pendiente del artefacto integrado/desplegado. |
| Rollback/recuperación | Revertir parser + consumers, ancla del panel y wrapping del footer como unidad; volver a ejecutar ambos UAT. | Sin cambios de datos/configuración remotos. |
| No degradacion funcional | PASS dentro de fixtures/casos locales descritos; cobertura global y aceptación Development pendientes. | No transferir los PASS locales al producto remoto. |

## Evidencia Para Cliente

La referencia sanitizada es H3-CA4.9/H3-CA4.11 en `.context/requerimientos/` y la asignación de fuentes está en `.context/trazabilidad/`. Resultado local: ambos casos PASS en Docker. Resultado remoto: no ejecutado; sin waiver. El resto de los criterios H3REQ1 permanece abierto.

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS, exit 0, 39/39 paths incluidos | Docker, local | `scripts/security/scan_credentials.sh` sobre `includedPaths` exactos del manifiesto; no se inspeccionó `.env`. Los 89 paths excluidos se conservaron fuera del paquete. Owner: Codex. |
| Python tests | N/A | No cambió Python | Sin efecto sobre runtime Python. |
| Python compile | N/A | No cambió Python | Sin efecto sobre runtime Python. |
| PostgreSQL DB Change Gate | N/A como migración; fixture SQL ejecutado en PG17 desechable | Docker, fixture local | No DDL/DML remoto ni migración de producto. |
| ESLint | PASS, exit 0, 0 errores, 9 warnings | Docker, fuente local | Los warnings están en líneas no modificadas; log adjunto. |
| TypeScript | PASS, exit 0 | Docker | `npx tsc --noEmit --incremental false`. |
| Static build | PASS, exit 0 | Docker, static mock export | `npm run build:mock`; log y hash adjuntos. |
| actionlint / ShellCheck | N/A | No se cambiaron workflows ni scripts shell | CI/operación remota fuera de este diff. |
| UAT/runtime/integración | PASS local: H3-UAT-058/059 2/2, 6/6; helper tests 18/18 | Docker + Chrome Windows local | Fixtures sintéticos; no es Development ni aceptación completa. |
| security-audit / CI independiente efectivo | Pendiente | GitHub PR aún no abierto al preparar este cuerpo | El check deberá ejecutarse en el PR; no hay resultado remoto que declarar todavía. Owner: workflow/review. |
| CodeQL si aplica | N/A a nivel local; automatización del repositorio pendiente de comprobar en PR | Sin PR abierto | No se atribuye un resultado CodeQL. |
| Cloudflare Pages / smoke preview | Pendiente | No hay push ni Preview confirmado | El push autorizado puede disparar Preview automático. Owner: revisión humana/CI. |
| Browser snapshot si aplica | PASS local | Chrome Windows MCP, `http://localhost:3020/`, sin login | Captura canónica Docker cubre detail; DevTools local midió home/popover/footer. |
| security-auditor | PASS local, alcance del candidato | Local | Codex Security `660b6013-6caf-41f8-bb95-5a3e968b8186`: 0 findings, 4/4 superficies sin issue; se reconciliaron los 39 paths incluidos y 89 exclusiones. No cubre runtime remoto. Owner: Codex. |
| Documentación / trazabilidad / fuente cliente | PASS estructural local; verificación remota global parcial | Docker | `DOC_GATE_PASS`: fuentes 734/734, componentes 14/14, activos 115/115 e históricos 433/433; el inventario también reporta 9/15 checks de relación remota verificados y 6/15 pendientes, fuera de la aceptación de este paquete. H3REQ1 global sigue abierto. Owner: aceptación Development. |

## Seguridad Y Datos

- [x] No se añadieron datos personales, credenciales, firmas, JWT ni tokens a la evidencia seleccionada; el reset token sintético no se imprimió.
- [x] Auth, RLS, roles, MFA, último administrador, datos y configuración remota no cambian en este paquete.
- [x] HIGH/CRITICAL ausentes dentro del diff candidato: Codex Security scan completo con 0 findings; no equivale a runtime Development.
- [x] No hay escrituras Supabase remotas, producción, restore, schedules ni writers.

## Alcance Y Limites

- [x] H3REQ1 y H3-CA4.9/H3-CA4.11 enlazados; no se adjunta documento privado cliente.
- [x] Rama candidata aislada desde el SHA de desarrollo indicado; diff e inclusión exacta registrados.
- [x] Evidencia histórica RED conservada y resultados nuevos distinguidos.
- [x] No autoriza merge, deploy, promociones ni cambios fuera de Development.

## Checklist Tecnico

- [x] Checks afectados en Docker y casos canónicos locales contra candidato exacto.
- [x] Ficha pública, prueba/evidencia e índice actualizados.
- [x] Pilares, expansión/compatibilidad/rollback y límites registrados.
- [x] Revisión local final del paquete candidato: todos los paths incluidos revisados, exclusiones exactas preservadas y scanner de credenciales PASS.
- [x] GO local limitado a preparación del PR; NO-GO Development hasta despliegue y aceptación remota completa.
