#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S5-DIAGNOSTIC'
readonly RUNNER='tests/h3req1_c03_startup_smoke_s5.sh'
readonly MANIFEST='tests/h3req1-c03-startup-smoke-s5.sha256'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s5.md'
readonly PROBE_SCRIPT='tests/h3req1_c03_startup_runtime_probe_s5.mjs'
readonly S4_RUNNER='tests/h3req1_c03_startup_smoke_s3_resume_s4.sh'
readonly S4_RUNNER_SHA256='c4659f16889a41987c6512d7167ffe397d6a31edf58b645a77bc888d627eca7c'
readonly S4_MANIFEST='tests/h3req1-c03-startup-smoke-s3-resume-s4.sha256'
readonly S4_MANIFEST_SHA256='1cb90249466e65ccf59fc6ae3d2d7088f8c658917d91ece5f55c66bfd9268f29'
readonly S4_RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s4.md'
readonly S4_RESULT_SHA256='4136061965cde82eb926c450ac2efaafcd3832551097fd7767de0393398fea87'
readonly S4_DIAGNOSIS='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s4_diagnosis.md'
readonly S4_DIAGNOSIS_SHA256='581b7230713344142911357f63d890408705f6bde0c7124de3414df941517fc4'
readonly S3_JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S3'
readonly S3_RUNNER='tests/h3req1_c03_startup_smoke_s3.sh'
readonly S3_RUNNER_SHA256='4077a9c6e14a0588fb972f77c4b27385cc223306a63bbaea553b239c87af1689'
readonly S3_MANIFEST='tests/h3req1-c03-startup-smoke-s3.sha256'
readonly S3_MANIFEST_SHA256='351c6590c24c466fe8af531f1d9661ef7a6fcc1f7170c617f223fefc70bdc018'
readonly S3_RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s3.md'
readonly S3_RESULT_SHA256='b8aed3fedcbfab899b8c4a72a619e522bc156d94cfb04711d31661ffcca0224e'
readonly SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v3.sha256'
readonly SOURCE_MANIFEST_SHA256='4b6e99fb6feb85eb8b4ea8e899e69c2d3c497657b507b03004d45981b97417c8'
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly EXPECTED_DOCKER_CONTEXT='default'
readonly EXPECTED_DOCKER_ENDPOINT='unix:///var/run/docker.sock'
readonly EXPECTED_DOCKER_ENGINE='fc2115b2-c3c4-440e-89c6-26899eb7cb04|docker-desktop|Docker Desktop'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly SOURCE_VOLUME='h3req1-c03-startup-source-20261010-s3'
readonly TOOLS_VOLUME='h3req1-c03-startup-tools-20261010-s3'
readonly PAGES_VOLUME='h3req1-c03-startup-pages-20261010-s3'
readonly NETWORK='h3req1-c03-startup-net-20261010-s3'
readonly S3_SNAPSHOT='h3req1-c03-startup-snapshot-20261010-s3'
readonly S3_TOOLS='h3req1-c03-startup-tools-20261010-s3'
readonly S3_PAGES='h3req1-c03-startup-pages-20261010-s3'
readonly S3_HOLDER='h3req1-c03-startup-volume-holder-20261010-s3'
readonly S4_RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s4'
readonly RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s5'
RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"
readonly RUN_NONCE
readonly -a EMPTY_PROXY_ENV=(
  --env HTTP_PROXY= --env HTTPS_PROXY= --env FTP_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env ftp_proxy= --env all_proxy= --env no_proxy= \
  --env npm_config_proxy= --env npm_config_http_proxy= --env npm_config_https_proxy=
)
ACTIVE_CONTAINER=''
STOP_ATTEMPTED_CONTAINER=''
S3_RUN_NONCE=''

