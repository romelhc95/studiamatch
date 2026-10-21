# G07 — Preparación integrada R22 tras SQLSTATE 42501

## Diagnóstico y corrección

R21 obtuvo `adminMemberLastCode=42501` al consultar
`public.admin_members(user_id,role,is_active,account_status)`. El Edge `admin-invite`
crea su cliente con el secreto sintético del fixture; el gateway lo traduce al JWT
local con claim `role=service_role`. El código de Edge hace lectura directa de
`admin_members`. La migración original `20260828_h3_admin_auth.sql` crea la policy
`admin_members_service_select` pero no concede el privilegio de tabla. En cambio,
`20260918_h3_invitation_flow_persistence.sql` concede explícitamente a
`service_role` SELECT/INSERT/UPDATE sobre `admin_invitations`, que usa el mismo Edge.
El bloqueo observado corresponde a la falta de `SELECT` efectivo de `service_role`
sobre `admin_members`; no se atribuye a RLS ni a Auth/TLS.

La corrección es aditiva e idempotente:
`db/migrations/20261010_h3_admin_members_service_select.sql` concede solo
`SELECT` a `service_role`. No concede acceso directo a `anon` ni `authenticated`.
`tests/sql/h3_from_h2_pro_pg17_harness.sql` aplica la migración y comprueba
`has_table_privilege('service_role', 'public.admin_members', 'SELECT')` antes de
continuar. El flujo Edge y gateway firmado no cambia.

Esta decisión evita depender de default privileges del proyecto. Supabase documenta
que sus proyectos existentes conceden por defecto operaciones de tabla en `public`
—incluido `service_role`—, mientras cambia el default y advierte que no todos los
proyectos tienen esos grants; su bootstrap oficial muestra los ACL predeterminados.
La concesión explícita, limitada a una tabla y a SELECT, es determinista y mantiene
menor alcance que depender de `ALL` global.

## Validación previa

- Contrato R22: **23/23 PASS** en Node fijado, `network=none`, rootfs read-only,
  archivos allowlisted. Incluye aserciones de destino SQL y rol único.
- `node --check` de runtime/contrato, `bash -n` de runner: PASS en Docker.
- `sha256sum -c tests/h3req1-c03-integrated.sha256`: 77/77 PASS.
- Manifiesto SHA-256: `62ce09c082d9990fe9518aff8b94062a9de22786f0645d7968fa38e9781021b7`.
- `git diff --check`: PASS.
- Runner R22, comparado mecánicamente con R21 tras normalizar nombres/IDs/rutas:
  sin otros deltas.
- Rama/HEAD: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`. WIP antes de esta nota: 564 entradas,
  4584 rutas.
- No hay colisión de nombres/redes/log R22. R20/R21 permanecen detenidos y
  preservados; `studiamatch-dev` continúa healthy y fuera del ensayo.

## Ejecución siguiente

La autorización humana local del 2026-10-10 cubre migración/DDL, fixture PG17
desechable y la integración local; no se reutiliza ni extiende a servicios remotos.
R22 corre una sola vez con PG17 17.11, snapshot allowlisted y redes internas; verifica
el grant antes de PostgREST/Edge, luego ejecuta el C03 integrado hasta el primer
fallo. Sin cuentas, correo, datos operativos, secretos ni `.env*` reales; sin retry.

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=15s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r22.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R22 \
  --manifest-sha256 62ce09c082d9990fe9518aff8b94062a9de22786f0645d7968fa38e9781021b7
```

G07 sigue parcial; el grant y el contrato local aún no equivalen a C03 integrado
PASS. Métricas sin cambio: histórico G01–G10 **60%**, cierre local G01–G09
**6/9 = 66.67%**.
