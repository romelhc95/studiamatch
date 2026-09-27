from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web/src"
POLICY = WEB / "lib/password-policy.ts"
REQUIREMENTS = WEB / "components/admin/PasswordRequirements.tsx"
INPUT = WEB / "components/admin/PasswordInput.tsx"
RECOVERY = WEB / "app/admin/reset-password/page.tsx"
SETUP = WEB / "app/admin/setup-password/page.tsx"
EMAIL = ROOT / "supabase/templates/password-recovery.html"


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


def test_recovery_email_template_contains_safe_instructions_and_auth_link_variable():
    source = EMAIL.read_text(encoding="utf-8")

    assert '{{ .ConfirmationURL }}' in source
    assert '24 horas' in source
    assert '12 caracteres' in source
    assert 'un s&iacute;mbolo' in source
    assert 'No compartas este enlace' in source
    assert 'type="password"' not in source
