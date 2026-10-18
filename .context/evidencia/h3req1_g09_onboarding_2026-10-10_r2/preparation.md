# H3REQ1 G09 — onboarding local aislado R2

Fecha: 2026-10-10. Candidato: `feat/h3req1-sync-20261002` at baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Delta desde R1

R1 se detuvo antes de runtime porque `tests/sql/h3_pg17_harness.sql` incluye
`db/seeds/h3_admin_seed_local.sql` y el PG container no tenía montado `db/seeds`.
El fallo fue del runner/fixture (`PG17_H3_HARNESS_RESEED_FAILED`), no de producto.
El log está preservado en `../h3req1_g09_onboarding_2026-10-10_r1/` con SHA-256
`2d52a9ad8451b658d150afd425ef0577dadb683d12d850b931b186c0be2396ba`.

R2 es un runner separado, derivado de R1. Su único cambio funcional en el despacho es
añadir al PG17 el bind mount `db/seeds -> /candidate/db/seeds` read-only. Cambian
identificadores de run, base, red, archivos temporales y salida para mantener R1 intacto.
Reutiliza los volúmenes existentes `h3req1-g08-web-node-modules-r1`,
`h3req1-g08-mock-node-modules-20261010-r1` y
`h3req1-c03-integrated-miniflare-node-modules-20261006-r4`; el output de build es el
conjunto fijado `h3req1_final_build_2026-10-10_r2/out`.

## Alcance y aislamiento

PG17.11 desechable con PGDATA tmpfs de 1 GiB, límites de 2 GiB/2 CPU, red Docker
`--internal`, sin puertos publicados ni volúmenes persistentes. Pages/workerd y mock
usan la imagen local V3 fijada, máximo 4 GiB/2 CPU, mounts de código/build/dependencias
read-only y credenciales generadas solo para esta prueba. No se monta `.env*`, no hay
egress a servicios externos ni cuentas/correo/datos operativos. Onboarding usa los 10
casos y pacing de `tests/h3_invitation_uat.mjs`, sin retries.

## Preflight y revisión R2

Runner: `h3req1_g09_onboarding_local_runner_r2.sh`, SHA-256
`2c287bb50baaf858f7af500bb9ec3c7938cc1374c047608153d4fc819eff1d60`.
`bash -n` PASS; ShellCheck 0.11.0 en contenedor read-only/network-none PASS. Revisión
comparativa con R1: montajes, volúmenes, límites, sintéticos, gating, stop-on-failure,
resumen sanitizado y cleanup coinciden; R2 añade únicamente el bind read-only de seeds
y usa recursos/salidas con sufijo R2. Fuente previa de aceptación PG17:
`.context/evidencia/h3req1_g09_pg17_harness_2026-10-10_r1.txt` (marker `h3_pg17_harness_ok`).

## Resultado

### R2 — detenido en runtime-readiness

Exit 1 con `PAGES_WORKER_OR_MOCK_RUNTIME_NOT_READY`. La aserción exacta en
`tests/h3_local_runtime_server.mjs:14` exige que `MOCK_DB_NAME` comience con
`h3_final_uat_`; R2 usó `h3_onboarding_g09_...`. El proceso local salió antes de abrir
los puertos del runtime. El mock inició en 3332. No se ejecutaron Playwright ni casos de
invitación. App exit 137 por el trap, `OOMKilled=false`.

Runtime log SHA-256 `20528a4ac10ffc60734bbd913e1cd1f358e224799e0ba5b9d4637100183981d9`;
mock log SHA-256 `76ef9be1338b976d207e130b5464f213d276e8b32e2b8d829b300bdd97b31756`.
R2 PG17 ID `b8c43ec6ef8a6efc3531f58955d7aeed9b4c6de59f9a27d6bc654b0c482d7bef`, app
ID `e9d8c62d81f5ce206053f7bb18125984e2cc97ee772ef75d1fe9a46a0d5d4e70`, red interna
ID `b76b1922787f51f53b46c7edd3a73292c5b50dcf81c52f05cf34a74395f9bf19`. Se verificaron
labels/estado/tmpfs y luego se retiraron solo esos IDs (sin `-v`):
`APP_TMPFS_FIXTURE_AND_INTERNAL_NETWORK_REMOVED`. Los logs/manifiestos R2 permanecen.

El R1 fallido también fue retirado selectivamente después de preservar su log y
metadata, según el registro de R1. R3 cambia únicamente el prefijo del nombre de base
sintética para satisfacer el guard local; el próximo resultado queda pendiente.
