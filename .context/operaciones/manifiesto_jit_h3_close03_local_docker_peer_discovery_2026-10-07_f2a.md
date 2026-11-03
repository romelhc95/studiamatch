# Solicitud JIT F2a — identificar endpoint y listener local Docker

Estado: **propuesto, NO aprobado, NO ejecutado**. F1 fue consumido con NO-GO pre-start;
F2 metadata read también permanece NO-GO. F2a no inspecciona ni accede al contenedor F1.

## Propósito y alcance

La revisión de F2 determinó que `unix://` + `stat` no autentica un daemon local: un socket
local podría ser proxy. Esta operación descubre únicamente la configuración local del Docker
context seleccionado y el proceso que tiene abierto el socket correspondiente, usando
`/proc`; no envía peticiones al socket ni accede al daemon, a contenedores o a recursos.

El fin es obtener evidencia sanitizada para que un humano determine si el listener es el
engine local autorizado. Un proceso `proxy`/desconocido o una configuración no Unix significa
NO-GO; no se intenta resolver upstream, ni conectar a otro destino, ni inferir que el proxy es
seguro.

## Candidato e input/output

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

- Lee localmente `docker context show` y `docker context inspect --format` para el endpoint
  del contexto activo; son lecturas de configuración cliente, no solicitan metadata al daemon.
- Si el endpoint no es Unix local, registra solo `endpoint-kind=non-unix`; no imprime la URL
  ni contacta el destino.
- Si es Unix local, resuelve y registra path canónico más owner/group/mode/device/inode del
  socket; lee `/proc/net/unix`, `/proc/<pid>/fd`, `/proc/<pid>/comm`, `/proc/<pid>/exe` y
  UID del proceso para mapear listener(s). No lee `cmdline`, `environ`, memoria del proceso,
  archivos de configuración de daemon ni filesystem del contenedor.
- No abre ni conecta al socket; no manda bytes. No ejecuta `docker inspect`, `info`, `ps`,
  `logs`, `exec`, `create`, `start`, `stop`, `wait` o `rm`.
- Evidencia nueva: `.context/evidencia/h3req1_c03_local_docker_peer_discovery_f2a_2026-10-07.md`;
  debe no existir ni ser symlink. `umask 077`; se escriben endpoint Unix sanitizado,
  identidad del socket, identidades de proceso visibles y resultado de descubrimiento. Para
  endpoint no Unix solo se registra su clase, nunca URL/host.

## Límites, fallo y autorización

Timeout local ≤5 s por operación de configuración/stat; scan de `/proc` ≤10 s, salida total
≤8 KiB, timeout global 60 s + 10 s de gracia. Errores, timeout, campos incompletos, ruta no
allowlisted o listener no identificado producen NO-GO, evidencia sanitizada y ningún reintento.
Una ejecución consume este JIT.

La API Docker no se invoca y el socket no se conecta. Leer metadatos de contexto y procesos
locales sigue sujeto a la autorización JIT. El residual same-user de un script local se
documenta: quien controle la cuenta puede invocar directamente la operación. Owner: Romel,
responsable humano del proyecto y titular operativo del checkout. Expira al concluir la única
lectura F2a o cancelarla.

No autoriza la lectura F2 del contenedor, ningún otro recurso, consultas Docker al daemon,
red/remote, DB/SQL/Auth/Supabase, logs/exec/filesystem, npm/workerd/Pages, push/PR/merge/deploy,
limpieza, restart, rollback o retry. F2 requerirá un JIT actualizado y una aprobación separada
si F2a demuestra una identidad local aceptable.

## Comando exacto — solo tras aprobación humana de este JIT

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /usr/bin/timeout --signal=TERM --kill-after=10s 60s \
  /bin/bash -Eeuo pipefail <<'H3_C03_LOCAL_DOCKER_PEER_DISCOVERY_F2A'
