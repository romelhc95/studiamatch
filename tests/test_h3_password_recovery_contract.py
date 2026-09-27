from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web/src"
AUTH = WEB / "lib/admin-auth.ts"
RECOVERY = WEB / "app/admin/reset-password/page.tsx"
MIDDLEWARE = ROOT / "web/functions/_middleware.ts"
STATIC_SERVER = ROOT / "mock-server/static-server.js"


def test_recovery_route_uses_auth_only_and_never_onboarding_rpc():
    source = RECOVERY.read_text(encoding="utf-8")
    auth_source = AUTH.read_text(encoding="utf-8")

    assert "exchangeRecoveryCodeForSession" in source
    assert "consumeRecoverySessionFromHash" in source
    assert "getAuthSession" in source
    assert "updateAdminPassword(password)" in source
    assert "signOutAdmin" in source
    assert "completePasswordSetup" not in source
    assert "admin_complete_password_setup" not in source
    assert "acceptCurrentInvitation" not in source
    assert "adminRpc" not in source
    secret_key_marker = "NEXT_SUPABASE_" + "SECRET_KEY"
    assert secret_key_marker not in source
    assert secret_key_marker not in auth_source


def test_recovery_route_removes_callback_credentials_and_rejects_non_recovery_type():
    source = RECOVERY.read_text(encoding="utf-8")

    assert "window.history.replaceState" in source
    assert "callbackType !== 'recovery'" in source
    assert "access_token" not in source
    assert "refresh_token" not in source
    assert "window.location.assign" not in source
    assert "window.location.replace" not in source


def test_recovery_route_is_slash_normalized_in_runtime_and_mock_server():
    middleware = MIDDLEWARE.read_text(encoding="utf-8")
    static_server = STATIC_SERVER.read_text(encoding="utf-8")

    assert "/admin/reset-password" in middleware
    assert "/admin/reset-password" in static_server
