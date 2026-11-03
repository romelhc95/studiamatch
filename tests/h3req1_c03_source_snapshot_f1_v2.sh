#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-SOURCE-SNAPSHOT-F1-PROJECTION-V2-2026-10-10'
readonly RUNNER='tests/h3req1_c03_source_snapshot_f1_v2.sh'
readonly SIDECAR='tests/h3req1-c03-source-snapshot-f1-v2.sha256'
readonly EVIDENCE='.context/evidencia/h3req1_c03_source_snapshot_2026-10-10_v2.md'
readonly PROJECTION_HELPER='tests/h3req1_c03_source_snapshot_projection_v2.sh'
readonly PROJECTION_HELPER_SHA256='7be1caec879e7e22db6da8c10a0623f254ec329e101ed675b7928803cba005f6'
readonly SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v2.sha256'
readonly SOURCE_MANIFEST_SHA256='e2436719f0d164f4bf93c2dcd3a5b89014621f6f54a76316bb86a4470b7c542c'
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly CONTAINER='h3req1-c03-source-snapshot-f1-v2-20261010'
readonly MAX_WALL_SECONDS=180
readonly CLEANUP_RESERVE_SECONDS=10
readonly POST_RUN_RESERVE_SECONDS=60
readonly MAX_LOCAL_OPERATION_SECONDS=5
readonly MAX_SOURCE_MANIFEST_BYTES=16384
readonly MAX_SOURCE_FILE_BYTES=4194304
readonly MAX_SOURCE_TOTAL_BYTES=8388608
readonly MAX_SNAPSHOT_TAR_BYTES=16777217
readonly STARTED_AT="$SECONDS"
readonly RUN_NONCE="${BASHPID}-${SECONDS}-${RANDOM}"

phase='preflight'
report_open=false
active_container=false
stop_attempted=false
cleanup_attempted=false
CONTAINER_ID=''
CREATED_CONTAINER_ID=''
CREATION_ID_TRUSTED=false
IDENTITY_VERIFIED=false
PRESTART_VERIFIED=false
START_ATTEMPTED=false
DOCKER_SOCKET_PATH=''
DOCKER_SOCKET_IDENTITY=''
SNAPSHOT_FILES=()
exec 3>&1

die() {
  printf 'NO-GO: %s\n' "$1" >&2
  exit 1
}

on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$status" -ne 0 && "$active_container" == true && "$cleanup_attempted" == false ]]; then
    printf 'failure-cleanup-attempt=prestart-verified-id-only\n'
    recover_and_stop_new_container || printf 'bounded-stop=not-performed-or-failed|resource-preserved=true\n'
  fi
  if [[ "$report_open" == true ]]; then
    if [[ "$status" -eq 0 ]]; then
      printf 'source-snapshot-result=PASS\n' || status=96
    else
      printf 'source-snapshot-result=NO-GO|phase=%s|exit=%s\n' "$phase" "$status" || status=96
    fi
  fi
  printf 'source-snapshot-exit=%s|phase=%s|evidence=%s\n' "$status" "$phase" "$EVIDENCE" >&3 \
    || status=96
  exit "$status"
}
trap on_exit EXIT

docker_socket_identity() {
  timeout --foreground --signal=TERM --kill-after=0.2s 1s \
    stat -Lc '%F|%d:%i:%u:%g:%a' -- "$1" 2>/dev/null
}

bounded_local() {
  local maximum_seconds=$1 remaining
  shift
  remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT)))
  (( remaining > 0 )) || return 124
  (( remaining > maximum_seconds )) && remaining=$maximum_seconds
  timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" "$@"
}

docker_socket_guard() {
  local current_identity
  [[ -n "$DOCKER_SOCKET_PATH" && -n "$DOCKER_SOCKET_IDENTITY" ]] || return 125
  current_identity="$(docker_socket_identity "$DOCKER_SOCKET_PATH")" || return 125
  [[ "$current_identity" == "socket|$DOCKER_SOCKET_IDENTITY" ]]
}

