# Seguimiento Sprint 1 H2-H5

> Esta nota no crea alcance ni autoriza ejecucion.

## Verificacion

`F11_H3_PR_DEVELOPMENT_READY_LOCAL`

Estado histórico preservado: `F11_H2_CLOSED_H3_READY_FOR_PROMPT_CONTINUA` y `H3_READY_FOR_PROMPT_CONTINUA` fueron gates previos al ciclo H3 vigente.

`H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED`
`PRODUCTION_REMEDIATION_PRO_EXPAND_COMPAT_BEFORE_MAIN`

| Control | Estado |
|---|---|
| O0-A preflight | `COMPLETED_READ_ONLY` |
| O0-B decision humana | `APPROVED` |
| Seguridad historica | `SECURITY_HISTORY_GO_WITH_SUPPLEMENTAL_REQUIRED` |
| Seguridad suplementaria D0 | `COMPLETED_REDACTED_NO_ACTIVE_SECRET_IN_SOURCES` |
| Preservacion archives | `COMPLETED` |
| T_CANONICO construccion | `COMPLETED` |
| O1 desarrollo | `COMPLETED` mediante PR #414 |
| Reconciliacion post-O1 | `COMPLETED` mediante PR #415 |
| Desarrollo commit | `a2c97ec17aabc790b656d6db1b16bdc95f0af1b2` |
| Desarrollo tree | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` |
| O2 certificacion | `COMPLETED` mediante PR #416 |
| Certificacion commit | `4e7e41a9fac08e657308849701b4b1f70b994e3b` |
| Certificacion tree | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` |
| Redefinicion de flujo | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` |
| Acciones remotas H3 | `BLOCKED_REQUIRES_SEPARATE_HUMAN_APPROVAL` |
| DB Free | `FREE_H2_COMPAT_REMOTE_VERIFIED` |
| DB Pro | `PRO_EXPAND_VERIFIED_MAIN` |
| GO documental | `RECEIVED` |
| PR H2 a desarrollo | `APPROVED_AND_MERGED_458@0c9e40f81f2a38141c9c2af170e26ab594b7533d` |
| PR gate documental | `APPROVED_AND_MERGED_459@4f7061585202301760d8068e13edc5c93b0f94e2` |
| PR H2 a certificacion | `APPROVED_AND_MERGED_460@0ed6afeec741c698f1111c2ea27357160fa77279` |
| Validacion fuente cliente | `SRC-REQ-002_VALIDATED_VIA_ADENDA_SANITIZADA` |
| Gate fuente privada local | `PASSED_6_TESTS_HASH_MATCH` |
| Work package activo | `NONE_SUPERSEDED` |
| QA read-only H2/H3 previa | `PASS_CERTIFICATION_READ_ONLY_QA` |
| PR H2 compat desarrollo | `APPROVED_AND_MERGED_466@e8376035d8d5c3e1b7893cbb1ede14f735ccd05d` |
| PR H2 compat certificacion | `APPROVED_AND_MERGED_467@2d499324bb21e750d9bc7c94cb80e7a193062b50` |
| Certificacion deployment | `STABLE_4cc2e34c` |
| PR #477 Security Advisor endpoint | `MERGED_TO_DESARROLLO_AND_CERTIFICATION` |
| PR #478 RLS cohorte privada | `MERGED_TO_CERTIFICATION` |
| PR #480/#481 DB Sync verify gate | `MERGED_TO_DESARROLLO_AND_CERTIFICATION` |
| Pro remediacion | `PRO_EXPAND_VERIFIED_MAIN` |
| Pro verify artifact | `PENDING_DB_SYNC_VERIFY_ON_CERTIFICACION` |
| Proximo gate unico | `COMMIT+PUSH+PR DESARROLLO (AUTORIZADO); LUEGO JIT FREE/AUTH, CLOUDFLARE, CERTIFICACION, MERGE Y DEPLOY SEPARADOS` |

## Porcentaje De Avance

### Hitos H2-H5

| Unidad | Estado | Puntos |
|---|---|---:|
| `H2-CA2` | `CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN` | 100 |
| `H2-CA3` | `CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN` | 100 |
| `H3-CA4` | `H3_PR_DEVELOPMENT_READY_LOCAL` | Bloqueadores HIGH/CRITICAL para PR resueltos en el ciclo de corrección local del 2026-09-02; UAT canónica 47/47 y 141/141 PASS con 0 retries |
| `H4-CA5` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H4-CA6` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H4-CA7` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H4-CA13H` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA8` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA9/CA12` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA10` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA11` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |
| `H5-CA13R` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | 0 |

