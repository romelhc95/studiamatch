# Borrador del cuerpo PR H3REQ1 — revisión local, no publicar — 2026-10-11

Este borrador sigue `.github/pull_request_template.md`. No se creó commit ni PR y no se realizó operación remota. G08 está completo para los checks locales aplicables; G09 continúa parcial; R75/R76 amplían LOCAL-09 (cookie sesión A/B y cleanup multi-chunk), sin cerrar el gate. G10 remoto pendiente.

## Resumen

Candidato local H3REQ1 para los criterios sanitizados de Sprint 1: edición y procedencia editorial, auditoría, disponibilidad/publicación, membresías e invitación, BFF con cookies HttpOnly, MFA/RBAC, gateway RPC firmado y cuotas. Los resultados corresponden a runtimes y datos sintéticos locales; no representan aceptación remota.

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama: `feat/h3req1-sync-20261002`.
- HEAD baseline: `4eb4d877a50b012bb630a129bd0c74482c33be9c`; no identifica el WIP.
- Inventario observado: 60 rutas tracked modificadas, 807 entradas untracked visibles, 16.480 paths untracked expandidos y 0 staged. La propuesta fija solo 86 rutas de cambio (60 tracked + 26 untracked) y 73 evidencias seleccionadas. Los demás paths, caches, builds, dependencias y archivos `.env*` operativos quedan excluidos; `.env.example` es el único template de entorno incluido. Datos operativos y recursos ajenos también quedan fuera.
- Manifiesto de contenido: `.context/evidencia/h3req1_pr_scope_manifest_2026-10-11_r2.json`, SHA-256 `22455628689a0ad1c90d2df515dcede1ac574ece7656d980f81132c74cc17b1f`; digest de las entradas fuente `fb53503cf8306644ebb8b09b942375af6c09386b3209c739350bc43a592c142d`.
- Veredicto local: G01–G08 completos; G09 parcial; G10 remoto pendiente. No declara GO local, `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.

## Evidencia De Este PR

| Resultado | Comando/casos e inputs | Ambiente y grado | Evidencia y límites |
|---|---|---|---|
| G08 — Python | `pytest tests/test_*.py`: 335 passed, 4 skipped, 1 warning PyPDF2, exit 0. R73 ejecutó dos casos focales de recuperación parcial: 2 passed, 0 retries. | `studiamatch-dev`, imagen local `studiamatch-h3req1:20261009-v3`; prueba sintética. El comando usó `env -i`, bytecode/cache desactivados. | `.context/evidencia/h3req1_g08_delta_r70/pytest-r70.log`; R73: `.context/evidencia/h3req1_g09_local_acceptance_delta_r73_2026-10-11.md` y `pipeline-partial-recovery-r73.log`. Los cuatro skips no son PASS; no hubo writer cloud. |
| G08 — calidad y seguridad local | Credential scanner, H2 writer scan, contrato de credenciales 43/43, Python AST 176, ESLint exit 0 (9 warnings, 0 errores), Next typegen/TypeScript PASS, actionlint/ShellCheck PASS o reutilizados por hashes coincidentes; npm audit full/prod 0 vulnerabilidades. | Docker local; inputs fijados por la evidencia G08. | `.context/evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md` y deltas R70/R72. La revisión independiente final del conjunto propuesto (86 rutas) todavía no está completa. |
| Builds estáticos | R69 normal build exit 0: 33/33 páginas, 17 rutas sintéticas y 206 artefactos; hashes verificados. | Next/Pages local, fuentes y REST sintéticos. | `.context/evidencia/h3req1_g09_uat_2026-10-10_r4/compare-build-r69/`. No demuestra producción ni publicación remota. |
| C03 integrado | R51 PASS; Pages/workerd + Edge + PostgreSQL 17 + PostgREST locales; 128/128 inputs coinciden con el corte. | Runtime y datos sintéticos en Docker. | `.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r51.txt`; no es servicio remoto. |
| Catálogo visual | 65 casos × 3 viewports; 195 combinaciones PASS seleccionadas entre corridas. R70: H3-UAT-049/064 6/6, 96/96 aserciones; R72 H3-UAT-065 3/3, 69/69 aserciones. | Chromium 1228 headless; R72 Pages/workerd Miniflare sirvió export R69 y usó REST sintético interceptado. Sin ventana visible; R72 no consultó PG17. | Matriz R28/R29/R30, deltas R64–R70 y R71–R72; tres capturas R72 con hashes. R71 se conserva pero se excluye por una aserción tautológica. Los 195 PASS son conciliación entre corridas, no un solo run. |
| Discovery/pipeline focal | R18 combinado 24/24; R73 fallo posterior de página y scroll más recuperación 2/2. | `studiamatch-dev`, `/app` montado desde candidato, SHA coincidente. R73 usó adaptador en memoria, sin red ni DB. | Handoff R2–R18 y delta R73. Persistencia/checkpoint de fallo parcial en PG17 queda pendiente. |
| Identidad PG17/build/runtime | R74 PASS: una fila PG17 leída `READ ONLY` coincide por ID/institución/nombre/slug/URL con el artefacto R69 y el detalle HTTP público (200). | PG17 sintético R12, export R69 y GET loopback R12/R47. | `.context/evidencia/h3req1_g09_local_acceptance_delta_r74_2026-10-11.md`. No acredita propagación de edición ni invalidación de caché; la proyección raw redundante se excluye. |
| Onboarding/INV-008 | R8 10/10 casos PASS, 10 capturas con hashes, un vídeo y cero retries. INV-008: ciclo de rutas de la aplicación para `password_pending`, corregido y revalidado. | Pages/workerd, Auth/BFF mock y PostgreSQL 17 sintético; Chromium 1228 headless. | `.context/evidencia/h3req1_g09_onboarding_r8_inv008_topology_2026-10-11.md`; los fallos R6/R7 se preservan, no se ocultan. No se usó cuenta ni correo real. |
| Acceso Windows | `http://localhost:3336/` y el detalle `/courses/ulima/analitica-aplicada-60000000/` respondieron HTTP 200; proxy R47 hacia el runtime R12 y PG17 sintéticos. | Loopback local; no se recrearon app ni DB. | `.context/evidencia/h3req1_g09_windows_loopback_r41_postflight_2026-10-11.md` y la matriz vigente. No es Cloudflare Preview. |
| Live/remoto | NO-EJECUTADO: pruebas que requieren credenciales/cloud/live, CI remoto, GitHub, Cloudflare y Supabase; no hubo PR, deploy ni writes. | Fuera del alcance local. | G10 e integración Development requieren instrucciones humanas posteriores. |

