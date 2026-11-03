# Evidencia — continuación local del candidato H3REQ1 — corte 2026-10-05

**Veredicto vigente:** `NO-GO_H3REQ1_DEVELOPMENT_FREE`. El JIT v2 detectó ambigüedad `key_id`, corregida localmente como `v_key_id`. En PG17 v3 el replay falló con headers residuales del non-editor. El harness se corrigió para probar el replay exacto inmediatamente; bajo JIT v4 pasaron los harnesses PG17, replay 409, PostgREST wire/assert y concurrencia. Otros gates de cierre siguen pendientes; no hay enforcement remoto acreditado.

Amarre: [estado](../estado_del_proyecto.md),
[plan único](../operaciones/plan_cierre_integral_h3req1_2026-10-04.md),
[traspaso actual](../seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md),
[HITO-003](../hitos/hito_003.md),
[TASK-H3-001](../backlog_tareas/req_est_001_sprint_1/tarea_003_hito_3.md) y
[mapa del histórico](../seguimiento/mapa_documental_obsidian_2026-10-04.md) y
[manifiesto JIT v1](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05.md),
[resultado JIT v2](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v2.md) y
[resultado JIT v3](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v3.md) y
[manifiesto JIT v4](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md).
Los estados/manifiestos inferiores pre-payload-bound y pre-NULL se preservan por
trazabilidad. El resultado runtime actual corresponde al manifiesto v4, consumido tras el
PASS del alcance local. Cualquier cambio futuro de fuente/harness invalida los hashes
anteriores y exige una selección transitiva nueva y otro JIT.

## Safe-suspend — corrección estática posterior al JIT v4 — 2026-10-05

Una revisión posterior detectó una brecha en el contrato de suspensión: el rollback
revocaba las RPC mutadoras internas, pero el dispatcher autenticado `admin_signed_rpc`
seguía concedido a `authenticated` y es `SECURITY DEFINER`; el harness solo medía las
ACL de las funciones internas. Esto significa que el PASS safe-suspend del JIT v4 no
acredita la nueva ruta ni cubre los bytes actuales.

Con autorización humana local acotada se actualizó `db/rollback/h3req1_safe_suspend.sql`
para revocar también `admin_signed_rpc`. El harness captura esa ACL, prepara una llamada
local con prueba payload-bound válida, ejecuta el pre-request y exige rechazo por
privilegios antes de que se consuma el nonce; la restauración TEST-only compara y
reconstruye los permisos efectivos capturados, incluido el dispatcher.

Revisión estática manual de los cambios y de la secuencia del workflow. Bajo el JIT inicial,
un PG17 desechable ejecutó y pasó `h3_from_h2_pro_pg17_harness.sql`,
`h3_admin_quota_harness.sql` y `h3_admin_rpc_signed_gateway_harness.sql`. Este último
imprimió filas `set_config` con HMACs sintéticos de fixture; por precaución se detuvo esa
secuencia antes de `h3_safe_suspend_harness.sql`. No se copiaron valores a evidencia ni se
expusieron credenciales/JWT de producto. Hubo una consulta de versión mal citada sin cambio
de datos; `pg_config` confirmó PostgreSQL 17.11. El contenedor parcial y tmpfs quedan
preservados.

Después se aprobó la [continuación JIT v2](../operaciones/manifiesto_jit_h3_close03_safe_suspend_pg17_2026-10-05_v2.md)
y se ejecutó solo safe-suspend con `-q -o /dev/null`; exit code 0, sin output.
No se reutiliza JIT v4. H3-CLOSE-03 sigue abierto: faltan el drill integrado
workerd+Edge+SQL y recuperación operativa explícita. El restore del harness sigue siendo
TEST-only. La atestación sanitizada
H3-CA4/H3 local fue revisada; no se amplió contrato ni se autorizó operación remota.

## Continuación local — hallazgos de seguridad, cuotas y contrato SDK — 2026-10-05

### Cambios locales

- Remediado el HIGH de cardinalidad del Durable Object: `login-ip` y `login-account-ip`
  comparten shard HMAC por IP; el Worker exige exactamente un contador de cada clase,
  rechaza cuenta-IP sin su IP emparejada y no crea una cuenta nueva una vez bloqueada la
  IP. Se conservan los límites **20/IP/10 min** y **10/cuenta-IP/10 min**. El payload BFF
  anterior sin `shard` se enruta por inferencia al mismo shard durante compatibilidad.
- Ledger expirado se elimina dentro de la transacción de alarma. El harness runtime local
  transforma `digest` y `shard` con el mismo epoch para aislar correctamente cada reset.
- El análisis del SDK fijado `@supabase/auth-js` 2.109.0 demostró que `listFactors()` usa
  GET `/auth/v1/user` y `user.factors`, no GET `/auth/v1/factors`. No se amplió la allowlist
  JWT; la decisión humana que autorizaba evaluar el GET extra quedó sin consumir. La
  regresión SDK verifica el request real y la atestación sanitizada conserva la decisión.

### Validación local Docker de los bytes candidatos

| Gate | Resultado |
|---|---|
| `python -m pytest tests -q` | **287 passed, 4 skipped**, 1 warning PyPDF2 deprecado |
| `npx tsc --noEmit` | PASS |
| ESLint | 0 errores, **9 warnings preexistentes** (7 hooks/facetas, 2 no-unused-vars) |
| `npm audit --include=dev` / `--omit=dev` | 0 vulnerabilidades cada uno |
| Cuotas `h3_admin_quota_uat.mjs` | PASS: 25 concurrencias, 20 identidades por IP en 1 DO, 21.ª bloqueada sin nueva cuenta, paired/legacy shard, borrado de ledger expirado |
| Cuotas `h3_admin_quota_runtime.mjs` | PASS Miniflare/workerd: concurrencia, persistencia tras restart, shard común y payload BFF anterior; ejecutado con Node `v20.20.2` |
| SDK `h3_supabase_sdk_headers_uat.mjs` | PASS, 39 checks y 7 redirecciones rechazadas; `listFactors()` GET `/auth/v1/user`, factors POST-only |
| BFF mock / Auth errors / Edge typecheck+UAT / safe-suspend fixture | PASS: 60 checks BFF; 7 errores Auth; SDK 2.109.0; casos replay/concurrencia Edge; 5 suspensión y 8 aliases rechazados |
| H2 web mock smoke | PASS (`h2_web_mock_smoke_ok`) |
| Credential scan de fuentes pertinentes | PASS ejecutado como root dentro del contenedor (el primer intento como `node` no pudo escribir el temporal fijo `/tmp/studiamatch_credential_findings`; se repitió correctamente) |
| `git diff --check` | PASS; WIP no staged |
| Allowlist del runner PostgREST | `node --check tests/h3_admin_quota_postgrest.mjs` PASS; permite solo `127.0.0.1:3233` (CI local) o el hostname/puerto exacto de este contenedor interno; sin host/puerto variables |
| Workflow PostgREST CI | Puerto de PostgreSQL mapeado a `127.0.0.1`; PostgREST usa `--network host` con config `server-host=127.0.0.1`. Parser YAML y `bash -n` del `db-gate` PASS; GitHub Actions no se ejecutó. |
| `actionlint` / CI remoto | **Pendiente**: `actionlint` no está instalado en el snapshot Docker y no se descargó; no se disparó CI remoto. Owner Romel; no se acredita check protegido hasta ejecutarlo en un ciclo autorizado. |
| Revisión de código producto | Sin defectos LOW+ no mitigados en cuotas/BFF/SDK. El riesgo **MEDIUM** de egress npm fue aceptado y limitado al bootstrap; `npm ci` instaló 90 paquetes y reportó 0 vulnerabilidades; ese permiso expiró al terminar. |
| SQL/PG17 | JIT v4 PASS: H2/H2 Pro (rollback guard esperado), H3 default/baseline Pro, cadena H2→H3, cuotas, signed gateway, safe-suspend y baseline futuro contraído. |
| Harness replay | `h3_admin_rpc_signed_gateway_harness_ok`; el replay exacto inmediato devuelve `rpc_replay_rejected`/409. Corrección local revisada por `security-auditor`: 0 hallazgos. |
| PostgREST wire/assert | PASS: HTTP + SDK; MFA 403, 120 admisiones, límite de cuota 429 y servicio restringido; `h3_quota_postgrest_assert.sql` PASS. |
| Concurrencia | `h3_invitation_reservation_concurrency_ok` en `h3_gate`, con correos/identidades sintéticas. |
| Revisión estática | Contrato de `v_key_id` PASS; `security-auditor` no halló vulnerabilidades en los cambios revisados. Los archivos SQL untracked no ofrecen diff Git confiable contra base. |
| Auth+MFA remoto / otros servicios remotos | No repetidos; PASS histórico conservado |

