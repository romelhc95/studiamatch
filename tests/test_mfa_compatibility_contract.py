from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_login_keeps_password_access_without_silent_mfa_enrollment() -> None:
    source = read("web/src/app/admin/login/page.tsx")

    assert "supabaseAdminLogin" in source
    assert "router.replace('/admin/')" in source
    assert "enrollTotp" not in source
    assert "challengeTotp" not in source
    assert '<form method="post"' in source


def test_sensitive_forms_do_not_fallback_to_get_query_submission() -> None:
    for relative_path in (
        "web/src/app/admin/login/page.tsx",
        "web/src/app/admin/reset-password/page.tsx",
        "web/src/app/admin/setup-password/page.tsx",
        "web/src/components/admin/MfaRequiredCard.tsx",
    ):
        source = read(relative_path)
        assert '<form method="post"' in source, relative_path


def test_mfa_client_uses_the_supabase_sdk_contract() -> None:
    source = read("web/src/lib/admin-auth.ts")

    assert "supabaseBrowserClient.auth.mfa.listFactors()" in source
    assert "supabaseBrowserClient.auth.mfa.enroll" in source
    assert "supabaseBrowserClient.auth.mfa.challenge" in source
    assert "supabaseBrowserClient.auth.mfa.verify" in source
    assert "supabaseBrowserClient.auth.mfa.unenroll" in source
    assert "fetch(`${SUPABASE_URL}/auth/v1/factors`" not in source


def test_sensitive_errors_are_normalized_to_an_explicit_mfa_state() -> None:
    source = read("web/src/lib/admin-auth.ts")
    queue = read("web/src/components/AdminCourseQueue.tsx")
    setup_card = read("web/src/components/admin/MfaRequiredCard.tsx")

    assert "class MfaRequiredError" in source
    assert "isMfaRequiredError" in source
    assert "MfaRequiredCard" in queue
    assert "Configurar MFA" in setup_card
    assert "no se configurará sin tu confirmación" in setup_card


def test_mock_user_contract_exposes_factors_for_the_official_sdk() -> None:
    source = read("mock-server/server.js")

    assert "factors: publicFactors(fixture)" in source


def test_mock_preserves_session_assurance_and_sanitizes_factor_reads() -> None:
    source = read("mock-server/server.js")

    assert "const effectiveAal = fixture.aal === 'aal2' ? 'aal2' : 'aal1'" in source
    assert "function publicFactors(fixture)" in source
    assert "return sendJson(res, 403, { message: 'MFA aal2 required', code: 'mfa_required' })" in source
