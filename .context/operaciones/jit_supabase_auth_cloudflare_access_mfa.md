# JIT — Supabase Auth + Cloudflare Access/MFA

Status: `JIT_A_JIT_B_PARTIAL_EVIDENCE_READY`
Fecha de actualización: 2026-09-03
Rama candidata local: `feat/h3-jit-supabase-admin-combined` desde `origin/desarrollo` `c675ef1`.

> Este documento consolida el paquete JIT-A/JIT-B y la evidencia de las acciones remotas ya ejecutadas bajo aprobaciones separadas. No autoriza acciones adicionales: la aplicación remota del delta `20260903`, la revalidación A6/A13, la dependencia de build, la configuración Auth pendiente, la certificación, el merge y el deploy conservan aprobaciones independientes.

## 1. Objetivo

1. Dejar listo y reproducible el paquete JIT-A **Supabase Free/Auth**: inventario read-only previo, habilitación de Auth email/password, MFA TOTP, aplicación de migraciones H3 en Free, bootstrap de membresías admin/user de prueba y validación remota de MFA real con sesión `aal2`. La evidencia ejecutada cubre el payload hasta `20260902`; el payload candidato añade `20260903` y exige revalidación A6/A13.
2. Dejar listo y reproducible el paquete JIT-B **Cloudflare Access/DNS**: `admin.studiamatch.com` protegido por Cloudflare Access como perímetro del panel editorial, `studiamatch.com/admin/` con HTTP 404, redirect URLs de Auth y validación de la integración. La ejecución actual valida solo E1/E3/E4/E8; E2/E5/E6/E7 siguen pendientes.
3. Ejecutar **todas las pruebas ejecutables hoy sin JIT** (validación offline Docker) y dejar la matriz de pruebas remotas que se ejecutarán tras cada aprobación.

## 2. Contexto Y Referencias

- Estado vigente: `H3_PR_DEVELOPMENT_READY_LOCAL`; `origin/desarrollo` permanece en `c675ef1` y la rama candidata local contiene el paquete documental JIT-A/JIT-B y el fix de contrato.
- Secuencia de entrega: pasos 10–12 del [Plan Vinculante Nuevo Pedido](../operaciones/plan_vinculante_nuevo_pedido_2026_08_25.md): JIT Free/Auth independiente; Cloudflare DNS/Access en otra aprobación JIT (no agrupada por defecto).
- Criterios objetivo (ver [HITO-003](../hitos/hito_003.md)): H3-CA4.7 (MFA/aal2), H3-CA4.8 (Edge Function invitación) y H3-CA4.9 (hostname/perímetro).
- Contrato de aceptación de Edge/Perímetro (HITO-003): "Cloudflare Access protege `admin.studiamatch.com`; `studiamatch.com/admin/` responde HTTP 404 y no sirve el panel"; "invitación de usuarios por correo mediante Edge Function protegida con `verify_jwt=true`; `service_role` nunca llega al navegador".
- `plan_vinculante` Testing: "La prueba de Cloudflare Access/MFA perimetral requiere JIT Cloudflare y no puede simularse como evidencia de producción únicamente con el mock local. Supabase Auth MFA y el enforcement `aal2` deben probarse además en Free con JIT separado."
- AGENTS.md: fuente de verdad de refs/envs; contrato de credenciales (`apikey` vs `Authorization: Bearer`); regla de Docker para todo comando de desarrollo.

## 3. Inventario De Artefactos Relevantes (estado actual del repo)

