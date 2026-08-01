# PLAN-F9.7-CIERRE-001 - Cierre Definitivo De F9.7

> Disposicion propuesta: los artifacts locales/terminales de este plan se
> preservan como WIP CA2 no promocionable si el cliente aprueba la adenda
> CA1-only. Hasta entonces, el plan conserva su historia y F9.7 sigue
> `IN_PROGRESS`; esta nota no autoriza incluirlos en el PR documental ni en el
> candidate productivo CA1-only.

| Campo | Valor |
|---|---|
| ID | `PLAN-F9.7-CIERRE-001` |
| Estado documental | `VIGENTE` |
| Subfase | `F9.7` |
| Tarea | [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md) |
| Decision | Cerrar el corte por seis work packages finitos antes del PR local y conservar el follow-up documental post-merge |
| Baseline Git | `8ab1cdf9173b8093781e75ba32c2fea9ae931b14` |
| Plan superior | [PLAN-H1-CORTE-SFE-001](./plan_corte_seguridad_funcionalidad_estabilidad_hito1.md) |

## Proposito

Este plan convierte el cierre local de F9.7 en seis work packages verificables. Su objetivo es evitar ciclos abiertos de remediacion y auditoria, producir checkpoints Git tangibles y llegar a un unico candidate local apto para commit, push y PR hacia `desarrollo`.

Los work packages no son subfases, subtareas, criterios nuevos ni autorizaciones independientes. `F9.7` sigue siendo la unica subfase activa y la frase de autorizacion permanece `Ejecuta las tareas pendientes de la Fase F9.7`, conforme a [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md).

El estado vivo de los work packages pertenece exclusivamente a [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md). Este documento fija alcance, dependencias, criterios de salida y evidencia.

## Decisiones Humanas Vinculantes

1. Leads y email permanecen fuera del perfil habilitado de Hito 1.
2. `anon`, `authenticated`, `authenticator` y `service_role` deben quedar sin acceso a `leads` y `email_log`.
3. Las filas legacy se preservan; solo el owner `postgres` puede inspeccionarlas bajo una operacion separada y autorizada.
4. No se crean IDs `F9.7.1`; se usan `WP-F9.7-01` a `WP-F9.7-06` dentro de F9.7.
5. La publishable key historica retirada del arbol actual fue rotada. La unica evidencia documental permitida es `ROTATED_HUMAN_ATTESTED`; no se registra valor, identificador, URL ni referencia sensible.
6. Los auditores validan un contrato congelado. No pueden ampliar el threat model ni convertir hardening fuera de alcance en bloqueo del PR local.
7. Free y Pro permanecen `UNCHANGED_NOT_ATTESTED`; este plan no autoriza acceso ni aplicacion remota.
8. Los checkpoints intermedios son commits locales. No hay push hasta completar `WP-F9.7-06`.

## Resultado Local Esperado

El cierre de este plan produce `GO_FOR_LOCAL_PR`, no `GO_FOR_FREE` ni `GO_F9.7_COMPLETE`. El resultado local esperado es:

- Frontend sin captura publica de PII ni transporte de leads/email.
- Edge Function historica como tombstone `410 Gone` solo en Git.
- Security hold historico local, separado, posterior a v3 y bloqueado para Free/Pro; no promocionable para la ruta sucesora.
- Cero acceso de roles de aplicacion a `leads` y `email_log`.
- Golden Pipeline y harvester byte-identicos al baseline protegido.
- Candidate Git inmutable con matriz Docker y auditorias acotadas en GO.
- PR hacia `desarrollo` listo para review humano, sin merge automatico.

## Resultados GO Diferenciados

| Resultado | Significado | Autoriza |
|---|---|---|
| `GO_WP` | El work package cumple su contrato y evidencia enfocada | Checkpoint local del WP |
| `GO_FOR_LOCAL_PR` | Todos los WP y auditorias finales validan el mismo tree | Commit final, push de `feat/*` y PR a `desarrollo` |
| `GO_FOR_FREE` | Binding, snapshot, restore, writers y package Free tienen aprobacion separada | Solo la operacion Free expresamente autorizada |
| `GO_F9.7_COMPLETE` | PR-O y contencion/certificacion schema Free terminaron con evidencia | Transicion hacia F9.8 |

`GO_FOR_LOCAL_PR` nunca implica `GO_FOR_FREE`. `Free=UNCHANGED_NOT_ATTESTED` y `Pro=UNCHANGED_NOT_ATTESTED` son estados esperados durante el corte local y no bloquean su PR.

## Invariantes Congelados

Un hallazgo solo puede bloquear el cierre local si demuestra de forma reproducible el incumplimiento de uno de estos invariantes:

1. No existe control publico que capture nombre, email, telefono, WhatsApp u otra PII para crear leads.
2. No existe transporte frontend hacia `leads`, `email_log`, `send-lead-emails` ni otra ruta equivalente.
3. La Edge Function local responde siempre `410 Gone`, no lee payload/secrets y no realiza egress.
4. `anon`, `authenticated`, `authenticator` y `service_role` no tienen acceso directo ni indirecto a `leads` o `email_log`.
5. Las filas legacy permanecen byte/valor equivalentes durante apply, replay y rollback; solo `postgres` conserva autoridad administrativa.
6. Views, materialized views, rutinas, overloads, publications, rules, triggers, ACL y memberships dentro del threat model no abren rutas ordinarias de aplicacion.
7. El manifest v3 y sus seis migrations permanecen byte-identicos; el hold actual queda historico/no promocionable y el sucesor no puede depender de `public.exec_sql(text)`.
8. Boundary 6, boundary 7 y cada fallo inyectado mantienen ledger, schema, ACL, RLS, funciones y datos en el estado esperado.
9. Catalogo, busqueda, filtros, detalle, comparacion, soporte estatico, privacidad y terminos conservan comportamiento publico y accesible.
10. FG1, FG2, FG3, harvester, `scripts/core`, `scripts/shared`, requisitos y auditorias del pipeline no cambian respecto del baseline protegido.
11. Actionlint, EOL por diff, whitespace por rango, hooks, secret scan, Context Graph y CI validan el candidate exacto.
12. Manifest y runbook mantienen `application_authorized=false`, Free/Pro bloqueados y cero capacidad remota.

## Threat Model Congelado

### Dentro Del Alcance

- Roles de aplicacion `anon`, `authenticated`, `authenticator` y `service_role`.
- `service_role` como rol de aplicacion no tiene acceso data-plane a `leads` ni `email_log`.
- `public.exec_sql(text)` exacto queda aceptado temporalmente como residual historico del PR local, enlazado a [BK-F9.5-07](../backlog_tareas/req_est_001_sprint_1/backlog_exec_sql_control_plane.md), no como ruta data-plane ni como estado final del PR-O sucesor.
- Privilegios de tabla y columna, incluidos caminos por membership, `INHERIT`, `SET ROLE` y `ADMIN OPTION`.
- Views y materialized views dependientes en schemas utilizables por roles de aplicacion.
- Rutinas ejecutables y overloads que dependan o hagan referencia comprobable a `leads`/`email_log`.
- Publications directas, globales y por schema.
- Policies, RLS/FORCE RLS, triggers, rules, constraints y ACL.
- Frontend, static export, Edge tombstone y egress observable durante pruebas.

