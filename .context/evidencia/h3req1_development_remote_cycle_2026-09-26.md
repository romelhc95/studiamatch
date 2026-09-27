# H3REQ1 — ciclo Development/Free remoto 2026-09-26

Estado del ciclo: `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`

## Actualización after-apply — 2026-09-26

Se recibió y consumió la autorización JIT humana para aplicar exclusivamente
los dos deltas `20260925` en Free/Development. No se aplicó ningún otro SQL ni
se ejecutó ninguna acción en Auth, datos, correo, Edge, Pages, Certification o
Production.

### Autorización utilizada

> Autorizo JIT Free/Development DDL exclusivamente para aplicar los deltas
> exactos `20260925_h3_legacy_member_creation_guard.sql` y
> `20260925_h3_admin_members_onboarding_reader.sql` en el proyecto
> `aqrldlmlszjtgpqiegaa`, después de verificar sus hashes.

### Hashes verificados antes de aplicar

| Migration | SHA-256 | Resultado |
|---|---|---|
| `20260925_h3_legacy_member_creation_guard.sql` | `bf7b240d76452105753883523428f6cfa4448bdb96c880b2f4aca467db0fe678` | `PASS` |
| `20260925_h3_admin_members_onboarding_reader.sql` | `0a9a0b5b694b9caef66da5f6e0d5a45d77bff9029e31b0ede54a5026c14a9d0d` | `PASS` |

### Aplicación y validación

- `20260925_h3_legacy_member_creation_guard`: aplicación `PASS`; registro
  remoto `20260926043750`.
- `20260925_h3_admin_members_onboarding_reader`: aplicación `PASS`; registro
  remoto `20260926043809`.
- `admin_create_member(p_email text, p_role text)`: `SECURITY DEFINER`,
  `search_path=pg_catalog, public, pg_temp`, mensaje legacy guard presente y
  sin operación de `INSERT`: `PASS`.
- `admin_list_members_onboarding()`: existe con la firma esperada,
  `SECURITY DEFINER`, guard de admin activo, consulta de invitación lateral y
  `search_path` explícito: `PASS`.
- Grants: ambas funciones tienen `EXECUTE` para `authenticated` y
  `service_role`; no se otorgó acceso a `anon`: `PASS`.
- Tablas H3 y RLS: preservadas; `admin_members`, `admin_invitations` y
  `admin_membership_audit` continúan con RLS habilitado: `PASS`.
- Datos: 3 miembros, 0 invitaciones pending, 0 invitaciones huérfanas y 1 fila
  de auditoría; no se modificaron datos operativos: `PASS`.

El drift de H3-001 específico de los dos deltas queda corregido. Esto no cierra
H3REQ1 completo: H3-002, H3-003 y H3-004 siguen `BLOCKED` hasta completar los
JIT y las pruebas remotas correspondientes.

## Actualización Edge read-only — 2026-09-26

Se consumió la autorización JIT Edge Development exclusivamente en modo
verificación. No se desplegó una nueva versión porque el runtime remoto ya
estaba `ACTIVE` y `verify_jwt=true`; tampoco se ejecutaron Auth writes, datos,
correo, Pages, cleanup ni acciones en otros ambientes.

### Resultado de la verificación

| Campo | Resultado |
|---|---|
| Proyecto | `aqrldlmlszjtgpqiegaa` — `PASS` |
| Function | `admin-invite` — `PASS` |
| Estado | `ACTIVE` — `PASS` |
| Versión | `4` después del despliegue autorizado |
| `verify_jwt` | `true` — `PASS` |
| Artefacto fuente remoto | Longitud `18,044` bytes; corresponde al artefacto aprobado |
| Artefacto fuente del candidato | Longitud `18,044` bytes; blob Git de `desarrollo` `946a19a7a9b31aaf9f209da52357cd9e1bf6ec73` |
| Correspondencia fuente/artefacto | `PASS` por fuente aprobado, longitud y marcadores; bundle runtime SHA `fc6e0c3dfdb337f4fcd38cdc75a74c0a73392673d78e169bc0125f8ca655a313` |
| Auth-owned invitation | Marcador presente — `PASS` |
| RPC reserve/complete/fail | Marcadores presentes — `PASS` |
| MFA `aal2` | Marcador presente — `PASS` |
| Redirect allowlist | Marcador presente — `PASS` |
| Password handling | No se encontró un flujo de password en la función — `PASS` |
| Security scan del código local | `PASS` |
| Contratos Edge locales | `20 passed` |

### Smoke negativo y logs

- GET sin `Authorization`: `401`, `UNAUTHORIZED_NO_AUTH_HEADER`.
- La evidencia del GET corresponde a la versión 3 anterior al despliegue; no
  se ejecutó una solicitud después del despliegue que generara datos o correo.
- El log remoto no expone passwords, JWT ni tokens; solo registra el método,
  código HTTP, `request_id` sanitizado y metadata operacional.
- No se ejecutó POST con credenciales ni se crearon invitaciones, por la
  exclusión explícita de Auth writes, datos y correo.

### Decisión Edge

El artefacto aprobado fue desplegado como versión 4 conservando
`verify_jwt=true`. La metadata y los marcadores del runtime quedan `PASS`.
No se ejecutó ningún POST autenticado ni se crearon datos; por tanto el smoke
funcional con admin `aal2` queda pendiente de la autorización Auth/test
data/correo y no se declara todavía H3-002.

## Alcance y autorización

- Ambiente único inspeccionado: Supabase Free/Development.
- Project ref: `aqrldlmlszjtgpqiegaa`.
- URL: `https://aqrldlmlszjtgpqiegaa.supabase.co`.
- PR #499: mergeado en `desarrollo`.
- Commit remoto de `desarrollo`: `c56f1cb5a0dac722a92e7ef3a6000a9bb2d6b4a9`.
- Checkout local de la sesión: `feat/h3req1-development-remote-tests` en
  `97168646b2a6bbd8e59f6d704446759303e11e64`; no se presenta como el commit
  remoto candidato.
- Modo remoto: exclusivamente read-only.
- No se ejecutaron DDL, migraciones, Auth writes, datos de prueba, correo,
  Edge deploy, Pages deploy, cleanup, rollback, push, PR, merge o promoción.
- Certification, Pro, Production y Cloudflare productivo no fueron consultados
  ni modificados durante este ciclo.

## Tareas y gates ejecutados

| Gate | Resultado | Evidencia sanitizada | Riesgo residual |
|---|---|---|---|
| Baseline local Docker | `PASS` parcial | 90 tests focalizados; TypeScript PASS; ESLint 0 errores/9 warnings históricos; sintaxis Node/Python PASS; credential scan PASS; `git diff --check` PASS | El checkout activo no coincide exactamente con `desarrollo` remoto; la corrección del harness local queda sin commit. |
| H3 PG17 canónico | `PASS` | `h3_pg17_harness_ok`; `h3_invitation_onboarding_harness_ok`; `h3_onboarding_rbac_hardening_harness_ok` | Ejecutado en base local descartable, no es evidencia remota. |
| H3 PG17 local no destructivo | `PASS` | `h3_pg17_harness_local_ok`, incluyendo identidad inválida tratada como anónima | Solo local; no autoriza DDL remoto. |
| Build normal | `PASS` | Static export en copia temporal del commit `c56f1cb`; rutas admin generadas: dashboard, login, callback, accept-invite y setup-password | No existe Pages/preview remoto funcional acreditado en este ciclo. |
| Build mock | `PASS` | Static export mock en copia temporal del commit `c56f1cb`; rutas H3 presentes | UAT mock completa no fue reejecutada en este ciclo. |
| H3-001 DB contract Free | `FAIL` | Las tablas H3 existen y tienen RLS; faltan los deltas `20260925_h3_legacy_member_creation_guard` y `20260925_h3_admin_members_onboarding_reader` en migrations remotas | El RPC legacy conserva el cuerpo anterior y no existe `admin_list_members_onboarding`. Requiere JIT Free DDL. |
| H3-002 invitación/onboarding remoto | `BLOCKED` | No se crearon usuarios, invitaciones ni correos; estado read-only: 0 invitaciones pending y 0 huérfanas | Requiere JIT Auth/test data/correo y Edge/Pages funcionales. |
| H3-003 RBAC/auditoría remoto | `BLOCKED` | 3 membresías Auth/DB reconciliadas, 0 huérfanas, 1 auditoría histórica y 0 secretos detectables en auditoría | No se ejecutaron mutaciones funcionales ni UAT por rol. El guard legacy pendiente bloquea el cierre. |
| H3-004 transición/rollback remoto | `BLOCKED` | No se ejecutaron deploy, contract, cleanup ni rollback | Requiere JIT Edge, Pages/preview, cleanup y rollback separados. |

## Baseline remoto Free/Development read-only

Captura sanitizada de este ciclo:

| Campo | Resultado |
|---|---|
| Project URL | `PASS`: URL corresponde a `aqrldlmlszjtgpqiegaa.supabase.co` |
| Migrations H3 | `PASS` para el inventario existente; `FAIL` para convergencia del candidato: la captura llega hasta los hardenings `20260924` y no registra los dos archivos `20260925` |
| Tablas | `PASS`: `admin_members`, `admin_invitations`, `admin_membership_audit` presentes |
| RLS | `PASS` habilitado en las tres tablas; `force_rls=false` |
| Policies | Solo se observan policies `service_role` para `admin_members`; invitaciones y auditoría no tienen policies directas |
| RPC legacy | `FAIL` de convergencia: `admin_create_member(p_email text, p_role text)` sigue con el cuerpo previo; no contiene el guard esperado |
| RPC lector aditivo | `FAIL` de convergencia: `admin_list_members_onboarding` no existe en Free |
| RPCs onboarding | `PASS` para las firmas/funciones ya presentes; `SECURITY DEFINER` con `search_path` explícito |
| Datos | `PASS` read-only: 3 miembros, 0 invitaciones pending, 0 invitaciones huérfanas, 1 auditoría, 0 hallazgos de password/token en los campos auditados |
| Edge `admin-invite` | `PASS` metadata: `ACTIVE`, versión 3, `verify_jwt=true`; smoke funcional real permanece pendiente |
| Advisories | `BLOCKED` para cierre: permanecen INFO sobre RLS sin policies y WARN sobre funciones `SECURITY DEFINER` ejecutables por authenticated |

## Artefactos y hashes

- `web/package.json`: SHA-256
  `39fd077951f3bd2235098c11bc4ba9425558329baca2129e9847bdef3f5b2b38`.
- `web/package-lock.json`: SHA-256
  `84c29b90ff854535d14a548eb9fd743419b7ed9043564436f94c94bf8474cc1c`.
- `tests/sql/h3_pg17_harness_local.sql` después de la corrección local:
  SHA-256 `40f5431ae05283e0c1227306f39354a34a20bd01492d07f27a4d3654bbec536e`.
- `supabase/functions/admin-invite/index.ts` local:
  SHA-256 `58371eea6945f83db62595afa350fd9218d2a101db41990768dab821d981d759`.
- Edge remoto `admin-invite`: metadata `ezbr_sha256`
  `ad394869312c8710dbfd3de22a2ed31ab2282623b8272598f6a5ab2571e4bd8f`.
  Este valor es del bundle remoto y no se equipara directamente al SHA del
  archivo fuente local sin un artefacto de build reproducible del runtime.

## Transición y decisión

- `expand`: `BLOCKED` para Development remoto hasta autorización JIT Free DDL
  de los dos deltas exactos del 2026-09-25.
- `compatibilidad`: `PASS` local; login legacy, rutas públicas, miembros
  `ready` y MFA/`aal2` no fueron retirados ni degradados. El harness local
  corregido mantiene el comportamiento anónimo para claims inválidos.
- `deploy`: `BLOCKED`; no se ejecutó Edge ni Pages/preview.
- `contract`: `BLOCKED`; no se retiró legacy ni se ejecutó cleanup.
- `rollback`: `BLOCKED`; no existe drill remoto autorizado.

Decisión: mantener `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`. No solicitar
Certification. El siguiente paso remoto permitido requiere, como mínimo,
autorización humana JIT separada para:

1. Free/Development DDL únicamente para los dos deltas `20260925` exactos.
2. Auth writes, datos de prueba y correo Development.
3. Edge deploy `admin-invite` Development.
4. Pages/preview Development.
5. Cleanup Development.
6. Rollback Development.

Ninguna de estas autorizaciones cubre Certification, Pro, Production, push,
merge, promoción o acciones en otro ambiente.

## Continuación del ciclo — preflight y revalidación 2026-09-26

| Campo | Valor |
|---|---|
| Ambiente | Free/Development |
| Project ref | `aqrldlmlszjtgpqiegaa` |
| URL | `https://aqrldlmlszjtgpqiegaa.supabase.co` |
| Timestamp UTC | `2026-09-26T12:36:06Z` |
| Checkout local | `97168646b2a6bbd8e59f6d704446759303e11e64` |
| Modo remoto | Read-only; no se generó run_id porque no hubo writes |
| Resultado | `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` |

### Preflight read-only actualizado

- Free registra las migraciones H3, incluidos `20260925_h3_legacy_member_creation_guard` y `20260925_h3_admin_members_onboarding_reader`.
- `admin_members`, `admin_invitations` y `admin_membership_audit` existen con RLS habilitado; se verificaron columnas, constraints, índices, policies observadas y RPCs H3.
- Las RPCs H3 relevantes mantienen `SECURITY DEFINER` y `search_path` explícito; el lector aditivo y el guard legacy están presentes. No se ejecutó DDL.
- `admin-invite` permanece `ACTIVE`, versión `4`, con `verify_jwt=true`; no se desplegó una nueva versión.
- Estado de datos antes/después: `3` miembros, `3` activos, `0` invitaciones, `0` pendientes, `0` huérfanas, `1` auditoría y `4` usuarios Auth.
- Advisories: INFO/WARN existentes sobre RLS sin policies, funciones `SECURITY DEFINER` ejecutables por `authenticated`, protección de passwords filtrados deshabilitada y foreign keys sin índice. No se observó HIGH/CRITICAL.

### Validación local en Docker

| Prueba | Resultado | Evidencia sanitizada |
|---|---|---|
| Contratos H3 focalizados | `PASS` | `60 passed` |
| Harness PG17 canónico | `PASS` | `h3_pg17_harness_ok` en base descartable; base eliminada al finalizar |
| TypeScript | `PASS` | `npx tsc --noEmit` |
| ESLint | `PASS` | 0 errores, 9 warnings históricos |
| Credential scan | `PASS` | `credential scan passed` |
| Sintaxis Python | `PASS` | `py_compile` |
| `git diff --check` | `PASS` | sin salida |
| Build normal con `.env.local` cargado | `BLOCKED` de entorno | `NEXT_PUBLIC_H3_MOCK_URL` de test está presente y el guard de producción lo rechaza |
| Build normal con variable mock vacía | `PASS` | static export generado; rutas `/admin/`, `/admin/login/`, `/admin/auth/callback/`, `/admin/accept-invite/` y `/admin/setup-password/` presentes |

