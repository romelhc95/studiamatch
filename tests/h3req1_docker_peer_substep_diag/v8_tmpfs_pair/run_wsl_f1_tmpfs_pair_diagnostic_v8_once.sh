#!/usr/bin/env bash
set -u -o pipefail
export LANG=C LC_ALL=C

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/v8_tmpfs_pair/f1_tmpfs_pair_diagnostic_v8_once.py"
readonly RUNNER_SHA256='bf99e3414c6aad157371ad2decdb338a9f07c5587d422d41a0e13ed17147f121'
readonly TEST="$ROOT/tests/h3req1_docker_peer_substep_diag/v8_tmpfs_pair/test_f1_tmpfs_pair_diagnostic_v8.py"
readonly TEST_SHA256='b9050f5d2f960beb0a25b0fd239f6e717cf5fe0061c747256255e8bdad51dfdd'
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'

fail() {
  printf 'phase=%s|error_code=%s\n' "$1" "$2"
  exit 1
}

(( EUID != 0 )) || fail 'wsl-preflight' 'RUN_AS_WSL_USER'
[[ -t 0 ]] || fail 'wsl-preflight' 'INTERACTIVE_TTY_REQUIRED'
[[ -x /usr/bin/sha256sum && -x /usr/bin/timeout && -x /usr/bin/python3 ]] || \
  fail 'wsl-preflight' 'RUNTIME_UNAVAILABLE'
[[ -d "$ROOT" && -f "$RUNNER" && -f "$TEST" ]] || fail 'wsl-preflight' 'SOURCE_UNAVAILABLE'

if ! runner_hash_line="$(/usr/bin/sha256sum -- "$RUNNER" 2>/dev/null)"; then
  fail 'source-pin' 'RUNNER_HASH_FAILED'
fi
if [[ "${runner_hash_line%% *}" != "$RUNNER_SHA256" ]]; then
  fail 'source-pin' 'RUNNER_HASH_MISMATCH'
fi
if ! test_hash_line="$(/usr/bin/sha256sum -- "$TEST" 2>/dev/null)"; then
  fail 'source-pin' 'TEST_HASH_FAILED'
fi
if [[ "${test_hash_line%% *}" != "$TEST_SHA256" ]]; then
  fail 'source-pin' 'TEST_HASH_MISMATCH'
fi

if ! test_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=2s 20s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B "$TEST" 2>/dev/null)"; then
  fail 'synthetic-tests' 'TESTS_FAILED'
fi
[[ "$test_output" == 'V8_SYNTHETIC_TESTS_PASS:4/4' ]] || fail 'synthetic-tests' 'TEST_RESULT_INVALID'
printf 'phase=synthetic-tests|error_code=OK\n'

if runner_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 900s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B "$RUNNER" 2>/dev/null)"; then
  runner_status=0
else
  runner_status=$?
fi
runner_size="$(printf '%s' "$runner_output" | wc -c)"
(( runner_size <= 8192 )) || fail 'diagnostic-output' 'OUTPUT_LIMIT'

invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ ! "$line" =~ $SAFE_LINE_RE ]]; then
    invalid_output=1
    break
  fi
done <<< "$runner_output"
(( invalid_output == 0 )) || fail 'diagnostic-output' 'OUTPUT_REJECTED'
[[ -n "$runner_output" ]] || fail 'diagnostic-output' 'NO_SANITIZED_OUTPUT'
printf '%s\n' "$runner_output"
printf 'exit=%s\n' "$runner_status"
exit "$runner_status"
