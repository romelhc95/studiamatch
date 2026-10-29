# H3REQ1 C03 startup S8 — campo Miniflare incompatible demostrado

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Ensayo: S8, una ejecución en Docker Desktop/WSL sobre la imagen fijada, snapshot y dependencias S3 en solo lectura; red Docker interna exacta, sin egress, `.env*`, DB, Edge ni SQL.
- Exit: `1`. `healthz=NO-GO reason=runtime-not-ready attempts=3`; runtime exit `1`, señal `none`, `OOMKilled=false`.
- Evidencia S8: `.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s8.md`, SHA-256 `a1571a0f41d85f8bf26dc635a0f0e29ba67242b5f15831e816efdaee1f22a41a`.
- Contenedor preservado: `h3req1-c03-startup-runtime-20261010-s8`, ID `4baae5ba4df9742d039b3ade4a34e68282b4551721aca6406b1e3ce033dc74d5`, `exited|1|OOMKilled=false`, red interna S3 `ffc476c62637ef44316255202a6b08a170df514685bb6d16efcf7976fd79a13f`.
- Diagnóstico sanitizado: `runtime-stage=miniflare-constructor-validation`; `runtime-validation-issue=scope:shared|index:na|path:log|code:custom|keys:none`.

## Causa demostrada

El runtime construye Miniflare con `log: { level: 'error' }` en `tests/h3req1_c03_integrated_runtime.mjs`. La versión local fijada en el volumen S3 (Miniflare `4.20260730.0`) declara `log` como `z.instanceof(Log).optional()` (`node_modules/miniflare/dist/src/index.js`), y su API exporta `Log` y `LogLevel`. El objeto literal produce el issue Zod `custom` en la ruta compartida `log`. Esto demuestra una incompatibilidad del harness con el API de la versión fijada; no es fallo de Docker ni de dependencias.

## Corrección mínima y revalidación pendiente

Cambiar únicamente el valor a `new Log(LogLevel.ERROR)` e importar esas exportaciones junto a `Miniflare`. Después: validar la opción contra el paquete fijado, renovar el snapshot completo y los pins transitivos afectados, ejecutar Pages/workerd hasta healthz, y solo con PASS iniciar G07 integrado. No se ejecutó Edge, PostgREST ni PG17 integrado en S8.
