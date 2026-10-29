from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web/src"
AUTH = WEB / "lib/admin-auth.ts"
CALLBACK = WEB / "app/admin/auth/callback/page.tsx"
ACCEPT = WEB / "app/admin/accept-invite/page.tsx"
PASSWORD = WEB / "app/admin/setup-password/page.tsx"
MIDDLEWARE = ROOT / "web/functions/_middleware.ts"
BFF = ROOT / "web/functions/_lib/admin-bff.ts"
SUPABASE_CLIENT = WEB / "lib/supabase.ts"
INVITE_TEMPLATE = ROOT / "supabase/templates/invite.html"
RECOVERY_TEMPLATE = ROOT / "supabase/templates/password-recovery.html"


def test_auth_client_uses_official_pkce_and_no_manual_token_exchange():
    source = AUTH.read_text(encoding="utf-8")
    browser_source = SUPABASE_CLIENT.read_text(encoding="utf-8")
    bff_source = BFF.read_text(encoding="utf-8")

    assert "createClient" in browser_source
    assert "flowType: 'pkce'" in browser_source
    assert "persistSession: false" in browser_source
    assert "flowType: 'pkce'" in bff_source
    assert "createServerClient" in bff_source
    assert "exchangeCodeForSession(code)" in bff_source
    assert "updateUser({ password })" in bff_source
    assert "encode: 'tokens-only'" not in bff_source
    assert "cannot supply MFA assurance checks on a later Pages Function request" in bff_source
    assert "httpOnly: true" in bff_source
    assert "access_token" not in source
    assert "refresh_token" not in source
    assert "Authorization" not in source
    assert "NEXT_SUPABASE_SECRET_KEY" not in source
    assert "NEXT_SUPABASE_SECRET_KEY" not in bff_source
    assert "service_role" not in source
    assert "service_role" not in bff_source


def test_callback_consumes_code_once_and_uses_fixed_internal_routes():
    source = CALLBACK.read_text(encoding="utf-8")
    bff_source = BFF.read_text(encoding="utf-8")
    get_callback = bff_source[bff_source.index("async function routeAuthCallback"):]

    assert "hasStarted" in source
    assert "searchParams.get('flow')" in source
    assert "getAuthSession" in source
    assert "window.history.replaceState" in source
    assert "acceptCurrentInvitation" in source
    assert "router.replace('/admin/accept-invite/')" in source
    assert "searchParams.get('next')" not in source
    assert "searchParams.get(\"next\")" not in source
    assert "window.location" not in source
    assert "url.searchParams.get('code')" in bff_source
    assert "url.searchParams.get('token_hash')" in bff_source
    assert "client.auth.verifyOtp" in bff_source
    assert "client.auth.exchangeCodeForSession(code)" in bff_source
    assert "'/admin/auth/callback/'" in bff_source
    assert "'/admin/reset-password/'" in bff_source
    assert "callbackConfirmationResponse(" in get_callback
    assert "client.auth.verifyOtp" not in get_callback
    assert "client.auth.exchangeCodeForSession" not in get_callback
    assert 'method="post" action="/api/admin/auth/callback"' in bff_source
    assert "readCallbackForm(request)" in bff_source
    assert "CALLBACK_CSRF_COOKIE" in bff_source
    assert "callbackCsrfMatches(request, body)" in bff_source
    assert "callbackMutationOriginAllowed(request)" in bff_source
    assert "name=\"callback_csrf\" value=\"${csrfToken}\"" in bff_source
    assert "if (providerError) return callbackErrorResponse();" in bff_source


def test_callback_keeps_tokens_server_side_without_open_redirect():
    source = CALLBACK.read_text(encoding="utf-8")
    auth_source = AUTH.read_text(encoding="utf-8")
    bff_source = BFF.read_text(encoding="utf-8")

    assert "document.location.hash" not in source
    assert "consumeInviteSessionFromHash" not in auth_source
    assert "token_hash" in bff_source
    assert "verifyOtp" in bff_source
    assert "url.origin}${pathname}${query}" in bff_source
    assert "window.location" not in source
    assert "router.replace('/admin/accept-invite/')" in source


def test_email_links_send_one_time_hash_to_the_allowlisted_bff_callback():
    invite = INVITE_TEMPLATE.read_text(encoding="utf-8")
    recovery = RECOVERY_TEMPLATE.read_text(encoding="utf-8")
    bff = BFF.read_text(encoding="utf-8")

    assert "{{ .RedirectTo }}?token_hash={{ .TokenHash }}&amp;type=invite" in invite
    assert "{{ .RedirectTo }}?token_hash={{ .TokenHash }}&amp;type=recovery" in recovery
    assert ".ConfirmationURL" not in invite
    assert ".ConfirmationURL" not in recovery
    assert "type !== 'invite' && type !== 'recovery'" in bff
    assert "ADMIN_AUTH_COOKIE" in bff
    assert "httpOnly: true" in bff


def test_admin_bff_applies_cookie_csrf_body_size_and_rpc_guards():
    source = BFF.read_text(encoding="utf-8")

    for marker in (
        "sameSite: 'lax'",
        "secure: true",
        "httpOnly: true",
        "ADMIN_RPC_ALLOWLIST.has(functionName)",
        "client.auth.getUser()",
        "client.auth.mfa.getAuthenticatorAssuranceLevel()",
        "request.headers.get('Origin')",
        "Sec-Fetch-Site",
        "MAX_BODY_BYTES = 64 * 1024",
        "request.body.getReader()",
        "readCallbackForm(request)",
        "form-action 'self'",
        "Cache-Control",
        "Referrer-Policy",
    ):
        assert marker in source
    assert "request.json()" not in source
    assert "NEXT_SUPABASE_SECRET_KEY" not in source
    assert "service_role" not in source


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


def test_admin_surfaces_fail_closed_without_an_explicit_hostname_allowlist():
    source = MIDDLEWARE.read_text(encoding="utf-8")
    assert 'const isExplicitLocalhost = context.env.ADMIN_BFF_ALLOW_LOCALHOST === "true" && isLocalhost(hostname);' in source
    assert "const isAllowedHost = allowedHosts.has(hostname) || isExplicitLocalhost;" in source
    assert "const isAllowedBffHost = isAllowedHost;" in source
    assert "const isAllowedHost = allowedHosts.size > 0 ? allowedHosts.has(hostname) : !isPublicHost;" not in source


class H3InvitationCallbackContractTest(unittest.TestCase):
    def test_auth_client_uses_official_pkce_and_no_manual_token_exchange(self):
        test_auth_client_uses_official_pkce_and_no_manual_token_exchange()

    def test_callback_consumes_code_once_and_uses_fixed_internal_routes(self):
        test_callback_consumes_code_once_and_uses_fixed_internal_routes()

    def test_onboarding_pages_consume_status_and_never_send_password_to_rpc(self):
        test_onboarding_pages_consume_status_and_never_send_password_to_rpc()

    def test_new_admin_routes_are_slash_normalized(self):
        test_new_admin_routes_are_slash_normalized()

    def test_callback_keeps_tokens_server_side_without_open_redirect(self):
        test_callback_keeps_tokens_server_side_without_open_redirect()

    def test_email_links_send_one_time_hash_to_the_allowlisted_bff_callback(self):
        test_email_links_send_one_time_hash_to_the_allowlisted_bff_callback()

    def test_admin_bff_applies_cookie_csrf_body_size_and_rpc_guards(self):
        test_admin_bff_applies_cookie_csrf_body_size_and_rpc_guards()