`Progreso H2-H5 ponderado por criterios = 265 / 1200 x 100 = 22.08%`.

`H3-CA4 = H3_PR_DEVELOPMENT_READY_LOCAL. UAT canónica 47/47 y 141/141 PASS con 0 retries regenerada el 2026-09-02; gates locales revalidados el 2026-09-03, incluyendo regresión PG17 A6/A13 para el delta 20260903. JIT-A remoto hasta 20260902 conserva A6/A13 FAIL históricos; JIT-B conserva E1/E3/E4/E8 PASS y E2/E5/E6/E7 pendientes. Build normal/mock PASS y waiver static export superseded. Commit + push + PR a desarrollo autorizados por instrucción humana separada.`

### Homologacion

`Flujo simple promovido por PR protegido a desarrollo, certificacion y main. Nuevos alcances esperan GO del cliente.`

## Porcentaje De Desviacion

`H3_PR_DEVELOPMENT_READY_LOCAL`: el audit de readiness previo revocó el GO para PR (histórico `H3_PR_DEVELOPMENT_NO_GO`); el ciclo de corrección y la revalidación documental del 2026-09-03 resolvieron los gates locales e incorporaron el delta `20260903_h3_rbac_contract_fix.sql` con regresión PG17 A6/A13. JIT-A remoto hasta `20260902` conserva A6/A13 FAIL históricos; JIT-B conserva E1/E3/E4/E8 PASS y E2/E5/E6/E7 pendientes. Commit + push + PR autorizados por instrucción humana separada; JIT remoto posterior sigue separado.

La ruta excede la optimizacion original de cinco PR porque la auditoria detecto autoridad faltante, enlaces rotos, trazabilidad insuficiente y endurecimiento H2 adicional. La desviacion queda registrada como remediacion obligatoria previa al PR H2.

## Cumplimiento De Criterios

- Hito 1: `COMPLETED_CONTRACTUALLY_WITH_WAIVERS`.
- Hito 2: DDL Free remediada, backfill editorial, seed diccionario, fix de vista publica y compatibilidad legacy aplicados/verificados; PR #458, PR #459, PR #460, PR #466 y PR #467 aprobados/mergeados con CI verde; post-apply Free detecto `227` cursos legacy elegibles, `227` efectivos, `0` faltantes y `0` inesperados; certificacion `4cc2e34c` muestra catalogo, detalle y comparador sin React #418, 401 ni 404 de rutas exportadas criticas; criterios contrastados contra `SRC-REQ-002` via adenda sanitizada.
- Hito 3: `H3_PR_DEVELOPMENT_READY_LOCAL`. Gates locales revalidados el 2026-09-03, delta `20260903_h3_rbac_contract_fix.sql` probado con regresión PG17 A6/A13, UAT canónica histórica 47/47 y 141/141 PASS con 0 retries, build normal/mock PASS; JIT-A/JIT-B remotos mantienen los pendientes documentados en sus evidencias.
- Hitos 4-5: planificados según dependencias del nuevo plan vinculante.
- Evidencia historica: no reutilizable como PASS.
- `active_work_package = NONE_SUPERSEDED`.
- Redefinicion: `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO`.
- Rutas protegidas: sin cambios frente a `origin/main@9b48614`.
- Leads: schema/flags y CTA visual solamente; cero captura/egress.
- Schedules: requieren autorizacion separada para cambios de estado.

## Hallazgos Y Backlog

