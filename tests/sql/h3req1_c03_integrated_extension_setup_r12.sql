\set ON_ERROR_STOP on
-- Disposable integrated fixture only. R12 proved that the configured
-- PostgREST extra search path requires this namespace to exist in fresh PG17.
CREATE SCHEMA IF NOT EXISTS extensions AUTHORIZATION postgres;
\ir ../../db/migrations/20261002_h3_admin_quota_expand.sql
\ir ../../db/migrations/20261002_h3_admin_quotas.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql
