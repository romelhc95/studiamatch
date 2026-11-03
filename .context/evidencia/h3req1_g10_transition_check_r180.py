#!/usr/bin/env python3
"""Structural assertions for the local two-stage H3REQ1 CI transition."""
from __future__ import annotations

import re
import os
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit('usage: transition_check.py STAGE1 STAGE2 PATCH')
stage1 = Path(sys.argv[1]).read_text(encoding='utf-8')
stage2 = Path(sys.argv[2]).read_text(encoding='utf-8')
patch = Path(sys.argv[3]).read_text(encoding='utf-8')

def top_level_block(text: str, key: str, next_key: str) -> str:
    start = text.find(f'\n{key}:\n')
    if start < 0:
        raise SystemExit(f'{key}=missing')
    end = text.find(f'\n{next_key}:\n', start + 1)
    if end < 0:
        raise SystemExit(f'{next_key}=missing')
    return text[start:end]

def job_block(text: str, name: str) -> str:
    match = re.search(rf'(?m)^  {re.escape(name)}:\n', text)
    if not match:
        raise SystemExit(f'job_{name}=missing')
    end = re.search(r'(?m)^  [a-z0-9_-]+:\n', text[match.end():])
    return text[match.start():match.end() + end.start()] if end else text[match.start():]

stage1_events = top_level_block(stage1, 'on', 'permissions')
if 'pull_request_review:' in stage1_events:
    raise SystemExit('stage1_review_event=unexpected')
if re.search(r'(?m)^  trusted-workflow-integrity:\n', stage1):
    raise SystemExit('stage1_waiter=unexpected')
permissions = top_level_block(stage1, 'permissions', 'env')
if 'contents: read' not in permissions or 'actions: read' not in permissions:
    raise SystemExit('stage1_existing_read_permissions=missing')
if 'checks: read' in permissions or 'pull-requests: read' in permissions:
    raise SystemExit('stage1_unneeded_permissions=present')
aggregate = job_block(stage1, 'security-audit')
needs = re.search(r'(?m)^    needs: \[(.*?)\]$', aggregate)
expected = 'credential-scan, protected-paths, python-check, lint, typecheck, static-build, workflow-lint, db-gate, h2-main-production-expand-gate'
if not needs or needs.group(1) != expected:
    raise SystemExit('stage1_aggregate=changed')
if "name: security-audit" not in aggregate:
    raise SystemExit('stage1_required_check=missing')

stage2_events = top_level_block(stage2, 'on', 'permissions')
if 'pull_request_review:' not in stage2_events:
    raise SystemExit('stage2_review_event=missing')
waiter = job_block(stage2, 'trusted-workflow-integrity')
expected_waiter_if = "if: (github.event_name == 'pull_request' || github.event_name == 'pull_request_review') && (github.event.pull_request.base.ref == 'desarrollo' || github.event.pull_request.base.ref == 'certificacion' || github.event.pull_request.base.ref == 'main')"
if expected_waiter_if not in waiter:
    raise SystemExit('stage2_waiter_branch_gate=unexpected')
if '      actions: read\n      pull-requests: read' not in waiter:
    raise SystemExit('stage2_waiter_permissions=unexpected')
if '      checks: read' in waiter:
    raise SystemExit('stage2_checks_permission=unexpected')
stage2_permissions = top_level_block(stage2, 'permissions', 'env')
if 'checks: read' in stage2_permissions or 'pull-requests: read' in stage2_permissions:
    raise SystemExit('stage2_permissions_not_scoped')
stage2_aggregate = job_block(stage2, 'security-audit')
stage2_needs = re.search(r'(?m)^    needs: \[(.*?)\]$', stage2_aggregate)
if not stage2_needs or not stage2_needs.group(1).startswith('trusted-workflow-integrity, '):
    raise SystemExit('stage2_waiter_dependency=missing')
