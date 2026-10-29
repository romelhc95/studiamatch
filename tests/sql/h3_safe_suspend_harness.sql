\set ON_ERROR_STOP on
-- Run after the chained H3 harness in a disposable database, never remote.
-- Synthetic post-expand evidence proves additive state/audit is not discarded.
INSERT INTO public.course_editorial_audit
  (course_id, actor_user_id, action, old_values, new_values, reason)
VALUES (
  '20000000-0000-0000-0000-000000000001',
  '60000000-0000-0000-0000-000000000001', 'update',
  '{}'::jsonb, '{"name":"local rollback evidence"}'::jsonb,
  'Local safe suspension drill, no operational data'
);
UPDATE public.course_editorial_state
SET availability_override_status = 'unavailable',
    availability_evidence_url = 'https://inst-a.example/curso-1',
    availability_observed_at = now() - interval '1 hour',
    availability_valid_until = now() + interval '1 day',
    availability_override_by = '60000000-0000-0000-0000-000000000001'
WHERE course_id = '20000000-0000-0000-0000-000000000001';

CREATE TEMP TABLE h3_suspend_grants AS
SELECT p.oid, p.oid::regprocedure AS signature, r.role_name,
       has_function_privilege(r.role_name, p.oid, 'EXECUTE') AS allowed
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
CROSS JOIN (VALUES ('anon'), ('authenticated'), ('service_role')) r(role_name)
WHERE n.nspname='public' AND p.proname IN (
  'admin_update_course','admin_set_course_availability','admin_publish_course',
  'admin_unpublish_course','admin_archive_course','admin_update_quality_status',
  'admin_update_member','admin_create_member','admin_invitation_reserve',
  'admin_signed_rpc'
);
CREATE TEMP TABLE h3_suspend_fingerprints AS
SELECT
  (SELECT md5(string_agg(row_to_json(es)::text, ',' ORDER BY es.course_id)) FROM public.course_editorial_state es) AS state_digest,
  (SELECT md5(string_agg(row_to_json(a)::text, ',' ORDER BY a.id)) FROM public.course_editorial_audit a) AS audit_digest,
  (SELECT count(*) FROM public.admin_invitations) AS invitation_count,
  (SELECT count(*) FROM public.courses_public_effective) AS visible_count,
  to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL AS cohort_present;

-- Create genuine reservations BEFORE suspension; finalizers run as service_role,
-- not owner (owner would mask an accidental EXECUTE revocation).
CREATE TEMP TABLE h3_suspend_inflight (operation TEXT, user_id UUID, email TEXT, invitation_id UUID);
INSERT INTO h3_suspend_inflight (operation, user_id, email)
SELECT operation, gen_random_uuid(), 'suspend-' || operation || '-' || gen_random_uuid()::text || '@local.test'
FROM (VALUES ('complete'), ('fail'), ('reconcile')) modes(operation);
INSERT INTO auth.users (id,email) SELECT user_id,email FROM h3_suspend_inflight;
INSERT INTO auth.users (id,email) VALUES ('70000000-0000-0000-0000-000000000001','suspend-actor@local.test')
ON CONFLICT (id) DO NOTHING;
INSERT INTO public.admin_members (user_id,role,is_active,account_status)
VALUES ('70000000-0000-0000-0000-000000000001','admin',true,'ready') ON CONFLICT (user_id) DO NOTHING;
GRANT SELECT,UPDATE ON h3_suspend_inflight TO service_role;
SET ROLE service_role;
DO $$
DECLARE fixture RECORD; result RECORD;
BEGIN
  FOR fixture IN SELECT * FROM h3_suspend_inflight LOOP
    SELECT * INTO result FROM public.admin_invitation_reserve(
      fixture.email,'user','70000000-0000-0000-0000-000000000001',fixture.user_id,
      false,'suspend-' || fixture.user_id::text,
      jsonb_build_object('delivery_method',CASE WHEN fixture.operation='complete' THEN 'recovery' ELSE 'invite' END,
                        'quota_recipient',encode(sha256(convert_to(fixture.email,'UTF8')),'hex')),NULL);
    IF result.success IS DISTINCT FROM true THEN RAISE EXCEPTION 'Pre-suspension reserve failed: %',result.error_code; END IF;
    UPDATE h3_suspend_inflight SET invitation_id=result.invitation_id WHERE operation=fixture.operation;
  END LOOP;
