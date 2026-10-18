from pathlib import Path
import json, re, sys
workflow = Path(sys.argv[1]).read_text()
manifest = json.loads(Path(sys.argv[2]).read_text())
def assignment(name):
    prefix = name + "='"
    line = next((line.strip() for line in workflow.splitlines() if line.strip().startswith(prefix)), None)
    if line is None:
        raise SystemExit(f'{name}=MISSING')
    return line[len(prefix):-1]
allowed = [re.compile(assignment('allowed_h3')), re.compile(assignment('allowed_h3_extra'))]
start = "allowed_h3_local=$(cat <<'H3_LOCAL_PATHS'"
if start not in workflow:
    raise SystemExit('allowed_h3_local=HEREDOC_MISSING')
body = workflow.split(start,1)[1].split('\n          H3_LOCAL_PATHS',1)[0]
local = {line.strip() for line in body.splitlines() if line.strip()}
entries = [e for e in manifest['scope']['entries'] if e['selection']=='proposed_change']
review_fixes = {
    'db/migrations/20261010_h3_admin_members_service_select.sql',
    'scripts/core/universal_harvester.py',
    'tests/test_h3req1_local_pipeline_walk.py',
    'web/src/app/HomeContent.tsx',
    'web/src/app/compare/CompareContent.tsx',
    'web/src/app/page.tsx',
}
missing = [e['path'] for e in entries if not any(rx.fullmatch(e['path']) for rx in allowed) and e['path'] not in local]
exact_fixes = {path for path in review_fixes if path in local and not any(rx.fullmatch(path) for rx in allowed)}
regex_count = sum(any(rx.fullmatch(e['path']) for rx in allowed) for e in entries)
exact_count = sum(e['path'] in local and not any(rx.fullmatch(e['path']) for rx in allowed) for e in entries)
if exact_fixes != review_fixes:
    print('review_fix_exact_mismatch=1')
    for path in sorted(review_fixes - exact_fixes): print('review_fix_unmatched=' + path)
    raise SystemExit(1)
if missing:
    for path in missing: print('unaccepted=' + path)
    raise SystemExit(1)
print(f'scope_allowlist=PASS|proposed={len(entries)}|regex={regex_count}|exact={exact_count}|review_fixes={len(exact_fixes)}/{len(review_fixes)}|missing={len(missing)}')
