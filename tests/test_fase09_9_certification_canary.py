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
    assert "max_records" in cleansing
    assert "active_batch_size" in cleansing
    assert "lock_staging_records returned non-cohort or unlocked row" in cleansing
    assert "--institution-id" in enrichment
    assert "institution_id=in." in enrichment
    assert "worker.db.patch_raise('cleansed_programs'" not in enrichment
    assert "--institution-id" in sync
    assert "cross_institution_url_collision" in sync
    assert "--institution-id" in integrity
    assert "active_limit = None if limit is None else max(limit - expired_count, 0)" in integrity


def test_mutable_canary_writers_mark_row_provenance() -> None:
    harvester = source("scripts/core/universal_harvester.py")
    cleansing = source("scripts/core/cleansing_worker.py")
    enrichment = source("scripts/core/enrichment_worker.py")
    sync = source("scripts/core/sync_vector_worker.py")

    assert "F99_CERTIFICATION_CANARY_RUN_ID" in harvester
    assert "f99_certification_canary_run_id" in harvester
    assert "F9.9 certification canary run" in harvester
    assert "f99_certification_canary_run_id" in cleansing
    assert "_mark_canary_metadata" in cleansing
    assert "_verify_canary_cleansed_row" in cleansing
    assert "f99_certification_canary_run_id" in enrichment
    assert "_mark_canary_metadata" in enrichment
    assert "_verify_canary_enriched_row" in enrichment
    assert "f99-certification-canary" in sync
    assert "_mark_canary_provider" in sync


def test_canary_manifest_is_sanitized_and_does_not_print_internal_ids() -> None:
    manifest = source("scripts/core/certification_canary_manifest.py")

    assert "institution_slug" in manifest
    assert "institution_name" in manifest
    assert "CANARY_INSTITUTION_ID" in manifest
    assert '"institution_id"' not in manifest
    assert "print(json" not in manifest
    assert "workflow_dispatch" in manifest
    assert "push" in manifest
    assert "after-cleanup" in manifest
    assert 'if os.getenv("GITHUB_ACTIONS") != "true"' not in manifest.split("def _ensure_certification_supabase_target():", 1)[1].split("def _resolve_institution", 1)[0]
    assert 'parsed.scheme != "https"' in manifest
    assert "parsed.username" in manifest
    assert "port not in (None, 443)" in manifest


def test_canary_state_private_snapshot_and_sanitized_summary_contract() -> None:
    state = source("scripts/core/certification_canary_state.py")

    assert "STATE_SCHEMA" in state
    assert "SUMMARY_SCHEMA" in state
    assert "select_all_pipeline" in state
    assert "select_all_service" in state
    assert "patch_exact_one_raise" in state
    assert "expect_noop" in state
    assert "private_digest" in state
    assert "deleted_canary_rows" in state
    assert "restored_existing_rows" in state
    assert "non_cohort_count_matches" in state
    assert "institution_site_profiles" in state
    assert '"institutions"' in state
    assert "_select_restore_rows" in state
    assert "_has_canary_marker" in state
    assert "_has_any_canary_marker" in state
    assert "_ensure_clean_prestate" in state
    assert "dirty canary leftovers" in state
    assert "canary_run_id" in state
    assert "f99-certification-canary" in state
    assert "f99_certification_canary_run_id" in state
    assert '.split("|")' in state
    assert ".splitlines()" in state
    assert "Refusing to delete pre-existing or unverified extra row" in state
    assert '"cohort_column": "institution_id"' in state
    assert 'null_filter = f"{column}=is.null"' in state
    assert "VOLATILE_RESTORE_COLUMNS" in state
    assert "updated_at" in state
    assert "_ensure_certification_supabase_target" in state
    assert 'if os.getenv("GITHUB_ACTIONS") != "true"' not in state.split("def _ensure_certification_supabase_target():", 1)[1].split("def _canonical", 1)[0]
    assert 'parsed.scheme != "https"' in state
    assert "parsed.username" in state
    assert "port not in (None, 443)" in state


def test_sync_vector_rejects_orphan_course_url_collision() -> None:
    sync = source("scripts/core/sync_vector_worker.py")

    collision_block = sync.split("Cross-institution URL collision", 1)[0].rsplit("if (", 1)[1]
    assert "existing_course" in collision_block
    assert "str(existing_inst_id) != str(enriched['institution_id'])" in collision_block
    assert "and existing_inst_id" not in collision_block
    assert "invalid_enriched_url" in sync
    assert "is_safe_public_url" in sync
    assert "validated_url" in sync
    assert "_verify_canary_course_marker" in sync
    assert "canary_course_marker_missing" in sync


def test_cleansing_fallback_rejects_cross_institution_url_collision() -> None:
    cleansing = source("scripts/core/cleansing_worker.py")

    fallback_block = cleansing.split("upsert('cleansed_programs'", 1)[0].rsplit("for item in cleansed_batch:", 1)[1]
    assert "select_pipeline_raise" in fallback_block
    assert "url=eq." in fallback_block
    assert "str(existing.get('institution_id')) != str(item['institution_id'])" in fallback_block
    assert "cross_institution_url_collision" in fallback_block
    assert "member_institutions" in cleansing
    assert "invalid_cleansed_url" in cleansing
    assert "canary provenance marker missing from cleansed_programs" in cleansing
    assert "is_safe_public_url(url)" in source("scripts/core/sync_vector_worker.py")


def test_security_audit_f99_runtime_manifest_includes_canary_runtime() -> None:
    workflow = source(".github/workflows/security-audit.yml")
    runtime_manifest = workflow.split("runtime_paths = {", 1)[1].split("harness_paths =", 1)[0]

    assert ".github/workflows/f9_9_certification_canary.yml" in runtime_manifest
    assert "scripts/core/certification_canary_manifest.py" in runtime_manifest
    assert "scripts/core/certification_canary_state.py" in runtime_manifest
    assert "scripts/core/enrichment_worker.py" in runtime_manifest
    assert "scripts/core/master_orchestrator.py" in runtime_manifest


def test_security_audit_freezes_selective_certification_identity() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "F99_CERTIFICATION_BASELINE: e4ad815624184b692219ca9490347880af8de6b6" in workflow
    assert "F99_CA1_SOURCE_COMMIT: 456becf94a2bab3d8091c7036509cfb80791a3f9" in workflow
    assert "denied_prefixes = ('db/', 'supabase/', 'web/', 'scripts/maintenance/')" in workflow
    assert "source-drift:{path}" in workflow
    assert "f99-certification-selective" in workflow
    assert "github.base_ref == 'certificacion'" in workflow
    assert "F99_REQUIRED" in workflow
    source_equal_exclusions = workflow.split("source_equal_paths = sorted(runtime_paths - {", 1)[1].split("})", 1)[0]
    assert "scripts/core/cleansing_worker.py" in source_equal_exclusions
    assert "scripts/core/enrichment_worker.py" in source_equal_exclusions
    assert "scripts/core/sync_vector_worker.py" in source_equal_exclusions
    assert "scripts/core/universal_harvester.py" in source_equal_exclusions