END;
$$;
RESET ROLE;
-- Preserve the fingerprint before suspension itself, including new reservations.
UPDATE h3_suspend_fingerprints SET invitation_count=(SELECT count(*) FROM public.admin_invitations);

-- Prepare a valid payload-bound mutation proof before suspension. The post-suspend
-- attempt must be denied at the authenticated dispatcher ACL, not merely rejected
-- later by a target RPC or by an invalid signature.
\set suspend_gateway_key_id 'local-pg17-k1'
\set suspend_gateway_project_ref 'local'
\set suspend_gateway_actor '70000000-0000-0000-0000-000000000001'
\set suspend_gateway_nonce '70000000-0000-4000-8000-000000000001'
\set suspend_gateway_rpc 'admin_update_course'
\set suspend_gateway_payload '{"p_course_id":"20000000-0000-0000-0000-000000000001","p_manual_overrides":{"name":"safe-suspend signed dispatcher must be blocked"},"p_version":1,"p_reason":"Local safe suspension fixture"}'
SELECT secret AS suspend_gateway_secret
FROM private.h3_admin_rpc_gateway_keys
WHERE key_id = :'suspend_gateway_key_id'
  AND project_ref = :'suspend_gateway_project_ref'
\gset
SELECT pg_catalog.floor(pg_catalog.date_part('epoch', clock_timestamp()))::BIGINT::TEXT AS suspend_gateway_issued_at
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-v1', :'suspend_gateway_project_ref', 'POST',
    'admin_signed_rpc', :'suspend_gateway_actor', :'suspend_gateway_issued_at',
    :'suspend_gateway_nonce', :'suspend_gateway_key_id'),
  :'suspend_gateway_secret'
) AS suspend_gateway_signature
\gset
SELECT private.h3_admin_rpc_gateway_hmac(
  pg_catalog.concat_ws(E'\n', 'studiamatch-admin-rpc-payload-v1', :'suspend_gateway_project_ref',
    'POST', 'admin_signed_rpc', :'suspend_gateway_rpc', :'suspend_gateway_actor',
    :'suspend_gateway_issued_at', :'suspend_gateway_nonce', :'suspend_gateway_key_id',
    :'suspend_gateway_payload'),
  :'suspend_gateway_secret'
) AS suspend_gateway_payload_signature
\gset
CREATE TEMP TABLE h3_suspend_signed_dispatch_proof AS
SELECT :'suspend_gateway_rpc'::TEXT AS rpc_name,
       :'suspend_gateway_payload'::JSONB AS payload,
       :'suspend_gateway_payload'::TEXT AS signed_payload;
GRANT SELECT ON h3_suspend_signed_dispatch_proof TO authenticated;

\ir ../../db/rollback/h3req1_safe_suspend.sql
\ir ../../db/rollback/h3req1_safe_suspend.sql

DO $$
DECLARE
  previous RECORD;
