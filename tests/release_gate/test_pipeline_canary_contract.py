from pathlib import Path

import hashlib
import json
import sys

import pytest

from scripts.maintenance import emit_pipeline_canary_evidence, pipeline_canary
from scripts.shared.db_client import DatabaseClient


ROOT = Path(__file__).resolve().parents[2]


def test_workers_expose_fail_closed_canary_cli():
    cleansing = (ROOT / "scripts/core/cleansing_worker.py").read_text(encoding="utf-8")
    enrichment = (ROOT / "scripts/core/enrichment_worker.py").read_text(encoding="utf-8")
    sync = (ROOT / "scripts/core/sync_vector_worker.py").read_text(encoding="utf-8")

    assert '--institution-id' in cleansing
    assert '--require-atomic-rpc' in cleansing
    assert '"inst_id": self.institution_id' in cleansing
    assert '--institution-id' in enrichment
    assert '--require-atomic-rpc' in enrichment
    assert 'institution_id=eq.{self.institution_id}' in enrichment
    assert '--institution-id' in sync
    assert '--canary-mode' in sync
    assert 'Canary mode requires production_enabled=false' in sync


def test_cleanup_is_idempotent_and_child_first():
    calls = []

    class FakeApi:
        def select_all(self, table, columns, query):
            if table == "institution_site_profiles":
                return [{
                    "id": "profile-id",
                    "institution_id": "institution-id",
                    "notes": "DB_AS_CODE_RELEASE_CANARY",
                    "production_enabled": False,
                }]
            if table == "institutions":
                return [{
                    "id": "institution-id",
                    "slug": "zz-studiamatch-canary-free-123",
                    "status": "Inactiva",
                }]
            return []

        def patch_one(self, table, row_id, payload):
            calls.append(("patch", table, row_id, payload))

        def delete(self, table, query):
            calls.append(("delete", table, query))
            return []

    assert pipeline_canary._cleanup(FakeApi(), {
        "institution_id": "institution-id",
        "slug": "zz-studiamatch-canary-free-123",
        "url_prefix": "https://canary.invalid/free/123/",
    }) == []
    deleted_tables = [call[1] for call in calls if call[0] == "delete"]
    assert deleted_tables == [
        "courses",
        "enriched_programs",
        "cleansed_programs",
        "staging_raw",
        "institution_site_profiles",
        "institutions",
    ]


def test_canary_migration_hides_reserved_fixture_markers():
    migration = (ROOT / "db/migrations/20260719_canary_fixture_isolation.sql").read_text(encoding="utf-8")
    assert "AS RESTRICTIVE" in migration
    assert "zz-studiamatch-canary-%" in migration
    assert "DB_AS_CODE_RELEASE_CANARY" in migration
    assert "https://canary.invalid/%" in migration


def test_cleanup_recovers_orphaned_canary_rows():
    calls = []

    class FakeApi:
        def select_all(self, table, columns, query):
            if table == "staging_raw":
                return [{"id": "staging-id", "url": "https://canary.invalid/free/123/programa"}]
            return []

        def delete(self, table, query):
            calls.append((table, query))
            return []

    errors = pipeline_canary._cleanup(FakeApi(), {
        "institution_id": "institution-id",
        "slug": "zz-studiamatch-canary-free-123",
        "url_prefix": "https://canary.invalid/free/123/",
    })

    assert errors == []
    assert ("staging_raw", "institution_id=eq.institution-id") in calls


def test_cleanup_rejects_non_canary_urls():
    class FakeApi:
        def select_all(self, table, columns, query):
            if table == "courses":
                return [{"id": "course-id", "url": "https://example.edu/programa"}]
            return []

    with pytest.raises(pipeline_canary.CanaryError, match="non-canary URL"):
        pipeline_canary._cleanup(FakeApi(), {
            "institution_id": "institution-id",
            "slug": "zz-studiamatch-canary-free-123",
            "url_prefix": "https://canary.invalid/free/123/",
        })


def test_cleanup_manifest_must_use_reserved_namespace():
    manifest = {
        "environment": "free",
        "run_id": "123",
        "institution_id": "00000000-0000-0000-0000-000000000001",
        "staging_id": "00000000-0000-0000-0000-000000000002",
        "slug": "ordinary-institution",
        "url_prefix": "https://example.edu/",
    }

    with pytest.raises(pipeline_canary.CanaryError, match="reserved canary namespace"):
        pipeline_canary._validate_run_manifest(manifest, "free")


def test_scoped_migration_enforces_atomic_cardinality_and_sync():
    migration = (ROOT / "db/migrations/20260719_canary_scoped_atomic_promotions.sql").read_text(
        encoding="utf-8"
    )

    assert "jsonb_array_length(p_cleansed_data) <> 1" in migration
    assert "jsonb_array_length(p_enriched_data) <> 1" in migration
    assert migration.count("GET DIAGNOSTICS") >= 6
    assert "atomic_canary_sync" in migration
    assert "TO service_role, canary_runner" in migration
    assert migration.count("OWNER TO postgres") == 4


