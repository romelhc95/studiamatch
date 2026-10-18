# H3REQ1 — lectura única de versión de imagen PG17 fijada

Estado: requiere aprobación humana nueva. La invocación autorizada del harness editorial
terminó en `pg17-version|VERSION_MISMATCH` y fue consumida. Este JIT no repite SQL ni el
harness; clasifica una vez la versión del binario en la imagen ya fijada para determinar el
predicado real. No cambia la imagen ni remedia nada.

## Ejecución solicitada

Una invocación como `romel` no-root en Ubuntu WSL, sin `sudo`, ejecutando exactamente:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_c03_atomicity_pg17/read_pinned_image_version_once.sh'
readonly RUNNER_SHA256='fa2203dc1f034116bdf2251b04f165f7e617e5e2aa988f6d94fd94a98bf2fcf4'
if (( EUID == 0 )); then
  printf 'phase=jit-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=jit-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=2s 45s /bin/bash "$RUNNER"
```

Una falla, discrepancia, timeout o salida inválida consume esta invocación. No hay retry.

## Alcance exacto

- Candidato rama `feat/h3req1-sync-20261002`, HEAD
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Inspección local read-only y una sola ejecución del binario `postgres --version` desde
  `postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`, con
  `--pull=never`.
- Un contenedor efímero identificado como `h3req1-pg17-image-version-once-20261009`, sin red,
  puertos, mounts de host, datos, SQL ni credenciales; root filesystem read-only, `/tmp` tmpfs
  8 MiB, 0.5 CPU, 128 MiB RAM y 16 PIDs; capacidades retiradas y `no-new-privileges`.
- El runner captura la línea del binario solo en memoria. Nunca emite la salida cruda: produce
  fase/código sanitizados (`VERSION_17_n`, `VERSION_OUTPUT_INVALID`, etc.) y elimina por ID el
  contenedor exacto en cleanup.
- No hace pull/build, no consulta `.env*`, no modifica imágenes/configuración, no ejecuta SQL,
  no reintenta el harness, no accede a `studiamatch-dev`, no lee F1/r9, y no realiza operaciones
  GitHub, Cloudflare, Supabase, push/PR/merge o deploy.

El resultado identifica el requisito real del siguiente paquete, pero no acredita G01 ni
autoriza otra ejecución del harness. Una eventual lectura del harness o cambio de pin tendrá
JIT propio.
