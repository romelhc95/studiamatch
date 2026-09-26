# Evidencia H3 Invitation Flow — Validación Local 2026-09-19

**Fecha:** 2026-09-19
**Hito:** H3 / `HITO-003` / `TASK-H3-001` / `H3-CA4`
**Ciclo:** `PROMPT_RETROALIMENTADO_REQUIRED` — fases analizar, implementar, validar ejecutadas
**Ambiente:** local (Docker `studiamatch-dev` + PostgreSQL 17 `studiamatch-pg17`)
**Estado:** `H3-BUILD-03A-EDGE_LOCAL_VALIDATED`
**Remote:** no se ejecutaron migraciones, writes, deploys, push, PR ni merges

## 1. Alcance

- Baseline preservado: `db/migrations/20260918_h3_invitation_flow_persistence.sql`
  no fue modificado.
- Nueva migración expand-only `db/migrations/20260919_h3_invitation_auth_token_delta.sql`
  para Opción A: token/código bajo autoridad de Supabase Auth y registro de
  negocio bajo autoridad StudIAMatch.
- Regresión extendida en `tests/sql/h3_pg17_harness.sql`.
- Refactor de entorno dev: `Dockerfile`, `docker-compose.yml`, `init-container.sh`,
  `.dockerignore`, `requirements-pipeline.txt` (hash-pinned).
- Documentos analíticos: Delivery Map, Closure Map, Development Validation,
  Invitation Design, Invitation Flow Impact.
- Runtime Edge: `supabase/functions/admin-invite/index.ts` usa
  `inviteUserByEmail`, redirect server-side allowlisted, autorización del caller,
  RPCs service-role de reserva/completado/fallo e idempotencia por request ID.
- Configuración: `supabase/config.toml` declara `verify_jwt = true` y CI ejecuta
  el contrato Edge y el harness runtime específico.

## 2. Gates ejecutados (solo local)

| Gate | Resultado | Evidencia |
|---|---|---|
| Harness PG17 completo (H3) desde base limpia `h3_build03a` | PASS — termina en `h3_pg17_harness_ok` | PostgreSQL 17.11, `ON_ERROR_STOP=1`, incluye baseline y delta `20260919` |
| Idempotencia del delta | PASS | La migración `20260919` se ejecuta dos veces en la misma base |
| Compatibilidad legacy | PASS | Hash existente preservado; constraint de longitud e índice propio retirados |
| Opción A / `send_failed` | PASS | `token_hash = NULL`, transición `pending -> send_failed`, `failure_code` obligatorio y auditoría |
| Credential scan (patron ${H3_CREDENTIAL_SCAN_PATTERN}) sobre archivos tocados | 0 coincidencias | grep sobre Dockerfile, docker-compose.yml, init-container.sh, .dockerignore, requirements-pipeline.txt, migracion 20260918, harness, informe y documentos analiticos (14 archivos) |
| `.env*` fuera del contexto Docker | PASS | `.dockerignore` excluye `.env` y `.env.*` (conserva `!.env.example`) |
| Runtime no-root | PASS | `Dockerfile` falla el build si UID/GID = 0; `USER` fijado; compose usa `user: 1000:1000` |
| `py_compile` completo (`find scripts -name '*.py'`) | PASS | contenedor `studiamatch-dev`, Python 3.11.2 |
| Suite Python `python-check` (12 archivos de test) | PASS — 142 tests | `pytest -q` en contenedor |
| `h2_scan_unauthorized_writers.py` | PASS | "h2 writer scan passed" |
| Diff dev-env revisado para drift/secrets | Sin drift ni credenciales | revisión línea a línea de los 3 diffs |
| `git diff --check` (whitespace) | PASS | sin errores de espacio/salto de línea |
| Contrato Edge local | PASS — 44 tests focalizados | `tests/test_admin_invite_edge_contract.py` y contrato de credenciales |
| Harness runtime Edge | PASS | `h3_invitation_edge_runtime_harness_ok`; reserva, membresía invited inactiva, Auth-owned token, duplicado y `send_failed` |
| TypeScript frontend | PASS | `npx tsc --noEmit` en Docker |
| Lint frontend | PASS con 9 warnings históricos | 0 errores; warnings preexistentes fuera del alcance |

### 2.1 Revalidación de cierre de ciclo (segunda pasada)

Re-ejecución de todos los gates sobre el mismo diff (11 archivos de código +
documentos) tras cerrar el ciclo retroalimentado. Sin cambios de código en esta
pasada:

