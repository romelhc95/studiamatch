#!/usr/bin/env bash
set -euo pipefail

current_phase='shellcheck-diagnostic-preflight'
on_error() {
  local status=$?
  printf 'phase=%s|error_code=CHECK_FAILED\nexit=%s\n' "$current_phase" "$status"
  exit "$status"
}
trap on_error ERR

cd /validation
sha256sum -c r4-package.sha256 >/dev/null 2>&1
sha256sum -c inputs.sha256 >/dev/null 2>&1
cd /validation-tools
sha256sum -c tools.sha256 >/dev/null 2>&1
phase_ok() { printf 'phase=%s|error_code=OK\n' "$1"; }
phase_ok "$current_phase"

current_phase='shellcheck-diagnostic-tool-extraction'
mkdir -p /lint-tools /tmp/h3req1-shellcheck/candidate
tar -xzf /validation-tools/shellcheck-v0.11.0.linux.x86_64.tar.gz \
  -C /lint-tools shellcheck-v0.11.0/shellcheck >/dev/null 2>&1
mv /lint-tools/shellcheck-v0.11.0/shellcheck /lint-tools/shellcheck
chmod 0755 /lint-tools/shellcheck
phase_ok "$current_phase"

current_phase='shellcheck-diagnostic-synthetics'
if synthetic_output="$(python3 /shellcheck-classifier.py --self-test 2>/dev/null)"; then
  [[ "$synthetic_output" == 'synthetic-count=34' ]]
else
  false
fi
phase_ok "$current_phase"

current_phase='shellcheck-diagnostic'
cp -a /validation/. /tmp/h3req1-shellcheck/candidate/ >/dev/null 2>&1
cd /tmp/h3req1-shellcheck/candidate
if /lint-tools/shellcheck --format=json1 \
  scripts/security/scan_credentials.sh \
  scripts/security/protected_path_scope_guard.sh \
  tests/test_protected_path_scope_guard.sh \
  scripts/security/h2_web_mock_smoke.sh \
  tests/sql/h3_invitation_reservation_concurrency.sh \
  .githooks/pre-commit \
  .githooks/pre-push > /tmp/h3req1-shellcheck/output.json 2>/dev/null; then
  shellcheck_status=0
else
  shellcheck_status=$?
fi
set +e
classification_output="$(python3 /shellcheck-classifier.py \
  /tmp/h3req1-shellcheck/output.json "$shellcheck_status" 2>/dev/null)"
classifier_status=$?
set -e
if (( classifier_status != 0 )); then
  printf 'phase=shellcheck-diagnostic|error_code=CLASSIFIER_EXECUTION_FAILED\nexit=1\n'
  exit 1
fi
classification="${classification_output%%$'\n'*}"
case "$classification" in
  PASS)
    if (( shellcheck_status != 0 )); then
      printf 'phase=shellcheck-diagnostic|error_code=EXIT_DIAGNOSTIC_MISMATCH\nexit=%s\n' "$shellcheck_status"
      exit "$shellcheck_status"
    fi
    phase_ok "$current_phase"
    printf 'exit=0\n'
    ;;
  FINDINGS)
    printf 'phase=shellcheck-diagnostic|error_code=CHECK_FAILED\n'
    printf '%s\n' "${classification_output#*$'\n'}"
    printf 'exit=%s\n' "$shellcheck_status"
    exit "$shellcheck_status"
    ;;
  STDOUT_EMPTY|OUTPUT_INVALID|ROOT_SHAPE_INVALID|PATH_UNCLASSIFIED|DIAGNOSTIC_LIMIT_EXCEEDED|EXIT_DIAGNOSTIC_MISMATCH|TOOL_EXIT_NON_DIAGNOSTIC)
    if (( shellcheck_status == 0 )); then shellcheck_status=1; fi
    printf 'phase=shellcheck-diagnostic|error_code=%s\nexit=%s\n' "$classification" "$shellcheck_status"
    exit "$shellcheck_status"
    ;;
  *)
    printf 'phase=shellcheck-diagnostic|error_code=CLASSIFIER_RESULT_UNKNOWN\nexit=1\n'
    exit 1
    ;;
esac
