# JIT — atomicidad de edición/auditoría editorial en PG17 — 2026-10-09

**Estado: PREPARADO; requiere aprobación humana.** La aprobación autorizará una sola
invocación del runner fijado abajo. No se ha ejecutado Docker ni SQL para este paquete.

## Objetivo y alcance

Validar en una base PostgreSQL 17 nueva, aislada y efímera la cobertura de atomicidad recién
añadida a `tests/sql/h3_pg17_harness.sql`: al fallar el append del evento de auditoría de
edición, el estado editorial y el conteo de auditoría deben quedar sin cambios. El harness
incluye sus migraciones y los tres harnesses anidados de invitación/onboarding. Esta es
cobertura de test; no cambia la migración ni el contrato del producto.

El usuario autorizó el desarrollo local al indicar `continua`. El cambio de bytes del
harness hace necesario este JIT para ejecutar SQL/DDL/DML, conforme a AGENTS.

## Candidato e inputs fijados

| Elemento | Valor |
|---|---|
| Checkout | `/home/romel/src/studiamatch-h3req1-sync-20261002` |
| Rama / HEAD | `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| Harness | `tests/sql/h3_pg17_harness.sql` — SHA-256 `24868250cf598a42412394c9cc714e6826096865846d0e8c3a73cb2a02f8e355` |
| Cierre transitivo | `.context/operaciones/manifest_h3req1_editorial_atomicity_pg17_2026-10-09.sha256` — SHA-256 `0ed63a7b439275121caa9255ea033030f20e363fdb71eb202a47a94792ab2bc5`; 36 rutas exactas incluidas/ejecutadas por el harness |
| Runner | `tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_once.sh` — SHA-256 `3465f73650d283f2731bfb10d28c8b01f66d81d8102dc539baf5b91f76e1aded` |
| Imagen local requerida | `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f` (PostgreSQL 17.11) |

No se monta el checkout completo, `.env*`, `web`, caches, dependencias, credenciales, socket
Docker dentro del contenedor, volúmenes persistentes, ni fuentes de otros checkouts. Los
únicos bind mounts son `tests/sql`, `db/migrations` y `db/seeds`, read-only; el manifest
verifica los 36 SQL inputs que alcanza el harness. El runner verifica rama/HEAD, hash del
manifest e inputs y disponibilidad local del digest antes de crear el contenedor.

## Operación autorizable

Una invocación como usuario `romel` no-root en Ubuntu WSL:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_once.sh'
readonly RUNNER_SHA256='3465f73650d283f2731bfb10d28c8b01f66d81d8102dc539baf5b91f76e1aded'
readonly MANIFEST='/home/romel/src/studiamatch-h3req1-sync-20261002/.context/operaciones/manifest_h3req1_editorial_atomicity_pg17_2026-10-09.sha256'
readonly MANIFEST_SHA256='0ed63a7b439275121caa9255ea033030f20e363fdb71eb202a47a94792ab2bc5'
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
manifest_line="$(/usr/bin/sha256sum -- "$MANIFEST" 2>/dev/null)" || {
  printf 'phase=dispatch-preflight|error_code=MANIFEST_HASH_FAILED\n'
  exit 1
}
if [[ "${manifest_line%% *}" != "$MANIFEST_SHA256" ]]; then
  printf 'phase=dispatch-preflight|error_code=MANIFEST_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=10s 240s /bin/bash "$RUNNER"
```

El wrapper no altera ni transforma el runner. `bash -n` pasó; el manifest pasó 36/36.
La revisión estática confirmó que el runner solo crea el nombre indicado y, en el trap,
para/elimina su ID exacto sin `-v`. `docker run --pull=never` prohíbe pulls; el container usa
`--network none`, máximo 2 CPU/2 GiB, un directorio PGDATA tmpfs de 1 GiB, tmpfs para
`/tmp` y socket de PostgreSQL y `--read-only` en la raíz. No crea red, volumen ni puerto.

Dentro del contenedor se ejecuta solo:

```text
psql -X -q -A -t --set=ON_ERROR_STOP=1 --set=VERBOSITY=sqlstate \
  --username=postgres --dbname=postgres --file=/candidate/tests/sql/h3_pg17_harness.sql
```

El harness crea/recrea roles, schemas, tablas, funciones y datos sintéticos solo en este
cluster nuevo y en su única base `postgres`; aplica las migraciones enumeradas por el
manifest y ejecuta el fixture editorial y los tres harnesses incluidos. No conecta a
Supabase, PostgREST, Edge, Cloudflare ni a otra DB. No hay egress de red. No hay instalación,
pull, build, cambio de imagen, modificación de Docker Desktop, cutover, suites adicionales,
reintento, publicación ni operación Git remota.

## Predicados, límites y parada

- Preflight: rama/HEAD exactos, los 36 hashes presentes, imagen exacta local, nombre de
  contenedor libre, salida de evidencia aún inexistente. Una divergencia detiene antes de
  iniciar PG17.
- Startup: `pg_isready` hasta 60 sondeos de 0.5 s; versión exacta 17.11. La llamada completa
  está limitada a 240 s; el psql a 180 s.
- PASS funcional: psql exit 0 y marcador exacto `h3_pg17_harness_ok`.
- FAIL/timeout: una fase sanitizada con código cerrado (`SQLSTATE_<código>` si se expone con
  verbosity SQLSTATE; de otro modo `HARNESS_FAILED`/`TIMEOUT`), exit no cero, stop y
  eliminación del contenedor efímero exacto. Sin reintento ni siguiente suite.
- stdout/stderr SQL crudos se capturan temporalmente en `/tmp` y se eliminan; nunca se
  imprimen ni conservan. Evidencia persistente: solo líneas `phase=…|error_code=…` en
  `.context/evidencia/h3req1_editorial_atomicity_pg17_once_2026-10-09.md`.
- El contenedor se elimina en la misma invocación sin tocar volúmenes o imágenes. Si el
  proceso recibe SIGKILL, puede quedar el contenedor nombrado; no se autoriza una limpieza
  distinta de la rutina exacta del runner ni una segunda invocación.

## Revisión del cambio y resultado esperado

El test agrega una restricción `NOT VALID` temporal para rechazar exclusivamente el insert
de `action='update'`, captura `CONSTRAINT_NAME` y exige el identificador inyectado. Compara
el registro completo `course_editorial_state` y el número de auditorías contra su snapshot
anterior. La restricción se retira antes de las aserciones positivas preexistentes. No se
modificó SQL de producto.

El resultado runtime está pendiente y no se infiere de la implementación PL/pgSQL ni de
41/41 del manifest separado de safe-suspend C03 v3. Un PASS solo valida este harness exacto;
no acredita F1, r9, Pages/workerd, integración Edge, UAT 144, onboarding 10/10, GO_LOCAL_PR,
CI remoto o GO_DEVELOPMENT_REAL.