### Fuera Del Alcance Aceptado

- Owner `postgres` y superuser como autoridad administrativa deliberada.
- `public.exec_sql(text)` exacto bajo owner `postgres`, `SECURITY DEFINER`, search_path atestado y EXECUTE solo para `service_role`, como residual control-plane aceptado solo para el PR local historico; el sucesor debe eliminarlo del estado final.
- SQL dinamico arbitrariamente ofuscado que no pueda probarse por catalogo o inspeccion estatica razonable.
- Free/Pro y Edge desplegada hasta que exista binding y autorizacion propios.
- Reactivacion futura de leads/email, que exige nuevo ciclo `INTAKE -> EST -> REQ -> TASK`.
- Hardening general no relacionado con los doce invariantes.

## Clasificacion De Hallazgos

| Clasificacion | Regla | Efecto |
|---|---|---|
| `BLOCKING_IN_SCOPE` | Existe reproduccion y mapeo a un invariante congelado | Impide GO y vuelve al WP propietario |
| `RESIDUAL_ACCEPTED` | Riesgo contenido en los limites humanos aceptados | Se documenta; no impide GO local |
| `BACKLOG_OUT_OF_SCOPE` | Mejora real sin violacion del corte | Se deriva a backlog; no amplifica F9.7 |
| `DUPLICATE` | Ya existe un hallazgo equivalente | Se enlaza al original |
| `FALSE_POSITIVE` | No existe ruta, impacto o reproduccion | Se cierra con evidencia |

Todo `BLOCKING_IN_SCOPE` debe incluir invariante afectado, archivo/linea, reproduccion determinista, resultado esperado y resultado observado. Una afirmacion teorica sin ese mapeo no cambia el verdict del WP.

Para `WP-F9.7-02`, el `exec_sql(text)` exacto descrito en [BK-F9.5-07](../backlog_tareas/req_est_001_sprint_1/backlog_exec_sql_control_plane.md) se clasifica como `RESIDUAL_ACCEPTED` para el PR local y `BACKLOG_OUT_OF_SCOPE` para su sustitucion futura. Cualquier otro executor SQL dinamico, overload inesperado o ACL distinta es `BLOCKING_IN_SCOPE`.

## Secuencia Y Dependencias

```text
WP-F9.7-01 Contrato y gobierno
        |
        +--> WP-F9.7-02 Security hold DB
        |
        +--> WP-F9.7-03 Frontend no-leads
        |
        `--> WP-F9.7-04 CI, hooks y release gates
                         |
                         v
                  WP-F9.7-05 Candidate inmutable
                         |
                         v
                  WP-F9.7-06 Auditoria final y PR
