from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def job_section(workflow: str, job_id: str) -> str:
    pattern = rf"^  {re.escape(job_id)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)"
    match = re.search(pattern, workflow, re.M | re.S)
    assert match, f"job {job_id} not found"
    return match.group(0)


WORKFLOW = source(".github/workflows/db-sync-to-pro.yml")
DB_MIGRATE = source("scripts/maintenance/db_migrate.py")
F97_WORKFLOW = source(".github/workflows/f9-7-contract.yml")
SECURITY_WORKFLOW = source(".github/workflows/security-audit.yml")


def test_push_main_without_db_changes_skips_production_jobs() -> None:
    detect = job_section(WORKFLOW, "detect-db-changes")
    preflight = job_section(WORKFLOW, "db-contract-preflight")
    report = job_section(WORKFLOW, "report")
    apply = job_section(WORKFLOW, "apply")
    verify = job_section(WORKFLOW, "verify")

    assert "github.event.before" in detect
    assert "github.sha" in detect
    assert 'git diff --quiet "$BEFORE_SHA" "$CANDIDATE_SHA" -- db/' in detect
    assert "db_changed=false" in detect
    assert "db_changed=true" in detect
    assert "0000000000000000000000000000000000000000" in detect
    assert "git merge-base --is-ancestor" in detect

    for section in (preflight, report):
        assert "needs.detect-db-changes.outputs.db_changed == 'true'" in section
    assert "needs.db-contract-preflight.result == 'success'" in report

    assert "github.event_name == 'workflow_dispatch'" in apply
    assert "github.event_name == 'workflow_dispatch'" in verify


def test_detector_and_preflight_do_not_load_production_or_secrets() -> None:
    detect = job_section(WORKFLOW, "detect-db-changes")
    preflight = job_section(WORKFLOW, "db-contract-preflight")

    for section in (detect, preflight):
        assert "environment:" not in section
        assert "Production" not in section
        assert "secrets." not in section
        assert "SUPABASE_URL" not in section
        assert "NEXT_SUPABASE_SECRET_KEY" not in section
        assert "persist-credentials: false" in section


def test_preflight_validates_manifest_before_secret_bearing_report() -> None:
    preflight = job_section(WORKFLOW, "db-contract-preflight")
    report = job_section(WORKFLOW, "report")

    assert WORKFLOW.index("  db-contract-preflight:") < WORKFLOW.index("  report:")
    assert "needs: detect-db-changes" in preflight
    assert 'test -f "db/migrations/${F10_8_ONLY_MIGRATION}.sql"' in preflight
    assert "--validate-only" not in preflight
    assert "--manifest" not in preflight
    assert "F10.8 migration is missing" in preflight
    assert "db_migrate.py must constrain Pro --only migrations" in preflight
    assert "needs: [detect-db-changes, db-contract-preflight]" in report
    assert "environment:" in report
    assert "name: Production" in report
    assert "secrets.SUPABASE_URL" in report
    assert "secrets.NEXT_SUPABASE_SECRET_KEY" in report
    assert "NEXT_SUPABASE_PUBLISHABLE_KEY" not in report


def test_workflow_dispatch_report_preserves_dry_run_only_path() -> None:
    detect = job_section(WORKFLOW, "detect-db-changes")
    report = job_section(WORKFLOW, "report")

    assert 'if [ "$EVENT_NAME" = "workflow_dispatch" ]; then' in detect
    assert "DB Sync manual dispatch requires report/preflight path" in detect
    assert '--dry-run --only "$F10_8_ONLY_MIGRATION"' in report
    assert "--manifest" not in report
    assert "Confirm report-only mode" in report
    assert "Apply migrations to Pro" not in report
    assert "printf '%s' \"$count\" | grep -Eq '^[0-9]+$'" in report