| Gate | Resultado | Nota |
|---|---|---|
| Harness PG17 desde base limpia | PASS — `h3_pg17_harness_ok` | recreación de `h3_build03a` (DROP/CREATE) + psql vía `host.docker.internal:55432` |
| Suite Python `python-check` (12 archivos) | PASS — 142 passed in 1.76s | misma lista de tests del job CI |
| `h2_scan_unauthorized_writers.py` | PASS | "h2 writer scan passed" |
| `py_compile` completo | PASS | Python 3.11.2 en contenedor |
| Credential scan (14 archivos) | PASS — TOTAL_HITS=0 | las menciones literales del patrón en este documento y en el informe se normalizaron al placeholder `${H3_CREDENTIAL_SCAN_PATTERN}` |
| `git diff --check` | PASS | whitespace limpio |

Hallazgos de la segunda pasada: ninguno HIGH/CRITICAL. Hallazgo menor
documentado: literales del patrón de credenciales dentro de la documentación
generaban hits falsos del scan; corregido con placeholder y revalidado a 0.

### 2.2 Revisión retroalimentada posterior

La revisión de seguridad detectó riesgos de reenvío Auth existente, compensación
no verificada e inventario CI incompleto. Se corrigieron localmente con
idempotencia por `request_id`, validación de respuestas de RPC de fallo, auditoría
con target resuelto, ejecución CI del test Edge y harness runtime separado. No se
declara validación remota de la semántica Auth ni del endpoint desplegado.

## 3. Delta 20260919 — controles verificados

- `admin_invitations.token_hash` pasa a nullable. Se elimina el `CHECK` de
  longitud mínima y el índice único asociado al token propio; los hashes legacy
  existentes permanecen intactos e inmutables.
- Se agrega `send_failed` al vocabulario de estados y a la guarda
  `pending -> send_failed`. El estado exige `failure_code` no vacío y no admite
  datos de aceptación o revocación.
- El índice parcial de un solo `pending` por email se conserva: un fallo no
  confirmado no bloquea el reintento, pero las invitaciones pendientes
  concurrentes siguen protegidas.
- La auditoría admite `send_failed`; metadata y códigos deben permanecer
  sanitizados, sin tokens, passwords, secret keys ni enlaces privados completos.

## 4. Migración 20260918 — controles verificados

- `admin_invitations`: token solo como hash (CHECK longitud >= 32, índice único),
  un solo `pending` por email (índice parcial), lifecycle `pending → accepted |
  expired | revoked | superseded`, constraints de estado coherente.
- Guardas: append-only (DELETE rechazado), inmutabilidad de `token_hash`,
  `email`, `created_by_user_id`, `created_at`.
- `admin_members`: máquina de estados `invited → accepted → password_pending →
  ready`, transiciones a `expired/revoked/inactive` controladas; `ready` exige
  `accepted_at` + `password_set_at`; backfill existentes a `ready` por default.
- `admin_membership_audit`: `entity_type`, `invitation_id`, `metadata`;
  vocabulario `invite | resend | accept | password_set | role_change |
  activation | deactivation | revoke | expire`.

## 5. Compatibilidad (expand → contract)

- Fase expand pura: columnas/tablas nuevas con defaults; RPCs, seed y auditoría
  existentes sin cambios de firma; filas existentes se backfilan a `ready`.
- `admin_require_aal2()` permanece intacto en esta migración (contrato vigente);
  su retiro es fase contract futura según design doc.
- Fase contract / migración remota: NO ejecutada. Requiere JIT y aprobación
  humana separada.
- Fase contract del token legacy: pendiente de evidencia de consumidores cero;
  durante expand la columna se conserva nullable para rollback y reconciliación.

## 6. Pendientes (corte 03A, actualizado tras 03B DB)

- B-01..B-06 del Closure Map permanecen: cierre remoto H3, revalidación A6/A13
  en Free, Auth/MFA real, prueba remota de `verify_jwt=true` e invitación real,
  hostnames por ambiente, convergencia Pro.
- `H3-BUILD-03B-DB-IMPLEMENTATION` ya fue implementado y validado localmente en
  `db/migrations/20260921_h3_invitation_onboarding_rpc.sql`; su evidencia está en
  `evidencia_h3_invitation_flow_db_implementation_local_2026-09-21.md`.
- `H3-BUILD-03B-FRONTEND-AUTH` quedó implementado en el ciclo siguiente y Mock
  UAT-02 pasó el 2026-09-23. Sigue pendiente Auth/PKCE remoto, correo real,
  reconciliación Auth/DB y UAT por ambiente.
- La validación Auth/Supabase remota, deploy, Certification, Pro, commit, push,
  PR y merge siguen bloqueados por aprobaciones separadas.
- Estado técnico local: `H3_PR_DEVELOPMENT_READY_LOCAL`; cierre contractual:
  `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`.

## 7. Siguiente checkpoint

1. `H3-BUILD-03B-FRONTEND-AUTH`: callback, aceptación, password setup,
   activación y UAT del flujo completo; no incluye deploy implícito ni retiro de
   `aal2` sin nuevo alcance contractual.
2. Cualquier acción remota (Supabase Free/Pro, deploy, schedules), commit, push
   o PR requiere instrucción y aprobación separadas.
