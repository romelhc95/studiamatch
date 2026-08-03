from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_production_control_preflight_is_fail_closed_and_output_based() -> None:
    script = source(".github/scripts/production_control_preflight.sh")

    assert "set -euo pipefail" in script
    assert "allow_writer=\"false\"" in script
    assert "production_writers_paused_or_unset" in script
    assert "automation_disabled" in script
    assert "--enforce" in script
    assert '"$reason" != "automation_disabled"' in script
    assert '"$reason" != "non_main_schedule_blocked"' in script
    assert "GITHUB_STEP_SUMMARY" in script
    assert "Production Control Preflight" in script
    for output in (
        "writer=$writer",
        "allow_writer=$allow_writer",
        "automation_enabled=${automation_enabled:-unset}",
        "writers_paused=${writers_paused:-unset}",
        "reason=$reason",
    ):
        assert output in script


def test_scheduled_workflows_use_environment_bound_preflight_outputs() -> None:
    workflows = {
        "fg1": source(".github/workflows/fg1_inventory.yml"),
        "fg2": source(".github/workflows/production_pipeline.yml"),
        "fg3": source(".github/workflows/fg3_integrity.yml"),
    }

    forbidden_job_if = "github.ref_name == 'main' && vars.AUTOMATION_ENABLED == 'true'"
    for name, workflow in workflows.items():
        assert "production_control_preflight:" in workflow, name
        assert "Resolve production controls" in workflow, name
        assert "steps.preflight.outputs.allow_writer" in workflow, name
        assert "needs.production_control_preflight.outputs.allow_writer == 'true'" in workflow, name
        assert forbidden_job_if not in workflow, name
        assert "PRODUCTION_WRITERS_PAUSED: ${{ vars.PRODUCTION_WRITERS_PAUSED }}" in workflow, name
        assert "AUTOMATION_ENABLED: ${{ vars.AUTOMATION_ENABLED }}" in workflow, name


def test_fg2_checks_writer_pause_before_every_mutating_station() -> None:
    workflow = source(".github/workflows/production_pipeline.yml")

    assert workflow.count("Verify production controls before mutating station") == 4
    for writer in (
        "FG2-HARVEST",
        "FG2-CLEANSING",
        "FG2-ENRICHMENT",
        "FG2-SYNC",
    ):
        assert f"production_control_preflight.sh {writer} --enforce" in workflow

    assert workflow.count("needs.production_control_preflight.outputs.allow_writer == 'true'") >= 5
    for job in (
        "phase_1_harvesting",
        "phase_1_5_cleansing",
        "phase_2_enrichment",
        "phase_3_sync",
        "phase_4_audit",
    ):
        assert f"  {job}:" in workflow


def test_fg1_and_fg3_check_writer_pause_before_mutation() -> None:
    fg1 = source(".github/workflows/fg1_inventory.yml")
    fg3 = source(".github/workflows/fg3_integrity.yml")

    assert "production_control_preflight.sh FG1 --enforce" in fg1
    assert "production_control_preflight.sh FG3 --enforce" in fg3
    assert fg1.index("Verify production controls before mutating station") < fg1.index(
        "Run Discovery Institutions"
    )
    assert fg3.index("Verify production controls before mutating station") < fg3.index(
        "Run Integrity Ping"
    )


def test_db_sync_main_push_is_report_only_and_manual_apply_is_guarded() -> None:
    workflow = source(".github/workflows/db-sync-to-pro.yml")

    assert "push:" in workflow
    assert "branches: [main]" in workflow
    assert "operation:" in workflow
    assert "backup_pitr_verified:" in workflow
    assert "ddl_authorization_id:" in workflow
    assert "Report pending migrations dry-run" in workflow
    assert "Confirm report-only mode" in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
    assert "inputs.operation == 'apply'" in workflow
    assert "inputs.apply_authorized" in workflow
    assert "inputs.backup_pitr_verified" in workflow
    assert "inputs.ddl_authorization_id != ''" in workflow
    assert "fromJSON(needs.report.outputs.pending_count) > 0" in workflow
    assert ".context/operaciones/ddl_authorizations/${DDL_AUTHORIZATION_ID}.md" in workflow
    assert "APPROVED_FOR_PRODUCTION_DDL" in workflow
    assert 'test "$(git rev-parse origin/main)" = "$CANDIDATE_SHA"' in workflow
    assert "production_control_preflight.sh DB-SYNC --enforce" in workflow
    assert "python3 scripts/maintenance/db_migrate.py --env pro --manifest" in workflow

    report_section = workflow.split("  report:", 1)[1].split("  apply:", 1)[0]
    assert "--dry-run --manifest" in report_section
    assert "Apply migrations to Pro" not in report_section
    assert not re.search(r"if:\s*github\.ref_name == 'main' && inputs\.apply_authorized", workflow)


def test_db_sync_workflow_change_is_allowed_by_transition_gates() -> None:
    security_audit = source(".github/workflows/security-audit.yml")
    f9_7_contract = source(".github/workflows/f9-7-contract.yml")

    security_allowlist = security_audit.split(
        "f98_ca1_allowed_statuses = {", 1
    )[1].split("f98_ca1_allowed = set", 1)[0]
    transition_allowlist = f9_7_contract.split("allowed_statuses = {", 1)[1].split(
        "allowed = set(allowed_statuses)", 1
    )[0]

    for allowlist in (security_allowlist, transition_allowlist):
        assert "'.github/workflows/db-sync-to-pro.yml': {'M'}" in allowlist
