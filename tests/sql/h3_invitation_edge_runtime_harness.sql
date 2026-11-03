\set ON_ERROR_STOP on

-- This harness is appended to the canonical H3 schema harness in CI/local
-- execution so the runtime RPCs are validated without changing seed counts.
DO $$
DECLARE
    actor_id UUID := '30000000-0000-0000-0000-000000000001';
    new_user UUID := gen_random_uuid();
    invite_email TEXT := 'edge-runtime-' || gen_random_uuid()::TEXT || '@local.test';
    accepted_user UUID := gen_random_uuid();
    accepted_email TEXT := 'edge-accepted-before-complete-' || gen_random_uuid()::TEXT || '@local.test';
    reserve_result RECORD;
    complete_result RECORD;
    accept_result RECORD;
    edge_invitation_id UUID;
    accepted_invitation_id UUID;
    member_status TEXT;
    audit_action TEXT;
    invite_audit_count INTEGER;
BEGIN
    INSERT INTO auth.users (id, email)
    VALUES (new_user, invite_email);

    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        invite_email, 'user', actor_id, new_user, false,
        'h3-edge-runtime-' || new_user::TEXT,
        '{"environment":"test","redirect_origin":"https://admin.local.test"}'::jsonb,
        now() - interval '60 seconds'
    );
    IF NOT reserve_result.success OR reserve_result.invitation_id IS NULL THEN
        RAISE EXCEPTION 'edge invitation reservation failed: %', reserve_result.error_code;
    END IF;

    edge_invitation_id := reserve_result.invitation_id;
    SELECT account_status INTO member_status
    FROM public.admin_members
    WHERE user_id = new_user;
    IF member_status <> 'invited' THEN
        RAISE EXCEPTION 'edge reservation did not create invited membership: %', member_status;
    END IF;
    IF (SELECT is_active FROM public.admin_members WHERE user_id = new_user) THEN
        RAISE EXCEPTION 'invited membership must not be active';
    END IF;

    SELECT * INTO complete_result
    FROM public.admin_invitation_complete(edge_invitation_id, new_user);
    IF NOT complete_result.success THEN
        RAISE EXCEPTION 'edge invitation completion failed: %', complete_result.error_code;
    END IF;
    IF (SELECT metadata ->> 'delivery_state' FROM public.admin_invitations WHERE id = edge_invitation_id) <> 'completed' THEN
        RAISE EXCEPTION 'completed Auth delivery was not marked for safe idempotent replay';
    END IF;
    SELECT * INTO complete_result
    FROM public.admin_invitation_complete(edge_invitation_id, new_user);
    IF NOT complete_result.success THEN
        RAISE EXCEPTION 'idempotent invitation completion failed: %', complete_result.error_code;
    END IF;
    SELECT count(*) INTO invite_audit_count
    FROM public.admin_membership_audit
    WHERE invitation_id = edge_invitation_id AND action = 'invite';
    IF invite_audit_count <> 1 THEN
        RAISE EXCEPTION 'idempotent completion duplicated invite audit: %', invite_audit_count;
    END IF;
    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        invite_email, 'user', actor_id, new_user, true,
        'h3-edge-runtime-' || new_user::TEXT, '{"source":"same-request-replay"}'::jsonb, now()
    );
    IF reserve_result.success OR reserve_result.error_code <> 'reconciliation_required' THEN
        RAISE EXCEPTION 'same request id created a second reservation: %', reserve_result.error_code;
    END IF;
    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        invite_email || '.other', 'user', actor_id, NULL, false,
        'h3-edge-runtime-' || new_user::TEXT, '{}'::jsonb, now()
    );
    IF reserve_result.success OR reserve_result.error_code <> 'reconciliation_required' THEN
        RAISE EXCEPTION 'same request id was reused with a different payload: %', reserve_result.error_code;
    END IF;
    IF (SELECT token_hash FROM public.admin_invitations WHERE id = edge_invitation_id) IS NOT NULL THEN
        RAISE EXCEPTION 'edge runtime wrote Auth-owned token material';
    END IF;

    INSERT INTO auth.users (id, email)
    VALUES (accepted_user, accepted_email);
    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        accepted_email, 'user', actor_id, accepted_user, false,
        'h3-accepted-before-complete-' || accepted_user::TEXT, '{}'::jsonb, NULL
    );
    IF NOT reserve_result.success THEN
        RAISE EXCEPTION 'pre-acceptance reservation failed: %', reserve_result.error_code;
    END IF;
    accepted_invitation_id := reserve_result.invitation_id;
    PERFORM set_config('request.jwt.claim.sub', accepted_user::TEXT, true);
    SELECT * INTO accept_result
    FROM public.admin_accept_current_invitation(accepted_invitation_id);
    IF NOT accept_result.success OR accept_result.account_status <> 'password_pending' THEN
        RAISE EXCEPTION 'accept-before-complete setup failed: %', accept_result.error_code;
    END IF;
    SELECT * INTO complete_result
    FROM public.admin_invitation_complete(accepted_invitation_id, accepted_user);
    IF NOT complete_result.success THEN
        RAISE EXCEPTION 'completion did not reconcile after prior acceptance: %', complete_result.error_code;
    END IF;
    IF (SELECT metadata ->> 'delivery_state'
        FROM public.admin_invitations WHERE id = accepted_invitation_id) <> 'completed' THEN
        RAISE EXCEPTION 'accept-before-complete left Auth delivery marked incomplete';
    END IF;
    SELECT count(*) INTO invite_audit_count
    FROM public.admin_membership_audit
    WHERE invitation_id = accepted_invitation_id AND action = 'invite';
    IF invite_audit_count <> 1 THEN
        RAISE EXCEPTION 'accept-before-complete did not create exactly one invite audit: %', invite_audit_count;
    END IF;
    SELECT count(*) INTO invite_audit_count
    FROM public.admin_membership_audit
    WHERE invitation_id = accepted_invitation_id AND action = 'accept';
    IF invite_audit_count <> 1 THEN
        RAISE EXCEPTION 'accept-before-complete changed the acceptance audit count: %', invite_audit_count;
    END IF;
    SELECT * INTO complete_result
    FROM public.admin_invitation_complete(accepted_invitation_id, accepted_user);
    IF NOT complete_result.success THEN
        RAISE EXCEPTION 'accept-before-complete replay failed: %', complete_result.error_code;
    END IF;

    SELECT audit_row.action INTO audit_action
    FROM public.admin_membership_audit AS audit_row
    WHERE audit_row.invitation_id = edge_invitation_id
    ORDER BY audit_row.created_at DESC
    LIMIT 1;
    IF audit_action <> 'invite' THEN
        RAISE EXCEPTION 'edge invitation audit missing invite action: %', audit_action;
    END IF;

    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        invite_email, 'user', actor_id, new_user, false,
        'h3-edge-runtime-duplicate', '{}', now()
    );
    IF reserve_result.success OR reserve_result.error_code <> 'duplicate_pending' THEN
        RAISE EXCEPTION 'duplicate pending invitation was not rejected: %', reserve_result.error_code;
    END IF;

    DELETE FROM auth.users WHERE id = new_user;
    -- Accepted invitations intentionally retain their Auth user and immutable
    -- audit trail; this disposable fixture uses a fresh random identity.
END;
$$;

SELECT 'h3_invitation_edge_runtime_harness_ok' AS result;
