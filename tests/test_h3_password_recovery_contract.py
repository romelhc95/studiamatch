from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web/src"
AUTH = WEB / "lib/admin-auth.ts"
RECOVERY = WEB / "app/admin/reset-password/page.tsx"
MIDDLEWARE = ROOT / "web/functions/_middleware.ts"
BFF = ROOT / "web/functions/_lib/admin-bff.ts"
STATIC_SERVER = ROOT / "mock-server/static-server.js"


def test_recovery_route_uses_auth_only_and_never_onboarding_rpc():
    source = RECOVERY.read_text(encoding="utf-8")
    auth_source = AUTH.read_text(encoding="utf-8")
    bff_source = BFF.read_text(encoding="utf-8")

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
    assert "type === 'recovery'" in bff_source
    assert "verifyOtp" in bff_source
    assert "updateUser({ password })" in bff_source


def test_recovery_route_removes_callback_credentials_and_rejects_non_recovery_type():
    source = RECOVERY.read_text(encoding="utf-8")
    bff_source = BFF.read_text(encoding="utf-8")

    assert "window.history.replaceState" in source
    assert "type !== 'invite' && type !== 'recovery'" in bff_source
    assert "access_token" not in source
    assert "refresh_token" not in source
    assert "window.location.assign" not in source
    assert "window.location.replace" not in source


def test_recovery_password_form_requires_existing_mfa_assurance_when_enrolled():
    source = RECOVERY.read_text(encoding="utf-8")
    auth_source = AUTH.read_text(encoding="utf-8")
    mfa_submit = source.split("const handleMfaSubmit = async", 1)[1].split("const handleSubmit = async", 1)[0]

    assert "getPasswordRecoveryAssurance" in source
    assert "listFactors" in source
    assert "challengeTotp" in source
    assert "verifyTotp" in source
    assert "assertValidAssurance(assurance)" in source
    assert "isNullableAssuranceLevel(assurance.currentLevel)" in source
    assert "isNullableAssuranceLevel(assurance.nextLevel)" in source
    assert "assurance.hasVerifiedFactor" in source
    assert "assurance.verifiedFactors" in source
    assert "const selectedFactor = verifiedFactors[factorIndex]" in mfa_submit
    assert "factor.id === selectedFactor.id" in mfa_submit
    assert "const challenge = await challengeTotp(currentFactor.id)" in mfa_submit
    assert mfa_submit.index("listFactors()") < mfa_submit.index("challengeTotp(currentFactor.id)")
    assert mfa_submit.index("challengeTotp(currentFactor.id)") < mfa_submit.index("verifyTotp(currentFactor.id, challenge.id, mfaCode)")
    assert "challengeId" not in source
    assert "currentLevel !== 'aal2'" in source
    assert "nextLevel === 'aal2'" in source
    assert "if (assurance.nextLevel === 'aal2')" in source
    assert "No se pudo confirmar el estado MFA de la sesión." in source
    assert "Tu cuenta usa un factor MFA que esta pantalla no puede verificar." in source
    assert "currentLevel: 'aal1' | 'aal2' | null" in auth_source
    assert "hasVerifiedFactor: boolean" in auth_source
    assert "No se pudo validar el estado de los factores MFA." in auth_source
    assert "action: 'recovery_assurance'" in auth_source
    assert "enrollTotp" not in source
    assert "unenrollTotp" not in source
    assert "pageState === 'mfa'" in source
    assert "pageState === 'ready' || pageState === 'saving'" in source


def test_recovery_mfa_allows_selecting_each_existing_verified_factor():
    source = RECOVERY.read_text(encoding="utf-8")

    assert "setVerifiedFactors(availableFactors)" in source
    assert "verifiedFactors.length > 1" in source
    assert 'htmlFor="recovery-mfa-factor"' in source
    assert 'id="recovery-mfa-factor"' in source
    assert "verifiedFactors.map((factor, index)" in source
    assert "Autenticador {index + 1}" in source
    assert "setMfaCode('')" in source


def test_mfa_factor_listing_rejects_malformed_responses():
    auth_source = AUTH.read_text(encoding="utf-8")
    bff_source = BFF.read_text(encoding="utf-8")

    assert "if (!Array.isArray(result.factors))" in auth_source
    assert "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" in auth_source
    assert "function readMfaFactorSummaries(value: unknown): MfaFactorSummary[] | null" in bff_source
    assert "!Array.isArray((value as Record<string, unknown>).all)" in bff_source
    assert "const factors = readMfaFactorSummaries(data);" in bff_source
    assert "if (error || !factors)" in bff_source
    assert "data.all || []" not in bff_source


def test_recovery_route_is_slash_normalized_in_runtime_and_mock_server():
    middleware = MIDDLEWARE.read_text(encoding="utf-8")
    static_server = STATIC_SERVER.read_text(encoding="utf-8")

    assert "/admin/reset-password" in middleware
    assert "/admin/reset-password" in static_server


def test_password_update_bff_requires_aal2_for_verified_mfa_before_auth_mutation():
    source = BFF.read_text(encoding="utf-8")
    route_start = source.index("if (pathname === '/api/admin/auth/password')")
    route_end = source.index("if (pathname === '/api/admin/auth/mfa')", route_start)
    password_route = source[route_start:route_end]

    assert "client.auth.mfa.listFactors()" in password_route
    assert "readMfaFactorSummaries(factorsData)" in password_route
    assert "factors.some((factor) => factor.status === 'verified')" in password_route
    assert "client.auth.mfa.getAuthenticatorAssuranceLevel()" in password_route
    assert "nextLevel === 'aal2'" in password_route
    assert "currentLevel !== 'aal2'" in password_route
    assert "code: 'mfa_required'" in password_route
    assert "code: 'mfa_unavailable'" in password_route
    assert password_route.index("client.auth.mfa.listFactors()") < password_route.index("client.auth.updateUser({ password })")
    assert password_route.index("currentLevel !== 'aal2'") < password_route.index("client.auth.updateUser({ password })")

    uat = (ROOT / "tests/h3_admin_bff_mock_uat.mjs").read_text(encoding="utf-8")
    assert "passwordUpdateWithMfaAal1" in uat
    assert "passwordUpdateWithMalformedFactors" in uat
    assert "passwordUpdateWithUnavailableFactors" in uat
    assert "passwordUpdateWithUnavailableAssurance" in uat
    assert "passwordUpdateWithVerifiedMfa" in uat
    assert "passwordUpdateWithoutMfa" in uat
    assert "passwordUpdateWithMfaAssuranceMismatch" in uat
