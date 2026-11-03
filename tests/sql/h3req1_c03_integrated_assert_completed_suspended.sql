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
    RAISE EXCEPTION 'Finalized in-flight request is missing or duplicated';
  END IF;
  IF (SELECT metadata->>'delivery_state' FROM public.admin_invitations WHERE id = v_invitation_id)
       IS DISTINCT FROM 'completed' THEN
    RAISE EXCEPTION 'service_role finalizer did not complete while SQL remained suspended';
  END IF;
  IF (SELECT cardinality(events) FROM private.h3_admin_quota_events
      WHERE scope = 'edge-request:70000000-0000-0000-0000-000000000001') IS DISTINCT FROM 2 THEN
    RAISE EXCEPTION 'In-flight completion unexpectedly admitted another Edge request';
  END IF;
  IF (SELECT count(*) FROM public.admin_membership_audit
      WHERE admin_membership_audit.invitation_id = v_invitation_id
        AND entity_type = 'invitation' AND action = 'invite') IS DISTINCT FROM 1 THEN
    RAISE EXCEPTION 'In-flight completion lost or duplicated its invitation audit';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM private.h3req1_safe_suspend_acl_snapshots
    WHERE database_name = current_database() AND captured_by = current_user AND state = 'suspended'
  ) THEN RAISE EXCEPTION 'Database was resumed before in-flight completion was verified'; END IF;
  IF EXISTS (SELECT 1 FROM private.h3_admin_rpc_gateway_nonces
             WHERE nonce = '77000000-0000-4000-8000-000000000001') THEN
    RAISE EXCEPTION 'Denied dispatcher nonce was consumed while suspended';
  END IF;
END;
$$;
