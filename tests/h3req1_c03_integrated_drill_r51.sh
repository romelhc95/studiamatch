#!/usr/bin/env bash
set -Eeuo pipefail
readonly JIT='H3-CLOSE-03-INTEGRATED-2026-10-10-R51'
readonly MANIFEST='tests/h3req1-c03-integrated-r51.sha256'
[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" && "${3:-}" == '--manifest-sha256' && $# -eq 4 ]] || { echo "Refusing to run: exact JIT $JIT and approved manifest SHA-256 required." >&2; exit 77; }
readonly APPROVED_MANIFEST_SHA256="${4:-}"
[[ "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] || { echo 'Refusing to run: invalid manifest SHA-256.' >&2; exit 77; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
exec 3>&1

readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EDGE_NETWORK='h3req1-c03-integrated-edge-20261010-r51'
readonly DATA_NETWORK='h3req1-c03-integrated-data-20261010-r51'
readonly PG='h3req1-c03-integrated-pg17-20261010-r51'
readonly POSTGREST='h3req1-c03-integrated-postgrest-20261010-r51'
readonly RUNTIME='h3req1-c03-integrated-runtime-20261010-r51'
readonly EDGE_ACTIVE='h3req1-c03-integrated-edge-active-20261010-r51'
readonly EDGE_SUSPENDED='h3req1-c03-integrated-edge-suspended-20261010-r51'
readonly TLS_VOLUME='h3req1-c03-integrated-tls-20261010-r51'
readonly CACHE_VERIFY='h3req1-c03-dependency-cache-verify-20261010-r51'
readonly SNAPSHOT_BOOTSTRAP='h3req1-c03-source-snapshot-20261010-r51'
readonly CONTRACT_TEST='h3req1-c03-runner-contract-test-20261010-r51'
readonly SOURCE_SNAPSHOT='h3req1-c03-integrated-source-snapshot-20261010-r51'
# Read-only dependency caches produced and verified by the preserved R4 run.
readonly TOOLS_MODULES='h3req1-c03-integrated-miniflare-node-modules-20261006-r4'
readonly WEB_MODULES='h3req1-g08-web-node-modules-r1'
readonly DENO_CACHE='h3req1-c03-integrated-edge-deno-cache-20261006-r5'
readonly EDGE_NODE_MODULES='h3req1-c03-integrated-edge-node-modules-20261006-r5'
readonly R4_JIT='H3-CLOSE-03-INTEGRATED-2026-10-06-R4'
readonly R4_MANIFEST_SHA256='e5d72e06b04fcfd3f68abaeea77fef81c982f24e20e587732de65b63b58167a7'
readonly EXPECTED_DEPENDENCY_DIGESTS='{"deno-cache":"0caf7782e6c39a383c41871d5d8bc62801c5ebd369ffd9400542fa9c9000c2ff","edge-node-modules":"00448e894ad63e0bc4d1f5a26cc92369a2d8cc9a882817a57d2a6c69ffe558c3","miniflare-node-modules":"637d7c16a194ec553e6cec3cd07efa1d06ba4a323a40f3ef72062f758e70088f","pages-node-modules":"ea36c13c72f0b1c13f2791118b4eb7ad89c17ba9ecbce44d413b794e6837e625"}'
readonly EXPECTED_DOCKER_HOST='unix:///var/run/docker.sock'
readonly EXPECTED_DOCKER_ID='fc2115b2-c3c4-440e-89c6-26899eb7cb04'
readonly EXPECTED_DOCKER_VERSION='29.8.2'
readonly DOCKER_BIN='/usr/bin/docker'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_integrated_run_2026-10-10_r51.txt'
readonly PG_IMAGE='postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly POSTGREST_IMAGE='postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly EDGE_IMAGE='supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09'
readonly JWT_SEED='Studiamatch H3REQ1 C03 disposable PostgREST JWT fixture 2026-10-06'
readonly SERVICE_SEED='Studiamatch H3REQ1 C03 service fixture 2026-10-06'
readonly QUOTA_SEED='Studiamatch H3REQ1 C03 admin quota fixture 2026-10-06'
RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"
readonly RUN_NONCE
phase='preflight'
DOCKER_TARGET_VERIFIED=0
docker() {
  local -a docker_target=()
  if (( DOCKER_TARGET_VERIFIED == 1 )); then
    docker_target=(--host "$EXPECTED_DOCKER_HOST")
  fi
  /usr/bin/timeout --foreground --signal=TERM --kill-after=3s 60s \
    "$DOCKER_BIN" "${docker_target[@]}" "$@"
}
bounded_docker() {
  local seconds=$1
  local -a docker_target=()
  shift
  if (( DOCKER_TARGET_VERIFIED == 1 )); then
    docker_target=(--host "$EXPECTED_DOCKER_HOST")
  fi
  /usr/bin/timeout --foreground --signal=TERM --kill-after=3s "${seconds}s" \
    "$DOCKER_BIN" "${docker_target[@]}" "$@"
}
bounded_exec() {
  local container=$1 seconds=$2 outer_seconds
  local -a docker_target=()
  shift 2
  outer_seconds=$((seconds + 10))
  if (( DOCKER_TARGET_VERIFIED == 1 )); then
    docker_target=(--host "$EXPECTED_DOCKER_HOST")
  fi
  /usr/bin/timeout --foreground --signal=TERM --kill-after=3s "${outer_seconds}s" \
    "$DOCKER_BIN" "${docker_target[@]}" exec "$container" \
      /usr/bin/timeout --foreground --signal=TERM --kill-after=3s "${seconds}s" "$@"
}
stop_owned_running_services_best_effort() {
  (( DOCKER_TARGET_VERIFIED == 1 )) || return 0
  local requested metadata container_id state jit_label manifest_label run_label
  local -a container_ids=()
  for requested in "$EDGE_SUSPENDED" "$EDGE_ACTIVE" "$POSTGREST" "$PG" "$RUNTIME" \
    "$CONTRACT_TEST" "$CACHE_VERIFY" "$SNAPSHOT_BOOTSTRAP"; do
    if ! metadata="$(bounded_docker 5 inspect -f '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}|{{index .Config.Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.c03.run"}}' "$requested" 2>/dev/null)"; then
      continue
    fi
    IFS='|' read -r container_id state jit_label manifest_label run_label <<< "$metadata"
    if [[ "$container_id" =~ ^[a-f0-9]{64}$ && "$state" == 'running' \
      && "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" \
      && "$run_label" == "$RUN_NONCE" ]]; then
      container_ids+=("$container_id")
    fi
  done
  if ((${#container_ids[@]})); then
    if bounded_docker 20 stop --time 3 "${container_ids[@]}" >/dev/null 2>&1; then
      printf 'failure-stop=completed exact_run_containers=%s\n' "${#container_ids[@]}"
    else
      printf 'failure-stop=timeout-or-failed exact_run_containers=%s\n' "${#container_ids[@]}"
    fi
  else
    printf 'failure-stop=no-matching-running-run-containers\n'
  fi
}
on_error() {
  local status=$?
  trap - ERR HUP INT TERM
  stop_owned_running_services_best_effort
  printf 'Halted phase=%s exit=%s; matching run-owned services were stopped if still active; resources are preserved.\n' "$phase" "$status" >&2
  printf 'C03 integrated drill halted in phase=%s (exit=%s); matching run-owned services were stopped if still active.\n' "$phase" "$status" >&3
  exit "$status"
}
on_signal() {
  local signal=$1 status
  case "$signal" in
    HUP) status=129 ;;
    INT) status=130 ;;
    TERM) status=143 ;;
    *) status=1 ;;
  esac
  trap - ERR HUP INT TERM
  stop_owned_running_services_best_effort
  printf 'Interrupted phase=%s signal=%s exit=%s; matching run-owned services were stopped if still active; resources are preserved.\n' "$phase" "$signal" "$status" >&2
  printf 'C03 integrated drill interrupted in phase=%s (signal=%s); matching run-owned services were stopped if still active.\n' "$phase" "$signal" >&3
  exit "$status"
}
trap on_error ERR
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
fail() {
  printf 'NO-GO: %s\n' "$1" >&2
  stop_owned_running_services_best_effort
  exit 1
}
sanitize_dynamic_output() {
  local line normalized
  while IFS= read -r line || [[ -n "$line" ]]; do
    normalized="${line,,}"
    if [[ "$normalized" == *token* || "$normalized" == *secret* || "$normalized" == *password* \
      || "$normalized" == *authorization* || "$normalized" == *api_key* || "$normalized" == *apikey* \
      || "$normalized" == *service_role_key* || "$normalized" == *publishable_key* || "$normalized" == *anon_key* \
      || "$normalized" == *bearer* || "$normalized" == *eyj* ]]; then
      printf '[redacted sensitive output line]\n'
      continue
    fi
    printf '%s\n' "$line" | sed -E \
      -e 's/(eyJhbG[A-Za-z0-9_-]{10,}|sb_publishable_[A-Za-z0-9_-]{20,}|sb_secret_[A-Za-z0-9_-]{10,}|sbp_[A-Za-z0-9_-]{10,}|sk-(proj-)?[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|ghs_[A-Za-z0-9]{20,}|opencode_[A-Za-z0-9_-]{20,}|oc_[A-Za-z0-9_-]{30,})/[REDACTED credential-like value]/g' \
      -e 's/[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/[REDACTED JWT]/g' \
      -e 's#([A-Za-z][A-Za-z0-9+.-]*://)[^/@[:space:]]+(:[^/@[:space:]]*)?@#\1[REDACTED]@#g' \
      -e 's/(Bearer[[:space:]]+)[A-Za-z0-9._~+\/=-]+/\1[REDACTED]/Ig'
  done
}
if ! ACTUAL_MANIFEST_SHA256="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"; then fail 'unable to hash integrated manifest'; fi
[[ "$ACTUAL_MANIFEST_SHA256" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'manifest bytes differ from the SHA-256 approved in the JIT'
check_free_container() {
  local requested=$1 matches existing
  matches="$(docker ps -a --format '{{.Names}}' --filter "name=$requested")" || fail 'unable to list matching container names'
  while IFS= read -r existing; do
    [[ "$existing" != "$requested" ]] || fail "container name occupied: $requested"
  done <<< "$matches"
}
check_free_volume() {
  local requested=$1 matches existing
  matches="$(docker volume ls --format '{{.Name}}' --filter "name=$requested")" || fail "unable to list matching volume names: $requested"
  while IFS= read -r existing; do
    [[ "$existing" != "$requested" ]] || fail "volume name occupied: $requested"
  done <<< "$matches"
}
create_fresh_volume() {
  local requested=$1 created run_label
  check_free_volume "$requested"
  created="$(docker volume create \
    --label "com.studiamatch.h3.c03.jit=$JIT" \
    --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.c03.run=$RUN_NONCE" "$requested")" || fail "unable to create fresh volume: $requested"
  [[ "$created" == "$requested" ]] || fail "Docker returned an unexpected volume name: $requested"
  run_label="$(docker volume inspect -f '{{ index .Labels "com.studiamatch.h3.c03.run" }}' "$requested")" || fail "unable to verify new volume label: $requested"
  [[ "$run_label" == "$RUN_NONCE" ]] || fail "volume was not created by this exact invocation: $requested"
}
verify_docker_target() {
  local active_context endpoint target details engine_id operating_system server_version memory_bytes cpu_count
  [[ ! -v DOCKER_HOST && ! -v DOCKER_CONTEXT ]] || fail 'Docker environment override is present'
  active_context="$(docker context show)" || fail 'unable to read Docker context'
  endpoint="$(docker context inspect default --format '{{.Endpoints.docker.Host}}')" || fail 'unable to read Docker endpoint'
  target="$(docker info --format '{{.ID}}|{{.OperatingSystem}}|{{.ServerVersion}}|{{.MemTotal}}|{{.NCPU}}')" || fail 'unable to read Docker daemon identity'
  [[ "$active_context" == 'default' && "$endpoint" == "$EXPECTED_DOCKER_HOST" ]] || fail 'Docker context or endpoint differs from the attested local Docker Desktop target'
  IFS='|' read -r engine_id operating_system server_version memory_bytes cpu_count <<< "$target"
  [[ "$engine_id" == "$EXPECTED_DOCKER_ID" && "$operating_system" == 'Docker Desktop' \
    && "$server_version" == "$EXPECTED_DOCKER_VERSION" ]] || fail 'Docker daemon identity differs from the attested local engine'
  [[ "$memory_bytes" =~ ^[0-9]+$ && "$cpu_count" =~ ^[0-9]+$ ]] || fail 'Docker capacity metadata is invalid'
  (( memory_bytes >= 10737418240 && cpu_count >= 8 )) || fail 'Docker capacity is below the aggregate bounded C03 fixture budget'
  DOCKER_TARGET_VERIFIED=1
  printf 'Docker target PASS: context=%s endpoint=%s engine=%s server=%s memory_bytes=%s cpu_count=%s\n' \
    "$active_context" "$endpoint" "$engine_id" "$server_version" "$memory_bytes" "$cpu_count"
}
verify_r4_cache_volume() {
  local requested=$1 labels active_users
  labels="$(docker volume inspect -f '{{.Driver}}|{{index .Labels "com.studiamatch.h3.c03.jit"}}|{{index .Labels "com.studiamatch.h3.c03.manifest"}}' "$requested")" \
    || fail "unable to inspect preserved dependency cache labels: $requested"
  [[ "$labels" == "local|$R4_JIT|$R4_MANIFEST_SHA256" ]] || fail "preserved dependency cache provenance mismatch: $requested"
  active_users="$(docker ps --filter "volume=$requested" --format '{{.Names}}')" || fail "unable to check active dependency cache consumers: $requested"
  [[ -z "$active_users" ]] || fail "preserved dependency cache is mounted by a running container: $requested"
}
verify_current_web_module_volume() {
  local metadata active_users
  metadata="$(docker volume inspect -f '{{.Name}}|{{.Driver}}|{{json .Options}}|{{json .Labels}}' "$WEB_MODULES")" \
    || fail 'unable to inspect current web dependency volume'
  [[ "$metadata" == "$WEB_MODULES|local|null|null" ]] || fail 'current web dependency volume identity/options/labels differ'
  active_users="$(docker ps --filter "volume=$WEB_MODULES" --format '{{.Names}}')" || fail 'unable to check current web dependency volume consumers'
  [[ -z "$active_users" ]] || fail 'current web dependency volume is mounted by an active container'
}
record_container() {
  local requested=$1 metadata
  metadata="$(docker inspect -f '{{.Id}}|{{.Image}}|{{.State.Status}}|{{.HostConfig.Memory}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.PidsLimit}}' "$requested")" \
    || fail "unable to read safe container metadata: $requested"
  printf 'container=%s metadata=%s\n' "$requested" "$metadata"
}
cleanup_run_containers_and_networks() {
  local requested container_state container_id state network_state network_id internal attached jit_label manifest_label run_label
  for requested in "$EDGE_SUSPENDED" "$EDGE_ACTIVE" "$POSTGREST" "$PG" "$RUNTIME" "$CACHE_VERIFY" "$SNAPSHOT_BOOTSTRAP"; do
    container_state="$(docker inspect -f '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}|{{index .Config.Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.c03.run"}}' "$requested")" \
      || fail "unable to read cleanup identity/state: $requested"
    IFS='|' read -r container_id state jit_label manifest_label run_label <<< "$container_state"
    [[ "$container_id" =~ ^[a-f0-9]{64}$ && "$state" == 'exited' \
      && "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" \
      && "$run_label" == "$RUN_NONCE" ]] \
      || fail "refusing to remove a container outside this completed run: $requested"
    docker rm "$container_id" >/dev/null || fail "unable to remove exact completed run container: $requested"
    printf 'removed-run-container=%s id=%s\n' "$requested" "$container_id"
  done
  for requested in "$EDGE_NETWORK" "$DATA_NETWORK"; do
    network_state="$(docker network inspect -f '{{.Id}}|{{.Internal}}|{{len .Containers}}|{{index .Labels "com.studiamatch.h3.c03.jit"}}|{{index .Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Labels "com.studiamatch.h3.c03.run"}}' "$requested")" \
      || fail "unable to inspect exact run network before removal: $requested"
    IFS='|' read -r network_id internal attached jit_label manifest_label run_label <<< "$network_state"
    [[ "$network_id" =~ ^[a-f0-9]{64}$ && "$internal" == 'true' && "$attached" == '0' \
      && "$jit_label" == "$JIT" && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" && "$run_label" == "$RUN_NONCE" ]] \
      || fail "refusing to remove a network outside this completed run: $requested"
    docker network rm "$network_id" >/dev/null || fail "unable to remove exact internal run network: $requested"
    printf 'removed-run-network=%s id=%s internal=true attached=0\n' "$requested" "$network_id"
  done
}
create_internal_network() {
  local requested=$1 created details
  created="$(docker network create --internal \
    --label "com.studiamatch.h3.c03.jit=$JIT" \
    --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.c03.run=$RUN_NONCE" "$requested")" || fail "unable to create internal network: $requested"
  [[ "$created" =~ ^[0-9a-f]{64}$ ]] || fail "Docker returned an invalid network identifier: $requested"
  details="$(docker network inspect -f '{{.Id}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.c03.run"}}' "$requested")" || fail "unable to verify internal network: $requested"
  [[ "$details" == "$created|true|$RUN_NONCE" ]] || fail "new internal network attestation failed: $requested"
  printf 'network=%s id=%s internal=true\n' "$requested" "$created"
}
control() {
  local command=$1 seconds=${2:-60}
  bounded_exec "$RUNTIME" "$seconds" node /candidate/tests/h3req1_c03_integrated_runtime.mjs --control "$command" 2>&1 | sanitize_dynamic_output
}
wait_control() {
  local command=$1 i runtime_state runtime_status runtime_exit runtime_oom
  for ((i=0; i<60; i+=1)); do
    if control "$command" 5 >/dev/null 2>&1; then return 0; fi
    if runtime_state="$(docker inspect -f '{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}' "$RUNTIME" 2>/dev/null)"; then
      IFS='|' read -r runtime_status runtime_exit runtime_oom <<< "$runtime_state"
      if [[ "$runtime_status" == 'exited' || "$runtime_status" == 'dead' ]]; then
        fail "runtime exited before control readiness: status=$runtime_status exit=$runtime_exit oom=$runtime_oom command=$command"
      fi
    else
      fail 'runtime state could not be inspected during readiness polling'
    fi
    sleep 1
  done
  fail "runtime readiness poll limit exhausted: $command"
}
run_sql() {
  local path=$1 label=$2 sql_output sql_status sqlstate failure_code line
  if sql_output="$(bounded_exec "$PG" 90 psql -X -q -U postgres -d h3_c03_chain \
      -v VERBOSITY=verbose -v ON_ERROR_STOP=1 -o /dev/null -f "/candidate/$path" 2>&1)"; then
    printf '%s PASS (psql exit=0)\n' "$label"
    return 0
  else
    sql_status=$?
  fi
  if (( sql_status == 124 || sql_status == 137 )); then
    failure_code='TIMEOUT'
  else
    sqlstate=''
    while IFS= read -r line; do
      if [[ "$line" =~ ^psql:.*:[0-9]+:[[:space:]]+ERROR:[[:space:]]+([A-Z0-9]{5}): ]]; then
        sqlstate="${BASH_REMATCH[1]}"
      elif [[ "$line" =~ ^ERROR:[[:space:]]+([A-Z0-9]{5}): ]]; then
        sqlstate="${BASH_REMATCH[1]}"
      elif [[ "$line" =~ ^SQL\ state:\ ([A-Z0-9]{5})$ ]]; then
        sqlstate="${BASH_REMATCH[1]}"
      fi
    done <<< "$sql_output"
    if [[ "$sqlstate" =~ ^(H3S[0-9]{2}|[A-Z0-9]{5})$ ]]; then
      failure_code="$sqlstate"
    else
      failure_code='UNCLASSIFIED'
    fi
  fi
  printf 'sql-gate-failure|label=%s|exit=%s|code=%s\n' "$label" "$sql_status" "$failure_code" >&2
  fail "SQL gate failed or exceeded its 90-second deadline: $label"
}
stop_run_services() {
  local requested metadata container_id state jit_label manifest_label run_label
  local -a container_ids=()
  for requested in "$EDGE_SUSPENDED" "$EDGE_ACTIVE" "$POSTGREST" "$PG" "$RUNTIME"; do
    metadata="$(docker inspect -f '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}|{{index .Config.Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.c03.run"}}' "$requested")" \
      || fail "unable to inspect service before stop: $requested"
    IFS='|' read -r container_id state jit_label manifest_label run_label <<< "$metadata"
    [[ "$container_id" =~ ^[a-f0-9]{64}$ && "$jit_label" == "$JIT" \
      && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" && "$run_label" == "$RUN_NONCE" ]] \
      || fail "service ownership changed before stop: $requested"
    if [[ "$state" == 'running' ]]; then
      container_ids+=("$container_id")
    elif [[ "$state" != 'exited' ]]; then
      fail "service is not in a stoppable state: $requested"
    fi
  done
  if ((${#container_ids[@]})); then
    bounded_docker 180 stop --time 30 "${container_ids[@]}" >/dev/null \
      || fail 'bounded stop of completed run services failed'
  fi
}
start_edge() {
  local name=$1 alias=$2 safe=$3
  docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$name" \
    --label "com.studiamatch.h3.c03.jit=$JIT" \
    --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
    --network "$EDGE_NETWORK" --network-alias "$alias" --read-only \
    --memory=1g --memory-swap=1g --cpus=1 --pids-limit=256 \
    --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
    --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache,readonly" \
    --mount "type=volume,src=$EDGE_NODE_MODULES,dst=/candidate/supabase/functions/admin-invite/node_modules,readonly" \
    --mount "type=volume,src=$TLS_VOLUME,dst=/run/c03-certs,readonly" \
    --tmpfs /tmp:rw,noexec,nosuid,size=256m \
    --env DENO_DIR=/deno-cache --env DENO_CERT=/tmp/ca-bundle.pem \
    --env DENO_TLS_CA_STORE=system --env SSL_CERT_FILE=/tmp/ca-bundle.pem \
    --env SUPABASE_URL=https://local.supabase.co:5443/ \
    --env NEXT_SUPABASE_SECRET_KEY="sb_secret_$(printf '%s' "$SERVICE_SEED" | sha256sum | cut -d' ' -f1)" \
    --env ADMIN_QUOTA_HMAC_KEY="$(printf '%s' "$QUOTA_SEED" | sha256sum | cut -d' ' -f1)" \
    --env ADMIN_INVITE_SAFE_SUSPEND="$safe" \
    --env ADMIN_INVITE_ALLOWED_ORIGINS=https://admin.local.test \
    --env ADMIN_INVITE_ALLOWED_REDIRECTS=https://admin.local.test/admin/auth/callback/ \
    --env ADMIN_INVITE_REDIRECT_URL=https://admin.local.test/admin/auth/callback/ \
    --env ADMIN_INVITE_RECOVERY_REDIRECT_URL=https://admin.local.test/admin/auth/callback/ \
    --env APP_ENV=development --entrypoint sh "$EDGE_IMAGE" -lc \
    'cat /etc/ssl/certs/ca-certificates.crt /run/c03-certs/ca.pem > /tmp/ca-bundle.pem && test -s /tmp/ca-bundle.pem && exec edge-runtime start --main-service /candidate/tests/h3req1-c03-edge-main -p 9000' \
    >/dev/null 2>&1
  record_container "$name"
  local bundle_sha256
  bundle_sha256="$(bounded_exec "$name" 5 sh -lc 'sha256sum /tmp/ca-bundle.pem | cut -d" " -f1' 2>/dev/null)" \
    || fail 'synthetic/system CA bundle is not readable in the Edge container'
  [[ "$bundle_sha256" =~ ^[a-f0-9]{64}$ ]] || fail 'Edge CA bundle digest is not a safe SHA-256'
  printf 'Edge synthetic/system CA bundle SHA-256: %s\n' "$bundle_sha256"
}

[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'
[[ "$ROOT" == '/home/romel/src/studiamatch-h3req1-sync-20261002' ]] || fail 'candidate checkout path changed'
[[ -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context" && ! -L "$ROOT/.context/evidencia" ]] || fail 'evidence log directory is missing or symlinked'
[[ ! -e "$ROOT/$RESULT_LOG" && ! -L "$ROOT/$RESULT_LOG" ]] || fail "result log path already exists: $RESULT_LOG"
[[ -x /usr/bin/timeout ]] || fail 'host timeout utility is unavailable'
[[ -x "$DOCKER_BIN" ]] || fail 'fixed Docker CLI path is unavailable'
set -o noclobber
exec >"$ROOT/$RESULT_LOG" 2>&1
set +o noclobber
printf 'candidate=%s branch=%s head=%s\n' "$ROOT" "$(git branch --show-current)" "$(git rev-parse HEAD)"
printf 'candidate-wip-entry-count=%s\n' "$(git status --short --untracked-files=all | wc -l | tr -d '[:space:]')"
verify_docker_target
sha256sum -c "$MANIFEST" || fail 'integrated manifest mismatch'
if awk '$2 ~ /(^|\/)\.env([^/]*|\/)/ || $2 ~ /(^|\/)node_modules(\/|$)/ || $2 ~ /(^|\/)\.git(\/|$)/ { found=1 } END { exit !found }' "$MANIFEST"; then
  fail 'integrated source manifest includes private environment, dependency tree or Git metadata'
fi
while IFS=' ' read -r _ source_path; do
  [[ "$source_path" =~ ^[A-Za-z0-9._/-]+$ && "$source_path" != /* && "$source_path" != '.' \
    && "/$source_path/" != *"/../"* && -f "$ROOT/$source_path" && ! -L "$ROOT/$source_path" ]] \
    || fail "unsafe or missing integrated source path: $source_path"
done < "$MANIFEST"
for image in "$PG_IMAGE" "$POSTGREST_IMAGE" "$NODE_IMAGE" "$EDGE_IMAGE"; do docker image inspect "$image" >/dev/null 2>&1 || fail "pinned image not local (no pulls): $image"; done
PG_VERSION="$(docker run --rm --pull=never --platform linux/amd64 --network none --read-only \
  --memory=256m --memory-swap=256m --cpus=0.5 --pids-limit=64 \
  "$PG_IMAGE" postgres --version 2>/dev/null)" || fail 'pinned PostgreSQL image version preflight failed'
[[ "$PG_VERSION" =~ ^postgres\ \(PostgreSQL\)\ 17\.11([[:space:]]|$) ]] || fail 'pinned PostgreSQL image is not version 17.11'
printf 'PostgreSQL pinned image version PASS: 17.11\n'
for name in "$PG" "$POSTGREST" "$RUNTIME" "$EDGE_ACTIVE" "$EDGE_SUSPENDED" "$CACHE_VERIFY" "$SNAPSHOT_BOOTSTRAP" "$CONTRACT_TEST"; do check_free_container "$name"; done
for volume in "$SOURCE_SNAPSHOT" "$TLS_VOLUME"; do check_free_volume "$volume"; done
for volume in "$TOOLS_MODULES" "$DENO_CACHE" "$EDGE_NODE_MODULES"; do verify_r4_cache_volume "$volume"; done
verify_current_web_module_volume
for network in "$EDGE_NETWORK" "$DATA_NETWORK"; do
  docker network inspect "$network" >/dev/null 2>&1 && fail "internal network name occupied: $network"
done

phase='immutable-manifest-verified-source-snapshot'
create_fresh_volume "$SOURCE_SNAPSHOT"
mapfile -t SNAPSHOT_FILES < <(awk '{print $2}' "$MANIFEST")
for source_path in "${SNAPSHOT_FILES[@]}"; do
  [[ "$source_path" =~ ^[A-Za-z0-9._/-]+$ && "$source_path" != /* && "$source_path" != '.' && "$source_path" != "$MANIFEST" && "/$source_path/" != *"/../"* ]] || fail "unsafe path in approved manifest: $source_path"
done
# This quoted program runs in the isolated snapshot container; expand only there.
# shellcheck disable=SC2016
if ! tar -C "$ROOT" --no-recursion -cf - -- "${SNAPSHOT_FILES[@]}" "$MANIFEST" |
  bounded_docker 300 run --pull=never --platform linux/amd64 --interactive --log-driver none --name "$SNAPSHOT_BOOTSTRAP" --network none --read-only \
    --label "com.studiamatch.h3.c03.jit=$JIT" \
    --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
    --memory=512m --memory-swap=512m --cpus=1 --pids-limit=128 \
    --tmpfs /tmp:rw,nosuid,size=32m --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/snapshot" \
    --env H3_C03_MANIFEST_SHA256="$APPROVED_MANIFEST_SHA256" \
    "$NODE_IMAGE" sh -lc 'set -eu; test -z "$(find /snapshot -mindepth 1 -print -quit)"; tar -xf - -C /snapshot; cd /snapshot; actual="$(sha256sum tests/h3req1-c03-integrated-r51.sha256 | cut -d" " -f1)"; test "$actual" = "$H3_C03_MANIFEST_SHA256"; if find . -type l -print -quit | grep -q .; then exit 41; fi; sha256sum -c tests/h3req1-c03-integrated-r51.sha256; expected="$(sed -E "s/^[a-f0-9]{64}[[:space:]]+//" tests/h3req1-c03-integrated-r51.sha256 | sort)"; actual_files="$(find . -type f ! -path "./tests/h3req1-c03-integrated-r51.sha256" -print | sed "s#^\\./##" | sort)"; test "$expected" = "$actual_files"; test ! -e supabase/functions/admin-invite/package.json; cp tests/h3req1-c03-edge-lock-resolver/deno.json supabase/functions/admin-invite/deno.json; cp tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock supabase/functions/admin-invite/deno.lock; cmp tests/h3req1-c03-edge-lock-resolver/deno.json supabase/functions/admin-invite/deno.json; cmp tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock supabase/functions/admin-invite/deno.lock; mkdir -p supabase/functions/admin-invite/node_modules; test -z "$(find supabase/functions/admin-invite/node_modules -mindepth 1 -print -quit)"' \
    >/dev/null 2>&1; then
  fail 'manifest-pinned source snapshot failed verification; output suppressed'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$SNAPSHOT_BOOTSTRAP")" == '0' ]] || fail 'source snapshot verification exited non-zero'
record_container "$SNAPSHOT_BOOTSTRAP"

phase='runner-safety-contract-tests'
if ! bounded_docker 90 run --pull=never --rm --name "$CONTRACT_TEST" --platform linux/amd64 --log-driver none --network none --read-only \
  --label "com.studiamatch.h3.c03.jit=$JIT" \
  --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
  --memory=256m --memory-swap=256m --cpus=0.5 --pids-limit=64 \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
  "$NODE_IMAGE" node --test /candidate/tests/h3req1_c03_integrated_drill_r51_contract.test.mjs >/dev/null 2>&1; then
  fail 'R51 runner safety contract tests failed'
fi
check_free_container "$CONTRACT_TEST"
printf 'R51 runner safety contract tests PASS\n'

phase='verify-preserved-r4-dependency-caches-read-only'
if ! DEPENDENCY_DIGESTS="$(bounded_docker 180 run --pull=never --platform linux/amd64 --log-driver none --name "$CACHE_VERIFY" --network none --read-only \
  --label "com.studiamatch.h3.c03.jit=$JIT" \
  --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
  --memory=512m --memory-swap=512m --cpus=1 --pids-limit=128 \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/source,readonly" \
  --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache,readonly" \
  --mount "type=volume,src=$EDGE_NODE_MODULES,dst=/edge-node-modules,readonly" \
  --mount "type=volume,src=$TOOLS_MODULES,dst=/tools,readonly" \
  --mount "type=volume,src=$WEB_MODULES,dst=/web-deps/node_modules,readonly" \
  "$NODE_IMAGE" node /source/tests/h3req1_c03_cache_digest.mjs deno-cache=/deno-cache edge-node-modules=/edge-node-modules \
  miniflare-node-modules=/tools/node_modules pages-node-modules=/web-deps/node_modules 2>/dev/null)"; then
  fail 'dependency-volume content verification failed; output suppressed'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$CACHE_VERIFY")" == '0' ]] || fail 'dependency-volume content verifier exited non-zero'
readonly DEPENDENCY_DIGEST_PATTERN='^\{"deno-cache":"[a-f0-9]{64}","edge-node-modules":"[a-f0-9]{64}","miniflare-node-modules":"[a-f0-9]{64}","pages-node-modules":"[a-f0-9]{64}"\}$'
[[ "$DEPENDENCY_DIGESTS" =~ $DEPENDENCY_DIGEST_PATTERN ]] || fail 'dependency-volume digest output does not match the exact safe schema'
[[ "$DEPENDENCY_DIGESTS" == "$EXPECTED_DEPENDENCY_DIGESTS" ]] || fail 'preserved R4 dependency cache digest differs from its recorded verified content'
printf 'Locked dependency volume SHA-256: %s\n' "$DEPENDENCY_DIGESTS"
record_container "$CACHE_VERIFY"

phase='isolated-workerd-bootstrap'
create_internal_network "$EDGE_NETWORK"
create_internal_network "$DATA_NETWORK"
create_fresh_volume "$TLS_VOLUME"
docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$RUNTIME" \
  --label "com.studiamatch.h3.c03.jit=$JIT" \
  --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
  --network "$EDGE_NETWORK" --network-alias local.supabase.co --read-only \
  --memory=4g --memory-swap=4g --cpus=2 --pids-limit=512 \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m --tmpfs /run/c03-private:rw,noexec,nosuid,size=8m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
  --mount "type=volume,src=$TLS_VOLUME,dst=/run/c03-certs" \
  --mount "type=volume,src=$TOOLS_MODULES,dst=/tools,readonly" \
  --mount "type=volume,src=$WEB_MODULES,dst=/web-deps/node_modules,readonly" \
  --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache,readonly" \
  --mount "type=volume,src=$EDGE_NODE_MODULES,dst=/edge-node-modules,readonly" \
  --env H3_C03_ROOT=/candidate --env H3_C03_TOOLS_ROOT=/tools --env H3_C03_CERTS_ROOT=/run/c03-certs \
  --env H3_C03_MANIFEST_PATH="$MANIFEST" \
  --env H3_C03_WEB_DEPS_ROOT=/web-deps --env H3_C03_PRIVATE_ROOT=/run/c03-private \
  --env H3_C03_EXPECTED_DEPENDENCY_DIGESTS="$DEPENDENCY_DIGESTS" \
  --env H3_C03_MANIFEST_SHA256="$APPROVED_MANIFEST_SHA256" \
  "$NODE_IMAGE" node /candidate/tests/h3req1_c03_integrated_runtime.mjs >/dev/null 2>&1
record_container "$RUNTIME"
wait_control healthz
docker network connect "$DATA_NETWORK" "$RUNTIME"

phase='fresh-pg17-schema-and-synthetic-fixtures'
PG_PASSWORD="$(od -An -N32 -tx1 /dev/urandom | tr -d '[:space:]')"
readonly PG_PASSWORD
[[ "$PG_PASSWORD" =~ ^[a-f0-9]{64}$ ]] || fail 'synthetic PostgreSQL password generation failed'
docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$PG" \
  --label "com.studiamatch.h3.c03.jit=$JIT" \
  --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
  --network "$DATA_NETWORK" --network-alias h3req1-c03-pg17 --read-only \
  --memory=2g --memory-swap=2g --cpus=2 --pids-limit=512 \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=1g --tmpfs /var/run/postgresql:rw,noexec,nosuid,size=16m \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --env POSTGRES_HOST_AUTH_METHOD=scram-sha-256 --env POSTGRES_PASSWORD="$PG_PASSWORD" \
  --env POSTGRES_DB=h3_c03_chain --env PGDATA=/var/lib/postgresql/data/pgdata \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" "$PG_IMAGE" >/dev/null
record_container "$PG"
for _ in {1..60}; do if bounded_exec "$PG" 2 pg_isready -U postgres -d h3_c03_chain >/dev/null 2>&1; then break; fi; sleep 1; done
bounded_exec "$PG" 2 pg_isready -U postgres -d h3_c03_chain >/dev/null 2>&1 || fail 'fresh PG17 not ready within a bounded readiness call'
run_sql tests/sql/h3_from_h2_pro_pg17_harness.sql 'H2-Pro-to-H3 schema bootstrap'
run_sql tests/sql/h3req1_c03_integrated_extension_setup_r13.sql 'integrated-only quota and signed-dispatcher schema setup'
run_sql tests/sql/h3req1_c03_integrated_setup.sql 'synthetic in-flight/editorial fixture'

phase='isolated-postgrest'
JWT_SECRET="$(printf '%s' "$JWT_SEED" | sha256sum | cut -d' ' -f1)"
docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$POSTGREST" \
  --label "com.studiamatch.h3.c03.jit=$JIT" \
  --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
  --network "$DATA_NETWORK" --network-alias h3req1-c03-postgrest --read-only \
  --memory=512m --memory-swap=512m --cpus=1 --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --env PGRST_DB_URI="postgres://postgres:${PG_PASSWORD}@h3req1-c03-pg17:5432/h3_c03_chain" \
  --env PGRST_DB_SCHEMAS=public --env PGRST_DB_ANON_ROLE=anon \
  --env PGRST_DB_PRE_REQUEST=public.h3_admin_rpc_signed_gateway_pre_request \
  --env PGRST_JWT_SECRET="$JWT_SECRET" --env PGRST_DB_EXTRA_SEARCH_PATH=public,extensions "$POSTGREST_IMAGE" >/dev/null
record_container "$POSTGREST"
postgrest_probe_result='phase=postgrest-probe|error_code=EXEC_TIMEOUT_OR_FAILED'
postgrest_ready=0
for _ in {1..60}; do
  probe_output=''
  if probe_output="$(bounded_exec "$RUNTIME" 5 node /candidate/tests/h3req1_c03_postgrest_probe.mjs 2>/dev/null)"; then
    if [[ "$probe_output" == 'phase=postgrest-probe|error_code=OK' ]]; then
      postgrest_probe_result="$probe_output"
      postgrest_ready=1
      break
    fi
  fi
  if [[ "$probe_output" =~ ^phase=postgrest-probe\|error_code=(HTTP_[1-5][0-9]{2}(_(PGRST[0-9]{3}|[A-Z0-9]{5}))?|HTTP_STATUS_INVALID|ABORT_ERR|ECONNREFUSED|ECONNRESET|EAI_AGAIN|EHOSTUNREACH|ENETUNREACH|ENOTFOUND|ETIMEDOUT|UND_ERR_CONNECT_TIMEOUT|TIMEOUT|FETCH_FAILED)$ ]]; then
    postgrest_probe_result="$probe_output"
  elif [[ -z "$probe_output" ]]; then
    postgrest_probe_result='phase=postgrest-probe|error_code=EXEC_TIMEOUT_OR_FAILED'
  else
    postgrest_probe_result='phase=postgrest-probe|error_code=OUTPUT_REJECTED'
  fi
  sleep 1
done
(( postgrest_ready == 1 )) || fail "isolated PostgREST readiness failed: $postgrest_probe_result"
printf 'isolated PostgREST readiness PASS\n'

phase='real-edge-invite-held-after-reservation'
start_edge "$EDGE_ACTIVE" h3req1-c03-edge-active false
wait_control edge-active-ready
control login
control trigger-inflight
run_sql tests/sql/h3req1_c03_integrated_assert_inflight.sql 'reservation confirmed before Auth hold'

phase='safe-suspend-and-runtime-denials'
run_sql db/rollback/h3req1_safe_suspend.sql 'persistent safe suspension'
start_edge "$EDGE_SUSPENDED" h3req1-c03-edge-suspended true
wait_control edge-suspended-ready
control pages-suspended
control edge-suspended
control signed-dispatcher
run_sql tests/sql/h3req1_c03_integrated_assert_suspended.sql 'suspended ACL/data/quota/audit assertions'

phase='in-flight-finalization-under-suspension'
control release-inflight
run_sql tests/sql/h3req1_c03_integrated_assert_completed_suspended.sql 'finalizer completed while SQL suspended'

phase='same-database-safe-resume'
run_sql db/rollback/h3req1_safe_resume.sql 'persistent safe resume on a new psql connection'
run_sql tests/sql/h3req1_c03_integrated_assert_recovered.sql 'recovered ACL/data/audit assertions'

phase='edge-first-pages-last-recovery-smoke'
control recovery
run_sql tests/sql/h3req1_c03_integrated_assert_final.sql 'final idempotency/quota/audit assertions'
control finish

phase='verify-runtime-graceful-shutdown'
for _ in {1..100}; do
  [[ "$(docker inspect -f '{{.State.Status}}' "$RUNTIME")" == 'exited' ]] && break
  sleep 0.2
done
RUNTIME_STATE="$(docker inspect -f '{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}' "$RUNTIME")"
[[ "$RUNTIME_STATE" == 'exited|0|false' ]] || fail "runtime did not complete graceful shutdown: $RUNTIME_STATE"
phase='stop-new-services-preserve-resources'
stop_run_services
for name in "$EDGE_SUSPENDED" "$EDGE_ACTIVE" "$RUNTIME" "$POSTGREST" "$PG"; do
  state="$(docker inspect -f '{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}' "$name")"
  IFS='|' read -r status exit_code oom_killed <<< "$state"
  [[ "$status" == 'exited' && "$oom_killed" == 'false' && "$exit_code" != '137' ]] || fail "unclean shutdown for $name: $state"
done
PASS_LINE='C03 integrated drill: PASS (local synthetic scope only; no Development GO).'
printf 'C03 integrated assertions PASS; synthetic evidence is captured in this run log. Beginning exact fixture cleanup.\n'
phase='remove-exact-completed-run-containers-and-internal-networks'
cleanup_run_containers_and_networks
printf '%s\n' "$PASS_LINE" \
  'Exact R51 containers and internal networks removed after the assertions; source snapshot, synthetic TLS volume, and read-only R4 dependency caches are preserved. PG17 used tmpfs only; no image or checkout file was removed.' \
  "Sanitized run log: $RESULT_LOG"
if ! grep -Fqx "$PASS_LINE" "$ROOT/$RESULT_LOG"; then
  printf 'NO-GO: result log did not retain the final PASS record.\n' >&3
  exit 1
fi
trap - ERR
printf '%s\n' "$PASS_LINE" "Sanitized run log: $RESULT_LOG" >&3
exec 3>&-
