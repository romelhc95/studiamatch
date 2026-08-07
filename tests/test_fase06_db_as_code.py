from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance.migration_manifest import (
    ManifestError,
    canonical_sql_sha256,
    load_manifest,
    validate_promotable_sql,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "db" / "manifests" / "fase06_promotable.json"


def _write_manifest(tmp_path: Path, entries: list[dict]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "phase": "FASE-06",
                "package_id": "F6-DB-AS-CODE-20260724",
                "status": "reconciled_not_certified",
                "prerequisites": [
                    "g1b_frontend_compatible",
                    "editorial_backfill_certified",
                    "free_postconditions_certified",
                ],
                "excluded": {
                    "H-00": "historical_free_only",
                    "canary": "observed_effective_unledgered",
                    "historical_snapshots": "superseded",
                },
                "entries": entries,
            }
        ),
        encoding="utf-8",
    )
    return path


def _entry(
    tmp_path: Path,
    *,
    name: str,
    component: str = "g1b",
    targets: list[str] | None = None,
) -> dict:
    migration_dir = tmp_path / "db" / "migrations"
    migration_dir.mkdir(parents=True, exist_ok=True)
    path = migration_dir / name
    path.write_text(
        "SET search_path = '';\nCREATE TABLE public.f6_test (id bigint);\n",
        encoding="utf-8",
    )
    return {
        "id": f"F6-{component.upper()}-FORWARD",
        "component": component,
        "path": path.relative_to(tmp_path).as_posix(),
        "sha256": canonical_sql_sha256(path),
        "provenance": "new_forward_only",
        "targets": targets or ["free"],
    }


def test_real_manifest_is_exact_forward_only_package():
    free_paths = load_manifest(MANIFEST, "free")
    pro_paths = load_manifest(MANIFEST, "pro")

    assert free_paths == pro_paths
    assert [path.name for path in pro_paths] == [
        "20260724_fase06_g1b_reconciliation.sql",
        "20260724_fase06_hito1_editorial_contract.sql",
        "20260725_fase07_g1b_closure.sql",
    ]
    assert all(
        path.stem.startswith(("20260724_fase06_", "20260725_fase07_"))
        for path in pro_paths
    )
    with pytest.raises(ManifestError, match="required ready_for_free"):
        load_manifest(MANIFEST, "free", required_status="ready_for_free")
    with pytest.raises(ManifestError, match="required free_certified"):
        load_manifest(MANIFEST, "pro", required_status="free_certified")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "H-00"),
        ("component", "h_00"),
        ("path", "db/migrations/20260724_fase06_h00.sql"),
    ],
)
def test_manifest_rejects_h00_variants(tmp_path: Path, field: str, value: str):
    entry = _entry(
        tmp_path,
        name="20260724_fase06_g1b_test.sql",
    )
    entry[field] = value

    with pytest.raises(ManifestError, match="H-00"):
        load_manifest(_write_manifest(tmp_path, [entry]), "free", root=tmp_path)


@pytest.mark.parametrize(
    "provenance", ["historical_free_only", "source_unavailable", "superseded"]
)
def test_manifest_rejects_non_promotable_provenance(
    tmp_path: Path, provenance: str
):
    entry = _entry(tmp_path, name="20260724_fase06_g1b_test.sql")
    entry["provenance"] = provenance

    with pytest.raises(ManifestError, match="non-promotable provenance"):
        load_manifest(_write_manifest(tmp_path, [entry]), "free", root=tmp_path)


def test_manifest_rejects_duplicate_stems(tmp_path: Path):
    entry = _entry(tmp_path, name="20260724_fase06_g1b_test.sql")
    duplicate = dict(entry, id="F6-G1B-DUPLICATE")

    with pytest.raises(ManifestError, match="duplicate"):
        load_manifest(
            _write_manifest(tmp_path, [entry, duplicate]), "free", root=tmp_path
        )


def test_manifest_validates_forbidden_unselected_entries(tmp_path: Path):
    free_entry = _entry(
        tmp_path,
        name="20260724_fase06_g1b_test.sql",
        targets=["free"],
    )
    pro_entry = _entry(
        tmp_path,
        name="20260724_fase06_hito1_test.sql",
        component="hito1",
        targets=["pro"],
    )
    free_entry["id"] = "H-00-FREE"

    with pytest.raises(ManifestError, match="H-00"):
        load_manifest(
            _write_manifest(tmp_path, [free_entry, pro_entry]),
            "pro",
            root=tmp_path,
        )


def test_pro_manifest_requires_one_entry_per_component(tmp_path: Path):
    first = _entry(
        tmp_path,
        name="20260724_fase06_g1b_one.sql",
        targets=["pro"],
    )
    second = _entry(
        tmp_path,
        name="20260724_fase06_g1b_two.sql",
        targets=["pro"],
    )
    second["id"] = "F6-G1B-FORWARD-TWO"
    hito1 = _entry(
        tmp_path,
        name="20260724_fase06_hito1_test.sql",
        component="hito1",
        targets=["pro"],
    )

    with pytest.raises(ManifestError, match="exactly"):
        load_manifest(
            _write_manifest(tmp_path, [first, second, hito1]),
            "pro",
            root=tmp_path,
        )


