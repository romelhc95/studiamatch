#!/usr/bin/env bash
set -u -o pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly CLASSIFIER='tests/h3req1_docker_peer_substep_diag/f1_read_failure_classification_v5_once.py'
readonly CLASSIFIER_SHA256='2f47ebed1977d360df8aa5905a3a1cf3fa0a813f606e1c3aa583c56d26330c51'
readonly PRIOR_ATTESTATION='.context/evidencia/h3req1_c03_socket_classifier_v3_assertion_reporter_failure_2026-10-09.md'
readonly PRIOR_ATTESTATION_SHA256='8e6360143d15e47c819beb540edd69bd2a08634ac85b9267d03fd61c5c5ac33a'
readonly R9_ROOT='/tmp/h3req1-g03-validation-29d8fff9-r2'
readonly R9_RUNNER='/tmp/h3req1-g03-validation-29d8fff9-r2/run-r9.sh'
readonly R9_RUNNER_SHA256='2a38e3038440d7b6e6a5c77871eae88f2adba03bf44abca79b76175015eedb97'
readonly R9_MANIFEST_SHA256='b2020404af4ae373907cab6bd777fba2bd397d8b5677c874aaa72bc34083d866'
readonly R9_TOOLS_SHA256='4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa'
readonly EXPECTED_DIAGNOSTIC=$'phase=prior-desktop-wsl-endpoint-attestation|error_code=OK\nphase=classifier-synthetic-image-read|error_code=OK\nphase=classifier-synthetic-tests|error_code=OK\nphase=f1-image-read|error_code=OK\nphase=f1-container-read|error_code=OK'

emit_failure() {
  printf 'phase=classifier-v5-r9-preflight|error_code=%s\n' "$1"
  exit 1
}

verify_hash() {
  local file="$1" expected="$2" hash_line
  [[ -f "$file" && ! -L "$file" ]] || return 1
  hash_line="$(/usr/bin/sha256sum -- "$file" 2>/dev/null)" || return 1
  [[ "${hash_line%% *}" == "$expected" ]]
}

