from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_queue_ux_migration_preserves_legacy_and_adds_server_side_facets() -> None:
    source = read("db/migrations/20260927_h3_admin_queue_facets_filter.sql")

    assert "admin_get_course_queue_filtered" in source
    assert "admin_count_course_queue_filtered" in source
    assert "admin_get_course_queue_facets" in source
    assert "p_institution_slug" in source
    assert "admin_get_course_queue(" not in source
    assert "DROP FUNCTION" not in source
    assert "GRANT EXECUTE ON FUNCTION public.admin_get_course_queue_facets() TO authenticated, service_role" in source
    assert "REVOKE ALL ON FUNCTION public.admin_get_course_queue_facets() FROM PUBLIC, anon" in source


def test_queue_ux_migration_keeps_auth_and_editor_gates() -> None:
    source = read("db/migrations/20260927_h3_admin_queue_facets_filter.sql")

    assert source.count("PERFORM public.admin_require_aal2();") == 3
    assert source.count("public.admin_is_active_editor()") == 3
    assert "p_first IS NULL OR p_first < 1 OR p_first > 100" in source
    assert "Invalid editorial status" in source
    assert "Invalid quality status" in source


def test_queue_pagination_rejects_null_limits_in_rpc_and_signed_dispatcher() -> None:
    queue_migration = read("db/migrations/20260927_h3_admin_queue_facets_filter.sql")
    queue_guard_migration = read("db/migrations/20261004_h3_admin_queue_first_null_guard.sql")
    quota_harness = read("tests/sql/h3_admin_quota_harness.sql")
    pro_harness = read("tests/sql/h3_from_h2_pro_pg17_harness.sql")
    gateway_migration = read(
        "db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql"
    )
    queue_harness = read("tests/sql/h3_pg17_harness.sql")
    gateway_harness = read("tests/sql/h3_admin_rpc_signed_gateway_harness.sql")

    assert "IF p_first IS NULL OR p_first < 1 OR p_first > 100 THEN" in queue_migration
    assert "public.admin_get_course_queue_filtered(integer,text,text,text,text)" in queue_guard_migration
    assert "private.h3_quota_base_admin_get_course_queue_filtered(integer,text,text,text,text)" in queue_guard_migration
    assert "H3_QUOTA_WRAPPER_V1" in queue_guard_migration
    assert "old_occurrences <> 1 OR new_occurrences <> 0" in queue_guard_migration
    assert "EXECUTE function_definition" in queue_guard_migration
    assert "Simulate the already-recorded legacy RPC body, then prove the forward patch" in pro_harness
    assert "forward migration did not repair the already-applied direct queue RPC" in pro_harness
    assert "Exercise the forward migration against the quota wrapper's copied original" in quota_harness
    assert "quota-wrapped queue RPC admitted a NULL page size" in quota_harness
    assert "FOR i IN 1..119 LOOP" in quota_harness
    assert "IF p_args ? 'p_first' AND p_args -> 'p_first' = 'null'::JSONB THEN" in gateway_migration
    queue_dispatch = gateway_migration.split(
        "ELSIF p_rpc_name = 'admin_get_course_queue_filtered' THEN", 1
    )[1].split("ELSIF p_rpc_name = 'admin_count_course_queue_filtered' THEN", 1)[0]
    null_guard = queue_dispatch.split("IF p_args ? 'p_first'", 1)[1].split("END IF;", 1)[0]
    assert "FROM public.admin_get_course_queue_filtered(\n        0," in null_guard
    assert "p_args ->> 'p_first'" not in null_guard
    assert "admin_get_course_queue_filtered(NULL, NULL, NULL, NULL, NULL)" in queue_harness
    assert "First must be between 1 and 100" in gateway_harness
    assert "mfa_required" in gateway_harness
    assert "User is not an active editor" in gateway_harness
    assert "gateway_null_admin_nonce" in gateway_harness
    assert "Run the disposable quota harness before the signed gateway harness" in gateway_harness
    assert '{"p_first":null}' in gateway_harness


def test_queue_guard_paths_are_allowlisted_by_the_protected_workflow() -> None:
    guard = read("scripts/security/protected_path_scope_guard.sh")

    patterns = {}
    for name in ("allowed_h3", "allowed_h3_extra"):
        assignment = next(
            line.strip() for line in guard.splitlines() if line.strip().startswith(f"{name}=")
        )
        patterns[name] = re.compile(assignment.split("='", 1)[1].rsplit("'", 1)[0])

    changed_paths = (
        "db/migrations/20260927_h3_admin_queue_facets_filter.sql",
        "db/migrations/20261004_h3_admin_queue_first_null_guard.sql",
        "db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql",
        "tests/test_h3_admin_queue_ux_contract.py",
        "tests/sql/h3_pg17_harness.sql",
        "tests/sql/h3_from_h2_pro_pg17_harness.sql",
        "tests/sql/h3_admin_quota_harness.sql",
        "tests/sql/h3_admin_rpc_signed_gateway_harness.sql",
        ".github/workflows/security-audit.yml",
    )
    for path in changed_paths:
        assert any(pattern.search(path) for pattern in patterns.values()), path


