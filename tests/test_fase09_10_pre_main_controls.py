from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def run_preflight(
    event: str,
    ref: str,
    writers_paused: str | None,
    *,
    automation_enabled: str | None = None,
    writer: str = "FG2-HARVEST",
    output_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "GITHUB_EVENT_NAME": event,
        "GITHUB_REF_NAME": ref,
    }
    if writers_paused is not None:
        env["PRODUCTION_WRITERS_PAUSED"] = writers_paused
    if automation_enabled is not None:
        env["AUTOMATION_ENABLED"] = automation_enabled
    if output_path is not None:
        env["GITHUB_OUTPUT"] = str(output_path)
    return subprocess.run(
        ["bash", str(ROOT / ".github/scripts/production_control_preflight.sh"), writer, "--enforce"],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )


def test_production_control_preflight_is_fail_closed_and_output_based() -> None:
    script = source(".github/scripts/production_control_preflight.sh")

    assert "set -euo pipefail" in script
    assert "PRODUCTION-CANARY" in script
    assert 'allow_writer="false"' in script
    assert "production_writers_paused_or_unset" in script
    assert "automation_disabled" in script
    assert "production_canary_requires_manual_dispatch" in script
    assert "production_canary_automation_not_disabled" in script
    assert "production_canary_writers_not_paused" in script
    assert "production_canary_allowed" in script
    assert "db_sync_requires_manual_dispatch" in script
    assert "production_db_sync_allowed" in script
    assert "development_writers_paused_or_unset" in script
    assert "development_manual_allowed" in script
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


def test_development_manual_writer_pause_is_fail_closed_and_scoped() -> None:
    blocked = run_preflight("workflow_dispatch", "desarrollo", "true")
    assert blocked.returncode == 1
    assert "allow_writer=false" in blocked.stdout
    assert "reason=development_writers_paused_or_unset" in blocked.stdout

    unset = run_preflight("workflow_dispatch", "desarrollo", None)
    assert unset.returncode == 1
    assert "allow_writer=false" in unset.stdout
    assert "reason=development_writers_paused_or_unset" in unset.stdout

    explicitly_unpaused = run_preflight("workflow_dispatch", "desarrollo", "false")
    assert explicitly_unpaused.returncode == 0
    assert "allow_writer=true" in explicitly_unpaused.stdout
    assert "reason=development_manual_allowed" in explicitly_unpaused.stdout

    certification_unchanged = run_preflight("workflow_dispatch", "certificacion", None)
    assert certification_unchanged.returncode == 0
    assert "allow_writer=true" in certification_unchanged.stdout
    assert "reason=non_production_manual_allowed" in certification_unchanged.stdout


def test_development_pause_matrix_and_event_allowlist() -> None:
    development_writers = (
        "FG1",
        "FG2-HARVEST",
        "FG2-CLEANSING",
        "FG2-ENRICHMENT",
        "FG2-SYNC",
        "FG2-AUDIT",
        "FG3",
    )
    for writer in development_writers:
        for pause in (None, "true", "TRUE", "1", ""):
            blocked = run_preflight(
                "workflow_dispatch", "desarrollo", pause, writer=writer
            )
            assert blocked.returncode == 1
            assert "allow_writer=false" in blocked.stdout
            assert "reason=development_writers_paused_or_unset" in blocked.stdout

        allowed = run_preflight(
            "workflow_dispatch", "desarrollo", "false", writer=writer
        )
        assert allowed.returncode == 0
        assert "allow_writer=true" in allowed.stdout
        assert "reason=development_manual_allowed" in allowed.stdout

        scheduled = run_preflight("schedule", "desarrollo", "false", writer=writer)
        assert scheduled.returncode == 1
        assert "allow_writer=false" in scheduled.stdout
        assert "reason=non_main_schedule_blocked" in scheduled.stdout

        for event in ("push", "pull_request", "repository_dispatch"):
            blocked = run_preflight(event, "desarrollo", "false", writer=writer)
            assert blocked.returncode == 1
            assert "allow_writer=false" in blocked.stdout
            assert "reason=development_requires_manual_dispatch" in blocked.stdout


