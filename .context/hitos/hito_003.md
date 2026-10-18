# HITO-003 - Admin Editorial

> **Nota de vigencia, 2026-10-12:** los cortes NO-GO locales de 2026-10-08 que siguen abajo son historia preservada. El estado actual del alcance local es G01–G09 GO por R178 y G10 local R181/R182; G10 remoto y el cierre contractual siguen pendientes. Consultar [estado operativo](../estado_del_proyecto.md), [navegación de hitos](README.md) y [evidencia R178](../evidencia/h3req1_g09_local_close_r178_2026-10-11.md). No alterar la historia ni inferir despliegue.

## Estado actual tras r4/r5/r6/r7 — 2026-10-08

r4 quedó consumido: 20 pytest PASS, proyector/scope guard PASS y regresión scanner FAIL
por un fallo del fixture de `grep`. r5/r6 localizaron que el falso `grep` no se invocó por
el límite `/tmp noexec`. La autorización exacta r7 se consumió en una ejecución; manifiesto
3/3 y regresión scanner PASS, exit 0, sin retry. G03 permanece abierto hasta completar
linters/revisión; el estado de GO del hito no cambia. Ver
[evidencia vigente](../evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

## Ejecución Docker r4 — 2026-10-08

Una ejecución autorizada: manifiesto 13/13; pytest 20/20; proyector y scope guard PASS;
falló la regresión scanner porque aceptó un error simulado de `grep`. Resultado general
NO-GO, exit 1 y sin retry. r5 confirmó que el `grep` simulado no se invocó; r6 mostró
que `noexec` impedía arrancarlo. El scanner no tiene defecto confirmado. El paquete r7
requiere autorización propia. G03 no se cierra; los
demás gates y el hito siguen NO-GO para GO_LOCAL_PR y GO_DEVELOPMENT_REAL. Ver
[evidencia r4/r5](../evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

## Actualización de ejecución BFF — 2026-10-08

La ejecución BFF r1 fue denegada por permisos del socket antes de iniciar la UAT; su
permiso quedó consumido y no se repitió. El reemplazo r2 pasó una sola vez con Node
`v20.20.2`, TypeScript `5.9.3`, `node --check` y UAT `PASS` (60 verificaciones, 10 casos de
cuota), exit 0. Esta prueba acotada no acredita bindings remotos ni cierra G08. r4 se
ejecutó después y terminó NO-GO por scanner. G01–G02 se mantienen en 20%; G03–G10 siguen abiertos.
Ver
[evidencia r1/r2](../evidencia/h3req1_bff_validation_access_2026-10-08.md).

## Estado operativo del candidato — 2026-10-08

Actualización: se implementó una validación fail-closed del BFF que responde 503 antes
de cuota si las dos claves HMAC coinciden; su UAT sintética pasó en r2 con 60 verificaciones
y 10 casos de cuota. El scan
formal del snapshot actual `13b4219e-4661-4e92-b4e0-1aafffc88ee3` revisó 51/51 rutas,
con cero hallazgos reportables confirmados, cuatro candidatos diferidos y cobertura
parcial. No acredita runtime ni bindings remotos. r4 se ejecutó después y terminó NO-GO
por scanner; el hito permanece **NO-GO** para `GO_LOCAL_PR` y `GO_DEVELOPMENT_REAL`.
Ver [evidencia](../evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

La ejecución aislada r3 terminó **NO-GO**: manifiesto 13/13 válido, pytest 19/20,
fallo del comparador por un registro duplicado mal ensamblado y fallo del scanner al no
imprimir su redacción; el scope guard pasó. Las causas se corrigieron. El paquete r4 tiene
13/13 hashes verificados contra las fuentes actuales y espera autorización nueva para una
única ejecución Docker. La revisión formal del snapshot registró cero hallazgos reportables
confirmados, cuatro candidatos diferidos y cobertura parcial; no acredita el árbol actual ni
resuelve enforcement remoto. No acredita F2d ni cambia el **NO-GO**. Ver
[evidencia de fixtures](../evidencia/h3req1_helper_docker_fixture_2026-10-08.md).

Traspaso actualizado: [hallazgos de sesión y dependencias para cierre local](../evidencia/h3req1_analisis_sesion_01a11a7e_2026-10-08.md)
y [prompt cíclico Luna 6 Max](../operaciones/h3req1_prompt_luna_6_max_cierre_local_2026-10-08.md).
La primera dependencia es validar/reconciliar el contexto del auxiliar F2d antes
del diagnóstico autorizado. Este traspaso no añade PASS runtime ni cambia los gates.

El candidato `feat/h3req1-sync-20261002` (baseline HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`) permanece **NO-GO** para `GO_LOCAL_PR` y
`GO_DEVELOPMENT_REAL`. Revalidación actual: C02 v4 no-C03 70/72 por cambios del workflow
de CI y del guard HMAC BFF; C03 SQL v3 41/41 coincide. No se repitieron suites SQL;
ver [evidencia de hashes](../evidencia/h3req1_revalidacion_hashes_2026-10-08.md). F2b no pasó
canonicalidad; F2c confirmó socket local canónico pero
no probó el peer ni llegó a Docker API/inspect F1. F1 sigue sin causa atribuida. El método
alternativo F2d usa `SO_PEERCRED`, estático/hash-bound, y requiere aprobación JIT separada
con residuales nuevos. Scanner, scope guard y C03 runtime necesitan validación dentro del
Docker aislado. No se ejecutó SQL ni se autorizan PR/remotos con este estado.

## Corte anterior de H3REQ1 — 2026-10-05

Actualización posterior: C03 SQL safe-suspend/resume persistente **PASS v3**; v2 abajo
es histórico. Falta integración cross-runtime, no la prueba SQL inicial. Consultar
[avance PR/remoto y siguiente sesión](../seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md).

NO-GO Development real. Payload-bound, NULL, cardinalidad de cuotas y el replay harness
corregidos localmente; 287 PASS/4 skips, Miniflare, SDK/BFF/Edge y los harnesses PG17/
PostgREST locales PASS. El JIT v4 validó SQL, replay 409, safe-suspend, baseline futuro,
wire/assert y concurrencia; no acredita enforcement remoto. El egress MEDIUM fue aceptado
solo durante npm ci y expiró al terminar. Faltan rollback integrado, UAT final, CI protegido
efectivo e integración/D01–D14 reales. Certification y Production no ejecutadas. Auth+MFA
real histórico no se reabre; no se habilitó GET innecesario `/auth/v1/factors`.
La revisión encontró y corrigió localmente la omisión del dispatcher `admin_signed_rpc`.
En PG17 pasaron baseline, cuotas, gateway y safe-suspend bajo JIT v2; la salida del
harness final se suprimió y terminó con exit code 0. Falta la integración workerd+Edge+SQL
y recuperación real; JIT v4 no cubre estos bytes. NO-GO se mantiene.
Amarre operativo: [tarea](../backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md),
[plan](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md),
[evidencia](../evidencia/h3req1_development_candidate_cycle_2026-10-04.md),
[traspaso](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md),
[resultado JIT v4](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md) y
[seguimiento](../seguimiento/seguimiento_sprint_1_h2_h5.md).

> Continuación 2026-10-04: consultar el [plan único de cierre H3REQ1](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md)
> y el [estado vivo](../estado_del_proyecto.md). Las matrices/porcentajes y bloqueos
> inferiores son cortes históricos, no inventario actual. Auth+MFA remoto ya tiene
> evidencia PASS; conservarlo y probar su transición BFF, sin convertirlo en un
> criterio comercial nuevo. El cierre permanece NO-GO hasta aceptación por ambiente,
> promoción protegida, estabilidad y contract; esta nota no habilita operaciones.

`PRESTART_CLIENT_SOURCE_ATTESTED_AFTER_H2_CERTIFICATION`
`SRC-REQ-002`
`ADENDA-REQ-EST-001-001`

| Campo | Valor |
|---|---|
| Estado | `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE` |
| Work package | `NONE_SUPERSEDED` |
| Criterio | `H3-CA4` |
| Gate | GO técnico local preservado; NO-GO para cierre contractual. La auditoría final 2026-09-23 confirma evidencia remota incompleta, 03A/03B remoto no acreditado, rutas nuevas 404 en el preview revisado y UAT por ambiente/Cerification pendiente. |

Estado histórico preservado: `READY_FOR_PROMPT_CONTINUA` fue el gate previo al inicio del ciclo H3 y no representa el estado vigente.

## Lectura Rápida Para Una Persona No Técnica

- **Objetivo:** crear una oficina privada dentro del sitio para corregir cursos y
  administrar quién puede entrar.
- **Estado:** lista localmente. Se aprobó el programa de pruebas completo dos veces
  seguidas: las 47 situaciones y las 141 comprobaciones (tres tamaños de pantalla)
  pasaron, con capturas de pantalla y sin reintentos.
- **Qué ocurrió antes:** el programa de pruebas anterior falló porque la oficina
  privada no aparecía en la copia construida que estaba siendo servida.
- **Qué se corrigió:** se ajustó el programa de pruebas para esperar a que la
  página terminara de cargar antes de tocarla, se validó el bloqueo público
  (`studiamatch.com/admin/` responde 404) sobre un servidor de perímetro y se
  corrigió un selector de prueba. Con eso, dos corridas consecutivas pasaron 47/47
  y 141/141.
- **Cómo se demuestra el cierre:** dos corridas consecutivas 141/141 aprobadas,
  con 141 capturas cada una, guardadas en la carpeta de evidencia, y evidencia
  canónica regenerada el 2026-09-02 tras el ciclo de corrección local.
- **Qué está autorizado ahora:** commit + push + PR protegido a `desarrollo` por
  instrucción humana separada. Publicar, tocar Supabase real, configurar accesos
  reales o desplegar siguen bloqueados hasta sus aprobaciones separadas.

## Alcance

`admin.studiamatch.com` como hostname canónico exclusivo del panel, Cloudflare Access
como perímetro, autenticación administrativa existente para `admin` y `user`,
membresía `admin_members`, invitación por correo mediante backend privilegiado,
gestión de roles y activación, cola paginada, filtros, edición editorial completa
para `admin`, edición de `missing_fields` para `user`, optimistic locking,
publicar/despublicar/archivar, calidad, auditoría y compatibilidad con static export.

`studiamatch.com/admin/` debe responder `404` y no servir el panel.

### Contrato de campos

Los campos editoriales públicos de curso son: `name`, `price_pen`, `price_status`,
`mode`, `duration`, `description_long`, `syllabus`, `target_audience`,
`requirements`, `certification`, `benefits`, `objectives` y `start_date_text`.

`admin` puede corregirlos todos. `user` puede corregir únicamente los que aparezcan
en `course_editorial_state.missing_fields`. Identidad, institución, URL, slug,
categoría, fecha estructurada, tipo de curso, brochure, cálculos ROI, métricas,
metadata y estados editoriales no son editables por `user`.

El pipeline debe transportar `benefits`, `certification`, `objectives` y
`target_audience` con semántica independiente; no se acepta sustituirlos
silenciosamente por el mismo origen ni marcar `missing_fields` únicamente por
`duration` sin validar el diccionario de publicación.

## Validacion Contra Fuente Cliente

El alcance base de H3 (`/admin`, cola, edición manual y publicación) se valida contra la fuente privada cliente `SRC-REQ-002` mediante la atestación sanitizada versionada [ADENDA-REQ-EST-001-001](../backlog_tareas/req_est_001_sprint_1/adenda_cliente_001_sanitizada.md). La ampliación está respaldada por la atestación sanitizada [H3-EXPANDED-PROMPT-2026-08-30](../evidencias_cliente/sprint_1/atestado_h3_ampliacion_prompt_humano_sanitizado.md), que autoriza únicamente ejecución local Docker hasta GO local. La fuente privada no se versiona ni se expone en PRs.

## Contrato De Acceso

- Usuario anonimo no accede.
- Usuario autenticado sin membresia activa no accede.
- Usuario con membresia activa `user` accede a `/admin/`, consulta la cola y completa unicamente campos incluidos en `missing_fields`.
- Usuario con membresia activa `admin` hereda las capacidades de `user` y ademas publica, despublica, archiva, actualiza `quality_status` y gestiona membresias.
- Toda mutación exige identidad y rol válidos dentro de la RPC; las acciones administrativas exigen rol `admin` y dejan auditoría.
- `admin` puede invitar por correo, cambiar el rol y activar/desactivar cualquier membresía `admin` o `user` desde el panel mediante botón o checkbox, sujeto únicamente a la invariante de conservar al menos un `admin` activo y evitar el auto-bloqueo accidental del último admin.

## Contrato Funcional

- Cola paginada con filtros por estado editorial/calidad.
- Edición admin de todos los campos editoriales públicos definidos; edición user solo de `missing_fields`.
- Optimistic locking por `version`.
- Publicar/despublicar/archivar y cambiar `quality_status` solo para admin.
- Publicar/despublicar/archivar sin que pipeline pueda saltar revisión.
- Auditoría append-only por cada mutación editorial y de membresía.
- MFA TOTP/`aal2` queda fuera del gate de aceptación H3REQ1 por decisión de alcance. La implementación existente se conserva como compatibilidad y mejora evolutiva; no se declara validación MFA como requisito de cierre.
- Cloudflare Access protege `admin.studiamatch.com`; `studiamatch.com/admin/` responde HTTP 404 y no sirve el panel.
- Invitación de usuarios por correo mediante Edge Function protegida con `verify_jwt=true`; `service_role` nunca llega al navegador.
- El panel admin debe mostrar el estado activo/inactivo y permitir activarlo o desactivarlo en cualquier miembro `admin` o `user` mediante botón o checkbox con confirmación y feedback.
- Pro es la fuente autoritativa del baseline H2: schema, tipos, constraints, campos y últimas migraciones; Free y el PostgreSQL 17 local deben converger hacia ese baseline Pro, nunca al revés.
- La convergencia H2 debe cubrir schema, funciones, grants, RLS, vistas, campos y migraciones; los datos operativos no se sincronizan como mecanismo normal.
- Las migraciones H3 son un delta funcional nuevo: pueden estar ausentes en Pro hasta su promoción protegida, pero deben ser el mismo artefacto versionado que se valida primero en local, luego en Free y finalmente en Pro.
- Las migraciones H3 Docker, harness y fixtures ya validados se reutilizan como candidato; se rebaten contra la forma Pro en una base PG17 limpia; solo se crean deltas idempotentes cuando exista incompatibilidad demostrada.
- No se borran ni se repiten automáticamente cambios H3 locales; los datos de prueba no se promueven.
- Segunda corrida `NOOP` y validación remota antes de Certification; la validación remota permanece bloqueada hasta GO local y JIT.
- UAT local ampliada: dos corridas reportan 47/47 casos y 141/141 ejecuciones PASS con cero retries y 141 screenshots por corrida. Auditoría posterior determinó que parte de la matriz valida presencia de código/controles y no E2E contractual completo.
- Static build: `npm run build` y `npm run build:mock` revalidados PASS en Docker; las cuatro rutas admin están exportadas. Waiver static export superseded.

## Gate

Estado vigente: `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`. El GO técnico
local `H3_PR_DEVELOPMENT_READY_LOCAL` permanece acreditado. Los bloqueadores
locales que QA, seguridad y DB detectaron fueron corregidos y revalidados en Docker:
`security-audit.yml` con allowlist H3 y `db-gate` PG17, contrato
`20260902_h3_pr_contract.sql`, seed idempotente, harnesses H3, MFA mock con
`aal` real, UAT canónica y evidencia vinculada al candidato. El delta
`20260903_h3_rbac_contract_fix.sql` añade la corrección de los hallazgos remotos
A6/A13 y la regresión PG17 correspondiente.

JIT-A Development se ejecutó remotamente sobre Free con `20260903` aplicado. `studiamatch.com`/`www.studiamatch.com` permanecen como producción (`main`); la URL `88f02c53.studiamatch-aty.pages.dev` es el preview reproducible de `desarrollo`:
A6/A13 fueron corregidos y validados; el ambiente quedó limpio tras las pruebas
con usuarios/factores temporales. JIT-B valida membresía Cloudflare y perímetro
E1/E3/E4/E8, pero E2/E5/E6/E7 requieren un hostname/deployment administrativo
correcto por ambiente. La documentación no presenta estas validaciones parciales
como cierre contractual.

## Addendum 2026-09-21 - H3-BUILD-03B DB

El subgate `H3-BUILD-03B-DB-IMPLEMENTATION` quedó en
`H3-BUILD-03B-DB_LOCAL_VALIDATED`. La migración
`db/migrations/20260921_h3_invitation_onboarding_rpc.sql` implementa TTL
server-side de 24 horas, aceptación, password setup, estado de onboarding,
locks, expiración lazy, auditoría idempotente y ACL mínima. El harness
`tests/sql/h3_invitation_onboarding_harness.sql` termina en
`h3_invitation_onboarding_harness_ok` y el harness Edge 03A conserva
`h3_invitation_edge_runtime_harness_ok`.

Este addendum no cambia el GO técnico local ni declara cierre contractual. La
auditoría final 2026-09-23 deja el cierre en NO-GO hasta completar evidencia remota.

### Addendum 2026-09-23 - Auditoría Final De Cierre

La matriz y decisión completas están en
`h3req1_closure_review_final_2026-09-23.md`. MFA fue retirado del gate por
complejidad de prueba y porque no bloquea la funcionalidad principal; queda como
mejora evolutiva. Permanecen abiertos 03A/03B remoto, UAT Development y
Certification, hostnames por ambiente, convergencia Pro/Free/local y
`expand -> compatibilidad -> deploy -> contract`.

## Matriz de avance por criterio

| Criterio | Implementación | Validación | Pendiente de cierre |
|---|---|---:|---:|---|
| H3-CA4.1 Auth/RBAC | 90% | 85% | Auth real y negativos remotos. |
| H3-CA4.2 Ownership de 13 campos | 85% | 75% | Cobertura de valores efectivos en entorno real. |
| H3-CA4.3 Transporte independiente | 60% | 40% | Prueba E2E diferenciando cuatro campos en entorno real. |
| H3-CA4.4 Cola | 85% | 70% | Segunda página y cursor en entorno real. |
| H3-CA4.5 Mutaciones | 90% | 75% | Locking de estados en entorno real. |
| H3-CA4.6 Auditoría | 85% | 60% | Auditoría de todas las mutaciones en entorno real. |
| H3-CA4.7 MFA/`aal2` (fuera del gate) | Evolutivo | No bloqueante | Retirado del criterio de aceptación por decisión de alcance; implementación existente conservada como compatibilidad/mejora evolutiva. |
| H3-CA4.8 Membresías | 75% | 45% | Invitación por correo (Edge Function) y Auth real. |
| H3-CA4.9 Hostname | 60% | 40% | Allowlist positiva, smoke en despliegue y Cloudflare Access. |
| H3-CA4.10 Convergencia | 55% | 35% | Diff Pro/Free/local y validación remota JIT. |
| H3-CA4.11 UAT/artifacts | 100% estructural | 55% contractual | UAT local canónica 47/47 y 141/141 PASS; falta UAT real en Free/Certification. |
| **Cierre H3REQ1** | **78.7% provisional** | **No-GO remoto** | **`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`; GO técnico local preservado, evidencia remota pendiente.** |
