#!/usr/bin/env bash
set -u -o pipefail
export LANG=C LC_ALL=C

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly PYTHON_RUNNER="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_template_minimal_failure_v15_once.py"
readonly PYTHON_RUNNER_SHA256='05947152fcfb356c1ea8bc0a283eda3c3aad0c94f31e9844083fac2678a0f764'
readonly OUTPUT_CONTRACT="$ROOT/tests/h3req1_docker_peer_substep_diag/f1_v15_output_contract_v3.py"
readonly OUTPUT_CONTRACT_SHA256='5b0f6d83c671816ad7cb891d4a78d3b4fe48f7640a3a9f6c2926fefbd41c7597'
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
readonly V14_JIT="$ROOT/.context/operaciones/jit_h3req1_docker_desktop_wsl_f1_v14_output_capture_then_r9_once_2026-10-09.md"
readonly V14_JIT_SHA256='60ba16f2b29919ef89869625360416cb87470a7e4ad374f7c1d4b763d9686f48'
readonly V14_RESULT="$ROOT/.context/evidencia/h3req1_c03_v14_template_field_interaction_failure_2026-10-09.md"
readonly V14_RESULT_SHA256='abf6be735583098f5a196b6d5284438aefcb8329adbd9601a73a6ed728c80940'
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
verify_hash "$OUTPUT_CONTRACT" "$OUTPUT_CONTRACT_SHA256" || fail 'jit-preflight' 'OUTPUT_CONTRACT_HASH_MISMATCH'
verify_hash "$V10_JIT" "$V10_JIT_SHA256" || fail 'jit-preflight' 'V10_JIT_HASH_MISMATCH'
verify_hash "$V10_RESULT" "$V10_RESULT_SHA256" || fail 'jit-preflight' 'V10_RESULT_HASH_MISMATCH'
verify_hash "$V3_IDENTITY_RESULT" "$V3_IDENTITY_RESULT_SHA256" || fail 'jit-preflight' 'IDENTITY_RESULT_HASH_MISMATCH'
verify_hash "$V11_JIT" "$V11_JIT_SHA256" || fail 'jit-preflight' 'V11_JIT_HASH_MISMATCH'
verify_hash "$V11_RESULT" "$V11_RESULT_SHA256" || fail 'jit-preflight' 'V11_RESULT_HASH_MISMATCH'
verify_hash "$V12_JIT" "$V12_JIT_SHA256" || fail 'jit-preflight' 'V12_JIT_HASH_MISMATCH'
verify_hash "$V12_RESULT" "$V12_RESULT_SHA256" || fail 'jit-preflight' 'V12_RESULT_HASH_MISMATCH'
verify_hash "$V13_JIT" "$V13_JIT_SHA256" || fail 'jit-preflight' 'V13_JIT_HASH_MISMATCH'
verify_hash "$V13_RESULT" "$V13_RESULT_SHA256" || fail 'jit-preflight' 'V13_RESULT_HASH_MISMATCH'
verify_hash "$V14_JIT" "$V14_JIT_SHA256" || fail 'jit-preflight' 'V14_JIT_HASH_MISMATCH'
verify_hash "$V14_RESULT" "$V14_RESULT_SHA256" || fail 'jit-preflight' 'V14_RESULT_HASH_MISMATCH'

if diagnostic_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=3s 600s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B "$PYTHON_RUNNER" 2>/dev/null)"; then
  diagnostic_status=0
else
  diagnostic_status=$?
fi

(( ${#diagnostic_output} <= MAX_DIAGNOSTIC_OUTPUT_BYTES )) || fail 'f1-v15-output-capture' 'OUTPUT_LIMIT'
if parsed_output="$(printf '%s' "$diagnostic_output" | /usr/bin/env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -B "$OUTPUT_CONTRACT" --runner-status "$diagnostic_status" 2>/dev/null)"; then
  :
else
  [[ -n "$parsed_output" ]] && printf '%s\n' "$parsed_output"
  exit 1
fi
printf '%s\n' "$parsed_output"
printf 'phase=f1-v15-summary|error_code=MINIMAL_SET_FOUND\n'
printf 'exit=0\n'
exit 0
