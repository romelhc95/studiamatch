# H3REQ1 C03 startup S8 — paquete diagnóstico preparado

## Candidato y estado

- Checkout: `/home/romel/src/studiamatch-h3req1-sync-20261002`
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`
- WIP antes de añadir esta nota: 55 tracked modificados, 340 entradas untracked, 0 staged; se conserva íntegro.
- S7 ya ejecutado: exit 1, OOM false, `ERR_VALIDATION`, clase `MINIFLARECOREERROR`, healthz NO-GO. Evidencia vigente S7: SHA-256 `f947a115e9f269376bef4103dce53a4817ded48085e3df855de5ccd6bfcd12ac`; contenedor exacto preservado.

## Diagnóstico y alcance de S8

La inspección read-only del Miniflare fijado `4.20260730.0` demuestra que `ERR_VALIDATION` se crea en `validateOptions()` cuando una validación Zod falla al procesar las opciones de `new Miniflare()` (`index.js`, líneas 102631–102674). S7 no identificó el campo porque descartó el mensaje. El campo concreto aún no está demostrado.

S8 añade una captura de diagnóstico para una sola ejecución. El preload en el proceso hijo no escribe mensajes, valores, stack ni entorno: conserva solo código Miniflare y `cause.issues` acotados. El probe mapea ruta, código de validación y nombres de campos a allowlists finitas; el filtro de salida aplica otra comprobación cerrada. Sintéticos verifican valores y campos con forma de secreto. El runtime y el manifiesto fuente no cambiaron.

El runner reutiliza fuentes/dependencias S3 verificadas como mounts read-only y la red interna sin egress con ID `ffc476c62637ef44316255202a6b08a170df514685bb6d16efcf7976fd79a13f`. Monta únicamente el probe y preload S8 individualmente; no monta el checkout ni `.env*`. Una sola ejecución, timeout 180 s, 2 CPU/2 GiB, rootfs read-only, capabilities dropped, sin DB, PostgREST, Edge, SQL, Auth, correo ni remoto. El contenedor nuevo se conserva; no limpia ni modifica recursos históricos.

## Validación local del paquete S8

| Check | Resultado |
|---|---|
| SHA-256 de manifiesto, runner, probe, filtro, preload y fuente S3 | PASS; manifiesto `a52a4118346d54f6f9fdda110a696c95b4e923ab043eb25e3c60dc2b823a6493` |
| Bash syntax de runner/filtro en Docker aislado | PASS |
| Node syntax de probe/preload en Docker aislado | PASS |
| Sintéticos del output filter | PASS, salida cerrada `phase=runtime-output-filter-synthetic|error_code=PASS` |
| Sintéticos del probe | PASS, salida cerrada `phase=runtime-diagnostic-synthetic|error_code=PASS` |
| ShellCheck 0.11.0, severity warning | PASS en contenedor aislado de 512 MiB; exit 0, OOM false, network none, solo mounts read-only de runner/filtro |
| `git diff --check` | PASS |

Fallos del setup de ShellCheck conservados: una llamada duplicó el nombre del binario del entrypoint y trató `shellcheck` como archivo; otra ejecución con `--rm` terminó exit 137 sin salida ni metadata recuperable, por lo que su causa no se atribuye a OOM. La ejecución identificable posterior con 512 MiB pasó. El contenedor exacto exitoso es `h3req1-c03-startup-shellcheck-20261010-s8`, ID `f06140f208ed7a062f3b7c407c449c78d59393e4c00a4bb0b84ced331aa59a70`; evidencia guardada antes de su retirada selectiva por ID, sin volúmenes.

## Pins y estado de ejecución

- Runner SHA-256: `31dd06386736924792623a652f74eeeccd4799af017e9aa4d433d633651e81fc`
- Probe SHA-256: `160fd41a22f2cc856f8f4b579fb5b006b3ad461c21a73953a6b58be3b2a68131`
- Filtro SHA-256: `c41ff1d5a1f8fe70930101f747549df3dcfa83df93d58fb2945e682056fbbfd1`
- Preload SHA-256: `682b6b412f497e384ff543f73a8cff1390cfc2fc9a8e2e35893db5e6b1dbc0af`
- La revisión independiente y el intento runtime S8 están pendientes. No se declara G06 PASS ni se inicia G07.

Recuperación: continuar desde la revisión S8; si resulta limpia, ejecutar el comando fijado por el runner una vez. Ante fallo, conservar el contenedor/evidencia S8 y usar su fase/campo sanitario para una corrección mínima antes de la siguiente ejecución. G01–G05 permanecen completos; métricas continúan tablero G01–G10 50% y cierre local G01–G09 5/9 = 55.56%.
