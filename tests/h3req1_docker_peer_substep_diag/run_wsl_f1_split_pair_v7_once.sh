#!/usr/bin/env bash
set -u -o pipefail
export LANG=C LC_ALL=C

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_v7_split_pair_once.py"
readonly RUNNER_SHA256='331d2a99bfbae7d8bd470a0fc5ac91e74eb8af26f72e2b244ad4683d68d3b4ef'
readonly TEST="$ROOT/tests/h3req1_docker_peer_substep_diag/test_f1_read_failure_classification_v7_split_pair.py"
readonly TEST_SHA256='c357175e1a72638db7ac494e5ef4ad86b4a4f107863cba49deb3692ee473fef2'
readonly SYNTHETIC_RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/classifier_synthetic_runner_v7_split_pair.py"
readonly SYNTHETIC_RUNNER_SHA256='0c0a106a3adfe8a471913ca649ef1af110952a44490f020d5644334e622f68b4'
readonly V6_SOURCE="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_v6_once.py"
readonly V6_SOURCE_SHA256='b17266a33559b16b28cdf1b619f9b5d7dae666203f6d9a357b046ed7ae809128'
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'
readonly EXPECTED=$'phase=prior-desktop-wsl-endpoint-attestation|error_code=OK\nphase=classifier-synthetic-image-volumes-read|error_code=OK\nphase=classifier-synthetic-image-read|error_code=OK\nphase=classifier-synthetic-unit-tests|error_code=OK\nphase=f1-template-synthetic-check|error_code=OK\nphase=classifier-synthetic-tests|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK'

fail() {
  printf 'phase=%s|error_code=%s\n' "$1" "$2"
  if [[ $# -ge 3 ]]; then exit "$3"; else exit 1; fi
}

verify_hash() {
  local file="$1" expected="$2" hash_line actual
  [[ -f "$file" && ! -L "$file" ]] || return 1
  hash_line="$(/usr/bin/sha256sum -- "$file" 2>/dev/null)" || return 1
  read -r actual _ <<< "$hash_line"
  [[ "$actual" == "$expected" ]]
}

(( EUID != 0 )) || fail 'jit-preflight' 'RUN_AS_WSL_USER'
[[ -t 0 ]] || fail 'jit-preflight' 'INTERACTIVE_TTY_REQUIRED'
[[ -x /usr/bin/sha256sum && -x /usr/bin/timeout && -x /usr/bin/git && -x /usr/bin/python3 ]] || fail 'jit-preflight' 'RUNTIME_UNAVAILABLE'
[[ -d "$ROOT" && ! -L "$ROOT" ]] || fail 'jit-preflight' 'CHECKOUT_UNAVAILABLE'
cd -- "$ROOT" || fail 'jit-preflight' 'CHECKOUT_UNAVAILABLE'
[[ "$(pwd -P 2>/dev/null)" == "$ROOT" ]] || fail 'jit-preflight' 'CHECKOUT_MISMATCH'
[[ "$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse --show-toplevel 2>/dev/null)" == "$ROOT" ]] || fail 'jit-preflight' 'GIT_PREFLIGHT_FAILED'
[[ "$(/usr/bin/git -c "safe.directory=$ROOT" branch --show-current 2>/dev/null)" == "$BRANCH" ]] || fail 'jit-preflight' 'CANDIDATE_MISMATCH'
[[ "$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse HEAD 2>/dev/null)" == "$HEAD" ]] || fail 'jit-preflight' 'CANDIDATE_MISMATCH'
if [[ -v DOCKER_HOST || -v DOCKER_CONTEXT || -v DOCKER_TLS_VERIFY || -v DOCKER_CERT_PATH ]]; then
  fail 'jit-preflight' 'DOCKER_OVERRIDE_PRESENT'
fi
verify_hash "$RUNNER" "$RUNNER_SHA256" || fail 'jit-preflight' 'V7_HELPER_HASH_MISMATCH'
verify_hash "$TEST" "$TEST_SHA256" || fail 'jit-preflight' 'V7_TEST_HASH_MISMATCH'
verify_hash "$SYNTHETIC_RUNNER" "$SYNTHETIC_RUNNER_SHA256" || fail 'jit-preflight' 'V7_SYNTHETIC_RUNNER_HASH_MISMATCH'
verify_hash "$V6_SOURCE" "$V6_SOURCE_SHA256" || fail 'jit-preflight' 'V6_SOURCE_HASH_MISMATCH'

if diagnostic_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 600s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B "$RUNNER" 2>/dev/null)"; then
  diagnostic_status=0
else
  diagnostic_status=$?
fi
diagnostic_size="$(printf '%s' "$diagnostic_output" | wc -c)"
(( diagnostic_size <= 8192 )) || fail 'diagnostic-output' 'OUTPUT_LIMIT'
safe_output=''
invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ $SAFE_LINE_RE ]]; then
    safe_output+="$line"$'\n'
  else
    invalid_output=1
    break
  fi
done <<< "$diagnostic_output"
(( invalid_output == 0 )) || fail 'diagnostic-output' 'OUTPUT_REJECTED'
[[ -n "$safe_output" ]] || fail 'diagnostic-output' 'NO_SANITIZED_OUTPUT'

if (( diagnostic_status == 0 )) && [[ "$safe_output" == "$EXPECTED"$'\n' ]]; then
  printf '%s' "$safe_output"
  printf 'exit=0\n'
  exit 0
fi
printf '%s' "$safe_output"
if (( diagnostic_status == 0 )); then diagnostic_status=1; fi
printf 'exit=%s\n' "$diagnostic_status"
exit "$diagnostic_status"
