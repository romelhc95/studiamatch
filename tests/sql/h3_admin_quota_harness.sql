\set ON_ERROR_STOP on
-- Disposable PG17 only; baseline H3 already installed, no operational data.
\ir ../../db/migrations/20261002_h3_admin_quota_expand.sql
CREATE TEMP TABLE h3_quota_legacy_inflight (invitation_id UUID,user_id UUID);
INSERT INTO auth.users(id,email) VALUES
  ('73000000-0000-0000-0000-000000000001','quota-compat-admin@local.test'),
  ('73000000-0000-0000-0000-000000000002','quota-compat-user@local.test') ON CONFLICT DO NOTHING;
INSERT INTO public.admin_members(user_id,role,is_active,account_status)
VALUES('73000000-0000-0000-0000-000000000001','admin',true,'ready') ON CONFLICT DO NOTHING;
GRANT INSERT,SELECT ON h3_quota_legacy_inflight TO service_role;
SET ROLE service_role;
DO $$ DECLARE result RECORD; BEGIN
  IF position('H3_QUOTA_WRAPPER_V1' IN (SELECT p.prosrc FROM pg_proc p WHERE p.oid='public.admin_invitation_reserve(text,text,uuid,uuid,boolean,text,jsonb,timestamptz)'::regprocedure))=0 THEN
    SELECT * INTO result FROM public.admin_invitation_reserve('quota-compat-user@local.test','user',
      '73000000-0000-0000-0000-000000000001','73000000-0000-0000-0000-000000000002',false,'quota-compat-no-hmac','{}',NULL);
    IF result.success IS DISTINCT FROM true THEN RAISE EXCEPTION 'EXPAND broke legacy reservation'; END IF;
    INSERT INTO h3_quota_legacy_inflight VALUES(result.invitation_id,'73000000-0000-0000-0000-000000000002');
  END IF;
END; $$;
RESET ROLE;
\ir ../../db/migrations/20261002_h3_admin_quotas.sql
\ir ../../db/migrations/20261002_h3_admin_quota_expand.sql
\ir ../../db/migrations/20261002_h3_admin_quotas.sql
\ir ../../db/migrations/20261025_h3_admin_members_onboarding_forbidden_status.sql

-- Exercise the forward migration against the quota wrapper's copied original.
DO $$
DECLARE
  function_definition TEXT;
  old_guard CONSTANT TEXT := 'IF p_first < 1 OR p_first > 100 THEN';
  new_guard CONSTANT TEXT := 'IF p_first IS NULL OR p_first < 1 OR p_first > 100 THEN';
BEGIN
  SELECT pg_catalog.pg_get_functiondef(
    'private.h3_quota_base_admin_get_course_queue_filtered(integer,text,text,text,text)'::REGPROCEDURE
  ) INTO function_definition;
  IF pg_catalog.strpos(function_definition, new_guard) = 0 THEN
    RAISE EXCEPTION 'quota fixture did not copy the queue page-size guard';
  END IF;
  function_definition := pg_catalog.replace(function_definition, new_guard, old_guard);
  IF pg_catalog.strpos(function_definition, old_guard) = 0
     OR pg_catalog.strpos(function_definition, new_guard) > 0 THEN
    RAISE EXCEPTION 'could not stage the legacy quota-function fixture';
  END IF;
  EXECUTE function_definition;
END;
$$;
\ir ../../db/migrations/20261004_h3_admin_queue_first_null_guard.sql
DO $$
DECLARE
  private_source TEXT;
  wrapper_source TEXT;
BEGIN
  SELECT p.prosrc INTO private_source
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = 'private.h3_quota_base_admin_get_course_queue_filtered(integer,text,text,text,text)'::REGPROCEDURE;
  SELECT p.prosrc INTO wrapper_source
  FROM pg_catalog.pg_proc AS p
  WHERE p.oid = 'public.admin_get_course_queue_filtered(integer,text,text,text,text)'::REGPROCEDURE;
  IF pg_catalog.strpos(private_source, 'IF p_first IS NULL OR p_first < 1 OR p_first > 100 THEN') = 0
     OR pg_catalog.strpos(wrapper_source, 'H3_QUOTA_WRAPPER_V1') = 0 THEN
    RAISE EXCEPTION 'forward migration failed to guard the quota snapshot while preserving its wrapper';
  END IF;
END;
$$;

