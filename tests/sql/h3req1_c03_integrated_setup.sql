\set ON_ERROR_STOP on
\set gateway_key_id 'local-pg17-k1'
\set gateway_project_ref 'local'
\set gateway_secret 'local-only-pg17-rpc-gateway-fixture-key-32-bytes'
-- Synthetic fixtures for the integrated C03 drill in a new disposable PG17 DB.
-- Run only after the schema bootstrap and integrated-only additive migrations.
BEGIN;

INSERT INTO private.h3_admin_rpc_gateway_keys(key_id, project_ref, secret)
VALUES (:'gateway_key_id', :'gateway_project_ref', :'gateway_secret');

-- Read-only diagnostic for the local integrated signed-dispatcher fixture.
-- Exposes only booleans about the synthetic request context, never claim or
-- header values. It is not part of the application schema or production path.
CREATE OR REPLACE FUNCTION public.h3_c03_request_context_probe()
RETURNS JSONB
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, auth, pg_temp
AS $$
  SELECT pg_catalog.jsonb_build_object(
    'role_authenticated', COALESCE(
      NULLIF(pg_catalog.current_setting('request.jwt.claim.role', true), ''),
      NULLIF(pg_catalog.current_setting('request.jwt.claims', true), '')::JSONB ->> 'role',
      ''
    ) = 'authenticated',
    'actor_matches', auth.uid() = '70000000-0000-0000-0000-000000000001'::UUID,
    'legacy_sub_matches', NULLIF(pg_catalog.current_setting('request.jwt.claim.sub', true), '') = '70000000-0000-0000-0000-000000000001',
    'claims_sub_matches', NULLIF(pg_catalog.current_setting('request.jwt.claims', true), '')::JSONB ->> 'sub' = '70000000-0000-0000-0000-000000000001',
    'key_id_present', NULLIF(headers.value ->> 'x-studiamatch-admin-rpc-key-id', '') IS NOT NULL,
    'actor_header_present', NULLIF(headers.value ->> 'x-studiamatch-admin-rpc-actor', '') IS NOT NULL,
    'issued_at_present', NULLIF(headers.value ->> 'x-studiamatch-admin-rpc-issued-at', '') IS NOT NULL,
    'nonce_present', NULLIF(headers.value ->> 'x-studiamatch-admin-rpc-nonce', '') IS NOT NULL,
    'metadata_signature_present', NULLIF(headers.value ->> 'x-studiamatch-admin-rpc-signature', '') IS NOT NULL,
    'payload_signature_present', NULLIF(headers.value ->> 'x-studiamatch-admin-rpc-payload-signature', '') IS NOT NULL
  )
  FROM (SELECT COALESCE(
    NULLIF(pg_catalog.current_setting('request.headers', true), '')::JSONB,
    '{}'::JSONB
  ) AS value) headers;
$$;
REVOKE ALL ON FUNCTION public.h3_c03_request_context_probe() FROM PUBLIC, anon, service_role;
GRANT EXECUTE ON FUNCTION public.h3_c03_request_context_probe() TO authenticated;

INSERT INTO auth.users (id, email, email_confirmed_at)
VALUES
  ('70000000-0000-0000-0000-000000000001', 'c03-admin@local.test', now()),
  ('75000000-0000-0000-0000-000000000001', 'c03-inflight@local.test', NULL)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.admin_members (user_id, role, is_active, account_status)
VALUES ('70000000-0000-0000-0000-000000000001', 'admin', true, 'ready')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO public.course_editorial_audit
  (course_id, actor_user_id, action, old_values, new_values, reason)
VALUES (
  '20000000-0000-0000-0000-000000000001',
  '70000000-0000-0000-0000-000000000001',
  'update', '{}'::jsonb, '{"name":"C03 synthetic preservation baseline"}'::jsonb,
  'C03 integrated synthetic audit sentinel'
);

UPDATE public.course_editorial_state
SET availability_override_status = 'unavailable',
    availability_evidence_url = 'https://inst-a.example/curso-1',
    availability_observed_at = now() - interval '1 hour',
    availability_valid_until = now() + interval '1 day',
    availability_override_by = '70000000-0000-0000-0000-000000000001'
WHERE course_id = '20000000-0000-0000-0000-000000000001';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.admin_members
    WHERE user_id = '70000000-0000-0000-0000-000000000001'
      AND role = 'admin' AND is_active AND account_status = 'ready'
  ) THEN RAISE EXCEPTION 'C03 synthetic admin fixture was not established'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM auth.users
    WHERE id = '75000000-0000-0000-0000-000000000001'
      AND email = 'c03-inflight@local.test' AND email_confirmed_at IS NULL
  ) THEN RAISE EXCEPTION 'C03 synthetic invitation identity was not established'; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.course_editorial_state
    WHERE course_id = '20000000-0000-0000-0000-000000000001'
      AND availability_override_status = 'unavailable'
  ) THEN RAISE EXCEPTION 'C03 editorial availability fixture was not established'; END IF;
  IF EXISTS (
    SELECT 1 FROM public.admin_invitations
    WHERE metadata ->> 'request_id' = 'c03-inflight-request-20261006'
  ) THEN RAISE EXCEPTION 'C03 request id unexpectedly exists before the drill'; END IF;
  IF EXISTS (
    SELECT 1 FROM private.h3_admin_quota_events
    WHERE scope = 'edge-request:70000000-0000-0000-0000-000000000001'
      AND cardinality(events) <> 0
  ) THEN RAISE EXCEPTION 'C03 Edge quota scope is not clean before the drill'; END IF;
END;
$$;

COMMIT;
