# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-09-24-H3-CYCLE4-NO-GO-REMOTE-DRIFT`.

Historical gates preserved: `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED`, `PRODUCTION_REMEDIATION_PRO_EXPAND_COMPAT_BEFORE_MAIN`, `H2_CLOSED_H3_READY_FOR_PROMPT_CONTINUA`, `H3_READY_FOR_PROMPT_CONTINUA`, `H3_GO_LOCAL_CLOSED_READY_FOR_SUPABASE_FREE_JIT`, `H3_SUPABASE_FREE_AUTH_JIT_VALIDATION`, `H3_LOCAL_EXPANDED_NO_GO` (histórico del ciclo anterior, fechado 2026-08-30), `H3_PR_DEVELOPMENT_NO_GO` (readiness, resuelto por el ciclo de corrección local del 2026-09-02).

Esta nota es la autoridad exclusiva del estado vivo del proyecto y de sus fases.
Ningun documento historico crea alcance ni autoriza ejecucion por fuera de esta nota.

## Resumen H3 En Lenguaje Simple

### Qué se intenta construir

H3 agrega una zona privada para que personas autorizadas revisen y corrijan la
información de los cursos. Hay dos tipos de personas: `user`, que completa datos
faltantes, y `admin`, que además aprueba cambios y administra usuarios. El acceso
debe usar una segunda comprobación de seguridad y la zona privada no debe aparecer
en la dirección pública normal.

### Qué significa el estado actual

`H3_PR_DEVELOPMENT_READY_LOCAL` acredita **GO técnico local**, no cierre
contractual. El ciclo read-only 2 del 2026-09-24 mantiene
`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`: Free ahora registra las
migraciones 03A/03B y los hardenings 20260924, pero Pro sigue sin migraciones H3,
tablas ni RPCs consultables. También faltan UAT
remota completa, hostnames por ambiente, Certification y la transición
`deploy -> contract`. La UAT canónica local conserva 47/47 casos y 141/141
ejecuciones PASS con cero reintentos.

### Qué se corrigió desde la prueba fallida anterior

La corrida inicial falló porque las páginas privadas no aparecían en la copia
servida. El programa de pruebas se corrigió para esperar a que la página terminara
de cargar antes de interactuar (espera de hidratación), se validó el bloqueo
público `studiamatch.com/admin/ → 404` sobre un servidor de perímetro real
(`static-server.js`) y se corrigió un selector de prueba.

### Qué acredita la evidencia actual

- UAT canónica `h3_local_uat.mjs` regenerada el 2026-09-02: **`47/47` casos y
  `141/141` ejecuciones PASS, 141 screenshots, 0 retries**, evidencia en
  `.context/evidencia/h3-expanded/`.
- Build normal y `build:mock` ejecutados en Docker el 2026-09-03: compilación
  exitosa y rutas `web/out/admin/{index,login,edit,users}/index.html` presentes.
  El waiver de static export queda superseded para este candidato.
- Suite CI-local seleccionada: 142 tests PASS; TypeScript PASS; lint sin errores
  (9 warnings históricos); `py_compile`, credential scan, actionlint, shellcheck,
  mock smoke y `git diff --check` PASS. H2/H2-Pro/H3 PG17 PASS; el harness H3
  termina en `h3_pg17_harness_ok` e incluye regresión A6/A13.
- La corrida completa indiscriminada `pytest -q` no es un gate válido en este
  checkout porque recolecta worktrees históricos montados bajo `local/worktrees/`
  y tests de integración que requieren entorno; produjo 540 errores de colección.
  El PR usa el conjunto versionado del job `python-check` y documenta esta
  exclusión.

### Qué resolvió el ciclo de corrección local (2026-09-02) y la sincronización documental (2026-09-03)

