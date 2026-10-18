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
python3 - <<'PYSYN'
import json
import re

allowed = {
    '.githooks/pre-commit',
    '.githooks/pre-push',
    'scripts/security/h2_web_mock_smoke.sh',
    'scripts/security/protected_path_scope_guard.sh',
    'scripts/security/scan_credentials.sh',
    'tests/sql/h3_invitation_reservation_concurrency.sh',
    'tests/test_protected_path_scope_guard.sh',
}

def classify(raw, status):
    if len(raw.encode('utf-8')) > 65536:
        return 'DIAGNOSTIC_LIMIT_EXCEEDED', []
    try:
        findings = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError):
        return 'OUTPUT_INVALID', []
    if not isinstance(findings, list):
        return 'OUTPUT_INVALID', []
    if not findings:
        return ('PASS', []) if status == 0 else ('NO_DIAGNOSTICS', [])
    if status == 0:
        return 'EXIT_DIAGNOSTIC_MISMATCH', []
    if len(findings) > 40:
        return 'DIAGNOSTIC_LIMIT_EXCEEDED', []
    result = []
    for finding in findings:
        if not isinstance(finding, dict):
            return 'OUTPUT_INVALID', []
        raw_path = finding.get('file')
        if not isinstance(raw_path, str):
            return 'PATH_UNCLASSIFIED', []
        normalized = raw_path.replace('\\', '/')
        matches = [path for path in allowed if normalized == path or normalized.endswith('/' + path)]
        if len(matches) != 1:
            return 'PATH_UNCLASSIFIED', []
        line = finding.get('line')
        column = finding.get('column')
        code = finding.get('code')
        if any(type(value) is not int or value < 0 or value > 999999 for value in (line, column)):
            return 'OUTPUT_INVALID', []
        if type(code) is not int or code <= 0 or code > 9999:
            return 'OUTPUT_INVALID', []
        result.append(
            f"diagnostic=script={matches[0]}|line={line}|column={column}|rule=SC{code:04d}"
        )
    return 'FINDINGS', result

valid = json.dumps([{
    'file': 'scripts/security/scan_credentials.sh', 'line': 7, 'column': 3,
    'code': 2155, 'message': 'synthetic raw text must not escape',
}])
assert classify(valid, 1) == ('FINDINGS', [
    'diagnostic=script=scripts/security/scan_credentials.sh|line=7|column=3|rule=SC2155'
])
absolute = json.dumps([{
    'file': '/tmp/candidate/.githooks/pre-commit', 'line': 0, 'column': 0,
    'code': 1000, 'message': 'synthetic',
}])
assert classify(absolute, 1) == ('FINDINGS', [
    'diagnostic=script=.githooks/pre-commit|line=0|column=0|rule=SC1000'
])
assert classify(json.dumps([{'file': 'unlisted.sh', 'line': 1, 'column': 1, 'code': 1}]), 1) == ('PATH_UNCLASSIFIED', [])
assert classify('', 1) == ('OUTPUT_INVALID', [])
assert classify('[]', 1) == ('NO_DIAGNOSTICS', [])
assert classify(valid, 0) == ('EXIT_DIAGNOSTIC_MISMATCH', [])
assert 'synthetic raw text' not in '\n'.join(classify(valid, 1)[1])
assert classify('[]', 0) == ('PASS', [])
assert classify(' ' * 65537, 1) == ('DIAGNOSTIC_LIMIT_EXCEEDED', [])
too_many = json.dumps([{
    'file': 'scripts/security/scan_credentials.sh', 'line': 1, 'column': 1,
    'code': 2155, 'message': 'synthetic',
}] * 41)
assert classify(too_many, 1) == ('DIAGNOSTIC_LIMIT_EXCEEDED', [])
assert classify(json.dumps([{
    'file': 'scripts/security/scan_credentials.sh', 'line': -1, 'column': 1,
    'code': 2155,
}]), 1) == ('OUTPUT_INVALID', [])
assert classify(json.dumps([{
    'file': 'scripts/security/scan_credentials.sh', 'line': 1, 'column': 1,
    'code': 10000,
}]), 1) == ('OUTPUT_INVALID', [])
assert classify('{"comments":[]}', 0) == ('OUTPUT_INVALID', [])
PYSYN
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
classification_output="$(python3 - /tmp/h3req1-shellcheck/output.json "$shellcheck_status" <<'PYCLASS'
import json
import sys
from pathlib import Path

allowed = {
    '.githooks/pre-commit',
    '.githooks/pre-push',
    'scripts/security/h2_web_mock_smoke.sh',
    'scripts/security/protected_path_scope_guard.sh',
    'scripts/security/scan_credentials.sh',
    'tests/sql/h3_invitation_reservation_concurrency.sh',
    'tests/test_protected_path_scope_guard.sh',
}

def classify(raw, status):
    if len(raw.encode('utf-8')) > 65536:
        return 'DIAGNOSTIC_LIMIT_EXCEEDED', []
    try:
        findings = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError):
        return 'OUTPUT_INVALID', []
    if not isinstance(findings, list):
        return 'OUTPUT_INVALID', []
    if not findings:
        return ('PASS', []) if status == 0 else ('NO_DIAGNOSTICS', [])
    if status == 0:
        return 'EXIT_DIAGNOSTIC_MISMATCH', []
    if len(findings) > 40:
        return 'DIAGNOSTIC_LIMIT_EXCEEDED', []
    result = []
    for finding in findings:
        if not isinstance(finding, dict):
            return 'OUTPUT_INVALID', []
        raw_path = finding.get('file')
        if not isinstance(raw_path, str):
            return 'PATH_UNCLASSIFIED', []
        normalized = raw_path.replace('\\', '/')
        matches = [path for path in allowed if normalized == path or normalized.endswith('/' + path)]
        if len(matches) != 1:
            return 'PATH_UNCLASSIFIED', []
        line = finding.get('line')
        column = finding.get('column')
        code = finding.get('code')
        if any(type(value) is not int or value < 0 or value > 999999 for value in (line, column)):
            return 'OUTPUT_INVALID', []
        if type(code) is not int or code <= 0 or code > 9999:
            return 'OUTPUT_INVALID', []
        result.append(
            f"diagnostic=script={matches[0]}|line={line}|column={column}|rule=SC{code:04d}"
        )
    return 'FINDINGS', result

path = Path(sys.argv[1])
if not path.is_file():
    print('OUTPUT_INVALID')
    raise SystemExit(0)
classification, diagnostics = classify(path.read_text(encoding='utf-8'), int(sys.argv[2]))
print(classification)
if diagnostics:
    print('\n'.join(diagnostics))
PYCLASS
)"
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
  OUTPUT_INVALID|PATH_UNCLASSIFIED|NO_DIAGNOSTICS|DIAGNOSTIC_LIMIT_EXCEEDED|EXIT_DIAGNOSTIC_MISMATCH)
    if (( shellcheck_status == 0 )); then shellcheck_status=1; fi
    printf 'phase=shellcheck-diagnostic|error_code=%s\nexit=%s\n' "$classification" "$shellcheck_status"
    exit "$shellcheck_status"
    ;;
  *)
    if (( shellcheck_status == 0 )); then shellcheck_status=1; fi
    printf 'phase=shellcheck-diagnostic|error_code=CLASSIFIER_RESULT_UNKNOWN\nexit=%s\n' "$shellcheck_status"
    exit "$shellcheck_status"
    ;;
esac