def test_workflow_dispatch_apply_remains_manual_and_gated() -> None:
    apply = job_section(WORKFLOW, "apply")
    verify = job_section(WORKFLOW, "verify")
    defer = job_section(WORKFLOW, "defer-fg2")

    assert "needs: [detect-db-changes, report]" in apply
    assert "github.event_name == 'workflow_dispatch'" in apply
    assert "inputs.operation == 'apply'" in apply
    assert "inputs.apply_authorized" in apply
    assert "inputs.backup_pitr_verified" in apply
    assert "inputs.ddl_authorization_id != ''" in apply
    assert "fromJSON(needs.report.outputs.pending_count) > 0" in apply
    assert ".context/operaciones/ddl_authorizations/${DDL_AUTHORIZATION_ID}.md" in apply
    assert "Status: APPROVED_FOR_PRODUCTION_DDL" in apply
    assert "Authorized base SHA:" in apply
    assert "Authorized non-auth digest SHA256:" in apply
    assert "EXPECTED_NON_AUTH_DIGEST" in apply
    assert "non-auth-digest:" in apply
    assert "BACKUP_PITR_RUNTIME_GATE_REQUIRED" in apply
    assert "APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR" in apply
    assert "git merge-base --is-ancestor \"$auth_base_sha\" \"$CANDIDATE_SHA\"" in apply
    assert 'grep -F "$CANDIDATE_SHA"' not in apply
    assert "production_control_preflight.sh DB-SYNC --enforce" in apply
    assert "ref: ${{ needs.detect-db-changes.outputs.candidate_sha }}" in apply
    assert '--only "$F10_8_ONLY_MIGRATION"' in apply
    assert "--manifest" not in apply

    assert "needs: [detect-db-changes, report, apply]" in verify
    assert "needs.report.result == 'success'" in verify
    assert "needs.apply.result == 'success'" in verify
    assert "needs.verify.result == 'success'" in defer


def test_untrusted_inputs_are_not_interpolated_directly_into_shell() -> None:
    shell_blocks = re.findall(r"run: \|\n((?:          .+\n)+)", WORKFLOW)
    assert shell_blocks, "expected shell blocks"
    for block in shell_blocks:
        assert "${{ inputs.candidate_sha }}" not in block
        assert "${{ github.event.before }}" not in block
        assert "${{ github.sha }}" not in block


def test_no_prohibited_surfaces_are_introduced() -> None:
    assert "schedule:" not in WORKFLOW
    assert "production_canary" not in WORKFLOW
    assert "workflow_dispatch" in WORKFLOW
    assert "supabase/functions" not in WORKFLOW


def test_db_sync_is_limited_to_f10_8_single_forward_migration() -> None:
    assert "MIGRATION_MANIFEST" not in WORKFLOW
    assert "F10_8_ONLY_MIGRATION: 20260808_fase10_8_atomic_cleansing_provenance" in WORKFLOW
    assert WORKFLOW.count("F10_8_ONLY_MIGRATION") >= 4
    assert "db/migrations/${F10_8_ONLY_MIGRATION}.sql" in WORKFLOW
    assert "--validate-only" not in WORKFLOW
    assert "--manifest" not in WORKFLOW
    assert "F10_8_ALLOWED_PRO_ONLY_MIGRATIONS" in DB_MIGRATE
    assert "20260808_fase10_8_atomic_cleansing_provenance" in DB_MIGRATE
    assert 'if args.env == "pro":' in DB_MIGRATE
    assert "not args.manifest" not in DB_MIGRATE
    assert "--manifest es obligatorio para Pro salvo la remediacion" in DB_MIGRATE


def test_atomic_cleansing_provenance_migration_contract() -> None:
    migration = source("db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql")
    restore = source("db/restore_full_schema.sql")

    for sql in (migration, restore):
        assert "CREATE OR REPLACE FUNCTION public.atomic_cleansing_promote" in sql
        assert "RETURNS SETOF public.cleansed_programs" in sql
        assert "SET search_path = pg_catalog" in sql
        assert "INSERT INTO public.cleansed_programs AS target" in sql
        assert "COALESCE(target.metadata, '{}'::jsonb)" in sql
        assert "|| COALESCE(EXCLUDED.metadata, '{}'::jsonb)" in sql
        assert "status IN ('pending', 'processing')" in sql
        assert "REVOKE ALL ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) FROM PUBLIC" in sql
        assert "REVOKE ALL ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) FROM anon" in sql
        assert "REVOKE ALL ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) FROM authenticated" in sql
        assert "GRANT EXECUTE ON FUNCTION public.atomic_cleansing_promote(uuid[], jsonb) TO service_role" in sql


