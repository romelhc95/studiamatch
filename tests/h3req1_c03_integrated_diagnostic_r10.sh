#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"

readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_DOCKER_HOST='unix:///var/run/docker.sock'
readonly EXPECTED_DOCKER_ID='fc2115b2-c3c4-440e-89c6-26899eb7cb04'
readonly EXPECTED_DOCKER_VERSION='29.8.2'
readonly R9_MANIFEST='tests/h3req1-c03-integrated.sha256'
readonly R9_MANIFEST_SHA256='6b0a469325b466a59211b3f6e50f16bce49910d78cad994068daa51caba13de9'
readonly R10_INPUTS='tests/h3req1_c03_r10_diag/inputs.sha256'
readonly R10_INPUTS_SHA256='19271aac83e46f84c36d608956d2ff84e1d8ecf7706edb909f09f3a9f8c122a0'
readonly -a SNAPSHOT_NONCANDIDATE_PATHS=(
  'supabase/functions/admin-invite/deno.json'
  'supabase/functions/admin-invite/deno.lock'
)
readonly SOURCE_SNAPSHOT='h3req1-c03-integrated-source-snapshot-20261010-r9'
readonly SOURCE_SNAPSHOT_JIT='H3-CLOSE-03-INTEGRATED-2026-10-10-R9'
readonly DATA_NETWORK='h3req1-c03-diagnostic-data-20261010-r10'
readonly PG='h3req1-c03-diagnostic-pg17-20261010-r10'
readonly POSTGREST='h3req1-c03-diagnostic-postgrest-20261010-r10'
readonly VOLUME_VERIFY='h3req1-c03-diagnostic-snapshot-verify-20261010-r10'
readonly RESULT_FILE='.context/evidencia/h3req1_c03_integrated_diagnostic_r10_v5.txt'
readonly PG_IMAGE='postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly POSTGREST_IMAGE='postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly JIT='H3-CLOSE-03-DIAGNOSTIC-R10'
readonly DOCKER_BIN='/usr/bin/docker'
readonly CLASSIFIER_DIR="$ROOT/tests/h3req1_c03_r10_diag"
RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"
readonly RUN_NONCE

phase='preflight'
DOCKER_TARGET_VERIFIED=0

docker() {
  local -a target=()
  if (( DOCKER_TARGET_VERIFIED )); then target=(--host "$EXPECTED_DOCKER_HOST"); fi
  /usr/bin/timeout --foreground --signal=TERM --kill-after=3s 30s \
    "$DOCKER_BIN" "${target[@]}" "$@"
}
bounded_docker() {
  local seconds=$1
  local -a target=()
  shift
  if (( DOCKER_TARGET_VERIFIED )); then target=(--host "$EXPECTED_DOCKER_HOST"); fi
  /usr/bin/timeout --foreground --signal=TERM --kill-after=3s "${seconds}s" \
    "$DOCKER_BIN" "${target[@]}" "$@"
}
bounded_exec() {
  local container=$1 seconds=$2
  local -a target=()
  shift 2
  if (( DOCKER_TARGET_VERIFIED )); then target=(--host "$EXPECTED_DOCKER_HOST"); fi
  /usr/bin/timeout --foreground --signal=TERM --kill-after=3s "$((seconds + 10))s" \
    "$DOCKER_BIN" "${target[@]}" exec "$container" \
    /usr/bin/timeout --foreground --signal=TERM --kill-after=3s "${seconds}s" "$@"
}