El ciclo descrito en [Siguiente Gate](#siguiente-gate) eliminó los bloqueadores
locales que la auditoría de readiness había identificado en CI, contratos DB, MFA
local, UAT/evidencia y rollback; la sincronización del 2026-09-03 incorporó el
delta A6/A13 y separó explícitamente la evidencia remota parcial:

1. `security-audit.yml` corregido (YAML válido), allowlist H3 explícita y
   `db-gate` con harness H3 en PG17; gate emulado localmente `GATE_OK`.
2. Migración `20260902_h3_pr_contract.sql`: lector efectivo de valores y gate de
   publicabilidad; seed idempotente con categorías para los 30 cursos.
3. MFA: `admin-auth.ts` y login muestran secreto/QR y resuelven `aal` real sin
   forzarlo; retirado el spec UAT duplicado.
4. Perímetro 3002 con `Host` mapping correcto (`/admin/login` 200 en admin
   origin, `/admin/` 404 en `studiamatch.com`).

### Qué sigue ahora

Commit + push + PR protegido a `desarrollo` quedaron **autorizados por
instrucción humana separada** y se ejecutan con la plantilla
`.github/pull_request_template.md` llena con resultados reales del ciclo.
Permanecen como gates remotos posteriores y separados: `security-audit` en
GitHub y revisión del PR, aplicación/revalidación de `20260903` en Free,
configuración Auth, Cloudflare restante, promoción a `certificacion`, merge y
deploy. No se ejecuta ninguna de esas acciones sin su aprobación.

### Auditoría Final De Cierre H3REQ1 (2026-09-23)

El documento canónico es
[H3REQ1 Closure Review Final](hitos/h3req1_closure_review_final_2026-09-23.md).
La decisión es `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`.

- MFA fue retirado del gate de aceptación por decisión de alcance: la prueba es
  compleja y no bloquea autenticación administrativa existente, RBAC,
  invitaciones, onboarding, edición, ownership ni perímetro. El MFA/`aal2`
  existente se conserva como compatibilidad y mejora evolutiva.
- La evidencia local permanece PASS: core H3 47/47 y 141/141, builds,
  contratos, PG17, Edge 03A, DB 03B y Mock UAT-02.
- La evidencia remota permanece parcial: `admin-invite` está ACTIVE con
  `verify_jwt=true`, pero las migraciones 03A/03B no aparecen en los inventarios
  remotos revisados; el preview de Development devuelve 404 para callback,
  aceptación y setup de password.
- No se autoriza promoción `desarrollo -> certificacion -> main`, deploy, merge,
  push ni writes adicionales con la evidencia actual.

### Diccionario mínimo

- `GO`: evidencia suficiente para pasar al siguiente control; no significa publicar.
- `NO_GO`: hay fallas o evidencia insuficiente; se debe corregir y volver a probar.
- `build`: proceso que convierte el código en las páginas que se pueden servir.
- `UAT`: prueba que usa la interfaz como lo haría una persona.
- `PASS` / `FAIL`: comprobación aprobada / comprobación fallida.
- `mock`: imitación local de un servicio real, usada para probar sin tocar internet.
- `JIT`: autorización humana puntual para una acción concreta y sensible.
- `PR`: solicitud para revisar cambios antes de integrarlos.

## Pilares Transversales Obligatorios

Todo desarrollo futuro del producto debe preservar continuamente funcionalidad,
escalabilidad, seguridad, mantenimiento, calidad y rendimiento. Ningun hito, task o
requerimiento puede cerrarse sin validar estas premisas frente al alcance
ejecutado.

Para cualquier nuevo desarrollo con requerimiento cliente, antes de iniciar y al cerrar un hito o task vinculado a un requerimiento se debe validar criterios de aceptacion contra el documento privado del cliente mediante atestacion sanitizada versionada.
El documento privado no se versiona y no se expone en PRs;
la evidencia versionada solo registra el identificador de fuente, resultado y
trazabilidad.
Si este gate documental falla, no se puede ejecutar codigo, DB, UI, pipeline ni
PR del hito siguiente hasta corregir la atestacion sanitizada.

Todo cambio funcional, DB, UI, pipeline o despliegue debe incluir una transicion
transparente obligatoria: `expand -> compatibilidad -> deploy -> contract`.
Durante construccion y promocion se debe preservar el comportamiento legacy
necesario para que la aplicacion siga funcionando; luego de estabilizar en
produccion se debe retirar la funcionalidad legacy y dejar activo el nuevo
contrato solicitado. Ningun hito, task o PR puede cerrarse ni promoverse sin
documentar compatibilidad, contraccion, rollback y evidencia de no degradacion
funcional.

Todo prompt futuro de desarrollo queda bajo `PROMPT_RETROALIMENTADO_REQUIRED`
segun [Estandar De Prompts Retroalimentados](operaciones/estandar_prompts_retroalimentados.md).
Un prompt retroalimentado mantiene un ciclo de analizar, implementar, validar,
revisar, convertir cada fallo, hallazgo, drift o gate incompleto en tareas,
corregir y revalidar hasta cumplir sus criterios de GO. No se declara GO por
intencion, implementacion parcial o pruebas locales cuando el alcance exige
evidencia remota. Si se requiere JIT, push, PR, merge, deploy,
workflow_dispatch, Supabase writes, ramas protegidas o acciones destructivas,
la ejecucion se detiene y se pide aprobacion humana separada con opciones
concretas, recomendacion y consecuencias. Cada aprobacion recibida obliga a
reevaluar estado, actualizar el plan y continuar desde el gate detenido. El
cierre exige evidencia canonica, criterios cliente, pruebas completas,
revisiones especializadas y ausencia de hallazgos HIGH/CRITICAL. No se pueden
ocultar fallos como historicos o fuera de alcance sin demostrar baseline; cada
waiver requiere causa, evidencia reproducible, owner, riesgo, vencimiento y
aprobacion humana.

Todo PR debe usar la plantilla versionada `.github/pull_request_template.md`.
Antes de abrir o actualizar un PR se deben ejecutar las validaciones necesarias
para completar sus secciones con resultados reales. La plantilla no se llena con
intenciones, placeholders ni omisiones silenciosas; toda validacion no aplicable
o pendiente debe indicar causa, riesgo residual y owner.

## Fases

| ID | Fase | Estado | Resultado vigente |
|---|---|---|---|
| `F0`-`F8` | Historia contractual y tecnica | `COMPLETED` | Preservada como antecedente. |
| `F9` | Certificacion Hito 1 CA1-only | `COMPLETED_BY_CONTRACT_REBASELINE` | Historia superseded para ejecucion; no autoriza remediacion operacional historica. |
| `F10` | Produccion CA1-only | `COMPLETED_CONTRACTUALLY_WITH_WAIVERS` | Hito 1 cerrado por decision humana O0-B; F10.9/WP2B y F10.10/M3 quedan historicos no promocionables. |
| `F10.11` | Redefinicion de flujo simple | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Flujo simplificado validado en `desarrollo`, `certificacion` y `main`; preservado como historia no ejecutable. |
| `F11` | H3REQ1 ampliado: campos, invitaciones y hostname; MFA evolutivo fuera del gate | `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` | GO técnico local preservado; UAT remota, 03A/03B remoto, hostnames por ambiente, Certification y contract pendientes. |

## Subfases F10

| ID | Estado | Identidad vigente |
|---|---|---|
| `F10.7` | `COMPLETED_TECHNICAL_DELIVERY` | PR #291 es el cutoff contractual de Hito 1. |
| `F10.8` | `COMPLETED_PRODUCTION_CANARY_VERIFIED` | Evidencia tecnica historica preservada; no ejecutable. |
| `F10.9` | `SUPERSEDED_BY_O0_B` | WP2B queda superseded; PR #413 cerrado sin merge y excluido. |
| `F10.10` | `HISTORICAL_NON_PROMOTABLE` | M3 reader/DDL queda congelado; no autoriza DDL/DML ni payloads. |
| `F10.11` | `DEPLOYED_TO_MAIN_SUPERSEDED_BY_NEW_GO` | Reemplaza WP/digest/Context Graph por flujo simple protegido; el soporte temporal fue retirado al recibir GO documental. |

## Bases Vinculantes

| Concepto | Valor |
|---|---|
| Requerimiento | `REQ-EST-001` |
| Cutoff contractual Hito 1 | PR #291 / `64e4ed895d43121c5683e26a355993f18e528a5c` |
| Baseline tecnico | PR #327 / `main@ad89e8ab9575b37476502d6062e22c044ad6447b` |
| Tree tecnico | `54098b3ff581cc7728979afc8e6d47c9535141b5` |
| Autoridad funcional | `desarrollo@9f163c2c5f8dc54b4986ce75ef1d5c69a740bedf` |
| Certificacion preservada | `certificacion@33b1c9ec3c49117c2020860d5850d9d67988f836` |
| PR #413 | `CLOSED_NOT_MERGED_EXCLUDED`, head `4461f13c79ac893cb428074a729d75140056557b` |
| Archives Etapa 1 | `archive/post-h1-desarrollo-20260820-9f163c2`, `archive/post-h1-certificacion-20260820-33b1c9e` |
| Desarrollo canonico O2 | `desarrollo@a2c97ec17aabc790b656d6db1b16bdc95f0af1b2` |
| Certificacion canonica O2 | `certificacion@4e7e41a9fac08e657308849701b4b1f70b994e3b` |
| Tree canonico O2 | `a03681d271475e8ccbf6061ce63bc4ee5990cd5c` |

## Tarea Activa

- Requerimiento: `REQ-EST-001`.
- Hito: [HITO-003](hitos/hito_003.md).
- Tarea H3: `TASK-H3-001` en el backlog canónico versionado: `backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md`.
- Subfase tecnica activa: `F11`.
- Work package activo: `NONE_SUPERSEDED`.
- Work package completado: `NONE_APPLICABLE`.
- Gate técnico local: `H3_PR_DEVELOPMENT_READY_LOCAL`; gate de cierre vigente: `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`.
- UAT canónica histórica: `47/47` casos y `141/141` ejecuciones PASS con 141
  screenshots y 0 retries, evidencia en `.context/evidencia/h3-expanded/`. La
  regresión A6/A13 del delta `20260903` fue revalidada separadamente en PG17.
- Build normal/mock revalidado en Docker: PASS; rutas admin exportadas presentes.
  El waiver de static export queda superseded para el candidato actual.
- Gates reejecutados en Docker: suite CI-local 142 PASS; TypeScript PASS; lint 0
  errores y 9 warnings históricos; py_compile PASS; credential scan PASS;
  `git diff --check` limpio; actionlint/shellcheck PASS; H2/H2-Pro/H3 PG17
  `h3_pg17_harness_ok` (incluye regresión A6/A13);
  gate `protected-paths` emulado `GATE_OK`. `pytest -q` global indiscriminado no es
  válido por recolectar worktrees históricos y tests de integración fuera del gate,
  y produjo 540 errores de colección.
- Auditorías especializadas del ciclo previo quedaron resueltas para el alcance
  local. JIT-A remoto tiene `20260903` aplicado en Free y A6/A13 corregidos; JIT-DEV
  dejó el ambiente limpio después de probar usuarios/factores temporales. JIT-B
  valida el perímetro y membresía Cloudflare, pero la UAT administrativa completa
  debe usar el deployment/preview correcto por ambiente; E2/E5/E6/E7 no se cierran
  contra `admin.studiamatch.com` mientras este siga asociado al proyecto productivo.
- Commit + push + PR protegido a `desarrollo` quedaron **autorizados por
  instrucción humana separada** y se ejecutan con la plantilla de PR.
- Gates remotos posteriores y separados: UAT administrativa por ambiente, proyecto/
  artefacto Pages admin separado, políticas Access por ambiente, 404 público estable,
  promoción a `certificacion`, merge y deploy. No se ejecutan sin su aprobación.

### Matriz de avance H3REQ1 ampliado

Los porcentajes son estimaciones separadas: implementación no equivale a aceptación; validación exigida solo por evidencia ejecutada y reproducible. La UAT local acredita el cierre local. Development remoto sobre Free valida actualmente el contrato A6/A13 y el entorno de datos; la UAT administrativa/Pages/Access debe ejecutarse contra el deployment correcto de la rama antes de certificar.

| Criterio | Implementación | Validación verificable | Bloqueo principal |
|---|---:|---:|---|
| H3-CA4 local | 78.7% provisional | GO técnico local | `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`; porcentajes previos conservados solo como estimación, no cierre contractual. |
| H3-CA4.1 Auth/RBAC | 90% | 85% | UAT local cubre RBAC y negativos; Auth real pendiente de JIT. |
| H3-CA4.2 Ownership | 85% | 75% | 13 campos y `missing_fields` cubiertos por UAT; falta entorno real. |
| H3-CA4.3 Transporte independiente | 60% | 40% | Fixture E2E diferenciando cuatro campos validado local; falta entorno real. |
| H3-CA4.4 Cola | 85% | 70% | Paginación, cursor y filtros cubiertos por UAT; falta entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | Mutaciones admin y locking cubiertos por UAT; falta entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Auditoría append-only cubierta por UAT; falta entorno real. |
| H3-CA4.7 MFA/`aal2` (fuera del gate) | Evolutivo | No bloqueante | Implementación existente conservada como compatibilidad/mejora evolutiva; no se requiere Auth real para cerrar H3REQ1. |
| H3-CA4.8 Membresías/invitaciones | 85% | 55% | Gestión, último admin, Edge 03A y DB onboarding 03B cubiertos localmente; falta Auth/frontend real y UAT remota. |
| H3-CA4.9 Hostname/perímetro | 60% | 40% | Perímetro Access y 404 público parcial; falta separar el deployment admin por ambiente y validar cada hostname contra su SHA. |
| H3-CA4.10 Convergencia Pro/Free/local | 55% | 35% | PG17 y Free validados; falta diff completo/remoto con Pro como baseline y configuración por ambiente. |
| H3-CA4.11 UAT/artifacts | 100% estructural | 55% contractual | UAT canónica 47/47 y 141/141 PASS con 0 retries regenerada el 2026-09-02; evidencia autocontenida en `.context/evidencia/h3-expanded/`; falta UAT real en Free/Certification. |
| **Promedio simple** | **78.7% provisional** | **No aplica como cierre** | **`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`; UAT administrativa por ambiente, 03A/03B remoto, separación Pages/Access y Certification pendientes.** |

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `REDEFINED_ACTIVE_AFTER_H2_H3` | `TASK-H1-001` |
| `HITO-002` | `CLOSED_H2_PRO_EXPAND_VERIFIED_MAIN` | `TASK-H2-001` |
| `HITO-003` | `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` | `TASK-H3-001` |
| `HITO-004` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | `TASK-H4-001` |
| `HITO-005` | `PLANNED_AFTER_H2_CONTRACT_STABLE` | `TASK-H5-001` |

## Activacion Documental

| Etapa | Estado | Evidencia |
|---|---|---|
| Baseline local | `COMPLETED` | `origin/main@9b486146962bd2a092acfd649fdcf716e922de89` |
| WIP previo | `DISCARDED_BY_AUTHORIZATION` | No se preserva WIP fuera del baseline. |
| Flujo simple | `DEPLOYED_TO_MAIN` | PR #451 a `desarrollo`, PR #452 a `certificacion`, PR #453 a `main`. |
| GO documental | `RECEIVED` | Pedido humano: aplicar actualizacion documental completa y retirar soporte temporal. |
| Soporte temporal raiz | `REMOVED` | `REDEFINICION.md` eliminado definitivamente; no debe recrearse. |
| Plan vinculante | `MOVED_TO_OBSIDIAN` | [Plan vinculante nuevo pedido](operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md). |
| Acciones remotas | `FLOW_NORMALIZED` | Nuevos cambios siguen PR protegido `desarrollo -> certificacion -> main`. |
| CI/CD DB Sync Pro | `H2_VERIFY_NO_OP_APPLY_GATE_FIXED` | Workflow `db-sync-to-pro.yml` ajustado en PRs #480/#481 para que el job `Apply pending migrations` tenga exito como no-op bajo `operation=verify` cuando no hay migraciones pendientes, permitiendo generar el artifact H2 requerido por `security-audit`. |
| Base de datos | `PRO_EXPAND_APPLIED_AND_VERIFIED` | DDL Free inicial, forward-fix, remediacion Security Advisor, backfill editorial, seed, fix de vista y compatibilidad legacy aplicados/verificados en Supabase Free. El manifiesto `h2-expand-compat` fue aplicado y verificado en Pro con backup/PITR verificado; baseline elegible productivo `224`, evidence canonico del run `33143730910` y rerun `33188932351` success, advisors sin hallazgos HIGH/CRITICAL. |
| Evidencia cliente | `GRADE_A_CLIENT_SOURCE_VALIDATED_H2_CERTIFICACION` | Acta ejecutiva y matriz H2 con veredicto, metricas verificables, validacion contra `SRC-REQ-002` via adenda sanitizada, PRs #458/#459/#460 mergeados y QA read-only definida. |
| QA certificacion previa | `PASS_CERTIFICATION_READ_ONLY_QA` | [QA H2/H3 read-only](operaciones/h2_h3_certification_readonly_qa.md) ejecutada antes de la compatibilidad legacy: suite `108 passed`, build/static smoke PASS, vista publica sin privados y advisors sin bloqueantes H2. |
| Compatibilidad Desarrollo | `MERGED_TO_DESARROLLO_READY_FOR_CERTIFICATION_PROMOTION` | PR #466 mergeado a `desarrollo` en `e8376035d8d5c3e1b7893cbb1ede14f735ccd05d`; post-apply Free: `227` cursos legacy elegibles, `227` en cohorte, `227` en `courses_public_effective`, `0` faltantes y `0` inesperados. Preview final `af2ac376` valida Home, detalle, comparador, HTML inicial correcto, bundle sin `ratings`/`reviews` y rutas relacionadas `200`. |
| Compatibilidad Certificacion | `MERGED_AND_DEPLOYED_STABLE` | PR #467 mergeado a `certificacion` en `2d499324bb21e750d9bc7c94cb80e7a193062b50`; deployment `4cc2e34c`; checks verdes; host `https://certificacion.studiamatch-aty.pages.dev/` con Home, detalle y comparador `200`. |
| Remediacion productiva | `H2_EXPAND_VERIFIED_AND_PROMOTED_MAIN` | [Plan De Remediacion Productiva H2](operaciones/h2_production_remediation_plan.md), evidence canonico del run `33143730910`, rerun `33188932351` success y PR #486 mergeado a `main`. |

## H3-BUILD-03B DB Implementation (2026-09-21)

El checkpoint `H3-BUILD-03B-DB-IMPLEMENTATION` fue implementado y validado
localmente en Docker PostgreSQL 17. La evidencia canonica del ciclo es
`.context/evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_db_implementation_local_2026-09-21.md` y el reporte detallado es
`STUDIAMATCH-INFORME-IMPLEMENTACION-H3-BUILD-03B-DB-2026-09-21.md`.

### Cambios validados

- Nueva migracion expand-only `db/migrations/20260921_h3_invitation_onboarding_rpc.sql`.
- TTL server-side de 24 horas desde `last_sent_at`/`sent_at` interno.
- RPCs `admin_accept_current_invitation`, `admin_complete_password_setup` y
  `admin_get_onboarding_status`.
- Locks por email/usuario/invitacion/membresia, expiracion lazy e idempotencia.
- Auditoria `accept`, `expire` y `password_set` sin duplicados efectivos.
- ACL minima, `SECURITY DEFINER`, search path explicito y sin exposicion de
  token, password o secretos.
- Harness nuevo integrado en `tests/sql/h3_pg17_harness.sql`.

### Validacion

- `h3_invitation_onboarding_harness_ok`.
- `h3_pg17_harness_ok`.
- `h3_invitation_edge_runtime_harness_ok`.
- Credential scan PASS.
- `git diff --check` PASS.

### Estado y limites

Estado: `H3-BUILD-03B-DB_LOCAL_VALIDATED`.

No se ejecutaron migraciones remotas, writes Supabase, Auth remoto, deploy,
schedules, workflow dispatch, commit, push, PR ni merge. Las migraciones
`20260918`, `20260919` y `20260920` permanecen intactas. Las invitaciones
anteriores al nuevo contrato no recibieron backfill DML.

### Expand -> compatibilidad -> deploy -> contract

- `expand`: nueva migracion y RPCs, conservando columnas/firmas legacy.
- `compatibilidad`: runtime Edge 03A, Auth-owned token y usuarios legacy `ready`
  permanecen soportados.
- `deploy`: pendiente de aprobacion JIT y validacion Free/Certification/Pro.
- `contract`: pendiente de callback/frontend validado y retiro controlado de
  compatibilidad.
- Rollback: futura migracion aprobada; no editar historicos ni aplicar rollback
  remoto implícito.

## Alcance Inmediato

El alcance inmediato es versionar la remediacion productiva H2 y habilitar el
flujo protegido hacia `main` sin ejecutarlo. Pro, `main`, writers, schedules,
deploys manuales o DML adicional requieren aprobacion JIT separada. La secuencia
obligatoria para produccion es expandir y verificar Pro antes del deploy frontend.
`web/**`, `db/**`, `supabase/**`, `scripts/core/**`, `scripts/shared/**`,
`scripts/maintenance/**`, `config/**`, dependencias y Docker permanecen protegidos
salvo autorizacion separada. H2 fue mergeado por PR #458 a `desarrollo`, PR #459
agrego gate documental post-merge y PR #460 lo promovio a `certificacion`, todos
con CI verde. Forward-fix, remediacion Security Advisor, backfill editorial,
seed, fix de vista publica y compatibilidad legacy aplicados/verificados en
Supabase Free. La web real de Certificacion muestra cursos reales; la limpieza de
calidad quedo validada remotamente en preview Cloudflare `4cc2e34c`. Pro, writer,
schedule o nueva accion remota requiere aprobacion JIT separada.

## H3-BUILD-03B Frontend Auth (2026-09-22)

El checkpoint frontend quedó implementado y validado localmente en Docker como
`H3-BUILD-03B-FRONTEND_AUTH_LOCAL_VALIDATED_WITH_RESIDUALS`. La evidencia
canonica es `.context/evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_frontend_auth_local_2026-09-22.md`.

- Cliente browser oficial Supabase con PKCE, persistencia de sesión compatible y
  `detectSessionInUrl = false`.
- Callback `/admin/auth/callback/` con exchange único, limpieza de URL,
  aceptación RPC y destinos internos fijos.
- Pantallas `/admin/accept-invite/` y `/admin/setup-password/` consumiendo las
  tres RPCs de onboarding; password enviada solo a Auth, nunca al RPC.
- Login/MFA legacy preservado como compatibilidad; MFA queda fuera del gate de
  aceptación por decisión de alcance.
- Mock local extendido para grant PKCE one-shot, actualización de password y
  RPCs de onboarding.
- `tsc`, lint sin errores, build normal, build mock, contratos focalizados,
  credential scan y `git diff --check` PASS. Lint mantiene 9 warnings históricos
  fuera del delta.
- `npm audit --omit=dev --audit-level=high` conserva 16 hallazgos HIGH y 1
  CRITICAL de dependencias transitorias; no se aplicó `npm audit fix` fuera del
  alcance.

No se ejecutaron Auth remoto, writes Supabase, migraciones remotas, deploy,
workflow dispatch, commit, push, PR, merge ni promoción protegida. Mock UAT-02
validó localmente callback, aceptación y password setup; el siguiente gate es UAT
remota por ambiente.

## Orden Vinculante Nuevo Pedido

```text
Intake documental
-> H2 Modelo editorial y pipeline tolerante a incompletos
-> H3 Administracion editorial autenticada
-> H1 Automatizacion segura y reactivacion gradual
-> H4 Home publica y documentacion tecnica
-> H5 Resultados publicos, filtros y cards
```

## Siguiente Gate

El checkpoint local `H3-BUILD-03B-FRONTEND-AUTH` y Mock UAT-02 quedaron validados.
El siguiente gate es UAT remota por ambiente, validación 03A/03B, Certification y
`contract/cleanup`. Supabase remoto, deploy, workflow dispatch, commit, push, PR,
merge y contract/cleanup requieren aprobaciones separadas.

H2REQ1 esta cerrado: `h2-expand-compat` fue aplicado y verificado en Pro,
la evidencia canonica esta en `.context/operaciones/h2_main_production_expand_evidence.json`
y la promocion `certificacion -> main` fue completada por PR #486.

La UAT ampliada de H3REQ1 alcanzó dos corridas estructurales 47/47 y 141/141 PASS,
pero la auditoría de readiness posterior revocó el GO para PR y dejó el estado
`H3_PR_DEVELOPMENT_NO_GO` (histórico). El build normal y mock ya pasaban en Docker
y las rutas admin se exportaban, por lo que el waiver de static export quedó
superseded; persistían bloqueadores reproducibles en CI, invariantes DB, MFA
real, cobertura E2E, rollback y vinculación de evidencia al candidato. La
atestación sanitizada
`.context/evidencias_cliente/sprint_1/atestado_h3_ampliacion_prompt_humano_sanitizado.md`
autorizó la corrección local hasta GO verificable. El ciclo siguiente resolvió esos
bloqueadores y dejó el estado `H3_PR_DEVELOPMENT_READY_LOCAL`.

### Ciclo de corrección local (2026-09-02) — bloqueadores HIGH/CRITICAL resueltos

Correcciones aplicadas y revalidadas en Docker (sin push/PR/remoto):

1. `security-audit.yml`: eliminada la línea corrupta bajo `h2-main-production-expand-gate:`
   (YAML parse OK) y reescrita la allowlist de `protected-paths` con el contrato H3
   explícito (`20260828_h3_admin_*`, `20260829_h3_rbac_users`, `20260830_h3_expanded_contract`,
   `20260902_h3_pr_contract`, `20260903_h3_rbac_contract_fix`, seed, harnesses,
   archivos admin web, workflows). El job
   `db-gate` ahora también crea la DB `h3_gate` y ejecuta `h3_pg17_harness.sql`.
   Gate replicado localmente con el diff real de `protected-paths` vs baseline
   `9b486146…`: `GATE_OK` (57 archivos en scope, todos allowlisted, incluida la
   restauración del sufijo `\.sql` compartido de migraciones H2/H3).
2. Migración `20260902_h3_pr_contract.sql`: `admin_get_course_editorial` devuelve valores
   efectivos consistentes (`current_values` + `current_value` por field) y
   `admin_publish_course` aplica gate de publicabilidad (rechaza `pending`/missing con
   error `Course is not publishable: pending quality or missing fields`).
3. Seed `h3_admin_seed_local.sql` idempotente (`ON CONFLICT DO NOTHING`) y con categorías
   asignadas a los 30 cursos fixture; el recompute de calidad tras ediciones ya no
   degrada cursos completos (30/30 con `category_id`).
4. Harness `h3_pg17_harness.sql` (CI, destructivo): re-run de seed idempotente, lector
   efectivo, rechazo de publish en draft incompleto y publish exitoso con auditoría;
   desde el candidato actual también cubre la regresión A6/A13 del delta `20260903`.
   Verificado en PG17 (`h3_gate3`): `h3_pg17_harness_ok`.
5. Harness `h3_pg17_harness_local.sql` (local, rollback): guard de idempotencia de seed +
   gate de publish + lector efectivo. Verificado en `studiamatch_h3`:
   `h3_pg17_harness_local_ok` (baseline DB restaurado a la seed canónica).
6. MFA: `admin-auth.ts` normaliza `enrollTotp` (shape anidada real y top-level mock),
   resuelve `aal` (top-level → decode JWT → `aal1`) sin forzar `aal2`, y el login
   (`web/src/app/admin/login/page.tsx`) muestra el panel “Registra tu autenticador”
   (QR `data:image`, secreto agrupado, `otpauth URI`) cuando el factor no está verificado.
7. Harness local spec `tests/h3_local_uat.spec.mjs` retirado (duplicado del runner canónico).
8. `.gitignore` actualizado (evidencia stale, `.worktrees/`, logs y node_modules del mock).

Validaciones del ciclo (local, Docker): TypeScript `tsc --noEmit` 0 errores; `npm run lint`
0 errores; build normal y `build:mock` estáticos PASS (rutas admin presentes);
`scripts/security/h2_web_mock_smoke.sh` PASS; actionlint y shellcheck PASS; suite CI-local
142 tests PASS; `py_compile`, credential scan y `git diff --check` PASS; H2/H2-Pro/H3
PG17 PASS con `h3_pg17_harness_ok` y regresión A6/A13.

Estado resultante: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR a `desarrollo`). El PR
incluye el delta `20260903` y documentación JIT sincronizada, sin afirmar aplicación
remota posterior. JIT-A mantiene A6/A13 históricos FAIL hasta revalidación; JIT-B
mantiene E1/E3/E4/E8 PASS y E2/E5/E6/E7 pendientes. Commit + push + PR protegido a
`desarrollo` siguen la plantilla `.github/pull_request_template.md`; la aplicación
remota del delta, configuración Auth, dependencia build, certificación y deploy
requieren aprobaciones separadas.

