#!/usr/bin/env bash
set -u -o pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly MANIFEST="$ROOT/.context/evidencia/h3req1_g01_editorial_v6/inputs-v6.sha256"
readonly EXPECTED_MANIFEST_SHA256='71aab76f4dae5c881151f024f830fb79769b9ac7d4868dd7797d71e0a4ed76a3'
readonly HARNESS='tests/sql/h3_pg17_harness.sql'
readonly QUOTA_HARNESS='tests/sql/h3_admin_quota_harness.sql'
readonly GATEWAY_HARNESS='tests/sql/h3_admin_rpc_signed_gateway_harness.sql'
readonly IMAGE='postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly INVOCATION_ID="${BASHPID}-${RANDOM}-${RANDOM}"
readonly NAME="h3req1-editorial-atomicity-pg17-v6-${INVOCATION_ID}"
readonly SCOPE='g01-editorial-atomicity-pg17-v6'
readonly LABEL_SCOPE="org.studiamatch.h3req1.scope=$SCOPE"
readonly LABEL_FIXTURE="org.studiamatch.h3req1.fixture=$NAME"
readonly LABEL_INVOCATION="org.studiamatch.h3req1.invocation=$INVOCATION_ID"
readonly EVIDENCE="$ROOT/.context/evidencia/h3req1_g01_editorial_v6/pg17-editorial-and-signed-gateway-v6.txt"

container_id=''
identity=''
fixture_create_started=0
evidence_open=0
evidence_failed=0
cleanup_code='NOT_CREATED'

record() {
  local phase="$1" code="$2" line
  [[ "$phase" =~ ^[a-z][a-z0-9-]{0,47}$ ]] || return 1
  [[ "$code" =~ ^[A-Z][A-Z0-9_]{0,47}$ ]] || return 1
  line="phase=$phase|error_code=$code"
  if (( evidence_open )) && ! printf '%s\n' "$line" >&3; then
    evidence_failed=1
    printf 'phase=evidence-write|error_code=WRITE_FAILED\n'
    return 1
  fi
  printf '%s\n' "$line"
}

emit() {
  record "$@" || exit 1
}

fail() {
  local status="${3:-1}"
  record "$1" "$2" || status=1
  exit "$status"
}

# shellcheck disable=SC2329 # Called only by the EXIT cleanup/recovery path.
read_fixture_identity() {
  /usr/bin/timeout --foreground --signal=TERM --kill-after=1s 10s \
    /usr/bin/docker --context default inspect --format '{{.Id}}|{{.Image}}|{{index .Config.Labels "org.studiamatch.h3req1.scope"}}|{{index .Config.Labels "org.studiamatch.h3req1.fixture"}}|{{index .Config.Labels "org.studiamatch.h3req1.invocation"}}|{{.State.Status}}' "$1" 2>/dev/null
}

# shellcheck disable=SC2329 # Reached through cleanup_fixture from the EXIT trap.
container_presence() {
  local listed=''
  listed="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=1s 10s \
    /usr/bin/docker --context default ps --all --no-trunc --filter "id=$1" --format '{{.ID}}' 2>/dev/null)" || return 2
  if [[ "$listed" == "$1" ]]; then return 0; fi
  if [[ -z "$listed" ]]; then return 1; fi
  return 2
}

# shellcheck disable=SC2329 # Called only by the EXIT cleanup/recovery path.
fixture_identity_matches() {
  local identity_value="$1" expected_id="${2:-}" found_id found_image found_scope found_fixture found_invocation found_state
  IFS='|' read -r found_id found_image found_scope found_fixture found_invocation found_state <<< "$identity_value"
  [[ "$found_id" =~ ^[0-9a-f]{64}$ && ( -z "$expected_id" || "$found_id" == "$expected_id" ) && \
     "$found_image" == "$image_id" && "$found_scope" == "$SCOPE" && \
     "$found_fixture" == "$NAME" && "$found_invocation" == "$INVOCATION_ID" ]]
}

# shellcheck disable=SC2329 # Invoked by on_exit if docker run is interrupted.
recover_fixture() {
  local identity_value='' listed=''
  if identity_value="$(read_fixture_identity "$NAME")"; then
    if fixture_identity_matches "$identity_value"; then
      IFS='|' read -r container_id _ <<< "$identity_value"
      return 0
    fi
    return 3
  fi
  listed="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=1s 10s \
    /usr/bin/docker --context default ps --all --filter "name=^/${NAME}$" --format '{{.Names}}' 2>/dev/null)" || return 2
  if [[ -z "$listed" ]]; then return 1; fi
  return 3
}