safe_owner() {
  local requested=$1 metadata id container_jit manifest run
  metadata="$(bounded_docker 5 inspect -f '{{.Id}}|{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}|{{index .Config.Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.c03.run"}}' "$requested" 2>/dev/null)" || return 1
  IFS='|' read -r id container_jit manifest run <<< "$metadata"
  [[ "$id" =~ ^[a-f0-9]{64}$ && "$container_jit" == "$JIT" \
    && "$manifest" == "$R9_MANIFEST_SHA256" && "$run" == "$RUN_NONCE" ]]
}
stop_owned_best_effort() {
  (( DOCKER_TARGET_VERIFIED )) || return 0
  local requested metadata id state container_jit manifest run
  local -a ids=()
  for requested in "$POSTGREST" "$PG"; do
    if metadata="$(bounded_docker 5 inspect -f '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}|{{index .Config.Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.c03.run"}}' "$requested" 2>/dev/null)"; then
      IFS='|' read -r id state container_jit manifest run <<< "$metadata"
      if [[ "$id" =~ ^[a-f0-9]{64}$ && "$state" == 'running' && "$container_jit" == "$JIT" \
        && "$manifest" == "$R9_MANIFEST_SHA256" && "$run" == "$RUN_NONCE" ]]; then ids+=("$id"); fi
    fi
  done
  if ((${#ids[@]})); then bounded_docker 20 stop --time 5 "${ids[@]}" >/dev/null 2>&1 || true; fi
}
on_error() {
  local status=$?
  trap - ERR HUP INT TERM
  stop_owned_best_effort
  printf 'halted phase=%s exit=%s owned_services=stopped_if_running resources=preserved\n' "$phase" "$status" >&2
  exit "$status"
}
on_signal() {
  local signal=$1 status=143
  [[ "$signal" == 'INT' ]] && status=130
  [[ "$signal" == 'HUP' ]] && status=129
  trap - ERR HUP INT TERM
  stop_owned_best_effort
  printf 'interrupted phase=%s signal=%s exit=%s owned_services=stopped_if_running resources=preserved\n' "$phase" "$signal" "$status" >&2
  exit "$status"
}
trap on_error ERR
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
fail() { printf 'NO-GO: %s\n' "$1" >&2; exit 1; }

verify_docker_target() {
  local context endpoint identity engine_id os version memory cpu
  [[ ! -v DOCKER_HOST && ! -v DOCKER_CONTEXT ]] || fail 'Docker environment override is present'
  context="$(docker context show)" || fail 'Docker context unavailable'
  endpoint="$(docker context inspect default --format '{{.Endpoints.docker.Host}}')" || fail 'Docker endpoint unavailable'
  identity="$(docker info --format '{{.ID}}|{{.OperatingSystem}}|{{.ServerVersion}}|{{.MemTotal}}|{{.NCPU}}')" || fail 'Docker identity unavailable'
  IFS='|' read -r engine_id os version memory cpu <<< "$identity"
  [[ "$context" == 'default' && "$endpoint" == "$EXPECTED_DOCKER_HOST" \
    && "$engine_id" == "$EXPECTED_DOCKER_ID" && "$os" == 'Docker Desktop' \
    && "$version" == "$EXPECTED_DOCKER_VERSION" ]] || fail 'Docker target differs from the locally attested Docker Desktop engine'
  [[ "$memory" =~ ^[0-9]+$ && "$cpu" =~ ^[0-9]+$ ]] || fail 'Docker capacity metadata invalid'
  (( memory >= 10737418240 && cpu >= 8 )) || fail 'Docker capacity below the accepted local test budget'
  DOCKER_TARGET_VERIFIED=1
  printf 'docker-target=PASS context=default endpoint=unix:///var/run/docker.sock engine=%s version=%s\n' "$engine_id" "$version"
}

free_name() {
  local kind=$1 requested=$2 matches
  if [[ "$kind" == 'container' ]]; then
    matches="$(docker ps -a --format '{{.Names}}' --filter "name=$requested")" || fail 'container inventory unavailable'
  else
    matches="$(docker network ls --format '{{.Name}}' --filter "name=$requested")" || fail 'network inventory unavailable'
  fi
  while IFS= read -r existing; do [[ "$existing" != "$requested" ]] || fail "$kind name occupied: $requested"; done <<< "$matches"
}

log_classifier() {
  local kind=$1 source=$2
  bounded_docker 30 logs --tail 64 "$source" 2>/dev/null |
    bounded_docker 30 run --pull=never --platform linux/amd64 --interactive --rm \
      --name "h3req1-c03-diagnostic-log-filter-${kind}-${RUN_NONCE}" --network none --read-only \
      --memory=256m --memory-swap=256m --cpus=0.5 --pids-limit=64 \
      --tmpfs /tmp:rw,noexec,nosuid,size=8m \
      --mount "type=bind,src=$CLASSIFIER_DIR,dst=/diag,readonly" \
      "$NODE_IMAGE" node "/diag/postgres_log_classifier.mjs" "$kind"
}

probe_network_auth() {
  local stage=$1 output result
  if output="$(bounded_docker 20 run --pull=never --platform linux/amd64 --rm \
    --name "h3req1-c03-diagnostic-pg-client-${stage}-${RUN_NONCE}" \
    --network "$DATA_NETWORK" --read-only --memory=128m --memory-swap=128m \
    --cpus=0.5 --pids-limit=64 --tmpfs /tmp:rw,noexec,nosuid,size=8m \
    --env "PGPASSWORD=$PG_PASSWORD" --env PGCONNECT_TIMEOUT=3 \
    --entrypoint psql "$PG_IMAGE" -X -qAt -w -v ON_ERROR_STOP=1 \
    -h h3req1-c03-pg17 -p 5432 -U postgres -d h3_c03_chain -c 'SELECT 1' 2>&1)"; then
    [[ "$output" == '1' ]] && result='OK' || result='QUERY_RESULT_MISMATCH'
  else
    case "$output" in
      *'could not translate host name'*) result='DNS_NAME_UNRESOLVED' ;;
      *'connection refused'*) result='CONNECTION_REFUSED' ;;
      *'timeout expired'*|*'Connection timed out'*) result='CONNECT_TIMEOUT' ;;
      *'password authentication failed'*) result='AUTHENTICATION_FAILED' ;;
      *'no pg_hba.conf entry'*) result='ACCESS_RULE_REJECTED' ;;
      *'server closed the connection unexpectedly'*) result='CONNECTION_CLOSED' ;;
      *) result='TCP_CLIENT_FAILED' ;;
    esac
  fi
  [[ "$result" =~ ^(OK|QUERY_RESULT_MISMATCH|DNS_NAME_UNRESOLVED|CONNECTION_REFUSED|CONNECT_TIMEOUT|AUTHENTICATION_FAILED|ACCESS_RULE_REJECTED|CONNECTION_CLOSED|TCP_CLIENT_FAILED)$ ]] || result='OUTPUT_REJECTED'
  printf 'phase=postgres-tcp-auth-%s|error_code=%s\n' "$stage" "$result"
}

