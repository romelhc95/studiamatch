# G06 Pages/workerd S13 — captura sanitaria del import faltante

Fecha: 2026-10-10. Candidato: `feat/h3req1-sync-20261002` /
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Estado del gate y resultado S12

G06 sigue pendiente; S12 consumió su única ejecución y terminó exit 1 en
`one-shot-pages-workerd-runtime-diagnostic`. Evidencia:
[`S12`](h3req1_c03_startup_smoke_2026-10-10_s12_diagnostic.md), runner SHA
`34fe573e3d6b2dcc5072317a8f0cdb8ee40a2332d3ee7e44dd30765a633ca8f6`, sidecar
SHA `fbfbed931f0253a1a7165419bc9ff3de18e0fad79eb942a2a38d5a2592c5dfba`.
El error sanitario fue clase `ERROR`, código `ERR_MODULE_NOT_FOUND`; `healthz`
no estuvo listo tras 2 consultas, el proceso salió 1, `OOMKilled=false`, la red
internal quedó con 0 endpoints. El contenedor fallido S12 se preserva por ID
`09de091c56585687a0dd3166742f37cb80c6a45b116e6a817547a227ccbd5810`.

El código no identifica todavía el módulo exacto. Los checks de lectura en
contenedores `network none` confirmaron que `miniflare`, `undici`, `esbuild` y
`workerd` cargan desde los volúmenes S11; los dos bundles Pages/cuota terminan
sin imports externos. Esto acota el error a una resolución posterior del runtime,
pero no demuestra una dependencia faltante ni justifica reinstalar.

## Corrección diagnóstica acotada

Se añadió clasificación de módulo faltante en el preload y probe. El clasificador
solo emite un ID ordinal derivado de los nombres de paquete presentes en los dos
lockfiles montados read-only, más un origen cerrado (`tools`, `web-deps`, rutas
de candidato u `other`). No serializa `message`, stack, URL, ruta absoluta ni el
specifier libre. El filtro de salida acepta únicamente IDs `pNNNNNN` y categorías
cerradas. El runtime funcional, snapshot S16, dependencias instaladas y contratos
H3 no cambian.

Evidencia sintética actual en imagen Node fijada, red none y mounts read-only:

```text
phase=runtime-preload-diagnostic-synthetic|error_code=PASS
phase=runtime-diagnostic-synthetic|error_code=PASS
phase=runtime-output-filter-synthetic|error_code=PASS
```

La recuperación del runner se extrajo para un self-test aislado y pasó cinco
casos: inspect inaccesible, ownership ajeno, runtime ya detenido, stop seguido
de verificación exitosa y stop no confirmado. El test comprueba que solo se
emita stop para ID/labels propios y que los fallos de verificación queden como
`runtime-stop=not-confirmed` con estado desconocido.

También pasan `node --check`, `bash -n`, ShellCheck 0.11.0 y `git diff --check`
para los helpers, runner, self-test y filtro. Un caso negativo demuestra que un
package private/token no aparece en el evento; valores fuera del contrato son
descartados por el filtro. La revisión independiente encontró etiquetas S12
obsoletas y un stop de emergencia que se ocultaba; ambos se corrigieron y el
runner solo registra los estados cerrados `completed`, `not-required` o
`not-confirmed`. La revisión independiente confirmó PASS estático del runner
final SHA `6b9527169e1c4c9abbefe37a10175e87dcfc61d99fa68df399d7baddc2b33dff`,
del sidecar `0591fc3e7e98aecc5b69534286b97f56d9548bfa9b8d3d081990d8ad84278611`
y del self-test de cinco casos. El sidecar incluye el self-test pero excluye el
runner, sin hash circular; `sha256sum -c` verificó los 12 inputs.

## Diagnósticos auxiliares y límites

- Un lector de paquete intentó abrir `workerd/index.js` (exit 1); el manifiesto
  real define `lib/main.js`, y la lectura corregida identificó el ejecutable
  `bin/workerd` sin inspeccionar el entorno.
- La primera construcción del probe de esbuild tuvo un error de quoting; la
  corrección expuso después `name` como opción no válida; al separar metadatos de
  opciones, el build exacto terminó PASS (Pages bundle 794727 bytes; cuota 6047,
  ambos sin imports externos). No es un fallo de producto.
- Una primera aserción sintética del filtro tuvo el orden esperado incorrecto;
  se corrigió la expectativa y el conjunto completo pasó.
- Un comando ShellCheck fue rechazado por digest de imagen mal formado (exit
  125 antes de crear contenedor); con el digest local fijado ejecutó exit 0.
- Una lectura de código que usó `rg` dentro de la imagen Node falló porque esa
  imagen no lo contiene; una extracción Node read-only reemplazó esa consulta.
- El primer despacho de ShellCheck pasó `/bin/shellcheck` como argumento pese a
  que la imagen ya lo usa como entrypoint. El contenedor `--rm` no persistió; el
  entrypoint se verificó con metadata acotada y el despacho corregido pasó.
- El self-test de recovery primero asumió que el path del checkout existía
  dentro del contenedor y después tenía una extracción de constantes que podía
  enmascarar fallo. Se cambió a recibir el path read-only montado y a validar
  cada pin antes de evaluar la función; los cinco casos ya pasan.

## Resultado ejecutado S13

S13 fija el runtime S12 fallido, sus labels/run ID, evidencia `ERR_MODULE_NOT_FOUND`,
snapshot S16 y volúmenes S11. Ejecuta un runtime Pages/workerd nuevo con timeout
180 s, 2 CPU/2 GiB, red internal, imagen digest fijada, source/deps read-only,
sin `.env*`, datos reales, PG/PostgREST/Edge/Auth, SQL ni egress. Cero retries.
Ante fallo conserva solo el nuevo contenedor de esta invocación; S12, S11 y S16
siguen preservados. El sidecar de 12 inputs SHA-256 es
`0591fc3e7e98aecc5b69534286b97f56d9548bfa9b8d3d081990d8ad84278611`; el
runner `tests/h3req1_c03_startup_runtime_diagnostic_s13.sh` SHA-256 es
`6b9527169e1c4c9abbefe37a10175e87dcfc61d99fa68df399d7baddc2b33dff`.

El comando S13 se ejecutó una vez, exit 1. El resultado sanitizado fue:
`runtime-error-code=ERR_MODULE_NOT_FOUND`,
`runtime-missing-module=unclassified|from=other`,
`healthz=NO-GO reason=runtime-not-ready attempts=2`,
`runtime-exit=code:1 signal:none`, `OOMKilled=false`; el filtro terminó exit 0.
El stop de recovery no era necesario porque el runtime ya estaba exited; se
preservó por ID exacto. Véase [resultado S13](h3req1_c03_startup_smoke_2026-10-10_s13_diagnostic.md).

No cambia el tablero: histórico G01–G10 50%; cierre local G01–G09 5/9 = 55.56%.
G07 espera healthz PASS. `studiamatch-dev` continúa healthy y separado. S14
prepara clasificación estructurada de la forma del import faltante; aún no
demuestra causa ni habilita G07. Véase [preparación S14](h3req1_c03_startup_s14_diagnostic_preparation_2026-10-10.md).
