# G07 R16 — observar respuesta temprana del flujo de invitación

## Tareas y gates

1. Confirmar R15 login PASS y causa del timeout como falta de observación del runner: PASS.
2. Añadir clasificación cerrada del resultado temprano: implementado.
3. Validar helper, runtime, runner y manifest: PASS 18/18; ShellCheck/Bash; 65/65.
4. Ejecutar C03 integrado desde snapshot y healthz hasta reserva/hold: pendiente.
5. Solo si la reserva y hold pasan: suspensión, denegaciones, liberación in-flight, datos/auditoría/publicación/admin, resume, recuperación y smoke final.

## Ficha de impacto

- Componente: orquestación de la espera de Auth en el driver integrado R16.
- Consumidores: test local Pages/workerd → BFF → Edge → PostgREST/PG17 y runner R16.
- Contratos preservados: el evento de Auth es condición necesaria, el early response es FAIL, no hay retry; status/códigos son allowlisted y no se emiten body/mensaje/cookies/tokens. No cambia el producto.
- Evidencia preservada: R14/R15 logs, source snapshots R14/R15 y manifests históricos; R15 tuvo login PASS, sin hold/reservation acreditados.
- A renovar: G07 integrado y asserts posteriores; no se repiten G01, G03–G06 ni SQL completo fuera del fixture que cada drill necesariamente recrea.
- Recuperación: resources propios etiquetados R16, redes internas, PGDATA tmpfs, cache read-only. Failure-stop por IDs del nonce, conservar logs/volúmenes; sin egress ni `.env*`.

## Identidad y ejecución prevista

- Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, `feat/h3req1-sync-20261002`, baseline `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
- Manifiesto `tests/h3req1-c03-integrated.sha256`: SHA-256 `186862f80907e1e668b258d9c3ab7058d0360476be8b58f491288e501a324dfc`, 65 entradas.
- Runner `tests/h3req1_c03_integrated_drill_r16.sh`: SHA-256 `4522cf3c9c92353cce7095577e5849abe386ed98584b02cf044ff40cd26daf85`.
- Runtime `tests/h3req1_c03_integrated_runtime.mjs`: SHA-256 `828b93c2d9774884cd3cfa710b891bb84b8a85ac123445383fac30733a12ca38`.
- Clasificador `tests/h3req1_c03_login_result.mjs`: SHA-256 `14a69f7cc19197057c29caf8aabdf3117bf1387b616bf591594820b6cecad6b6`.
- Contratos: `tests/h3req1_c03_integrated_drill_r16_contract.test.mjs`, SHA-256 `a12ccde71582b48041f3298f3f98532ce88298e87cc0a56caeccd456998d5ae3`, 18/18.
- Timeout externo 1800 s, helpers Docker acotados, images local/pinned `--pull=never`, sin retry.

El resultado de R15 y su hash se conservan en [R15 result](h3req1_c03_integrated_r15_result_2026-10-10.md). La estática R16 se detalla en [R16 static](h3req1_c03_integrated_r16_static_validation_2026-10-10.md).