- PR #414, #415 y #416 fueron fusionados mediante PR protegidos.
- El flujo normal de PR protegido queda restaurado para cambios futuros.
- H2 compat esta mergeado en `certificacion` por PR #467 y el despliegue esta estable. La siguiente accion es remediacion productiva Pro/main: `expand + compatibilidad` aditivo, DB Sync H2 por manifest y verificacion de baseline Pro `224` antes de cualquier PR efectivo a `main`. Cualquier DDL/DML adicional requiere JIT separada.
- API de tipo de cambio permanece backlog.
- Ruta canónica contractual futura: `/programas/[slug]`.
- H3 ampliado: `H3_PR_DEVELOPMENT_READY_LOCAL`. Ciclo de corrección local completado: workflow/allowlist/db-gate H3, invariantes DB, MFA real, E2E, rollback y artifacts resueltos; auditorías repetidas sin HIGH/CRITICAL; UAT canónica 47/47 y 141/141 PASS. Static build revalidado PASS. Commit + push + PR autorizados.
- H2 remediacion Free: `20260826_h2_security_advisor_remediation.sql` aplicado y verificado read-only; backfill Free aplicado con segundo `NOOP`; seed `editorial_field_definitions` aplicado con 41 definiciones y visibilidad publica acotada; `20260826_h2_public_effective_view_public_fields_fix.sql` aplicado y verificado con `0` campos privados en `courses_public_effective` remoto.

### Backlog Tecnico Post Requerimiento 1

- `BACKLOG-HIGIENE-EOL-001`: se detectaron nueve archivos con ruido exclusivo CRLF/LF; `git diff --ignore-space-at-eol` no mostro cambios funcionales y fueron restaurados a HEAD para no contaminar H2. Si reaparece el ruido, normalizar EOL en tarea separada.
- `BACKLOG-MAINT-WRITERS-001`: `scripts/maintenance/lightweight_ping.py` y `scripts/maintenance/preventive_cleanup.py` son herramientas manuales con capacidad de escritura/borrado sobre datos; quedan fuera del alcance H2 actual y deben revisarse despues de cerrar el requerimiento 1 antes de conservarlas, retirarlas o endurecerlas.
- `BACKLOG-MAINT-REPORTS-001`: reportes legacy en `scripts/maintenance/*audit*.py` y `metadata_quality_report.py` siguen leyendo `courses` directamente; deben evaluarse frente al contrato H2 `courses_public_effective`, RLS/grants y pipeline tolerante antes de reutilizarlos.
- `BACKLOG-TEST-LEGACY-001`: `tests/test_harvester.py` contiene pruebas de integracion vivas contra Supabase y supuestos legacy sobre `courses`; requiere clasificacion posterior para mantenerlo, aislarlo o migrarlo al contrato H2.
- `BACKLOG-UTILS-ACTIVE-001`: `scripts/shared/utils.py` es dependencia activa de workers core; no debe eliminarse como basura. Solo corresponde normalizar EOL o modificarlo con alcance tecnico explicito.
- Estos hallazgos no autorizan cambios de codigo, DB, writers, backfill, schedules ni limpieza destructiva durante H2; se revisaran al finalizar el requerimiento 1.

## Avances

- O0-A completado.
- O0-B aprobado.
- Escaneo historico completado.
- D0 suplementario ejecutado con reporte redactado.
- Archives de desarrollo y certificacion preservados.
- Fuentes locales verificadas y hasheadas sin versionar contenido.
- T_CANONICO construido desde PR #327.
- Flujo simple desplegado y luego superseded por GO documental.
- Soporte temporal raiz eliminado definitivamente; autoridad queda en `AGENTS.md` y Obsidian.
- WP/digest/Context Graph dejan de ser autoridad ejecutable.
- PR #413 cerrado sin merge y excluido.
- PR #414, #415 y #416 fusionados.

## Siguientes Pasos

1. Corregir el runner H3 para producir exactamente 47 casos lógicos y separar sus ejecuciones por viewport.
2. Cerrar transporte independiente, reglas de publicación, locking de estados, valores efectivos, negativos `aal1`, mutaciones de membresía y auditoría completa.
3. Ejecutar una corrida limpia de mock Auth/static server y UAT 47/47 en 1440x900, 768x1024 y 390x844.
4. Ejecutar pytest completo, Python compile, credential scan, revisión de seguridad, TypeScript, lint, build, harness PG17, segunda corrida NOOP e integridad de artifacts.
5. Reconciliar documentación y, solo con todos los gates PASS, declarar `H3_LOCAL_EXPANDED_GO`.
6. No ejecutar Supabase/Auth remoto, Cloudflare, DNS, DB Sync, writers, schedules, push, PR, merge ni deploy sin aprobación JIT separada.