El build bloqueado no produjo un defecto de código: el checkout usa una variable
de mock local en `.env.local`. La revalidación con el entorno de producción
limpio (`NEXT_PUBLIC_H3_MOCK_URL=`) pasó sin editar código ni configuración.

### Smoke remoto no autenticado

- GET sin autorización: HTTP `401`, `UNAUTHORIZED_NO_AUTH_HEADER`.
- POST sin autorización: HTTP `401`, `UNAUTHORIZED_NO_AUTH_HEADER`.
- POST con JWT inválido: HTTP `401`, error sanitizado de autorización inválida.
- La captura final de conteos confirma que ninguna de estas solicitudes mutó
  Auth, membresías, invitaciones o auditoría.

### Gates del ciclo

| Gate | Resultado | Bloqueador |
|---|---|---|
| H3-001 DB contract Free | `PASS` | Advisories INFO/WARN residuales documentados |
| H3-002 invitación/onboarding | `BLOCKED` | No hay sesión admin ready/AAL2 ni buzón de prueba materializados; no se ejecutó correo, PKCE, callback ni password |
| H3-003 RBAC/auditoría | `BLOCKED` | No hay actor autenticado para mutaciones por rol; solo se pudo verificar el baseline read-only |
| H3-004 compatibilidad/Pages/rollback | `BLOCKED` | El preview conocido sirve login pero devuelve 404 en callback, aceptación y setup; no existe hostname Development acreditado ni autorización Pages/rollback |
| Cleanup | `BLOCKED` | No hubo datos temporales que limpiar; no se ejecuta cleanup vacío como sustituto de UAT |

### Inputs pendientes y siguiente acción

El navegador accesible permanece en `about:blank` y el contenedor no expone una
sesión admin ni un buzón/API de prueba. El preview
`88f02c53.studiamatch-aty.pages.dev` sigue sin las tres rutas nuevas. Para
continuar la UAT real se requiere que, fuera del chat, quede disponible una
sesión admin activa/ready con AAL2 y un buzón temporal accesible; para validar
frontend se requiere además el hostname/artefacto Development correcto y la
autorización JIT Pages/preview separada indicada por el alcance. No se requieren
ni deben compartirse passwords, MFA, JWT, refresh tokens ni enlaces con token.

## Intake revalidado — 2026-09-26T13:12:45Z

La confirmación humana recibida fue `A+B+C + continua`. La comprobación de
materialización en el entorno no pudo corroborarla: el navegador disponible
continúa en `about:blank`, no aparecen variables de sesión admin ni de inbox
temporal, y el preview conocido continúa devolviendo `404` para callback,
aceptación y setup. La autorización no se consumió porque no existía una vía
segura operable para crear datos. No se generó `run_id`, no se ejecutaron Auth,
correo, Pages, cleanup, rollback ni writes remotos.

Resultado de intake: `BLOCKED` por inputs no materializados. El siguiente gate
requiere conectar la sesión admin ready/AAL2, el buzón temporal y el hostname/
artefacto Development desde el entorno autorizado; no se debe pegar ningún
secreto en el chat.

## Revalidación coordinada — 2026-09-26T14:40:25Z

| Campo | Valor |
|---|---|
| Ambiente | Free/Development |
| Project ref | `aqrldlmlszjtgpqiegaa` |
| URL | `https://aqrldlmlszjtgpqiegaa.supabase.co` |
| Commit local | `97168646b2a6bbd8e59f6d704446759303e11e64` |
| Edge remoto | `admin-invite` v4, `ACTIVE`, `verify_jwt=true`, bundle SHA `fc6e0c3dfdb337f4fcd38cdc75a74c0a73392673d78e169bc0125f8ca655a313` |
| Resultado global | `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` |

### Delta ACL autorizado y after-apply

**Prueba:** corrección mínima del grant directo observado en
`public.admin_members`.

**Resultado:** `PASS` after-apply.

**Autorización utilizada:** JIT consolidado exclusivamente para Free/Development,
project ref `aqrldlmlszjtgpqiegaa`, con impacto limitado a revocar privilegios
directos de `anon` y `authenticated` sobre `public.admin_members`; sin otros
DDL, Auth, Edge, Pages, cleanup remoto, rollback operativo, otros ambientes o
promoción.

**Artefacto:** `h3req1_admin_members_acl_delta_20260926.sql`, SHA-256
`39d5a2e852cebad117f7292591d0658255281804915ad7fdfec968f3366636ef`.

**Evidencia sanitizada:** migración remota registrada como
`h3req1_admin_members_acl_delta_20260926`, versión `20260926143836`; después de
aplicar, `anon` y `authenticated` tienen `SELECT/INSERT/UPDATE/DELETE/TRUNCATE`
en `false` sobre `public.admin_members`. RLS continúa habilitado en
`admin_members`, `admin_invitations` y `admin_membership_audit`; el guard legacy,
el lector onboarding, las firmas RPC y los `search_path` explícitos permanecen.

**Baseline after-apply:** 3 membresías, 2 admins activos/ready, 3 activos, 4
usuarios Auth, 0 invitaciones, 0 pendientes huérfanas, 1 auditoría, 0 usuarios
temporales y 0 registros de auditoría con marcadores de secretos. Fingerprint de
membresías sin cambio: `4164a256f8714ee5f209d1ed19558cc5`.

**Rollback previsto/ejecutado:** previsto mediante restauración explícita de los
privilegios ACL anteriores, con autorización separada; `NOT EXECUTED`.

### Validación local Docker y regresiones

**Resultado:** `PASS`.

Evidencia reproducible: 60 contratos focalizados; 142 pruebas offline; TypeScript;
credential scan; sintaxis Python y Node; `git diff --check`; build normal con
`NEXT_PUBLIC_H3_MOCK_URL` vacío; build mock; UAT mock de invitación 9/9;
`h3_pg17_harness_ok`; `h3_invitation_onboarding_harness_ok`;
`h3_onboarding_rbac_hardening_harness_ok`;
`h3_invitation_edge_runtime_harness_ok`; `h3_pg17_harness_local_ok`;
`h2_pg17_harness_ok`; y regresiones A6/A13. Docker quedó healthy y respondió
HTTP 200 en `/admin/login/`. El primer intento del runner UAT quedó clasificado
`LOCAL_TEST`: el redirect del mock apuntaba al puerto 3000 mientras el static
server de prueba estaba en 3002; se corrigió únicamente el entorno de ejecución,
sin editar código, y la repetición fue `PASS` 9/9.

Los DB/containers temporales creados para estas pruebas fueron eliminados. No se
registraron passwords, MFA, JWT, refresh tokens, enlaces con token, API keys ni
contenido sensible de correo.

**Hallazgo de seguridad pendiente:** `npm audit --omit=dev --audit-level=high`
terminó `FAIL` con 36 vulnerabilidades: 16 HIGH y 1 CRITICAL. No se ejecutó
`npm audit fix` por estar fuera del alcance autorizado; el hallazgo bloquea el
criterio de ausencia de HIGH/CRITICAL.

### UAT remota e inputs

| Gate | Resultado | Evidencia sanitizada | Bloqueador | Siguiente acción |
|---|---|---|---|---|
| H3-001 Free DB/RPC/ACL | `PASS` | Migraciones H3, tablas, constraints, RLS, RPCs, ACL after-apply y baseline reconciliados | Advisors INFO/WARN conocidos | Mantener compatibilidad y continuar solo con inputs reales |
| H3-002 invitación/onboarding | `BLOCKED` | No se generó `run_id`; no hubo Auth, correo, PKCE, callback ni password remoto | Sesión admin `active/ready/aal2` y buzón no materializados en las herramientas | Conectar ambos desde entorno seguro |
| H3-003 RBAC/auditoría | `BLOCKED` | Baseline read-only intacto; no hubo actores temporales ni mutaciones de membresías | Falta sesión real para admin/user/inactivo/anónimo | Ejecutar UAT por rol y reconciliar auditoría |
| H3-004 compatibilidad/Pages/rollback | `BLOCKED` | Edge v4 verificado; preview conocido: `/admin/`, login y users 200; callback, accept y setup 404 | Hostname/artefacto Development no acreditado; rollback no autorizado | Conectar hostname/artefacto y solicitar Pages/rollback exactos |
| Cleanup remoto | `BLOCKED` | No había cohorte temporal; no se ejecutó cleanup vacío | Depende de UAT real | Limpiar únicamente el `run_id` después de todos los casos |

**Riesgo residual:** no existe evidencia remota de correo/Auth/PKCE, onboarding
real, RBAC por actor, Pages Development ni rollback. No se solicita
Certification ni se declara GO.

## Verificación posterior a `continua` — 2026-09-26T14:49:35Z

**Ambiente/project ref:** Free/Development — `aqrldlmlszjtgpqiegaa`.

**Prueba:** comprobación read-only de materialización de sesión admin, buzón y
artefacto Development.

**Resultado:** `BLOCKED`.

**Evidencia sanitizada:** Chrome DevTools reportó cero páginas abiertas; el
navegador accesible permaneció fuera del hostname administrativo, en una API de
GitHub. No se observó un buzón/API temporal conectado ni un hostname/artefacto
Development acreditado. No se generó `run_id` ni se ejecutaron Auth, correo,
UAT remota, cleanup, rollback o nuevos writes.

**Autorización utilizada:** ninguna nueva; el delta ACL anterior permanece
aplicado y validado.

**Rollback:** no ejecutado. **Riesgo residual:** H3-002/H3-003/H3-004 siguen sin
evidencia remota y el ciclo no cumple el criterio de ausencia de HIGH/CRITICAL.

**Siguiente acción:** conectar desde el entorno seguro la sesión admin
`active/ready/aal2`, el buzón temporal y el hostname/artefacto Development, sin
compartir secretos en el chat.

## Pages/preview H3 recovery — 2026-09-26T17:38:49Z

| Campo | Valor |
|---|---|
| Ambiente | Free/Development |
| Pages project | `studiamatch` |
| Environment | `preview` |
| Branch | `feat/h3req1-development-remote-tests` |
| Commit asociado | `97168646b2a6bbd8e59f6d704446759303e11e64` (`commit-dirty=true`) |
| Deployment | `946d11cc` — `success` |
| URL única | `https://946d11cc.studiamatch-aty.pages.dev` |
| Alias verificado | `https://feat-h3req1-development-remo.studiamatch-aty.pages.dev` |
| Resultado Pages | `PASS` para artefacto y rutas; cierre H3 global continúa `NO-GO` |

### Cambio funcional

Se añadió `/admin/reset-password/` como flujo separado del onboarding de
invitaciones. El callback acepta únicamente `recovery`, elimina code/hash/error
de la URL antes del trabajo asíncrono, establece sesión con los métodos oficiales
de Supabase Auth y ejecuta `updateUser({ password })`. No llama
`completePasswordSetup`, `adminRpc` ni envía password a una RPC. Se añadió el
slash redirect en middleware y en el servidor estático de pruebas.

### Validación

Docker: 165 pruebas contractuales/regresiones `PASS`; TypeScript `PASS`; lint sin
errores con 9 warnings históricos; credential scan `PASS`; Python compile `PASS`;
build normal `PASS` con 243 páginas; build mock `PASS` con 17 páginas; smoke
Playwright recovery `PASS`; `git diff --check` `PASS`.

Smoke remoto del alias Pages:

| Ruta | HTTP | Resultado |
|---|---:|---|
| `/` | 200 | Home servida |
| `/admin/` | 200 | Panel servido |
| `/admin/login/` | 200 | Login servido |
| `/admin/auth/callback/` | 200 | Callback servido |
| `/admin/accept-invite/` | 200 | Aceptación servida |
| `/admin/setup-password/` | 200 | Setup servido |
| `/admin/reset-password/` | 200 | Recovery servido |
| `/admin/users/` | 200 | Gestión servida |

El HTML de recovery no presentó marcadores `access_token`, `refresh_token` ni
`token=`. El hostname único `946d11cc` permanece protegido por el middleware
hasta que se añada a la allowlist; el alias operativo verificado quedó incluido
en `ADMIN_ALLOWED_HOSTS` del entorno Preview junto con el hostname anterior. La
configuración Production no fue modificada.

Hashes locales del candidato desplegado históricamente en el deployment `946d11cc`
(no corresponden al checkout posterior de política de password):

| Artefacto | SHA-256 |
|---|---|
| `web/src/app/admin/reset-password/page.tsx` | `5caeac0bc2f83e5c406a886a0742837a683e868edf9d4cb9a606745db27e76fb` |
| `web/src/lib/admin-auth.ts` | `9e17b8eb7d217b00c4c6c5d27add07b4de57418ed061a92e8c01c70d2fbc418c` |
| `web/functions/_middleware.ts` | `26fa6c6babe628feab63ac8f81ae4b84659c7f6340aaccd5e62bad0d6a4a53ff` |
| `web/out/admin/reset-password/index.html` | `03bb5d4601ef81350f278aa79e220f37d3b526b83a8c76a95020e5856d3d1aa8` |

### Límites y siguiente gate

No se ejecutaron Auth, correo, redirect allowlist de Supabase, DDL, Edge, MFA,
usuarios temporales, `run_id`, UAT real, cleanup, rollback, push, PR, merge o
promoción. El siguiente gate requiere autorización separada de Auth/configuración
de redirect y luego la sesión admin, buzón temporal y UAT remota. El hallazgo
`npm audit --omit=dev --audit-level=high` continúa bloqueando cualquier GO por
16 HIGH y 1 CRITICAL.

## Auth recovery redirect Free/Development — 2026-09-26T18:02:31Z

| Campo | Valor |
|---|---|
| Ambiente | Free/Development |
| Project ref | `aqrldlmlszjtgpqiegaa` |
| Acción autorizada | Configuración exclusiva del redirect de recovery |
| Site URL persistida | `https://feat-h3req1-development-remo.studiamatch-aty.pages.dev/admin/reset-password/` |
| Redirect URL persistida | `https://feat-h3req1-development-remo.studiamatch-aty.pages.dev/admin/reset-password/` |
| Resultado | `PASS` configuración persistida tras recarga del Dashboard |

La modificación se realizó únicamente en Authentication → URL Configuration de
Free/Development. No se enviaron correos, no se consumió ningún token, no se
modificaron usuarios ni factores MFA y no se ejecutó UAT Auth. El token de
recovery anterior, cuyo redirect era localhost, queda descartado.

**Siguiente acción humana:** desde Auth Users seleccionar el usuario admin
existente y pulsar `Send password recovery`; abrir exclusivamente el correo nuevo
en el navegador seguro y verificar que redirige al preview Development. No se
debe pegar en el chat la URL completa ni ningún token.

## Password policy, live validation and recovery TTL — 2026-09-26T18:54:19Z

