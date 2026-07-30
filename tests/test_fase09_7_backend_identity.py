from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock

import pytest

if "curl_cffi" not in sys.modules and importlib.util.find_spec("curl_cffi") is None:
    curl_cffi = types.ModuleType("curl_cffi")
    curl_cffi.__path__ = []
    curl_requests = types.ModuleType("curl_cffi.requests")
    curl_requests.AsyncSession = object
    sys.modules["curl_cffi"] = curl_cffi
    sys.modules["curl_cffi.requests"] = curl_requests

if "bs4" not in sys.modules and importlib.util.find_spec("bs4") is None:
    bs4 = types.ModuleType("bs4")
    bs4.BeautifulSoup = object
    sys.modules["bs4"] = bs4

from scripts.core import discovery_institutions, integrity_ping, universal_harvester
from scripts.maintenance import (
    category_coverage_audit,
    quality_assurance_audit,
    taxonomy_roi_audit,
)
from scripts.shared import db_client as db_client_module
from scripts.shared.db_client import DatabaseAPIError, DatabaseClient


ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


@pytest.mark.parametrize("status_code", [200, 206])
def test_count_service_raise_uses_secret_identity_and_exact_count(
    monkeypatch,
    status_code,
):
    response = Mock(
        status_code=status_code,
        headers={"Content-Range": "*/17"},
    )
    request = Mock(return_value=response)
    monkeypatch.setattr(db_client_module, "_request_with_retry", request)
    client = DatabaseClient(
        "https://explicit.supabase.co",
        "sb_secret_explicit",
    )

    count = client.count_service_raise(
        "courses",
        filters="is_active=eq.true&is_verified=eq.true",
    )

    assert count == 17
    method, url = request.call_args.args
    headers = request.call_args.kwargs["headers"]
    assert method is db_client_module.requests.get
    assert url.endswith(
        "/rest/v1/courses?select=id&limit=0"
        "&is_active=eq.true&is_verified=eq.true"
    )
    assert headers["apikey"] == "sb_secret_explicit"
    assert headers["Prefer"] == "count=exact"
    assert "Authorization" not in headers


@pytest.mark.parametrize(
    ("status_code", "content_range", "message"),
    [
        (500, "*/17", "HTTP 500"),
        (200, "", "Content-Range"),
        (206, "*/*", "invalid"),
        (200, "*/-1", "invalid"),
    ],
)
def test_count_service_raise_fails_closed_on_unproven_count(
    monkeypatch,
    status_code,
    content_range,
    message,
):
    response = Mock(
        status_code=status_code,
        headers={"Content-Range": content_range},
        text="sensitive-response-body",
    )
    monkeypatch.setattr(
        db_client_module,
        "_request_with_retry",
        Mock(return_value=response),
    )
    client = DatabaseClient(
        "https://explicit.supabase.co",
        "sb_secret_explicit",
    )

    with pytest.raises(DatabaseAPIError, match=message) as exc_info:
        client.count_service_raise("courses")

    assert "sensitive-response-body" not in str(exc_info.value)


def test_automatic_fg_readers_use_explicit_backend_identities():
    expected_markers = {
        "scripts/core/discovery_institutions.py": (
            "select_all_service(",
            "select_service_raise(",
        ),
        "scripts/core/master_orchestrator.py": (
            "select_service_raise(",
            "select_pipeline_raise(",
            "count_pipeline_raise(",
        ),
        "scripts/core/universal_harvester.py": ("select_pipeline_raise(",),
        "scripts/core/cleansing_worker.py": (
            "select_service_raise(",
            "select_pipeline_raise(",
        ),
        "scripts/core/enrichment_worker.py": (
            "select_service_raise(",
            "select_pipeline_raise(",
        ),
        "scripts/core/sync_vector_worker.py": (
            "select_service_raise(",
            "select_pipeline_raise(",
            "lookup_market_salary_service as lookup_market_salary",
        ),
        "scripts/core/integrity_ping.py": (
            "count_service_raise(",
            "select_service_raise(",
            "select_all_service(",
        ),
        "scripts/maintenance/quality_assurance_audit.py": (
            "select_all_service(",
        ),
        "scripts/maintenance/taxonomy_roi_audit.py": (
            "select_all_service(",
        ),
        "scripts/maintenance/category_coverage_audit.py": (
            "select_all_service(",
        ),
    }
    forbidden_markers = (
        ".db.select(",
        ".db.select_all(",
        ".db.select_raise(",
        ".db.select_pipeline(",
        "db.select(",
        "db.select_all(",
        "db.select_raise(",
        "db.select_pipeline(",
    )

    for relative_path, markers in expected_markers.items():
        source = _source(relative_path)
        for marker in markers:
            assert marker in source, f"{relative_path} is missing {marker}"
        for marker in forbidden_markers:
            assert marker not in source, f"{relative_path} still uses {marker}"


