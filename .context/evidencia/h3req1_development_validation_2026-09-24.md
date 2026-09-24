# H3REQ1 Development Validation — Free — 2026-09-24

Estado: `NO-GO DESARROLLO H3REQ1` para promoción. El contrato DB y Edge de Development quedaron aplicados; el cierre H3REQ1 sigue abierto por UAT Auth/correo y preview UI remota.

## Alcance y autorización

- Ambiente: Supabase Free / Development, ref `aqrldlmlszjtgpqiegaa`.
- No se ejecutó Pro, Certification, producción, Cloudflare Pages, cleanup, rollback, merge ni promoción.
- Se aplicaron únicamente las migraciones H3 `20260918`–`20260921`, en orden.
- Se desplegó `admin-invite` Free con `verify_jwt=true`, versión remota 2.
- El PR se prepara separadamente desde `feat/h3req1-free-remediation` hacia `desarrollo`, usando la plantilla versionada.

## Hallazgos remediados

| Hallazgo | Cambio | Resultado |
|---|---|---|
| H3-001/H3-003 | Persistencia y contrato H3 03A/03B en Free | PASS remoto |
| H3-002 | Tablas/RPCs de invitación y onboarding | PASS metadata remoto; UAT real pendiente |
| H3-004 | Expand/compatibilidad y Edge Development | Expand + compatibilidad PASS; contract/rollback pendientes |

## Evidencia remota DB

Migrations registradas en Free:

- `20260918_h3_invitation_flow_persistence` — versión remota `20260924051844`
- `20260919_h3_invitation_auth_token_delta` — versión remota `20260924051908`
- `20260920_h3_invitation_edge_runtime` — versión remota `20260924052006`
- `20260921_h3_invitation_onboarding_rpc` — versión remota `20260924052131`

Tablas presentes:

- `public.admin_invitations`
- `public.admin_members`
- `public.admin_membership_audit`

RPCs presentes como `SECURITY DEFINER`:

- `admin_invitation_reserve(text,text,uuid,uuid,boolean,text,jsonb,timestamptz)`
- `admin_invitation_record_failure(text,text,uuid,uuid,text,text,jsonb)`
- `admin_invitation_complete(uuid,uuid)`
- `admin_invitation_fail(uuid,uuid,text)`
- `admin_accept_current_invitation(uuid)`
- `admin_complete_password_setup()`
- `admin_get_onboarding_status()`

ACL comprobado:

- Onboarding: `authenticated` y `service_role`.
- Runtime Edge: `service_role`; no `anon`/`authenticated`.
- Tablas de invitación: no exposición pública; RLS/policies existentes se preservan.

## Evidencia remota Edge

- Function: `admin-invite`
- Estado: `ACTIVE`
- Versión: `2`
- `verify_jwt`: `true`
- Hash remoto: `2111046c686dda6ccb9186c645c7a711a0ea9af4cc43adf9f3ee5b26d6deb9fe`
- El hash corresponde al artefacto desplegado en el ciclo; no se registran secretos, tokens ni passwords.

## Validaciones locales en Docker

- TypeScript `npx --no-install tsc --noEmit`: PASS.
- ESLint: PASS, 0 errores y 9 warnings históricos de `HomeContent.tsx`.
- `npm run build:mock`: PASS, compilación estática exitosa.
- Contratos H3 focalizados: PASS, 8 tests.
- Node syntax / mock server: PASS.
- Credential scan: PASS.
- `git diff --check`: PASS en archivos versionables del worktree.
- Harness PG17 remoto/local: no se volvió a ejecutar aquí porque la imagen de desarrollo no contiene `psql`; la evidencia canónica local previa conserva `h3_invitation_onboarding_harness_ok`, `h3_invitation_edge_runtime_harness_ok` y `h3_pg17_harness_ok`.
- Revisión de seguridad: se detectó y corrigió el bypass de activación de
  membresías incompletas mediante `20260924_h3_onboarding_rbac_hardening.sql`.
  El cambio exige `account_status = 'ready'` para activar y hace que las
  funciones de autorización consideren simultáneamente estado e `is_active`.
- `security-audit` CI: actualizado para incluir el delta H3 03A/03B, el hardening
  RBAC y los contratos focalizados; pendiente de ejecución remota al abrir el PR.

## Criterios de aceptación H3REQ1

- RBAC y preservación legacy: PASS local; Free metadata validada.
- Invitación/onboarding DB: PASS remoto en metadata.
- Auth/PKCE/correo real admin → invitación → aceptación → password → privado: PENDIENTE; requiere prueba controlada y reconciliación Auth/DB.
- UAT UI Development: PENDIENTE; el preview/hostname correcto y las nuevas rutas deben validarse.
- Expand → compatibilidad: PASS.
- Deploy: PASS en Edge Free; frontend remoto no acreditado.
- Contract/cleanup: PENDIENTE, no autorizado.
- Rollback remoto reproducible: PENDIENTE, no ejecutado.
- Rate limiting/payload limit de Edge: riesgo residual documentado; no se declara
  resuelto en este ciclo.

## Gate

`NO-GO DESARROLLO H3REQ1`.

Razón: no se declara cierre ni promoción con metadata DB/Edge solamente. Faltan UAT remota Auth/PKCE/correo, hostname/preview Development, reconciliación Auth/DB, smoke funcional de la UI y rollback/contract documentados. Certification y Pro permanecen fuera del alcance.

## Compatibilidad y rollback

- Expand: migraciones idempotentes `20260918`–`20260921`.
- Compatibilidad: `token_hash` nullable, Auth como autoridad del token, runtime Edge, firmas legacy y membresías `ready` preservadas.
- Deploy: Edge Free versión 2; frontend no desplegado por este ciclo.
- Contract: no ejecutado; no se eliminaron columnas ni RPCs legacy.
- Rollback: requiere migración inversa aprobada y rollback Edge versionado; no se ejecutó.
- Harness PG17 limpio reejecutado después del hardening: `h3_invitation_onboarding_harness_ok` y `h3_pg17_harness_ok` PASS; la regresión incluye el rechazo de activación de membresías no-ready y la preservación de autorización legacy ready.
- El hardening RBAC se validó además en PG17: una membresía `ready` conserva autorización y los estados incompletos no pueden activarse por `admin_update_member`.
