# JIT — atestación limitada de Docker Desktop WSL y lectura F1

ID: `H3REQ1-C03-DOCKER-DESKTOP-WSL-ENDPOINT-F1-ONCE-20261008-V1`  
Estado: **preparado; aprobación explícita pendiente; no ejecutado**.  
Candidato: `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Decisión de entorno

El usuario confirmó Docker Desktop para Windows con WSL integration. Docker documenta que
el Engine corre en su propia distribución WSL `docker-desktop`, aislada de Ubuntu; Ubuntu
recibe acceso al CLI/socket por integración. Por ello `sudo -i` en Ubuntu solo da root en
Ubuntu, no visibilidad de `/proc` del Engine. Tampoco es un contenedor el lugar correcto.
Fuentes: [Docker Desktop WSL 2 backend](https://docs.docker.com/desktop/features/wsl/) y
[Docker Desktop networking](https://docs.docker.com/desktop/features/networking/).

La aprobación anterior del JIT
`H3REQ1-C03-PEER-SUBSTEP-DIAGNOSTIC-F1-READ-ONCE-20261008-V1`, SHA-256
`e474440a425e376b238858af820698ec3ea88fb5ef20002de6852eef10e27173`, sigue **sin consumir**.
Su condición de ejecutar desde el Linux que ve el proceso y `/proc` del daemon no se puede
satisfacer desde Ubuntu WSL ni desde el contenedor en esta topología. No pegar ese bloque en
Ubuntu ni entrar a la distro interna `docker-desktop` para intentar satisfacerlo.

## Solicitud de autorización agrupada

Solicito una invocación del runner acotado de Ubuntu WSL y la aceptación explícita de que el
resultado `desktop-wsl-endpoint-attested|OK` sea la alternativa ambiental al requisito de
identidad de proceso para continuar el ciclo local ya aprobado. Solo después de esa señal se
lee F1 mediante las dos consultas allowlisted. Si el endpoint/Linux Engine no coincide, la
imagen no cumple o F1 no coincide, se detiene; no hay retry.

**Riesgo residual nuevo (MEDIUM):** la salida no prueba PID/UID del peer, ejecutable `dockerd`,
namespace ni integridad del proceso. Prueba únicamente que la configuración local `default`
apunta a `unix:///var/run/docker.sock`, que ese endpoint devuelve `linux` en `docker version`
y, condicionalmente, que el F1 exacto conserva la política allowlisted. La inferencia depende
de la declaración del usuario de que la integración activa es Docker Desktop WSL. Un root
comprometido en Ubuntu podría reemplazar el socket/contexto o falsificar esta ruta. No es
equivalente criptográfico a identidad de proceso. Owner del residual: Romel; vence al aceptar
o rechazar la decisión y, si se acepta, al cerrar el ciclo local aprobado.

La aprobación cubre solo una invocación del diagnóstico, la lectura de la imagen fijada y la
lectura del ID F1 exacto condicionada al endpoint aprobado. Si devuelve los tres registros
PASS, también acepta esa atestación como precondición para continuar r9 y etapas locales bajo
la autorización consolidada existente y su excepción iterativa; los límites originales se
mantienen. Este JIT por sí solo no ejecuta r9, crea recursos, ni cambia Docker. No revive ni
consume JITs antiguos.

La respuesta debe aprobar este ID/SHA como un único objetivo y aceptar el residual MEDIUM;
no se solicitará permiso separado por archivo o hash.

## Ejecutor, ubicación y comando único

Ejecutor: el usuario `romel`, en una terminal **Ubuntu WSL del host Windows** donde exista
exactamente el checkout indicado y Docker Desktop WSL integration esté activo. No usar
`studiamatch-dev`, ningún otro contenedor, PowerShell ni la distro interna `docker-desktop`.
No hace falta `sudo`; el usuario debe poder leer el socket por la integración normal. El runner
comprueba checkout/branch/HEAD, pin del helper y del proyector F1, WSL, contexto `default` y
el endpoint esperado. Ejecuta exactamente una vez con timeout externo de 50 s:

