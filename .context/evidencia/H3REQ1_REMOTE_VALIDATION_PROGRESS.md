# H3REQ1 Remote Validation Progress

**Fecha:** 2026-09-24 UTC
**Estado:** `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`
**Modo:** avance remoto Development; no se declara GO, no se ejecutó Certification,
Pro, cleanup, rollback, promoción, push ni PR.

## Autorización y alcance ejecutado

Se recibió autorización humana para Development/Free DDL, Auth/correo real y
deploy de `admin-invite` en Development.

Correos autorizados informados por el solicitante:

- Admin: `romelhc95@gmail.com`
- User: `hzbj84@gmail.com`

No se registran contraseñas, tokens, links de invitación ni secretos en esta
evidencia.

## Tareas y gates de este ciclo

| Tarea | Gate | Resultado |
|---|---|---|
| Preparar Development remoto | Proyecto Free identificado y baseline before/after | `PASS` |
| Contrato DB H3REQ1 | Migraciones, tablas, RPCs y ACL verificables | `PASS` en Free; Pro/Certification pendientes |
| Edge `admin-invite` | Runtime activo, `verify_jwt=true`, smoke sanitizado | `PARTIAL`; runtime activo, deploy autorizado no ejecutado |
| Flujo Auth real | Invitación, correo, aceptación, password, onboarding | `BLOCKED`; no se enviaron invitaciones reales porque el artefacto Edge remoto no coincide con el código H3REQ1 candidato y el callback remoto Development responde 404 |
| RBAC | Admin/user y ACL del contrato | `PARTIAL`; ACL DB verificada; UAT interactiva pendiente |
| Evidencia Certification | Hostname, contrato y UAT del ambiente | `BLOCKED`; no hay autorización Certification |

## Baseline remoto Development / Free

- Project ref: `aqrldlmlszjtgpqiegaa`
- API URL: `https://aqrldlmlszjtgpqiegaa.supabase.co`
- PostgreSQL: `17.6`
- Antes del apply: la auditoría read-only del ciclo previo reportó ausencia de las migraciones 03A/03B, `admin_invitations` y RPCs de invitación/onboarding.
- `admin_members` y `admin_membership_audit` ya existían.
- Conteo before de `admin_invitations`: `0`.

Se aplicaron en orden, mediante `apply_migration`, únicamente en Free:

1. `20260918_h3_invitation_flow_persistence`
2. `20260919_h3_invitation_auth_token_delta`
3. `20260920_h3_invitation_edge_runtime`
4. `20260921_h3_invitation_onboarding_rpc`

Registro remoto after observado en `supabase_migrations.schema_migrations`:

```text
20260924051844  20260918_h3_invitation_flow_persistence
20260924051908  20260919_h3_invitation_auth_token_delta
20260924052006  20260920_h3_invitation_edge_runtime
20260924052131  20260921_h3_invitation_onboarding_rpc
```

## Contrato DB verificado

Presentes en `public`:

- `admin_invitations`
- columnas H3 de `admin_members`: `account_status`, timestamps de onboarding,
  `invited_by`, `last_invitation_id` y campos de estado
- columnas H3 de `admin_membership_audit`: `entity_type`, `invitation_id`, `metadata`
- `admin_invitation_reserve`
- `admin_invitation_record_failure`
- `admin_invitation_complete`
- `admin_invitation_fail`
- `admin_accept_current_invitation`
- `admin_complete_password_setup`
- `admin_get_onboarding_status`

ACL observada:

| RPC | anon | authenticated | service_role |
|---|---:|---:|---:|
| `admin_invitation_reserve` | false | false | true |
| `admin_invitation_record_failure` | false | false | true |
| `admin_invitation_complete` | false | false | true |
| `admin_invitation_fail` | false | false | true |
| `admin_accept_current_invitation` | false | true | true |
| `admin_complete_password_setup` | false | true | true |
| `admin_get_onboarding_status` | false | true | true |

Advisory remoto posterior: el advisor de seguridad reporta como `WARN` que las
tres RPC autenticadas de onboarding son `SECURITY DEFINER` ejecutables por
`authenticated`. Esto es coherente con el contrato de onboarding, pero queda como
hallazgo para revisión de seguridad antes de cierre; no se oculta ni se waiva.

## Edge Function `admin-invite`

Estado remoto Free observado:

- status: `ACTIVE`
- version: `1`
- `verify_jwt`: `true`
- hash remoto: `012d9b04f6e1038ab5c66dddf8ec007a4d8112345ff63563b96540ff3043cf35`
- source remoto: `5342` bytes

El source remoto observado es un artefacto anterior: usa `SUPABASE_SERVICE_ROLE_KEY`,
`admin_has_aal2`, `admin_is_active_admin` y `admin_create_member`; no coincide con
el source H3REQ1 candidato local que usa `NEXT_SUPABASE_SECRET_KEY`, reserva/complete
de invitación y reconciliación Auth/DB. Por control de integridad no se envió correo
real ni se ejecutó UAT de invitación contra ese runtime. El deploy autorizado de
Development queda pendiente de ejecutarse con el artefacto aprobado y variables
configuradas.

Smoke remoto no destructivo:

- request sin JWT válido: `401 UNAUTHORIZED_INVALID_JWT_FORMAT`
- request con publishable key como bearer: `403`, respuesta sanitizada `MFA aal2 required`
- logs remotos asociados: request IDs y status `401/403`, sin tokens ni passwords

## Flujo real Auth / correo / onboarding

Resultado: `BLOCKED`, sin envío real a los correos autorizados.

Razones reproducibles:

1. El Edge remoto no corresponde al artefacto H3REQ1 candidato.
2. Las rutas remotas del preview Development revisado devuelven `404`:
   `/admin/auth/callback/`, `/admin/accept-invite/`, `/admin/setup-password/`.
3. No existe una sesión interactiva AAL2 de un admin autorizado disponible para
   llamar al Edge; el correo autorizado por sí solo no proporciona una sesión ni
   credenciales y no se solicitaron ni registraron tokens.
4. Sin callback servido y sin runtime alineado, una invitación real produciría un
   estado Auth/DB no reconciliable.

Estado after de datos de prueba en Free:

- `admin_invitations` pendientes: `0`
- no se crearon invitaciones nuevas en este ciclo
- miembros observados: dos `admin/ready/active`, un `user/ready/active`
- no se modificaron esos miembros ni se registraron passwords/tokens

## RBAC

Verificado de forma remota:

- caller admin existente: `romelhc95@gmail.com`, `admin`, `active`, `ready`
- RPCs de persistencia restringidas a `service_role`
- RPCs autenticadas de aceptación/status/password no ejecutables por `anon`
- Edge mantiene `verify_jwt=true`
- las rutas públicas de preview para el callback y onboarding no están disponibles;
  la validación RBAC por UI queda pendiente

## Certification

No se ejecutó. No hay autorización JIT para Certification ni para Pro. La evidencia
preparada para el siguiente gate debe incluir, antes de cualquier UAT:

- ref/URL y snapshot before de Certification
- migrations 03A/03B y contrato DB verificados
- hash/version de Edge con `verify_jwt=true`
- hostname de Certification que sirva callback, aceptación y password setup
- correo/Auth real separado de Development
- reconciliación Auth/DB, RBAC y logs sanitizados

## Decisión del ciclo

`NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`.

Se completó la evidencia de aplicación del contrato H3REQ1 en Free y del estado
remoto actual de Edge/RBAC. Permanecen abiertos el deploy alineado de Edge,
el flujo Auth/correo real, la UAT UI de Development, Certification, Pro,
contract/cleanup y rollback. No se declara GO.