# shellcheck disable=SC2329 # Invoked by on_exit while the fixture is still owned.
cleanup_fixture() {
  [[ -n "$container_id" ]] || return 0
  local identity='' after=''
  local found_id found_image found_scope found_fixture found_invocation found_state presence_status
  if ! identity="$(read_fixture_identity "$container_id")"; then
    if container_presence "$container_id"; then
      cleanup_code='INSPECT_FAILED'
      return 1
    else
      presence_status=$?
      if (( presence_status == 1 )); then
        cleanup_code='OK'
        return 0
      fi
      cleanup_code='DOCKER_UNAVAILABLE'
      return 1
    fi
  fi
  IFS='|' read -r found_id found_image found_scope found_fixture found_invocation found_state <<< "$identity"
  image_id="$(/usr/bin/docker --context default image inspect --format '{{.Id}}' "$IMAGE" 2>/dev/null)" || image_id=''
  if ! fixture_identity_matches "$identity" "$container_id"; then
    cleanup_code='IDENTITY_MISMATCH'
    return 1
  fi
  if [[ "$found_state" == running ]]; then
    /usr/bin/timeout --foreground --signal=TERM --kill-after=2s 12s \
      /usr/bin/docker --context default stop --time 3 "$container_id" >/dev/null 2>&1 || {
        cleanup_code='STOP_FAILED'
        return 1
      }
  elif [[ "$found_state" != exited && "$found_state" != created ]]; then
    cleanup_code='STATE_NOT_REMOVABLE'
    return 1
  fi
  if after="$(read_fixture_identity "$container_id")"; then
    IFS='|' read -r found_id found_image found_scope found_fixture found_invocation found_state <<< "$after"
    if ! fixture_identity_matches "$after" "$container_id" || \
       [[ "$found_state" != exited && "$found_state" != created ]]; then
      cleanup_code='POST_STOP_IDENTITY_MISMATCH'
      return 1
    fi
  else
    cleanup_code='POST_STOP_INSPECT_FAILED'
    return 1
  fi
  /usr/bin/timeout --foreground --signal=TERM --kill-after=1s 10s \
    /usr/bin/docker --context default rm "$container_id" >/dev/null 2>&1 || {
      cleanup_code='REMOVE_FAILED'
      return 1
    }
  if container_presence "$container_id"; then
    cleanup_code='REMOVE_NOT_CONFIRMED'
    return 1
  else
    presence_status=$?
    if (( presence_status != 1 )); then
      cleanup_code='CLEANUP_VERIFY_FAILED'
      return 1
    fi
  fi
  cleanup_code='OK'
  return 0
}

# shellcheck disable=SC2329 # Registered as the EXIT trap callback.
on_exit() {
  local original_status=$?
  local final_status=$original_status
  local recovery_status=0
  trap '' INT TERM HUP
  trap - EXIT
  if (( fixture_create_started )) && [[ -z "$container_id" ]]; then
    if recover_fixture; then
      :
    else
      recovery_status=$?
      if (( recovery_status == 1 )); then
        cleanup_code='OK'
      elif (( recovery_status == 2 )); then
        cleanup_code='RECOVERY_QUERY_FAILED'
        final_status=1
      else
        cleanup_code='OWNERSHIP_MISMATCH'
        final_status=1
      fi
    fi
  fi
  if [[ -n "$container_id" ]]; then
    cleanup_fixture || final_status=1
  fi
  if (( fixture_create_started )); then
    record container-cleanup "$cleanup_code" || final_status=1
  fi
  if (( evidence_open )); then
    if ! printf 'exit=%s\n' "$final_status" >&3; then
      final_status=1
      evidence_failed=1
      printf 'exit=1\n' >&3 2>/dev/null || true
    fi
  fi
  printf 'exit=%s\n' "$final_status"
  if (( evidence_open )); then exec 3>&-; evidence_open=0; fi
  if (( evidence_failed )); then final_status=1; fi
  exit "$final_status"
}

trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

