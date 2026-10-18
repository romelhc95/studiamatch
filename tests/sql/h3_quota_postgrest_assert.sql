\set ON_ERROR_STOP on
DO $$
BEGIN
  IF (SELECT cardinality(events) FROM private.h3_admin_quota_events
      WHERE scope='rpc-write:72000000-0000-0000-0000-000000000001') IS DISTINCT FROM 1 THEN
    RAISE EXCEPTION 'HTTP MFA rejection rolled back admission';
  END IF;
END;
$$;