docker_context_control() {
  local remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT)))
  (( remaining > 0 )) || return 124
  (( remaining > 5 )) && remaining=5
  timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" docker context "$@" 2>/dev/null
}

docker_control_with_limit() {
  local maximum_seconds=$1
  shift
  local remaining
  docker_socket_guard || return 125
  remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT)))
  (( remaining > 0 )) || return 124
  (( remaining > maximum_seconds )) && remaining=$maximum_seconds
  # Docker CLI/daemon stderr is always discarded at this boundary.
  timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" docker "$@" 2>/dev/null
}

docker_cleanup_control_with_limit() {
  local maximum_seconds=$1
  shift
  local remaining
  docker_socket_guard || return 125
  remaining=$((MAX_WALL_SECONDS + CLEANUP_RESERVE_SECONDS - (SECONDS - STARTED_AT)))
  (( remaining > 0 )) || return 124
  (( remaining > maximum_seconds )) && remaining=$maximum_seconds
  # Recovery calls use the same raw-stderr suppression boundary.
  timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" docker "$@" 2>/dev/null
}

docker_control() {
  docker_control_with_limit 15 "$@"
}

stop_new_container() {
  [[ "$stop_attempted" == false ]] || {
    printf 'bounded-stop=not-repeated|resource-preserved=true\n'
    return 1
  }
  stop_attempted=true
  [[ "$CREATION_ID_TRUSTED" == true && "$PRESTART_VERIFIED" == true \
    && "$START_ATTEMPTED" == true \
    && "$CONTAINER_ID" =~ ^[a-f0-9]{64}$ \
    && "$CONTAINER_ID" == "$CREATED_CONTAINER_ID" ]] || {
      printf 'bounded-stop=not-performed|reason=identity-not-verified|resource-preserved=true\n'
      return 1
    }
  if docker_cleanup_control_with_limit 5 stop --time 5 "$CONTAINER_ID" >/dev/null 2>&1; then
    printf 'bounded-stop=request-completed|resource-preserved=true\n'
    return 0
  fi
  printf 'bounded-stop=request-failed|resource-preserved=true\n'
  return 1
}

on_signal() {
  local signal=$1 status=1
  case "$signal" in HUP) status=129 ;; INT) status=130 ;; TERM) status=143 ;; esac
  trap - HUP INT TERM
  printf 'snapshot-interrupted=signal-%s\n' "$signal" >&3
  if [[ "$active_container" == true ]]; then
    recover_and_stop_new_container >&3 || true
  fi
  printf 'snapshot-interrupted=signal-%s|resource-preserved=true\n' "$signal" >&3
  exit "$status"
}
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" \
  && "${3:-}" == '--runner-sha256' && "${5:-}" == '--sidecar-sha256' && $# -eq 6 ]] \
  || die "exact JIT $JIT, runner SHA-256, and sidecar SHA-256 required"
readonly APPROVED_RUNNER_SHA256="${4:-}"
readonly APPROVED_SIDECAR_SHA256="${6:-}"
[[ "$APPROVED_RUNNER_SHA256" =~ ^[a-f0-9]{64}$ \
  && "$APPROVED_SIDECAR_SHA256" =~ ^[a-f0-9]{64}$ ]] || die 'invalid approved input hash'
