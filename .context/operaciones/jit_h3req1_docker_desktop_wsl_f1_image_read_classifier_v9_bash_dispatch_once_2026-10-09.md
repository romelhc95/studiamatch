# JIT — ejecutar V9 con el intérprete fijado

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-READ-CLASSIFIER-V9-BASH-DISPATCH-ONCE-20261009-V1`
Estado: preparado; requiere nueva autorización; una invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo y permiso

La autorización anterior del JIT V9 (`f2d19ea…`) se consumió porque Codex despachó el archivo
`.sh` a Python. El wrapper no se ejecutó y no hubo operaciones Docker. La evidencia está en
[el resultado del despacho](../evidencia/h3req1_c03_v9_python_dispatch_failure_2026-10-09.md).
No se reutiliza esa aprobación.

Esta solicitud autoriza una sola invocación del wrapper V9, con el mismo alcance del
[JIT clasificador V9](jit_h3req1_docker_desktop_wsl_f1_image_read_classifier_v9_once_2026-10-09.md):
una lectura read-only de la imagen sintética exacta; si pasa, catorce pruebas en un contenedor
efímero y hasta 25 probes sintéticos de expresiones en un contenedor temporal. El wrapper limita
stdout/stderr, usa fases/códigos allowlisted y detiene ante FAIL/timeout. No lee F1, no ejecuta
r9, no accede a `studiamatch-dev`, no hace pull/build/install/retry y no cambia Docker.

Ejecutor: `romel` no-root en terminal Ubuntu WSL interactiva, con `require_escalated` del entorno
y sin `sudo`.

## Pines y comando único

- JIT V9 base: SHA-256 `f2d19ea84397c66ab6ba2755e38b840448a8f40def796ac7895904029805d86c`.
- Wrapper V9: SHA-256 `2f12d0afe106b49ed2dba68a5403783837b6883bfc329384112424a718a1e2b3`.
- El JIT V9 base contiene y fija los hashes del clasificador, 14 pruebas, test runner y
  orquestador; la revisión independiente final confirmó su alineación.

```bash
(
set -u -o pipefail
readonly BASE_JIT='/home/romel/src/studiamatch-h3req1-sync-20261002/.context/operaciones/jit_h3req1_docker_desktop_wsl_f1_image_read_classifier_v9_once_2026-10-09.md'
readonly BASE_JIT_SHA256='f2d19ea84397c66ab6ba2755e38b840448a8f40def796ac7895904029805d86c'
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_template_expression_probe_v9_once.sh'
readonly RUNNER_SHA256='2f12d0afe106b49ed2dba68a5403783837b6883bfc329384112424a718a1e2b3'
if (( EUID == 0 )); then
  printf 'phase=jit-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=jit-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
base_line="$(/usr/bin/sha256sum -- "$BASE_JIT" 2>/dev/null)" || {
  printf 'phase=jit-preflight|error_code=BASE_JIT_HASH_FAILED\n'
  exit 1
}
if [[ "${base_line%% *}" != "$BASE_JIT_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=BASE_JIT_HASH_MISMATCH\n'
  exit 1
fi
runner_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${runner_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=5s 450s \
  /bin/bash "$RUNNER" 2>/dev/null
)
```

Solo el wrapper en Bash puede iniciar el runner. La autorización nueva cubre ese bloque una vez;
cualquier resultado/timeout la consume. Si falla un preflight, no repetir ni ejecutar Docker.
Esta solicitud no aprueba operaciones posteriores ni amplía el scope V9.