```

`WP-F9.7-02`, `WP-F9.7-03` y `WP-F9.7-04` dependen del contrato congelado por `WP-F9.7-01`. Pueden implementarse separadamente, pero `WP-F9.7-05` requiere los tres en GO.

## WP-F9.7-01 - Contrato, Inventario Y Gobierno

### Objetivo

Congelar este contrato, reconciliar autoridad documental, clasificar el arbol dirty y producir el primer checkpoint local sin modificar codigo de producto, SQL o workflows.

### Alcance

- [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md).
- [PLAN-H1-CORTE-SFE-001](./plan_corte_seguridad_funcionalidad_estabilidad_hito1.md).
- Este `PLAN-F9.7-CIERRE-001`.
- [Estado del proyecto](../estado_del_proyecto.md).
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md), indices y changelog.
- `AGENTS.md` para preservar el protocolo Plan/Build corregido.

### Actividades

1. Confirmar rama, HEAD, baseline y subfase activa.
2. Confirmar que los seis SQL v3 y protected paths tienen diff cero.
3. Inventariar todos los `M/A/D/??` actuales, separar las rutas documentales del checkpoint `WP-F9.7-01` y asignar el resto tecnico exactamente a WP-02, WP-03 o WP-04.
4. Reconciliar enlaces y decisiones humanas sin declarar tests o remotos no ejecutados.
5. Registrar `historical_publishable_key=ROTATED_HUMAN_ATTESTED` sin valor sensible.
6. Configurar localmente `core.hooksPath=.githooks` para el checkpoint documental.
7. Stagear solo documentacion intencional y `AGENTS.md`.
8. Validar Context Graph, staged diff, EOL del stage y scanner de credenciales redacted.

### Inventario Dirty Capturado

Captura local en `feat/f9-7-security-cutoff` sobre `8ab1cdf9173b8093781e75ba32c2fea9ae931b14`, antes de staging. Las rutas documentales pertenecen al checkpoint `WP-F9.7-01`; las rutas tecnicas quedan asignadas al WP propietario y no deben stagearse en este checkpoint.

| Estado | Ruta | Owner |
|---|---|---|
| `M` | `.context/00_INDICE.md` | `WP-F9.7-01` |
| `M` | `.context/arquitectura_pipeline.md` | `WP-F9.7-01` |
| `M` | `.context/backlog_tareas/_README.md` | `WP-F9.7-01` |
| `M` | `.context/backlog_tareas/req_est_001_sprint_1/_index.md` | `WP-F9.7-01` |
| `M` | `.context/backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md` | `WP-F9.7-01` |
| `M` | `.context/backlog_tareas/req_est_001_sprint_1/seguimiento_detallado_hito_1.md` | `WP-F9.7-01` |
| `M` | `.context/backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md` | `WP-F9.7-01` |
| `M` | `.context/decisiones/ADR-0004_simplificacion_contractual_hito1.md` | `WP-F9.7-01` |
| `M` | `.context/decisiones/_index.md` | `WP-F9.7-01` |
| `M` | `.context/estado_del_proyecto.md` | `WP-F9.7-01` |
| `M` | `.context/estructura_frontend.md` | `WP-F9.7-01` |
| `M` | `.context/hitos/hito_001.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/atestacion_origen_acl_f9_7.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/certificacion_hito1_f9.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/flujo_release_minimo.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/matriz_adopcion_db.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/pg_net_queue_drain_f9_7.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/plan_simplificado_hito1.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/remediacion_gate_b_f9_7.md` | `WP-F9.7-01` |
| `M` | `.context/operaciones/remediacion_trigger_f9_7.md` | `WP-F9.7-01` |
| `M` | `.context/sistema_db_supabase.md` | `WP-F9.7-01` |
| `M` | `AGENTS.md` | `WP-F9.7-01` |
| `??` | `.context/backlog_tareas/req_est_001_sprint_1/backlog_seguridad_leads_email.md` | `WP-F9.7-01` |
| `??` | `.context/changelog/2026-07-29.md` | `WP-F9.7-01` |
| `??` | `.context/decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md` | `WP-F9.7-01` |
| `??` | `.context/operaciones/cierre_definitivo_f9_7.md` | `WP-F9.7-01` |
| `??` | `.context/operaciones/plan_corte_seguridad_funcionalidad_estabilidad_hito1.md` | `WP-F9.7-01` |
| `M` | `scripts/maintenance/db_migrate.py` | `WP-F9.7-02` |
| `M` | `tests/test_fase09_7_schema_rls.py` | `WP-F9.7-02` |
| `??` | `db/manifests/fase09_7_leads_email_security_hold.json` | `WP-F9.7-02` |
| `??` | `db/migrations/20260729_fase09_7_leads_email_security_hold.sql` | `WP-F9.7-02` |
| `??` | `db/runbooks/fase09_7_leads_email_security_hold.json` | `WP-F9.7-02` |
| `??` | `scripts/maintenance/fase09_7_leads_email_security_hold_candidate.py` | `WP-F9.7-02` |
| `??` | `tests/sql/fase09_7_leads_email_security_hold_test.sql` | `WP-F9.7-02` |
| `??` | `tests/sql/run_fase09_7_leads_email_security_hold_postgres.sh` | `WP-F9.7-02` |
| `??` | `tests/test_fase09_7_leads_email_security_hold.py` | `WP-F9.7-02` |
| `M` | `supabase/functions/send-lead-emails/index.ts` | `WP-F9.7-03` |
| `D` | `tests/mobile_usability.spec.ts` | `WP-F9.7-03` |
| `D` | `tests/test_frontend_lead_capture_playwright.py` | `WP-F9.7-03` |
| `M` | `web/src/app/HomeContent.tsx` | `WP-F9.7-03` |
| `M` | `web/src/app/compare/CompareContent.tsx` | `WP-F9.7-03` |
| `M` | `web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx` | `WP-F9.7-03` |
| `M` | `web/src/app/courses/[institution]/[slug]/page.tsx` | `WP-F9.7-03` |
| `M` | `web/src/app/courses/page.tsx` | `WP-F9.7-03` |
| `M` | `web/src/app/page.tsx` | `WP-F9.7-03` |
| `D` | `web/src/lib/leadCapture.ts` | `WP-F9.7-03` |
| `D` | `web/src/lib/leadCaptureCore.ts` | `WP-F9.7-03` |
| `D` | `web/tests/assertLeadCaptureExport.mjs` | `WP-F9.7-03` |
| `D` | `web/tests/leadCapture.test.ts` | `WP-F9.7-03` |
| `??` | `tests/test_frontend_public_surfaces_playwright.py` | `WP-F9.7-03` |
| `??` | `web/src/lib/compareStorage.ts` | `WP-F9.7-03` |
| `??` | `web/tests/assertPublicExport.mjs` | `WP-F9.7-03` |
| `??` | `web/tests/buildWithLocalSupabaseStub.mjs` | `WP-F9.7-03` |
| `M` | `.env.example` | `WP-F9.7-04` |
| `M` | `.gitattributes` | `WP-F9.7-04` |
| `M` | `.github/workflows/f9-7-contract.yml` | `WP-F9.7-04` |
| `M` | `.github/workflows/security-audit.yml` | `WP-F9.7-04` |
| `M` | `tests/test_supabase_credentials_contract.py` | `WP-F9.7-04` |
| `??` | `tests/test_fase09_7_pipeline_no_regression.py` | `WP-F9.7-04` |

### Evidencia GO

- Context Graph PASS dentro de Docker.
- `git diff --cached --check` PASS.
- Cero archivos de codigo/SQL/workflows en el stage.
- Cero credenciales o PII en el stage.
- Inventario restante asignado sin rutas huerfanas.
- Commit local `docs(f9.7): freeze definitive closure contract`.

### Evidencia De Cierre WP-01

- Commit: `88c7139`.
- Tree: `8f5ad9c269bb5665a5bdc805736dce25ef28e282`.
- Parent/baseline: `8ab1cdf9173b8093781e75ba32c2fea9ae931b14`.
- Context Graph: `PASS (51 files, 498 links)`.
- Stage: exclusivamente documental.
- Secret scan: `PASS` redacted.
- Push/remoto: cero.
- Inventario tecnico restante: `WP-F9.7-02=9`, `WP-F9.7-03=17`, `WP-F9.7-04=6`.

### Stop Conditions

- Contradiccion entre ADR, plan, tarea o estado.
- Cambio no explicado en v3 o protected paths.
- Documento que afirme aplicacion, test, key o remoto no demostrado.
- Archivo no documental en el stage.

## WP-F9.7-02 - Security Hold DB Historico

### Objetivo

Cerrar el package historico de hold con acceso cero para roles de aplicacion, identidad/verificacion segura y matriz PostgreSQL 17 adversarial finita. Este resultado no es terminal para la ruta sucesora.

### Alcance Tecnico

- Migration historica del security hold actual.
- Manifest, runbook y candidate generator historicos no promocionables para la ruta sucesora.
- Integracion manifest-only en `db_migrate.py`.
- Runner y tests Python/PostgreSQL del hold.
- Fixtures historicos estrictamente necesarios para roles y `exec_sql`; no heredables por el PR-O sucesor.

### Actividades

1. Revocar todo acceso de `service_role` a `leads` y `email_log`; eliminar el positivo SELECT del contrato.
2. Preservar filas legacy y verificar su contenido como `postgres`.
3. Atestar identidad completa de verifiers antes de invocarlos.
4. Exigir `authenticator` con atributos y memberships exactos, sin caminos transitivos privilegiados.
5. Detectar grants de tabla/columna y DML por views dependientes.
6. Detectar view chains, materialized views, routines, wrappers y overloads dentro del threat model.
7. Detectar publications directas, `FOR ALL TABLES` y `FOR TABLES IN SCHEMA`.
8. Validar cada stem/hash individualmente bajo lock en boundaries 6 y 7.
9. Evidenciar historicamente el payload del hold actual; el PR-O sucesor reemplaza esta ruta por executor privado no expuesto por Data API.
10. Ampliar fingerprint con owner, RLS/FORCE RLS, schema ACL, views, rutinas, memberships, publications y filas.
11. Inyectar fallos despues de cada etapa y despues del intento de ledger; exigir rollback exacto.
12. Probar una rutina exclusivamente administrativa/service-only no expuesta para evitar falsos positivos fuera de alcance.

### Matriz Minima PostgreSQL 17

- Boundary 6 exacto aplica una vez.
- Boundary 7 exacto solo revalida y no cambia fingerprint.
- Hold sin v3 falla.
- Stem, hash, verifier, ACL o dependency drift falla.
- `anon`, `authenticated`, `authenticator` y `service_role` reciben denegacion directa.
- Membership `INHERIT`, `SET ROLE` o `ADMIN OPTION` peligrosa falla.
- Membership `INHERIT OPTION`, `SET OPTION` y `ADMIN OPTION` peligrosa falla con fixtures dinamicos separados, incluyendo camino transitivo.
- View directa, column grant, DML view, view chain y materialized view fallan.
- Routine wrapper, helper transitivo y overload peligroso fallan; rutina fuera de ruta publica no genera falso positivo.
- Boundary 7 rechaza drift de return type del verifier terminal antes de invocarlo; sentinel no transaccional confirma no ejecucion.
- Fingerprint de rollback/replay cubre catalogo, ACLs, dependencias, rutinas relevantes, publications, policies, constraints, ledger y digest legacy sin filas PII.
- Trigger/rule relay con grants por tabla o columna falla.
- Rule relay mediante helper privado peligroso falla.
- Rutinas, triggers y rules con `SET search_path` y referencias no calificadas a `leads`/`email_log` o helpers peligrosos fallan.
- Publication directa, global y por schema falla.
- Trigger/rule/policy inesperada falla.
- Fault injection despues de revokes, policies, constraints, verifier, postcondition, terminal verification, before-ledger y after-ledger restaura fingerprint exacto.
- Digest legacy canonico de `leads` y `email_log` permanece identico en apply, replay y cada rollback.

### Evidencia GO

- Runner v3 PostgreSQL 17 PASS.
- Runner hold apply/replay/rollback PostgreSQL 17 PASS con FF04-FF08.
- Contratos Python DB PASS.
- Hashes y manifest recalculados desde bytes finales.
- `GO_SECURITY`: FF04 return type antes de invocacion y FF05 fingerprint completo PASS.
- `GO_FUNCTIONALITY`: FF06 fault injection completa, FF07 membership options dinamicos y FF08 digest legacy en apply/replay/rollback PASS.
- `GO_EFFICIENCY`: sin dependencia nueva, sin runtime normal, checks limitados a apply/replay/tests, CTE recursivos con proteccion de ciclos y sin ampliar rutas WP-02.
- Auditor `supabase-architect`: `GO_WP`.
- Auditor `security-auditor`: `GO_WP`.
- Commit local forward-fix objetivo: `fix(db): complete F9.7 hold adversarial closure`.

### Evidencia De Cierre WP-02

- PostgreSQL 17 v3: PASS local en Docker.
- PostgreSQL 17 hold apply/replay/rollback: PASS local en Docker, incluyendo return type domain adversarial, fingerprint completo, fault injection after-ledger, membership option fixtures y digest legacy.
- Python compile: PASS para `db_migrate.py` y candidate del hold.
- Pytest focused: PASS para `tests/test_fase09_7_leads_email_security_hold.py`.
- Validate-only manifest Free/Pro: PASS sin acceso remoto.
- Backlog nuevo: ninguno.
- Auditor `supabase-architect`: `GO_WP` sin findings despues de remediacion.
- Auditor `security-auditor`: `GO_WP` sin findings despues de remediacion.
- `MANIFEST_SHA256`: `3248376c2d92e953907590d158702a07f0b5523f7559ae4a0f85809b4aff4ebb`.
- Hold SQL SHA256: `29082d96cbfd746753324aef0330a7af6f34b0e8bcfa2db0841ac0a8af90134e`.
- Terminal verifier SHA256: `ceb80ae8865cf522b0cf2354c856f13c8c32156e38b492fdc55a223f44b51ab2`; octets `47721`.
- `public.exec_sql(text)` queda como residual aceptado exacto del hold historico; manifest normal/dry-run queda fail-closed y solo `--validate-only` resuelve paths. Esta aceptacion no se hereda al PR-O sucesor.

### Stop Conditions

- Necesidad de leer Free/Pro para hacer pasar el contrato local.
- Mutacion de cualquiera de los seis SQL v3.
- Uso de `CASCADE`, ledger idempotente o aplicacion legacy.
- Acceso residual de cualquier rol de aplicacion.

## WP-F9.7-03 - Frontend Publico No-Leads

### Objetivo

Cerrar el perfil web sin PII/leads y preservar todas las superficies publicas con accesibilidad, reflow y egress hermeticos.

### Alcance Tecnico

- Home, catalogo, detalle y comparador.
- Storage canonico de comparacion.
- Static generation y stub Supabase local.
- Edge tombstone local.
- Assertions de export y Playwright publico.
- Eliminacion de modulos/tests legacy de lead capture.

### Actividades

1. Mantener eliminados flag, modulos, formularios, PII controls y mutaciones leads/email.
2. Canonicalizar UUID a lowercase, deduplicar y limitar comparacion a tres IDs.
3. Validar query hostil con IDs invalidos, duplicados y mas de tres valores.
4. Rechazar mutaciones same-origin antes de permitir recursos estaticos.
5. Limitar el stub a origen, metodos, headers, paths y queries esperados.
6. Corregir labels persistentes, disclosure de filtros, disclosure movil y restauracion de foco.
7. Mantener todos los `tabpanel` referenciados y navegacion de teclado completa.
8. Probar reflow equivalente a 200% en Home, catalogo, detalle y comparador, incluidos filtros abiertos y compare bar.
9. Verificar rutas de privacidad y terminos.
10. Mantener build con entorno minimo, hostile lead flag y egress loopback-only.

### Matriz Minima Frontend

- Lint sin errores nuevos.
- Typecheck cero errores.
- Static build con stub local PASS.
- Export sin tokens, modulos, PII ni endpoints prohibidos.
- Playwright Home/catalogo/detalle/comparador/privacidad/terminos PASS.
- Keyboard y foco de disclosures/tabs PASS.
- Reflow equivalente a 200% sin overflow ni clipping PASS.
- Storage/query malformed, duplicate y oversized PASS.
- Cero request inesperado, mutacion, email egress, warning o console error.
- Edge tombstone `410 Gone` sin body read, env read o fetch.

### Evidencia GO

- Lint, typecheck, build, export y Playwright PASS en Docker.
- Auditor `frontend-architect`: `GO_WP`.
- Auditor `qa-test-engineer`: `GO_WP` para el perimetro frontend.
- Auditor `security-auditor`: `GO_WP` para el perimetro frontend/no-leads.
- Commit local `fix(web): finalize no-leads public surface`.

### Evidencia De Cierre WP-03

- Docker `npm run lint`: PASS con 9 warnings preexistentes en `HomeContent.tsx`, sin errores.
- Docker `npx tsc --noEmit`: PASS.
- Docker `node tests/buildWithLocalSupabaseStub.mjs`: PASS con stub loopback fijo `SUPABASE_TEST_ORIGIN`, apikey sintetica, GET-only, sin `Authorization` y guard de red loopback-only.
- Docker `node tests/assertPublicExport.mjs`: PASS; export publico sin modulos lead capture, PII controls, endpoints `leads`/`email_log`/`send-lead-emails`, flags de reactivacion ni tokens.
- Docker `pytest -q tests/test_frontend_public_surfaces_playwright.py`: PASS (`1 passed`); cubre Home, catalogo, detalle, comparador, privacidad, terminos, filtros abiertos, tabs, compare bar, storage/query hostile y canaries de egress.
- Comparador cubierto explicitamente a `188x334`; Home, detalle, privacidad y terminos cubiertos a `188x334`; viewport movil base `375x667` cubierto.
- Edge Function historica `send-lead-emails` queda tombstone Git-only `410 Gone`, `text/plain`, `no-store`, sin lectura de request/env ni `fetch`.
- Edge disablement separada autorizada en Free: `send-lead-emails` version `15`, `verify_jwt=false`, `ezbr_sha256=e004eab92d3ebb60aa5a1ce6d9a6f4072fb6cf47f8b58638af4675e5f5170e03`, target `FREE_BOUND`, owner `external_required_not_in_git`, timestamp `2026-07-31T21:02:35.6790000Z`; estado remoto observado `REMOTE_TOMBSTONE_410`, sin body read, sin env read, sin `fetch`, sin egress, sin DDL/DML y sin cambios en Pro.
- `compareStorage` canonicaliza UUID trim/lowercase, deduplica, limita a tres y falla cerrado ante storage malformed.
- `Header`/`Footer` y enlaces publicos deshabilitan prefetch de `next/link` para evitar HEAD abortados en static export; menu movil cierra overlays y links.
- Canaries esperados se cumplen sin generar request failures ni console errors; egress real no-canary sigue abortando fail-closed.
- Auditorias finales acotadas: `frontend-architect=GO_WP`, `qa-test-engineer=GO_WP`, `security-auditor=GO_WP`.
- Residuales aceptados: 9 warnings lint preexistentes en `HomeContent.tsx`; cobertura Chromium-only; tres tarjetas de comparador a `188x334` queda como gap visual no bloqueante; Header movil no tiene prueba dedicada aunque la remediacion fue revisada.

### Stop Conditions

- Reintroduccion de PII, lead endpoint, transport helper o flag de reactivacion.
- Dependencia de un Supabase remoto para build/test.
- Regresion de catalogo, detalle, comparacion, privacidad o terminos.

## WP-F9.7-04 - CI, Hooks Y Release Gates

### Objetivo

Hacer que el candidate exacto, no un checkout vacio o HEAD anterior, sea el objeto mecanicamente protegido antes de commit, push y PR.

### Alcance Tecnico

- `.gitattributes`.
- `security-audit.yml` y `f9-7-contract.yml`.
- Hooks versionados pre-commit/pre-push.
- Contratos de credenciales, pipeline preservation y workflow identity.
- Actionlint fijado y verificado.

### Actividades

1. Reconciliar assertions obsoletas con el build helper hermetico.
2. Corregir asset, version y SHA256 de actionlint desde fuente oficial.
3. Ejecutar whitespace con rango explicito `BASELINE..CANDIDATE`.
4. Aplicar EOL solo a blobs textuales cambiados, NUL-safe y deletion-safe.
5. Comparar protected paths contra el tree/index candidato, no contra `HEAD` anterior.
6. Congelar tambien manifest v3, `requirements-db-migrate.txt` y scripts runtime de auditoria FG2.
7. Hacer cleanup de firewalls fail-closed, con ownership y prueba de ausencia final.
8. Hacer pre-commit NUL-safe, index-aware y sensible a A/C/M/R.
9. Hacer pre-push escanear cada commit saliente, incluidos commits intermedios.
10. Mantener credential output redacted y fail-closed ante errores.
11. Agregar gates nuevos al agregador requerido `security-audit` sin `continue-on-error`.

### Matriz Minima Release

- Actionlint PASS sobre todos los workflows.
- EOL del diff candidato PASS sin renormalizacion global.
- `git diff --check BASELINE CANDIDATE` PASS.
- V3 manifest + seis SQL sin drift.
- Protected closure completa sin drift.
- Hooks activos, ejecutables y probados con stage no vacio.
- Scanner detecta fixture sintetico sin imprimir el valor.
- Pre-push detecta secreto agregado y retirado en un commit intermedio.
- Cleanup egress deja cero chain/jump propio.
- Aggregator bloquea cualquier dependencia fallida.

### Evidencia GO

- Auditor `devops-release-manager`: `GO_WP`.
- Auditor `security-auditor`: `GO_WP` para supply chain/credentials.
- Auditor `pipeline-engineer`: `GO_WP` para preservacion.
- Commit local `ci(f9.7): bind cutoff release gates`.

### Evidencia Local WP-F9.7-04

- Estado: `GO_WP_LOCAL`.
- Tree tecnico validado antes de cierre documental: `eac02134877441a0e7ff6d5646b2a3a23579d98d`.
- Candidate tree posterior a la excepcion EOL mecanica: `a9d8f93750d295b394584e6435ae98117494dfcc`; el tree final del commit se captura despues de esta evidencia documental.
- Actionlint oficial: version `1.7.7`, asset `actionlint_1.7.7_linux_amd64.tar.gz`, SHA256 `023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757`; archive y binario usados solo bajo `/tmp`/`RUNNER_TEMP`.
- R01 actionlint: PASS sobre 7 workflows `.yml`; no existen workflows `.yaml` tracked.
- R02 EOL changed-only: PASS, con renames/copies y blobs del candidate. Excepcion mecanica autorizada: `git add --renormalize -- web/src/app/compare/CompareContent.tsx`; CRLF previo `237`, CRLF posterior `0`, `semantic_bytes_changed=false` porque `old_bytes.replace(b"\r\n", b"\n") == staged_bytes`; cero CR aislado, modo/path preservados, sin rename, sin formatter y sin renormalizacion global. No se reabrio WP-F9.7-03.
- R03 whitespace ranged: PASS con `git diff --check BASELINE CANDIDATE`.
- R04 protected closure: PASS, 21 pathspecs canonicos expanden a 32 archivos baseline y comparan blob/path/mode sin drift.
- R05 candidate identity: PASS, modo local `index`, baseline `8ab1cdf9173b8093781e75ba32c2fea9ae931b14`, candidate tree explicito y stage estable.
- R06 hooks: PASS, `.githooks/pre-commit` y `.githooks/pre-push` modo `100755`, scan Git-native fail-closed.
- R07 credential scan: PASS, candidate tree/index sin findings y output redacted.
- R08 firewall cleanup: PASS, helper unico `.github/scripts/fase09_7_firewall_guard.sh` modo `100755`, ownership y cleanup solo para `F97_FRONTEND_EGRESS`, `FASE097_EGRESS`, `FASE097_AUDIT_EGRESS`.
- R09 aggregator: PASS, job requerido `security-audit` con `if: always()`, `release-gates` en `needs` y cero `continue-on-error`.
- Tests locales Docker: `tests/test_fase09_7_release_gates.py` + `tests/test_fase09_7_pipeline_no_regression.py` = `102 passed, 1 skipped`; subset credenciales WP-04 = `5 passed`; subset integrado schema/RLS = `3 passed`; Context Graph = `PASS (55 files, 561 links)`.
- Backlog fuera de alcance registrado como [BK-F9.5-08](../backlog_tareas/req_est_001_sprint_1/backlog_f9_5_known_findings.md#bk-f95-08---hardening-futuro-fuera-de-alcance-wp-f97-04), estado `DEFERRED_NO_IMPLEMENTATION`.
- Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`; sin Supabase Free/Pro, Cloudflare manual, DDL/DML remoto en Free/Pro, pipeline, frontend runtime, push ni PR.

