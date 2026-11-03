\set ON_ERROR_STOP on
-- Apply only schema prerequisites for this integrated drill. Do not rerun the
-- already-preserved quota or signed-gateway behavior harnesses.
\ir ../../db/migrations/20261002_h3_admin_quota_expand.sql
\ir ../../db/migrations/20261002_h3_admin_quotas.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql
