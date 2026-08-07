from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_certification_canary_workflow_is_manual_and_environment_bound() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    assert "workflow_dispatch:" in workflow
    assert "push:" in workflow
    assert "branches: [certificacion]" in workflow
    assert "schedule:" not in workflow
    assert "name: Certification" in workflow
    assert "github.ref_name == 'certificacion'" in workflow
    assert 'test "$GITHUB_REF_NAME" = "certificacion"' in workflow
    assert "default: false" in workflow
    assert "F99_CERTIFICATION_CANARY_MUTABLE_APPROVED=true" in workflow
    assert "F99_CERTIFICATION_CANARY_SUPABASE_HOST" in workflow
    assert "F99_CERTIFICATION_CANARY_RUN_ID: ${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert "parsed.scheme != 'https'" in workflow
    assert "parsed.username" in workflow
    assert "port not in (None, 443)" in workflow
    assert "Production-Scheduled" not in workflow
    assert "github.ref_name == 'main'" not in workflow
    assert "fg1_source_slug must be empty or equal to institution_slug" in workflow
    assert "--no-insert" in workflow
    assert "inputs.institution_slug" not in workflow
    assert "inputs.fg1_source_slug" not in workflow


def test_certification_canary_workflow_avoids_input_shell_injection_with_secrets() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    run_blocks = "\n".join(block for block in workflow.split("\n      - name:") if "run: |" in block)
    assert "${{ inputs.max_harvest_urls }}" not in run_blocks
    assert "${{ inputs.max_staging_records }}" not in run_blocks
    assert "${{ inputs.max_enrichment_records }}" not in run_blocks
    assert "${{ inputs.max_sync_records }}" not in run_blocks
    assert "${{ inputs.max_integrity_courses }}" not in run_blocks
    assert "SUPABASE_URL: ${{ secrets.SUPABASE_URL }}" in workflow
    job_env = workflow.split("    steps:", 1)[0]
    assert "CONFIG_INSTITUTION_SLUG: ${{ secrets.F99_CERTIFICATION_CANARY_INSTITUTION_SLUG }}" in job_env
    assert "CONFIG_FG1_SOURCE_SLUG: ${{ secrets.F99_CERTIFICATION_CANARY_FG1_SOURCE_SLUG }}" in job_env
    assert "F99_CERTIFICATION_CANARY_SUPABASE_HOST: ${{ secrets.F99_CERTIFICATION_CANARY_SUPABASE_HOST }}" in job_env
    assert "vars.F99_CERTIFICATION_CANARY_INSTITUTION_SLUG" not in workflow
    assert "vars.F99_CERTIFICATION_CANARY_FG1_SOURCE_SLUG" not in workflow
    assert "vars.F99_CERTIFICATION_CANARY_SUPABASE_HOST" not in workflow


def test_certification_canary_masks_private_identifiers_before_github_env() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    concurrency = workflow.split("concurrency:", 1)[1].split("permissions:", 1)[0]
    assert "institution" not in concurrency.lower()
    assert "slug" not in concurrency.lower()
    assert "host" not in concurrency.lower()

    mask_step = workflow.split("Mask Certification private identifiers", 1)[1].split(
        "Guard Certification target and limits", 1
    )[0]
    assert "::add-mask::%s" in mask_step
    assert "$CONFIG_INSTITUTION_SLUG" in mask_step
    assert "$CONFIG_FG1_SOURCE_SLUG" in mask_step
    assert "$F99_CERTIFICATION_CANARY_SUPABASE_HOST" in mask_step

    manifest = source("scripts/core/certification_canary_manifest.py")
    assert manifest.index("_mask_github_value(institution_id)") < manifest.index(
        "handle.write(f\"CANARY_INSTITUTION_ID="
    )
    assert manifest.index("_mask_github_value(institution[\"slug\"])") < manifest.index(
        "_write_github_env(args.github_env"
    )


