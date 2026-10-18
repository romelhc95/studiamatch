# Solicitud JIT D4 — diagnóstico sintético de ownership con logging válido

Estado: **propuesto, NO aprobado, NO ejecutado**. D2, S1, D3, J1 y J2 están consumidos;
este JIT no reutiliza sus permisos ni accede a sus recursos.

## Objetivo y corrección mínima

Confirmar el comportamiento del fixture sintético tar que D3 no alcanzó. La causa del
fallo de D3 fue recuperada bajo J2: Docker rechazó `--log-driver local` con
`max-file=1` y compresión habilitada. Este runner nuevo fija `--log-opt compress=false`
y conserva `max-size=1m`, `max-file=1`; verifica además que Docker almacenó `compress=false`.

El fixture incluye únicamente `owner.txt`, `nested/data.json` y `SHA256SUMS`; no empaqueta
fuentes del producto ni toca el snapshot S1. D4 puede demostrar o descartar el mecanismo
de ownership bajo estas condiciones; **no demuestra la causa histórica de S1**.

## Inputs fijados

| Input | SHA-256 | Uso |
|---|---|---|
| `tests/h3req1_c03_snapshot_diagnostic_d4.sh` | `785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107` | Runner D4; captura en memoria y ejecución de bytes verificados |
| `tests/h3req1-c03-snapshot-diagnostic-d4.sha256` | `84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c` | Sidecar que fija el runner |

Imagen local ya disponible, sin pull: `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`, plataforma `linux/amd64`.

## Recurso y operaciones autorizables

- Solo contenedor nuevo `h3req1-c03-snapshot-diagnostic-d4-20261007`, etiquetado con
  JIT D4, hash del sidecar y nonce de esta invocación.
- Contexto Docker local: `context show/inspect` solo para obtener el endpoint, exigir
  socket Unix, comprobar `stat`/`realpath` e identidad estable antes de cada llamada.
- `docker image inspect` solo sobre la imagen fijada, sin pull, para verificar que no
  declara volúmenes.
- Una invocación `docker run --detach` para el contenedor nuevo y el fixture offline;
  una espera `docker wait`; una inspección por el ID exacto devuelto; lectura de hasta
  64 líneas del log de ese contenedor nuevo con el sanitizador del runner.
- En error, el runner puede inspeccionar únicamente ese ID completo para verificar
  nombre/labels/red antes de un `docker stop --time 5`, solo si sigue `running`.
  No detiene otros recursos. Contenedor/resource se preserva; no hay `rm` ni cleanup.

Controles del contenedor: `--network none`, sin puertos, `--pull=never`, rootfs read-only,
UID/GID 1001:1001, `--cap-drop=ALL`, `no-new-privileges`, 0.5 CPU, 128 MiB RAM/swap,
64 PIDs, `/dev/shm` 16 MiB, `/diag` tmpfs 16 MiB `noexec,nosuid,nodev`, sin mounts
persistentes y restart deshabilitado. Logging `local`, `max-size=1m`, `max-file=1`,
`compress=false`; el reporte valida el valor efectivo de compresión.

El runner separa exit codes del productor tar, receptor `--same-owner` y receptor
`--no-same-owner`; el diagnóstico de stderr tar se clasifica en memoria, con límite de
4 KiB, sin imprimir stderr crudo. El output Docker allowlisted queda limitado por líneas
sanitizadas y timeouts. Riesgo residual: stdout de algunos controles Docker estructurados
está limitado por timeout pero no tiene un límite explícito de bytes; se presupone daemon
local confiable. También persiste la carrera local stat/connect del socket, no una
autenticación criptográfica del peer. Aceptar o rechazar estos riesgos es decisión humana.

Presupuesto nominal del runner: 180 s; create/start máximo 20 s, wait máximo 60 s,
lecturas/stop máximo 20 s cada una, reserva post-run 100 s. No es watchdog global duro;
el runner detiene solo su recurso nuevo bajo las condiciones descritas.

## Criterio y límites

PASS de mecanismo sintético solo si productor=0; `--same-owner` falla como
`ownership-restore-denied`; `--no-same-owner`=0; y paths allowlisted, sin symlinks,
permisos, espacio y hashes pasan. Cualquier otro resultado es NO-GO y conserva recursos.
No atribuir a S1 ni declarar snapshot completo, smoke, C03 integrado o GO local.

Exclusiones: recursos S1/R1–R4/D3/J1/J2; cualquier `.env*`, secretos, identidad/Auth,
correo, fuentes de producto, npm, workerd/Pages, Edge, PG17/PostgREST, SQL/DB, red externa,
Supabase/Cloudflare, logs/exec/mounts de otros recursos, cleanup, retry, rollback/resume,
Git remoto, CI remoto, push/PR/merge/deploy, schedules y workflow_dispatch.

