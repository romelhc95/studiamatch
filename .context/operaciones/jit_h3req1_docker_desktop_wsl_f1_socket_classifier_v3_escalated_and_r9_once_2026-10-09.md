# JIT — reconciliación de socket EPERM fuera del sandbox + F1/r9 condicional

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-F1-SOCKET-CLASSIFIER-V3-ESCALATED-AND-R9-ONCE-20261009-V1`
Estado: preparado; requiere aprobación exacta; una sola invocación.
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Resultado V2 y predicado pendiente

El JIT socket classifier V2, SHA-256
`edecb9534187fc522cd7b97851fe1cfaa6ab0473e7d975585aeff3f12074476a`, se aprobó y ejecutó una
vez como `romel` en Ubuntu WSL interactiva, no-root. Su salida completa fue:

```text
phase=desktop-wsl-socket-path|error_code=OK
phase=desktop-wsl-socket-create|error_code=OK
phase=desktop-wsl-socket-connect|error_code=EPERM
exit=1
```

La ruta fijada existe como socket y el proceso pudo crear un socket; `connect()` devolvió
`EPERM`. La ejecución se hizo bajo el perfil sandbox normal del agente. Que el sandbox deniegue
el syscall es una hipótesis plausible, no una causa demostrada; el error también puede provenir
del host/WSL. No se alcanzaron HTTP/identidad, sintéticos Docker, F1 ni r9. No se emitió metadata
cruda ni hubo retry.

## Propósito y límite de la nueva invocación

La nueva ejecución solicita `sandbox_permissions=require_escalated` para ejecutar en el
contexto Ubuntu WSL sin el sandbox Codex. Esto no usa `sudo`, no cambia el usuario y no modifica
Docker. Si el auto-review del entorno deniega la escalación, no se ejecuta el runner.

El probe V3 reutiliza el PASS sintético in-memory previo del probe V1, fijado al SHA
`fb8ee1b3afb4496e4c00d827cec57793c449957193fae7c4924485db758dcbbf`; no repite esos casos
porque el input no cambió. Intenta una vez `lstat`, socket create/connect y un GET `/version`
con timeout de 5 s y cuerpo máximo 8192 bytes. Solo acepta status 200, JSON válido y `Os=linux`;
registra fases/códigos cerrados, sin metadata ni stderr. Después y solo tras identidad PASS,
ejecuta sintéticos Docker V3, lee F1 una vez y ejecuta r9 una vez si los controles F1 son
exactos. No llama `docker context inspect` ni `docker version`; no consulta `/proc`.

## Alcance de una invocación

Ejecutor: `romel`, Ubuntu WSL interactiva, TTY, sin `sudo`; proceso no-root bajo ejecución
escalada del sandbox Codex.

1. Verifica candidato, usuario, hashes y paquete r9. Rechaza overrides Docker y cualquier
   branch/HEAD distinto.
2. Reusa `socket-probe-synthetic-tests/OK` de la invocación V2 y verifica que el probe mantiene
   el SHA fijado exacto.
3. Diagnostica ruta del socket, creación, conexión y lectura/decodificación de identidad una
   vez cada una. No repite las consultas Docker CLI consumidas.
4. Solo con las fases de identidad exactas en `OK`, ejecuta los casos sintéticos V3 fijados en
   un contenedor efímero existente, `--pull=never`, sin red, rootfs read-only, UID 1001,
   capacidades removidas, límites de recursos y pruebas montadas read-only.
5. Solo con los sintéticos PASS, lee una vez el digest de la imagen F1 allowlisted y el
   contenedor F1 fijado.
6. Solo con identidad, sintéticos y controles F1 en `OK`, ejecuta el runner r9 fijado una vez.

Todo error o timeout consume la autorización y detiene fases dependientes; no hay retry. No
repite F2d ni las invocaciones consumidas y no reejecuta los comandos Docker CLI fallidos. El
runner r9 conserva su preflight `context inspect`, solo tras identidad, sintéticos y F1 PASS.
No hace pull, build, instalación, cambio de configuración, cleanup ni reparación Docker; no
accede ni modifica `studiamatch-dev`, producto, SQL, secretos, workflows, GitHub, Pages, ramas
o recursos externos. No autoriza copia completa, arranque Pages/workerd, C03
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
- Runner combinado V3: `4278709eda6a2b2a2640acbfa99c80a92cc6ff34bdd2df4ecebf40363e133eeb`.
- Runner F1 socket V3: `efd3c608ef08e82ec882c95bc4ec86814aa3900c819cf3f5b84d0d8b99228ddc`.
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

## Comando único — Ubuntu WSL interactiva, sandbox escalado, usuario no-root

```bash
(
set -u -o pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_f1_socket_classifier_v3_then_r9_once.sh'
readonly RUNNER_SHA256='4278709eda6a2b2a2640acbfa99c80a92cc6ff34bdd2df4ecebf40363e133eeb'
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