start_network() {
  local created metadata id internal net_jit net_manifest net_run
  created="$(docker network create --internal \
    --label "com.studiamatch.h3.c03.jit=$JIT" \
    --label "com.studiamatch.h3.c03.manifest=$R9_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.c03.run=$RUN_NONCE" "$DATA_NETWORK")" || fail 'internal network creation failed'
  [[ "$created" =~ ^[a-f0-9]{64}$ ]] || fail 'internal network ID malformed'
  metadata="$(docker network inspect -f '{{.Id}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.c03.jit"}}|{{index .Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Labels "com.studiamatch.h3.c03.run"}}' "$DATA_NETWORK")" || fail 'internal network verification failed'
  IFS='|' read -r id internal net_jit net_manifest net_run <<< "$metadata"
  [[ "$id" == "$created" && "$internal" == 'true' && "$net_jit" == "$JIT" \
    && "$net_manifest" == "$R9_MANIFEST_SHA256" && "$net_run" == "$RUN_NONCE" ]] || fail 'internal network identity mismatch'
  printf 'network=%s internal=true created=PASS\n' "$DATA_NETWORK"
}

record_container() {
  local requested=$1 metadata
  metadata="$(docker inspect -f '{{.Id}}|{{.Image}}|{{.State.Status}}|{{.HostConfig.Memory}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.PidsLimit}}' "$requested")" || fail "safe container metadata unavailable: $requested"
  printf 'container=%s metadata=%s\n' "$requested" "$metadata"
}

