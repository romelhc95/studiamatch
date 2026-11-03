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
    RAISE EXCEPTION 'Final integrated replay changed invitation cardinality';
  END IF;
  IF (SELECT metadata->>'delivery_state' FROM public.admin_invitations WHERE id = v_invitation_id)
       IS DISTINCT FROM 'completed' THEN
    RAISE EXCEPTION 'Final integrated replay changed completed delivery state';
  END IF;
  IF (SELECT cardinality(events) FROM private.h3_admin_quota_events
      WHERE scope = 'edge-request:70000000-0000-0000-0000-000000000001') IS DISTINCT FROM 3 THEN
    RAISE EXCEPTION 'Expected exactly three synthetic Edge admission events including one replay';
  END IF;
  IF (SELECT count(*) FROM public.admin_membership_audit
      WHERE admin_membership_audit.invitation_id = v_invitation_id
        AND entity_type = 'invitation' AND action = 'invite') IS DISTINCT FROM 1 THEN
    RAISE EXCEPTION 'Idempotent replay duplicated the invitation audit';
  END IF;
END;
$$;
