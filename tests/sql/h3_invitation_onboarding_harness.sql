\set ON_ERROR_STOP on

-- H3-BUILD-03B onboarding RPC contract. This file is included by the canonical
-- PG17 harness after the 20260921 migration and uses isolated fixture identities.
DO $$
DECLARE
    actor_id UUID := '30000000-0000-0000-0000-000000000001';
    accepted_user UUID := '3a000000-0000-0000-0000-000000000001';
    expired_user UUID := '3a000000-0000-0000-0000-000000000002';
    resend_user UUID := '3a000000-0000-0000-0000-000000000003';
    revoked_user UUID := '3a000000-0000-0000-0000-000000000004';
    setup_user UUID := '3a000000-0000-0000-0000-000000000005';
    mismatch_user UUID := '3a000000-0000-0000-0000-000000000006';
    legacy_user UUID := '30000000-0000-0000-0000-000000000002';
    current_invitation_id UUID;
    old_invitation_id UUID;
    new_invitation_id UUID;
    result_row RECORD;
    status_row RECORD;
    audit_count INTEGER;
    first_expiry TIMESTAMPTZ;
    first_sent TIMESTAMPTZ;
    old_account_status TEXT;
    old_is_active BOOLEAN;
BEGIN
    DELETE FROM public.admin_members
    WHERE user_id IN (accepted_user, expired_user, resend_user, revoked_user, setup_user, mismatch_user);
    DELETE FROM auth.users
    WHERE id IN (accepted_user, expired_user, resend_user, revoked_user, setup_user, mismatch_user);

    INSERT INTO auth.users (id, email, encrypted_password, role, aud, email_confirmed_at, created_at, updated_at)
    VALUES
      (accepted_user, 'onboarding-accepted@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
      (expired_user, 'onboarding-expired@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
      (resend_user, 'onboarding-resend@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
      (revoked_user, 'onboarding-revoked@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
      (setup_user, 'onboarding-setup@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now()),
      (mismatch_user, 'onboarding-mismatch-auth@local.test', 'x', 'authenticated', 'authenticated', now(), now(), now());

    PERFORM set_config('request.jwt.claim.sub', actor_id::text, false);
    PERFORM set_config('request.jwt.claim.aal', 'aal2', false);

    -- Acceptance before 24 hours: server-side TTL and invited -> password_pending.
    SELECT * INTO result_row
    FROM public.admin_invitation_reserve(
      'ONBOARDING-ACCEPTED@LOCAL.TEST', 'user', actor_id, accepted_user, false,
      'h3-03b-accepted', '{}', NULL
    );
    IF NOT result_row.success THEN
        RAISE EXCEPTION 'valid reservation failed: %', result_row.error_code;
    END IF;
    current_invitation_id := result_row.invitation_id;
    SELECT expires_at, last_sent_at INTO first_expiry, first_sent
    FROM public.admin_invitations WHERE id = current_invitation_id;
    IF first_expiry IS DISTINCT FROM first_sent + interval '24 hours' THEN
        RAISE EXCEPTION 'invitation TTL is not exactly 24 hours from server-side sent_at';
    END IF;

    PERFORM set_config('request.jwt.claim.sub', accepted_user::text, false);
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(current_invitation_id);
    IF NOT result_row.success OR result_row.account_status <> 'password_pending' THEN
        RAISE EXCEPTION 'valid invitation acceptance failed: %', result_row.error_code;
    END IF;
    IF (SELECT is_active FROM public.admin_members WHERE user_id = accepted_user) THEN
        RAISE EXCEPTION 'accepted membership must remain inactive until password setup';
    END IF;
    IF (SELECT status FROM public.admin_invitations WHERE id = current_invitation_id) <> 'accepted' THEN
        RAISE EXCEPTION 'accepted invitation did not close';
    END IF;

    -- Double acceptance is a successful no-op and does not duplicate accept audit.
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(current_invitation_id);
    IF NOT result_row.success OR result_row.account_status <> 'password_pending' THEN
        RAISE EXCEPTION 'double acceptance was not idempotent: %', result_row.error_code;
    END IF;
    SELECT count(*) INTO audit_count
    FROM public.admin_membership_audit AS audit_row
    WHERE audit_row.invitation_id = current_invitation_id AND audit_row.action = 'accept';
    IF audit_count <> 1 THEN
        RAISE EXCEPTION 'double acceptance created duplicate accept audit rows: %', audit_count;
    END IF;

    -- Password setup does not receive a password; it requires accepted state.
    SELECT * INTO result_row FROM public.admin_complete_password_setup();
    IF NOT result_row.success OR result_row.account_status <> 'ready' THEN
        RAISE EXCEPTION 'password setup failed: %', result_row.error_code;
    END IF;
    IF NOT (SELECT is_active FROM public.admin_members WHERE user_id = accepted_user) THEN
        RAISE EXCEPTION 'completed password setup did not activate membership';
    END IF;
    SELECT * INTO result_row FROM public.admin_complete_password_setup();
    IF NOT result_row.success OR result_row.account_status <> 'ready' THEN
        RAISE EXCEPTION 'password setup retry was not idempotent: %', result_row.error_code;
    END IF;
    SELECT count(*) INTO audit_count
    FROM public.admin_membership_audit AS audit_row
    WHERE audit_row.invitation_id = current_invitation_id AND audit_row.action = 'password_set';
    IF audit_count <> 1 THEN
        RAISE EXCEPTION 'password setup created duplicate audit rows: %', audit_count;
    END IF;

    -- Password setup without invitation acceptance is rejected and remains inactive.
    PERFORM set_config('request.jwt.claim.sub', setup_user::text, false);
    SELECT * INTO result_row
    FROM public.admin_invitation_reserve(
      'onboarding-setup@local.test', 'user', actor_id, setup_user, false,
      'h3-03b-setup-without-accept', '{}', NULL
    );
    IF NOT result_row.success THEN
        RAISE EXCEPTION 'setup fixture reservation failed: %', result_row.error_code;
    END IF;
    SELECT * INTO result_row FROM public.admin_complete_password_setup();
    IF result_row.success OR result_row.error_code <> 'password_setup_not_pending' THEN
        RAISE EXCEPTION 'password setup without acceptance was not rejected: %', result_row.error_code;
    END IF;
    IF (SELECT is_active FROM public.admin_members WHERE user_id = setup_user) THEN
        RAISE EXCEPTION 'unaccepted setup fixture became active';
    END IF;

    -- Acceptance at or after 24 hours expires lazily under lock and audits once.
    PERFORM set_config('request.jwt.claim.sub', expired_user::text, false);
    INSERT INTO public.admin_members (
      user_id, role, is_active, account_status, invited_at, last_invited_at,
      invited_by, status_reason
    ) VALUES (
      expired_user, 'user', false, 'invited', clock_timestamp() - interval '2 days',
      clock_timestamp() - interval '2 days', actor_id, 'expired_fixture'
    );
    INSERT INTO public.admin_invitations (
      admin_member_user_id, email, role, token_hash, status, created_by_user_id,
      created_at, expires_at, last_sent_at
    ) VALUES (
      expired_user, 'onboarding-expired@local.test', 'user', NULL, 'pending', actor_id,
      clock_timestamp() - interval '2 days', clock_timestamp() - interval '1 day',
      clock_timestamp() - interval '2 days'
    ) RETURNING id INTO current_invitation_id;
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(current_invitation_id);
    IF result_row.success OR result_row.error_code <> 'invitation_expired' THEN
        RAISE EXCEPTION '24-hour boundary was not rejected: %', result_row.error_code;
    END IF;
    IF (SELECT status FROM public.admin_invitations WHERE id = current_invitation_id) <> 'expired' THEN
        RAISE EXCEPTION 'expired invitation was not materialized lazily';
    END IF;
    SELECT count(*) INTO audit_count
    FROM public.admin_membership_audit AS audit_row
    WHERE audit_row.invitation_id = current_invitation_id AND audit_row.action = 'expire';
    IF audit_count <> 1 THEN
        RAISE EXCEPTION 'lazy expiration audit count is % instead of 1', audit_count;
    END IF;
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(current_invitation_id);
    IF result_row.success OR result_row.error_code <> 'invitation_expired' THEN
        RAISE EXCEPTION 'expired invitation retry returned an unsafe result: %', result_row.error_code;
    END IF;

    -- Resend supersedes the old invitation; only the new 24-hour window accepts.
    PERFORM set_config('request.jwt.claim.sub', resend_user::text, false);
    SELECT * INTO result_row
    FROM public.admin_invitation_reserve(
      'onboarding-resend@local.test', 'user', actor_id, resend_user, false,
      'h3-03b-resend-1', '{}', NULL
    );
    IF NOT result_row.success THEN
        RAISE EXCEPTION 'initial resend fixture reservation failed: %', result_row.error_code;
    END IF;
    old_invitation_id := result_row.invitation_id;
    SELECT * INTO result_row
    FROM public.admin_invitation_reserve(
      'onboarding-resend@local.test', 'user', actor_id, resend_user, true,
      'h3-03b-resend-2', '{}', NULL
    );
    IF NOT result_row.success OR NOT result_row.resent THEN
        RAISE EXCEPTION 'resend did not supersede prior invitation: %', result_row.error_code;
    END IF;
    new_invitation_id := result_row.invitation_id;
    IF (SELECT status FROM public.admin_invitations WHERE id = old_invitation_id) <> 'superseded' THEN
        RAISE EXCEPTION 'resend did not supersede old invitation';
    END IF;
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(old_invitation_id);
    IF result_row.success OR result_row.error_code <> 'invitation_superseded' THEN
        RAISE EXCEPTION 'superseded invitation was accepted: %', result_row.error_code;
    END IF;
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(new_invitation_id);
    IF NOT result_row.success OR result_row.account_status <> 'password_pending' THEN
        RAISE EXCEPTION 'new resend invitation did not accept: %', result_row.error_code;
    END IF;

    -- Revoked invitation is terminal and cannot alter the membership.
    PERFORM set_config('request.jwt.claim.sub', revoked_user::text, false);
    SELECT * INTO result_row
    FROM public.admin_invitation_reserve(
      'onboarding-revoked@local.test', 'user', actor_id, revoked_user, false,
      'h3-03b-revoked', '{}', NULL
    );
    IF NOT result_row.success THEN
        RAISE EXCEPTION 'revoked fixture reservation failed: %', result_row.error_code;
    END IF;
    current_invitation_id := result_row.invitation_id;
    UPDATE public.admin_invitations
    SET status = 'revoked', revoked_by_user_id = actor_id
    WHERE id = current_invitation_id;
    SELECT account_status, is_active INTO old_account_status, old_is_active
    FROM public.admin_members WHERE user_id = revoked_user;
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(current_invitation_id);
    IF result_row.success OR result_row.error_code <> 'invitation_revoked' THEN
        RAISE EXCEPTION 'revoked invitation was accepted: %', result_row.error_code;
    END IF;
    IF (SELECT account_status FROM public.admin_members WHERE user_id = revoked_user) <> old_account_status
       OR (SELECT is_active FROM public.admin_members WHERE user_id = revoked_user) IS DISTINCT FROM old_is_active THEN
        RAISE EXCEPTION 'revoked invitation changed membership state';
    END IF;

    -- Auth email mismatch is rejected even when the invitation id is supplied.
    PERFORM set_config('request.jwt.claim.sub', mismatch_user::text, false);
    INSERT INTO public.admin_invitations (
      email, role, token_hash, created_by_user_id, expires_at, last_sent_at
    ) VALUES (
      'onboarding-mismatch-business@local.test', 'user', NULL, actor_id,
      now() + interval '24 hours', now()
    ) RETURNING id INTO current_invitation_id;
    SELECT * INTO result_row FROM public.admin_accept_current_invitation(current_invitation_id);
    IF result_row.success OR result_row.error_code <> 'auth_identity_mismatch' THEN
        RAISE EXCEPTION 'email mismatch was not rejected: %', result_row.error_code;
    END IF;

    -- Legacy ready membership remains readable/operational without invitation history.
    PERFORM set_config('request.jwt.claim.sub', legacy_user::text, false);
    SELECT * INTO status_row FROM public.admin_get_onboarding_status();
    IF NOT status_row.success OR status_row.account_status <> 'ready' OR status_row.invitation_id IS NOT NULL THEN
        RAISE EXCEPTION 'legacy ready onboarding status was not preserved';
    END IF;
    SELECT public.admin_current_user_role() INTO old_account_status;
    IF old_account_status <> 'admin' AND old_account_status <> 'user' THEN
        RAISE EXCEPTION 'legacy ready member lost operational role: %', old_account_status;
    END IF;
END;
$$;

SELECT 'h3_invitation_onboarding_harness_ok' AS result;