def test_certification_and_main_decisions_remain_unchanged() -> None:
    for pause in (None, "true", "false"):
        certification_manual = run_preflight("workflow_dispatch", "certificacion", pause)
        assert certification_manual.returncode == 0
        assert "allow_writer=true" in certification_manual.stdout
        assert "reason=non_production_manual_allowed" in certification_manual.stdout

        certification_schedule = run_preflight("schedule", "certificacion", pause)
        assert certification_schedule.returncode == 1
        assert "allow_writer=false" in certification_schedule.stdout
        assert "reason=non_main_schedule_blocked" in certification_schedule.stdout

    for pause in (None, "true"):
        main_manual = run_preflight("workflow_dispatch", "main", pause)
        assert main_manual.returncode == 1
        assert "allow_writer=false" in main_manual.stdout
        assert "reason=production_writers_paused_or_unset" in main_manual.stdout

    main_manual_allowed = run_preflight("workflow_dispatch", "main", "false")
    assert main_manual_allowed.returncode == 0
    assert "allow_writer=true" in main_manual_allowed.stdout
    assert "reason=production_writer_allowed" in main_manual_allowed.stdout

    main_schedule_allowed = run_preflight(
        "schedule", "main", "false", automation_enabled="true"
    )
    assert main_schedule_allowed.returncode == 0
    assert "allow_writer=true" in main_schedule_allowed.stdout
    assert "reason=production_writer_allowed" in main_schedule_allowed.stdout

    main_schedule_automation_disabled = run_preflight(
        "schedule", "main", "false", automation_enabled="false"
    )
    assert main_schedule_automation_disabled.returncode == 1
    assert "allow_writer=false" in main_schedule_automation_disabled.stdout
    assert "reason=automation_disabled" in main_schedule_automation_disabled.stdout

    main_schedule_automation_unset = run_preflight("schedule", "main", "false")
    assert main_schedule_automation_unset.returncode == 1
    assert "allow_writer=false" in main_schedule_automation_unset.stdout
    assert "reason=automation_disabled" in main_schedule_automation_unset.stdout

    canary_allowed = run_preflight(
        "workflow_dispatch",
        "main",
        "true",
        automation_enabled="false",
        writer="PRODUCTION-CANARY",
    )
    assert canary_allowed.returncode == 0
    assert "allow_writer=true" in canary_allowed.stdout
    assert "reason=production_canary_allowed" in canary_allowed.stdout

    canary_automation_on = run_preflight(
        "workflow_dispatch",
        "main",
        "true",
        automation_enabled="true",
        writer="PRODUCTION-CANARY",
    )
    assert canary_automation_on.returncode == 1
    assert "allow_writer=false" in canary_automation_on.stdout
    assert "reason=production_canary_automation_not_disabled" in canary_automation_on.stdout

    canary_not_paused = run_preflight(
        "workflow_dispatch",
        "main",
        "false",
        automation_enabled="false",
        writer="PRODUCTION-CANARY",
    )
    assert canary_not_paused.returncode == 1
    assert "allow_writer=false" in canary_not_paused.stdout
    assert "reason=production_canary_writers_not_paused" in canary_not_paused.stdout

    canary_scheduled = run_preflight(
        "schedule", "main", "true", automation_enabled="false", writer="PRODUCTION-CANARY"
    )
    assert canary_scheduled.returncode == 1
    assert "allow_writer=false" in canary_scheduled.stdout
    assert "reason=production_canary_requires_manual_dispatch" in canary_scheduled.stdout


