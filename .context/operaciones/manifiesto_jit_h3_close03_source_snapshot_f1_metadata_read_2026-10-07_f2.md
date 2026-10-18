# Solicitud JIT F2 — lectura metadata pre-start de F1

Estado: **propuesto, NO aprobado, NO ejecutado**. F1 fue aprobado/consumido una vez y
falló pre-start; su decisión humana se registra en
[`atestación F1`](../evidencia/h3req1_c03_source_snapshot_f1_approval_2026-10-07.md). F2 no
hereda ni amplía el permiso F1.

## Propósito

El F1 runner registró que la inspección de identidad/controles pre-start falló, pero no
guardó el nombre del campo discrepante. F2 autoriza una única lectura read-only de metadata
allowlisted del contenedor F1 exacto para identificar la condición, sin modificar su estado.

## Recurso e inputs fijos

Único recurso: ID
`54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9`, nombre esperado
`h3req1-c03-source-snapshot-f1-20261007`, nonce `552890-0-28538`, JIT label
`H3-CLOSE-03-SOURCE-SNAPSHOT-F1-2026-10-07`, manifest label
`23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40`.

| Input | SHA-256 |
|---|---|
| JIT F1 consumido | `e4a651f47322cec8a9d7551a93b40186d2c25089215aa1b7b8c87a4263c2547f` |
| Runner F1 | `3249cdfed8043dfd751074ec0d844d6a9a88f14328b144f10d93c41cbbb446e0` |
| Sidecar F1 | `23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40` |
| Source manifest S1 | `ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d` |
| Evidencia F1 | `c28338c811b305428126ea7bea9fa5d4f9f9e3cfd09e8a26aeb370f032a41913` |
| Atestación aprobación F1 | `9f0027bb3b6ec85347349f3dace69952719d2931f10de5b47f76e753828e9626` |

Candidato `/home/romel/src/studiamatch-h3req1-sync-20261002`, rama
`feat/h3req1-sync-20261002`, HEAD `4eb4d877a50b012bb630a129bd0c74482c33be9c`.

## Operación permitida

- Preflight local de branch/HEAD/hashes/evidencia y Docker context; exigir Unix socket local
  y comparar `stat`/`realpath`. Sin endpoint override.
- Una consulta `docker inspect --type container --format` al ID literal indicado. stdout
  máximo 8 KiB, stderr descartado, timeout 10 s. Solo lee ID/nombre/estado/exit/OOM, tres
  labels F1, red, rootfs read-only, usuario, capabilities/security options, RAM/swap/CPU/PIDs,
  restart, tmpfs/count, logging, puertos, shm, HostConfig Binds y Mounts.
- Comparar valores contra el contrato pre-start de F1 y escribir únicamente resultado
  PASS/NO-GO y nombres de campos discrepantes en evidencia nueva. No imprimir ni persistir
  metadata raw, IDs/nombre/nonce del recurso, valores observados, mounts/paths, env, command,
  `.State.Error` ni datos de filesystem.
- Evidencia nueva: `.context/evidencia/h3req1_c03_source_snapshot_f2_metadata_read_2026-10-07.md`,
  debe no existir y no ser symlink.

## Exclusiones y salvaguardas

No `logs`, `exec`, Env/command/image history, `.State.Error`, filesystem, `create`, `start`,
`wait`, `stop`, `rm`, cleanup, retry, consulta por nombre/u otro ID, red, npm/workerd/Pages,
DB/SQL/Auth/Supabase, otros recursos, push/PR/merge/deploy. El F1 JIT está consumido; no
repetir F1. F2 es una sola lectura de metadata; cualquier error/timeout/parser mismatch
consume el permiso sin reintento.

