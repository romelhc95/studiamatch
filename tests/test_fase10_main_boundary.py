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
    assert "EXPECTED_ORIGINAL = {" in workflow
    assert "ALLOWED_PATHS" not in workflow
    assert "exact CA1 objects" in workflow
    assert '".context/estado_del_proyecto.md": ("A", "100644")' in workflow
    assert '".github/workflows/f9-7-contract.yml": ("A", "100644")' in workflow
    assert '"scripts/core/production_canary_source_preflight.py"' in workflow
    assert '"scripts/security/scan_credentials.sh"' in workflow
    assert '".context/evidencias_cliente/sprint_1/registro_canary_production_f10_8_2026-08-07.md"' in workflow
    assert '"tests/test_supabase_credentials_contract.py"' in workflow
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
    assert "f6fb25b2f00f283081de3180238da808117137cf" in workflow
    assert "f108-f97-main-scope:" in workflow
    assert "F10.8 F9.7 Main Scope" in workflow
    assert "8958ffdd021e09e43c48495057dc0869c990c9df" in workflow
    assert "F108_F97_SCOPE_REQUIRED" in workflow
    assert "needs.f108-f97-main-scope.result" in workflow
    assert '".github/workflows/f9-7-contract.yml": ("M", "100644")' in workflow
    assert "f108-fg1-source-slug:" in workflow
    assert "F10.8 FG1 Source Slug" in workflow
    assert "7b948c3ea5fe5057f17cf7aa11124c116f93c2f2" in workflow
    assert "F108_FG1_SOURCE_REQUIRED" in workflow
    assert "needs.f108-fg1-source-slug.result" in workflow
    assert "F10.8 FG1 source slug boundary passed" in workflow
    assert "EXPECTED_FG1_SOURCE_PROMOTION" in workflow
    assert "32526efadc21b734c58e47ff00f3a5be5b042f24" in workflow
    assert '".github/workflows/production_canary.yml": ("M", "100644")' in workflow
    assert "f108-fg1-main-boundary:" in workflow
    assert "F10.8 FG1 Main Boundary" in workflow
    assert "90bbcd76c670d84d396051dfa8af74eec9876f9c" in workflow
    assert "F108_FG1_MAIN_BOUNDARY_REQUIRED" in workflow
    assert "needs.f108-fg1-main-boundary.result" in workflow


def test_legacy_f97_gate_does_not_block_main_promotion() -> None:
    workflow = source(".github/workflows/f9-7-contract.yml")

    assert "github.event_name != 'pull_request' || github.base_ref != 'main'" in workflow


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
