# Evidencia H3 Invitation Flow - DB Implementation Local 2026-09-21

**Fecha:** 2026-09-21
**Hito:** H3 / `HITO-003` / `TASK-H3-001`
**Checkpoint:** `H3-BUILD-03B-DB-IMPLEMENTATION`
**Ciclo:** `PROMPT_RETROALIMENTADO_REQUIRED` - analizar, implementar, validar y documentar
**Ambiente:** local Docker + PostgreSQL 17 temporal
**Estado:** `H3-BUILD-03B-DB_LOCAL_VALIDATED`
**Remote:** no hubo migraciones, writes, deploys, push, PR ni merges remotos

## 1. Alcance Ejecutado

- Nueva migracion expand-only:
  `db/migrations/20260921_h3_invitation_onboarding_rpc.sql`.
- Harness especifico:
  `tests/sql/h3_invitation_onboarding_harness.sql`.
- Integracion del harness en `tests/sql/h3_pg17_harness.sql`.
- No se modificaron `20260918`, `20260919` ni `20260920`.
- No se modifico frontend, callback, Auth remoto ni Supabase remoto.

## 2. Contrato Validado

| Area | Evidencia |
|---|---|
| TTL | `expires_at = last_sent_at + 24 hours`, timestamp capturado server-side. |
| Aceptacion | `pending -> accepted`; membresia `invited -> password_pending`, inactiva. |
| Password setup | `password_pending -> ready`, activa y con `password_set_at`. |
| Status | Solo devuelve el estado del usuario autenticado. |
| Lazy expiration | `pending` vencida pasa a `expired` bajo lock. |
| Auditoria | `accept`, `expire` y `password_set`, sin duplicados por reintento. |
| Seguridad | SECURITY DEFINER, search path explicito y ACL minimo. |
| Legacy | `ready` sin invitacion historica permanece operativo. |
| Auth-owned | No se genera ni se expone token o password. |

## 3. Matriz De Pruebas

| Caso | Resultado |
|---|---|
| Aceptacion menor a 24 horas | PASS |
| Aceptacion en/despues de 24 horas | PASS: `invitation_expired` |
| Resend | PASS: anterior `superseded`, nueva pendiente |
| Superseded | PASS: no acepta enlace anterior |
| Revoked | PASS: no cambia membresia |
| Mismatch email | PASS: `auth_identity_mismatch` |
| Doble aceptacion | PASS: idempotente, una auditoria |
| Password setup sin aceptacion | PASS: rechazado |
| Password setup valido | PASS |
| Password setup repetido | PASS: idempotente, una auditoria |
| Legacy ready | PASS |
| Auditoria sin duplicados | PASS |
| Edge runtime 03A | PASS |

## 4. Resultados De Ejecucion

- `h3_invitation_onboarding_harness_ok`
- `h3_pg17_harness_ok`
- `h3_invitation_edge_runtime_harness_ok`
- Credential scan: `PASS`.
- `git diff --check`: `PASS`.
- ACL verificado: `anon=false`, `authenticated=true`, `service_role=true`.

La prueba se ejecuto en PostgreSQL 17 limpio dentro de Docker y no utilizo
credenciales ni endpoints Supabase.

## 5. Expand, Compatibilidad, Deploy, Contract

### Expand

La nueva migracion redefine las RPCs runtime al contrato de 24 horas y agrega
las RPCs de onboarding, guardas, locks, auditoria y grants.

### Compatibilidad

Se mantiene `token_hash` nullable, el runtime Edge 03A, las filas legacy
`ready`, las firmas existentes y la separacion entre Auth y Postgres. Las filas
pendientes preexistentes no fueron reinterpretadas ni backfilleadas.

### Deploy

Pendiente de aprobacion JIT remota y validacion por ambiente.

### Contract

Pendiente de consumidores frontend validados, evidencia Auth/PKCE real y retiro
posterior de compatibilidad legacy. No se eliminaron columnas ni RPCs historicas.

## 6. Rollback Y Riesgos

- No hubo rollback remoto porque no hubo apply remoto.
- La base de prueba fue temporal y descartable.
- El rollback remoto futuro debe ser una migracion aprobada; no se deben editar
  migraciones historicas.
- Fallo parcial Auth/DB requiere reconciliacion.
- La TTL nueva aplica a emisiones persistidas bajo el nuevo contrato; las filas
  antiguas mantienen su valor materializado hasta una decision de backfill.

## 7. Siguiente Gate

`H3-BUILD-03B-FRONTEND-AUTH`.

El siguiente ciclo debe consumir exclusivamente estas RPCs para callback,
aceptacion y setup. No autoriza deploy, Supabase remoto, commit, push, PR o
merge.