BEGIN
  SELECT * INTO previous FROM h3_suspend_fingerprints;
  IF previous.state_digest IS DISTINCT FROM
       (SELECT md5(string_agg(row_to_json(es)::text, ',' ORDER BY es.course_id)) FROM public.course_editorial_state es)
     OR previous.audit_digest IS DISTINCT FROM
       (SELECT md5(string_agg(row_to_json(a)::text, ',' ORDER BY a.id)) FROM public.course_editorial_audit a)
     OR previous.invitation_count <> (SELECT count(*) FROM public.admin_invitations)
     OR previous.visible_count <> (SELECT count(*) FROM public.courses_public_effective)
     OR previous.cohort_present IS DISTINCT FROM (to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL) THEN
    RAISE EXCEPTION 'Safe suspension changed data, evidence, audit or cohort';
  END IF;
  IF EXISTS (SELECT 1 FROM h3_suspend_grants g WHERE has_function_privilege(g.role_name, g.oid, 'EXECUTE')) THEN
    RAISE EXCEPTION 'Safe suspension left an initiating mutation or signed dispatcher executable';
  END IF;
  IF EXISTS (SELECT 1 FROM public.courses_public_effective
             WHERE id='20000000-0000-0000-0000-000000000001') THEN
    RAISE EXCEPTION 'Rollback exposed a course with current unavailable evidence';
  END IF;
  IF NOT has_function_privilege('service_role', 'public.admin_invitation_complete(uuid,uuid)', 'EXECUTE') THEN
    RAISE EXCEPTION 'In-flight invitation completion was disabled';
  END IF;
  IF NOT has_function_privilege('service_role','public.admin_invitation_fail(uuid,uuid,text)','EXECUTE')
     OR NOT has_function_privilege('service_role','public.admin_invitation_mark_delivery_reconciliation(uuid,uuid,text,text)','EXECUTE') THEN
    RAISE EXCEPTION 'In-flight failure/reconciliation was disabled';
  END IF;
  BEGIN
    DELETE FROM public.course_editorial_audit
    WHERE actor_user_id='60000000-0000-0000-0000-000000000001';
    RAISE EXCEPTION 'Rollback disabled append-only audit enforcement';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM NOT ILIKE '%append-only%' THEN RAISE; END IF;
  END;
END;
$$;

-- Exercise the actual authenticated PostgREST signed-dispatch path after SQL
-- suspension using a valid local proof. Pre-request admits the intended wrapper,
-- but the wrapper ACL must reject it before its SECURITY DEFINER body can run.
SELECT set_config('request.path', '/rpc/admin_signed_rpc', false);
SELECT set_config('request.method', 'POST', false);
SELECT set_config('request.jwt.claim.sub', :'suspend_gateway_actor', false);
SELECT set_config('request.jwt.claim.role', 'authenticated', false);
SELECT set_config('request.jwt.claim.aal', 'aal2', false);
SELECT set_config('request.jwt.claims', pg_catalog.jsonb_build_object(
  'sub', :'suspend_gateway_actor', 'role', 'authenticated', 'aal', 'aal2')::TEXT, false);
SELECT set_config('request.headers', pg_catalog.jsonb_build_object(
  'x-studiamatch-admin-rpc-key-id', :'suspend_gateway_key_id',
  'x-studiamatch-admin-rpc-actor', :'suspend_gateway_actor',
  'x-studiamatch-admin-rpc-issued-at', :'suspend_gateway_issued_at',
  'x-studiamatch-admin-rpc-nonce', :'suspend_gateway_nonce',
  'x-studiamatch-admin-rpc-signature', :'suspend_gateway_signature',
  'x-studiamatch-admin-rpc-payload-signature', :'suspend_gateway_payload_signature'
)::TEXT, false);
SET ROLE authenticated;
SELECT public.h3_admin_rpc_signed_gateway_pre_request();
DO $$
DECLARE proof RECORD;
BEGIN
  IF has_function_privilege('authenticated', 'public.admin_signed_rpc(text,jsonb,text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'Safe suspension left authenticated EXECUTE on the signed dispatcher';
  END IF;
  SELECT * INTO proof FROM h3_suspend_signed_dispatch_proof;
  BEGIN
    PERFORM public.admin_signed_rpc(proof.rpc_name, proof.payload, proof.signed_payload);
    RAISE EXCEPTION 'Valid signed mutation crossed the safe-suspend dispatcher';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END;
$$;
RESET ROLE;
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM private.h3_admin_rpc_gateway_nonces
             WHERE nonce = '70000000-0000-4000-8000-000000000001') THEN
    RAISE EXCEPTION 'Suspended signed dispatcher consumed the mutation proof nonce';
  END IF;
END;
$$;

