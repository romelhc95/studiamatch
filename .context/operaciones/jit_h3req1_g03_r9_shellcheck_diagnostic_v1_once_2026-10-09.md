# JIT — diagnóstico sanitizado ShellCheck r9 — 2026-10-09

**ID:** `H3REQ1-G03-R9-SHELLCHECK-DIAGNOSTIC-V1-ONCE-20261009-V1`  
**Estado:** preparado; requiere aprobación humana para una invocación.

## Hecho precedente

El JIT r9 V4 fue aprobado y consumido. Preflight, extracción, copia aislada, nueve sintéticos de
actionlint y actionlint de los tres workflows pasaron. ShellCheck de los siete scripts terminó
`CHECK_FAILED`, exit 1; por stop-on-failure no corrieron ESLint, TypeScript ni suites focales.
V4 no preservó el diagnóstico ShellCheck y no se reintenta.

Esta invocación nueva clasifica una sola ejecución de ShellCheck para identificar scripts,
líneas, columnas y códigos `SC####`, sin devolver mensajes, fragmentos de código ni salida cruda.
Trece sintéticos comprueban allowlist, coordenadas, códigos, entrada inválida, mismatch de exit,
límite de bytes y cantidad, formato JSON y que el texto sintético no escape. Usa `json1`, el formato de arreglo JSON documentado
por ShellCheck; el formato `json` usa un objeto con `comments` y no corresponde al parser
allowlisted ([manual oficial](https://github.com/koalaman/shellcheck/blob/master/shellcheck.1.md)).

## Candidato e inputs

- Rama/HEAD/WIP tras agregar este JIT: `feat/h3req1-sync-20261002` /
  `4eb4d877a50b012bb630a129bd0c74482c33be9c` / `55/276/0`.
- Package r5: `/tmp/h3req1-g03-validation-29d8fff9-r5`; manifiesto
  `5363610a5fd28558f3e2168dd926aaf1c26037d01b2645de815da7201c00b0ae`, inputs
  `290905c8c88f56ce8c17aaf112e6536185068ea644008c685f299beeaeb1c57b`.
- Tools manifest: `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.
- Imagen local existente `studiamatch-h3req1:20261009-v3`, ID
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Runner host `tests/h3req1_docker_peer_substep_diag/run-r9-shellcheck-diagnostic-v1.sh`,
  SHA-256 `c9097daea8535a82a779fe39d3751e0078593e7b03c1b15026e3991a0771b5cd`.
- Helper interior `tests/h3req1_docker_peer_substep_diag/run-r9-shellcheck-diagnostic-inner-v1.sh`,
  SHA-256 `4d5ded37449829a364f9c6655107e0e1af5ebbd3b62f79a1b41c24cdbdffe47d`.

El runner revalida branch/HEAD/WIP, 68 hashes fuente y 3 archivos package-only, manifests,
endpoint Docker default e ID de la imagen antes de una ejecución temporal. Mounts package,
tools y helper son read-only.

## Alcance de la única ejecución

Como `romel` no-root en terminal Ubuntu WSL interactiva, timeout 120 s:

1. Validar pins e identidad del candidato; detener ante drift.
2. Ejecutar ocho casos sintéticos del clasificador dentro del contenedor aislado.
3. Ejecutar una vez ShellCheck `0.11.0` con salida JSON `json1` para estos siete archivos exactos:
   `scripts/security/scan_credentials.sh`,
   `scripts/security/protected_path_scope_guard.sh`,
   `tests/test_protected_path_scope_guard.sh`,
   `scripts/security/h2_web_mock_smoke.sh`,
   `tests/sql/h3_invitation_reservation_concurrency.sh`, `.githooks/pre-commit` y
   `.githooks/pre-push`.
4. Emitir únicamente `script`, `line`, `column`, `rule=SC####` o código sanitizado de parser;
   fallo o exceso detiene y consume la invocación. No se ejecutan reintentos ni correcciones.

El contenedor es efímero `--rm --pull=never --network=none --read-only`, usuario 1001,
capabilities eliminadas, no-new-privileges y límites de memoria/CPU/PIDs. Usa solo la imagen y
tool archive locales. No toca `studiamatch-dev`, checkout, `.env*`, secretos, DB/SQL, producto,
F1, Git remoto, GitHub, Cloudflare, publicación, PR, merge, settings o deploy. No ejecuta
actionlint, ESLint, TypeScript ni las suites que V4 no alcanzó. Esta autorización no permite
repetir V4; tras el diagnóstico habrá que corregir solo la causa evidenciada y preparar la
validación posterior correspondiente.

## Comando único

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-shellcheck-diagnostic-v1.sh"
readonly RUNNER_SHA256='c9097daea8535a82a779fe39d3751e0078593e7b03c1b15026e3991a0771b5cd'
if (( EUID == 0 )); then
  printf 'phase=dispatch-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=dispatch-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ "$(uname -s 2>/dev/null)" != Linux || "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" != *microsoft* ]]; then
  printf 'phase=dispatch-preflight|error_code=WSL_REQUIRED\n'
  exit 1
fi
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=dispatch-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=INT --kill-after=5s 120s /bin/bash "$RUNNER"
```
