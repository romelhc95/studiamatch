#!/usr/bin/env bash
set -u -o pipefail

phase='r9-container-preflight'
fail() {
  local code="$1" status="${2:-1}"
  (( status != 0 )) || status=1
  printf 'phase=%s|error_code=%s\nexit=%s\n' "$phase" "$code" "$status"
  exit "$status"
}
ok() { printf 'phase=%s|error_code=OK\n' "$1"; }

cd /validation 2>/dev/null || fail VALIDATION_MOUNT_UNAVAILABLE
sha256sum -c r4-package.sha256 >/dev/null 2>&1 || fail PACKAGE_HASH_MISMATCH
sha256sum -c inputs.sha256 >/dev/null 2>&1 || fail INPUT_MANIFEST_MISMATCH
[[ "$(sha256sum /r9_typegen_classifier_v1.py 2>/dev/null | cut -d' ' -f1)" == '91005ad43781de0ba157898f7851a1ea273ca211b7772b4285218e3234a3e901' ]] || fail TYPEGEN_CLASSIFIER_HASH_MISMATCH
[[ "$(sha256sum /test_r9_typegen_classifier_v1.py 2>/dev/null | cut -d' ' -f1)" == 'f00cfc98c3b566c104abdb702c97876edef6e1c0c43572c78db63bf82afc1447' ]] || fail TYPEGEN_CLASSIFIER_TEST_HASH_MISMATCH
ok "$phase"

phase='r9-candidate-copy'
mkdir -p /work/candidate 2>/dev/null || fail SCRATCH_UNAVAILABLE
cp -R /validation/. /work/candidate/ >/dev/null 2>&1 || fail CANDIDATE_COPY_FAILED
[[ -d /work/candidate/web/node_modules && -f /work/candidate/web/node_modules/.studiamatch-node-deps.sha256 ]] || fail NODE_MODULES_MOUNT_UNAVAILABLE
cd /work/candidate 2>/dev/null || fail SCRATCH_UNAVAILABLE
ok "$phase"

phase='r9-npm-dependency-manifest'
python3 - <<'PYDEPS' >/dev/null 2>&1
import hashlib
from pathlib import Path

root = Path('/work/candidate/web')
manifest = root / 'node_modules/.studiamatch-node-deps.sha256'
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
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
        raise SystemExit(1)
PYDEPS
deps_status=$?
(( deps_status == 0 )) || fail DEPENDENCY_MANIFEST_MISMATCH "$deps_status"
ok "$phase"

phase='r9-node-and-typescript-versions'
node_version="$(node --version 2>/dev/null)" || fail NODE_UNAVAILABLE
ts_version="$(node -p "require('/work/candidate/web/node_modules/typescript/package.json').version" 2>/dev/null)" || fail TYPESCRIPT_UNAVAILABLE
[[ "$node_version" == 'v20.20.2' && "$ts_version" == '5.9.3' ]] || fail VERSION_MISMATCH
ok "$phase"

phase='r9-typegen-classifier-synthetics'
classifier_tests="$(python3 /test_r9_typegen_classifier_v1.py 2>/dev/null)" || fail TYPEGEN_CLASSIFIER_TESTS_FAILED
[[ "$classifier_tests" == 'phase=r9-typegen-classifier-synthetics|error_code=OK' ]] || fail TYPEGEN_CLASSIFIER_TESTS_FAILED
ok "$phase"
phase='r9-next-typegen'
if (cd /work/candidate/web && ./node_modules/.bin/next typegen) >/tmp/h3req1-next-typegen.log 2>&1; then
  ok "$phase"
else
  typegen_status=$?
  python3 /r9_typegen_classifier_v1.py /tmp/h3req1-next-typegen.log /work/candidate/web/package.json 2>/dev/null || \
    printf 'diagnostic=next-typegen|class=UNKNOWN|module=UNCLASSIFIED\n'
  fail CHECK_FAILED "$typegen_status"
fi

phase='r9-typescript'
if (cd /work/candidate/web && env NODE_OPTIONS='--max-old-space-size=3072' \
  ./node_modules/.bin/tsc --noEmit --pretty false) \
  >/tmp/h3req1-tsc.log 2>&1; then
  ok "$phase"
else
  tsc_status=$?
  if grep -Eiq 'JavaScript heap out of memory|Reached heap limit|heap out of memory' \
    /tmp/h3req1-tsc.log 2>/dev/null; then
    fail NODE_HEAP_LIMIT "$tsc_status"
  fi
  python3 - /tmp/h3req1-tsc.log <<'PYTSC'
import re
import sys
from pathlib import Path

log = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
pattern = re.compile(r'^(.+?)\((\d+),(\d+)\): error (TS\d+):')
reported = 0
unclassified = 0
for line in log.splitlines():
    match = pattern.match(line)
    if not match:
        continue
    raw_path, row, col, code = match.groups()
    path = Path(raw_path)
    try:
        resolved = path.resolve() if path.is_absolute() else (Path('/work/candidate/web') / path).resolve()
        relative = resolved.relative_to(Path('/work/candidate').resolve()).as_posix()
    except (OSError, ValueError):
        unclassified += 1
        continue
    if '..' in Path(relative).parts or not relative.startswith((
        'web/src/', 'web/functions/', 'web/next-env.d.ts', 'web/.next/types/'
    )):
        unclassified += 1
        continue
    if reported < 20:
        print(f'diagnostic=file={relative}|line={row}|column={col}|code={code}')
        reported += 1
    else:
        unclassified += 1
if unclassified:
    print(f'diagnostic=unclassified_errors={unclassified}')
if not reported and not unclassified:
    print('diagnostic=typescript_output=NO_CLASSIFIED_DIAGNOSTIC')
PYTSC
  fail CHECK_FAILED "$tsc_status"
fi

phase='r9-protected-workflow-tests'
if [[ ! -x /opt/venv/bin/python ]]; then
  fail TEST_RUNTIME_UNAVAILABLE
fi
if ! /opt/venv/bin/python -c 'import pytest' >/dev/null 2>&1; then
  fail PYTEST_UNAVAILABLE
fi
if /opt/venv/bin/python -m pytest -q -p no:cacheprovider tests/test_protected_workflow_review.py \
  >/tmp/h3req1-workflow-tests.log 2>&1; then
  ok "$phase"
else
  test_status=$?
  python3 - /tmp/h3req1-workflow-tests.log <<'PYTEST'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
matches = re.findall(r'^=+\s*(\d+) failed(?:,|\s|=)', text, re.MULTILINE)
if matches:
    print(f'diagnostic=suite=protected-workflow-review|failed={matches[-1]}')
else:
    print('diagnostic=suite=protected-workflow-review|failed=UNKNOWN')
PYTEST
  fail CHECK_FAILED "$test_status"
fi

phase='r9-credential-scan'
if bash tests/test_scan_credentials.sh >/tmp/h3req1-credential-scan.log 2>&1; then
  ok "$phase"
else
  test_status=$?
  printf 'diagnostic=suite=credential-scan|failed=1\n'
  fail CHECK_FAILED "$test_status"
fi

phase='r9-protected-path-guard'
if bash tests/test_protected_path_scope_guard.sh >/tmp/h3req1-path-guard.log 2>&1; then
  ok "$phase"
else
  test_status=$?
  printf 'diagnostic=suite=protected-path-guard|failed=1\n'
  fail CHECK_FAILED "$test_status"
fi

phase='r9-summary'
printf 'phase=%s|error_code=ALL_PENDING_CHECKS_OK\n' "$phase"
exit 0
