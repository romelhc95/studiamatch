-- Disposable PG17-only fixture. Exercises the existing callback RPC contract;
-- no application Admin mail, Auth identity, or Pro data is contacted.
-- StudIAMatch-Docs: .context/componentes/database_migrations.md#first-admin-auth-bootstrap

BEGIN;

INSERT INTO auth.users (id, email, invited_at, email_confirmed_at)
VALUES (
  '39000000-0000-0000-0000-000000000002',
  'romelhc95@gmail.com',
  clock_timestamp() - INTERVAL '1 hour',
  NULL
);
INSERT INTO auth.users (id, email, invited_at, email_confirmed_at)
VALUES (
  '39000000-0000-0000-0000-000000000003',
  'other-first-admin@local.test',
  clock_timestamp() - INTERVAL '1 hour',
  clock_timestamp()
);

SELECT set_config('request.jwt.claim.sub', '39000000-0000-0000-0000-000000000002', true);

SET LOCAL ROLE authenticated;
DO $$
DECLARE
  result_row RECORD;
BEGIN
  SELECT * INTO result_row FROM public.admin_accept_current_invitation(
    '49000000-0000-0000-0000-000000000099'
  );
  IF result_row.success IS DISTINCT FROM false
     OR result_row.error_code IS DISTINCT FROM 'invitation_not_pending' THEN
    RAISE EXCEPTION 'an explicit missing invitation id must not fall back to first-admin bootstrap';
  END IF;
END;
$$;
RESET ROLE;

SET LOCAL ROLE authenticated;
DO $$
DECLARE
  result_row RECORD;
BEGIN
  SELECT * INTO result_row FROM public.admin_accept_current_invitation(NULL);
  IF result_row.success IS DISTINCT FROM false
     OR result_row.error_code IS DISTINCT FROM 'invitation_not_pending' THEN
    RAISE EXCEPTION 'unconfirmed Auth identity must not bootstrap an Admin';
  END IF;
END;
$$;
RESET ROLE;

SELECT set_config('request.jwt.claim.sub', '39000000-0000-0000-0000-000000000003', true);
SET LOCAL ROLE authenticated;
DO $$
DECLARE
  result_row RECORD;
BEGIN
  SELECT * INTO result_row FROM public.admin_accept_current_invitation(NULL);
  IF result_row.success IS DISTINCT FROM false
     OR result_row.error_code IS DISTINCT FROM 'invitation_not_pending' THEN
    RAISE EXCEPTION 'a different confirmed Auth identity must not bootstrap the first Admin';
  END IF;
END;
$$;
RESET ROLE;

-- A previously confirmed address is not proof that the current Auth invite
-- was accepted. Confirmation must be at or after the invitation timestamp.
UPDATE auth.users
SET email_confirmed_at = invited_at - INTERVAL '1 minute'
WHERE id = '39000000-0000-0000-0000-000000000002';
SELECT set_config('request.jwt.claim.sub', '39000000-0000-0000-0000-000000000002', true);
SET LOCAL ROLE authenticated;
DO $$
DECLARE
  result_row RECORD;
BEGIN
  SELECT * INTO result_row FROM public.admin_accept_current_invitation(NULL);
  IF result_row.success IS DISTINCT FROM false
     OR result_row.error_code IS DISTINCT FROM 'invitation_not_pending' THEN
    RAISE EXCEPTION 'confirmation predating the Auth invite must not bootstrap an Admin';
  END IF;
END;
$$;
RESET ROLE;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.admin_members WHERE user_id IN (
       '39000000-0000-0000-0000-000000000002',
       '39000000-0000-0000-0000-000000000003'
     ))
     OR EXISTS (SELECT 1 FROM public.admin_invitations WHERE email IN (
       'romelhc95@gmail.com', 'other-first-admin@local.test'
     )) THEN
    RAISE EXCEPTION 'unconfirmed or non-designated Auth identity created bootstrap rows';
  END IF;
END;
$$;

UPDATE auth.users
SET email_confirmed_at = clock_timestamp()
WHERE id = '39000000-0000-0000-0000-000000000002';

SELECT set_config('request.jwt.claim.sub', '39000000-0000-0000-0000-000000000002', true);
\set first_admin_key_id 'pg17-first-admin-k1'
\set first_admin_project_ref 'local-h3-first-admin'
\set first_admin_actor '39000000-0000-0000-0000-000000000002'
\set first_admin_secret 'local-only-pg17-first-admin-rpc-gateway-key-32-bytes'
\set first_admin_nonce '39000000-0000-4000-8000-000000000001'
\set first_admin_rpc 'admin_accept_current_invitation'
\set first_admin_payload '{"p_invitation_id":null}'

INSERT INTO private.h3_admin_rpc_gateway_keys(key_id, project_ref, secret)
VALUES (:'first_admin_key_id', :'first_admin_project_ref', :'first_admin_secret');

SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT
  AS first_admin_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'first_admin_project_ref',
    'POST', 'admin_signed_rpc', :'first_admin_actor', :'first_admin_issued_at',
    :'first_admin_nonce', :'first_admin_key_id'),
  :'first_admin_secret'
) AS first_admin_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'first_admin_project_ref',
    'POST', 'admin_signed_rpc', :'first_admin_rpc', :'first_admin_actor',
    :'first_admin_issued_at', :'first_admin_nonce', :'first_admin_key_id',
    :'first_admin_payload'),
  :'first_admin_secret'
) AS first_admin_payload_signature
\gset

SELECT set_config('request.path', '/rpc/admin_signed_rpc', true);
SELECT set_config('request.method', 'POST', true);
SELECT set_config('request.jwt.claim.role', 'authenticated', true);
SELECT set_config('request.jwt.claim.aal', 'aal2', true);
SELECT set_config('request.jwt.claims', pg_catalog.jsonb_build_object(
  'sub', :'first_admin_actor', 'role', 'authenticated', 'aal', 'aal2'
)::TEXT, true);
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'first_admin_key_id',
  'x-studiamatch-admin-rpc-actor', :'first_admin_actor',
  'x-studiamatch-admin-rpc-issued-at', :'first_admin_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'first_admin_nonce',
  'x-studiamatch-admin-rpc-signature', :'first_admin_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'first_admin_payload_signature'
)::TEXT, true);

CREATE TEMP TABLE h3_first_admin_quota_before AS
SELECT COALESCE((
  SELECT cardinality(events)
  FROM private.h3_admin_quota_events
  WHERE scope = 'rpc-write:' || :'first_admin_actor'
), 0) AS event_count;

SET LOCAL ROLE authenticated;
SELECT public.h3_admin_rpc_signed_gateway_pre_request();
DO $$
DECLARE
  result_payload JSONB;
BEGIN
  result_payload := public.admin_signed_rpc(
    'admin_accept_current_invitation',
    '{"p_invitation_id":null}'::JSONB,
    '{"p_invitation_id":null}'
  );
  IF result_payload #>> '{0,success}' IS DISTINCT FROM 'true'
     OR result_payload #>> '{0,account_status}' IS DISTINCT FROM 'password_pending'
     OR result_payload #>> '{0,role}' IS DISTINCT FROM 'admin' THEN
    RAISE EXCEPTION 'signed callback must enter existing password_pending lifecycle, got %', result_payload;
  END IF;
END;
$$;
RESET ROLE;

DO $$
DECLARE event_count INTEGER; previous_count INTEGER;
BEGIN
  SELECT quota_before.event_count INTO previous_count
  FROM h3_first_admin_quota_before AS quota_before;
  SELECT COALESCE((
    SELECT cardinality(events)
    FROM private.h3_admin_quota_events
    WHERE scope = 'rpc-write:39000000-0000-0000-0000-000000000002'
  ), 0) INTO event_count;
  IF event_count <> previous_count + 1 THEN
    RAISE EXCEPTION 'one signed callback must charge the lifecycle write quota exactly once; before %, after %', previous_count, event_count;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM private.h3_admin_rpc_gateway_nonces
    WHERE nonce = '39000000-0000-4000-8000-000000000001'
      AND actor = '39000000-0000-0000-0000-000000000002'
      AND rpc_name = 'admin_accept_current_invitation'
  ) THEN
    RAISE EXCEPTION 'signed callback gateway proof was not consumed';
  END IF;
END;
$$;

DO $$
DECLARE
  invitation_row public.admin_invitations%ROWTYPE;
  member_row public.admin_members%ROWTYPE;
  invitation_count INTEGER;
  bootstrap_audit_count INTEGER;
BEGIN
  SELECT * INTO member_row FROM public.admin_members
  WHERE user_id = '39000000-0000-0000-0000-000000000002';
  IF member_row.role IS DISTINCT FROM 'admin'
     OR member_row.is_active IS DISTINCT FROM false
     OR member_row.account_status IS DISTINCT FROM 'password_pending'
     OR member_row.password_set_at IS NOT NULL
     OR member_row.invited_by IS NOT NULL THEN
    RAISE EXCEPTION 'bootstrap membership must remain inactive/password-pending with no fabricated inviter';
  END IF;

  SELECT * INTO invitation_row FROM public.admin_invitations WHERE id = member_row.last_invitation_id;
  IF invitation_row.status IS DISTINCT FROM 'accepted'
     OR invitation_row.accepted_user_id IS DISTINCT FROM member_row.user_id
     OR invitation_row.role IS DISTINCT FROM 'admin'
     OR invitation_row.created_by_user_id IS NOT NULL
     OR invitation_row.token_hash IS NOT NULL
     OR invitation_row.last_sent_at IS NULL
     OR invitation_row.last_sent_at IS DISTINCT FROM
          (invitation_row.metadata ->> 'auth_invited_at')::TIMESTAMPTZ
     OR invitation_row.send_count IS DISTINCT FROM 1
     OR invitation_row.metadata ->> 'source' IS DISTINCT FROM 'first_admin_auth_bootstrap'
     OR invitation_row.metadata ->> 'auth_invitation_origin' IS DISTINCT FROM 'supabase_auth'
     OR invitation_row.metadata ->> 'auth_invited_at' IS NULL
     OR invitation_row.metadata ->> 'auth_email_confirmed_at' IS NULL
     OR (invitation_row.metadata ->> 'auth_email_confirmed_at')::TIMESTAMPTZ <
          (invitation_row.metadata ->> 'auth_invited_at')::TIMESTAMPTZ
     OR invitation_row.metadata ->> 'app_email_sent' IS DISTINCT FROM 'false' THEN
    RAISE EXCEPTION 'bootstrap invitation must accurately represent external Auth delivery';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.admin_membership_audit AS audit_row
    WHERE audit_row.invitation_id = invitation_row.id
      AND audit_row.action = 'first_admin_bootstrap'
      AND audit_row.actor_user_id = member_row.user_id
      AND audit_row.target_user_id = member_row.user_id
      AND audit_row.old_values ->> 'supabase_auth_invitation' = 'created_and_email_confirmed'
  ) OR NOT EXISTS (
    SELECT 1 FROM public.admin_membership_audit AS audit_row
    WHERE audit_row.invitation_id = invitation_row.id
      AND audit_row.action = 'accept'
      AND audit_row.actor_user_id = member_row.user_id
      AND audit_row.target_user_id = member_row.user_id
  ) THEN
    RAISE EXCEPTION 'bootstrap and normal acceptance events must both be audited against the real Auth actor';
  END IF;

  SELECT count(*) INTO invitation_count FROM public.admin_invitations
  WHERE email = 'romelhc95@gmail.com';
  SELECT count(*) INTO bootstrap_audit_count FROM public.admin_membership_audit
  WHERE action = 'first_admin_bootstrap';
  IF invitation_count <> 1 OR bootstrap_audit_count <> 1 THEN
    RAISE EXCEPTION 'first Admin bootstrap must be one-time';
  END IF;

  IF has_function_privilege('anon', 'public.admin_accept_current_invitation(uuid)', 'EXECUTE')
     OR NOT has_function_privilege('authenticated', 'public.admin_accept_current_invitation(uuid)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'private.h3_first_admin_auth_bootstrap_invitation()', 'EXECUTE') THEN
    RAISE EXCEPTION 'bootstrap must keep the RPC authenticated-only and helper private';
  END IF;
END;
$$;

CREATE TEMP TABLE h3_first_admin_repeat_quota_before AS
SELECT COALESCE((
  SELECT cardinality(events)
  FROM private.h3_admin_quota_events
  WHERE scope = 'rpc-write:39000000-0000-0000-0000-000000000002'
), 0) AS event_count;
SET LOCAL ROLE authenticated;
DO $$
DECLARE
  result_row RECORD;
BEGIN
  SELECT * INTO result_row FROM public.admin_accept_current_invitation(NULL);
  IF result_row.success IS DISTINCT FROM true
     OR result_row.account_status IS DISTINCT FROM 'password_pending' THEN
    RAISE EXCEPTION 'repeated callback must be idempotent and must not reactivate the Admin';
  END IF;
END;
$$;
RESET ROLE;
DO $$
DECLARE event_count INTEGER; previous_count INTEGER;
BEGIN
  SELECT quota_before.event_count INTO previous_count
  FROM h3_first_admin_repeat_quota_before AS quota_before;
  SELECT COALESCE((
    SELECT cardinality(events)
    FROM private.h3_admin_quota_events
    WHERE scope = 'rpc-write:39000000-0000-0000-0000-000000000002'
  ), 0) INTO event_count;
  IF event_count <> previous_count + 1 THEN
    RAISE EXCEPTION 'one repeated callback must charge the lifecycle write quota exactly once; before %, after %', previous_count, event_count;
  END IF;
END;
$$;

-- The harness marks a synthetic Auth password update before calling the
-- existing completion RPC; it does not exercise real Supabase Auth passwords.
UPDATE auth.users
SET encrypted_password = 'synthetic-pg17-test-hash'
WHERE id = '39000000-0000-0000-0000-000000000002';
SET LOCAL ROLE authenticated;
DO $$
DECLARE
  result_row RECORD;
BEGIN
  SELECT * INTO result_row FROM public.admin_complete_password_setup();
  IF result_row.success IS DISTINCT FROM true
     OR result_row.account_status IS DISTINCT FROM 'ready'
     OR result_row.role IS DISTINCT FROM 'admin' THEN
    RAISE EXCEPTION 'existing password-completion lifecycle did not finish the accepted first Admin';
  END IF;
END;
$$;
RESET ROLE;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.admin_members
    WHERE user_id = '39000000-0000-0000-0000-000000000002'
      AND role = 'admin' AND account_status = 'ready' AND is_active = true
      AND password_set_at IS NOT NULL
  ) OR NOT EXISTS (
    SELECT 1 FROM public.admin_membership_audit
    WHERE target_user_id = '39000000-0000-0000-0000-000000000002'
      AND action = 'password_set'
  ) THEN
    RAISE EXCEPTION 'ready/active state must follow the existing password-completion lifecycle';
  END IF;
