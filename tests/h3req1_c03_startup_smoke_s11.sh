#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S11-CURRENT-LOCKS'
readonly MANIFEST='tests/h3req1-c03-startup-smoke-s11.sha256'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s11r2.md'
readonly SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v8.sha256'
readonly SOURCE_MANIFEST_SHA256='5312e12762db37a8a2eac28658bd609d966c74dd0d210d38363cb3ebb62e209e'
readonly SOURCE_VOLUME='h3req1-c03-startup-source-20261010-s16'
readonly SNAPSHOT_CONTAINER='h3req1-c03-startup-snapshot-20261010-s16'
readonly SNAPSHOT_CONTAINER_ID='fd13e700d0853c03020ad9889f1cd6c063a320904fa1d5ecc969a28226e2f4d2'
readonly SNAPSHOT_JIT='H3-CLOSE-03-SOURCE-SNAPSHOT-S16-2026-10-10'
readonly SNAPSHOT_RUNNER='tests/h3req1_c03_source_snapshot_s16.sh'
readonly SNAPSHOT_RUNNER_SHA256='16f160c42ff1e89fd1b6daab876e2c2121cfe51e56f15716851a3c181a33a8e6'
readonly SNAPSHOT_SIDECAR='tests/h3req1-c03-source-snapshot-s16.sha256'
readonly SNAPSHOT_SIDECAR_SHA256='4b159bae0f92fa16d466d6150a6cba8b672ad2d997b15bf14f4b983d4f9bd242'
readonly SNAPSHOT_EVIDENCE='.context/evidencia/h3req1_c03_source_snapshot_2026-10-10_s16.md'
readonly SNAPSHOT_EVIDENCE_SHA256='5c9f395a911cd3b52e207d481a23e0dc4eca496eceee8514358e6159a2d9a4c9'
readonly BOOTSTRAP_FILTER='tests/h3req1_c03_bootstrap_output_filter_s1.mjs'
readonly BOOTSTRAP_FILTER_SHA256='34b99e849901809dc4754a6f677561f3e81539221946abdff90d1ed25cec1f80'
readonly OUTPUT_FILTER='tests/h3req1_c03_startup_output_filter_s8.sh'
readonly OUTPUT_FILTER_SHA256='bd0ef4154ce231d5b7b04c8a63d61947a9b3c8862950f0384da8f94f237d0ab2'
readonly PROBE_SCRIPT='tests/h3req1_c03_startup_runtime_probe_s8.mjs'
readonly PROBE_SCRIPT_SHA256='b83c62ebc49dc14c5c01b182bad45b9d46c2bd6f6e2332b83e1be6ff45478081'
readonly PRELOAD_SCRIPT='tests/h3req1_c03_startup_validation_preload_s8.cjs'
readonly PRELOAD_SCRIPT_SHA256='682b6b412f497e384ff543f73a8cff1390cfc2fc9a8e2e35893db5e6b1dbc0af'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly EXPECTED_DOCKER_CONTEXT='default'
readonly EXPECTED_DOCKER_ENDPOINT='unix:///var/run/docker.sock'
readonly EXPECTED_DOCKER_ENGINE='fc2115b2-c3c4-440e-89c6-26899eb7cb04|docker-desktop|Docker Desktop'
readonly TOOLS_VOLUME='h3req1-c03-startup-tools-20261010-s11'
readonly PAGES_VOLUME='h3req1-c03-startup-pages-20261010-s11'
readonly VOLUME_HOLDER='h3req1-c03-startup-volume-holder-20261010-s11'
readonly TOOLS_CONTAINER='h3req1-c03-startup-tools-20261010-s11'
readonly PAGES_CONTAINER='h3req1-c03-startup-pages-20261010-s11'
readonly NETWORK='h3req1-c03-startup-net-20261010-s11'
readonly RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s11'
RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"
readonly RUN_NONCE
readonly -a EMPTY_PROXY_ENV=(
  --env HTTP_PROXY= --env HTTPS_PROXY= --env FTP_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env ftp_proxy= --env all_proxy= --env no_proxy= \
  --env npm_config_proxy= --env npm_config_http_proxy= --env npm_config_https_proxy= \
  --env NPM_CONFIG_USERCONFIG=/dev/null --env npm_config_userconfig=/dev/null
)

ROOT=''
APPROVED_MANIFEST_SHA256=''
phase='preflight'
report_open=false
ACTIVE_CONTAINER=''
STOP_ATTEMPTED_CONTAINER=''
NETWORK_ID=''
VERIFIED_CONTAINER_ID=''
VERIFIED_CONTAINER_EXIT=''
exec 3>&1

fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }
docker_control() { timeout --foreground --signal=TERM --kill-after=5s 20s docker "$@" 2>/dev/null; }

