#!/usr/bin/env bash
set -u -o pipefail
export LANG=C LC_ALL=C

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly TAG='studiamatch-h3req1:20261009-v3'
readonly AUDIT_DIR="$ROOT/tests/h3req1_docker_peer_substep_diag/v3_npm_audit_classifier_v3"
readonly PY_RUNNER="$AUDIT_DIR/audit_candidate_v3_v3.py"
readonly TEST="$AUDIT_DIR/test_audit_candidate_v3_v3.py"
readonly DOCKER_SOCKET='unix:///var/run/docker.sock'

fail() {
  printf 'phase=%s|error_code=%s\n' "$1" "$2"
  exit 1
}

parse_capture() {
  local status="$1" output="$2" first rest
  CAPTURE_KIND='invalid'
  CAPTURE_CODE='OUTPUT_REJECTED'
  CAPTURE_PREFIX=''
  CAPTURE_DETAIL=''
  CAPTURE_SUMMARY=''
  (( ${#output} <= 8192 )) || { CAPTURE_CODE='OUTPUT_LIMIT'; return 0; }
  [[ -n "$output" ]] || { CAPTURE_CODE='OUTPUT_REJECTED'; return 0; }
  if [[ "$output" != *$'\n'* ]]; then
    if [[ "$output" =~ ^phase=synthetic-tests\|error_code=(TESTS_FAILED|TEST_RESULT_INVALID)$ ]]; then
      (( status == 1 )) || { CAPTURE_CODE='OUTPUT_STATUS_MISMATCH'; return 0; }
      CAPTURE_KIND='phase-error'
      CAPTURE_DETAIL="$output"
      CAPTURE_CODE=''
    fi
    return 0
  fi
  [[ "${output#*$'\n'}" != *$'\n'* ]] || { CAPTURE_CODE='OUTPUT_REJECTED'; return 0; }
  first="${output%%$'\n'*}"
  rest="${output#*$'\n'}"
  [[ "$first" == 'phase=synthetic-tests|error_code=OK' && -n "$rest" ]] || {
    CAPTURE_CODE='PHASE_ORDER_INVALID'
    return 0
  }
  CAPTURE_PREFIX="$first"
  if [[ "$rest" =~ ^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$ ]]; then
    (( status == 1 )) || { CAPTURE_CODE='OUTPUT_STATUS_MISMATCH'; return 0; }
    CAPTURE_KIND='phase-error'
    CAPTURE_DETAIL="$rest"
    CAPTURE_CODE=''
    return 0
  fi
  (( status == 0 )) || { CAPTURE_CODE='SUMMARY_STATUS_MISMATCH'; return 0; }
  [[ "$rest" == '{"auditCommandExit":'* || "$rest" == '{"counts":'* ]] || {
    CAPTURE_CODE='SUMMARY_REJECTED'
    return 0
  }
  [[ "$rest" == *'"schema":"h3req1-npm-audit-summary-v2"'* ]] || {
    CAPTURE_CODE='SUMMARY_SCHEMA_INVALID'
    return 0
  }
  [[ "$rest" == *'"image":"sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63"'* ]] || {
    CAPTURE_CODE='SUMMARY_IMAGE_INVALID'
    return 0
  }
  [[ "$rest" == *'"auditCommandExit":'* && "$rest" == *'"stderrPresent":'* && "$rest" == *'"verdict":'* ]] || {
    CAPTURE_CODE='SUMMARY_FIELDS_INVALID'
    return 0
  }
  CAPTURE_KIND='summary'
  CAPTURE_SUMMARY="$rest"
  CAPTURE_CODE=''
}

test_capture_parser() {
  local valid_summary
  valid_summary='{"auditCommandExit":1,"counts":{},"image":"sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63","schema":"h3req1-npm-audit-summary-v2","stderrPresent":false,"verdict":"HIGH_CRITICAL_PRESENT"}'
  parse_capture 1 'phase=synthetic-tests|error_code=TESTS_FAILED'
  [[ "$CAPTURE_KIND" == 'phase-error' && "$CAPTURE_DETAIL" == 'phase=synthetic-tests|error_code=TESTS_FAILED' ]] || \
    fail 'capture-synthetic-tests' 'SYNTHETIC_FAILURE_CASE_INVALID'
  parse_capture 1 $'phase=synthetic-tests|error_code=OK\nphase=npm-audit|error_code=REPORT_INVALID'
  [[ "$CAPTURE_KIND" == 'phase-error' && "$CAPTURE_PREFIX" == 'phase=synthetic-tests|error_code=OK' \
    && "$CAPTURE_DETAIL" == 'phase=npm-audit|error_code=REPORT_INVALID' ]] || \
    fail 'capture-synthetic-tests' 'ORDERED_AUDIT_FAILURE_CASE_INVALID'
  parse_capture 0 $'phase=synthetic-tests|error_code=OK\n'"$valid_summary"
  [[ "$CAPTURE_KIND" == 'summary' && "$CAPTURE_SUMMARY" == "$valid_summary" ]] || \
    fail 'capture-synthetic-tests' 'SUMMARY_CASE_INVALID'
  parse_capture 1 $'phase=npm-audit|error_code=REPORT_INVALID\nphase=synthetic-tests|error_code=OK'
  [[ "$CAPTURE_KIND" == 'invalid' && "$CAPTURE_CODE" == 'PHASE_ORDER_INVALID' ]] || \
    fail 'capture-synthetic-tests' 'REVERSED_PHASES_ACCEPTED'
  parse_capture 0 $'phase=synthetic-tests|error_code=OK\nphase=npm-audit|error_code=REPORT_INVALID'
  [[ "$CAPTURE_KIND" == 'invalid' && "$CAPTURE_CODE" == 'OUTPUT_STATUS_MISMATCH' ]] || \
    fail 'capture-synthetic-tests' 'STATUS_MISMATCH_ACCEPTED'
  parse_capture 0 $'phase=synthetic-tests|error_code=OK\n'"$valid_summary"$'\nextra'
  [[ "$CAPTURE_KIND" == 'invalid' && "$CAPTURE_CODE" == 'OUTPUT_REJECTED' ]] || \
    fail 'capture-synthetic-tests' 'EXTRA_LINE_ACCEPTED'
  printf 'phase=capture-synthetic-tests|error_code=OK\n'
}

hash_is() {
  local path="$1" expected="$2" hash_line
  if ! hash_line="$(/usr/bin/sha256sum -- "$path" 2>/dev/null)"; then return 1; fi
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
hash_is "$PY_RUNNER" 'd821152adfde8fe1b9b58c51b2b04c344581211e3318521c1709636d650dd7e1' || fail 'source-pin' 'RUNNER_HASH_MISMATCH'
hash_is "$TEST" '46ae18fa6edc33c9625d6256ac0933fcd4dfedad4ce3d61fb177817d31ee5cfe' || fail 'source-pin' 'TEST_HASH_MISMATCH'
hash_is "$ROOT/web/package.json" '4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a' || fail 'source-inputs' 'PACKAGE_JSON_MISMATCH'
hash_is "$ROOT/web/package-lock.json" '8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc' || fail 'source-inputs' 'PACKAGE_LOCK_MISMATCH'
expected_files=$'audit_candidate_v3_v3.py\nrun_candidate_npm_audit_classifier_v3_once.sh\ntest_audit_candidate_v3_v3.py'
actual_files="$(/usr/bin/find "$AUDIT_DIR" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | /usr/bin/sort)" || \
  fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'
[[ "$actual_files" == "$expected_files" ]] || fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'
non_file="$(/usr/bin/find "$AUDIT_DIR" -mindepth 1 -maxdepth 1 ! -type f -print -quit 2>/dev/null)" || \
  fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'
[[ -z "$non_file" ]] || fail 'source-pin' 'SOURCE_DIRECTORY_INVALID'
test_capture_parser

docker_bin="$(command -v docker 2>/dev/null)" || fail 'docker-preflight' 'DOCKER_UNAVAILABLE'
readonly docker_bin
docker_config="$(/usr/bin/mktemp -d /tmp/h3req1-npm-audit-classifier-config.XXXXXX 2>/dev/null)" || \
  fail 'docker-preflight' 'CONFIG_DIR_FAILED'
cleanup() {
  [[ "$docker_config" == /tmp/h3req1-npm-audit-classifier-config.* ]] || return 0
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
if ! test_output="$(/opt/venv/bin/python -B /h3-audit/test_audit_candidate_v3_v3.py 2>/dev/null)"; then
  printf "phase=synthetic-tests|error_code=TESTS_FAILED\n"
  exit 1
fi
if [[ "$test_output" != "V3_NPM_AUDIT_CLASSIFIER_V3_SYNTHETIC_PASS:16/16" ]]; then
  printf "phase=synthetic-tests|error_code=TEST_RESULT_INVALID\n"
  exit 1
fi
printf "phase=synthetic-tests|error_code=OK\n"
exec /opt/venv/bin/python -B /h3-audit/audit_candidate_v3_v3.py'

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
if (( container_status == 124 )); then fail 'npm-audit' 'ETIMEDOUT'; fi
if (( container_status == 137 )); then fail 'docker-run' 'CONTAINER_TERMINATED'; fi
if (( container_status != 0 && container_status != 1 )); then fail 'docker-run' 'CONTAINER_FAILED'; fi
parse_capture "$container_status" "$audit_output"
if [[ "$CAPTURE_KIND" == 'phase-error' ]]; then
  [[ -z "$CAPTURE_PREFIX" ]] || printf '%s\n' "$CAPTURE_PREFIX"
  printf '%s\n' "$CAPTURE_DETAIL"
  exit 1
fi
[[ "$CAPTURE_KIND" == 'summary' ]] || fail 'npm-audit-capture' "$CAPTURE_CODE"
printf '%s\nphase=npm-audit|error_code=OK\n' "$CAPTURE_PREFIX"
printf 'summary=%s\n' "$CAPTURE_SUMMARY"
