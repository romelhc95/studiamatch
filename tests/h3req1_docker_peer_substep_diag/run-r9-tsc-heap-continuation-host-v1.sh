#!/usr/bin/env bash
set -u -o pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly PACKAGE='/tmp/h3req1-g03-validation-29d8fff9-r6'
readonly IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly NODE_VOLUME='studiamatch_h3req1_node_modules'
readonly INNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-tsc-heap-continuation-inner-v1.sh"
readonly TYPEGEN_CLASSIFIER="$ROOT/tests/h3req1_docker_peer_substep_diag/r9_typegen_classifier_v1.py"
readonly TYPEGEN_CLASSIFIER_TESTS="$ROOT/tests/h3req1_docker_peer_substep_diag/test_r9_typegen_classifier_v1.py"
readonly EVIDENCE="$ROOT/.context/evidencia/h3req1_g03_r9_tsc_heap_and_pending_suites_2026-10-10_v5.txt"
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_PACKAGE_SHA='d10cc19b87adfff36f8092c97b59dc8fb4a247166c0dcbf8f0653dd9f2db6186'
readonly EXPECTED_INPUTS_SHA='c53e3321190646a2449e28b935711fc6f7b8425d1b19289f2374f4488eaff4c8'
readonly EXPECTED_IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly EXPECTED_INNER_SHA='6f688c868a22ea25d712193aaf589b6a8dd033c01d0e83d065b97dc838d750d3'
readonly EXPECTED_TYPEGEN_CLASSIFIER_SHA='91005ad43781de0ba157898f7851a1ea273ca211b7772b4285218e3234a3e901'
readonly EXPECTED_TYPEGEN_CLASSIFIER_TESTS_SHA='f00cfc98c3b566c104abdb702c97876edef6e1c0c43572c78db63bf82afc1447'
readonly NAME="h3req1-g03-tsc-heap-20261010-$$"
readonly LABEL_SCOPE='org.studiamatch.h3req1.scope=g03-tsc-heap-continuation'
readonly LABEL_FIXTURE="org.studiamatch.h3req1.fixture=$NAME"

emit_fail() { printf 'phase=%s|error_code=%s\nexit=%s\n' "$1" "$2" "${3:-1}"; exit "${3:-1}"; }
hash_is() {
  local line
  [[ -f "$1" && ! -L "$1" ]] || return 1
  line="$(/usr/bin/sha256sum -- "$1" 2>/dev/null)" || return 1
  [[ "${line%% *}" == "$2" ]]
}

[[ "$EUID" != 0 && "$(id -un 2>/dev/null)" == romel ]] || emit_fail g03-preflight RUN_AS_ROMEL_NONROOT
[[ "$(git -C "$ROOT" branch --show-current 2>/dev/null)" == "$EXPECTED_BRANCH" && \
   "$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" == "$EXPECTED_HEAD" ]] || emit_fail g03-candidate-identity MISMATCH
[[ ! -L "$EVIDENCE" && ! -e "$EVIDENCE" ]] || emit_fail g03-preflight EVIDENCE_PATH_OCCUPIED
[[ -d "$PACKAGE" && ! -L "$PACKAGE" ]] || emit_fail g03-snapshot SNAPSHOT_UNAVAILABLE
hash_is "$PACKAGE/r4-package.sha256" "$EXPECTED_PACKAGE_SHA" || emit_fail g03-snapshot PACKAGE_MANIFEST_MISMATCH
hash_is "$PACKAGE/inputs.sha256" "$EXPECTED_INPUTS_SHA" || emit_fail g03-snapshot INPUT_MANIFEST_MISMATCH
(cd "$PACKAGE" && /usr/bin/sha256sum -c r4-package.sha256 >/dev/null 2>&1) || emit_fail g03-snapshot PACKAGE_CONTENT_MISMATCH
(cd "$PACKAGE" && /usr/bin/sha256sum -c inputs.sha256 >/dev/null 2>&1) || emit_fail g03-snapshot INPUT_CONTENT_MISMATCH
hash_is "$INNER" "$EXPECTED_INNER_SHA" || emit_fail g03-runner-hash INNER_RUNNER_MISMATCH
hash_is "$TYPEGEN_CLASSIFIER" "$EXPECTED_TYPEGEN_CLASSIFIER_SHA" || emit_fail g03-runner-hash TYPEGEN_CLASSIFIER_MISMATCH
hash_is "$TYPEGEN_CLASSIFIER_TESTS" "$EXPECTED_TYPEGEN_CLASSIFIER_TESTS_SHA" || emit_fail g03-runner-hash TYPEGEN_CLASSIFIER_TESTS_MISMATCH

