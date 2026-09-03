# Evidencia JIT-A — Supabase Free Auth (email/password + MFA TOTP)

- **Fecha de ejecución remota**: 2026-09-02
- **Fecha de actualización documental**: 2026-09-03
- **Proyecto**: Free `aqrldlmlszjtgpqiegaa` (`https://aqrldlmlszjtgpqiegaa.supabase.co`)
- **Autorización**: frase humana `Apruebo JIT-A Supabase Free/Auth`
- **Payload remoto ejecutado**: `db/migrations/20260828_h3_admin_auth.sql`, `20260828_h3_admin_course_queue_view.sql`, `20260828_h3_admin_editorial_reader_rpc.sql`, `20260828_h3_admin_editorial_rpc.sql`, `20260828_h3_admin_queue_rpc.sql`, `20260829_h3_rbac_users.sql`, `20260830_h3_expanded_contract.sql`, `20260902_h3_pr_contract.sql`
- **Delta posterior incorporado al payload candidato**: `db/migrations/20260903_h3_rbac_contract_fix.sql` (validado localmente en PG17; **no aplicado remotamente todavía** y no cubierto por la matriz A1–A14 histórica).
- **Alcance ejecutado**: preflight + aplicar migraciones H3 hasta `20260902` en Free + bootstrap membresías de prueba + matriz remota A1–A14. Sin push/PR/merge/deploy/config de Dashboard durante JIT-A.
- **Alcance candidato para el PR**: el payload remoto anterior más `20260903_h3_rbac_contract_fix.sql`; este delta fue validado localmente en PG17 y queda pendiente de aplicación remota y repetición de A6/A13 bajo aprobación JIT DDL separada.

## Preflight (read-only)
- `auth.users` = 0 antes del bootstrap; migraciones H3 ausentes (última `h2_development_legacy_public_compat` 20260826164745); sin `public.handle_updated_at` previo.
- `public.exec_sql` existe como función pero `anon`/`authenticated` no pueden invocarla.
- Config Auth no legible por DB (`auth.instances` vacía); no hay Management API token en el entorno del agente (toggles de Dashboard no ejecutables por el agente).

## Migraciones aplicadas (todas success; registradas en `supabase_migrations.schema_migrations`)
Orden exacto del payload. Verificación post-DDL:
- Tablas: `admin_members`, `admin_membership_audit` (append-only, triggers), `admin_course_queue`.
- Funciones `admin_*` en `public`: **17/17** presentes.
- RLS `admin_members`: policies solo `service_role`. `admin_membership_audit`: RLS habilitado, sin policies explícitas (BYpass service_role).

## Bootstrap
Usuarios Auth creados vía Admin API (service role), email confirmado:
| Rol | Email | ID |
|---|---|---|
| admin | jit-h3-admin@dev.studiamatch.test | cff393ca-7ca8-40db-82d0-d85af4670bba |
| user | jit-h3-user@dev.studiamatch.test | b67b0817-fc8c-412a-9b0b-739af9859eb0 |
| invite | jit-h3-invite@dev.studiamatch.test | 6b2e5856-2987-4a8c-bbe6-26eaa0ed61f9 |

Membresía admin para cff393ca insertada directa (SQL). Estado final memberships: admin (activo) + user rol `user` (activo, vía RPC `admin_create_member`); audit `invite` = 1. Factores MFA finales de los 3 usuarios: **0** (limpio tras pruebas; snapshots de factors `verified` capturados en el proceso).

## Hallazgos de plataforma GoTrue (Free)
1. Tokens firmados **ES256**; el endpoint real de verify es `POST /auth/v1/factors/{factor_id}/verify` (la ruta `/challenge/verify` devuelve `404 page not found`).
2. `GET /auth/v1/factors` (listar) devuelve 405 en este despliegue; la lista de factores se verifica por SQL en `auth.mfa_factors`.
3. Enrolar un factor adicional requiere sesión `aal2` (`insufficient_aal: AAL2 required to enroll a new factor`); el primer factor se enrola con sesión `aal1`.
4. Desenrolar (un-enroll) un factor verificado requiere `aal2` (`insufficient_aal: AAL2 required to unenroll verified factor`).
5. `DELETE /auth/v1/factors/{id}` con token aal2 responde 200 y elimina la fila en `auth.mfa_factors` (verificado: factor e1ab3778-83a5-488e-8d2f-52723040d69b eliminado).
6. TOTP está disponible y funcional en el plan Free (enroll 200 + verify 200 → `aal2`).