### Remediación local de cierre H3REQ1 (2026-09-23)

Con autorización humana `continua` se ejecutó únicamente el ciclo local. Se corrigió
el runner `tests/h3_local_uat.mjs` para consumir la sesión persistida por el cliente
oficial PKCE (`*-auth-token`, `access_token`, `refresh_token`), se hizo configurable
el Chromium instalado en Docker y el mock reconstruye sus identidades RBAC estables
antes de cada corrida. No se modificaron ambientes Supabase ni se ejecutaron
deploy, workflow dispatch, commit, push, PR, merge o promoción protegida.

Evidencia nueva y reproducible:

- `.context/evidencia/h3-invitation-flow/evidencia_h3_invitation_flow_remediation_local_2026-09-23.md`.
- `.context/evidencia/h3req1_uat_matrix_local_2026-09-23.md`.
- `.context/evidencia/h3req1_remediation_report_2026-09-23.md`.
- `.context/evidencia/h3-expanded/h3-expanded-uat-matrix.json`: 47/47 casos y
  141/141 ejecuciones PASS, 141 screenshots y 0 retries.
- `tests/h3_invitation_uat.mjs`: 9/9 casos de invitación PASS, incluyendo user/admin,
  aceptación, password setup, expiración, revocación, resend/supersede, redirect y replay.
