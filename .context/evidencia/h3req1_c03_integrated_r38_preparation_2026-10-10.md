# G07 C03 integrado R38 — confirmar orden de auditoría

Candidato: rama `feat/h3req1-sync-20261002`, baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`. R37 pasó membresía (`H3S11`) y
falló el predicado de auditoría prefinalización (`H3S12`). El código de
`admin_invitation_complete` inserta la auditoría al finalizar Auth; el runtime
libera la llamada Auth antes de completar la RPC, y el check posterior bajo SQL
suspendido exige una fila exactamente.

R38 corrige el orden del harness: antes de la finalización verifica que no exista
auditoría `invite`; después de liberar el request, la aserción
`h3req1_c03_integrated_assert_completed_suspended.sql` exige exactamente una
fila, mientras la base sigue suspendida. No cambia implementación, privilegios,
contratos ni cobertura; conserva el control de no auditar antes de que Auth acepte
la invitación y el de auditar exactamente una vez al completar.

Runner: `tests/h3req1_c03_integrated_drill_r38.sh`.
Contrato: `tests/h3req1_c03_integrated_drill_r38_contract.test.mjs`.
SQL de aserción: `tests/sql/h3req1_c03_integrated_assert_suspended.sql`.

Preflight PASS: Bash syntax, Node syntax, contrato 29/29 en `studiamatch-dev`,
ShellCheck 0.11.0, `git diff --check`; manifiesto 109/109, SHA-256
`6706ff38f2ea8461d3c1437df6f43188cc3efcbf40eb22188c3c2d46f27e4558`.

Ejecución fijada, una vez con timeout total 2400 s y stop-on-failure:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r38.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R38 \
  --manifest-sha256 6706ff38f2ea8461d3c1437df6f43188cc3efcbf40eb22188c3c2d46f27e4558
```

## Resultado R38

R38 pasó manifest/snapshot, cachés, PG17 17.11, bootstrap, setup, PostgREST,
Pages/workerd login AAL2, reserva in-flight, suspensión Pages/Edge, dispatcher
firmado 403/42501 con nonce preservado, suspensión SQL, liberación Auth una vez,
finalización/auditoría mientras SQL seguía suspendido, safe-resume y aserciones
de recuperación SQL. Falló el siguiente control de runtime
`/control/recovery`, exit 1: el wrapper reportó solo `AssertionError`, sin
predicado clasificable. Log sanitizado `h3req1_c03_integrated_run_2026-10-10_r38.txt`,
SHA-256 `5bbd56dedf647ca7f391ef792b466f8cfdd8bb7b2ddc97bc65729178e5c6beee`.

La causa del fallo de recovery aún no está identificada. No se atribuye a Pages,
Edge, BFF o sesión. Se instrumentará únicamente `pagesAndEdgeRecovery` con códigos
cerrados para sus predicados (replay Edge, no segunda invitación, sesión AAL2 y
rol admin), manteniendo ocultos mensajes, payloads y valores recibidos.
