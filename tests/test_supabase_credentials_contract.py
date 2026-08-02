from pathlib import Path
import os
import re
import subprocess
import sys
from unittest.mock import Mock

import pytest

from scripts.shared import db_client as db_client_module
from scripts.maintenance import migrate_data_to_pro as migration_module
from scripts.shared.db_client import DatabaseAPIError, DatabaseClient
from scripts.shared.supabase_credentials import (
    SupabaseCredentialError,
    build_supabase_headers,
    get_environment_credentials,
    get_publishable_key,
    get_secret_key,
    require_distinct_environments,
    validate_api_key,
)


ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()
SOURCE_PATTERNS = (
    "scripts/**/*.py",
    "scripts/**/*.sh",
    "tests/**/*.py",
    "web/src/**/*.ts",
    "web/src/**/*.tsx",
    "supabase/functions/**/*.ts",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".github/scripts/*.sh",
    ".githooks/*",
    "db/migrations/*.py",
    "*.py",
    "*.sh",
    "web/*.js",
    "web/*.ts",
)
SOURCE_FILES = tuple(
    sorted(
        {
            path.resolve()
            for pattern in SOURCE_PATTERNS
            for path in ROOT.glob(pattern)
            if path.is_file() and path.resolve() != THIS_FILE
        }
    )
)

FORBIDDEN_LEGACY_KEY_NAMES = {
    "NEXT_PUBLIC_SUPABASE_" + "ANON_KEY",
    "SUPABASE_" + "ANON_KEY",
    "SUPABASE_" + "KEY",
    "SUPABASE_PRO_" + "PUBLISHABLE_KEY",
    "SUPABASE_PRO_" + "SECRET_KEY",
    "SUPABASE_" + "SERVICE_ROLE_KEY",
}

BEARER_IDENTITY_PATTERN = re.compile(
    r"Bearer\s+(?:\$\{(?P<template>[A-Za-z_][A-Za-z0-9_.]*)\}"
    r"|\{(?P<braced>[A-Za-z_][A-Za-z0-9_.]*)\}"
    r"|(?P<literal>[A-Za-z0-9_-]+))"
    r"|Bearer\s*[\"']\s*\+\s*(?P<concat>[A-Za-z_][A-Za-z0-9_.]*)",
    re.IGNORECASE,
)