- Harness PG17 limpio: `h3_invitation_onboarding_harness_ok` y
  `h3_pg17_harness_ok`.

La matriz UAT local registra `PASS` únicamente para la evidencia local. El estado
contractual vivo permanece `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` porque
siguen pendientes Auth/PKCE y correo real, aplicación y validación remota 03A/03B,
UAT por ambiente, hostnames Development/Certification, Certification, Pro H3,
deploy y `contract/cleanup`. No se declara cierre definitivo. MFA/`aal2` permanece
fuera del gate H3REQ1 y como mejora evolutiva; su compatibilidad existente no fue
retirada.

### Ciclo 3 — afinación documental del plan y baseline local

El 2026-09-24 se afinó únicamente `.context/operaciones/h3req1_remediation_plan_2026-09-24.md`
y la ficha read-only del ciclo 2. No se modificó código, SQL, Edge, frontend ni
pruebas; tampoco se ejecutaron DDL, writes, Auth, correo, deploy, push, PR,
merge, cleanup, rollback o promoción. R1 queda clasificado como `PASS` por la
captura read-only, mientras H3-001 sigue `FAIL` por drift Pro y H3-002/H3-003/
H3-004 siguen `BLOCKED`. El siguiente paso autorizado es preparar el delta
exacto y solicitar los paquetes JIT separados; no aplicar migraciones ni iniciar
UAT con la evidencia actual.