La lectura es read-only, pero la misma cuenta con acceso al daemon puede invocar Docker
directamente. Además, Docker Engine entrega al CLI el objeto de inspección completo antes de
aplicar `--format`; el cliente procesa internamente metadata fuera de la allowlist aunque el
runner solo parsea campos seleccionados y nunca persiste/imprime raw. **Residual MEDIUM y
waiver propuesto, NO aprobado:** causa/evidencia reproducible: comportamiento de la API
container-inspect de Docker y comando `docker inspect --format` del bloque siguiente; el
formato limita la salida, no el objeto recibido por el CLI. Mitigación: una sola consulta al
ID literal, output limitado, stderr descartado, sin campos raw ni paths en el reporte, sin
filesystem ni acciones mutantes. Owner: Romel, responsable humano del proyecto y titular
operativo del checkout/Docker local. Riesgo: procesamiento transitorio en memoria de campos
no usados y bypass local same-user; no hay persistencia, publicación ni operación remota.
Expiración: tras la única lectura F2 o cancelación de esta solicitud. La aprobación humana
debe aceptar explícitamente ambos residuales o F2 no se ejecutará.

## Comando exacto — solo tras aprobación humana de este JIT

```bash
/usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME="${HOME:?HOME is required for the selected local Docker context}" LANG=C LC_ALL=C \
  /usr/bin/timeout --signal=TERM --kill-after=10s 45s \
  /bin/bash -Eeuo pipefail <<'H3_C03_SOURCE_SNAPSHOT_F1_METADATA_F2'
set -Eeuo pipefail
readonly ROOT_EXPECTED='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH_EXPECTED='feat/h3req1-sync-20261002'
readonly HEAD_EXPECTED='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly ID_EXPECTED='54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9'
readonly NAME_EXPECTED='h3req1-c03-source-snapshot-f1-20261007'
readonly NONCE_EXPECTED='552890-0-28538'
readonly JIT_EXPECTED='H3-CLOSE-03-SOURCE-SNAPSHOT-F1-2026-10-07'
readonly MANIFEST_EXPECTED='23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40'
readonly F1_JIT='.context/operaciones/manifiesto_jit_h3_close03_source_snapshot_2026-10-07_f1.md'
readonly F1_RUNNER='tests/h3req1_c03_source_snapshot_f1.sh'
readonly F1_SIDECAR='tests/h3req1-c03-source-snapshot-f1.sha256'
readonly SOURCE='tests/h3req1-c03-startup-source-s1.sha256'
readonly F1_EVIDENCE='.context/evidencia/h3req1_c03_source_snapshot_2026-10-07_f1.md'
readonly F1_APPROVAL='.context/evidencia/h3req1_c03_source_snapshot_f1_approval_2026-10-07.md'
readonly REPORT='.context/evidencia/h3req1_c03_source_snapshot_f2_metadata_read_2026-10-07.md'
readonly STARTED_AT="$SECONDS"
report_open=false
report_complete=false
die() {
  if [[ "$report_open" == true ]]; then
    printf 'metadata-result=NO-GO|mismatch-fields=preflight\nraw-metadata=discarded|resource-preserved=true\n' >&2
    report_complete=true
  else
    printf 'NO-GO: %s\n' "$1" >&2
  fi
  exit 1
}
on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$report_open" == true && "$report_complete" != true ]]; then
    printf 'metadata-result=NO-GO|mismatch-fields=unexpected-exit\nraw-metadata=discarded|resource-preserved=true\n' >&2
    status=1
  fi
  exit "$status"
}
trap on_exit EXIT
local_control() {
  local maximum=$1 remaining
  shift
  remaining=$((45 - (SECONDS - STARTED_AT)))
  (( remaining > 0 )) || return 124
  (( remaining > maximum )) && remaining=$maximum
  timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" "$@"
}
hash_of() {
  local line
  line="$(local_control 5 sha256sum -- "$1")" || return 1
  printf '%s' "${line%% *}"
}
root="$(local_control 5 realpath -e -- .)" || die 'cannot resolve checkout'
[[ "$root" == "$ROOT_EXPECTED" ]] || die 'unexpected checkout root'
[[ "$(local_control 5 git rev-parse --show-toplevel)" == "$ROOT_EXPECTED" ]] || die 'checkout root differs'
[[ "$(local_control 5 git branch --show-current)" == "$BRANCH_EXPECTED" ]] || die 'branch differs'
[[ "$(local_control 5 git rev-parse HEAD)" == "$HEAD_EXPECTED" ]] || die 'HEAD differs'
for directory in tests .context .context/operaciones .context/evidencia; do
  [[ -d "$directory" && ! -L "$directory" ]] || die 'fixed input directory missing or symlinked'
  canonical_directory="$(local_control 5 realpath -e -- "$directory")" || die 'cannot resolve fixed input directory'
  [[ "$canonical_directory" == "$ROOT_EXPECTED/$directory" ]] || die 'fixed input directory escapes checkout'
done
evidence_dir="$(local_control 5 realpath -e -- .context/evidencia)" || die 'cannot resolve evidence directory'
[[ "$evidence_dir" == "$ROOT_EXPECTED/.context/evidencia" ]] || die 'unexpected evidence directory'
for path in "$F1_JIT" "$F1_RUNNER" "$F1_SIDECAR" "$SOURCE" "$F1_EVIDENCE" "$F1_APPROVAL"; do
  [[ -f "$path" && ! -L "$path" ]] || die 'fixed F1 evidence missing or symlinked'
done
[[ ! -e "$REPORT" && ! -L "$REPORT" ]] || die 'F2 evidence already exists or is symlinked'
[[ "$(hash_of "$F1_JIT")" == e4a651f47322cec8a9d7551a93b40186d2c25089215aa1b7b8c87a4263c2547f ]] || die 'F1 JIT hash differs'
[[ "$(hash_of "$F1_RUNNER")" == 3249cdfed8043dfd751074ec0d844d6a9a88f14328b144f10d93c41cbbb446e0 ]] || die 'F1 runner hash differs'
[[ "$(hash_of "$F1_SIDECAR")" == 23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40 ]] || die 'F1 sidecar hash differs'
[[ "$(hash_of "$SOURCE")" == ae335c8e197d2c380bc877abbd53aa9f52a30f2b00e3310865bccb64ecb17c5d ]] || die 'source manifest hash differs'
[[ "$(hash_of "$F1_EVIDENCE")" == c28338c811b305428126ea7bea9fa5d4f9f9e3cfd09e8a26aeb370f032a41913 ]] || die 'F1 evidence hash differs'
[[ "$(hash_of "$F1_APPROVAL")" == 9f0027bb3b6ec85347349f3dace69952719d2931f10de5b47f76e753828e9626 ]] || die 'F1 approval attestation hash differs'
grep -Fxq 'Decision: accept waiver and approve one F1 execution.' "$F1_APPROVAL" || die 'F1 approval attestation marker differs'
grep -Fxq "container-created-id=$ID_EXPECTED" "$F1_EVIDENCE" || die 'fixed container ID absent from F1 evidence'
grep -Fxq "run-nonce=$NONCE_EXPECTED" "$F1_EVIDENCE" || die 'fixed nonce absent from F1 evidence'

unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH
context="$(local_control 5 docker context show 2>/dev/null)" || die 'cannot read Docker context'
[[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || die 'Docker context schema invalid'
endpoint_json="$(local_control 5 docker context inspect --format '{{json (index .Endpoints "docker").Host}}' "$context" 2>/dev/null)" || die 'cannot read context endpoint'
[[ "$endpoint_json" =~ ^\"unix:///[A-Za-z0-9_./-]+\"$ ]] || die 'Docker endpoint is not a local Unix socket'
socket="${endpoint_json#\"unix://}"
socket="${socket%\"}"
socket_identity="$(local_control 2 stat -Lc '%F|%d:%i:%u:%g:%a' -- "$socket" 2>/dev/null)" || die 'cannot stat Docker socket'
[[ "$socket_identity" =~ ^socket\|[0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4}$ ]] || die 'endpoint is not a socket'
canonical_socket="$(local_control 2 realpath -e -- "$socket" 2>/dev/null)" || die 'cannot canonicalize socket'
canonical_identity="$(local_control 2 stat -Lc '%F|%d:%i:%u:%g:%a' -- "$canonical_socket" 2>/dev/null)" || die 'cannot verify canonical socket'
[[ "$canonical_identity" == "$socket_identity" ]] || die 'socket identity changed'
export DOCKER_HOST="unix://$canonical_socket"
unset DOCKER_CONTEXT

set -o noclobber
umask 077
exec >"$REPORT" 2>&1
set +o noclobber
report_open=true
readonly FORMAT='{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{.Config.User}}|{{json .HostConfig.CapDrop}}|{{json .HostConfig.SecurityOpt}}|{{.HostConfig.Memory}}|{{.HostConfig.MemorySwap}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.PidsLimit}}|{{.HostConfig.RestartPolicy.Name}}|{{index .HostConfig.Tmpfs "/snapshot"}}|{{len .HostConfig.Tmpfs}}|{{.HostConfig.LogConfig.Type}}|{{json .HostConfig.PortBindings}}|{{.HostConfig.ShmSize}}|{{json .HostConfig.Binds}}|{{json .HostConfig.Mounts}}'
set +e
metadata_b64="$(set -o pipefail; timeout --foreground --signal=TERM --kill-after=1s 10s docker inspect --type container --format "$FORMAT" "$ID_EXPECTED" 2>/dev/null | head -c 8193 | base64 -w0)"
inspect_status=$?
set -e
[[ "$inspect_status" -eq 0 && -n "$metadata_b64" ]] || die 'single inspect failed, timed out, or exceeded output cap'
metadata_bytes="$(printf '%s' "$metadata_b64" | base64 --decode 2>/dev/null | wc -c)" || die 'metadata decode failed'
[[ "$metadata_bytes" =~ ^[0-9]+$ ]] && (( metadata_bytes > 0 && metadata_bytes <= 8192 )) || die 'metadata exceeds 8 KiB'
metadata="$(printf '%s' "$metadata_b64" | base64 --decode 2>/dev/null)" || die 'metadata decode failed'
[[ "$metadata" != *$'\n'* && "$metadata" != *$'\r'* ]] || die 'unexpected multiline metadata'
field_count="$(awk -F '|' '{print NF}' <<< "$metadata")" || die 'metadata field count failed'
[[ "$field_count" == 25 ]] || die 'metadata schema/field count mismatch'
IFS='|' read -r id name state exit_code oom jit_label manifest_label run_label network_mode readonly_root configured_user \
  cap_drop security_opt memory memory_swap nano_cpus pids_limit restart tmpfs tmpfs_count \
  log_type port_bindings shm_size binds host_mounts <<< "$metadata"
[[ "$shm_size" =~ ^[0-9]+$ && "$tmpfs_count" =~ ^[0-9]+$ ]] || die 'metadata schema/field count mismatch'
mismatches=()
compare() { [[ "$2" == "$3" ]] || mismatches+=("$1"); }
compare id "$id" "$ID_EXPECTED"
compare name "$name" "/$NAME_EXPECTED"
compare state "$state" created
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
compare diag_tmpfs "$tmpfs" 'rw,noexec,nosuid,nodev,size=96m,uid=1001,gid=1001,mode=0700'
compare tmpfs_count "$tmpfs_count" 1
compare log_type "$log_type" none
[[ "$port_bindings" == null || "$port_bindings" == '{}' ]] || mismatches+=(port_bindings)
compare shm_size "$shm_size" 16777216
[[ "$binds" == null || "$binds" == '[]' ]] || mismatches+=(binds)
[[ "$host_mounts" == null || "$host_mounts" == '[]' ]] || mismatches+=(host_mounts)
if (( ${#mismatches[@]} == 0 )); then
  printf 'metadata-result=PASS|fields=all-prestart-controls-match\n'
else
  mismatch_csv="$(IFS=,; printf '%s' "${mismatches[*]}")"
  printf 'metadata-result=NO-GO|mismatch-fields=%s\n' "$mismatch_csv"
fi
printf 'raw-metadata=discarded|resource-preserved=true\n'
report_complete=true
H3_C03_SOURCE_SNAPSHOT_F1_METADATA_F2
```

La aprobación F2, si se concede, autoriza exclusivamente esta lectura. El JIT se consume
aunque falle la consulta o el parser. No reintentar ni ampliar alcance sin otro JIT.
