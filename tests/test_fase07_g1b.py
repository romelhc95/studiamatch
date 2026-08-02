from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.core import master_orchestrator, sync_vector_worker
from scripts.maintenance import db_migrate
from scripts.maintenance.migration_manifest import (
    ManifestError,
    load_manifest,
    validate_promotable_sql,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "db/manifests/fase06_promotable.json"


def test_fase07_migration_closes_legacy_rpc_and_social_acl():
    migration = ROOT / "db/migrations/20260725_fase07_g1b_closure.sql"
    sql = migration.read_text(encoding="utf-8")

    validate_promotable_sql(sql, label=migration.name)
    assert "DROP FUNCTION IF EXISTS public.increment_view_count(uuid)" in sql
    assert "DROP FUNCTION IF EXISTS public.increment_view_count_v2(uuid, text)" in sql
    assert "GRANT SELECT (" in sql
    assert "moderation_status" in sql
    assert "verify_fase07_g1b_closure" in sql
    assert "verify_fase06_hito1_contract" in sql
    assert "procedure.proname IN" in sql
    assert "FOREACH privilege_name" in sql
    assert "policy.cmd <> 'SELECT'" in sql
    assert "policy.permissive <> 'PERMISSIVE'" in sql
    assert "course.is_active" in sql
    assert "course.is_verified" in sql
    assert "policy.tablename" in sql
    assert "'.course_id%'" in sql
    assert "pg_catalog.aclexplode" in sql
    assert "has_function_privilege" in sql
    assert "SELECT,INSERT,UPDATE,DELETE" not in sql
    assert migration in load_manifest(MANIFEST, "free")
    assert migration in load_manifest(MANIFEST, "pro")


def test_manifest_rejects_reordered_package(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["entries"][1], manifest["entries"][2] = (
        manifest["entries"][2],
        manifest["entries"][1],
    )
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ManifestError, match="exactly"):
        load_manifest(path, "free")


def test_free_accepts_later_free_certified_status(tmp_path: Path):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["status"] = "free_certified"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert load_manifest(
        path,
        "free",
        required_status=("ready_for_free", "free_certified"),
    )


def test_frontend_has_no_revoked_g1b_mutations():
    web_files = [
        ROOT / "web/src/app/HomeContent.tsx",
        ROOT / "web/src/app/compare/CompareContent.tsx",
        ROOT / "web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx",
        ROOT / "web/src/lib/supabase.ts",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in web_files)
    detail = web_files[2].read_text(encoding="utf-8")

    assert "increment_view_count" not in source
    assert "view_count" not in source
    assert "comparison_count" not in source
    assert "ALLOWED_SORTS" in source
    assert "'popular'" not in source
    assert "handleSubmitSocial" not in detail
    assert "PUBLICAR RESEÑA" not in detail
    assert "ratings?course_id=eq.${safeId}&select=*" not in detail
    assert "reviews?course_id=eq.${safeId}&select=*" not in detail
    assert "select=id,course_id,rating_value,user_nickname,created_at" in detail
    assert "select=id,course_id,content,user_nickname,created_at" in detail


def test_pipeline_gate_reason_matches_requeue_contract():
    cleansing = (ROOT / "scripts/core/cleansing_worker.py").read_text(
        encoding="utf-8"
    )
    enrichment = (ROOT / "scripts/core/enrichment_worker.py").read_text(
        encoding="utf-8"
    )
    sync = (ROOT / "scripts/core/sync_vector_worker.py").read_text(
        encoding="utf-8"
    )

    assert "'processing_error': 'pipeline_gate=false'" in cleansing
    assert "metadata['skip_reason'] = 'pipeline_gate=false'" in enrichment
    assert "No pipeline-enabled institutions available for sync" in sync
    assert "institution_id=in." in sync
    assert "pipeline_enabled=false" not in cleansing + enrichment + sync
    assert 'filters = "status=eq.pending"' in enrichment
    assert "status=eq.pending&institution_id" in sync
    assert "select_pipeline_raise('cleansed_programs'" in enrichment
    assert "select_pipeline_raise('enriched_programs'" in sync
    assert "select_pipeline_raise('staging_raw'" in cleansing
    assert "select_pipeline_raise('institution_site_profiles')" in cleansing
    assert "select_pipeline_raise('institution_site_profiles')" in enrichment
    assert "select_pipeline_raise('institution_site_profiles')" in sync
    assert "worker.db.patch_raise('staging_raw'" in cleansing
    assert "worker.db.patch_raise('cleansed_programs'" in enrichment
    assert "self.db.patch_exact_one_raise(" in sync


def test_sync_writer_preserves_editorial_state_and_fails_closed():
    sync = (ROOT / "scripts/core/sync_vector_worker.py").read_text(
        encoding="utf-8"
    )
    payload = sync.split("course_data = {", 1)[1].split(
        "# Generate Embedding", 1
    )[0]

    assert "profile else False" in sync
    assert "self.db.select_service_raise(" in sync
    assert "'courses'," in sync
    assert "id,institution_id,is_active,last_404_at" in sync
    assert "quote(str(url), safe='')" in sync
    assert "existing_metadata=enriched.get('metadata')" in sync
    assert "cross_institution_url_collision" in sync
    assert "publication_status" not in sync
    assert "manual_updated_at" not in sync
    assert "publication_status" not in payload
    assert "manual_updated_at" not in payload
    assert "sponsorship_priority" not in payload


class _SyncDatabase:
    def __init__(self, existing):
        self.existing = existing
        self.filters = []
        self.upserts = []
        self.patches = []

    def select_service_raise(self, table, filters=None, columns="*"):
        self.filters.append(filters)
        return list(self.existing)

    def select_pipeline_raise(self, table, filters=None, columns="*", limit=None):
        return [_enriched_record()]

    def upsert(self, table, data, on_conflict=None):
        self.upserts.append(data)
        return [{"id": "course-id", "category_id": None}]

    def patch(self, table, filters=None, data=None):
        self.patches.append((table, filters, data))
        return {"status": "success"}

    def patch_raise(self, table, filters=None, data=None):
        return self.patch(table, filters=filters, data=data)

    def patch_exact_one_raise(self, table, filters=None, data=None, expected_id=None):
        self.patches.append((table, filters, data, expected_id))
        return {"id": expected_id, **(data or {})}


def _sync_worker(database):
    worker = sync_vector_worker.SyncVectorWorker.__new__(
        sync_vector_worker.SyncVectorWorker
    )
    worker.db = database
    worker.ready_inst_ids = {"institution-id"}
    worker._get_noise_patterns_for_inst = lambda inst_id: []
    worker._get_profile = lambda inst_id: {
        "production_enabled": True,
        "field_defaults": {},
        "section_mode_map": {},
    }
    return worker


def _enriched_record():
    return {
        "id": "enriched-id",
        "institution_id": "institution-id",
        "official_name": "Programa Seguro",
        "url": "https://example.com/program?a=1&b=2",
        "categories": [],
        "metadata": {"provider": "test"},
    }


def test_sync_updates_automatically_inactive_course_without_publishing(monkeypatch):
    database = _SyncDatabase([
        {
            "id": "course-id",
            "institution_id": "institution-id",
            "is_active": False,
        }
    ])
    worker = _sync_worker(database)
    monkeypatch.setattr(sync_vector_worker, "parse_start_date", lambda value: (None, False))
    monkeypatch.setattr(sync_vector_worker, "duration_months_to_hours", lambda value: None)
    monkeypatch.setattr(sync_vector_worker, "infer_seniority", lambda *args: "Junior")
    monkeypatch.setattr(sync_vector_worker, "lookup_market_salary", lambda *args: None)
    monkeypatch.setattr(sync_vector_worker, "compute_roi", lambda *args: (None, None))

    assert worker.sync_to_production(_enriched_record())
    assert database.upserts == []
    assert database.patches[-1][2] == {"status": "synced"}
    assert "%26" in database.filters[0]


def test_sync_preserves_manually_unpublished_course(monkeypatch):
    database = _SyncDatabase([
        {
            "id": "course-id",
            "institution_id": "institution-id",
            "is_active": False,
        }
    ])
    worker = _sync_worker(database)
    monkeypatch.setattr(sync_vector_worker, "parse_start_date", lambda value: (None, False))
    monkeypatch.setattr(sync_vector_worker, "duration_months_to_hours", lambda value: None)
    monkeypatch.setattr(sync_vector_worker, "infer_seniority", lambda *args: "Junior")

    assert worker.sync_to_production(_enriched_record())
    assert database.upserts == []


def test_sync_aborts_when_editorial_lookup_fails(monkeypatch):
    class BrokenDatabase(_SyncDatabase):
        def select_service_raise(self, table, filters=None, columns="*"):
            raise RuntimeError("Data API unavailable")

    database = BrokenDatabase([])
    worker = _sync_worker(database)
    monkeypatch.setattr(sync_vector_worker, "parse_start_date", lambda value: (None, False))
    monkeypatch.setattr(sync_vector_worker, "duration_months_to_hours", lambda value: None)
    monkeypatch.setattr(sync_vector_worker, "infer_seniority", lambda *args: "Junior")

    with pytest.raises(RuntimeError, match="Data API unavailable"):
        worker.sync_to_production(_enriched_record())
    assert database.upserts == []


def test_sync_error_update_preserves_existing_metadata():
    database = _SyncDatabase([])
    worker = _sync_worker(database)

    worker.update_enriched_status(
        "enriched-id",
        "skipped",
        error_msg="pipeline_gate=false",
        existing_metadata={"provider": "test"},
    )

    assert database.patches[-1][2]["metadata"] == {
        "provider": "test",
        "error": "pipeline_gate=false",
    }


def test_sync_materializes_disabled_gate_for_requeue():
    database = _SyncDatabase([])
    worker = _sync_worker(database)
    worker.ready_inst_ids = set()

    assert worker.get_pending_enriched(limit=1) == []
    assert database.patches == []


def test_sync_gate_patch_failure_is_not_silenced():
    class BrokenDatabase(_SyncDatabase):
        def patch_exact_one_raise(self, table, filters=None, data=None, expected_id=None):
            raise RuntimeError("patch failed")

    worker = _sync_worker(BrokenDatabase([]))
    worker.ready_inst_ids = set()

    assert worker.sync_to_production(_enriched_record()) is False


class _FakeDatabase:
    def __init__(self, institutions, profiles, dense_ids=None):
        self.institutions = institutions
        self.profiles = profiles
        self.dense_ids = set(dense_ids or [])

    def select_service_raise(self, *args, **kwargs):
        return list(self.institutions)

    def select_pipeline_raise(self, *args, **kwargs):
        return list(self.profiles)

    def count_pipeline_raise(self, table, filters=None):
        return 51 if any(item in (filters or "") for item in self.dense_ids) else 0


def test_orchestrator_applies_gates_before_limit(monkeypatch):
    now = datetime(2026, 7, 25, tzinfo=timezone.utc)
    institutions = [
        {"id": "disabled", "name": "Disabled", "slug": "disabled", "last_harvest_at": None},
        {"id": "excluded", "name": "Excluded", "slug": "excluded", "last_harvest_at": None},
        {"id": "circuit", "name": "Circuit", "slug": "circuit", "last_harvest_at": None},
        {"id": "recent", "name": "Recent", "slug": "recent", "last_harvest_at": (now - timedelta(days=1)).isoformat()},
        {"id": "first", "name": "First", "slug": "first", "last_harvest_at": None},
        {"id": "second", "name": "Second", "slug": "second", "last_harvest_at": None},
    ]
    profiles = [
        {"institution_id": "disabled", "discovery_enabled": False},
        {"institution_id": "excluded", "discovery_enabled": True},
        {
            "institution_id": "circuit",
            "discovery_enabled": True,
            "circuit_open": True,
            "circuit_opened_at": (now - timedelta(hours=1)).isoformat(),
        },
        {"institution_id": "recent", "discovery_enabled": True},
        {"institution_id": "first", "discovery_enabled": True},
        {"institution_id": "second", "discovery_enabled": True},
    ]
    monkeypatch.setattr(
        master_orchestrator,
        "db",
        _FakeDatabase(institutions, profiles, dense_ids={"recent"}),
    )

    selected = master_orchestrator.get_institutions(
        limit=2,
        excluded_slugs={"excluded"},
        now=now,
    )

    assert [item["slug"] for item in selected] == ["first", "second"]
    assert master_orchestrator.get_institutions(limit=0, now=now) == []


def test_orchestrator_fails_closed_when_selection_fails(monkeypatch):
    def fail_selection(**kwargs):
        raise RuntimeError("Data API unavailable")

    monkeypatch.setattr(master_orchestrator, "get_institutions", fail_selection)
    assert master_orchestrator.main(["--skip-cleansing"]) == 1


def test_orchestrator_fails_on_unverifiable_freshness(monkeypatch):
    institution = {
        "id": "invalid-time",
        "name": "Invalid Time",
        "slug": "invalid-time",
        "last_harvest_at": "not-a-timestamp",
    }
    profiles = [{"institution_id": "invalid-time", "discovery_enabled": True}]
    monkeypatch.setattr(
        master_orchestrator,
        "db",
        _FakeDatabase([institution], profiles),
    )

    with pytest.raises(RuntimeError, match="Invalid freshness timestamp"):
        master_orchestrator.get_institutions(limit=1)
    assert master_orchestrator.main(["--limit", "1", "--skip-cleansing"]) == 1


def test_orchestrator_limit_zero_launches_no_stage(monkeypatch):
    monkeypatch.setattr(master_orchestrator, "get_institutions", lambda **kwargs: [])

    def unexpected_run(*args, **kwargs):
        raise AssertionError("stage launched with limit zero")

    monkeypatch.setattr(master_orchestrator, "run_script", unexpected_run)
    assert master_orchestrator.main(["--limit", "0", "--skip-cleansing"]) == 0


def test_orchestrator_returns_failure_after_partial_stage_failure(monkeypatch):
    institution = {
        "id": "one",
        "name": "One",
        "slug": "one",
        "website_url": "https://example.com",
        "last_harvest_at": None,
    }
    monkeypatch.delenv("JOB_START_TIME", raising=False)
    monkeypatch.setattr(
        master_orchestrator,
        "get_institutions",
        lambda **kwargs: [institution],
    )
    monkeypatch.setattr(
        master_orchestrator,
        "run_script",
        lambda *args, **kwargs: False,
    )

    assert master_orchestrator.main(["--limit", "1", "--skip-cleansing"]) == 1


def test_orchestrator_does_not_launch_after_global_budget(monkeypatch):
    institution = {
        "id": "one",
        "name": "One",
        "slug": "one",
        "website_url": "https://example.com",
        "last_harvest_at": None,
    }
    monkeypatch.setenv(
        "JOB_START_TIME",
        str(time.time() - master_orchestrator.MAX_RUN_SECONDS - 1),
    )
    monkeypatch.setattr(
        master_orchestrator,
        "get_institutions",
        lambda **kwargs: [institution],
    )

    def unexpected_run(*args, **kwargs):
        raise AssertionError("stage launched after global budget")

    monkeypatch.setattr(master_orchestrator, "run_script", unexpected_run)

    assert master_orchestrator.main(["--limit", "1", "--skip-cleansing"]) == 1


def test_run_script_fails_closed_on_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], timeout=1)

    monkeypatch.setattr(master_orchestrator.subprocess, "run", timeout)
    assert not master_orchestrator.run_script("worker.py", timeout=1)


