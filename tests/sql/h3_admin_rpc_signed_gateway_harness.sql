\set ON_ERROR_STOP on
-- Disposable PG17 only. The caller must receive a separate JIT before running.
-- Requires h3_admin_quota_harness.sql first; fixtures are synthetic and local-only.
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql
\ir ../../db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql

DO $$ DECLARE quota_wrapper TEXT; BEGIN
  IF pg_catalog.to_regclass('private.h3_admin_quota_events') IS NULL THEN
    RAISE EXCEPTION 'Run the disposable quota harness before the signed gateway harness';
  END IF;
  SELECT p.prosrc INTO quota_wrapper
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = 'public.admin_get_course_queue_filtered(integer,text,text,text,text)'::REGPROCEDURE;
  IF quota_wrapper IS NULL OR pg_catalog.strpos(quota_wrapper, 'H3_QUOTA_WRAPPER_V1') = 0 THEN
    RAISE EXCEPTION 'Signed gateway quota assertions require the public H3 quota wrapper';
  END IF;
END; $$;

\set gateway_key_id 'local-pg17-k1'
\set gateway_project_ref 'local'
\set gateway_actor '74000000-0000-0000-0000-000000000001'
\set gateway_secret 'local-only-pg17-rpc-gateway-fixture-key-32-bytes'
\set gateway_nonce '74000000-0000-4000-8000-000000000001'
\set gateway_rpc 'admin_current_user_role'
\set gateway_payload '{}'

INSERT INTO private.h3_admin_rpc_gateway_keys(key_id, project_ref, secret)
VALUES (:'gateway_key_id', :'gateway_project_ref', :'gateway_secret');
INSERT INTO auth.users(id,email)
VALUES (:'gateway_actor'::UUID,'gateway-admin@local.test') ON CONFLICT DO NOTHING;
INSERT INTO public.admin_members(user_id,role,is_active,account_status)
VALUES (:'gateway_actor'::UUID,'admin',true,'ready') ON CONFLICT DO NOTHING;
INSERT INTO auth.users(id,email)
VALUES ('74000000-0000-0000-0000-000000000002','gateway-non-editor@local.test') ON CONFLICT DO NOTHING;

SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT AS gateway_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'gateway_project_ref', 'POST', 'admin_signed_rpc',
    :'gateway_actor', :'gateway_issued_at', :'gateway_nonce', :'gateway_key_id'),
  :'gateway_secret'
) AS gateway_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'gateway_project_ref', 'POST',
    'admin_signed_rpc', :'gateway_rpc', :'gateway_actor', :'gateway_issued_at', :'gateway_nonce',
    :'gateway_key_id', :'gateway_payload'),
  :'gateway_secret'
) AS gateway_payload_signature
\gset

SELECT set_config('request.path', '/rpc/admin_signed_rpc', false);
SELECT set_config('request.method', 'POST', false);
SELECT set_config('request.jwt.claim.sub', :'gateway_actor', false);
SELECT set_config('request.jwt.claim.role', 'authenticated', false);
SELECT set_config('request.jwt.claim.aal', 'aal2', false);
SELECT set_config('request.jwt.claims',
  pg_catalog.jsonb_build_object('sub', :'gateway_actor', 'role', 'authenticated', 'aal', 'aal2')::TEXT, false);
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'gateway_key_id',
  'x-studiamatch-admin-rpc-actor', :'gateway_actor',
  'x-studiamatch-admin-rpc-issued-at', :'gateway_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'gateway_nonce',
  'x-studiamatch-admin-rpc-signature', :'gateway_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'gateway_payload_signature'
)::TEXT, false);

SET ROLE authenticated;
SELECT public.h3_admin_rpc_signed_gateway_pre_request();
SELECT public.admin_signed_rpc(:'gateway_rpc', :'gateway_payload'::JSONB, :'gateway_payload');
RESET ROLE;

-- Replay the exact same proof immediately, while its timestamp and nonce record are
-- both still inside their 60-second validity window.
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM private.h3_admin_rpc_gateway_nonces
    WHERE nonce = '74000000-0000-4000-8000-000000000001'
      AND actor = '74000000-0000-0000-0000-000000000001'
      AND rpc_name = 'admin_current_user_role'
  ) THEN
    RAISE EXCEPTION 'verified dispatcher proof did not consume the nonce';
  END IF;
