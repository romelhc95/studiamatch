#!/usr/bin/env bash
set -u -o pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly RUNNER='tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_socket_v3_once.py'
readonly RUNNER_SHA256='efd3c608ef08e82ec882c95bc4ec86814aa3900c819cf3f5b84d0d8b99228ddc'
readonly PROBE='tests/h3req1_docker_peer_substep_diag/desktop_wsl_engine_socket_probe_v1_once.py'
readonly PROBE_SHA256='fb8ee1b3afb4496e4c00d827cec57793c449957193fae7c4924485db758dcbbf'
readonly R9_ROOT='/tmp/h3req1-g03-validation-29d8fff9-r2'
readonly R9_RUNNER='/tmp/h3req1-g03-validation-29d8fff9-r2/run-r9.sh'
readonly R9_RUNNER_SHA256='2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97'
readonly R9_MANIFEST_SHA256='b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866'
readonly R9_TOOLS_SHA256='4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa'
readonly EXPECTED_DIAGNOSTIC=$'phase=desktop-wsl-socket-path|error_code=OK\nphase=desktop-wsl-socket-create|error_code=OK\nphase=desktop-wsl-socket-connect|error_code=OK\nphase=desktop-wsl-engine-response-read|error_code=OK\nphase=desktop-wsl-engine-identity|error_code=OK\nphase=desktop-wsl-endpoint-attested|error_code=OK\nphase=classifier-synthetic-image-read|error_code=OK\nphase=classifier-synthetic-tests|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK'
readonly SAFE_LINE_RE='^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$'

emit_failure() {
  printf 'phase=socket-classifier-r9-preflight|error_code=%s\n' "$1"
  exit 1
}

(( EUID != 0 )) || emit_failure 'RUN_AS_WSL_USER'
[[ -t 0 ]] || emit_failure 'INTERACTIVE_TTY_REQUIRED'
[[ -x /usr/bin/sha256sum && -x /usr/bin/timeout && -x /usr/bin/git && -x /usr/bin/python3 ]] || emit_failure 'RUNTIME_UNAVAILABLE'
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

verify_hash "$RUNNER" "$RUNNER_SHA256" || emit_failure 'RUNNER_HASH_MISMATCH'
verify_hash "$PROBE" "$PROBE_SHA256" || emit_failure 'PROBE_HASH_MISMATCH'
[[ -d "$R9_ROOT" && ! -L "$R9_ROOT" && -d "${R9_ROOT}.tools" && ! -L "${R9_ROOT}.tools" ]] || emit_failure 'R9_PACKAGE_UNAVAILABLE'
verify_hash "$R9_RUNNER" "$R9_RUNNER_SHA256" || emit_failure 'R9_RUNNER_HASH_MISMATCH'
verify_hash "$R9_ROOT/r9-package.sha256" "$R9_MANIFEST_SHA256" || emit_failure 'R9_MANIFEST_HASH_MISMATCH'
verify_hash "${R9_ROOT}.tools/tools.sha256" "$R9_TOOLS_SHA256" || emit_failure 'R9_TOOLS_HASH_MISMATCH'

diagnostic_output=''
if diagnostic_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=1s 100s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -B "$ROOT/$RUNNER" 2>/dev/null)"; then
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