SET ROLE service_role;
DO $$ DECLARE fixture RECORD; result RECORD; BEGIN
  FOR fixture IN SELECT * FROM h3_quota_legacy_inflight LOOP
    SELECT * INTO result FROM public.admin_invitation_complete(fixture.invitation_id,fixture.user_id);
    IF result.success IS DISTINCT FROM true THEN RAISE EXCEPTION 'Activation broke legacy in-flight completion'; END IF;
  END LOOP;
END; $$;
RESET ROLE;
INSERT INTO auth.users(id,email) VALUES('71000000-0000-0000-0000-000000000001','quota-admin@local.test') ON CONFLICT DO NOTHING;
INSERT INTO auth.users(id,email) VALUES('71000000-0000-0000-0000-000000000002','quota-onboarding-user@local.test') ON CONFLICT DO NOTHING;
INSERT INTO public.admin_members(user_id,role,is_active,account_status)
VALUES('71000000-0000-0000-0000-000000000001','admin',true,'ready') ON CONFLICT DO NOTHING;
INSERT INTO public.admin_members(user_id,role,is_active,account_status)
VALUES('71000000-0000-0000-0000-000000000002','user',true,'ready') ON CONFLICT DO NOTHING;
SELECT set_config('request.jwt.claim.sub','71000000-0000-0000-0000-000000000001',false);
SELECT set_config('request.jwt.claim.aal','aal2',false);
SELECT set_config('response.status','200',false);
SET ROLE authenticated;
DO $$
DECLARE i INTEGER; details TEXT; message TEXT; queue_result RECORD;
BEGIN
  SELECT * INTO queue_result
  FROM public.admin_get_course_queue_filtered(NULL, NULL, NULL, NULL, NULL);
  IF queue_result.error IS DISTINCT FROM 'First must be between 1 and 100'
     OR queue_result.courses IS NOT NULL OR queue_result.page_info IS NOT NULL THEN
    RAISE EXCEPTION 'quota-wrapped queue RPC admitted a NULL page size';
  END IF;
  FOR i IN 1..119 LOOP PERFORM public.admin_current_user_role(); END LOOP;
  BEGIN
    PERFORM public.admin_current_user_role();
    RAISE EXCEPTION 'Direct authenticated RPC bypassed read quota';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS details=PG_EXCEPTION_DETAIL,message=MESSAGE_TEXT;
    IF (details::jsonb->>'status')::int<>429 OR message::jsonb->>'code'<>'quota_rate_limited'
       OR (details::jsonb->'headers'->>'Retry-After')::int NOT BETWEEN 1 AND 60 THEN
      RAISE EXCEPTION 'Quota did not propagate 429/Retry-After';
    END IF;
  END;
  IF has_table_privilege('authenticated','private.h3_admin_quota_events','INSERT')
     OR has_function_privilege('authenticated','private.h3_take_admin_quota(text[],integer[],integer[])','EXECUTE') THEN
    RAISE EXCEPTION 'Quota internal writer exposed';
  END IF;
END;
$$;
RESET ROLE;
DO $$
BEGIN
  IF EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname='private' AND p.proname LIKE 'h3_quota_base_%'
              AND (has_function_privilege('authenticated',p.oid,'EXECUTE')
                   OR has_function_privilege('service_role',p.oid,'EXECUTE')
                   OR has_function_privilege('anon',p.oid,'EXECUTE'))) THEN
    RAISE EXCEPTION 'Private originals allow direct quota bypass';
  END IF;
  IF (SELECT cardinality(events) FROM private.h3_admin_quota_events
      WHERE scope='rpc-read:71000000-0000-0000-0000-000000000001')<>120 THEN
    RAISE EXCEPTION 'Read counter did not persist admitted calls';
  END IF;
END;
$$;
UPDATE private.h3_admin_quota_events SET events=ARRAY[clock_timestamp()-interval '61 seconds']
WHERE scope='rpc-read:71000000-0000-0000-0000-000000000001';
SET ROLE authenticated;
SELECT public.admin_current_user_role();
RESET ROLE;
SELECT set_config('request.jwt.claim.sub','',false);

