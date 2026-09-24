from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/admin-invite/index.ts"
MIGRATION = ROOT / "db/migrations/20260920_h3_invitation_edge_runtime.sql"
CONFIG = ROOT / "supabase/config.toml"


def test_admin_invite_uses_auth_owned_invitation_and_server_redirect_allowlist():
    source = EDGE.read_text(encoding="utf-8")

    assert "auth.admin.inviteUserByEmail" in source
    assert "redirectTo: redirect.url" in source
    assert "ADMIN_INVITE_ALLOWED_REDIRECTS" in source
    assert "token_hash" not in source
    assert "auth/v1/admin/users" not in source
    assert "verify_jwt = true" in CONFIG.read_text(encoding="utf-8")


def test_admin_invite_checks_caller_identity_and_ready_admin_state():
    source = EDGE.read_text(encoding="utf-8")

    assert "admin.auth.getUser(accessToken)" in source
    assert "claims?.aal !== \"aal2\"" in source
    assert "member.role !== \"admin\"" in source
    assert "member.account_status !== \"ready\"" in source
    assert "member.is_active" in source
    assert 'claims?.aal !== "aal2"' in source
    assert "findRequestInvitation" in source
    assert "request_id" in source


def test_admin_invite_persists_only_through_service_role_rpc_contract():
    source = EDGE.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")

    assert 'Deno.env.get("NEXT_SUPABASE_SECRET_KEY")' in source
    assert 'admin.rpc("admin_invitation_reserve"' in source
    assert 'admin.rpc("admin_invitation_complete"' in source
    assert 'admin.rpc("admin_invitation_fail"' in source
    assert 'admin.rpc("admin_invitation_record_failure"' in source
    assert "GRANT EXECUTE ON FUNCTION public.admin_invitation_reserve" in migration
    assert "GRANT EXECUTE ON FUNCTION public.admin_invitation_complete" in migration
    assert "GRANT EXECUTE ON FUNCTION public.admin_invitation_fail" in migration


def test_admin_invite_has_duplicate_resend_and_failure_contracts_without_secrets():
    source = EDGE.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")

    for marker in (
        "duplicate_ready",
        "duplicate_pending",
        "resend_cooldown",
        "membership_blocked",
        "role_mismatch",
        "reconciliation_required",
        "send_failed",
    ):
        assert marker in source or marker in migration
    assert "password_set" not in source.lower()
    assert "private link" not in source.lower()
    assert "token_hash = NULL" not in source
    assert "p_failure_code" in migration
    assert "SET is_active = false" in migration
    assert "admin_invitation_fail" in migration
