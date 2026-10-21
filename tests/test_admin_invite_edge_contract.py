from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / "supabase/functions/admin-invite/index.ts"
MIGRATION = ROOT / "db/migrations/20260920_h3_invitation_edge_runtime.sql"
CONFIG = ROOT / "supabase/config.toml"
ACCEPT_FIX = ROOT / "db/migrations/20260928_h3_invitation_accept_email_regex_fix.sql"


def test_admin_invite_uses_auth_owned_invitation_and_server_redirect_allowlist():
    source = EDGE.read_text(encoding="utf-8")

    assert "auth.admin.inviteUserByEmail" in source
    assert "redirectTo: redirect.url" in source
    assert "ADMIN_INVITE_ALLOWED_REDIRECTS" in source
    assert "token_hash" not in source
    assert "auth/v1/admin/users" not in source
    assert "verify_jwt = true" in CONFIG.read_text(encoding="utf-8")


def test_admin_invite_cors_allowlist_is_normalized_and_fail_closed():
    source = EDGE.read_text(encoding="utf-8")

    assert "ADMIN_INVITE_ALLOWED_ORIGINS" in source
    assert "new URL(value.trim()).origin" in source
    assert "new URL(origin).origin" in source
    assert "allowedOrigins.has(normalizedOrigin)" in source
    assert '"Access-Control-Allow-Origin": origin' not in source
    assert 'headers["Access-Control-Allow-Origin"] = normalizedOrigin' in source
    assert '"Access-Control-Allow-Origin": normalizedOrigin && allowedOrigins.has(normalizedOrigin) ? normalizedOrigin : "null"' not in source


def test_admin_invite_redirects_require_explicit_environment_allowlist():
    source = EDGE.read_text(encoding="utf-8")

    assert "feat-h3req1-development-remo.studiamatch-aty.pages.dev" not in source
    assert "FREE_DEVELOPMENT_PROJECT_HOST" not in source
    assert "developmentFallback" not in source
    assert source.count("if (!configuredUrl || !allowed.includes(configuredUrl)) return null;") == 2
    assert "const configuredUrl = Deno.env.get(\"ADMIN_INVITE_REDIRECT_URL\")?.trim() || \"\";" in source
    assert "const configuredUrl = Deno.env.get(\"ADMIN_INVITE_RECOVERY_REDIRECT_URL\")?.trim() || \"\";" in source
    assert "ADMIN_INVITE_ALLOWED_REDIRECTS" in source
    assert 'parsed.pathname !== "/admin/auth/callback/"' in source
    assert "parsed.search" in source
    assert source.count('parsed.protocol !== "https:"') == 2


def test_admin_invite_validates_privileged_project_configuration_and_api_key_transport():
    source = EDGE.read_text(encoding="utf-8")

    assert "function isValidSupabaseConfiguration" in source
    assert "/^sb_secret_[A-Za-z0-9_-]+$/" in source
    assert "parsed.protocol === \"https:\"" in source
    assert "parsed.hostname" in source and "\\.supabase\\.co" in source
    assert "global: { fetch: createApiKeyOnlyFetch(SERVICE_KEY) }" in source
    assert 'headers.delete("authorization")' in source


def test_admin_invite_error_and_success_responses_preserve_request_cors():
    source = EDGE.read_text(encoding="utf-8")

    assert '"Server configuration incomplete", request_id: requestId }, 500, req' in source
    assert '"Invitation redirect is not configured", request_id: requestId }, 500, req' in source
    assert '"Missing access token", request_id: requestId }, 401, req' in source
    assert 'parsedBody.code === "body_too_large"' in source
    assert 'code: parsedBody.code' in source
    assert '"Invalid email", code: "invalid_email", request_id: requestId }, 400, req' in source
    assert '"Invalid role: must be admin or user", code: "invalid_role", request_id: requestId }, 400, req' in source
    assert re.search(r'status: "pending",\s+resent: reserved\.resent,', source)
    assert 'recovery_sent: false' in source


def test_admin_invite_authorizes_before_bounded_body_parsing():
    source = EDGE.read_text(encoding="utf-8")
    start = source.index("async function handleInvite")
    auth_at = source.index("actorId = await authorize(admin, accessToken)", start)
    parse_at = source.index("const parsedBody = await readInvitePayload(req)", start)

    assert "MAX_INVITE_BODY_BYTES = 64 * 1024" in source
    assert "req.body.getReader()" in source
    assert "reader.cancel()" in source
    assert "Content-Length" in source
    assert auth_at < parse_at
    assert "req.json()" not in source
    assert 'startsWith("application/json")' in source


