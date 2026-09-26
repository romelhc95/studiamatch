# H3REQ1 — ciclo Development/Free 2026-09-24

## Iteración local/read-only 3 — 2026-09-24

| Campo | Valor |
|---|---|
| Ambiente | Docker local PG17 `h3_cycle3_clean`; mock `Development` local; snapshot remoto Free/Pro separado |
| Project ref | Free `aqrldlmlszjtgpqiegaa`; Pro `xwhtiqmboljkshrtviyw`; local sin project ref |
| Branch/commit/artefacto | `chore/rf-03-dev-environment` / `4b29d771625d6231c5875c9276eb1303a970ef02`; artefacto local `web/out` |
| Timestamp UTC | 2026-09-24; ejecución local registrada en horario `2026-09-24T15:06:10-05:00` |
| Pruebas ejecutadas | Harness PG17 limpio H3-001/H3-003; harness onboarding H3-002; build mock; TypeScript; lint; credential scan; sintaxis Node/Python; UAT mock invitation; smoke de perímetro local |
| Resultado | Local H3-001/H3-002/H3-003: `PASS`; H3-004 local compatibilidad/perímetro: `PASS`; evidencia remota contractual: `FAIL`/`BLOCKED` según matriz vigente |
| Evidencia sanitizada | Sin passwords, JWT, refresh tokens, URLs con tokens, PII ni secretos |

### Validación local reproducible

- PG17 limpio `h3_cycle3_clean`: `PASS`; `h3_pg17_harness_ok` y
  `h3_invitation_onboarding_harness_ok`; 13 tablas públicas y 24 rutinas
  `admin_*` después del harness.
- Contratos de callback/mock: 8/8 `PASS` mediante `unittest`; contrato Edge
  ejecutado por funciones directas: `PASS`.
- UAT mock de invitación: 9/9 casos `PASS` (`INV-001`, `INV-002`, `INV-003`,
  `INV-004`, `INV-005`, `INV-007`, `INV-008`, `INV-009`, `INV-012`).
- `build:mock`: `PASS`; TypeScript: `PASS`; ESLint: `PASS` con 9 warnings
  históricos y 0 errores; credential scan: `PASS`; `git diff --check`: `PASS`;
  sintaxis Node/Python: `PASS`.
- Perímetro local: `/admin/` con `Host: studiamatch.com` `404`, `/` `200`,
  host administrativo `/admin/login/` `200`: `PASS`.

### Limitaciones y fallos no convertidos en PASS

- `pytest`: `PASS` en la imagen Docker validada; las dependencias quedaron
  versionadas con hashes en `requirements-pipeline.txt`.
- UAT mock inicialmente ejecutada contra el dev server en `3000`: `FAIL` por
  entorno incorrecto y rutas HMR/manifiestos incompletos. Se corrigió la
  ejecución usando build estático `web/out` en perímetro local `3002`; la
  corrida final 9/9 fue `PASS`. No se modificó código por este hallazgo.
- Evidencia remota no se infiere desde estas pruebas locales.

## Iteración de desarrollo 4 — hardening RBAC/onboarding

Se reincorporaron al checkout principal las migraciones que ya estaban
registradas en Free y habían sido localizadas en el worktree de remediación:

| Componente | SHA-256 | Resultado |
|---|---|---|
| `db/migrations/20260924_h3_onboarding_rbac_hardening.sql` | `E466BF1F7968D71CE715724779CC4BD37818F6462021724D01AD48A9BFB1A857` | `PASS` local |
| `db/migrations/20260924_h3_onboarding_rbac_hardening_fix.sql` | `9A5C5D46BCA6B4DEC438BC6AE63036641423FEE95B73E188237EF8BA230B2978` | `PASS` local |
| `tests/sql/h3_onboarding_rbac_hardening_harness.sql` | `0A85D7734457FBDE3AC6BA0E642B8A2EC8D72F08444F3B71443A7B457AF1166D` | `PASS` local |

El harness valida que membresías incompletas no puedan activarse, que el user
ready conserve edición, que un no-admin no mutile membresías, que el último
admin quede protegido y que cada mutación agregue auditoría. Resultado:
`h3_onboarding_rbac_hardening_harness_ok`.

La corrección local no se presenta como evidencia remota y no modifica Free ni
Pro.

### Cierre de hallazgos de auditoría local — ciclo 5

- `admin_create_member` legacy: `PASS` como shim de compatibilidad rechazado;
  ya no puede crear una membresía `ready`/activa fuera de onboarding.
- ACL/RLS: `PASS` en harness PG17; `authenticated` no tiene mutaciones directas
  sobre `admin_members`/auditoría y `anon` no tiene lectura administrativa.
- Hardening y shim legacy quedaron incluidos en el harness canónico y pasan
  junto con `h3_invitation_onboarding_harness_ok`,
  `h3_onboarding_rbac_hardening_harness_ok` y `h3_pg17_harness_ok`.
- La UI de gestión ahora consulta `admin_list_members_onboarding`, un RPC
  aditivo; el RPC legacy `admin_list_members` se conserva sin cambios para
  compatibilidad.
- El mock server expone el mismo RPC aditivo para que la UAT local pruebe el
  contrato de lectura enriquecido sin alterar el endpoint legacy.

### Reauditoría de seguridad — ciclo 7

