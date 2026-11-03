#!/usr/bin/env bash
set -u -o pipefail
export LANG=C LC_ALL=C

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly PYTHON_RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_output_capture_classifier_v14_once.py"
readonly PYTHON_RUNNER_SHA256='776d56c87101f5f4b632f7dd58fddc3405f591cfcd756343741ce4095a47ce29'
readonly R9_RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-r9-r3-sanitized.sh"
readonly R9_RUNNER_SHA256='bdef0351abfa8697cb13c788b5b3cdbb7a5568672e4c8c9d56b860826364f0a7'
readonly CONTAINER_RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/run-in-container-r9-sanitized.sh"
readonly CONTAINER_RUNNER_SHA256='d384964d84b86b9a0c006bb819a8795950345513396860efc1168b094061fadc'
readonly V10_JIT="$ROOT/.context/operaciones/jit_h3req1_docker_desktop_wsl_f1_image_template_field_isolation_v10_once_2026-10-09.md"
readonly V10_JIT_SHA256='08ced8865cffae2c46319897c98d368f45621dbe6650ff445ab701d55f546d7c'
readonly V10_RESULT="$ROOT/.context/evidencia/h3req1_c03_v10_image_template_field_isolation_result_2026-10-09.md"
readonly V10_RESULT_SHA256='a6bd87303def9c1b4a60f4a1e862deff73e82b20c0855d5050050654bd74da09'
readonly V3_IDENTITY_RESULT="$ROOT/.context/evidencia/h3req1_c03_socket_classifier_v3_assertion_reporter_failure_2026-10-09.md"
readonly V3_IDENTITY_RESULT_SHA256='8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a'
readonly V11_JIT="$ROOT/.context/operaciones/jit_h3req1_docker_desktop_wsl_f1_v10_gated_read_and_r9_once_2026-10-09.md"
readonly V11_JIT_SHA256='7775d8df1a71fe00f27e78e6a4e73599eab0a62bc064b438932adfb2dcd660b7'
readonly V11_RESULT="$ROOT/.context/evidencia/h3req1_c03_v11_combined_template_failure_2026-10-09.md"
readonly V11_RESULT_SHA256='971d9f770650411c963adba6270ae70891f332e3b6477663034a732e62156d29'
readonly V12_JIT="$ROOT/.context/operaciones/jit_h3req1_docker_desktop_wsl_f1_v12_template_variant_and_r9_once_2026-10-09.md"
readonly V12_JIT_SHA256='b06bd50b6bea6c63d0fcec63ffef6fc47527f506e13ca840777bfa652bce16cf'
readonly V12_RESULT="$ROOT/.context/evidencia/h3req1_c03_v12_synthetic_image_label_map_failure_2026-10-09.md"
readonly V12_RESULT_SHA256='790dba22c034a79a4620a8303b3de23ddffc6c9b88b19adf8d79efb79f992c46'
readonly V13_JIT="$ROOT/.context/operaciones/jit_h3req1_docker_desktop_wsl_f1_v13_label_classifier_then_r9_once_2026-10-09.md"
readonly V13_JIT_SHA256='5019c8cd6aab75d18d3f4e369744470fee16ad91398855f6d3c18c781250aa25'
readonly V13_RESULT="$ROOT/.context/evidencia/h3req1_c03_v13_output_rejected_2026-10-09.md"
readonly V13_RESULT_SHA256='d46d2774af0ca2f70f44445a183e8f073de2446bcb6bdab0d74ad2f17acada64'
readonly R9_PACKAGE='/tmp/h3req1-g03-validation-29d8fff9-r3'
readonly R9_PACKAGE_MANIFEST_SHA256='688e81efaae70a841a64cd4c0a074ae3c76c355f5ef9bc77756cff9ad607fc02'
readonly R9_INPUTS_SHA256='6b3f3d856f906cb247b792a8d89d29f4abc0422c990fa473222b9dbe89097aee'
readonly R9_TOOLS='/tmp/h3req1-g03-validation-29d8fff9-r2.tools'
readonly R9_TOOLS_MANIFEST_SHA256='4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa'
readonly MAX_OUTPUT_BYTES=4096
readonly MAX_DIAGNOSTIC_OUTPUT_BYTES=8192

