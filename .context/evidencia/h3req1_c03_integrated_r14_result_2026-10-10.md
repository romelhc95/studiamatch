# G07 R14 — resultado runtime y causa observada

## Identidad y exits

- Candidato: `feat/h3req1-sync-20261002` @ `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto: 65/65; SHA-256 `2d7a88458de45f70941c256263c51118eb5e02fc71163324c987603e6e05e8a0`.
- Invocación R14: timeout externo 1800 s; exit final 1.
- Fase: `real-edge-invite-held-after-reservation` (el nombre es histórico; el login precede a la reserva y no se inició una invitación).
- Resultado del control: `step=/control/login`, `type=TypeError`, respuesta 500; el runtime no emitió un código HTTP del BFF.
- Log sanitizado: [R14](h3req1_c03_integrated_run_2026-10-10_r14.log), SHA-256 `b1adfb4cc9edb32f3adebc99508cddfa432d2ba7e788b1154c82e51a5f36923e`.

## Fases que sí pasaron

Docker Desktop esperado, rama/HEAD y manifiesto pasaron. Snapshot integrado y hashes de dependencias pasaron. PostgreSQL 17.11 inició; bootstrap H2-Pro→H3, esquema de cuotas/dispatcher y fixture de in-flight/editorial dieron exit 0. PostgREST readiness pasó y Edge activo inició. El login falló antes de reserva, por lo que ninguna aserción posterior de C03 queda acreditada.

El failure-stop detuvo por ID/labels del nonce R14 los cuatro servicios runtime, Edge, PostgREST y PG17; sus exits posteriores 143/255/0 son efecto del stop y no causa. El log y los recursos R14 quedan preservados. No se ejecutó cleanup de recursos del ensayo fallido.

## Diagnóstico reproducible en fixture Miniflare aislado

Se creó un Worker sintético sin bindings ni servicios, en contenedor Node fijado, red `none`, rootfs read-only y cache Miniflare de solo lectura. Se reprodujeron los tres casos relevantes:

- El `Request` global de Node entregado a `worker.fetch(request)` termina en `TypeError` antes de una respuesta. R14 lo había construido con ese constructor global.
- El `undici.Request` compatible con la dependencia fijada de Miniflare se acepta, pero un `Origin` con hostname `admin.local.test` recibe `Invalid Origin header` cuando no hay ruta Miniflare para ese host.
- Con `routes: ['admin.local.test/*']` y el `Request` de Undici, el Worker devuelve 200 y observa URL y Origin iguales (`https://admin.local.test/api/admin/auth/login`) y `Sec-Fetch-Site: same-origin`.

Esto demuestra que el adaptador de prueba R14 usó una clase Request incompatible con Miniflare y que el host del BFF requiere una ruta explícita en la simulación local. No es un defecto del BFF, Docker, Auth ni de los cuatro criterios cliente. No se determina retrospectivamente que R13 tuviera ambas causas: R13 queda con su 403 sanitizado; el fixture ahora demuestra que la ruta faltaba en la configuración de prueba.

Evidencia del probe sintético: [Miniflare request compatibility](h3req1_c03_miniflare_request_compatibility_2026-10-10.txt).

## Siguiente acción

Corregir únicamente el harness: usar `Request` del Undici que Miniflare instala y declarar la ruta local `admin.local.test/*` en las dos configuraciones Pages. Añadir pruebas de contrato para ambos predicados, conservar R14 y validar un nuevo drill con recursos R15 únicos. El gate G07 sigue parcial hasta el flujo integrado completo y recovery smoke con exit 0.