## Avances Del Cambio

| Componente/contrato | Cambio implementado | Consumidores/impacto | Evidencia |
|---|---|---|---|
| Admin/editoría y procedencia | Mantiene fuente pipeline/manual, overrides y control de versión en las rutas cubiertas. | Admin, pipeline y lectores públicos. | R30/R70 y contratos SQL; el barrido por todos los grupos de campos/conflictos sigue pendiente en G09. |
| Auditoría y disponibilidad | Registra los cambios cubiertos; evidencia HTTPS, actor/razón, máximo inclusivo de 90 días y rechazo de publicaciones no elegibles. | RPC Admin, publicación y lectura pública. | PG17/C03 R51 y UAT R30. La matriz G09 sigue siendo el registro de cobertura parcial/restante. |
| BFF y sesión | Cookie HttpOnly ligada a sesión Auth; MFA/RBAC, gateway firmado y cuotas se preservan. | Admin UI, Pages Functions y RPC allowlisted. | G03/R76: BFF UAT 96 checks; R76 prueba cleanup de siete nombres de cookie Auth/chunks con confirmación `--network=none`; R75 concilia sesión A/B, expiración de actividad, flags y rebind MFA. Auth expiry/browser y refresh concurrente end-to-end siguen pendientes; [R76](.context/evidencia/h3req1_g09_local_acceptance_delta_r76_2026-10-11.md) detalla el alcance y la confirmación sin red; no acredita bindings ni enforcement remoto. |
| Pipeline | Discovery, cleansing, enrichment y sync conservan los estados/fallos ensayados; R73 verifica recuperación parcial en memoria. | Pipeline de datos y catálogo. | R2–R18/R73; falta integrar ese escenario parcial con persistencia PG17. |
| Reflejo público | R74 coteja una fila PG17 con el artefacto R69 y respuesta loopback pública por identidad/ruta. | Admin, export estático, lector público. | Persiste la brecha de cache/rebuild tras edición; R74 no la cierra. |
| CI independiente | Workflow y controles locales están propuestos en el inventario. | Protección futura del flujo de cambios. | No publicado ni requerido: G10 pendiente. Un YAML local no acredita enforcement. |

## Pilares Obligatorios