SET ROLE service_role;
DO $$
DECLARE fixture RECORD; result RECORD;
BEGIN
  FOR fixture IN SELECT * FROM h3_suspend_inflight LOOP
    -- A new initiating RPC must actually be denied after suspension.
    BEGIN
      PERFORM public.admin_invitation_reserve(fixture.email,'user',
        '70000000-0000-0000-0000-000000000001',fixture.user_id,false,'blocked-' || fixture.user_id::text,'{}'::jsonb,NULL);
      RAISE EXCEPTION 'Suspended reservation remained callable';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
    IF fixture.operation='complete' THEN
      SELECT * INTO result FROM public.admin_invitation_complete(fixture.invitation_id,fixture.user_id);
    ELSIF fixture.operation='fail' THEN
      SELECT * INTO result FROM public.admin_invitation_fail(fixture.invitation_id,fixture.user_id,'auth_invite_failed');
    ELSE
      SELECT * INTO result FROM public.admin_invitation_mark_delivery_reconciliation(
        fixture.invitation_id,fixture.user_id,'unknown','auth_delivery_unknown');
    END IF;
    IF result.success IS DISTINCT FROM true THEN RAISE EXCEPTION 'In-flight % failed: %',fixture.operation,result.error_code; END IF;
  END LOOP;
END;
$$;
RESET ROLE;
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM h3_suspend_inflight f JOIN public.admin_invitations i ON i.id=f.invitation_id
    WHERE (f.operation='complete' AND (i.metadata->>'delivery_state' IS DISTINCT FROM 'completed' OR i.admin_member_user_id IS DISTINCT FROM f.user_id
              OR i.metadata->>'delivery_method' IS DISTINCT FROM 'recovery'))
       OR (f.operation='fail' AND (i.status IS DISTINCT FROM 'send_failed' OR i.failure_code IS DISTINCT FROM 'auth_invite_failed'))
       OR (f.operation='reconcile' AND (i.metadata->>'delivery_state' IS DISTINCT FROM 'reconciliation_required' OR i.metadata->>'reconciliation_required' IS DISTINCT FROM 'true'))
  ) THEN RAISE EXCEPTION 'In-flight finalizer did not persist the expected state'; END IF;
  IF (SELECT count(*) FROM public.admin_membership_audit a JOIN h3_suspend_inflight f ON a.invitation_id=f.invitation_id
      WHERE a.action IN ('invite','send_failed','delivery_unknown')) <> 3 THEN
    RAISE EXCEPTION 'In-flight finalizers did not preserve traceable audit';
  END IF;
END;
$$;

-- A separate psql connection proves the snapshot survives process/session state.
-- Introduce a local ACL drift and require the real recovery file to fail closed;
-- then restore only that fixture grant and perform the approved-snapshot resume.
\connect
GRANT EXECUTE ON FUNCTION public.admin_signed_rpc(TEXT, JSONB, TEXT) TO anon;
\set ON_ERROR_STOP off
\ir ../../db/rollback/h3req1_safe_resume.sql
\if :ERROR
  SELECT :'SQLSTATE' = 'H3D01' AS h3_resume_acl_drift_rejected
  \gset
  \if :h3_resume_acl_drift_rejected
    \echo 'PASS: safe resume rejected ACL drift and kept the transaction fail-closed'
  \else
    \echo 'FAIL: safe resume failed for an unexpected SQLSTATE'
    \quit 1
  \endif
\else
  \echo 'FAIL: safe resume accepted ACL drift'
  \quit 1
\endif
\set ON_ERROR_STOP on
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM private.h3req1_safe_suspend_acl_snapshots
    WHERE state = 'suspended'
  ) OR EXISTS (
    SELECT 1 FROM private.h3req1_safe_suspend_acl_snapshots
    WHERE state = 'resumed'
  ) THEN
    RAISE EXCEPTION 'Rejected safe-resume attempt changed persistent snapshot state';
  END IF;
