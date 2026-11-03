\set ON_ERROR_STOP on
-- LOCAL disposable PG17 fixture only: emulate modern PostgREST claim settings.
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql
CREATE OR REPLACE FUNCTION auth.uid() RETURNS UUID LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
  SELECT COALESCE(NULLIF(current_setting('request.jwt.claim.sub',true),''),
    NULLIF(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid
$$;
CREATE OR REPLACE FUNCTION auth.jwt() RETURNS JSONB LANGUAGE sql STABLE SET search_path=pg_catalog AS $$
  SELECT COALESCE(NULLIF(current_setting('request.jwt.claims',true),'')::jsonb,
    jsonb_build_object('aal',current_setting('request.jwt.claim.aal',true)))
$$;
INSERT INTO auth.users(id,email) VALUES('72000000-0000-0000-0000-000000000001','quota-api-admin@local.test') ON CONFLICT DO NOTHING;
INSERT INTO public.admin_members(user_id,role,is_active,account_status)
VALUES('72000000-0000-0000-0000-000000000001','admin',true,'ready') ON CONFLICT DO NOTHING;
INSERT INTO private.h3_admin_rpc_gateway_keys(key_id,project_ref,secret)
VALUES ('local-pg17-k1','local','local-only-pg17-rpc-gateway-fixture-key-32-bytes')
ON CONFLICT (key_id) DO UPDATE SET project_ref=EXCLUDED.project_ref,secret=EXCLUDED.secret,valid_until='infinity';
DELETE FROM private.h3_admin_rpc_gateway_nonces
WHERE actor='72000000-0000-0000-0000-000000000001';
-- Test-only reset limited to this synthetic actor's rolling windows.
UPDATE private.h3_admin_quota_events SET events='{}'
WHERE scope IN ('rpc-read:72000000-0000-0000-0000-000000000001','rpc-write:72000000-0000-0000-0000-000000000001');