END; $$;
SET ROLE authenticated;
DO $$ DECLARE payload TEXT; detail TEXT; BEGIN
  BEGIN
    PERFORM public.admin_signed_rpc('admin_current_user_role', '{}'::JSONB, '{}');
    RAISE EXCEPTION 'committed payload-bound proof replay was admitted';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS payload = MESSAGE_TEXT, detail = PG_EXCEPTION_DETAIL;
    IF payload::JSONB->>'code' <> 'rpc_replay_rejected'
       OR (detail::JSONB->>'status')::INTEGER <> 409 THEN RAISE; END IF;
  END;
END; $$;
RESET ROLE;

-- Explicit JSON null must not become SQL LIMIT NULL (an unbounded page).
\set gateway_null_rpc 'admin_get_course_queue_filtered'
\set gateway_null_payload '{"p_first":null}'
\set gateway_null_nonce '74000000-0000-4000-8000-000000000011'
SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT AS null_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'gateway_project_ref', 'POST', 'admin_signed_rpc',
    :'gateway_actor', :'null_issued_at', :'gateway_null_nonce', :'gateway_key_id'),
  :'gateway_secret'
) AS null_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'gateway_project_ref', 'POST',
    'admin_signed_rpc', :'gateway_null_rpc', :'gateway_actor', :'null_issued_at', :'gateway_null_nonce',
    :'gateway_key_id', :'gateway_null_payload'),
  :'gateway_secret'
) AS null_payload_signature
\gset
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'gateway_key_id',
  'x-studiamatch-admin-rpc-actor', :'gateway_actor',
  'x-studiamatch-admin-rpc-issued-at', :'null_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'gateway_null_nonce',
  'x-studiamatch-admin-rpc-signature', :'null_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'null_payload_signature'
)::TEXT, false);
SELECT set_config('request.jwt.claim.aal', 'aal1', false);
SELECT set_config('request.jwt.claims',
  pg_catalog.jsonb_build_object('sub', :'gateway_actor', 'role', 'authenticated', 'aal', 'aal1')::TEXT, false);
SET ROLE authenticated;
DO $$ DECLARE result JSONB; BEGIN
  result := public.admin_signed_rpc(
    'admin_get_course_queue_filtered', '{"p_first":null}'::JSONB, '{"p_first":null}'
  );
  IF result #>> '{0,error}' IS DISTINCT FROM 'mfa_required'
     OR current_setting('response.status', true) IS DISTINCT FROM '403' THEN
    RAISE EXCEPTION 'signed NULL request did not preserve MFA response and charge its quota';
  END IF;
END; $$;
RESET ROLE;
DO $$ BEGIN
  IF COALESCE((SELECT cardinality(events) FROM private.h3_admin_quota_events
               WHERE scope = 'rpc-read:74000000-0000-0000-0000-000000000001'), 0) <> 2 THEN
    RAISE EXCEPTION 'signed AAL1 NULL request did not charge its read quota';
  END IF;
END; $$;

-- The quota wrapper returns the AAL1 error row, so that proof's nonce commits.
-- A fresh proof is required for the following AAL2 request.
\set gateway_null_admin_nonce '74000000-0000-4000-8000-000000000013'
SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT AS null_admin_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'gateway_project_ref', 'POST', 'admin_signed_rpc',
    :'gateway_actor', :'null_admin_issued_at', :'gateway_null_admin_nonce', :'gateway_key_id'),
  :'gateway_secret'
) AS null_admin_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'gateway_project_ref', 'POST',
    'admin_signed_rpc', :'gateway_null_rpc', :'gateway_actor', :'null_admin_issued_at',
    :'gateway_null_admin_nonce', :'gateway_key_id', :'gateway_null_payload'),
  :'gateway_secret'
) AS null_admin_payload_signature
\gset
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'gateway_key_id',
  'x-studiamatch-admin-rpc-actor', :'gateway_actor',
  'x-studiamatch-admin-rpc-issued-at', :'null_admin_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'gateway_null_admin_nonce',
  'x-studiamatch-admin-rpc-signature', :'null_admin_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'null_admin_payload_signature'
)::TEXT, false);
SELECT set_config('request.jwt.claim.aal', 'aal2', false);
SELECT set_config('request.jwt.claims',
  pg_catalog.jsonb_build_object('sub', :'gateway_actor', 'role', 'authenticated', 'aal', 'aal2')::TEXT, false);
