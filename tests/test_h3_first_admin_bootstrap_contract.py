# StudIAMatch-Docs: .context/componentes/database_migrations.md#first-admin-auth-bootstrap
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/migrations/20261105_h3_first_admin_auth_bootstrap.sql"
HARNESS = ROOT / "tests/sql/h3_first_admin_bootstrap_harness.sql"
CALLBACK = ROOT / "web/src/app/admin/auth/callback/page.tsx"
SUSPEND = ROOT / "web/functions/_middleware.ts"
BFF = ROOT / "web/functions/_lib/admin-bff.ts"
INVITE_TEMPLATE = ROOT / "supabase/templates/invite.html"


def test_bootstrap_is_exact_identity_auth_invite_only_and_not_ready() -> None:
    source = MIGRATION.read_text(encoding="utf-8")
    helper = source.split("CREATE OR REPLACE FUNCTION private.h3_first_admin_auth_bootstrap_invitation()", 1)[1]
    wrapper = source.split("CREATE OR REPLACE FUNCTION public.admin_accept_current_invitation(", 1)[1]

    assert "auth.uid()" in helper
    assert "romelhc95@gmail.com" in helper
    assert "auth_user.invited_at" in helper
    assert "auth_user.email_confirmed_at" in helper
    assert "auth_confirmed_at < auth_invited_at" in helper
    assert "member.role = 'admin'" in helper
    assert "audit_row.action = 'first_admin_bootstrap'" in helper
    assert "created_by_user_id, last_sent_at, send_count" not in helper
    assert "'created_by_user_id', NULL" in helper
    assert "'app_email_sent', false" in helper
    assert "user_id, role, is_active, account_status, invited_at, last_invited_at" in helper
    assert "invited_by, status_reason" in helper
    assert "actor_id, 'admin', false, 'invited', auth_invited_at, auth_invited_at" in helper
    assert "'password_pending'" not in helper
    assert "'ready'" not in helper
    assert "is_active = true" not in helper
    assert "token_hash IS NULL" in source
    assert "send_count = 1" in source
    assert "metadata ->> 'auth_invitation_origin' = 'supabase_auth'" in source
    assert "email = 'romelhc95@gmail.com'" in source
    assert "last_sent_at IS NOT DISTINCT FROM" in source
    assert "auth_email_confirmed_at')::TIMESTAMPTZ >=" in source
    assert "ALTER COLUMN created_by_user_id DROP NOT NULL" in source
    assert "ALTER COLUMN token_hash DROP NOT NULL" not in source
    assert "token_hash IS NOT NULL" not in source
    assert "AND token_hash IS NOT NULL" not in source
    assert "ALTER COLUMN last_sent_at DROP NOT NULL" not in source
    assert "DROP CONSTRAINT IF EXISTS admin_invitations_send_count_positive" not in source
    assert "CASE\n      WHEN metadata ->> 'source' = 'first_admin_auth_bootstrap' THEN" in source
    assert "COALESCE(" in source
    assert "'delivery_unknown', 'delivery_reconciliation'" in source

    assert "bootstrap_invitation_id := private.h3_first_admin_auth_bootstrap_invitation()" in wrapper
    assert "COALESCE(bootstrap_invitation_id, p_invitation_id)" in wrapper
    assert "IF p_invitation_id IS NULL" in wrapper
    assert wrapper.count("FROM public.admin_accept_current_invitation_lifecycle(") == 1
    assert "PZ001" in wrapper
    assert "TO authenticated, service_role" in source
    assert "FROM PUBLIC, anon, authenticated, service_role" in source


def test_existing_auth_callback_reuses_acceptance_contract_and_safe_suspend_stays_closed() -> None:
    callback = CALLBACK.read_text(encoding="utf-8")
    middleware = SUSPEND.read_text(encoding="utf-8")
    bff = BFF.read_text(encoding="utf-8")
    invite_template = INVITE_TEMPLATE.read_text(encoding="utf-8")
    harness = HARNESS.read_text(encoding="utf-8")

    assert "flow') !== 'invite'" in callback
    assert "acceptCurrentInvitation()" in callback
    assert "admin_accept_current_invitation" in callback or "acceptCurrentInvitation" in callback
    assert "url.searchParams.get('token_hash')" in bff
    assert "url.searchParams.get('type')" in bff
    assert "callbackConfirmationResponse(" in bff
    assert "client.auth.verifyOtp({ token_hash: tokenHash, type })" in bff
    assert "'?flow=invite'" in bff
    assert "{{ .RedirectTo }}?token_hash={{ .TokenHash }}&amp;type=invite" in invite_template
    assert "ADMIN_BFF_SAFE_SUSPEND === 'true'" in middleware
    assert "Administración temporalmente en mantenimiento." in middleware
    assert "invited_at" in harness
    assert "rejected_incomplete_bootstrap" in harness
    assert "rejected_missing_provenance" in harness
    assert "confirmation predating the Auth invite" in harness
    assert "ordinary-reservation@local.test" in harness
    assert "public.admin_invitation_reserve(" in harness
    assert "invitation_row.token_hash IS NOT NULL" in harness
    assert "ordinary invitation reservation with a NULL token hash failed" in harness
    assert "ordinary invitations must not accept a null creator" in harness
    assert "ordinary reservation must charge each established invite quota scope once" in harness
    assert "one signed callback must charge the lifecycle write quota exactly once" in harness
    assert "one repeated callback must charge the lifecycle write quota exactly once" in harness
    assert "h3_admin_rpc_signed_gateway_pre_request()" in harness
    assert "public.admin_signed_rpc(" in harness
    pg17_harness = (ROOT / "tests/sql/h3_first_admin_bootstrap_pg17_harness.sql").read_text(encoding="utf-8")
    runner = (ROOT / "tests/h3_first_admin_bootstrap_pg17.sh").read_text(encoding="utf-8")
    assert "20261002_h3_admin_quota_expand.sql" in pg17_harness
    assert "20261002_h3_admin_quotas.sql" in pg17_harness
    assert "20261004_h3_admin_rpc_signed_gateway_expand.sql" in pg17_harness
    assert "20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql" in pg17_harness
    assert "--network none" in runner
    assert "--pull=never" in runner
    assert "docker image inspect \"$IMAGE\"" in runner
    assert "target=/workspace,readonly" in runner
    assert "--tmpfs /var/lib/postgresql/data" in runner
    assert "20261105_h3_first_admin_auth_bootstrap.sql" in pg17_harness
    assert "20261102_h3_legacy_public_withdrawal_guard.sql" in pg17_harness
    assert "h3_first_admin_bootstrap_harness.sql" in pg17_harness
