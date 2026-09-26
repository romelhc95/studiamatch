# Evidencia H3 Invitation Flow Frontend Auth

Estado: `H3-BUILD-03B-FRONTEND_AUTH_LOCAL_VALIDATED_WITH_RESIDUALS`

Fecha: 2026-09-22

## Alcance

Se implemento localmente el consumidor frontend del contrato H3-BUILD-03B sin
modificar Edge Functions, migraciones SQL, Supabase remoto, configuracion MFA ni
deploy.

## Cambios

- Cliente browser oficial `@supabase/supabase-js` configurado con `flowType: 'pkce'`,
  `persistSession`, `autoRefreshToken` y `detectSessionInUrl: false`.
- `exchangeCodeForSession()` y `updateUser({ password })` delegados al SDK oficial.
- Callback `/admin/auth/callback/` con exchange unico por montaje, limpieza de URL,
  aceptacion RPC y destinos internos constantes.
- Pantalla `/admin/accept-invite/` para accepted, password pending, ready,
  expired, revoked, superseded y sesion no disponible.
- Pantalla `/admin/setup-password/` con validacion local, actualizacion Auth antes
  de `admin_complete_password_setup()` y sin password en el RPC.
- Slash redirects para las tres rutas nuevas.
- Compatibilidad de login y MFA conservada porque el backend editorial vigente
  continua requiriendo `aal2` para operaciones legacy.
- Panel de usuarios preparado para estado de invitacion, `account_status` y
  expiracion; el RPC legacy actual solo devuelve email, rol, activo y created_at,
  por lo que se muestra `No expuesta` sin inferir estados.
- Mock Auth ampliado con grant PKCE one-shot, update password y RPC onboarding.

## Validaciones ejecutadas en Docker

| Check | Resultado |
|---|---|
| `npx eslint` | PASS, 0 errores; 9 warnings preexistentes fuera del delta frontend Auth |
| `npx tsc --noEmit` | PASS |
| `npm run build` | PASS, compilacion estatica |
| `npm run build:mock` | PASS, compilacion estatica con mock |
| `python3 -m unittest tests.test_h3_invitation_callback_contract -v` | PASS, 4 tests |
| `bash scripts/security/scan_credentials.sh` | PASS |
| `git diff --check` | PASS |
| `npm audit --omit=dev --audit-level=high` | NO-GO independiente: vulnerabilidades transitorias preexistentes/dependientes, con 16 high y 1 critical reportadas por npm; no se ejecuto `npm audit fix` porque puede alterar el baseline fuera del alcance |

## Casos cubiertos por contrato frontend

- callback valido y exchange PKCE oficial;
- callback sin code, error Auth y replay sanitizado;
- limpieza del code antes de navegar;
- aceptacion expirada, revocada, superseded, mismatch y usada;
- sesion inexistente para status/setup;
- password corta, debil, no coincidente y valida;
- orden Auth password update -> RPC complete;
- password nunca enviada al RPC;
- rutas internas sin `next` externo ni open redirect.

## Expand -> compatibilidad -> deploy -> contract

- `expand`: cliente SDK, callback, pantallas y mock agregados; no se reescriben
  migraciones historicas.
- `compatibilidad`: login legacy, MFA obligatorio vigente, RPCs existentes y
  cuentas `ready` se conservan.
- `deploy`: pendiente de aprobacion JIT, configuracion Auth por ambiente y UAT
  remota; no ejecutado.
- `contract`: pendiente de UAT H3 completa y de una evolucion backend que exponga
  estados de invitacion al listado administrativo; no se retira MFA ni legacy.
- Rollback: retirar las nuevas rutas/cliente sin tocar filas Auth/DB ni invalidar
  cuentas legacy.

## Riesgos residuales

1. El login no puede eliminar TOTP mientras las RPC editoriales existentes
   mantengan `admin_require_aal2()`; se preservo deliberadamente.
2. El listado administrativo no puede mostrar valores reales de invitacion,
   `account_status` y expiracion para cada miembro con la firma legacy actual.
3. El mock valida el contrato local, pero no acredita correo real, Auth remoto,
   redirect allowlist remoto ni reloj/TTL remoto.
4. `npm audit` conserva hallazgos transitorios altos/criticos que requieren una
   remediacion de dependencias separada.

## Siguiente checkpoint

`H3-UAT`: ampliar Playwright con callback valido, expirado, usado, setup valido,
setup sin acceptance, sesion inexistente, refresh, responsive, no exposición de
code y evidencia por ambiente. Auth remoto, Supabase Free/Pro, deploy y
promocion protegida requieren aprobaciones separadas.
