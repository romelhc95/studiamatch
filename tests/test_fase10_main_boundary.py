from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_f10_main_boundary_gate_is_present_in_security_audit() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "f10-main-boundary:" in workflow
    assert "F10 Main Boundary" in workflow
    assert "F10 main PR must be certificacion -> main" in workflow
    assert "F10 main PR must use the protected certificacion tip" in workflow
    assert "merge-base" not in workflow
    assert "EXPECTED_COUNT = 9" in workflow
    assert '".github/workflows/opencode.yml"' in workflow
    assert '".github/workflows/f9-7-contract.yml"' in workflow
    assert "needs.f10-main-boundary.result" in workflow
    assert "MAIN_PROMOTION" in workflow
    assert "f107-certification-gate-update:" in workflow
    assert "F10.7 Certification Gate Update" in workflow
    assert "5cd27c6f6c35808865b7084673a83f9f690d3760" in workflow
    assert "f107-certification-gate-update" in workflow
    assert "f910-pre-main-controls:" in workflow
    assert "F9.10 Pre-Main Repository Controls" in workflow
    assert "bc227629b8df1fcabca47ea7be3ea1d5b4c7667b" in workflow
    assert "bfe46ab31b150051f2842e6d8c196a2bfd431fab" in workflow
    assert "needs.f910-pre-main-controls.result" in workflow
    assert "F910: ${{ needs.f910-pre-main-controls.result }}" in workflow
    assert "CERTIFICATION_TRANSITION" in workflow
    assert "F910_REQUIRED" in workflow
    assert "f108-main-gate-update:" in workflow
    assert "F10.8 Main Gate Update" in workflow
    assert "f9f66e6d37b26b0f9b03ce3a3267f29c35738604" in workflow


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


def test_production_canary_is_manual_main_only_before_schedules() -> None:
    workflow = source(".github/workflows/production_canary.yml")

    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "github.ref_name == 'main'" in workflow
    assert 'test "$GITHUB_REF_NAME" = "main"' in workflow
    assert "Production-Scheduled" not in workflow
