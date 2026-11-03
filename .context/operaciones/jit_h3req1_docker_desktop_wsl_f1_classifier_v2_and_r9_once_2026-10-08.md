# JIT V2 — prueba sintética del clasificador, lectura F1 y r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-AND-R9-ONCE-20261008-V1`  
Estado: **preparado; requiere aprobación exacta; no ejecutado**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo y cambio revisable

La última invocación aprobada terminó con
`phase=f1-container-read|error_code=INSPECT_TEMPLATE_ERROR`. Su runner terminó exit 1; el
código numérico de `docker inspect` no se emitió. El template allowlisted no se cambia: el
error sanitizado no identifica token o campo.

El clasificador V1 mezclaba parseo y evaluación. El helper V2 prioriza el marcador `executing`
para evaluación, separa parseo conocido y conserva un código ambiguo cuando el texto no basta.
Docker CLI puede anteponer “Template parsing error” también a un error de evaluación; por eso
el marcador de ejecución tiene prioridad ([ejemplo en el repositorio oficial docker/cli](https://github.com/docker/cli/issues/3727)).
Se añadieron casos sintéticos con códigos cerrados y aserciones de que no se imprime metadata
cruda. Esos casos aún no fueron ejecutados.

## Alcance de una única invocación

`run_wsl_f1_classifier_v2_then_r9_once.sh` realiza en secuencia, con stop-on-failure:

1. Verifica el checkout, rama, HEAD, hashes fijados y que no haya overrides Docker.
2. Atestigua el endpoint Docker Desktop WSL y que el Engine reporta Linux.
3. Ejecuta los casos `v2` de `test_f1_read_failure_classification_once.py` en **un contenedor
   efímero** de la imagen ya fijada `sha256:29d8fff9a799aaacd45d771696f40762511d4c3a4c1ebfe536bd2a69a2f16be0`, con
   `--pull=never`, red desactivada, rootfs de solo lectura, usuario 1001, límites de recursos,
   `/tmp` temporal y solo el directorio de diagnóstico montado read-only. La salida de pytest
   se descarta; se emite únicamente fase/código.
4. Solo si las pruebas pasan, lee la imagen F1 allowlisted y ejecuta **una vez** el `docker
   inspect` del mismo ID y formato fijados. Los errores se traducen a códigos permitidos;
   stdout/stderr y metadata no se conservan ni muestran.
5. Solo si las cuatro fases exactas —endpoint, pruebas sintéticas, imagen F1 y contenedor F1—
   devuelven `OK` y los controles F1 coinciden con la allowlist, ejecuta una vez el paquete r9
   ya fijado. r9 conserva sus límites, manifiestos, herramientas e imagen existente; no descarga
   ni instala dependencias.

No ejecuta F2d, no consulta `/proc`, no reconstruye/descarga imágenes, no monta el socket
Docker en el contenedor de pruebas, no toca el contenedor `studiamatch-dev`, no crea recursos
persistentes y no modifica Docker, repositorio remoto, SQL, secretos, reglas, Pages o despliegues.
El contenedor sintético y el contenedor de r9 son efímeros y se retiran con `--rm`; no se toca
ningún recurso preexistente. No hay retry. Si falla una prueba, endpoint, lectura F1, control
F1, hash, timeout o r9, la invocación termina y no continúa a la fase posterior.

Esta solicitud no autoriza copia completa, arranque Pages/workerd, integración Edge/PG17/
PostgREST, C03 integrado ni aceptación final. Esos gates conservan su paquete y autorizaciones
propias. No reactiva la aprobación del JIT V1 consumido.

## Pines

- El SHA-256 de este documento se entrega en la solicitud de aprobación; no se embebe en el
  propio archivo.
- Runner combinado: `tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v2_then_r9_once.sh`,
  SHA-256 `385f94732d8f93420533284cd1f4ceee36d82b742ba7ab519c3af0749c6c88df`.
- Runner de diagnóstico: `run_wsl_f1_read_classification_v2_once.sh`, SHA-256
  `1fe0f175e6164e31e1562bac7c85604cc8e0711c7a2f47a6fdd476aa7f870a9b`.
- Helper V2: `f1_read_failure_classification_v2_once.py`, SHA-256
  `3b5f7c6dd00ba6b690fcaadbc0c018f7d2e0dc11079ac0991cd0ffd06926f706`.
- Pruebas sintéticas: `test_f1_read_failure_classification_once.py`, SHA-256
  `48b6944cb741115597319c7097890270f837eef4e3c9a043bd94f16d30f9bd2e`.
- El runner conserva los pins de Desktop helper `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb`,
  proyector F1 `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463`, y V1 classifier
  `b84e46250823a0a7f3c73bf0bbd3359147585dea7d1c4b8ef322d87a1c12d4fc`.
- r9: runner `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`, manifest
  `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`, tools manifest
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`. Los tres fueron
  verificados antes de preparar esta solicitud; el propio runner vuelve a validarlos.

## Comando único — Ubuntu WSL interactiva

Ejecutar una sola vez como `romel`, sin `sudo`, después de aprobar este JIT. El bloque verifica
el hash exacto del runner combinado, mantiene la terminal interactiva y hace pausa al final.

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v2_then_r9_once.sh'
readonly RUNNER_SHA256='385f94732d8f93420533284cd1f4ceee36d82b742ba7ab519c3af0749c6c88df'

if (( EUID == 0 )); then
  printf 'phase=jit-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -t 0 ]]; then
  printf 'phase=jit-preflight|error_code=INTERACTIVE_TTY_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=jit-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
if ! hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)"; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
fi
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=jit-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi

/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 300s /bin/bash "$RUNNER"
runner_status=$?
IFS= read -r -p 'Copia las fases sanitizadas y el resumen r9; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

Compartir solo las líneas `phase=…|error_code=…` del diagnóstico, el exit y resumen de r9.
No copiar metadata Docker, stderr crudo, valores de entorno ni secretos. Una salida de error
consume el JIT; no ejecutar el bloque otra vez.
