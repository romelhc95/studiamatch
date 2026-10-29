# JIT — diagnóstico peer por subpasos y lectura F1 condicionada

ID: `H3REQ1-C03-PEER-SUBSTEP-DIAGNOSTIC-F1-READ-ONCE-20261008-V1`  
Estado: **SOLICITUD PREPARADA; requiere aprobación nueva; NO EJECUTADA**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Objetivo y autorización solicitada

Una sola invocación, sin retry, del runner Linux acotado que:

1. Compruebe que corre como root efectivo en el checkout/branch/HEAD fijados.
2. Resuelva el contexto local y distinga conexión, lectura/decodificación de `SO_PEERCRED`,
   cada lectura de metadata `/proc` y cada revalidación del socket. Cada fallo termina el
   flujo e imprime solo `phase=<fase>|error_code=<código>`.
3. Solo después de `phase=peer-identity-verified|error_code=OK`, lea la configuración de
   volúmenes de la imagen fijada y los campos allowlisted del ID F1 exacto. Si identidad
   falla, no se llama la Docker API ni se lee F1.

La aprobación de este ID/SHA autorizaría **una única ejecución** del comando del host
administrativo descrito abajo y el alcance F1 condicional aquí fijado. Reconoce los dos
residuales MEDIUM ya aceptados en el alcance A: el CLI Docker puede procesar transitoriamente
el objeto inspect completo antes de aplicar el formato; y el mismo usuario local puede operar
Docker por fuera del runner/JIT. Owner: Romel. Vencimiento: después de esta invocación o al
cancelarla. La aceptación no permite ampliar los recursos/comandos ni ejecutar r9.

## Reconciliación de autorizaciones

- La autorización consolidada `H3REQ1-CLOSE-LOCAL-ITERATIVE-20261008-V1`, SHA-256
  `4b2649342395f8bb14fb43958d660d3588f1f6ca55bce4a6516858b395cfb4f8`, conserva el objetivo
  A y su lectura F1 allowlisted condicionada. El usuario aceptó allí los dos residuales MEDIUM.
- El diagnóstico `H3REQ1-C03-PEER-PHASE-DIAGNOSTIC-ONCE-20261008-V1`, SHA-256
  `70764727e392ebb612ca44d9ffadc0bec4b1bb2ef38158d20489b99200c396df`, ya se ejecutó una vez
  y terminó `phase=peer-identity|error_code=EACCES`. Está consumido; no se repite.
- F2d y la creación/arranque F1 también están consumidos. No se reusan sus JITs. La propuesta
  F2 de lectura de metadata F1 del 2026-10-07 quedó NO aprobada y no se invoca; esta solicitud
  concreta la lectura F1 incluida por el alcance A vigente.
- El paquete, comandos y pins aquí fijados requieren la aprobación fresca de este ID/SHA.
  Una aprobación no significa que `sudo`, el UID root ni el host correcto estén disponibles.

## Ejecutor requerido y comando único

La llamada elevada de Codex anterior no acreditó permisos de lectura y el runner exige
`euid=0`. `require_escalated` solo controla el sandbox del entorno; **no garantiza** UID 0 del
host. Para evitar gastar la invocación en un preflight sin privilegios, abre una terminal Linux
en el host Docker correcto como administrador (`sudo -i` si hace falta). Tras aprobar este JIT,
pega el siguiente bloque una sola vez. El bloque valida el SHA-256 del runner antes de la única
invocación y no imprime hash, rutas ni salida cruda:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_host_admin_once.sh'
readonly RUNNER_SHA256='01222bf1c142651e267253313aa6a9d555d69699bda3f025e94b1e307ead8cb6'
if (( EUID != 0 )); then
  printf 'phase=host-admin-preflight|error_code=ROOT_REQUIRED\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=host-admin-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=host-admin-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=host-admin-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /usr/bin/timeout --foreground --signal=TERM --kill-after=1s 60s \
  /bin/bash "$RUNNER" 2>/dev/null
