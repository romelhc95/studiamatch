from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_f99_certification_canary_workflow_was_retired_for_h2_main_gate() -> None:
    assert not (ROOT / ".github/workflows/f9_9_certification_canary.yml").exists()

    workflow = source(".github/workflows/db-sync-to-pro.yml")
    assert "workflow_dispatch:" in workflow
    assert "h2-expand-compat)" in workflow
    assert 'test "${GITHUB_REF_NAME}" = "certificacion"' in workflow
    assert "h2-contract-public-reader|h2-contract-legacy-cohort|h2-rollback-public-reader-contract)" in workflow
    assert 'test "${GITHUB_REF_NAME}" = "main"' in workflow
    assert "schedule:" not in workflow


def test_h2_main_gate_replaces_f99_runtime_workflow_checks() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "h2-main-production-expand-gate:" in workflow
    assert "H2 Main Production Expand Gate" in workflow
    assert "h2_main_production_expand_evidence.json" in workflow
    assert "api.github.com/repos/${REPOSITORY}/actions/runs/${run_id}/artifacts" in workflow
    assert "supabase-security-advisors.json" in workflow
    assert "supabase-performance-advisors.json" in workflow


def test_certification_canary_helpers_still_mask_private_identifiers() -> None:
    manifest = source("scripts/core/certification_canary_manifest.py")
    assert manifest.index("_mask_github_value(institution_id)") < manifest.index(
        "handle.write(f\"CANARY_INSTITUTION_ID="
    )
    assert manifest.index("_mask_github_value(institution[\"slug\"])") < manifest.index(
        "_write_github_env(args.github_env"
    )


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
    assert "F9.9 certification" in harvester
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
    state = source("scripts/core/certification_canary_state.py")

    assert '"institution_slug": "redacted"' in manifest
    assert '"institution_name": "redacted"' in manifest
    assert '"institution_slug": "redacted"' in state
    assert '"institution_name": "redacted"' in state
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
    assert "_mask_github_value(institution_id)" in manifest
    assert "_mask_github_value(institution_id)" in state
    assert "Expected exactly one institution for slug" not in manifest
    assert "Expected exactly one institution for slug" not in state


def test_canary_state_private_snapshot_and_sanitized_summary_contract() -> None:
    state = source("scripts/core/certification_canary_state.py")

    assert "STATE_SCHEMA" in state
    assert "SUMMARY_SCHEMA" in state
    assert "select_all_pipeline" in state
    assert "select_all_service" in state
    assert "patch_exact_one_raise" in state
    assert "expect_noop" in state
    assert "private_digest" not in state
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
    assert "_mask_github_value(institution_id)" in state
    assert '"institution_slug": "redacted"' in state
    assert '"institution_name": "redacted"' in state
    assert 'if os.getenv("GITHUB_ACTIONS") != "true"' not in state.split("def _ensure_certification_supabase_target():", 1)[1].split("def _canonical", 1)[0]
    assert 'parsed.scheme != "https"' in state
    assert "parsed.username" in state
    assert "port not in (None, 443)" in state
    assert "Canary pre-state contains dirty canary leftovers:" not in state
    assert "Duplicate row id in canary state: {row_id}" not in state
    assert "extra row from {table}: {row_id}" not in state


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

    assert "h2-main-production-expand-gate:" in workflow
    assert "h2_main_production_expand_evidence.json" in workflow
    db_sync = source(".github/workflows/db-sync-to-pro.yml")
    assert "scripts/maintenance/h2_pro_preflight_report.py" in db_sync
    assert "scripts/maintenance/db_migrate.py" in db_sync
    assert "scripts/maintenance/check_db_parity.py" in db_sync


def test_security_audit_freezes_selective_certification_identity() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "h2-main-production-expand-gate:" in workflow
    assert "github.event.pull_request.base.ref == 'main'" in workflow
    assert "PR_HEAD_SHA" in workflow
    assert "expected_artifact" in workflow
    assert "artifact != committed" in workflow
    assert "evidence_candidate" in workflow
    assert "allowed_after_candidate" in workflow


def test_security_audit_accepts_certification_canary_redaction_boundary() -> None:
    workflow = source(".github/workflows/security-audit.yml")

    assert "H2 Main Production Expand Gate" in workflow
    assert "archive_download_url" in workflow
    assert "DDL-[A-Z0-9][A-Z0-9_-]{3,}\\.md" in workflow
    assert "h2_main_production_expand_evidence.json" in workflow
    assert "supabase-security-advisors.json" in workflow
    assert "supabase-performance-advisors.json" in workflow