## Comando exacto — solo tras aprobación humana

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /bin/bash -Eeuo pipefail <<'H3_C03_D4_LAUNCHER'
set -Eeuo pipefail
root="$(git rev-parse --show-toplevel)"
[[ "$root" == "$(pwd -P)" ]] || { printf 'NO-GO: run from candidate root\n' >&2; exit 1; }
[[ "$root" == '/home/romel/src/studiamatch-h3req1-sync-20261002' ]] || { printf 'NO-GO: unexpected checkout\n' >&2; exit 1; }
[[ "$(git branch --show-current)" == 'feat/h3req1-sync-20261002' ]] || { printf 'NO-GO: candidate branch changed\n' >&2; exit 1; }
[[ "$(git rev-parse HEAD)" == '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]] || { printf 'NO-GO: candidate HEAD changed\n' >&2; exit 1; }
runner='tests/h3req1_c03_snapshot_diagnostic_d4.sh'
manifest='tests/h3req1-c03-snapshot-diagnostic-d4.sha256'
expected_runner='785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107'
expected_manifest='84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c'
[[ -f "$runner" && ! -L "$runner" && -f "$manifest" && ! -L "$manifest" ]] \
  || { printf 'NO-GO: D4 runner/manifest unavailable or symlinked\n' >&2; exit 1; }
runner_b64="$(base64 -w0 -- "$runner" 2>/dev/null)" \
  || { printf 'NO-GO: D4 runner capture failed\n' >&2; exit 1; }
manifest_b64="$(base64 -w0 -- "$manifest" 2>/dev/null)" \
  || { printf 'NO-GO: D4 manifest capture failed\n' >&2; exit 1; }
actual_runner="$(printf '%s' "$runner_b64" | base64 --decode | sha256sum | awk '{print $1}')"
actual_manifest="$(printf '%s' "$manifest_b64" | base64 --decode | sha256sum | awk '{print $1}')"
[[ "$actual_runner" == "$expected_runner" && "$actual_manifest" == "$expected_manifest" ]] \
  || { printf 'NO-GO: approved D4 input digest mismatch\n' >&2; exit 1; }
manifest_text="$(printf '%s' "$manifest_b64" | base64 --decode)"
[[ "$manifest_text" == "$expected_runner  $runner" ]] \
  || { printf 'NO-GO: D4 manifest does not pin its runner\n' >&2; exit 1; }
printf '%s' "$runner_b64" | base64 --decode | \
  /usr/bin/env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="$HOME" LANG=C LC_ALL=C \
  H3_DIAG_ROOT="$root" \
  H3_DIAG_VERIFIED_RUNNER_SHA256="$actual_runner" \
  H3_DIAG_VERIFIED_MANIFEST_SHA256="$actual_manifest" \
  /bin/bash -s -- \
    --jit H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D4 \
    --runner-sha256 "$actual_runner" \
    --manifest-sha256 "$actual_manifest"
H3_C03_D4_LAUNCHER
```

La aprobación corresponde a una única invocación de este comando y a los efectos listados.
No autoriza validar el snapshot fuente completo ni iniciar Pages/workerd; ambos necesitan
manifiestos y JIT separados.

## Estado del preflight estático (2026-10-07)

- `bash -n` del runner, `sh -n` del payload sintético, `bash -n` del launcher, verificación
  del sidecar y hashes ejecutados localmente: PASS; no se ejecutó Docker.
- Auditor `security-auditor`: el primer intento no pudo acceder al checkout; la segunda
  revisión cubrió solo el delta descrito, no el runner/JIT completos. No encontró HIGH o
  MEDIUM aparentes en ese delta; observó que `--pull=never` no basta para afirmar offline.
  El runner fija `--network none`, por lo que esa salvedad condicional queda cubierta.
- La revisión estática local confirma `--network none`, límites de línea/timeout, sanitizado
  de streams, identidad/labels antes de stop, `compress=false` comprobado en inspect y
  conservación sin remove/cleanup. Esto no equivale a auditoría runtime.
- Riesgos residuales explícitos: stdout de algunos controles Docker estructurados no tiene
  límite de bytes aunque sí timeout; se presupone daemon local confiable. La comprobación
  de identidad del socket conserva una carrera stat/connect y no autentica criptográficamente
  el peer. La decisión de aceptar esos riesgos corresponde al humano que apruebe este JIT.

Este JIT está propuesto, NO aprobado y NO ejecutado. Un fallo, timeout o desajuste de hash
detiene el runner; no autoriza retry ni acceso a otros recursos.