SET ROLE authenticated;
DO $$ DECLARE result JSONB; BEGIN
  result := public.admin_signed_rpc(
    'admin_get_course_queue_filtered', '{"p_first":null}'::JSONB, '{"p_first":null}'
  );
  IF pg_catalog.jsonb_array_length(result) <> 1
     OR result #>> '{0,error}' IS DISTINCT FROM 'First must be between 1 and 100'
     OR result #> '{0,courses}' IS DISTINCT FROM 'null'::JSONB
     OR result #> '{0,page_info}' IS DISTINCT FROM 'null'::JSONB THEN
    RAISE EXCEPTION 'signed queue dispatcher did not preserve the NULL page-size error contract';
  END IF;
END; $$;
RESET ROLE;
DO $$ BEGIN
  IF COALESCE((SELECT cardinality(events) FROM private.h3_admin_quota_events
               WHERE scope = 'rpc-read:74000000-0000-0000-0000-000000000001'), 0) <> 3 THEN
    RAISE EXCEPTION 'signed AAL2 NULL request did not charge its read quota';
  END IF;
END; $$;

-- A signed JSON null version must reach the editor's conflict guard and remain mutation-free.
\set gateway_null_version_rpc 'admin_update_course'
\set gateway_null_version_nonce '74000000-0000-4000-8000-000000000014'
SELECT course_id::TEXT AS null_version_course_id
  FROM public.course_editorial_state ORDER BY course_id LIMIT 1
\gset
CREATE TEMP TABLE h3_gateway_null_version_before AS
SELECT es.course_id, pg_catalog.to_jsonb(es) AS row_state,
       (SELECT count(*) FROM public.course_editorial_audit a
         WHERE a.course_id = es.course_id AND a.action = 'update') AS audit_count
  FROM public.course_editorial_state es
 WHERE es.course_id = :'null_version_course_id'::UUID;
SELECT pg_catalog.jsonb_build_object(
  'p_course_id', :'null_version_course_id',
  'p_manual_overrides', pg_catalog.jsonb_build_object('name', 'Null version must not write'),
  'p_version', NULL,
  'p_reason', 'reject missing version'
)::TEXT AS null_version_payload
\gset
SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT AS null_version_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'gateway_project_ref', 'POST', 'admin_signed_rpc',
    :'gateway_actor', :'null_version_issued_at', :'gateway_null_version_nonce', :'gateway_key_id'),
  :'gateway_secret'
) AS null_version_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'gateway_project_ref', 'POST',
    'admin_signed_rpc', :'gateway_null_version_rpc', :'gateway_actor', :'null_version_issued_at',
    :'gateway_null_version_nonce', :'gateway_key_id', :'null_version_payload'),
  :'gateway_secret'
) AS null_version_payload_signature
\gset
SELECT set_config('request.path', '/rpc/admin_signed_rpc', false);
SELECT set_config('request.method', 'POST', false);
SELECT set_config('request.jwt.claim.sub', :'gateway_actor', false);
SELECT set_config('request.jwt.claim.role', 'authenticated', false);
SELECT set_config('request.jwt.claim.aal', 'aal2', false);
SELECT set_config('request.jwt.claims', pg_catalog.jsonb_build_object(
  'sub', :'gateway_actor', 'role', 'authenticated', 'aal', 'aal2'
)::TEXT, false);
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'gateway_key_id',
  'x-studiamatch-admin-rpc-actor', :'gateway_actor',
  'x-studiamatch-admin-rpc-issued-at', :'null_version_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'gateway_null_version_nonce',
  'x-studiamatch-admin-rpc-signature', :'null_version_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'null_version_payload_signature'
)::TEXT, false);
CREATE TEMP TABLE h3_gateway_null_version_result(result JSONB);
GRANT INSERT ON h3_gateway_null_version_result TO authenticated;
SET ROLE authenticated;
SELECT public.h3_admin_rpc_signed_gateway_pre_request();
INSERT INTO h3_gateway_null_version_result(result)
SELECT public.admin_signed_rpc(
  :'gateway_null_version_rpc', :'null_version_payload'::JSONB, :'null_version_payload'
);
RESET ROLE;
DO $$
DECLARE result JSONB; before_row RECORD; after_row RECORD;
BEGIN
  SELECT r.result INTO result FROM h3_gateway_null_version_result r;
  SELECT * INTO before_row FROM h3_gateway_null_version_before;
  SELECT pg_catalog.to_jsonb(es) AS row_state,
         (SELECT count(*) FROM public.course_editorial_audit a
           WHERE a.course_id = es.course_id AND a.action = 'update') AS audit_count
    INTO after_row
    FROM public.course_editorial_state es
   WHERE es.course_id = before_row.course_id;
  IF result #>> '{0,success}' IS DISTINCT FROM 'false'
     OR result #>> '{0,error}' NOT LIKE 'Version conflict:%'
     OR after_row.row_state IS DISTINCT FROM before_row.row_state
     OR after_row.audit_count IS DISTINCT FROM before_row.audit_count THEN
    RAISE EXCEPTION 'signed NULL version was not rejected without a write';
  END IF;