def test_fg3_and_fg2_filters_use_postgrest_top_level_conjunction():
    fg3 = _source("scripts/core/integrity_ping.py")
    fg2 = _source("scripts/core/universal_harvester.py")

    assert "start_date=lt.{grace_cutoff}&is_active=eq.true" in fg3
    assert "start_date=lt.{grace_cutoff},is_active=eq.true" not in fg3
    assert '"&status=in.(processed,discarded,discovered)"' in fg2
    assert "institution_id=eq.{inst_id},status=" not in fg2


def test_phase_4_backend_audits_receive_only_secret_database_identity():
    workflow = _source(".github/workflows/production_pipeline.yml")
    phase_4 = workflow.split("phase_4_audit:", 1)[1]

    for step_name in (
        "Quality Assurance Audit",
        "Taxonomy & ROI Audit",
        "Category Coverage Audit",
    ):
        step = phase_4.split(f"- name: {step_name}", 1)[1].split(
            "- name:", 1
        )[0]
        assert "NEXT_SUPABASE_SECRET_KEY:" in step
        assert "NEXT_SUPABASE_PUBLISHABLE_KEY:" not in step
        assert "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:" not in step

    for workflow_path in (
        ".github/workflows/fg1_inventory.yml",
        ".github/workflows/fg3_integrity.yml",
        ".github/workflows/production_pipeline.yml",
    ):
        automatic_workflow = _source(workflow_path)
        assert "NEXT_SUPABASE_PUBLISHABLE_KEY:" not in automatic_workflow
        assert "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:" not in automatic_workflow


def test_fg2_secret_workflow_uses_pinned_least_privilege_actions():
    workflow = _source(".github/workflows/production_pipeline.yml")
    checkout = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
    setup_python = (
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
    )
    upload_artifact = (
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
    )
    phase_4 = workflow.split("phase_4_audit:", 1)[1]
    install_step = phase_4.split("- name: Install Dependencies", 1)[1].split(
        "- name:", 1
    )[0]

    assert "permissions:\n  contents: read" in workflow
    assert "permissions:\n      contents: read" in phase_4
    assert workflow.count(checkout) == 5
    assert workflow.count("persist-credentials: false") == 5
    assert workflow.count(setup_python) == 5
    assert "actions/checkout@v4" not in workflow
    assert "actions/setup-python@v5" not in workflow
    assert "actions/cache@" not in workflow
    assert upload_artifact in phase_4
    assert "actions/upload-artifact@v4" not in phase_4
    assert (
        "pip install --require-hashes -r requirements-db-migrate.txt"
        in install_step
    )
    assert "requirements.txt" not in install_step
    assert "pip install -r requirements.txt" not in workflow
    assert workflow.count(
        "pip install --require-hashes -r requirements-pipeline.txt"
    ) == 4