cleanup_completed() {
  local requested metadata id state jit manifest run net_meta net_id internal attached net_jit net_manifest net_run
  local -a ids=()
  for requested in "$POSTGREST" "$PG"; do
    if safe_owner "$requested"; then
      metadata="$(docker inspect -f '{{.Id}}|{{.State.Status}}' "$requested")" || fail "completion state unavailable: $requested"
      IFS='|' read -r id state <<< "$metadata"
      [[ "$state" == 'running' ]] && ids+=("$id")
    fi
  done
  if ((${#ids[@]})); then bounded_docker 20 stop --time 5 "${ids[@]}" >/dev/null || fail 'bounded fixture stop failed'; fi
  for requested in "$POSTGREST" "$PG"; do
    metadata="$(docker inspect -f '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.c03.jit"}}|{{index .Config.Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.c03.run"}}' "$requested")" || fail "cleanup ownership unavailable: $requested"
    IFS='|' read -r id state jit manifest run <<< "$metadata"
    [[ "$id" =~ ^[a-f0-9]{64}$ && "$state" == 'exited' && "$jit" == "$JIT" \
      && "$manifest" == "$R9_MANIFEST_SHA256" && "$run" == "$RUN_NONCE" ]] || fail "refusing cleanup outside this diagnostic run: $requested"
    docker rm "$id" >/dev/null || fail "exact fixture removal failed: $requested"
    printf 'removed-fixture=%s id=%s\n' "$requested" "$id"
  done
  net_meta="$(docker network inspect -f '{{.Id}}|{{.Internal}}|{{len .Containers}}|{{index .Labels "com.studiamatch.h3.c03.jit"}}|{{index .Labels "com.studiamatch.h3.c03.manifest"}}|{{index .Labels "com.studiamatch.h3.c03.run"}}' "$DATA_NETWORK")" || fail 'diagnostic network cleanup metadata unavailable'
  IFS='|' read -r net_id internal attached net_jit net_manifest net_run <<< "$net_meta"
  [[ "$net_id" =~ ^[a-f0-9]{64}$ && "$internal" == 'true' && "$attached" == '0' \
    && "$net_jit" == "$JIT" && "$net_manifest" == "$R9_MANIFEST_SHA256" && "$net_run" == "$RUN_NONCE" ]] \
    || fail 'refusing to remove a network outside this completed diagnostic run'
  docker network rm "$net_id" >/dev/null || fail 'exact empty diagnostic network removal failed'
  printf 'removed-network=%s id=%s internal=true attached=0\n' "$DATA_NETWORK" "$net_id"
}

[[ "$ROOT" == '/home/romel/src/studiamatch-h3req1-sync-20261002' ]] || fail 'candidate path drift'
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch drift'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD drift'
for extra_path in "${SNAPSHOT_NONCANDIDATE_PATHS[@]}"; do
  [[ ! -e "$ROOT/$extra_path" && ! -L "$ROOT/$extra_path" ]] \
    || fail 'historical snapshot extra path is now present in the candidate'
done
[[ -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context/evidencia" ]] || fail 'evidence directory unavailable or symlinked'
[[ ! -e "$RESULT_FILE" && ! -L "$RESULT_FILE" ]] || fail 'R10 evidence path already exists'
[[ -x /usr/bin/timeout && -x "$DOCKER_BIN" ]] || fail 'required fixed host utilities unavailable'
set -o noclobber
exec >"$ROOT/$RESULT_FILE" 2>&1
set +o noclobber
printf 'candidate=%s branch=%s head=%s\n' "$ROOT" "$EXPECTED_BRANCH" "$EXPECTED_HEAD"
printf 'candidate-wip-entry-count=%s\n' "$(git status --short --untracked-files=all | wc -l | tr -d '[:space:]')"
verify_docker_target

phase='r9-manifest-and-snapshot-provenance'
[[ "$(sha256sum "$R10_INPUTS" | cut -d' ' -f1)" == "$R10_INPUTS_SHA256" ]] \
  || fail 'R10 diagnostic input-manifest hash mismatch'
if ! sha256sum -c "$R10_INPUTS" >/dev/null 2>&1; then fail 'R10 diagnostic input manifest mismatch'; fi
printf 'r10-diagnostic-inputs=7/7 PASS manifest_sha256=%s\n' "$R10_INPUTS_SHA256"
# shellcheck source=tests/h3req1_c03_r10_diag/postgres_version_classifier.sh
source "$CLASSIFIER_DIR/postgres_version_classifier.sh"
[[ "$(sha256sum "$R9_MANIFEST" | cut -d' ' -f1)" == "$R9_MANIFEST_SHA256" ]] || fail 'R9 manifest hash drift'
if ! sha256sum -c "$R9_MANIFEST" >/dev/null 2>&1; then fail 'R9 integrated inputs differ from preserved 64-file manifest'; fi
printf 'r9-integrated-manifest=64/64 PASS sha256=%s\n' "$R9_MANIFEST_SHA256"
snapshot_meta="$(docker volume inspect -f '{{.Driver}}|{{index .Labels "com.studiamatch.h3.c03.jit"}}|{{index .Labels "com.studiamatch.h3.c03.manifest"}}' "$SOURCE_SNAPSHOT")" \
  || fail 'preserved R9 source snapshot volume unavailable'
[[ "$snapshot_meta" == "local|$SOURCE_SNAPSHOT_JIT|$R9_MANIFEST_SHA256" ]] || fail 'preserved source snapshot provenance mismatch'
snapshot_users="$(docker ps --filter "volume=$SOURCE_SNAPSHOT" --format '{{.Names}}')" || fail 'source snapshot consumer inventory unavailable'
[[ -z "$snapshot_users" ]] || fail 'preserved source snapshot is mounted by an active container'
for image in "$PG_IMAGE" "$POSTGREST_IMAGE" "$NODE_IMAGE"; do docker image inspect "$image" >/dev/null 2>&1 || fail 'a locally pinned diagnostic image is unavailable'; done
for requested in "$PG" "$POSTGREST" "$VOLUME_VERIFY"; do free_name container "$requested"; done
free_name network "$DATA_NETWORK"
snapshot_verify="$(bounded_docker 90 run --pull=never --platform linux/amd64 --rm \
  --name "$VOLUME_VERIFY" --network none --read-only --memory=512m --memory-swap=512m \
  --cpus=1 --pids-limit=128 --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
  --mount "type=bind,src=$CLASSIFIER_DIR,dst=/diag,readonly" \
  --entrypoint node "$NODE_IMAGE" /diag/source_snapshot_verifier.mjs \
  /candidate "$R9_MANIFEST" "$R9_MANIFEST_SHA256" 2>/dev/null)" \
  || fail 'preserved R9 source snapshot content verification failed'
[[ "$snapshot_verify" == 'phase=source-snapshot|error_code=VERIFIED_64_2' ]] \
  || fail 'preserved source snapshot output rejected'
printf 'r9-source-snapshot=64/64 noncandidate_extras=2 hash_pinned=2 symlinks=0 read_only=PASS\n'
pg_version="$(bounded_docker 15 run --pull=never --platform linux/amd64 --rm --network none \
  --read-only --memory=128m --memory-swap=128m --cpus=0.5 --pids-limit=64 \
  "$PG_IMAGE" postgres --version 2>/dev/null)" || fail 'PostgreSQL image version probe failed'
if ! h3req1_is_postgres_17_11 "$pg_version"; then fail 'PostgreSQL image version differs from pinned 17.11'; fi
printf 'postgresql-image=17.11 PASS\n'

phase='isolated-postgres-fixture'
start_network
PG_PASSWORD="$(od -An -N32 -tx1 /dev/urandom | tr -d '[:space:]')"
readonly PG_PASSWORD
[[ "$PG_PASSWORD" =~ ^[a-f0-9]{64}$ ]] || fail 'synthetic password generation failed'
if ! bounded_docker 30 run --pull=never --platform linux/amd64 -d --name "$PG" \
  --label "com.studiamatch.h3.c03.jit=$JIT" \
  --label "com.studiamatch.h3.c03.manifest=$R9_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
  --network "$DATA_NETWORK" --network-alias h3req1-c03-pg17 --read-only \
  --log-driver=json-file --log-opt max-size=1m --log-opt max-file=1 \
  --memory=2g --memory-swap=2g --cpus=2 --pids-limit=512 \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=1g \
  --tmpfs /var/run/postgresql:rw,noexec,nosuid,size=16m --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --env POSTGRES_HOST_AUTH_METHOD=scram-sha-256 --env "POSTGRES_PASSWORD=$PG_PASSWORD" \
  --env POSTGRES_DB=h3_c03_chain --env PGDATA=/var/lib/postgresql/data/pgdata \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
  "$PG_IMAGE" postgres -c log_min_messages=error -c log_error_verbosity=terse \
  -c 'log_line_prefix=SQLSTATE=%e ' >/dev/null 2>&1; then fail 'PostgreSQL fixture failed to start'; fi
record_container "$PG"
pg_ready=0
for _ in {1..60}; do
  if bounded_exec "$PG" 5 pg_isready -U postgres -d h3_c03_chain >/dev/null 2>&1; then pg_ready=1; break; fi
  sleep 1
done
(( pg_ready )) || fail 'local PG17 readiness deadline exceeded'
printf 'phase=postgres-local-readiness|error_code=OK\n'
for sql_path in \
  tests/sql/h3_from_h2_pro_pg17_harness.sql \
  tests/sql/h3req1_c03_integrated_extension_setup.sql \
  tests/sql/h3req1_c03_integrated_setup.sql; do
  if ! bounded_exec "$PG" 90 psql -X -q -U postgres -d h3_c03_chain -v ON_ERROR_STOP=1 \
    -o /dev/null -f "/candidate/$sql_path" >/dev/null 2>&1; then
    fail "isolated PG17 SQL bootstrap failed: $sql_path"
  fi
  printf 'sql-fixture=%s exit=0\n' "$sql_path"
done
probe_network_auth before

phase='isolated-postgrest-diagnostic'
JWT_SECRET="$(printf '%s' 'Studiamatch H3REQ1 C03 disposable PostgREST JWT fixture 2026-10-06' | sha256sum | cut -d' ' -f1)"
if ! bounded_docker 30 run --pull=never --platform linux/amd64 -d --name "$POSTGREST" \
  --label "com.studiamatch.h3.c03.jit=$JIT" \
  --label "com.studiamatch.h3.c03.manifest=$R9_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.c03.run=$RUN_NONCE" \
  --network "$DATA_NETWORK" --network-alias h3req1-c03-postgrest --read-only \
  --log-driver=json-file --log-opt max-size=1m --log-opt max-file=1 \
  --memory=512m --memory-swap=512m --cpus=1 --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --env "PGRST_DB_URI=postgres://postgres:${PG_PASSWORD}@h3req1-c03-pg17:5432/h3_c03_chain" \
  --env PGRST_DB_SCHEMAS=public --env PGRST_DB_ANON_ROLE=anon \
  --env PGRST_DB_PRE_REQUEST=public.h3_admin_rpc_signed_gateway_pre_request \
  --env "PGRST_JWT_SECRET=$JWT_SECRET" --env PGRST_DB_EXTRA_SEARCH_PATH=public,extensions \
  "$POSTGREST_IMAGE" >/dev/null 2>&1; then fail 'PostgREST fixture failed to start'; fi
record_container "$POSTGREST"
sleep 5
postgrest_state="$(docker inspect -f '{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}' "$POSTGREST")" || fail 'PostgREST state metadata unavailable'
printf 'postgrest-state=%s\n' "$postgrest_state"
probe_status=0
probe_output="$(bounded_docker 20 run --pull=never --platform linux/amd64 --rm \
  --name "h3req1-c03-diagnostic-http-probe-$RUN_NONCE" --network "$DATA_NETWORK" \
  --read-only --memory=128m --memory-swap=128m --cpus=0.5 --pids-limit=64 \
  --tmpfs /tmp:rw,noexec,nosuid,size=8m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
  "$NODE_IMAGE" node /candidate/tests/h3req1_c03_postgrest_probe.mjs 2>/dev/null)" || probe_status=$?
if [[ "$probe_output" =~ ^phase=postgrest-probe\|error_code=(OK|HTTP_[1-5][0-9]{2}(_(PGRST[0-9]{3}|[A-Z0-9]{5}))?|HTTP_STATUS_INVALID|ABORT_ERR|ECONNREFUSED|ECONNRESET|EAI_AGAIN|EHOSTUNREACH|ENETUNREACH|ENOTFOUND|ETIMEDOUT|UND_ERR_CONNECT_TIMEOUT|TIMEOUT|FETCH_FAILED)$ ]]; then
  printf '%s probe_exit=%s\n' "$probe_output" "$probe_status"
else
  printf 'phase=postgrest-probe|error_code=OUTPUT_REJECTED probe_exit=%s\n' "$probe_status"
fi
probe_network_auth after

phase='sanitize-bounded-server-logs'
if pg_log_result="$(log_classifier postgres "$PG")"; then
  [[ "$pg_log_result" =~ ^phase=postgres-log\|error_code=(SQLSTATE_[A-Z0-9]{5}|NO_SCHEMA_CACHE_SQLSTATE|LOG_INPUT_LIMIT|LOG_ENCODING_INVALID)$ ]] \
    || pg_log_result='phase=postgres-log|error_code=OUTPUT_REJECTED'
else
  pg_log_result='phase=postgres-log|error_code=CLASSIFIER_FAILED'
fi
if postgrest_log_result="$(log_classifier postgrest "$POSTGREST")"; then
  [[ "$postgrest_log_result" =~ ^phase=postgrest-log\|error_code=(SQLSTATE_[A-Z0-9]{5}|POSTGREST_CODE_PGRST[0-9]{3}|STRUCTURED_SQLSTATE_[A-Z0-9]{5}|STRUCTURED_POSTGREST_CODE_PGRST[0-9]{3}|SCHEMA_CACHE_CODE_NOT_EXPOSED|JSON_CODE_NOT_EXPOSED|NO_JSON_RECORD|LOG_EMPTY|LOG_INPUT_LIMIT|LOG_ENCODING_INVALID)$ ]] \
    || postgrest_log_result='phase=postgrest-log|error_code=OUTPUT_REJECTED'
else
  postgrest_log_result='phase=postgrest-log|error_code=CLASSIFIER_FAILED'
fi
printf '%s\n%s\n' "$pg_log_result" "$postgrest_log_result"

phase='preserve-classified-result-and-retire-fixtures'
cleanup_completed
printf 'phase=r10-diagnostic|error_code=COMPLETE exit=0 raw_logs_persisted=false edge_started=false\n'