END;
$$;

-- The real reservation RPC creates a normal pending row before Auth delivery;
-- the established contract intentionally leaves token_hash NULL at this step.
SET LOCAL ROLE service_role;
DO $$
DECLARE
  result_row RECORD;
  invitation_row public.admin_invitations%ROWTYPE;
  invitation_found BOOLEAN;
  failed_assertions TEXT[];
BEGIN
  SELECT * INTO result_row FROM public.admin_invitation_reserve(
    'ordinary-reservation@local.test', 'user',
    '39000000-0000-0000-0000-000000000002', NULL, false,
    'ordinary-null-token',
    jsonb_build_object('quota_recipient', repeat('a', 64)), NULL
  );
  IF result_row.success IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'ordinary invitation reservation with a NULL token hash failed: %', row_to_json(result_row);
  END IF;
  SELECT * INTO invitation_row FROM public.admin_invitations WHERE id = result_row.invitation_id;
  invitation_found := FOUND;
  failed_assertions := array_remove(ARRAY[
    CASE WHEN NOT invitation_found THEN 'invitation_row_missing' END,
    CASE WHEN invitation_row.token_hash IS NOT NULL THEN 'token_hash_not_null' END,
    CASE WHEN invitation_row.created_by_user_id IS DISTINCT FROM '39000000-0000-0000-0000-000000000002'::UUID
      THEN 'creator_mismatch' END,
    CASE WHEN invitation_row.status IS DISTINCT FROM 'pending' THEN 'status_not_pending' END,
    CASE WHEN invitation_row.metadata ->> 'source' IS DISTINCT FROM 'admin-invite'
      THEN 'source_mismatch' END,
    CASE WHEN invitation_row.metadata ->> 'delivery_state' IS DISTINCT FROM 'reserved'
      THEN 'delivery_state_mismatch' END
  ], NULL);
  IF invitation_row.token_hash IS NOT NULL
     OR invitation_row.created_by_user_id IS DISTINCT FROM '39000000-0000-0000-0000-000000000002'::UUID
     OR invitation_row.status IS DISTINCT FROM 'pending'
     OR invitation_row.metadata ->> 'source' IS DISTINCT FROM 'admin-invite'
     OR invitation_row.metadata ->> 'delivery_state' IS DISTINCT FROM 'reserved' THEN
    RAISE EXCEPTION 'ordinary invitation reservation contract failed: assertions=%, row_found=%, row=%, result=%',
      failed_assertions, invitation_found, row_to_json(invitation_row), row_to_json(result_row);
  END IF;