if ! python3 - "$ROOT" "$PACKAGE/inputs.sha256" <<'PYSOURCE' >/dev/null 2>&1
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = Path(sys.argv[2])
package_only = {'fetch-linters.sh', 'run-in-container.sh', 'run-r8.sh'}
rows = manifest.read_text(encoding='utf-8').splitlines()
if len(rows) != 71:
    raise SystemExit(1)
missing = set()
checked = 0
for row in rows:
    digest, relative = row.split('  ', 1)
    if not relative.startswith('./') or len(digest) != 64:
        raise SystemExit(1)
    relative = relative[2:]
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or any(part == '.env' or part.startswith('.env.') for part in path.parts):
        raise SystemExit(1)
    source = root / path
    if not source.exists():
        if relative in package_only:
            missing.add(relative)
            continue
        raise SystemExit(1)
    if source.is_symlink() or not source.is_file():
        raise SystemExit(1)
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise SystemExit(1)
    checked += 1
if checked != 68 or missing != package_only:
    raise SystemExit(1)
PYSOURCE
then
  emit_fail g03-candidate-source SOURCE_HASH_MISMATCH
fi
for spec in \
  '276641005c0bc1dc64b26e479b9ef197137a69b3dc4b08be8e56246fdb75df23:.github/workflows/security-audit.yml' \
  '016551e6a6e280dcd515788ffcf93b18a6d48647079e3c0cd7be9c2d4f58864b:.github/workflows/protected-workflow-integrity.yml' \
  '3899f29a026861400707827e7e6c9248446d938451232eb5fee157775b39fda8:.github/workflows/db-sync-to-pro.yml'; do
  expected="${spec%%:*}"
  rel="${spec#*:}"
  hash_is "$PACKAGE/$rel" "$expected" || emit_fail g03-actionlint-reuse INPUT_HASH_MISMATCH
done

/usr/bin/docker --context default context inspect default --format '{{ .Endpoints.docker.Host }}' 2>/dev/null | /usr/bin/grep -Fxq 'unix:///var/run/docker.sock' || emit_fail g03-docker-context ENDPOINT_MISMATCH
image_id="$(/usr/bin/docker --context default image inspect --format '{{.Id}}' "$IMAGE" 2>/dev/null)" || emit_fail g03-docker-image IMAGE_UNAVAILABLE
[[ "$image_id" == "$EXPECTED_IMAGE" ]] || emit_fail g03-docker-image IMAGE_MISMATCH
/usr/bin/docker --context default volume inspect "$NODE_VOLUME" >/dev/null 2>&1 || emit_fail g03-node-volume VOLUME_UNAVAILABLE
if /usr/bin/docker --context default inspect "$NAME" >/dev/null 2>&1; then emit_fail g03-fixture-name NAME_ALREADY_EXISTS; fi

tmp_out="$(/usr/bin/mktemp /tmp/h3req1-g03-tsc-output.XXXXXXXX 2>/dev/null)" || emit_fail g03-output-capture TEMP_UNAVAILABLE
umask 077
set -o noclobber
if ! { exec 3>"$EVIDENCE"; } 2>/dev/null; then
  set +o noclobber
  /usr/bin/rm -f -- "$tmp_out"
  emit_fail g03-evidence EVIDENCE_CREATE_FAILED
fi
set +o noclobber
evidence_open=1
cleanup_armed=1
cleanup_done=0
cleanup_in_progress=0
cleanup_signal='NONE'
container_id='unavailable'
container_state='unavailable'
cleanup_code='NOT_ATTEMPTED'

