-- Approved LOCAL design. Remote DDL/deploy remains separately gated.
-- Additive rolling-window quotas; originals retained privately, auth/RLS unchanged.
BEGIN;
-- EXPAND must already be installed; deploy compatible reserve-before-Auth Edge
-- with HMAC before activating these wrappers. Do not blanket-sync both phases.
DO $$ BEGIN
  IF to_regclass('private.h3_admin_quota_events') IS NULL
     OR to_regprocedure('public.admin_invitation_request_admit(uuid)') IS NULL THEN
    RAISE EXCEPTION 'Quota EXPAND prerequisite missing';
  END IF;
END; $$;

-- Keep public OIDs/signatures/defaults/grants. Private copies cannot be called by
-- client roles; wrapper still passes original arguments and Supabase identity.
DO $$
DECLARE f RECORD; base_name TEXT; call_args TEXT; quota_body TEXT; result_body TEXT; definition TEXT; error_body TEXT;
  names TEXT[] := ARRAY[
    'admin_current_user_role','admin_get_onboarding_status','admin_get_course_audit','admin_get_course_editorial',
    'admin_get_course_queue_facets','admin_get_course_queue_filtered','admin_count_course_queue_filtered',
    'admin_list_members_onboarding','admin_accept_current_invitation','admin_complete_password_setup',
    'admin_update_course','admin_set_course_availability','admin_publish_course','admin_unpublish_course',
    'admin_archive_course','admin_update_quality_status','admin_update_member','admin_invitation_reserve',
    'admin_get_course_queue','admin_count_course_queue','admin_list_members','admin_create_member'];
BEGIN
  FOREACH base_name IN ARRAY names LOOP
    IF NOT EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                  WHERE n.nspname='public' AND p.proname=base_name) THEN
      RAISE EXCEPTION 'Quota baseline missing %',base_name;
    END IF;
  END LOOP;
  FOR f IN SELECT p.*,pg_get_function_arguments(p.oid) args,pg_get_function_result(p.oid) result,
                  pg_get_function_identity_arguments(p.oid) identity_args
           FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
           WHERE n.nspname='public' AND p.proname=ANY(names) LOOP
    IF position('H3_QUOTA_WRAPPER_V1' IN f.prosrc)>0 THEN CONTINUE; END IF;
    base_name := 'h3_quota_base_' || f.proname;
    IF EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
              WHERE n.nspname='private' AND p.proname=base_name AND p.proargtypes=f.proargtypes) THEN
      RAISE EXCEPTION 'Quota baseline drift for %, do not overwrite hardened wrappers',f.proname;
    END IF;
    definition := replace(pg_get_functiondef(f.oid),'FUNCTION public.' || f.proname || '(',
                         'FUNCTION private.' || base_name || '(');
    EXECUTE definition;
    EXECUTE format('REVOKE ALL ON FUNCTION private.%I(%s) FROM PUBLIC,anon,authenticated,service_role',base_name,f.identity_args);
    SELECT string_agg('$' || position::text,',' ORDER BY position) INTO call_args
    FROM generate_series(1,f.pronargs) position;
    call_args := COALESCE(call_args,'');
    IF f.proname='admin_invitation_reserve' THEN
      quota_body := $body$
        IF NOT EXISTS(SELECT 1 FROM public.admin_members WHERE user_id=p_actor_user_id
                      AND role='admin' AND is_active AND account_status='ready') THEN
          RETURN QUERY SELECT * FROM private.h3_quota_base_admin_invitation_reserve($1,$2,$3,$4,$5,$6,$7,$8); RETURN;
        END IF;
        IF COALESCE(p_metadata->>'quota_recipient','') !~ '^[a-f0-9]{64}$' THEN
          RAISE SQLSTATE 'PGRST' USING MESSAGE='{"code":"quota_unavailable","message":"Quota unavailable","details":null,"hint":null}',
              DETAIL='{"status":503,"headers":{"Retry-After":"30"}}';
        END IF;
        retry := private.h3_take_admin_quota(
          ARRAY['invite-burst:'||p_actor_user_id,'invite-hour:'||p_actor_user_id,
                'invite-recipient:'||(p_metadata->>'quota_recipient'),'invite-environment'],
          ARRAY[3,10,3,50],ARRAY[60,3600,86400,86400]);
      $body$;
    ELSE
      quota_body := format($body$
        IF auth.uid() IS NOT NULL THEN
          retry := private.h3_take_admin_quota(ARRAY[%L||auth.uid()::text],ARRAY[%s],ARRAY[60]);
        END IF;
      $body$, CASE WHEN f.proname ~ '^admin_(current|get|count|list)' THEN 'rpc-read:' ELSE 'rpc-write:' END,
        CASE WHEN f.proname ~ '^admin_(current|get|count|list)' THEN 120 ELSE 30 END);
    END IF;
    result_body := CASE WHEN f.proretset THEN format('RETURN QUERY SELECT * FROM private.%I(%s);',base_name,call_args)
                       ELSE format('RETURN private.%I(%s);',base_name,call_args) END;
    -- Preserve admission OUTSIDE the original's exception subtransaction. Return
    -- a failed HTTP status without rethrowing and rolling back its quota. Inputs
    -- rejected by PostgREST before invocation are outside this SQL perimeter.
    IF f.proretset THEN
      SELECT 'RETURN QUERY SELECT ' || string_agg(
        CASE WHEN f.proargnames[position] IN ('error','error_code') THEN 'failure_code::' || format_type(f.proallargtypes[position],NULL)
             WHEN f.proargnames[position]='success' AND f.proallargtypes[position]='boolean'::regtype THEN 'false'
             ELSE 'NULL::' || format_type(f.proallargtypes[position],NULL) END,',' ORDER BY position) || '; RETURN;'
      INTO error_body FROM generate_subscripts(f.proallargtypes,1) position WHERE f.proargmodes[position] IN ('o','t');
      IF error_body IS NULL THEN error_body := 'RETURN;'; END IF;
    ELSE error_body := 'RETURN NULL;'; END IF;
    EXECUTE format('CREATE OR REPLACE FUNCTION public.%I(%s) RETURNS %s LANGUAGE plpgsql VOLATILE SECURITY DEFINER
      SET search_path=pg_catalog,pg_temp AS $wrapper$ /* H3_QUOTA_WRAPPER_V1 */
      DECLARE retry INTEGER := 0; failure_code TEXT; failure_status TEXT; BEGIN %s IF retry>0 THEN PERFORM private.h3_raise_admin_quota(retry); END IF;
      BEGIN %s EXCEPTION WHEN OTHERS THEN
        IF SQLSTATE=''PGRST'' THEN RAISE; END IF;
        failure_code := CASE WHEN SQLERRM ~* ''mfa|aal2|insufficient_aal'' THEN ''mfa_required'' ELSE ''rpc_failed'' END;
        failure_status := CASE WHEN failure_code=''mfa_required'' THEN ''403''
                               WHEN SQLSTATE=''42501'' THEN ''403''
                               WHEN SQLSTATE LIKE ''22%%'' OR SQLSTATE LIKE ''23%%'' THEN ''400'' ELSE ''503'' END;
        PERFORM set_config(''response.status'',failure_status,true);
        %s
      END; END; $wrapper$',f.proname,f.args,f.result,quota_body,result_body,error_body);
  END LOOP;
END;
$$;
COMMIT;
