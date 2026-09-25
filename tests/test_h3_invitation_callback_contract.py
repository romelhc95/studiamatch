from pathlib import Path
import unittest

# This module is intentionally a source-level contract test and is inventoried
# by the credential contract as a test-only Supabase consumer.
SUPABASE_PATTERN_TEST_ONLY = True


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web/src"
AUTH = WEB / "lib/admin-auth.ts"
CALLBACK = WEB / "app/admin/auth/callback/page.tsx"
ACCEPT = WEB / "app/admin/accept-invite/page.tsx"
PASSWORD = WEB / "app/admin/setup-password/page.tsx"
MIDDLEWARE = ROOT / "web/functions/_middleware.ts"


def test_auth_client_uses_official_pkce_and_no_manual_token_exchange():
    source = AUTH.read_text(encoding="utf-8")

    assert "createClient" in (WEB / "lib/supabase.ts").read_text(encoding="utf-8")
    assert "flowType: 'pkce'" in (WEB / "lib/supabase.ts").read_text(encoding="utf-8")
    assert "exchangeCodeForSession" in source
    assert "updateUser({ password })" in source
    assert "NEXT_SUPABASE_SECRET_KEY" not in source
    assert "service_role" not in source


def test_callback_consumes_code_once_and_uses_fixed_internal_routes():
    source = CALLBACK.read_text(encoding="utf-8")

    assert "hasStarted" in source
    assert "searchParams.get('code')" in source
    assert "window.history.replaceState" in source
    assert "acceptCurrentInvitation" in source
    assert "router.replace('/admin/accept-invite/')" in source
    assert "searchParams.get('next')" not in source
    assert "searchParams.get(\"next\")" not in source
    assert "window.location" not in source


def test_callback_accepts_auth_invite_fragment_without_open_redirect():
    source = CALLBACK.read_text(encoding="utf-8")
    auth_source = AUTH.read_text(encoding="utf-8")

    assert "document.location.hash" in source
    assert "consumeInviteSessionFromHash" in source
    assert "new URLSearchParams(value)" in auth_source
    assert "access_token" in auth_source
    assert "refresh_token" in auth_source
    assert "router.replace('/admin/accept-invite/')" in source


def test_onboarding_pages_consume_status_and_never_send_password_to_rpc():
    accept_source = ACCEPT.read_text(encoding="utf-8")
    password_source = PASSWORD.read_text(encoding="utf-8")

    assert "getOnboardingStatus" in accept_source
    for state in ("expired", "revoked", "superseded", "password_pending"):
        assert state in accept_source
    assert "updateAdminPassword(password)" in password_source
    assert "completePasswordSetup()" in password_source
    assert "p_password" not in password_source
    assert "password: password" not in password_source


def test_new_admin_routes_are_slash_normalized():
    source = MIDDLEWARE.read_text(encoding="utf-8")
    for route in ("/admin/auth/callback", "/admin/accept-invite", "/admin/setup-password"):
        assert route in source


class H3InvitationCallbackContractTest(unittest.TestCase):
    def test_auth_client_uses_official_pkce_and_no_manual_token_exchange(self):
        test_auth_client_uses_official_pkce_and_no_manual_token_exchange()

    def test_callback_consumes_code_once_and_uses_fixed_internal_routes(self):
        test_callback_consumes_code_once_and_uses_fixed_internal_routes()

    def test_onboarding_pages_consume_status_and_never_send_password_to_rpc(self):
        test_onboarding_pages_consume_status_and_never_send_password_to_rpc()

    def test_new_admin_routes_are_slash_normalized(self):
        test_new_admin_routes_are_slash_normalized()

    def test_callback_accepts_auth_invite_fragment_without_open_redirect(self):
        test_callback_accepts_auth_invite_fragment_without_open_redirect()