### Baseline, límites y siguiente gate

Rama `feat/h3req1-sync-20261002`; `HEAD` y `origin/desarrollo` permanecen en
`4eb4d877a50b012bb630a129bd0c74482c33be9c`, divergencia `0/0`, sin staged. Se preservó
el WIP amplio y el directorio anidado preexistente. El JIT v4 preflightó los 74 inputs con
solo dos sustituciones aprobadas; Node `v22.23.2`, SDK `2.109.0` e imágenes por digest.
No hubo npm ni egress.

El JIT v2 detectó `gateway_key.key_id = key_id`; la migración renombró la variable a
`v_key_id`. El JIT v3 pasó la migración pero su replay inválido conservó headers del
non-editor. Tras aprobación se movió el replay exacto al lado de la primera llamada
positiva; v4 ejecutó los nuevos bytes en PG17 limpio. Pasaron H2, H2 Pro (incluido rechazo
esperado del rollback guard), H3 default, baseline Pro, cadena H2→H3, cuotas, signed gateway
con replay 409, safe-suspend y baseline futuro contraído. PostgREST HTTP/SDK pasó con MFA
403, 120 lecturas admitidas, rate-limit 429 y acceso service-only; assert SQL y concurrencia
también PASS. Evidencia/recursos en el [manifiesto v4](../operaciones/manifiesto_jit_pg17_postgrest_h3req1_2026-10-05_v4.md).

El JIT v4 queda consumido. No hubo SQL Supabase remoto, Auth/correo remoto, grants,
Cloudflare, Git/CI remoto, push/PR/merge/deploy ni cleanup. Rollback integrado, UAT final,
CI protegido efectivo, criterios cliente/pilares/atestación restante y H3-CLOSE-03–08 siguen
pendientes; no se declara GO. Certification/Production siguen fuera del alcance.

## Continuación — remediación local de `p_first: null` — 2026-10-04

Esta continuación supersede el LOW y los hashes del ciclo payload-bound descritos
debajo; no cambia el veredicto general ni amplía permisos.

### Cambio implementado

- La RPC fuente `admin_get_course_queue_filtered` rechaza SQL `NULL` antes de alcanzar
  sus `LIMIT`, además de preservar AAL2/editor y el error `First must be between 1 and
  100`.
- `20261004_h3_admin_queue_first_null_guard.sql` actualiza forward-only la función ya
  aplicada: detecta la RPC pública directa o el wrapper `H3_QUOTA_WRAPPER_V1`, parchea
  solo su snapshot privado cuando corresponde y falla cerrada si falta la firma, el
  snapshot o el fragmento esperado. El `EXECUTE` usa la definición de catálogo de esa
  firma fija; no recibe datos de solicitudes.
- El dispatcher detecta el JSON `null` antes del cast y envía el sentinel entero acotado
  `0` a la RPC pública. Esa ruta conserva admisión de cuota, AAL2, RBAC y el error legacy;
  nunca entrega SQL `NULL` a `LIMIT`. HMAC payload-bound, allowlist, identidad y ruta
  `service_role` no se relajan.
- Se añadieron regresiones para la RPC directa, parche forward del snapshot privado,
  wrapper/cuota, prueba firmada AAL1 → AAL2 admin → AAL2 no-editor y nonces distintos
  cuando un error MFA confirmado ya consumió el nonce.

### Validación y límites

| Gate | Resultado |
|---|---|
| Docker `/opt/venv/bin/python -m pytest tests -q` | **287 passed, 4 skipped**, 1 warning de deprecación PyPDF2 |
| Credential scan de los archivos tocados | **PASS** |
| `git diff --check` | **PASS** |
| Revisión estática `security-auditor` posterior a las iteraciones | **0 hallazgos LOW+** |
| Harnesses SQL, PG17, PostgREST y wire | **NO EJECUTADOS**; requieren un JIT nuevo y hashes exactos |
| Auth/Supabase remoto, Git remoto, PR, deploy, promoción | **NO EJECUTADOS** |

Los SQL harnesses fueron editados pero no se presentan como validación runtime. Esta
revisión no cierra el gate H3 ni acredita `db_pre_request` activo. El SQL JIT, wire,
rollback integrado, UAT y aceptación D01–D14 permanecen pendientes.

### Hashes SHA-256 de los bytes actuales

Estos hashes identifican los archivos para una solicitud posterior; **no autorizan**
JIT, SQL, PostgREST ni una operación remota.

| Archivo | SHA-256 |
|---|---|
| `db/migrations/20260927_h3_admin_queue_facets_filter.sql` | `efabbb35e5fc8b9dc28ce3159ed3ed2328f20c74e4d8e02d2a1a222e8351600b` |
| `db/migrations/20261004_h3_admin_queue_first_null_guard.sql` | `012f994af8b44353e385e68b22dc1b15535e31f47f8f990716cbd726f1908711` |
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | `f1b4dce0dc0634585b5448514877b200924448c7e2dcc06441f1c3f66af78d0f` |
| `tests/test_h3_admin_queue_ux_contract.py` | `7586fd24b199791fcc72090150027dca7b1dfcb41bf3ef200d713fc9d2da23c8` |
| `tests/sql/h3_pg17_harness.sql` | `e1525daa888895619b477402b688e0a3409d2eba9d53c1e2c60f674f03aa61d3` |
| `tests/sql/h3_from_h2_pro_pg17_harness.sql` | `c5f45bd65427497050832b9c0f7c517e687ea9e1961fcdc0e8653f2932b8d379` |
| `tests/sql/h3_admin_quota_harness.sql` | `890464e81ae5bbbce9c3440d7318460c32970e8e5b89dc9693ef7aa30af7ca90` |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | `221e9100e9353db89e3fafd7f16fad4addcd9f958d8738b4d9a262e62819af01` |
| `.github/workflows/security-audit.yml` | `6af27960422d089d8de1042c0c580f54ea0a1c8235064bea59754a49e4b4304b` |

