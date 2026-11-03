# JIT H3REQ1 C03 — V15 con TTY, invocación única

Fecha: 2026-10-09. Estado: preparado; requiere nueva autorización humana. La aprobación
anterior no se reutiliza porque se consumió en preflight.

## Resultado que motiva este JIT

La autorización del JIT V15 parser V2 SHA-256
`b9b44f70121be8f7ca91471fdd4410767e5c160ab943996c6dee412b40e7af95` se consumió con
`phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED`, exit 1. El dispatcher fue
lanzado sin TTY interactivo; el runner se detuvo antes de Docker, sintéticos, probes y
lectura F1. No hubo operación Docker ni cambio de recursos. No reintentar esa autorización.

## Solicitud concreta

Autorizar una invocación del comando exacto siguiente en Ubuntu WSL como `romel` no-root,
sin `sudo`, lanzada por Codex con `exec_command(tty=true)` y una terminal PTY persistente.
No se acepta salida de shell no interactiva. La llamada respetará el gate normal de
revisión automática.

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 600s /bin/bash /home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v15_minimal_subset_diagnostic_once.sh
```

El runner fijado conserva branch/HEAD, pins de helper/parser/evidencias y el límite de 52
probes de cinco segundos. Ejecuta el diagnóstico sintético aislado y reporta el conjunto
mínimo de campos que reproduce la interacción. No lee F1, no ejecuta r9, no modifica
`studiamatch-dev`, no hace pull/build/install, no repite probes y no cambia configuración
Docker. Cualquier FAIL, mismatch o timeout consume la invocación; no se reintenta.

## Pins y permisos

- Runner: `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v15_minimal_subset_diagnostic_once.sh`
- SHA-256 runner: `01b0e62d0d80d0292b0ee032854340dbbe0158988b3395ae3704e48ba71cd6cb`
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`
- Aprobación solicitada: una invocación; no cubre F1/r9 ni rebuild/cutover.