| Artefacto | Estado | Nota |
|---|---|---|
| `web/src/lib/admin-auth.ts` | Presente | Login password grant, `listFactors`, `enrollTotp`, `challengeTotp`, `verifyTotp`, `unenrollTotp`, refresh, logout, `resolveAal`; sesión en `sessionStorage` + cookie `studiamatch_admin_session` (riesgo pre-Certification ya documentado). |
| `web/src/app/admin/login/page.tsx` | Presente | Panel "Registra tu autenticador" (QR `data:image`, secreto, otpauth URI). |
| `db/migrations/20260828_h3_admin_auth.sql` | Presente | Tabla `public.admin_members` + `admin_current_user_role`. |
| `db/migrations/20260829_h3_rbac_users.sql` | Presente | `admin_list_members`, `admin_create_member(p_email,p_role)`, `admin_is_active_editor`, auditoría. |
| `db/migrations/20260830_h3_expanded_contract.sql` | Presente | `admin_has_aal2`, `admin_require_aal2` (gates `aal2` en mutaciones), gestión membresías con invariante último admin. |
| `db/migrations/20260902_h3_pr_contract.sql` | Presente | Reafirma `admin_require_aal2` en contract y lector efectivo. |
| `db/migrations/20260903_h3_rbac_contract_fix.sql` | Presente | Delta idempotente para corregir A6/A13; validado en harness PG17, pendiente de aplicación remota y nueva matriz A. |
| Migraciones H3 en Free | **Aplicadas hasta 20260902** | JIT-A remoto ejecutado sobre Free; `20260903` aún requiere aprobación JIT DDL separada. |
| `supabase/functions/send-lead-emails/index.ts` | Presente (legacy H1) | Única Edge Function existente. |
| Edge Function de invitación | **No existe** | Código a construir (ver dependencia 6.1). |
| Pages Function / Worker para 404 público | **No existe** | Solo emulado por `mock-server/static-server.js` local. |
| `web/public/_headers` | Presente | Cabeceras estáticas. |
| `mock-server/` | Presente | Emulación local de perímetro y host-mapping para UAT. |
| `.context/evidencia/h3-expanded/` | Presente | UAT local canónica 47/47 y 141/141 PASS (corrida 2026-09-02). |

## 4. Autorizaciones

Paquetes separados (no se agrupan por defecto). Frases de aprobación esperadas al final del documento.

| Paquete | Alcance | Bloquea |
|---|---|---|
| **JIT-A** | Supabase Free (`aqrldlmlszjtgpqiegaa`): inventario read-only, Auth email/password + MFA TOTP, migraciones H3 (JIT DDL Free), bootstrap membresías y validación MFA real `aal2`. | Cierre H3-CA4.7 y prueba remota de RPC `admin_*` con `aal2`. |
| **JIT-B** | Cloudflare (cuenta/proyecto Pages `studiamatch`, zona `studiamatch.com`): DNS/custom domain `admin.studiamatch.com`, Access application+policy, edge 404 público y smoke. | Cierre H3-CA4.9 y pruebas perimetrales reales. |
| **Dependencia build** | Construcción (código + PR) de la Edge Function de invitación y del mecanismo de 404 público (Pages Function/Worker) si se elige esa vía. | H3-CA4.8 y, según vía elegida, parte de H3-CA4.9. |

## 5. Paquete JIT-A — Supabase Free/Auth (MFA TOTP)

### 5.1 Preflight read-only (antes de cualquier cambio)

Comandos/consultas de diagnóstico que no escriben nada:

1. Confirmar proyecto y claves presentes sin imprimir valores:
   `supabase list` / MCP `supabase-free`; verificar ref `aqrldlmlszjtgpqiegaa` y URL `https://aqrldlmlszjtgpqiegaa.supabase.co`.
2. Verificar disponibilidad de **MFA TOTP en el plan Free** (Dashboard → Authentication → Multi-factor authentication). Si TOTP no está disponible en Free, detener JIT-A y escalar antes de configurar (riesgo de disponibilidad de plan, no se asume).
3. Estado Auth actual: proveedores habilitados, signup público, confirmación de email, Site URL/redirect URLs. Registrar estado previo para rollback.
4. Inventario migraciones: `supabase_migrations` en Free vs `db/migrations/*.sql` H3 (esperado: H2 aplicadas; H3 ausentes).
5. Inventario de usuarios/membresías existentes en `auth.users` y `public.admin_members`.
6. Verificar que NO existe `public.exec_sql` expuesto para `anon`/`authenticated` (restringido a `service_role`). Cualquier DDL usa vía autorizada por JIT DDL Free.

### 5.2 Configuración Auth

Cambios de configuración (Dashboard Authentication o Management API; verificar rutas exactas en la UI durante el JIT):

1. Proveedor Email habilitado con email + password.
2. **Signup público deshabilitado**; anonymous sign-ins deshabilitado.
3. Confirmación de email: definir política. Los usuarios de prueba se crean con `email_confirm=true` vía Management API o Dashboard.
4. **Site URL**: `https://admin.studiamatch.com`. Redirect URLs adicionales (según despliegue de prueba previo a certificación): `https://*.studiamatch.pages.dev/*`, `http://localhost:3000/*`.
5. **MFA**: habilitar factor TOTP (app authenticator). Decidir y registrar si se activa "Enforce" a nivel Auth: la aplicación ya enforce `aal2` en RPC (`admin_require_aal2`); mantener enforcement a nivel RPC (no romper invitación), salvo decisión contraria documentada.
6. Mantener `service_role`/secret fuera del navegador (solo server/CI).

