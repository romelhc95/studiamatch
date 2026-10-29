# G07 — resultado R19, TLS superado; invitación aún no llega a Auth

## Identidad e inputs

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`.
- Rama `feat/h3req1-sync-20261002`; HEAD baseline
  `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Runner R19 SHA-256 `f439671c221fdd7440243ec09a56c63d75c37259a0d6b04516cae56d3f25d349`;
  contrato `0244e86232402a9cd3015c68af83939c351d45a1b092b878b2ffebd6ad6c4e07`;
  runtime `11dd1bb70bad3e8f19eee01f5683482e8d0da912042ddb1f0c4810c1274896c6`.
- Manifiesto: 69/69; SHA-256
  `6bed68f48085fa69992f4fecd32f6c6014ac8fe6c12809d4ce8688535a987d1a`.
- Registro íntegro sanitizado: [R19 log](h3req1_c03_integrated_run_2026-10-10_r19.txt),
  SHA-256 `48a58c1f312bfc99505afef57a567cfd33b86858d18799521f68219f90b6ca28`.
  La copia `.log` es byte-idéntica; se conservó `.txt` porque `*.log` está ignorado.

## Resultado realmente ejecutado

Comando: `bash tests/h3req1_c03_integrated_drill_r19.sh --jit
H3-CLOSE-03-INTEGRATED-2026-10-10-R19 --manifest-sha256
6bed68f48085fa69992f4fecd32f6c6014ac8fe6c12809d4ce8688535a987d1a`.

Exit final **1**. Pasaron Docker Desktop identity/capacity, manifiesto 69/69, versión PG17
17.11, snapshot y cache verifiers, contrato del runner, tres SQL bootstrap/fixture gates,
PostgREST readiness y login Pages/workerd (`aal2`, cookies requeridas). La generación de CA
v3 pasó sus predicados de extensiones y cadena. No se acreditó la invitación ni su reserva.

La etapa `real-edge-invite-held-after-reservation` falló con `INVITE_EARLY_UNAUTHORIZED`.
Contadores del mismo paso: `functionRequests=1`, `functionCalls=1`, rechazos de key/session
en el bridge de Function `0`; `authUserRequests=1`, `authUserAccepted=1` en toda la corrida
(consistente con login), `adminMemberRequests=0`, `requestAdmission=0` y
`invitationReserve=0`. El error TLS R18 ya no apareció como clasificación de esta corrida,
pero el contador Auth compartido no demuestra un handshake Edge/Auth. No se atribuye el fallo
a TLS, al código funcional ni al gateway hasta observar esa frontera.

El runner detuvo los cuatro servicios de la invocación por sus identidades fijadas. Estado:
Edge/PostgREST `exited 15/255`, PG17 `exited 0`, runtime `exited 143`; no se informó OOM.
Snapshot de código, TLS, cachés y redes internas R19 se conservaron; `studiamatch-dev`
permaneció healthy y sin uso en C03. No se retiraron volúmenes ni imágenes.

## Siguiente diagnóstico mínimo

El primer intento de diagnóstico por `docker start` del contenedor mock R19 produjo
`phase=mock-gateway-restart|error_code=PROCESS_EXIT_1`, exit 1, `OOMKilled=false` y sin
error del daemon; el Edge probe no llegó a iniciarse. Como el runtime es one-shot y usa
`log-driver none`, la causa de ese reinicio no quedó observable. Resultado sanitizado en
`h3req1_c03_edge_auth_transport_probe_r19_restart_failure_2026-10-10.txt`. No se atribuye
este resultado al producto ni se reintenta el mismo contenedor.

Antes de otra C03 completa, una prueba Deno limitada en la red interna R19 debe hacer un
GET sintético a la ruta Auth del gateway con CA R19 y devolver únicamente código HTTP o
clasificación cerrada de DNS/connect/TLS. El gateway usa API key/JWT sintéticos; no se envía
correo ni se usan servicios operativos. Esto separa transporte TLS/DNS de la construcción
de petición `supabase-js` del Edge sin imprimir payloads. Si el transporte responde, revisar
la allowlist `createApiKeyOnlyFetch` y el método/path de la petición del mock, sin cambiar el
contrato del BFF ni flexibilizar Authorization.

## Gates

G07 sigue parcial; no se suma punto. Métricas sin cambio: tablero histórico G01–G10 **60%**;
cierre local G01–G09 **6/9 = 66.67%**. G08 y G09 pendientes; G10 remoto pendiente.
