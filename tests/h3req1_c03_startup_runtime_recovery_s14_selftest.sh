#!/usr/bin/env bash
set -Eeuo pipefail

readonly RUNNER="${1:?pass the read-only mounted S14 runner path}"
readonly TEST_ID='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
TRACE="$(mktemp)"
readonly TRACE
trap 'rm -f -- "$TRACE"' EXIT

extract_constant() {
  local key="$1" value
  value="$(awk -F"'" -v wanted="readonly $key=" '$1 == wanted { print $2 }' "$RUNNER")"
  [[ -n "$value" ]] || { printf 'selftest=FAIL|reason=constant-not-found\n' >&2; return 1; }
  printf '%s' "$value"
}

RUNTIME="$(extract_constant RUNTIME)"
readonly RUNTIME
JIT="$(extract_constant JIT)"
readonly JIT
INPUTS_SHA="$(extract_constant INPUTS_SHA)"
readonly INPUTS_SHA
readonly RUN_ID='synthetic-stop-recovery-run'
FUNCTION_SOURCE="$(sed -n '/^stop_running_owned_runtime() {/,/^}/p' "$RUNNER")"
readonly FUNCTION_SOURCE
[[ -n "$FUNCTION_SOURCE" ]] || { printf 'selftest=FAIL|reason=stop-function-not-found\n' >&2; exit 1; }
eval "$FUNCTION_SOURCE"

mode=''
docker_control() {
  case "$1" in
    inspect)
      printf 'inspect\n' >>"$TRACE"
      case "$mode" in
        inspect-fail) return 23 ;;
        foreign-owner) printf '%s|running|foreign-jit|%s|%s\n' "$TEST_ID" "$INPUTS_SHA" "$RUN_ID" ;;
        unknown-state) printf '%s|removing|%s|%s|%s\n' "$TEST_ID" "$JIT" "$INPUTS_SHA" "$RUN_ID" ;;
        exited) printf '%s|exited|%s|%s|%s\n' "$TEST_ID" "$JIT" "$INPUTS_SHA" "$RUN_ID" ;;
        running-ok|stop-fail|post-inspect-fail|post-owner-mismatch|post-active-state)
          if [[ "$(awk '$1 == "inspect" { count++ } END { print count + 0 }' "$TRACE")" == 1 ]]; then
            printf '%s|running|%s|%s|%s\n' "$TEST_ID" "$JIT" "$INPUTS_SHA" "$RUN_ID"
          else
            case "$mode" in
              post-inspect-fail) return 23 ;;
              post-owner-mismatch) printf '%s|exited|foreign-jit|%s|%s\n' "$TEST_ID" "$INPUTS_SHA" "$RUN_ID" ;;
              post-active-state) printf '%s|running|%s|%s|%s\n' "$TEST_ID" "$JIT" "$INPUTS_SHA" "$RUN_ID" ;;
              *) printf '%s|exited|%s|%s|%s\n' "$TEST_ID" "$JIT" "$INPUTS_SHA" "$RUN_ID" ;;
            esac
          fi
          ;;
        *) return 24 ;;
      esac
      ;;
    stop)
      printf 'stop\n' >>"$TRACE"
      [[ "$mode" != stop-fail ]]
      ;;
    *) return 25 ;;
  esac
}

assert_case() {
  local case_mode="$1" expected_status="$2" expected_event="$3" expected_trace="$4" status actual_trace
  mode="$case_mode"
  : >"$TRACE"
  stop_event=''
  if stop_running_owned_runtime; then status=0; else status=$?; fi
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

assert_case inspect-fail 1 \
  "runtime-stop=not-confirmed|reason=inspect-failed|container-name=$RUNTIME|resource-state=unknown" \
  'inspect,'
assert_case foreign-owner 1 \
  "runtime-stop=not-confirmed|reason=ownership-mismatch|container-name=$RUNTIME|resource-state=unknown" \
  'inspect,'
assert_case unknown-state 1 \
  "runtime-stop=not-confirmed|reason=unknown-state|container-id=$TEST_ID|resource-state=unknown" \
  'inspect,'
assert_case exited 0 \
  "runtime-stop=not-required|state=exited|container-id=$TEST_ID|resource=preserved" \
  'inspect,'
assert_case running-ok 0 \
  "runtime-stop=completed|container-id=$TEST_ID|resource=preserved" \
  'inspect,stop,inspect,'
assert_case stop-fail 1 \
  "runtime-stop=not-confirmed|reason=stop-command-failed|container-id=$TEST_ID|resource-state=unknown" \
  'inspect,stop,'
assert_case post-inspect-fail 1 \
  "runtime-stop=not-confirmed|reason=post-stop-inspect-failed|container-id=$TEST_ID|resource-state=unknown" \
  'inspect,stop,inspect,'
assert_case post-owner-mismatch 1 \
  "runtime-stop=not-confirmed|reason=post-stop-ownership-mismatch|container-id=$TEST_ID|resource-state=unknown" \
  'inspect,stop,inspect,'
assert_case post-active-state 1 \
  "runtime-stop=not-confirmed|reason=post-stop-state-active|container-id=$TEST_ID|resource-state=unknown" \
  'inspect,stop,inspect,'

printf 'phase=runtime-stop-recovery-synthetic|error_code=PASS|cases=9\n'