def test_fg1_fg3_workflow_governance():
    fg1 = (ROOT / ".github/workflows/fg1_inventory.yml").read_text(
        encoding="utf-8"
    )
    fg2 = (ROOT / ".github/workflows/production_pipeline.yml").read_text(
        encoding="utf-8"
    )
    fg3 = (ROOT / ".github/workflows/fg3_integrity.yml").read_text(
        encoding="utf-8"
    )

    assert "DESACTIVADO" not in fg1 + fg3
    assert "timeout-minutes: 60" in fg1
    assert "permissions:\n  contents: read" in fg1
    assert "permissions:\n  contents: read" in fg3
    assert "persist-credentials: false" in fg1
    assert "persist-credentials: false" in fg3
    assert "refs/heads/main" in fg1
    assert "refs/heads/main" in fg2
    assert "refs/heads/main" in fg3
    assert "github.ref)" in fg1
    assert "github.ref)" in fg2
    assert "github.ref)" in fg3
    assert "github.ref_name)" not in fg1
    assert "github.ref_name)" not in fg2
    assert "github.ref_name)" not in fg3
    assert "pip install --require-hashes -r requirements-fg1.txt" in fg1
    assert "pip install --require-hashes -r requirements-fg3.txt" in fg3
    assert "cron: '0 5 * * *'" in fg2
    assert "cron: '0 11 * * *'" in fg3
    assert "group: studiamatch-fg2-${{ github.ref }}" in fg2
    assert "group: studiamatch-fg2-${{ github.ref }}" in fg3


def test_security_audit_blocks_on_f7_and_frontend_build():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(
        encoding="utf-8"
    )

    assert "name: FASE-07 G1b Contract" in workflow
    assert "python3 -m pytest -q tests/test_fase07_g1b.py" in workflow
    assert "name: Frontend Static Build" in workflow
    assert "node-version: '22'" in workflow
    assert "continue-on-error: true" not in workflow
    assert "F7: ${{ needs.fase07-g1b.result }}" in workflow
    assert "BUILD: ${{ needs.frontend-build.result }}" in workflow


def test_target_parity_requires_fase07_ledger_and_verifier():
    parity = (ROOT / "scripts/maintenance/check_db_parity.py").read_text(
        encoding="utf-8"
    )

    assert '"20260725_fase07_g1b_closure"' in parity
    assert '"verify_fase07_g1b_closure"' in parity


def test_applied_manifest_entry_rechecks_postcondition():
    class Database:
        def __init__(self):
            self.calls = []

        def rpc_raise(self, name, params):
            self.calls.append((name, params))
            return True

    database = Database()
    db_migrate.verify_applied_postcondition(
        database, "20260725_fase07_g1b_closure"
    )

    assert database.calls == [("verify_fase07_g1b_closure", {})]
