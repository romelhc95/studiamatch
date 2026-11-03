#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-SNAPSHOT-CAUSE-DIAGNOSTIC-2026-10-07-D3'
readonly RUNNER='tests/h3req1_c03_snapshot_diagnostic_d3.sh'
readonly MANIFEST='tests/h3req1-c03-snapshot-diagnostic-d3.sha256'
readonly EVIDENCE='.context/evidencia/h3req1_c03_snapshot_diagnostic_2026-10-07_d3.md'
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly CONTAINER='h3req1-c03-snapshot-diagnostic-d3-20261007'
readonly RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}"
readonly STARTED_AT="$SECONDS"
readonly MAX_WALL_SECONDS=180
readonly POST_RUN_RESERVE_SECONDS=100

phase='preflight'
report_open=false
active_container=''
stop_attempted=false
verified_exit_code=''
CONTAINER_ID=''
CREATED_CONTAINER_ID=''
created_container_id_count=0
CREATION_ID_TRUSTED=false
DOCKER_SOCKET_PATH=''
DOCKER_SOCKET_IDENTITY=''
set +m
shopt -s lastpipe
exec 3>&1

die() {
  printf 'NO-GO: %s\n' "$1" >&2
  exit 1
}

on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$status" -ne 0 && -n "$active_container" && "$stop_attempted" == false ]]; then
    printf 'failure-stop-attempt=exact-new-container-only\n'
    stop_new_container || printf 'bounded-stop=failed-or-not-performed|resource-preserved=true\n'
    active_container=''
  fi
  if [[ "$report_open" == true ]]; then
    if [[ "$status" -eq 0 ]]; then
      printf 'diagnostic-result=synthetic-comparison-complete\n' || status=96
    else
      printf 'diagnostic-result=NO-GO|phase=%s|exit=%s\n' "$phase" "$status" || status=96
    fi
  fi
  printf 'snapshot-diagnostic-exit=%s|phase=%s|evidence=%s\n' "$status" "$phase" "$EVIDENCE" >&3 \
    || status=96
  exit "$status"
}
trap on_exit EXIT

docker_socket_identity() {
  timeout --foreground --signal=TERM --kill-after=0.2s 1s \
    stat -Lc '%F|%d:%i:%u:%g:%a' -- "$1" 2>/dev/null
}

docker_socket_guard() {
  local current_socket_identity
  [[ -n "$DOCKER_SOCKET_PATH" && -n "$DOCKER_SOCKET_IDENTITY" ]] || return 125
  current_socket_identity="$(docker_socket_identity "$DOCKER_SOCKET_PATH")" || return 125
  [[ "$current_socket_identity" == "socket|$DOCKER_SOCKET_IDENTITY" ]] || return 125
}

docker_context_control() {
  local remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT)))
  (( remaining > 0 )) || return 124
  (( remaining > 20 )) && remaining=20
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
  timeout --foreground --signal=TERM --kill-after=1s "${remaining}s" docker "$@" 2>/dev/null
}

docker_control() {
  docker_control_with_limit 20 "$@"
}

stop_new_container() {
  local metadata id name state jit_label manifest_label run_label network_mode
  [[ "$stop_attempted" == false ]] || {
    printf 'bounded-stop=not-repeated|resource-preserved=true\n'
    return 1
  }
  stop_attempted=true
  [[ "$CREATION_ID_TRUSTED" == true ]] || {
    printf 'bounded-stop=not-performed|reason=create-id-not-authoritative|resource-preserved=true\n'
    return 1
  }
  [[ "$created_container_id_count" -eq 1 ]] || {
    printf 'bounded-stop=not-performed|reason=create-output-id-count-mismatch|resource-preserved=true\n'
    return 1
  }
  if [[ -z "$CONTAINER_ID" && "$created_container_id_count" -eq 1 \
    && "$CREATED_CONTAINER_ID" =~ ^[a-f0-9]{64}$ ]]; then
    CONTAINER_ID="$CREATED_CONTAINER_ID"
  fi
  [[ "$CONTAINER_ID" =~ ^[a-f0-9]{64}$ ]] || {
    printf 'bounded-stop=not-performed|reason=creation-id-unavailable|resource-preserved=true\n'
    return 1
  }
  [[ "$CONTAINER_ID" == "$CREATED_CONTAINER_ID" ]] || {
    printf 'bounded-stop=not-performed|reason=create-output-id-mismatch|resource-preserved=true\n'
    return 1
  }
  if ! metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}|{{.HostConfig.NetworkMode}}' "$CONTAINER_ID")"; then
    printf 'bounded-stop=not-performed|reason=run-created-container-inspection-failed|resource-preserved=true\n'
    return 1
  fi
  IFS='|' read -r id name state jit_label manifest_label run_label network_mode <<< "$metadata"
  [[ "$id" == "$CONTAINER_ID" && "$name" == "/$CONTAINER" \
    && "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" \
    && "$run_label" == "$RUN_NONCE" && "$network_mode" == none ]] || {
      printf 'bounded-stop=not-performed|reason=identity-mismatch|resource-preserved=true\n'
      return 1
    }
  if [[ "$state" == running ]]; then
    if ! docker_control stop --time 5 "$id"; then
      printf 'bounded-stop=failed|resource-preserved=true\n'
      return 1
    fi
    printf 'bounded-stop=completed|resource-preserved=true\n'
  else
    printf 'bounded-stop=not-needed|state=%s|resource-preserved=true\n' "$state"
  fi
}

