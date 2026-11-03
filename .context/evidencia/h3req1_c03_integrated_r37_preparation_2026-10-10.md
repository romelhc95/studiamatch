# G07 C03 integrado R37 — aislar continuidad admin y auditoría

Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
R36 llegó a suspensión y falló `H3S11`, exit 3. La aserción agrupaba continuidad
de `admin_members` y una fila de `admin_membership_audit`; R36 no podía distinguir
cuál. No se presume cuál falla.

R37 separa las condiciones estrictamente en el harness:

- `H3S11`: existe la membresía Admin sintética activa, lista y con rol admin.
- `H3S12`: existe la auditoría de invitación asociada a la invitación in-flight.

No cambia el producto ni reduce cobertura. Runner:
`tests/h3req1_c03_integrated_drill_r37.sh`; contrato:
`tests/h3req1_c03_integrated_drill_r37_contract.test.mjs`; SQL existente:
`tests/sql/h3req1_c03_integrated_assert_suspended.sql`.

Durante la primera validación local del contrato, la lista de SQLSTATE detectó el
antiguo `H3S11` combinado duplicado junto a los dos nuevos: 28/29 tests PASS,
1 FAIL. Se retiró solo esa condición antigua. El contrato posterior pasó 29/29.

Preflight actual: Bash syntax, Node syntax, contrato 29/29 en `studiamatch-dev`,
ShellCheck 0.11.0, `git diff --check`; manifiesto 107/107 hashes PASS, SHA-256
`a7ad6a667a43764a974f2e5aac0a3eb0054a9898731212b641cd9d371a63190b`.

Próxima ejecución fijada (una vez, timeout total 2400 s, stop-on-failure):

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 2400s \
  /bin/bash tests/h3req1_c03_integrated_drill_r37.sh \
  --jit H3-CLOSE-03-INTEGRATED-2026-10-10-R37 \
  --manifest-sha256 a7ad6a667a43764a974f2e5aac0a3eb0054a9898731212b641cd9d371a63190b
```

La salida posterior podrá clasificar solo `H3S11` o `H3S12`; si pasa ambas,
continúa según el runner a finalización in-flight, resume persistente, idempotencia,
cuotas, auditoría y cleanup. Si falla, detener y corregir el predicado demostrado.

## Resultado R37

Preflight/manifest, PG17 17.11, bootstrap, fixtures, PostgREST, login AAL2, reserva,
suspensión coordinada Pages/Edge y dispatcher firmado 403/42501 con nonce
preservado pasaron. `H3S11` pasó; falló `H3S12` con psql exit 3. Log sanitizado
`h3req1_c03_integrated_run_2026-10-10_r37.txt`, SHA-256
`f5b4e9b7f099aa21dad4b73da6fa408c424bf0742548fc955b5bba691c96a3c8`.

La causa demostrada es un predicado de prueba anticipado: el harness esperaba la
auditoría antes de liberar la llamada Auth retenida. El código SQL de
`admin_invitation_complete` inserta esa auditoría durante la finalización, y el
runtime solo la invoca tras `releaseInFlight`. La prueba posterior
`h3req1_c03_integrated_assert_completed_suspended.sql` exige exactamente una
auditoría mientras SQL sigue suspendido. R38 cambiará solo el predicado previo a
esperar ausencia de esa auditoría, manteniendo la aserción post-finalización de
exactamente una. Esto es una corrección del orden de aceptación del test, no una
remediación de producto ni eliminación de controles.