END; $$;

-- A signed malformed page request from a non-editor keeps the RBAC error first.
\set gateway_non_editor_actor '74000000-0000-0000-0000-000000000002'
\set gateway_non_editor_nonce '74000000-0000-4000-8000-000000000012'
SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT AS non_editor_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'gateway_project_ref', 'POST', 'admin_signed_rpc',
    :'gateway_non_editor_actor', :'non_editor_issued_at', :'gateway_non_editor_nonce', :'gateway_key_id'),
  :'gateway_secret'
) AS non_editor_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'gateway_project_ref', 'POST',
    'admin_signed_rpc', :'gateway_null_rpc', :'gateway_non_editor_actor', :'non_editor_issued_at',
    :'gateway_non_editor_nonce', :'gateway_key_id', :'gateway_null_payload'),
  :'gateway_secret'
) AS non_editor_payload_signature
\gset
SELECT set_config('request.jwt.claim.sub', :'gateway_non_editor_actor', false);
SELECT set_config('request.jwt.claim.aal', 'aal2', false);
SELECT set_config('request.jwt.claims', pg_catalog.jsonb_build_object(
  'sub', :'gateway_non_editor_actor', 'role', 'authenticated', 'aal', 'aal2'
)::TEXT, false);
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'gateway_key_id',
  'x-studiamatch-admin-rpc-actor', :'gateway_non_editor_actor',
  'x-studiamatch-admin-rpc-issued-at', :'non_editor_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'gateway_non_editor_nonce',
  'x-studiamatch-admin-rpc-signature', :'non_editor_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'non_editor_payload_signature'
)::TEXT, false);
SET ROLE authenticated;
DO $$ DECLARE result JSONB; BEGIN
  result := public.admin_signed_rpc(
    'admin_get_course_queue_filtered', '{"p_first":null}'::JSONB, '{"p_first":null}'
  );
  IF pg_catalog.jsonb_array_length(result) <> 1
     OR result #>> '{0,error}' IS DISTINCT FROM 'User is not an active editor'
     OR result #> '{0,courses}' IS DISTINCT FROM 'null'::JSONB
     OR result #> '{0,page_info}' IS DISTINCT FROM 'null'::JSONB THEN
    RAISE EXCEPTION 'signed queue dispatcher bypassed the active-editor gate';
  END IF;
END; $$;
RESET ROLE;
DO $$ BEGIN
  IF COALESCE((SELECT cardinality(events) FROM private.h3_admin_quota_events
               WHERE scope = 'rpc-read:74000000-0000-0000-0000-000000000002'), 0) <> 1 THEN
    RAISE EXCEPTION 'signed non-editor NULL request did not charge its read quota';
  END IF;
END; $$;
SELECT set_config('request.jwt.claim.sub', :'gateway_actor', false);
SELECT set_config('request.jwt.claim.aal', 'aal2', false);
SELECT set_config('request.jwt.claims',
  pg_catalog.jsonb_build_object('sub', :'gateway_actor', 'role', 'authenticated', 'aal', 'aal2')::TEXT, false);

-- The signed source string and the actual JSONB dispatch arguments must agree.
\set gateway_nonce_mismatch '74000000-0000-4000-8000-000000000002'
SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT AS mismatch_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'gateway_project_ref', 'POST', 'admin_signed_rpc',
    :'gateway_actor', :'mismatch_issued_at', :'gateway_nonce_mismatch', :'gateway_key_id'),
  :'gateway_secret'
) AS mismatch_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'gateway_project_ref', 'POST',
    'admin_signed_rpc', :'gateway_rpc', :'gateway_actor', :'mismatch_issued_at', :'gateway_nonce_mismatch',
    :'gateway_key_id', :'gateway_payload'),
  :'gateway_secret'
) AS mismatch_payload_signature
\gset
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'gateway_key_id',
  'x-studiamatch-admin-rpc-actor', :'gateway_actor',
  'x-studiamatch-admin-rpc-issued-at', :'mismatch_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'gateway_nonce_mismatch',
  'x-studiamatch-admin-rpc-signature', :'mismatch_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'mismatch_payload_signature'
)::TEXT, false);
SET ROLE authenticated;
DO $$ DECLARE payload TEXT; BEGIN
  BEGIN
    PERFORM public.admin_signed_rpc('admin_current_user_role', '{"unexpected":true}'::JSONB, '{}');
    RAISE EXCEPTION 'payload/argument mismatch was admitted';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS payload = MESSAGE_TEXT;
    IF payload::JSONB->>'code' <> 'rpc_signature_invalid' THEN RAISE; END IF;
  END;
END; $$;
RESET ROLE;

-- A payload signature cannot be moved to a different target, even if both targets
-- are on the application allowlist.
SET ROLE authenticated;
DO $$ DECLARE payload TEXT; BEGIN
  BEGIN
    PERFORM public.admin_signed_rpc('admin_get_onboarding_status', '{}'::JSONB, '{}');
    RAISE EXCEPTION 'payload proof was portable across RPC targets';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS payload = MESSAGE_TEXT;
    IF payload::JSONB->>'code' <> 'rpc_signature_invalid' THEN RAISE; END IF;
  END;
END; $$;
RESET ROLE;

-- Authenticated legacy RPC paths are closed; service-role finalizers retain their
-- previously authorized path and the regular non-Admin route remains a no-op.
SELECT set_config('request.path', '/rpc/admin_current_user_role', false);
SET ROLE authenticated;
DO $$ DECLARE payload TEXT; BEGIN
  BEGIN
    PERFORM public.h3_admin_rpc_signed_gateway_pre_request();
    RAISE EXCEPTION 'legacy authenticated Admin RPC bypass was admitted';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS payload = MESSAGE_TEXT;
    IF payload::JSONB->>'code' <> 'rpc_signed_wrapper_required' THEN RAISE; END IF;
  END;
END; $$;
RESET ROLE;

SELECT set_config('request.path', '/rpc/admin_signed_rpc', false);
SELECT set_config('request.headers', '{}'::TEXT, false);
SET ROLE authenticated;
DO $$ DECLARE payload TEXT; detail TEXT; BEGIN
  BEGIN
    PERFORM public.h3_admin_rpc_signed_gateway_pre_request();
    RAISE EXCEPTION 'unsigned dispatcher request was admitted';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS payload = MESSAGE_TEXT, detail = PG_EXCEPTION_DETAIL;
    IF payload::JSONB->>'code' <> 'rpc_signature_required'
       OR (detail::JSONB->>'status')::INTEGER <> 403
       OR NOT (detail::JSONB ? 'headers') THEN RAISE; END IF;
  END;
END; $$;
RESET ROLE;

SELECT set_config('request.jwt.claim.role', 'service_role', false);
SELECT set_config('request.jwt.claims', pg_catalog.jsonb_build_object('role', 'service_role')::TEXT, false);
SELECT set_config('request.path', '/rpc/admin_invitation_complete', false);
SET ROLE service_role;
SELECT public.h3_admin_rpc_signed_gateway_pre_request();
RESET ROLE;
SELECT set_config('request.jwt.claim.role', 'anon', false);
SELECT set_config('request.jwt.claims', pg_catalog.jsonb_build_object('role', 'anon')::TEXT, false);
SELECT set_config('request.path', '/courses', false);
SELECT set_config('request.method', 'GET', false);
SET ROLE anon;
SELECT public.h3_admin_rpc_signed_gateway_pre_request();
RESET ROLE;

DO $$ BEGIN
  IF has_table_privilege('anon', 'private.h3_admin_rpc_gateway_keys', 'SELECT')
     OR has_table_privilege('authenticated', 'private.h3_admin_rpc_gateway_keys', 'SELECT')
     OR has_table_privilege('service_role', 'private.h3_admin_rpc_gateway_keys', 'SELECT')
     OR has_table_privilege('authenticated', 'private.h3_admin_rpc_gateway_nonces', 'INSERT')
     OR has_function_privilege('authenticated', 'private.h3_admin_rpc_gateway_hmac(text,text)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'private.h3_admin_rpc_gateway_verify_payload(text,jsonb,text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'gateway key, nonce, or verifier is exposed to API roles';
  END IF;
  IF NOT has_function_privilege('authenticated', 'public.admin_signed_rpc(text,jsonb,text)', 'EXECUTE')
     OR has_function_privilege('anon', 'public.admin_signed_rpc(text,jsonb,text)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'public.admin_update_course(uuid,jsonb,integer,text)', 'EXECUTE') IS FALSE THEN
    RAISE EXCEPTION 'wrapper grants do not preserve the authenticated execution contract';
  END IF;
END; $$;

SELECT 'h3_admin_rpc_signed_gateway_harness_ok' AS result;