La validación Docker/PG17 del ciclo 3 cerró `LOCAL-VAL-001` y `LOCAL-VAL-002`
como `PASS`: harness canónico limpio en `h3_cycle3_clean`, con resultados
`h3_pg17_harness_ok` y `h3_invitation_onboarding_harness_ok`. Los contratos H3
focalizados quedaron 8/8 `PASS`, la UAT mock de invitación 9/9 `PASS`, build
mock, TypeScript, credential scan, sintaxis y perímetro local `PASS`. `pytest`
continúa `BLOCKED` porque no está instalado en la imagen Docker y no se infiere
PASS por otra herramienta.

La revalidación remota read-only del ciclo 3 confirma: Free con 15 migraciones
H3 relacionadas y `admin-invite` v3 `ACTIVE`/`verify_jwt=true`; Pro con 0
migraciones H3, sin `admin_members`, `admin_membership_audit` ni
`admin_invitations`, y sin `admin-invite`. En aquel snapshot el hardening
registrado en Free no tenía archivo correspondiente en el checkout. El ciclo 4
lo recuperó y lo validó localmente; queda pendiente únicamente su
reconciliación after-apply remota. Estado contractual: H3-001 `FAIL`;
H3-002/H3-003/H3-004 `BLOCKED`; no se solicita Certification.

