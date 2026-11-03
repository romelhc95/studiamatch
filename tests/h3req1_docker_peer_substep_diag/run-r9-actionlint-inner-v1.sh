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

current_phase='r9-tool-extraction'
mkdir -p /lint-tools /tmp/h3req1-g03-r2
tar -xzf /validation-tools/actionlint_1.7.7_linux_amd64.tar.gz -C /lint-tools actionlint >/dev/null 2>&1
tar -xzf /validation-tools/shellcheck-v0.11.0.linux.x86_64.tar.gz -C /lint-tools shellcheck-v0.11.0/shellcheck >/dev/null 2>&1
mv /lint-tools/shellcheck-v0.11.0/shellcheck /lint-tools/shellcheck
chmod 0755 /lint-tools/actionlint /lint-tools/shellcheck
export PATH="/lint-tools:$PATH"
phase_ok "$current_phase"

current_phase='r9-candidate-copy'
cp -a /validation/. /tmp/h3req1-g03-r2/ >/dev/null 2>&1
cd /tmp/h3req1-g03-r2
ln -s /app/web/node_modules web/node_modules
phase_ok "$current_phase"

current_phase='r9-actionlint-classifier'
python3 - <<'PYCLASS' >/dev/null 2>&1
import re

allowed = {
    '.github/workflows/security-audit.yml',
    '.github/workflows/protected-workflow-integrity.yml',
    '.github/workflows/db-sync-to-pro.yml',
}
pattern = re.compile(
    r'^(?:.*/)?(?P<path>\.github/workflows/(?:security-audit|protected-workflow-integrity|db-sync-to-pro)\.yml)'
    r':(?P<line>[1-9][0-9]*):(?P<column>[1-9][0-9]*): .+?(?: \[(?P<rule>[a-z0-9_-]+)\])?$'
)

def classify(lines):
    result = []
    for line in lines:
        match = pattern.fullmatch(line)
        if not match or match.group('path') not in allowed:
            return None
        name = match.group('path').rsplit('/', 1)[-1]
        rule = match.group('rule') or 'unknown'
        result.append(
            f"diagnostic=workflow={name}|line={match.group('line')}|"
            f"column={match.group('column')}|rule={rule}"
        )
    if len(result) > 20:
        return 'LIMIT'
    return result

sample = '.github/workflows/security-audit.yml:7:2: synthetic error [expression]'
assert classify([sample]) == [
    'diagnostic=workflow=security-audit.yml|line=7|column=2|rule=expression'
]
assert classify(['.github/workflows/unlisted.yml:7:2: synthetic [syntax-check]']) is None
assert classify(['.github/workflows/security-audit.yml:0:2: synthetic [syntax-check]']) is None
assert classify([]) == []
assert classify([sample] * 21) == 'LIMIT'
PYCLASS
phase_ok "$current_phase"

current_phase='r9-actionlint'
actionlint_log='/tmp/actionlint-diagnostics.log'
if /lint-tools/actionlint -oneline \
  .github/workflows/security-audit.yml \
  .github/workflows/protected-workflow-integrity.yml \
  .github/workflows/db-sync-to-pro.yml >"$actionlint_log" 2>&1; then
  actionlint_status=0
else
  actionlint_status=$?
fi
actionlint_classification="$(python3 - "$actionlint_log" "$actionlint_status" <<'PYDIAG'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
status = int(sys.argv[2])
allowed = {
    '.github/workflows/security-audit.yml',
    '.github/workflows/protected-workflow-integrity.yml',
    '.github/workflows/db-sync-to-pro.yml',
}
pattern = re.compile(
    r'^(?:.*/)?(?P<path>\.github/workflows/(?:security-audit|protected-workflow-integrity|db-sync-to-pro)\.yml)'
    r':(?P<line>[1-9][0-9]*):(?P<column>[1-9][0-9]*): .+?(?: \[(?P<rule>[a-z0-9_-]+)\])?$'
)
if path.stat().st_size > 16384:
    print('LIMIT')
    raise SystemExit(0)
raw = path.read_text(encoding='utf-8', errors='strict').splitlines()
if not raw:
    print('PASS' if status == 0 else 'EMPTY')
    raise SystemExit(0)
items = []
for line in raw:
    match = pattern.fullmatch(line)
    if not match or match.group('path') not in allowed:
        print('UNCLASSIFIED')
        raise SystemExit(0)
    name = match.group('path').rsplit('/', 1)[-1]
    rule = match.group('rule') or 'unknown'
    items.append(
        f"diagnostic=workflow={name}|line={match.group('line')}|"
        f"column={match.group('column')}|rule={rule}"
    )
if len(items) > 20:
    print('LIMIT')
elif status == 0:
    print('EXIT_DIAGNOSTIC_MISMATCH')
else:
    print('FAIL')
    print('\n'.join(items))
PYDIAG
)"
case "${actionlint_classification%%$'\n'*}" in
  PASS)
    [[ "$actionlint_status" == 0 ]] || {
      printf 'phase=r9-actionlint-diagnostic|error_code=EXIT_DIAGNOSTIC_MISMATCH\nexit=%s\n' "$actionlint_status"
      exit "$actionlint_status"
    }
    phase_ok "$current_phase"
    ;;
  FAIL)
    printf 'phase=r9-actionlint|error_code=CHECK_FAILED\n'
    printf '%s\n' "${actionlint_classification#*$'\n'}"
    printf 'exit=%s\n' "$actionlint_status"
    exit "$actionlint_status"
    ;;
  LIMIT)
    if (( actionlint_status == 0 )); then actionlint_status=1; fi
    printf 'phase=r9-actionlint-diagnostic|error_code=DIAGNOSTIC_LIMIT_EXCEEDED\nexit=%s\n' "$actionlint_status"
    exit "$actionlint_status"
    ;;
  EMPTY|UNCLASSIFIED|EXIT_DIAGNOSTIC_MISMATCH|*)
    if (( actionlint_status == 0 )); then actionlint_status=1; fi
    printf 'phase=r9-actionlint-diagnostic|error_code=OUTPUT_UNCLASSIFIED\nexit=%s\n' "$actionlint_status"
    exit "$actionlint_status"
    ;;
esac

current_phase='r9-shellcheck'
/lint-tools/shellcheck scripts/security/scan_credentials.sh scripts/security/protected_path_scope_guard.sh tests/test_protected_path_scope_guard.sh scripts/security/h2_web_mock_smoke.sh tests/sql/h3_invitation_reservation_concurrency.sh .githooks/pre-commit .githooks/pre-push >/dev/null 2>&1
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