[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" \
  && "${3:-}" == '--runner-sha256' && "${5:-}" == '--manifest-sha256' && $# -eq 6 ]] || {
  echo "Refusing to run: exact JIT $JIT, runner SHA-256, and manifest SHA-256 required." >&2
  exit 77
}
readonly APPROVED_RUNNER_SHA256="${4:-}"
readonly APPROVED_MANIFEST_SHA256="${6:-}"
[[ "$APPROVED_RUNNER_SHA256" =~ ^[a-f0-9]{64}$ && "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] \
  || { echo 'Refusing to run: invalid SHA-256 pin.' >&2; exit 77; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
[[ "$ROOT" == "$EXPECTED_ROOT" ]] || { echo 'Refusing to run: candidate checkout path changed.' >&2; exit 77; }
exec 3>&1
phase='preflight'
fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }
docker_control() { timeout --foreground --signal=TERM --kill-after=5s 20s docker "$@"; }

stop_runtime() {
  local metadata container_id jit_label manifest_label run_label
  [[ "$RUNTIME_CONTAINER" == "${1:-}" ]] || { printf 'Refusing stop outside S5 runtime allowlist.\n' >&2; return 2; }
  metadata="$(docker_control inspect --format '{{.Id}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$RUNTIME_CONTAINER")" \
    || { printf 'Refusing stop: runtime ownership metadata unavailable.\n' >&2; return 1; }
  IFS='|' read -r container_id jit_label manifest_label run_label <<< "$metadata"
  [[ "$container_id" =~ ^[a-f0-9]{64}$ && "$jit_label" == "$JIT" \
    && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" && "$run_label" == "$RUN_NONCE" ]] \
    || { printf 'Refusing stop: runtime ownership labels do not match this run.\n' >&2; return 2; }
  if timeout --foreground --signal=TERM --kill-after=5s 20s docker stop --time 10 "$container_id" >/dev/null 2>&1; then
    printf 'bounded-stop=completed container=%s owner=verified; resource preserved\n' "$RUNTIME_CONTAINER"
  else
    printf 'bounded-stop=failed-or-timed-out container=%s; resource preserved\n' "$RUNTIME_CONTAINER"
    return 1
  fi
}

stop_active_runtime() {
  [[ -n "$ACTIVE_CONTAINER" && "$ACTIVE_CONTAINER" != "$STOP_ATTEMPTED_CONTAINER" ]] || return 0
  STOP_ATTEMPTED_CONTAINER="$ACTIVE_CONTAINER"
  if stop_runtime "$ACTIVE_CONTAINER"; then
    printf 'bounded-stop=completed container=%s; resource preserved\n' "$ACTIVE_CONTAINER" >&2
  else
    printf 'bounded-stop=failed-or-timed-out container=%s; preserve resource and report NO-GO\n' "$ACTIVE_CONTAINER" >&2
  fi
}

on_error() {
  local status=$?
  stop_active_runtime
  printf 'Startup continuation halted phase=%s exit=%s; preserve all S3 resources.\n' "$phase" "$status" >&2
  printf 'Startup continuation halted phase=%s exit=%s; no cleanup/resume.\n' "$phase" "$status" >&3
}

on_signal() {
  local signal=$1 status=1
  case "$signal" in HUP) status=129 ;; INT) status=130 ;; TERM) status=143 ;; esac
  stop_active_runtime
  printf 'Startup continuation interrupted phase=%s signal=%s; preserve all resources.\n' "$phase" "$signal" >&2
  printf 'Startup continuation interrupted phase=%s signal=%s; no cleanup/resume.\n' "$phase" "$signal" >&3
  trap - ERR HUP INT TERM
  exit "$status"
}

trap on_error ERR
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