if (
    'EVENT_NAME: ${{ github.event_name }}' not in stage2_aggregate
    or 'PR_BASE_REF: ${{ github.event.pull_request.base.ref }}' not in stage2_aggregate
    or 'WORKFLOW_CHECK_RESULT: ${{ needs.trusted-workflow-integrity.result }}' not in stage2_aggregate
):
    raise SystemExit('stage2_aggregate_context=missing')
if 'if [ "$EVENT_NAME" = \'pull_request\' ] || [ "$EVENT_NAME" = \'pull_request_review\' ]; then' not in stage2_aggregate:
    raise SystemExit('stage2_aggregate_event_gate=missing')
if 'case "$PR_BASE_REF" in\n              desarrollo|certificacion|main)' not in stage2_aggregate:
    raise SystemExit('stage2_aggregate_protected_base_gate=missing')
if '*) test "$WORKFLOW_CHECK_RESULT" = \'skipped\' ;;' not in stage2_aggregate:
    raise SystemExit('stage2_aggregate_unprotected_base_gate=missing')
if '+  pull_request_review:' not in patch or '+  trusted-workflow-integrity:' not in patch:
    raise SystemExit('stage2_patch_transition=missing')
if '+  checks: read' in patch or '+  pull-requests: read' in patch:
    raise SystemExit('stage2_patch_global_permission=present')
if '+      actions: read\n+      pull-requests: read' not in patch:
    raise SystemExit('stage2_patch_job_permissions=missing')
if (
    '+          PR_BASE_REF: ${{ github.event.pull_request.base.ref }}' not in patch
    or '+          WORKFLOW_CHECK_RESULT: ${{ needs.trusted-workflow-integrity.result }}' not in patch
    or '+              desarrollo|certificacion|main)' not in patch
):
    raise SystemExit('stage2_aggregate_gate=missing')
aggregate_lines = stage2_aggregate.splitlines()
run_marker = aggregate_lines.index('        run: |')
run_lines: list[str] = []
for line in aggregate_lines[run_marker + 1:]:
    if line.startswith('          '):
        run_lines.append(line[10:])
    elif not line.strip():
        run_lines.append('')
    else:
        break
gate_start = run_lines.index('if [ "$EVENT_NAME" = \'pull_request\' ] || [ "$EVENT_NAME" = \'pull_request_review\' ]; then')
gate_end = run_lines.index('fi', gate_start)
gate_script = 'set -euo pipefail\n' + '\n'.join(run_lines[gate_start:gate_end + 1]) + '\n'
cases = (
    ('pr-desarrollo', 'pull_request', 'desarrollo', 'success', 0),
    ('review-desarrollo', 'pull_request_review', 'desarrollo', 'success', 0),
    ('review-certificacion', 'pull_request_review', 'certificacion', 'success', 0),
    ('review-main', 'pull_request_review', 'main', 'success', 0),
    ('protected-failure', 'pull_request_review', 'main', 'failure', 1),
    ('unprotected-review', 'pull_request_review', 'feature/test', 'skipped', 0),
    ('unprotected-waiter-unexpected', 'pull_request_review', 'feature/test', 'success', 1),
    ('push-skipped', 'push', 'main', 'skipped', 0),
    ('dispatch-skipped', 'workflow_dispatch', '', 'skipped', 0),
)
for name, event, base, result, expected_exit in cases:
    env = os.environ.copy()
    env.update({'EVENT_NAME': event, 'PR_BASE_REF': base, 'WORKFLOW_CHECK_RESULT': result})
    completed = subprocess.run(['/bin/bash', '-c', gate_script], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != expected_exit:
        raise SystemExit(f'synthetic_transition=FAIL|case={name}|exit={completed.returncode}')
print('transition=PASS|shell_gate_cases=9/9|stage1_waiter=absent|stage1_aggregate=preserved|stage2_waiter=protected-bases-only|stage2_permissions=job-scoped|unprotected-review=skipped|checks_read=absent')