| Pilar | Estado | Resultado validado y límites |
|---|---|---|
| Funcionalidad | Parcial | G01–G08 completos y casos funcionales locales ejecutados; áreas LOCAL-01..03, 06..10, 12..14, 16..17, 19..20 y 22..23 siguen parciales según la matriz. R73/R74 añaden cobertura parcial, no gates completos. |
| Escalabilidad | Parcial | Contenedores y pruebas locales acotados; no se ejecutó carga comparativa ni se demuestra SLA. |
| Seguridad | Parcial | Scanner, writer scan, auditorías y contratos locales PASS; revisión independiente final de todo el conjunto propuesto pendiente. Sin secretos/cuentas reales en las pruebas nuevas. |
| Mantenimiento | Parcial | ESLint, TypeScript, Python, ShellCheck/actionlint y builds con resultados favorables; 9 warnings ESLint y una advertencia PyPDF2 registradas. |
| Calidad | Parcial | G08 completo; G09 conserva áreas funcionales abiertas y fallos históricos de harness/fixture. Cuatro skips no se cuentan PASS. |
| Rendimiento | Parcial | Se verificaron rutas y runtimes locales; falta medición repetible de p50/p95 sobre dataset ampliado frente a baseline. |

## Transicion Transparente

| Fase | Alcance/resultado real | Evidencia / autorización cuando aplique |
|---|---|---|
| expand | Cambios aditivos y migraciones locales ensayados en PG17 desechable; no se escribió en Supabase. | G01/G02 y R51 locales. |
| compatibilidad | BFF HttpOnly, roles, MFA, gateway y comportamientos legacy se conservaron donde están cubiertos. | G03, R51 y UAT local; límites restantes en matriz LOCAL-01..23. |
| deploy | NO EJECUTADO. | Fuera de esta autorización; requiere instrucción separada. |
| contract | NO EJECUTADO; no se retiró funcionalidad legacy de servicios remotos. | Depende de promoción/estabilización futura y autorización. |
| Rollback/recuperación | Suspensión/resume y recuperación local cubiertas en R51; rollback remoto no probado. | R51 y SQL rollback local versionado; no equivale a operación remota. |
| No degradacion funcional | Catálogo visual seleccionado, R51 y onboarding PASS en los alcances declarados; LOCAL-01..23 no está completo. | Evidencia local sintética, no aceptación final. |

## Evidencia Para Cliente

Se usa la atestación sanitizada versionada; no se adjunta documento privado. La siguiente tabla informa subalcances observados, no aceptación contractual total.

| Criterio | Resultado local observado | Pendiente/límite |
|---|---|---|
| Admin completa/corrige cursos conservando origen | Recorrido R30/R70 del curso sintético pasa en preview, override y lectura pública. | Matriz completa por campo, cancelación y conflictos/concurrencia sigue pendiente en LOCAL-13/14. |
| Auditoría actor/fecha/antes/después | Evidencia del recorrido editorial y SQL/C03 local. | Cotejo de atomicidad y ownership por matriz completa de campos pendiente en LOCAL-13. |
| Disponibilidad válida, máximo 90 días y legacy | Casos cubiertos aceptan el límite inclusivo y rechazan exceso/evidencia inválida; LOCAL-15 completo en su alcance. | No implica aceptación final de G09 ni despliegue de contrato remoto. |
| Encabezado muestra correo y conserva roles | Flujos Admin/user y membresías sintéticos probados; R41 verifica último admin. | Sesión/MFA y concurrencia adicional LOCAL-09/10 siguen parciales. |

## Validaciones

