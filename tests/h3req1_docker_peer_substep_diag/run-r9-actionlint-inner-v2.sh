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

allowed_paths = {
    '.github/workflows/security-audit.yml',
    '.github/workflows/protected-workflow-integrity.yml',
    '.github/workflows/db-sync-to-pro.yml',
}
pattern = re.compile(
    r'^(?:.*?)(?P<path>\.github/workflows/'
    r'(?:security-audit|protected-workflow-integrity|db-sync-to-pro)\.yml)'
    r':(?P<line>[0-9]{1,6}):(?P<column>[0-9]{1,6}):[ \t]+.*?'
    r'(?:[ \t]+\[(?P<rule>[^\r\n]{1,80})\])?$'
)

def classify(text, status):
    lines = [line for line in text.splitlines() if line]
    if not lines:
        return ('PASS' if status == 0 else 'NO_DIAGNOSTIC_TEXT', [])
    if len(lines) > 20:
        return ('DIAGNOSTIC_LIMIT_EXCEEDED', [])
    result = []
    for line in lines:
        match = pattern.fullmatch(line)
        if not match or match.group('path') not in allowed_paths:
            return ('OUTPUT_UNCLASSIFIED', [])
        rule = match.group('rule')
        if not rule or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', rule):
            rule = 'unknown'
        else:
            rule = rule.lower()
        filename = match.group('path').rsplit('/', 1)[-1]
        result.append(
            f"diagnostic=workflow={filename}|line={match.group('line')}|"
            f"column={match.group('column')}|rule={rule}"
        )
    if status == 0:
        return ('EXIT_DIAGNOSTIC_MISMATCH', [])
    return ('OUTPUT_CLASSIFIED', result)

relative = '.github/workflows/security-audit.yml:7:2: synthetic message [expression]'
assert classify(relative, 1) == ('OUTPUT_CLASSIFIED', [
    'diagnostic=workflow=security-audit.yml|line=7|column=2|rule=expression'
])
absolute = '/tmp/candidate/.github/workflows/protected-workflow-integrity.yml:0:0: synthetic [Rule_v2]'
assert classify(absolute, 1) == ('OUTPUT_CLASSIFIED', [
    'diagnostic=workflow=protected-workflow-integrity.yml|line=0|column=0|rule=rule_v2'
])
prefixed = 'actionlint: /tmp/checkout/.github/workflows/security-audit.yml:12:3: synthetic [rule.v2]'
assert classify(prefixed, 1) == ('OUTPUT_CLASSIFIED', [
    'diagnostic=workflow=security-audit.yml|line=12|column=3|rule=unknown'
])
no_rule = '.github/workflows/db-sync-to-pro.yml:42:4: synthetic message'
assert classify(no_rule, 1) == ('OUTPUT_CLASSIFIED', [
    'diagnostic=workflow=db-sync-to-pro.yml|line=42|column=4|rule=unknown'
])
assert classify('.github/workflows/unlisted.yml:7:2: synthetic [syntax-check]', 1) == ('OUTPUT_UNCLASSIFIED', [])
assert classify('', 1) == ('NO_DIAGNOSTIC_TEXT', [])
assert classify('\n'.join([relative] * 21), 1) == ('DIAGNOSTIC_LIMIT_EXCEEDED', [])
assert classify(relative, 0) == ('EXIT_DIAGNOSTIC_MISMATCH', [])
kind, diagnostics = classify(relative, 1)
assert kind == 'OUTPUT_CLASSIFIED' and 'synthetic message' not in '\n'.join(diagnostics)
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
set +e
classification_output="$(python3 - "$actionlint_log" "$actionlint_status" <<'PYDIAG'
import re
import sys
from pathlib import Path

allowed_paths = {
    '.github/workflows/security-audit.yml',
    '.github/workflows/protected-workflow-integrity.yml',
    '.github/workflows/db-sync-to-pro.yml',
}
pattern = re.compile(
    r'^(?:.*?)(?P<path>\.github/workflows/'
    r'(?:security-audit|protected-workflow-integrity|db-sync-to-pro)\.yml)'
    r':(?P<line>[0-9]{1,6}):(?P<column>[0-9]{1,6}):[ \t]+.*?'
    r'(?:[ \t]+\[(?P<rule>[^\r\n]{1,80})\])?$'
)
path = Path(sys.argv[1])
status = int(sys.argv[2])
if path.stat().st_size > 16384:
    print('DIAGNOSTIC_LIMIT_EXCEEDED')
    raise SystemExit(0)
raw = path.read_text(encoding='utf-8', errors='strict')
lines = [line for line in raw.splitlines() if line]
if not lines:
    print('PASS' if status == 0 else 'NO_DIAGNOSTIC_TEXT')
    raise SystemExit(0)
if len(lines) > 20:
    print('DIAGNOSTIC_LIMIT_EXCEEDED')
    raise SystemExit(0)
items = []
for line in lines:
    match = pattern.fullmatch(line)
    if not match or match.group('path') not in allowed_paths:
        print('OUTPUT_UNCLASSIFIED')
        raise SystemExit(0)
    rule = match.group('rule')
    if not rule or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', rule):
        rule = 'unknown'
    else:
        rule = rule.lower()
    filename = match.group('path').rsplit('/', 1)[-1]
    items.append(
        f"diagnostic=workflow={filename}|line={match.group('line')}|"
        f"column={match.group('column')}|rule={rule}"
    )
if status == 0:
    print('EXIT_DIAGNOSTIC_MISMATCH')
elif not items:
    print('NO_DIAGNOSTIC_TEXT')
else:
    print('OUTPUT_CLASSIFIED')
    print('\n'.join(items))
PYDIAG
)"
classifier_status=$?
set -e
if (( classifier_status != 0 )); then
  printf 'phase=r9-actionlint-diagnostic|error_code=CLASSIFIER_EXECUTION_FAILED\nexit=1\n'
  exit 1
fi
classification="${classification_output%%$'\n'*}"
case "$classification" in
  PASS)
    if (( actionlint_status != 0 )); then
      printf 'phase=r9-actionlint-diagnostic|error_code=EXIT_DIAGNOSTIC_MISMATCH\nexit=%s\n' "$actionlint_status"
      exit "$actionlint_status"
    fi
    phase_ok "$current_phase"
    ;;
  OUTPUT_CLASSIFIED)
    printf 'phase=r9-actionlint|error_code=CHECK_FAILED\n'
    printf '%s\n' "${classification_output#*$'\n'}"
    printf 'exit=%s\n' "$actionlint_status"
    exit "$actionlint_status"
    ;;
  NO_DIAGNOSTIC_TEXT|OUTPUT_UNCLASSIFIED|DIAGNOSTIC_LIMIT_EXCEEDED|EXIT_DIAGNOSTIC_MISMATCH)
    if (( actionlint_status == 0 )); then actionlint_status=1; fi
    printf 'phase=r9-actionlint-diagnostic|error_code=%s\nexit=%s\n' "$classification" "$actionlint_status"
    exit "$actionlint_status"
    ;;
  *)
    if (( actionlint_status == 0 )); then actionlint_status=1; fi
    printf 'phase=r9-actionlint-diagnostic|error_code=CLASSIFIER_RESULT_UNKNOWN\nexit=%s\n' "$actionlint_status"
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
