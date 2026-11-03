#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S2'
readonly RUNNER='tests/h3req1_c03_startup_smoke_s2.sh'
readonly MANIFEST='tests/h3req1-c03-startup-smoke-s2.sha256'
readonly R4_MANIFEST='tests/h3req1-c03-integrated.sha256'
readonly R4_MANIFEST_SHA256='e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7'
readonly SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v3.sha256'
readonly SOURCE_MANIFEST_SHA256='4b6e99fb6feb85eb8b4ea8e899e69c2d3c497657b507b03004d45981b97417c8'
readonly BOOTSTRAP_OUTPUT_FILTER='tests/h3req1_c03_bootstrap_output_filter_s1.mjs'
readonly R4_LOG='.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log'
readonly D2_LOG='.context/evidencia/h3req1_c03_integrated_runtime_diag_2026-10-06_d2.log'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s2.md'
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly EXPECTED_DOCKER_CONTEXT='default'
readonly EXPECTED_DOCKER_ENDPOINT='unix:///var/run/docker.sock'
readonly EXPECTED_DOCKER_ENGINE='fc2115b2-c3c4-440e-89c6-26899eb7cb04|docker-desktop|Docker Desktop'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly SOURCE_VOLUME='h3req1-c03-startup-source-20261010-s2'
readonly TOOLS_VOLUME='h3req1-c03-startup-tools-20261010-s2'
readonly PAGES_VOLUME='h3req1-c03-startup-pages-20261010-s2'
readonly NETWORK='h3req1-c03-startup-net-20261010-s2'
readonly VOLUME_HOLDER='h3req1-c03-startup-volume-holder-20261010-s2'
readonly SNAPSHOT_CONTAINER='h3req1-c03-startup-snapshot-20261010-s2'
readonly TOOLS_CONTAINER='h3req1-c03-startup-tools-20261010-s2'
readonly PAGES_CONTAINER='h3req1-c03-startup-pages-20261010-s2'
readonly RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s2'
RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"
readonly RUN_NONCE
readonly -a EMPTY_PROXY_ENV=(
  --env HTTP_PROXY= --env HTTPS_PROXY= --env FTP_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env ftp_proxy= --env all_proxy= --env no_proxy= \
  --env npm_config_proxy= --env npm_config_http_proxy= --env npm_config_https_proxy=
)
ACTIVE_CONTAINER=''
STOP_ATTEMPTED_CONTAINER=''