is_safe_errno_code() {
  case "$1" in
    EACCES|EAGAIN|EBUSY|ECONNABORTED|ECONNREFUSED|ECONNRESET|EEXIST|EFAULT|EINTR|EINVAL|EIO|EISDIR|EMFILE|EMLINK|ENAMETOOLONG|ENFILE|ENOBUFS|ENODEV|ENOENT|ENOMEM|ENOSPC|ENOSYS|ENOTDIR|ENOTSOCK|ENXIO|EOPNOTSUPP|EPIPE|EPERM|EROFS|ESPIPE|ETIMEDOUT|ETXTBSY|EOTHER)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_allowed_diagnostic_line() {
  local line="$1" phase code
  [[ "$line" =~ ^phase=([a-z][a-z0-9-]{0,47})\|error_code=([A-Z][A-Z0-9_]{0,47})$ ]] || return 1
  phase="${BASH_REMATCH[1]}"
  code="${BASH_REMATCH[2]}"

  case "$phase:$code" in
    prior-desktop-wsl-endpoint-attestation:OK|prior-desktop-wsl-endpoint-attestation:EVIDENCE_MISMATCH|prior-desktop-wsl-endpoint-attestation:ENDPOINT_MISMATCH|\
    wsl-checkout-preflight:ARGUMENTS_REJECTED|wsl-checkout-preflight:LINUX_REQUIRED|wsl-checkout-preflight:WSL_REQUIRED|wsl-checkout-preflight:PREFLIGHT_FAILED|wsl-checkout-preflight:CHECKOUT_MISMATCH|wsl-checkout-preflight:RUN_AS_WSL_USER|wsl-checkout-preflight:CHECKOUT_OWNER_MISMATCH|wsl-checkout-preflight:DOCKER_OVERRIDE_PRESENT|wsl-checkout-preflight:CANDIDATE_MISMATCH|\
    projection-pin-check:PROJECTION_UNAVAILABLE|projection-pin-check:PROJECTION_HASH_MISMATCH|projection-pin-check:PROJECTION_READ_FAILED|projection-pin-check:PROJECTION_LOAD_FAILED|\
    desktop-wsl-context:DOCKER_CONTEXT_UNAVAILABLE|desktop-wsl-context:OUTPUT_LIMIT|desktop-wsl-context:COMMAND_START_FAILED|desktop-wsl-context:ENDPOINT_METADATA_INVALID|desktop-wsl-context:EXPECTED_ENDPOINT_MISMATCH|\
    desktop-wsl-engine:DOCKER_ENGINE_UNAVAILABLE|desktop-wsl-engine:OUTPUT_LIMIT|desktop-wsl-engine:COMMAND_START_FAILED|desktop-wsl-engine:ENGINE_METADATA_INVALID|desktop-wsl-engine:LINUX_ENGINE_REQUIRED|\
    classifier-synthetic-image-read:OK|classifier-synthetic-image-read:SYNTHETIC_IMAGE_UNAVAILABLE|classifier-synthetic-image-read:SYNTHETIC_IMAGE_ID_MISMATCH|classifier-synthetic-image-read:OUTPUT_LIMIT|classifier-synthetic-image-read:COMMAND_START_FAILED|\
    classifier-synthetic-tests:OK|classifier-synthetic-tests:TEST_SOURCE_UNAVAILABLE|classifier-synthetic-tests:TEST_SOURCE_HASH_MISMATCH|classifier-synthetic-tests:SYNTHETIC_CONTAINER_RUN_FAILED|classifier-synthetic-tests:TEST_RESULT_INVALID|classifier-synthetic-tests:MULTIPLE_TEST_CASE_FAILURES|classifier-synthetic-tests:PYTEST_UNAVAILABLE|classifier-synthetic-tests:PYTEST_IMPORT_FAILED|classifier-synthetic-tests:PYTEST_RUNNER_FAILED|classifier-synthetic-tests:V2_TEST_COLLECTION_FAILED|classifier-synthetic-tests:V2_TEST_PHASE_FAILED|classifier-synthetic-tests:V2_TEST_SKIPPED|classifier-synthetic-tests:V2_TEST_RESULT_INCOMPLETE|classifier-synthetic-tests:V2_PARSE_CASE_FAILED|classifier-synthetic-tests:V2_EVALUATION_CASE_FAILED|classifier-synthetic-tests:V2_AMBIGUOUS_CASE_FAILED|classifier-synthetic-tests:V2_MAIN_SANITIZATION_FAILED|classifier-synthetic-tests:V2_FAILURE_CODE_CLASSIFIER_FAILED|classifier-synthetic-tests:V2_TEST_FAILURE_UNCLASSIFIED|classifier-synthetic-tests:V2_MAIN_EXIT_ASSERT_FAILED|classifier-synthetic-tests:V2_MAIN_OUTPUT_ASSERT_FAILED|classifier-synthetic-tests:V2_MAIN_SECRET_ASSERT_FAILED|classifier-synthetic-tests:V5_TEMPLATE_GUARD_ASSERT_FAILED|classifier-synthetic-tests:V5_APPLY_ASSERT_FAILED|classifier-synthetic-tests:V5_LABEL_POLICY_ASSERT_FAILED|classifier-synthetic-tests:V5_TMPFS_POLICY_ASSERT_FAILED|classifier-synthetic-tests:V5_TEST_SOURCE_UNAVAILABLE|classifier-synthetic-tests:V5_TEST_SOURCE_HASH_MISMATCH|\
    classifier-synthetic-test-case:V2_PARSE_CASE_FAILED|classifier-synthetic-test-case:V2_EVALUATION_CASE_FAILED|classifier-synthetic-test-case:V2_AMBIGUOUS_CASE_FAILED|classifier-synthetic-test-case:V2_MAIN_SANITIZATION_FAILED|classifier-synthetic-test-case:V2_FAILURE_CODE_CLASSIFIER_FAILED|classifier-synthetic-test-case:V2_TEST_FAILURE_UNCLASSIFIED|classifier-synthetic-test-case:V2_MAIN_EXIT_ASSERT_FAILED|classifier-synthetic-test-case:V2_MAIN_OUTPUT_ASSERT_FAILED|classifier-synthetic-test-case:V2_MAIN_SECRET_ASSERT_FAILED|classifier-synthetic-test-case:V5_TEMPLATE_GUARD_ASSERT_FAILED|classifier-synthetic-test-case:V5_APPLY_ASSERT_FAILED|classifier-synthetic-test-case:V5_LABEL_POLICY_ASSERT_FAILED|classifier-synthetic-test-case:V5_TMPFS_POLICY_ASSERT_FAILED|\
    f1-image-read:OK|f1-image-read:DOCKER_READ_FAILED|f1-image-read:IMAGE_METADATA_INVALID|f1-image-read:PINNED_IMAGE_VOLUMES|\
    f1-container-read:OK|f1-container-read:OUTPUT_LIMIT|f1-container-read:ERROR_OUTPUT_LIMIT|f1-container-read:COMMAND_START_FAILED|f1-container-read:CONTAINER_NOT_FOUND|f1-container-read:DOCKER_ACCESS_DENIED|f1-container-read:DOCKER_ENGINE_UNAVAILABLE|f1-container-read:INSPECT_TEMPLATE_ERROR|f1-container-read:INSPECT_TEMPLATE_PARSE_ERROR|f1-container-read:INSPECT_TEMPLATE_EVALUATION_ERROR|f1-container-read:DOCKER_READ_FAILED|f1-container-read:CONTAINER_METADATA_INVALID|f1-container-read:F1_POLICY_MISMATCH|\
    f1-classification-v5-preflight:V2_HELPER_UNAVAILABLE|f1-classification-v5-preflight:V2_HELPER_READ_FAILED|f1-classification-v5-preflight:V2_HELPER_HASH_MISMATCH|f1-classification-v5-preflight:V2_HELPER_LOAD_FAILED|f1-classification-v5-preflight:LEGACY_HELPER_UNAVAILABLE|f1-classification-v5-preflight:LEGACY_HELPER_HASH_MISMATCH|f1-classification-v5-preflight:LEGACY_HELPER_LOAD_FAILED|f1-classification-v5-preflight:F1_CLASSIFICATION_FAILED|f1-classification-v5-preflight:LOAD_FAILED|\
    f1-classification-v5:CLASSIFICATION_FAILED|classifier-v5-r9-preflight:RUN_AS_WSL_USER|classifier-v5-r9-preflight:INTERACTIVE_TTY_REQUIRED|classifier-v5-r9-preflight:RUNTIME_UNAVAILABLE|classifier-v5-r9-preflight:CHECKOUT_UNAVAILABLE|classifier-v5-r9-preflight:CHECKOUT_MISMATCH|classifier-v5-r9-preflight:GIT_PREFLIGHT_FAILED|classifier-v5-r9-preflight:CANDIDATE_MISMATCH|classifier-v5-r9-preflight:DOCKER_OVERRIDE_PRESENT|classifier-v5-r9-preflight:CLASSIFIER_HASH_MISMATCH|classifier-v5-r9-preflight:PRIOR_ATTESTATION_HASH_MISMATCH|classifier-v5-r9-preflight:R9_PACKAGE_UNAVAILABLE|classifier-v5-r9-preflight:R9_RUNNER_HASH_MISMATCH|classifier-v5-r9-preflight:R9_MANIFEST_HASH_MISMATCH|classifier-v5-r9-preflight:R9_TOOLS_HASH_MISMATCH|classifier-v5-r9-preflight:DIAGNOSTIC_OUTPUT_INVALID|classifier-v5-r9-preflight:DIAGNOSTIC_FAILURE|classifier-v5-r9-preflight:PACKAGE_HASH_MISMATCH|classifier-v5-r9-preflight:CHECK_FAILED|classifier-v5-r9-preflight:OUTPUT_LIMIT|classifier-v5-r9-preflight:COMMAND_START_FAILED|classifier-v5-r9-preflight:ETIMEDOUT)
      return 0
      ;;
  esac

  case "$phase" in
    wsl-checkout-preflight|projection-pin-check|desktop-wsl-context|desktop-wsl-engine|classifier-synthetic-image-read|classifier-synthetic-tests|f1-image-read|f1-container-read)
      is_safe_errno_code "$code"
      return
      ;;
    *)
      return 1
      ;;
  esac
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