## Fecha

2026-08-30

## Resultado validado del Prompt CONTINUA H3REQ1 extendido

### Explicación sin términos técnicos

La oficina privada todavía no abre en la copia del sitio usada para probar. El
catálogo de pruebas está bien armado, pero ninguna prueba funcional pasó. Después
se comenzó a ordenar el código que construye las páginas, aunque ese trabajo quedó
parcial y aún no fue probado de principio a fin. Por eso no se puede publicar ni
pedir acceso a servicios reales.

`H3_LOCAL_EXPANDED_NO_GO`

- UAT canónica versionada: `0/47` casos lógicos y `0/141` ejecuciones PASS; 141 screenshots de una corrida completa fallida, sin retries.
- Causa observable: HTTP 404 en `/admin/` y `/admin/login/`, seguido de timeouts y errores de consola.
- Build mock: cierre no acreditado; la generación estática observada falla porque `generateStaticParams` consume `SUPABASE_URL` desde un módulo marcado `'use client'`.
- Los resultados históricos de pytest, TypeScript, lint, `py_compile` y PG17/NOOP se conservan como evidencia parcial y no sustituyen la UAT fallida.
- No existe artifact canónico que demuestre una segunda corrida PASS.
- `sessionStorage` es riesgo pendiente sin waiver formal completo.
- Acciones remotas no ejecutadas ni autorizadas: commit, push, PR, merge, deploy, Supabase, Cloudflare y DNS.

### Resolución y auditoría posterior (2026-09-02)

El ciclo siguiente corrigió hidratación, hostname y selector 035, y produjo dos
corridas estructurales 47/47 y 141/141 PASS. La auditoría posterior de readiness
revocó el GO para PR: `H3_PR_DEVELOPMENT_NO_GO` (histórico). QA, seguridad y DB
detectaron bloqueadores HIGH/CRITICAL en CI H3, contratos DB, MFA real, cobertura
E2E, rollback y artifacts. Build normal/mock revalidado PASS; waiver static export
superseded.

### Resolución final del ciclo de corrección (2026-09-02)

El ciclo de corrección local resolvió los bloqueadores HIGH/CRITICAL:
`security-audit.yml` corregido (allowlist H3 + `db-gate` con harness PG17, gate
emulado `GATE_OK`), contrato `20260902_h3_pr_contract.sql` (lector efectivo + gate
de publicabilidad), seed idempotente con categorías, harnesses
`h3_pg17_harness_ok` / `h3_pg17_harness_local_ok`, MFA con secreto/QR y `aal`
real, y UAT canónica regenerada: **47/47 casos y 141/141 ejecuciones PASS, 141
screenshots, 0 retries** (evidencia `.context/evidencia/h3-expanded/`).
Estado resultante: `H3_PR_DEVELOPMENT_READY_LOCAL`. Commit + push + PR protegido a
`desarrollo` quedaron autorizados por instrucción humana separada; JIT Free/Auth,
Cloudflare, certificación, merge y deploy permanecen como gates posteriores.

## Próximo Prompt CONTINUA H3REQ1 extendido

