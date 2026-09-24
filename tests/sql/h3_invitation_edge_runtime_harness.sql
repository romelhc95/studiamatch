\set ON_ERROR_STOP on

-- This harness is appended to the canonical H3 schema harness in CI/local
-- execution so the runtime RPCs are validated without changing seed counts.
DO $$
DECLARE
    actor_id UUID := '30000000-0000-0000-0000-000000000001';
    new_user UUID := '39000000-0000-0000-0000-000000000010';
    reserve_result RECORD;
    complete_result RECORD;
    edge_invitation_id UUID;
    member_status TEXT;
    audit_action TEXT;
BEGIN
    INSERT INTO auth.users (id, email)
    VALUES (new_user, 'edge-runtime@local.test');

    SELECT * INTO reserve_result
    FROM public.admin_invitation_reserve(
        'EDGE-RUNTIME@LOCAL.TEST', 'user', actor_id, new_user, false,
        'h3-edge-runtime-01',
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
    IF (SELECT token_hash FROM public.admin_invitations WHERE id = edge_invitation_id) IS NOT NULL THEN
        RAISE EXCEPTION 'edge runtime wrote Auth-owned token material';
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
        'edge-runtime@local.test', 'user', actor_id, new_user, false,
        'h3-edge-runtime-duplicate', '{}', now()
    );
    IF reserve_result.success OR reserve_result.error_code <> 'duplicate_pending' THEN
        RAISE EXCEPTION 'duplicate pending invitation was not rejected: %', reserve_result.error_code;
    END IF;

    SELECT * INTO reserve_result
    FROM public.admin_invitation_fail(edge_invitation_id, new_user, 'persistence_failed');
    IF NOT reserve_result.success THEN
        RAISE EXCEPTION 'send_failed transition failed: %', reserve_result.error_code;
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.admin_invitations
        WHERE id = edge_invitation_id
          AND status = 'send_failed'
          AND failure_code = 'persistence_failed'
    ) THEN
        RAISE EXCEPTION 'send_failed state was not persisted';
    END IF;

    DELETE FROM auth.users WHERE id = new_user;
END;
$$;

SELECT 'h3_invitation_edge_runtime_harness_ok' AS result;