def test_database_client_does_not_use_restricted_access_token_outside_canary(monkeypatch):
    monkeypatch.setenv("NEXT_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x")
    monkeypatch.setenv("NEXT_SUPABASE_SECRET_KEY", "sb_secret_x")
    monkeypatch.setenv("NEXT_SUPABASE_ACCESS_TOKEN", "restricted-token")
    monkeypatch.delenv("STUDIAMATCH_CANARY_WORKER", raising=False)

    headers = DatabaseClient("https://example.supabase.co")._get_headers(use_service_role=True)

    assert headers["apikey"] == "sb_secret_x"
    assert "Authorization" not in headers


def test_database_client_uses_restricted_access_token_for_canary_worker(monkeypatch):
    monkeypatch.setenv("NEXT_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x")
    monkeypatch.setenv("NEXT_SUPABASE_ACCESS_TOKEN", "restricted-token")
    monkeypatch.setenv("STUDIAMATCH_CANARY_WORKER", "1")
    monkeypatch.delenv("NEXT_SUPABASE_SECRET_KEY", raising=False)

    headers = DatabaseClient("https://example.supabase.co")._get_headers(use_service_role=True)

    assert headers["apikey"] == "sb_publishable_x"
    assert headers["Authorization"] == "Bearer restricted-token"


def test_strict_rest_uses_access_token_only_for_authorization(monkeypatch):
    captured = {}

    class Response:
        status_code = 200
        content = b"[]"

        @staticmethod
        def json():
            return []

    def fake_request(method, url, headers, json, timeout):
        captured.update(headers)
        return Response()

    monkeypatch.setattr(pipeline_canary.requests, "request", fake_request)
    api = pipeline_canary.StrictRest(
        "https://example.supabase.co",
        "sb_secret_x",
        "sb_publishable_x",
    )

    assert api.rpc_with_access_token("verify_canary_runner_identity", "restricted-token") == []
    assert captured["apikey"] == "sb_publishable_x"
    assert captured["Authorization"] == "Bearer restricted-token"


def test_canary_evidence_binds_candidate_worker_hashes(tmp_path, monkeypatch):
    candidate_sha = "a" * 40
    candidate_root = tmp_path / "candidate"
    worker_paths = {
        "cleansing": "scripts/core/cleansing_worker.py",
        "enrichment": "scripts/core/enrichment_worker.py",
        "sync": "scripts/core/sync_vector_worker.py",
    }
    worker_hashes = {}
    for name, relative_path in worker_paths.items():
        path = candidate_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name, encoding="utf-8")
        worker_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "release_id": "pre-hito1",
        "revision": 1,
        "candidate_commit": candidate_sha,
        "state": "WRITERS_PAUSED",
        "evidence": [],
    }
    report = {
        "environment": "free",
        "run_id": "123",
        "candidate_commit": candidate_sha,
        "institution_id": "00000000-0000-0000-0000-000000000001",
        "cleanup_remaining_rows": 0,
        "cleanup_errors": [],
        "cleanup_out_of_scope_unchanged": True,
        "worker_sha256": worker_hashes,
        "checks": {
            "pipeline_lineage": "PASS",
            "public_fixtures_zero": "PASS",
            "out_of_scope_mutations_zero": "PASS",
            "production_enabled_false": "PASS",
            "rpc_fallback_zero": "PASS",
            "rls_guard_definitions": "PASS",
            "mock_provenance": "PASS",
        },
    }
    cleanup = {
        "environment": "free",
        "run_id": "123",
        "institution_id": report["institution_id"],
        "remaining_rows": 0,
        "errors": [],
    }
    manifest_path = tmp_path / "manifest.json"
    report_path = tmp_path / "report.json"
    cleanup_path = tmp_path / "cleanup.json"
    output_path = tmp_path / "evidence.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report_path.write_text(json.dumps(report), encoding="utf-8")
    cleanup_path.write_text(json.dumps(cleanup), encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    monkeypatch.setattr(sys, "argv", [
        "emit_pipeline_canary_evidence.py",
        "--manifest", str(manifest_path),
        "--manifest-sha256", manifest_sha,
        "--report", str(report_path),
        "--cleanup-report", str(cleanup_path),
        "--env", "free",
        "--run-id", "123",
        "--commit", "b" * 40,
        "--candidate-commit", candidate_sha,
        "--candidate-root", str(candidate_root),
        "--output", str(output_path),
    ])

    assert emit_pipeline_canary_evidence.main() == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["verdict"] == "PASS"