```text
CONTINUA H3REQ1 — CORRECCIÓN LOCAL DE BUILD/UAT HASTA GO

Estado inicial: `H3_LOCAL_EXPANDED_NO_GO`. En palabras simples, las páginas privadas no aparecieron en la copia construida del sitio y ninguna de las 141 comprobaciones pasó. Después se inició una corrección: `generateStaticParams` ya usa `web/src/lib/supabase-server.ts`, pero otras tareas ejecutadas durante la construcción todavía importan desde el módulo marcado `'use client'`. La separación no está terminada, no existe una nueva construcción completa acreditada y no hay evidencia de dos corridas PASS.

Este prompt autoriza exclusivamente análisis, implementación, pruebas y documentación local en Docker hasta alcanzar GO verificable. NO autoriza commit, push, PR, Supabase writes, Auth remoto, Edge Function, Cloudflare, DNS, merge, deploy, schedules ni `workflow_dispatch`.

FASE A — CORREGIR BUILD Y RUTAS
- Revalidar rama `feat/h3req1-extended`, árbol, diff y alcance sin tocar `.env*` ni exponer credenciales.
- Separar configuración Supabase server-safe de utilidades client-only; `generateStaticParams` no debe importar valores desde un módulo marcado `'use client'`.
- Ejecutar `build:mock` dentro de `studiamatch-dev` y exigir exit 0 sin errores de generación estática.
- Verificar antes de UAT que `web/out/admin/index.html`, `web/out/admin/login/index.html`, `web/out/admin/edit/index.html` y `web/out/admin/users/index.html` existan y sean servibles en localhost.
- Mantener la guarda de producción: endpoint mock solo local, sin endpoint remoto ni referencia `service_role` en bundle.

FASE B — REVALIDAR UAT Y GATES
- Arrancar una sola instancia de mock Auth y static server; comprobar health, puertos y ausencia de `EADDRINUSE`.
- Ejecutar exactamente 47 casos lógicos x 3 viewports = 141 ejecuciones, cero retries, cero duplicados/huérfanos, cero 404 inesperados y cero errores atribuibles de consola/red.
- Verificar resultados funcionales completos para RBAC, ownership, transporte independiente, cola/paginación, mutaciones, auditoría, MFA AAL1/AAL2, membresías/invitación, último admin, hostname y no degradación pública.
- Persistir atómicamente matriz, executions, manifest, screenshots y hashes. Una corrida solo es PASS si 47/47 y 141/141 pasan.
- Repetir una segunda corrida completa PASS sin retries y conservar evidencia canónica diferenciada o un índice que acredite ambas corridas.
- Ejecutar en Docker pytest completo, TypeScript, lint, py_compile, harness PG17/NOOP, `git diff --check`, credential scan del diff/bundle/artifacts y revisión especializada de seguridad. Cero HIGH/CRITICAL y ningún secreto.

FASE C — DOCUMENTACIÓN Y HANDOFF
- Reconciliar estado, hito, matriz, backlog, evidencia cliente, planes, seguimiento y reporte únicamente con resultados reales.
- No tratar `sessionStorage` como waiver aprobado: resolverlo o documentar causa, evidencia, owner, riesgo residual, vencimiento y solicitar aprobación humana separada.
- Solo con build limpio, dos UAT PASS y todos los gates finales declarar `H3_LOCAL_EXPANDED_GO` y preparar localmente el paquete/cuerpo del PR con la plantilla versionada, sin commit ni publicación.
- Si cualquier gate falla, conservar `H3_LOCAL_EXPANDED_NO_GO`, registrar causa reproducible y continuar corrigiendo localmente salvo condición real de detención.
- Al alcanzar GO, detenerse y solicitar por separado: A) autorización para commit + push + PR protegido a `desarrollo`; B) después, JIT Supabase Free/Auth. No ejecutar ninguna acción remota por inferencia.
```
CONTINUA H3REQ1 EXTENDIDO — EJECUCIÓN INTEGRAL LOCAL HASTA GO Y PREPARACIÓN DEL SIGUIENTE GATE

Este `continua` autoriza un único ciclo integral de implementación, corrección, pruebas y documentación exclusivamente local en Docker hasta alcanzar `H3_LOCAL_EXPANDED_GO`. No vuelvas a pedir `continua` entre iteraciones locales: analiza, implementa, valida, revisa hallazgos, conviértelos en tareas, corrige y revalida hasta cerrar todos los gates o encontrar una condición real de detención.

No autoriza Supabase writes, Auth remoto, Edge Function remota, Cloudflare Access, DNS, DB Sync, backfills, writers, schedules, push, creación o actualización remota de PR, merge, deploy ni `workflow_dispatch`. Al alcanzar GO local debes preparar completamente el paquete local del PR y detenerte para solicitar las aprobaciones humanas separadas de: A) push + creación de PR protegido a `desarrollo`; B) JIT Supabase Free/Auth para aplicar y probar los artefactos H3. No confundas preparación de PR con autorización para publicarlo.

ESTADO DE PARTIDA
- Gate: `H3_LOCAL_EXPANDED_NO_GO`.
- Implementación estática estimada histórica: 64.1%; validación verificable histórica: 37.7%. No son aceptación.
- Última UAT ampliada versionada: 47 casos, 141 ejecuciones, 0 PASS; rutas admin 404.
- El runner ya representa 47 IDs lógicos x 3 viewports; la estructura es válida, la ejecución funcional no.
- Build mock vigente: requiere corregir el consumo server-side de configuración exportada desde un módulo `'use client'`.
- Harness previo: `h3_pg17_harness_local_ok`.

