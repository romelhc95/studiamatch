# Cuerpo propuesto para PR H3REQ1 — R14 reconciliado y revisado localmente

Este cuerpo local usa la plantilla versionada. No se abrió ni actualizó un PR. El paquete combina funcionalidad R8 y documentación R13; R8/R9/R12/R13 y sus evidencias históricas quedan preservados. El documento privado del cliente no se leyó ni se incluye.

## Resumen

R14 combina el alcance funcional R8 con el cierre documental R13 y verifica la disponibilidad de los destinos directos de sus catálogos. Checkout `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`; el HEAD no identifica todo el WIP. El paquete tiene 1,117 rutas propuestas: 1,116 entradas de scope y el propio manifiesto, cuyo hash se excluye por circularidad. Evidencia: [estado operativo](../estado_del_proyecto.md), [atestación cliente sanitizada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md), [manifiesto R14](h3req1_pr_scope_manifest_2026-10-13_r14_reconciled.json), [reporte R14](h3req1_reconciliacion_local_2026-10-13_r14.md), [checks R14](h3req1_reconciliation_checks_2026-10-13_r14.txt) y [revisión independiente R14](h3req1_reconciliation_independent_review_2026-10-13_r14.txt).

## Evidencia De Este PR

La aceptación funcional local G01–G09 se reutiliza desde R178 y el delta G10 local desde R181/R182, limitados a inputs compatibles. Se repiten las pruebas cuyo input cambió y los gates afectados por el manifiesto, el test de scope, el allowlist y la corrección puntual de referencias a artefactos generados. Los resultados, comandos, hash/estado por ruta y límites Docker están en R14. La salida y las herramientas ausentes se distinguen de los checks PASS; no se presenta una ejecución histórica como ejecución R14.

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Funcional H3REQ1 | Se integra el scope funcional R8; no se incluye WIP funcional fuera del manifiesto. | Portal Admin/BFF, Edge invite, RPC/migraciones y pipeline de pruebas local. | R178 y R181/R182; manifiesto R14. |
| Documentación vigente | R13 es la versión actual; las rutas R12 quedan cubiertas por R13, y R9 permanece como antecedente con su evidencia. | Índice único, registro canónico, fichas, checker y catálogos. | Reporte R14; evidencias R8/R9/R12/R13 sin reescritura. |
| Disponibilidad de catálogos | 737 destinos directos que faltaban en paquete/base se agregan por path, hash y relación; no se agrega WIP por directorio. | 13 catálogos, checker de documentación y workflow de paths protegidos. | 1,173 targets reconciliados; test de scope PASS. |
| Corrección de fuentes generadas | Se retiran tres enlaces a `web/out/...`, `web/next-env.d.ts` y `web/tsconfig.tsbuildinfo`; quedan fuera del paquete conforme a la exclusión R8 de outputs/cache. | Registro JSON canónico y catálogo `infra_seguridad_ci`; no cambia la navegación de 433 históricos. | JSON y catálogo R14 generados; gate normal/self-test PASS. Los artefactos/evidencias R13 permanecen intactos. |
| Workflow protegido | Se amplía el allowlist con 602 rutas exactas y se conserva el regex existente. Se elimina una rama `pull_request_review` inalcanzable del gate H2; Stage 1 sigue separado de PWI Stage 2. | `security-audit.yml`, `tests/test_protected_path_scope_guard.sh`, `tests/test_security_flow.py`. | 1,117/1,117 candidate paths, 13 catálogos, 1,173 destinos, 78/78 contratos/workflow tests PASS; `actionlint` en todos los workflows y `ShellCheck -x` en los dos scripts del guard PASS. |
| Dependencia `braces` | Se conserva `braces@3.0.4-h3.1` y su tarball local; no se modifica versión ni lock. | Instalación reproducible local. | Opciones y decisión local en el reporte; origen upstream pendiente de G10. |