### Ciclo 4 — hardening local H3REQ1

Se corrigió el bloqueador local de SQL no reproducible: las migraciones de
hardening 20260924 fueron reincorporadas al checkout principal desde el
worktree de remediación y validadas en PG17 limpio. El nuevo harness acredita
protección de onboarding incompleto, RBAC de admin/user/inactivo, último admin,
auditoría append-only compatible y preservación legacy. Resultado local:
`h3_onboarding_rbac_hardening_harness_ok` y `h3_pg17_harness_ok`.

También quedaron `PASS` los 60 tests focalizados con pytest, TypeScript,
build normal, build mock, credential scan, sintaxis y UAT mock 9/9. Las
dependencias de pytest quedaron versionadas con hashes en
`requirements-pipeline.txt`. Los 9
warnings ESLint históricos permanecen sin errores.

Esto no cierra el gate remoto. H3-001 sigue `FAIL` porque Pro no tiene el
baseline H3; H3-002/H3-003/H3-004 siguen `BLOCKED` por falta de DDL, Auth/correo,
Edge/Pages, contract, cleanup y rollback autorizados. Estado: `NO-GO`.

El ciclo 5 corrigió los dos hallazgos locales HIGH/MEDIUM del auditor: la ruta
legacy `admin_create_member` ahora rechaza creación directa y el harness PG17
comprueba ACL/RLS de roles PostgREST. Los tests focalizados siguen 60/60
`PASS`; esto mantiene GO técnico local, pero no convierte evidencia local en
GO contractual remoto.

El ciclo 6 cerró la brecha de visibilidad operativa: se añadió el lector
aditivo `admin_list_members_onboarding` y la pantalla de miembros lo consume,
sin retirar el RPC legacy. TypeScript, build mock, lint sin errores, credential
scan, harness PG17 y tests focalizados permanecen `PASS`.

El ciclo 6 también alineó el mock server con ese RPC aditivo y limpió el lock
de Pygments para que `requirements-pipeline.txt` mantenga un único bloque con
hash reproducible. El gate remoto continúa `NO-GO` hasta las autorizaciones JIT
y la convergencia Free/Pro.

La reauditoría del ciclo 7 cerró los hallazgos locales restantes: mock reader
protegido por RPC, fixture PG17 coherente, legacy guard probado contra un user
`ready` real, lock pytest/Pygments reproducible y sin HIGH/MEDIUM local abierto.
H3REQ1 queda en `GO técnico local`, pero sigue `NO-GO contractual remoto` por
Pro sin baseline H3 y por falta de DDL/Auth/Edge/Pages/contract/rollback con
autorización JIT.
