# JIT H3REQ1 C03 — V15 parser de fases corregido, invocación única

Fecha: 2026-10-09. Estado: listo para nueva aprobación humana; no ejecutar hasta aprobar este JIT.

## Por qué es una nueva invocación

La autorización V15 anterior, SHA `b5f98329415c613f5ab4c96b3d3721db97f56cd60749748eb7eadd56666efe4c`, ya se consumió. Reprodujo el baseline sintético y el helper emitió el subconjunto 1-minimal `{nano-cpus, mounts}`, pero el wrapper esperaba `f1-v15-reducer-tests` antes de las fases sintéticas anidadas y terminó exit 1 antes de F1/r9. La causa es el contrato de prefijo de salida; este paquete fija el parser V2 y no reutiliza esa aprobación.

## Alcance de una invocación

Ejecutor Codex en Ubuntu WSL interactiva como `romel`, no-root y sin `sudo`, sujeto a la revisión automática normal. Comando exacto:

```bash
/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 600s /bin/bash /home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_v15_minimal_subset_diagnostic_once.sh
```

El runner verifica rama/HEAD, hashes de helper/parser/evidencias previas y ausencia de overrides Docker. Ejecuta sintéticos y crea solo un contenedor temporal sintético con `--network=none`, rootfs read-only, usuario no-root, `cap-drop` y tmpfs; limita la reducción a 52 probes y 5 s por probe. El parser acepta como máximo 8192 bytes, solo fases/códigos sanitizados, orden anidado exacto, status helper 1, lista allowlisted, resumen único y la pasada final 1-minimal. El wrapper solo devuelve fases/códigos sintéticos: no consulta metadata del F1 real, no modifica `studiamatch-dev`, no ejecuta r9, no hace pull/build/install, no cambia configuración Docker y no reintenta. La limpieza del contenedor temporal falla cerrada.

No captura metadata cruda, secretos, Env, logs ni nombres aleatorios. Ante FAIL/timeout conserva solo la primera fase/código sanitizado disponible; la invocación se consume.

## Inputs fijados

- Wrapper: `01b0e62d0d80d0292b0ee032854340dbbe0158988b3395ae3704e48ba71cd6cb`
- Parser de salida V2: `d9e45441d96f811ae303d17f85a447bae555b7b1ad2fcd05f3dad9ed905c0f57`
- Helper V15: `05947152fcfb356c1ea8bc0a283eda3c3aad0c94f31e9844083fac2678a0f764`
- Rama/HEAD: `feat/h3req1-sync-20261002` / `4eb4d877a50b012bb630a129bd0c74482c33be9c`

La validación sintética local aprobó seis casos del parser, `bash -n` del wrapper y compilación Python en memoria. No es resultado Docker.

## Solicitud concreta

Aprobar una invocación del comando exacto anterior con estas rutas/hashes y solo el alcance indicado. No cubre F1/r9, integración, reconstrucción, CI remoto ni fases posteriores.
