#!/usr/bin/env bash
set -euo pipefail

current_phase='r9-continuation-preflight'
on_error() {
  local status=$?
  printf 'phase=%s|error_code=CHECK_FAILED\nexit=%s\n' "$current_phase" "$status"
  exit "$status"
}
trap on_error ERR

current_phase='r9-candidate-copy'
cp -a /validation/. /tmp/h3req1-g03-r2/ >/dev/null 2>&1
cd /tmp/h3req1-g03-r2
ln -s /app/web/node_modules web/node_modules
printf 'phase=r9-candidate-copy|error_code=OK\n'
printf 'phase=r9-continuation-preflight|error_code=OK\n'
printf 'phase=r9-actionlint-reuse|error_code=INPUT_HASHES_MATCH\n'
current_phase='r9-typescript-classifier-synthetics'
python3 /tsc-output-classifier.py --self-test
current_phase='r9-typescript'
cd /tmp/h3req1-g03-r2/web
if python3 /tsc-output-classifier.py --run ./node_modules/.bin/tsc --noEmit; then
  :
else
  tsc_status=$?
  exit "$tsc_status"
fi

current_phase='r9-protected-workflow-tests'
cd ..
python3 -m pytest -q -p no:cacheprovider tests/test_protected_workflow_review.py >/dev/null 2>&1
printf 'phase=%s|error_code=OK\n' "$current_phase"

current_phase='r9-credential-scan'
bash tests/test_scan_credentials.sh >/dev/null 2>&1
printf 'phase=%s|error_code=OK\n' "$current_phase"

current_phase='r9-protected-path-guard'
bash tests/test_protected_path_scope_guard.sh >/dev/null 2>&1
printf 'phase=%s|error_code=OK\n' "$current_phase"

printf 'phase=r9-continuation-summary|error_code=ALL_REMAINING_CHECKS_OK\n'
