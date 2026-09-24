# H3REQ1 Remediation Baseline â€” 2026-09-23

**Estado vivo:** `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`
**Modo de captura:** inspecciÃ³n local y evidencia remota read-only; no se
ejecutaron DDL, writes Supabase, Auth writes, Edge deploy, Cloudflare, push, PR,
merge, promociÃ³n ni acciones destructivas.

## Autoridad y alcance

- Fuente de estado: `.context/estado_del_proyecto.md`.
- AtestaciÃ³n sanitizada: `.context/evidencias_cliente/sprint_1/atestado_h3_ampliacion_prompt_humano_sanitizado.md`.
- El alcance se limita a H3REQ1: RBAC administrativo, invitaciones, aceptaciÃ³n,
  onboarding, gestiÃ³n de usuarios, ediciÃ³n, ownership, restricciÃ³n pÃºblica y
  transiciÃ³n compatible. MFA/`aal2` existente se conserva como compatibilidad.
- La atestaciÃ³n solo autoriza trabajo local Docker; cualquier operaciÃ³n remota
  requiere aprobaciÃ³n JIT separada por clase de acciÃ³n.

## ReproducciÃ³n del estado Git

Comandos ejecutados desde la raÃ­z del workspace:

```text
git -c safe.directory='//wsl.localhost/Ubuntu/home/romel/src/studiamatch' status --short --branch
git -c safe.directory='//wsl.localhost/Ubuntu/home/romel/src/studiamatch' branch --show-current
git -c safe.directory='//wsl.localhost/Ubuntu/home/romel/src/studiamatch' log -1 --format='%H%n%ad%n%s' --date=iso-strict
```

Resultado al corte:

```text
branch: chore/rf-03-dev-environment
HEAD:   4b29d771625d6231c5875c9276eb1303a970ef02
commit: 2026-09-10T21:35:21-05:00
title:  chore(rf-02): normalize EOL and UTF-8 BOM
working tree: dirty; 123 paths modified and 23 paths untracked
```

El working tree ya estaba sucio al iniciar la auditorÃ­a. No se ejecutÃ³ reset,
checkout, clean ni otra operaciÃ³n para descartar trabajo potencial de terceros.
Por tanto, el estado Git no se interpreta como un diff atribuible a esta
remediaciÃ³n.

## Inventario local solicitado

| Ãrea | Resultado | Evidencia reproducible |
|---|---|---|
| Estado vivo | `PASS` | `.context/estado_del_proyecto.md` declara NO-GO remoto |
| Evidencia | `PASS` | `.context/evidencia/` contiene auditorÃ­a read-only, evidencia local y artefactos UAT |
| Evidencia cliente | `PASS` | `.context/evidencias_cliente/` contiene atestaciÃ³n H3 sanitizada |
| Panel admin | `PASS` | `web/src/app/admin/` contiene panel, login, users, callback, aceptaciÃ³n y setup |
| Auth frontend | `PASS` | `web/src/lib/admin-auth.ts` usa cliente PKCE oficial, RPCs de onboarding y rutas internas fijas |
| Edge | `PASS local / remoto parcial` | `supabase/functions/admin-invite/index.ts`; remoto Free ACTIVE/v1/`verify_jwt=true` |
| Migraciones | `PASS local / remoto FAIL` | Las cuatro SQL existen localmente, pero no estÃ¡n trackeadas y no constan aplicadas remotamente |

## Migraciones H3 locales

Las cuatro migraciones requeridas estÃ¡n presentes en `db/migrations/`, pero no
son evidencia de aplicaciÃ³n remota ni estÃ¡n incluidas en el Ã­ndice Git del
checkout actual.

| Archivo | Presencia local | SHA-256 local | LÃ­neas |
|---|---|---|---:|
| `20260918_h3_invitation_flow_persistence.sql` | `PRESENT / NOT_TRACKED` | `0837D448D8552FEB62BB3AB63701123E2449A00FFDCC84DC776849E879030F77` | 383 |
| `20260919_h3_invitation_auth_token_delta.sql` | `PRESENT / NOT_TRACKED` | `701F5C74FF923765FB39EFA1605600CB58C93C8CAA820B7D49A17FBA73E8275D` | 119 |
| `20260920_h3_invitation_edge_runtime.sql` | `PRESENT / NOT_TRACKED` | `46F7D24AC9C8AF033EBD84B9EDE44C27241382B9CBA3FE179EC745B9A25F9188` | 411 |
| `20260921_h3_invitation_onboarding_rpc.sql` | `PRESENT / NOT_TRACKED` | `138E2D3690EC880C51F3834E42FA33EBCE008C6AD9E08B5FE34B8DF76DE84F2` | 805 |

Contratos locales identificados:

- `admin_invitations`, estado de ciclo de vida, auditorÃ­a y guardas append-only.
- Token bajo autoridad de Supabase Auth; `token_hash` queda solo como columna de
  compatibilidad nullable.
- RPCs service-role para reserva/completado/fallo y TTL server-side de 24 horas.
- RPCs autenticadas `admin_accept_current_invitation`,
  `admin_complete_password_setup` y `admin_get_onboarding_status`.
- ACL explÃ­cito: onboarding para `authenticated`/`service_role`; persistencia
  de invitaciÃ³n solo para `service_role`; sin ejecuciÃ³n anÃ³nima.

## Frontend y Edge local

