#!/usr/bin/env bash
set -u -o pipefail
export LANG=C LC_ALL=C

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly PYTHON_RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_v7_split_pair_once.py"
readonly PYTHON_RUNNER_SHA256='331d2a99bfbae7d8bd470a0fc5ac91e74eb8af26f72e2b244ad4683d68d3b4ef'
readonly PYTHON_TEST="$ROOT/tests/h3req1_docker_peer_substep_diag/test_f1_read_failure_classification_v7_split_pair.py"
readonly PYTHON_TEST_SHA256='c357175e1a72638db7ac494e5ef4ad86b4a4f107863cba49deb3692ee473fef2'
readonly PYTHON_SYNTHETIC_RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/classifier_synthetic_runner_v7_split_pair.py"
readonly PYTHON_SYNTHETIC_RUNNER_SHA256='0c0a106a3adfe8a471913ca649ef1af110952a44490f020d5644334e622f68b4'
readonly R6_SOURCE="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_v6_once.py"
readonly R6_SOURCE_SHA256='b17266a33559b16b28cdf1b619f9b5d7dae666203f6d9a357b046ed7ae809128'
readonly R9_ROOT='/tmp/h3req1-g03-validation-29d8fff9-r3'
readonly R9_DISPATCH="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-r3-sanitized.sh"
readonly R9_DISPATCH_SHA256='bdef0351abfa8697cb13c788b5b3cdbb7a5568672e4c8c9d56b860826364f0a7'
readonly R9_PACKAGE_MANIFEST_SHA256='688e81efaae70a841a64cd4c0a074ae3c76c355f5ef9bc77756cff9ad607fc02'
readonly R9_INPUTS_SHA256='6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee'
readonly R9_TOOLS='/tmp/h3req1-g03-validation-29d8fff9-r2.tools'
readonly R9_TOOLS_SHA256='4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa'
readonly MAX_DIAGNOSTIC_BYTES=8192
readonly MAX_R9_BYTES=2048
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'
readonly EXPECTED_DIAGNOSTIC=$'phase=prior-desktop-wsl-endpoint-attestation|error_code=OK\nphase=classifier-synthetic-image-volumes-read|error_code=OK\nphase=classifier-synthetic-image-read|error_code=OK\nphase=classifier-synthetic-unit-tests|error_code=OK\nphase=f1-template-synthetic-check|error_code=OK\nphase=classifier-synthetic-tests|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK'

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
verify_hash "$PYTHON_RUNNER" "$PYTHON_RUNNER_SHA256" || fail 'jit-preflight' 'V7_HELPER_HASH_MISMATCH'
verify_hash "$PYTHON_TEST" "$PYTHON_TEST_SHA256" || fail 'jit-preflight' 'V7_TEST_HASH_MISMATCH'
verify_hash "$PYTHON_SYNTHETIC_RUNNER" "$PYTHON_SYNTHETIC_RUNNER_SHA256" || fail 'jit-preflight' 'V7_SYNTHETIC_RUNNER_HASH_MISMATCH'
verify_hash "$R6_SOURCE" "$R6_SOURCE_SHA256" || fail 'jit-preflight' 'V6_SOURCE_HASH_MISMATCH'
verify_hash "$R9_DISPATCH" "$R9_DISPATCH_SHA256" || fail 'jit-preflight' 'R9_DISPATCH_HASH_MISMATCH'