El conjunto de scope contiene 7 eliminaciones, 85 archivos modificados y 1,024 rutas untracked. El status observado contiene 20,566 rutas; 1,082 aparecen en status y se proponen, 19,484 quedan fuera. Se agregan 35 logs ignorados por `.gitignore` que se requieren por evidencia R8 o links directos; no se stagearon. En un ciclo futuro autorizado requerirán inclusión explícita, incluida la excepción a ignore.

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | APROBADO local acotado | R178 G01–G09, con contratos focales R14 repetidos. Harnesses y datos sintéticos; no es aceptación remota. |
| Escalabilidad | APROBADO dentro de evidencia local | Métricas descriptivas/harnesses existentes; no hay SLA ni carga de producción. |
| Seguridad | PASS local; revisión independiente 0 HIGH/CRITICAL | Scanner sobre 1,110 archivos, workflow scope y revisión independiente PASS; no se consultaron secretos/configuración remota. |
| Mantenimiento | APROBADO con seguimiento | R8/R9/R12/R13 y evidencia se preservan. `braces` queda asignado a Romel con revisión el 2026-11-03. |
| Calidad | PASS local con alcance declarado | Pruebas focales, docs, TypeScript, `actionlint` y los scripts shell del guard PASS. El barrido ShellCheck de los 181 `.sh` del paquete informó diagnósticos en runners/evidencias históricos, fuera de la delta shell funcional; no se aplicó limpieza masiva. |
| Rendimiento | APROBADO dentro de evidencia local | No se cambia runtime fuera de R8; pruebas descriptivas previas, sin SLA ni medición remota. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Migraciones de alcance R8 probadas en PostgreSQL 17 desechable; R14 no aplica SQL. | R178/G01–G02; sin DB operativa ni Supabase writes. |
| compatibilidad | R178 cubre BFF, MFA, roles, gateway/cuota, procedencia y fallback legacy en los recorridos declarados. No se retira compatibilidad remota. | R178/R51 y matriz local; G10 debe verificar consumidores desplegados. |
| deploy | Build normal servido por Pages/workerd local acreditado en R178 para inputs compatibles. | No se ejecutó deploy GitHub/Cloudflare; el build no se repitió porque limpia `.next`/`out`. |
| contract | Contracción legacy remota NO-EJECUTADA. | Requiere G10, estabilidad de consumidores, evidencia remota y aprobación separada. |
| Rollback/recuperación | Rollback SQL local y recuperación sintética C03/pipeline acreditados en R178. | Rollback de deploy remoto NO-EJECUTADO. |
| No degradacion funcional | Fixtures/harnesses R178, contratos de invitación y verificación de scope/documentación R14 pasan dentro de sus límites. | No extrapolar a usuarios, correo, Auth o datos reales. |

## Evidencia Para Cliente

Se incluye y enlaza la [atestación sanitizada versionada](../evidencias_cliente/sprint_1/atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md). El documento privado del cliente no se consultó, adjuntó ni versionó.

