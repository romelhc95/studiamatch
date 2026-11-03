#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-F1-DAEMON-METADATA-DIAGNOSTIC-2026-10-08-F2D'
readonly JIT_FILE='.context/operaciones/manifiesto_jit_h3_close03_f1_diagnostic_f2d_2026-10-08.md'
readonly RUNNER='tests/h3req1_c03_f1_diagnostic_f2d.sh'
readonly SIDECAR='tests/h3req1-c03-f1-diagnostic-f2d.sha256'
readonly INPUTS='tests/h3req1-c03-f1-diagnostic-f2d-inputs.sha256'
readonly PEER_CHECK='tests/h3req1_c03_docker_daemon_identity_f2d.py'
readonly PROJECTION='tests/h3req1_c03_docker_inspect_projection.sh'
readonly REPORT='.context/evidencia/h3req1_c03_f1_daemon_diagnostic_f2d_2026-10-08.md'
readonly F1_ID='54d0ad11fb6a7e0b91ffa59538958407e36cee79fc875d8446ac7b1e1bf67dd9'
readonly F1_NAME='h3req1-c03-source-snapshot-f1-20261007'
readonly F1_JIT='H3-CLOSE-03-SOURCE-SNAPSHOT-F1-2026-10-07'
readonly F1_LABEL='23d676776ce7fb95001576315d39913425756ea388809eed199dab4c0260af40'
readonly F1_NONCE='552890-0-28538'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'

phase=preflight
report_open=false
report_complete=false
socket_path=''
socket_identity=''
daemon_pid=''
daemon_inode=''
exec 3>&1

fail() { printf 'NO-GO: %s\n' "$1" >&2; exit 1; }
on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$report_open" == true && "$report_complete" != true ]]; then
    printf 'diagnostic-result=NO-GO|phase=%s|exit=%s|raw-metadata=discarded|F1-resource=preserved\n' \
      "$phase" "$status" >&2 || status=1
  fi
  printf 'f1-diagnostic-exit=%s|phase=%s|report=%s\n' "$status" "$phase" "$REPORT" >&3 || status=1
  exit "$status"
}
trap on_exit EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

hash_of() {
  local output
  output="$(timeout --foreground --signal=TERM --kill-after=1s 5s sha256sum -- "$1")" || return 1
  printf '%s' "$output" | cut -d ' ' -f 1
}
no_go() {
  printf 'diagnostic-result=NO-GO|phase=%s|reason=%s|raw-metadata=discarded|F1-resource=preserved\n' \
    "$phase" "$1"
  report_complete=true
  exit 1
}
capture_docker() {
  local cap=$1 encoded status size
  shift
  set +e
  encoded="$(set -o pipefail; timeout --foreground --signal=TERM --kill-after=1s 10s docker "$@" 2>/dev/null \
    | head -c "$((cap + 1))" | base64 -w0)"
  status=$?
  set -e
  [[ "$status" -eq 0 && -n "$encoded" ]] || return 1
  size="$(printf '%s' "$encoded" | base64 --decode 2>/dev/null | wc -c)" || return 1
  [[ "$size" =~ ^[0-9]+$ ]] && (( size > 0 && size <= cap )) || return 1
  printf '%s' "$encoded" | base64 --decode 2>/dev/null
}
peer_proof() {
  local current peer reason found_pid found_inode
  LAST_PEER_REASON='peer-proof-failed'
  current="$(stat -Lc '%F|%d:%i:%u:%g:%a' -- "$socket_path" 2>/dev/null)" || return 1
  [[ "$current" == "socket|$socket_identity" ]] || return 1
  if ! peer="$(timeout --foreground --signal=TERM --kill-after=1s 5s python3 "$PEER_CHECK" \
    "$socket_path" "$selected_socket_path" 2>/dev/null)"; then
    reason="${peer#daemon-proof=NO-GO|reason=}"
    [[ "$reason" =~ ^[a-z0-9-]{1,80}$ ]] || reason='peer-proof-helper-failed'
    LAST_PEER_REASON="$reason"
    return 1
  fi
  [[ "$peer" =~ ^daemon-proof=PASS\|pid=([0-9]+)\|process=dockerd\|exe=dockerd\|uid=[0-9]+\|pid-namespace=local\|exe-owner=root\|exe-group-world-writable=false\|socket-inode=([0-9]+)$ ]] || {
    LAST_PEER_REASON='peer-proof-output-invalid'
    return 1
  }
  found_pid="${BASH_REMATCH[1]}"
  found_inode="${BASH_REMATCH[2]}"
  [[ "$found_inode" == "$daemon_inode" ]] || {
    LAST_PEER_REASON='peer-socket-inode-changed'
    return 1
  }
  [[ -z "$daemon_pid" || "$daemon_pid" == "$found_pid" ]] || {
    LAST_PEER_REASON='peer-process-changed'
    return 1
  }
  daemon_pid="$found_pid"
  LAST_PEER_REASON='pass'
}