[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" \
  && "${3:-}" == '--runner-sha256' && "${5:-}" == '--manifest-sha256' && $# -eq 6 ]] || {
  echo "Refusing to run: exact JIT $JIT, runner SHA-256, and manifest SHA-256 required." >&2
  exit 77
}
readonly APPROVED_RUNNER_SHA256="${4:-}"
readonly APPROVED_MANIFEST_SHA256="${6:-}"
[[ "$APPROVED_RUNNER_SHA256" =~ ^[a-f0-9]{64}$ ]] || { echo 'Refusing to run: invalid runner SHA-256.' >&2; exit 77; }
[[ "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] || { echo 'Refusing to run: invalid manifest SHA-256.' >&2; exit 77; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
[[ "$ROOT" == "$EXPECTED_ROOT" ]] || { echo 'Refusing to run: candidate checkout path changed.' >&2; exit 77; }
exec 3>&1
phase='preflight'
fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }
docker_control() { timeout --foreground --signal=TERM --kill-after=5s 20s docker "$@"; }
stop_new_container() {
  local metadata container_id jit_label manifest_label run_label
  case "${1:-}" in
    "$SNAPSHOT_CONTAINER"|"$TOOLS_CONTAINER"|"$PAGES_CONTAINER"|"$RUNTIME_CONTAINER") ;;
    *) printf 'Refusing stop outside S1 new-container allowlist.\n' >&2; return 2 ;;
  esac
  metadata="$(docker_control inspect --format '{{.Id}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$1")" \
    || { printf 'Refusing stop: ownership metadata unavailable for %s.\n' "$1" >&2; return 1; }
  IFS='|' read -r container_id jit_label manifest_label run_label <<< "$metadata"
  [[ "$container_id" =~ ^[a-f0-9]{64}$ && "$jit_label" == "$JIT" \
    && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" && "$run_label" == "$RUN_NONCE" ]] \
    || { printf 'Refusing stop: container ownership labels do not match this run for %s.\n' "$1" >&2; return 2; }
  if timeout --foreground --signal=TERM --kill-after=5s 20s docker stop --time 10 "$container_id" >/dev/null 2>&1; then
    printf 'bounded-stop=completed container=%s owner=verified; resource preserved\n' "$1"
  else
    printf 'bounded-stop=failed-or-timed-out container=%s; resource preserved\n' "$1"
    return 1
  fi
}
stop_active_container() {
  [[ -n "$ACTIVE_CONTAINER" ]] || return 0
  [[ "$ACTIVE_CONTAINER" != "$STOP_ATTEMPTED_CONTAINER" ]] || return 0
  STOP_ATTEMPTED_CONTAINER="$ACTIVE_CONTAINER"
  if stop_new_container "$ACTIVE_CONTAINER"; then
    printf 'bounded-stop=completed container=%s; resource preserved\n' "$ACTIVE_CONTAINER" >&2
  else
    printf 'bounded-stop=failed-or-timed-out container=%s; preserve resource and report NO-GO\n' "$ACTIVE_CONTAINER" >&2
  fi
}
on_error() {
  local status=$?
  stop_active_container
  printf 'Startup smoke halted phase=%s exit=%s; preserve all resources; no cleanup/resume.\n' "$phase" "$status" >&2
  printf 'Startup smoke halted phase=%s exit=%s; no cleanup/resume.\n' "$phase" "$status" >&3
}
on_signal() {
  local signal=$1 status=1
  case "$signal" in HUP) status=129 ;; INT) status=130 ;; TERM) status=143 ;; esac
  stop_active_container
  printf 'Startup smoke interrupted phase=%s signal=%s; preserve all resources.\n' "$phase" "$signal" >&2
  printf 'Startup smoke interrupted phase=%s signal=%s; no cleanup/resume.\n' "$phase" "$signal" >&3
  trap - ERR HUP INT TERM
  exit "$status"
}
trap on_error ERR
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