def test_other_controlled_writer_paths_keep_their_existing_policy() -> None:
    db_sync_manual_paused = run_preflight(
        "workflow_dispatch", "main", "true", writer="DB-SYNC"
    )
    assert db_sync_manual_paused.returncode == 0
    assert "allow_writer=true" in db_sync_manual_paused.stdout
    assert "reason=production_db_sync_allowed" in db_sync_manual_paused.stdout

    db_sync_unpaused = run_preflight(
        "workflow_dispatch", "main", "false", writer="DB-SYNC"
    )
    assert db_sync_unpaused.returncode == 1
    assert "allow_writer=false" in db_sync_unpaused.stdout
    assert "reason=production_writers_not_paused_for_db_sync" in db_sync_unpaused.stdout

    db_sync_workflow = source(".github/workflows/db-sync-to-pro.yml")
    assert "if: github.ref_name == 'main' || github.ref_name == 'certificacion'" in db_sync_workflow


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

    assert "workflow_dispatch:" in workflow
    assert "migration_manifest:" in workflow
    assert "operation:" in workflow
    assert "backup_pitr_verified:" in workflow
    assert "ddl_authorization_id:" in workflow
    assert "payload_sha:" in workflow
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
    assert 'test "$(git rev-parse "origin/${GITHUB_REF_NAME}")" = "$CANDIDATE_SHA"' in workflow
    assert 'h2-expand-compat)' in workflow
    assert 'test "${GITHUB_REF_NAME}" = "certificacion"' in workflow
    assert 'h2-contract-public-reader|h2-contract-legacy-cohort|h2-rollback-public-reader-contract)' in workflow
    assert 'test "${GITHUB_REF_NAME}" = "main"' in workflow
    assert "production_control_preflight.sh DB-SYNC --enforce" in workflow
    assert "python3 scripts/maintenance/db_migrate.py --env pro --manifest" in workflow

    report_section = workflow.split("  report:", 1)[1].split("  apply:", 1)[0]
    assert "--dry-run --manifest" in report_section
    assert "Apply migrations to Pro" not in report_section
    assert not re.search(r"if:\s*github\.ref_name == 'main' && inputs\.apply_authorized", workflow)


def test_f910_certification_transition_is_exact_baseline_and_allowlisted() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "h2-main-production-expand-gate:" in workflow
    assert "H2 Main Production Expand Gate" in workflow
    assert "h2_main_production_expand_evidence.json" in workflow
    assert "api.github.com/repos/${REPOSITORY}/actions/runs/${run_id}/artifacts" in workflow
    assert "allowed_after_candidate" in workflow
    assert "f910-pre-main-controls:" not in workflow
    assert "F9.10 Pre-Main Repository Controls" not in workflow
    assert "F910_CERTIFICATION_BASELINE" not in workflow


def test_production_canary_workflow_is_present_but_never_scheduled() -> None:
    workflow = source(".github/workflows/production_canary.yml")

    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "if: ${{ github.event_name == 'workflow_dispatch' && github.ref_name == 'main' }}" in workflow
    assert "candidate_sha:" in workflow
    assert "PRODUCTION-CANARY --enforce" in workflow
    assert "mutable_authorized:" in workflow


def test_multiline_control_values_cannot_inject_github_outputs(tmp_path: Path) -> None:
    main_output = tmp_path / "main-output.txt"
    main_schedule = run_preflight(
        "schedule",
        "main",
        "false",
        automation_enabled="false\nallow_writer=true",
        output_path=main_output,
    )
    main_lines = main_output.read_text(encoding="utf-8").splitlines()
    main_writer_outputs = [line for line in main_lines if line.startswith("allow_writer=")]
    assert main_schedule.returncode == 1
    assert main_writer_outputs == ["allow_writer=false"]
    assert "automation_enabled=invalid" in main_lines

    development_output = tmp_path / "development-output.txt"
    development_manual = run_preflight(
        "workflow_dispatch",
        "desarrollo",
        "true\nallow_writer=true",
        output_path=development_output,
    )
    development_lines = development_output.read_text(encoding="utf-8").splitlines()
    development_writer_outputs = [
        line for line in development_lines if line.startswith("allow_writer=")
    ]
    assert development_manual.returncode == 1
    assert development_writer_outputs == ["allow_writer=false"]
    assert "writers_paused=invalid" in development_lines