# Bearer is denied unless path, runtime identity, provider and source variable
# all match this closed inventory.
APPROVED_BEARERS = {
    "scripts/core/enrichment_worker.py": {
        "identities": {"CF_API_TOKEN"},
        "provider": "cloudflare-workers-ai",
        "provider_marker": "api.cloudflare.com",
        "provider_env": "CF_API_TOKEN",
        "derivation_marker": 'CF_API_TOKEN = os.getenv("CF_API_TOKEN")',
    },
    "scripts/maintenance/diag_schema_diff.py": {
        "identities": {"MGMT_TOKEN"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
    "scripts/maintenance/migrate_data_to_pro.py": {
        "identities": {"MGMT_TOKEN"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
    "scripts/maintenance/migrate_rpcs_to_pro.py": {
        "identities": {"supabase_management_token"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "supabase_management_token = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
    "scripts/maintenance/verify_pro_schema.py": {
        "identities": {"supabase_management_token"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "supabase_management_token = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
    "scripts/deprecated/fase32b_migrate_free_to_pro.py": {
        "identities": {"MGMT_TOKEN"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
    "db/migrations/apply_cleansing_fix_pro.py": {
        "identities": {"MGMT_TOKEN"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
}

APPROVED_BEARER_TEST_LITERALS = {
    "tests/test_frontend_public_surfaces_playwright.py": {"blocked"},
}

DIRECT_SUPABASE_CONSUMERS = {
    "tests/test_fase09_7_backend_identity.py": "supabase-data-api-test",
    "tests/test_fase09_7_schema_rls.py": "supabase-data-api-test",
    "tests/test_frontend_public_surfaces_playwright.py": "supabase-data-api-test",
    "tests/test_harvester.py": "supabase-data-api-test",
    "scripts/core/cleansing_worker.py": "supabase-data-api",
    "scripts/core/certification_canary_manifest.py": "supabase-data-api",
    "scripts/core/discovery_institutions.py": "supabase-data-api",
    "scripts/core/enrichment_worker.py": "supabase-data-api",
    "scripts/core/integrity_ping.py": "supabase-data-api",
    "scripts/core/master_orchestrator.py": "supabase-data-api",
    "scripts/core/sync_vector_worker.py": "supabase-data-api",
    "scripts/core/universal_harvester.py": "supabase-data-api",
    "scripts/shared/supabase_credentials.py": "supabase-data-api",
    "scripts/shared/db_client.py": "supabase-data-api",
    "scripts/shared/test_db_compatibility.py": "supabase-data-api",
    "scripts/shared/utils.py": "supabase-data-api",
    "scripts/maintenance/apply_noise_exclusions.py": "supabase-data-api",
    "scripts/maintenance/audit_url_slugs.py": "supabase-data-api",
    "scripts/maintenance/batch_enrich_courses.py": "supabase-data-api",
    "scripts/maintenance/category_audit_report.py": "supabase-data-api",
    "scripts/maintenance/category_coverage_audit.py": "supabase-data-api",
    "scripts/maintenance/check_db_parity.py": "supabase-data-api",
    "scripts/maintenance/check_pro_data.py": "supabase-data-api",
    "scripts/maintenance/db_migrate.py": "supabase-data-api",
    "scripts/maintenance/dedup_integrity_audit.py": "supabase-data-api",
    "scripts/maintenance/diag_pro.py": "supabase-data-api",
    "scripts/maintenance/diag_schema_diff.py": "supabase-data-and-management-api",
    "scripts/maintenance/diagnose_pro_db.py": "supabase-data-api",
    "scripts/maintenance/fase62_update_profiles.py": "supabase-data-api",
    "scripts/maintenance/fase62b_create_pucp_and_sync_pro.py": "supabase-data-api",
    "scripts/maintenance/fase74_seed_pro.py": "supabase-data-api",
    "scripts/maintenance/fix_taxonomy_roi.py": "supabase-data-api",
    "scripts/maintenance/force_harvest_up.py": "supabase-data-api",
    "scripts/maintenance/generate_sitemap.py": "supabase-data-api",
    "scripts/maintenance/lightweight_ping.py": "supabase-data-api",
    "scripts/maintenance/merge_exclusions_to_profiles.py": "supabase-data-api",
    "scripts/maintenance/metadata_quality_report.py": "supabase-data-api",
    "scripts/maintenance/migrate_data_to_pro.py": "supabase-data-and-management-api",
    "scripts/maintenance/migrate_rpcs_to_pro.py": "supabase-management-api",
    "scripts/maintenance/noise_discovery_engine.py": "supabase-data-api",
    "scripts/maintenance/preventive_cleanup.py": "supabase-data-api",
    "scripts/maintenance/pucp_sync_to_pro.py": "supabase-data-api",
    "scripts/maintenance/quality_assurance_audit.py": "supabase-data-api",
    "scripts/maintenance/review_autogen_profiles.py": "supabase-data-api",
    "scripts/maintenance/seed_institutions.py": "supabase-data-api",
    "scripts/maintenance/seed_pro_profiles.py": "supabase-data-api",
    "scripts/maintenance/seed_site_profiles.py": "supabase-data-api",
    "scripts/maintenance/sync_pro_to_free.py": "supabase-data-api",
    "scripts/maintenance/taxonomy_roi_audit.py": "supabase-data-api",
    "scripts/maintenance/test_inst_insert.py": "supabase-data-api",
    "scripts/maintenance/validate_dmc_pro_coverage.py": "supabase-data-api",
    "scripts/maintenance/validate_profile_extraction_config.py": "supabase-data-api",
    "scripts/maintenance/verify_pro_schema.py": "supabase-management-api",
    "scripts/deprecated/add_exclusion.py": "supabase-data-api",
    "scripts/deprecated/fase32b_migrate_free_to_pro.py": "supabase-data-and-management-api",
    "scripts/deprecated/seed_crawler_exclusions.py": "supabase-data-api",
    "scripts/deprecated/harvesters/continental_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/idat_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/nacional_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/new-horizons-peru_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/pucp_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/senati_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/smartdata_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/ulima_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/upc_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/usil_harvester.py": "supabase-data-api",
    "scripts/deprecated/harvesters/utp_harvester.py": "supabase-data-api",
    "web/src/lib/supabase.ts": "supabase-data-api",
    "web/src/app/HomeContent.tsx": "supabase-data-api",
    "web/src/app/page.tsx": "supabase-data-api",
    "web/src/app/compare/CompareContent.tsx": "supabase-data-api",
    "web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx": "supabase-data-api",
    "web/src/app/courses/[institution]/[slug]/page.tsx": "supabase-data-api",
    "supabase/functions/send-lead-emails/index.ts": "supabase-edge-function",
    ".github/workflows/f9_9_certification_canary.yml": "supabase-ci",
    ".github/workflows/production_pipeline.yml": "supabase-ci",
    ".github/workflows/fg1_inventory.yml": "supabase-ci",
    ".github/workflows/fg3_integrity.yml": "supabase-ci",
    ".github/workflows/db-sync-to-pro.yml": "supabase-ci",
    "db/migrations/apply_cleansing_fix_pro.py": "supabase-management-api",
}

SUPABASE_CONSUMER_MARKERS = (
    "NEXT_SUPABASE_PUBLISHABLE_KEY",
    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
    "NEXT_SUPABASE_SECRET_KEY",
    "get_publishable_key",
    "get_secret_key",
    "validate_api_key",
    "build_supabase_headers",
    "get_db_client",
    "DatabaseClient",
    "shared.db_client",
    "/rest/v1",
    '"apikey"',
    "'apikey'",
    "api.supabase.com",
)

PRO_EXPLICIT_DATA_API_SCRIPTS = {
    "scripts/maintenance/check_pro_data.py",
    "scripts/maintenance/diag_pro.py",
    "scripts/maintenance/diagnose_pro_db.py",
    "scripts/maintenance/fase74_seed_pro.py",
    "scripts/maintenance/validate_dmc_pro_coverage.py",
}

CROSS_ENVIRONMENT_DATA_API_SCRIPTS = {
    "scripts/deprecated/add_exclusion.py",
    "scripts/deprecated/fase32b_migrate_free_to_pro.py",
    "scripts/maintenance/check_db_parity.py",
    "scripts/maintenance/diag_schema_diff.py",
    "scripts/maintenance/fase62b_create_pucp_and_sync_pro.py",
    "scripts/maintenance/migrate_data_to_pro.py",
    "scripts/maintenance/pucp_sync_to_pro.py",
    "scripts/maintenance/seed_pro_profiles.py",
    "scripts/maintenance/sync_pro_to_free.py",
    "scripts/maintenance/test_inst_insert.py",
}


def test_modern_api_key_prefixes_are_required():
    assert validate_api_key(
        "sb_publishable_x", kind="publishable", variable_name="publishable"
    ) == "sb_publishable_x"
    assert validate_api_key(
        "sb_secret_x", kind="secret", variable_name="secret"
    ) == "sb_secret_x"

    with pytest.raises(SupabaseCredentialError, match="sb_publishable_"):
        validate_api_key("legacy-value", kind="publishable", variable_name="publishable")
    with pytest.raises(SupabaseCredentialError, match="sb_secret_"):
        validate_api_key("legacy-value", kind="secret", variable_name="secret")
    with pytest.raises(SupabaseCredentialError, match="sb_publishable_"):
        validate_api_key(
            "sb_publishable_", kind="publishable", variable_name="publishable"
        )


def test_legacy_environment_variables_are_not_consumed():
    legacy_publishable_name = "_".join(
        ("NEXT", "PUBLIC", "SUPABASE", "ANON", "KEY")
    )
    legacy_secret_name = "_".join(("SUPABASE", "SERVICE", "ROLE", "KEY"))
    legacy_env = {
        legacy_publishable_name: "legacy-anon",
        legacy_secret_name: "legacy-service-role",
    }

    with pytest.raises(SupabaseCredentialError, match="NEXT_SUPABASE_PUBLISHABLE_KEY"):
        get_publishable_key(legacy_env)
    with pytest.raises(SupabaseCredentialError, match="NEXT_SUPABASE_SECRET_KEY"):
        get_secret_key(legacy_env)


def test_explicit_environment_credentials_validate_prefix_url_and_identity_separation():
    free = get_environment_credentials(
        "FREE",
        {
            "FREE_SUPABASE_URL": "https://free-ref.supabase.co",
            "FREE_NEXT_SUPABASE_SECRET_KEY": "sb_secret_free",
        },
    )
    pro = get_environment_credentials(
        "PRO",
        {
            "PRO_SUPABASE_URL": "https://pro-ref.supabase.co",
            "PRO_NEXT_SUPABASE_SECRET_KEY": "sb_secret_pro",
        },
    )
    require_distinct_environments(free, pro)
    assert free.url == "https://free-ref.supabase.co"

    with pytest.raises(SupabaseCredentialError, match="sb_secret_"):
        get_environment_credentials(
            "PRO",
            {
                "PRO_SUPABASE_URL": "https://pro-ref.supabase.co",
                "PRO_NEXT_SUPABASE_SECRET_KEY": "legacy-key",
            },
        )
    with pytest.raises(SupabaseCredentialError, match="must differ"):
        require_distinct_environments(
            free,
            get_environment_credentials(
                "PRO",
                {
                    "PRO_SUPABASE_URL": "https://pro-ref.supabase.co",
                    "PRO_NEXT_SUPABASE_SECRET_KEY": "sb_secret_free",
                },
            ),
        )
    with pytest.raises(SupabaseCredentialError, match="SUPABASE_URL.*must differ"):
        require_distinct_environments(
            free,
            get_environment_credentials(
                "PRO",
                {
                    "PRO_SUPABASE_URL": "https://free-ref.supabase.co/",
                    "PRO_NEXT_SUPABASE_SECRET_KEY": "sb_secret_other",
                },
            ),
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://project.supabase.co",
        "https://project.supabase.co/path",
        "https://project.supabase.co?query=value",
        "https://project.supabase.co.evil.example",
        "https://nested.project.supabase.co",
        "https://user@project.supabase.co",
        "https://project.supabase.co:443",
    ],
)
def test_explicit_environment_credentials_reject_noncanonical_urls(url):
    with pytest.raises(SupabaseCredentialError, match="<project-ref>"):
        get_environment_credentials(
            "FREE",
            {
                "FREE_SUPABASE_URL": url,
                "FREE_NEXT_SUPABASE_SECRET_KEY": "sb_secret_free",
            },
        )


@pytest.mark.parametrize(
    ("environ", "missing_name"),
    [
        ({}, "FREE_SUPABASE_URL"),
        (
            {"FREE_SUPABASE_URL": "https://free-ref.supabase.co"},
            "FREE_NEXT_SUPABASE_SECRET_KEY",
        ),
        (
            {"FREE_NEXT_SUPABASE_SECRET_KEY": "sb_secret_free"},
            "FREE_SUPABASE_URL",
        ),
    ],
)
def test_explicit_environment_credentials_reject_partial_pairs(
    environ,
    missing_name,
):
    with pytest.raises(SupabaseCredentialError, match=missing_name):
        get_environment_credentials("FREE", environ)


@pytest.mark.parametrize(
    ("kind", "api_key"),
    [("publishable", "sb_publishable_x"), ("secret", "sb_secret_x")],
)
def test_api_keys_are_sent_only_as_apikey(kind, api_key):
    headers = build_supabase_headers(api_key, kind=kind)

    assert headers["apikey"] == api_key
    assert "Authorization" not in headers


def test_data_api_helper_never_builds_bearer_authorization():
    headers = build_supabase_headers("sb_publishable_x", kind="publishable")

    assert "Authorization" not in headers


def test_database_client_separates_api_keys_from_bearer(monkeypatch):
    monkeypatch.setenv("NEXT_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x")
    monkeypatch.setenv("NEXT_SUPABASE_SECRET_KEY", "sb_secret_x")

    client = DatabaseClient("https://example.supabase.co")

    assert client._get_headers(use_service_role=False) == {
        "apikey": "sb_publishable_x",
        "Content-Type": "application/json",
    }
    assert client._get_headers(use_service_role=True) == {
        "apikey": "sb_secret_x",
        "Content-Type": "application/json",
    }


def test_database_client_rejects_malformed_configured_key(monkeypatch):
    monkeypatch.setenv("NEXT_SUPABASE_PUBLISHABLE_KEY", "legacy-value")
    monkeypatch.delenv("NEXT_SUPABASE_SECRET_KEY", raising=False)

    with pytest.raises(SupabaseCredentialError, match="sb_publishable_"):
        DatabaseClient("https://example.supabase.co")


def test_database_client_explicit_identity_does_not_inherit_process_keys(monkeypatch):
    monkeypatch.setenv("NEXT_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_process")
    monkeypatch.setenv("NEXT_SUPABASE_SECRET_KEY", "sb_secret_process")

    client = DatabaseClient(
        "https://explicit.supabase.co",
        "sb_secret_explicit",
    )

    assert client._get_headers(use_service_role=True)["apikey"] == "sb_secret_explicit"
    with pytest.raises(SupabaseCredentialError, match="publishable key"):
        client._get_headers(use_service_role=False)


@pytest.mark.parametrize("final_status", [200, 206])
def test_select_all_service_accumulates_206_page_and_final_page(
    monkeypatch,
    final_status,
):
    first_page = Mock(status_code=206)
    first_page.json.return_value = [{"id": "one"}, {"id": "two"}]
    final_page = Mock(status_code=final_status)
    final_page.json.return_value = [{"id": "three"}]
    responses = iter([first_page, final_page])
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs["headers"].copy()))
        return next(responses)

    monkeypatch.setattr(db_client_module, "_request_with_retry", fake_request)
    client = DatabaseClient(
        "https://explicit.supabase.co",
        "sb_secret_explicit",
    )

    result = client.select_all_service("courses", batch_size=2)

    assert result == [{"id": "one"}, {"id": "two"}, {"id": "three"}]
    assert [call[0] for call in calls] == [db_client_module.requests.get] * 2
    assert "limit=2&offset=0" in calls[0][1]
    assert "limit=2&offset=2" in calls[1][1]
    assert calls[0][2]["Range"] == "0-1"
    assert calls[1][2]["Range"] == "2-3"


def test_select_all_service_raises_safe_error_on_unexpected_status(
    monkeypatch,
):
    first_page = Mock(status_code=206)
    first_page.json.return_value = [{"id": "one"}, {"id": "two"}]
    failed_page = Mock(status_code=500, text="sensitive-response-body")
    failed_page.json.side_effect = AssertionError("unexpected response must not be parsed")
    responses = iter([first_page, failed_page])
    urls = []

    def fake_request(_method, url, **_kwargs):
        urls.append(url)
        return next(responses)

    monkeypatch.setattr(db_client_module, "_request_with_retry", fake_request)
    client = DatabaseClient(
        "https://explicit.supabase.co",
        "sb_secret_explicit",
    )

    with pytest.raises(DatabaseAPIError) as exc_info:
        client.select_all_service("courses", batch_size=2)

    assert "courses" in str(exc_info.value)
    assert "500" in str(exc_info.value)
    assert "sensitive-response-body" not in str(exc_info.value)
    assert len(urls) == 2
    assert "limit=2&offset=0" in urls[0]
    assert "limit=2&offset=2" in urls[1]


@pytest.mark.parametrize("status_code", [200, 206])
def test_select_all_service_returns_empty_list_for_valid_empty_table(
    monkeypatch,
    status_code,
):
    empty_page = Mock(status_code=status_code)
    empty_page.json.return_value = []
    request = Mock(return_value=empty_page)
    monkeypatch.setattr(db_client_module, "_request_with_retry", request)
    client = DatabaseClient(
        "https://explicit.supabase.co",
        "sb_secret_explicit",
    )

    result = client.select_all_service("courses", batch_size=2)

    assert result == []
    request.assert_called_once()


def test_migration_preflight_failure_makes_zero_pro_calls():
    db = Mock()
    failing_table = migration_module.MIGRATION_ORDER[-2]

    def read_free(table):
        if table == failing_table:
            raise DatabaseAPIError("safe Free read failure")
        return [{"source_table": table}]

    db.select_all_service.side_effect = read_free
    run_mgmt_sql_fn = Mock()
    upsert_pro_fn = Mock()

    with pytest.raises(DatabaseAPIError, match="safe Free read failure"):
        migration_module.execute_migration(
            db,
            run_mgmt_sql_fn=run_mgmt_sql_fn,
            upsert_pro_fn=upsert_pro_fn,
        )

    assert db.select_all_service.call_args_list == [
        ((table,), {}) for table in migration_module.MIGRATION_ORDER[:-1]
    ]
    run_mgmt_sql_fn.assert_not_called()
    upsert_pro_fn.assert_not_called()


def test_migration_uses_completed_snapshot_after_all_free_reads():
    events = []
    snapshots = {
        table: [{"source_table": table}]
        for table in migration_module.MIGRATION_ORDER
    }
    db = Mock()

    def read_free(table):
        events.append(("read", table))
        return snapshots[table]

    def run_mgmt_sql_fn(sql):
        events.append(("pro_sql", sql))
        return Mock(status_code=201)

    upsert_pro_fn = Mock(side_effect=lambda _table, rows: len(rows))
    db.select_all_service.side_effect = read_free

    total = migration_module.execute_migration(
        db,
        run_mgmt_sql_fn=run_mgmt_sql_fn,
        upsert_pro_fn=upsert_pro_fn,
    )

    assert total == len(migration_module.MIGRATION_ORDER)
    assert events[:len(migration_module.MIGRATION_ORDER)] == [
        ("read", table) for table in migration_module.MIGRATION_ORDER
    ]
    assert events[len(migration_module.MIGRATION_ORDER)][0] == "pro_sql"
    assert upsert_pro_fn.call_args_list == [
        ((table, snapshots[table]), {})
        for table in migration_module.MIGRATION_ORDER
    ]


def test_migration_aborts_on_failed_delete_before_any_upsert():
    db = Mock()
    db.select_all_service.return_value = []
    responses = iter([Mock(status_code=201), Mock(status_code=500)])
    run_mgmt_sql_fn = Mock(side_effect=lambda _sql: next(responses))
    upsert_pro_fn = Mock()

    with pytest.raises(RuntimeError, match="Pro DELETE failed.*500"):
        migration_module.execute_migration(
            db,
            run_mgmt_sql_fn=run_mgmt_sql_fn,
            upsert_pro_fn=upsert_pro_fn,
        )

    assert db.select_all_service.call_count == len(migration_module.MIGRATION_ORDER)
    assert run_mgmt_sql_fn.call_count == 2
    upsert_pro_fn.assert_not_called()


@pytest.mark.parametrize(
    ("pythonpath", "statement"),
    [
        (
            ROOT / "scripts",
            "import shared.db_client; import shared.utils; import shared.supabase_credentials",
        ),
        (
            ROOT,
            "import scripts.shared.db_client; import scripts.shared.utils; "
            "import scripts.shared.supabase_credentials",
        ),
    ],
)
def test_shared_modules_import_under_both_supported_package_names(pythonpath, statement):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(pythonpath)
    result = subprocess.run(
        [sys.executable, "-c", statement],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_all_maintenance_and_deprecated_consumers_bootstrap_before_shared_imports():
    findings = []
    for relative in DIRECT_SUPABASE_CONSUMERS:
        if not relative.startswith(("scripts/maintenance/", "scripts/deprecated/")):
            continue
        source = (ROOT / relative).read_text(encoding="utf-8-sig")
        shared_import_offsets = [
            offset
            for marker in ("from shared.", "from scripts.shared.")
            if (offset := source.find(marker)) >= 0
        ]
        if not shared_import_offsets:
            continue
        prefix = source[:min(shared_import_offsets)]
        if not any(marker in prefix for marker in ("sys.path.insert", "sys.path.append")):
            findings.append(f"{relative}: shared import precedes project path bootstrap")

    assert findings == []


@pytest.mark.parametrize(
    "script_args",
    [
        ["scripts/maintenance/category_audit_report.py"],
        ["scripts/deprecated/add_exclusion.py", "--help"],
        ["scripts/deprecated/harvesters/upc_harvester.py"],
    ],
)
def test_documented_script_execution_from_app_has_no_module_not_found(script_args):
    env = os.environ.copy()
    for name in (
        "NEXT_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_SUPABASE_SECRET_KEY",
        "FREE_NEXT_SUPABASE_SECRET_KEY",
        "PRO_NEXT_SUPABASE_SECRET_KEY",
    ):
        env.pop(name, None)
    result = subprocess.run(
        [sys.executable, *script_args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    combined = result.stdout + result.stderr
    assert "ModuleNotFoundError" not in combined, combined


def test_dual_environment_tool_requires_distinct_explicit_credentials():
    source = (ROOT / "scripts/deprecated/add_exclusion.py").read_text(encoding="utf-8")
    for variable_name in (
        "FREE_SUPABASE_URL",
        "FREE_NEXT_SUPABASE_SECRET_KEY",
        "PRO_SUPABASE_URL",
        "PRO_NEXT_SUPABASE_SECRET_KEY",
    ):
        assert variable_name in source
    assert "get_secret_key" not in source

    env = os.environ.copy()
    env.update(
        {
            "FREE_SUPABASE_URL": "https://same.supabase.co",
            "PRO_SUPABASE_URL": "https://same.supabase.co",
            "FREE_NEXT_SUPABASE_SECRET_KEY": "sb_secret_same",
            "PRO_NEXT_SUPABASE_SECRET_KEY": "sb_secret_same",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/deprecated/add_exclusion.py",
            "--db",
            "both",
            "--dry-run",
            "--institution",
            "test",
            "--pattern",
            "/test/",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode != 0
    assert "distinct URLs and secret keys" in result.stderr


def test_manual_pro_and_cross_environment_scripts_use_explicit_identities():
    findings = []
    for relative in sorted(PRO_EXPLICIT_DATA_API_SCRIPTS):
        source = (ROOT / relative).read_text(encoding="utf-8-sig")
        has_pro_identity = "'PRO'" in source or '"PRO"' in source
        if "get_environment_credentials" not in source or not has_pro_identity:
            findings.append(f"{relative}: missing explicit PRO identity")
        if "get_secret_key" in source:
            findings.append(f"{relative}: canonical secret fallback remains")

    for relative in sorted(CROSS_ENVIRONMENT_DATA_API_SCRIPTS):
        source = (ROOT / relative).read_text(encoding="utf-8-sig")
        has_free = any(
            marker in source
            for marker in (
                "FREE_NEXT_SUPABASE_SECRET_KEY",
                "get_environment_credentials('FREE')",
                'get_environment_credentials("FREE")',
            )
        )
        has_pro = any(
            marker in source
            for marker in (
                "PRO_NEXT_SUPABASE_SECRET_KEY",
                "get_environment_credentials('PRO')",
                'get_environment_credentials("PRO")',
            )
        )
        rejects_reuse = (
            "require_distinct_environments" in source
            or "FREE_URL == PRO_URL" in source
        )
        if not (has_free and has_pro and rejects_reuse):
            findings.append(f"{relative}: incomplete explicit cross-environment contract")

    assert findings == []


def test_environment_example_uses_only_explicit_pro_data_api_identity():
    source = (ROOT / ".env.example").read_text(encoding="utf-8-sig")
    legacy_pro_url_name = "SUPABASE_PRO_" + "URL="

    assert "PRO_SUPABASE_URL=" in source
    assert "PRO_NEXT_SUPABASE_SECRET_KEY=" in source
    assert legacy_pro_url_name not in source


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def test_executable_tree_rejects_legacy_supabase_key_names():
    findings = []
    for path in SOURCE_FILES:
        source = path.read_text(encoding="utf-8-sig")
        for forbidden in FORBIDDEN_LEGACY_KEY_NAMES:
            if forbidden in source:
                findings.append(f"{_relative(path)}: {forbidden}")

    assert findings == []


def test_every_bearer_is_approved_by_path_identity_provider_and_origin():
    findings = []
    observed_paths = set()

    assert all(
        approval["provider"] != "supabase-data-api"
        for approval in APPROVED_BEARERS.values()
    )

    for path in SOURCE_FILES:
        source = path.read_text(encoding="utf-8-sig")
        matches = list(BEARER_IDENTITY_PATTERN.finditer(source))
        bearer_count = len(re.findall(r"\bBearer\b", source, flags=re.IGNORECASE))
        if bearer_count != len(matches):
            findings.append(f"{_relative(path)}: unparsed Bearer construction")
            continue
        if not matches:
            continue

        relative = _relative(path)
        observed_paths.add(relative)
        approval = APPROVED_BEARERS.get(relative)
        if approval is None:
            approved_test_literals = APPROVED_BEARER_TEST_LITERALS.get(relative, set())
            identities = {next(group for group in match.groupdict().values() if group) for match in matches}
            contexts = [
                source[max(0, match.start() - 240):match.end() + 240]
                for match in matches
            ]
            if identities <= approved_test_literals and all(
                "Authorization" in context for context in contexts
            ):
                continue
            findings.append(f"{relative}: path is not approved for Bearer auth")
            continue
        if not approval["provider"] or approval["provider_marker"] not in source:
            findings.append(f"{relative}: approved provider marker is absent")
        if (
            not approval["provider_env"]
            or approval["provider_env"] not in source
            or approval["derivation_marker"] not in source
        ):
            findings.append(f"{relative}: approved identity has no provider derivation")
        for match in matches:
            identity = next(group for group in match.groupdict().values() if group)
            if identity not in approval["identities"]:
                findings.append(f"{relative}: unapproved Bearer identity {identity}")
            context = source[max(0, match.start() - 240):match.end() + 240]
            if "Authorization" not in context:
                findings.append(f"{relative}: Bearer is not bound to Authorization")

    stale_approvals = set(APPROVED_BEARERS) - observed_paths
    findings.extend(
        f"{path}: stale Bearer approval" for path in sorted(stale_approvals)
    )
    assert findings == []


def test_direct_supabase_consumer_inventory_is_complete():
    discovered = set()

    for path in SOURCE_FILES:
        relative = _relative(path)
        source = path.read_text(encoding="utf-8-sig")
        if relative.startswith("supabase/functions/") or any(
            marker in source for marker in SUPABASE_CONSUMER_MARKERS
        ):
            discovered.add(relative)

    assert discovered == set(DIRECT_SUPABASE_CONSUMERS)
    assert set(DIRECT_SUPABASE_CONSUMERS.values()) <= {
        "supabase-data-api",
        "supabase-management-api",
        "supabase-data-and-management-api",
        "supabase-edge-function",
        "supabase-ci",
        "supabase-data-api-test",
    }


def test_credential_scanners_block_real_supabase_publishable_keys():
    scanner_paths = [
        ROOT / ".github/workflows/security-audit.yml",
        ROOT / ".githooks/pre-commit",
        ROOT / ".githooks/pre-push",
    ]

    for path in scanner_paths:
        source = path.read_text(encoding="utf-8")
        assert "sb_publishable_[A-Za-z0-9_-]{20,}" in source
        assert "sb_secret_[A-Za-z0-9_-]{10,}" in source