# These environment values are consistency checks, not an unforgeable authorization token.
[[ "${H3_SNAPSHOT_ROOT:-}" == /* \
  && "${H3_SNAPSHOT_VERIFIED_RUNNER_SHA256:-}" == "$APPROVED_RUNNER_SHA256" \
  && "${H3_SNAPSHOT_VERIFIED_SIDECAR_SHA256:-}" == "$APPROVED_SIDECAR_SHA256" ]] \
  || die 'launcher integrity inputs missing or inconsistent'

ROOT="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" realpath -e -- "$H3_SNAPSHOT_ROOT")" \
  || die 'cannot resolve candidate root within the local operation bound'
cd "$ROOT"
git_root="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" git rev-parse --show-toplevel)" \
  || die 'cannot resolve candidate checkout root within the local operation bound'
branch="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" git branch --show-current)" \
  || die 'cannot resolve candidate branch within the local operation bound'
head="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" git rev-parse HEAD)" \
  || die 'cannot resolve candidate HEAD within the local operation bound'
[[ "$ROOT" == '/home/romel/src/studiamatch-h3req1-sync-20261002' \
  && "$git_root" == "$ROOT" ]] || die 'unexpected candidate checkout'
[[ "$branch" == "$EXPECTED_BRANCH" && "$head" == "$EXPECTED_HEAD" ]] \
  || die 'candidate branch/HEAD changed'
[[ -d tests && ! -L tests && -d .context/evidencia \
  && ! -L .context && ! -L .context/evidencia ]] || die 'test/evidence path missing or symlinked'
[[ ! -e "$EVIDENCE" && ! -L "$EVIDENCE" ]] || die 'source snapshot evidence already exists'

[[ -f "$RUNNER" && ! -L "$RUNNER" && -f "$SIDECAR" && ! -L "$SIDECAR" \
  && -f "$SOURCE_MANIFEST" && ! -L "$SOURCE_MANIFEST" \
  && -f "$PROJECTION_HELPER" && ! -L "$PROJECTION_HELPER" ]] \
  || die 'fixed source/runner input missing or symlinked'
runner_bytes="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" stat -Lc '%s' -- "$RUNNER")" \
  || die 'cannot read runner size within the local operation bound'
sidecar_bytes="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" stat -Lc '%s' -- "$SIDECAR")" \
  || die 'cannot read sidecar size within the local operation bound'
projection_helper_bytes="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" stat -Lc '%s' -- "$PROJECTION_HELPER")" \
  || die 'cannot read projection helper size within the local operation bound'
[[ "$runner_bytes" =~ ^[0-9]+$ && "$runner_bytes" -le 262144 \
  && "$sidecar_bytes" =~ ^[0-9]+$ && "$sidecar_bytes" -le 512 \
  && "$projection_helper_bytes" =~ ^[0-9]+$ && "$projection_helper_bytes" -le 32768 ]] \
  || die 'runner/sidecar/helper exceeded static input bounds'
runner_hash_line="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" sha256sum -- "$RUNNER")" \
  || die 'cannot hash runner within the local operation bound'
sidecar_hash_line="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" sha256sum -- "$SIDECAR")" \
  || die 'cannot hash sidecar within the local operation bound'
runner_hash="${runner_hash_line%% *}"
sidecar_hash="${sidecar_hash_line%% *}"
[[ "$runner_hash" == "$APPROVED_RUNNER_SHA256" \
  && "$sidecar_hash" == "$APPROVED_SIDECAR_SHA256" ]] || die 'approved runner/sidecar hash mismatch'
sidecar_text="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" cat -- "$SIDECAR")" \
  || die 'cannot read sidecar within the local operation bound'
[[ "$sidecar_text" == "$APPROVED_RUNNER_SHA256  $RUNNER" ]] \
  || die 'sidecar does not pin the runner bytes'
projection_helper_hash_line="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" sha256sum -- "$PROJECTION_HELPER")" \
  || die 'cannot hash projection helper within the local operation bound'
[[ "${projection_helper_hash_line%% *}" == "$PROJECTION_HELPER_SHA256" ]] \
  || die 'projection helper hash mismatch'
# The helper path is covered by a fixed SHA-256 check immediately above.
# shellcheck disable=SC1090
source "$PROJECTION_HELPER"
manifest_bytes="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" stat -Lc '%s' -- "$SOURCE_MANIFEST")" \
  || die 'cannot read source manifest size within the local operation bound'
[[ "$manifest_bytes" =~ ^[0-9]+$ && "$manifest_bytes" -le "$MAX_SOURCE_MANIFEST_BYTES" ]] \
  || die 'source manifest exceeds its byte bound'
manifest_hash_line="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" sha256sum -- "$SOURCE_MANIFEST")" \
  || die 'cannot hash source manifest within the local operation bound'
[[ "${manifest_hash_line%% *}" == "$SOURCE_MANIFEST_SHA256" ]] \
  || die 'S1 source manifest digest changed'
manifest_lines="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" wc -l < "$SOURCE_MANIFEST")" \
  || die 'cannot count source manifest lines within the local operation bound'
manifest_lines="${manifest_lines//[[:space:]]/}"
[[ "$manifest_lines" == 13 ]] || die 'S1 source manifest must contain exactly 13 records'
bounded_local "$MAX_LOCAL_OPERATION_SECONDS" awk 'NF != 2 || length($1) != 64 || $1 !~ /^[a-f0-9]+$/ || $2 !~ /^[A-Za-z0-9._/-]+$/ \
  || $2 ~ /(^|\/)\.\.?($|\/)/ { exit 1 } END { if (NR != 13) exit 1 }' "$SOURCE_MANIFEST" \
  || die 'S1 source manifest schema/path validation failed'

source_total_bytes=0
while IFS=' ' read -r expected_hash source_path; do
  [[ -n "$expected_hash" && -n "$source_path" \
    && "$source_path" =~ ^[A-Za-z0-9._/-]+$ \
    && ${#source_path} -le 100 \
    && "$source_path" != /* && "$source_path" != '.' \
    && "/$source_path/" != *"/../"* && "/$source_path/" != *"/./"* ]] \
    || die 'source manifest contains an unsafe path'
  [[ -f "$source_path" && ! -L "$source_path" ]] || die 'a source input is missing or symlinked'
  resolved_path="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" realpath -e -- "$source_path")" \
    || die 'cannot resolve a source input within the local operation bound'
  [[ "$resolved_path" == "$ROOT/$source_path" ]] || die 'source path escapes candidate root'
  source_bytes="$(bounded_local "$MAX_LOCAL_OPERATION_SECONDS" stat -Lc '%s' -- "$source_path")" \
    || die 'cannot read source input size within the local operation bound'
  [[ "$source_bytes" =~ ^[0-9]+$ && "$source_bytes" -le "$MAX_SOURCE_FILE_BYTES" ]] \
    || die 'a source input exceeds its per-file byte bound'
  source_total_bytes=$((source_total_bytes + source_bytes))
  (( source_total_bytes <= MAX_SOURCE_TOTAL_BYTES )) || die 'source input set exceeds total byte bound'
  SNAPSHOT_FILES+=("$source_path")
done < "$SOURCE_MANIFEST"
SNAPSHOT_FILES+=("$SOURCE_MANIFEST")
sorted_snapshot_files="$(printf '%s\n' "${SNAPSHOT_FILES[@]}" \
  | bounded_local "$MAX_LOCAL_OPERATION_SECONDS" env LC_ALL=C sort -u)" \
  || die 'cannot sort the bounded snapshot path set'
mapfile -t SNAPSHOT_FILES <<< "$sorted_snapshot_files"
[[ "${#SNAPSHOT_FILES[@]}" -eq 14 ]] || die 'snapshot input set is not exactly 14 files'
bounded_local 20 \
  sha256sum --check "$SOURCE_MANIFEST" >/dev/null 2>&1 \
  || die 'source manifest inputs do not match their pinned hashes within the bound'

readonly CIDFILE="$ROOT/.context/evidencia/h3req1_c03_source_snapshot_f1_v2_${RUN_NONCE}.cid"
[[ ! -e "$CIDFILE" && ! -L "$CIDFILE" ]] || die 'unique container ID file already exists'

verify_local_docker_context() {
  local context endpoint_json endpoint socket socket_identity initial_identity
  [[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" \
    && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] \
    || die 'Docker endpoint override rejected'
  context="$(docker_context_control show)" || die 'cannot determine Docker context'
  [[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || die 'Docker context name outside safe schema'
  endpoint_json="$(docker_context_control inspect --format '{{json (index .Endpoints "docker").Host}}' "$context")" \
    || die 'cannot read Docker context endpoint'
  [[ "$endpoint_json" =~ ^\"unix:///[A-Za-z0-9_./-]+\"$ ]] \
    || die 'Docker endpoint is not a plain local Unix socket path'
  endpoint="${endpoint_json:1:${#endpoint_json}-2}"
  socket="${endpoint#unix://}"
  socket_identity="$(docker_socket_identity "$socket")" || die 'cannot inspect Docker socket'
  [[ "$socket_identity" =~ ^socket\|[0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4}$ ]] \
    || die 'Docker endpoint is not a local Unix socket'
  initial_identity="$socket_identity"
  socket="$(timeout --foreground --signal=TERM --kill-after=0.2s 1s realpath -e -- "$socket" 2>/dev/null)" \
    || die 'cannot canonicalize Docker socket'
  socket_identity="$(docker_socket_identity "$socket")" || die 'cannot verify canonical Docker socket'
  [[ "$socket_identity" == "$initial_identity" ]] || die 'Docker socket identity changed during canonicalization'
  DOCKER_SOCKET_PATH="$socket"
  DOCKER_SOCKET_IDENTITY="${socket_identity#socket|}"
  unset DOCKER_CONTEXT
  export DOCKER_HOST="unix://$DOCKER_SOCKET_PATH"
  printf 'docker-context=local-unix-socket-verified\n'
}

sanitize_snapshot_output() {
  local chunk='' read_ok count=0 failed=false
  while :; do
    chunk=''
    if IFS= read -r -n 256 chunk; then read_ok=true; else read_ok=false; fi
    if (( ${#chunk} >= 256 )); then
      printf 'container-output=long-line-suppressed\n'
      failed=true
      break
    fi
    if [[ "$read_ok" == true || -n "$chunk" ]]; then
      if [[ "$read_ok" == true \
        && "$chunk" == 'source-snapshot=PASS|files=14|source-manifest=13/13|no-same-owner=true' \
        && "$count" -eq 0 ]]; then
        printf '%s\n' "$chunk"
        count=1
      else
        printf 'container-output=suppressed\n'
        failed=true
        break
      fi
    fi
    [[ "$read_ok" == true ]] || break
  done
  [[ "$failed" == false && "$count" -eq 1 ]]
}

SNAPSHOT_SCRIPT=''
IFS= read -r -d '' SNAPSHOT_SCRIPT <<'SNAPSHOT_EOF' || [[ "$?" -eq 1 ]]
set -eu
fail() { exit "$1"; }
test "$(id -u):$(id -g)" = '1001:1001' || fail 11
test -w /snapshot || fail 12
test -z "$(find /snapshot -mindepth 1 -print -quit)" || fail 13
tar --no-same-owner -xf - -C /snapshot 2>/dev/null || fail 14
cd /snapshot || fail 15
test -z "$(find . -type l -print -quit)" || fail 16
actual_manifest_sha="$(sha256sum tests/h3req1-c03-startup-source-s1-v2.sha256 2>/dev/null)" || fail 17
actual_manifest_sha="${actual_manifest_sha%% *}"
test "$actual_manifest_sha" = "$H3_C03_SOURCE_MANIFEST_SHA256" || fail 18
sha256sum -c tests/h3req1-c03-startup-source-s1-v2.sha256 >/dev/null 2>&1 || fail 19
expected_paths="$( { awk '{print $2}' tests/h3req1-c03-startup-source-s1-v2.sha256; printf '%s\n' tests/h3req1-c03-startup-source-s1-v2.sha256; } | LC_ALL=C sort -u )" || fail 20
actual_paths="$(find . -type f -printf '%P\n' | LC_ALL=C sort)" || fail 21
test "$actual_paths" = "$expected_paths" || fail 22
file_count="$(find . -type f -printf '.' | wc -c | tr -d '[:space:]')" || fail 23
test "$file_count" = 14 || fail 24
printf 'source-snapshot=PASS|files=14|source-manifest=13/13|no-same-owner=true\n'
SNAPSHOT_EOF
readonly SNAPSHOT_SCRIPT

verify_new_container() {
  local expected_state=${1:-exited} expected_exit=${2:-0}
  local metadata
  local id name state exit_code oom jit_label manifest_label run_label network_mode readonly_root configured_user
  local cap_drop security_opt memory memory_swap nano_cpus pids_limit restart tmpfs tmpfs_count
  local log_type port_bindings shm_size binds host_mounts
  h3_source_snapshot_collect_metadata "$CONTAINER_ID" "$MAX_LOCAL_OPERATION_SECONDS" || return 1
  metadata="$H3_SOURCE_SNAPSHOT_METADATA"
  [[ -n "$metadata" && ${#metadata} -le 8192 ]] || return 1
  [[ "$metadata" != *$'\n'* && "$metadata" != *$'\r'* ]] || return 1
  IFS='|' read -r id name state exit_code oom jit_label manifest_label run_label network_mode readonly_root configured_user \
    cap_drop security_opt memory memory_swap nano_cpus pids_limit restart tmpfs tmpfs_count \
    log_type port_bindings shm_size binds host_mounts <<< "$metadata"
  [[ "$shm_size" =~ ^[0-9]+$ && "$tmpfs_count" =~ ^[0-9]+$ ]] || return 1
  if [[ "$id" == "$CONTAINER_ID" && "$name" == "/$CONTAINER" \
    && "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_SIDECAR_SHA256" \
    && "$run_label" == "$RUN_NONCE" && "$network_mode" == none ]]; then
    IDENTITY_VERIFIED=true
  else
    IDENTITY_VERIFIED=false
  fi
  [[ "$IDENTITY_VERIFIED" == true ]] || {
    printf 'container-identity=NO-GO|resource-preserved=true\n'
    return 1
  }
  [[ "$state" == "$expected_state" && "$exit_code" =~ ^[0-9]+$ && "$oom" == false \
    && "$exit_code" == "$expected_exit" && "$readonly_root" == true \
    && "$configured_user" == '1001:1001' && "$cap_drop" == '["ALL"]' \
    && "$security_opt" == '["no-new-privileges:true"]' \
    && "$memory" == 134217728 && "$memory_swap" == 134217728 \
    && "$nano_cpus" == 500000000 && "$pids_limit" == 64 && "$restart" == no \
    && "$tmpfs" == 'rw,noexec,nosuid,nodev,size=96m,uid=1001,gid=1001,mode=0700' \
    && "$tmpfs_count" == 1 && "$log_type" == none \
    && ( "$port_bindings" == null || "$port_bindings" == '{}' ) \
    && "$shm_size" == 16777216 \
    && ( "$binds" == null || "$binds" == '[]' ) \
    && ( "$host_mounts" == null || "$host_mounts" == '[]' ) ]] || {
      printf 'container-controls=NO-GO|resource-preserved=true\n'
      return 1
    }
  printf 'container-controls=PASS|state=%s|exit=%s|oom=false|network=none|rootfs=read-only|user=1001:1001|cap-drop=ALL|memory=128m|cpus=0.5|pids=64|snapshot-tmpfs=96m|shm=16m|persistent-mounts=none|logs=none\n' \
    "$state" "$exit_code"
  return 0
}

read_cidfile_bounded() {
  local cidfile_hex id_byte id_value index
  [[ -f "$CIDFILE" && ! -L "$CIDFILE" ]] || return 1
  cidfile_hex="$(bounded_local 2 bash -o pipefail -c \
    'head -c 66 -- "$1" 2>/dev/null | od -An -v -tx1 | tr -d "[:space:]"' \
    _ "$CIDFILE")" || return 1
  [[ "$cidfile_hex" =~ ^([0-9a-f]{2}){64,65}$ ]] || return 1
  if [[ "${#cidfile_hex}" -eq 130 ]]; then
    [[ "${cidfile_hex:128:2}" == 0a ]] || return 1
    cidfile_hex="${cidfile_hex:0:128}"
  fi
  [[ "${#cidfile_hex}" -eq 128 && "$cidfile_hex" =~ ^(3[0-9]|6[1-6]){64}$ ]] || return 1
  CREATED_CONTAINER_ID=''
  for ((index = 0; index < 128; index += 2)); do
    id_byte="${cidfile_hex:index:2}"
    printf -v id_value '%b' "\\x$id_byte"
    CREATED_CONTAINER_ID+="$id_value"
  done
  [[ "$CREATED_CONTAINER_ID" =~ ^[a-f0-9]{64}$ ]] || return 1
  CONTAINER_ID="$CREATED_CONTAINER_ID"
  CREATION_ID_TRUSTED=true
}

recover_and_stop_new_container() {
  [[ "$cleanup_attempted" == false ]] || return 1
  cleanup_attempted=true
  if [[ "$START_ATTEMPTED" != true ]]; then
    printf 'bounded-stop=not-needed|reason=container-never-started|resource-preserved=true\n'
    return 0
  fi
  if [[ "$CREATION_ID_TRUSTED" != true || "$PRESTART_VERIFIED" != true ]]; then
    printf 'bounded-stop=not-performed|reason=prestart-identity-not-verified|resource-preserved=true\n'
    return 1
  fi
  stop_new_container
}

verify_local_docker_context
image_volumes_b64="$(set -o pipefail; docker_control image inspect --format '{{json .Config.Volumes}}' "$NODE_IMAGE" 2>/dev/null | head -c 4097 | base64 -w0)" \
  || die 'pinned Node image is not local or image inspect failed; pulls are forbidden'
image_volumes_bytes="$(printf '%s' "$image_volumes_b64" | base64 --decode 2>/dev/null | wc -c)" \
  || die 'pinned image metadata decode failed'
[[ "$image_volumes_bytes" =~ ^[0-9]+$ ]] && (( image_volumes_bytes > 0 && image_volumes_bytes <= 4096 )) \
  || die 'pinned image volume metadata exceeded its output bound'
image_volumes="$(printf '%s' "$image_volumes_b64" | base64 --decode 2>/dev/null)" \
  || die 'pinned image volume metadata decode failed'
[[ -z "$image_volumes" || "$image_volumes" == null || "$image_volumes" == '{}' ]] \
  || die 'pinned image declares volumes; no container will be created'

phase='create-one-new-offline-source-container'
remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT) - POST_RUN_RESERVE_SECONDS))
(( remaining > 15 )) && remaining=15
(( remaining > 0 )) || die 'insufficient time budget before creating the new snapshot container'
[[ ! -e "$CIDFILE" && ! -L "$CIDFILE" ]] || die 'cidfile path collided before Docker create'
set -o noclobber
exec >"$ROOT/$EVIDENCE" 2>&1
set +o noclobber
report_open=true
printf 'jit=%s\nrunner-sha256=%s\nsidecar-sha256=%s\nprojection-helper-sha256=%s\nsource-manifest-sha256=%s\n' \
  "$JIT" "$APPROVED_RUNNER_SHA256" "$APPROVED_SIDECAR_SHA256" \
  "$PROJECTION_HELPER_SHA256" "$SOURCE_MANIFEST_SHA256"
printf '# H3REQ1 complete source snapshot validation F1\n\n'
printf 'scope=14 allowlisted files only (13 S1 inputs plus source manifest); no npm/workerd/Pages/DB/SQL/Auth/network/remotes\n'
printf 'branch=%s\nhead=%s\nimage=%s\ncontainer=%s\nrun-nonce=%s\nsource-files=%s\nsource-bytes=%s\ntar-stream-cap=%s\n' \
  "$EXPECTED_BRANCH" "$EXPECTED_HEAD" "$NODE_IMAGE" "$CONTAINER" "$RUN_NONCE" \
  "${#SNAPSHOT_FILES[@]}" "$source_total_bytes" "$MAX_SNAPSHOT_TAR_BYTES"

active_container=true
set +e
docker_control_with_limit "$remaining" create --pull=never --platform linux/amd64 \
  --attach=stdin --attach=stdout --attach=stderr --interactive \
  --cidfile "$CIDFILE" --name "$CONTAINER" --network none --log-driver none --restart=no \
  --read-only --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 --shm-size=16m \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  --tmpfs /snapshot:rw,noexec,nosuid,nodev,size=96m,uid=1001,gid=1001,mode=0700 --user 1001:1001 \
  --label "com.studiamatch.h3.snapshot.jit=$JIT" \
  --label "com.studiamatch.h3.snapshot.manifest=$APPROVED_SIDECAR_SHA256" \
  --label "com.studiamatch.h3.snapshot.run=$RUN_NONCE" \
  --env H3_C03_SOURCE_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" \
  "$NODE_IMAGE" sh -c "$SNAPSHOT_SCRIPT" >/dev/null 2>&1
create_status=$?
set -e
[[ "$create_status" -eq 0 ]] || die 'single Docker create failed; no start/retry attempted'
read_cidfile_bounded || die 'Docker create did not produce one bounded valid ID'
printf 'container-created-id=%s\ncontainer-create-status=%s\n' "$CONTAINER_ID" "$create_status"

phase='verify-created-container-identity-and-controls-before-start'
if ! verify_new_container created 0; then
  die 'created container identity/controls differed; it was not started'
fi
PRESTART_VERIFIED=true

phase='stream-allowlisted-source-to-no-same-owner-receiver'
remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT) - POST_RUN_RESERVE_SECONDS))
(( remaining > 60 )) && remaining=60
(( remaining > 0 )) || die 'insufficient time budget before streaming snapshot'
START_ATTEMPTED=true
set +e
timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" \
  tar --format=ustar --numeric-owner -C "$ROOT" --no-recursion -cf - -- "${SNAPSHOT_FILES[@]}" 2>/dev/null | \
  head -c "$MAX_SNAPSHOT_TAR_BYTES" | \
  docker_control_with_limit "$remaining" start --attach --interactive "$CONTAINER_ID" \
    2>/dev/null | sanitize_snapshot_output
pipeline_status=("${PIPESTATUS[@]}")
set -e
tar_status="${pipeline_status[0]}"
tar_bound_status="${pipeline_status[1]}"
DOCKER_START_STATUS="${pipeline_status[2]}"
filter_status="${pipeline_status[3]}"
printf 'source-tar-producer-status=%s|tar-bound-status=%s|docker-start-status=%s|output-filter-status=%s\n' \
  "$tar_status" "$tar_bound_status" "$DOCKER_START_STATUS" "$filter_status"

phase='verify-started-container-identity-and-controls'
verify_new_container exited 0 || die 'started container identity/controls/result differed'
if [[ "$tar_status" -ne 0 || "$tar_bound_status" -ne 0 \
  || "$DOCKER_START_STATUS" -ne 0 || "$filter_status" -ne 0 ]]; then
  die 'source snapshot producer, receiver, or bounded output validation failed'
fi
active_container=false
cleanup_attempted=true
printf 'resource-preservation=one-new-exited-container; no-cleanup-no-retry\n'
phase='complete'