pause_for_copy() {
  if [[ -t 0 ]]; then
    IFS= read -r -p 'Copia solo phase/error_code y exit; presiona Enter para cerrar: ' _ || true
  fi
}
trap pause_for_copy EXIT

fail() {
  printf 'phase=%s|error_code=%s\n' "$1" "$2"
  exit "${3:-1}"
}

verify_hash() {
  local file="$1" expected="$2" hash_line
  [[ -f "$file" && ! -L "$file" ]] || return 1
  hash_line="$(/usr/bin/sha256sum -- "$file" 2>/dev/null)" || return 1
  [[ "${hash_line%% *}" == "$expected" ]]
}

(( EUID != 0 )) || fail 'jit-preflight' 'RUN_AS_WSL_USER'
[[ -t 0 ]] || fail 'jit-preflight' 'INTERACTIVE_TTY_REQUIRED'
[[ -x /usr/bin/sha256sum && -x /usr/bin/timeout && -x /usr/bin/git && -x /usr/bin/python3 ]] || fail 'jit-preflight' 'RUNTIME_UNAVAILABLE'
[[ -d "$ROOT" && ! -L "$ROOT" ]] || fail 'jit-preflight' 'CHECKOUT_UNAVAILABLE'
cd -- "$ROOT" || fail 'jit-preflight' 'CHECKOUT_UNAVAILABLE'
[[ "$(pwd -P 2>/dev/null)" == "$ROOT" ]] || fail 'jit-preflight' 'CHECKOUT_MISMATCH'

git_root="$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse --show-toplevel 2>/dev/null)" || fail 'jit-preflight' 'GIT_PREFLIGHT_FAILED'
branch="$(/usr/bin/git -c "safe.directory=$ROOT" branch --show-current 2>/dev/null)" || fail 'jit-preflight' 'GIT_PREFLIGHT_FAILED'
head="$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse HEAD 2>/dev/null)" || fail 'jit-preflight' 'GIT_PREFLIGHT_FAILED'
[[ "$git_root" == "$ROOT" && "$branch" == "$BRANCH" && "$head" == "$HEAD" ]] || fail 'jit-preflight' 'CANDIDATE_MISMATCH'

if [[ -v DOCKER_HOST || -v DOCKER_CONTEXT || -v DOCKER_TLS_VERIFY || -v DOCKER_CERT_PATH ]]; then
  fail 'jit-preflight' 'DOCKER_OVERRIDE_PRESENT'
fi

verify_hash "$PYTHON_RUNNER" "$PYTHON_RUNNER_SHA256" || fail 'jit-preflight' 'PYTHON_RUNNER_HASH_MISMATCH'
verify_hash "$R9_RUNNER" "$R9_RUNNER_SHA256" || fail 'jit-preflight' 'R9_RUNNER_HASH_MISMATCH'
verify_hash "$CONTAINER_RUNNER" "$CONTAINER_RUNNER_SHA256" || fail 'jit-preflight' 'CONTAINER_RUNNER_HASH_MISMATCH'
verify_hash "$V10_JIT" "$V10_JIT_SHA256" || fail 'jit-preflight' 'V10_JIT_HASH_MISMATCH'
verify_hash "$V10_RESULT" "$V10_RESULT_SHA256" || fail 'jit-preflight' 'V10_RESULT_HASH_MISMATCH'
verify_hash "$V3_IDENTITY_RESULT" "$V3_IDENTITY_RESULT_SHA256" || fail 'jit-preflight' 'IDENTITY_RESULT_HASH_MISMATCH'
verify_hash "$V11_JIT" "$V11_JIT_SHA256" || fail 'jit-preflight' 'V11_JIT_HASH_MISMATCH'
verify_hash "$V11_RESULT" "$V11_RESULT_SHA256" || fail 'jit-preflight' 'V11_RESULT_HASH_MISMATCH'
verify_hash "$V12_JIT" "$V12_JIT_SHA256" || fail 'jit-preflight' 'V12_JIT_HASH_MISMATCH'
verify_hash "$V12_RESULT" "$V12_RESULT_SHA256" || fail 'jit-preflight' 'V12_RESULT_HASH_MISMATCH'
verify_hash "$V13_JIT" "$V13_JIT_SHA256" || fail 'jit-preflight' 'V13_JIT_HASH_MISMATCH'
verify_hash "$V13_RESULT" "$V13_RESULT_SHA256" || fail 'jit-preflight' 'V13_RESULT_HASH_MISMATCH'