## Resultados matriz A (remota, Free; payload ejecutado hasta 20260902)
| Id | Caso | Resultado |
|---|---|---|
| A1 | Login email/password → `aal1` | PASS |
| A2 | Enroll TOTP (primer factor, sesión aal1) | PASS |
| A3 | Verify código correcto → token `aal2` | PASS |
| A4 | Verify código incorrecto → 422 `mfa_verification_failed` | PASS |
| A5 | `admin_list_members` con sesión aal1 → 400 `MFA aal2 required` | PASS |
| A6 | `admin_list_members` con sesión aal2 (payload remoto hasta 20260902) | **FAIL — bug contrato 42804; requiere repetir tras aplicar 20260903** |
| A7 | Refresh mantiene `aal2` | PASS |
| A8 | Cola editorial con sesión aal1 → 400 `MFA aal2 required` | PASS |
| A9 | Un-enroll factor (DELETE con aal2) → 200 y fila eliminada | PASS |
| A10 | Logout → 204 (token vigente hasta expiración, comportamiento JWT GoTrue) | PASS |
| A11 | Miembro sin rol no puede operar cola (error `User is not an active editor`, 200 con columna error) | PASS (semántica revisada) |
| A12a | `admin_create_member` invitación positiva (rol `user`) + audit `invite` | PASS (corrida 1) |
| A12-dup | Email duplicado → `Duplicate email: membership already exists` | PASS |
| A12b | `user` no puede `list_members` (`User is not an active admin`) | PASS |
| A12c | `user` `admin_user_can_edit_field` y rechazo `admin_update_course` (`User is not allowed to edit field: name`) | PASS |
| A13 | `admin_update_member` (payload remoto hasta 20260902) | **FAIL — bug contrato 42702; requiere repetir tras aplicar 20260903** |
| A14 | Segunda corrida NOOP read-only, sin drift (snap_a == snap_b: 17 funciones / 2 members / 1 audit / 227 courses activos / 59 migraciones) | PASS |

## Hallazgos de contrato (requieren fix + PR)
1. **A6 → 42804**: `admin_list_members` declara RETURNS `email TEXT` pero `auth.users.email` es `varchar(255)`: `Returned type character varying(255) does not match expected type text in column 2`. Origen: `db/migrations/20260829_h3_rbac_users.sql`. Visible solo en runtime con datos.
2. **A13 → 42702**: `admin_update_member` referencia columna `role` sin calificar; OUT param de `RETURNS TABLE` colisiona: `column reference "role" is ambiguous`. Origen: `db/migrations/20260830_h3_expanded_contract.sql`. Mismo riesgo para `is_active`. Visible solo en runtime con datos. El delta correctivo `20260903_h3_rbac_contract_fix.sql` renombra la variable local conflictiva y califica las referencias; su resultado remoto aún no está certificado.
Ambos bugs NO fueron detectados por el harness PG17 (sin filas en `auth.users` en la prueba).

## Estado posterior y bloqueos
- El fix A6/A13 está versionado en `db/migrations/20260903_h3_rbac_contract_fix.sql`, incluido en el payload candidato del PR y validado en el harness PG17 con regresión explícita. La aplicación remota en Free y la nueva corrida A6/A13 PASS requieren aprobación JIT DDL separada; no se afirma que ya estén aplicados.
- Toggles de configuración Auth (Site URL `https://admin.studiamatch.com`, allowlist, disable public signup, policies provider) requieren Dashboard/Management API humana; permanecen pendientes.
- El PR a `desarrollo` contiene solo artefactos versionados y no autoriza por sí mismo la aplicación del delta remoto, cambios de configuración, Pro, deploy ni promoción.