on_signal() {
  local signal=$1 status=1
  case "$signal" in HUP) status=129 ;; INT) status=130 ;; TERM) status=143 ;; esac
  trap - HUP INT TERM
  printf 'diagnostic-interrupted=signal-%s|stop-attempted=%s\n' "$signal" "$([[ -n "$active_container" ]] && printf true || printf false)" >&3
  if [[ -n "$active_container" ]]; then
    stop_new_container || true
    active_container=''
  fi
  printf 'diagnostic-interrupted=signal-%s|resource-preserved=true\n' "$signal" >&3
  exit "$status"
}
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" \
  && "${3:-}" == '--runner-sha256' && "${5:-}" == '--manifest-sha256' && $# -eq 6 ]] \
  || die "exact JIT $JIT, runner SHA-256, and manifest SHA-256 required"
readonly APPROVED_RUNNER_SHA256="${4:-}"
readonly APPROVED_MANIFEST_SHA256="${6:-}"
[[ "$APPROVED_RUNNER_SHA256" =~ ^[a-f0-9]{64}$ ]] || die 'invalid runner SHA-256'
[[ "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] || die 'invalid manifest SHA-256'

[[ "${H3_DIAG_ROOT:-}" == /* ]] || die 'verified launcher did not provide an absolute repository root'
[[ "${H3_DIAG_VERIFIED_RUNNER_SHA256:-}" == "${4:-}" \
  && "${H3_DIAG_VERIFIED_MANIFEST_SHA256:-}" == "${6:-}" ]] \
  || die 'runner must be launched from the hash-verifying JIT wrapper'
ROOT="$(realpath -e -- "$H3_DIAG_ROOT")" || die 'cannot resolve verified repository root'
cd "$ROOT"
[[ "$(git rev-parse --show-toplevel)" == "$ROOT" ]] || die 'unexpected repository root'
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || die 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || die 'candidate baseline HEAD changed'
[[ -d tests && ! -L tests && -d .context/evidencia \
  && ! -L .context && ! -L .context/evidencia ]] || die 'test/evidence path missing or symlinked'
[[ ! -e "$EVIDENCE" && ! -L "$EVIDENCE" ]] || die 'diagnostic evidence path already exists'

set -o noclobber
exec >"$ROOT/$EVIDENCE" 2>&1
set +o noclobber
report_open=true
printf 'jit=%s\nrunner-sha256=%s\nmanifest-sha256=%s\n' \
  "$JIT" "$APPROVED_RUNNER_SHA256" "$APPROVED_MANIFEST_SHA256"
printf '# H3REQ1 snapshot diagnostic D3\n\n'
printf 'scope=synthetic-fixture-only; no candidate sources or S1/R1-R4 resources; no network, npm, workerd, DB, Edge, SQL, Auth, email, or remote\n'
printf 'candidate-branch=%s\ncandidate-head=%s\nimage=%s\ncontainer=%s\nrun-nonce=%s\n' \
  "$EXPECTED_BRANCH" "$EXPECTED_HEAD" "$NODE_IMAGE" "$CONTAINER" "$RUN_NONCE"

readonly DIAGNOSTIC_SCRIPT=$(cat <<'DIAGNOSTIC_EOF'
set -eu
fail() { printf 'diagnostic-class=%s\n' "$1"; exit "$2"; }
producer_tar_exit=not-run
receiver_same_owner_tar_exit=not-run
receiver_no_same_owner_tar_exit=not-run
report_stage_exit_codes() {
  original_status=$?
  trap - EXIT
  if ! printf 'diagnostic-stage-exits=producer:%s,receiver-same-owner:%s,receiver-no-same-owner:%s\n' \
    "$producer_tar_exit" "$receiver_same_owner_tar_exit" "$receiver_no_same_owner_tar_exit"; then
    original_status=94
  fi
  exit "$original_status"
}
trap report_stage_exit_codes EXIT
classify_error() {
  error_file=$1
  error_size="$(wc -c < "$error_file")" || return 90
  case "$error_size" in ''|*[!0-9]*) return 91 ;; esac
  test "$error_size" -le 4096 || { ERROR_CLASS=stderr-over-limit; return 92; }
  if grep -Eiq '(owner|ownership|chown).*(operation not permitted|permission denied)|(operation not permitted|permission denied).*(owner|ownership|chown)' "$error_file"; then
    ERROR_CLASS=ownership-restore-denied
    return 0
  else
    grep_status=$?
    test "$grep_status" -eq 1 || { ERROR_CLASS=error-classifier-io-failed; return 93; }
  fi
  if grep -Eiq 'no space left|disk quota' "$error_file"; then
    ERROR_CLASS=space-exhausted
    return 0
  else
    grep_status=$?
    test "$grep_status" -eq 1 || { ERROR_CLASS=error-classifier-io-failed; return 93; }
  fi
  if grep -Eiq 'permission denied|operation not permitted|read-only file system' "$error_file"; then
    ERROR_CLASS=permission-denied
    return 0
  else
    grep_status=$?
    test "$grep_status" -eq 1 || { ERROR_CLASS=error-classifier-io-failed; return 93; }
  fi
  if grep -Eiq 'not a directory|unsafe|symlink|\.\.' "$error_file"; then
    ERROR_CLASS=path-or-symlink-error
    return 0
  else
    grep_status=$?
    test "$grep_status" -eq 1 || { ERROR_CLASS=error-classifier-io-failed; return 93; }
  fi
  ERROR_CLASS=tar-error-unclassified
}
verify_free_space() {
  df -Pk /diag >/diag/space.df 2>/diag/space.err || return 1
  test ! -s /diag/space.err || return 1
  free_kib="$(awk 'NR == 2 {print $4}' /diag/space.df)" || return 1
  case "$free_kib" in ''|*[!0-9]*) return 1 ;; esac
  test "$free_kib" -ge 4096 || return 1
  printf 'diagnostic-free-kib=%s\n' "$free_kib"
}
verify_archive_hash() {
  sha256sum /diag/snapshot.tar >/diag/archive.verify.sha256 || return 1
  IFS=' ' read -r current_archive_hash _ < /diag/archive.verify.sha256 || return 1
  test "$current_archive_hash" = "$archive_hash"
}

test "$(id -u):$(id -g)" = '1001:1001' || fail receiver-uid-gid-mismatch 10
test -w /diag || fail diagnostic-tmpfs-not-writable 11
verify_free_space || fail diagnostic-space-check-failed 12
umask 022
mkdir -p /diag/source/nested /diag/default /diag/no-same-owner || fail fixture-directory-create-failed 13
printf 'fixture=synthetic-owner\n' > /diag/source/owner.txt || fail fixture-write-failed 14
printf '{"fixture":"synthetic","version":1}\n' > /diag/source/nested/data.json || fail fixture-write-failed 14
chmod 0640 /diag/source/owner.txt || fail fixture-mode-failed 15
chmod 0600 /diag/source/nested/data.json || fail fixture-mode-failed 15
chmod 0750 /diag/source/nested || fail fixture-mode-failed 15
test "$(stat -c '%u:%g' /diag/source/owner.txt)" = '1001:1001' || fail fixture-source-owner-check-failed 16
test "$(stat -c '%a' /diag/source/owner.txt)" = 640 || fail fixture-source-mode-check-failed 17
test "$(stat -c '%u:%g' /diag/source/nested/data.json)" = '1001:1001' || fail fixture-source-data-owner-check-failed 16
test "$(stat -c '%a' /diag/source/nested/data.json)" = 600 || fail fixture-source-data-mode-check-failed 17
test "$(stat -c '%u:%g' /diag/source/nested)" = '1001:1001' || fail fixture-source-directory-owner-check-failed 16
test "$(stat -c '%a' /diag/source/nested)" = 750 || fail fixture-source-directory-mode-check-failed 17
links="$(find /diag/source -type l -print -quit)" || fail fixture-symlink-scan-failed 18
test -z "$links" || fail fixture-unexpected-symlink 19
find /diag/source -mindepth 1 -printf '%P\n' >/diag/source.paths.unsorted 2>/diag/source.find.err || fail fixture-path-scan-failed 20
test ! -s /diag/source.find.err || fail fixture-path-scan-warning 20
LC_ALL=C sort /diag/source.paths.unsorted >/diag/source.paths || fail fixture-path-sort-failed 20
paths="$(cat /diag/source.paths)" || fail fixture-path-read-failed 20
test "$paths" = "$(printf 'nested\nnested/data.json\nowner.txt')" || fail fixture-path-set-mismatch 21
(cd /diag/source && sha256sum owner.txt nested/data.json > SHA256SUMS) || fail fixture-hash-create-failed 22
chmod 0644 /diag/source/SHA256SUMS || fail fixture-manifest-mode-failed 23

if tar --format=posix --numeric-owner --owner=1000 --group=1000 --no-recursion \
  -cf /diag/snapshot.tar -C /diag/source nested owner.txt nested/data.json SHA256SUMS \
  2>/diag/producer.stderr; then producer_tar_exit=0; else producer_tar_exit=$?; fi
printf 'producer-tar-exit=%s\n' "$producer_tar_exit"
if [ "$producer_tar_exit" -ne 0 ]; then
  if classify_error /diag/producer.stderr; then
    printf 'producer-class=%s\n' "$ERROR_CLASS"
  else
    printf 'producer-class=error-classifier-failed\n'
    fail producer-error-classifier-failed 24
  fi
  exit 25
fi
test ! -s /diag/producer.stderr || fail producer-tar-warning 26
sha256sum /diag/snapshot.tar >/diag/archive.sha256 || fail archive-hash-failed 27
IFS=' ' read -r archive_hash _ < /diag/archive.sha256 || fail archive-hash-read-failed 27
case "$archive_hash" in ''|*[!a-f0-9]*) fail archive-hash-invalid 28 ;; esac
test "${#archive_hash}" -eq 64 || fail archive-hash-invalid 28
archive_bytes="$(stat -c '%s' /diag/snapshot.tar)" || fail archive-size-check-failed 29
case "$archive_bytes" in ''|*[!0-9]*) fail archive-size-invalid 30 ;; esac
test "$archive_bytes" -le 1048576 || fail archive-over-limit 31
printf 'archive-bytes=%s\narchive-sha256=%s\n' "$archive_bytes" "$archive_hash"

members="$(tar -tf /diag/snapshot.tar 2>/diag/list.stderr)" || fail archive-list-failed 32
test ! -s /diag/list.stderr || fail archive-list-warning 33
expected_members="$(printf 'nested/\nowner.txt\nnested/data.json\nSHA256SUMS')"
test "$members" = "$expected_members" || fail archive-path-allowlist-mismatch 34
if tar --numeric-owner -tvf /diag/snapshot.tar >/diag/archive.verbose 2>/diag/verbose.stderr; then :; else fail archive-metadata-read-failed 35; fi
test ! -s /diag/verbose.stderr || fail archive-metadata-warning 36
if awk '$2 == "1000/1000" { count++ } END { print count + 0 }' \
  /diag/archive.verbose >/diag/archive.owner-count 2>/diag/archive.owner-count.err; then :; else
  fail archive-owner-check-failed 37
fi
test ! -s /diag/archive.owner-count.err || fail archive-owner-check-failed 37
owner_count="$(cat /diag/archive.owner-count)" || fail archive-owner-count-read-failed 37
test "$owner_count" -eq 4 || fail archive-owner-metadata-mismatch 38
printf 'archive-owner-metadata=1000:1000,entries=%s\n' "$owner_count"

# Explicit --same-owner reproduces the ownership-restore request without running as root.
if tar --same-owner -xf - -C /diag/default < /diag/snapshot.tar 2>/diag/default.stderr; then
  default_tar_exit=0
  default_class=PASS
else
  default_tar_exit=$?
  if classify_error /diag/default.stderr; then
    default_class="$ERROR_CLASS"
  else
    default_class=error-classifier-failed
  fi
fi
receiver_same_owner_tar_exit="$default_tar_exit"
printf 'receiver-same-owner-tar-exit=%s\nreceiver-same-owner-class=%s\n' "$default_tar_exit" "$default_class"
if [ "$default_tar_exit" -eq 0 ]; then
  test ! -s /diag/default.stderr || fail default-tar-warning 39
else
  test "$default_class" != error-classifier-failed || fail default-error-classifier-failed 40
fi

verify_archive_hash || fail archive-hash-changed-before-corrected-receiver 40
verify_free_space || fail diagnostic-space-check-failed 53
if tar --no-same-owner -xf - -C /diag/no-same-owner < /diag/snapshot.tar 2>/diag/fixed.stderr; then
  fixed_tar_exit=0
  fixed_class=PASS
else
  fixed_tar_exit=$?
  if classify_error /diag/fixed.stderr; then
    fixed_class="$ERROR_CLASS"
  else
    fixed_class=error-classifier-failed
  fi
fi
receiver_no_same_owner_tar_exit="$fixed_tar_exit"
printf 'receiver-no-same-owner-tar-exit=%s\nreceiver-no-same-owner-class=%s\n' "$fixed_tar_exit" "$fixed_class"
if [ "$fixed_tar_exit" -eq 0 ]; then
  test ! -s /diag/fixed.stderr || fail corrected-tar-warning 41
else
  test "$fixed_class" != error-classifier-failed || fail corrected-error-classifier-failed 42
fi

if [ "$fixed_tar_exit" -eq 0 ]; then
  links="$(find /diag/no-same-owner -type l -print -quit)" || fail corrected-symlink-scan-failed 43
  test -z "$links" || fail corrected-unexpected-symlink 44
  find /diag/no-same-owner -type f -printf '%P\n' >/diag/corrected.paths.unsorted 2>/diag/corrected.find.err || fail corrected-path-scan-failed 45
  test ! -s /diag/corrected.find.err || fail corrected-path-scan-warning 45
  LC_ALL=C sort /diag/corrected.paths.unsorted >/diag/corrected.paths || fail corrected-path-sort-failed 45
  paths="$(cat /diag/corrected.paths)" || fail corrected-path-read-failed 45
  expected_paths="$(printf 'SHA256SUMS\nnested/data.json\nowner.txt')"
  test "$paths" = "$expected_paths" || fail corrected-path-set-mismatch 46
  test "$(stat -c '%a' /diag/no-same-owner/owner.txt)" = 640 || fail corrected-owner-mode-mismatch 47
  test "$(stat -c '%a' /diag/no-same-owner/nested/data.json)" = 600 || fail corrected-data-mode-mismatch 48
  test "$(stat -c '%a' /diag/no-same-owner/nested)" = 750 || fail corrected-directory-mode-mismatch 49
  test "$(stat -c '%a' /diag/no-same-owner/SHA256SUMS)" = 644 || fail corrected-manifest-mode-mismatch 50
  test "$(stat -c '%u:%g' /diag/no-same-owner/owner.txt)" = '1001:1001' || fail corrected-owner-result-mismatch 51
  test "$(stat -c '%u:%g' /diag/no-same-owner/nested/data.json)" = '1001:1001' || fail corrected-data-owner-result-mismatch 51
  test "$(stat -c '%u:%g' /diag/no-same-owner/nested)" = '1001:1001' || fail corrected-directory-owner-result-mismatch 51
  test "$(stat -c '%u:%g' /diag/no-same-owner/SHA256SUMS)" = '1001:1001' || fail corrected-manifest-owner-result-mismatch 51
  (cd /diag/no-same-owner && sha256sum -c SHA256SUMS >/dev/null 2>&1) || fail corrected-hash-check-failed 52
  printf 'receiver-no-same-owner-paths=PASS\nreceiver-no-same-owner-symlinks=none\nreceiver-no-same-owner-permissions=PASS\nreceiver-no-same-owner-hashes=PASS\n'
fi
verify_free_space || fail diagnostic-space-check-failed 53

if [ "$default_tar_exit" -ne 0 ] && [ "$default_class" = ownership-restore-denied ] \
  && [ "$fixed_tar_exit" -eq 0 ] && [ "$fixed_class" = PASS ]; then
  printf 'hypothesis-result=fixture-confirms-owner-restore-denial-and-no-same-owner-correction\n'
  printf 'historical-s1-cause=unproven-original-output-unavailable\n'
  exit 0
fi
printf 'hypothesis-result=not-confirmed-by-fixture\n'
exit 90
DIAGNOSTIC_EOF
)

verify_local_docker_context() {
  local context endpoint endpoint_json socket socket_identity initial_socket_identity
  [[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" \
    && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] \
    || die 'Docker endpoint override rejected'
  context="$(docker_context_control show)" || die 'cannot determine Docker context'
  [[ "$context" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || die 'Docker context name outside safe schema'
  endpoint_json="$(docker_context_control inspect --format '{{json (index .Endpoints "docker").Host}}' "$context")" \
    || die 'cannot read Docker context endpoint'
  [[ "$endpoint_json" =~ ^\"unix:///[A-Za-z0-9_./-]+\"$ ]] \
    || die 'Docker context endpoint is not a plain local Unix socket path'
  endpoint="${endpoint_json:1:${#endpoint_json}-2}"
  [[ "$endpoint" == unix:///* ]] || die 'non-local Docker endpoint rejected'
  socket="${endpoint#unix://}"
  [[ "$socket" != *$'\n'* && "$socket" != *$'\r'* ]] || die 'Docker socket path contains control characters'
  socket_identity="$(docker_socket_identity "$socket")" \
    || die 'cannot inspect Docker socket type/identity within its bound'
  [[ "$socket_identity" =~ ^socket\|[0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4}$ ]] \
    || die 'Docker endpoint is not a local Unix socket with expected identity'
  initial_socket_identity="$socket_identity"
  socket="$(timeout --foreground --signal=TERM --kill-after=0.2s 1s \
    realpath -e -- "$socket" 2>/dev/null)" || die 'cannot canonicalize local Docker socket within its bound'
  [[ "$socket" == /* && "$socket" != *$'\n'* && "$socket" != *$'\r'* ]] \
    || die 'canonical Docker socket path is invalid'
  socket_identity="$(docker_socket_identity "$socket")" \
    || die 'cannot verify canonical Docker socket type/identity within its bound'
  [[ "$socket_identity" =~ ^socket\|([0-9]+:[0-9]+:[0-9]+:[0-9]+:[0-7]{3,4})$ ]] \
    || die 'canonical Docker endpoint is not a local Unix socket'
  [[ "$socket_identity" == "$initial_socket_identity" ]] \
    || die 'Docker socket identity changed during canonicalization'
  DOCKER_SOCKET_PATH="$socket"
  DOCKER_SOCKET_IDENTITY="${BASH_REMATCH[1]}"
  endpoint="unix://$DOCKER_SOCKET_PATH"
  unset DOCKER_CONTEXT
  export DOCKER_HOST="$endpoint"
  printf 'docker-context=local-unix-socket-verified\n'
}

verify_new_container() {
  local metadata id name state exit_code oom jit_label manifest_label run_label network_mode readonly_root
  local configured_user cap_drop security_opt memory memory_swap nano_cpus pids_limit restart tmpfs
  local log_type log_max_size log_max_file mount_type mount_destination port_bindings shm_size
  [[ "$CREATION_ID_TRUSTED" == true ]] || die 'Docker create ID was not independently accepted'
  [[ "$created_container_id_count" -eq 1 ]] || die 'Docker create returned more than one candidate ID'
  [[ "$CONTAINER_ID" =~ ^[a-f0-9]{64}$ ]] || die 'Docker create did not return a verifiable ID'
  [[ "$CONTAINER_ID" == "$CREATED_CONTAINER_ID" ]] || die 'container ID differs from Docker create output'
  metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{.Config.User}}|{{json .HostConfig.CapDrop}}|{{json .HostConfig.SecurityOpt}}|{{.HostConfig.Memory}}|{{.HostConfig.MemorySwap}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.PidsLimit}}|{{.HostConfig.RestartPolicy.Name}}|{{index .HostConfig.Tmpfs "/diag"}}|{{.HostConfig.LogConfig.Type}}|{{index .HostConfig.LogConfig.Config "max-size"}}|{{index .HostConfig.LogConfig.Config "max-file"}}|{{range .Mounts}}{{.Type}}|{{.Destination}}{{end}}|{{json .HostConfig.PortBindings}}|{{.HostConfig.ShmSize}}' "$CONTAINER_ID")" \
    || die 'cannot inspect the new container identified by docker run output'
  IFS='|' read -r id name state exit_code oom jit_label manifest_label run_label network_mode readonly_root \
    configured_user cap_drop security_opt memory memory_swap nano_cpus pids_limit restart tmpfs \
    log_type log_max_size log_max_file mount_type mount_destination port_bindings shm_size <<< "$metadata"
  [[ "$id" == "$CONTAINER_ID" && "$name" == "/$CONTAINER" && "$state" == exited \
    && "$exit_code" =~ ^[0-9]+$ && ( "$oom" == true || "$oom" == false ) \
    && "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" \
    && "$run_label" == "$RUN_NONCE" && "$network_mode" == none && "$readonly_root" == true \
    && "$configured_user" == '1001:1001' && "$cap_drop" == '["ALL"]' \
    && "$security_opt" == '["no-new-privileges:true"]' \
    && "$memory" == 134217728 && "$memory_swap" == 134217728 \
    && "$nano_cpus" == 500000000 && "$pids_limit" == 64 && "$restart" == no \
    && "$tmpfs" == 'rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700' \
    && "$log_type" == local && "$log_max_size" == 1m && "$log_max_file" == 1 \
    && "$mount_type" == tmpfs && "$mount_destination" == /diag \
    && "$shm_size" == 16777216 \
    && ( "$port_bindings" == null || "$port_bindings" == '{}' ) ]] \
    || die 'new diagnostic container identity, state, or controls differed from this JIT'
  verified_exit_code="$exit_code"
  printf 'container=%s|state=%s|exit=%s|oom=%s|network=none|rootfs=read-only|user=%s|cap-drop=ALL|no-new-privileges=true|memory=128m|cpus=0.5|pids=64|tmpfs=16m|shm=16m|logs=local:1m\n' \
    "$CONTAINER" "$state" "$exit_code" "$oom" "$configured_user"
  [[ "$oom" == false ]] || die 'new diagnostic container was OOM-killed'
}

sanitize_container_stream() {
  local allow_id=${1:-false} chunk='' discard_line=false read_ok emitted=0 stop_reading=false
  local over_limit_reported=false output_sink_failed=false create_output_unexpected=false
  sanitized_emit() {
    if ! printf "$@"; then output_sink_failed=true; fi
    return 0
  }
  emit_bounded() {
    if (( emitted < 64 )); then
      sanitized_emit "$@"
      emitted=$((emitted + 1))
    else
      over_limit_reported=true
    fi
  }
  emit_line() {
    local candidate=$1
    if [[ "$allow_id" == true && "$candidate" =~ ^[a-f0-9]{64}$ ]]; then
      created_container_id_count=$((created_container_id_count + 1))
      if (( created_container_id_count == 1 )); then
        CREATED_CONTAINER_ID="$candidate"
        CONTAINER_ID="$candidate"
        CREATION_ID_TRUSTED=true
        emit_bounded 'container-created-id=%s\n' "$candidate"
      else
        emit_bounded 'docker-error-class=multiple-container-id-lines\n'
        create_output_unexpected=true
        stop_reading=true
      fi
    elif [[ "$allow_id" == true ]]; then
      create_output_unexpected=true
      emit_bounded 'docker-error-class=unexpected-create-stdout\n'
      stop_reading=true
    elif [[ "$candidate" =~ ^(producer|archive|receiver|diagnostic|hypothesis|historical)-[a-z0-9_-]+=[A-Za-z0-9:._,-]{1,180}$ ]]; then
      emit_bounded '%s\n' "$candidate"
    elif [[ "${candidate,,}" =~ (name.*already[[:space:]]in[[:space:]]use|name[[:space:]]conflict|conflict) ]]; then
      emit_bounded 'docker-error-class=container-name-conflict\n'
    elif [[ "${candidate,,}" =~ (no[[:space:]]space[[:space:]]left|disk[[:space:]]quota) ]]; then
      emit_bounded 'docker-error-class=space-exhausted\n'
    elif [[ "${candidate,,}" =~ (permission[[:space:]]denied|operation[[:space:]]not[[:space:]]permitted) ]]; then
      emit_bounded 'docker-error-class=permission-denied\n'
    elif [[ "${candidate,,}" =~ (cannot[[:space:]]connect[[:space:]]to[[:space:]]the[[:space:]]docker[[:space:]]daemon|error[[:space:]]during[[:space:]]connect|connection[[:space:]]refused) ]]; then
      emit_bounded 'docker-error-class=daemon-unavailable\n'
    elif [[ "${candidate,,}" =~ (no[[:space:]]such[[:space:]]image|manifest[[:space:]]unknown|pull[[:space:]]access[[:space:]]denied) ]]; then
      emit_bounded 'docker-error-class=image-unavailable\n'
    elif [[ "${candidate,,}" =~ ^docker:|^error[[:space:]]response[[:space:]]from[[:space:]]daemon ]]; then
      emit_bounded 'docker-error-class=unclassified\n'
    else
      emit_bounded 'diagnostic-output=suppressed\n'
    fi
  }
  while :; do
    chunk=''
    if IFS= read -r -n 513 chunk; then read_ok=true; else read_ok=false; fi
    if [[ "$discard_line" == true ]]; then
      if (( ${#chunk} < 513 )); then discard_line=false; fi
    elif (( ${#chunk} >= 513 )); then
      if [[ "$allow_id" == true ]]; then
        create_output_unexpected=true
        stop_reading=true
      fi
      emit_bounded 'diagnostic-output=long-line-suppressed\n'
      discard_line=true
    elif [[ "$read_ok" == true || -n "$chunk" ]]; then
      emit_line "$chunk"
    fi
    [[ "$stop_reading" == false ]] || break
    [[ "$read_ok" == true ]] || break
  done
  if [[ "$allow_id" == true && "$created_container_id_count" -ne 1 ]]; then
    create_output_unexpected=true
  fi
  [[ "$over_limit_reported" == false && "$output_sink_failed" == false \
    && "$create_output_unexpected" == false ]] || return 1
}

capture_wait_status() {
  local status_hex='' status_bytes='' byte
  WAIT_OUTPUT=''
  status_hex="$(dd bs=1 count=5 status=none 2>/dev/null | od -An -v -tx1 2>/dev/null | tr -d ' \n' 2>/dev/null)" \
    || return 1
  [[ "$status_hex" =~ ^((3[0-9]){1,3})0a$ ]] || return 1
  status_bytes="${BASH_REMATCH[1]}"
  while [[ -n "$status_bytes" ]]; do
    byte="${status_bytes:0:2}"
    WAIT_OUTPUT+="$((16#$byte - 48))"
    status_bytes="${status_bytes:2}"
  done
  [[ "$WAIT_OUTPUT" =~ ^[0-9]{1,3}$ ]] && (( 10#$WAIT_OUTPUT <= 255 ))
}

verify_local_docker_context
image_volumes="$(docker_control image inspect --format '{{json .Config.Volumes}}' "$NODE_IMAGE")" \
  || die 'pinned Node image is not local or inspect failed; pulls are forbidden'
[[ -z "$image_volumes" || "$image_volumes" == null || "$image_volumes" == '{}' ]] \
  || die 'pinned image declares volumes; no container will be created'

phase='one-new-offline-synthetic-diagnostic-container'
remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT)))
remaining=$((remaining - POST_RUN_RESERVE_SECONDS - 5))
(( remaining > 0 )) || die 'insufficient wall-clock budget to launch safely with inspection/stop reserve'
(( remaining > 20 )) && remaining=20
CREATED_CONTAINER_ID=''
created_container_id_count=0
active_container="$CONTAINER"
set +e
  docker_control_with_limit "$remaining" run --detach \
  --pull=never --platform linux/amd64 --name "$CONTAINER" --network none \
  --log-driver local --log-opt max-size=1m --log-opt max-file=1 --restart=no \
  --read-only --cpus=0.5 --memory=128m --memory-swap=128m --shm-size=16m --pids-limit=64 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  --tmpfs /diag:rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700 --user 1001:1001 \
  --label "com.studiamatch.h3.snapshot.jit=$JIT" \
  --label "com.studiamatch.h3.snapshot.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.snapshot.run=$RUN_NONCE" \
  --env LC_ALL=C --env LANG=C \
  "$NODE_IMAGE" sh -c "$DIAGNOSTIC_SCRIPT" | sanitize_container_stream true
pipeline_status=("${PIPESTATUS[@]}")
set -e
container_create_status="${pipeline_status[0]}"
output_filter_status="${pipeline_status[1]}"
if [[ "$output_filter_status" -ne 0 ]]; then
  if [[ "$created_container_id_count" -eq 1 && "$CREATED_CONTAINER_ID" =~ ^[a-f0-9]{64}$ ]]; then
    CREATION_ID_TRUSTED=true
    CONTAINER_ID="$CREATED_CONTAINER_ID"
  fi
  die 'bounded output sanitizer failed; preserve resource'
fi
if [[ "$container_create_status" -ne 0 \
  && "$container_create_status" -ne 124 && "$container_create_status" -ne 137 \
  && "$container_create_status" -ne 143 && "$container_create_status" -ne 129 \
  && "$container_create_status" -ne 130 ]]; then
  if [[ "$created_container_id_count" -eq 1 && "$CREATED_CONTAINER_ID" =~ ^[a-f0-9]{64}$ ]]; then
    CREATION_ID_TRUSTED=true
    CONTAINER_ID="$CREATED_CONTAINER_ID"
    stop_new_container || printf 'bounded-stop=failed-or-not-performed|resource-preserved=true\n'
  fi
  active_container=''
  die 'Docker create/start failed; only an ID returned by that invocation was eligible for bounded handling'
fi
[[ "$created_container_id_count" -eq 1 && "$CREATED_CONTAINER_ID" =~ ^[a-f0-9]{64}$ ]] \
  || die 'Docker create/start did not return exactly one full container ID; no resource inspected'
CREATION_ID_TRUSTED=true
CONTAINER_ID="$CREATED_CONTAINER_ID"
active_container="$CONTAINER"
if [[ "$container_create_status" -ne 0 ]]; then
  stop_new_container || printf 'bounded-stop=failed-or-not-performed|resource-preserved=true\n'
  active_container=''
  die 'Docker create/start timed out after returning a verifiable ID'
fi
printf 'container-create-status=0|container-id=%s\n' "$CONTAINER_ID"

phase='wait-for-new-diagnostic-container'
remaining=$((MAX_WALL_SECONDS - (SECONDS - STARTED_AT) - POST_RUN_RESERVE_SECONDS))
(( remaining > 60 )) && remaining=60
(( remaining > 0 )) || die 'no remaining wait budget; stopping the verified new container'
set +e
docker_control_with_limit "$remaining" wait "$CONTAINER_ID" | capture_wait_status
wait_pipeline_status=("${PIPESTATUS[@]}")
set -e
wait_command_status="${wait_pipeline_status[0]}"
wait_filter_status="${wait_pipeline_status[1]}"
if [[ "$wait_command_status" -ne 0 || "$wait_filter_status" -ne 0 ]]; then
  stop_new_container || printf 'bounded-stop=failed-or-not-performed|resource-preserved=true\n'
  active_container=''
  die 'bounded docker wait failed, timed out, or returned unexpected output; new container preserved'
fi
wait_output="$WAIT_OUTPUT"
[[ "$wait_output" =~ ^[0-9]{1,3}$ ]] && (( 10#$wait_output <= 255 )) \
  || die 'docker wait returned an invalid exit status'
printf 'container-wait-status=%s|container-id=%s\n' "$wait_output" "$CONTAINER_ID"

verify_new_container
[[ "$wait_output" == "$verified_exit_code" ]] || die 'docker wait and inspected container exit differ'
phase='read-sanitized-logs-from-new-container'
set +e
docker_control logs --tail 64 "$CONTAINER_ID" | sanitize_container_stream
logs_pipeline_status=("${PIPESTATUS[@]}")
set -e
[[ "${logs_pipeline_status[0]}" -eq 0 && "${logs_pipeline_status[1]}" -eq 0 ]] \
  || die 'could not read bounded sanitized logs from the verified new container'
active_container=''
printf 'container-id=%s|container-exit=%s\n' "$CONTAINER_ID" "$verified_exit_code"
if [[ "$verified_exit_code" -ne 0 ]]; then
  printf 'NO-GO: synthetic-comparison-did-not-confirm-the-expected-mechanism\n' >&2
  exit "$verified_exit_code"
fi
printf 'resources=single-new-container-preserved; no-cleanup-no-retry\n'
phase='complete'