def test_f10_8_ddl_authorization_record_is_runtime_gated() -> None:
    authorization = source(
        ".context/operaciones/ddl_authorizations/DDL-F10_8_ATOMIC_CLEANSING_PROVENANCE_PRO.md"
    )

    assert "Status: APPROVED_FOR_PRODUCTION_DDL" in authorization
    assert "Authorized migration: 20260808_fase10_8_atomic_cleansing_provenance" in authorization
    assert "Authorized base SHA: 1885806f0d9f189600d410d353fcf13fb8dd4676" in authorization
    assert "Authorized non-auth digest SHA256: sha256:" in authorization
    assert "sha256:0000000000000000000000000000000000000000000000000000000000000000" not in authorization
    assert "Backup/PITR gate: BACKUP_PITR_RUNTIME_GATE_REQUIRED" in authorization
    assert "APPLY_REQUIRES_WORKFLOW_DISPATCH_PRODUCTION_ENVIRONMENT_APPROVAL_AND_RUNTIME_BACKUP_PITR" in authorization
    assert "31243797695=SUCCESS_REPORT_ONLY" in authorization
    assert "no aplico DDL" in authorization
    assert "NEXT_SUPABASE_SECRET_KEY" not in authorization


def test_postgres_regression_script_is_local_only_guarded() -> None:
    script = source("tests/sql/run_fase10_8_atomic_cleansing_postgres.sh")
    assert "ALLOW_DESTRUCTIVE_LOCAL_TEST_DB" in script
    assert "studiamatch_f108" in script
    assert "localhost" in script
    assert "DROP SCHEMA IF EXISTS public CASCADE" in script


def test_f9_7_boundary_allows_exact_f10_8_db_remediation_only() -> None:
    allowed = F97_WORKFLOW.split("allowed_statuses = {", 1)[1].split("allowed = set(allowed_statuses)", 1)[0]
    trigger_paths = F97_WORKFLOW.split("pull_request:", 1)[1].split("push:", 1)[0]
    assert "'db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql'" in trigger_paths
    assert "'db/restore_full_schema.sql'" in trigger_paths
    assert "'db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql': {'A'}" in allowed
    assert "'db/restore_full_schema.sql': {'M'}" in allowed
    assert "'scripts/maintenance/db_migrate.py': {'M'}" in allowed
    assert "denied_prefixes = ('db/', 'supabase/', 'web/', 'scripts/maintenance/')" in F97_WORKFLOW
    assert "and not any(p in allowed for p in paths_to_check)" in F97_WORKFLOW


def test_security_audit_supports_f10_8_cleansing_provenance_certification_baseline() -> None:
    assert "F108_CLEANSING_PROVENANCE_CERT_BASELINE: 12e270166c26d4bc93c1c609c23045a6b6720d96" in SECURITY_WORKFLOW
    assert "github.event.pull_request.base.sha == '12e270166c26d4bc93c1c609c23045a6b6720d96'" in SECURITY_WORKFLOW
    assert "github.event.before == '12e270166c26d4bc93c1c609c23045a6b6720d96'" in SECURITY_WORKFLOW
    assert '"db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql": ("A", "100644")' in SECURITY_WORKFLOW
    assert '"scripts/maintenance/db_migrate.py": ("M", "100644")' in SECURITY_WORKFLOW
    assert '"tests/sql/run_fase10_8_atomic_cleansing_postgres.sh": ("A", "100755")' in SECURITY_WORKFLOW
    assert "F108_CERT_REQUIRED" in SECURITY_WORKFLOW


if __name__ == "__main__":
    for name, value in sorted(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("F10.8 DB Sync contract assertions passed")
