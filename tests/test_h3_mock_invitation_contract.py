from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "mock-server/server.js"
UAT = ROOT / "tests/h3_invitation_uat.mjs"


def test_mock_exposes_auth_owned_invitation_and_fake_inbox_only_in_test_mode():
    source = MOCK.read_text(encoding="utf-8")

    for marker in (
        "'/functions/v1/admin-invite'",
        "'/auth/v1/verify'",
        "'/__test/inbox'",
        "'/__test/clock'",
        "'/__test/invitation'",
        "MOCK_ADMIN_INVITE_ALLOWED_REDIRECTS",
        "invitationRedirect",
        "deliverInvitation",
        "admin_invitation_reserve",
        "admin_invitation_complete",
    ):
        assert marker in source
    assert "if (process.env.NODE_ENV !== 'test') return notFound(res);" in source


def test_mock_email_get_only_renders_interstitial_and_post_consumes_token_once():
    source = MOCK.read_text(encoding="utf-8")
    inbox_route = source.split("pathname.startsWith('/__auth/invite/')", 1)[1].split("pathname === '/auth/v1/verify' && req.method === 'POST'", 1)[0]
    verify_post = source.split("pathname === '/auth/v1/verify' && req.method === 'POST'", 1)[1].split("pathname === '/auth/v1/verify' && req.method === 'GET'", 1)[0]

    assert "target.searchParams.set('token_hash', token)" in inbox_route
    assert "record.linkOpened = true" not in inbox_route
    assert "body.token_hash" in verify_post
    assert "record.linkOpened = true" in verify_post
    assert "email_confirmed_at = COALESCE(email_confirmed_at, now())" in verify_post


def test_mock_routes_editorial_audit_and_availability_through_database_rpcs():
    source = MOCK.read_text(encoding="utf-8")

    assert "case 'admin_get_course_audit':" in source
    assert "public.admin_get_course_audit($1, $2, $3, $4)" in source
    assert "case 'admin_set_course_availability':" in source
    assert "public.admin_set_course_availability($1, $2, $3, $4, $5, $6, $7)" in source


def test_mock_invitation_never_returns_private_link_from_admin_endpoint():
    source = MOCK.read_text(encoding="utf-8")
    response_block = source.split("return sendJson(res, 200, {", 1)[-1].split("});", 1)[0]
    assert "link" not in response_block
    assert "token" not in response_block
    assert "password" not in response_block


def test_invitation_uat_exercises_ui_inbox_verify_and_onboarding():
    source = UAT.read_text(encoding="utf-8")
    for marker in (
        "inviteFromUi",
        "/__test/inbox",
        "openInvite",
        "completePasswordSetup",
        "INV-001",
        "INV-002",
        "INV-003",
        "INV-004",
        "INV-005",
        "INV-012",
        "INV-008",
        "INV-009",
        "INV-013",
        "Continuar con la invitación",
        "waitForURL(`${BASE_URL}/admin/auth/callback/?error=invalid`)",
        "/api/admin/auth/callback",
        "/api/admin/invitations",
    ):
        assert marker in source
    assert "sessionToken(page)" not in source
    assert "localStorage" not in source


class H3MockInvitationContractTest(unittest.TestCase):
    def test_mock_exposes_auth_owned_invitation_and_fake_inbox_only_in_test_mode(self):
        test_mock_exposes_auth_owned_invitation_and_fake_inbox_only_in_test_mode()

    def test_mock_invitation_never_returns_private_link_from_admin_endpoint(self):
        test_mock_invitation_never_returns_private_link_from_admin_endpoint()

    def test_invitation_uat_exercises_ui_inbox_verify_and_onboarding(self):
        test_invitation_uat_exercises_ui_inbox_verify_and_onboarding()