def test_certification_canary_workflow_passes_cohort_limits_to_all_stages() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    assert "--source-slug \"$source_slug\"" in workflow
    assert "--institution-slug \"$CANARY_INSTITUTION_SLUG\"" in workflow
    assert "--max-urls \"$CANARY_MAX_HARVEST_URLS\"" in workflow
    assert "scripts/core/cleansing_worker.py" in workflow
    assert "--institution-id \"$CANARY_INSTITUTION_ID\"" in workflow
    assert "--limit \"$CANARY_MAX_STAGING_RECORDS\"" in workflow
    assert "scripts/core/enrichment_worker.py" in workflow
    assert "--limit \"$CANARY_MAX_ENRICHMENT_RECORDS\"" in workflow
    assert "scripts/core/sync_vector_worker.py" in workflow
    assert "--limit \"$CANARY_MAX_SYNC_RECORDS\"" in workflow
    assert "scripts/core/integrity_ping.py" in workflow
    assert "--limit \"$CANARY_MAX_INTEGRITY_COURSES\"" in workflow


def test_certification_canary_workflow_has_actionlint_safe_shell_and_artifacts() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    assert 'export JOB_START_TIME="$(' not in workflow
    assert 'JOB_START_TIME="$(date +%s)"' in workflow
    assert "export JOB_START_TIME" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "path: artifacts/f9_9_canary_*.json" in workflow
    assert "retention-days: 30" in workflow


def test_certification_canary_restores_mutable_state_and_checks_idempotence() -> None:
    workflow = source(".github/workflows/f9_9_certification_canary.yml")

    assert "Stop mutable canary until cleanup is approved" not in workflow
    assert "Capture private mutable canary pre-state" in workflow
    assert "certification_canary_state.py snapshot" in workflow
    assert "Restore mutable canary state" in workflow
    assert "certification_canary_state.py restore" in workflow
    assert "Verify mutable canary cleanup idempotence" in workflow
    assert "--expect-noop" in workflow
    assert "CANARY_PRIVATE_SNAPSHOT=$RUNNER_TEMP/f9_9_canary_state/private_snapshot.json" in workflow
    assert "path: artifacts/f9_9_canary_*.json" in workflow


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
    state = source("scripts/core/certification_canary_state.py")

    assert '"institution_slug": "redacted"' in manifest
    assert '"institution_name": "redacted"' in manifest
    assert '"institution_slug": "redacted"' in state
    assert '"institution_name": "redacted"' in state
    assert "CANARY_INSTITUTION_ID" in manifest
    assert '"institution_id"' not in manifest
    assert "print(json" not in manifest
    assert "_mask_github_value(institution_id)" in manifest
    assert "_mask_github_value(institution_id)" in state
    assert "Expected exactly one institution for slug" not in manifest
    assert "Expected exactly one institution for slug" not in state


def test_canary_state_private_snapshot_and_sanitized_summary_contract() -> None:
    state = source("scripts/core/certification_canary_state.py")

    assert "STATE_SCHEMA" in state
    assert "SUMMARY_SCHEMA" in state
    assert "private_digest" not in state
    assert "deleted_canary_rows" in state
    assert "restored_existing_rows" in state
    assert "non_cohort_count_matches" in state
    assert "CANARY_PRIVATE_SNAPSHOT" not in state
    assert "VOLATILE_RESTORE_COLUMNS" in state
    assert "updated_at" in state
    assert "_ensure_certification_supabase_target" in state
    assert "_mask_github_value(institution_id)" in state
    assert '"institution_slug": "redacted"' in state
    assert '"institution_name": "redacted"' in state
    assert 'if os.getenv("GITHUB_ACTIONS") != "true"' not in state.split(
        "def _ensure_certification_supabase_target():", 1
    )[1].split("def _canonical", 1)[0]
    assert 'parsed.scheme != "https"' in state
    assert "parsed.username" in state
    assert "port not in (None, 443)" in state
    assert "Canary pre-state contains dirty canary leftovers:" not in state
    assert "Duplicate row id in canary state: {row_id}" not in state
    assert "extra row from {table}: {row_id}" not in state


def test_security_audit_f99_runtime_manifest_includes_canary_runtime() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    runtime_manifest = workflow.split("runtime_paths = {", 1)[1].split("harness_paths =", 1)[0]

    assert ".github/workflows/f9_9_certification_canary.yml" in runtime_manifest
    assert "scripts/core/certification_canary_manifest.py" in runtime_manifest
    assert "scripts/core/certification_canary_state.py" in runtime_manifest
    assert "scripts/core/enrichment_worker.py" in runtime_manifest
    assert "scripts/core/master_orchestrator.py" in runtime_manifest