SELECT set_config('request.jwt.claim.sub','71000000-0000-0000-0000-000000000001',false);
SELECT set_config('request.jwt.claim.aal','aal1',false);
SET ROLE authenticated;
-- MFA rejection must leave its admission committed, not rethrow the original.
SELECT * FROM public.admin_update_course('20000000-0000-0000-0000-000000000001','{}',0,'quota rejected attempt');
RESET ROLE;
DO $$
BEGIN
  IF (SELECT cardinality(events) FROM private.h3_admin_quota_events
      WHERE scope='rpc-write:71000000-0000-0000-0000-000000000001')<>1 THEN
    RAISE EXCEPTION 'RPC rejection rolled back its admission';
  END IF;
  IF EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname='public' AND p.proname IN ('admin_get_course_queue','admin_count_course_queue','admin_list_members','admin_create_member')
              AND position('H3_QUOTA_WRAPPER_V1' IN p.prosrc)=0) THEN
    RAISE EXCEPTION 'Legacy RPC bypasses quota wrapper';
  END IF;
END;
$$;
SELECT set_config('request.jwt.claim.sub','71000000-0000-0000-0000-000000000001',false);
SELECT set_config('request.jwt.claim.aal','aal2',false);
SELECT set_config('response.status','200',false);
SET ROLE authenticated;
DO $$
DECLARE allowed_rows INTEGER;
BEGIN
  SELECT count(*) INTO allowed_rows
  FROM public.admin_list_members_onboarding()
  WHERE user_id IN (
    '71000000-0000-0000-0000-000000000001'::UUID,
    '71000000-0000-0000-0000-000000000002'::UUID
  );
  IF current_setting('response.status', true) = '403' OR allowed_rows <> 2 THEN
    RAISE EXCEPTION 'admin onboarding reader lost its authorized rows';
  END IF;
END;
$$;
RESET ROLE;
SELECT set_config('request.jwt.claim.sub','71000000-0000-0000-0000-000000000002',false);
SELECT set_config('response.status','200',false);
SET ROLE authenticated;
DO $$
DECLARE denied RECORD;
BEGIN
  SELECT * INTO denied FROM public.admin_list_members_onboarding();
  IF current_setting('response.status', true) IS DISTINCT FROM '403'
     OR denied.user_id IS NOT NULL OR denied.email IS NOT NULL
     OR denied.role IS NOT NULL THEN
    RAISE EXCEPTION 'User role unexpectedly read onboarding members';
  END IF;
END;
$$;
RESET ROLE;
SELECT set_config('request.jwt.claim.sub','',false);
SELECT set_config('request.jwt.claim.aal','aal2',false);

SET ROLE service_role;
DO $$
DECLARE result RECORD; i INTEGER; message TEXT;
BEGIN
  FOR i IN 1..3 LOOP
    SELECT * INTO result FROM public.admin_invitation_reserve(
      'quota-recipient-'||i||'@local.test','user','71000000-0000-0000-0000-000000000001',NULL,false,
      'quota-request-'||i,jsonb_build_object('quota_recipient',repeat(i::text,64)),NULL);
    IF result.success IS DISTINCT FROM true THEN RAISE EXCEPTION 'Within-quota reservation failed: %',result.error_code; END IF;
  END LOOP;
  BEGIN
    PERFORM public.admin_invitation_reserve('quota-recipient-4@local.test','user',
      '71000000-0000-0000-0000-000000000001',NULL,false,'quota-request-4',
      jsonb_build_object('quota_recipient',repeat('4',64)),NULL);
    RAISE EXCEPTION 'Direct service reserve bypassed burst quota';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS message=MESSAGE_TEXT;
    IF message::jsonb->>'code'<>'quota_rate_limited' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.admin_invitation_reserve('quota-missing@local.test','user',
      '71000000-0000-0000-0000-000000000001',NULL,false,'quota-missing','{}'::jsonb,NULL);
    RAISE EXCEPTION 'Missing recipient HMAC admitted a reservation';
  EXCEPTION WHEN SQLSTATE 'PGRST' THEN
    GET STACKED DIAGNOSTICS message=MESSAGE_TEXT;
    IF message::jsonb->>'code'<>'quota_unavailable' THEN RAISE; END IF;
  END;
END;
$$;
RESET ROLE;
DO $$
BEGIN
  IF EXISTS(SELECT 1 FROM public.admin_invitations WHERE email IN ('quota-recipient-4@local.test','quota-missing@local.test')) THEN
    RAISE EXCEPTION 'Rejected quota request produced invitation state';
  END IF;
END;
$$;
SELECT 'h3_admin_quota_harness_ok' AS result;