[[ -f "$ROOT/$MANIFEST" && ! -L "$ROOT/$MANIFEST" ]] || fail 'S5 manifest missing or symlinked'
[[ -d "$ROOT/.context" && ! -L "$ROOT/.context" \
  && -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context/evidencia" ]] \
  || fail 'S5 evidence parent is missing, non-directory, or symlinked'
[[ ! -e "$ROOT/$RESULT_LOG" && ! -L "$ROOT/$RESULT_LOG" ]] || fail 'S5 evidence path already exists'
[[ -f "$ROOT/$S3_RUNNER" && ! -L "$ROOT/$S3_RUNNER" \
  && -f "$ROOT/$S3_MANIFEST" && ! -L "$ROOT/$S3_MANIFEST" \
  && -f "$ROOT/$S3_RESULT_LOG" && ! -L "$ROOT/$S3_RESULT_LOG" \
  && -f "$ROOT/$PROBE_SCRIPT" && ! -L "$ROOT/$PROBE_SCRIPT" \
  && -f "$ROOT/$S4_RUNNER" && ! -L "$ROOT/$S4_RUNNER" \
  && -f "$ROOT/$S4_MANIFEST" && ! -L "$ROOT/$S4_MANIFEST" \
  && -f "$ROOT/$S4_RESULT_LOG" && ! -L "$ROOT/$S4_RESULT_LOG" \
  && -f "$ROOT/$S4_DIAGNOSIS" && ! -L "$ROOT/$S4_DIAGNOSIS" ]] || fail 'pinned S3/S4 artifact missing or symlinked'
[[ "$(sha256sum "$RUNNER" | cut -d' ' -f1)" == "$APPROVED_RUNNER_SHA256" ]] || fail 'S5 runner digest changed'
[[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'S5 manifest digest changed'
[[ "$(sha256sum "$S3_RUNNER" | cut -d' ' -f1)" == "$S3_RUNNER_SHA256" ]] || fail 'S3 runner digest changed'
[[ "$(sha256sum "$S3_MANIFEST" | cut -d' ' -f1)" == "$S3_MANIFEST_SHA256" ]] || fail 'S3 manifest digest changed'
[[ "$(sha256sum "$S3_RESULT_LOG" | cut -d' ' -f1)" == "$S3_RESULT_SHA256" ]] || fail 'S3 result evidence digest changed'
[[ "$(sha256sum "$S4_RUNNER" | cut -d' ' -f1)" == "$S4_RUNNER_SHA256" ]] || fail 'S4 runner digest changed'
[[ "$(sha256sum "$S4_MANIFEST" | cut -d' ' -f1)" == "$S4_MANIFEST_SHA256" ]] || fail 'S4 manifest digest changed'
[[ "$(sha256sum "$S4_RESULT_LOG" | cut -d' ' -f1)" == "$S4_RESULT_SHA256" ]] || fail 'S4 result evidence digest changed'
[[ "$(sha256sum "$S4_DIAGNOSIS" | cut -d' ' -f1)" == "$S4_DIAGNOSIS_SHA256" ]] || fail 'S4 diagnosis digest changed'
[[ "$(sha256sum "$SOURCE_MANIFEST" | cut -d' ' -f1)" == "$SOURCE_MANIFEST_SHA256" ]] || fail 'source manifest digest changed'
[[ "$(awk -v path="$RUNNER" '$2 == path { print $1 }' "$MANIFEST")" == "$APPROVED_RUNNER_SHA256" ]] || fail 'S5 manifest does not pin its runner'
sha256sum -c "$MANIFEST" >/dev/null || fail 'S5 inputs differ from manifest'
sha256sum -c "$S3_MANIFEST" >/dev/null || fail 'S3 inputs differ from the preserved manifest'
sha256sum -c "$S4_MANIFEST" >/dev/null || fail 'S4 inputs differ from the preserved manifest'
sha256sum -c "$SOURCE_MANIFEST" >/dev/null || fail 'source inputs differ from source manifest'
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'
grep -Fqx "jit=$S3_JIT" "$S3_RESULT_LOG" || fail 'S3 evidence identity changed'
grep -Fqx "manifest-sha256=$S3_MANIFEST_SHA256" "$S3_RESULT_LOG" || fail 'S3 evidence manifest pin changed'
grep -Fqx 'source-snapshot=PASS files=14 symlinks=0 extraction-owner-restore=disabled' "$S3_RESULT_LOG" \
  || fail 'S3 snapshot PASS marker missing'
grep -Fqx "container=$S3_SNAPSHOT state=exited|0|false network=none" "$S3_RESULT_LOG" || fail 'S3 snapshot exit evidence missing'
grep -Fqx "container=$S3_TOOLS state=exited|0|false network=bridge" "$S3_RESULT_LOG" || fail 'S3 tools bootstrap exit evidence missing'
grep -Fqx "container=$S3_PAGES state=exited|0|false network=bridge" "$S3_RESULT_LOG" || fail 'S3 Pages bootstrap exit evidence missing'
grep -Fqx 'NO-GO: unexpected network name returned' "$S3_RESULT_LOG" || fail 'S3 stopped at an unexpected phase'

[[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] \
  || fail 'Docker endpoint override rejected; local Unix context only'
context_name="$(docker_control context show)" || fail 'cannot read Docker context within timeout'
[[ "$context_name" == "$EXPECTED_DOCKER_CONTEXT" ]] || fail 'Docker context differs from attested Desktop context'
endpoint="$(docker_control context inspect --format '{{ (index .Endpoints "docker").Host }}' "$context_name")" || fail 'cannot read Docker endpoint within timeout'
[[ "$endpoint" == "$EXPECTED_DOCKER_ENDPOINT" && -S "${endpoint#unix://}" ]] || fail 'Docker endpoint differs from attested Unix socket'
export DOCKER_CONTEXT="$context_name"
engine_identity="$(docker_control info --format '{{.ID}}|{{.Name}}|{{.OperatingSystem}}')" || fail 'cannot verify Docker Desktop identity'
[[ "$engine_identity" == "$EXPECTED_DOCKER_ENGINE" ]] || fail 'Docker engine identity differs from attested Desktop daemon'
docker_control image inspect "$NODE_IMAGE" >/dev/null 2>&1 || fail 'pinned Node image is not local; pulls are forbidden'

verify_s3_container() {
  local name=$1 expected_state=$2 expected_network=$3 metadata actual_name image state exit_code oom network jit manifest run
  metadata="$(docker_control inspect --format '{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$name")" \
    || fail "cannot verify preserved S3 resource: $name"
  IFS='|' read -r actual_name image state exit_code oom network jit manifest run <<< "$metadata"
  [[ "$actual_name" == "/$name" && "$image" == "$NODE_IMAGE" && "$state" == "$expected_state" \
    && "$oom" == false && "$network" == "$expected_network" && "$jit" == "$S3_JIT" \
    && "$manifest" == "$S3_MANIFEST_SHA256" && "$run" =~ ^[0-9]+-[0-9]+-[0-9]+-[0-9]+$ ]] \
    || fail "preserved S3 container identity/state mismatch: $name"
  if [[ -z "$S3_RUN_NONCE" ]]; then S3_RUN_NONCE="$run"; else [[ "$run" == "$S3_RUN_NONCE" ]] || fail 'S3 run ownership labels differ'; fi
  if [[ "$expected_state" == exited ]]; then [[ "$exit_code" == 0 ]] || fail "S3 bootstrap container exit is not zero: $name"; fi
}

verify_s3_volume() {
  local name=$1 size=$2 metadata actual_name driver type device options jit manifest run
  metadata="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}' "$name")" \
    || fail "cannot verify preserved S3 volume: $name"
  IFS='|' read -r actual_name driver type device options jit manifest run <<< "$metadata"
  [[ "$actual_name" == "$name" && "$driver" == local && "$type" == tmpfs && "$device" == tmpfs \
    && "$options" == "nosuid,nodev,size=$size" && "$jit" == "$S3_JIT" \
    && "$manifest" == "$S3_MANIFEST_SHA256" && "$run" == "$S3_RUN_NONCE" ]] \
    || fail "preserved S3 volume identity/options mismatch: $name"
}

phase='verify-preserved-s3-resources-and-resolve-network-id'
verify_s3_container "$S3_SNAPSHOT" exited none
verify_s3_container "$S3_TOOLS" exited bridge
verify_s3_container "$S3_PAGES" exited bridge
verify_s3_container "$S3_HOLDER" running none
verify_s3_volume "$SOURCE_VOLUME" 96m
verify_s3_volume "$TOOLS_VOLUME" 768m
verify_s3_volume "$PAGES_VOLUME" 1024m
network_meta="$(docker_control network inspect --format '{{.Id}}|{{.Name}}|{{.Driver}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}' "$NETWORK")" \
  || fail 'cannot resolve preserved S3 network by name'
IFS='|' read -r network_id network_name network_driver network_internal network_jit network_manifest network_run <<< "$network_meta"
[[ "$network_id" =~ ^[a-f0-9]{64}$ && "$network_name" == "$NETWORK" && "$network_driver" == bridge \
  && "$network_internal" == true && "$network_jit" == "$S3_JIT" \
  && "$network_manifest" == "$S3_MANIFEST_SHA256" && "$network_run" == "$S3_RUN_NONCE" ]] \
  || fail 'preserved S3 network ID/name/internal/owner metadata mismatch'
network_container_count="$(docker_control network inspect --format '{{len .Containers}}' "$network_id")" \
  || fail 'cannot verify preserved S3 network endpoint count'
[[ "$network_container_count" == 0 ]] || fail 'S3 internal network already has an unexpected endpoint'

phase='verify-preserved-s4-failure-metadata'
s4_metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{.HostConfig.NetworkMode}}' "$S4_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S4 runtime metadata'
IFS='|' read -r s4_id s4_name s4_state s4_exit s4_oom s4_jit s4_manifest s4_network_mode <<< "$s4_metadata"
[[ "$s4_id" =~ ^[a-f0-9]{64}$ && "$s4_name" == "/$S4_RUNTIME_CONTAINER" \
  && "$s4_state" == exited && "$s4_exit" == 1 && "$s4_oom" == false \
  && "$s4_jit" == 'H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S4-RESUME-S3' \
  && "$s4_manifest" == "$S4_MANIFEST_SHA256" && "$s4_network_mode" == "$network_id" ]] \
  || fail 'preserved S4 runtime metadata differs from the recorded failure'
s4_network_attachment="$(docker_control inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}|{{$v.NetworkID}}{{end}}' "$S4_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S4 network attachment'
[[ "$s4_network_attachment" == "$NETWORK|$network_id" ]] \
  || fail 'preserved S4 runtime network attachment differs from the verified S3 network'

container_names="$(docker_control ps -a --format '{{.Names}}' --filter "name=$RUNTIME_CONTAINER")" || fail 'cannot check S5 runtime-name collision'
while IFS= read -r existing_name; do [[ "$existing_name" != "$RUNTIME_CONTAINER" ]] || fail 'S5 runtime container name is already occupied'; done <<< "$container_names"

set -o noclobber
exec >"$ROOT/$RESULT_LOG" 2>&1
set +o noclobber
printf 'jit=%s\nmanifest-sha256=%s\nrunner-sha256=%s\n' "$JIT" "$APPROVED_MANIFEST_SHA256" "$APPROVED_RUNNER_SHA256"
printf '# H3REQ1 C03 startup smoke S5 — diagnostic continuation from verified S3 resources\n\n'
printf 'scope=Pages/workerd startup and healthz only; reused S3 snapshot/dependency volumes; no egress, DB, PostgREST, Edge, SQL, Auth, email, or remotes\n'
sha256sum -c "$MANIFEST"
printf 'phase=s3-resources|error_code=OK\nphase=s3-network-id-resolution|error_code=OK\n'

sanitize_output() {
  local line category
  while IFS= read -r line || [[ -n "$line" ]]; do
    category=''
    case "$line" in
      'phase=runtime-diagnostic-synthetic|error_code=PASS') category='synthetic-diagnostic' ;;
      'runtime-stage=dependency-roots-present'|'runtime-stage=runtime-ready') category='runtime-stage' ;;
      'healthz=PASS workerd=true attempts='[0-9]*) category='healthz-pass' ;;
      'healthz=NO-GO reason=runtime-not-ready attempts='[0-9]*) category='healthz-fail' ;;
      'runtime-last-stage=runtime-process-start'|'runtime-last-stage=dependency-roots-present'|'runtime-last-stage=runtime-ready') category='runtime-last-stage' ;;
      'runtime-error-class=PERMISSION'|'runtime-error-class=MODULE_RESOLUTION'|'runtime-error-class=ADDRESS_IN_USE' \
        |'runtime-error-class=RESOURCE_EXHAUSTION'|'runtime-error-class=TLS'|'runtime-error-class=WORKERD' \
        |'runtime-error-class=ASSERTION'|'runtime-error-class=MISSING_FILE'|'runtime-error-class=ERROR' \
        |'runtime-error-class=ASSERTIONERROR'|'runtime-error-class=TYPEERROR'|'runtime-error-class=REFERENCEERROR' \
        |'runtime-error-class=SYNTAXERROR'|'runtime-error-class=RANGEERROR'|'runtime-error-class=SENSITIVE_REDACTED') category='runtime-error-class' ;;
      'runtime-spawn-error='[A-Z0-9_]*) category='runtime-spawn-error' ;;
      'runtime-project-frame=line:'[0-9]*':column:'[0-9]*) category='runtime-project-frame' ;;
      'runtime-exit=code:'[0-9]*' signal:none'|'runtime-exit=code:null signal:'[A-Z]*) category='runtime-exit' ;;
      runtime-probe-error=type:[A-Z0-9_]*\|code:[A-Z0-9_]*) category='runtime-probe-error' ;;
      'runtime-stop=grace-period-expired; signal=SIGKILL') category='runtime-stop' ;;
      'smoke=PASS workerd-pages-healthz=true edge-runtime=not-started database=not-started') category='smoke-pass' ;;
      'smoke=NO-GO reason=runtime-exit-not-clean') category='smoke-fail' ;;
    esac
    if [[ -n "$category" ]]; then printf '%s\n' "$line"; else printf 'runtime-output-class=unclassified-line-suppressed\n'; fi
  done
  printf 'runtime-output-sanitization=allowlisted-events-only\n'
}