@pytest.mark.parametrize(
    "audit_module",
    [
        quality_assurance_audit,
        taxonomy_roi_audit,
        category_coverage_audit,
    ],
)
def test_phase_4_audits_reproduce_public_visibility(audit_module):
    database = Mock()

    def select_all_service(table, **kwargs):
        if table == "institution_site_profiles":
            return [{"institution_id": "production-inst"}]
        if table == "courses":
            return [
                {
                    "id": "visible",
                    "institution_id": "production-inst",
                    "name": "Visible",
                },
                {
                    "id": "hidden",
                    "institution_id": "disabled-inst",
                    "name": "Hidden",
                },
            ]
        raise AssertionError(f"Unexpected table: {table}")

    database.select_all_service.side_effect = select_all_service

    courses = audit_module._load_public_visible_courses(database)

    assert [course["id"] for course in courses] == ["visible"]
    profile_call, course_call = database.select_all_service.call_args_list
    assert profile_call.args == ("institution_site_profiles",)
    assert profile_call.kwargs["filters"] == "production_enabled=eq.true"
    assert profile_call.kwargs["columns"] == "institution_id"
    assert course_call.args == ("courses",)
    assert course_call.kwargs["filters"] == (
        "is_active=eq.true&is_verified=eq.true"
        "&publication_status=eq.publicado"
    )
    assert "institution_id" in course_call.kwargs["columns"].split(",")


@pytest.mark.parametrize(
    "audit_module",
    [
        quality_assurance_audit,
        taxonomy_roi_audit,
        category_coverage_audit,
    ],
)
def test_phase_4_visibility_reads_fail_closed(audit_module):
    database = Mock()
    database.select_all_service.side_effect = [
        [{"institution_id": "production-inst"}],
        DatabaseAPIError("catalog read unavailable"),
    ]

    with pytest.raises(DatabaseAPIError, match="catalog read unavailable"):
        audit_module._load_public_visible_courses(database)


def test_fg1_backend_read_failure_propagates(monkeypatch):
    database = Mock()
    database.select_service_raise.side_effect = DatabaseAPIError(
        "backend read unavailable"
    )
    monkeypatch.setattr(discovery_institutions, "db", database)
    monkeypatch.setattr(
        discovery_institutions,
        "load_sources",
        lambda: [{"name": "Example", "url": "https://example.edu/"}],
    )

    with pytest.raises(DatabaseAPIError, match="backend read unavailable"):
        discovery_institutions.run_discovery()
    database.insert.assert_not_called()


def test_fg2_backend_read_failure_propagates(monkeypatch):
    database = Mock()
    database.select_pipeline_raise.side_effect = DatabaseAPIError(
        "backend read unavailable"
    )
    harvester = universal_harvester.UniversalHarvester.__new__(
        universal_harvester.UniversalHarvester
    )
    harvester.db = database
    harvester.institution = {"id": "institution-id"}

    with pytest.raises(DatabaseAPIError, match="backend read unavailable"):
        asyncio.run(harvester._load_existing_urls())


def test_fg2_phase_4_read_failure_propagates(monkeypatch):
    database = Mock()
    database.select_all_service.side_effect = DatabaseAPIError(
        "backend read unavailable"
    )
    monkeypatch.setattr(quality_assurance_audit, "db", database)

    with pytest.raises(DatabaseAPIError, match="backend read unavailable"):
        quality_assurance_audit.run_audit()


def test_fg3_read_failure_propagates(monkeypatch):
    read_failure = Mock()
    read_failure.count_service_raise.side_effect = DatabaseAPIError(
        "backend read unavailable"
    )
    monkeypatch.setattr(integrity_ping, "get_db_client", lambda: read_failure)

    with pytest.raises(DatabaseAPIError, match="backend read unavailable"):
        integrity_ping.run_integrity_ping()


def test_frontend_and_public_surface_audits_keep_publishable_identity():
    frontend = _source("web/src/lib/supabase.ts")
    build_helper = _source("web/tests/buildWithLocalSupabaseStub.mjs")
    security_audit = _source(".github/workflows/security-audit.yml")
    f9_7_contract = _source(".github/workflows/f9-7-contract.yml")
    sitemap = _source("scripts/maintenance/generate_sitemap.py")

    assert "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" in frontend
    assert "NEXT_SUPABASE_SECRET_KEY" not in frontend
    assert "sb_publishable_ci_test" in build_helper
    assert "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" in build_helper
    assert "node tests/buildWithLocalSupabaseStub.mjs" in security_audit
    assert "node tests/buildWithLocalSupabaseStub.mjs" in f9_7_contract
    assert "sb_publishable_ci_test" not in security_audit
    assert "sb_publishable_ci_test" not in f9_7_contract
    assert "db.select_all('courses'" in sitemap
    assert "select_all_service" not in sitemap