```bash
set -Eeuo pipefail
readonly RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run_wsl_desktop_attestation_once.sh'
readonly RUNNER_SHA256='39cebc3e0dbf1e290c11ff6fce0f7a98586209bd94a8af2acf0e6d43cad88f87'
if (( EUID == 0 )); then
  printf 'phase=wsl-attestation-preflight|error_code=RUN_AS_WSL_USER\n'
  exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout ]]; then
  printf 'phase=wsl-attestation-preflight|error_code=RUNTIME_UNAVAILABLE\n'
  exit 1
fi
hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)" || {
  printf 'phase=wsl-attestation-preflight|error_code=RUNNER_HASH_FAILED\n'
  exit 1
}
if [[ "${hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  printf 'phase=wsl-attestation-preflight|error_code=RUNNER_HASH_MISMATCH\n'
  exit 1
fi
exec /bin/bash "$RUNNER" 2>/dev/null
```

El runner no eleva privilegios, no escribe configuración ni instala herramientas. Limpia
variables de override de Docker y fija el `HOME`/`PATH` del usuario del checkout. El helper
consulta el endpoint local solo después de comprobar el contexto; el Engine API se limita a
`docker version --format '{{.Server.Os}}'`. F1 se consulta solo tras `linux` y el endpoint
exacto. La ruta `unix:///var/run/docker.sock` es la documentada para clientes Windows WSL.

## Operaciones incluidas y orden

1. Preflight local WSL, checkout, branch/HEAD, ausencia de `DOCKER_HOST`, `DOCKER_CONTEXT`,
   `DOCKER_TLS_VERIFY` y `DOCKER_CERT_PATH`; hash del proyector F1 ya revisado.
2. Lectura local de `docker context inspect default`; solo se acepta el endpoint literal
   `unix:///var/run/docker.sock`. No revela el JSON.
3. Una consulta read-only `docker version --format '{{.Server.Os}}'` en ese socket; solo se
   acepta `linux`. Esto es la atestación limitada, no PID-level.
4. Tras `desktop-wsl-endpoint-attested|OK`, consulta read-only de volúmenes de la imagen
   fijada `node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844`; no
   hace pull, acepta solo vacío/`null`/`{}`.
5. Si la imagen pasa, una consulta read-only al ID F1
   `54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9` con exactamente la
   proyección F1 fijada por el helper. Comparación en memoria; no emite valores.

Salida aceptada, y nada más que fase/código:

```text
phase=desktop-wsl-endpoint-attested|error_code=OK
phase=f1-image-read|error_code=OK
phase=f1-container-read|error_code=OK
```

Ante fallo devuelve la fase/código sanitizado; si ya superó una etapa, sus líneas PASS pueden
preceder la primera falla. No compartir stdout/stderr crudo, rutas/IDs del daemon, metadata,
hashes de runtime, credenciales ni screenshots. La salida del runner se limita a esas líneas.

## Exclusiones y condición de parada

No ejecuta el diagnóstico de SO_PEERCRED o `/proc`, `docker info`, `ps`, logs, otros `inspect`,
pull, create/run/start/exec/wait/stop/rm, redes/volúmenes, limpieza, configuración, cambio o
instalación de Docker. No corre r9 ni tests; no toca código de producto, DB, secretos, CI
remoto, ramas protegidas ni Pages. Un resultado/timeout consume el JIT. Si falla, detenerse y
presentar esa primera fase; no retry ni reinstalación.

## Pins del runner y código revisado

| Artefacto | SHA-256 |
|---|---|
| `tests/h3req1_docker_peer_substep_diag/desktop_wsl_attestation_once.py` | `c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb` |
| `tests/h3req1_docker_peer_substep_diag/test_desktop_wsl_attestation_once.py` | `063e05162bb432d7b9c48871da62fae21ff57ac00ffe975a8cfe1795fd4d32b3` |
| `tests/h3req1_docker_peer_substep_diag/run_wsl_desktop_attestation_once.sh` | `39cebc3e0dbf1e290c11ff6fce0f7a98586209bd94a8af2acf0e6d43cad88f87` |
| proyector F1 preexistente, sin modificar | `794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463` |

No se ejecutaron los tests sintéticos, el runner ni Docker. La revisión estática cubrió el
orden endpoint → OS → imagen → F1; el pin de proyector; límites de salida/timeout; comandos
read-only; ausencia de operaciones mutantes; comparación contra el parser F1 existente y
salida sanitizada. Esta revisión no acredita runtime ni que el endpoint pertenezca a un
proceso `dockerd` concreto.