phase='one-shot-pages-workerd-runtime-healthz'
set +e
ACTIVE_CONTAINER="$RUNTIME_CONTAINER"
timeout --foreground --signal=TERM --kill-after=10s 180s docker run --pull=never --platform linux/amd64 \
  --name "$RUNTIME_CONTAINER" --network "$network_id" --log-driver none --read-only \
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
  --env H3_C03_ROOT=/candidate --env H3_C03_TOOLS_ROOT=/tools --env H3_C03_CERTS_ROOT=/run/c03-certs \
  --env H3_C03_WEB_DEPS_ROOT=/web-deps --env H3_C03_PRIVATE_ROOT=/run/c03-private \
  --env H3_C03_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" --env H3_C03_DEPENDENCY_BOOTSTRAP_COMPLETE=true \
  "$NODE_IMAGE" node /probe.mjs 2>&1 | sanitize_output
runtime_status=$?
set -e
if [[ "$runtime_status" -eq 124 || "$runtime_status" -eq 137 || "$runtime_status" -eq 143 || "$runtime_status" -eq 129 || "$runtime_status" -eq 130 ]]; then
  printf 'runtime-time-limit-reached; stopping only this new runtime container\n'
  stop_active_runtime || true
fi
runtime_metadata="$(docker_control inspect --format '{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}|{{.HostConfig.NetworkMode}}' "$RUNTIME_CONTAINER")" \
  || fail 'cannot verify S5 runtime exit'
