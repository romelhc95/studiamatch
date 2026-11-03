#!/usr/bin/env bash
set -euo pipefail

current_phase='r9-input-hashes'
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
sha256sum -c inputs.sha256 >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-tool-hashes'
cd /validation-tools
sha256sum -c tools.sha256 >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-tool-extraction'
mkdir -p /lint-tools /tmp/h3req1-g03-r1
tar -xzf /validation-tools/actionlint_1.7.7_linux_amd64.tar.gz -C /lint-tools actionlint >/dev/null 2>&1
tar -xzf /validation-tools/shellcheck-v0.11.0.linux.x86_64.tar.gz -C /lint-tools shellcheck-v0.11.0/shellcheck >/dev/null 2>&1
mv /lint-tools/shellcheck-v0.11.0/shellcheck /lint-tools/shellcheck
chmod 0755 /lint-tools/actionlint /lint-tools/shellcheck
export PATH="/lint-tools:$PATH"
phase_ok "$current_phase"

current_phase='r9-tool-versions'
/lint-tools/actionlint -version >/dev/null 2>&1
/lint-tools/shellcheck --version | grep -F 'version: 0.11.0' >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-candidate-copy'
cp -a /validation/. /tmp/h3req1-g03-r1/ >/dev/null 2>&1
cd /tmp/h3req1-g03-r1
ln -s /app/web/node_modules web/node_modules
phase_ok "$current_phase"

current_phase='r9-npm-dependency-manifest'
python3 - <<'PYDEPS' >/dev/null 2>&1
import hashlib
from pathlib import Path

manifest = Path("/app/web/node_modules/.studiamatch-node-deps.sha256")
if not manifest.is_file():
    raise SystemExit(1)
lines = manifest.read_text(encoding="utf-8").splitlines()
entries = {}
for line in lines[2:]:
    parts = line.split()
    if len(parts) != 2 or parts[1] not in {"package.json", "package-lock.json"}:
        raise SystemExit(1)
    entries[parts[1]] = parts[0]
if set(entries) != {"package.json", "package-lock.json"}:
    raise SystemExit(1)
for name, expected in entries.items():
    actual = hashlib.sha256((Path("/tmp/h3req1-g03-r1/web") / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(1)
PYDEPS
phase_ok "$current_phase"

current_phase='r9-node-and-typescript-versions'
test "$(node --version)" = 'v20.20.2' >/dev/null 2>&1
test "$(node -p "require('./web/node_modules/typescript/package.json').version")" = '5.9.3' >/dev/null 2>&1
phase_ok "$current_phase"

current_phase='r9-actionlint'
cd /tmp/h3req1-g03-r1
/lint-tools/actionlint .github/workflows/security-audit.yml .github/workflows/protected-workflow-integrity.yml .github/workflows/db-sync-to-pro.yml >/dev/null 2>&1
phase_ok "$current_phase"

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
