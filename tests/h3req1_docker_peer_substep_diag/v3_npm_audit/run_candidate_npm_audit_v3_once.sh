#!/usr/bin/env bash
set -u -o pipefail
export LANG=C LC_ALL=C

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly TAG='studiamatch-h3req1:20261009-v3'
readonly AUDIT_DIR="$ROOT/tests/h3req1_docker_peer_substep_diag/v3_npm_audit"
readonly PY_RUNNER="$AUDIT_DIR/candidate_npm_audit_v3_once.py"
readonly PY_RUNNER_SHA256='4ca41e19643192abec6f0547efd665e996be575e7ed39416940a2d840d34d2d6'
readonly TEST="$AUDIT_DIR/test_candidate_npm_audit_v3.py"
readonly TEST_SHA256='48036a07f1754335e2c503f248d68cdc07d353a0756fcd0afcb4d234c11c0c64'
readonly PACKAGE_JSON_SHA256='4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a'
readonly PACKAGE_LOCK_SHA256='8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc'
readonly DOCKER_SOCKET='unix:///var/run/docker.sock'

fail() {
  printf 'phase=%s|error_code=%s\n' "$1" "$2"
  exit 1
}

hash_is() {
  local path="$1" expected="$2" hash_line
  if ! hash_line="$(/usr/bin/sha256sum -- "$path" 2>/dev/null)"; then
    return 1
  fi
  [[ "${hash_line%% *}" == "$expected" ]]
}

(( EUID != 0 )) || fail 'wsl-preflight' 'RUN_AS_WSL_USER'
[[ -t 0 ]] || fail 'wsl-preflight' 'INTERACTIVE_TTY_REQUIRED'
[[ -x /usr/bin/sha256sum && -x /usr/bin/timeout && -x /usr/bin/mktemp && -x /usr/bin/find && -x /usr/bin/sort ]] || \
  fail 'runtime-preflight' 'RUNTIME_UNAVAILABLE'
[[ "$(uname -s 2>/dev/null)" == 'Linux' ]] || fail 'wsl-preflight' 'LINUX_REQUIRED'
[[ "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" == *microsoft* ]] || \
  fail 'wsl-preflight' 'WSL_REQUIRED'
[[ -d "$ROOT" && -f "$PY_RUNNER" && -f "$TEST" ]] || fail 'source-preflight' 'SOURCE_UNAVAILABLE'

if ! branch="$(/usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  git -C "$ROOT" branch --show-current 2>/dev/null)" || [[ "$branch" != "$BRANCH" ]]; then
  fail 'candidate-preflight' 'BRANCH_MISMATCH'
fi
if ! head="$(/usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  git -C "$ROOT" rev-parse HEAD 2>/dev/null)" || [[ "$head" != "$HEAD" ]]; then
  fail 'candidate-preflight' 'HEAD_MISMATCH'
fi
hash_is "$PY_RUNNER" "$PY_RUNNER_SHA256" || fail 'source-pin' 'RUNNER_HASH_MISMATCH'
hash_is "$TEST" "$TEST_SHA256" || fail 'source-pin' 'TEST_HASH_MISMATCH'
hash_is "$ROOT/web/package.json" "$PACKAGE_JSON_SHA256" || fail 'source-inputs' 'PACKAGE_JSON_MISMATCH'
hash_is "$ROOT/web/package-lock.json" "$PACKAGE_LOCK_SHA256" || fail 'source-inputs' 'PACKAGE_LOCK_MISMATCH'
expected_files=$'candidate_npm_audit_v3_once.py\nrun_candidate_npm_audit_v3_once.sh\ntest_candidate_npm_audit_v3.py'
actual_files="$(/usr/bin/find "$AUDIT_DIR" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | /usr/bin/sort)" || \
  fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'
[[ "$actual_files" == "$expected_files" ]] || fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'
non_file="$(/usr/bin/find "$AUDIT_DIR" -mindepth 1 -maxdepth 1 ! -type f -print -quit 2>/dev/null)" || \
  fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'
[[ -z "$non_file" ]] || fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'

docker_bin="$(command -v docker 2>/dev/null)" || fail 'docker-preflight' 'DOCKER_UNAVAILABLE'
readonly docker_bin
docker_config="$(/usr/bin/mktemp -d /tmp/h3req1-npm-audit-config.XXXXXX 2>/dev/null)" || \
  fail 'docker-preflight' 'CONFIG_DIR_FAILED'
cleanup() {
  [[ "$docker_config" == /tmp/h3req1-npm-audit-config.* ]] || return 0
  /usr/bin/rm -rf -- "$docker_config" 2>/dev/null || true
}
trap cleanup EXIT
chmod 700 "$docker_config" 2>/dev/null || fail 'docker-preflight' 'CONFIG_DIR_FAILED'

if ! image_id="$(/usr/bin/env -i HOME="$docker_config" DOCKER_CONFIG="$docker_config" DOCKER_HOST="$DOCKER_SOCKET" \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C LC_ALL=C \
  "$docker_bin" --host "$DOCKER_SOCKET" image inspect --format '{{.Id}}' "$TAG" 2>/dev/null)"; then
  fail 'image-preflight' 'IMAGE_INSPECT_FAILED'
fi
[[ "$image_id" == "$IMAGE" ]] || fail 'image-preflight' 'CANDIDATE_IMAGE_MISMATCH'
printf 'phase=image-preflight|error_code=OK\n'

container_command='set -u
if ! test_output="$(/opt/venv/bin/python -B /h3-audit/test_candidate_npm_audit_v3.py 2>/dev/null)"; then
  printf "phase=synthetic-tests|error_code=TESTS_FAILED\n"
  exit 41
fi
if [[ "$test_output" != "V3_NPM_AUDIT_SYNTHETIC_PASS:6/6" ]]; then
  printf "phase=synthetic-tests|error_code=TEST_RESULT_INVALID\n"
  exit 42
fi
exec /opt/venv/bin/python -B /h3-audit/candidate_npm_audit_v3_once.py'

if audit_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 150s \
  /usr/bin/env -i HOME="$docker_config" DOCKER_CONFIG="$docker_config" DOCKER_HOST="$DOCKER_SOCKET" \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C LC_ALL=C \
  "$docker_bin" --host "$DOCKER_SOCKET" run --rm --pull=never --network=bridge --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges:true --pids-limit=64 --memory=512m --memory-swap=512m \
  --cpus=0.5 --user=1000:1000 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  --mount "type=bind,source=$AUDIT_DIR,target=/h3-audit,readonly" \
  --env HOME=/tmp --env TMPDIR=/tmp --entrypoint /bin/bash "$IMAGE" -lc "$container_command" 2>/dev/null)"; then
  container_status=0
else
  container_status=$?
fi
if (( container_status == 124 )); then
  fail 'npm-audit' 'ETIMEDOUT'
fi
if (( container_status == 137 )); then
  fail 'docker-run' 'CONTAINER_TERMINATED'
fi
if [[ -z "$audit_output" ]] && (( container_status != 0 && container_status != 1 )); then
  fail 'docker-run' 'CONTAINER_FAILED'
fi
(( ${#audit_output} <= 8192 )) || fail 'npm-audit-capture' 'OUTPUT_LIMIT'
[[ -n "$audit_output" && "$audit_output" != *$'\n'* ]] || fail 'npm-audit-capture' 'OUTPUT_REJECTED'

if [[ "$audit_output" =~ ^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$ ]]; then
  printf '%s\n' "$audit_output"
  exit "${container_status:-1}"
fi
[[ "$container_status" -eq 0 && "$audit_output" == \{"auditCommandExit":* ]] || \
  fail 'npm-audit-capture' 'SUMMARY_REJECTED'
[[ "$audit_output" == *'"schema":"h3req1-npm-audit-summary-v1"'* ]] || \
  fail 'npm-audit-capture' 'SUMMARY_SCHEMA_INVALID'
printf 'phase=synthetic-tests|error_code=OK\nphase=npm-audit|error_code=OK\n'
printf 'summary=%s\n' "$audit_output"
