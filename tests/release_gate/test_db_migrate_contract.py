import hashlib
import json

import pytest

from scripts.maintenance import db_migrate
from scripts.maintenance import apply_nontransactional_migration as nontransactional
from scripts.maintenance import emit_production_apply_evidence
from scripts.maintenance import verify_manifest_postconditions
from scripts.maintenance import emit_release_authorization_evidence
from scripts.maintenance import emit_writers_pause_evidence


def _migration_entry(path):
    return {
        "absolute_path": str(path),
        "path": "db/migrations/20260719_test.sql",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "transactional": True,
        "targets": ["free", "pro"],
        "postconditions": [{"id": "object-exists", "sql": "SELECT true", "expected": True}],
        "rollback": {"strategy": "forward_fix", "instructions": "apply correction"},
    }


def test_manifest_package_preserves_order_and_checksum(tmp_path):
    migration_dir = tmp_path / "db/migrations"
    migration_dir.mkdir(parents=True)
    first = migration_dir / "20260719_first.sql"
    second = migration_dir / "20260719_second.sql"
    first.write_text("select 1;", encoding="utf-8")
    second.write_text("select 2;", encoding="utf-8")
    entries = []
    for path in (second, first):
        entry = _migration_entry(path)
        entry["path"] = f"db/migrations/{path.name}"
        entries.append({key: value for key, value in entry.items() if key != "absolute_path"})
    manifest = {"release_id": "release", "revision": 1, "candidate_commit": "a" * 40, "migrations": entries}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    _, selected = db_migrate.migration_entries_from_manifest(manifest_path, "pro", digest, tmp_path)

    assert [entry["absolute_path"] for entry in selected] == [str(second), str(first)]


def test_environment_must_match_authorized_project_ref(monkeypatch):
    monkeypatch.setenv("NEXT_SUPABASE_SECRET_KEY", "test-only")
    monkeypatch.setenv("SUPABASE_URL", "https://wrong.supabase.co")
    with pytest.raises(RuntimeError, match="project ref autorizado"):
        db_migrate.assert_environment("pro")


def test_apply_and_ledger_registration_share_one_rpc(tmp_path, monkeypatch):
    migration = tmp_path / "20260719_test.sql"
    migration.write_text("create table test_table(id integer)", encoding="utf-8")
    entry = _migration_entry(migration)
    calls = []

    class FakeDb:
        def rpc_raise(self, name, payload):
            calls.append((name, payload["sql_text"]))
            return {}

        def rpc(self, name, payload):
            return {}

    metadata = {
        "sha256": entry["sha256"],
        "release_id": "release",
        "revision": 1,
        "candidate_commit": "a" * 40,
        "manifest_sha256": "b" * 64,
    }
    monkeypatch.setattr(
        db_migrate,
        "get_applied_migrations",
        lambda _db: {"20260719_test": json.dumps(metadata)},
    )

    assert db_migrate.apply_migration(FakeDb(), entry, metadata) is True
    assert len(calls) == 1
    assert "create table test_table" in calls[0][1]
    assert "INSERT INTO public.supabase_migrations" in calls[0][1]
    assert entry["sha256"] in calls[0][1]


def test_checksum_is_revalidated_immediately_before_execution(tmp_path):
    migration = tmp_path / "20260719_test.sql"
    migration.write_text("select 1", encoding="utf-8")
    entry = _migration_entry(migration)
    migration.write_text("select 2", encoding="utf-8")

    class FailingDb:
        def rpc_raise(self, *_args, **_kwargs):
            raise AssertionError("RPC must not execute")

    assert db_migrate.apply_migration(FailingDb(), entry) is False


def test_plpgsql_begin_is_not_mistaken_for_top_level_transaction(tmp_path):
    migration = tmp_path / "20260719_function.sql"
    migration.write_text(
        "DO $$\nBEGIN\n  PERFORM 1;\nEND\n$$;",
        encoding="utf-8",
    )
    entry = _migration_entry(migration)

    class UnusedDb:
        pass

    assert db_migrate.apply_migration(UnusedDb(), entry, dry_run=True) is True