```

El runner no se autoeleva. Si no hay root efectivo o faltan herramientas del bloque, este
devuelve `phase=host-admin-preflight` con un código sanitizado y termina antes de invocar el
runner. El runner también valida UID efectivo, checkout, branch, HEAD y pin del auxiliar antes
de leer contexto, socket, peer o F1. Cualquier resultado consume la invocación; no se reintenta.
Debe ejecutarse en el host Linux que sirve el socket y el `/proc` del daemon, no dentro del
contenedor de desarrollo.
El preflight valida root efectivo, ruta de checkout, branch, HEAD y hash del auxiliar; el
auxiliar vuelve a validar checkout/branch/HEAD y el UID efectivo. No se usa `os.access()` como
sustituto de permisos reales: las operaciones `open/readlink/stat` que se reportan son las
lecturas reales acotadas. Las consultas Git como root pasan el checkout propiedad de `romel`
mediante `git -c safe.directory=<checkout>` en cada invocación; no escriben configuración
global/local ni desactivan la protección de ownership.

| Archivo fijado | SHA-256 |
|---|---|
| `tests/h3req1_docker_peer_substep_diag/diagnostic_once.py` | `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463` |
| `tests/h3req1_docker_peer_substep_diag/test_diagnostic_once.py` | `b4c68a3fa9ed2cfe09dc9e6b036a7db9ecec85b55e2dd63625cefb5486e46d81` |
| `tests/h3req1_docker_peer_substep_diag/run_host_admin_once.sh` | `01222bf1c142651e267253313aa6a9d555d69699bda3f025e94b1e307ead8cb6` |

No se debe ejecutar antes de que el humano apruebe este ID y el SHA íntegro de esta solicitud.
La respuesta de aprobación se registra una vez para el objetivo y runner completos; no se pide
aprobación individual por archivo/campo/hash.

## Fases y lecturas del diagnóstico

Las fallas se reducen a una fase fija y un nombre errno (`EACCES`, `ENOENT`, etc.) o código
constante. No se imprime ni persiste ruta/endpoint, PID, UID/GID, target del ejecutable, bytes
de `SO_PEERCRED`, contenido `/proc`, estado/configuración observada de F1, valores de metadata,
secrets, mensajes de excepción, stdout/stderr raw de Docker ni archivos de evidencia.

| Fase | Operación exacta distinguida |
|---|---|
| `host-admin-preflight` / `host-admin-runner` | Linux, root efectivo, checkout, branch/HEAD y pin auxiliar. |
| `endpoint-context-show` / `endpoint-context-inspect` | Lectura local `docker context`; sin llamada al daemon. |
| `socket-path-canonicalize`, `socket-preflight-canonical`, `socket-preflight-selected` | Resolver endpoint Unix local y comprobar que ambas rutas representan el mismo socket. |
| `socket-create`, `socket-configure`, `socket-connect` | Creación, timeout y conexión Unix; no se envían bytes de aplicación. |
| `peercred-read`, `peercred-decode` | `getsockopt(SO_PEERCRED)` y decodificación `struct 3i`, separados. |
| `peer-process-start-before`, `peer-comm-read`, `peer-exe-readlink`, `peer-exe-stat`, `peer-status-read`, `peer-pidns-read`, `local-pidns-read`, `peer-process-start-after` | Lecturas individuales usadas por la regla de identidad vigente. Se permiten solo `stat/comm/status`, link/metadata de `exe` y namespace PID; no se leen `/proc` adicionales. |
| `socket-revalidate-canonical`, `socket-revalidate-selected` | Relectura por separado del socket después de metadata del peer. |
| `peer-identity-verified` | El peer, UID, estabilidad del proceso, `dockerd`, propiedad/modo del ejecutable y namespace PID coinciden con el predicado local aprobado. |

El criterio preserva el predicado usado en F2d; no verifica hash/firma del binario ni acredita
integridad frente a root comprometido. Un error de lectura se devuelve en la subfase exacta;
una discrepancia legible devuelve `IDENTITY_MISMATCH` sin valores.

## Revalidaciones locales antes de F1

Antes de cada consulta Docker condicional, el helper vuelve a hacer stat separado del socket
canónico y seleccionado. Las fases exactas son socket-revalidate-f1-image-canonical,
socket-revalidate-f1-image-selected, socket-revalidate-f1-container-canonical y
socket-revalidate-f1-container-selected. Un error detiene la consulta asociada y devuelve
solo fase/código sanitizado. Estas fases son posteriores a la identidad válida y no abren
consultas adicionales.

## F1 — etapa posterior y estrictamente condicional

Después de la línea `peer-identity-verified|OK` solamente:

1. Una consulta `docker image inspect --format '{{json .Config.Volumes}}'` a
   `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`. No se hace
   pull; se acepta solo metadata vacía/`null`/`{}`. La consulta precede a F1 container.
2. Una consulta `docker inspect --type container --format` al ID literal
   `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`. Solo proyecta los
   campos ya allowlisted por F1: ID/nombre/estado/exit/OOM, tres labels de snapshot, red,
   rootfs, user, cap-drop, security options, memoria/swap/CPU/PIDs, restart, tmpfs/count,
   logging, puertos, shm, Binds y Mounts. Compara en memoria contra el contrato F1 y devuelve
   solo `OK`, `F1_POLICY_MISMATCH` o error de lectura/parser; no devuelve nombres de campos ni
   valores.

Para ambas llamadas se fija `DOCKER_HOST` al socket local ya acreditado, se descartan otros
overrides y stderr, se limitan stdout (4 KiB/8 KiB) y timeout (10 s por consulta). La segunda
lectura no ocurre si falla la primera. No se inspecciona por nombre ni otro ID. Ninguna llamada
ocurre si la identidad no está probada.

## Límites y stop

- Una invocación total, timeout externo 60 s, cero retries. El helper acota las dos lecturas de
  contexto a 5 s, conexión a 3 s y cada lectura Docker condicional a 10 s.
- Las únicas llamadas posibles al daemon son los dos GET read-only descritos en F1, solo tras
  identidad válida. No `docker info`, inspect de otros recursos, `ps`, logs, exec, filesystem,
  create/run/start/wait/stop/rm, cleanup, network/volume, cambios de configuración, motor o
  instalación de paquetes.
- No se corre r9, copia, arranque Pages/workerd ni C03 integrado en este runner. Esos pasos
  permanecen bloqueados hasta un resultado de identidad útil y sus preflights/alcances.
- Todo resultado/timeout consume esta autorización. Si root efectivo tampoco puede leer un
  subpaso, se conserva solo la línea sanitized y se presenta una alternativa con causa/alcance;
  no se repite esta invocación.