### 5.3 Migraciones H3 en Free (JIT DDL Free)

Aplicar únicamente tras aprobación JIT-A con payload exacto. Archivos candidatos (mismo artefacto que pasó harness PG17 y db-gate):

- `db/migrations/20260828_h3_admin_auth.sql`
- `db/migrations/20260828_h3_admin_course_queue_view.sql`
- `db/migrations/20260828_h3_admin_editorial_reader_rpc.sql`
- `db/migrations/20260828_h3_admin_editorial_rpc.sql`
- `db/migrations/20260828_h3_admin_queue_rpc.sql`
- `db/migrations/20260829_h3_rbac_users.sql`
- `db/migrations/20260830_h3_expanded_contract.sql`
- `db/migrations/20260902_h3_pr_contract.sql`
- `db/migrations/20260903_h3_rbac_contract_fix.sql` — delta posterior al hallazgo remoto A6/A13; aplicar únicamente con aprobación JIT DDL separada.

**Exclusiones**: `db/seeds/h3_admin_seed_local.sql` es SOLO local Docker (datos de prueba no se promueven). No DML operativo, no backfill. La evidencia histórica A1–A14 cubre el payload hasta `20260902`; A6/A13 deben repetirse después de aplicar `20260903`. Esta incorporación documental no afirma que el delta remoto ya haya sido aplicado.

Post-apply verificaciones read-only: funciones presentes (`admin_current_user_role`, `admin_is_active_editor`, `admin_has_aal2`, `admin_require_aal2`, `admin_list_members`, `admin_create_member`), tabla `admin_members`, políticas RLS, `h3_*_contract` lector efectivo.

### 5.4 Bootstrap de membresías de prueba

1. Crear usuario admin inicial (email confirmado) vía Dashboard/Management API.
2. Insertar su membresía: `INSERT INTO public.admin_members (user_id, role, is_active) VALUES (…, 'admin', true);` (SQL Editor/service_role; la invariante "último admin" se aplica luego por RPC).
3. Crear un segundo usuario `user` y añadir membresía usando la RPC `admin_create_member(p_email, p_role)` desde sesión admin activa (ejercita RPC + auditoría). Mantener al menos un admin activo en todo momento.

### 5.5 Validación remota MFA real (JIT-A) — matriz de pruebas

Ejecutar contra Free real tras JIT-A. Cada caso con evidencia (captura/curl + salida):

| # | Prueba | Esperado |
|---|---|---|
| A1 | Login password (usuario `admin` confirmado) | Sesión `aal1`; factores listables. |
| A2 | Enrollment TOTP (factor nuevo) | Devuelve factor id + secreto/QR; factor `unverified`. |
| A3 | Challenge + verify con código correcto | Sesión `aal2` (claim `aal` en JWT). |
| A4 | Challenge + verify con código incorrecto/reusado | Rechazo; sin promoción a `aal2`. |
| A5 | Mutación editorial/RPC sensible con token `aal1` | `MFA aal2 required` (enforcement RPC). |
| A6 | Misma mutación con token `aal2` | Éxito + auditoría append-only. |
| A7 | Refresh token | Renueva sesión conservando `aal2`. |
| A8 | `aal1` rechazado en cola/lectura sensible según contrato | Comportamiento contract. |
| A9 | Unenroll/revocación de factor | Factor eliminado; sesión degradada/rechazada según contrato. |
| A10 | Logout | Sesión cerrada; sin acceso residual. |
| A11 | Usuario autenticado sin membresía activa | Bloqueado. |
| A12 | Segundo usuario `user` con membresía activa | Solo edita `missing_fields`; negativos admin rechazados. |
| A13 | Invariante último admin (desactivar/cambiar último admin activo) | Rechazado. |
| A14 | Segunda corrida `NOOP` | Sin drift; misma salida. |

### 5.6 Dependencia abierta: Edge Function de invitación (H3-CA4.8)

- **No existe código** (`supabase/functions/` solo tiene `send-lead-emails` legacy).
- Requiere build funcional separado (rama `feat/*`, PR protegido a `desarrollo`, allowlist `protected-paths` actualizada): Edge Function `admin-invite` (o equivalente) con `verify_jwt=true`, invocada desde el panel, que crea el `auth.users` (invite email confirmado/`invite_user`) y ejecuta membresía + auditoría con secret key en servidor; nunca en navegador.
- Pruebas de invitación real (email válido/inválido/duplicado/rol inválido) quedan bloqueadas hasta ese build. Este paquete JIT-A queda **parcial** respecto a H3-CA4.8 y no cierra el criterio sin esa dependencia.