def test_admin_invite_resend_confirmed_pending_identity_uses_auth_recovery():
    source = EDGE.read_text(encoding="utf-8")
    handler = source[source.index("async function handleInvite"):]

    assert 'admin.auth.resetPasswordForEmail(email, { redirectTo: recoveryRedirect.url })' in source
    assert 'const confirmedResend = Boolean(' in source
    assert 'livePending &&' in source
    assert 'resend &&' in source
    assert 'existingAuthUser?.email_confirmed_at' in source
    assert 'existingMember?.account_status === "invited"' in source
    assert 'if (confirmedResend)' in source
    assert 'await sendAuthRecovery(admin, email, recoveryRedirect);' in source
    assert 'recovery_sent: true' in source
    assert 'if (existingAuthUser?.email_confirmed_at || existingAuthUser?.confirmed_at)' in source
    assert handler.index('const reserved = await reserveInvitation') < handler.index('await sendAuthRecovery(admin, email, recoveryRedirect);')
    assert 'preservePendingOnRecoveryFailure' not in source


def test_admin_invitation_reservation_precedes_auth_email_side_effects():
    source = EDGE.read_text(encoding="utf-8")
    handler = source[source.index("async function handleInvite"):]

    reservation = handler.index("const reserved = await reserveInvitation")
    auth_invite = handler.index("await sendAuthInvitation(admin, email, redirect)")
    auth_recovery = handler.index("await sendAuthRecovery(admin, email, recoveryRedirect)")
    assert reservation < auth_invite
    assert reservation < auth_recovery
    assert "await completeInvitation(admin, invitationId, authUserId)" in handler
    assert "await failInvitation(admin, invitationId, authUserId, failureCode" in handler


def test_admin_invite_allows_only_orphaned_pending_reinvite_without_live_auth_identity():
    source = EDGE.read_text(encoding="utf-8")
    persistence = (ROOT / "db/migrations/20260828_h3_admin_auth.sql").read_text(encoding="utf-8")

    assert 'const orphanedPendingReinvite = Boolean(livePending && !existingAuthUser && !existingMember && !resend);' in source
    assert 'REFERENCES auth.users(id) ON DELETE CASCADE' in persistence
    assert 'if (livePending && !resend && !orphanedPendingReinvite)' in source
    assert 'if (livePending && (resend || orphanedPendingReinvite))' in source
    assert 'resend: Boolean(livePending && (resend || orphanedPendingReinvite))' in source


def test_admin_invite_records_auth_delivery_failure_once_and_surfaces_rate_limit():
    source = EDGE.read_text(encoding="utf-8")

    assert 'function authEmailError' in source
    assert 'error?.status === 429' in source
    assert 'new InviteError("auth_rate_limited"' in source
    assert 'if (actorId && failure.code === "auth_invite_failed"' not in source
    assert 'failureCode === "auth_recovery_failed"' in source
    assert 'error.status >= 400 && error.status < 500' in source
    assert 'Auth delivery outcome requires reconciliation' in source
    assert 'new InviteError("auth_delivery_unknown"' in source
    assert 'admin.rpc("admin_invitation_mark_delivery_reconciliation"' in source
    assert 'failureCode === "auth_delivery_unknown"' in source
    assert 'error?.status === 408' in source
    assert 'catch {' in source
    assert 'authCallSucceeded' in source
    assert 'if (code === "auth_rate_limited" || code === "quota_rate_limited") return 429;' in source
    assert 'requestInvitation.deliveryCompleted' in source
    assert 'error?.status === 429' in source
    assert 'error?.status === 408' in source
    assert 'delivery_state' in source
    assert '.update({ status: "expired" })' not in source


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
    compensation = (ROOT / "db/migrations/20261001_h3_invitation_reservation_compensation.sql").read_text(encoding="utf-8")

    assert 'Deno.env.get("NEXT_SUPABASE_SECRET_KEY")' in source
    assert 'admin.rpc("admin_invitation_reserve"' in source
    assert 'admin.rpc("admin_invitation_complete"' in source
    assert 'admin.rpc("admin_invitation_fail"' in source
    assert "restored_previous_invitation_id" in compensation
    assert 'admin.rpc("admin_invitation_record_failure"' in source
    assert "GRANT EXECUTE ON FUNCTION public.admin_invitation_reserve" in migration
    assert "GRANT EXECUTE ON FUNCTION public.admin_invitation_complete" in migration
    assert "GRANT EXECUTE ON FUNCTION public.admin_invitation_fail" in compensation
    assert 'CREATE OR REPLACE FUNCTION public.admin_invitation_mark_delivery_reconciliation' in compensation
    assert 'GRANT EXECUTE ON FUNCTION public.admin_invitation_mark_delivery_reconciliation' in compensation
    assert 'CREATE OR REPLACE FUNCTION public.admin_invitation_expire' in compensation
    assert 'CREATE OR REPLACE FUNCTION public.admin_invitation_reserve' in compensation
    assert "existing.metadata ->> 'request_id' = p_request_id" in compensation
    assert 'CREATE OR REPLACE FUNCTION public.admin_invitation_complete' in compensation
    assert 'CREATE OR REPLACE FUNCTION public.admin_accept_current_invitation' in compensation
    assert "'delivery_unknown'" in compensation
    assert "'delivery_reconciliation'" in compensation
    assert "h3_admin_invite:' || normalized_email" in compensation


