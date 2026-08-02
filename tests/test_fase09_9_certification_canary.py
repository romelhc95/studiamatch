from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_certification_canary_workflow_is_manual_and_environment_bound() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "name: Certification" in workflow
    assert "github.ref_name == 'certificacion'" in workflow
    assert 'test "$GITHUB_REF_NAME" = "certificacion"' in workflow
    assert "Production-Scheduled" not in workflow
    assert "github.ref_name == 'main'" not in workflow
    assert "fg1_source_slug must be empty or equal to institution_slug" in workflow
    assert "--no-insert" in workflow


def test_certification_canary_workflow_avoids_input_shell_injection_with_secrets() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    run_blocks = "\n".join(block for block in workflow.split("\n      - name:") if "run: |" in block)
    assert "${{ inputs.institution_slug }}" not in run_blocks
    assert "${{ inputs.fg1_source_slug }}" not in run_blocks
    assert "${{ inputs.max_harvest_urls }}" not in run_blocks
    assert "${{ inputs.max_staging_records }}" not in run_blocks
    assert "${{ inputs.max_enrichment_records }}" not in run_blocks
    assert "${{ inputs.max_sync_records }}" not in run_blocks
    assert "${{ inputs.max_integrity_courses }}" not in run_blocks
    assert "SUPABASE_URL: ${{ secrets.SUPABASE_URL }}" in workflow
    job_env = workflow.split("    steps:", 1)[0]
    assert "secrets." not in job_env


def test_certification_canary_workflow_passes_cohort_limits_to_all_stages() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    assert "--source-slug \"$source_slug\"" in workflow
    assert "--institution-slug \"$CANARY_INSTITUTION_SLUG\"" in workflow
    assert "--max-urls \"$INPUT_MAX_HARVEST_URLS\"" in workflow
    assert "scripts/core/cleansing_worker.py" in workflow
    assert "--institution-id \"$CANARY_INSTITUTION_ID\"" in workflow
    assert "--limit \"$INPUT_MAX_STAGING_RECORDS\"" in workflow
    assert "scripts/core/enrichment_worker.py" in workflow
    assert "--limit \"$INPUT_MAX_ENRICHMENT_RECORDS\"" in workflow
    assert "scripts/core/sync_vector_worker.py" in workflow
    assert "--limit \"$INPUT_MAX_SYNC_RECORDS\"" in workflow
    assert "scripts/core/integrity_ping.py" in workflow
    assert "--limit \"$INPUT_MAX_INTEGRITY_COURSES\"" in workflow


def test_certification_canary_workflow_has_actionlint_safe_shell_and_artifacts() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    assert 'export JOB_START_TIME="$(' not in workflow
    assert 'JOB_START_TIME="$(date +%s)"' in workflow
    assert "export JOB_START_TIME" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "path: artifacts/f9_9_canary_*.json" in workflow
    assert "retention-days: 30" in workflow


def test_certification_canary_blocks_mutable_stages_until_cleanup_is_approved() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    blocker = workflow.split("Stop mutable canary until cleanup is approved", 1)[1].split("FG2 bounded harvest canary", 1)[0]
    assert "inputs.run_fg2 || inputs.run_fg3" in blocker
    assert "cleanup/restoration is implemented, idempotent, and approved" in blocker
    assert "exit 1" in blocker


def test_runtime_scripts_keep_default_schedules_but_accept_canary_cohort_flags() -> None:
    discovery = source("scripts/core/discovery_institutions.py")
    orchestrator = source("scripts/core/master_orchestrator.py")
    harvester = source("scripts/core/universal_harvester.py")
    cleansing = source("scripts/core/cleansing_worker.py")
    enrichment = source("scripts/core/enrichment_worker.py")
    sync = source("scripts/core/sync_vector_worker.py")
    integrity = source("scripts/core/integrity_ping.py")

    assert "--source-slug" in discovery
    assert "--no-insert" in discovery
    assert "--institution-slug" in orchestrator
    assert "--max-urls" in orchestrator
    assert "max_discovered_urls" in harvester
    assert "self._limit_urls(self._merge_resumable_urls" in harvester
    assert "--institution-id" in cleansing
    assert "--limit" in cleansing
    assert "--institution-id" in enrichment
    assert "--institution-id" in sync
    assert "cross_institution_url_collision" in sync
    assert "--institution-id" in integrity
    assert "active_limit = None if limit is None else max(limit - expired_count, 0)" in integrity


def test_canary_manifest_is_sanitized_and_does_not_print_internal_ids() -> None:
    manifest = source("scripts/core/certification_canary_manifest.py")

    assert "institution_slug" in manifest
    assert "institution_name" in manifest
    assert "CANARY_INSTITUTION_ID" in manifest
    assert '"institution_id"' not in manifest
    assert "print(json" not in manifest


def test_security_audit_f99_runtime_manifest_includes_canary_runtime() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    runtime_manifest = workflow.split("runtime_paths = {", 1)[1].split("harness_paths =", 1)[0]

    assert ".github/workflows/f9_9_certification_canary.yml" in runtime_manifest
    assert "scripts/core/certification_canary_manifest.py" in runtime_manifest
    assert "scripts/core/enrichment_worker.py" in runtime_manifest
    assert "scripts/core/master_orchestrator.py" in runtime_manifest