[[ -d "$R9_PACKAGE" && ! -L "$R9_PACKAGE" && -d "$R9_TOOLS" && ! -L "$R9_TOOLS" ]] || fail 'r9-preflight' 'PACKAGE_UNAVAILABLE'
verify_hash "$R9_PACKAGE/r3-package.sha256" "$R9_PACKAGE_MANIFEST_SHA256" || fail 'r9-preflight' 'PACKAGE_HASH_MISMATCH'
verify_hash "$R9_PACKAGE/inputs.sha256" "$R9_INPUTS_SHA256" || fail 'r9-preflight' 'INPUT_MANIFEST_MISMATCH'
verify_hash "$R9_TOOLS/tools.sha256" "$R9_TOOLS_MANIFEST_SHA256" || fail 'r9-preflight' 'TOOLS_MANIFEST_MISMATCH'
(cd "$R9_PACKAGE" && /usr/bin/sha256sum -c r3-package.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'PACKAGE_HASH_MISMATCH'
(cd "$R9_PACKAGE" && /usr/bin/sha256sum -c inputs.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'INPUT_MANIFEST_MISMATCH'
(cd "$R9_TOOLS" && /usr/bin/sha256sum -c tools.sha256 >/dev/null 2>&1) || fail 'r9-preflight' 'TOOLS_MANIFEST_MISMATCH'

candidate_inputs=0
package_only_inputs=0
input_mismatch=0
while read -r expected relative; do
  path="${relative#./}"
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
  [[ "${current_hash%% *}" == "$expected" ]] || input_mismatch=$((input_mismatch + 1))
done < "$R9_PACKAGE/inputs.sha256"
[[ "$candidate_inputs" == 68 && "$package_only_inputs" == 3 && "$input_mismatch" == 0 ]] || fail 'r9-preflight' 'CANDIDATE_INPUT_DRIFT'

if diagnostic_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 360s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B "$PYTHON_RUNNER" 2>/dev/null)"; then
  diagnostic_status=0
else
  diagnostic_status=$?
fi

(( ${#diagnostic_output} <= MAX_DIAGNOSTIC_OUTPUT_BYTES )) || fail 'f1-v14-output-capture' 'OUTPUT_LIMIT'
safe_diagnostic=''
invalid_diagnostic=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ ^phase=[a-z][a-z0-9-]{0,47}\|error_code=[A-Z][A-Z0-9_]{0,47}$ ]]; then
    safe_diagnostic+="${line}"$'\n'
  else
    invalid_diagnostic=1
    break
  fi
done <<< "$diagnostic_output"
if (( invalid_diagnostic != 0 )); then
  [[ -n "$safe_diagnostic" ]] && printf '%s' "$safe_diagnostic"
  fail 'f1-v14-output-capture' 'OUTPUT_REJECTED'
fi

expected_diagnostic=$'phase=prior-v13-output-capture|error_code=OK\nphase=prior-v12-failure|error_code=OK\nphase=classifier-v13-null|error_code=OK\nphase=classifier-v13-empty-object|error_code=OK\nphase=classifier-v13-unrelated-label|error_code=OK\nphase=classifier-v13-target-label-1|error_code=OK\nphase=classifier-v13-target-label-2|error_code=OK\nphase=classifier-v13-target-label-3|error_code=OK\nphase=classifier-v13-malformed-json|error_code=OK\nphase=prior-v11-failure|error_code=OK\nphase=prior-v10-evidence|error_code=OK\nphase=prior-endpoint-attestation|error_code=OK\nphase=prior-v13-container-audit|error_code=OK\nphase=f1-template-synthetic-label-map|error_code=OK\nphase=f1-template-present-inspect|error_code=OK\nphase=f1-template-absent-inspect|error_code=OK\nphase=f1-template-synthetic-check|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK\n'
if (( diagnostic_status != 0 )) || [[ "$safe_diagnostic" != "$expected_diagnostic" ]]; then
  [[ -n "$safe_diagnostic" ]] && printf '%s' "$safe_diagnostic"
  if (( diagnostic_status == 0 )); then
    diagnostic_status=1
  fi
  printf 'exit=%s\n' "$diagnostic_status"
  exit "$diagnostic_status"
fi
printf '%s' "$safe_diagnostic"

if r9_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 240s /bin/bash "$R9_RUNNER" 2>/dev/null)"; then
  r9_status=0
else
  r9_status=$?
fi
(( ${#r9_output} <= MAX_OUTPUT_BYTES )) || fail 'r9-output' 'OUTPUT_REJECTED'

safe_r9=''
invalid_r9=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ ^phase=r9-[a-z0-9-]{1,48}\|error_code=(OK|CHECK_FAILED|ALL_CHECKS_OK|OUTPUT_REJECTED|OUTPUT_MISMATCH|PACKAGE_UNAVAILABLE|PACKAGE_MODE_MISMATCH|PACKAGE_HASH_MISMATCH|INPUT_MANIFEST_MISMATCH|TOOLS_MANIFEST_MISMATCH|ENDPOINT_MISMATCH|CANDIDATE_INPUT_DRIFT)$ ]] || [[ "$line" =~ ^exit=[0-9]{1,3}$ ]]; then
    safe_r9+="${line}"$'\n'
  else
    invalid_r9=1
    break
  fi
done <<< "$r9_output"
(( invalid_r9 == 0 )) || fail 'r9-output' 'OUTPUT_REJECTED'

expected_r9=$'phase=r9-context|error_code=OK\nphase=r9-input-hashes|error_code=OK\nphase=r9-tool-hashes|error_code=OK\nphase=r9-tool-extraction|error_code=OK\nphase=r9-tool-versions|error_code=OK\nphase=r9-candidate-copy|error_code=OK\nphase=r9-npm-dependency-manifest|error_code=OK\nphase=r9-node-and-typescript-versions|error_code=OK\nphase=r9-actionlint|error_code=OK\nphase=r9-shellcheck|error_code=OK\nphase=r9-eslint|error_code=OK\nphase=r9-typescript|error_code=OK\nphase=r9-protected-workflow-tests|error_code=OK\nphase=r9-credential-scan|error_code=OK\nphase=r9-protected-path-guard|error_code=OK\nphase=r9-summary|error_code=ALL_CHECKS_OK\n'
if (( r9_status != 0 )) || [[ "$safe_r9" != "$expected_r9" ]]; then
  [[ -n "$safe_r9" ]] && printf '%s' "$safe_r9"
  if [[ "$safe_r9" != *$'exit='* ]]; then
    if (( r9_status == 0 )); then
      r9_status=1
    fi
    printf 'exit=%s\n' "$r9_status"
  elif (( r9_status == 0 )); then
    r9_status=1
  fi
  exit "$r9_status"
fi
printf '%s' "$safe_r9"