| Campo | Valor |
|---|---|
| Alcance autorizado | `continua + Free Auth` |
| Ambiente | Free/Development |
| Project ref | `aqrldlmlszjtgpqiegaa` |
| Minimum password length | `12` |
| Password requirements | lowercase + uppercase + digits + symbols |
| Email OTP/link expiration | `86400` seconds / `24 hours` |
| Verificación remota | `PASS` antes/después de guardar y después de recargar |
| Template remoto | No aplicado; versión local en `supabase/templates/password-recovery.html` |

### Cambio local

`web/src/lib/password-policy.ts` centraliza la política; recovery y setup usan
`PasswordInput` y `PasswordRequirements` para mostrar en vivo el cumplimiento de
longitud, mayúscula, minúscula, número, símbolo y coincidencia. El botón permanece
deshabilitado hasta completar todas las reglas. La plantilla incluye CTA, uso
único, expiración de 24 horas, pasos de recuperación, requisitos y aviso de
seguridad, usando únicamente `{{ .ConfirmationURL }}` para el enlace Auth.

### Checks

| Check | Resultado |
|---|---|
| Contratos H3/recovery/password policy/context | `23 passed` |
| `npx tsc --noEmit` en Docker | `PASS` |
| `npm run lint` en Docker | `PASS` — 9 warnings históricos, 0 errors |
| `npm run build` sin `NEXT_PUBLIC_H3_MOCK_URL` | `PASS` — 243 páginas |
| `npm run build:mock` | `PASS` — 17 páginas |
| `git diff --check` | `PASS` |
| Credential scan | `PASS` |

El aviso del Dashboard `OTP expiry exceeds recommended threshold` es consistente
con el valor autorizado de 24 horas y queda como riesgo operativo documentado para
la UAT con buzón real. No se desplegó el artefacto ni se aplicó aún la plantilla
remota; no se tocaron Certification, Production, usuarios, MFA, cleanup,
rollback, push, PR, merge o promoción.

### Smoke UI de validación en vivo

En un contexto de navegador local aislado se verificaron tres estados sin submit:

| Estado | Resultado |
|---|---|
| Entrada incompleta | Reglas pendientes visibles; botón deshabilitado |
| Reglas completas con confirmación distinta | Requisito de coincidencia en rojo; botón deshabilitado |
| Reglas completas y confirmación coincidente | Cinco reglas verdes, `Lista para guardar`; botón habilitado |

La sesión usada para el smoke fue sintética y se eliminó al cerrar el contexto; no
se usó un usuario remoto ni se enviaron passwords, tokens o correos.

## Security remediation and current checkout traceability — 2026-09-26T20:18:46Z

La reauditoría del ciclo confirmó que la política de longitud, estados accesibles
de las reglas y el flujo Auth-only no exponen secretos. Se añadió `aria-invalid`,
se eliminan IDREF de error cuando no existe el mensaje y los errores generales de
setup se anuncian con `role="alert"`. El smoke final comprobó:

| Estado | Resultado |
|---|---|
| Entrada incompleta | `status=En progreso`, submit deshabilitado |
| Reglas completas, confirmación distinta | mismatch anunciado, submit deshabilitado |
| Cinco reglas y confirmación coincidente | `Lista para guardar`, cinco estados `true`, submit habilitado |

En la comprobación granular final, con mismatch solo el campo de confirmación
expuso `aria-invalid=true`; el campo principal no se marcó inválido. Con la
coincidencia correcta ambos campos retiraron el error y conservaron únicamente la
descripción de requisitos.

### Hashes del checkout actual

Estos hashes corresponden al checkout local que produjo los checks de este ciclo;
no se afirma que estén desplegados porque deploy/Pages quedó fuera del alcance.

| Artefacto | SHA-256 |
|---|---|
| `web/src/lib/password-policy.ts` | `4707e20753fec4eaac39e4046b8bb8b1d73171e08844686d9dceb63888ddff69` |
| `web/src/components/admin/PasswordInput.tsx` | `95addf000a842bbaaffff92ca0c26c2dc5482199813ba97cd05997ab5ea6da28` |
| `web/src/components/admin/PasswordRequirements.tsx` | `e2215f5cebf9a1a91f44b01c4e9d3e51d6458a337930a2dd0af5193675b59a6e` |
| `web/src/app/admin/reset-password/page.tsx` | `d015907bd2a0ca53b7846b775226f8021d3b3f26e391aca5cd30509bbdbcb6f0` |
| `web/src/app/admin/setup-password/page.tsx` | `a58aae50a3acd5104b24d28d0cdac4c11894659d3932e0ecf3bc7549b5750a3f` |
| `supabase/templates/password-recovery.html` | `638f26c8fe97e6a932707024d18861593df8866a232e5fc49c8b7f924be7a70e` |
| `tests/test_password_policy_contract.py` | `665a4e201b9fac5b4f53ff097d134aebd79006f756dad32d59c256fdf7f4e43a` |
| `tests/test_h3_password_recovery_contract.py` | `58331b5a7d098f3950e970dd952eb6c015a6234111b367d81c9feb849b79121a` |
| `mock-server/static-server.js` | `fba00f34847d8e5219e400b6ba4e37ea7ff726645f3b7c057e5df38c2f7e5e9e` |
| `web/out/admin/reset-password/index.html` (mock build) | `de4e8246a36e2aa00da479b8cdf11d628e5fab88808c9cb1d16410ddbd7d26b8` |

La expiración Auth de 24 horas permanece como riesgo autorizado y el Dashboard
mantiene el aviso de recomendación por superar una hora. No hay hallazgos
CRITICAL/HIGH en el código revisado; el cierre funcional sigue bloqueado por falta
de plantilla remota, correo/UAT real, deploy y la deuda `npm audit` (16 HIGH,
1 CRITICAL).

La auditoría final no dejó hallazgos HIGH ni MEDIUM en la remediación local:
`GO técnico local`. El estado contractual global continúa `NO-GO` por los
pendientes operativos y de promoción indicados arriba.

## Recovery real, plantilla Auth y Preview actualizado — 2026-09-26T21:42:07Z

| Campo | Valor |
|---|---|
| Alcance | Free/Development exclusivamente |
| Project ref | `aqrldlmlszjtgpqiegaa` |
| Pages project | `studiamatch` / `preview` |
| Branch | `feat/h3req1-development-remote-tests` |
| Commit asociado | `97168646b2a6bbd8e59f6d704446759303e11e64` (`commit-dirty=true`) |
| Deployment | `5fb35afa-4d3c-43e7-850b-91b5e94c5818` — `success` |
| Alias operativo | `https://feat-h3req1-development-remo.studiamatch-aty.pages.dev` |

### Plantilla Auth remota

La plantilla `supabase/templates/password-recovery.html` se aplicó mediante la
configuración Auth de Free/Development y se verificó con una lectura posterior:

| Verificación | Resultado |
|---|---|
| `MAILER_SUBJECTS_RECOVERY` | `Restablece tu contraseña de StudIAMatch` |
| Plantilla remota | 6,554 caracteres / 6,556 bytes UTF-8 |
| SHA-256 normalizada | `b09ef52fa1fab97e0a8f1d74a065b4045d53f05c828c089b8a4ef1c04d9719b2` |
| Local con salto de línea final | `638f26c8fe97e6a932707024d18861593df8866a232e5fc49c8b7f924be7a70e` |
| `MAILER_OTP_EXP` | `86400` segundos / 24 horas |
| `PASSWORD_MIN_LENGTH` | `12` |
| Categorías fuertes | minúscula, mayúscula, número y símbolo |
| Variables de enlace | solo `{{ .ConfirmationURL }}` |

La plantilla remota confirmó idioma español, vigencia de 24 horas, uso único,
pasos de recuperación y requisitos de contraseña. La diferencia de SHA-256 se
explica únicamente por el salto de línea final que conserva el archivo local;
el contenido normalizado coincide.