def test_admin_invite_behavioral_edge_harness_runs_in_ci():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(encoding="utf-8")

    assert "node ../tests/h3_admin_bff_mock_uat.mjs" in workflow
    assert "node ../tests/h3_admin_auth_error_uat.mjs" in workflow
    assert "node ../tests/h3_admin_invite_edge_uat.mjs" in workflow
    assert "node ../tests/h3_supabase_sdk_headers_uat.mjs" in workflow
    assert (ROOT / "tests/h3_admin_auth_error_uat.mjs").is_file()


def test_signed_rpc_gateway_harness_is_run_in_ci():
    workflow = (ROOT / ".github/workflows/security-audit.yml").read_text(encoding="utf-8")

    assert "tests/sql/h3_admin_rpc_signed_gateway_harness.sql" in workflow
    assert "PGRST_DB_PRE_REQUEST=public.h3_admin_rpc_signed_gateway_pre_request" in workflow
    assert "H3_POSTGREST_TEST_RPC_SECRET=local-only-pg17-rpc-gateway-fixture-key-32-bytes" in workflow
    assert "tests/h3_admin_quota_postgrest.mjs" in workflow


def test_protected_h3_path_allowlist_is_narrow_and_covers_this_candidate():
    guard = (ROOT / "scripts/security/protected_path_scope_guard.sh").read_text(encoding="utf-8")
    match = re.search(r"allowed_h3='([^']+)'", guard)
    assert match is not None
    allowed = [re.compile(match.group(1))]
    extra = re.search(r"allowed_h3_extra='([^']+)'", guard)
    if extra:
        allowed.append(re.compile(extra.group(1)))

    for candidate in (
        ".github/workflows/security-audit.yml",
        ".github/workflows/protected-workflow-integrity.yml",
        ".github/workflows/fg1_inventory.yml",
        ".github/workflows/fg3_integrity.yml",
        ".github/workflows/production_pipeline.yml",
        ".github/workflows/opencode.yml",
        "web/functions/_lib/admin-bff.ts",
        "web/src/app/admin/login/page.tsx",
        "supabase/functions/admin-invite/index.ts",
        "web/src/lib/supabase-transport.ts",
        "db/migrations/20261001_h3_invitation_reservation_compensation.sql",
        "tests/h3_admin_invite_edge_uat.mjs",
        "tests/test_fase09_9_certification_canary.py",
        "tests/test_security_flow.py",
        "tests/h3_admin_bff_mock_uat.mjs",
        "tests/h3_supabase_sdk_headers_uat.mjs",
        "tests/h3_admin_invite_edge_typecheck.mjs",
        "tests/sql/h2_pro_pg17_harness.sql",
        "tests/sql/h3_from_h2_pro_pg17_harness.sql",
        "tests/sql/h3_safe_suspend_harness.sql",
        "db/rollback/h3req1_safe_suspend.sql",
        "db/migrations/20261002_h3_admin_quotas.sql",
        "db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql",
        "db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql",
        "tests/sql/h3_admin_quota_harness.sql",
        "tests/sql/h3_admin_rpc_signed_gateway_harness.sql",
        "tests/h3_admin_quota_uat.mjs",
        "tests/h3_admin_quota_runtime.mjs",
        "tests/h3_admin_quota_postgrest.mjs",
        "tests/h3_admin_safe_suspend_runtime_uat.mjs",
        "tests/sql/h3_quota_postgrest_fixture.sql",
        "tests/sql/h3_quota_postgrest_assert.sql",
        "web/functions/_lib/admin-quota.ts",
        "workers/admin-quota/index.ts",
        "workers/admin-quota/wrangler.jsonc",
        "scripts/security/h2_web_mock_smoke.sh",
        "web/eslint.config.mjs",
        ".context/sistema_db_supabase.md",
        "tests/h3_admin_auth_error_uat.mjs",
        "tests/h3req1_c03_docker_daemon_identity_f2d.py",
        "tests/test_h3req1_c03_docker_daemon_identity_f2d.py",
        "tests/sql/h3_invitation_onboarding_harness.sql",
        "tests/sql/h3_invitation_edge_runtime_harness.sql",
        ".context/operaciones/plan_go_h3req1_local_development_2026-10-02.md",  # deleted archive source path
        ".context/evidencia/planes_historicos/plan_go_h3req1_local_development_2026-10-02.md",
        ".context/operaciones/h3req1_remediation_plan_2026-09-24.md",  # deleted archive source path
        ".context/evidencia/planes_historicos/h3req1_remediation_plan_2026-09-24.md",
        ".context/operaciones/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md",  # deleted archive source path
        ".context/evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md",
        ".context/operaciones/plan_cierre_integral_h3req1_2026-10-04.md",
        "AGENTS.md",
    ):
        assert any(pattern.fullmatch(candidate) for pattern in allowed), candidate

    local_match = re.search(
        r"allowed_h3_local=\$\(cat <<'H3_LOCAL_PATHS'\n(.*?)\nH3_LOCAL_PATHS",
        guard,
        re.DOTALL,
    )
    assert local_match is not None
    local_allowed = {line.strip() for line in local_match.group(1).splitlines() if line.strip()}
    retired_local_paths = (
        ".context/evidencia/planes_historicos/h3req1_ruta_ejecutable_go_pr_y_remoto_2026-10-06.md",
        ".context/indice.md",
        ".context/trazabilidad/registro_fuentes_componentes.json",
        ".context/evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md",
        ".context/evidencia/h3req1_documentacion_semantica_reanudacion_2026-10-13_r11.md",
        ".context/h3req1_inventario_cobertura.md",
        ".context/trazabilidad/00_entrada_tecnica.md",
        ".context/trazabilidad/cobertura_evidencia.md",
        ".context/trazabilidad/contratos_dependencias.md",
        ".context/trazabilidad/mapa_componentes.md",
        ".context/trazabilidad/matriz_impacto.md",
        ".context/h3req1_mapa_reorganizacion.md",
        ".context/operaciones/h3req1_prompt_luna_6_max_cierre_local_2026-10-08.md",
        ".context/operaciones/h3req1_avance_por_gates_y_prompt_luna_2026-10-08.md",
        ".context/seguimiento/h3req1_estado_pr_y_remoto_2026-10-05.md",
        ".context/seguimiento/h3req1_traspaso_avance_y_proximo_ciclo_2026-10-04.md",
        ".context/seguimiento/mapa_documental_obsidian_2026-10-04.md",
    )
    # These exact retired paths remain allowlisted so scoped deletions still trigger the gate.
    for candidate in retired_local_paths:
        assert candidate in local_allowed, candidate

    active_local_docs = (".context/trazabilidad/protocolo_constructor.md",)
    for candidate in active_local_docs:
        assert candidate in local_allowed, candidate
        assert (ROOT / candidate).is_file(), candidate

    for unrelated in (
        "web/src/app/HomeContent.tsx",
        "db/migrations/20261002_unrelated.sql",
        "supabase/functions/unrelated/index.ts",
        "test-results/h3-output.json",
    ):
        assert not any(pattern.fullmatch(unrelated) for pattern in allowed), unrelated


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


def test_invitation_acceptance_regex_fix_is_single_escaped_dot_and_idempotent():
    source = ACCEPT_FIX.read_text(encoding="utf-8")

    assert "CREATE OR REPLACE FUNCTION public.admin_accept_current_invitation" in source
    assert "normalized_email !~ '^[^[:space:]@]+@[^[:space:]@]+\\.[^[:space:]@]+$'" in source
    assert "normalized_email !~ '^[^[:space:]@]+@[^[:space:]@]+\\\\.[^[:space:]@]+$'" not in source
    assert "admin_accept_current_invitation(UUID)" in source