| Criterio | Resultado local | Límite |
|---|---|---|
| Edición y procedencia editorial | PASS R178 en fixtures sintéticos. | No contiene cursos operativos. |
| Auditoría atómica actor/fecha/antes/después | PASS en PG17 desechable y C03. | No es escritura remota. |
| Disponibilidad y compatibilidad legacy | PASS en harnesses locales R178. | No acredita producción. |
| Invitación, email y roles | PASS local sintético R178 y 18 contratos de Edge PASS R14. | Auth/email reales y callers desplegados pendientes de G10. |

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS; 1,110/1,110 archivos, 14 lotes, 0 hallazgos. | Docker `studiamatch-dev`; incluye 35 logs ignorados seleccionados; 7 eliminaciones sin contenido. | Checks R14/manifiesto. Ningún valor de credencial se imprimió. |
| Python tests | PASS: 78/78 focales; full suite NO-EJECUTADA. | Docker; fixtures/contratos locales. | `test_admin_invite_edge_contract.py`, `test_obsidian_context_state.py`, `test_security_flow.py`, `test_protected_workflow_review.py`, `test_fase10_main_boundary.py`, `test_fase09_10_pre_main_controls.py`, `test_fase09_9_certification_canary.py`. Un primer collection de workflow sin `PYTHONPATH=/app` falló y se corrigió; `security_flow` encontró aserciones antiguas de estado/Stage 2, alineadas a R13/Stage 1 antes del PASS combinado. |
| Python compile | AST PASS para 2/2 archivos focales. | Docker; sin escribir bytecode. | No equivale a compilar/importar todos los módulos Python. |
| PostgreSQL DB Change Gate | Reutilizado: R178 G01/G02 y R51 128/128 inputs PASS. R14 no ejecuta SQL. | PostgreSQL 17 desechable histórico. | Sin conexión/escritura Supabase. |
| ESLint | PASS exit 0; 0 errors, 9 warnings. El lint seleccionado de 29 archivos también pasa con esos 9 warnings en `HomeContent.tsx`. | Docker. | Los warnings ya constaban en R8; no se silencian. |
| TypeScript | PASS exit 0 con `npx tsc --noEmit --incremental false`. | Docker. | No escribió el cache `web/tsconfig.tsbuildinfo`. |
| Static build | NO-EJECUTADO R14. | Build local R178 reutilizado por inputs de runtime compatibles. | `npm run build` borra `.next` y `out`; no se ejecutó una operación con efecto de limpieza. No se agregan outputs. Owner Romel si el ciclo autorizado requiere rebuild aislado. |
| actionlint / ShellCheck | `actionlint` v1.7.12 PASS en todos los workflows; `ShellCheck -x` 0.11.0 PASS en los 2 scripts del guard; `bash -n` PASS en 4 scripts. El barrido ShellCheck de 181 scripts halló diagnósticos en runners/evidencias históricos. | Docker local; herramientas temporales, SHA-256 de distribución verificados. | Actionlint incluye parseo/validación YAML. Los hallazgos del barrido histórico no se arreglaron en bloque y quedan explícitos para triage separado si se exige cobertura estricta de todos esos scripts. |
| UAT/runtime/integración | Reutilizado de R178: R51 128/128, C03 y recorridos locales declarados. | Pages/workerd/Edge/PG17 sintéticos. | No se repitió con inputs iguales; sin servicios remotos/cuentas reales. |
| security-audit / CI independiente efectivo | PASS del gate local de paths 1,117/1,117; no hubo CI/Actions remoto. | Docker local. | Protecciones, required checks, instalación y run para SHA exacto se revisan en G10. |
| CodeQL si aplica | NO-EJECUTADO. | GitHub remoto no consultado. | Owner responsable de integración/G10. |
| Cloudflare Pages / smoke preview | NO-EJECUTADO remoto. R178 acredita Pages/workerd local para inputs compatibles. | Local, sin preview/deploy. | No se purgó cache ni se tocó Cloudflare. |
| Browser snapshot si aplica | Reutilizados R173/R178 para inputs compatibles. | Chromium local sintético. | No se usaron usuarios reales. |
| security-auditor | PASS: revisión independiente local R14, cero HIGH/CRITICAL y cero findings de código abiertos. | Revisión read-only, sin tests ni lecturas remotas. | Dictamen en `h3req1_reconciliation_independent_review_2026-10-13_r14.txt`; resultados actuales y residual del barrido ShellCheck histórico en `h3req1_reconciliation_checks_2026-10-13_r14.txt`. No autoriza PR/promoción. |
| Documentación / trazabilidad / fuente cliente | PASS normal/self-test: 801/801 fuentes, 97/97 activos, 433/433 históricos en 13 catálogos, 9,349 links, 4,567 anchors. | Docker/local. | R14 corrige tres links a outputs no versionados; R13 queda como antecedente inalterado. Solo se consultó la atestación sanitizada. |

## Seguridad Y Datos

- [x] Scanner R14 sin hallazgos en el inventario declarado; el escaneo no imprime credenciales.
- [x] API keys, roles, MFA y protección del último admin se cubren con la evidencia local R178 y contratos focales; no hubo identidad/DB real.
- [x] Revisión independiente local R14: cero HIGH/CRITICAL y ningún finding de código abierto; sin waiver.
- [x] Sin DB writes, deploys, schedules, workflows remotos ni cambios de secretos.

## Alcance Y Limites

- [ ] PR no creado por el alcance autorizado; al abrirlo, enlazarlo a esta sesión. Requerimiento H3REQ1, aceptación local y atestación sanitizada identificados; contenido privado no consultado.
- [x] R8 funcional + R13 documental combinados; R12 contenido, R9 intermedio, R8/R13 solapamientos y exclusiones descritos en el reporte/manifiesto.
- [x] Cierre de catálogos verificado: 1,173 destinos; 903 incluidos en el candidato y 270 disponibles por HEAD base. G10 debe validar base `desarrollo`.
- [x] 19,484 paths del status local excluidos; 35 logs ignorados incluidos explícitamente. Sin staging, commit, push, PR, merge, lecturas remotas o deploy.
- [x] Dependencia `braces` intacta; el paquete no afirma verificación upstream.

## Checklist Tecnico

- [x] Checks locales disponibles ejecutados contra el candidato R14 en Docker y registrados con resultados/owners.
- [x] Registro canónico, consumidores, fuente y relación de outputs generados corregidos de forma puntual; gate normal/self-test PASS.
- [x] Pilares, atestación sanitizada, transición `expand -> compatibilidad -> deploy -> contract` y rollback descritos con límites reales.
- [x] Revisión independiente final PASS local, cero HIGH/CRITICAL y hallazgos de código resueltos; CI remoto sigue pendiente.
- [x] Este es un paquete para revisión local, no `GO_LOCAL_PR`, `GO_DEVELOPMENT_REAL` ni autorización G10.
