# G07 C03 integrado R39 — clasificar recuperación Pages/Edge

Candidato: `feat/h3req1-sync-20261002`, baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. R38 pasó SQL suspension,
finalización de Auth una vez, audit exacto mientras seguía suspendido, safe-resume
y assertions SQL recuperadas. `/control/recovery` falló con `AssertionError`
genérico, sin predicate; no se atribuye el fallo a producto.

R39 añade códigos cerrados para cada predicado de `pagesAndEdgeRecovery`: replay
Edge (status, misma invitación, sin segunda llamada Auth), sesión Pages (status,
authenticated, AAL2) y rol Admin BFF (status y valor). El wrapper valida el
formato `RECOVERY_[A-Z0-9_]{1,48}` y solo adjunta `{predicate}`. No registra
mensajes, valores de respuesta, cookies, metadata ni secretos.

Archivos de cambio: `tests/h3req1_c03_integrated_runtime.mjs`,
`tests/h3req1_c03_login_result.mjs`; runner y contrato R39. Sin cambios al
producto o SQL.

Preflight PASS: sintaxis Bash y Node; contrato 30/30 en `studiamatch-dev`;
ShellCheck 0.11.0; `git diff --check`; manifiesto 111/111, SHA-256
`703129159e15e1a3f0ea92e2594c9fa33420946944c06c2b9ec47200196b1763`.

Ejecución, una vez, timeout 2400 s, stop-on-failure:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r39.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R39 \
  --manifest-sha256 703129159e15e1a3f0ea92e2594c9fa33420946944c06c2b9ec47200196b1763
```

## Resultado ejecutado R39

R39 se consumió una vez, exit 1, con resultado sanitizado
`RECOVERY_CONTRACT_FAILED` / `RECOVERY_EDGE_REPLAY_STATUS`. Antes de detenerse,
pasaron snapshot, PG17 17.11, bootstrap H2→H3, setup de cuota y dispatcher,
fixture, PostgREST, login Pages/workerd AAL2, reserva previa, suspensión
persistente, rechazo del dispatcher con HTTP 403/SQLSTATE 42501 y nonce
preservado, finalización única de Auth mientras SQL seguía suspendido, safe-resume
y assertions SQL recuperadas. No quedó registrado el status ni el código
estructurado de la respuesta Edge al replay; no se atribuye aún a producto ni al
harness. El siguiente cambio acotado agrega solo esa clasificación cerrada.

Log sanitizado: [R39](h3req1_c03_integrated_run_2026-10-10_r39.txt), SHA-256
`b526908cd89b0b30c440ac184a795a14c23244f31a264258f7b0f39c30ac79d3`.
Inventario y retirada selectiva: [recursos R39](h3req1_c03_r39_resource_inventory_2026-10-10.md).
