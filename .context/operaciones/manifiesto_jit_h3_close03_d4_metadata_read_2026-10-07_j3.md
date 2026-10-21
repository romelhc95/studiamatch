# Solicitud JIT J3 — lectura acotada de metadata D4

Estado: **propuesto, NO aprobado, NO ejecutado**. D4 ya fue aprobado/consumido; este JIT
separado no hereda ni amplía sus permisos.

## Propósito y alcance

El runner D4 terminó NO-GO porque una comparación allowlisted de identidad/controles no
coincidió, pero solo persistió un error genérico. El proceso del fixture devolvió exit 0;
el contenedor quedó `exited` y preservado. J3 busca identificar cuál campo concreto falló,
sin cambiar el recurso y sin volver a leer logs.

Único recurso: contenedor existente con ID exacto
`d52d606bdc809eb7bfd13c6e16c4e0a7bc29db2bf3e71e7941b75a84de868650`, nombre esperado
`h3req1-c03-snapshot-diagnostic-d4-20261007`, JIT label D4, manifest label
`84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c` y run nonce
`545995-1791421960085913804-12717`.

La única consulta al daemon autorizable es `docker inspect --type container --format`
contra ese ID literal. Puede leer solo ID/nombre/estado/exit/OOM, labels D4, red/rootfs/user,
capabilities/security options, memoria/CPU/PIDs/restart, tmpfs `/diag`, logging `local`
(type/max-size/max-file/compress), tipos/destinos de mounts, port bindings y shm size.
No lee `.Config.Env`, command, image history, `.State.Error`, logs ni datos de filesystem.
El stdout se limita a 8 KiB; el raw permanece en memoria y se descarta; la salida muestra
solo nombres de campos discrepantes y valores estructurales sanitizados. `stderr` se
descarta. Un fallo, timeout, salida excesiva, identidad/schema no válido o error del
sanitizador emite NO-GO sin volver a consultar.

Preflight local permitido: comprobar rama/HEAD, hashes de D4, evidencia y sidecar; consultar
`docker context show/inspect` solo para exigir endpoint Unix local, y verificar identidad
del socket con `stat`/`realpath`. No se crea, inicia, para ni elimina recurso. No hay `logs`,
`exec`, `rm`, cleanup, retry, query por nombre, ni acceso a otros IDs. Riesgo residual:
carrera local stat/connect del socket; no existe autenticación criptográfica del peer.

## Inputs fijados

| Input | SHA-256 |
|---|---|
| JIT D4 consumido | `fcec517023f4a85e1381ad4b1b2be949fba933596e469293fed28315397a4fba` |
| Runner D4 | `785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107` |
| Sidecar D4 | `84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c` |
| Evidencia D4 | `022edaab6a693cb7d1261595aefd1588f89904c03b8a741d296b85f5cd2a5efe` |

## Comando exacto — solo tras aprobación J3

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /bin/bash -Eeuo pipefail <<'H3_C03_D4_METADATA_J3'
set -Eeuo pipefail
readonly ROOT_EXPECTED='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH_EXPECTED='feat/h3req1-sync-20261002'
readonly HEAD_EXPECTED='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly ID_EXPECTED='d52d606bdc809eb7bfd13c6e16c4e0a7bc29db2bf3e71e7941b75a84de868650'
readonly NAME_EXPECTED='h3req1-c03-snapshot-diagnostic-d4-20261007'
readonly JIT_EXPECTED='H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D4'
readonly MANIFEST_EXPECTED='84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c'
readonly NONCE_EXPECTED='545995-1791421960085913804-12717'
readonly D4_JIT='.context/operaciones/manifiesto_jit_h3_close03_snapshot_diagnostic_2026-10-07_d4.md'
readonly D4_RUNNER='tests/h3req1_c03_snapshot_diagnostic_d4.sh'
readonly D4_SIDECAR='tests/h3req1-c03-snapshot-diagnostic-d4.sha256'
readonly D4_EVIDENCE='.context/evidencia/h3req1_c03_snapshot_diagnostic_2026-10-07_d4.md'
die() { printf 'NO-GO: %s\n' "$1" >&2; exit 1; }
hash_of() { sha256sum -- "$1" 2>/dev/null | awk '{print $1}'; }
[[ "$(pwd -P)" == "$ROOT_EXPECTED" && "$(git rev-parse --show-toplevel)" == "$ROOT_EXPECTED" ]] || die 'unexpected checkout root'
[[ "$(git branch --show-current)" == "$BRANCH_EXPECTED" && "$(git rev-parse HEAD)" == "$HEAD_EXPECTED" ]] || die 'candidate branch/HEAD changed'
for path in "$D4_JIT" "$D4_RUNNER" "$D4_SIDECAR" "$D4_EVIDENCE"; do
  [[ -f "$path" && ! -L "$path" ]] || die 'a fixed D4 input is missing or symlinked'