verify_hash "$CLASSIFIER" "$CLASSIFIER_SHA256" || emit_failure 'CLASSIFIER_HASH_MISMATCH'
verify_hash "$PRIOR_ATTESTATION" "$PRIOR_ATTESTATION_SHA256" || emit_failure 'PRIOR_ATTESTATION_HASH_MISMATCH'
[[ -d "$R9_ROOT" && ! -L "$R9_ROOT" && -d "${R9_ROOT}.tools" && ! -L "${R9_ROOT}.tools" ]] || emit_failure 'R9_PACKAGE_UNAVAILABLE'
verify_hash "$R9_RUNNER" "$R9_RUNNER_SHA256" || emit_failure 'R9_RUNNER_HASH_MISMATCH'
verify_hash "$R9_ROOT/r9-package.sha256" "$R9_MANIFEST_SHA256" || emit_failure 'R9_MANIFEST_HASH_MISMATCH'
verify_hash "${R9_ROOT}.tools/tools.sha256" "$R9_TOOLS_SHA256" || emit_failure 'R9_TOOLS_HASH_MISMATCH'

diagnostic_output=''
if diagnostic_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=2s 110s \
  /usr/bin/env -i HOME=/home/romel PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -B "$ROOT/$CLASSIFIER" 2>/dev/null)"; then
  diagnostic_status=0
else
  diagnostic_status=$?
fi

safe_output=''
invalid_output=0
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if is_allowed_diagnostic_line "$line"; then
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

if /usr/bin/timeout --foreground --signal=TERM --kill-after=5s 180s /bin/bash "$R9_RUNNER" >/dev/null 2>&1; then
  printf 'phase=r9|error_code=OK\n'
else
  r9_status=$?
  printf 'phase=r9|error_code=CHECK_FAILED\nexit=%s\n' "$r9_status"
  exit "$r9_status"
fi
