from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_f10_main_boundary_gate_is_present_in_security_audit() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "f910-pre-main-controls:" in workflow
    assert "F9.10 Pre-Main Repository Controls" in workflow
    assert "needs.f910-pre-main-controls.result" in workflow
    assert "F910: ${{ needs.f910-pre-main-controls.result }}" in workflow
    assert "CERTIFICATION_TRANSITION" in workflow
    assert "F910_REQUIRED" in workflow


def test_main_promotion_cannot_auto_apply_database_changes() -> None:
    workflow = source(".github/workflows/db-sync-to-pro.yml")

    assert "push:" in workflow
    assert "Report pending migrations dry-run" in workflow
    assert "Confirm report-only mode" in workflow
    assert "operation == 'apply'" in workflow
    assert "backup_pitr_verified" in workflow
    assert "ddl_authorization_id" in workflow

    apply_section = workflow.split("  apply:", 1)[1].split("  verify:", 1)[0]
    assert "github.event_name == 'workflow_dispatch'" in apply_section
    assert "inputs.operation == 'apply'" in apply_section
    assert "inputs.apply_authorized" in apply_section
    assert "inputs.backup_pitr_verified" in apply_section
    assert "inputs.ddl_authorization_id != ''" in apply_section
    assert "fromJSON(needs.report.outputs.pending_count) > 0" in apply_section
    assert ".context/operaciones/ddl_authorizations/${DDL_AUTHORIZATION_ID}.md" in apply_section
    assert "APPROVED_FOR_PRODUCTION_DDL" in apply_section
    assert "Verify production controls before migrations" in apply_section


def test_main_scheduled_writers_start_paused_until_environment_controls_allow_them() -> None:
    workflows = [
        source(".github/workflows/fg1_inventory.yml"),
        source(".github/workflows/production_pipeline.yml"),
        source(".github/workflows/fg3_integrity.yml"),
    ]

    for workflow in workflows:
        assert "Production-Scheduled-" in workflow
        assert "PRODUCTION_WRITERS_PAUSED: ${{ vars.PRODUCTION_WRITERS_PAUSED }}" in workflow
        assert "needs.production_control_preflight.outputs.allow_writer == 'true'" in workflow
        assert "production_control_preflight.sh" in workflow
        assert "github.ref_name == 'main' && vars.AUTOMATION_ENABLED == 'true'" not in workflow


def test_pre_main_controls_do_not_touch_denied_runtime_surfaces() -> None:
    plan = source(".context/operaciones/plan_cierre_hito1_ca1_only.md")

    assert "Allowlist De Controles Pre-Main F9.10" in plan
    assert "`db/**`, `supabase/**`, `web/**`" in plan
    assert "Production o schedules antes de cerrar los controles pre-main" in plan
