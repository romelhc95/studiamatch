# JIT — atomicidad editorial PG17 con clasificador de versión acotado — 2026-10-09

Estado: requiere aprobación humana nueva. El JIT editorial inicial se consumió en
`VERSION_MISMATCH`; la consulta de versión posterior se consumió en
`VERSION_OUTPUT_INVALID`. Ninguna ejecución alcanzó el harness SQL. Este paquete usa un runner
versionado que prueba primero la clasificación sintética de versiones y reporta solo major/minor.

## Objetivo y alcance

Ejecutar una vez el harness editorial fijado solo si la imagen local fijada informa PostgreSQL
17.11 después de normalizar un sufijo de distribución permitido. Si informa otra versión, se
detiene antes de SQL y emite únicamente un código `VERSION_<major>_<minor>`. No se corrige ni
reemplaza la imagen.

## Candidato e inputs

| Elemento | Valor |
|---|---|
| Checkout / rama / HEAD | `/home/romel/src/studiamatch-h3req1-sync-20261002` / `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c` |
| Harness | `tests/sql/h3_pg17_harness.sql`, SHA-256 `24868250cf598a42412394c9cc714e6826096865846d0e8c3a73cb2a02f8e355` |
| Manifest transitivo | `.context/operaciones/manifest_h3req1_editorial_atomicity_pg17_2026-10-09.sha256`, SHA-256 `0ed63a7b439275121caa9255ea033030f20e363fdb71eb202a47a94792ab2bc5`, 36 inputs |
| Runner V2 | `tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_v2_once.sh`, SHA-256 `0292c231da0c379312152471d5f455103d6399985c2aef0fc839f81d08294d6a` |
| Imagen local | `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`, sin pull |

## Comando único

Ejecutar una vez como `romel` no-root en Ubuntu WSL:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_c03_atomicity_pg17/run_editorial_atomicity_v2_once.sh'
readonly RUNNER_SHA256='0292c231da0c379312152471d5f455103d6399985c2aef0fc839f81d08294d6a'
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

## Etapas condicionadas y límites

1. Verifica candidato, manifest e imagen local exacta.
2. Ejecuta siete casos sintéticos del parser de versión antes de crear Docker. Los casos cubren
   formato corto, sufijo Debian con separador ASCII, minor distinto, major distinto, CR final y
   entradas con saltos de línea o sufijos no clasificables. Cualquier fallo detiene la invocación.
3. Crea un contenedor nuevo `h3req1-editorial-atomicity-pg17-v2-once-20261009` con `--pull=never`,
   `--network none`, sin puertos ni volúmenes, bind mounts read-only de `tests/sql`,
   `db/migrations`, `db/seeds` y PGDATA tmpfs de 1 GiB. Máximo 2 CPU, 2 GiB RAM y 256 PIDs.
4. Lee `postgres --version` una vez. Solo `VERSION_17_11` permite ejecutar una vez el harness
   `tests/sql/h3_pg17_harness.sql`; cualquier otro major/minor termina antes de SQL.
5. PSQL se limita a 180 s. Salidas SQL crudas se capturan temporalmente y se eliminan. Se
   conserva solo fase/código sanitizados. El trap detiene y elimina el ID exacto del contenedor,
   nunca volúmenes.

No consulta datos remotos, Supabase, PostgREST, Edge o Cloudflare; no lee `.env*`, no usa
credenciales, no hace pull/build/install, no cambia Docker, no toca `studiamatch-dev`, y no
realiza push/PR/merge/deploy. Un fallo/timeout consume la invocación; sin retry ni suite siguiente.

La aprobación anterior del harness y la consulta de versión no se reutilizan. Este paquete no
acredita por sí solo G01 ni GO; el resultado funcional exige el marcador exacto
`h3_pg17_harness_ok` y limpieza PASS.