### Reapertura Forward-Fix WP-F9.7-04

- PR #258 produjo `NO_GO_CI` inicial contra candidate `b711e0b`/tree `249295`.
- Candidate `b711e0b`/`249295` queda `SUPERSEDED_BY_CI_FORWARD_FIX`, no se reescribe ni se amenda.
- Causa raiz CRLF: `.gitattributes` aplicaba `eol=lf` a blobs historicos CRLF; el fix debe acotar patrones a rutas cuyos blobs candidate ya son LF, sin `--ignore-cr-at-eol`, sin `git add --renormalize .` y sin normalizacion global.
- Causa raiz firewall: el helper verificaba jumps mediante `-C OUTPUT -j CHAIN` antes de que la cadena existiera; el fix debe inspeccionar `-S OUTPUT`, capturar primero el rc del firewall, registrar ownership antes de mutaciones recuperables y preservar recursos no-owned.
- Estado historico: `WP-F9.7-05` y las seis auditorias finales previas quedaron invalidadas por cambio de tree y fueron repetidas sobre el candidate final.
- `AUTOMATIC_PR_PREVIEW_ACCEPTED`: se acepta solo el preview automatico preexistente del PR; no hay operacion manual Cloudflare, dashboard, API, Workers, produccion ni deploy manual.
- Supabase previews skipped; no Supabase Free/Pro, DDL/DML remoto en Free/Pro, backup, writers ni backfill.
- Accion historica/superseded: `validate_wp_f9_7_04_ci_forward_fix`; fue consumida por `CORR-WP-F9.7-04-02` y ya no es la siguiente accion vigente.