stop_owned_container() {
  local name=${1:-} metadata id jit manifest run state
  case "$name" in "$TOOLS_CONTAINER"|"$PAGES_CONTAINER"|"$RUNTIME_CONTAINER") ;; *) return 2 ;; esac
  metadata="$(docker_control inspect --format '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$name")" \
    || { printf 'bounded-stop=not-performed|owner-metadata-unavailable\n' >&2; return 1; }
  IFS='|' read -r id state jit manifest run <<< "$metadata"
  [[ "$id" =~ ^[a-f0-9]{64}$ && "$jit" == "$JIT" \
    && "$manifest" == "$APPROVED_MANIFEST_SHA256" && "$run" == "$RUN_NONCE" ]] \
    || { printf 'bounded-stop=not-performed|owner-mismatch\n' >&2; return 2; }
  [[ "$state" == running ]] || return 0
  timeout --foreground --signal=TERM --kill-after=5s 20s docker stop --time 10 "$id" >/dev/null 2>&1 \
    && printf 'bounded-stop=completed|container=%s|resource-preserved=true\n' "$name" >&2
}

on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$status" -ne 0 && -n "$ACTIVE_CONTAINER" && "$ACTIVE_CONTAINER" != "$STOP_ATTEMPTED_CONTAINER" ]]; then
    STOP_ATTEMPTED_CONTAINER="$ACTIVE_CONTAINER"
    stop_owned_container "$ACTIVE_CONTAINER" || true
  fi
  if [[ "$report_open" == true ]]; then
    if [[ "$status" -eq 0 ]]; then
      printf 'startup-result=PASS\n'
    else
      printf 'startup-result=NO-GO|phase=%s|exit=%s\n' "$phase" "$status"
    fi
  fi
  printf 'startup-runner-exit=%s|phase=%s|evidence=%s\n' "$status" "$phase" "$RESULT_LOG" >&3
  exit "$status"
}
trap on_exit EXIT

sanitize_bootstrap_output() {
  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      'bootstrap-output=non-diagnostic-lines-suppressed' \
        |'bootstrap-output-classification=capped-after-16777216-bytes' \
        |bootstrap-diagnostic-class=sensitive-line-redacted \
        |bootstrap-diagnostic-class=permission-denied \
        |bootstrap-diagnostic-class=missing-file-or-directory \
        |bootstrap-diagnostic-class=integrity-or-checksum-failure \
        |bootstrap-diagnostic-class=module-resolution-failure \
        |bootstrap-diagnostic-class=network-or-registry-failure \
        |bootstrap-diagnostic-class=bootstrap-error)
        printf '%s\n' "$line" ;;
      *) printf 'bootstrap-output-class=unclassified-line-suppressed\n' ;;
    esac
  done
}

check_free_name() {
  local kind=$1 requested=$2 existing matches
  case "$kind" in
    container) matches="$(docker_control ps -a --format '{{.Names}}' --filter "name=$requested")" || fail 'cannot check container-name collision' ;;
    volume) matches="$(docker_control volume ls --format '{{.Name}}' --filter "name=$requested")" || fail 'cannot check volume-name collision' ;;
    network) matches="$(docker_control network ls --format '{{.Name}}' --filter "name=$requested")" || fail 'cannot check network-name collision' ;;
    *) fail 'unknown Docker resource type' ;;
  esac
  while IFS= read -r existing; do [[ "$existing" != "$requested" ]] || fail "exact resource name is occupied: $requested"; done <<< "$matches"
}

create_tmpfs_volume() {
  local name=$1 size=$2 created metadata
  check_free_name volume "$name"
  created="$(docker_control volume create --driver local --opt type=tmpfs --opt device=tmpfs \
    --opt "o=nosuid,nodev,size=$size" \
    --label "com.studiamatch.h3.startup.jit=$JIT" \
    --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.startup.run=$RUN_NONCE" "$name")" || fail "cannot create bounded dependency volume: $name"
  [[ "$created" == "$name" ]] || fail "unexpected volume-create result for $name"
  metadata="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}' "$name")" \
    || fail "cannot inspect bounded dependency volume: $name"
  [[ "$metadata" == "$name|local|tmpfs|tmpfs|nosuid,nodev,size=$size|$JIT|$APPROVED_MANIFEST_SHA256|$RUN_NONCE" ]] \
    || fail "dependency volume controls differ: $name"
}

verify_owned_container() {
  local name=$1 expected_network=$2 expected_image=$3 expected_exit=$4
  local metadata id actual_name image state exit_code oom network jit manifest run
  metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$name")" \
    || fail "cannot verify owned container metadata: $name"
  IFS='|' read -r id actual_name image state exit_code oom network jit manifest run <<< "$metadata"
  [[ "$id" =~ ^[a-f0-9]{64}$ && "$actual_name" == "/$name" && "$image" == "$expected_image" \
    && "$state" == exited && "$exit_code" =~ ^[0-9]+$ && "$oom" == false \
    && "$network" == "$expected_network" && "$jit" == "$JIT" \
    && "$manifest" == "$APPROVED_MANIFEST_SHA256" && "$run" == "$RUN_NONCE" ]] \
    || fail "owned container identity/state mismatch: $name"
  [[ "$expected_exit" == any || "$exit_code" == "$expected_exit" ]] || fail "owned container exit differs from expected result: $name"
  VERIFIED_CONTAINER_ID="$id"
  VERIFIED_CONTAINER_EXIT="$exit_code"
  printf 'container=%s|state=%s|exit=%s|oom=%s|network=%s\n' "$name" "$state" "$exit_code" "$oom" "$network"
}

