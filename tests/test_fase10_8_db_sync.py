from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def job_section(workflow: str, job_id: str) -> str:
    pattern = rf"^  {re.escape(job_id)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)"
    match = re.search(pattern, workflow, re.M | re.S)
    assert match, f"job {job_id} not found"
    return match.group(0)


WORKFLOW = source(".github/workflows/db-sync-to-pro.yml")


def test_push_main_without_db_changes_skips_production_jobs() -> None:
    detect = job_section(WORKFLOW, "detect-db-changes")
    preflight = job_section(WORKFLOW, "db-contract-preflight")
    report = job_section(WORKFLOW, "report")
    apply = job_section(WORKFLOW, "apply")
    verify = job_section(WORKFLOW, "verify")

    assert "github.event.before" in detect
    assert "github.sha" in detect
    assert 'git diff --quiet "$BEFORE_SHA" "$CANDIDATE_SHA" -- db/' in detect
    assert "db_changed=false" in detect
    assert "db_changed=true" in detect
    assert "0000000000000000000000000000000000000000" in detect
    assert "git merge-base --is-ancestor" in detect

    for section in (preflight, report):
        assert "needs.detect-db-changes.outputs.db_changed == 'true'" in section
    assert "needs.db-contract-preflight.result == 'success'" in report

    assert "github.event_name == 'workflow_dispatch'" in apply
    assert "github.event_name == 'workflow_dispatch'" in verify


def test_detector_and_preflight_do_not_load_production_or_secrets() -> None:
    detect = job_section(WORKFLOW, "detect-db-changes")
    preflight = job_section(WORKFLOW, "db-contract-preflight")

    for section in (detect, preflight):
        assert "environment:" not in section
        assert "Production" not in section
        assert "secrets." not in section
        assert "SUPABASE_URL" not in section
        assert "NEXT_SUPABASE_SECRET_KEY" not in section
        assert "persist-credentials: false" in section


def test_preflight_validates_manifest_before_secret_bearing_report() -> None:
    preflight = job_section(WORKFLOW, "db-contract-preflight")
    report = job_section(WORKFLOW, "report")

    assert WORKFLOW.index("  db-contract-preflight:") < WORKFLOW.index("  report:")
    assert "needs: detect-db-changes" in preflight
    assert "test -f \"$MIGRATION_MANIFEST\"" in preflight
    assert (
        'python3 scripts/maintenance/db_migrate.py --env pro --validate-only --manifest "$MIGRATION_MANIFEST"'
        in preflight
    )
    assert "needs: [detect-db-changes, db-contract-preflight]" in report
    assert "environment:" in report
    assert "name: Production" in report
    assert "secrets.SUPABASE_URL" in report
    assert "secrets.NEXT_SUPABASE_SECRET_KEY" in report
    assert "NEXT_SUPABASE_PUBLISHABLE_KEY" not in report


def test_workflow_dispatch_report_preserves_dry_run_only_path() -> None:
    detect = job_section(WORKFLOW, "detect-db-changes")
    report = job_section(WORKFLOW, "report")

    assert 'if [ "$EVENT_NAME" = "workflow_dispatch" ]; then' in detect
    assert "DB Sync manual dispatch requires report/preflight path" in detect
    assert '--dry-run --manifest "$MIGRATION_MANIFEST"' in report
    assert "Confirm report-only mode" in report
    assert "Apply migrations to Pro" not in report
    assert "printf '%s' \"$count\" | grep -Eq '^[0-9]+$'" in report


def test_workflow_dispatch_apply_remains_manual_and_gated() -> None:
    apply = job_section(WORKFLOW, "apply")
    verify = job_section(WORKFLOW, "verify")
    defer = job_section(WORKFLOW, "defer-fg2")

    assert "needs: [detect-db-changes, report]" in apply
    assert "github.event_name == 'workflow_dispatch'" in apply
    assert "inputs.operation == 'apply'" in apply
    assert "inputs.apply_authorized" in apply
    assert "inputs.backup_pitr_verified" in apply
    assert "inputs.ddl_authorization_id != ''" in apply
    assert "fromJSON(needs.report.outputs.pending_count) > 0" in apply
    assert ".context/operaciones/ddl_authorizations/${DDL_AUTHORIZATION_ID}.md" in apply
    assert "APPROVED_FOR_PRODUCTION_DDL" in apply
    assert "production_control_preflight.sh DB-SYNC --enforce" in apply
    assert "ref: ${{ needs.detect-db-changes.outputs.candidate_sha }}" in apply

    assert "needs: [detect-db-changes, report, apply]" in verify
    assert "needs.report.result == 'success'" in verify
    assert "needs.apply.result == 'success'" in verify
    assert "needs.verify.result == 'success'" in defer


def test_untrusted_inputs_are_not_interpolated_directly_into_shell() -> None:
    shell_blocks = re.findall(r"run: \|\n((?:          .+\n)+)", WORKFLOW)
    assert shell_blocks, "expected shell blocks"
    for block in shell_blocks:
        assert "${{ inputs.candidate_sha }}" not in block
        assert "${{ github.event.before }}" not in block
        assert "${{ github.sha }}" not in block


def test_no_prohibited_surfaces_are_introduced() -> None:
    assert "schedule:" not in WORKFLOW
    assert "production_canary" not in WORKFLOW
    assert "workflow_dispatch" in WORKFLOW
    assert "supabase/functions" not in WORKFLOW


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("F10.8 DB Sync contract assertions passed")