### Reapertura Forward-Fix WP-F9.7-04 - CORR-02

- `CORR-WP-F9.7-04-01` produjo commit `120d234a99a5f856f209b1f5007d713c296b4612` con tree `bf68ed90d186439ced713bcef2a4a6b1448e38fb`; la evidencia local fue util, pero CI produjo `NO_GO_CI_120D234` y el candidate queda `NO_GO_CI_NOT_PROMOTABLE`.
- Causa raiz actionlint: `actionlint -version` puede emitir salida multilinea y el gate comparaba el output completo en bruto contra `1.7.7`; el fix debe comparar solo la primera linea y mantener asset/SHA256 fijados.
- Causa raiz `env -i`: los jobs ejecutados como UID/GID `65534` no propagaban `F97_BASELINE_COMMIT`, `F97_CANDIDATE_MODE`, `F97_CANDIDATE_COMMIT`, `F97_CANDIDATE_TREE` ni `safe.directory` restringido al workspace; el fix debe pasar esas variables explicitamente sin usar `safe.directory=*`.
- Causa raiz frontend cold-cache: el helper hermetico trataba como fallo el warning exacto de Next.js `No build cache found` en CI frio; el fix permite una unica ocurrencia exacta en stdout, mantiene stderr fail-closed y conserva fallo absoluto ante exit code distinto de cero.
- CI de `d2cb32ea118a4b8461460f57973d02f9d3e39754` / tree `16081a60c0e90b4e7fc39e4223371f1c388b8ae3` produjo `NO_GO_CI_D2CB32E`; ese candidate queda `NO_GO_CI_D2CB32E_NOT_PROMOTABLE`.
- Frontend Static Build CI de `d2cb32e=PASS`; las causas restantes son actionlint/ShellCheck parity y commit-mode Git read-only.
- Dos findings `SC2086` legacy en `.github/workflows/db-sync-to-pro.yml` y `.github/workflows/production_pipeline.yml` quedan `RESIDUAL_ACCEPTED_PROTECTED_BASELINE`; no autorizan waivers amplios ni cambios a workflows legacy.
- `CORR-WP-F9.7-04-02=COMPLETED_LOCAL_MERGED`: commit `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de` paso CI, seis auditorias finales y merge humano.
- Orden ejecutado: `READY_FOR_CI` -> CI verde -> seis auditorias finales nuevas sobre el mismo commit/tree -> `GO_FOR_HUMAN_REVIEW` -> aprobacion humana -> merge PR #258 -> replay post-merge PASS.
- Las auditorias anteriores quedan `INVALIDATED_STALE_ORACLE`; no se reutilizan aunque hayan sido GO sobre `b711e0b` o `120d234`.