## 6. Paquete JIT-B — Cloudflare Access/DNS (perímetro admin)

### 6.1 Preflight read-only Cloudflare

1. Verificar zona `studiamatch.com`, proyecto Cloudflare Pages `studiamatch`, build/production branch (`main` → producción; `desarrollo` → preview `.pages.dev`).
2. Verificar si hay una aplicación/Worker/Pages Function que hoy sirva el panel por hostname administrativo y si ese hostname apunta al proyecto/deployment correcto del ambiente bajo prueba.
3. Inventariar IdPs disponibles en Zero Trust para la política Access (Cloudflare/One-time PIN/correo u otro IdP con MFA).
4. No asociar `admin.studiamatch.com` al proyecto público si se pretende validar una rama preview: ese custom domain pertenece al deployment de producción del proyecto actual y no representa automáticamente `desarrollo`.

### 6.2 DNS + hostname

1. Separar explícitamente el hostname por ambiente antes de una nueva UAT perimetral:
   - producción: `admin.studiamatch.com` → proyecto administrativo de producción, rama `main`;
   - desarrollo: alias de rama estable o hostname administrativo de preview dedicado, nunca el custom domain de producción;
   - certificación: hostname/preview dedicado de `certificacion`.
2. Para una separación de bajo riesgo, conservar `studiamatch-aty.pages.dev` como dominio del proyecto y usar las URLs de commit como evidencia inmutable; si el alias estable de rama no está disponible/configurado para Pages, crear un proyecto Pages administrativo separado por ambiente o una ruta/Worker explícita con destino preview.
3. Añadir DNS/custom domain únicamente después de confirmar el destino del ambiente; tráfico proxy y Universal SSL deben validarse sobre ese destino, no asumirse por el nombre.
4. Registrar CNAME/DNS, deployment ID, commit SHA, rama y estado de certificado en la evidencia de cada corrida.

### 6.3 Edge 404 público `studiamatch.com/admin/`

- Hoy **no existe** Pages Function/Worker en el repo que implemente el 404 por hostname (solo emulado en `mock-server/static-server.js`).
- Vías posibles a decidir/ejecutar durante JIT-B (infra o código, según aprobación):
  1. Pages Function en el proyecto (raíz `functions/admin/[...].ts`) que responda 404 para host `studiamatch.com` y continue (`ctx.next()`) para `admin.studiamatch.com`; o
  2. Worker de zona para `studiamatch.com/admin/*` con respuesta 404; o
  3. Proyecto Pages separado para el panel (solo `admin.studiamatch.com`).
- Si la vía exige código nuevo (funciones/wrangler) ⇒ depende de build separado y PR protegido (mismo criterio que 5.6). Sin esa pieza, `studiamatch.com/admin/` podría seguir sirviendo el export estático (que incluye `/admin`) en producción. **No se simula como evidencia de producción con el mock local** (plan vinculante).

### 6.4 Cloudflare Access (MFA de perímetro)

1. Zero Trust → Access → Applications: crear una aplicación self-hosted por ambiente/hostname. La app administrativa de producción protege `admin.studiamatch.com`; una prueba de `desarrollo` debe proteger el hostname/preview que realmente apunta al deployment de `desarrollo`.
2. Política: permitir acceso tras autenticación del IdP elegido. Definir factor MFA en la política/IdP:
   - La policy debe permitir al usuario/grupo de prueba y la configuración del IdP debe ser compatible con esa policy. `restrict_to_account_members=true` obliga a que cada identidad que atraviese el IdP sea miembro del account Cloudflare; un selector de email no sustituye esa membresía.
   - La MFA de aplicación real (TOTP/`aal2`) la exige Supabase dentro del panel. Documentar capa por capa: perímetro Access (identidad/MFA de entrada) → Supabase Auth (login) → TOTP `aal2` (mutaciones sensibles).
   - Registrar IdP, duración de sesión, miembros aceptados, policy exacta, hostname, deployment ID, commit SHA y rama.
3. No exponer rutas del panel por otro hostname. Si el dominio Pages directo/preview permite bypass del custom domain, protegerlo o deshabilitarlo explícitamente para el panel.