set -Eeuo pipefail
readonly ROOT_EXPECTED='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH_EXPECTED='feat/h3req1-sync-20261002'
readonly HEAD_EXPECTED='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly REPORT='.context/evidencia/h3req1_c03_local_docker_peer_discovery_f2a_2026-10-07.md'
readonly STARTED_AT="$SECONDS"
report_open=false
report_done=false
die() {
  if [[ "$report_open" == true ]]; then
    printf 'discovery-result=NO-GO|reason=preflight-or-reader-failure\nraw-endpoint=discarded\n' >&2
    report_done=true
  else
    printf 'NO-GO: %s\n' "$1" >&2
  fi
  exit 1
}
on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$report_open" == true && "$report_done" != true ]]; then
    printf 'discovery-result=NO-GO|reason=unexpected-exit\nraw-endpoint=discarded\n' >&2
    status=1
  fi
  exit "$status"
}
trap on_exit EXIT
local_control() {
  local maximum=$1 remaining
  shift
  remaining=$((60 - (SECONDS - STARTED_AT)))
  (( remaining > 0 )) || return 124
  (( remaining > maximum )) && remaining=$maximum
  timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" "$@"
}
root="$(local_control 5 realpath -e -- .)" || die 'cannot resolve checkout'
[[ "$root" == "$ROOT_EXPECTED" ]] || die 'unexpected checkout root'
[[ "$(local_control 5 git rev-parse --show-toplevel)" == "$ROOT_EXPECTED" ]] || die 'checkout root differs'
[[ "$(local_control 5 git branch --show-current)" == "$BRANCH_EXPECTED" ]] || die 'branch differs'
[[ "$(local_control 5 git rev-parse HEAD)" == "$HEAD_EXPECTED" ]] || die 'HEAD differs'
for directory in .context .context/operaciones .context/evidencia; do
  [[ -d "$directory" && ! -L "$directory" ]] || die 'documentation directory missing or symlinked'
  canonical="$(local_control 5 realpath -e -- "$directory")" || die 'cannot resolve documentation directory'
  [[ "$canonical" == "$ROOT_EXPECTED/$directory" ]] || die 'documentation directory escapes checkout'
done
[[ ! -e "$REPORT" && ! -L "$REPORT" ]] || die 'F2a evidence exists or is symlinked'

unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH
context="$(local_control 5 docker context show 2>/dev/null)" || die 'cannot read local context selection'
[[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || die 'context name schema invalid'
endpoint_json="$(local_control 5 docker context inspect --format '{{json (index .Endpoints "docker").Host}}' "$context" 2>/dev/null)" \
  || die 'cannot read local context endpoint configuration'

umask 077
set -o noclobber
exec >"$REPORT" 2>&1
set +o noclobber
report_open=true
printf 'jit=H3-CLOSE-03-LOCAL-DOCKER-PEER-DISCOVERY-F2A-2026-10-07\n'
printf 'scope=context-config-and-proc-listener-only|daemon-api=not-called|socket=not-connected|F1-resource=not-accessed\n'

if [[ ! "$endpoint_json" =~ ^\"unix:///[A-Za-z0-9_./-]+\"$ ]]; then
  if [[ "$endpoint_json" == '"unix://' * ]]; then
    printf 'endpoint-kind=unix-unclassified\ndiscovery-result=NO-GO|reason=endpoint-path-schema\n'
  else
    printf 'endpoint-kind=non-unix\ndiscovery-result=NO-GO|reason=endpoint-not-local-unix\n'
  fi
  printf 'raw-endpoint=discarded\n'
  report_done=true
  exit 0
fi
socket="${endpoint_json#\"unix://}"
socket="${socket%\"}"
socket_identity="$(local_control 2 stat -Lc '%F|%d:%i:%u:%g:%a' -- "$socket" 2>/dev/null)" \
  || die 'cannot stat context socket'
[[ "$socket_identity" =~ ^socket\|[0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4}$ ]] || die 'endpoint is not a Unix socket'
canonical_socket="$(local_control 2 realpath -e -- "$socket" 2>/dev/null)" || die 'cannot canonicalize socket'
canonical_identity="$(local_control 2 stat -Lc '%F|%d:%i:%u:%g:%a' -- "$canonical_socket" 2>/dev/null)" \
  || die 'cannot stat canonical socket'
[[ "$canonical_identity" == "$socket_identity" ]] || die 'socket identity changed during resolution'
[[ "$canonical_socket" =~ ^/[A-Za-z0-9_./+-]{1,240}$ ]] || die 'canonical socket path not allowlisted'

peer_b64="$(set -o pipefail; local_control 10 python3 - "$canonical_socket" <<'PY' | head -c 8193 | base64 -w0
import os
import re
import sys

sock_path = sys.argv[1]
try:
    with open('/proc/net/unix', 'r', encoding='ascii', errors='strict') as handle:
        lines = handle.readlines()
except OSError:
    print('PROC_UNAVAILABLE')
    raise SystemExit(0)

inodes = set()
for line in lines[1:]:
    fields = line.rstrip('\n').split(None, 7)
    if len(fields) == 8 and fields[7] == sock_path and fields[6].isdigit():
        inodes.add(fields[6])

peers = set()
if inodes:
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        fd_root = f'/proc/{pid}/fd'
        try:
            descriptors = os.listdir(fd_root)
        except OSError:
            continue
        matched = False
        for fd in descriptors:
            try:
                target = os.readlink(f'{fd_root}/{fd}')
            except OSError:
                continue
            if target.startswith('socket:[') and target.endswith(']') and target[8:-1] in inodes:
                matched = True
                break
        if not matched:
            continue
        try:
            with open(f'/proc/{pid}/comm', 'r', encoding='ascii', errors='strict') as handle:
                comm = handle.read(128).strip()
            exe = os.readlink(f'/proc/{pid}/exe')
            uid = os.stat(f'/proc/{pid}').st_uid
        except OSError:
            peers.add('PROCESS_UNREADABLE')
            continue
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', comm):
            comm = 'PROCESS_NAME_UNCLASSIFIED'
        if not re.fullmatch(r'/[A-Za-z0-9_./+-]{1,240}', exe):
            exe = 'EXECUTABLE_PATH_UNCLASSIFIED'
        peers.add(f'{uid}|{comm}|{exe}')
        if len(peers) > 8:
            peers = {'TOO_MANY_LISTENERS'}
            break

if not inodes:
    print('NO_SOCKET_INODE')
elif not peers:
    print('NO_VISIBLE_LISTENER_PROCESS')
else:
    for peer in sorted(peers):
        print(peer)
PY
)" || die 'bounded /proc listener discovery failed'
peer_bytes="$(printf '%s' "$peer_b64" | base64 --decode 2>/dev/null | wc -c)" || die 'listener result decode failed'
[[ "$peer_bytes" =~ ^[0-9]+$ ]] && (( peer_bytes > 0 && peer_bytes <= 8192 )) || die 'listener result exceeded cap'
peer_result="$(printf '%s' "$peer_b64" | base64 --decode 2>/dev/null)" || die 'listener result decode failed'
[[ "$peer_result" != *$'\r'* ]] || die 'listener result contains CR'
after_identity="$(local_control 2 stat -Lc '%F|%d:%i:%u:%g:%a' -- "$canonical_socket" 2>/dev/null)" \
  || die 'cannot recheck socket identity'
[[ "$after_identity" == "$canonical_identity" ]] || die 'socket changed during process discovery'
printf 'endpoint-kind=local-unix\nsocket-path=%s\nsocket-identity=%s\n' "$canonical_socket" "$canonical_identity"
printf 'daemon-api=not-called|socket-connected=false|remote-request=false\n'
if [[ "$peer_result" == NO_SOCKET_INODE || "$peer_result" == NO_VISIBLE_LISTENER_PROCESS \
  || "$peer_result" == PROC_UNAVAILABLE || "$peer_result" == PROCESS_UNREADABLE \
  || "$peer_result" == TOO_MANY_LISTENERS ]]; then
  printf 'listener-discovery=NO-GO|reason=%s\n' "$peer_result"
else
  while IFS= read -r peer_line; do
    [[ "$peer_line" =~ ^[0-9]+\|[A-Za-z0-9_.-]{1,64}\|(/[A-Za-z0-9_./+-]{1,240}|EXECUTABLE_PATH_UNCLASSIFIED)$ ]] \
      || die 'listener metadata schema invalid'
    printf 'listener=%s\n' "$peer_line"
  done <<< "$peer_result"
  printf 'listener-discovery=IDENTIFIED\n'
fi
printf 'raw-endpoint=discarded|f1-resource=untouched\n'
report_done=true
H3_C03_LOCAL_DOCKER_PEER_DISCOVERY_F2A
```

La revisión/aprobación de F2a, si se concede, autoriza exclusivamente esta lectura local de
configuración y `/proc`. El JIT se consume aunque falle. No constituye aprobación ni ejecución
de F2; cualquier acceso al daemon requiere JIT F2 corregido y aprobación separada.
