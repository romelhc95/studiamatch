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
    RAISE EXCEPTION USING ERRCODE = 'H3S01', MESSAGE = 'Suspension lost or duplicated the pre-reserved invitation';
  END IF;
  IF (SELECT status FROM public.admin_invitations WHERE id = v_invitation_id) <> 'pending'
     OR (SELECT metadata->>'delivery_state' FROM public.admin_invitations WHERE id = v_invitation_id) = 'completed' THEN
    RAISE EXCEPTION USING ERRCODE = 'H3S02', MESSAGE = 'Held synthetic Auth operation is not still in flight';
  END IF;
  IF (SELECT cardinality(events) FROM private.h3_admin_quota_events
      WHERE scope = 'edge-request:70000000-0000-0000-0000-000000000001') IS DISTINCT FROM 2 THEN
    RAISE EXCEPTION USING ERRCODE = 'H3S03', MESSAGE = 'Expected one in-flight and one suspended-attempt admission event';
  END IF;
  IF EXISTS (SELECT 1 FROM private.h3_admin_rpc_gateway_nonces
             WHERE nonce = '77000000-0000-4000-8000-000000000001') THEN
    RAISE EXCEPTION USING ERRCODE = 'H3S04', MESSAGE = 'ACL-denied signed dispatcher consumed its nonce';
  END IF;
  IF has_function_privilege('authenticated', 'public.admin_signed_rpc(text,jsonb,text)', 'EXECUTE') THEN
    RAISE EXCEPTION USING ERRCODE = 'H3S05', MESSAGE = 'Authenticated role can still execute the signed dispatcher while suspended';
  END IF;
  IF NOT has_function_privilege('service_role', 'public.admin_invitation_complete(uuid,uuid)', 'EXECUTE')
     OR NOT has_function_privilege('service_role', 'public.admin_invitation_fail(uuid,uuid,text)', 'EXECUTE')
     OR NOT has_function_privilege('service_role', 'public.admin_invitation_mark_delivery_reconciliation(uuid,uuid,text,text)', 'EXECUTE') THEN
    RAISE EXCEPTION USING ERRCODE = 'H3S06', MESSAGE = 'An in-flight invitation finalizer was disabled';
  END IF;
  IF NOT has_function_privilege('service_role', 'public.admin_invitation_request_admit(uuid)', 'EXECUTE') THEN
    RAISE EXCEPTION USING ERRCODE = 'H3S07', MESSAGE = 'Service-only quota admission contract changed unexpectedly';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM private.h3req1_safe_suspend_acl_snapshots
    WHERE database_name = current_database() AND captured_by = current_user AND state = 'suspended'
  ) THEN RAISE EXCEPTION USING ERRCODE = 'H3S08', MESSAGE = 'Persistent safe-suspend capture is missing'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.course_editorial_audit
    WHERE course_id = '20000000-0000-0000-0000-000000000001'
      AND reason = 'C03 integrated synthetic audit sentinel'
  ) THEN RAISE EXCEPTION USING ERRCODE = 'H3S09', MESSAGE = 'Synthetic editorial audit evidence was lost'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.course_editorial_state
    WHERE course_id = '20000000-0000-0000-0000-000000000001'
      AND availability_override_status = 'unavailable'
  ) OR EXISTS (
    SELECT 1 FROM public.courses_public_effective
    WHERE id = '20000000-0000-0000-0000-000000000001'
  ) THEN RAISE EXCEPTION USING ERRCODE = 'H3S10', MESSAGE = 'Unavailable-course publication state degraded'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.admin_members
    WHERE user_id = '70000000-0000-0000-0000-000000000001'
      AND role = 'admin' AND is_active AND account_status = 'ready'
  ) THEN RAISE EXCEPTION USING ERRCODE = 'H3S11', MESSAGE = 'Admin continuity evidence was lost'; END IF;
  IF EXISTS (
    SELECT 1 FROM public.admin_membership_audit
    WHERE admin_membership_audit.invitation_id = v_invitation_id
      AND entity_type = 'invitation' AND action = 'invite'
  ) THEN RAISE EXCEPTION USING ERRCODE = 'H3S12', MESSAGE = 'Invitation audit preceded Auth finalization'; END IF;
END;
$$;