if (( EUID == 0 )); then fail preflight RUN_AS_NONROOT; fi
if [[ "$(/usr/bin/git -C "$ROOT" branch --show-current 2>/dev/null)" != 'feat/h3req1-sync-20261002' || \
      "$(/usr/bin/git -C "$ROOT" rev-parse HEAD 2>/dev/null)" != '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]]; then
  fail preflight CANDIDATE_IDENTITY_MISMATCH
fi
if [[ -e "$EVIDENCE" || -L "$EVIDENCE" ]]; then fail preflight EVIDENCE_PATH_OCCUPIED; fi
umask 077
set -o noclobber
if ! { exec 3>"$EVIDENCE"; } 2>/dev/null; then
  set +o noclobber
  fail preflight EVIDENCE_CREATE_FAILED
fi
set +o noclobber
evidence_open=1
emit preflight CANDIDATE_IDENTITY_OK

manifest_line="$(/usr/bin/sha256sum -- "$MANIFEST" 2>/dev/null)" || fail preflight MANIFEST_READ_FAILED
[[ "${manifest_line%% *}" == "$EXPECTED_MANIFEST_SHA256" ]] || fail preflight MANIFEST_HASH_MISMATCH
cd "$ROOT" || fail preflight ROOT_UNAVAILABLE
manifest_output="$(/usr/bin/sha256sum --check --strict "$MANIFEST" 2>/dev/null)" || fail preflight INPUT_HASH_MISMATCH
ok_inputs="$(printf '%s\n' "$manifest_output" | /usr/bin/grep -c ': OK$')" || ok_inputs=0
[[ "$ok_inputs" == 38 ]] || fail preflight INPUT_COUNT_MISMATCH
emit input-manifest INPUTS_38_OF_38_MATCH

image_id="$(/usr/bin/docker --context default image inspect --format '{{.Id}}' "$IMAGE" 2>/dev/null)" || fail pg17-image PINNED_IMAGE_UNAVAILABLE
[[ "$image_id" == 'sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f' ]] || fail pg17-image IMAGE_ID_MISMATCH
/usr/bin/docker --context default context inspect default --format '{{.Endpoints.docker.Host}}' 2>/dev/null | /usr/bin/grep -Fxq 'unix:///var/run/docker.sock' || fail docker-context ENDPOINT_MISMATCH
existing_name="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=1s 10s \
  /usr/bin/docker --context default ps --all --filter "name=^/${NAME}$" --format '{{.Names}}' 2>/dev/null)" || fail pg17-fixture DOCKER_QUERY_FAILED
[[ -z "$existing_name" ]] || fail pg17-fixture NAME_COLLISION
emit pg17-image PINNED_IMAGE_OK

fixture_create_started=1
if container_id="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=2s 40s \
  /usr/bin/docker --context default run -d --pull=never --network=none \
  --name "$NAME" --label "$LABEL_SCOPE" --label "$LABEL_FIXTURE" --label "$LABEL_INVOCATION" \
  --read-only --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 \
  --tmpfs /var/lib/postgresql/data:rw,nosuid,nodev,size=1024m \
  --tmpfs /var/run/postgresql:rw,nosuid,nodev,size=64m \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  --mount "type=bind,src=$ROOT/tests/sql,dst=/candidate/tests/sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations,dst=/candidate/db/migrations,readonly" \
  --mount "type=bind,src=$ROOT/db/seeds,dst=/candidate/db/seeds,readonly" \
  "$IMAGE" 2>/dev/null)"; then
  :
else
  run_status=$?
  container_id=''
  if (( run_status == 124 || run_status == 137 )); then fail pg17-start CONTAINER_START_TIMEOUT; fi
  fail pg17-start CONTAINER_START_FAILED
fi
if [[ ! "$container_id" =~ ^[0-9a-f]{64}$ ]]; then
  container_id=''
  fail pg17-start CONTAINER_ID_INVALID
fi
emit pg17-start FIXTURE_STARTED

ready=0
for ((attempt=0; attempt<60; attempt++)); do
  if /usr/bin/docker --context default exec "$container_id" pg_isready --quiet --username=postgres >/dev/null 2>&1; then
    ready=1
    break
  fi
  /usr/bin/sleep 0.5
done
(( ready == 1 )) || fail pg17-ready READY_TIMEOUT
emit pg17-ready READY_OK

version_output="$(/usr/bin/docker --context default exec "$container_id" postgres --version 2>/dev/null)" || fail pg17-version VERSION_READ_FAILED
if [[ "$version_output" =~ ^postgres\ \(PostgreSQL\)\ 17\.11([[:space:]][A-Za-z0-9\ \(\)_\.\+~-]{1,100})?$ ]]; then
  emit pg17-version VERSION_17_11
else
  fail pg17-version VERSION_MISMATCH
fi

run_harness() {
  local harness="$1" marker="$2" phase="$3" output='' status=0
  set +e
  output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 180s \
    /usr/bin/docker --context default exec "$container_id" psql -X -q -A -t \
    --set=ON_ERROR_STOP=1 --set=VERBOSITY=sqlstate --username=postgres --dbname=postgres \
    --file="/candidate/$harness" 2>&1)"
  status=$?
  set -e
  emit "${phase}-status" "EXIT_$status"
  if (( status == 0 )) && printf '%s\n' "$output" | /usr/bin/grep -Fxq "$marker"; then
    emit "$phase" HARNESS_MARKER_AND_EXIT_OK
    return 0
  fi
  if (( status == 124 || status == 137 )); then fail "$phase" TIMEOUT; fi
  if [[ "$output" =~ ERROR:[[:space:]]+([A-Z0-9]{5})([[:space:]]|$) ]]; then
    fail "$phase" "SQLSTATE_${BASH_REMATCH[1]}"
  fi
  fail "$phase" HARNESS_FAILED
}

run_harness "$HARNESS" 'h3_pg17_harness_ok' editorial-harness
run_harness "$QUOTA_HARNESS" 'h3_admin_quota_harness_ok' quota-harness
run_harness "$GATEWAY_HARNESS" 'h3_admin_rpc_signed_gateway_harness_ok' signed-gateway-harness

exit 0