[[ -d "$ROOT/tests" && ! -L "$ROOT/tests" ]] || fail 'tests directory missing or symlinked'
[[ -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context" && ! -L "$ROOT/.context/evidencia" ]] || fail 'evidence directory missing or symlinked'
[[ -f "$ROOT/$MANIFEST" && ! -L "$ROOT/$MANIFEST" ]] || fail 'startup smoke manifest missing or symlinked'
[[ -f "$ROOT/$R4_MANIFEST" && ! -L "$ROOT/$R4_MANIFEST" ]] || fail 'R4 source manifest missing or symlinked'
[[ -f "$ROOT/$SOURCE_MANIFEST" && ! -L "$ROOT/$SOURCE_MANIFEST" ]] || fail 'startup source manifest missing or symlinked'
[[ -f "$ROOT/$BOOTSTRAP_OUTPUT_FILTER" && ! -L "$ROOT/$BOOTSTRAP_OUTPUT_FILTER" ]] || fail 'bootstrap output filter missing or symlinked'
[[ -f "$ROOT/$R4_LOG" && ! -L "$ROOT/$R4_LOG" && -f "$ROOT/$D2_LOG" && ! -L "$ROOT/$D2_LOG" ]] || fail 'R4/D2 evidence missing or symlinked'
[[ ! -e "$ROOT/$RESULT_LOG" && ! -L "$ROOT/$RESULT_LOG" ]] || fail "result path already exists: $RESULT_LOG"
ACTUAL_MANIFEST_SHA256="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"
[[ "$ACTUAL_MANIFEST_SHA256" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'startup smoke manifest differs from approved digest'
ACTUAL_RUNNER_SHA256="$(sha256sum "$RUNNER" | cut -d' ' -f1)"
[[ "$ACTUAL_RUNNER_SHA256" == "$APPROVED_RUNNER_SHA256" ]] || fail 'startup smoke runner differs from approved digest'
MANIFEST_RUNNER_SHA256="$(awk -v path="$RUNNER" '$2 == path { print $1 }' "$MANIFEST")"
[[ "$MANIFEST_RUNNER_SHA256" == "$ACTUAL_RUNNER_SHA256" ]] || fail 'startup smoke manifest does not pin the executing runner'
[[ "$(sha256sum "$R4_MANIFEST" | cut -d' ' -f1)" == "$R4_MANIFEST_SHA256" ]] || fail 'R4 source manifest digest changed'
[[ "$(sha256sum "$SOURCE_MANIFEST" | cut -d' ' -f1)" == "$SOURCE_MANIFEST_SHA256" ]] || fail 'startup source manifest digest changed'
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'
grep -Fqx 'NO-GO: runtime state timeout: healthz' "$R4_LOG" || fail 'R4 healthz failure evidence changed'
grep -Fqx 'runtime-state=exited' "$D2_LOG" || fail 'D2 runtime state evidence changed'
grep -Fqx 'runtime-exit-code=1' "$D2_LOG" || fail 'D2 exit evidence changed'
grep -Fqx 'runtime-oom-killed=false' "$D2_LOG" || fail 'D2 OOM evidence changed'
grep -Fqx 'runtime-log-driver=none' "$D2_LOG" || fail 'D2 log-driver evidence changed'

set -o noclobber
exec >"$ROOT/$RESULT_LOG" 2>&1
set +o noclobber
set -o pipefail
printf 'jit=%s\nmanifest-sha256=%s\n' "$JIT" "$APPROVED_MANIFEST_SHA256"
printf 'runner-sha256=%s\n' "$APPROVED_RUNNER_SHA256"
printf '# H3REQ1 C03 startup smoke S1\n\n'
printf 'scope=one fresh Pages/workerd startup smoke; no DB/PostgREST/Edge/SQL/Auth/email/remotes\n'
sha256sum -c "$MANIFEST" || fail 'startup smoke inputs do not match manifest'
sha256sum -c "$SOURCE_MANIFEST" || fail 'startup source inputs do not match pinned S1 source manifest'
command -v node >/dev/null 2>&1 || fail 'local Node.js is required for bounded bootstrap-output filtering'

check_free_container() {
  local requested=$1 existing matches
  matches="$(docker_control ps -a --format '{{.Names}}' --filter "name=$requested")" || fail 'cannot query exact candidate container-name collision'
  while IFS= read -r existing; do [[ "$existing" != "$requested" ]] || fail "new container name occupied: $requested"; done <<< "$matches"
}
verify_local_docker_context() {
  local context_name endpoint socket_path
  [[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] \
    || fail 'Docker endpoint override rejected; local Unix context only'
  context_name="$(docker_control context show)" || fail 'unable to determine Docker context within timeout'
  [[ "$context_name" == "$EXPECTED_DOCKER_CONTEXT" ]] || fail 'Docker context differs from the attested Docker Desktop context'
  endpoint="$(docker_control context inspect --format '{{ (index .Endpoints "docker").Host }}' "$context_name")" \
    || fail 'unable to read Docker context endpoint within timeout'
  [[ "$endpoint" == "$EXPECTED_DOCKER_ENDPOINT" ]] || fail 'Docker endpoint differs from the attested Docker Desktop socket'
  socket_path="${endpoint#unix://}"
  [[ -S "$socket_path" ]] || fail 'Docker endpoint is not a local Unix socket'
  export DOCKER_CONTEXT="$context_name"
  local engine_identity
  engine_identity="$(docker_control info --format '{{.ID}}|{{.Name}}|{{.OperatingSystem}}')" \
    || fail 'unable to verify the Docker Desktop engine identity within timeout'
  [[ "$engine_identity" == "$EXPECTED_DOCKER_ENGINE" ]] || fail 'Docker engine identity differs from the attested Docker Desktop daemon'
  printf 'docker-context=docker-desktop-wsl-attested\n'
}
check_free_volume() {
  local requested=$1 existing matches
  matches="$(docker_control volume ls --format '{{.Name}}' --filter "name=$requested")" || fail 'cannot query exact candidate volume-name collision'
  while IFS= read -r existing; do [[ "$existing" != "$requested" ]] || fail "new volume name occupied: $requested"; done <<< "$matches"
}
check_free_network() {
  local requested=$1 existing matches
  matches="$(docker_control network ls --format '{{.Name}}' --filter "name=$requested")" || fail 'cannot query exact candidate network-name collision'
  while IFS= read -r existing; do [[ "$existing" != "$requested" ]] || fail "new network name occupied: $requested"; done <<< "$matches"
}
assert_manifest_path() {
  local relative=$1 path="$ROOT" part
  local -a parts
  IFS='/' read -r -a parts <<< "$relative"
  for part in "${parts[@]}"; do
    path="$path/$part"
    [[ ! -L "$path" ]] || fail "symlinked startup input rejected: $relative"
  done
  [[ -f "$path" ]] || fail "startup input is not a regular file: $relative"
}
create_fresh_volume() {
  local requested=$1 requested_size=$2 created label options
  check_free_volume "$requested"
  created="$(docker_control volume create --driver local \
    --opt type=tmpfs --opt device=tmpfs --opt "o=nosuid,nodev,size=$requested_size" \
    --label "com.studiamatch.h3.startup.jit=$JIT" \
    --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.startup.run=$RUN_NONCE" "$requested")" || fail "unable to create fresh volume: $requested"
  [[ "$created" == "$requested" ]] || fail "unexpected volume name returned: $requested"
  label="$(docker_control volume inspect -f '{{ index .Labels "com.studiamatch.h3.startup.jit" }}|{{ index .Labels "com.studiamatch.h3.startup.manifest" }}|{{ index .Labels "com.studiamatch.h3.startup.run" }}' "$requested")" || fail "unable to verify new volume labels: $requested"
  [[ "$label" == "$JIT|$APPROVED_MANIFEST_SHA256|$RUN_NONCE" ]] || fail "volume labels do not match this run: $requested"
  options="$(docker_control volume inspect -f '{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}' "$requested")" || fail "unable to verify bounded tmpfs volume: $requested"
  [[ "$options" == "tmpfs|tmpfs|nosuid,nodev,size=$requested_size" ]] || fail "volume options are not the approved tmpfs cap: $requested"
}
inspect_exit() {
  local name=$1 expected_network=$2 metadata actual_name state exit_code oom_killed jit_label manifest_label run_label network_mode
  metadata="$(docker_control inspect --format '{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}|{{.HostConfig.NetworkMode}}' "$name")" || fail "cannot verify new container: $name"
  IFS='|' read -r actual_name state exit_code oom_killed jit_label manifest_label run_label network_mode <<< "$metadata"
  [[ "$actual_name" == "/$name" && "$state" =~ ^(exited|created|running)$ && "$exit_code" =~ ^[0-9]+$ \
    && ( "$oom_killed" == true || "$oom_killed" == false ) ]] || fail "container metadata outside safe schema: $name"
  [[ "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" && "$run_label" == "$RUN_NONCE" \
    && "$network_mode" == "$expected_network" ]] || fail "container identity/network does not match this run: $name"
  printf 'container=%s state=%s|%s|%s network=%s\n' "$name" "$state" "$exit_code" "$oom_killed" "$network_mode"
  [[ "$state|$exit_code|$oom_killed" == 'exited|0|false' ]] || fail "container did not exit cleanly: $name"
}
inspect_running_holder() {
  local metadata name state jit_label manifest_label run_label network_mode
  metadata="$(docker_control inspect --format '{{.Name}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}|{{.HostConfig.NetworkMode}}' "$VOLUME_HOLDER")" || fail 'cannot verify bounded tmpfs volume holder'
  IFS='|' read -r name state jit_label manifest_label run_label network_mode <<< "$metadata"
  [[ "$name" == "/$VOLUME_HOLDER" && "$state" == 'running' && "$network_mode" == 'none' \
    && "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" && "$run_label" == "$RUN_NONCE" ]] \
    || fail 'tmpfs volume holder identity/state differs from this run'
  printf 'volume-holder=%s state=running network=none\n' "$VOLUME_HOLDER"
}
run_bootstrap() {
  local name=$1; shift
  local status
  set +e
  ACTIVE_CONTAINER="$name"
  timeout --foreground --signal=TERM --kill-after=10s 600s "$@" 2>&1 | node "$ROOT/$BOOTSTRAP_OUTPUT_FILTER"
  status=$?
  set -e
  if [[ "$status" -eq 124 || "$status" -eq 137 || "$status" -eq 143 || "$status" -eq 129 || "$status" -eq 130 ]]; then
    printf 'bootstrap-time-limit-reached; stopping only new container=%s\n' "$name"
    stop_active_container || true
  fi
  [[ "$status" -eq 0 ]] || fail "fresh dependency bootstrap failed: $name (exit=$status)"
  inspect_exit "$name" bridge
  ACTIVE_CONTAINER=''
}
sanitize_output() {
  local line normalized category seen='|'
  while IFS= read -r line || [[ -n "$line" ]]; do
    normalized="${line,,}"
    if [[ "$normalized" == *token* || "$normalized" == *secret* || "$normalized" == *password* \
      || "$normalized" == *authorization* || "$normalized" == *api_key* || "$normalized" == *apikey* \
      || "$normalized" == *service_role* || "$normalized" == *publishable* || "$normalized" == *bearer* \
      || "$normalized" == *cookie* || "$normalized" == *hmac* || "$normalized" == *email* || "$normalized" == *jwt* ]]; then
      printf '[redacted sensitive diagnostic line]\n'
      continue
    fi
    category=''
    case "$normalized" in
      *healthz=pass*) category='healthz-pass' ;;
      *healthz=no-go*) category='healthz-fail' ;;
      *healthz=not-ready*) category='healthz-not-ready' ;;
      *dependency-bootstrap=both-locked-npm-ci-containers-exited-zero*) category='dependency-bootstrap' ;;
      *runtime-output-class=runtime-ready*|*runtime-output-class=dependency-digests-verified* \
        |*runtime-output-class=permission-denied*|*runtime-output-class=missing-file-or-directory* \
        |*runtime-output-class=module-resolution-failure*|*runtime-output-class=address-in-use* \
        |*runtime-output-class=resource-exhaustion*|*runtime-output-class=tls-bootstrap-failure* \
        |*runtime-output-class=workerd-startup-failure*|*runtime-output-class=runtime-assertion-failure* \
        |*runtime-output-class=local-transport-failure*|*runtime-output-class=dependency-roots-present* \
        |*runtime-output-class=unclassified* \
        |*runtime-output-class=redacted-sensitive-*) category='runtime-output' ;;
      *runtime-exit=*) category='runtime-exit' ;;
      *smoke=pass*) category='smoke-pass' ;;
      *smoke=no-go*) category='smoke-fail' ;;
      *dependency-digests-sha256=*) category='dependency-digests' ;;
    esac
    if [[ -n "$category" ]]; then
      printf '%s\n' "${line:0:1024}"
      seen+="$category|"
    else
      printf 'runtime-output-class=unclassified-line-suppressed\n'
    fi
  done
  printf 'runtime-output-sanitization=allowlisted-events-only\n'
}

verify_local_docker_context
for name in "$SNAPSHOT_CONTAINER" "$TOOLS_CONTAINER" "$PAGES_CONTAINER" "$RUNTIME_CONTAINER" "$VOLUME_HOLDER"; do check_free_container "$name"; done
for volume in "$SOURCE_VOLUME" "$TOOLS_VOLUME" "$PAGES_VOLUME"; do check_free_volume "$volume"; done
check_free_network "$NETWORK"
docker_control image inspect "$NODE_IMAGE" >/dev/null 2>&1 || fail 'pinned Node image is not already local; pulls are forbidden'

mapfile -t SNAPSHOT_FILES < <({ awk '{print $2}' "$SOURCE_MANIFEST"; printf '%s\n' "$SOURCE_MANIFEST"; } | sort -u)
for source_path in "${SNAPSHOT_FILES[@]}"; do
  [[ "$source_path" =~ ^[A-Za-z0-9._/-]+$ && "$source_path" != /* && "$source_path" != '.' && "/$source_path/" != *"/../"* ]] || fail "unsafe manifest path: $source_path"
  assert_manifest_path "$source_path"
done

phase='create-new-size-capped-tmpfs-volumes-and-offline-holder'
create_fresh_volume "$SOURCE_VOLUME" 96m
create_fresh_volume "$TOOLS_VOLUME" 768m
create_fresh_volume "$PAGES_VOLUME" 1024m
created_holder="$(docker_control run --detach --pull=never --platform linux/amd64 \
  --name "$VOLUME_HOLDER" --network none --log-driver none --read-only --cpus=0.1 --memory=64m --memory-swap=64m --pids-limit=16 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
    --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,nosuid,size=8m \
  --mount "type=volume,src=$SOURCE_VOLUME,dst=/source,readonly" \
  --mount "type=volume,src=$TOOLS_VOLUME,dst=/tools,readonly" \
  --mount "type=volume,src=$PAGES_VOLUME,dst=/pages,readonly" \
  "$NODE_IMAGE" sh -lc 'exec sleep infinity')" || fail 'unable to start offline tmpfs holder'
[[ "$created_holder" =~ ^[a-f0-9]{12,64}$ ]] || fail 'unexpected holder container identity'
inspect_running_holder

phase='create-new-source-snapshot'
set +e
ACTIVE_CONTAINER="$SNAPSHOT_CONTAINER"
tar -C "$ROOT" --no-recursion -cf - -- "${SNAPSHOT_FILES[@]}" |
  timeout --foreground --signal=TERM --kill-after=5s 120s docker run --pull=never --platform linux/amd64 --interactive --log-driver none \
    --name "$SNAPSHOT_CONTAINER" --network none --read-only --cpus=1 --memory=1g --memory-swap=1g --pids-limit=128 \
    --cap-drop=ALL --security-opt no-new-privileges:true \
    "${EMPTY_PROXY_ENV[@]}" \
     --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
     --tmpfs /tmp:rw,nosuid,size=32m --mount "type=volume,src=$SOURCE_VOLUME,dst=/snapshot" \
    --env H3_C03_EXPECTED_SOURCE_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" \
    "$NODE_IMAGE" sh -lc 'set -eu; test -z "$(find /snapshot -mindepth 1 -print -quit)"; tar -xf - -C /snapshot; cd /snapshot; if find . -type l -print -quit | grep -q .; then exit 41; fi; actual="$(sha256sum tests/h3req1-c03-startup-source-s1-v3.sha256)"; actual="${actual%% *}"; test "$actual" = "$H3_C03_EXPECTED_SOURCE_MANIFEST_SHA256"; sha256sum -c tests/h3req1-c03-startup-source-s1-v3.sha256 >/dev/null' \
    >/dev/null 2>&1
snapshot_status=$?
set -e
if [[ "$snapshot_status" -eq 124 || "$snapshot_status" -eq 137 || "$snapshot_status" -eq 143 || "$snapshot_status" -eq 129 || "$snapshot_status" -eq 130 ]]; then
  printf 'snapshot-time-limit-reached; stopping only new container=%s\n' "$SNAPSHOT_CONTAINER"
  stop_active_container || true
fi
[[ "$snapshot_status" -eq 0 ]] || fail "new source snapshot failed; safe output suppressed (exit=$snapshot_status)"
inspect_exit "$SNAPSHOT_CONTAINER" none
ACTIVE_CONTAINER=''

phase='fresh-npm-workerd-tools-bootstrap-with-registry-egress'
run_bootstrap "$TOOLS_CONTAINER" docker run --pull=never --platform linux/amd64 \
  --name "$TOOLS_CONTAINER" --network bridge --log-driver none --read-only --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  "${EMPTY_PROXY_ENV[@]}" \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,nosuid,size=512m --mount "type=volume,src=$SOURCE_VOLUME,dst=/source,readonly" \
  --mount "type=volume,src=$TOOLS_VOLUME,dst=/out" --workdir /out --env HOME=/tmp --env npm_config_cache=/tmp/npm-cache \
  "$NODE_IMAGE" sh -lc 'cp /source/tests/h3req1-c03-bootstrap/package.json /source/tests/h3req1-c03-bootstrap/package-lock.json /out/ && npm ci --no-audit --no-fund --foreground-scripts --fetch-retries=0 --registry=https://registry.npmjs.org/'

phase='fresh-pages-dependency-bootstrap-with-registry-egress'
run_bootstrap "$PAGES_CONTAINER" docker run --pull=never --platform linux/amd64 \
  --name "$PAGES_CONTAINER" --network bridge --log-driver none --read-only --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  "${EMPTY_PROXY_ENV[@]}" \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,nosuid,size=512m --mount "type=volume,src=$SOURCE_VOLUME,dst=/source,readonly" \
  --mount "type=volume,src=$PAGES_VOLUME,dst=/out" --workdir /out --env HOME=/tmp --env npm_config_cache=/tmp/npm-cache \
  "$NODE_IMAGE" sh -lc 'cp /source/web/package.json /source/web/package-lock.json /out/ && cp -a /source/web/vendor /out/vendor && npm ci --omit=dev --ignore-scripts --no-audit --no-fund --fetch-retries=0 --registry=https://registry.npmjs.org/'

phase='create-new-egress-blocked-internal-network'
check_free_network "$NETWORK"
created_network="$(docker_control network create --internal --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" --label "com.studiamatch.h3.startup.run=$RUN_NONCE" "$NETWORK")" || fail 'unable to create isolated internal network'
[[ "$created_network" == "$NETWORK" ]] || fail 'unexpected network name returned'
network_labels="$(docker_control network inspect -f '{{ index .Labels "com.studiamatch.h3.startup.jit" }}|{{ index .Labels "com.studiamatch.h3.startup.manifest" }}|{{ index .Labels "com.studiamatch.h3.startup.run" }}' "$NETWORK")" || fail 'unable to verify new network labels'
[[ "$network_labels" == "$JIT|$APPROVED_MANIFEST_SHA256|$RUN_NONCE" ]] || fail 'network labels do not match this run'
network_metadata="$(docker_control network inspect -f '{{.Name}}|{{.Driver}}|{{.Internal}}' "$NETWORK")" || fail 'unable to verify internal network mode'
[[ "$network_metadata" == "$NETWORK|bridge|true" ]] || fail 'runtime network is not the approved internal bridge network'

phase='one-shot-real-workerd-pages-startup-smoke'
inspect_running_holder
set +e
ACTIVE_CONTAINER="$RUNTIME_CONTAINER"
timeout --foreground --signal=TERM --kill-after=10s 180s docker run --pull=never --platform linux/amd64 --name "$RUNTIME_CONTAINER" \
  --network "$NETWORK" --log-driver none --read-only --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 --stop-timeout 10 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  "${EMPTY_PROXY_ENV[@]}" \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m --tmpfs /run/c03-private:rw,noexec,nosuid,size=8m \
  --tmpfs /run/c03-certs:rw,nosuid,size=16m \
  --mount "type=volume,src=$SOURCE_VOLUME,dst=/candidate,readonly" \
  --mount "type=volume,src=$TOOLS_VOLUME,dst=/tools,readonly" --mount "type=volume,src=$PAGES_VOLUME,dst=/web-deps,readonly" \
  --env H3_C03_ROOT=/candidate --env H3_C03_TOOLS_ROOT=/tools --env H3_C03_CERTS_ROOT=/run/c03-certs \
  --env H3_C03_WEB_DEPS_ROOT=/web-deps --env H3_C03_PRIVATE_ROOT=/run/c03-private \
  --env H3_C03_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" \
  --env H3_C03_DEPENDENCY_BOOTSTRAP_COMPLETE=true \
  "$NODE_IMAGE" node /candidate/tests/h3req1_c03_startup_smoke_s1.mjs 2>&1 | sanitize_output
runtime_status=$?
set -e
if [[ "$runtime_status" -eq 124 || "$runtime_status" -eq 137 || "$runtime_status" -eq 143 || "$runtime_status" -eq 129 || "$runtime_status" -eq 130 ]]; then
  printf 'runtime-time-limit-reached; stopping only new runtime container=%s\n' "$RUNTIME_CONTAINER"
  stop_active_container || true
fi
inspect_exit "$RUNTIME_CONTAINER" "$NETWORK"
ACTIVE_CONTAINER=''
[[ "$runtime_status" -eq 0 ]] || fail "one-shot workerd startup smoke failed (exit=$runtime_status)"
grep -Fqx 'smoke=PASS workerd-pages-healthz=true edge-runtime=not-started database=not-started' "$RESULT_LOG" || fail 'sanitized evidence lacks the exact startup smoke PASS'
printf '%s\n' 'Startup smoke: PASS (fresh real Miniflare/workerd Pages workers only).' \
  'All new containers, volumes, and network are preserved; no cleanup/resume was performed.' \
  "Sanitized evidence: $RESULT_LOG"
trap - ERR
printf '%s\n' 'Startup smoke: PASS (fresh real Miniflare/workerd Pages workers only).' "Sanitized evidence: $RESULT_LOG" >&3
exec 3>&-