## Continuación posterior a `continua` — remediación payload-bound — 2026-10-04

Esta actualización supersede solo el estado de implementación LOW descrito en las
secciones históricas siguientes; los JIT y resultados anteriores conservan su alcance
original. El veredicto vigente permanece **`NO-GO_H3REQ1_DEVELOPMENT_FREE`**.

### Cambio implementado localmente

- Nuevo archivo ordenado después de la migración EXPAND existente:
  `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql`.
- `web/src/lib/supabase-transport.ts` solo admite destinos originales en la allowlist,
  firma metadata y un payload independiente que incluye nombre destino + JSON de args,
  y reescribe la llamada a `public.admin_signed_rpc`.
- El dispatcher SQL no usa SQL dinámico. Valida firma de metadata, firma del payload,
  igualdad entre el payload parseado y `p_args`, nonce/actor/vigencia/destino, llaves
  permitidas por destino y casts explícitos a la firma de cada RPC original. Luego
  ejecuta solo la rama estática aprobada. La identidad continúa siendo `auth.uid()`;
  las validaciones MFA/RBAC y la lógica/RLS de las RPC originales se conservan.
- El `db-pre-request` admite el dispatcher para `authenticated` y bloquea las RPC
  Admin legacy directas; los destinos service-role existentes se mantienen. La
  configuración PostgREST y las claves no se activan ni se aprovisionan aquí.
- Transición prevista: aplicar ambas migraciones EXPAND con JIT → desplegar BFF nuevo
  mientras los RPC originales siguen como compatibilidad → verificar wire → activar el
  gate estricto con aprobación separada → tras estabilidad, una fase CONTRACT futura
  puede revocar grants directos legacy. Rollback documentado: suspensión segura primero,
  rollback coordinado de BFF y función de pre-request a su contrato anterior mediante
  operación SQL aprobada; no borrar tablas/keys ni hacer rollback destructivo. Este
  procedimiento todavía no se ensayó.

### Validación realmente ejecutada

| Gate local | Resultado |
|---|---|
| `python3 -m pytest tests -q` en Docker | **285 passed, 4 skipped**, 1 warning deprecación PyPDF2 |
| `h3_supabase_sdk_headers_uat.mjs` | **PASS, 28 checks y 7 redirect cases**; prueba ambos HMAC y la reescritura |
| `h3_admin_bff_mock_uat.mjs` | **PASS, 60 checks/10 casos de cuota** |
| `h3_admin_auth_error_uat.mjs` | **PASS, 7 checks** |
| `h3_admin_invite_edge_uat.mjs` | **PASS**, éxito/replay/CORS/errores/concurrencia/expiración |
| `npx tsc --noEmit` | **PASS** |
| `npm run lint` | **0 errores, 9 warnings existentes** |
| `h2_web_mock_smoke.sh` | **PASS**, build y ruta legacy contra fixture local aislada |
| Credential scan / Node syntax / `git diff --check` | **PASS**; scanner ejecutado en modo `files` sobre los archivos regulares del snapshot, como root |
| PG17/PostgREST firmado y wire | **NO EJECUTADO**; exige nuevo JIT con hashes finales |
| UAT completo, rollback integrado, CI/GitHub y promoción | **Pendiente**, aprobaciones separadas |

No se cargaron secretos ni se consultaron servicios remotos. El intento amplio `pytest
-q` desde la raíz recogió `scripts/maintenance/test_inst_insert.py`, que exige
`FREE_SUPABASE_URL` durante collection. Al excluirlo quedó una prueba legacy independiente
fallida (`scripts/shared/test_db_compatibility.py::test_db_client`, atributo `use_local`
ausente); el gate canónico `pytest tests -q` terminó PASS. El build inicial con
`local.example.invalid` registró el fetch esperado de DNS fallido; no se cuenta como
PASS; el smoke build posterior contra fixture local sí pasó.

Nota de reproducibilidad del escaneo: el snapshot Docker no contiene `.git`, por lo que
`scan_credentials.sh --tree` no es un modo válido allí (`git ls-files` no puede enumerar
archivos). Para el PASS se enumeraron archivos regulares con `find`, excluyendo solo
`.git`, `node_modules`, `.next`, `out` y `__pycache__`, y se invocó el modo `files` del
scanner por archivo como root. Una ejecución previa de `--tree` en ese snapshot imprimió
un falso mensaje PASS y no se considera evidencia.

La revisión inicial `security-auditor` quedó pendiente en ese corte histórico. La revisión
estática posterior sobre los bytes actuales cerró sus LOW/MEDIUM iterativos con **0
hallazgos LOW+**; no es validación runtime ni waiver. El NO-GO persiste hasta los gates
JIT/UAT. Owner: Romel; implementadores: Backend/DB Security; objetivo `2026-10-11`.

### Hashes del corte payload-bound anterior — históricos, no usar para JIT actual

Orden de migración previsto (léxico): EXPAND existente → follow-up payload-bound. Los
hashes son para revisión/JIT posterior; no conceden permiso para ejecutar.

| Archivo | SHA-256 |
|---|---|
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql` | `e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c` |
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql` | `2e1d12423cfab9a48aa3a79ff9c7283813fc81d52787003726b48879ed4dee45` |
| `web/src/lib/supabase-transport.ts` | `0b4043403c294467f370b5adfe186cf97452efe1c1d031ae07e0ea3d10a9652f` |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | `8e910d715055b6328b36782e06136ce88ebf369c659c63413c902d2287dc8b6f` |
| `tests/h3_admin_quota_postgrest.mjs` | `7b1770a533773ef9ca7be2bfb9ab24994e25895857c37a50b958fcdbd383be3e` |
| `tests/h3_supabase_sdk_headers_uat.mjs` | `f4fb6f059b30309ae5e861dc6023314432f15cacfb966c981cf3cf9b3a1a31e3` |
| `tests/test_supabase_credentials_contract.py` | `7beaebb3226f81da2f1591cdd16d335512eb60167296b7bba597fe322027447a` |
| `tests/test_admin_invite_edge_contract.py` | `5a08f3fdac27ab0973e6d4293bbbfb9362aedf2f9657874f42d6781b75d4d33a` |
| `.github/workflows/security-audit.yml` | `00d7720785d99f07152ea50d103c7f2e0a2a4bfdeccfd0767abb58eadb1b2824` |

## Candidato y preservación

