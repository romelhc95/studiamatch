# H3REQ1 G09 — onboarding local aislado R3

Fecha: 2026-10-10. Candidato: `feat/h3req1-sync-20261002` at baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Historial del fixture

- R1 exit 1 en `pg17-fixture-seed-after-tmpfs-reset`: faltaba montar `db/seeds`
  read-only. Diagnóstico, log, hash y cleanup exacto están registrados en
  `../h3req1_g09_onboarding_2026-10-10_r1/preparation.md`.
- R2 exit 1 en `runtime-readiness`: `tests/h3_local_runtime_server.mjs:14` exige
  `MOCK_DB_NAME` con prefijo `h3_final_uat_`; el nombre R2 no cumplía. Log del runtime
  SHA-256 `20528a4ac10ffc60734bbd913e1cd1f358e224799e0ba5b9d4637100183981d9`; mock log
  SHA-256 `76ef9be1338b976d207e130b5464f213d276e8b32e2b8d829b300bdd97b31756`. Playwright
  y los diez casos no iniciaron. El app terminó exit 137 por stop del trap,
  `OOMKilled=false`; no indica falta de memoria. Tras archivar metadata, PG17 ID
  `b8c43ec6ef8a6efc3531f58955d7aeed9b4c6de59f9a27d6bc654b0c482d7bef`, app ID
  `e9d8c62d81f5ce206053f7bb18125984e2cc97ee772ef75d1fe9a46a0d5d4e70` y red interna ID
  `b76b1922787f51f53b46c7edd3a73292c5b50dcf81c52f05cf34a74395f9bf19` se verificaron
  por label/estado/tmpfs y se retiraron sin `-v`:
  `APP_TMPFS_FIXTURE_AND_INTERNAL_NETWORK_REMOVED`.

## Preparación R3

R3 deriva del runner R2, conserva el mount read-only de seeds, los recursos fijados,
límites, gating, credenciales sintéticas, contención de egress y cleanup exacto. El delta
de configuración que corrige el fallo R2 es `MOCK_DB_NAME=h3_final_uat_onboarding_g09_20261010_r3`;
los nombres de red/app/PG, DB tmpfs y salidas son propios de R3. Reutiliza el build
verificado `h3req1_final_build_2026-10-10_r2/out` y los volúmenes de dependencias fijados
en R2; no toca `studiamatch-dev` ni los dos holders de snapshots activos.

Runner: `h3req1_g09_onboarding_local_runner_r3.sh`, SHA-256
`78bfc6e8729a975dafc67cb2831570d333fa76cb2902d6b30f7168f65aeaefb0`.
`bash -n` y ShellCheck 0.11.0 dentro de contenedor `--network none --read-only`: PASS.

## Aislamiento y aceptación

PG17.11 tmpfs 1 GiB, límite 2 GiB/2 CPU; red interna sin puertos; runtime de hasta
4 GiB/2 CPU; PG migrations/tests/seeds y fuentes read-only; no se carga `.env*`. Se
ejecutará `tests/h3_invitation_uat.mjs` con 10 IDs fijos, spacing mínimo 20,100 ms,
correo/inbox mock y cuentas sintéticas. El resumen omite correos, tokens y errores crudos;
la meta es 10/10 y cero retries. No se ejecutarán escritores cloud ni se tocarán cuentas
reales.

## Resultado

### R3 — PASS

Exit 0 en `bash .context/evidencia/h3req1_g09_onboarding_local_runner_r3.sh`.
PG17.11 harness emitió los cuatro marcadores; cuota, gateway sintético y Pages/workerd
pasaron. `tests/h3_invitation_uat.mjs` completó `INV-013`, `INV-008`, `INV-001`,
`INV-002`, `INV-009`, `INV-007`, `INV-003`, `INV-004`, `INV-005`, `INV-012`: **10/10,
cero retries**, spacing mínimo de 20,100 ms. Ambiente separado con cuentas/inbox
sintéticas; ninguna cuenta real ni correo externo.

Resumen sanitizado:
`onboarding-r3/onboarding-summary-r3.json`, SHA-256
`0f10784463cecb8951ed2b443f7d798f8c9c7a62525b9dd5179c2575762911b3`. Validación
independiente del JSON confirmó exactamente los diez IDs, PASS individual, pacing y
`environment=isolated-synthetic-local`. Manifiesto de fuentes: 610 archivos, SHA-256
`52c17ce999f616ed7a1828554584cc26298f9b7c4f5b2544232849601f8910e8`; digest de runner
R3 `78bfc6e8729a975dafc67cb2831570d333fa76cb2902d6b30f7168f65aeaefb0`.

Exit mostró `EXACT_FIXTURES_REMOVED_NO_VOLUMES`; el inventario posterior no encuentra
contenedores ni red R1–R3. `studiamatch-dev` sigue healthy. Permanece detenido y
preservado el app R8 de ID `63b1adc5c87d1d7fb5418e5144c5ef606c25ed14135d8ee554da86faaab8019f`;
los startup volume holders S2/S3 son anteriores y quedan fuera de este onboarding.
