\set ON_ERROR_STOP on
-- Disposable integrated fixture only. R13 proved that the configured
-- PostgREST extra search path requires this namespace to exist in fresh PG17.
CREATE SCHEMA IF NOT EXISTS extensions AUTHORIZATION postgres;
-- Supabase's managed service_role bypasses RLS. Mirror that role attribute in
-- this isolated PG17 fixture so PostgREST sees the same invitation rows.
ALTER ROLE service_role BYPASSRLS;
DO $$
DECLARE service_role_bypasses_rls BOOLEAN;
BEGIN
  SELECT rolbypassrls INTO service_role_bypasses_rls
  FROM pg_roles WHERE rolname = 'service_role';
  IF service_role_bypasses_rls IS DISTINCT FROM TRUE THEN
    RAISE EXCEPTION 'Synthetic service_role must bypass row security';
  END IF;
END;
$$;
\ir ../../db/migrations/20261002_h3_admin_quota_expand.sql
\ir ../../db/migrations/20261002_h3_admin_quotas.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql
