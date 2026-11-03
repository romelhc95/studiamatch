\set ON_ERROR_STOP on
DO $$
DECLARE v_invitation_id UUID;
BEGIN
  SELECT id INTO v_invitation_id
  FROM public.admin_invitations
  WHERE metadata ->> 'request_id' = 'c03-inflight-request-20261006'
    AND email = 'c03-inflight@local.test'
    AND created_by_user_id = '70000000-0000-0000-0000-000000000001';
  IF v_invitation_id IS NULL OR (SELECT count(*) FROM public.admin_invitations
      WHERE metadata ->> 'request_id' = 'c03-inflight-request-20261006') <> 1 THEN
    RAISE EXCEPTION 'Recovered drill has missing or duplicate invitation';
  END IF;
  IF (SELECT metadata->>'delivery_state' FROM public.admin_invitations WHERE id = v_invitation_id)
       IS DISTINCT FROM 'completed' THEN
    RAISE EXCEPTION 'In-flight Auth completion was not committed after suspension';
  END IF;
  IF (SELECT count(*) FROM public.admin_membership_audit
      WHERE admin_membership_audit.invitation_id = v_invitation_id
        AND entity_type = 'invitation' AND action = 'invite') IS DISTINCT FROM 1 THEN
    RAISE EXCEPTION 'Invitation audit was missing or duplicated';
  END IF;
  IF EXISTS (SELECT 1 FROM private.h3_admin_rpc_gateway_nonces
             WHERE nonce = '77000000-0000-4000-8000-000000000001') THEN
    RAISE EXCEPTION 'Denied dispatcher nonce unexpectedly exists after recovery';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM private.h3req1_safe_suspend_acl_snapshots
    WHERE database_name = current_database() AND captured_by = current_user
      AND state = 'resumed' AND resumed_at IS NOT NULL
  ) THEN RAISE EXCEPTION 'Persistent safe-resume capture is missing'; END IF;
  IF NOT has_function_privilege('authenticated', 'public.admin_signed_rpc(text,jsonb,text)', 'EXECUTE')
     OR NOT has_function_privilege('service_role', 'public.admin_invitation_reserve(text,text,uuid,uuid,boolean,text,jsonb,timestamp with time zone)', 'EXECUTE') THEN
    RAISE EXCEPTION 'Original initiating/dispatcher grants were not restored';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.course_editorial_audit
    WHERE course_id = '20000000-0000-0000-0000-000000000001'
      AND reason = 'C03 integrated synthetic audit sentinel'
  ) OR NOT EXISTS (
    SELECT 1 FROM public.course_editorial_state
    WHERE course_id = '20000000-0000-0000-0000-000000000001'
      AND availability_override_status = 'unavailable'
  ) OR EXISTS (
    SELECT 1 FROM public.courses_public_effective
    WHERE id = '20000000-0000-0000-0000-000000000001'
  ) THEN RAISE EXCEPTION 'Editorial audit/publication state changed across recovery'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.admin_members
    WHERE user_id = '70000000-0000-0000-0000-000000000001'
      AND role = 'admin' AND is_active AND account_status = 'ready'
  ) THEN RAISE EXCEPTION 'Synthetic active admin was not preserved'; END IF;
END;
$$;
