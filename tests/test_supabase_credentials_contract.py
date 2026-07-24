from pathlib import Path
import re

import pytest

from scripts.shared.db_client import DatabaseClient
from scripts.maintenance import pipeline_canary
from scripts.shared.supabase_credentials import (
    SupabaseCredentialError,
    build_supabase_headers,
    get_publishable_key,
    get_secret_key,
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

APPROVED_BEARERS = {
    "scripts/shared/supabase_credentials.py": {
        "identities": {"access_token"},
        "provider": "supabase-data-api",
        "provider_marker": 'headers = {"apikey": key}',
        "provider_env": "NEXT_SUPABASE_ACCESS_TOKEN",
        "derivation_marker": 'access_token = env.get("NEXT_SUPABASE_ACCESS_TOKEN", "")',
    },
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
    "scripts/maintenance/release_gate.py": {
        "identities": {"github_token"},
        "provider": "github-api",
        "provider_marker": "api.github.com",
        "provider_env": "GITHUB_TOKEN",
        "derivation_marker": 'os.environ.get("GITHUB_TOKEN", "")',
    },
    "scripts/maintenance/verify_pro_schema.py": {
        "identities": {"supabase_management_token"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "supabase_management_token = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
    "db/migrations/apply_cleansing_fix_pro.py": {
        "identities": {"MGMT_TOKEN"},
        "provider": "supabase-management-api",
        "provider_marker": "api.supabase.com",
        "provider_env": "SUPABASE_MGMT_TOKEN",
        "derivation_marker": "MGMT_TOKEN = os.environ.get('SUPABASE_MGMT_TOKEN', '')",
    },
    "supabase/functions/send-lead-emails/index.ts": {
        "identities": {"RESEND_API_KEY"},
        "provider": "resend-api",
        "provider_marker": "api.resend.com",
        "provider_env": "RESEND_API_KEY",
        "derivation_marker": 'RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")',
    },
    ".github/workflows/production_pipeline.yml": {
        "identities": {"CF_API_TOKEN"},
        "provider": "cloudflare-api",
        "provider_marker": "api.cloudflare.com",
        "provider_env": "CF_API_TOKEN",
        "derivation_marker": "CF_API_TOKEN: ${{ secrets.CF_API_TOKEN }}",
    },
    "tests/release_gate/test_pipeline_canary_contract.py": {
        "identities": {"restricted-token"},
        "provider": "supabase-data-api-test",
        "provider_marker": "pipeline_canary.StrictRest",
        "provider_env": "NEXT_SUPABASE_ACCESS_TOKEN",
        "derivation_marker": 'monkeypatch.setenv("NEXT_SUPABASE_ACCESS_TOKEN", "restricted-token")',
    },
}

DIRECT_SUPABASE_CONSUMERS = {
    "scripts/shared/supabase_credentials.py": "supabase-data-api",
    "scripts/shared/db_client.py": "supabase-data-api",
    "scripts/shared/utils.py": "supabase-data-api",
    "scripts/maintenance/audit_url_slugs.py": "supabase-data-api",
    "scripts/maintenance/category_audit_report.py": "supabase-data-api",
    "scripts/maintenance/check_db_parity.py": "supabase-data-api",
    "scripts/maintenance/check_pro_data.py": "supabase-data-api",
    "scripts/maintenance/db_migrate.py": "supabase-data-api",
    "scripts/maintenance/dedup_integrity_audit.py": "supabase-data-api",
    "scripts/maintenance/diag_pro.py": "supabase-data-api",
    "scripts/maintenance/diag_schema_diff.py": "supabase-data-and-management-api",
    "scripts/maintenance/fase62b_create_pucp_and_sync_pro.py": "supabase-data-api",
    "scripts/maintenance/fase74_seed_pro.py": "supabase-data-api",
    "scripts/maintenance/lightweight_ping.py": "supabase-data-api",
    "scripts/maintenance/metadata_quality_report.py": "supabase-data-api",
    "scripts/maintenance/migrate_data_to_pro.py": "supabase-data-and-management-api",
    "scripts/maintenance/migrate_rpcs_to_pro.py": "supabase-management-api",
    "scripts/maintenance/pipeline_canary.py": "supabase-data-api",
    "scripts/maintenance/pucp_sync_to_pro.py": "supabase-data-api",
    "scripts/maintenance/seed_institutions.py": "supabase-data-api",
    "scripts/maintenance/seed_pro_profiles.py": "supabase-data-api",
    "scripts/maintenance/sync_pro_to_free.py": "supabase-data-api",
    "scripts/maintenance/test_inst_insert.py": "supabase-data-api",
    "scripts/maintenance/verify_pro_schema.py": "supabase-management-api",
    "web/src/lib/supabase.ts": "supabase-data-api",
    "web/src/app/HomeContent.tsx": "supabase-data-api",
    "web/src/app/page.tsx": "supabase-data-api",
    "web/src/app/compare/CompareContent.tsx": "supabase-data-api",
    "web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx": "supabase-data-api",
    "web/src/app/courses/[institution]/[slug]/page.tsx": "supabase-data-api",
    "supabase/functions/send-lead-emails/index.ts": "supabase-edge-function",
    ".github/workflows/production_pipeline.yml": "supabase-ci",
    ".github/workflows/pipeline-canary.yml": "supabase-ci",
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
    '"apikey"',
    "'apikey'",
    "api.supabase.com",
)


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


@pytest.mark.parametrize(
    ("kind", "api_key"),
    [("publishable", "sb_publishable_x"), ("secret", "sb_secret_x")],
)
def test_api_keys_are_sent_only_as_apikey(kind, api_key):
    headers = build_supabase_headers(api_key, kind=kind)

    assert headers["apikey"] == api_key
    assert "Authorization" not in headers


def test_authorization_uses_only_a_separate_access_token():
    headers = build_supabase_headers(
        "sb_publishable_x",
        kind="publishable",
        access_token="worker-access-token",
    )

    assert headers["apikey"] == "sb_publishable_x"
    assert headers["Authorization"] == "Bearer worker-access-token"

    with pytest.raises(SupabaseCredentialError, match="separate access token"):
        build_supabase_headers(
            "sb_publishable_x",
            kind="publishable",
            access_token="sb_secret_x",
        )


def test_database_client_separates_api_keys_from_bearer(monkeypatch):
    monkeypatch.setenv("NEXT_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_x")
    monkeypatch.setenv("NEXT_SUPABASE_SECRET_KEY", "sb_secret_x")
    monkeypatch.delenv("NEXT_SUPABASE_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("STUDIAMATCH_CANARY_WORKER", raising=False)

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


@pytest.mark.parametrize(
    ("public", "expected_key"),
    [(False, "sb_secret_x"), (True, "sb_publishable_x")],
)
def test_strict_rest_api_keys_are_apikey_only(monkeypatch, public, expected_key):
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

    assert api._request("GET", "courses", public=public) == []
    assert captured["apikey"] == expected_key
    assert "Authorization" not in captured


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


def test_every_bearer_is_approved_by_path_identity_and_provider():
    findings = []
    observed_paths = set()

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
        if relative.startswith("tests/"):
            continue
        source = path.read_text(encoding="utf-8-sig")
        if relative.startswith("supabase/functions/") or any(
            marker in source for marker in SUPABASE_CONSUMER_MARKERS
        ):
            discovered.add(relative)

    assert discovered == set(DIRECT_SUPABASE_CONSUMERS)