- Worktree: `/home/romel/src/studiamatch-h3req1-sync-20261002`; rama `feat/h3req1-sync-20261002`; `HEAD` baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`. HEAD no identifica el WIP.
- No se stageó ni se creó commit. El worktree conserva cambios tracked y untracked preexistentes y nuevos; no se revirtió ni sobrescribió el WIP. Los dos archivos literales de plantilla vacíos permanecen intactos. El checkout original `/home/romel/src/studiamatch` no se editó; su propio WIP se dejó intacto.
- Docker: `h3req1-candidate-docker-20261004`, bind de solo lectura al candidato y snapshot de trabajo en `/workspace`; el contenedor `studiamatch-dev` no se tocó. No se montaron `.git`, `.env.local`, `.env.gitprod` ni secretos. `.env.example` sanitizado se leyó aparte, read-only; SHA-256 `1b9903eb6fb8719659b1d17c697bf6165a64804219b866b66f0b6ee221e98576`.
- Manifiesto fuente agregado: SHA-256 `1b36634e6a916df737e6314dbb6f786144cbe28958800208becd4502fe1512b4` sobre 579 archivos regulares ordenados. Excluye `.git`, `.env*` (incluido `.env.example`, cuyo hash se registra aparte), dependencias/caches/builds, `.openchamber`, `.obsidian`, `.codex` y las carpetas de artefactos UAT grandes `h3-expanded`/`h3-invitation-flow`. Esta nota se excluye para evitar digest circular. No equivale a commit ni a candidato congelado.

## Autoridad y alcance

Se conserva la evidencia PASS Auth+MFA remota del 2026-09-27; no se repitieron reset, reenrolamiento, login remoto ni cambios de identidad. La atestación de aceptación cliente y la ampliación H3 autorizan implementación/validación local, no DB/Auth remota, Cloudflare, Git remoto, despliegue, rollback remoto ni promoción. La fuente privada no se incorpora ni se afirma haberla consultado.

Se implementó localmente el gateway de RPC BFF: firma HMAC con clave separada de cuotas, límites Durable Object 120 lecturas/min y 30 escrituras/min por actor, firma ligada a proyecto/método/RPC/actor/tiempo/nonce/key-id, y fail-closed si falta configuración. El quinto JIT confirmó HTTP 403 tras corregir `DETAIL.headers`; el runner sobre esos bytes observó un desacuerdo de código. Tras un nuevo `continua`, el hook/harness/runner ahora distinguen firma completamente ausente (`rpc_signature_required`) de prueba parcial/inválida (`rpc_signature_invalid`), siempre 403. Esta revisión solo pasó estáticamente; falta un nuevo JIT.

## Validación ejecutada en Docker

| Área | Resultado real |
|---|---|
| Dependencias web | `npm ci`: PASS (paquetes instalados; el conteo no quedó conservado en la evidencia de consola) |
| TypeScript | `npx tsc --noEmit`: PASS, sin salida |
| ESLint | PASS de proceso, 0 errores; 9 warnings existentes: 7 hooks en `HomeContent.tsx` y 2 `_e` no usados |
| Auditoría npm | `npm audit --include=dev`: 0 vulnerabilidades; `npm audit --omit=dev`: 0 |
| Pytest | `python3 -m pytest -q -rs tests`: **285 passed, 4 skipped**, 1 `DeprecationWarning` de PyPDF2. Los cuatro skips requieren `RUN_SUPABASE_INTEGRATION_TESTS=1` y Supabase live |
| Escritores H2 | `python3 scripts/maintenance/h2_scan_unauthorized_writers.py`: PASS |
| Credenciales | Barrido de archivos del candidato y fixtures sanitizadas con `scan_credentials.sh`: PASS; se excluyeron `.git`, secretos/env locales, caches y estado personal |
| SDK/BFF | `h3_supabase_sdk_headers_uat.mjs`: PASS 28 checks/7 redirects; `h3_admin_bff_mock_uat.mjs`: PASS 60 checks/10 casos de cuota; sin red a Supabase |
| Auth/invitación Edge | `h3_admin_auth_error_uat.mjs`: PASS 7; `h3_admin_invite_edge_uat.mjs`: PASS (éxito/replay, CORS, clasificación, ambigüedad, concurrencia y expiración); typecheck semántico Edge: PASS |
| Cuotas/suspensión | `h3_admin_quota_uat.mjs`: PASS, 25 solicitudes concurrentes/10 admitidas, límites 120/30; `h3_admin_safe_suspend_uat.mjs`: PASS 5 casos/8 aliases |
| Worker real local | Node 22.22.0 + Miniflare 4.20260730.0 + esbuild 0.25.10: quota DO PASS (25 concurrentes, persistencia tras reinicio); Pages/workerd safe-suspend PASS (3 rutas Admin suspendidas, 3 públicas, 8 aliases rechazados, cookies limpiadas) |
| Build estático | `h2_web_mock_smoke.sh`: `h2_web_mock_smoke_ok`; build normal contra fixture HTTP local exportó `/courses/inst-a/curso-legacy-visible/` y verificó el nombre/detalle real, no fallback. Artefacto: 126 archivos, SHA-256 agregado `38f5b3a4faa9d118fb301537daa83f48ca9cab75c9d59cfd0641cf2fd3ed4ef0`; ruta detalle SHA-256 `dc0a04381502095658eef13ec8350b4ca4076be4c03b04550f48d7b6b6c4552c` |
| Build mock | `npm run build:mock` con `NEXT_PUBLIC_H3_MOCK_URL=http://127.0.0.1:3211`: PASS; generó ruta `/courses/mock/mock-course/` |
| Sintaxis/control | `node --check tests/h3_admin_quota_postgrest.mjs`, `bash -n` de los scripts SQL shell y `git diff --check`: PASS. Ambos workflows parsean como YAML (11 jobs en `security-audit.yml`) |

`actionlint` y `shellcheck` no estaban instalados en el contenedor; no se reportan como PASS. `h3_admin_quota_postgrest.mjs` pasó `node --check`, pero su ejecución wire en PostgREST 13 falló: RPC Admin directa sin firma obtuvo HTTP 500/PGRST121 en vez del 403 esperado. El fixture SQL posterior no se ejecutó. Tampoco se ejecutaron `h3_local_uat.mjs` ni `h3_invitation_uat.mjs`, que requieren el harness/DB local y resets de fixtures.

## Ejecución JIT local PG17 — 2026-10-04

El usuario aprobó el alcance exacto del manifiesto de hashes fijado en esta nota
(snapshot de solicitud SHA-256 `193c267671553880399a1dcc0bdb4f279347579062f6827cb334bbc4b166ae1d`).
Antes de ejecutar, se verificaron sin mismatch los 41 hashes: 40 archivos SQL copiados
al contenedor y el runner Node contra el origen readonly y `/workspace`. PG17 usó la
imagen fijada, DB `h3req1_rpc_gateway_jit`, tmpfs, sin volumen ni puerto publicado. El
primer `psql` omitió `-h/-p` y falló al buscar el socket local; no ejecutó SQL. La
repetición por TCP loopback a `127.0.0.1:35432` sí ejecutó:

