# G07 — compatibilidad de R49 con el candidato actual

Fecha: 2026-10-10. Checkout candidato, rama y HEAD baseline coinciden con el
corte vigente. Esta comprobación es de hashes/alcance; no vuelve a ejecutar C03.

## Resultado histórico preservado

R49 terminó con exit 0 y `C03 integrated drill: PASS (local synthetic scope only; no Development GO)`.
Su log sanitizado SHA-256 es
`3a6cf426e8e6f72b2ac55f43ba28a3d5005a9e8f2c816c01bdc9af44d5f7d504`; el manifiesto
R49 archivado conserva SHA-256
`5238e20f4711ad033f0d8f3571f9445705c9a193f19905d866fc4ad694d0ac00` y 127 entradas.
El resultado prueba el alcance sintético de R49 para aquellos bytes, no el candidato
con los cambios BFF/runtime posteriores.

## Compatibilidad comprobada

`sha256sum -c tests/h3req1-c03-integrated-r49.sha256`: **125/127 PASS, 2 MISMATCH**.

| Input | Hash R49 | Hash actual | Impacto |
|---|---|---|---|
| `tests/h3req1_c03_integrated_runtime.mjs` | `5dbd35906e04acdc4d58db11940336fccc2128ee2edb38bd32197d15475ae75e` | `157d6fc3b103aa2ae3a7e5d5be8742989038207a0f0f1b652c971188bf249b89` | Fixture del runtime actualizado para `session_id` y el contrato de cookie ligada a sesión; requiere ejecutar el Pages/workerd integrado actual. |
| `web/functions/_lib/admin-bff.ts` | `829cd9cdce85f318800674949a7b6f93f64f8283d3c217f453ab3c75361827cf` | `0cf11ce7729dcd0f1a681c5faee81131456f2e1fb337c46611f76507a593dea7` | Cookie de actividad firmada con vínculo a sesión Auth y re-firma cuando cambia la sesión tras MFA; requiere renovar su recorrido integrado. |

Los 125 hashes coincidentes incluyen las migraciones C03, SQL de setup/aserciones,
Edge, PostgREST probes, locks y manifiestos auxiliares. El mismatch no prueba por sí
solo que el producto falle; sí impide reutilizar R49 para acreditar G07 del candidato
actual.

## Recursos y decisión

El log R49 confirma que sus contenedores y redes temporales se retiraron por IDs exactos.
El snapshot fuente R49, volumen TLS sintético y caches read-only quedaron preservados;
`studiamatch-dev` siguió healthy. R50 usa nombres nuevos sin colisiones observadas,
mantiene los mismos images digest-pinned y vuelve a comprobar cache/volúmenes antes de
crear recursos. El checkout original y servicios remotos no se tocaron.

Siguiente acción: validar y ejecutar R50 con manifiesto de 127 entradas basado en el
candidato actual. No se repite R49 ni se declara G07 completo hasta el resultado R50.