def test_ledger_read_fails_closed(monkeypatch):
    class Response:
        status_code = 500

    class FakeDb:
        supabase_url = "https://example.supabase.co"

        @staticmethod
        def _get_headers(use_service_role=False):
            return {}

    monkeypatch.setattr(db_migrate.requests, "get", lambda *_args, **_kwargs: Response())
    with pytest.raises(RuntimeError, match="No se pudo leer"):
        db_migrate.get_applied_migrations(FakeDb())


def test_nontransactional_runner_only_accepts_concurrent_indexes():
    parsed = nontransactional.split_index_statements(
        """
        -- approved index
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_one ON public.courses(id);
        CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_two ON public.courses(url);
        """
    )
    assert [item["name"] for item in parsed] == ["idx_one", "idx_two"]
    with pytest.raises(RuntimeError, match="Solo se permite"):
        nontransactional.split_index_statements("DROP TABLE public.courses;")


def test_nontransactional_dsn_is_bound_to_target():
    nontransactional.assert_database_url(
        "postgresql://postgres.xwhtiqmboljkshrtviyw:test@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=verify-full",
        "pro",
    )
    with pytest.raises(RuntimeError, match="project ref"):
        nontransactional.assert_database_url(
            "postgresql://postgres.other:test@pooler.supabase.com:5432/postgres?sslmode=verify-full",
            "pro",
        )
    with pytest.raises(RuntimeError, match="TLS"):
        nontransactional.assert_database_url(
            "postgresql://postgres.xwhtiqmboljkshrtviyw:test@aws-0-us-east-1.pooler.supabase.com:5432/postgres",
            "pro",
        )


def test_production_apply_evidence_is_structured_for_next_role():
    manifest = {
        "state": "PRODUCTION_APPROVED",
        "release_id": "release",
        "revision": 2,
        "candidate_commit": "a" * 40,
        "evidence": [{"path": "previous.json", "sha256": "b" * 64}],
    }
    evidence = emit_production_apply_evidence.build_evidence(
        manifest, "12345", "github-actions", "c" * 40
    )
    assert evidence["sequence"] == 2
    assert evidence["event"] == "PRODUCTION_APPLY"
    assert evidence["handoff"]["to_role"] == "pipeline-engineer"
    assert {check["id"] for check in evidence["checks"]} == {"manifest-applied", "ledger-recorded"}


def test_postconditions_are_single_read_only_selects():
    verify_manifest_postconditions.validate_query("SELECT true")
    with pytest.raises(RuntimeError, match="SELECT"):
        verify_manifest_postconditions.validate_query("UPDATE courses SET is_active = false")
    with pytest.raises(RuntimeError, match="no permitida"):
        verify_manifest_postconditions.validate_query("SELECT * FROM courses FOR UPDATE")
    with pytest.raises(RuntimeError, match="funcion no permitida"):
        verify_manifest_postconditions.validate_query("SELECT net.http_post('https://example.com')")


def test_human_authorization_evidence_uses_protected_workflow():
    manifest = {
        "state": "FREE_CERTIFIED",
        "release_id": "release",
        "revision": 1,
        "candidate_commit": "a" * 40,
        "evidence": [],
    }
    evidence = emit_release_authorization_evidence.build_evidence(
        manifest, "AUTHORIZE_PRODUCTION", "12345", "c" * 40
    )
    assert evidence["actor"]["kind"] == "human"
    assert evidence["provenance"]["workflow"] == ".github/workflows/authorize-release.yml"
    assert evidence["handoff"]["to_role"] == "devops-release-manager"


def test_writers_pause_evidence_is_run_backed():
    manifest = {
        "state": "PIPELINE_VALIDATED",
        "release_id": "release",
        "revision": 1,
        "candidate_commit": "a" * 40,
        "evidence": [],
    }
    evidence = emit_writers_pause_evidence.build_evidence(manifest, "12345", "c" * 40)
    assert evidence["event"] == "WRITERS_PAUSE"
    assert evidence["provenance"]["workflow"] == ".github/workflows/pause-production-writers.yml"
    assert {check["id"] for check in evidence["checks"]} == {"writers-paused", "active-runs-zero"}