### Stop Conditions

- Gate que pase vaciamente por comparar worktree limpio contra index.
- Escaneo que omita archivos nuevos, renames o commits intermedios.
- Normalizacion masiva de protected paths.
- Descarga mutable o sin checksum.

## WP-F9.7-05 - Candidate Inmutable Y Evidencia

### Objetivo

Materializar un unico tree acumulado, ejecutar toda la matriz contra sus bytes exactos y prohibir cambios posteriores sin invalidar la evidencia.

### Actividades

1. Confirmar que todos los cambios intencionales pertenecen a los commits WP-01 a WP-04.
2. Exigir worktree limpio, cero untracked y ancestry exacta desde baseline.
3. Registrar `CANDIDATE_COMMIT` y `CANDIDATE_TREE`.
4. Materializar el tree en un directorio Linux limpio dentro de Docker.
5. Ejecutar suites DB, frontend, pipeline, credentials, Context Graph, actionlint, EOL y compile.
6. Registrar comandos, versiones, resultados, warnings/skips y hashes sin secrets, endpoints, PII ni filas crudas.
7. Repetir tree SHA al terminar y exigir igualdad.

### Matriz Acumulada

- F9.7 Python focused PASS.
- PostgreSQL 17 v3 PASS.
- PostgreSQL 17 hold PASS.
- Frontend lint/type/build/export/Playwright PASS.
- Python compile PASS.
- Context Graph PASS.
- Actionlint/EOL/whitespace PASS.
- Credential scan PASS.
- V3/protected paths zero drift.
- Candidate tree estable.

### Evidencia GO

- Auditor `qa-test-engineer`: `GO_WP` sobre matriz completa.
- Auditor `devops-release-manager`: `GO_WP` sobre tree/ancestry/evidence.
- Cero cambio de archivos despues de capturar el tree.

### Evidencia Local WP-F9.7-05

