# H3-UAT-MOCK-01

Estado: `NO-GO_LOCAL_UAT_INCOMPLETE`

Fecha: 2026-09-23

## Implementado

- Mock `POST /functions/v1/admin-invite` con autorización de admin `aal2`, roles, duplicados, resend y redirect allowlist.
- Auth invitation fake con enlace one-shot y `GET /auth/v1/verify`.
- Fake inbox protegido por `NODE_ENV=test` y `x-h3-test-token`.
- Reloj virtual y endpoints de test para reset, inbox, expiración y revocación.
- Persistencia de password mock para login posterior.
- Callback acepta el fragmento de sesión de invitación y conserva el flujo `?code=` PKCE existente.
- Runner Playwright `tests/h3_invitation_uat.mjs` con casos user/admin, pre-READY, expirado, revocado, resend, superseded, redirect y replay.

## Validaciones

| Check | Resultado |
|---|---|
| `node --check mock-server/server.js` | PASS |
| `node --check tests/h3_invitation_uat.mjs` | PASS |
| contratos callback/mock | PASS: 8 tests unittest |
| TypeScript | PASS |
| `npm run build:mock` | PASS |
| ESLint | PASS, 0 errores; 9 warnings históricos |
| `git diff --check` | PASS |
| PG17 H3 harness limpio | PASS: `h3_invitation_onboarding_harness_ok`, `h3_pg17_harness_ok` |
| Playwright invitation UAT | NO-GO: el runner aún falla antes de completar aceptación real |

## Hallazgo bloqueante

La UAT browser no alcanzó un PASS reproducible del flujo completo. El fallo restante está en la integración runtime del mock/Auth/session con la página callback y debe resolverse antes de declarar GO. No se afirma cobertura E2E real ni cierre H3.

## Transición

- `expand`: mock, inbox, verify, callback fragment y runner agregados.
- `compatibilidad`: login/MFA legacy, endpoint PKCE manual y RPCs existentes conservados.
- `deploy`: no ejecutado.
- `contract`: bloqueado hasta que el runner Playwright pase el flujo completo y los negativos.
- Rollback: retirar estos cambios locales sin writes remotos; no hubo deploy ni migración remota.
