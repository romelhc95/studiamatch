# JIT H3REQ1 C03 — V15 output contract V3, invocación única

Fecha: 2026-10-09. Estado: preparado; requiere autorización humana nueva.

## Resultado que motiva este JIT

La autorización del JIT V15 output contract V2 TTY SHA-256
`49243bda140af6038d3e93ed9a2d4d8b19b2206c54a7ac4648f2ab93d5904703` se consumió con
`phase=f1-v15-output-capture|error_code=PHASE_ORDER_MISMATCH`, exit 1. El parser esperaba
un bloque `prior-v12-failure` más siete fases de clasificador antes de
`f1-v15-reducer-tests`. El helper valida esa evidencia sin emitir fases, ejecuta las pruebas
del reductor y después invoca el clasificador anidado. V3 elimina solo ese bloque imposible;
mantiene la segunda secuencia de clasificador y las validaciones de minimalidad. No se
alcanzaron F1 ni r9. No reintentar V2.

## Solicitud concreta

Autorizar una invocación del comando exacto siguiente en Ubuntu WSL como `romel` no-root,
sin `sudo`, lanzada por Codex con `exec_command(tty=true)` y una terminal PTY persistente.
No se acepta salida de shell no interactiva. La llamada respetará el gate normal de
revisión automática. El alcance es una ejecución del diagnóstico sintético V15, hasta 52
probes; no cubre F1, r9, rebuild/cutover, pruebas de producto ni operaciones remotas. Un
FAIL o timeout consume la invocación.

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 600s /bin/bash /home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v15_output_contract_v3_once.sh
```

El runner fijado conserva branch/HEAD, pins de helper/parser/evidencias y el límite de 52
probes de cinco segundos. Ejecuta el diagnóstico sintético aislado y reporta el conjunto
1-minimal de campos que reproduce la interacción. No lee F1, no ejecuta r9, no modifica
`studiamatch-dev`, no hace pull/build/install ni cambia configuración Docker. Cualquier
FAIL, mismatch o timeout consume la invocación; no se reintenta.

## Pins y permisos

- Runner: `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v15_output_contract_v3_once.sh`
- SHA-256 parser: `5b0f6d83c671816ad7cb891d4a78d3b4fe48f7640a3a9f6c2926fefbd41c7597`
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`
- Aprobación solicitada: una invocación; no cubre F1/r9 ni rebuild/cutover.
