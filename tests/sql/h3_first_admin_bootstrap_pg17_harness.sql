\set ON_ERROR_STOP on
-- Disposable PG17 fixture: build the existing H2→H3 invitation contract,
-- apply the exact current predecessor and the proposed bootstrap delta, then
-- exercise only synthetic Auth identities inside a rollback transaction.
-- No Supabase project, real account, mail, or persistent DB is contacted.
-- StudIAMatch-Docs: .context/componentes/database_migrations.md#first-admin-auth-bootstrap

\ir h3_from_h2_pro_pg17_harness.sql

-- Supabase service_role bypasses RLS. Mirror that role attribute in this
-- disposable database so service-role readback matches the Pro contract.
ALTER ROLE service_role BYPASSRLS;

-- Supabase Auth owns invited_at; add it only to this local Auth fixture.
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS invited_at TIMESTAMPTZ;

-- Add the production quota and signed-gateway layers before the candidate so
-- the callback is exercised through the same wrapped public RPC path.
\ir ../../db/migrations/20261002_h3_admin_quota_expand.sql
\ir ../../db/migrations/20261002_h3_admin_quotas.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql
\ir ../../db/migrations/20261102_h3_legacy_public_withdrawal_guard.sql
\ir ../../db/migrations/20261105_h3_first_admin_auth_bootstrap.sql
-- The idempotent migration is re-applied before the behavior harness.
\ir ../../db/migrations/20261105_h3_first_admin_auth_bootstrap.sql
\ir h3_first_admin_bootstrap_harness.sql

SELECT 'h3_first_admin_bootstrap_pg17_harness_ok' AS result;