def test_queue_ui_explains_statuses_and_uses_catalogued_institution_filter() -> None:
    source = read("web/src/components/AdminCourseQueue.tsx")

    for label in ("Entender estados", "Estado editorial", "Estado de calidad", "Institución", "Buscar curso"):
        assert label in source
    assert "admin_get_course_queue_filtered" in source
    assert "admin_count_course_queue_filtered" in source
    assert "admin_get_course_queue_facets" in source
    assert "p_institution_slug" in source
    assert "institutions.map" in source


def test_publication_contract_cannot_claim_public_visibility_without_availability() -> None:
    source = read("db/migrations/20260927_h3_publication_visibility_contract.sql")

    assert "_availability_status TEXT" in source
    assert "availability_status" in source
    assert "availability is not confirmed" in source
    assert "_availability_status IS DISTINCT FROM 'available'" in source


def test_editorial_audit_and_availability_delta_are_bounded_and_fail_closed() -> None:
    source = read("db/migrations/20261001_h3_course_editorial_audit_availability.sql")
    editor = read("web/src/app/admin/edit/page.tsx")

    assert "CREATE OR REPLACE FUNCTION public.admin_get_course_audit" in source
    assert "public.admin_is_active_admin()" in source
    assert "p_first > 100" in source
    assert "LEFT JOIN auth.users u" in source
    assert "REVOKE ALL ON FUNCTION public.admin_get_course_audit" in source
    assert "GRANT EXECUTE ON FUNCTION public.admin_get_course_audit" in source
    assert "jsonb_strip_nulls(_current_overrides || _filtered_overrides)" in source
    assert "Evidence host must match the course source or its subdomain" in source
    assert "availability_valid_until > now()" in source
    assert "INTERVAL '90 days'" in source
    assert "availability_valid_until AT TIME ZONE 'UTC'" in source
    assert "Evidence validity cannot exceed 90 calendar days from observed_at" in source
    availability_writer = (
        editor.split("const saveAvailabilityEvidence = async", 1)[1]
        .split("const updatePublication", 1)[0]
    )
    assert "maxValidUntil.setUTCDate(maxValidUntil.getUTCDate() + 90)" in availability_writer
    assert "validUntil > maxValidUntil" in availability_writer
    assert (
        availability_writer.index("validUntil > maxValidUntil")
        < availability_writer.index("admin_set_course_availability")
    )
    assert "La evidencia puede tener una vigencia máxima global de 90 días calendario desde la verificación." in availability_writer
    assert "IS DISTINCT FROM 'unavailable'" in source
    admin_update = source.split("CREATE OR REPLACE FUNCTION public.admin_update_course(", 1)[1].split("$$;", 1)[0]
    assert "IF NOT public.admin_is_active_editor() THEN" in admin_update
    assert "AND am.account_status = 'ready'" in admin_update
    assert "IF p_version IS NULL OR _current_version IS DISTINCT FROM p_version THEN" in admin_update
    assert "NULL::INTEGER, 'reject missing version'" in read("tests/sql/h3_pg17_harness.sql")
    assert "signed NULL version was not rejected without a write" in read("tests/sql/h3_admin_rpc_signed_gateway_harness.sql")
    assert "DB_AS_CODE_RELEASE_CANARY" in source
    assert "canary.invalid" in source
    assert "private.h2_legacy_public_course_cohort" in source
    assert "DROP TABLE" not in source.upper()


def test_admin_editor_exposes_evidence_and_paginated_audit_without_direct_table_reads() -> None:
    editor = read("web/src/app/admin/edit/page.tsx")
    migration = read("db/migrations/20261001_h3_course_editorial_audit_availability.sql")

    for marker in (
        "Disponibilidad y fuente oficial",
        "Registrar comprobación respaldada",
        "availabilityEvidenceUrl",
        "availabilityValidUntil",
        "Restaurar valor del pipeline",
        "Valor base del pipeline",
        "Difiere del pipeline",
        "Fecha del dato base del pipeline:",
        "Faltante",
        "Motivo de la corrección",
        "Historial de auditoría",
        "Cargar eventos anteriores",
    ):
        assert marker in editor
    assert "admin_get_course_audit" in editor
    assert "auditEvents.map" in editor
    assert "admin_get_course_audit" in migration
    assert "LEFT JOIN auth.users u" in migration
    assert "public.course_editorial_audit a" in migration
    assert "GRANT SELECT ON TABLE public.course_editorial_audit TO authenticated" not in migration
    assert "Máximo global: 90 días calendario desde la verificación." in editor
    assert "maxValidUntil.setUTCDate(maxValidUntil.getUTCDate() + 90)" in editor