REGLAS DE EJECUCIÓN
- Usa `todowrite` y mantén exactamente una tarea en progreso. Convierte cada hallazgo en tarea y no cierres ninguna sin evidencia.
- Todo npm, Python y pip corre dentro de `studiamatch-dev`; SQL local corre únicamente en el contenedor PostgreSQL 17 autorizado.
- No leas ni imprimas valores de `.env*`, passwords, tokens, API keys, JWT, cabeceras Authorization, PII ni secretos. Las comprobaciones de bundle y entorno reportan solo booleanos o nombres de variables.
- No uses `docker compose down -v`, no borres volúmenes, no mates procesos no identificados y no alteres datos fuera de fixtures/transacciones locales.
- Preserva funcionalidad, escalabilidad, seguridad, mantenimiento, calidad y rendimiento, además de `expand -> compatibilidad -> deploy pendiente -> contract`, rollback y no degradación.
- No declares PASS por intención, implementación estática, prueba parcial, retry o promedio. Si un test revela un defecto, corrige la causa y repite el gate afectado y la regresión completa.

FASE 0 — PREFLIGHT Y AISLAMIENTO
1. Revalida la autoridad canónica, la atestación sanitizada `H3-EXPANDED-PROMPT-2026-08-30`, alcance Git y ausencia de drift.
2. Inventaría Docker, PostgreSQL 17, puertos 3000/3001 y procesos mock sin mostrar entornos sensibles.
3. Investiga sanitizadamente los valores credential-like observados previamente. Si se confirma un secreto real o posible exposición, detente: no lo copies; registra solo tipo/ubicación sanitizada y solicita rotación humana separada.
4. Define cleanup garantizado para navegador y servidores incluso ante fallo. Solo una instancia de Auth mock y una de static server pueden quedar activas.
5. Gate: entorno reproducible, sin drift, sin secreto confirmado y sin puertos/procesos conflictivos.

FASE 1 — CONTRATOS Y POSTGRESQL 17
1. Revisa y completa enforcement `aal2`, RBAC y grants para anon, authenticated sin membresía, inactivo, user y admin.
2. Completa cola y contador: filtros editorial/calidad, archivados excluidos, más de una página, cursor estable, `endCursor`, siguiente/anterior y parámetros inválidos.
3. Completa optimistic locking por `version` en update, publish, unpublish, archive y quality; los conflictos deben ser visibles y no generar mutación parcial.
4. Alinea publicación con el diccionario real de campos requeridos/calidad y valida el lector de valores efectivos preservando `manual_overrides`.
5. Completa membresías: alta/invitación contractual local, cambio de rol, activación, desactivación y revocación; conserva al menos un admin activo y evita auto-bloqueo accidental.
6. Verifica una única auditoría atómica por mutación editorial o de membresía. Ambas auditorías son append-only: `UPDATE`, `DELETE` y `TRUNCATE` deben rechazarse.
7. Ejecuta las migraciones H3 sobre un baseline local PG17 limpio con forma Pro y después una segunda corrida NOOP. No uses ni sincronices datos operativos remotos.
8. Gate: harness completo PASS, segunda corrida NOOP, firmas/constraints/índices/grants/RLS/vistas/RPC locales inventariados y sin hallazgos HIGH/CRITICAL.

FASE 2 — TRANSPORTE Y OWNERSHIP
1. Corrige el transporte independiente `enrichment -> sync -> courses` de `benefits`, `certification`, `objectives` y `target_audience`; elimina el vacío forzado, omisiones y reutilización semántica incorrecta documentados en `sync_vector_worker.py`.
2. Añade un fixture determinista con cuatro valores inequívocamente diferentes y assertions en cada estación; cubre nulos, reprocesamiento y compatibilidad legacy. No uses fallback para aparentar cobertura.
3. Valida los 13 campos: `name`, `price_pen`, `price_status`, `mode`, `duration`, `description_long`, `syllabus`, `target_audience`, `requirements`, `certification`, `benefits`, `objectives`, `start_date_text`.
4. Admin puede corregir los 13. User solo completa campos presentes en `missing_fields`; rechaza identidad, institución, URL, slug, categoría, fecha estructurada, tipo, brochure, ROI, métricas, estados, timestamps y metadata.
5. Gate: cuatro valores independientes preservados hasta `courses`, 13 campos cubiertos uno a uno, `manual_overrides` preservados y regresiones de pipeline PASS.

