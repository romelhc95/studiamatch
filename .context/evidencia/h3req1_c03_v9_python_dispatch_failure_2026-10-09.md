# Resultado de despacho incorrecto de V9

Fecha: 2026-10-09. Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado

El usuario aprobó una invocación del JIT V9
`H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-IMAGE-READ-CLASSIFIER-V9-ONCE-20261009-V1`, SHA-256
`f2d19ea84397c66ab6ba2755e38b840448a8f40def796ac7895904029805d86c`. La llamada de Codex
terminó exit 1, sin stdout ni fases sanitizadas. El comando de despacho pasó el archivo
`.sh` del wrapper a `/usr/bin/python3`; el JIT fijado especifica `/bin/bash`. Resultado local
normalizado: `phase=jit-dispatch|error_code=INTERPRETER_MISMATCH`.

El wrapper fijado no llegó a ejecutarse: el intérprete recibió el script Bash como fuente
Python y su stderr se descartó. Por tanto, el wrapper no lanzó `docker image inspect`, no creó
contenedores temporales y no leyó F1. Tampoco se alcanzaron pruebas, probes, r9, `studiamatch-dev`,
pull/build/install ni cambios de configuración Docker. No se infiere ninguna causa del Engine.

## Permiso y corrección

La aprobación de una sola invocación queda consumida por el fallo de despacho; no se reutiliza.
El paquete V9 fuente y sus pines no cambian. Se preparó una nueva solicitud agrupada que invoca
el mismo wrapper con Bash y valida los hashes del JIT anterior y del wrapper antes de arrancar:
[JIT de despacho Bash corregido](../operaciones/jit_h3req1_docker_desktop_wsl_f1_image_read_classifier_v9_bash_dispatch_once_2026-10-09.md).
SHA-256 `a1b28cb9b3a2bc40bc9d4150dc2ffd8d90371e78672920ba75028c064abf8c43`. La revisión
independiente read-only confirmó el intérprete `/bin/bash`, los hashes fijados y el alcance,
sin hallazgos; no ejecutó Python, pytest ni Docker. El comando pasó `bash -n` y la documentación
`git diff --check`. Requiere una autorización nueva antes de cualquier llamada Docker.

G01=10/10, G02=10/10, G03–G10=0/10; total 20%, delta cero. El intento no acredita tests ni
cierra gates. No hay `GO_LOCAL_PR` ni `GO_DEVELOPMENT_REAL`.