- Estado: `COMPLETED_LOCAL_REPLAYED` para el corte local; F9.7 completo en Free sigue pendiente.
- Candidates previos no promocionables: `b711e0b`/`249295`, `120d234`/`bf68ed` y `d2cb32e`/`16081a60`.
- Candidate final PR: `258ef3a98c7c1010efe58522bb1eca892e26390e` / tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
- Merge humano: `e95eeaccc864477db587bbb13c827d0c17340d8d`, parents `8ab1cdf9173b8093781e75ba32c2fea9ae931b14` y `258ef3a98c7c1010efe58522bb1eca892e26390e`, tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
- Materializacion post-merge: checkout Linux limpio dentro de Docker sobre `e95eeac`; tree inicial y final `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
- Comandos replay registrados: `git fetch`, `git rev-parse`, checkout Linux limpio de `e95eeac`, `python3 -m venv`, `pip install`, `python3 -m py_compile`, `python3 scripts/maintenance/validate_context_graph.py`, `actionlint`, `shellcheck`, `npm ci`, `npm run lint`, `npx tsc --noEmit`, `npm run build`, Playwright publico, `python3 -m pytest` y `psql` contra PostgreSQL local efimero.
- Versiones replay: Docker host con `studiamatch-dev`; Python `3.11.2`, Node `v20.20.2`, npm `10.8.2`, Git `2.39.5`, pytest `8.4.1`, Playwright `1.61.0`, Chromium `149.0.7827.55` / playwright chromium `v1228`, actionlint `1.7.7`, ShellCheck `0.9.0`, cliente PostgreSQL `15.18` y servidor `postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193`.
- Matriz Git/release post-merge: candidate identity, ancestry, actionlint `1.7.7`, ShellCheck `0.9.0`, EOL changed-only, whitespace ranged, protected closure, hooks, credential scan, firewall helper y Context Graph en PASS.
- Matriz Python sin database post-merge: backend identity, Gate B readonly, remediation definition, schema/RLS, security hold, pipeline no-regression, release gates y credentials en PASS bajo UID/GID `65534`; conteos observados `227 passed, 4 skipped, 1 warning` y subset hold `7 passed`.
- Matriz PostgreSQL 17 post-merge: v3 y hold ejecutados en PostgreSQL 17 efimero sin red mediante socket compartido, con apply/replay/rollback en PASS y cleanup final; `F9.7 PostgreSQL 17 public access and trigger retirement: PASS` y `F9.7 leads/email security hold PostgreSQL 17 contract: PASS`.
- Matriz frontend post-merge: `npm ci` instalo `630 packages` y audito `631 packages`; `npm run lint` termino con `0 errors, 9 warnings`; typecheck, build con stub loopback, export y Playwright publico `1 passed` en PASS con firewall local F9.7.
- Warnings/skips no bloqueantes: `npm warn deprecated node-domexception@1.0.0`, `npm audit` reporto `14 vulnerabilities (2 low, 5 moderate, 7 high)` heredadas, npm aviso upgrade `10.8.2 -> 12.0.2`, PyPDF2 `DeprecationWarning`, PostgreSQL emitio `NOTICE ... does not exist, skipping` y cleanup efimero con `drop cascades to 37 other objects` durante reset local; no hubo secretos ni endpoints remotos en la evidencia.
- Python compile, Context Graph `PASS (53 files, 512 links)`, actionlint, credential scan y protected closure PASS; evidencia de replay termina en `POST_MERGE_REPLAY PASS e95eeaccc864477db587bbb13c827d0c17340d8d 2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
- Free/Pro permanecen `UNCHANGED_NOT_ATTESTED`; security hold permanece `LOCAL_CANDIDATE_BLOCKED`; sin Supabase Free/Pro, Cloudflare manual, DDL/DML remoto en Free/Pro, backup, writers, backfill ni deploy.

### Stop Conditions

- Test ejecutado contra worktree distinto del tree registrado.
- Archivo generado, untracked o secreto en el candidate.
- Cualquier cambio posterior sin nuevo tree y repeticion de gates afectados.

## WP-F9.7-06 - Auditoria Final, Push Y PR

### Objetivo

Emitir el verdict agregado `GO_FOR_LOCAL_PR`, publicar la rama feature y abrir un PR revisable sin efectuar merge ni operacion remota de datos.

### Contrato De Auditoria Final

Los seis auditores revisan el mismo `CANDIDATE_COMMIT`/`CANDIDATE_TREE` y usan exclusivamente los doce invariantes y la clasificacion de hallazgos de este plan:

- `security-auditor`.
- `supabase-architect`.
- `frontend-architect`.
- `pipeline-engineer`.
- `qa-test-engineer`.
- `devops-release-manager`.

Remote unknown, owner/superuser y SQL dinamico ofuscado se registran segun su clasificacion aceptada y no cambian por si solos `GO_FOR_LOCAL_PR`.

### Criterio De GO

- Seis verdicts `GO_FOR_LOCAL_PR` sobre el mismo tree.
- Cero `BLOCKING_IN_SCOPE` abierto.
- Residuales y backlog identificados sin ampliar F9.7.
- Pre-commit y pre-push PASS.
- Push exclusivo de `feat/f9-7-security-cutoff`.
- PR hacia `desarrollo` con template, matriz, hashes, threat model y riesgos.
- Review solicitado a `romelhc95-approver`.
- Checks requeridos, incluido `security-audit`, en success.
- Para `CORR-WP-F9.7-04-02`, CI verde antecede a las seis auditorias finales; solo despues puede emitirse `GO_FOR_HUMAN_REVIEW`.

### Evidencia Final WP-F9.7-06

- Estado: `COMPLETED_LOCAL_MERGED`.
- Evidencia final sanitizada: `issuecomment-5133103661`.
- CI requerida: `security-audit=pass`; checks del PR en success y Supabase Preview skipped esperado.
- Seis verdicts individuales finales: `security-auditor=GO_FOR_LOCAL_PR`, `supabase-architect=GO_FOR_LOCAL_PR`, `frontend-architect=GO_FOR_LOCAL_PR`, `pipeline-engineer=GO_FOR_LOCAL_PR`, `qa-test-engineer=GO_FOR_LOCAL_PR`, `devops-release-manager=GO_FOR_LOCAL_PR`.
- `BLOCKING_IN_SCOPE=0`; residuales aceptados historicos: `public.exec_sql(text)` control-plane local, autoridad administrativa `postgres`/superuser, Free/Pro `UNCHANGED_NOT_ATTESTED`, dos `SC2086` legacy de baseline protegido y warnings externos no mapeados a invariantes. `public.exec_sql(text)` no es aceptable como estado final del PR-O sucesor.
- Aprobacion humana: `romelhc95-approver`, review `APPROVED` sobre `258ef3a98c7c1010efe58522bb1eca892e26390e`.
- Merge humano: PR #258 cerrado como merged por `romelhc95-approver` en `e95eeaccc864477db587bbb13c827d0c17340d8d`, sin merge automatico por agente.

### Follow-Up Documental Post-Merge

- PR #259 reconcilio documentalmente el replay post-merge y fue fusionado por humano en `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c`.
- `fdaac633d29476e3323a8f88741a87570ece3b7c` conserva tree `2fa573d878eb566dd00f6fe21939e5b6420133ed`; este snapshot sustituye la accion documental anterior y no cambia el candidate tecnico `258ef3a`/`2cb182` ni el replay `e95eeac`/`2cb182`.
- Acciones anteriores `validate_wp_f9_7_04_ci_forward_fix`, `CORR-WP-F9.7-04-01`, candidates `b711e0b`, `120d234` y `d2cb32e`, y auditorias previas al tree final quedan historicas o `SUPERSEDED`.
- Siguiente accion historica de PR #259: `definicion de PR-O combinado v3 + hold`; queda satisfecha por la seccion siguiente. No se implemento ni aplico PR-O en ese follow-up.

