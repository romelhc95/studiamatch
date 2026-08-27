from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_db_migrate_requires_closed_manifest_for_pro() -> None:
    text = read("scripts/maintenance/db_migrate.py")

    assert "PRO_MIGRATION_MANIFESTS" in text
    assert '"h2-expand-compat"' in text
    assert '"20260827_h2_pro_enable_legacy_cohort_rls"' in text
    assert '"h2-contract-public-reader"' in text
    assert '"h2-contract-legacy-cohort"' in text
    assert '"h2-rollback-public-reader-contract"' in text
    assert 'parser.error("--manifest es obligatorio para Pro")' in text
    assert "--only no esta permitido con --env pro" in text
    assert "resolve_migration_files(requested_migrations)" in text
    assert "os.path.join(MIGRATIONS_DIR, f\"{name}.sql\")" in text
    assert "raise RuntimeError(f\"No se pudo leer supabase_migrations" in text
    assert "raise RuntimeError(f\"No se pudo registrar migration" in text
    assert "assert_h2_expand_preapply_guard" in text
    assert "build_atomic_migration_sql" in text
    assert "H2 Pro pre-apply public visibility drift" in text
    assert "Dry-run Pro en CI requiere ledger remoto accesible" in text
    assert "sha256:<64 hex chars>" in text
    assert "F10_8_ALLOWED_PRO_ONLY_MIGRATIONS" not in text


def test_db_sync_workflow_uses_manifest_and_authorization_gate() -> None:
    text = read(".github/workflows/db-sync-to-pro.yml")

    assert "migration_manifest:" in text
    assert "h2-expand-compat" in text
    assert "h2-contract-public-reader" in text
    assert "h2-contract-legacy-cohort" in text
    assert "h2-rollback-public-reader-contract" in text
    assert "h2_expected_eligible_count:" in text
    assert "h2_expected_cohort_digest:" in text
    assert "h2_advisors_reviewed:" in text
    assert "H2 expected eligible count: ${{ inputs.h2_expected_eligible_count }}" in text
    assert "H2 expected cohort digest: ${{ inputs.h2_expected_cohort_digest }}" in text
    assert 'db_migrate.py --env pro --dry-run --manifest "$MIGRATION_MANIFEST"' in text
    assert 'db_migrate.py --env pro --manifest "$MIGRATION_MANIFEST"' in text
    assert "Authorized manifest: ${{ inputs.migration_manifest }}" in text
    assert "payload_sha:" in text
    assert "Authorized payload SHA: ${PAYLOAD_SHA}" in text
    assert 'test "$changed_after_payload" = "$auth_file"' in text
    assert "Authorized non-auth digest SHA256" in text
    assert "non-auth-digest" in text
    assert "h2-production-expand-verify-${{ needs.detect-db-changes.outputs.candidate_sha }}" in text
    assert "h2-main-production-expand-evidence-v1" in text
    assert "h2_advisors_result" in text
    assert "SUPABASE_ACCESS_TOKEN" in text
    assert '"critical", "high", "error"' in text
    assert "supabase-security-advisors.json" in text
    assert "supabase-performance-advisors.json" in text
    assert "BACKUP_PITR_RUNTIME_GATE_REQUIRED" in text
    assert "production_control_preflight.sh DB-SYNC --enforce" in text


def test_check_db_parity_has_h2_manifest_specific_contracts() -> None:
    text = read("scripts/maintenance/check_db_parity.py")

    assert "H2_MANIFEST_MIGRATIONS" in text
    assert "check_h2_manifest_contract" in text
    assert "h2_verify_expand_compat" in text
    assert "H2_EXPECTED_COHORT_DIGEST es obligatorio" in text
    assert "p_expected_cohort_digest" in text
    assert "rest_select_all" in text
    assert "courses_public_effective digest mismatch" in text
    assert "courses_public_effective?select=id,slug,name,url" in text
    assert "for field in" in text
    assert "courses_public_effective expone campo editorial privado" in text
    assert "institution_site_profiles.exclusion_patterns esta expuesto publicamente" in text
    assert "RPC {function_name} no fue denegada con publishable key" in text
    assert "h2_update_course_quality" in text
    assert "h2_update_course_quality_batch" in text
    assert "debe preservar lectura publica legacy de courses" in text
    assert "h2 contract debe retirar lectura publica directa de courses" in text
    assert "legacy_public_required" in text


def test_security_audit_runs_h2_pro_harness_and_allows_only_pro_remediation_paths() -> None:
    text = read(".github/workflows/security-audit.yml")

    assert "20260827_h2_pro_(expand_schema_compat|seed_editorial_field_definitions|backfill_editorial_state|capture_legacy_cohort|enable_legacy_cohort_rls|contract_public_reader|contract_legacy_cohort|rollback_public_reader_contract)" in text
    assert "maintenance/(h2_(backfill_editorial_state|scan_unauthorized_writers)|h2_pro_preflight_report|db_migrate|check_db_parity)" in text
    assert "tests/sql/h2_pro_pg17_harness.sql" in text
    assert "tests/test_h2_pro_migration_controls.py" in text
    assert "psql -h localhost -U postgres -v ON_ERROR_STOP=1 -f tests/sql/h2_pro_pg17_harness.sql" in text
    assert "H2 Main Production Expand Gate" in text
    assert "h2_main_production_expand_evidence.json" in text
    assert "actions: read" in text
    assert "missing successful DB Sync jobs" in text
    assert "missing H2 production expand verify artifact" in text
    assert "PR_HEAD_SHA" in text
    assert "git merge-base --is-ancestor \"$evidence_candidate\" \"$PR_HEAD_SHA\"" in text
    assert "change after verified H2 candidate is not allowed" in text
    assert "h2 advisors must be reviewed before main" in text
    assert "committed H2 expand evidence differs from DB Sync artifact" in text


def test_h2_pro_preflight_report_outputs_jit_digest_contract() -> None:
    text = read("scripts/maintenance/h2_pro_preflight_report.py")
    workflow = read(".github/workflows/db-sync-to-pro.yml")

    assert "h2-pro-preflight-report-v1" in text
    assert "ordered_eligible_ids_digest" in text
    assert "public_visible_count" in text
    assert "missing_from_public_count" in text
    assert "Duplicados institution_id+slug bloquean" in text
    assert "Objetos H2 Pro ya existen" in text
    assert "H2_ALLOW_CRAWLER_EXCLUSIONS_DRIFT" in text
    assert "table_has_rows" in text
    assert "crawler_exclusions_empty" in text
    assert "duplicate_institution_slug_groups" in text
    assert "H2 expected eligible count: " in text
    assert "H2 expected cohort digest: " in text
    assert "h2_pro_preflight_report.py | tee h2-pro-preflight-report.json" in workflow
    assert "Upload H2 Pro preflight report" in workflow


def test_h2_pro_expand_reconciles_empty_legacy_crawler_exclusions_drift() -> None:
    migration = read("db/migrations/20260827_h2_pro_expand_schema_compat.sql")

    assert "DROP TABLE IF EXISTS public.crawler_exclusions;" in migration
    assert "canonical exclusions live in institution_site_profiles" in migration