### Deploy y verificación del artefacto

El build de producción falló inicialmente porque el contenedor heredaba
`NEXT_PUBLIC_H3_MOCK_URL`; el reintento dentro de Docker con esa variable retirada
pasó correctamente y generó 243 páginas. Wrangler publicó el export actual al
branch configurado para el alias operativo. El endpoint remoto
`/admin/reset-password/index.html` respondió `200` y coincidió byte a byte con
`web/out/admin/reset-password/index.html`:

| Artefacto | Bytes | SHA-256 |
|---|---:|---|
| Export local y HTML remoto | `21,321` | `c38d65166996cee5aed95b32764ff44eb8d7bd21fcb6eae53c2a6f6806488abe` |

El hostname hash del deployment no se incorporó a `ADMIN_ALLOWED_HOSTS`; el alias
operativo existente se mantuvo como único hostname administrativo de este Preview.
Production no fue modificado.

### Recovery real

Se solicitó un recovery nuevo al usuario admin existente mediante
`POST /auth/v1/recover` en Free/Development con respuesta `200`. La consulta
sanitizada de `auth_logs` del intervalo `2026-09-26T21:20:00Z`–
`2026-09-26T22:00:00Z` registró:

| Ruta | Resultado observado |
|---|---:|
| `/recover` | `200` |
| `/verify` | `303` |
| `/user` | `200` |
| `/logout` | `204` |

La atestación humana confirmó recepción del correo real, apertura del botón,
visualización del formulario con validación en vivo y actualización correcta de
la contraseña. No se almacenaron ni expusieron el enlace, tokens, MFA secrets o
passwords. No se crearon usuarios adicionales.

### Decisión MFA

La indicación de MFA se conserva. El recovery solo comunica que se debe completar
MFA si el panel lo solicita; el login mantiene el flujo de enrolamiento cuando no
existe un factor TOTP verificado y exige `aal2` después de verificarlo. Ningún
factor MFA fue habilitado, revocado o modificado durante este ciclo. No se debe
marcar MFA como habilitada hasta completar ese enrolamiento de forma explícita.

### Transición, rollback y estado

- `expand`: política de password compartida, checklist accesible y plantilla Auth.
- `compatibilidad`: rutas legacy y callback permanecen disponibles durante la
  construcción y el Preview.
- `deploy`: deployment `5fb35afa` activo en el alias operativo autorizado.
- `contract`: limitado a Free/Development; no se contraen rutas legacy ni se
  promueve el cambio hasta completar la UAT restante.
- `rollback`: restaurar la plantilla Auth previa y reasignar el alias al
  deployment anterior, solo con JIT separado; no se ejecutó.

El resultado de este ciclo funcional es `PASS` para plantilla, Preview y recovery
real. El cierre contractual sigue `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`
por H3-002/H3-003/H3-004, UAT de invitaciones/RBAC/onboarding/MFA-AAL2,
`npm audit` (16 HIGH y 1 CRITICAL) y promoción protegida pendiente.

## Continuación local: MFA de compatibilidad — 2026-09-27

Esta continuación corresponde únicamente al árbol local Docker. No modifica el
Preview `5fb35afa`, el alias operativo, Free/Development remoto, Certification ni
Production.

### Implementación local

- El login usa `signInWithPassword` y permite llegar al panel con `aal1`; ya no
  consulta factores ni crea un TOTP automáticamente durante la autenticación.
- Las RPCs sensibles conservan `admin_require_aal2()` como autoridad server-side.
  Los errores `MFA aal2 required` se normalizan a un estado explícito de UI.
- `MfaRequiredCard` ofrece configuración únicamente después de una acción humana.
  Reutiliza factores TOTP verificados, permite reiniciar un factor pendiente de
  forma explícita y usa `supabase.auth.mfa.*` para listar, enrolar, desafiar,
  verificar y retirar factores.
- Los formularios sensibles declaran `method="post"` para evitar que un fallback
  HTML coloque passwords o códigos en la query string.
- El mock local expone `user.factors`, preserva el `aal` de la sesión actual y
  convierte el rechazo de AAL2 a la respuesta `403/mfa_required` usada por el
  cliente.

### Evidencia local observada

- Smoke estático local: login password-only llegó al panel; sin factor apareció
  `Configurar MFA`; el flujo explícito ejecutó enrolamiento, challenge y verify;
  la sesión resultante quedó en `aal2` y la cola cargó.
- El primer intento del UAT canónico no fue funcional porque PostgreSQL local
  estaba detenido y devolvía `EHOSTUNREACH`; sus artefactos temporales se
  restauraron desde la evidencia PASS previamente versionada.
- PostgreSQL local se inició nuevamente sin tocar ningún ambiente remoto. El UAT
  canónico se relanzó contra el static export/mock server en segundo plano; su
  resultado se registrará solo cuando termine, sin sustituir evidencia PASS con
  una ejecución incompleta.

### Gates locales ejecutados

`npx tsc --noEmit` PASS; `npm run lint` PASS con 9 warnings históricos en
`HomeContent.tsx` y ningún error; build normal de 243 páginas PASS; build mock de
17 páginas PASS; contratos MFA PASS; sintaxis de ambos runners UAT PASS;
`git diff --check` PASS; credential scan PASS. No se ejecutaron writes Supabase,
DDL, cambios de factores remotos, deploy, push, PR, merge ni promoción.

### Transición y rollback

- `expand`: cliente MFA oficial, estado explícito de AAL2 y tarjeta de
  configuración humana.
- `compatibilidad`: el login password-only y el enforcement server-side conviven;
  factores verificados y sesiones `aal2` existentes continúan funcionando.
- `deploy`: pendiente de autorización JIT de Preview; no se publicó este cambio.
- `contract`: pendiente de UAT local completa y validación remota Free/Development;
  no se retira ninguna ruta legacy en este ciclo.
- `rollback`: restaurar los archivos MFA/login al estado previo y reasignar el
  alias al deployment estable anterior; ejecutar solo con autorización humana
  separada.

El estado contractual permanece `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

## Diagnóstico Auth recovery rate-limit — 2026-09-27T03:17:11Z

Se realizó una comprobación read-only de `auth_logs` en Free/Development,
project ref `aqrldlmlszjtgpqiegaa`, después del error mostrado por el Dashboard.
La evidencia no contiene password, enlace de recovery, token, código MFA ni API
key.

| Campo | Resultado |
|---|---|
| Acción | `user_recovery_requested` |
| Método/ruta | `POST /recover` |
| Estado HTTP | `429` |
| Código Auth | `over_email_send_rate_limit` |
| Causa | Supabase impone una espera mínima de 9 segundos entre solicitudes de recovery |
| Resultado del diagnóstico | `PASS`: rate-limit esperado; no es defecto de MFA, redirect, RPC ni del Preview |

El mensaje del Dashboard es el envoltorio visible de esta respuesta Auth. Se
debe esperar más de 9 segundos desde la última solicitud y pulsar el envío una
sola vez; repetir clicks dentro de la ventana vuelve a producir `429`. No se
requiere DDL, cambio de código ni modificación de factores para corregir este
evento.

El intento de login observado previamente quedó en `Invalid login credentials`
antes de crear sesión, por lo que no habilitó MFA ni alcanzó una operación
`aal2`. El Preview `10205113` quedó publicado en el alias Development y no hubo
writes adicionales durante este diagnóstico.

Por seguridad, cualquier password compartida en el chat o expuesta durante la
inspección anterior se considera comprometida y debe rotarse antes de continuar
la UAT autenticada. No se registra su valor en esta evidencia ni se usará para
validar el login. El estado contractual permanece
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` hasta completar la rotación, login
exitoso, MFA explícita y operaciones sensibles con evidencia sanitizada.