| Paso | Resultado |
|---|---|
| `h3_from_h2_pro_pg17_harness.sql` | PASS, marker `h3_from_h2_pro_pg17_harness_ok`; avisos de columnas/índice existentes esperados por deltas idempotentes |
| `h3_admin_quota_harness.sql` | PASS, marker `h3_admin_quota_harness_ok` |
| Aplicación de `20261004_h3_admin_rpc_signed_gateway_expand.sql` desde el harness firmado | **FAIL** en parseo PL/pgSQL: `syntax error at or near "FROM"`, línea 48 del cuerpo; `pg_catalog.substring(request_path FROM ...)`. `psql -v ON_ERROR_STOP=1` detuvo el harness y la transacción `BEGIN` se revirtió al cerrar la conexión |
| Harness de gateway firmado restante | No ejecutado |
| `h3_safe_suspend_harness.sql`, fixture/assert PostgREST, contenedor PostgREST y wire runner | No ejecutados; se detuvo el ciclo al encontrar el defecto SQL |

Contenedor PG17 creado: `h3req1-jit-pg17-20261004-a1`, ID
`f63fa8dfe6abcfa001704d6b6a012782613e9a4b095e0f605b29c78c61f89fad`; se detuvo y
eliminó después del fallo. No se creó el contenedor PostgREST. No se tocaron los
contenedores históricos detenidos, ni Supabase remoto, Auth, Git remoto o Cloudflare.
La corrección local cambió la migración fuera de la huella aprobada; por ello el primer
JIT no autorizó reejecución. Hash corregido `2b474ba6b3b944584126b90ac60efddf8174e22041ec4005a5a5a7e07a309df7`.
El segundo JIT queda registrado abajo.

### Segundo intento JIT — migración corregida

El usuario aprobó el manifiesto actualizado, snapshot SHA-256
`a32e5d0aae75f767e1fe05da8805624da8c1ebd2d4b494c29873bb6c6ea7efbc`. Se revalidaron
los 41 hashes; los 40 SQL se copiaron y comprobaron en una DB nueva. Baseline H3 Pro/H2
y cuota pasaron; la migración gateway corregida aplicó/commiteó. El harness firmado
falló antes de sus assertions en la primera expresión `pg_catalog.extract(epoch FROM
...)` (`h3_admin_rpc_signed_gateway_harness.sql`, línea 24), con error de sintaxis cerca
de `FROM`; no se continuó con sus casos. El test source fue corregido a
`pg_catalog.date_part('epoch', clock_timestamp())` en las tres ocurrencias. Hash nuevo
del harness: `20d77ae009c432bb89d16361587f82e88892815059f4a09759994b4a0801c4cd`. Después
del cambio: pytest completo **285 passed/4 skipped**, TypeScript PASS, credential scan y
`git diff --check` PASS. No se repitió SQL/PostgREST con el harness nuevo.

Contenedor PG17 del segundo intento `h3req1-jit-pg17-20261004-a1`, ID
`0321aba032d05c639fe57376437a46b94c99bbe5d22847bcb9eb8b7abc9584e5`, se detuvo y
eliminó. No se creó PostgREST ni se tocaron contenedores históricos/remotos. El JIT dos
no autoriza estos bytes actualizados; se requiere tercero con hashes nuevos.

### Tercer intento JIT — harness con `date_part`

El usuario aprobó el snapshot de manifiesto SHA-256
`3d58a7eeb48ff2e724cee3240284bfe6901cd93e23ce3dddae64cb7cbd7abc8f`; se verificaron
de nuevo los 41 hashes y los 40 SQL copiados. Baseline, cuotas y migración pasaron.
El harness firmó correctamente, rechazó replay comprometido, permitió reintento tras
rollback, y pasó checks de actor/método/destino. Falló en el caso de HMAC inválido con
`could not determine polymorphic type because input has type unknown` en la conversión
`pg_catalog.to_jsonb(:'gateway_issued_at')`, línea 149/psql línea 150. `ON_ERROR_STOP`
paró el harness antes de los casos de expiración, RPC legacy, service-role/anon y
PostgREST. El contenedor `h3req1-jit-pg17-20261004-a1`, ID
`68b80cb02c5840209b97ed5699339ae8c670002b5116bfb937e1fcf1cc22795e`, se eliminó; no
se creó PostgREST.

Se corrigió localmente el literal con cast explícito a `TEXT`; hash actual del harness
`e13e338677644967503b60411c2e4ac2aac1079551029d806ad0e23e879b5f4c`. El test
contractual actualizado y pytest completo vuelven a pasar: **285 passed/4 skipped**;
TypeScript, credential scan y `git diff --check` PASS.

### Cuarto intento JIT — PostgREST wire

El usuario autorizó el manifiesto, snapshot SHA-256
`f5030e5ee7a497c5e3dce4d93f896606ae663d5046c9406701dbd76485c8c3fe`; se validaron los
41 hashes, imágenes y los 40 SQL copiados. Baseline (`h3_from_h2_pro_pg17_harness.sql`),
cuotas, harness firmado completo (`h3_admin_rpc_signed_gateway_harness_ok`) y
safe-suspend (`h3_safe_suspend_harness_ok`) pasaron. PostgREST v13.0.7 inició conectado
por loopback al PG17 tmpfs; el fixture cargó. En `tests/h3_admin_quota_postgrest.mjs`,
la primera llamada directa sin firma a `admin_current_user_role` respondió **500** en vez
de 403. Log de PostgREST: `PGRST121`, `Invalid JSON value for DETAIL: '{"status": 403}'`;
v13 exige objeto DETAIL con claves obligatorias `status` y `headers`. La misma forma
aparece en varios `RAISE SQLSTATE 'PGRST'` con status-only en la migración. No continuó
con las siguientes rutas, SDK, cuota wire ni `h3_quota_postgrest_assert.sql`.

Contenedores del cuarto intento, ambos detenidos y eliminados tras el fallo:
`h3req1-jit-pg17-20261004-a1` ID
`1f2731c35589ca86576ad397e9211fb1937bae65140cd956e17df4f80a61f31c`; y
`h3req1-jit-postgrest-20261004-a1` ID
`4b852dee97e366dc69a8d35b899036e56e47c00840277148a50793d19845984a`. No se ejecutó
assert SQL posterior ni se tocaron Supabase/Auth/Git/Cloudflare o contenedores
históricos.

### Corrección local posterior al cuarto JIT

Tras `continua`, la migración se corrigió sin ejecutar SQL: los diez bloques
`RAISE SQLSTATE 'PGRST'` incluyen ahora `status` y `headers`; los dos errores 503
mantienen `Retry-After: 30`. El test contractual recorre cada bloque y falla si falta
cualquiera de ambas claves, además de comprobar que las dos ramas 503 preserven
`Retry-After: 30`.
Hash actual de migración
`647cbcd408aa66e5dee93b1990d47d8c8e597e34147a083bf112afbdc23e5aec`; test contractual
`670a942a3fc08dacfaee06f64851f432cf709356763f4e37f317f72abc240959`.

