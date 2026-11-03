# H3REQ1 — classifier V2 detenido en pruebas sintéticas

Fecha: 2026-10-09. Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`,
rama `feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.
WIP al corte: 230 entradas en este checkout y 78 en el checkout original, preservadas.

## Autorización y resultado de una sola invocación

El usuario aprobó `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-AND-R9-ONCE-20261008-V1`,
SHA-256 `c2f9414cea67402af76727b3c240982d1c264252569ab94aea9dedc47c687a66`. Los hashes del
paquete, runner combinado, runner diagnóstico, helper V2 y archivo de pruebas coincidieron con
los pins antes de ejecutar. Ejecutor: `romel`, Ubuntu WSL2, terminal con TTY, sin sudo.

Resultado capturado únicamente como fases sanitizadas:

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=classifier-synthetic-tests|error_code=SYNTHETIC_TESTS_FAILED
```

El proceso del runner terminó con **exit 1**. El stop-on-failure funcionó: no hubo lectura de
imagen F1, inspect de contenedor F1 ni ejecución de r9. No se repitió la invocación. El runner
no conservó stdout/stderr de pytest; el exit individual del contenedor sintético y el nombre
exacto del test fallido no están disponibles. El contenedor de prueba era efímero (`--rm`), sin
red, rootfs de solo lectura y con el directorio de diagnóstico read-only. No se cambió ni
reconstruyó Docker.

## Hallazgo estático y límite

La revisión posterior encontró un defecto concreto en `test_v2_main_emits_only_sanitized_template_error`:
el test invoca `diagnostic_v2.main()` pero no sustituye `run_synthetic_tests()`. `main()` vuelve a
orquestar esa fase y ejecuta `docker run`; el propio fixture tampoco implementa
`helper.run_fixed_command`. Por ello el test intenta iniciar Docker anidado desde el contenedor
aislado de pytest, que no monta el socket, y su manejo de excepción emite el código genérico
`F1_CLASSIFICATION_FAILED`, contrario a la salida esperada. Se añade un no-op solo para la
orquestación en ese test unitario; el runner exterior sigue ejecutando los casos sintéticos en el
contenedor efímero fijado. Como se suprimió la salida de pytest, no se puede afirmar que este
fuera el único fallo observado en la ejecución.

No se demuestra defecto del clasificador de Docker ni de F1. La corrección limitada es aislar la
prueba unitaria de la orquestación Docker de `main()`, actualizar los SHA de ese test en los
runners y preparar una nueva invocación JIT. El JIT consumido no se repite; el nuevo permiso debe
autorizar la invocación corregida. Solo si las pruebas sintéticas pasan se podrá leer F1 una vez;
r9 sigue estrictamente condicionado a las fases y controles descritos en el nuevo paquete.

## Gates vigentes

G01=10/10 y G02=10/10; G03–G10 permanecen 0/10; total **20%**, delta cero. El parcial de
diagnóstico endpoint `OK` no cierra G04. No hay PASS de tooling ni GO_LOCAL_PR. Se conserva el
resultado previo de F1 `INSPECT_TEMPLATE_ERROR`; esta nueva invocación no volvió a leer F1.
