from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web/src"
POLICY = WEB / "lib/password-policy.ts"
REQUIREMENTS = WEB / "components/admin/PasswordRequirements.tsx"
INPUT = WEB / "components/admin/PasswordInput.tsx"
RECOVERY = WEB / "app/admin/reset-password/page.tsx"
SETUP = WEB / "app/admin/setup-password/page.tsx"
EMAIL = ROOT / "supabase/templates/password-recovery.html"
INVITE_EMAIL = ROOT / "supabase/templates/invite.html"


def test_password_policy_has_server_aligned_rules_and_matching_gate():
    source = POLICY.read_text(encoding="utf-8")

    assert "PASSWORD_MIN_LENGTH = 12" in source
    assert "lowercase" in source
    assert "uppercase" in source
    assert "number" in source
    assert "symbol" in source
    assert "PASSWORD_SYMBOLS" in source
    assert "getPasswordChecks" in source
    assert "isPasswordValid" in source
    assert "hasPasswordRequirements" in source
    assert "Array.from(password).length" in source
    assert "password === confirmation" in source


def test_recovery_and_onboarding_use_the_same_live_password_components():
    requirements_source = REQUIREMENTS.read_text(encoding="utf-8")
    input_source = INPUT.read_text(encoding="utf-8")

    assert "Se valida en tiempo real" in requirements_source
    assert 'data-rule={id}' in requirements_source
    assert 'aria-label={`${label}: ${satisfied ? \'cumplido\' : \'pendiente\'}`}' in requirements_source
    assert "autoComplete=\"new-password\"" in input_source
    assert 'aria-invalid={invalid || undefined}' in input_source

    for path in (RECOVERY, SETUP):
        source = path.read_text(encoding="utf-8")
        assert "PasswordInput" in source
        assert "PasswordRequirements" in source
        assert "isPasswordValid(password, confirmation)" in source
        assert "hasPasswordRequirements(password)" in source
        assert "getPasswordValidationMessage(password, confirmation)" in source
        assert "aria-live=\"polite\"" in source
        assert "passwordDescription" in source


def test_recovery_email_template_sends_the_one_time_hash_to_the_bff():
    source = EMAIL.read_text(encoding="utf-8")

    assert '{{ .RedirectTo }}?token_hash={{ .TokenHash }}&amp;type=recovery' in source
    assert '{{ .ConfirmationURL }}' not in source
    assert 'token_hash' in source
    assert '24 horas' in source
    assert '12 caracteres' in source
    assert 'un s&iacute;mbolo' in source
    assert 'No compartas este enlace' in source
    assert 'type="password"' not in source


def test_invitation_email_template_matches_recovery_visual_contract_with_bff_token_handling():
    source = INVITE_EMAIL.read_text(encoding="utf-8")

    assert '<html lang="es">' in source
    assert 'background:#0f172a' in source
    assert 'background:#eff6ff' in source
    assert '{{ .RedirectTo }}?token_hash={{ .TokenHash }}&amp;type=invite' in source
    assert '{{ .ConfirmationURL }}' not in source
    assert '24 horas' in source
    assert '12 caracteres' in source
    assert 'No compartas este enlace' in source
    assert 'token_hash' in source
    assert 'type="password"' not in source
