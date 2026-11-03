# JIT — diagnóstico por aserción V2, F1 y r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V3-MAIN-ASSERTION-AND-R9-ONCE-20261009-V1`  
Estado: preparado; requiere aprobación exacta; una sola invocación.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, `feat/h3req1-sync-20261002`, HEAD
`4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Motivo y resultado anterior

El JIT anterior `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-CLASSIFIER-V2-SYNTHETIC-DIAGNOSTIC-AND-R9-ONCE-20261009-V1`, SHA-256
`708cb4210fb59df7f85d1f69c83f22007304b99a6414496ea0c9268d8bb32d26`, fue aprobado y consumido
una vez. Salida: endpoint y digest de la imagen sintética `OK`; el caso `main()` falló con
`V2_MAIN_SANITIZATION_FAILED`, exit 1. No se leyó F1 y no se ejecutó r9. No se retuvo salida
cruda. La revisión del fixture mostró tres predicados distintos (exit code, líneas sanitizadas
y ausencia de un marcador sensible), pero la prueba no etiquetaba cuál discrepó.

Este paquete agrega etiquetas constantes en la prueba y un clasificador que traduce solo esas
etiquetas a códigos cerrados. La salida de pytest/traceback permanece solo en memoria del
contenedor efímero; no se imprime ni persiste. Un mensaje desconocido continúa como el código
genérico `V2_MAIN_SANITIZATION_FAILED`.

## Alcance de la única invocación

Ejecutor: `romel`, en una terminal Ubuntu WSL interactiva con TTY, sin `sudo`.

1. Comprueba rama/HEAD, hashes y paquete r9 fijados, y rechaza overrides Docker.
2. Atestigua el endpoint Desktop WSL y lee solo el digest de la imagen sintética fijada; no
   descarga imágenes.
3. Corre nueve casos sintéticos V2 en un contenedor efímero `--pull=never`, sin red, rootfs
   read-only, UID 1001, capacidades removidas, límites de recursos y el directorio de pruebas
   montado read-only. Si falla `main()`, los códigos posibles discriminan exit, texto
   sanitizado, presencia de marcador sensible o fallo no clasificado.
4. Solo con las fases anteriores exactas en `OK`, lee una vez la imagen F1 allowlisted y el
   contenedor F1 fijado.
5. Solo si pasan los controles F1, verifica y ejecuta r9 una vez.

Cualquier error consume la invocación y detiene las etapas posteriores. No hay retry. No repite
F2d ni otro JIT consumido; no consulta `/proc`, no instala/reconstruye/configura Docker, no
hace pull, no accede ni modifica `studiamatch-dev`, no cambia producto, SQL, secretos, workflows,
Settings GitHub/Pages, ramas, ni despliega. No autoriza copia completa, Pages/workerd, C03
integrado, UAT final, publicación, PR, merge, settings remotos ni despliegue de producto.

El reporte anterior de `studiamatch-dev` sobre manifests sigue separado: este JIT no lo consulta
ni lo repara.

## Fases esperadas

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
phase=r9|error_code=OK
```

Si un predicado del caso `main()` falla, la salida final de fase puede informar uno de estos
códigos, sin revelar detalles: `V2_MAIN_EXIT_ASSERT_FAILED`,
`V2_MAIN_OUTPUT_ASSERT_FAILED`, `V2_MAIN_SECRET_ASSERT_FAILED` o
`V2_MAIN_SANITIZATION_FAILED`. Framework, colección y otros casos conservan códigos cerrados
del runner. Si hay una falla, compartir solo fase, código sanitizado y exit.

## Pines

- Este documento: SHA-256 comunicado fuera del archivo para la aprobación.
- Runner combinado: `09755cd55d874bbae2b07afeaead9747abbb86f6d6126f3bee3ca71c9c9147c7`.
- Wrapper diagnóstico V3: `fd3053f1781807de8633f56e3f6e08fb2bc42c79617f2fc0bb9522725eea7793`.
- Runner sintético V3: `89782f58c558535beb0891592cd7981bd7fa848334831fdc605e2616b0920d04`.
- Tests sintéticos: `4c58403f07649ea6cd195fa1e967699ff6f481966391022abc0bc4ec896393bd`.
- Helper base V2 fijado: `5ae493c50559b588ac9e40f49f54376da82c50af73b1bacf2e4133611136c90f`.
- Runner r9: `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`.
- Manifiesto r9: `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866`.
- Manifiesto tools: `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

Todos los runners vuelven a comprobar los pines antes de su etapa. No ejecutar si algún pin,
rama o HEAD no coincide exactamente.

## Comando único — Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_classifier_v3_assertions_then_r9_once.sh'
readonly RUNNER_SHA256='09755cd55d874bbae2b07afeaead9747abbb86f6d6126f3bee3ca71c9c9147c7'

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
IFS= read -r -p 'Copia solo las fases/códigos sanitizados y el exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

Una vez aprobado, ejecutar exactamente una vez. La autorización se consume aunque falle un
preflight. No modificar el bloque ni reintentar.
