# H3REQ1 G06 S9 — primer preflight detenido antes de Docker

Fecha: 2026-10-10. Candidato: rama `feat/h3req1-sync-20261002`, HEAD baseline
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado observado

El comando S9 con runner SHA-256
`421160aa131ee0ad8c73c92fc5c12820691f8d70c5eeff7bdc0fde4a40bd0259` y manifiesto SHA-256
`0676ae6c1454078f89ddedaaa53f4f6aafb694f33ef307b650d29d29de370707` terminó `exit=1`,
`phase=preflight`, `NO-GO: S3 inputs differ from the preserved manifest`. `sha256sum -c`
mostró una sola discrepancia: `tests/h3req1_c03_integrated_runtime.mjs` en el manifiesto
histórico S3.

No se consultó Docker ni se creó, arrancó, detuvo o limpió recurso alguno. El archivo de
resultado de runtime S9 no se creó. Este es un fallo de compatibilidad del preflight, no un
resultado de Pages/workerd ni de `healthz`.

## Causa demostrada y corrección

El manifiesto S3 preserva el hash V3 `7a16c11471fce2f7e9a09e5365abe00e3482fcd43d5bd3bbfe282252dc9b920a`.
La fuente actual V4 fija `17ddfa989a1f3322fa1812bb4fefbe83161d5a82d289ae170eb6b31ac7a8ec40`.
La comparación V3/V4 demuestra que es la única diferencia entre las 13 rutas; los cuatro
`package.json`/`package-lock.json` de bootstrap y Pages conservan los mismos hashes.

La primera corrección ajustó únicamente el preflight S9 para validar el delta V3→V4. La siguiente
ejecución de S9, con runner SHA-256 `a3767e62dcf35a1cf4d8bc72fc52141a3d116172b9fb5ba9c43474766be18739`
y manifiesto SHA-256 `7faee4ce38d14baf8929b87bdd143d20302ae5745a1d25b17f00eef22669cfa8`, se detuvo
también en `phase=preflight`, exit 1: el manifiesto S4 conservaba la misma fila V3. Una lectura
read-only de S3/S4/S5 mostró que cada manifiesto histórico fija ese runtime V3 una vez, mientras
que todas las demás entradas coinciden; S6/S7 verifican íntegramente sin delta.

La corrección actual aplica el mismo chequeo cerrado a los manifiestos S3/S4/S5: la fila antigua
de runtime debe ser única y corresponder al hash V3; el resto de sus entradas se verifica con
`sha256sum -c`. Además, el source-set V3/V4 exige las mismas 13 rutas, el único delta de runtime y
hashes iguales de los cuatro manifests de dependencias. S6/S7 conservan su verificación completa.
El snapshot S12 V4 y sus controles no se modifican. Ninguna de las dos ejecuciones llegó a Docker.

## Validación posterior a la corrección

- `bash -n` del runner S9: PASS.
- `git diff --check`: PASS.
- ShellCheck 0.11.0, contenedor efímero aislado con 512 MiB: PASS, exit 0.
- Sidecar S9 actualizado: todos sus pins verifican.
- Prueba read-only del manifiesto histórico: la fila V3 se conserva y todas las entradas
  restantes coinciden con sus fuentes actuales.
- Manifiestos históricos S3/S4/S5: fuera de su única fila runtime V3, todas las entradas pasan;
  manifiestos S6/S7 pasan completos.
- Revisión independiente del delta vigente S3/S4/S5: pendiente al corte de este registro.

G05 permanece PASS por S12; G06 sigue pendiente hasta un arranque real y healthz. G07 no se
inicia antes de ese PASS. No hubo reintentos automáticos; cualquier nueva ejecución es una
revalidación posterior a la corrección registrada.
