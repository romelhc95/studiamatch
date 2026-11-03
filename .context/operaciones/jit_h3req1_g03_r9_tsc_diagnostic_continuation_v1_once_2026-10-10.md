# H3REQ1 G03 — diagnóstico TypeScript y continuación r9 (V1 one-shot)

Fecha: 2026-10-10. Estado: preparado; requiere aprobación humana nueva.

## Motivo y resultado anterior

El JIT r9 V7 terminó con `phase=r9-typescript|error_code=CHECK_FAILED`, exit 134. Llegó a ese
gate después de que pasaran los pins, cuatro sintéticos del lector Docker, actionlint reutilizado
por hashes idénticos, ShellCheck, snapshot de candidato, manifest de dependencias, versiones,
`next typegen` y ESLint. El runner descartó el texto de TypeScript; la causa no está demostrada.
V7 está consumido y no se repite.

## Solicitud agrupada

Se solicita una sola invocación de
`H3REQ1-G03-R9-TSC-OUTPUT-CLASSIFIED-CONTINUATION-V1-ONCE-20261010-V1`, ejecutada en TTY Ubuntu
WSL como `romel` no-root, sin `sudo`, con `sandbox_permissions=require_escalated` para acceso al
socket Docker Desktop. Timeout total 180 s; cero retries. La elevación pertenece al sandbox de
Codex y no cambia el EUID.

El runner repite solo preflight read-only y verificaciones de hashes. Copia el snapshot fijado a
`/tmp` dentro del contenedor y enlaza el volumen de dependencias read-only. Actionlint, ShellCheck,
`next typegen`, ESLint y sus PASS V7 se reutilizan porque sus inputs permanecen fijados. En el
contenedor efímero ejecuta siete sintéticos de clasificación, `tsc --noEmit` una vez y, solo si
TypeScript pasa, las tres suites r9 restantes: revisión de workflow protegido, credential scan y
path scope guard. Cualquier fallo detiene las posteriores.

El clasificador captura stdout/stderr de `tsc` en memoria con límite de 64 KiB, elimina el texto
crudo y permite emitir únicamente fase/código o, para errores TS parseables, path relativo bajo
`web/src`, `web/test(s)` o `web/types`, línea, columna y `TS####`. Clasifica por separado heap
limit, proceso abortado/muerto, salida excedida, paths no allowlisted y fallo no clasificado.
No infiere OOM a partir de exit 134 por sí solo.

## Inputs, recursos y límites

- Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
  `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`, WIP previsto
  `55/284/0` al guardar este JIT.
- Imagen local `studiamatch-h3req1:20261009-v3`, digest
  `sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63`.
- Contenedor existente solo para comprobar su identidad/health: `studiamatch-dev`, ID
  `500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049`; volumen
  `studiamatch_h3req1_node_modules` read-only.
- Host runner: [run_r9_tsc_diagnostic_host_v1.sh](../../tests/h3req1_docker_peer_substep_diag/run_r9_tsc_diagnostic_host_v1.sh), SHA-256
  `462f97186f13780fafeeb4e10095370746098ea0629e9b0d66476b77ad6c3694`.
- Inner runner: [run_r9_tsc_diagnostic_inner_v1.sh](../../tests/h3req1_docker_peer_substep_diag/run_r9_tsc_diagnostic_inner_v1.sh), SHA-256
  `37e72af44a00e556cdd75e720b943d2215cf6f8a206e38786a10c27b26664458`.
- Clasificador: [r9_tsc_output_classifier_v1.py](../../tests/h3req1_docker_peer_substep_diag/r9_tsc_output_classifier_v1.py), SHA-256
  `80ffe519aba990cf081fdd48a9c014ba26094176df0efaf09772b0a96baff8a6`.
- Dispatcher/captura: [run_r9_tsc_diagnostic_dispatch_v1.sh](../../tests/h3req1_docker_peer_substep_diag/run_r9_tsc_diagnostic_dispatch_v1.sh), SHA-256
  `4c55ca82a8c0ed2f89b83fc216a8643a5694b7968b9f5ae1e90ed1d30f2775a5`.
- Contenedor temporal: `--rm --pull=never --network=none --read-only`, UID 1001, sin capabilities,
  memoria/swap total 512 MiB, 1 CPU, 64 PIDs, tmpfs ya fijados por V7, mounts del paquete y
  herramientas read-only. No sube límites respecto al intento previo.
- Evidencia sanitizada: `.context/evidencia/h3req1_g03_r9_tsc_v1_execution_2026-10-10.txt`;
  el dispatcher limita la captura total a 8192 bytes.
- Sin pull/build/install, egress, `.env`/secretos, F1, DB/SQL, volúmenes escribibles, cambios
  Docker persistentes, limpieza ajena, operaciones Git/CI remotas ni deploy.

## Comando único

Ejecutar este bloque exactamente una vez con TTY y `sandbox_permissions=require_escalated`:

```bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly DISPATCHER="$ROOT/tests/h3req1_docker_peer_substep_diag/run_r9_tsc_diagnostic_dispatch_v1.sh"
readonly DISPATCHER_SHA256='4c55ca82a8c0ed2f89b83fc216a8643a5694b7968b9f5ae1e90ed1d30f2775a5'
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
hash_line="$(/usr/bin/sha256sum -- "$DISPATCHER" 2>/dev/null)" || {
  printf 'phase=dispatch-preflight|error_code=DISPATCHER_HASH_FAILED\n'
  exit 1
}
if [[ "${hash_line%% *}" != "$DISPATCHER_SHA256" ]]; then
  printf 'phase=dispatch-preflight|error_code=DISPATCHER_HASH_MISMATCH\n'
  exit 1
fi
exec /bin/bash "$DISPATCHER"
```

El dispatcher verifica de nuevo rama/HEAD/WIP, hashes, ausencia de evidencia previa y el timeout.
La autorización se considera consumida al iniciar el bloque, incluso si falla preflight; no se
repite. Un resultado TypeScript distinto de PASS detiene las tres suites dependientes. Este JIT
no acredita G03 hasta que termine también el resumen `ALL_REMAINING_CHECKS_OK`.
