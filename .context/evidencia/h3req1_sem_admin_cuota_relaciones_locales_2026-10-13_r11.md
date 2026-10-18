# Relación local de pruebas para cuota Admin — R11

> Corte candidato `feat/h3req1-sync-20261002`, HEAD base `4eb4d877a50b012bb630a129bd0c74482c33be9c` más WIP inventariado. Evidencia de relación fuente→caso, no nueva ejecución. No se consultaron servicios remotos.

## Componentes y contratos

- [`web/functions/_lib/admin-quota.ts`](../../web/functions/_lib/admin-quota.ts): `trustedQuotaIp` toma la identidad IP del request validado y `checkAdminQuota` deriva digests HMAC; remite `POST /check` al binding interno `ADMIN_QUOTA`. No envía IP ni cuenta en claro. Lo consume `web/functions/_lib/admin-bff.ts` en rutas de login, callback, password, RPC y MFA. Respuestas `429` llevan `Retry-After`; error interno/falta de binding cierra con `503`.
- [`workers/admin-quota/index.ts`](../../workers/admin-quota/index.ts): el Worker valida método, ruta y forma del payload, determina shard y envía a `AdminQuotaCounter`. El DO serializa updates de ventanas/ledger con storage transaccional y alarma de expiración; `wrangler.jsonc` declara el binding/clase, runtime y opciones locales. La ruta local no configura `workers_dev`, preview URL ni rutas públicas.
- La cuota SQL `admin_invitation_request_admit` tiene una tabla/propósito separados. `tests/sql/h3_admin_quota_harness.sql` es precondición de `h3_admin_rpc_signed_gateway_harness.sql`; no es evidencia del Worker Durable Object ni del binding de Pages.

## Relación test → contrato → resultado disponible

| Suite/caso | Contrato que inspecciona o afirma | Evidencia e input | Alcance del resultado |
|---|---|---|---|
| `tests/h3_admin_quota_uat.mjs` | Compila la fuente del cliente y Worker con TypeScript; prueba 25 requests concurrentes, 10 admisiones, bloqueo y `Retry-After`, persistencia al recrear la instancia del contador emulado, expiración por alarma, forma inválida y aislamiento sintético de digests/shard. Su storage es un `transaction()` fixture en memoria. | `.context/evidencia/h3req1_g08_final_2026-10-10_r2/quota-uat.out` y `h3req1_g08_app_regressions_inputs_r1.sha256`. El JSON observado dice `PASS`, `concurrentRequests=25`, `admitted=10`, `persistence=emulated`, `runtime=unit-intercepted`; el test/BFF/Worker actuales tienen los hashes del manifiesto. | Acredita ese test unit-intercepted y su contrato con storage emulado; no acredita el runtime Durable Object. |
| `tests/h3_admin_quota_runtime.mjs` | Compila `workers/admin-quota/index.ts`, lee `wrangler.jsonc`, comprueba que no hay rutas/preview públicos y configura Miniflare con SQLite Durable Object persistido; afirma concurrencia, reinicio/persistencia, otro shard y rechazos de input. | El SHA-256 actual del test coincide con `source-inputs-r6.sha256` y `source-inputs-r7.sha256`. En esos directorios no se encontró salida `*.out`, `*.log`, `*.txt` o `*.md` con resultado Miniflare/cuota runtime. | La relación test→DO y test→config queda documentada; no se afirma que el test Miniflare haya pasado. Ese runtime queda `NO-EJECUTADO` en la evidencia local encontrada. |
| `tests/h3_admin_quota_postgrest.mjs` | Con cliente SDK instalado simula el transporte HTTP PostgREST; afirma límite de 120 lecturas, propagación del rechazo MFA, `429` y `Retry-After`, y deniega al usuario autenticado la RPC service-only. | El SHA-256 actual del test coincide con manifests de inputs R6/R7. En esos directorios no se encontró resultado fechado para esta prueba en archivos `*.out`, `*.log`, `*.txt` o `*.md`. | El caso y su transporte están identificados; no se afirma ejecución de esta suite ni llamada a un PostgREST remoto. |
| H3-UAT-070 en G09 R135 | Flujo BFF integrado con requests sintéticos firmados: 3 viewports × 8 assertions, 30 writes rechazados antes de mutación y request 31 `429` con `Retry-After: 60`. | [Delta R135–R139](h3req1_g09_local_acceptance_delta_r135_r139_2026-10-11.md) identifica runner, entorno Pages/workerd mock y hashes del paquete de ese ensayo. | Valida el flujo BFF/mock descrito en ese informe; no sustituye la prueba Miniflare DO ni demuestra binding/deploy remoto. |

Los hashes fuente de R6/R7 identifican que el paquete incluyó esos bytes; por sí solos no demuestran ejecución. La salida `quota-uat.out` se atribuye solamente al test con el mismo resumen JSON y el manifiesto local adyacente. El límite de búsqueda sin resultado se restringe a los dos paquetes R6/R7 mencionados arriba; no demuestra que nunca existió otro output.

## Operación y mantenimiento

La ruta de cuota del BFF depende del binding `ADMIN_QUOTA`; el Worker/DO necesita la binding clase y el runtime configurados en `workers/admin-quota/wrangler.jsonc`. Los secretos HMAC son bindings server-side distintos; no se usa service role en el BFF. El DO conserva claves derivadas en estado operativo, no identidades originales. Fallos de config/storage deben mantener el cierre `503`; el cliente no reintenta una mutación por su cuenta.

Para cambiar categorías, ventanas, claves, shard o serialización, revisar en conjunto `admin-quota.ts`, `admin-bff.ts`, `workers/admin-quota/index.ts`, `wrangler.jsonc` y los tres tests UAT citados; actualizar los límites y ejemplos de [`admin_runtime.md`](../componentes/admin_runtime.md#cliente-de-cuota) y el registro por path. Ejecutar solo las suites Docker locales afectadas, con `H3_QUOTA_TOOLS` apuntando a las herramientas aisladas que documenta el test de runtime. No invocar Wrangler remoto ni inferir deploy a partir de configuración.

[Runtime Admin](../componentes/admin_runtime.md) · [Registro](../trazabilidad/registro_fuentes_componentes.md#runtime-admin) · [Índice](../indice.md)
