-- Keep the disposable PG17 Auth actor aligned with the runtime's local.test
-- synthetic login identity. This never runs against an operational project.
\set ON_ERROR_STOP on

DO $$
DECLARE
  updated_rows INTEGER;
BEGIN
  UPDATE auth.users
     SET email = 'admin@local.test'
   WHERE id = '30000000-0000-0000-0000-000000000001'
     AND email IN ('admin@studiamatch.com', 'admin@local.test');
  GET DIAGNOSTICS updated_rows = ROW_COUNT;
  IF updated_rows <> 1
     OR (SELECT email FROM auth.users WHERE id='30000000-0000-0000-0000-000000000001') <> 'admin@local.test' THEN
    RAISE EXCEPTION 'synthetic admin identity did not normalize';
  END IF;
END;
$$;

SELECT 'h3_uat_synthetic_identity_fixup_ok' AS marker;