cleanup_fixture() {
  [[ "$cleanup_done" == 0 ]] || return 0
  [[ "$cleanup_in_progress" == 0 ]] || return 1
  cleanup_in_progress=1
  trap 'cleanup_signal=INT' INT
  trap 'cleanup_signal=TERM' TERM
  trap 'cleanup_signal=HUP' HUP
  cleanup_code='INSPECT_FAILED'
  local identity='' found_id='' found_image='' found_scope='' found_fixture='' found_state=''
  identity="$(/usr/bin/docker --context default inspect --format '{{.Id}}|{{.Image}}|{{index .Config.Labels "org.studiamatch.h3req1.scope"}}|{{index .Config.Labels "org.studiamatch.h3req1.fixture"}}|{{.State.Status}}' "$NAME" 2>/dev/null)" || identity=''
  if [[ -n "$identity" ]]; then
    IFS='|' read -r found_id found_image found_scope found_fixture found_state <<< "$identity"
    if [[ "$found_id" =~ ^[0-9a-f]{64}$ && ( "$container_id" == unavailable || "$found_id" == "$container_id" ) && \
          "$found_image" == "$EXPECTED_IMAGE" && "$found_scope" == 'g03-tsc-heap-continuation' && \
          "$found_fixture" == "$NAME" ]]; then
      container_id="$found_id"
      cleanup_code='OK'
      if [[ "$found_state" == running ]]; then
        /usr/bin/timeout --foreground --signal=TERM --kill-after=2s 12s \
          /usr/bin/docker --context default stop --time 5 "$found_id" >/dev/null 2>&1 || cleanup_code='STOP_FAILED'
        identity="$(/usr/bin/docker --context default inspect --format '{{.Id}}|{{.Image}}|{{index .Config.Labels "org.studiamatch.h3req1.scope"}}|{{index .Config.Labels "org.studiamatch.h3req1.fixture"}}|{{.State.Status}}' "$found_id" 2>/dev/null)" || identity=''
        [[ "$identity" == "$found_id|$EXPECTED_IMAGE|g03-tsc-heap-continuation|$NAME|exited" ]] || cleanup_code='POST_STOP_IDENTITY_MISMATCH'
      elif [[ "$found_state" != exited && "$found_state" != created ]]; then
        cleanup_code='STATE_NOT_REMOVABLE'
      fi
      if [[ "$cleanup_code" == OK ]]; then
        /usr/bin/docker --context default rm "$found_id" >/dev/null 2>&1 || cleanup_code='REMOVE_FAILED'
        if [[ "$cleanup_code" == OK ]] && /usr/bin/docker --context default inspect "$found_id" >/dev/null 2>&1; then
          cleanup_code='REMOVE_NOT_CONFIRMED'
        fi
      fi
    else
      cleanup_code='IDENTITY_MISMATCH'
    fi
  fi
  if [[ "${evidence_open:-0}" == 1 ]]; then
    printf 'phase=r9-fixture-cleanup|error_code=%s\n' "$cleanup_code" >&3 2>/dev/null || true
  fi
  cleanup_done=1
  cleanup_in_progress=0
  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap 'exit 129' HUP
  [[ "$cleanup_code" == OK ]]
}

# Invoked indirectly by the EXIT trap below.
# shellcheck disable=SC2329
on_exit() {
  local saved_status=$?
  trap - EXIT INT TERM HUP
  if [[ "${cleanup_armed:-0}" == 1 && "${cleanup_done:-0}" == 0 ]]; then
    printf 'phase=g03-host-exit|error_code=CLEANUP_REQUIRED|exit=%s\n' "$saved_status" >&3 2>/dev/null || true
    printf 'phase=g03-host-exit|error_code=CLEANUP_REQUIRED|exit=%s\n' "$saved_status"
    cleanup_fixture || true
    printf 'phase=r9-fixture-cleanup|error_code=%s\n' "$cleanup_code"
    case "$cleanup_signal" in
      INT|TERM|HUP)
        printf 'phase=g03-cleanup-signal|error_code=DEFERRED_%s\n' "$cleanup_signal" >&3 2>/dev/null || true
        printf 'phase=g03-cleanup-signal|error_code=DEFERRED_%s\n' "$cleanup_signal"
        ;;
    esac
    printf 'exit=%s\n' "$saved_status" >&3 2>/dev/null || true
    printf 'exit=%s\n' "$saved_status"
  fi
  exit "$saved_status"
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

container_status=0
/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 300s \
  /usr/bin/docker --context default run --name "$NAME" --label "$LABEL_SCOPE" --label "$LABEL_FIXTURE" --pull=never --network=none --read-only \
  --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges \
  --memory=4g --memory-swap=4g --cpus=2 --pids-limit=128 \
  --tmpfs /work:rw,exec,nosuid,nodev,size=512m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /work/candidate:rw,exec,nosuid,nodev,size=512m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /work/candidate/web:rw,exec,nosuid,nodev,size=256m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=512m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /exec-fixture:rw,exec,nosuid,nodev,size=2m,uid=1001,gid=1001,mode=0700 \
  --mount "type=bind,src=$PACKAGE,dst=/validation,readonly" \
  --mount "type=bind,src=$INNER,dst=/r9-inner.sh,readonly" \
  --mount "type=bind,src=$TYPEGEN_CLASSIFIER,dst=/r9_typegen_classifier_v1.py,readonly" \
  --mount "type=bind,src=$TYPEGEN_CLASSIFIER_TESTS,dst=/test_r9_typegen_classifier_v1.py,readonly" \
  --mount "type=volume,src=$NODE_VOLUME,dst=/work/candidate/web/node_modules,readonly" \
  --workdir /validation --entrypoint /bin/bash "$IMAGE" -c \
  'exec /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/tmp PYTHONDONTWRITEBYTECODE=1 SCANNER_TEST_EXEC_ROOT=/exec-fixture NEXT_TELEMETRY_DISABLED=1 NO_COLOR=1 TERM=dumb GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null /bin/bash /r9-inner.sh' \
  >"$tmp_out" 2>/dev/null || container_status=$?
docker_run_exit=$container_status

safe_out=''
invalid=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ ^phase=[a-z][a-z0-9-]*\|error_code=[A-Z0-9_]{2,48}$ || \
        "$line" =~ ^exit=[0-9]{1,3}$ || \
        "$line" =~ ^diagnostic=file=web/[A-Za-z0-9_./-]{1,180}\|line=[0-9]{1,6}\|column=[0-9]{1,6}\|code=TS[0-9]{4,5}$ || \
        "$line" =~ ^diagnostic=unclassified_errors=[0-9]{1,6}$ || \
        "$line" =~ ^diagnostic=typescript_output=NO_CLASSIFIED_DIAGNOSTIC$ || \
        "$line" =~ ^diagnostic=next-typegen\|class=(PROJECT_CONTEXT|PERMISSION_DENIED|DEPENDENCY_MISSING|CONFIGURATION_ERROR|UNKNOWN)\|module=(UNCLASSIFIED|[A-Za-z0-9][A-Za-z0-9._~-]{0,99}|@[A-Za-z0-9][A-Za-z0-9._~-]{0,99}/[A-Za-z0-9][A-Za-z0-9._~-]{0,99})$ || \
        "$line" =~ ^diagnostic=suite=(protected-workflow-review\|failed=([0-9]{1,6}|UNKNOWN)|credential-scan\|failed=1|protected-path-guard\|failed=1)$ ]]; then
    safe_out+="$line"$'\n'
  else
    invalid=1
    break
  fi
done <"$tmp_out"
/usr/bin/rm -f -- "$tmp_out"
if (( invalid )); then safe_out=$'phase=r9-output-capture|error_code=OUTPUT_REJECTED\n'; container_status=1; fi
inner_exit_count=0
inner_exit_value=''
while IFS= read -r line; do
  if [[ "$line" =~ ^exit=([0-9]{1,3})$ ]]; then
    inner_exit_count=$((inner_exit_count + 1))
    inner_exit_value="${BASH_REMATCH[1]}"
  fi
done <<< "$safe_out"
if (( container_status == 124 )); then
  safe_out+=$'phase=r9-container|error_code=TIMEOUT\n'
  safe_out+="exit=$container_status"$'\n'
elif (( container_status != 0 )) && [[ "$safe_out" != *$'exit='* ]]; then
  safe_out+=$'phase=r9-container|error_code=CONTAINER_EXIT_NONZERO\n'
  safe_out+="exit=$container_status"$'\n'
fi
if (( container_status == 0 )); then
  expected_success=$'phase=r9-container-preflight|error_code=OK\nphase=r9-candidate-copy|error_code=OK\nphase=r9-npm-dependency-manifest|error_code=OK\nphase=r9-node-and-typescript-versions|error_code=OK\nphase=r9-typegen-classifier-synthetics|error_code=OK\nphase=r9-next-typegen|error_code=OK\nphase=r9-typescript|error_code=OK\nphase=r9-protected-workflow-tests|error_code=OK\nphase=r9-credential-scan|error_code=OK\nphase=r9-protected-path-guard|error_code=OK\nphase=r9-summary|error_code=ALL_PENDING_CHECKS_OK\n'
  if [[ "$safe_out" != "$expected_success" ]]; then
    safe_out=$'phase=r9-output-contract|error_code=SUCCESS_SEQUENCE_MISMATCH\n'
    container_status=1
  fi
fi