def test_manifest_rejects_checksum_drift(tmp_path: Path):
    entry = _entry(tmp_path, name="20260724_fase06_g1b_test.sql")
    entry["sha256"] = "0" * 64

    with pytest.raises(ManifestError, match="checksum mismatch"):
        load_manifest(_write_manifest(tmp_path, [entry]), "free", root=tmp_path)


def test_manifest_and_ledger_checksum_are_stable_across_lf_and_crlf(tmp_path: Path):
    g1b = _entry(
        tmp_path,
        name="20260724_fase06_g1b_test.sql",
        targets=["free"],
    )
    hito1 = _entry(
        tmp_path,
        name="20260724_fase06_hito1_test.sql",
        component="hito1",
        targets=["free"],
    )
    closure = _entry(
        tmp_path,
        name="20260725_fase07_g1b_closure_test.sql",
        component="g1b_closure",
        targets=["free"],
    )
    closure["id"] = "F7-G1B-CLOSURE"
    entries = [g1b, hito1, closure]

    for entry in entries:
        path = tmp_path / entry["path"]
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        assert canonical_sql_sha256(path) == entry["sha256"]
        assert db_migrate._file_sha256(path) == entry["sha256"]

    assert load_manifest(
        _write_manifest(tmp_path, entries), "free", root=tmp_path
    ) == [tmp_path / entry["path"] for entry in entries]


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM public.courses;",
        "UPDATE public.courses SET is_active = false;",
        "DO $block$ BEGIN DELETE FROM public.courses; END; $block$;",
        "DO $block$ BEGIN EXECUTE 'TRUNCATE public.courses'; END; $block$;",
        "CREATE TABLE public.x(id int); DELETE FROM public.courses;",
        "WITH changed AS (UPDATE public.courses SET is_active=false RETURNING id) SELECT * FROM changed;",
        "DO $block$ BEGIN EXECUTE $sql$DELETE FROM public.courses$sql$; END; $block$;",
        "DO $block$ BEGIN PERFORM public.side_effect(); END; $block$;",
        "DO $block$ BEGIN EXECUTE pg_catalog.format('%s', 'DELETE FROM public.courses'); END; $block$;",
        "DO $block$ DECLARE ignored integer; BEGIN SELECT public.side_effect() INTO ignored; END; $block$;",
        "DO $block$ DECLARE ignored integer; BEGIN SELECT side_effect() INTO ignored; END; $block$;",
        "SELECT public.side_effect();",
        "EXPLAIN ANALYZE DELETE FROM public.courses;",
    ],
)
def test_dml_guard_rejects_migration_time_dml(sql: str):
    with pytest.raises(ManifestError, match="DML|DO blocks"):
        validate_promotable_sql(sql)


def test_dml_guard_allows_policy_and_runtime_function_dml():
    validate_promotable_sql(
        """
        CREATE POLICY leads_insert_public ON public.leads
        FOR INSERT TO anon WITH CHECK (true);
        CREATE FUNCTION public.runtime_write() RETURNS void
        LANGUAGE sql AS $function$
            UPDATE public.courses SET is_active = false;
        $function$;
        """
    )


def test_ledger_read_failure_is_fail_closed():
    class BrokenDatabase:
        supabase_url = "https://example.invalid"

        def _get_headers(self, **kwargs):
            return {}

    original_get = db_migrate.requests.get
    try:
        def fail(*args, **kwargs):
            raise db_migrate.requests.RequestException("ledger unavailable")

        db_migrate.requests.get = fail
        with pytest.raises(RuntimeError, match="No se pudo leer"):
            db_migrate.get_applied_migrations(BrokenDatabase())
    finally:
        db_migrate.requests.get = original_get


def test_apply_registers_in_same_privileged_sql(monkeypatch, tmp_path: Path):
    migration = tmp_path / "20260603_test.sql"
    migration.write_text("CREATE TABLE public.f6_test (id bigint);", encoding="utf-8")
    captured: dict[str, str] = {}

    class Database:
        supabase_url = "https://example.invalid"

        def rpc_raise(self, *args, **kwargs):
            return {"status": "success"}

        def rpc(self, *args, **kwargs):
            return {"status": "success"}

        def _get_headers(self, **kwargs):
            return {}

    def fake_exec(db, sql, max_retries=2):
        captured["sql"] = sql
        return {"status": "success"}

    monkeypatch.setattr(db_migrate, "_exec_sql_with_retry", fake_exec)

    class Response:
        status_code = 200

        @staticmethod
        def json():
            marker = f"sha256:{hashlib.sha256(migration.read_bytes()).hexdigest()}"
            return [{"name": migration.stem, "statements": marker}]

    monkeypatch.setattr(db_migrate.requests, "get", lambda *args, **kwargs: Response())

    assert db_migrate.apply_migration(Database(), str(migration))
    assert "INSERT INTO public.supabase_migrations" in captured["sql"]
    assert migration.stem in captured["sql"]
    assert "ON CONFLICT (name) DO NOTHING" in captured["sql"]
    assert "sha256:" in captured["sql"]