def test_editorial_preview_uses_public_renderer_and_live_field_impact() -> None:
    preview = read("web/src/components/admin/CourseLivePreview.tsx")
    renderer = read("web/src/components/courses/CoursePublicRenderer.tsx")
    public_detail = read("web/src/app/courses/[institution]/[slug]/CourseDetailClient.tsx")
    editor = read("web/src/app/admin/edit/page.tsx")

    assert "CoursePublicRenderer" in preview
    assert "CoursePublicRenderer" in public_detail
    assert "preview-impact-${activeField}" in renderer
    assert "Contenido publicado" in preview
    assert "Previsualización del borrador" in preview
    assert "publishedCourse" in preview
    assert "Estos cambios todavía no están guardados ni publicados." in preview
    assert "Admin debe volver a publicar" in preview
    assert "Ver impacto" in editor
    assert "setActivePreviewField(fieldKey)" in editor
    assert "scrollIntoView({ behavior: 'smooth', block: 'center' })" in editor
    assert editor.count("scrollIntoView({ behavior: 'smooth', block: 'center' })") == 1
    assert "Cambios sin guardar" in editor


def test_admin_session_timeout_is_shared_and_activity_resets_it() -> None:
    auth = read("web/src/lib/admin-auth.ts")
    storage = read("web/src/lib/supabase.ts")
    guard = read("web/src/components/admin/AdminSessionGuard.tsx")
    bff = read("web/functions/_lib/admin-bff.ts")

    assert "30 * 60 * 1000" in auth
    assert "persistSession: false" in storage
    assert "window.localStorage" in auth
    assert "ADMIN_ACTIVITY_EVENT_KEY" in auth
    assert "ADMIN_LOGOUT_EVENT_KEY" in auth
    assert "recordAdminActivity" in guard
    assert "touchAdminSession" in guard
    assert "60_000" in guard
    assert "ADMIN_IDLE_TIMEOUT_MS" in guard
    assert "window.addEventListener('storage', handleStorage)" in guard
    assert "signOutAdmin({ broadcast })" in guard
    assert "ADMIN_ACTIVITY_COOKIE" in bff
    assert "activityIsFresh(request, signingKey, authenticated.sessionId)" in bff
    assert "sessionIdFromAccessToken(session.access_token, user.id)" in bff
    assert re.search(r"crypto\.subtle\.verify\(\s*'HMAC'", bff)
    assert "sameOriginSessionRead(request)" in bff
    assert "ADMIN_SESSION_ACTIVITY_HMAC_KEY" in bff


def test_login_redirects_existing_sessions_without_bypassing_authentication() -> None:
    login = read("web/src/app/admin/login/page.tsx")

    assert "getAuthSession" in login
    assert "sessionState" in login
    assert "router.replace('/admin/')" in login
    assert "Sesión activa. Abriendo el panel..." in login
    assert "setSessionState('anonymous')" in login


def test_admin_users_resend_button_is_limited_to_pending_invited_members():
    users = read("web/src/app/admin/users/page.tsx")
    auth = read("web/src/lib/admin-auth.ts")

    assert "handleResend" in users
    assert "member.invitation_status === 'pending'" in users
    assert "member.account_status === 'invited'" in users
    assert "{ resend: true, requestId: attempt.requestId }" in users
    assert "Reenviar invitación" in users
    assert "recovery_sent" in users
    assert "interface InviteAttempt" in users
    assert "Consultar/reintentar misma operación" in users
    assert "requestId: globalThis.crypto.randomUUID()" in users
    assert "reason.code === 'reconciliation_required'" in users
    assert "options: { resend?: boolean; requestId?: string } = {}" in auth
    assert "'x-request-id': requestId" in auth
    assert "class AdminApiError" in auth
    assert "requestId: string | null" in auth


def test_admin_header_shows_authenticated_email_without_changing_role_gates():
    page = read("web/src/app/admin/page.tsx")
    auth = read("web/src/lib/admin-auth.ts")
    bff = read("web/functions/_lib/admin-bff.ts")

    assert "getAuthenticatedUserEmail" in page
    assert "getAuthSession())?.email" in auth
    assert "client.auth.getUser()" in bff
    assert "{userEmail || 'Usuario autenticado'}" in page
    assert "{isAdmin ? 'Admin' : 'User'}" not in page
    assert "{isAdmin && (" in page
    assert "role={role === 'admin' ? 'admin' : 'user'}" in page
    assert page.index("await requireActiveAdmin()") < page.index("getAuthenticatedUserEmail().then")
    assert page.index("setRole(authenticatedRole)") < page.index("getAuthenticatedUserEmail().then")
    email_helper = auth[auth.index("export async function getAuthenticatedUserEmail"):auth.index("export async function updateAdminPassword")]
    assert "getAuthSession()" in email_helper
    assert "?.email ?? null" in email_helper
    assert "catch { return null; }" in email_helper
