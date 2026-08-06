from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _run_preflight(
    writer: str,
    *,
    event_name: str = "workflow_dispatch",
    ref_name: str = "main",
    automation_enabled: str = "false",
    writers_paused: str = "true",
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_EVENT_NAME": event_name,
            "GITHUB_REF_NAME": ref_name,
            "AUTOMATION_ENABLED": automation_enabled,
            "PRODUCTION_WRITERS_PAUSED": writers_paused,
        }
    )
    return subprocess.run(
        ["bash", str(ROOT / ".github/scripts/production_control_preflight.sh"), writer, "--enforce"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_db_sync_preflight_requires_writers_paused_and_manual_dispatch() -> None:
    script = source(".github/scripts/production_control_preflight.sh")

    assert 'if [ "$writer" = "DB-SYNC" ]; then' in script
    assert "PRODUCTION-CANARY" in script
    assert 'reason="production_canary_automation_not_disabled"' in script
    assert 'reason="production_canary_writers_not_paused"' in script
    assert 'reason="db_sync_requires_manual_dispatch"' in script
    assert 'reason="production_writers_not_paused_for_db_sync"' in script
    assert 'reason="production_db_sync_allowed"' in script
    assert '[ "$writers_paused" != "true" ]' in script
    assert 'elif [ "$writers_paused" != "false" ]; then' in script


def test_preflight_allows_only_manual_production_canary_with_automation_off_and_writers_paused() -> None:
    allowed = _run_preflight("PRODUCTION-CANARY")
    automation_on = _run_preflight("PRODUCTION-CANARY", automation_enabled="true")
    writers_active = _run_preflight("PRODUCTION-CANARY", writers_paused="false")
    scheduled = _run_preflight("PRODUCTION-CANARY", event_name="schedule")

    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert "reason=production_canary_allowed" in allowed.stdout
    assert automation_on.returncode != 0
    assert "production_canary_automation_not_disabled" in automation_on.stdout + automation_on.stderr
    assert writers_active.returncode != 0
    assert "production_canary_writers_not_paused" in writers_active.stdout + writers_active.stderr
    assert scheduled.returncode != 0
    assert "production_canary_requires_manual_dispatch" in scheduled.stdout + scheduled.stderr


def test_preflight_db_sync_requires_manual_dispatch_and_paused_writers() -> None:
    allowed = _run_preflight("DB-SYNC", automation_enabled="true")
    push = _run_preflight("DB-SYNC", event_name="push", automation_enabled="true")
    writers_active = _run_preflight("DB-SYNC", automation_enabled="true", writers_paused="false")

    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert "reason=production_db_sync_allowed" in allowed.stdout
    assert push.returncode != 0
    assert "db_sync_requires_manual_dispatch" in push.stdout + push.stderr
    assert writers_active.returncode != 0
    assert "production_writers_not_paused_for_db_sync" in writers_active.stdout + writers_active.stderr


def test_preflight_fg_writers_require_active_writers_and_automation_for_schedules() -> None:
    scheduled_allowed = _run_preflight(
        "FG2-SYNC",
        event_name="schedule",
        automation_enabled="true",
        writers_paused="false",
    )
    paused = _run_preflight(
        "FG2-SYNC",
        event_name="schedule",
        automation_enabled="true",
        writers_paused="true",
    )
    automation_disabled = _run_preflight(
        "FG2-SYNC",
        event_name="schedule",
        automation_enabled="false",
        writers_paused="false",
    )

    assert scheduled_allowed.returncode == 0, scheduled_allowed.stdout + scheduled_allowed.stderr
    assert "reason=production_writer_allowed" in scheduled_allowed.stdout
    assert paused.returncode != 0
    assert "production_writers_paused_or_unset" in paused.stdout + paused.stderr
    assert automation_disabled.returncode != 0
    assert "automation_disabled" in automation_disabled.stdout + automation_disabled.stderr


def test_f910_security_audit_has_dedicated_f10_boundary_gate() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "f10-main-boundary:" in workflow
    assert "F10 Main Boundary And Production Canary" in workflow
    assert "tests/test_fase10_production_canary.py" in workflow
    assert "tests/test_fase09_10_pre_main_controls.py tests/test_fase10_main_boundary.py tests/test_fase10_production_canary.py" in workflow
    assert "needs.f10-main-boundary.result" in workflow
    assert "f10-main-boundary**" in workflow


def test_f910_allowed_surfaces_are_documented_without_authorizing_f10() -> None:
    plan = source(".context/operaciones/plan_cierre_hito1_ca1_only.md")
    estado = source(".context/estado_del_proyecto.md")

    assert "Allowlist De Controles Pre-Main F9.10" in plan
    assert ".github/workflows/production_canary.yml" in plan
    assert "scripts/core/production_canary_state.py" in plan
    assert "F10 permanece bloqueada" in estado
    assert "EVID-H1-010" in plan


def test_production_canary_files_are_in_release_gate_allowlist() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    f97_contract = source(".github/workflows/f9-7-contract.yml")

    release_gate = workflow.split("f98_ca1_allowed_statuses = {", 1)[1].split(
        "f98_ca1_allowed = set", 1
    )[0]
    assert "'scripts/core/production_canary_manifest.py': {'A'}" in release_gate
    assert "'scripts/core/production_canary_state.py': {'A'}" in release_gate
    assert "'.gitattributes': {'M'}" in release_gate
    assert "'scripts/core/production_canary_manifest.py': {'A', 'M'}" in f97_contract
    assert "'scripts/core/production_canary_state.py': {'A', 'M'}" in f97_contract
    assert "'.gitattributes': {'M'}" in f97_contract