Validación en Docker después del cambio: test dirigido **43 passed**; pytest completo
**285 passed, 4 skipped** (Supabase live opt-in); TypeScript PASS; credential scan PASS;
`git diff --check` PASS. Security-auditor no detectó HIGH/CRITICAL; reportó un hallazgo
LOW porque el test original solo comprobaba presencia de Retry-After. Se endureció para
exigir exactamente ambas respuestas 503 y la segunda revisión confirmó remediación, sin
nuevos hallazgos. Luego se ejecutó el quinto JIT, que verificó HTTP 403 pero encontró el
desacuerdo del cuerpo descrito abajo; no se ejecutaron más aserciones.

### Quinto intento JIT — PostgREST con `DETAIL.headers`

El usuario autorizó el snapshot SHA-256
`173b087e075166f0cce9587e7c10a3b4b5abe69c94ff7754e252d7a4b519c1af`; se verificaron
41 entradas: 40 inputs sin cambios y la migración corregida
(`647cbcd408aa66e5dee93b1990d47d8c8e597e34147a083bf112afbdc23e5aec`). Baseline, cuotas,
gateway firmado, safe-suspend y fixture PostgREST pasaron. PostgREST 13 devolvió **HTTP
403** para la petición Admin sin firma, resolviendo el defecto PGRST121. Luego falló en
`tests/h3_admin_quota_postgrest.mjs:61`: payload `rpc_signature_invalid`, expectativa
`rpc_signature_required`. Se detuvo antes del resto de aliases/SDK/cuota HTTP y del
assert SQL.

Contenedores del quinto intento, detenidos y eliminados: PG17
`h3req1-jit-pg17-20261004-a2`, ID
`a1296e4c87e262a11efdd6a1c3733b5b32e7d5fe0599b8208b7dc62ffff038ee`; PostgREST
`h3req1-jit-postgrest-20261004-a2`, ID
`932486ff1bb77c54013c74bcbd4d1ac9b041746bd638878cf3e4cbe2878395a8`. No se tocaron
contenedores históricos ni servicios remotos.

### Corrección local posterior al quinto JIT

Tras `continua`, se añadió un branch explícito para las cinco cabeceras de firma
ausentes; deja sin cambios el rechazo de cabeceras parciales, malformed o HMAC incorrecto.
El harness SQL comprueba ambos códigos/status y `headers`; el wire runner añade una
llamada con prueba parcial; el test contractual protege el branch. Hashes actuales:
migración `e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c`, harness
`f281996d647f12ccba73371eb95df02698d09144e6c836c080fb43c3928e8bed`, runner
`89d02dfc1f7795567d2e4f766bcfdd58e307f9e2c719975b06de4744d137c011`, test
`ef1df0ec29a6be8707715ad998e349d18d8d781f74d8617f65e935da8cf92f06`.

Validación en Docker: pytest completo **285 passed/4 skipped**, TypeScript PASS,
`node --check` runner PASS, `py_compile`, credential scan y `git diff --check` PASS.
Security-auditor encontró **0 HIGH/CRITICAL** y un LOW residual no introducido por este
ajuste: la firma no incluye parámetros/cuerpo. El token firmado se crea server-side y no
se observó bypass; el riesgo teórico requiere exposición de la prueba antes de consumir
nonce y podría permitir alterar argumentos. Owner/disposición humana quedan pendientes;
no se concede waiver ni se declara GO. La versión actual no se ha ejecutado en DB.

## Estado H3-CLOSE-01 a H3-CLOSE-08 — corte histórico previo a payload-bound/NULL

La matriz vigente está en el traspaso enlazado arriba. No reabrir LOW de parámetros
sin firma: se remediaron localmente. Runtime/rollback/CI/remoto continúan pendientes.

| Gate | Estado del corte |
|---|---|
| H3-CLOSE-01 baseline/candidato | Parcial PASS: rama/HEAD y aislamiento confirmados; WIP íntegro; digest reproducible sin evidencia circular. Aún no hay candidato integrado/congelado |
| H3-CLOSE-02 gateway/cuotas | NO-GO: el contrato ausente/parcial está corregido y pasa pruebas estáticas; falta revalidar la versión actual en PG17/PostgREST y completar wire/assert SQL |
| H3-CLOSE-03 rollback/recuperación | Parcial: piezas safe-suspend Pages/workerd pasan; drill integrado Pages+Edge+SQL/datos/cookies y recuperación no ejecutado |
| H3-CLOSE-04 mantenimiento | Parcial: Romel owner de revisión/reemplazo `braces` para `2026-11-03`; facetas `priceMin` quedan fuera de H3 con Romel para `2026-11-03`. Owner de los 2 warnings no usados, PyPDF2 y 4 live skips pendiente; sin waiver |
| H3-CLOSE-05 CI/protección efectiva | Bloqueado remoto: YAML y pruebas locales de allowlist pasan; actionlint/shellcheck no ejecutados y required checks/review efectivos no acreditados |
| H3-CLOSE-06 aceptación local | Parcial; discriminación ausente/parcial pasa pytest/TypeScript/Node syntax; runtime para los nuevos bytes y UAT visual/onboarding completos pendientes |
| H3-CLOSE-07 integración/despliegue Development | No ejecutado: faltan lecturas y permisos exactos para Free, Auth, Pages/Worker/Edge, secretos, Git y deploy |
| H3-CLOSE-08 D01–D14 remoto | No ejecutado; el PASS Auth+MFA histórico no sustituye la matriz Development actual |

La transición sigue `expand -> compatibilidad -> deploy -> contract`: código y EXPAND propuestos localmente, compatibilidad limitada a mocks/UAT local; sin DB remota aplicada ni deploy. Contract, rollback integral y recuperación permanecen pendientes. No se tocó Certification ni Production.

## Próximo ciclo requerido — propuesta histórica supersedida

La propuesta siguiente no cubre payload-bound, guard NULL ni harness nuevos. No
ejecutarla ni renovar únicamente tres hashes: preparar manifiesto nuevo completo.

El nuevo `continua` completó la distinción de cabeceras ausentes/parciales. La versión
actual pasó pruebas locales y review estática (0 HIGH/CRITICAL); quedan el LOW de
parámetros no ligados a HMAC sin disposición humana, y la revalidación PG17/PostgREST.
Los hashes actuales se fijaron arriba; antes de SQL debe aprobarse el JIT nuevo. No es GO.

### Sexto JIT propuesto (pendiente de aprobación)

Se conservarían 38 de los 41 inputs SQL/runner del quinto JIT; se reemplazan solamente
la migración (`e80e236348c2eefe79035c6f6ea5e22bc5dea194555d07a1f1b5a8b41a02876c`), el
harness firmado (`f281996d647f12ccba73371eb95df02698d09144e6c836c080fb43c3928e8bed`) y
el wire runner (`89d02dfc1f7795567d2e4f766bcfdd58e307f9e2c719975b06de4744d137c011`).
El contrato Python actual es `ef1df0ec29a6be8707715ad998e349d18d8d781f74d8617f65e935da8cf92f06`
y ya pasó pytest; no forma parte de SQL. Mismas imágenes PG17/PostgREST 13.0.7 por
digest, DB `h3req1_rpc_gateway_jit_a3` en tmpfs sin publicación de puerto; nombres
`h3req1-jit-pg17-20261004-a3` y `h3req1-jit-postgrest-20261004-a3`. Secuencia completa:
baseline → cuotas → harness firmado → safe-suspend → fixture → PostgREST wire → assert
SQL; detener ante cualquier fallo y limpiar solo los dos contenedores a3. No remoto/Auth/
Git/Cloudflare/deploy, y no se toca el hallazgo LOW ni se entiende su aprobación como
waiver. Requiere JIT humano separado y explícito.

