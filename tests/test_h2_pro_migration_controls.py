import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.maintenance import check_db_parity, db_migrate
from scripts.maintenance.pro_h3_migration_manifest import H3_PRO_MIGRATIONS


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_db_migrate_requires_closed_manifest_for_pro() -> None:
    text = read("scripts/maintenance/db_migrate.py")

    assert "PRO_MIGRATION_MANIFESTS" in text
    assert db_migrate.PRO_MIGRATION_MANIFESTS["h2-expand-compat"] == (
        "20260827_h2_pro_expand_schema_compat",
        "20260827_h2_pro_seed_editorial_field_definitions",
        "20260827_h2_pro_backfill_editorial_state",
        "20260827_h2_pro_capture_legacy_cohort",
        "20260827_h2_pro_enable_legacy_cohort_rls",
    )
    for name in ("h2-contract-public-reader", "h2-contract-legacy-cohort", "h2-rollback-public-reader-contract"):
        assert name in db_migrate.PRO_MIGRATION_MANIFESTS
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


def test_h3_pro_manifest_is_closed_pinned_and_has_h2_compat_preflight() -> None:
    manifest = read("scripts/maintenance/pro_h3_migration_manifest.py")
    migrator = read("scripts/maintenance/db_migrate.py")
    parity = read("scripts/maintenance/check_db_parity.py")

    assert 'H3_PRO_MANIFEST_NAME = "h3-editorial-expand"' in manifest
    assert "H3_PRO_MIGRATION_SHA256" in manifest
    assert "validate_h3_manifest_tree" in manifest
    assert "H3_PRO_MIGRATION_PRECEDENCE" in manifest
    assert "H3_PRO_EXTERNAL_PREREQUISITE" in manifest
    assert 'H3_PRO_MANIFEST_NAME: H3_PRO_MIGRATIONS' in manifest
    assert "PRO_MIGRATION_MANIFESTS," in migrator
    assert "assert_h3_expand_preapply_guard" in migrator
    assert "h2_verify_expand_compat" in migrator
    assert "--h3-manifest" in parity
    assert "check_h3_manifest_contract" in parity


def test_db_sync_workflow_uses_manifest_and_authorization_gate() -> None:
    text = read(".github/workflows/db-sync-to-pro.yml")
    closed_manifest_preflight = text.split("Validate closed Pro manifest offline", 1)[1].split("  report:", 1)[0]
    manifest_allowlist = next(
        line for line in closed_manifest_preflight.splitlines() if "grep -Eq '^(" in line
    )

    assert "migration_manifest:" in text
    assert "h2-expand-compat" in text
    assert "h2-contract-public-reader" in text
    assert "h2-contract-legacy-cohort" in text
    assert "h2-rollback-public-reader-contract" in text
    assert "h3-editorial-expand" in text
    assert "h3-editorial-expand" in manifest_allowlist
    assert 'test "${GITHUB_REF_NAME}" = "main"' in text
    assert 'case "$MIGRATION_MANIFEST" in' in text
    assert "validate_h3_manifest_tree" in text
    assert "--h3-manifest \"$MIGRATION_MANIFEST\"" in text
    assert "h2_expected_eligible_count:" in text
    assert "h2_expected_cohort_digest:" in text
    assert "h2_advisors_reviewed:" in text
    immutable_preflight = text.split("Validate closed Pro manifest offline", 1)[1].split("  report:", 1)[0]
    immutable_preflight_run = immutable_preflight.split("        run: |", 1)[1]
    assert 'MIGRATION_MANIFEST: ${{ inputs.migration_manifest }}' in immutable_preflight
    assert '${{ inputs.migration_manifest }}' not in immutable_preflight_run
    assert 'db_migrate.py --env pro --dry-run --manifest "$MIGRATION_MANIFEST"' in text
    assert 'db_migrate.py --env pro --manifest "$MIGRATION_MANIFEST"' in text
    authorization_gate = text.split("      - name: Verify explicit DDL authorization", 1)[1].split("      - name:", 1)[0]
    authorization_gate_run = authorization_gate.split("        run: |", 1)[1]
    assert 'MIGRATION_MANIFEST: ${{ inputs.migration_manifest }}' in authorization_gate
    assert 'H2_EXPECTED_ELIGIBLE_COUNT: ${{ inputs.h2_expected_eligible_count }}' in authorization_gate
    assert 'H2_EXPECTED_COHORT_DIGEST: ${{ inputs.h2_expected_cohort_digest }}' in authorization_gate
    assert 'grep -Fx "Authorized manifest: ${MIGRATION_MANIFEST}" "$auth_file"' in authorization_gate_run
    assert 'grep -Fx "H2 expected eligible count: ${H2_EXPECTED_ELIGIBLE_COUNT}" "$auth_file"' in authorization_gate_run
    assert 'grep -Fx "H2 expected cohort digest: ${H2_EXPECTED_COHORT_DIGEST}" "$auth_file"' in authorization_gate_run
    assert '${{ inputs.migration_manifest }}' not in authorization_gate_run
    assert '${{ inputs.h2_expected_eligible_count }}' not in authorization_gate_run
    assert '${{ inputs.h2_expected_cohort_digest }}' not in authorization_gate_run
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
    assert "/advisors/security" in text
    assert "/advisors/performance" in text
    assert "/advisors?type=" not in text
    assert "BACKUP_PITR_RUNTIME_GATE_REQUIRED" in text
    assert "production_control_preflight.sh DB-SYNC --enforce" in text