## Remediación de redirección posterior al login — 2026-09-27T03:37:18Z

La nueva comprobación read-only separó el fallo de credenciales del fallo de
autorización de la UI:

| Gate | Resultado |
|---|---|
| Supabase Auth `POST /token` | `200` — password aceptada y sesión creada |
| Preview `POST /rpc/admin_current_user_role` | `200` |
| Membresía remota | `role=admin`, `is_active=true`, `account_status=ready` |
| Función remota | `RETURNS text` |
| Causa raíz | El cliente no interpretaba la respuesta escalar `"admin"`; la trataba como `anon` y redirigía al login |

La corrección en `web/src/lib/admin-auth.ts` acepta ahora respuestas del RPC en
formato escalar, objeto o array, conservando la compatibilidad con el mock y con
variantes PostgREST. Validaciones Docker: TypeScript `PASS`, contratos focalizados
`12 passed`, build normal `PASS` con 243 páginas, credential scan `PASS`,
`git diff --check` `PASS` y lint `PASS` con 9 warnings históricos.

### Preview corregido

El candidato se publicó únicamente en Free/Development:

| Campo | Resultado |
|---|---|
| Pages deployment | `e6948d54` — `success` |
| Alias | `https://feat-h3req1-development-remo.studiamatch-aty.pages.dev` |
| `/admin/login/` | HTTP `200` |
| `/admin/` | HTTP `200` |
| Otros ambientes | Certification y Production intactos |

No se ejecutaron DDL, writes de datos, cambios de factores MFA, push, PR, merge
ni promoción. El login posterior al nuevo deployment aún requiere confirmación
humana en el navegador; hasta esa evidencia el estado sigue
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

## MFA existente presenta challenge directo — 2026-09-27T03:48:54Z

Los logs Auth sanitizados confirmaron el enrolamiento previo sin exponer secreto
ni código: creación de factor `200`, challenge `200` y verify `200`. Los accesos
posteriores con password continúan correctamente en `aal1`, como define la
política de compatibilidad; las operaciones sensibles deben elevar a `aal2`.

El Preview actualizado detectó el factor `verified` y OpenChamber mostró:

- `Verifica MFA para continuar`;
- `Tu autenticador ya está configurado. Ingresa el código de 6 dígitos para continuar.`;
- campo `Código de 6 dígitos` y botón `Verificar MFA`;
- ningún QR, secreto, botón de enrolamiento ni reinicio de factor.

La corrección se publicó en el deployment `ea787a8a` del alias Development. El
gate de detección de factor verificado y presentación del challenge queda `PASS`.
La verificación del código actual y la operación sensible posterior siguen
pendientes; el estado global permanece `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

## MFA `aal2` y operación sensible confirmadas — 2026-09-27T03:55:45Z

La verificación final del código TOTP se confirmó sin registrar el código ni
ningún secreto:

| Gate | Resultado |
|---|---|
| Challenge TOTP | HTTP `200` |
| Verify TOTP | HTTP `200` |
| `admin_get_course_queue` | HTTP `200` |
| `admin_count_course_queue` | HTTP `200` |
| OpenChamber | `/admin/`, cola editorial visible, 131 cursos |
| Tarjeta MFA después de verificar | Ausente; la operación continuó |

La sesión elevó correctamente la assurance para la operación sensible y el
servidor aceptó ambas RPC protegidas. El gate remoto login + MFA explícita +
operación sensible queda `PASS`. Logout, refresh, regresión post-refresh y
reconciliación final de la transición continúan pendientes; el estado contractual
global permanece `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

## Login confirmado después de la remediación — 2026-09-27T03:41:43Z

La validación en OpenChamber sobre el alias Preview corregido confirmó:

| Gate | Resultado |
|---|---|
| URL | `/admin/` |
| Encabezado | `StudIAMatch Admin` |
| Rol visible | `Admin` |
| Panel | `Cola editorial` y enlace `Usuarios` visibles |
| Password login Auth | `POST /auth/v1/token` → `200` |
| MFA | Tarjeta explícita `Configura MFA para continuar` visible |
| Enrolamiento automático | No ejecutado |

La sesión ya no regresó a `/admin/login/`. La tarjeta confirma que la contraseña
es válida y que MFA requiere una acción humana explícita; no se creó ni modificó
ningún factor durante esta validación. El gate de login/compatibilidad queda
`PASS`; la UAT MFA y la operación sensible `aal2` permanecen pendientes y el
estado contractual global sigue `NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION`.

## Continuación UX editorial — 2026-09-27

Esta continuación implementa la mejora evolutiva de UX indicada por el pedido
humano: no amplía el criterio contractual del cliente ni autoriza Certification o
Production. El alcance ejecutado fue local Docker más el delta DDL ya autorizado
para Free/Development.

### Cola server-side en Free/Development

La migración local
`db/migrations/20260927_h3_admin_queue_facets_filter.sql` quedó aplicada en Free/
Development y registrada remotamente como `20260927044751`.

| Gate | Resultado |
|---|---|
| `admin_get_course_queue_filtered` | `SECURITY DEFINER`, `aal2`, editor activo, cursor y filtro institucional |
| `admin_count_course_queue_filtered` | `SECURITY DEFINER`, `aal2`, estados allowlisted e institución opcional |
| `admin_get_course_queue_facets` | `SECURITY DEFINER`, `aal2`, contadores agrupados y catálogo institucional |
| Grants | `EXECUTE` para `authenticated`/`service_role`; `PUBLIC`/`anon` revocados |
| Facets remotas con identidad `aal2` | `pending_review=350`, `quality pending=219`, `complete=131`, `17` instituciones |
| Filtro institucional remoto | `certus`: `56` filas; página de `5`; `hasNextPage=true` |
| Funciones legacy | Conservadas; no hubo `DROP FUNCTION` |
| Datos operativos | No se ejecutó backfill ni writer; miembros/invitaciones/auditoría no fueron mutados por el delta |

El hash del archivo aplicado es
`3dcbc296f50f25539edf3ddc6dbf171517070f6d673829ad548638148fc1f47c`.

La relectura remota final del 2026-09-27 fue read-only y conservó los mismos
facets: `pending_review=350`, calidad `pending=219`/`complete=131`, `17`
instituciones y sin errores RPC. Con los filtros iniciales de la cola
(`pending_review` + `complete`), `certus` devolvió `16` registros. No se ejecutó
ninguna escritura adicional en Free/Development durante esta relectura.

### UX/editor/preview local

- `AdminCourseQueue` muestra contadores de editorial y calidad con semántica de
  color: verde para completo/publicado, ámbar para pendiente/revisión, rojo para
  bloqueado y slate para archivado; cada estado tiene descripción contextual.
- La institución se elige desde el catálogo recibido por la RPC; no existe input
  libre ni mutación de `institution_id`.
- `page.tsx` del editor traduce labels, ayuda, propósito, impacto y acciones al
  español. `Guardar cambios`, `Publicar`, `Despublicar`, `Archivar` y la calidad
  conservan control de versión, auditoría, RBAC y `aal2`.
- La previsualización inferior consume `CoursePublicRenderer`, el mismo renderer
  visual usado por `CourseDetailClient`. El valor sin guardar actualiza el detalle
  en vivo; al cambiar de campo el editor desplaza y resalta automáticamente el
  bloque público correspondiente, y `Ver impacto` permite repetir el salto manual.
