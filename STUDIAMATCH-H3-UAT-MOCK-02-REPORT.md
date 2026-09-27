# STUDIAMATCH-H3-UAT-MOCK-02

Estado: `PASS`

Fecha: 2026-09-23

## Causa raíz

El mock emitía tokens opacos como `access_token` y `refresh_token`. El cliente oficial `@supabase/supabase-js` necesita que el access token sea un JWT compatible para completar `setSession`, consultar `/auth/v1/user` y persistir la sesión en `sessionStorage`. La callback sí recibía correctamente el fragmento, pero `setSession` rechazaba la sesión antes de ejecutar `admin_accept_current_invitation`, por lo que el flujo quedaba en `Invitación no disponible`.

También faltaban datos de expiración completos en las respuestas de token y el runner tenía dos errores de observación (`request.url()` sobre URLs ya materializadas y `extra` fuera del contexto de `page.evaluate`).

## Archivos modificados

- `mock-server/server.js`
- `mock-server/static-server.js`
- `web/src/lib/admin-auth.ts`
- `tests/h3_invitation_uat.mjs`
- `web/src/app/admin/auth/callback/page.tsx`
- `web/src/app/admin/accept-invite/page.tsx`
- `web/src/app/admin/setup-password/page.tsx`

`web/src/app/layout.tsx` no forma parte de la corrección final y no se incluye en el ZIP. Se restauró después de usar una variante temporal para diagnosticar el build offline.

## Solución aplicada

- El mock genera tokens JWT estructuralmente compatibles con Supabase Auth, conservando sesiones opacas en memoria como estado interno.
- Las respuestas password, invite y refresh incluyen `expires_at`, `expires_in`, `token_type` y usuario autenticado.
- El mock valida la expiración de sesiones en requests autenticados.
- `setSession` y MFA pasan a Supabase Auth los campos de expiración disponibles.
- Se amplían los métodos CORS permitidos para cubrir el contrato browser del Auth mock.
- El runner corrige la captura de URL de Playwright y pasa el objeto `extra` explícitamente al contexto evaluado.

No se modificaron migraciones SQL, Supabase remoto, deploy ni configuración de producción.

## Pruebas ejecutadas

| Prueba | Resultado |
|---|---|
| `node --check mock-server/server.js` | PASS |
| `node --check tests/h3_invitation_uat.mjs` | PASS |
| Contratos Python H3 mock/callback, 8 tests | PASS |
| `npm run build:mock` | PASS, `Compiled successfully` |
| Playwright H3 invitation UAT | PASS |
| `git diff --check` | PASS |

## Evidencia UAT

```json
{
  "result": "PASS",
  "cases": [
    { "id": "INV-008", "result": "PASS" },
    { "id": "INV-001", "result": "PASS" },
    { "id": "INV-002", "result": "PASS" },
    { "id": "INV-009", "result": "PASS" },
    { "id": "INV-007", "result": "PASS" },
    { "id": "INV-003", "result": "PASS" },
    { "id": "INV-004", "result": "PASS" },
    { "id": "INV-005", "result": "PASS" },
    { "id": "INV-012", "result": "PASS" }
  ]
}
```

El flujo browser quedó validado como `admin invite -> fake inbox -> verify -> callback/hash -> setSession -> accept -> password -> READY`. La misma ejecución cubrió user invitation, admin invitation, expired, revoked, resend/superseded, password pending, pre-ready blocked, redirect protection y replay.

## Riesgos restantes

- El token JWT del mock es deliberadamente no firmado y solo sirve para el entorno local de test; no debe reutilizarse fuera del mock.
- La validación ejecutada usa el runtime local con PostgreSQL H3 y no implica cambios ni validación de Supabase remoto.
- El comando `pytest` no está instalado en la imagen disponible; los ocho contratos solicitados se ejecutaron equivalentemente con `python3 -m unittest` y pasaron.

## Transición

- `expand`: se conserva el flujo legacy PKCE y se añade compatibilidad JWT/session para el mock.
- `compatibilidad`: callback hash, PKCE, MFA, RPCs de onboarding y rutas slash-normalizadas permanecen activos.
- `deploy`: no ejecutado.
- `contract`: PASS local para H3-UAT-MOCK-02.
- Rollback: retirar los archivos del ZIP; no hubo writes remotos, migraciones ni deploy.