def test_fase06_verifier_runs_before_ledger_registration(monkeypatch, tmp_path: Path):
    migration = tmp_path / "20260724_fase06_g1b_reconciliation.sql"
    migration.write_text("CREATE TABLE public.f6_test (id bigint);", encoding="utf-8")
    captured: dict[str, str] = {}

    class Database:
        supabase_url = "https://example.invalid"

        def rpc_raise(self, *args, **kwargs):
            return {"status": "success"}

        def rpc(self, *args, **kwargs):
            return {"status": "success"}

        def _get_headers(self, **kwargs):
            return {}

    def fake_exec(db, sql, max_retries=2):
        captured["sql"] = sql
        return {"status": "success"}

    class Response:
        status_code = 200

        @staticmethod
        def json():
            marker = f"sha256:{hashlib.sha256(migration.read_bytes()).hexdigest()}"
            return [{"name": migration.stem, "statements": marker}]

    monkeypatch.setattr(db_migrate, "_exec_sql_with_retry", fake_exec)
    monkeypatch.setattr(db_migrate.requests, "get", lambda *args, **kwargs: Response())

    assert db_migrate.apply_migration(Database(), str(migration))
    verifier = "public.verify_fase06_g1b_reconciliation()"
    assert verifier in captured["sql"]
    assert captured["sql"].index(verifier) < captured["sql"].index(
        "INSERT INTO public.supabase_migrations"
    )


def test_pro_workflow_uses_manifest_for_detect_and_apply():
    workflow = (ROOT / ".github" / "workflows" / "db-sync-to-pro.yml").read_text(
        encoding="utf-8"
    )
    command = '--env pro --manifest "$MIGRATION_MANIFEST"'
    normalized = workflow.replace("--dry-run ", "")

    assert normalized.count(command) == 2
    assert "MIGRATION_MANIFEST: db/manifests/fase08_candidate.json" in workflow
    assert "push:" in workflow
    assert "Report pending migrations dry-run" in workflow
    assert "candidate_sha:" in workflow
    assert "apply_authorized:" in workflow
    assert "backup_pitr_verified:" in workflow
    assert "ddl_authorization_id:" in workflow
    assert workflow.count("persist-credentials: false") == 5
    assert "detect-db-changes:" in workflow
    assert "db-contract-preflight:" in workflow
    assert "--validate-only --manifest \"$MIGRATION_MANIFEST\"" in workflow
    assert 'test "$(git rev-parse origin/main)" = "$CANDIDATE_SHA"' in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
    assert "inputs.operation == 'apply'" in workflow
    assert ".context/operaciones/ddl_authorizations/${DDL_AUTHORIZATION_ID}.md" in workflow
    assert "APPROVED_FOR_PRODUCTION_DDL" in workflow


def test_free_glob_path_rejects_fase06_without_manifest():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/maintenance/db_migrate.py",
            "--env",
            "free",
            "--dry-run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 2
    assert "FASE-06/07 requieren --manifest" in result.stdout


def test_free_only_can_select_a_non_fase06_migration():
    name = "20260602_fase121_profile_pillar_extractors"
    selected = db_migrate.select_legacy_migrations([name])

    assert [db_migrate.extract_name(path) for path in selected] == [name]


def test_reconciliation_note_and_backfill_contract_are_linked():
    note = ROOT / ".context" / "operaciones" / "reconciliacion_db_as_code_f6.md"
    backfill = ROOT / "db" / "operations" / "editorial" / "README.md"

    assert note.is_file()
    text = note.read_text(encoding="utf-8")
    assert "fase06_promotable.json" in text
    assert "historical_free_only" in text
    assert "observed_effective_unledgered" in text
    assert backfill.is_file()


def test_editorial_contract_closes_public_policy_and_column_drift():
    migration = (
        ROOT / "db/migrations/20260724_fase06_hito1_editorial_contract.sql"
    ).read_text(encoding="utf-8")
    public_grant = migration.split("GRANT SELECT (", 1)[1].split(
        ") ON TABLE public.courses TO anon, authenticated;", 1
    )[0]

    assert 'DROP POLICY IF EXISTS "Public read for courses"' in migration
    assert "policy.policyname NOT IN" in migration
    assert "verify_fase06_hito1_contract" in migration
    assert "missing_fields" not in public_grant
    assert "field_sources" not in public_grant
    assert "sponsorship_priority" not in public_grant
    assert "name" in public_grant
    assert "publication_status" in public_grant
    assert "has_table_privilege('anon', 'public.courses', 'SELECT')" not in migration


def test_target_verification_requires_fase06_postconditions():
    verifier = (
        ROOT / "scripts" / "maintenance" / "check_db_parity.py"
    ).read_text(encoding="utf-8")

    assert "20260724_fase06_g1b_reconciliation" in verifier
    assert "20260724_fase06_hito1_editorial_contract" in verifier
    assert "verify_fase06_g1b_reconciliation" in verifier
    assert "verify_fase06_hito1_contract" in verifier