- Mock reader: `PASS`; ejecuta el RPC protegido dentro de `withIdentity()`.
- Legacy guard: `PASS`; se probó con el fixture `seed-4@studiamatch.local`,
  user `ready` real del seed, y devuelve `Legacy membership creation disabled;
  use admin-invite` sin insertar membresía.
- Harness canónico: `PASS`; `h3_onboarding_rbac_hardening_harness_ok` y
  `h3_pg17_harness_ok` en PG17 limpio.
- Lock de dependencias: `PASS`; Pygments único y pytest reproducible con hashes.
- Resultado auditoría local: sin HIGH/MEDIUM abierto. El único bloqueador HIGH
  restante es contractual remoto: Pro sin baseline H3 y sin evidencia after-apply.

### Revalidación de tests y dependencias — ciclo 4

- Pytest focalizado: `60 passed` en Docker; incluye contratos de callback/mock,
  Edge y credential contract.
- `requirements.txt` conserva `pytest`; `requirements-pipeline.txt` incorpora
  `pytest==9.1.1`, `pluggy==1.6.0`, `packaging==26.3`, `iniconfig==2.3.0` y
  `pygments==2.20.0` con hashes.
- TypeScript: `PASS`; build mock: `PASS`; ESLint: `PASS`, 0 errores y 9
  warnings históricos; credential scan: `PASS`; sintaxis y `git diff --check`:
  `PASS`.

Estado del ciclo: `NO-GO_H3REQ1_CLOSURE_REMOTE_EVIDENCE_INCOMPLETE`.
Ambiente remoto inspeccionado: Supabase Free/Development
`aqrldlmlszjtgpqiegaa`. No se ejecutaron acciones en Certification, Pro,
producción, cleanup, rollback ni promoción.

## Resultados por tarea

| Tarea | Resultado | Evidencia sanitizada | Riesgo / pendiente |
|---|---|---|---|
| H3-001 — DB contract | `PASS` para metadata remota | 6 migraciones H3 registradas, `admin_invitations` presente, 7 RPCs presentes, 30 constraints e índices del contrato, RLS habilitado, RPCs de persistencia restringidas a `service_role` y RPCs de onboarding restringidas a `authenticated`/`service_role` | El advisor mantiene warnings INFO/WARN sobre tablas RLS sin policies y funciones `SECURITY DEFINER`; requieren revisión antes del cierre contractual. |
| H3-002 — invitación/onboarding real | `BLOCKED` | Smoke negativo Edge sin credenciales: `401` para POST sin auth, JWT inválido y GET. No se crearon invitaciones; pendientes remotas `0`; no se enviaron correos ni se registraron passwords/tokens | El preview remoto Development responde `404` en login/callback/accept/setup. Falta sesión Auth real, correo, PKCE, aceptación, password, onboarding y reconciliación Auth/DB. |
| H3-003 — RBAC/seguridad/auditoría | `PARTIAL` | Free tiene 2 admins activos `ready`, 1 user activo `ready`, 0 membresías activas no-ready, 0 invitaciones huérfanas y 1 fila de auditoría histórica. Edge v3 `ACTIVE`, `verify_jwt=true`, hash `ad394869312c8710dbfd3de22a2ed31ab2282623b8272598f6a5ab2571e4bd8f` | Falta UAT funcional con admin/user/anónimo/inactivo y completar la validación de auditoría/mutaciones en runtime real. Advisor WARN permanece abierto. |
| H3-004 — transición | `BLOCKED` | Compatibilidad local y checks CI del candidato PASS; rutas locales `/admin/login/`, `/admin/auth/callback/`, `/admin/accept-invite/` y `/admin/setup-password/` responden `200` con el dev server | El deployment Pages remoto no sirve las rutas H3 nuevas; `deploy → contract`, cleanup y rollback remoto no están acreditados. |

## Validaciones ejecutadas

- Contratos Python H3 focalizados: `8/8 PASS` mediante `unittest` en Docker.
- TypeScript: `PASS`.
- ESLint: `PASS`, 0 errores y 9 warnings históricos.
- `build:mock`: `PASS`.
- Node syntax y mock server: `PASS`.
- Credential scan y `git diff --check`: `PASS` en la evidencia del candidato.
- Checks remotos del PR candidato: `security-audit`, CodeQL, Static Build,
  PostgreSQL DB Change Gate, TypeScript, ESLint, credential scan,
  actionlint/shellcheck y Cloudflare Pages aparecen `success`.
- La URL de preview publicada sigue devolviendo `404` para las rutas admin;
  el check de despliegue verde no sustituye el smoke funcional.
- MFA/`aal2` no se ejecutó como gate, conforme al alcance vigente.

## Transición y decisión

- `expand`: PASS en Free para el contrato DB y Edge.
- `compatibilidad`: PASS local; login legacy, usuarios `ready`, roles, permisos
  y rutas locales preservados.
- `deploy`: Edge Development PASS; frontend Pages funcional remoto BLOCKED.
- `contract`: BLOCKED; no se retiró legacy ni se ejecutó cleanup.
- `rollback`: BLOCKED; no existe todavía un drill remoto reproducible.

Decisión: mantener `NO-GO`. No se declara `READY_FOR_CERTIFICATION_REVIEW` y
no se ejecuta promoción a Certification ni a main/Pro.