remove_verified_container() {
  local name=$1 id=$2 metadata actual_id actual_name state exit_code jit manifest run remaining
  metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$id")" \
    || { printf 'container-retirement=not-performed|resource-preserved=true|reason=metadata-unavailable|name=%s\n' "$name"; return 1; }
  IFS='|' read -r actual_id actual_name state exit_code jit manifest run <<< "$metadata"
  [[ "$actual_id" == "$id" && "$actual_name" == "/$name" && "$state" == exited && "$exit_code" == 0 \
    && "$jit" == "$JIT" && "$manifest" == "$APPROVED_MANIFEST_SHA256" && "$run" == "$RUN_NONCE" ]] \
    || { printf 'container-retirement=not-performed|resource-preserved=true|reason=owner-or-state-mismatch|name=%s\n' "$name"; return 1; }
  printf 'container-retirement=evidence-written|name=%s|id=%s\n' "$name" "$id"
  docker_control rm "$id" >/dev/null || { printf 'container-retirement=not-performed|resource-preserved=true|reason=remove-failed|name=%s\n' "$name"; return 1; }
  remaining="$(docker_control ps -a --no-trunc --filter "id=$id" --format '{{.ID}}')" \
    || { printf 'container-retirement=not-confirmed|resource-preserved=true|reason=list-failed|name=%s\n' "$name"; return 1; }
  [[ -z "$remaining" ]] \
    || { printf 'container-retirement=not-confirmed|resource-preserved=true|reason=container-still-listed|name=%s\n' "$name"; return 1; }
  printf 'container-retirement=completed|name=%s|id=%s\n' "$name" "$id"
}

run_bootstrap() {
  local name=$1; shift
  local docker_status filter_status container_id
  ACTIVE_CONTAINER="$name"
  set +e
  timeout --foreground --signal=TERM --kill-after=10s 600s "$@" 2>&1 | sanitize_bootstrap_output
  local -a statuses=("${PIPESTATUS[@]}")
  set -e
  docker_status="${statuses[0]:-1}"
  filter_status="${statuses[1]:-1}"
  printf 'bootstrap-docker-exit=%s|filter-exit=%s\n' "$docker_status" "$filter_status"
  [[ "$filter_status" == 0 ]] || fail "bootstrap output filter failed: $name"
  verify_owned_container "$name" bridge "$NODE_IMAGE" any
  container_id="$VERIFIED_CONTAINER_ID"
  ACTIVE_CONTAINER=''
  [[ "$docker_status" == 0 && "$VERIFIED_CONTAINER_EXIT" == 0 ]] || fail "locked npm bootstrap failed: $name"
  remove_verified_container "$name" "$container_id" || fail "successful bootstrap container could not be retired: $name"
}