END;
$$;
RESET ROLE;

DO $$
DECLARE
  rejected_null_creator BOOLEAN := false;
  rejected_incomplete_bootstrap BOOLEAN := false;
  rejected_missing_provenance BOOLEAN := false;
BEGIN
  IF COALESCE((SELECT cardinality(events) FROM private.h3_admin_quota_events
               WHERE scope = 'invite-burst:39000000-0000-0000-0000-000000000002'), 0) <> 1
     OR COALESCE((SELECT cardinality(events) FROM private.h3_admin_quota_events
                  WHERE scope = 'invite-hour:39000000-0000-0000-0000-000000000002'), 0) <> 1
     OR COALESCE((SELECT cardinality(events) FROM private.h3_admin_quota_events
                  WHERE scope = 'invite-recipient:' || repeat('a', 64)), 0) <> 1
     OR COALESCE((SELECT cardinality(events) FROM private.h3_admin_quota_events
                  WHERE scope = 'invite-environment'), 0) <> 1 THEN
    RAISE EXCEPTION 'ordinary reservation must charge each established invite quota scope once';
  END IF;

  BEGIN
    INSERT INTO public.admin_invitations (
      email, role, token_hash, status, created_by_user_id, expires_at,
      last_sent_at, send_count, metadata
    ) VALUES (
      'forged-reservation@local.test', 'user', NULL, 'pending',
      NULL, clock_timestamp() + INTERVAL '24 hours', clock_timestamp(), 1,
      jsonb_build_object('source', 'admin-invite', 'reserved', true)
    );
  EXCEPTION WHEN check_violation THEN
    rejected_null_creator := true;
  END;
  IF NOT rejected_null_creator THEN
    RAISE EXCEPTION 'ordinary invitations must not accept a null creator';
  END IF;

  BEGIN
    INSERT INTO public.admin_invitations (
      email, role, token_hash, status, created_by_user_id, expires_at,
      last_sent_at, send_count, metadata
    ) VALUES (
      'forged-bootstrap@local.test', 'admin', NULL, 'pending',
      NULL, clock_timestamp() + INTERVAL '24 hours', clock_timestamp(), 1,
      jsonb_build_object('source', 'first_admin_auth_bootstrap')
    );
  EXCEPTION WHEN check_violation THEN
    rejected_incomplete_bootstrap := true;
  END;
  IF NOT rejected_incomplete_bootstrap THEN
    RAISE EXCEPTION 'bootstrap rows must include every required provenance field';
  END IF;

  BEGIN
    INSERT INTO public.admin_invitations (
      email, role, token_hash, status, created_by_user_id, expires_at,
      last_sent_at, send_count, metadata
    ) VALUES (
      'missing-provenance@local.test', 'admin', NULL, 'pending',
      NULL, clock_timestamp() + INTERVAL '24 hours', clock_timestamp(), 1,
      '{}'::JSONB
    );
  EXCEPTION WHEN check_violation THEN
    rejected_missing_provenance := true;
  END;
  IF NOT rejected_missing_provenance THEN
    RAISE EXCEPTION 'NULL metadata source must not admit an un-attributed invitation';
  END IF;
END;
$$;

ROLLBACK;