### Definicion Local PR-O V1

- PR #260 fue mergeado por humano en `desarrollo@e2721a0ec4581e422246dfabfa2048297f537025`, tree `0bc0d4b806117fb1b6a2a9fc4d618daa367829ee`, y contiene `779001c5a63b59bcd902928d1db333e82e6f1d3b`.
- PR #261 fue mergeado por humano en `desarrollo@ee0e320d55b70dedd72c5a09429ed84a34bf7543`, tree `218bfcc7e99bdef3569fc730bba21228dee53540`, y llevo [PR-O F9.7 v3 + hold](./pr_o_f9_7_v3_hold.md) a historia.
- [PR-O F9.7 v1 superseded](./pr_o_f9_7_v3_hold.md) queda `SUPERSEDED_NON_PROMOTABLE`; el hold actual `F9.7-LEADS-EMAIL-SECURITY-HOLD-20260729` queda `SUPERSEDED_NON_PROMOTABLE_FOR_FUTURE_ROUTE`.
- [PR-O F9.7 executor privado](./pr_o_f9_7_successor_private_executor.md) queda `CERTIFIED_LOCAL_PR_O_SUCCESSOR`: exige eliminar `public.exec_sql(text)` del estado final, usar executor privado digest-bound, target-bound, single-use y no expuesto por Data API, validar Edge como `REMOTE_ABSENT`, `REMOTE_TOMBSTONE_410` o `DISABLEMENT_SEPARATE_AUTHORIZED`, y separar preflight read-only, backup/restore, writer pause, `GO_FOR_FREE` y aplicacion final.
- La secuencia atomica futura queda `pending v3 -> postcondiciones v3 -> ledger v3 -> hold sucesor -> verificador terminal -> ledger hold -> verificacion final -> commit unico`; boundary `7` es replay `READ ONLY` sin locks de escritura.
- `application_authorized=false`, `capabilities=[]`, Free/Pro `UNCHANGED_NOT_ATTESTED`, backup/restore/writers/drain/window `PENDING`; cero capacidad remota ejecutable.
- Los siete SQL y los manifests actuales no se modifican y quedan ligados por digest en el contrato sucesor.

### Prohibiciones

- No merge automatico.
- No push directo a `desarrollo`, `certificacion` o `main`.
- No Supabase Free/Pro, DDL/DML remoto en Free/Pro, backup/restore, writers, deploy o aplicacion PR-O.
- No reutilizar auditorias de un tree anterior.

## Propiedad De Archivos

| Superficie | WP propietario |
|---|---|
| ADR, plan, tarea, estado, indices, changelog, `AGENTS.md` | `WP-F9.7-01` |
| Migration/manifest/runbook/candidate DB y tests PostgreSQL | `WP-F9.7-02` |
| Frontend, Edge tombstone, compare storage, export y Playwright | `WP-F9.7-03` |
| Workflows, gitattributes, hooks y contratos de release | `WP-F9.7-04` |
| Tree, matriz acumulada y evidencia sanitizada | `WP-F9.7-05` |
| Auditorias finales, push y PR | `WP-F9.7-06` |

Si un archivo requiere cambios desde mas de un WP, el WP que descubre la necesidad debe derivarlo al propietario y declarar la dependencia. No se modifica silenciosamente desde otro paquete.

## Checkpoints Git

| WP | Commit local esperado | Push |
|---|---|---|
| `WP-F9.7-01` | `docs(f9.7): freeze definitive closure contract` | Prohibido |
| `WP-F9.7-02` | `fix(db): close F9.7 terminal hold routes` | Prohibido |
| `WP-F9.7-03` | `fix(web): finalize no-leads public surface` | Prohibido |
| `WP-F9.7-04` | `ci(f9.7): bind cutoff release gates` | Prohibido |
| `WP-F9.7-05` | Sin commit si el tree no cambia | Prohibido |
| `WP-F9.7-06` | Fix commit nuevo solo si invalida y repite evidencia | Permitido tras GO final |

No se usa amend, squash local, reset destructivo ni bypass de hooks. El PR puede usar el metodo de merge permitido por proteccion de rama despues de review humano.

## Ruta Posterior Al PR Local

1. Merge humano del corte: completado en PR #258 (`e95eeaccc864477db587bbb13c827d0c17340d8d`).
2. Replay post-merge en checkout Linux limpio: PASS sobre tree `2cb182ab9ece141bd8e84d7bbf9c91d771f603de`.
3. Follow-up documental post-merge sobre `desarrollo@fdaac633d29476e3323a8f88741a87570ece3b7c`: completado en PR #260; merge humano `e2721a0ec4581e422246dfabfa2048297f537025` contiene `779001c5a63b59bcd902928d1db333e82e6f1d3b`.
4. `definicion de PR-O combinado v3 + hold`: completada en PR #261 y luego superseded; merge humano `ee0e320d55b70dedd72c5a09429ed84a34bf7543` / tree `218bfcc7e99bdef3569fc730bba21228dee53540`.
5. Definicion local del PR-O sucesor con executor privado: [PR-O F9.7 executor privado](./pr_o_f9_7_successor_private_executor.md).
6. Implementacion local del PR-O sucesor: `GO_WP_LOCAL`, sin autorizacion de aplicacion.
7. Certificacion local separada `CERTIFICACION_LOCAL_PR_O_SUCCESSOR`: `CONSUMED_PASS` como `CERTIFIED_LOCAL_PR_O_SUCCESSOR` en `771b8b1366e302eae52e4263577e0f6967679d7b` / tree `99f315c6820966e94213665df43cd21f9f4ef730`.
8. Gate separado `PREFLIGHT_READ_ONLY_FREE` para snapshot catalog-only Free sin filas ni payloads, pendiente de autorizacion propia.
9. Aprobacion independiente de `GO_FOR_FREE` y aplicacion/certificacion schema Free hasta `GO_F9.7_COMPLETE`.
10. F9.8 plan editorial y F9.9 ejecucion/no-op certificado.
11. F9.10 `free_certified`.
12. F10 Pro/main/observacion.
13. F11 cierre final.

## Datos Y Aprobaciones Futuras

El cierre local no necesita keys, URLs, passwords ni identificadores sensibles del usuario. La etapa Free posterior requerira decisiones humanas separadas sobre target binding, owner de recuperacion, backup/restore, pausa de writers y ventana operativa. Esas decisiones no se anticipan mediante este plan.

## Referencias

- [Estado del proyecto](../estado_del_proyecto.md)
- [TASK-H1-001](../backlog_tareas/req_est_001_sprint_1/tarea_001_hito_1.md)
- [ADR-0003](../decisiones/ADR-0003_taxonomia_macrofases_subfases.md)
- [ADR-0005](../decisiones/ADR-0005_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- [Plan de corte Hito 1](./plan_corte_seguridad_funcionalidad_estabilidad_hito1.md)
- [Flujo de release minimo](./flujo_release_minimo.md)
- [Arquitectura del pipeline](../arquitectura_pipeline.md)
- [Estructura frontend](../estructura_frontend.md)
