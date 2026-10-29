#!/usr/bin/env bash
set -Eeuo pipefail

readonly RUNNER="${1:?pass the S17 runner path}"
readonly TEST_ID='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
readonly TEST_MANIFEST='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
readonly TEST_RUN='synthetic-snapshot-run'
TRACE="$(mktemp)"
readonly TRACE
trap 'rm -f -- "$TRACE"' EXIT

extract_constant() {
  local key="$1" value
  value="$(awk -F"'" -v wanted="readonly $key=" '$1 == wanted { print $2 }' "$RUNNER")"
  [[ -n "$value" ]] || { printf 'selftest=FAIL|reason=constant-not-found\n' >&2; return 1; }
  printf '%s' "$value"
}

JIT="$(extract_constant JIT)"
readonly JIT
SNAPSHOT_CONTAINER="$(extract_constant SNAPSHOT_CONTAINER)"
readonly SNAPSHOT_CONTAINER
readonly APPROVED_SIDECAR_SHA256="$TEST_MANIFEST"
readonly RUN_NONCE="$TEST_RUN"

FUNCTION_SOURCE="$(sed -n '/^stop_owned_container() {/,/^}/p' "$RUNNER")"
[[ -n "$FUNCTION_SOURCE" ]] || { printf 'selftest=FAIL|reason=stop-function-not-found\n' >&2; exit 1; }
eval "$FUNCTION_SOURCE"

mode=''
container_started=true
created_container_id="$TEST_ID"

emit_metadata() {
  local state="$1" jit="${2:-$JIT}" name="${3:-/$SNAPSHOT_CONTAINER}" \
    manifest="${4:-$APPROVED_SIDECAR_SHA256}" run="${5:-$RUN_NONCE}" id="${6:-$TEST_ID}"
  printf '%s|%s|%s|%s|%s|%s\n' "$id" "$name" "$state" "$jit" "$manifest" "$run"
}

docker_control() {
  local inspect_num
  [[ "${1:-}" == inspect ]] || return 25
  printf 'inspect\n' >>"$TRACE"
  inspect_num="$(awk '$0 == "inspect" { count++ } END { print count + 0 }' "$TRACE")"
  case "$mode" in
    inspect-fail) return 23 ;;
    foreign-owner) emit_metadata running foreign-jit ;;
    unexpected-state) emit_metadata removing ;;
    created) emit_metadata created ;;
    exited) emit_metadata exited ;;
    dead) emit_metadata dead ;;
    running-complete|stop-fail|post-inspect-fail|post-owner-mismatch|post-active-state)
      if (( inspect_num == 1 )); then
        emit_metadata running
      else
        case "$mode" in
          post-inspect-fail) return 23 ;;
          post-owner-mismatch) emit_metadata exited "$JIT" "/$SNAPSHOT_CONTAINER" "$APPROVED_SIDECAR_SHA256" foreign-run ;;
          post-active-state) emit_metadata running ;;
          *) emit_metadata exited ;;
        esac
      fi
      ;;
    *) return 24 ;;
  esac
}

docker_stop() {
  printf 'stop\n' >>"$TRACE"
  [[ "$mode" != stop-fail ]]
}

assert_case() {
  local case_mode="$1" expected_status="$2" expected_event="$3" expected_trace="$4" \
    started="${5:-true}" id="${6:-$TEST_ID}" status actual_trace
  mode="$case_mode"
  # shellcheck disable=SC2034 # The extracted runner function reads this global.
  container_started="$started"
  # shellcheck disable=SC2034 # The extracted runner function reads this global.
  created_container_id="$id"
  stop_event=''
  : >"$TRACE"
  if stop_owned_container; then status=0; else status=$?; fi
  [[ "$status" == "$expected_status" && "$stop_event" == "$expected_event" ]] || {
    printf 'selftest=FAIL|case=%s|reason=outcome-mismatch\n' "$case_mode" >&2
    return 1
  }
  actual_trace="$(tr '\n' ',' <"$TRACE")"
  [[ "$actual_trace" == "$expected_trace" ]] || {
    printf 'selftest=FAIL|case=%s|reason=command-scope-mismatch\n' "$case_mode" >&2
    return 1
  }
}

assert_case not-started 0 \
  'bounded-stop=not-required|reason=container-not-started|container-preserved=true' '' false
assert_case invalid-id 1 \
  'bounded-stop=not-confirmed|reason=invalid-container-id|resource-preserved=true' '' true invalid
assert_case inspect-fail 1 \
  'bounded-stop=not-confirmed|reason=inspect-failed|resource-preserved=true' 'inspect,'
assert_case foreign-owner 1 \
  'bounded-stop=not-confirmed|reason=ownership-mismatch|resource-preserved=true' 'inspect,'
assert_case unexpected-state 1 \
  'bounded-stop=not-confirmed|reason=unexpected-state|resource-preserved=true' 'inspect,'
assert_case created 0 \
  "bounded-stop=not-required|state=created|container-preserved=true" 'inspect,'
assert_case exited 0 \
  "bounded-stop=not-required|state=exited|container-preserved=true" 'inspect,'
assert_case dead 0 \
  "bounded-stop=not-required|state=dead|container-preserved=true" 'inspect,'
assert_case running-complete 0 \
  'bounded-stop=completed|container-preserved=true' 'inspect,stop,inspect,'
assert_case stop-fail 1 \
  'bounded-stop=not-confirmed|reason=stop-command-failed|resource-preserved=true' 'inspect,stop,'
assert_case post-inspect-fail 1 \
  'bounded-stop=not-confirmed|reason=post-stop-inspect-failed|resource-preserved=true' 'inspect,stop,inspect,'
assert_case post-owner-mismatch 1 \
  'bounded-stop=not-confirmed|reason=post-stop-ownership-mismatch|resource-preserved=true' 'inspect,stop,inspect,'
assert_case post-active-state 1 \
  'bounded-stop=not-confirmed|reason=post-stop-state-not-terminal|resource-preserved=true' 'inspect,stop,inspect,'

printf 'phase=snapshot-stop-recovery-synthetic|error_code=PASS|cases=13\n'