| Validacion | Resultado/exit/casos | Ambiente/grado | Evidencia/límites/owner |
|---|---|---|---|
| Credential scan | PASS en G08 y runner R72. | Docker local; sin mostrar secretos. | Logs G08/R72; revisión independiente final pendiente, owner: responsable H3. |
| Python tests | Exit 0: 335 passed, 4 skipped, 1 warning; delta focal R73 2 passed. | `studiamatch-dev`, synthetic/in-memory en R73. | Log pytest R70 y R73; skips/live no PASS. |
| Python compile | PASS; 176 fuentes parseadas como AST. | Docker local. | Evidencia G08; AST no equivale a ejecutar los 176 módulos. |
| PostgreSQL DB Change Gate | PASS en harnesses G01/G02 y C03 integrado R51. | PG17.11 desechable/sintético. | No son writes remotos; la recuperación parcial R73 no usó DB. |
| ESLint | PASS, exit 0, 9 warnings conocidos y 0 errores. | Docker local. | `.context/evidencia/h3req1_g08_final_checks_reconciliation_2026-10-11.md`. |
| TypeScript | Next typegen y `tsc --noEmit` PASS con heap acotado. | Docker local. | Evidencia G08; live no ejecutado. |
| Static build | R69 normal: 33/33 páginas, 17 rutas sintéticas, 206 artefactos con hash verificado; normal/mock anteriores PASS. | Docker local, datos sintéticos. | Logs/manifest R69 y G08. |
| actionlint / ShellCheck | PASS o reutilizados con inputs coincidentes. | Checks locales; sin CI remoto. | G03/G08 con pins compatibles. |
| UAT/runtime/integración | R51 128/128 inputs; catálogo 195 combinaciones seleccionadas; R70 6/6, R72 3/3, R73 2/2, R74 identidad PG17/build/GET PASS, R75 reutiliza subcasos de sesión/MFA por hash coincidente; R76 ejecuta BFF multi-chunk 96 checks ([evidencia](.context/evidencia/h3req1_g09_local_acceptance_delta_r76_2026-10-11.md)); R8 onboarding 10/10. | Docker, Pages/workerd, Edge, PG17/PostgREST locales; Chromium headless. | Ver filas de evidencia anteriores. No es un único UAT global; G09 parcial. |
| security-audit / CI independiente efectivo | NO-EJECUTADO remoto. YAML local preparado, no requerido ni probado por PR. | GitHub remoto fuera de alcance. | G10 pendiente de integración, enforcement y revisión humana. |
| CodeQL si aplica | NO-EJECUTADO. | No hubo CI/acción remota. | Aplicabilidad para el PR requiere revisión del responsable. |
| Cloudflare Pages / smoke preview | NO-EJECUTADO remoto. | No hubo deploy/preview. | Certification y Production preservados. |
| Browser snapshot si aplica | Capturas R70 y R72 verificadas; R70 conserva vídeo desktop y R8 conserva vídeo onboarding. | Chromium 1228 headless; R72 sin ventana. | R72: tres PNG; paths en manifiesto R2. |
| security-auditor | Revisión focal previa sin bloqueantes; revisión independiente final de las 86 rutas no ejecutada. | Estático/local. | No se declara ausencia final de HIGH/CRITICAL. |
| Documentación / trazabilidad / fuente cliente | Estado, matriz LOCAL-01..23, deltas R73–R76 y borrador/manifest R2 actualizados con límites. | Local; atestación sanitizada. | La revisión final y aceptación responsable siguen pendientes. |

## Seguridad Y Datos

- [ ] Scanner y revisión final del diff completo sin credenciales/PII/firmas/JWT. Scanner local PASS; revisión independiente de las 86 rutas pendiente.
- [x] API keys, BFF/HttpOnly, roles, MFA y último admin preservados en los casos locales indicados; no se utilizaron cuentas reales.
- [ ] HIGH/CRITICAL ausentes en revisión final independiente: no acreditado todavía.
- [x] Sin DB remota, secretos, producción, restore, schedules, writers cloud o acciones remotas.

## Alcance Y Limites

- [x] Requerimiento/criterios vinculados con la atestación sanitizada y matriz de aceptación.
- [ ] Rama/base/inventario aprobados para un PR real: manifest R2 propuesto para revisión, scope guard final y aprobación responsable pendientes.
- [x] Evidencia vigente, histórica y descartada identificada; R71 y fallos anteriores preservados sin contarlos como PASS.
- [x] Sin PR, merge, deploy o promoción; estas acciones necesitan instrucción humana separada.

## Checklist Tecnico

- [ ] Todos los checks necesarios para cierre local G09 ejecutados en Docker: G08 completo, G09 sigue parcial.
- [x] Ficha de impacto, consumidores/contratos y matriz LOCAL-01..23 actualizados.
- [x] Atestación sanitizada, seis pilares y transición/rollback revisados con fases no ejecutadas explícitas.
- [ ] Review final/CI requerido efectivo: revisión independiente completa y G10 remoto pendientes.
- [x] G08, G09 parcial, G10 remoto y GO_LOCAL_PR/GO_DEVELOPMENT_REAL distinguidos; este borrador no declara GO.

**Estado de revisión:** G01–G08 completos; G09 parcial. Tablero G01–G10: 80% (8/10), sin delta en este corte. Cierre local G01–G09: 8/9 = 88,89%, sin delta. G10 sigue pendiente. Este texto y el scope manifest son materiales de revisión; no se creó PR.