actual_container_exit='unavailable'
if container_id="$(/usr/bin/docker --context default inspect --format '{{.Id}}' "$NAME" 2>/dev/null)"; then
  inspect_line="$(/usr/bin/docker --context default inspect --format '{{.Image}}|{{index .Config.Labels "org.studiamatch.h3req1.scope"}}|{{index .Config.Labels "org.studiamatch.h3req1.fixture"}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}' "$container_id" 2>/dev/null)" || inspect_line=''
  if [[ "$inspect_line" == "$EXPECTED_IMAGE|g03-tsc-heap-continuation|$NAME|"* ]]; then
    IFS='|' read -r _ _ _ container_state actual_container_exit oom_state <<< "$inspect_line"
    if [[ "$oom_state" == true ]]; then
      safe_out=$'phase=r9-container|error_code=MEMORY_LIMIT\n'
      container_status=137
    elif (( container_status == 0 )); then
      if [[ "$actual_container_exit" != 0 || "$inner_exit_count" != 0 ]]; then
        safe_out=$'phase=r9-output-contract|error_code=EXIT_MISMATCH\n'
        container_status=1
      fi
    elif (( container_status != 124 )); then
      if [[ "$inner_exit_count" != 1 || "$inner_exit_value" != "$actual_container_exit" || \
            "$container_status" != "$actual_container_exit" ]]; then
        safe_out=$'phase=r9-output-contract|error_code=EXIT_MISMATCH\n'
        container_status=1
      fi
    fi
  else
    safe_out=$'phase=r9-fixture-identity|error_code=IDENTITY_MISMATCH\n'
    container_status=1
  fi
else
  container_id='unavailable'
  [[ "$container_status" != 0 ]] || { safe_out=$'phase=r9-fixture-identity|error_code=CONTAINER_MISSING\n'; container_status=1; }
  if (( inner_exit_count != 0 )); then
    safe_out=$'phase=r9-output-contract|error_code=EXIT_MISMATCH\n'
    container_status=1
  fi
fi

evidence_body="$( {
  printf 'candidate_branch=%s\ncandidate_head=%s\n' "$EXPECTED_BRANCH" "$EXPECTED_HEAD"
  printf 'snapshot=r6|package_sha256=%s|inputs_sha256=%s\n' "$EXPECTED_PACKAGE_SHA" "$EXPECTED_INPUTS_SHA"
  printf 'image_id=%s|memory_limit=4GiB|cpu_limit=2|node_heap=3072MiB|network=none|node_modules_mount=read_only_at_project_path\n' "$image_id"
  printf 'fixture_name=%s|fixture_id=%s|fixture_state=%s|container_exit=%s|docker_run_exit=%s|gate_exit=%s\n' "$NAME" "$container_id" "$container_state" "$actual_container_exit" "$docker_run_exit" "$container_status"
  printf 'phase=g03-candidate-source|error_code=68_INPUTS_MATCH\nphase=g03-actionlint-reuse|error_code=INPUT_HASHES_MATCH\n'
  printf '%s' "$safe_out"
} )" || emit_fail g03-evidence ASSEMBLY_FAILED
printf '%s\n' "$evidence_body" >&3 || emit_fail g03-evidence WRITE_FAILED
printf '%s\n' "$evidence_body"

cleanup_fixture || true
printf 'phase=r9-fixture-cleanup|error_code=%s\n' "$cleanup_code"
final_exit=$container_status
[[ "$cleanup_code" == OK ]] || final_exit=1
if [[ "$cleanup_code" == OK && "$final_exit" == 0 ]]; then
  case "$cleanup_signal" in
    INT) final_exit=130; printf 'phase=g03-cleanup-signal|error_code=DEFERRED_INT\n' >&3; printf 'phase=g03-cleanup-signal|error_code=DEFERRED_INT\n' ;;
    TERM) final_exit=143; printf 'phase=g03-cleanup-signal|error_code=DEFERRED_TERM\n' >&3; printf 'phase=g03-cleanup-signal|error_code=DEFERRED_TERM\n' ;;
    HUP) final_exit=129; printf 'phase=g03-cleanup-signal|error_code=DEFERRED_HUP\n' >&3; printf 'phase=g03-cleanup-signal|error_code=DEFERRED_HUP\n' ;;
  esac
fi
printf 'exit=%s\n' "$final_exit" >&3 || emit_fail g03-evidence FINAL_STATUS_WRITE_FAILED
printf 'exit=%s\n' "$final_exit"
cleanup_done=1
cleanup_armed=0
exit "$final_exit"