done
[[ "$(hash_of "$D4_JIT")" == 'fcec517023f4a85e1381ad4b1b2be949fba933596e469293fed28315397a4fba' ]] || die 'D4 JIT hash changed'
[[ "$(hash_of "$D4_RUNNER")" == '785908597840def21e394c11181114d34a349746226a3c058a8bb3426f2f6107' ]] || die 'D4 runner hash changed'
[[ "$(hash_of "$D4_SIDECAR")" == '84b06ba5dcaa3795e1267397d13d57f12aa0b2b5d83b4beca14a9b8fb49b3e4c' ]] || die 'D4 sidecar hash changed'
[[ "$(hash_of "$D4_EVIDENCE")" == '022edaab6a693cb7d1261595aefd1588f89904c03b8a741d296b85f5cd2a5efe' ]] || die 'D4 evidence hash changed'
sha256sum --check "$D4_SIDECAR" >/dev/null 2>&1 || die 'D4 sidecar no longer pins its runner'
grep -Fxq "container-created-id=$ID_EXPECTED" "$D4_EVIDENCE" || die 'fixed ID not present in D4 evidence'
grep -Fxq 'run-nonce=545995-1791421960085913804-12717' "$D4_EVIDENCE" || die 'fixed nonce not present in D4 evidence'

unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH
context="$(timeout --foreground --signal=TERM --kill-after=1s 5s docker context show 2>/dev/null)" || die 'cannot read local Docker context'
[[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || die 'Docker context name outside schema'
endpoint_json="$(timeout --foreground --signal=TERM --kill-after=1s 5s docker context inspect --format '{{json (index .Endpoints "docker").Host}}' "$context" 2>/dev/null)" || die 'cannot read Docker context endpoint'
[[ "$endpoint_json" =~ ^\"unix:///[A-Za-z0-9_./-]+\"$ ]] || die 'Docker endpoint is not a local Unix socket'
endpoint="${endpoint_json:1:${#endpoint_json}-2}"
socket="${endpoint#unix://}"
socket_identity="$(timeout --foreground --signal=TERM --kill-after=0.2s 1s stat -Lc '%F|%d:%i:%u:%g:%a' -- "$socket" 2>/dev/null)" || die 'cannot stat local Docker socket'
[[ "$socket_identity" =~ ^socket\|[0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4}$ ]] || die 'endpoint is not a Unix socket'
initial_socket_identity="$socket_identity"
socket="$(timeout --foreground --signal=TERM --kill-after=0.2s 1s realpath -e -- "$socket" 2>/dev/null)" || die 'cannot canonicalize Docker socket'
socket_identity="$(timeout --foreground --signal=TERM --kill-after=0.2s 1s stat -Lc '%F|%d:%i:%u:%g:%a' -- "$socket" 2>/dev/null)" || die 'cannot verify canonical Docker socket'
[[ "$socket_identity" == "$initial_socket_identity" ]] || die 'Docker socket identity changed during canonicalization'
export DOCKER_HOST="unix://$socket"
unset DOCKER_CONTEXT
[[ "$(timeout --foreground --signal=TERM --kill-after=0.2s 1s stat -Lc '%F|%d:%i:%u:%g:%a' -- "$socket" 2>/dev/null)" == "$initial_socket_identity" ]] || die 'Docker socket changed before inspect'

readonly FORMAT='{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{.Config.User}}|{{json .HostConfig.CapDrop}}|{{json .HostConfig.SecurityOpt}}|{{.HostConfig.Memory}}|{{.HostConfig.MemorySwap}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.PidsLimit}}|{{.HostConfig.RestartPolicy.Name}}|{{index .HostConfig.Tmpfs "/diag"}}|{{.HostConfig.LogConfig.Type}}|{{index .HostConfig.LogConfig.Config "max-size"}}|{{index .HostConfig.LogConfig.Config "max-file"}}|{{index .HostConfig.LogConfig.Config "compress"}}|{{range .Mounts}}{{.Type}}:{{.Destination}};{{end}}|{{json .HostConfig.PortBindings}}|{{.HostConfig.ShmSize}}'
set +e
metadata_b64="$(set -o pipefail; timeout --foreground --signal=TERM --kill-after=1s 10s docker inspect --type container --format "$FORMAT" "$ID_EXPECTED" 2>/dev/null | head -c 8193 | base64 -w0)"
inspect_status=$?
set -e
[[ "$inspect_status" -eq 0 && -n "$metadata_b64" ]] || die 'single inspect failed, timed out, or exceeded output bound; raw discarded'
metadata_bytes="$(printf '%s' "$metadata_b64" | base64 --decode 2>/dev/null | wc -c)" || die 'bounded metadata decode failed'
[[ "$metadata_bytes" =~ ^[0-9]+$ ]] && (( metadata_bytes > 0 && metadata_bytes <= 8192 )) || die 'metadata output exceeded 8 KiB; raw discarded'
metadata="$(printf '%s' "$metadata_b64" | base64 --decode 2>/dev/null)" || die 'metadata decode failed'
[[ "$metadata" != *$'\n'* && "$metadata" != *$'\r'* ]] || die 'unexpected multiline metadata; raw discarded'
IFS='|' read -r id name state exit_code oom jit_label manifest_label run_label network_mode readonly_root configured_user cap_drop security_opt memory memory_swap nano_cpus pids_limit restart tmpfs log_type log_max_size log_max_file log_compress mounts port_bindings shm_size <<< "$metadata"
[[ "$shm_size" =~ ^[0-9]+$ ]] || die 'metadata schema/field count mismatch; raw discarded'

mismatches=()
compare() { [[ "$2" == "$3" ]] || mismatches+=("$1"); }
compare id "$id" "$ID_EXPECTED"
compare name "$name" "/$NAME_EXPECTED"
compare state "$state" exited
compare exit_code "$exit_code" 0
compare oom "$oom" false
compare jit_label "$jit_label" "$JIT_EXPECTED"
compare manifest_label "$manifest_label" "$MANIFEST_EXPECTED"
compare run_label "$run_label" "$NONCE_EXPECTED"
compare network "$network_mode" none
compare readonly_root "$readonly_root" true
compare user "$configured_user" '1001:1001'
compare cap_drop "$cap_drop" '["ALL"]'
compare security_opt "$security_opt" '["no-new-privileges:true"]'
compare memory "$memory" 134217728
compare memory_swap "$memory_swap" 134217728
compare nano_cpus "$nano_cpus" 500000000
compare pids_limit "$pids_limit" 64
compare restart "$restart" no
compare diag_tmpfs "$tmpfs" 'rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700'
compare log_type "$log_type" local
compare log_max_size "$log_max_size" 1m
compare log_max_file "$log_max_file" 1
compare log_compress "$log_compress" false
[[ "$mounts" == 'tmpfs:/diag;' ]] || mismatches+=(mounts)
if [[ "$port_bindings" != null && "$port_bindings" != '{}' ]]; then mismatches+=(port_bindings); fi
compare shm_size "$shm_size" 16777216

if (( ${#mismatches[@]} == 0 )); then
  printf 'metadata-result=all-allowlisted-fields-match\n'
else
  mismatch_csv="$(IFS=,; printf '%s' "${mismatches[*]}")"
  printf 'metadata-result=control-mismatch\nmismatch-fields=%s\n' "$mismatch_csv"
fi
if [[ "$state" =~ ^(created|running|paused|restarting|removing|exited|dead)$ ]]; then printf 'container-state=%s\n' "$state"; else printf 'container-state=unclassified\n'; fi
if [[ "$exit_code" =~ ^[0-9]{1,3}$ ]]; then printf 'container-exit=%s\n' "$exit_code"; else printf 'container-exit=unclassified\n'; fi
if [[ "$oom" == true || "$oom" == false ]]; then printf 'container-oom=%s\n' "$oom"; else printf 'container-oom=unclassified\n'; fi
if [[ -z "$mounts" ]]; then
  printf 'mounts-observed=none\n'
elif [[ "$mounts" =~ ^((tmpfs|bind|volume):/[A-Za-z0-9_./-]+;?)+$ ]]; then
  printf 'mounts-observed=%s\n' "${mounts%;}"
else
  printf 'mounts-observed=unclassified\n'
fi
if [[ "$tmpfs" =~ ^[A-Za-z0-9_=,:./-]{0,256}$ ]]; then printf 'diag-tmpfs-observed=%s\n' "$tmpfs"; else printf 'diag-tmpfs-observed=unclassified\n'; fi
if [[ "$log_type" =~ ^[A-Za-z0-9_-]{1,32}$ && "$log_max_size" =~ ^[A-Za-z0-9]+$ && "$log_max_file" =~ ^[0-9]{1,3}$ && ( "$log_compress" == true || "$log_compress" == false || -z "$log_compress" ) ]]; then
  printf 'logging-observed=%s|max-size=%s|max-file=%s|compress=%s\n' "$log_type" "$log_max_size" "$log_max_file" "${log_compress:-unset}"
else
  printf 'logging-observed=unclassified\n'
fi
H3_C03_D4_METADATA_J3
```

Esta solicitud no autoriza ninguna acción adicional sobre D4. Si se aprueba, se ejecuta una
sola vez; el permiso queda consumido aunque haya error, timeout o parser NO-GO. Sin otro JIT
no se repite ni se amplía la consulta.
