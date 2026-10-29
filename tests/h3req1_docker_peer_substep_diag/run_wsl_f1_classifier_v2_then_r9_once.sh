#!/bin/bash
set -Eeuo pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly DIAGNOSTIC_RUNNER='tests/h3req1_docker_peer_substep_diag/run_wsl_f1_read_classification_v2_once.sh'
readonly DIAGNOSTIC_RUNNER_SHA256='781750a9e839eaa81fa3e17287fba970e9c5535d9c097f3caa88df05f42b8c8a'
readonly DIAGNOSTIC_HELPER='tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_v2_once.py'
readonly DIAGNOSTIC_HELPER_SHA256='d7ae28af55d3f45d41588fc8b2d3f5ed5b56710d0d91d5e7d49618d7e1cca5bf'
readonly TEST_FILE='tests/h3req1_docker_peer_substep_diag/test_f1_read_failure_classification_once.py'
readonly TEST_FILE_SHA256='231a6d04ad00ac0cbc4574378109ffd39dde5cfe897b83e692fe55ac35113574'
readonly SYNTHETIC_RUNNER='tests/h3req1_docker_peer_substep_diag/classifier_synthetic_runner_v2.py'
readonly SYNTHETIC_RUNNER_SHA256='45ad0f6849a0c4a96becb25df54c7df7ddd94716bdeddba3e0ae1a2400d44bdf'
readonly R9_ROOT='/tmp/h3req1-g03-validation-29d8fff9-r2'
readonly R9_RUNNER='/tmp/h3req1-g03-validation-29d8fff9-r2/run-r9.sh'
readonly R9_RUNNER_SHA256='2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97'
readonly R9_MANIFEST_SHA256='b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866'
readonly R9_TOOLS_SHA256='4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa'
readonly EXPECTED_DIAGNOSTIC=$'phase=desktop-wsl-endpoint-attested|error_code=OK\nphase=classifier-synthetic-image-read|error_code=OK\nphase=classifier-synthetic-tests|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK'
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'

emit_failure() {
  printf 'phase=classifier-v2-r9-preflight|error_code=%s\n' "$1"
  exit 1
}

[[ "$EUID" != 0 ]] || emit_failure 'RUN_AS_WSL_USER'
[[ -t 0 ]] || emit_failure 'INTERACTIVE_TTY_REQUIRED'
[[ -x /usr/bin/sha256sum && -x /usr/bin/timeout && -x /usr/bin/git ]] || emit_failure 'RUNTIME_UNAVAILABLE'
[[ -d "$ROOT" && ! -L "$ROOT" ]] || emit_failure 'CHECKOUT_UNAVAILABLE'
cd -- "$ROOT" || emit_failure 'CHECKOUT_UNAVAILABLE'
[[ "$(pwd -P 2>/dev/null)" == "$ROOT" ]] || emit_failure 'CHECKOUT_MISMATCH'

git_root="$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse --show-toplevel 2>/dev/null)" || emit_failure 'GIT_PREFLIGHT_FAILED'
branch="$(/usr/bin/git -c "safe.directory=$ROOT" branch --show-current 2>/dev/null)" || emit_failure 'GIT_PREFLIGHT_FAILED'
head="$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse HEAD 2>/dev/null)" || emit_failure 'GIT_PREFLIGHT_FAILED'
[[ "$git_root" == "$ROOT" && "$branch" == "$BRANCH" && "$head" == "$HEAD" ]] || emit_failure 'CANDIDATE_MISMATCH'

if [[ -v DOCKER_HOST || -v DOCKER_CONTEXT || -v DOCKER_TLS_VERIFY || -v DOCKER_CERT_PATH ]]; then
  emit_failure 'DOCKER_OVERRIDE_PRESENT'
fi

verify_hash() {
  local file="$1" expected="$2" hash_line
  [[ -f "$file" && ! -L "$file" ]] || return 1
  hash_line="$(/usr/bin/sha256sum -- "$file" 2>/dev/null)" || return 1
  [[ "${hash_line%% *}" == "$expected" ]]
}

verify_hash "$DIAGNOSTIC_RUNNER" "$DIAGNOSTIC_RUNNER_SHA256" || emit_failure 'DIAGNOSTIC_RUNNER_HASH_MISMATCH'
verify_hash "$DIAGNOSTIC_HELPER" "$DIAGNOSTIC_HELPER_SHA256" || emit_failure 'DIAGNOSTIC_HELPER_HASH_MISMATCH'
verify_hash "$TEST_FILE" "$TEST_FILE_SHA256" || emit_failure 'TEST_FILE_HASH_MISMATCH'
verify_hash "$SYNTHETIC_RUNNER" "$SYNTHETIC_RUNNER_SHA256" || emit_failure 'SYNTHETIC_RUNNER_HASH_MISMATCH'
[[ -d "$R9_ROOT" && ! -L "$R9_ROOT" && -d "${R9_ROOT}.tools" && ! -L "${R9_ROOT}.tools" ]] || emit_failure 'R9_PACKAGE_UNAVAILABLE'
verify_hash "$R9_RUNNER" "$R9_RUNNER_SHA256" || emit_failure 'R9_RUNNER_HASH_MISMATCH'
verify_hash "$R9_ROOT/r9-package.sha256" "$R9_MANIFEST_SHA256" || emit_failure 'R9_MANIFEST_HASH_MISMATCH'
verify_hash "${R9_ROOT}.tools/tools.sha256" "$R9_TOOLS_SHA256" || emit_failure 'R9_TOOLS_HASH_MISMATCH'

diagnostic_output=''
if diagnostic_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=1s 100s /bin/bash "$DIAGNOSTIC_RUNNER" 2>/dev/null)"; then
  diagnostic_status=0
else
  diagnostic_status=$?
fi

safe_output=''
invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ $SAFE_LINE_RE ]]; then
    safe_output+="${line}"$'\n'
  else
    invalid_output=1
    break
  fi
done <<< "$diagnostic_output"

if (( invalid_output )); then
  printf 'phase=output-capture|error_code=OUTPUT_REJECTED\n'
  exit 1
fi
if [[ -n "$safe_output" ]]; then
  printf '%s' "$safe_output"
else
  printf 'phase=output-capture|error_code=NO_SANITIZED_OUTPUT\n'
fi
if (( diagnostic_status != 0 )) || [[ "$diagnostic_output" != "$EXPECTED_DIAGNOSTIC" ]]; then
  exit 1
fi

if ! (cd -- "$R9_ROOT" && /usr/bin/sha256sum -c r9-package.sha256 >/dev/null 2>&1); then
  printf 'phase=r9-preflight|error_code=PACKAGE_HASH_MISMATCH\n'
  exit 1
fi
if ! (cd -- "${R9_ROOT}.tools" && /usr/bin/sha256sum -c tools.sha256 >/dev/null 2>&1); then
  printf 'phase=r9-preflight|error_code=TOOLS_HASH_MISMATCH\n'
  exit 1
fi

if /usr/bin/timeout --foreground --signal=TERM --kill-after=5s 180s /bin/bash "$R9_RUNNER"; then
  printf 'phase=r9|error_code=OK\n'
else
  r9_status=$?
  printf 'phase=r9|error_code=CHECK_FAILED\n'
  exit "$r9_status"
fi