### Frontend

Se verificÃ³ la existencia de:

- `web/src/app/admin/auth/callback/page.tsx`: exchange PKCE de una sola ejecuciÃ³n,
  limpieza de URL y destinos internos sin `next` externo.
- `web/src/app/admin/accept-invite/page.tsx`: estados accepted, password pending,
  ready, expired, revoked y superseded.
- `web/src/app/admin/setup-password/page.tsx`: `updateUser({ password })` antes
  de `admin_complete_password_setup()`; no envÃ­a password al RPC.
- `web/src/app/admin/users/page.tsx`: invitaciÃ³n por rol y gestiÃ³n de membresÃ­as.
- `web/src/lib/admin-auth.ts`: sesiÃ³n oficial Supabase PKCE y RPCs de onboarding.

### Edge

La configuraciÃ³n local declara `verify_jwt = true` en `supabase/config.toml`.
El runtime local usa `auth.admin.inviteUserByEmail`, redirect allowlisted,
identidad del caller, `NEXT_SUPABASE_SECRET_KEY` solo server-side y RPCs de
persistencia. El SHA-256 local de `index.ts` es:

```text
58371EEA6945F83DB62595AFA350FD9218D2A101DB41990768DAB821D981D759
```

Este hash es un identificador de evidencia, no autorizaciÃ³n de deploy.

## Evidencia remota read-only

Fuente canÃ³nica: `.context/evidencia/h3_remote_validation_readonly_2026-09-24.md`.

La captura remota reporta:

| Check | Free `aqrldlmlszjtgpqiegaa` | Pro `xwhtiqmboljkshrtviyw` | ConclusiÃ³n |
|---|---|---|---|
| PostgreSQL | 17.6 | 17.6 | Informativo |
| Migraciones H3 | Hasta `20260903_h3_rbac_contract_fix` | Ninguna H3 devuelta | Drift probado |
| `admin_members` | Presente | Ausente | RBAC parcial |
| `admin_membership_audit` | Presente | Ausente | AuditorÃ­a parcial |
| `admin_invitations` | Ausente | Ausente | Contrato 03A/03B ausente |
| RPCs de invitaciÃ³n/onboarding | Ausentes | Ausentes | Flujo remoto bloqueado |
| `admin-invite` | ACTIVE, v1, `verify_jwt=true` | No listado | Runtime Free sin DB; Pro ausente |

Filas de migraciÃ³n Free observadas: `20260828_*`, `20260829_h3_rbac_users`,
`20260830_h3_expanded_contract`, `20260902_h3_pr_contract` y
`h3_rbac_contract_fix`. No se devolvieron filas `20260918`â€“`20260921`.

La evidencia remota no contiene usuarios, tokens, passwords, credenciales,
invitaciones ni datos operativos.

## Hallazgos baseline

| Hallazgo | Estado al corte | Causa demostrada | Impacto |
|---|---|---|---|
| H3-001 | `OPEN / HIGH` | Falta evidencia de aplicaciÃ³n en Free/Pro; el inventario read-only prueba ausencia | No se puede certificar el contrato remoto |
| H3-002 | `BLOCKED / HIGH` | `admin_invitations` y RPCs requeridas no existen remotamente | InvitaciÃ³n real y onboarding no operables |
| H3-003 | `OPEN / HIGH` | Free estÃ¡ en H3 parcial y Pro sin H3 consultable | Ambientes no convergentes |
| H3-004 | `BLOCKED / HIGH` | No hay deploy, contract/cleanup ni rollback remoto evidenciado | No se acredita transiciÃ³n SDLC completa |

## Evidencia local disponible, no sustitutiva de la remota

- UAT H3 local: 47/47 casos, 141/141 ejecuciones, 0 retries.
- UAT invitaciÃ³n local: 9/9 casos, incluyendo aceptaciÃ³n, expiraciÃ³n,
  revocaciÃ³n, resend/supersede, password setup y replay.
- Harness PG17 local: `h3_invitation_onboarding_harness_ok`,
  `h3_pg17_harness_ok` y runtime Edge local PASS.
- TypeScript, build normal/mock, contratos focalizados, py_compile, credential
  scan y `git diff --check` reportados PASS en la evidencia local existente.

Estas pruebas validan el diseÃ±o local, no prueban que Free o Pro tengan el
contrato instalado.

## Gating y estado de ejecuciÃ³n

| Fase | Estado | Motivo |
|---|---|---|
| FASE 1 â€” auditorÃ­a inicial | `COMPLETADA` | Baseline local y remoto read-only reproducible |
| FASE 2 â€” plan | `COMPLETADA` | Matriz de remediaciÃ³n en `.context/operaciones/h3req1_remediation_plan_2026-09-24.md` |
| FASE 3 â€” implementaciÃ³n | `DETENIDA` | Requiere `continua`; no se ejecutan cambios funcionales en este ciclo |
| FASE 4 â€” validaciÃ³n remota | `BLOQUEADA` | Requiere JIT separado para Free DDL, Pro DDL, Auth/test data y Edge deploy |
| FASE 5 â€” evidencia final | `PENDIENTE` | No puede cerrarse mientras existan hallazgos remotos abiertos |

**DecisiÃ³n:** `NO-GO`. Este baseline no declara `READY FOR VALIDATION`, no
declara GO y no autoriza ninguna operaciÃ³n remota.
