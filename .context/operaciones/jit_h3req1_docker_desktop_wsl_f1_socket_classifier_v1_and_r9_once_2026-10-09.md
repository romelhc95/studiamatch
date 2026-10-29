# JIT — clasificador de socket Docker Desktop WSL + F1/r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V1-AND-R9-ONCE-20261009-V1`
Estado: preparado; requiere aprobación exacta; una sola invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Causa concreta que se diagnostica

El JIT V3 aprobado, SHA-256
`1aa957146fbe98b6bec2e04c9d9cbc67414cbb4a9dbe3af138d53b592f8af178`, se ejecutó una vez y
terminó `phase=desktop-wsl-engine|error_code=DOCKER_ENGINE_UNAVAILABLE`, exit 1. El flujo alcanzó
la consulta de OS de servidor en el endpoint fijo `unix:///var/run/docker.sock`; el runner
convirtió cualquier salida no cero del CLI al código genérico. No distingue CLI, ruta, creación
del socket, conexión, respuesta ni decodificación. No se mostró ni guardó salida cruda. F1 y r9
no se alcanzaron. No se concluye que Docker Desktop esté caído ni defectuoso.

El diagnóstico nuevo no repite `docker context inspect` ni `docker version`. El helper nuevo
comprueba la ruta fija una vez, crea un socket, intenta una conexión y envía una sola solicitud HTTP
`GET /version` de solo lectura, con timeout de 5 s y cuerpo limitado a 8192 bytes. Valida solo
HTTP 200, JSON válido y `Os=linux`; conserva en memoria únicamente los bytes necesarios y emite
fases/códigos cerrados. No muestra ni persiste metadata, endpoint dinámico, stderr, secretos,
PID, UID o datos de proceso. No consulta `/proc`.

## Alcance de una invocación

Ejecutor: `romel`, terminal Ubuntu WSL interactiva, TTY, sin `sudo`.

1. Verifica candidato, usuario, hashes y paquete r9. Rechaza overrides Docker y cualquier
   branch/HEAD distinto.
2. Ejecuta doce aserciones sintéticas in-memory para errno de socket, fases create/connect,
   HTTP, tamaño, JSON, identidad y OS. Cualquier mismatch detiene el ciclo.
3. Diagnostica ruta del socket, creación, conexión y lectura/decodificación de identidad una
   vez cada una. No repite las consultas Docker CLI consumidas.
4. Solo con las fases de identidad exactas en `OK`, ejecuta los nueve casos sintéticos V3 en
   un contenedor efímero existente, `--pull=never`, sin red, rootfs read-only, UID 1001,
   capacidades removidas, límites de recursos y pruebas montadas read-only.
5. Solo con los sintéticos PASS, lee una vez el digest de la imagen F1 allowlisted y el
   contenedor F1 fijado.
6. Solo con identidad, sintéticos y controles F1 en `OK`, ejecuta el runner r9 fijado una vez.

Cualquier error o timeout consume la autorización e impide las fases dependientes; no hay
retry. No repite F2d ni las invocaciones consumidas; el diagnóstico no reejecuta las consultas
Docker CLI fallidas; el runner r9 conserva su preflight `context inspect` existente, solo tras
pasar identidad, pruebas y F1. No hace pull, build, instalación, cambio de configuración,
cleanup ni reparación Docker; no accede ni modifica `studiamatch-dev`, producto, SQL, secretos,
workflows, GitHub, Pages, ramas o recursos externos. No autoriza copia completa, arranque Pages/workerd, C03
integrado, UAT final, publicación, PR, merge, Settings remotos ni despliegue.

La lectura del socket y `GET /version` prueban respuesta Linux desde la ruta WSL allowlisted;
no acreditan PID, UID ni ejecutable del daemon. F1 es una política de lectura acotada, no una
atestación de proceso. El residual de identidad se reporta explícitamente.

## Resultado exacto requerido

```text
phase=socket-probe-synthetic-tests|error_code=OK
phase=desktop-wsl-socket-path|error_code=OK
phase=desktop-wsl-socket-create|error_code=OK
phase=desktop-wsl-socket-connect|error_code=OK
phase=desktop-wsl-engine-response-read|error_code=OK
phase=desktop-wsl-engine-identity|error_code=OK
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=classifier-synthetic-image-read|error_code=OK
phase=classifier-synthetic-tests|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
phase=r9|error_code=OK
```

Una salida parcial/fallida se comparte como fases y códigos permitidos, además del exit. No
copiar stderr, metadata ni scrollback crudo.

## Pines

- Este JIT: SHA-256 a verificar antes de solicitar/aplicar aprobación.
- Runner combinado: `546946238013267a1ce8f74ddda39f3c74336d3dbf2b1040ce185e751455c0a5`.
- Runner F1 socket: `ae69a8f221026d518dfa96205baf09208eaa919f7f5065875dbcef49a8dee72a`.
- Socket probe y pruebas sintéticas: `fb8ee1b3afb4496e4c00d827cec57793c449957193fae7c4924485db758dcbbf`.
- Clasificador V3 reutilizado: `fd3053f1781807de8633f56e3f6e08fb2bc42c79617f2fc0bb9522725eea7793`.
- Helper V2 fijado: `5ae493c50559b588ac9e40f49f54376da82c50af73b1bacf2e4133611136c90f`.
- Pruebas/runner sintético fijados: `4c58403f07649ea6cd195fa1e967699ff6f481966391022abc0bc4ec896393bd` y
  `89782f58c558535beb0891592cd7981bd7fa848334831fdc605e2616b0920d04`.
- Runner r9: `2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97`.
- Manifiestos r9/tools: `b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866` y
  `4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa`.

Los runners revalidan sus pines antes de cada fase. No ejecutar si algún pin, rama o HEAD no
coincide exactamente.

## Comando único — Ubuntu WSL interactiva

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_socket_classifier_v1_then_r9_once.sh'
readonly RUNNER_SHA256='546946238013267a1ce8f74ddda39f3c74336d3dbf2b1040ce185e751455c0a5'
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
IFS= read -r -p 'Copia solo fases/códigos sanitizados y exit; presiona Enter para cerrar: ' _ || true
exit "$runner_status"
)
```

La autorización cubre una ejecución exacta. No modificar el bloque, no reintentar y no
continuar tras FAIL.
