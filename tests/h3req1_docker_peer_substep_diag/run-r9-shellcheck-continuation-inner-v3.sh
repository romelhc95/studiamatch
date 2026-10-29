#!/usr/bin/env bash
set -euo pipefail

current_phase='r9-continuation-preflight'
on_error() {
  local status=$?
  printf 'phase=%s|error_code=CHECK_FAILED\nexit=%s\n' "$current_phase" "$status"
  exit "$status"
}
trap on_error ERR

phase_ok() {
  printf 'phase=%s|error_code=OK\n' "$1"
}

cd /validation
sha256sum -c r4-package.sha256 >/dev/null 2>&1
sha256sum -c inputs.sha256 >/dev/null 2>&1
cd /validation-tools
sha256sum -c tools.sha256 >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-actionlint-reuse'
verify_workflow_hash() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum -- "$path" 2>/dev/null)"
  [[ "${actual%% *}" == "$expected" ]]
}
verify_workflow_hash '276641005c0bc1dc64b26e479b9ef197137a69b3dc4b08be8e56246fdb75df23' \
  /validation/.github/workflows/security-audit.yml
verify_workflow_hash '016551e6a6e280dcd515788ffcf93b18a6d48647079e3c0cd7be9c2d4f58864b' \
  /validation/.github/workflows/protected-workflow-integrity.yml
verify_workflow_hash '3899f29a026861400707827e7e6c9248446d938451232eb5fee157775b39fda8' \
  /validation/.github/workflows/db-sync-to-pro.yml
printf 'phase=%s|error_code=INPUT_HASHES_MATCH\n' "$current_phase"

current_phase='r9-tool-extraction'
mkdir -p /lint-tools /tmp/h3req1-g03-r2
tar -xzf /validation-tools/shellcheck-v0.11.0.linux.x86_64.tar.gz \
  -C /lint-tools shellcheck-v0.11.0/shellcheck >/dev/null 2>&1
mv /lint-tools/shellcheck-v0.11.0/shellcheck /lint-tools/shellcheck
chmod 0755 /lint-tools/shellcheck
export PATH="/lint-tools:$PATH"
phase_ok "$current_phase"

current_phase='r9-shellcheck'
cd /validation
if /lint-tools/shellcheck --format=json1 \
  scripts/security/scan_credentials.sh \
  scripts/security/protected_path_scope_guard.sh \
  tests/test_protected_path_scope_guard.sh \
  scripts/security/h2_web_mock_smoke.sh \
  tests/sql/h3_invitation_reservation_concurrency.sh \
  .githooks/pre-commit .githooks/pre-push > /tmp/shellcheck-output.json 2>/dev/null; then
  shellcheck_status=0
else
  shellcheck_status=$?
fi
if classification_output="$(python3 /shellcheck-classifier.py \
  /tmp/shellcheck-output.json "$shellcheck_status" 2>/dev/null)"; then
  classifier_status=0
else
  classifier_status=$?
fi
if (( classifier_status != 0 )); then
  printf 'phase=r9-shellcheck-diagnostic|error_code=CLASSIFIER_EXECUTION_FAILED\nexit=1\n'
  exit 1
fi
classification="${classification_output%%$'\n'*}"
case "$classification" in
  PASS)
    if (( shellcheck_status != 0 )); then
      printf 'phase=r9-shellcheck-diagnostic|error_code=EXIT_DIAGNOSTIC_MISMATCH\nexit=%s\n' "$shellcheck_status"
      exit "$shellcheck_status"
    fi
    phase_ok "$current_phase"
    ;;
  FINDINGS)
    printf 'phase=r9-shellcheck|error_code=CHECK_FAILED\n'
    printf '%s\n' "${classification_output#*$'\n'}"
    printf 'exit=%s\n' "$shellcheck_status"
    exit "$shellcheck_status"
    ;;
  STDOUT_EMPTY|OUTPUT_INVALID|ROOT_SHAPE_INVALID|PATH_UNCLASSIFIED|DIAGNOSTIC_LIMIT_EXCEEDED|EXIT_DIAGNOSTIC_MISMATCH|TOOL_EXIT_NON_DIAGNOSTIC)
    if (( shellcheck_status == 0 )); then shellcheck_status=1; fi
    printf 'phase=r9-shellcheck-diagnostic|error_code=%s\nexit=%s\n' "$classification" "$shellcheck_status"
    exit "$shellcheck_status"
    ;;
  *)
    printf 'phase=r9-shellcheck-diagnostic|error_code=CLASSIFIER_RESULT_UNKNOWN\nexit=1\n'
    exit 1
    ;;
esac

current_phase='r9-candidate-copy'
cp -a /validation/. /tmp/h3req1-g03-r2/ >/dev/null 2>&1
cd /tmp/h3req1-g03-r2
ln -s /app/web/node_modules web/node_modules
phase_ok "$current_phase"

current_phase='r9-npm-dependency-manifest'
python3 - <<'PYDEPS' >/dev/null 2>&1
import hashlib
from pathlib import Path

manifest = Path('/app/web/node_modules/.studiamatch-node-deps.sha256')
if not manifest.is_file():
    raise SystemExit(1)
lines = manifest.read_text(encoding='utf-8').splitlines()
entries = {}
for line in lines[2:]:
    parts = line.split()
    if len(parts) != 2 or parts[1] not in {'package.json', 'package-lock.json'}:
        raise SystemExit(1)
    entries[parts[1]] = parts[0]
if set(entries) != {'package.json', 'package-lock.json'}:
    raise SystemExit(1)
for name, expected in entries.items():
    actual = hashlib.sha256((Path('/tmp/h3req1-g03-r2/web') / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(1)
PYDEPS
phase_ok "$current_phase"

current_phase='r9-node-and-typescript-versions'
test "$(node --version)" = 'v20.20.2' >/dev/null 2>&1
test "$(node -p "require('./web/node_modules/typescript/package.json').version")" = '5.9.3' >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-next-typegen'
cd /tmp/h3req1-g03-r2/web
./node_modules/.bin/next typegen >/dev/null 2>&1
cd ..
phase_ok "$current_phase"

current_phase='r9-eslint'
cd web
npm run lint >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-typescript'
./node_modules/.bin/tsc --noEmit >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-protected-workflow-tests'
cd ..
python3 -m pytest -q -p no:cacheprovider tests/test_protected_workflow_review.py >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-credential-scan'
bash tests/test_scan_credentials.sh >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-protected-path-guard'
bash tests/test_protected_path_scope_guard.sh >/dev/null 2>&1
phase_ok "$current_phase"

trap - ERR
printf 'phase=r9-continuation-summary|error_code=ALL_REMAINING_CHECKS_OK\n'
