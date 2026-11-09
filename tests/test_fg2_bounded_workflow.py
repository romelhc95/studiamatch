"""Repository-level guards for the manual FG2 cohort handoff."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/production_pipeline.yml"


def test_bounded_first_run_is_opt_in_and_does_not_change_the_schedule() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    header = workflow.split("concurrency:", 1)[0]

    assert "cron: '0 5 * * *'" in header
    assert "bounded_first_run:" in header
    bounded_input = header.split("bounded_first_run:", 1)[1].split("concurrency:", 1)[0]
    assert "type: boolean" in bounded_input
    assert "default: false" in bounded_input
    assert "required: false" in bounded_input
    assert "github.event_name == 'workflow_dispatch' && inputs.bounded_first_run" in workflow


def test_controlled_manifest_is_bound_through_each_downstream_job() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "cohort_manifest_b64: ${{ steps.harvest.outputs.cohort_manifest_b64 }}" in workflow
    assert "cohort_manifest_sha256: ${{ steps.harvest.outputs.cohort_manifest_sha256 }}" in workflow
    assert workflow.count("Restore exact controlled cohort manifest") == 3
    assert "Preserve controlled FG2 cohort manifest for review and recovery" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "if-no-files-found: ignore" in workflow
    assert workflow.count("--cohort-manifest-sha256 \"$FG2_COHORT_MANIFEST_SHA256\"") == 3

    for job in ("phase_1_5_cleansing", "phase_2_enrichment", "phase_3_sync"):
        section = workflow.split(f"  {job}:", 1)[1].split("\n  phase_", 1)[0]
        assert "needs: [production_control_preflight, phase_1_harvesting" in section
        assert "FG2_COHORT_MANIFEST_SHA256" in section


def test_ordinary_harvest_and_downstream_paths_remain_available() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "python3 scripts/core/master_orchestrator.py --limit 10 --skip-cleansing" in workflow
    assert "python scripts/core/cleansing_worker.py\n" in workflow
    assert "python scripts/core/enrichment_worker.py\n" in workflow
    assert "python scripts/core/sync_vector_worker.py\n" in workflow
    assert "production_control_preflight.sh FG2-HARVEST --enforce" in workflow
    assert "production_control_preflight.sh FG2-CLEANSING --enforce" in workflow
    assert "production_control_preflight.sh FG2-ENRICHMENT --enforce" in workflow
    assert "production_control_preflight.sh FG2-SYNC --enforce" in workflow


def test_every_downstream_cli_rejects_an_unhashed_manifest_before_startup() -> None:
    for script in (
        "cleansing_worker.py",
        "enrichment_worker.py",
        "sync_vector_worker.py",
    ):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/core" / script),
                "--cohort-manifest",
                "/tmp/fg2-manifest-must-not-be-opened.json",
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 2, (script, result.stderr)
        assert "controlled cohort requires an expected SHA-256" in result.stderr, script
