\set ON_ERROR_STOP on
DO $$
DECLARE v_invitation_id UUID;
BEGIN
  SELECT id INTO v_invitation_id
  FROM public.admin_invitations
  WHERE metadata ->> 'request_id' = 'c03-inflight-request-20261006'
    AND email = 'c03-inflight@local.test'
    AND created_by_user_id = '70000000-0000-0000-0000-000000000001';
  IF v_invitation_id IS NULL THEN
    RAISE EXCEPTION 'Expected one invitation reserved before the Auth hold';
  END IF;
  IF (SELECT count(*) FROM public.admin_invitations
      WHERE metadata ->> 'request_id' = 'c03-inflight-request-20261006') <> 1 THEN
    RAISE EXCEPTION 'In-flight fixture created duplicate reservations';
  END IF;
  IF (SELECT status FROM public.admin_invitations WHERE id = v_invitation_id) <> 'pending'
     OR (SELECT metadata->>'delivery_state' FROM public.admin_invitations WHERE id = v_invitation_id) = 'completed' THEN
    RAISE EXCEPTION 'Auth hold did not leave a pending in-flight invitation';
  END IF;
  IF (SELECT cardinality(events) FROM private.h3_admin_quota_events
      WHERE scope = 'edge-request:70000000-0000-0000-0000-000000000001') IS DISTINCT FROM 1 THEN
    RAISE EXCEPTION 'Normal in-flight request admission was not recorded exactly once';
  END IF;
END;
$$;