### Manifiesto del quinto JIT — autorizado y ejecutado

La autorización cubrió repetir la secuencia local previamente fijada con una sustitución:
las otras 40 entradas (39 SQL/harness y el runner HTTP) conservan los hashes históricos
verificados en la tabla del cuarto JIT; `20261004_h3_admin_rpc_signed_gateway_expand.sql` se reemplaza
por SHA-256 `647cbcd408aa66e5dee93b1990d47d8c8e597e34147a083bf112afbdc23e5aec`.
La regresión local está en
`tests/test_supabase_credentials_contract.py`, SHA-256
`670a942a3fc08dacfaee06f64851f432cf709356763f4e37f317f72abc240959`; ya pasó pytest y
no hace falta reejecutar SQL para ella. Imágenes: PostgreSQL 17
`postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` y
PostgREST 13.0.7
`postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`.
Nombres usados: `h3req1-jit-pg17-20261004-a2`,
`h3req1-jit-postgrest-20261004-a2`, DB `h3req1_rpc_gateway_jit_a2`, tmpfs, sin puertos
publicados ni volúmenes. Se ejecutó baseline, cuotas, harness firmado, safe-suspend y
fixture PostgREST con `ON_ERROR_STOP`; el wire runner alcanzó HTTP 403 y paró por el
código de error inesperado antes del assert SQL. Los dos contenedores fueron detenidos
y eliminados. Autorización humana: snapshot SHA-256
`173b087e075166f0cce9587e7c10a3b4b5abe69c94ff7754e252d7a4b519c1af`. No hubo operaciones
remotas ni se tocaron contenedores históricos.

### Alcance ejecutado bajo JIT (cuarto intento)

Crear un PostgreSQL desechable `h3req1-jit-pg17-20261004-a1` desde
`postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`;
almacén en tmpfs, sin bind/volumen persistente, puerto publicado ni credenciales reales.
Crear PostgREST desechable `h3req1-jit-postgrest-20261004-a1` desde
`postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228`,
con escucha solo local y `db_pre_request=public.h3_admin_rpc_signed_gateway_pre_request`.
La DB nueva se llamará `h3req1_rpc_gateway_jit`. Se copiarían únicamente `db/` y
`tests/sql/` del snapshot readonly del candidato al contenedor, sin `.env*`, `.git` ni
evidencias privadas. El cliente Node corre en el contenedor candidato dedicado contra
`127.0.0.1:3234`; PostgreSQL escucha en `127.0.0.1:35432`. Se usarán exclusivamente
JWT, publishable key, HMAC gateway y filas sintéticas locales.

Secuencia autorizada: `h3_from_h2_pro_pg17_harness.sql` (incluye baseline H2 Pro y
migraciones H3); `h3_admin_quota_harness.sql`; `h3_admin_rpc_signed_gateway_harness.sql`;
`h3_safe_suspend_harness.sql` (aplica dos veces la suspensión solo en DB desechable,
verifica y restaura los grants previos de fixture); `h3_quota_postgrest_fixture.sql`;
runner HTTP `h3_admin_quota_postgrest.mjs`; y `h3_quota_postgrest_assert.sql`. No se
ejecutará el workflow GitHub ni se usarán las otras DB/servicios/contenedores existentes.
Resultado: baseline, cuotas, gateway firmado y safe-suspend PASS; PostgREST runner falló
en la primera aserción de 403. Los dos contenedores nombrados arriba fueron detenidos y
eliminados; no se tocaron los contenedores históricos detenidos listados en Docker.

La tabla siguiente conserva los 41 inputs exactos autorizados y verificados en el
cuarto JIT; es evidencia histórica de esa ejecución, no el manifiesto vigente del código
tras el fix. Los nombres son rutas relativas a la raíz del worktree candidato:

| Archivo | SHA-256 |
|---|---|
| `tests/sql/h2_pro_pg17_harness.sql` | `676a149546d8f3ff045d7d4332eedeefe343a8ef25375cd72e906ed6d1f26bfe` |
| `tests/sql/h3_from_h2_pro_pg17_harness.sql` | `b996b46762ee249326bdd8a4474307829f75fb8470175201c577416d458cafa0` |
| `tests/sql/h3_admin_quota_harness.sql` | `cc96f6460dee925096899af8ed48af2c0a3b0f54e546f992fe7803f45d754552` |
| `tests/sql/h3_admin_rpc_signed_gateway_harness.sql` | `e13e338677644967503b60411c2e4ac2aac1079551029d806ad0e23e879b5f4c` |
| `tests/sql/h3_safe_suspend_harness.sql` | `c1dcfef828b836e6627530127eb66a157db1df1437ad923a06f6c64e2c6782f1` |
| `tests/sql/h3_quota_postgrest_fixture.sql` | `307704d2734506902b8974beb36fb29c5dd35d36f797e70c9bd2f27070b228ed` |
| `tests/sql/h3_quota_postgrest_assert.sql` | `f0f2285b23bb4fddb7e5fdc4aa2ee409d822524fc1ed110abd42e6ff11a6aad9` |
| `tests/h3_admin_quota_postgrest.mjs` | `bef6feda9d1f7bd1317080014dbe8dc6882928020f23295a412d42b368a6d256` |
| `db/migrations/20260827_h2_pro_expand_schema_compat.sql` | `e3b8665e0ceafc590a41390d3c206fc1e9846332ddd5cf9385f0a704ffabb577` |
| `db/migrations/20260827_h2_pro_seed_editorial_field_definitions.sql` | `ecf46e71b6b261fdba8a8fee0cab76a3d4d57eefb1b097f4496bac9c717f2d17` |
| `db/migrations/20260827_h2_pro_backfill_editorial_state.sql` | `0118a17cf1e9fbfa001f67d07e92770f5a8787a14722e1dee992592f3bcee3c3` |
| `db/migrations/20260827_h2_pro_capture_legacy_cohort.sql` | `4212a94e59df8a0702176265848f16746486299852ab94267247f26f50e393f9` |
| `db/migrations/20260827_h2_pro_contract_public_reader.sql` | `86ce2998bdfb2e0a91ebc9f7ec50f88b285de60ed8dbe538ead21611df132da3` |
| `db/migrations/20260827_h2_pro_rollback_public_reader_contract.sql` | `b0ad29f6bf092b723936589d5902ee1081499a1278d054320f35933fe2a46f40` |
| `db/migrations/20260827_h2_pro_contract_legacy_cohort.sql` | `62db91e741ab448ec057cc7cea41bb813535f26b762d38ef66a120210fc20c28` |
| `db/migrations/20260828_h3_admin_auth.sql` | `9a962d01cb3969f6442cac44e3947e7591e93015c4383d245fb3d1f9a1beb314` |
| `db/migrations/20260830_h3_expanded_contract.sql` | `387c6247976e92dcbaeff3b53ffa59a9f3f989dd8a50ded1ff61df4721769e27` |
| `db/migrations/20260828_h3_admin_editorial_rpc.sql` | `ee8d5b1458da1291ec8b1e4f943728af82cd3cef42a5aee36d490ef8cbda9726` |
| `db/migrations/20260828_h3_admin_editorial_reader_rpc.sql` | `2783ad358c035db03456b8934e2fa598a4af8272d3715404a8d3c00189e3b63b` |
| `db/migrations/20260828_h3_admin_course_queue_view.sql` | `96f2ffffdbae1ea3f85ff32ade1a2987821c9e837dd771e1a188165cf377caf9` |
| `db/migrations/20260828_h3_admin_queue_rpc.sql` | `e4fd2ff6733667520916d136eb5d657778c27e5f291e74613a02a595c4bbfb0c` |
| `db/migrations/20260829_h3_rbac_users.sql` | `b1f96c366f506d52ce11fcf6ef64759ba543af63304da124af0dc10b21fd24c7` |
| `db/migrations/20260902_h3_pr_contract.sql` | `6c22319a66c10e323a6fa4ed1fdbd612a609f8057c6e952a8601cb17c46a4e74` |
| `db/migrations/20260903_h3_rbac_contract_fix.sql` | `4274e114882fae1deb3039036c612bdc682d59921833c297ed691e87c0440797` |
| `db/migrations/20260918_h3_invitation_flow_persistence.sql` | `0837d448d8552feb62bb3ab63701123e2449a00ffdcc84dc776849e879030f77` |
| `db/migrations/20260919_h3_invitation_auth_token_delta.sql` | `701f5c74ff923765fb39efa1605600cb58c93c8caa820b7d49a17fba73e8275d` |
| `db/migrations/20260920_h3_invitation_edge_runtime.sql` | `46f7d24ac9c8af033ebd84b9ede44c27241382b9cba3fe179ec745b9a25f9188` |
| `db/migrations/20260921_h3_invitation_onboarding_rpc.sql` | `138e2d3690ec880c51f3834e42fa33ebce0080c6ad9e08b5fe34b8df76de84f2` |
| `db/migrations/20260924_h3_onboarding_rbac_hardening.sql` | `e466bf1f7968d71ce715724779cc4bd37818f6462021724d01ad48a9bfb1a857` |
| `db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql` | `9a5c5d46bca6b4dec438bc6ae63036641423fee95b73e188237ef8ba230b2978` |
| `db/migrations/20260925_h3_legacy_member_creation_guard.sql` | `bf7b240d76452105753883523428f6cfa4448bdb96c880b2f4aca467db0fe678` |
| `db/migrations/20260925_h3_admin_members_onboarding_reader.sql` | `0a9a0b5b694b9caef66da5f6e0d5a45d77bff9029e31b0ede54a5026c14a9d0d` |
| `db/migrations/20260927_h3_admin_queue_facets_filter.sql` | `3dcbc296f50f25539edf3ddc6dbf171517070f6d673829ad548638148fc1f47c` |
| `db/migrations/20260927_h3_publication_visibility_contract.sql` | `2b02df3f9ab5736da292d5b8653ca567111cd82705ada182b5baa8085b21e1aa` |
| `db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql` | `a1b9eaa799d7cc760c84e1df2f66b362ebf1b0556a9f446222f2f9cbea99cd44` |
| `db/migrations/20261001_h3_invitation_reservation_compensation.sql` | `1001c059b951eaa907016e31be08bef9f3e0a7835f30ea2cac5227a123927270` |
| `db/migrations/20261001_h3_course_editorial_audit_availability.sql` | `590d4c6e177ded33384b746f187a3476af663db6aef8d5c789d4d7bcad093717` |
| `db/migrations/20261002_h3_admin_quota_expand.sql` | `d839f7f760bdb12025297a24e09b547cf4f0b5989d3c0142835978083be9bb67` |
| `db/migrations/20261002_h3_admin_quotas.sql` | `7ea746ca73f2acee31956e59d490083c4fbfcaebf51941d4c6cb52618c906619` |
| `db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql` | `2b474ba6b3b944584126b90ac60efddf8174e22041ec4005a5a5a7e07a309df7` |
| `db/rollback/h3req1_safe_suspend.sql` | `09fcd8f6a5b9590f2e8db20f00c0fd9244ffd6a4a8db714c3c2837f04c22369d` |

`security-audit.yml` fija el mismo PostgREST digest; su SHA-256 en este snapshot es
`2572bac539d55f387c8313f24d1d37215da0389bca695a78df0df393071b85be`. Los únicos
SQL target son el PostgreSQL nuevo: el baseline recrea `public`/`private`, crea roles
locales si faltan, carga fixtures y ejecuta grants sobre roles y objetos sintéticos.
No se autoriza conexión a ningún proyecto Supabase.

La autorización humana del cuarto intento cubrió exclusivamente crear/ejecutar esos dos contenedores,
la DB nueva y esa lista cerrada de harness/migraciones/runner, comprobar los hashes
antes de ejecutar y limpiar solo los dos contenedores nuevos con los nombres indicados.
No autoriza otros harnesses, contenedores existentes, Supabase, Auth/correo real,
credenciales reales, Git, Cloudflare, deploy, rollback remoto, Certification o
Production. Esta tabla conserva exactamente los 41 inputs autorizados en el cuarto JIT;
no representa la migración actualizada tras descubrir PGRST121. Su migración ejecutada
tenía hash `2b474ba6b3b944584126b90ac60efddf8174e22041ec4005a5a5a7e07a309df7`; la actual
es `647cbcd408aa66e5dee93b1990d47d8c8e597e34147a083bf112afbdc23e5aec` y el test nuevo
es `670a942a3fc08dacfaee06f64851f432cf709356763f4e37f317f72abc240959`. No son bytes
cubiertos por el JIT consumido. Las otras versiones previas incluyen migración anterior
`22a4f6a1bc6724cba10d45eeb8ef8acd859b75d80d96c61b43f4d972465a8987`; harnesses
anteriores `1c41f21e1968d836bfc75f147bfe6af75b940ab4812ce127a34c53d7391aca46` y
`20d77ae009c432bb89d16361587f82e88892815059f4a09759994b4a0801c4cd`; snapshots JIT
previos `193c267671553880399a1dcc0bdb4f279347579062f6827cb334bbc4b166ae1d`,
`a32e5d0aae75f767e1fe05da8805624da8c1ebd2d4b494c29873bb6c6ea7efbc` y
`3d58a7eeb48ff2e724cee3240284bfe6901cd93e23ce3dddae64cb7cbd7abc8f`; el cuarto snapshot
de autorización fue `f5030e5ee7a497c5e3dce4d93f896606ae663d5046c9406701dbd76485c8c3fe`).
El arreglo `DETAIL.headers` cambiará bytes SQL y requerirá nuevo `continua`, hashes y JIT
antes de repetir PG17/PostgREST; no se declara GO Development.