FASE 3 — FRONTEND, MFA, MEMBRESÍAS Y HOSTNAME
1. Cubre admin y user: login, enrollment TOTP, challenge, verify válido, código inválido, sesión `aal2`, refresh, logout, unenroll/revocación y expiración/error.
2. Añade negativos `aal1` para cada operación sensible y confirma aceptación en `aal2`.
3. Implementa o simula únicamente local el contrato backend protegido de invitación; valida email inválido, duplicado y rol inválido sin afirmar Auth/Edge Function remotos y sin `service_role` en navegador.
4. Ejecuta en UI cambio de rol, activación, desactivación y revocación de admin/user con estado, confirmación, loading, error y feedback persistente.
5. Completa cola, filtros, contador, paginación siguiente/anterior, valores efectivos y conflictos de edición visibles.
6. Genera build mock limpio con endpoint local. Comprueba solo: `mock_endpoint_present=true`, `remote_endpoint_present=false`, `service_role_reference_present=false`.
7. Arranca una instancia de cada servidor; valida Auth/RPC mock, rutas exportadas, recursos same-origin, hostname administrativo local permitido y `Host: studiamatch.com` + `/admin/` = HTTP 404.
8. Gate: capacidades/rechazos coinciden en UI y backend; cero requests remotos, cero 404 inesperados, cero errores atribuibles de consola/red.

FASE 4 — RUNNER UAT DETERMINISTA
1. Reconstruye `tests/h3_local_uat.mjs` con un catálogo inmutable de exactamente 47 IDs únicos `H3-UAT-001..H3-UAT-047`, mapeados así:
   - H3-CA4.1 Auth/RBAC: 5.
   - H3-CA4.2 Ownership/valores efectivos: 5.
   - H3-CA4.3 Transporte independiente: 2.
   - H3-CA4.4 Cola/paginación: 5.
   - H3-CA4.5 Mutaciones/locking/publicación: 6.
   - H3-CA4.6 Auditoría: 4.
   - H3-CA4.7 MFA/assurance: 6.
   - H3-CA4.8 Membresías/invitación/último admin: 6.
   - H3-CA4.9 Hostname/perímetro: 3.
   - H3-CA4.10 Convergencia/NOOP: 2.
   - H3-CA4.11 runtime/responsive/accesibilidad: 3.
2. Ejecuta el producto cartesiano completo en 1440x900, 768x1024 y 390x844: `logical_cases=47`, `viewport_executions=141`. No omitas casos por viewport. Un caso lógico pasa solo si pasan sus tres ejecuciones.
3. Valida estructura antes de abrir Chromium: 47 IDs únicos, distribución exacta, 141 ejecuciones esperadas y paths de artifacts seguros.
4. Instala listeners antes de navegar; usa esperas de DOM/respuesta, no sleeps arbitrarios; serializa mutaciones, restaura fixture entre viewports y no dependas del orden.
5. Cada ejecución registra ID, criterio, rol, assurance, hostname, viewport, ruta, esperado, observado, assertions, HTTP, consola, requests fallidos, duración, timestamps, resultado y screenshot.
6. Usa `try/catch/finally`, persistencia atómica y cierre garantizado. Un artifact ausente, vacío o no hasheable es FAIL. Cero retries en la corrida canónica.
7. Gate: 141/141 ejecuciones PASS, 47/47 casos lógicos PASS, tres ejecuciones por ID, 47 por viewport, cero duplicados/huérfanos y cero errores atribuibles.