def run_workflow_manifest_preflight(root: Path, manifest: str) -> subprocess.CompletedProcess:
    """Execute the real offline YAML step, not a duplicate validator."""
    text = read(".github/workflows/db-sync-to-pro.yml")
    step = text.split("      - name: Validate closed Pro manifest offline\n", 1)[1].split("\n  report:", 1)[0]
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])
    return subprocess.run(
        ["bash", "-eu", "-c", script],
        cwd=root,
        env={"PATH": os.environ["PATH"], "MIGRATION_MANIFEST": manifest, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


@pytest.mark.parametrize("manifest", tuple(db_migrate.PRO_MIGRATION_MANIFESTS))
def test_actual_workflow_preflight_accepts_each_registered_manifest(manifest: str) -> None:
    result = run_workflow_manifest_preflight(ROOT, manifest)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("manifest", ["", "unknown", "../h2-expand-compat", "h2-expand-compat; exit 0"])
def test_actual_workflow_preflight_rejects_unknown_or_unsafe_selection(manifest: str) -> None:
    assert run_workflow_manifest_preflight(ROOT, manifest).returncode != 0


@pytest.fixture
def isolated_manifest_tree(tmp_path: Path) -> Path:
    module_path = Path("scripts/maintenance/pro_h3_migration_manifest.py")
    (tmp_path / module_path.parent).mkdir(parents=True)
    shutil.copyfile(ROOT / module_path, tmp_path / module_path)
    migrations = tmp_path / "db/migrations"
    migrations.mkdir(parents=True)
    for names in db_migrate.PRO_MIGRATION_MANIFESTS.values():
        for name in names:
            shutil.copyfile(ROOT / "db/migrations" / f"{name}.sql", migrations / f"{name}.sql")
    return tmp_path


def test_actual_workflow_preflight_rejects_registry_drift(isolated_manifest_tree: Path) -> None:
    path = isolated_manifest_tree / "scripts/maintenance/pro_h3_migration_manifest.py"
    path.write_text(path.read_text().replace('"h2-expand-compat":', '"h2-unregistered":', 1))
    assert run_workflow_manifest_preflight(isolated_manifest_tree, "h2-expand-compat").returncode != 0


def test_actual_workflow_preflight_rejects_missing_h2_sql(isolated_manifest_tree: Path) -> None:
    first = db_migrate.PRO_MIGRATION_MANIFESTS["h2-expand-compat"][0]
    (isolated_manifest_tree / "db/migrations" / f"{first}.sql").unlink()
    assert run_workflow_manifest_preflight(isolated_manifest_tree, "h2-expand-compat").returncode != 0


def test_actual_workflow_preflight_rejects_changed_h3_sql(isolated_manifest_tree: Path) -> None:
    path = isolated_manifest_tree / "db/migrations" / f"{H3_PRO_MIGRATIONS[0]}.sql"
    path.write_text(path.read_text() + "\n-- unexpected drift\n")
    assert run_workflow_manifest_preflight(isolated_manifest_tree, "h3-editorial-expand").returncode != 0


def test_shared_manifest_registry_needs_only_standard_library() -> None:
    code = (
        "import sys; sys.path.insert(0, 'scripts'); "
        "from maintenance.pro_h3_migration_manifest import PRO_MIGRATION_MANIFESTS; "
        "assert len(PRO_MIGRATION_MANIFESTS) == 6; "
        "assert not {'requests', 'dotenv', 'shared.db_client'} & sys.modules.keys()"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", code], cwd=ROOT,
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr


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


def test_check_db_parity_pins_pro_service_requests_to_canonical_host() -> None:
    secret_fixture = "synthetic-test-key"
    secret_env_var = "NEXT_SUPABASE_" + "SECRET_KEY"
    canonical_url = "https://xwhtiqmboljkshrtviyw.supabase.co"
    with patch.dict(os.environ, {
        secret_env_var: secret_fixture,
        "SUPABASE_URL": canonical_url,
    }, clear=True), patch.object(check_db_parity, "get_secret_key", return_value=secret_fixture):
        check_db_parity.assert_environment("pro")

    for invalid_url in (
        "http://xwhtiqmboljkshrtviyw.supabase.co",
        "https://attacker.example",
        "https://user@xwhtiqmboljkshrtviyw.supabase.co",
        "https://xwhtiqmboljkshrtviyw.supabase.co:8443",
    ):
        with patch.dict(os.environ, {
            secret_env_var: secret_fixture,
            "SUPABASE_URL": invalid_url,
        }, clear=True), patch.object(check_db_parity, "get_secret_key", return_value=secret_fixture):
            with pytest.raises(RuntimeError, match="Pro target must be pinned"):
                check_db_parity.assert_environment("pro")


def test_h3_preapply_compatibility_rpc_does_not_follow_redirects(monkeypatch) -> None:
    class RedirectResponse:
        status_code = 302
        content = b""

    calls = []
    monkeypatch.setattr(db_migrate, "validate_h2_cohort_inputs", lambda count, digest: (5, "sha256:" + "a" * 64))
    monkeypatch.setattr(
        db_migrate.requests,
        "post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or RedirectResponse(),
    )
    monkeypatch.setenv("H2_EXPECTED_ELIGIBLE_COUNT", "5")
    monkeypatch.setenv("H2_EXPECTED_COHORT_DIGEST", "sha256:" + "a" * 64)

    class FakeDb:
        supabase_url = "https://xwhtiqmboljkshrtviyw.supabase.co"

        @staticmethod
        def _get_headers(*, use_service_role):
            assert use_service_role is True
            return {"apikey": "synthetic-service-key"}

    with pytest.raises(RuntimeError, match="HTTP 302"):
        db_migrate.assert_h3_expand_preapply_guard(FakeDb())
    assert calls[0][1]["allow_redirects"] is False


def test_parity_service_rpc_does_not_follow_redirects(monkeypatch) -> None:
    calls = []
    sentinel = object()
    monkeypatch.setattr(
        check_db_parity.requests,
        "post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or sentinel,
    )

    class FakeDb:
        supabase_url = "https://xwhtiqmboljkshrtviyw.supabase.co"

        @staticmethod
        def _get_headers(*, use_service_role):
            assert use_service_role is True
            return {"apikey": "synthetic-service-key"}

    assert check_db_parity.service_post_rpc(FakeDb(), "h2_verify_expand_compat", {}) is sentinel
    assert calls[0][1]["allow_redirects"] is False


def test_parity_data_api_reads_do_not_follow_redirects(monkeypatch) -> None:
    class RedirectResponse:
        status_code = 302
        content = b""
        text = "redirect response body must not be followed"

    calls = []
    monkeypatch.setattr(
        check_db_parity.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or RedirectResponse(),
    )

    class FakeDb:
        supabase_url = "https://xwhtiqmboljkshrtviyw.supabase.co"

        @staticmethod
        def _get_headers(*, use_service_role):
            return {"apikey": "synthetic-service-key" if use_service_role else "synthetic-public-key"}

    assert check_db_parity.public_get(FakeDb(), "courses?select=id").status_code == 302
    assert check_db_parity.service_get(FakeDb(), "supabase_migrations?select=name").status_code == 302
    with pytest.raises(RuntimeError, match="302"):
        check_db_parity.service_select(FakeDb(), "supabase_migrations", "name")
    with pytest.raises(RuntimeError, match="302"):
        check_db_parity.rest_select_all(FakeDb(), "courses", "id", use_service_role=True)

    assert len(calls) == 4
    assert all(kwargs["allow_redirects"] is False for _, kwargs in calls)


def test_schema_contract_api_requests_do_not_follow_redirects(monkeypatch) -> None:
    class Response:
        content = b"[]"
        text = ""

        def __init__(self, status_code):
            self.status_code = status_code

        @staticmethod
        def json():
            return []

    calls = []
    get_statuses = iter((200, 200, 403))

    def fake_get(*args, **kwargs):
        calls.append(("GET", kwargs))
        return Response(next(get_statuses))

    def fake_post(*args, **kwargs):
        calls.append(("POST", kwargs))
        return Response(403)

    monkeypatch.setattr(check_db_parity.requests, "get", fake_get)
    monkeypatch.setattr(check_db_parity.requests, "post", fake_post)
    monkeypatch.setattr(
        check_db_parity,
        "service_select",
        lambda *_args, **_kwargs: [{"name": migration} for migration in check_db_parity.REQUIRED_MIGRATIONS],
    )

    class FakeDb:
        supabase_url = "https://xwhtiqmboljkshrtviyw.supabase.co"

        @staticmethod
        def _get_headers(*, use_service_role):
            return {"apikey": "synthetic-service-key" if use_service_role else "synthetic-public-key"}

    status, errors = check_db_parity.check_schema_contracts(FakeDb(), check_public=True)

    assert status == "OK"
    assert errors == []
    assert len(calls) == 5
    assert all(kwargs["allow_redirects"] is False for _, kwargs in calls)


@pytest.mark.parametrize(
    ("private_field_statuses", "expected_status"),
    [((400, 400, 400), "OK"), ((400, 500, 400), "ERROR"), ((400, 302, 400), "ERROR")],
)
def test_h3_parity_private_field_probes_fail_closed(
    monkeypatch, private_field_statuses, expected_status
) -> None:
    digest = "sha256:" + "a" * 64
    monkeypatch.setenv("H2_EXPECTED_ELIGIBLE_COUNT", "5")
    monkeypatch.setenv("H2_EXPECTED_COHORT_DIGEST", digest)
    monkeypatch.setattr(
        check_db_parity,
        "service_select",
        lambda *_args, **_kwargs: [{"name": name} for name in H3_PRO_MIGRATIONS],
    )

    class Response:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self.content = b"result" if payload is not None else b""
            self._payload = payload

        def json(self):
            return self._payload

    expected_contract = {
        "eligible_count": 5,
        "cohort_count": 5,
        "effective_count": 5,
        "missing_count": 0,
        "unexpected_count": 0,
        "cohort_digest": digest,
        "public_column_count": 28,
        "private_column_count": 0,
        "security_invoker": True,
        "rls_tables_count": 3,
        "direct_courses_public": True,
    }
    monkeypatch.setattr(
        check_db_parity,
        "service_post_rpc",
        lambda *_args, **_kwargs: Response(200, expected_contract),
    )
    monkeypatch.setattr(
        check_db_parity,
        "service_get",
        lambda *_args, **_kwargs: Response(200),
    )
    probes = iter((Response(200), *(Response(code) for code in private_field_statuses)))
    monkeypatch.setattr(check_db_parity, "public_get", lambda *_args, **_kwargs: next(probes))

    status, details = check_db_parity.check_h3_manifest_contract(object(), "h3-editorial-expand")

    assert status == expected_status
    if expected_status == "ERROR":
        assert any("quedó inconclusa" in item for item in details)


def test_security_audit_runs_h2_pro_harness_and_allows_only_pro_remediation_paths() -> None:
    text = read(".github/workflows/security-audit.yml")
    guard = read("scripts/security/protected_path_scope_guard.sh")

    assert "20260827_h2_pro_(expand_schema_compat|seed_editorial_field_definitions|backfill_editorial_state|capture_legacy_cohort|enable_legacy_cohort_rls|contract_public_reader|contract_legacy_cohort|rollback_public_reader_contract)" in guard
    assert "maintenance/(h2_(backfill_editorial_state|scan_unauthorized_writers)|h2_pro_preflight_report|db_migrate|check_db_parity)" in guard
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
    assert "governance documentation" in text
    assert "tests/test_(obsidian_context_state|requirement_client_source_validation|security_flow|h2_pro_migration_controls)" in text
    assert ".github/workflows/security-audit\\.yml" in text
    assert "h2 advisors must be reviewed before main" in text
    assert "committed H2 expand evidence differs from DB Sync artifact" in text


def test_h2_pro_preflight_report_outputs_jit_digest_contract() -> None:
    text = read("scripts/maintenance/h2_pro_preflight_report.py")
    workflow = read(".github/workflows/db-sync-to-pro.yml")
    preflight_step = workflow.split("      - name: H2 Pro preflight digest report", 1)[1].split(
        "      - name: Report pending migrations dry-run", 1
    )[0]

    assert "h2-pro-preflight-report-v2" in text
    assert "ordered_eligible_ids_digest" in text
    assert "public_visible_count" in text
    assert "missing_from_public_count" in text
    assert "duplicate institution_id+slug groups" in text
    assert "PARTIAL_UNLEDGERED" in text
    assert "H2_COMPATIBLE_OBSERVED_SURFACE" in text
    assert "INCONSISTENT" in text
    assert '"apply_authorized": False' in text
    assert '"private_h2_schema_observed": None' in text
    assert '"private_h2_schema_probe": "not_performed"' in text
    assert "read failed:" in text
    assert "H2_ALLOW_CRAWLER_EXCLUSIONS_DRIFT" not in text
    assert "table_has_rows" in text
    assert "crawler_exclusions_empty" in text
    assert "duplicate_institution_slug_groups" in text
    assert "H2 expected eligible count: " in text
    assert "H2 expected cohort digest: " in text
    assert "db.rpc(" not in text
    assert '"verification_rpc_probe": "not_performed"' in text
    assert '"rpc/' not in text
    assert "assert_h2_expand_preapply_guard(db)" in read("scripts/maintenance/db_migrate.py")
    assert "h2_pro_preflight_report.py | tee h2-pro-preflight-report.json" in workflow
    assert "set -euo pipefail" in preflight_step
    assert "Upload H2 Pro preflight report" in workflow


def test_h2_pro_expand_reconciles_empty_legacy_crawler_exclusions_drift() -> None:
    migration = read("db/migrations/20260827_h2_pro_expand_schema_compat.sql")

    assert "DROP TABLE IF EXISTS public.crawler_exclusions;" in migration
    assert "canonical exclusions live in institution_site_profiles" in migration