verify_snapshot_volume() {
  local mode_map=$1 output
  # The single-quoted command runs inside the pinned container; its variables expand there.
  # shellcheck disable=SC2016
  output="$(docker_control run --rm --pull=never --platform linux/amd64 --network none --log-driver none \
    --read-only --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 \
    --cap-drop=ALL --security-opt no-new-privileges:true \
    --mount "type=volume,src=$SOURCE_VOLUME,dst=/snapshot,readonly" \
    --env H3_SOURCE_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" \
    --env "H3_SOURCE_MODE_MANIFEST=$mode_map" \
    "$NODE_IMAGE" sh -lc 'set -eu; cd /snapshot; test "$(sha256sum tests/h3req1-c03-startup-source-s1-v8.sha256 | cut -d" " -f1)" = "$H3_SOURCE_MANIFEST_SHA256"; sha256sum -c tests/h3req1-c03-startup-source-s1-v8.sha256 >/dev/null 2>&1; test -z "$(find . -type l -print -quit)"; test "$(find . -type f | wc -l | tr -d "[:space:]")" = 14; expected="$( { awk "{print \$2}" tests/h3req1-c03-startup-source-s1-v8.sha256; printf "%s\\n" tests/h3req1-c03-startup-source-s1-v8.sha256; } | LC_ALL=C sort -u )"; actual="$(find . -type f -printf "%P\\n" | LC_ALL=C sort)"; test "$expected" = "$actual"; actual_modes="$(find . -type f -printf "%P|%m\\n" | LC_ALL=C sort | tr "\\n" ";")"; test "$actual_modes" = "$H3_SOURCE_MODE_MANIFEST"; printf "snapshot-volume-verification=PASS\\n"')" \
    || fail 'S16 snapshot read-only verification failed'
  [[ "$output" == 'snapshot-volume-verification=PASS' ]] || fail 'S16 snapshot verifier marker mismatch'
  printf 'phase=s16-snapshot-readonly-verifier|error_code=PASS\n'
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
[[ "$ROOT" == "$EXPECTED_ROOT" ]] || fail 'candidate path changed'
[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" && "${3:-}" == '--manifest-sha256' && $# -eq 4 ]] \
  || fail 'exact local JIT and startup manifest SHA-256 required'
APPROVED_MANIFEST_SHA256="${4:-}"
[[ "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] || fail 'invalid startup manifest digest'
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'
[[ -d .context/evidencia && ! -L .context && ! -L .context/evidencia \
  && -f "$MANIFEST" && ! -L "$MANIFEST" && ! -e "$RESULT_LOG" && ! -L "$RESULT_LOG" ]] \
  || fail 'startup manifest/evidence path unavailable'
[[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'startup manifest digest changed'
sha256sum -c "$MANIFEST" >/dev/null || fail 'startup inputs differ from manifest'
[[ "$(sha256sum "$SOURCE_MANIFEST" | cut -d' ' -f1)" == "$SOURCE_MANIFEST_SHA256" ]] || fail 'current source manifest digest changed'
sha256sum -c "$SOURCE_MANIFEST" >/dev/null || fail 'current source inputs differ from v8 manifest'
[[ "$(sha256sum "$SNAPSHOT_RUNNER" | cut -d' ' -f1)" == "$SNAPSHOT_RUNNER_SHA256" \
  && "$(cat "$SNAPSHOT_SIDECAR")" == "$SNAPSHOT_RUNNER_SHA256  $SNAPSHOT_RUNNER" \
  && "$(sha256sum "$SNAPSHOT_SIDECAR" | cut -d' ' -f1)" == "$SNAPSHOT_SIDECAR_SHA256" ]] \
  || fail 'S16 runner or sidecar pins changed'
[[ "$(sha256sum "$SNAPSHOT_EVIDENCE" | cut -d' ' -f1)" == "$SNAPSHOT_EVIDENCE_SHA256" ]] || fail 'S16 evidence digest changed'
grep -Fqx "jit=$SNAPSHOT_JIT" "$SNAPSHOT_EVIDENCE" || fail 'S16 evidence identity changed'
grep -Fqx "source-manifest-sha256=$SOURCE_MANIFEST_SHA256" "$SNAPSHOT_EVIDENCE" || fail 'S16 source manifest evidence changed'
grep -Fqx "container-created-id=$SNAPSHOT_CONTAINER_ID" "$SNAPSHOT_EVIDENCE" || fail 'S16 snapshot container ID evidence changed'
grep -Fqx 'source-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0' "$SNAPSHOT_EVIDENCE" || fail 'S16 complete snapshot marker missing'
[[ "$(sha256sum "$OUTPUT_FILTER" | cut -d' ' -f1)" == "$OUTPUT_FILTER_SHA256" \
  && "$(sha256sum "$PRELOAD_SCRIPT" | cut -d' ' -f1)" == "$PRELOAD_SCRIPT_SHA256" \
  && "$(sha256sum "$BOOTSTRAP_FILTER" | cut -d' ' -f1)" == "$BOOTSTRAP_FILTER_SHA256" \
  && "$(sha256sum "$PROBE_SCRIPT" | cut -d' ' -f1)" == "$PROBE_SCRIPT_SHA256" ]] \
  || fail 'runtime diagnostic helper digest changed'

for helper in "$BOOTSTRAP_FILTER" "$OUTPUT_FILTER" "$PROBE_SCRIPT" "$PRELOAD_SCRIPT"; do
  [[ -f "$helper" && ! -L "$helper" ]] || fail "required helper missing or symlinked: $helper"
done
# shellcheck source=tests/h3req1_c03_startup_output_filter_s8.sh
source "$OUTPUT_FILTER"
[[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] \
  || fail 'Docker endpoint override rejected'
context_name="$(docker_control context show)" || fail 'cannot determine Docker context'
[[ "$context_name" == "$EXPECTED_DOCKER_CONTEXT" ]] || fail 'Docker context differs from attested Docker Desktop context'
endpoint="$(docker_control context inspect --format '{{ (index .Endpoints "docker").Host }}' "$context_name")" || fail 'cannot read Docker endpoint'
[[ "$endpoint" == "$EXPECTED_DOCKER_ENDPOINT" && -S "${endpoint#unix://}" ]] || fail 'Docker endpoint differs from the attested local socket'
engine_identity="$(docker_control info --format '{{.ID}}|{{.Name}}|{{.OperatingSystem}}')" || fail 'cannot verify Docker Desktop identity'
[[ "$engine_identity" == "$EXPECTED_DOCKER_ENGINE" ]] || fail 'Docker engine identity differs from attestation'
docker_control image inspect "$NODE_IMAGE" >/dev/null || fail 'pinned Node image is not local; pulls are forbidden'

snapshot_metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}' "$SNAPSHOT_CONTAINER")" \
  || fail 'cannot verify S16 snapshot container metadata'
IFS='|' read -r snapshot_id snapshot_name snapshot_image snapshot_state snapshot_exit snapshot_oom snapshot_network snapshot_readonly snapshot_jit snapshot_manifest snapshot_run <<< "$snapshot_metadata"
[[ "$snapshot_id" == "$SNAPSHOT_CONTAINER_ID" && "$snapshot_name" == "/$SNAPSHOT_CONTAINER" \
  && "$snapshot_image" == "$NODE_IMAGE" && "$snapshot_state" == exited && "$snapshot_exit" == 0 \
  && "$snapshot_oom" == false && "$snapshot_network" == none && "$snapshot_readonly" == true \
  && "$snapshot_jit" == "$SNAPSHOT_JIT" && "$snapshot_manifest" == "$SNAPSHOT_SIDECAR_SHA256" \
  && "$snapshot_run" =~ ^[0-9]+-[0-9]+-[0-9]+$ ]] || fail 'S16 snapshot container identity/control mismatch'
snapshot_mount="$(docker_control inspect --format '{{range .Mounts}}{{.Type}}|{{.Name}}|{{.Destination}}|{{.RW}}{{end}}' "$SNAPSHOT_CONTAINER")" \
  || fail 'cannot verify S16 snapshot mount metadata'
[[ "$snapshot_mount" == "volume|$SOURCE_VOLUME|/snapshot|true" ]] || fail 'S16 snapshot volume attachment differs'
source_volume_meta="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Labels "com.studiamatch.h3.snapshot.run"}}' "$SOURCE_VOLUME")" \
  || fail 'cannot verify S16 source volume metadata'
[[ "$source_volume_meta" == "$SOURCE_VOLUME|local|$SNAPSHOT_JIT|$SNAPSHOT_SIDECAR_SHA256|$snapshot_run" ]] \
  || fail 'S16 source volume ownership metadata mismatch'

total_source_bytes=0
while IFS=' ' read -r _ source_path; do
  [[ -f "$source_path" && ! -L "$source_path" ]] || fail 'source manifest input missing or symlinked'
  resolved="$(realpath -e -- "$source_path")" || fail 'cannot resolve source input'
  [[ "$resolved" == "$ROOT/$source_path" ]] || fail 'source input escapes candidate checkout'
  size="$(stat -Lc '%s' -- "$source_path")" || fail 'cannot read source size'
  mode="$(stat -Lc '%a' -- "$source_path")" || fail 'cannot read source mode'
  [[ "$size" =~ ^[0-9]+$ && "$size" -le 4194304 && "$mode" =~ ^[0-7]{3,4}$ ]] || fail 'source size/mode outside bounds'
  (( (8#$mode & 06000) == 0 )) || fail 'setuid/setgid source rejected'
  total_source_bytes=$((total_source_bytes + size))
done < "$SOURCE_MANIFEST"
manifest_mode="$(stat -Lc '%a' -- "$SOURCE_MANIFEST")" || fail 'cannot read source manifest mode'
(( (8#$manifest_mode & 06000) == 0 )) || fail 'setuid/setgid source manifest rejected'
source_mode_manifest="$( {
  while IFS=' ' read -r _ source_path; do printf '%s|%s\n' "$source_path" "$(stat -Lc '%a' -- "$source_path")"; done < "$SOURCE_MANIFEST"
  printf '%s|%s\n' "$SOURCE_MANIFEST" "$manifest_mode"
} | LC_ALL=C sort | tr '\n' ';' )" || fail 'cannot calculate current source permission map'
(( total_source_bytes <= 8388608 )) || fail 'current source set exceeds size limit'
source_mode_sha256="$(printf '%s' "$source_mode_manifest" | sha256sum | cut -d' ' -f1)"
evidence_mode_sha256="$(awk -F= '$1 == "source-permission-map-sha256" { print $2 }' "$SNAPSHOT_EVIDENCE")"
[[ "$source_mode_sha256" == "$evidence_mode_sha256" ]] || fail 'current source permissions differ from S16 evidence'

lock_counts="$(awk -F'"' '/"resolved": "/ { url=$4; if (url ~ /^https:\/\/registry\.npmjs\.org\//) registry++; else if (url == "file:vendor/braces-3.0.4-h3.1.tgz") local++; else bad++ } END { printf "%d|%d|%d", registry+0, local+0, bad+0; if (bad) exit 1 }' tests/h3req1-c03-bootstrap/package-lock.json web/package-lock.json)" \
  || fail 'package locks contain a non-allowlisted dependency source'
[[ "$lock_counts" == '777|1|0' ]] || fail 'package lock registry/vendor entry counts changed'

for resource in "$VOLUME_HOLDER" "$TOOLS_CONTAINER" "$PAGES_CONTAINER" "$RUNTIME_CONTAINER"; do check_free_name container "$resource"; done
check_free_name volume "$TOOLS_VOLUME"
check_free_name volume "$PAGES_VOLUME"
check_free_name network "$NETWORK"

set -o noclobber
exec >"$RESULT_LOG" 2>&1
set +o noclobber
report_open=true
printf 'jit=%s\nmanifest-sha256=%s\nbranch=%s\nhead=%s\n' "$JIT" "$APPROVED_MANIFEST_SHA256" "$EXPECTED_BRANCH" "$EXPECTED_HEAD"
printf '# H3REQ1 C03 startup smoke S11-R2 — current source and fresh locked dependencies\n\n'
printf 'attempt=2; prior-attempt-evidence=.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s11.md\n'
printf 'scope=Pages/workerd healthz only; source snapshot S16; fresh npm dependencies from pinned package locks; npm registry bootstrap over Docker bridge with lifecycle scripts disabled; runtime on verified internal network; no DB, PostgREST, Edge, SQL, Auth, email, secrets, or remotes\n'
printf 'source-manifest-sha256=%s\nsource-files=13\nsource-bytes=%s\nsource-mode-map-sha256=%s\n' "$SOURCE_MANIFEST_SHA256" "$total_source_bytes" "$source_mode_sha256"
printf 'dependency-lock-resolutions=registry-npmjs-777|local-vendor-1|other-0\nnode-image=%s\n' "$NODE_IMAGE"
printf 'npm-lifecycle-scripts=disabled\n'
printf 'resource-limits=bootstrap-2GiB-2CPU-600s|runtime-2GiB-2CPU-180s|automatic-fetch-retries=0\n'
sha256sum -c "$MANIFEST"

phase='verify-current-snapshot-volume-readonly'
verify_snapshot_volume "$source_mode_manifest"

phase='bootstrap-synthetics'
bootstrap_filter_output="$(printf 'npm ERR! ERESOLVE synthetic\nfetch failed\ntoken=synthetic-secret\nordinary line\n' | \
  docker_control run --rm --pull=never --platform linux/amd64 --interactive --network none --log-driver none \
    --read-only --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 --cap-drop=ALL \
    --security-opt no-new-privileges:true --mount "type=bind,src=$ROOT/$BOOTSTRAP_FILTER,dst=/bootstrap-filter.mjs,readonly" \
    "$NODE_IMAGE" node /bootstrap-filter.mjs)" || fail 'bootstrap output-filter synthetic test failed'
[[ "$bootstrap_filter_output" == $'bootstrap-diagnostic-class=module-resolution-failure\nbootstrap-diagnostic-class=network-or-registry-failure\nbootstrap-diagnostic-class=sensitive-line-redacted' ]] \
  || fail 'bootstrap output-filter synthetic marker mismatch'
printf 'phase=bootstrap-output-filter-synthetic|error_code=PASS\n'
output_filter_test="$(docker_control run --rm --pull=never --platform linux/amd64 --network none --log-driver none \
  --read-only --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 --cap-drop=ALL \
  --security-opt no-new-privileges:true --mount "type=bind,src=$ROOT/$OUTPUT_FILTER,dst=/filter.sh,readonly" \
  "$NODE_IMAGE" bash /filter.sh --self-test)" || fail 'runtime output-filter synthetics failed'
[[ "$output_filter_test" == 'phase=runtime-output-filter-synthetic|error_code=PASS' ]] || fail 'runtime output-filter marker mismatch'
printf '%s\n' "$output_filter_test"
probe_synthetics="$(docker_control run --rm --pull=never --platform linux/amd64 --network none --log-driver none \
  --read-only --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 --cap-drop=ALL \
  --security-opt no-new-privileges:true \
  --mount "type=bind,src=$ROOT/$PROBE_SCRIPT,dst=/probe.mjs,readonly" \
  --mount "type=bind,src=$ROOT/$PRELOAD_SCRIPT,dst=/diag-preload.cjs,readonly" \
  "$NODE_IMAGE" sh -lc 'node --check /diag-preload.cjs && node /probe.mjs --self-test')" \
  || fail 'runtime diagnostic parser synthetics failed'
[[ "$probe_synthetics" == 'phase=runtime-diagnostic-synthetic|error_code=PASS' ]] || fail 'runtime diagnostic synthetic marker mismatch'
printf '%s\n' "$probe_synthetics"

phase='create-current-dependency-volumes-and-holder'
create_tmpfs_volume "$TOOLS_VOLUME" 768m
create_tmpfs_volume "$PAGES_VOLUME" 1024m
holder_id="$(docker_control run --detach --pull=never --platform linux/amd64 --name "$VOLUME_HOLDER" \
  --network none --log-driver none --read-only --restart=no --cpus=0.1 --memory=64m --memory-swap=64m --pids-limit=16 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  --mount "type=volume,src=$SOURCE_VOLUME,dst=/source,readonly" \
  --mount "type=volume,src=$TOOLS_VOLUME,dst=/tools,readonly" \
  --mount "type=volume,src=$PAGES_VOLUME,dst=/pages,readonly" \
  "$NODE_IMAGE" sh -lc 'exec sleep infinity')" || fail 'cannot start bounded dependency-volume holder'
[[ "$holder_id" =~ ^[a-f0-9]{12,64}$ ]] || fail 'unexpected volume-holder identity'
holder_meta="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.HostConfig.NetworkMode}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$VOLUME_HOLDER")" \
  || fail 'cannot verify dependency-volume holder'
[[ "$holder_meta" == "$holder_id|/$VOLUME_HOLDER|running|none|$JIT|$APPROVED_MANIFEST_SHA256|$RUN_NONCE" ]] \
  || fail 'dependency-volume holder identity/control mismatch'
printf 'volume-holder=%s|state=running|network=none\n' "$VOLUME_HOLDER"

phase='fresh-tools-npm-ci-registry-bootstrap'
run_bootstrap "$TOOLS_CONTAINER" docker run --pull=never --platform linux/amd64 --name "$TOOLS_CONTAINER" \
  --network bridge --log-driver none --read-only --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 \
  --cap-drop=ALL --security-opt no-new-privileges:true "${EMPTY_PROXY_ENV[@]}" \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,nosuid,size=512m --mount "type=volume,src=$SOURCE_VOLUME,dst=/source,readonly" \
  --mount "type=volume,src=$TOOLS_VOLUME,dst=/out" \
  --mount "type=bind,src=$ROOT/$BOOTSTRAP_FILTER,dst=/bootstrap-filter.mjs,readonly" \
  --workdir /out --env HOME=/tmp --env npm_config_cache=/tmp/npm-cache \
  "$NODE_IMAGE" bash -lc 'set -euo pipefail; cp /source/tests/h3req1-c03-bootstrap/package.json /source/tests/h3req1-c03-bootstrap/package-lock.json /out/; npm ci --ignore-scripts --no-audit --no-fund --fetch-retries=0 --registry=https://registry.npmjs.org/ 2>&1 | node /bootstrap-filter.mjs'

phase='fresh-pages-npm-ci-registry-bootstrap'
run_bootstrap "$PAGES_CONTAINER" docker run --pull=never --platform linux/amd64 --name "$PAGES_CONTAINER" \
  --network bridge --log-driver none --read-only --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 \
  --cap-drop=ALL --security-opt no-new-privileges:true "${EMPTY_PROXY_ENV[@]}" \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,nosuid,size=512m --mount "type=volume,src=$SOURCE_VOLUME,dst=/source,readonly" \
  --mount "type=volume,src=$PAGES_VOLUME,dst=/out" \
  --mount "type=bind,src=$ROOT/$BOOTSTRAP_FILTER,dst=/bootstrap-filter.mjs,readonly" \
  --workdir /out --env HOME=/tmp --env npm_config_cache=/tmp/npm-cache \
  "$NODE_IMAGE" bash -lc 'set -euo pipefail; cp /source/web/package.json /source/web/package-lock.json /out/; cp -a /source/web/vendor /out/vendor; npm ci --omit=dev --ignore-scripts --no-audit --no-fund --fetch-retries=0 --registry=https://registry.npmjs.org/ 2>&1 | node /bootstrap-filter.mjs'

phase='create-egress-blocked-internal-runtime-network'
created_network_id="$(docker_control network create --internal \
  --label "com.studiamatch.h3.startup.jit=$JIT" \
  --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.startup.run=$RUN_NONCE" "$NETWORK")" || fail 'cannot create internal runtime network'
[[ "$created_network_id" =~ ^[a-f0-9]{64}$ ]] || fail 'Docker network-create result is not a full network ID'
NETWORK_ID="$created_network_id"
network_meta="$(docker_control network inspect --format '{{.Id}}|{{.Name}}|{{.Driver}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}|{{len .Containers}}' "$NETWORK_ID")" \
  || fail 'cannot verify created internal network'
[[ "$network_meta" == "$NETWORK_ID|$NETWORK|bridge|true|$JIT|$APPROVED_MANIFEST_SHA256|$RUN_NONCE|0" ]] \
  || fail 'created network ID/name/internal/owner/endpoint controls differ'
printf 'runtime-network=%s|id=%s|driver=bridge|internal=true|endpoints=0\n' "$NETWORK" "$NETWORK_ID"

phase='one-shot-pages-workerd-healthz'
ACTIVE_CONTAINER="$RUNTIME_CONTAINER"
set +e
timeout --foreground --signal=TERM --kill-after=10s 180s docker run --pull=never --platform linux/amd64 \
  --name "$RUNTIME_CONTAINER" --network "$NETWORK_ID" --log-driver none --read-only \
  --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 --stop-timeout 10 \
  --cap-drop=ALL --security-opt no-new-privileges:true "${EMPTY_PROXY_ENV[@]}" \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m --tmpfs /run/c03-private:rw,noexec,nosuid,size=8m \
  --tmpfs /run/c03-certs:rw,nosuid,size=16m \
  --mount "type=volume,src=$SOURCE_VOLUME,dst=/candidate,readonly" \
  --mount "type=volume,src=$TOOLS_VOLUME,dst=/tools,readonly" \
  --mount "type=volume,src=$PAGES_VOLUME,dst=/web-deps,readonly" \
  --mount "type=bind,src=$ROOT/$PROBE_SCRIPT,dst=/probe.mjs,readonly" \
  --mount "type=bind,src=$ROOT/$PRELOAD_SCRIPT,dst=/diag-preload.cjs,readonly" \
  --env H3_C03_ROOT=/candidate --env H3_C03_TOOLS_ROOT=/tools --env H3_C03_CERTS_ROOT=/run/c03-certs \
  --env H3_C03_WEB_DEPS_ROOT=/web-deps --env H3_C03_PRIVATE_ROOT=/run/c03-private \
  --env H3_C03_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" --env H3_C03_DEPENDENCY_BOOTSTRAP_COMPLETE=true \
  "$NODE_IMAGE" node /probe.mjs 2>&1 | sanitize_runtime_output
runtime_pipeline_status=("${PIPESTATUS[@]}")
set -e
runtime_docker_status="${runtime_pipeline_status[0]:-1}"
runtime_filter_status="${runtime_pipeline_status[1]:-1}"
printf 'runtime-docker-exit=%s|filter-exit=%s\n' "$runtime_docker_status" "$runtime_filter_status"
[[ "$runtime_filter_status" == 0 ]] || fail 'runtime output filter failed'
verify_owned_container "$RUNTIME_CONTAINER" "$NETWORK_ID" "$NODE_IMAGE" any
runtime_id="$VERIFIED_CONTAINER_ID"
ACTIVE_CONTAINER=''
[[ "$runtime_docker_status" == 0 && "$VERIFIED_CONTAINER_EXIT" == 0 ]] || fail 'Pages/workerd runtime container returned nonzero exit'
# Docker's Go template variables must remain literal for Docker to expand them.
# shellcheck disable=SC2016
runtime_network_attachment="$(docker_control inspect --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}}|{{$net.NetworkID}}{{end}}' "$RUNTIME_CONTAINER")" \
  || fail 'cannot verify runtime attachment to the internal network'
[[ "$runtime_network_attachment" == "$NETWORK|$NETWORK_ID" ]] || fail 'runtime network attachment differs from the exact internal network ID'
printf 'runtime-network-attachment=%s|internal=true\n' "$NETWORK_ID"
grep -Fqx 'smoke=PASS workerd-pages-healthz=true edge-runtime=not-started database=not-started' "$RESULT_LOG" \
  || fail 'exact Pages/workerd healthz PASS marker missing'
printf 'phase=pages-workerd-healthz|error_code=PASS\nexit=0\n'
remove_verified_container "$RUNTIME_CONTAINER" "$runtime_id" || fail 'successful runtime container could not be retired'

network_after_run="$(docker_control network inspect --format '{{.Id}}|{{.Name}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}|{{len .Containers}}' "$NETWORK_ID")" \
  || network_after_run=''
if [[ "$network_after_run" == "$NETWORK_ID|$NETWORK|true|$JIT|$APPROVED_MANIFEST_SHA256|$RUN_NONCE|0" ]]; then
  docker_control network rm "$NETWORK_ID" >/dev/null \
    || { printf 'network-retirement=not-performed|resource-preserved=true|reason=remove-failed|name=%s\n' "$NETWORK"; fail 'internal runtime network could not be retired'; }
  remaining_network="$(docker_control network ls --no-trunc --filter "id=$NETWORK_ID" --format '{{.ID}}')" \
    || { printf 'network-retirement=not-confirmed|resource-preserved=true|reason=list-failed|name=%s\n' "$NETWORK"; fail 'internal runtime network retirement could not be verified'; }
  [[ -z "$remaining_network" ]] \
    || { printf 'network-retirement=not-confirmed|resource-preserved=true|reason=network-still-listed|name=%s\n' "$NETWORK"; fail 'internal runtime network remains after retirement'; }
  printf 'network-retirement=completed|name=%s|id=%s\n' "$NETWORK" "$NETWORK_ID"
else
  printf 'network-retirement=not-performed|resource-preserved=true|reason=metadata-or-endpoint-mismatch|name=%s\n' "$NETWORK"
  fail 'internal runtime network metadata or endpoint count changed before retirement'
fi
printf 'retained-for-next-local-gates=source-volume-s16,tools-volume-s11,pages-volume-s11,volume-holder-s11\n'
printf 'startup-result=PASS\n'
trap - EXIT
report_open=false
printf '%s\n' 'Startup smoke S11: PASS (current candidate source, fresh locked dependencies, internal-network workerd Pages healthz).' \
  "Sanitized evidence: $RESULT_LOG" >&3
exec 3>&-
