# Estado Del Proyecto

Snapshot: `SNAPSHOT-2026-09-02-H3-PR-DEVELOPMENT-READY-LOCAL`.

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

`H3_PR_DEVELOPMENT_READY_LOCAL` significa: **GO local alcanzado para el PR
protegido a `desarrollo`**. El ciclo de corrección local del 2026-09-02 (detalle
en [Siguiente Gate](#siguiente-gate)) resolvió los bloqueadores HIGH/CRITICAL de
CI, DB, MFA real, UAT y evidencia que había detectado la auditoría de readiness
previa (`H3_PR_DEVELOPMENT_NO_GO`, histórico). La UAT canónica volvió a pasar
47/47 casos y 141/141 ejecuciones con cero reintentos. Quedan pendientes
únicamente los gates remotos posteriores y separados (JIT Supabase Free/Auth,
Cloudflare, revisión/merge del PR y promoción).

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
- Build normal y `build:mock` ejecutados en Docker el 2026-09-02: compilación
  exitosa y rutas `web/out/admin/{index,login,edit,users}/index.html` presentes.
  El waiver de static export queda superseded para este candidato.
- Suite CI-local seleccionada: 142 tests PASS; TypeScript PASS; lint sin errores
  (9 warnings históricos); `py_compile`, credential scan y `git diff --check`
  PASS. Harnesses H3 en PG17: `h3_pg17_harness_ok` y `h3_pg17_harness_local_ok`.
- La corrida completa indiscriminada `pytest -q` no es un gate válido en este
  checkout porque recolecta worktrees históricos montados bajo `local/worktrees/`
  y tests de integración que requieren entorno; produjo 540 errores de colección.
  El PR usa el conjunto versionado del job `python-check` y documenta esta
  exclusión.

### Qué resolvió el ciclo de corrección local (2026-09-02)

El ciclo descrito en [Siguiente Gate](#siguiente-gate) eliminó los bloqueadores
HIGH/CRITICAL que la auditoría de readiness había identificado en CI, contratos
DB, MFA real, UAT/evidencia y rollback:

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
GitHub y revisión del PR, JIT Supabase Free/Auth, Cloudflare Access/DNS,
promoción a `certificacion`, merge y deploy. No se ejecuta ninguna de esas
acciones sin su aprobación.

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
| `F11` | H3REQ1 ampliado: campos, MFA, invitaciones y hostname | `H3_PR_DEVELOPMENT_READY_LOCAL` | Bloqueadores HIGH/CRITICAL de CI, DB, MFA real, UAT/evidencia y rollback resueltos en el ciclo de corrección local del 2026-09-02; UAT canónica 47/47 y 141/141 PASS con 0 retries. PR protegido a `desarrollo` autorizado por instrucción humana separada; validación remota y promoción siguen como gates posteriores. |

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
- Tarea H3: `TASK-H3-001` en el backlog canónico versionado.
- Subfase tecnica activa: `F11`.
- Work package activo: `NONE_SUPERSEDED`.
- Work package completado: `NONE_APPLICABLE`.
- Gate vigente: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR; ciclo de corrección 2026-09-02).
- UAT canónica regenerada: `47/47` casos y `141/141` ejecuciones PASS con 141
  screenshots y 0 retries, evidencia en `.context/evidencia/h3-expanded/`.
- Build normal/mock revalidado en Docker: PASS; rutas admin exportadas presentes.
  El waiver de static export queda superseded para el candidato actual.
- Gates reejecutados: suite CI-local 142 PASS; TypeScript PASS; lint 0 errores y 9
  warnings históricos; py_compile PASS; credential scan PASS; `git diff --check`
  limpio; harnesses H3 PG17 `h3_pg17_harness_ok` y `h3_pg17_harness_local_ok`;
  gate `protected-paths` emulado `GATE_OK`. `pytest -q` global indiscriminado no es
  válido por recolectar worktrees históricos y tests de integración fuera del gate,
  y produjo 540 errores de colección.
- Auditorías especializadas del ciclo previo (`SECURITY_PR_READY=NO`,
  `QA_PR_READY=false`, `DB_PR_READY=NO`) quedaron resueltas por las correcciones
  listadas en [Siguiente Gate](#siguiente-gate); sin hallazgos HIGH/CRITICAL
  pendientes para el gate local.
- Commit + push + PR protegido a `desarrollo` quedaron **autorizados por
  instrucción humana separada** y se ejecutan con la plantilla de PR.
- Gates remotos posteriores y separados: `security-audit` en GitHub y revisión del
  PR, JIT Supabase Free/Auth, Cloudflare Access/DNS, promoción a `certificacion`,
  merge y deploy. No se ejecutan sin su aprobación.

### Matriz de avance H3REQ1 ampliado

Los porcentajes son estimaciones separadas: implementación no equivale a aceptación; validación exigida solo por evidencia ejecutada y reproducible. La UAT local acredita el cierre local; las validaciones remotas quedan pendientes de JIT.

| Criterio | Implementación | Validación verificable | Bloqueo principal |
|---|---:|---:|---|
| H3-CA4 local | 78.7% provisional | 61.8% provisional | `H3_PR_DEVELOPMENT_READY_LOCAL`; porcentajes previos conservados solo como estimación, no readiness. Bloqueadores QA/seguridad/DB del ciclo previo resueltos localmente. |
| H3-CA4.1 Auth/RBAC | 90% | 85% | UAT local cubre RBAC y negativos; Auth real pendiente de JIT. |
| H3-CA4.2 Ownership | 85% | 75% | 13 campos y `missing_fields` cubiertos por UAT; falta entorno real. |
| H3-CA4.3 Transporte independiente | 60% | 40% | Fixture E2E diferenciando cuatro campos validado local; falta entorno real. |
| H3-CA4.4 Cola | 85% | 70% | Paginación, cursor y filtros cubiertos por UAT; falta entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | Mutaciones admin y locking cubiertos por UAT; falta entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Auditoría append-only cubierta por UAT; falta entorno real. |
| H3-CA4.7 MFA/`aal2` | 80% | 55% | Mock `aal2` positivo y negativos `aal1` cubiertos por UAT; falta Auth real. |
| H3-CA4.8 Membresías/invitaciones | 75% | 45% | Gestión, último admin e invitación mock cubiertos por UAT; falta Edge Function real. |
| H3-CA4.9 Hostname/perímetro | 60% | 40% | 404 público validado sobre perímetro real; falta allowlist de despliegue y Access. |
| H3-CA4.10 Convergencia Pro/Free/local | 55% | 35% | PG17 y snapshot Pro; falta diff completo/remoto con JIT. |
| H3-CA4.11 UAT/artifacts | 100% estructural | 55% contractual | UAT canónica 47/47 y 141/141 PASS con 0 retries regenerada el 2026-09-02; evidencia autocontenida en `.context/evidencia/h3-expanded/`; falta UAT real en Free/Certification. |
| **Promedio simple** | **78.7% provisional** | **57.7% provisional** | **`H3_PR_DEVELOPMENT_READY_LOCAL`; GO local para PR a `desarrollo`. Validación remota (Free/Auth, Cloudflare, certificación) pendiente de JIT/promoción separada.** |

## Estado De Hitos Sprint 1

| Hito | Estado | Tarea |
|---|---|---|
| `HITO-001` | `REDEFINED_ACTIVE_AFTER_H2_H3` | `TASK-H1-001` |
| `HITO-002` | `H2_CERTIFICATION_STABLE_PRO_REMEDIATION_PLANNED` | `TASK-H2-001` |
| `HITO-003` | `H3_PR_DEVELOPMENT_READY_LOCAL` | `TASK-H3-001` |
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
   `20260902_h3_pr_contract`, seed, harnesses, archivos admin web, workflows). El job
   `db-gate` ahora también crea la DB `h3_gate` y ejecuta `h3_pg17_harness.sql`.
   Gate replicado localmente con el set de archivos del PR: `GATE_OK` (28 archivos en scope).
2. Migración `20260902_h3_pr_contract.sql`: `admin_get_course_editorial` devuelve valores
   efectivos consistentes (`current_values` + `current_value` por field) y
   `admin_publish_course` aplica gate de publicabilidad (rechaza `pending`/missing con
   error `Course is not publishable: pending quality or missing fields`).
3. Seed `h3_admin_seed_local.sql` idempotente (`ON CONFLICT DO NOTHING`) y con categorías
   asignadas a los 30 cursos fixture; el recompute de calidad tras ediciones ya no
   degrada cursos completos (30/30 con `category_id`).
4. Harness `h3_pg17_harness.sql` (CI, destructivo): re-run de seed idempotente, lector
   efectivo, rechazo de publish en draft incompleto y publish exitoso con auditoría.
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
0 errores; `build:mock` estático OK (exporta `/admin`, `/admin/login`, `/admin/edit`,
`/admin/users`, cursos mock y rutas públicas); perímetro 3002 con `Host` mapping correcto
(`/admin/login` 200 en admin origin, `/admin/` 404 en `studiamatch.com`); UAT canónica
`h3_local_uat.mjs` **PASS 47/47 casos y 141/141 ejecuciones, 141 screenshots, 0 retries**;
evidencia regenerada en `.context/evidencia/h3-expanded/`.

Estado resultante: `H3_PR_DEVELOPMENT_READY_LOCAL` (GO para PR). Commit + push + PR
protegido a `desarrollo` fueron autorizados por instrucción humana separada y se
ejecutan con la plantilla `.github/pull_request_template.md` llena con validaciones
reales del ciclo. Luego siguen, cada una con aprobación separada: JIT Supabase
Free/Auth, Cloudflare, certificación y deploy como flujo posterior.