FASE 5 — REGRESIÓN Y ESTABILIDAD EN DOCKER
1. Ejecuta pruebas dirigidas H3 y pytest completo.
2. Ejecuta `py_compile` de `enrichment_worker.py` y `sync_vector_worker.py`.
3. Reejecuta harness PG17 y NOOP.
4. Ejecuta `npm run lint`, `npx tsc --noEmit`, build mock y build normal controlado sin tráfico remoto.
5. Ejecuta smokes de hostname, rutas públicas y recursos same-origin.
6. Ejecuta revisión visual, teclado, foco, labels, overflow y accesibilidad básica en los tres viewports; revisa rendimiento local sin convertirlo en afirmación de producción.
7. Ejecuta credential scan del diff/artifacts y revisión especializada de seguridad. Cero HIGH/CRITICAL y cero secretos. Lint: cero errores y ningún warning nuevo frente a los nueve preexistentes documentados.
8. Ejecuta una segunda corrida completa de UAT 47/47 y 141/141 sin retries para demostrar repetibilidad.
9. Ejecuta `git diff --check` y revisa que no existan cambios accidentales ni archivos sensibles.
10. Gate: todos los comandos PASS en dos corridas estables cuando aplique; cualquier flake, retry, timeout, warning nuevo o diferencia no explicada mantiene NO-GO.

FASE 6 — EVIDENCIA, DOCUMENTACIÓN Y DECLARACIÓN
1. Regenera solo `.context/evidencia/h3-expanded/`; preserva artifacts históricos.
2. Produce manifest, matriz de 47 casos, detalle de 141 ejecuciones, 141 screenshots frescos, status, logs sanitizados y hashes SHA-256. Verifica consistencia cruzada y ausencia de secretos, tokens, headers Auth, passwords y PII sensible.
3. Actualiza con resultados reales: estado del proyecto, hito, implementation report, tarea, matriz, evidencia cliente, plan maestro, plan vinculante y seguimiento.
4. Documenta `expand`, compatibilidad, rollback, no degradación, deploy/contract pendientes, limitaciones mock y waiver `sessionStorage`; no afirmes Supabase Auth, Free, Cloudflare ni producción sin evidencia remota autorizada.
5. Si cualquier gate falla, conserva `H3_LOCAL_EXPANDED_NO_GO`, registra bloqueador reproducible y continúa corrigiendo localmente salvo condición de detención.
6. Solo con todos los gates PASS declara exactamente `H3_LOCAL_EXPANDED_GO`.

FASE 7 — PREPARACIÓN LOCAL DEL PR Y HANDOFF
1. Después de GO, prepara sin publicar: diff final, inventario de archivos, commits propuestos sin crearlos, resultados reales, riesgos/waivers, rollback y cuerpo completo basado en `.github/pull_request_template.md` sin placeholders.
2. Verifica que la rama candidata emerja de `desarrollo` y define el orden remoto: push de la rama -> PR protegido a `desarrollo` -> JIT Supabase Free/Auth -> aplicar/probar artefactos H3 en Free -> incorporar evidencia real al mismo PR -> security-audit/revisión -> merge solo con aprobación posterior.
3. Detente y solicita opciones concretas separadas:
   A. Autorizar commit + push + creación del PR protegido a `desarrollo`.
   B. Autorizar JIT Supabase Free/Auth, incluyendo inventario previo, migraciones H3, configuración Auth/MFA, Edge Function de invitación y pruebas remotas; ninguna acción Pro.
   C. Mantener ambas acciones bloqueadas.
4. No ejecutes A ni B por inferencia ni porque este prompt haya alcanzado GO. Push/PR y Supabase writes requieren instrucciones humanas separadas y explícitas.

CONDICIONES DE DETENCIÓN
- Secreto real o posible exposición que requiera rotación.
- Drift de scope, baseline Pro, ambiente, rama protegida o fuente cliente.
- Acción destructiva, remota, DDL/DML, Auth, Cloudflare, push, PR, merge o deploy no autorizada separadamente.
- Decisión funcional no resuelta o imposibilidad de obtener evidencia reproducible.

SALIDA FINAL DEL CICLO
- Si falla: estado `H3_LOCAL_EXPANDED_NO_GO`, bloqueadores exactos, evidencia y siguiente corrección local.
- Si pasa: estado `H3_LOCAL_EXPANDED_GO`, resumen de gates, ubicación de artifacts, paquete local del PR listo y solicitud separada de A/B/C. No avances automáticamente a H4/H5 ni a acciones remotas.
```
