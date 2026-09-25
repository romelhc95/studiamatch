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
    ):
        assert marker in source


class H3MockInvitationContractTest(unittest.TestCase):
    def test_mock_exposes_auth_owned_invitation_and_fake_inbox_only_in_test_mode(self):
        test_mock_exposes_auth_owned_invitation_and_fake_inbox_only_in_test_mode()

    def test_mock_invitation_never_returns_private_link_from_admin_endpoint(self):
        test_mock_invitation_never_returns_private_link_from_admin_endpoint()

    def test_invitation_uat_exercises_ui_inbox_verify_and_onboarding(self):
        test_invitation_uat_exercises_ui_inbox_verify_and_onboarding()