### 6.5 Redirect URLs / entorno Supabase

- Con Access activo, confirmar Site URL/redirect URLs de Auth apuntando al hostname administrativo del ambiente bajo prueba, no siempre a producción: `admin.studiamatch.com` solo para producción; hostname/preview de `desarrollo` para Development; hostname de `certificacion` para Certification.
- Variables de entorno (nombres, sin valores): `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` en GitHub env `Development`/`Certification` y en el proyecto Pages correspondiente. Nunca reutilizar el endpoint/key de producción en el preview de desarrollo.
- Registrar explícitamente el par `hostname → Supabase project ref` en cada evidencia para impedir pruebas cruzadas.

### 6.6 Validación perimetral real (JIT-B) — matriz de pruebas

| # | Prueba | Esperado |
|---|---|---|
| E1 | `curl -I` del hostname administrativo del ambiente sin sesión Access | Redirección a login de Access (302 a `{team}.cloudflareaccess.com/…`), registrando rama/SHA/deployment. |
| E2 | Acceso tras autenticación Access (factor perimetral) | `200` en `/admin/login`/panel del mismo ambiente; no se valida contra `admin.studiamatch.com` si la prueba es `desarrollo`. |
| E3 | `curl -I https://studiamatch.com/admin/` y equivalente `www` | `404`, no sirve panel público. |
| E4 | `curl -I https://studiamatch.com/` y `www` | `200` normal (sin regresión pública). |
| E5 | Login Supabase + enrollment/verify TOTP dentro del hostname del ambiente | Sesión `aal2`; QR/secreto visibles; RPCs sensibles OK y project ref correcto. |
| E6 | Negativos: `aal1` en mutación, usuario sin membresía, código MFA inválido | Rechazo (misma expectativa A5/A11/A4). |
| E7 | Headers/cabeceras en panel y público | Sin leaks; cabeceras estáticas presentes; no bypass por URL hash/dominio Pages. |
| E8 | Segunda corrida `NOOP` y revisión advisors | Sin drift; deployment/branch/hostname constantes; sin hallazgos HIGH/CRITICAL. |

## 7. Pruebas Ejecutadas Hoy (offline, Docker) — Resultado Local

Rama `feat/h3-jit-supabase-admin-combined` desde `origin/desarrollo` (`c675ef1`), dentro de `studiamatch-dev`. Fecha de esta revalidación: 2026-09-03.

| Validación | Resultado |
|---|---|
| `find scripts -name '*.py' -exec python3 -m py_compile {} \;` | PASS |
| `scripts/maintenance/h2_scan_unauthorized_writers.py` | PASS (writer scan passed) |
| `pytest` (subset CI: credentials contract, security flow, obsidian state, requirement client source, editorial contract, H2 editorial/backfill/client docs/legacy compat/pro migration controls/pipeline/writer scan) | **142 passed** |
| `npm run lint` | PASS — 0 errores, 9 warnings históricos |
| `npx tsc --noEmit` | PASS |
| `npm run build` y `npm run build:mock` | PASS — rutas estáticas exportadas: `/`, `/admin`, `/admin/edit`, `/admin/login`, `/admin/users`, `/compare`, `/courses`, `/courses/[institution]/[slug]` (SSG) |
| `scripts/security/h2_web_mock_smoke.sh` | PASS (`h2_web_mock_smoke_ok`) |
| `scripts/security/scan_credentials.sh --tree` y `--diff origin/desarrollo HEAD` | PASS (credential scan passed) |
| `actionlint` y `shellcheck` sobre workflows/hooks/scripts | PASS (Docker) |
| `git diff --check` (origin/desarrollo..HEAD) | Limpio |
| H2/H2-Pro/H3 PG17 (`h3_pg17_harness.sql`, incluyendo regresión A6/A13) | PASS — `h3_pg17_harness_ok` |

**Estado tras el PR mergeado y la primera UAT remota:** `20260903` ya está aplicado en Free y A6/A13 fueron validados con el ambiente limpio al cierre. La prueba de membresía Cloudflare para `romelhc95@gmail.com` también fue aceptada. Permanecen no cerrados: UAT administrativa E2/E5/E6/E7 contra el deployment correcto de `desarrollo`, separación Pages/Access por ambiente, configuración Auth por hostname, invitación Edge Function, mecanismo 404 público estable, UAT en Free/Certification y promoción. La UAT local con mock (47/47 y 141/141) no es evidencia de producción para Access/MFA perimetral. `pytest -q` global no es gate válido en este checkout porque recoge worktrees históricos y pruebas de integración fuera del alcance; el job CI usa el subset anterior.