- El gate de assurance se comprueba antes de invocar RPCs protegidas en cola,
  editor y usuarios; el navegador no genera 403 prematuros antes del challenge.

### Validaciones Docker

| Check | Resultado |
|---|---|
| TypeScript | `PASS` |
| ESLint | `PASS` — 9 warnings históricos, 0 errors |
| Build normal | `PASS` — 243 páginas |
| Contratos focalizados | `16 passed` |
| UAT canónica local | `PASS` — 47/47 casos, 141/141 ejecuciones, 141 screenshots |
| PG17 harness con delta UX | `PASS` — `h3_pg17_harness_ok` |
| Credential scan | `PASS` |
| `git diff --check` | `PASS` |

UAT se ejecutó con mock local, PostgreSQL 17 local y `H3_EVIDENCE_DIR` temporal;
no se sustituyó la evidencia remota ni se almacenaron credenciales, códigos TOTP
o tokens.

### Hashes del candidato local

| Artefacto | SHA-256 |
|---|---|
| `web/src/components/courses/CoursePublicRenderer.tsx` | `03bffe13796bdfbdc648e8649ba538e6d9c54ce3d076a8f44529c4ca93ece7fe` |
| `web/src/components/admin/CourseLivePreview.tsx` | `b396eca318e123bf363f0047264f0db9aaca61cda86ddf04e7d8a219a0fe8136` |
| `web/src/components/AdminCourseQueue.tsx` | `986f28d33abdb6de1ab4da0862791ef61cecf1ab2c7072fc3738b173cb992b69` |
| `web/src/app/admin/edit/page.tsx` | `d6cafc0c42489a4bdaa38c119e1d507f156a217e2a3780629413a9fd10401b8e` |
| `tests/h3_local_uat.mjs` | `f8d8c79c64d72b25ef1b8ce26d63014bad47710f87d425ab19bf36d53075882d` |

### Transición y decisión de promoción

- `expand`: RPCs de lectura aditivas, renderer compartido, estados explicados y
  resaltado accionable.
- `compatibilidad`: RPCs legacy y detalle público existente permanecen activos;
  el login password-only y el enforcement `aal2` continúan funcionando.
- `deploy`: el candidato UX actual no fue publicado en Pages durante esta
  continuación.
- `contract`: pendiente de validación humana en el Preview y de la contracción
  posterior; no se retiró legacy.
- `rollback`: conservar el alias/deployment `ea787a8a` y retirar el delta UX solo
  mediante autorización separada; no se ejecutó rollback.

El estado contractual global permanece
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` por los gates remotos/documentales
restantes, `npm audit` con 16 HIGH y 1 CRITICAL, y la promoción protegida
pendiente. No se ejecutaron push, PR, merge, Certification, Production ni
promoción.

## Validación remota del candidato UX — 2026-09-27T16:18Z

Se consumió la autorización humana para publicar y validar únicamente el Preview
Free/Development. No se ejecutó merge, promoción, Certification ni Production.

### Trazabilidad de publicación

| Artefacto | Resultado |
|---|---|
| PR | `#500`, abierto hacia `desarrollo`, sin merge |
| Rama del PR | `feat/h3req1-development-remote-tests-v3` |
| Head del PR | `9d367f2f8ff487ec77080592946c4dfbdb2f34e1` |
| `security-audit` | `PASS` |
| Credential scan / protected paths / Python / ESLint / TypeScript / build / actionlint / DB gate | `PASS` |
| CodeQL aggregate y Analyze (`python`, `actions`, `javascript-typescript`) | `success` |
| Preview asociado al PR | `a8cf7db8`, `success`; branch URL hash no autorizado por `ADMIN_ALLOWED_HOSTS` |
| Rama que conserva el alias autorizado | `feat/h3req1-development-remote-tests` |
| Commit de sincronización frontend del alias | `5a9aeace32b14df4ff73b47918f7212d1fb985e2` |
| Deployment Pages del alias | `c0664c51-ed47-4c46-8ef7-e1a9a0e633d1`, `success` |
| Alias validado | `https://feat-h3req1-development-remo.studiamatch-aty.pages.dev` |

El branch URL hash del PR (`...-5f5c`) responde `404` en las rutas admin por la
allowlist de hosts Preview. Para no modificar configuración Auth/Cloudflare ni
Production, se sincronizó únicamente el frontend candidato con la rama que ya
corresponde al alias autorizado; Pages generó el deployment `c0664c51` y el
alias volvió a servir el candidato UX. No se expusieron credenciales.

### Smoke de rutas, red y consola

La matriz read-only contra el alias autorizado respondió `HTTP 200` en:

```text
/
/admin/
/admin/login/
/admin/auth/callback/
/admin/accept-invite/
/admin/setup-password/
/admin/reset-password/
/admin/users/
/courses/soyhenry/ai-automation-en-henry-carrera-de-inteligencia-artificial-aplicada-75d39c08/
```

El HTML de recovery no contiene `access_token`, `refresh_token` ni `token=`. En
Chrome DevTools, el login cargó todos los recursos con `200`/`304` y cero mensajes
de consola. La navegación no autenticada a `/admin/` produjo únicamente dos
warnings de preload de fuentes, sin errores JavaScript; no se observaron fallos
HTTP de assets, scripts o stylesheet.

### UAT editorial remota read-only

Con la sesión admin existente, activa y ya elevada, se observaron en el alias:

| Caso | Resultado |
|---|---|
| Panel y RBAC visible | `PASS`: rol `Admin`, enlaces `Cola editorial` y `Usuarios` |
| Facets iniciales | `PASS`: `131` visibles, editorial `pending_review=350`, calidad `pending=219`, `complete=131` |
| Filtro catalogado `Certus` | `PASS`: `16` filas; no existe input libre de institución |
| Búsqueda `Marketing` dentro de `Certus` | `PASS`: `2` filas |
| Filtro calidad `Pendiente` | `PASS`: `219` filas |
| Editor | `PASS`: copy en español, acciones `Guardar cambios`, `Publicar`, `Archivar` y `Actualizar calidad` |
| Previsualización compartida | `PASS`: renderer público visible debajo del editor |
| Actualización en vivo | `PASS`: el título sin guardar apareció simultáneamente en editor y preview |
| Resaltado y desplazamiento | `PASS`: `Ver impacto` resaltó el bloque y cambió el scroll de `891` a `831` |
| Responsive | `PASS` visual a `390px`: cola y controles permanecen utilizables; screenshot móvil capturado |
| Usuarios/RBAC | `PASS` read-only: tres membresías visibles, sin mutar rol ni estado |
| Escrituras | `NO EJECUTADAS`: no se pulsaron guardar/publicar/archivar/calidad, ni se modificó Auth/MFA |

La sesión ya existente permitió cargar las RPCs protegidas y el editor sin
mostrar una barrera MFA prematura. La continuidad de login + challenge TOTP +
operación `aal2` permanece acreditada por la evidencia remota del mismo ciclo
(`ea787a8a`); en esta pasada no se volvió a introducir un código ni se registró
ningún secreto MFA.

### Decisión del ciclo

El gate de candidato UX en Preview Development queda `PASS` para rutas, consola,
red, cola, filtros, editor, preview, responsive y RBAC read-only. El estado
contractual global permanece
`NO-GO_H3REQ1_DEVELOPMENT_REMOTE_VALIDATION` por `npm audit` (16 HIGH y 1
CRITICAL), gates de invitación/cleanup/rollback y promoción protegida pendientes.
La transición queda documentada como `expand -> compatibilidad -> deploy ->
contract`; la contracción legacy y el rollback no se ejecutaron.