IFS='|' read -r actual_name runtime_state runtime_exit oom jit manifest run network_mode <<< "$runtime_metadata"
[[ "$actual_name" == "/$RUNTIME_CONTAINER" && "$runtime_state" == exited && "$runtime_exit" =~ ^[0-9]+$ \
  && "$oom" == false && "$jit" == "$JIT" && "$manifest" == "$APPROVED_MANIFEST_SHA256" \
  && "$run" == "$RUN_NONCE" && "$network_mode" == "$network_id" ]] \
  || fail 'S5 runtime identity/state/exit predicate failed'
network_attachment="$(docker_control inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}|{{$v.NetworkID}}{{end}}' "$RUNTIME_CONTAINER")" \
  || fail 'cannot verify S5 runtime network attachment'
[[ "$network_attachment" == "$NETWORK|$network_id" ]] \
  || fail 'S5 runtime network attachment differs from the exact preflighted internal network ID'
ACTIVE_CONTAINER=''
printf 'container=%s state=%s|%s|%s network=internal-s3\n' "$RUNTIME_CONTAINER" "$runtime_state" "$runtime_exit" "$oom"
[[ "$runtime_status" -eq 0 && "$runtime_exit" == 0 ]] || fail 'Pages/workerd startup runtime failed'
grep -Fqx 'smoke=PASS workerd-pages-healthz=true edge-runtime=not-started database=not-started' "$RESULT_LOG" \
  || fail 'sanitized evidence lacks exact Pages/workerd healthz PASS'
printf 'phase=pages-workerd-healthz|error_code=OK\nexit=0\n'
printf '%s\n' 'Startup continuation: PASS (fresh real Miniflare/workerd Pages workers only).' \
  'S3 snapshot/dependency volumes and internal network remain preserved; no cleanup was performed.' \
  "Sanitized evidence: $RESULT_LOG"
trap - ERR
printf '%s\n' 'Startup continuation: PASS (fresh real Miniflare/workerd Pages workers only).' "Sanitized evidence: $RESULT_LOG" >&3
exec 3>&-