END;
$$;
REVOKE EXECUTE ON FUNCTION public.admin_signed_rpc(TEXT, JSONB, TEXT) FROM anon;

\ir ../../db/rollback/h3req1_safe_resume.sql
DO $$
DECLARE
  resumed private.h3req1_safe_suspend_acl_snapshots%ROWTYPE;
BEGIN
  PERFORM pg_catalog.set_config('search_path', 'pg_catalog, public', TRUE);
  SELECT * INTO resumed
  FROM private.h3req1_safe_suspend_acl_snapshots
  WHERE state = 'resumed'
  ORDER BY resumed_at DESC
  LIMIT 1;
  IF NOT FOUND OR EXISTS (
    SELECT 1 FROM private.h3req1_safe_suspend_acl_snapshots WHERE state = 'suspended'
  ) THEN
    RAISE EXCEPTION 'Persistent safe-resume did not finish from a new session';
  END IF;
  IF resumed.database_oid <> (SELECT oid FROM pg_catalog.pg_database
       WHERE datname = pg_catalog.current_database())
     OR resumed.database_name <> pg_catalog.current_database()
     OR resumed.captured_by <> current_user
     OR resumed.resumed_fingerprint IS DISTINCT FROM resumed.original_fingerprint
      OR resumed.snapshot_fingerprint <> pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
        pg_catalog.concat_ws('|', resumed.snapshot_id::TEXT, resumed.database_oid::TEXT,
          resumed.database_name::TEXT, resumed.captured_by::TEXT,
          pg_catalog.to_char(resumed.captured_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US'),
          resumed.grant_snapshot::TEXT, resumed.original_fingerprint,
          resumed.suspended_fingerprint), 'UTF8')), 'hex') THEN
    RAISE EXCEPTION 'Persistent safe-resume identity, ACL fingerprint or snapshot integrity changed';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM pg_catalog.jsonb_array_elements(resumed.grant_snapshot) saved(value)
    JOIN pg_catalog.pg_proc p ON p.oid = (saved.value ->> 'function_oid')::OID
    WHERE p.oid::REGPROCEDURE::TEXT <> saved.value ->> 'signature'
       OR p.proowner::TEXT <> saved.value ->> 'owner_oid'
       OR pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
       OR pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
          IS DISTINCT FROM (saved.value ->> 'authenticated_execute')::BOOLEAN
       OR pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE')
          IS DISTINCT FROM (saved.value ->> 'service_role_execute')::BOOLEAN
  ) THEN
    RAISE EXCEPTION 'Persistent resume did not restore the allowlisted effective ACLs';
  END IF;
END;
$$;
CREATE TEMP TABLE h3_resume_snapshot_before AS
SELECT snapshot_id, state, snapshot_fingerprint, resumed_fingerprint, resumed_at, grant_snapshot
FROM private.h3req1_safe_suspend_acl_snapshots
WHERE state = 'resumed';
\ir ../../db/rollback/h3req1_safe_resume.sql
DO $$
BEGIN
  IF (SELECT count(*) FROM h3_resume_snapshot_before) <> 1
     OR EXISTS (
       SELECT 1 FROM h3_resume_snapshot_before before_resume
       FULL JOIN private.h3req1_safe_suspend_acl_snapshots after_resume
         ON after_resume.snapshot_id = before_resume.snapshot_id
       WHERE before_resume.snapshot_id IS NULL
          OR after_resume.snapshot_id IS NULL
          OR ROW(after_resume.state, after_resume.snapshot_fingerprint,
                 after_resume.resumed_fingerprint, after_resume.resumed_at,
                 after_resume.grant_snapshot)
             IS DISTINCT FROM
             ROW(before_resume.state, before_resume.snapshot_fingerprint,
                 before_resume.resumed_fingerprint, before_resume.resumed_at,
                 before_resume.grant_snapshot)
     ) THEN
    RAISE EXCEPTION 'Repeated safe-resume changed the completed persistent snapshot';
  END IF;
END;
$$;
SELECT 'h3_safe_suspend_harness_ok' AS result;