[[ -d "$R9_ROOT" && ! -L "$R9_ROOT" && -d "$R9_TOOLS" && ! -L "$R9_TOOLS" ]] || fail 'r9-preflight' 'PACKAGE_UNAVAILABLE'
[[ "$(/usr/bin/stat -c '%a' "$R9_ROOT" 2>/dev/null)" == '755' ]] || fail 'r9-preflight' 'PACKAGE_MODE_MISMATCH'
verify_hash "$R9_ROOT/r3-package.sha256" "$R9_PACKAGE_MANIFEST_SHA256" || fail 'r9-preflight' 'PACKAGE_HASH_MISMATCH'
verify_hash "$R9_ROOT/inputs.sha256" "$R9_INPUTS_SHA256" || fail 'r9-preflight' 'INPUT_MANIFEST_MISMATCH'
verify_hash "$R9_TOOLS/tools.sha256" "$R9_TOOLS_SHA256" || fail 'r9-preflight' 'TOOLS_MANIFEST_MISMATCH'
(cd "$R9_ROOT" && /usr/bin/sha256sum -c r3-package.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'PACKAGE_HASH_MISMATCH'
(cd "$R9_ROOT" && /usr/bin/sha256sum -c inputs.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'INPUT_MANIFEST_MISMATCH'
(cd "$R9_TOOLS" && /usr/bin/sha256sum -c tools.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'TOOLS_MANIFEST_MISMATCH'

candidate_inputs=0
package_only_inputs=0
input_mismatch=0
while read -r expected relative; do
  path="$(printf '%s' "$relative" | sed 's#^\./##')"
  case "$path" in
    fetch-linters.sh|run-in-container.sh|run-r8.sh)
      package_only_inputs=$((package_only_inputs + 1))
      continue
      ;;
  esac
  candidate_inputs=$((candidate_inputs + 1))
  if [[ ! -f "$ROOT/$path" || -L "$ROOT/$path" ]]; then
    input_mismatch=$((input_mismatch + 1))
    continue
  fi
  current_hash="$(/usr/bin/sha256sum -- "$ROOT/$path" 2>/dev/null)" || {
    input_mismatch=$((input_mismatch + 1))
    continue
  }
  read -r actual_hash _ <<< "$current_hash"
  [[ "$actual_hash" == "$expected" ]] || input_mismatch=$((input_mismatch + 1))
done < "$R9_ROOT/inputs.sha256"
[[ "$candidate_inputs" == 68 && "$package_only_inputs" == 3 && "$input_mismatch" == 0 ]] || fail 'r9-preflight' 'CANDIDATE_INPUT_DRIFT'

if diagnostic_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 600s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B "$PYTHON_RUNNER" 2>/dev/null)"; then
  diagnostic_status=0
else
  diagnostic_status=$?
fi
diagnostic_size="$(printf '%s' "$diagnostic_output" | wc -c)"
(( diagnostic_size <= MAX_DIAGNOSTIC_BYTES )) || fail 'diagnostic-output' 'OUTPUT_LIMIT'
safe_diagnostic=''
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  [[ "$line" =~ $SAFE_LINE_RE ]] || fail 'diagnostic-output' 'OUTPUT_REJECTED'
  safe_diagnostic+="$line"$'\n'
done <<< "$diagnostic_output"
if (( diagnostic_status != 0 )) || [[ "$safe_diagnostic" != "$EXPECTED_DIAGNOSTIC"$'\n' ]]; then
  [[ -n "$safe_diagnostic" ]] && printf '%s' "$safe_diagnostic"
  if (( diagnostic_status == 0 )); then diagnostic_status=1; fi
  printf 'exit=%s\n' "$diagnostic_status"
  exit "$diagnostic_status"
fi
printf '%s\n' "$diagnostic_output"

if r9_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 240s /bin/bash "$R9_DISPATCH" 2>/dev/null)"; then
  r9_status=0
else
  r9_status=$?
fi
r9_size="$(printf '%s' "$r9_output" | wc -c)"
(( r9_size <= MAX_R9_BYTES )) || fail 'r9-output' 'OUTPUT_LIMIT'
safe_r9=''
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ ^phase=r9-[a-z0-9-]{1,48}\|error_code=[A-Z][A-Z0-9_]{0,47}$ ]] || [[ "$line" =~ ^exit=[0-9]{1,3}$ ]]; then
    safe_r9+="$line"$'\n'
  else
    fail 'r9-output' 'OUTPUT_REJECTED'
  fi
done <<< "$r9_output"
expected_r9=$'phase=r9-context|error_code=OK\nphase=r9-input-hashes|error_code=OK\nphase=r9-tool-hashes|error_code=OK\nphase=r9-tool-extraction|error_code=OK\nphase=r9-tool-versions|error_code=OK\nphase=r9-candidate-copy|error_code=OK\nphase=r9-npm-dependency-manifest|error_code=OK\nphase=r9-node-and-typescript-versions|error_code=OK\nphase=r9-actionlint|error_code=OK\nphase=r9-shellcheck|error_code=OK\nphase=r9-eslint|error_code=OK\nphase=r9-typescript|error_code=OK\nphase=r9-protected-workflow-tests|error_code=OK\nphase=r9-credential-scan|error_code=OK\nphase=r9-protected-path-guard|error_code=OK\nphase=r9-summary|error_code=ALL_CHECKS_OK\n'
if (( r9_status != 0 )) || [[ "$safe_r9" != "$expected_r9" ]]; then
  [[ -n "$safe_r9" ]] && printf '%s' "$safe_r9"
  if [[ "$safe_r9" != *$'exit='* ]]; then
    if (( r9_status == 0 )); then r9_status=1; fi
    printf 'exit=%s\n' "$r9_status"
  fi
  exit "$r9_status"
fi
printf '%s' "$safe_r9"
printf 'phase=split-pair-v7-r9-summary|error_code=ALL_CHECKS_OK\nexit=0\n'