## 8. Rollback

JIT-A:
- Si MFA/TOTP rompe flujo: deshabilitar factor/“Enforce” y revertir usuarios de prueba (no borrar último admin activo).
- Migraciones H3 en Free: deltas funcionales versionados; si algo rompe, se revierte con delta inverso aprobado o se re-aplica desde baseline H2 verificado en Free; nunca se corrige Pro desde Free.
- Ledger/evidencia de cada paso (read-only pre/post) para auditoría.

JIT-B:
- Quitar Access application/policy (vuelve a exposición directa si el custom domain sigue).
- Remover custom domain/DNS o apuntar de vuelta; revocar Worker/Pages Function si se añadió; purgar caché.
- Orden de contracción: Access primero, DNS después, para no dejar `admin` abierto en otro hostname.

## 9. Seguridad Y Contrato De Credenciales

- Sin credenciales en repo/PR; solo referencias por nombre a variables de entorno.
- Data API con `apikey` (publishable/secret); JWT de sesión solo en `Authorization: Bearer`. Nunca secret como bearer.
- `service_role` solo server/CI/Edge Function (invitación). Navegador solo publishable.
- MFA decisions en `raw_app_meta_data`/claims `aal` (JWT), nunca en `user_metadata` (editable por usuario).
- CORS Free: abierto por defecto (riesgo aceptado, datos públicos); en Pro restringir a `https://studiamatch.com` y `https://admin.studiamatch.com`.

## 10. Stop Conditions

- Falta la aprobación JIT-A o JIT-B separada (este documento no la sustituye).
- MFA TOTP no disponible en Free (se escala antes de configurar).
- Drift entre lo verificado localmente y lo observado en Free/Cloudflare (detener y consultar).
- Cualquier secreto/PII en outputs/PRs.
- No hay Gates HIGH/CRITICAL pendientes; cada waiver con causa, evidencia, owner, riesgo, vencimiento y aprobación humana.

## 11. Siguientes Pasos

1. Mantener `studiamatch.com`/`www.studiamatch.com` como público de producción (`main`) y no usarlos para UAT de `desarrollo`.
2. Validar `desarrollo` mediante la URL de commit `88f02c53.studiamatch-aty.pages.dev` o un alias estable real de rama; registrar deployment ID, SHA y Supabase Free ref.
3. Corregir la topología Pages/Access: `admin.studiamatch.com` queda reservado al panel de producción; desarrollo y certificación requieren hostnames/targets administrativos propios o proyectos/artefactos separados.
4. Crear policies Access separadas por ambiente; proteger también dominios Pages directos si permiten bypass.
5. Configurar Auth Site URL/redirects y keys por ambiente; repetir E2–E8 únicamente contra el deployment correcto.
6. Implementar Edge Function de invitación y mecanismo 404 público estable antes de promover H3 a `main`.
7. Ejecutar UAT completa sobre `desarrollo` + Free; después PR protegido a `certificacion`, UAT completa allí y finalmente PR a `main` + validación Pro/producción.

## 12. Frases De Aprobacion Esperadas

```text
Apruebo JIT-A Supabase Free/Auth para el paquete .context/operaciones/jit_supabase_auth_cloudflare_access_mfa.md sobre el proyecto Free aqrldlmlszjtgpqiegaa, exclusivamente para: inventario read-only, habilitación Auth email/password, MFA TOTP, aplicación de las migraciones H3 listadas hasta `20260902` y del delta `20260903` solo si se aprueba expresamente, bootstrap de membresías de prueba y validación remota de MFA aal2. No autorizo Pro, DML operativo, seed local en remoto, writers, schedules, deploys ni push/PR/merge.

Apruebo JIT-B Cloudflare Access/DNS para el paquete .context/operaciones/jit_supabase_auth_cloudflare_access_mfa.md, exclusivamente para: custom domain admin.studiamatch.com, aplicación/política Cloudflare Access con MFA de perímetro, edge 404 público de /admin y smoke perimetral. No autorizo cambios de código de aplicación fuera de la vía aprobada, push/PR/merge ni deploy de producción.

Apruebo la dependencia build de la Edge Function de invitación y/o Pages Function/Worker de 404 público como feat/* con PR protegido a desarrollo, con allowlist protected-paths actualizada.
```
