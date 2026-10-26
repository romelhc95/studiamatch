from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_onboarding_role_guard_uses_the_quota_wrapper_forbidden_status() -> None:
    migration = read(
        "db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql"
    )
    quota_migration = read("db/migrations/20261002_h3_admin_quotas.sql")

    assert "private.h3_quota_base_admin_list_members_onboarding()" in migration
    assert "public.admin_list_members_onboarding()" in migration
    assert "H3_QUOTA_WRAPPER_V1" in migration
    assert "RAISE EXCEPTION ''User is not an active admin'';" in migration
    assert "RAISE SQLSTATE ''42501'' USING MESSAGE = ''User is not an active admin'';" in migration
    assert "WHEN SQLSTATE=''42501'' THEN ''403''" in quota_migration
    assert "WHEN SQLSTATE=''42501'' THEN ''403''" in migration
    assert "EXECUTE function_definition;" in migration
    assert "DROP FUNCTION" not in migration.upper()
    assert "GRANT " not in migration.upper()
    assert "REVOKE " not in migration.upper()
    assert "public.admin_members" not in migration
    assert "UPDATE " not in migration.upper()


def test_quota_harness_checks_user_denial_and_admin_read_after_migration() -> None:
    harness = read("tests/sql/h3_admin_quota_harness.sql")

    assert "\\ir ../../db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql" in harness
    assert "quota-onboarding-user@local.test" in harness
    assert "current_setting('response.status', true) IS DISTINCT FROM '403'" in harness
    assert "User role unexpectedly read onboarding members" in harness
    assert "admin onboarding reader lost its authorized rows" in harness


def test_bff_maps_http_403_to_safe_forbidden_without_changing_mfa_or_5xx() -> None:
    bff = read("web/functions/_lib/admin-bff.ts")
    mock = read("tests/h3_admin_bff_mock_uat.mjs")

    assert "const forbidden = rpcStatus === 403;" in bff
    assert "forbidden ? 'forbidden' : 'rpc_failed'" in bff
    assert "No tienes permisos para esta operación." in bff
    assert "unknown PostgREST failures must map to a gateway error" in mock
    assert "a server-side authorization denial keeps its forbidden HTTP status" in mock
    assert "MFA-required RPC failures retain their safe status" in mock