[[ "$#" -eq 8 && "$1" == --jit && "$2" == "$JIT" \
  && "$3" == --runner-sha256 && "$5" == --sidecar-sha256 \
  && "$7" == --inputs-sha256 ]] || fail "exact JIT $JIT and three approved hashes required"
runner_hash="$4"
sidecar_hash="$6"
inputs_hash="$8"
for hash in "$runner_hash" "$sidecar_hash" "$inputs_hash"; do
  [[ "$hash" =~ ^[a-f0-9]{64}$ ]] || fail 'approved hash schema invalid'
done

root="$(realpath -e -- .)" || fail 'cannot resolve checkout'
[[ "$root" == /home/romel/src/studiamatch-h3req1-sync-20261002 ]] || fail 'unexpected checkout'
[[ "$(git rev-parse --show-toplevel)" == "$root" ]] || fail 'checkout root differs'
[[ "$(git branch --show-current)" == "$BRANCH" ]] || fail 'branch differs'
[[ "$(git rev-parse HEAD)" == "$HEAD" ]] || fail 'HEAD differs'
[[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" \
  && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] || fail 'Docker overrides rejected'
[[ -d .context/evidencia && ! -L .context && ! -L .context/evidencia ]] || fail 'evidence path missing or symlinked'
[[ ! -e "$REPORT" && ! -L "$REPORT" ]] || fail 'report exists or is symlinked'
for file in "$JIT_FILE" "$RUNNER" "$SIDECAR" "$INPUTS" "$PEER_CHECK" "$PROJECTION" \
  .context/evidencia/h3req1_c03_source_snapshot_2026-10-07_f1.md \
  .context/evidencia/h3req1_c03_f1_daemon_diagnostic_f2b_2026-10-08.md \
  .context/evidencia/h3req1_c03_f1_daemon_diagnostic_f2c_2026-10-08.md; do
  [[ -f "$file" && ! -L "$file" ]] || fail "fixed input missing or symlinked: $file"
done
[[ "$(hash_of "$RUNNER")" == "$runner_hash" ]] || fail 'runner hash mismatch'
jit_hash="$(hash_of "$JIT_FILE")" || fail 'JIT hash read failed'
[[ "$(hash_of "$SIDECAR")" == "$sidecar_hash" ]] || fail 'runner sidecar hash mismatch'
[[ "$(hash_of "$INPUTS")" == "$inputs_hash" ]] || fail 'input manifest hash mismatch'
[[ "$(cat "$SIDECAR")" == "$runner_hash  $RUNNER" ]] || fail 'sidecar does not pin runner'
sha256sum --check "$INPUTS" >/dev/null 2>&1 || fail 'input manifest check failed'
source "$PROJECTION"

umask 077
set -o noclobber
exec >"$REPORT" 2>&1
set +o noclobber
report_open=true
printf '# H3REQ1 F1 daemon and metadata diagnostic F2d\n\n'
printf 'jit=%s\njit-sha256=%s\nrunner-sha256=%s\ninputs-sha256=%s\n' "$JIT" "$jit_hash" "$runner_hash" "$inputs_hash"
printf 'candidate=%s|branch=%s|head=%s\n' "$root" "$BRANCH" "$HEAD"
printf 'resource-id=%s|name=%s|nonce=%s\n' "$F1_ID" "$F1_NAME" "$F1_NONCE"
printf 'scope=SO_PEERCRED direct-local-daemon proof; one pinned-image-ID read; one exact-F1 inspect\n'
printf 'mutations=none|cleanup=none|retry=none|remote=none|F1-resource=preserved\n'

phase=context-config
context="$(timeout --foreground --signal=TERM --kill-after=1s 5s docker context show 2>/dev/null)" || no_go context-read-failed
[[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || no_go context-name-schema
endpoint="$(timeout --foreground --signal=TERM --kill-after=1s 5s docker context inspect --format '{{json (index .Endpoints "docker").Host}}' "$context" 2>/dev/null)" || no_go context-endpoint-read-failed
if [[ ! "$endpoint" =~ ^\"unix:///[A-Za-z0-9_./+-]+\"$ ]]; then
  printf 'endpoint-kind=not-local-unix|remote-contact=false\n'
  no_go selected-endpoint-not-local-unix
fi
selected_socket_path="$(printf '%s' "$endpoint" | sed 's/^"unix:\/\///; s/"$//')"
[[ "$selected_socket_path" =~ ^/[A-Za-z0-9_./+-]{1,240}$ ]] || no_go selected-socket-path-schema
socket_path="$(timeout --foreground --signal=TERM --kill-after=1s 2s realpath -e -- "$selected_socket_path" 2>/dev/null)" || no_go socket-canonicalization-failed
[[ "$socket_path" =~ ^/[A-Za-z0-9_./+-]{1,240}$ ]] || no_go canonical-socket-path-schema
[[ -S "$socket_path" ]] || no_go canonical-target-not-socket
selected_metadata="$(timeout --foreground --signal=TERM --kill-after=1s 2s stat -Lc '%F|%d:%i:%u:%g:%a' -- "$selected_socket_path" 2>/dev/null)" || no_go selected-socket-stat-failed
canonical_metadata="$(timeout --foreground --signal=TERM --kill-after=1s 2s stat -Lc '%F|%d:%i:%u:%g:%a' -- "$socket_path" 2>/dev/null)" || no_go canonical-socket-stat-failed
[[ "$selected_metadata" == "$canonical_metadata" ]] || no_go selected-and-canonical-socket-differ
[[ "$canonical_metadata" =~ ^socket\|([0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4})$ ]] || no_go endpoint-not-socket
socket_identity="${BASH_REMATCH[1]}"
daemon_inode="${socket_identity#*:}"
daemon_inode="${daemon_inode%%:*}"
printf 'endpoint-kind=local-unix|socket-file=verified|canonical-path=resolved|path=redacted\n'

phase=daemon-identity-proof
if ! peer_proof; then
  printf 'daemon-proof=NO-GO|reason=%s|api-requests=0\n' "$LAST_PEER_REASON"
  no_go daemon-identity-not-proven
fi
printf 'daemon-proof=PASS|process=dockerd|uid=redacted|pid-namespace=local|exe-owner=root|group-world-writable=false\n'
export DOCKER_HOST="unix://$socket_path"
unset DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH

phase=resolve-pinned-image-ID-no-pull
peer_proof || no_go "$LAST_PEER_REASON-before-image-read"
image_json="$(capture_docker 128 image inspect --format '{{json .Id}}' "$NODE_IMAGE")" || no_go pinned-image-unavailable-or-read-failed
[[ "$image_json" =~ ^\"sha256:[a-f0-9]{64}\"$ ]] || no_go image-ID-schema
image_id="$(printf '%s' "$image_json" | sed 's/^"//; s/"$//')"
printf 'pinned-image-ID=resolved-locally|pull=not-attempted\n'

phase=inspect-exact-F1-resource
peer_proof || no_go "$LAST_PEER_REASON-before-container-inspect"
format="$(h3_docker_inspect_projection_format)"
projection="$(capture_docker 8192 inspect --type container --format "$format" "$F1_ID")" || no_go exact-F1-inspect-failed
phase=compare-allowlisted-fields
if h3_compare_docker_projection "$F1_ID" "/$F1_NAME" "$F1_JIT" "$F1_LABEL" "$F1_NONCE" \
  created 0 /snapshot 'rw,noexec,nosuid,nodev,size=96m,uid=1001,gid=1001,mode=0700' \
  none "$image_id" "$projection"; then
  printf 'metadata-result=PASS|mismatch-fields=none\n'
else
  compare_status=$?
  if [[ "$compare_status" -eq 1 ]]; then
    printf 'metadata-result=control-mismatch|mismatch-fields=%s\n' "$CONTROL_MISMATCH_FIELDS"
  else
    printf 'metadata-result=NO-GO|parser-error=%s|raw-metadata=discarded\n' "$CONTROL_SCHEMA_ERROR"
  fi
fi
printf 'image-check=container-immutable-ID-vs-local-pinned-image-ID\n'
printf 'tmpfs-check=HostConfig.Tmpfs[/snapshot]|persistent-mounts=HostConfig.Mounts-and-Mounts\n'
printf 'peer-proof=Linux-SO_PEERCRED direct kernel credentials; no /proc listener-FD scan\n'
printf 'image-inspect=1|F1-container-inspect=1|logs=0|exec=0|mutations=0|cleanup=0|retry=0\n'
printf 'projection-cap=8192-bytes|image-ID-cap=128-bytes|stderr=discarded|raw-output=discarded\n'
printf 'residual=full-inspect-object-transits-Docker-CLI-memory-before-formatting\n'
printf 'diagnostic-result=COMPLETE|F1-resource-preserved=true\n'
report_complete=true
