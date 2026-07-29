-- F9.7 terminal security hold for public leads and email_log access.
-- Forward-only local candidate. No remote application is authorized by this file.

SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path = '';

DO $security_hold_initial_precondition$
DECLARE
    expected_count integer;
BEGIN
    SELECT pg_catalog.count(*)::integer
    INTO expected_count
    FROM (VALUES
        ('20260724_fase06_g1b_reconciliation', 'sha256:d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df'),
        ('20260724_fase06_hito1_editorial_contract', 'sha256:b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a'),
        ('20260725_fase07_g1b_closure', 'sha256:9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120'),
        ('20260725_fase08_hito1_functional_closure', 'sha256:7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527'),
        ('20260727_fase09_7_public_access_closure', 'sha256:040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b'),
        ('20260728_fase09_7_notify_new_lead_retirement_v3', 'sha256:f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188')
    ) AS expected(name, statements)
    JOIN public.supabase_migrations AS ledger
      ON ledger.name = expected.name
     AND ledger.statements = expected.statements;

    IF expected_count <> 6
       OR EXISTS (
           SELECT 1
           FROM public.supabase_migrations AS ledger
           WHERE ledger.name = '20260729_fase09_7_leads_email_security_hold'
              OR ledger.name IN (
                  '20260726_fase09_5_rls_canary_reconciliation',
                  '20260726_fase09_5_policy_inventory_reconciliation',
                  '20260727_fase09_7_notify_new_lead_retirement'
              )
              OR (
                  ledger.name LIKE ANY (ARRAY[
                      '20260727_fase09_7_%',
                      '20260728_fase09_7_%',
                      '20260729_fase09_7_%'
                  ])
                  AND ledger.name NOT IN (
                      '20260727_fase09_7_public_access_closure',
                      '20260728_fase09_7_notify_new_lead_retirement_v3'
                  )
              )
       ) THEN
        RAISE EXCEPTION 'F9.7 security hold requires exact v3 ledger boundary 6'
            USING ERRCODE = '55000';
    END IF;

END;
$security_hold_initial_precondition$;

LOCK TABLE public.supabase_migrations IN SHARE ROW EXCLUSIVE MODE;
LOCK TABLE public.leads IN ACCESS EXCLUSIVE MODE;
LOCK TABLE public.email_log IN ACCESS EXCLUSIVE MODE;

DO $security_hold_locked_precondition$
DECLARE
    expected_count integer;
    service_role_oid oid;
BEGIN
    SELECT role.oid INTO service_role_oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'service_role';
    IF service_role_oid IS NULL THEN
        RAISE EXCEPTION 'F9.7 security hold requires service_role'
            USING ERRCODE = '55000';
    END IF;

    SELECT pg_catalog.count(*)::integer
    INTO expected_count
    FROM (VALUES
        ('20260724_fase06_g1b_reconciliation', 'sha256:d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df'),
        ('20260724_fase06_hito1_editorial_contract', 'sha256:b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a'),
        ('20260725_fase07_g1b_closure', 'sha256:9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120'),
        ('20260725_fase08_hito1_functional_closure', 'sha256:7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527'),
        ('20260727_fase09_7_public_access_closure', 'sha256:040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b'),
        ('20260728_fase09_7_notify_new_lead_retirement_v3', 'sha256:f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188')
    ) AS expected(name, statements)
    JOIN public.supabase_migrations AS ledger
      ON ledger.name = expected.name
     AND ledger.statements = expected.statements;

    IF expected_count <> 6
       OR EXISTS (
           SELECT 1
           FROM public.supabase_migrations AS ledger
           WHERE ledger.name = '20260729_fase09_7_leads_email_security_hold'
              OR ledger.name IN (
                  '20260726_fase09_5_rls_canary_reconciliation',
                  '20260726_fase09_5_policy_inventory_reconciliation',
                  '20260727_fase09_7_notify_new_lead_retirement'
              )
              OR (
                  ledger.name LIKE ANY (ARRAY[
                      '20260727_fase09_7_%',
                      '20260728_fase09_7_%',
                      '20260729_fase09_7_%'
                  ])
                  AND ledger.name NOT IN (
                      '20260727_fase09_7_public_access_closure',
                      '20260728_fase09_7_notify_new_lead_retirement_v3'
                  )
              )
       ) THEN
        RAISE EXCEPTION 'F9.7 security hold locked ledger boundary drift'
            USING ERRCODE = '55000';
    END IF;

    IF NOT (
        SELECT pg_catalog.count(*) = 1
           AND pg_catalog.bool_and(
               owner.rolname = 'postgres'
               AND language_record.lanname = 'plpgsql'
               AND return_namespace.nspname = 'pg_catalog'
               AND return_type.typname = 'bool'
               AND procedure_record.prokind = 'f'
               AND NOT procedure_record.prosecdef
               AND procedure_record.provolatile = 's'
               AND NOT procedure_record.proisstrict
               AND NOT procedure_record.proleakproof
               AND procedure_record.proparallel = 'u'
               AND NOT procedure_record.proretset
               AND procedure_record.pronargs = 0
               AND procedure_record.pronargdefaults = 0
               AND procedure_record.proconfig IS NOT DISTINCT FROM
                   ARRAY['search_path=""']::text[]
               AND pg_catalog.octet_length(pg_catalog.replace(
                   procedure_record.prosrc, E'\r\n', E'\n'
               )) = 35054
               AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                   pg_catalog.replace(procedure_record.prosrc, E'\r\n', E'\n'),
                   'UTF8'
               )), 'hex') = '207ea3023a7485bbec6cf4e90a975d15907bcd771cf155d2f4d0bc97ff1b7d2a'
               AND pg_catalog.octet_length(pg_catalog.replace(
                   pg_catalog.pg_get_functiondef(procedure_record.oid), E'\r\n', E'\n'
               )) = 35218
               AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                   pg_catalog.replace(
                       pg_catalog.pg_get_functiondef(procedure_record.oid),
                       E'\r\n', E'\n'
                   ),
                   'UTF8'
               )), 'hex') = 'be9d1514c8f40eae3b9a351640c0c2a21f3308224de103a4b8e9f4c4193ae137'
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.aclexplode(COALESCE(
                       procedure_record.proacl,
                       pg_catalog.acldefault('f', procedure_record.proowner)
                   )) AS acl
               ) = 2
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.aclexplode(COALESCE(
                       procedure_record.proacl,
                       pg_catalog.acldefault('f', procedure_record.proowner)
                   )) AS acl
                   WHERE acl.privilege_type = 'EXECUTE'
                     AND NOT acl.is_grantable
                     AND acl.grantee = procedure_record.proowner
               ) = 1
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.aclexplode(COALESCE(
                       procedure_record.proacl,
                       pg_catalog.acldefault('f', procedure_record.proowner)
                   )) AS acl
                   WHERE acl.privilege_type = 'EXECUTE'
                     AND NOT acl.is_grantable
                     AND acl.grantee = (
                         SELECT role.oid
                         FROM pg_catalog.pg_roles AS role
                         WHERE role.rolname = 'service_role'
                     )
               ) = 1
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.pg_depend AS dependency
                   WHERE dependency.classid =
                         'pg_catalog.pg_proc'::pg_catalog.regclass
                     AND dependency.objid = procedure_record.oid
                     AND dependency.objsubid = 0
               ) = 2
           )
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        JOIN pg_catalog.pg_type AS return_type
          ON return_type.oid = procedure_record.prorettype
        JOIN pg_catalog.pg_namespace AS return_namespace
          ON return_namespace.oid = return_type.typnamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.proname = 'verify_fase09_7_public_access_closure'
    ) THEN
        RAISE EXCEPTION 'F9.7 security hold predecessor identity drift'
            USING ERRCODE = '55000';
    END IF;

    IF NOT (
        SELECT pg_catalog.count(*) = 1
           AND pg_catalog.bool_and(
               owner.rolname = 'postgres'
               AND language_record.lanname = 'sql'
               AND return_namespace.nspname = 'pg_catalog'
               AND return_type.typname = 'bool'
               AND procedure_record.prokind = 'f'
               AND NOT procedure_record.prosecdef
               AND procedure_record.provolatile = 's'
               AND NOT procedure_record.proisstrict
               AND NOT procedure_record.proleakproof
               AND procedure_record.proparallel = 'u'
               AND NOT procedure_record.proretset
               AND procedure_record.pronargs = 0
               AND procedure_record.pronargdefaults = 0
               AND procedure_record.proconfig IS NOT DISTINCT FROM
                   ARRAY['search_path=""']::text[]
               AND pg_catalog.octet_length(pg_catalog.replace(
                   procedure_record.prosrc, E'\r\n', E'\n'
               )) = 7059
               AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                   pg_catalog.replace(procedure_record.prosrc, E'\r\n', E'\n'),
                   'UTF8'
               )), 'hex') = '38172c8a98884d317567e4a9814f7b8c340dfd0df9f5d2b2f39ae89e8e34e618'
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.aclexplode(COALESCE(
                       procedure_record.proacl,
                       pg_catalog.acldefault('f', procedure_record.proowner)
                   )) AS acl
               ) = 2
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.aclexplode(COALESCE(
                       procedure_record.proacl,
                       pg_catalog.acldefault('f', procedure_record.proowner)
                   )) AS acl
                   WHERE acl.privilege_type = 'EXECUTE'
                     AND NOT acl.is_grantable
                     AND acl.grantee = procedure_record.proowner
               ) = 1
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.aclexplode(COALESCE(
                       procedure_record.proacl,
                       pg_catalog.acldefault('f', procedure_record.proowner)
                   )) AS acl
                   WHERE acl.privilege_type = 'EXECUTE'
                     AND NOT acl.is_grantable
                     AND acl.grantee = (
                         SELECT role.oid
                         FROM pg_catalog.pg_roles AS role
                         WHERE role.rolname = 'service_role'
                     )
               ) = 1
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.pg_depend AS dependency
                   WHERE dependency.classid =
                         'pg_catalog.pg_proc'::pg_catalog.regclass
                     AND dependency.objid = procedure_record.oid
                     AND dependency.objsubid = 0
               ) = 1
           )
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        JOIN pg_catalog.pg_type AS return_type
          ON return_type.oid = procedure_record.prorettype
        JOIN pg_catalog.pg_namespace AS return_namespace
          ON return_namespace.oid = return_type.typnamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.proname = 'verify_fase09_7_notify_new_lead_retirement'
    ) THEN
        RAISE EXCEPTION 'F9.7 security hold retirement verifier identity drift'
            USING ERRCODE = '55000';
    END IF;

    IF NOT (
        SELECT pg_catalog.count(*) = 1
           AND pg_catalog.bool_and(
               owner.rolname = 'postgres'
               AND language_record.lanname = 'plpgsql'
               AND return_namespace.nspname = 'pg_catalog'
               AND return_type.typname = 'jsonb'
               AND procedure_record.prokind = 'f'
               AND procedure_record.prosecdef
               AND procedure_record.pronargs = 1
               AND procedure_record.pronargdefaults = 0
               AND procedure_record.proconfig IS NOT DISTINCT FROM
                   ARRAY['search_path=""']::text[]
               AND NOT pg_catalog.has_function_privilege(
                   'anon', procedure_record.oid, 'EXECUTE'
               )
               AND NOT pg_catalog.has_function_privilege(
                   'authenticated', procedure_record.oid, 'EXECUTE'
               )
               AND NOT pg_catalog.has_function_privilege(
                   'authenticator', procedure_record.oid, 'EXECUTE'
               )
                AND pg_catalog.has_function_privilege(
                    'service_role', procedure_record.oid, 'EXECUTE'
                )
                AND (
                    SELECT pg_catalog.count(*)
                    FROM pg_catalog.aclexplode(COALESCE(
                        procedure_record.proacl,
                        pg_catalog.acldefault('f', procedure_record.proowner)
                    )) AS acl
                ) = 2
                AND (
                    SELECT pg_catalog.count(*)
                    FROM pg_catalog.aclexplode(COALESCE(
                        procedure_record.proacl,
                        pg_catalog.acldefault('f', procedure_record.proowner)
                    )) AS acl
                    WHERE acl.privilege_type = 'EXECUTE'
                      AND NOT acl.is_grantable
                      AND acl.grantee = procedure_record.proowner
                ) = 1
                AND (
                    SELECT pg_catalog.count(*)
                    FROM pg_catalog.aclexplode(COALESCE(
                        procedure_record.proacl,
                        pg_catalog.acldefault('f', procedure_record.proowner)
                    )) AS acl
                    WHERE acl.privilege_type = 'EXECUTE'
                      AND NOT acl.is_grantable
                      AND acl.grantee = service_role_oid
                ) = 1
            )
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        JOIN pg_catalog.pg_type AS return_type
          ON return_type.oid = procedure_record.prorettype
        JOIN pg_catalog.pg_namespace AS return_namespace
          ON return_namespace.oid = return_type.typnamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.oid =
              pg_catalog.to_regprocedure('public.exec_sql(text)')
    ) OR EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.proname = 'exec_sql'
          AND procedure_record.oid <>
              pg_catalog.to_regprocedure('public.exec_sql(text)')
    ) THEN
        RAISE EXCEPTION 'F9.7 security hold exec_sql control-plane drift'
            USING ERRCODE = '55000';
    END IF;

    IF public.verify_fase09_7_public_access_closure() IS NOT TRUE
       OR public.verify_fase09_7_notify_new_lead_retirement() IS NOT TRUE THEN
        RAISE EXCEPTION 'F9.7 security hold locked predecessor drift'
            USING ERRCODE = '55000';
    END IF;
END;
$security_hold_locked_precondition$;

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leads FORCE ROW LEVEL SECURITY;
ALTER TABLE public.email_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_log FORCE ROW LEVEL SECURITY;

REVOKE SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, MAINTAIN
ON TABLE public.leads FROM PUBLIC, anon, authenticated, authenticator, service_role;
REVOKE SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, MAINTAIN
ON TABLE public.email_log FROM PUBLIC, anon, authenticated, authenticator, service_role;

REVOKE SELECT (
    id, first_name, last_name, email, whatsapp, source_page, type, course_id,
    area_interest, budget, modality, description,
    is_late_enrollment_request, status, created_at, lead_source_type
), INSERT (
    id, first_name, last_name, email, whatsapp, source_page, type, course_id,
    area_interest, budget, modality, description,
    is_late_enrollment_request, status, created_at, lead_source_type
), UPDATE (
    id, first_name, last_name, email, whatsapp, source_page, type, course_id,
    area_interest, budget, modality, description,
    is_late_enrollment_request, status, created_at, lead_source_type
), REFERENCES (
    id, first_name, last_name, email, whatsapp, source_page, type, course_id,
    area_interest, budget, modality, description,
    is_late_enrollment_request, status, created_at, lead_source_type
) ON TABLE public.leads FROM PUBLIC, anon, authenticated, authenticator, service_role;

REVOKE SELECT (
    id, lead_id, recipient_type, recipient_email, subject, status, resend_id,
    error_message, created_at
), INSERT (
    id, lead_id, recipient_type, recipient_email, subject, status, resend_id,
    error_message, created_at
), UPDATE (
    id, lead_id, recipient_type, recipient_email, subject, status, resend_id,
    error_message, created_at
), REFERENCES (
    id, lead_id, recipient_type, recipient_email, subject, status, resend_id,
    error_message, created_at
) ON TABLE public.email_log FROM PUBLIC, anon, authenticated, authenticator, service_role;

-- security-hold-stage-revokes-complete

DROP POLICY IF EXISTS leads_insert_public ON public.leads;
DROP POLICY IF EXISTS leads_insert_authenticated ON public.leads;
DROP POLICY IF EXISTS leads_service_role ON public.leads;
DROP POLICY IF EXISTS email_log_service_role ON public.email_log;
DROP POLICY IF EXISTS leads_security_hold_service_select ON public.leads;
DROP POLICY IF EXISTS leads_security_hold_service_delete ON public.leads;
DROP POLICY IF EXISTS email_log_security_hold_service_select ON public.email_log;
DROP POLICY IF EXISTS email_log_security_hold_service_delete ON public.email_log;

-- security-hold-stage-policies-complete

ALTER TABLE public.leads
ADD CONSTRAINT chk_fase09_7_leads_security_hold_no_insert_update
CHECK (false) NOT VALID;

ALTER TABLE public.email_log
ADD CONSTRAINT chk_fase09_7_email_log_security_hold_no_insert_update
CHECK (false) NOT VALID;

-- security-hold-stage-constraints-complete

CREATE OR REPLACE FUNCTION public.verify_fase09_7_leads_email_security_hold()
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $function$
DECLARE
    actual_count integer;
    actual_record record;
    role_name text;
    service_role_oid oid;
    authenticator_oid oid;
BEGIN
    SELECT role.oid INTO service_role_oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'service_role';
    IF service_role_oid IS NULL THEN
        RETURN false;
    END IF;

    SELECT role.oid INTO authenticator_oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'authenticator';
    IF authenticator_oid IS NULL THEN
        RETURN false;
    END IF;

    IF pg_catalog.current_setting('server_version_num')::integer < 170000
       OR pg_catalog.current_setting('server_version_num')::integer >= 180000 THEN
        RETURN false;
    END IF;

    SELECT pg_catalog.count(*)::integer
    INTO actual_count
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role');
    IF actual_count <> 4 THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_roles AS role
        WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
          AND (
              role.rolsuper
              OR role.rolcreatedb
              OR role.rolcreaterole
              OR role.rolreplication
              OR (role.rolbypassrls AND role.rolname <> 'service_role')
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_roles AS role
        WHERE role.rolname = 'authenticator'
          AND (role.rolinherit OR role.rolbypassrls)
    ) THEN
        RETURN false;
    END IF;

    IF NOT (
        SELECT pg_catalog.count(*) = 3
           AND pg_catalog.bool_and(
               target_role.rolname IN ('anon', 'authenticated', 'service_role')
               AND NOT membership.admin_option
               AND NOT membership.inherit_option
               AND membership.set_option
           )
        FROM pg_catalog.pg_auth_members AS membership
        JOIN pg_catalog.pg_roles AS target_role
          ON target_role.oid = membership.roleid
        WHERE membership.member = authenticator_oid
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_auth_members AS membership
        JOIN pg_catalog.pg_roles AS member_role
          ON member_role.oid = membership.member
        WHERE member_role.rolname IN ('anon', 'authenticated', 'service_role')
    ) THEN
        RETURN false;
    END IF;

    IF pg_catalog.to_regprocedure('public.notify_new_lead()') IS NOT NULL THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.proname = 'notify_new_lead'
    ) THEN
        RETURN false;
    END IF;

    SELECT pg_catalog.count(*)::integer
    INTO actual_count
    FROM pg_catalog.pg_class AS relation
    JOIN pg_catalog.pg_roles AS owner ON owner.oid = relation.relowner
    WHERE relation.oid = ANY(ARRAY[
        'public.leads'::pg_catalog.regclass,
        'public.email_log'::pg_catalog.regclass
    ])
      AND relation.relkind IN ('r', 'p')
      AND owner.rolname = 'postgres'
      AND relation.relrowsecurity
      AND relation.relforcerowsecurity
      AND NOT relation.relispartition;
    IF actual_count <> 2 THEN
        RETURN false;
    END IF;

    SELECT pg_catalog.count(*)::integer
    INTO actual_count
    FROM pg_catalog.pg_constraint AS constraint_record
    WHERE (constraint_record.conrelid, constraint_record.conname) IN (
        (
            'public.leads'::pg_catalog.regclass,
            'chk_fase09_7_leads_security_hold_no_insert_update'
        ),
        (
            'public.email_log'::pg_catalog.regclass,
            'chk_fase09_7_email_log_security_hold_no_insert_update'
        )
    )
      AND constraint_record.contype = 'c'
      AND NOT constraint_record.convalidated
      AND pg_catalog.pg_get_constraintdef(constraint_record.oid, true) =
          'CHECK (false) NOT VALID';
    IF actual_count <> 2 THEN
        RETURN false;
    END IF;

    FOR role_name IN
        SELECT * FROM pg_catalog.unnest(
            ARRAY['anon', 'authenticated', 'authenticator', 'service_role']
        )
    LOOP
        IF EXISTS (
            SELECT 1
            FROM pg_catalog.unnest(
                ARRAY['public.leads', 'public.email_log']::text[]
            ) AS denied_table(table_name)
            CROSS JOIN pg_catalog.unnest(ARRAY[
                'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                'REFERENCES', 'TRIGGER', 'MAINTAIN'
            ]::text[]) AS denied_privilege(privilege_name)
            WHERE pg_catalog.has_table_privilege(
                role_name,
                denied_table.table_name,
                denied_privilege.privilege_name
            )
        ) THEN
            RETURN false;
        END IF;

        IF EXISTS (
            SELECT 1
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid = ANY(ARRAY[
                'public.leads'::pg_catalog.regclass,
                'public.email_log'::pg_catalog.regclass
            ])
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
              AND (
                  pg_catalog.has_column_privilege(
                      role_name, attribute.attrelid, attribute.attnum, 'SELECT'
                  )
                  OR pg_catalog.has_column_privilege(
                      role_name, attribute.attrelid, attribute.attnum, 'INSERT'
                  )
                  OR pg_catalog.has_column_privilege(
                      role_name, attribute.attrelid, attribute.attnum, 'UPDATE'
                  )
                  OR pg_catalog.has_column_privilege(
                      role_name, attribute.attrelid, attribute.attnum, 'REFERENCES'
                  )
              )
        ) THEN
            RETURN false;
        END IF;
    END LOOP;

    IF EXISTS (
        WITH RECURSIVE reachable_roles(root_name, role_oid, path) AS (
            SELECT role.rolname, role.oid, ARRAY[role.oid]
            FROM pg_catalog.pg_roles AS role
            WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
            UNION ALL
            SELECT reachable_roles.root_name,
                   parent_role.oid,
                   reachable_roles.path || parent_role.oid
            FROM reachable_roles
            JOIN pg_catalog.pg_auth_members AS membership
              ON membership.member = reachable_roles.role_oid
            JOIN pg_catalog.pg_roles AS parent_role
              ON parent_role.oid = membership.roleid
            WHERE parent_role.oid <> ALL(reachable_roles.path)
              AND (
                  membership.inherit_option
                  OR membership.set_option
                  OR membership.admin_option
              )
        )
        SELECT 1
        FROM reachable_roles
        JOIN pg_catalog.pg_roles AS role
          ON role.oid = reachable_roles.role_oid
        WHERE role.rolname NOT IN ('anon', 'authenticated', 'authenticator', 'service_role')
           AND (
               role.rolsuper
               OR role.rolbypassrls
              OR role.rolcreaterole
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_class AS relation
                  WHERE relation.oid = ANY(ARRAY[
                      'public.leads'::pg_catalog.regclass,
                      'public.email_log'::pg_catalog.regclass
                  ])
                    AND relation.relowner = role.oid
              )
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.unnest(
                      ARRAY['public.leads', 'public.email_log']::text[]
                  ) AS held_table(table_name)
                  CROSS JOIN pg_catalog.unnest(ARRAY[
                      'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                      'REFERENCES', 'TRIGGER', 'MAINTAIN'
                  ]::text[]) AS privilege(privilege_name)
                  WHERE pg_catalog.has_table_privilege(
                      role.oid,
                      held_table.table_name,
                      privilege.privilege_name
                  )
              )
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_attribute AS attribute
                  WHERE attribute.attrelid = ANY(ARRAY[
                      'public.leads'::pg_catalog.regclass,
                      'public.email_log'::pg_catalog.regclass
                  ])
                    AND attribute.attnum > 0
                    AND NOT attribute.attisdropped
                    AND (
                        pg_catalog.has_column_privilege(
                            role.oid, attribute.attrelid, attribute.attnum, 'SELECT'
                        )
                        OR pg_catalog.has_column_privilege(
                            role.oid, attribute.attrelid, attribute.attnum, 'INSERT'
                        )
                        OR pg_catalog.has_column_privilege(
                            role.oid, attribute.attrelid, attribute.attnum, 'UPDATE'
                        )
                        OR pg_catalog.has_column_privilege(
                            role.oid, attribute.attrelid, attribute.attnum, 'REFERENCES'
                        )
                    )
              )
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class AS relation
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = relation.relowner
        CROSS JOIN LATERAL pg_catalog.aclexplode(
            COALESCE(relation.relacl, '{}'::aclitem[])
        ) AS acl
        WHERE relation.oid = ANY(ARRAY[
            'public.leads'::pg_catalog.regclass,
            'public.email_log'::pg_catalog.regclass
        ])
          AND (
              acl.grantee <> owner.oid
              OR acl.is_grantable
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_attribute AS attribute
        CROSS JOIN LATERAL pg_catalog.unnest(
            COALESCE(attribute.attacl, '{}'::aclitem[])
        ) AS acl(acl_item)
        WHERE attribute.attrelid = ANY(ARRAY[
            'public.leads'::pg_catalog.regclass,
            'public.email_log'::pg_catalog.regclass
        ])
          AND attribute.attnum > 0
          AND NOT attribute.attisdropped
          AND acl.acl_item IS NOT NULL
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        WITH RECURSIVE reachable_roles(role_oid, path) AS (
            SELECT role.oid, ARRAY[role.oid]
            FROM pg_catalog.pg_roles AS role
            WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
            UNION ALL
            SELECT parent_role.oid, reachable_roles.path || parent_role.oid
            FROM reachable_roles
            JOIN pg_catalog.pg_auth_members AS membership
              ON membership.member = reachable_roles.role_oid
            JOIN pg_catalog.pg_roles AS parent_role
              ON parent_role.oid = membership.roleid
            WHERE parent_role.oid <> ALL(reachable_roles.path)
              AND (
                  membership.inherit_option
                  OR membership.set_option
                  OR membership.admin_option
              )
        )
        SELECT 1
        FROM pg_catalog.pg_namespace AS namespace
        CROSS JOIN reachable_roles
        WHERE namespace.nspname = 'public'
          AND pg_catalog.has_schema_privilege(reachable_roles.role_oid, namespace.oid, 'CREATE')
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN ('leads', 'email_log')
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_record
        WHERE NOT trigger_record.tgisinternal
          AND (
              trigger_record.tgrelid IN (
                  'public.leads'::pg_catalog.regclass,
                  'public.email_log'::pg_catalog.regclass
              )
              OR trigger_record.tgname = 'trg_notify_new_lead'
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_rewrite AS rewrite_record
        WHERE rewrite_record.ev_class IN (
            'public.leads'::pg_catalog.regclass,
            'public.email_log'::pg_catalog.regclass
        )
          AND rewrite_record.rulename <> '_RETURN'
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        WITH RECURSIVE reachable_roles(role_oid, path) AS (
            SELECT role.oid, ARRAY[role.oid]
            FROM pg_catalog.pg_roles AS role
            WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
            UNION ALL
            SELECT parent_role.oid, reachable_roles.path || parent_role.oid
            FROM reachable_roles
            JOIN pg_catalog.pg_auth_members AS membership
              ON membership.member = reachable_roles.role_oid
            JOIN pg_catalog.pg_roles AS parent_role
              ON parent_role.oid = membership.roleid
            WHERE parent_role.oid <> ALL(reachable_roles.path)
              AND (
                  membership.inherit_option
                  OR membership.set_option
                  OR membership.admin_option
              )
        ),
        writable_relations(relation_oid) AS (
            SELECT DISTINCT relation.oid
            FROM pg_catalog.pg_class AS relation
            JOIN pg_catalog.pg_namespace AS relation_schema
              ON relation_schema.oid = relation.relnamespace
            CROSS JOIN reachable_roles
            WHERE relation.oid <> ALL(ARRAY[
                'public.leads'::pg_catalog.regclass,
                'public.email_log'::pg_catalog.regclass
            ])
              AND relation.relkind IN ('r', 'p', 'v', 'f')
              AND pg_catalog.has_schema_privilege(
                  reachable_roles.role_oid, relation_schema.oid, 'USAGE'
              )
              AND (
                  pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'INSERT')
                  OR pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'UPDATE')
                  OR pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'DELETE')
                  OR pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'TRUNCATE')
                  OR EXISTS (
                      SELECT 1
                      FROM pg_catalog.pg_attribute AS attribute
                      WHERE attribute.attrelid = relation.oid
                        AND attribute.attnum > 0
                        AND NOT attribute.attisdropped
                        AND (
                            pg_catalog.has_column_privilege(
                                reachable_roles.role_oid, relation.oid, attribute.attnum, 'INSERT'
                            )
                            OR pg_catalog.has_column_privilege(
                                reachable_roles.role_oid, relation.oid, attribute.attnum, 'UPDATE'
                            )
                        )
                  )
              )
        ),
        dangerous_routines(procedure_oid, path) AS (
            SELECT procedure_record.oid, ARRAY[procedure_record.oid]
            FROM pg_catalog.pg_proc AS procedure_record
            WHERE procedure_record.prokind IN ('f', 'p')
              AND (
                  procedure_record.prosrc ILIKE '%public.leads%'
                  OR procedure_record.prosrc ILIKE '%public.email_log%'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ILIKE
                     '%public.leads%'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ILIKE
                     '%public.email_log%'
                  OR procedure_record.prosrc ~* '\m(leads|email_log)\M'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ~*
                     '\m(leads|email_log)\M'
                  OR EXISTS (
                      SELECT 1
                      FROM pg_catalog.pg_depend AS dependency
                      WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.objid = procedure_record.oid
                        AND dependency.refobjid IN (
                            'public.leads'::pg_catalog.regclass,
                            'public.email_log'::pg_catalog.regclass
                        )
                  )
                  OR procedure_record.prosrc ~* '\mEXECUTE\M'
              )
            UNION ALL
            SELECT caller.oid, dangerous_routines.path || caller.oid
            FROM dangerous_routines
            JOIN pg_catalog.pg_proc AS dangerous_procedure
              ON dangerous_procedure.oid = dangerous_routines.procedure_oid
            JOIN pg_catalog.pg_namespace AS dangerous_schema
              ON dangerous_schema.oid = dangerous_procedure.pronamespace
            JOIN pg_catalog.pg_proc AS caller
              ON caller.prokind IN ('f', 'p')
            WHERE caller.oid <> ALL(dangerous_routines.path)
              AND (
                  EXISTS (
                      SELECT 1
                      FROM pg_catalog.pg_depend AS dependency
                      WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.objid = caller.oid
                        AND dependency.refobjid = dangerous_routines.procedure_oid
                  )
                  OR caller.prosrc ILIKE '%' || dangerous_schema.nspname || '.' ||
                     dangerous_procedure.proname || '%'
                  OR caller.prosrc ILIKE '%' || pg_catalog.format(
                      '%I.%I', dangerous_schema.nspname, dangerous_procedure.proname
                  ) || '%'
                  OR caller.prosrc ILIKE '%' || dangerous_procedure.proname || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     dangerous_schema.nspname || '.' || dangerous_procedure.proname || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     pg_catalog.format(
                         '%I.%I', dangerous_schema.nspname, dangerous_procedure.proname
                     ) || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     dangerous_procedure.proname || '%'
              )
        )
        SELECT 1
        FROM pg_catalog.pg_trigger AS trigger_record
        JOIN writable_relations
          ON writable_relations.relation_oid = trigger_record.tgrelid
        JOIN dangerous_routines
          ON dangerous_routines.procedure_oid = trigger_record.tgfoid
        WHERE NOT trigger_record.tgisinternal
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        WITH RECURSIVE reachable_roles(role_oid, path) AS (
            SELECT role.oid, ARRAY[role.oid]
            FROM pg_catalog.pg_roles AS role
            WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
            UNION ALL
            SELECT parent_role.oid, reachable_roles.path || parent_role.oid
            FROM reachable_roles
            JOIN pg_catalog.pg_auth_members AS membership
              ON membership.member = reachable_roles.role_oid
            JOIN pg_catalog.pg_roles AS parent_role
              ON parent_role.oid = membership.roleid
            WHERE parent_role.oid <> ALL(reachable_roles.path)
              AND (
                  membership.inherit_option
                  OR membership.set_option
                  OR membership.admin_option
              )
        ),
        dangerous_routines(procedure_oid, path) AS (
            SELECT procedure_record.oid, ARRAY[procedure_record.oid]
            FROM pg_catalog.pg_proc AS procedure_record
            WHERE procedure_record.prokind IN ('f', 'p')
              AND (
                  procedure_record.prosrc ILIKE '%public.leads%'
                  OR procedure_record.prosrc ILIKE '%public.email_log%'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ILIKE
                     '%public.leads%'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ILIKE
                     '%public.email_log%'
                  OR procedure_record.prosrc ~* '\m(leads|email_log)\M'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ~*
                     '\m(leads|email_log)\M'
                  OR EXISTS (
                      SELECT 1
                      FROM pg_catalog.pg_depend AS dependency
                      WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.objid = procedure_record.oid
                        AND dependency.refobjid IN (
                            'public.leads'::pg_catalog.regclass,
                            'public.email_log'::pg_catalog.regclass
                        )
                  )
                  OR procedure_record.prosrc ~* '\mEXECUTE\M'
              )
            UNION ALL
            SELECT caller.oid, dangerous_routines.path || caller.oid
            FROM dangerous_routines
            JOIN pg_catalog.pg_proc AS dangerous_procedure
              ON dangerous_procedure.oid = dangerous_routines.procedure_oid
            JOIN pg_catalog.pg_namespace AS dangerous_schema
              ON dangerous_schema.oid = dangerous_procedure.pronamespace
            JOIN pg_catalog.pg_proc AS caller
              ON caller.prokind IN ('f', 'p')
            WHERE caller.oid <> ALL(dangerous_routines.path)
              AND (
                  EXISTS (
                      SELECT 1
                      FROM pg_catalog.pg_depend AS dependency
                      WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.objid = caller.oid
                        AND dependency.refobjid = dangerous_routines.procedure_oid
                  )
                  OR caller.prosrc ILIKE '%' || dangerous_schema.nspname || '.' ||
                     dangerous_procedure.proname || '%'
                  OR caller.prosrc ILIKE '%' || pg_catalog.format(
                      '%I.%I', dangerous_schema.nspname, dangerous_procedure.proname
                  ) || '%'
                  OR caller.prosrc ILIKE '%' || dangerous_procedure.proname || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     dangerous_schema.nspname || '.' || dangerous_procedure.proname || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     pg_catalog.format(
                         '%I.%I', dangerous_schema.nspname, dangerous_procedure.proname
                     ) || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     dangerous_procedure.proname || '%'
              )
        )
        SELECT 1
        FROM pg_catalog.pg_rewrite AS rewrite_record
        JOIN pg_catalog.pg_class AS relation
          ON relation.oid = rewrite_record.ev_class
        JOIN pg_catalog.pg_namespace AS relation_schema
          ON relation_schema.oid = relation.relnamespace
        CROSS JOIN reachable_roles
        WHERE rewrite_record.rulename <> '_RETURN'
          AND relation.oid <> ALL(ARRAY[
              'public.leads'::pg_catalog.regclass,
              'public.email_log'::pg_catalog.regclass
          ])
          AND pg_catalog.has_schema_privilege(
              reachable_roles.role_oid, relation_schema.oid, 'USAGE'
          )
          AND (
              pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'SELECT')
              OR pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'INSERT')
              OR pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'UPDATE')
              OR pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'DELETE')
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_attribute AS attribute
                  WHERE attribute.attrelid = relation.oid
                    AND attribute.attnum > 0
                    AND NOT attribute.attisdropped
                    AND (
                        pg_catalog.has_column_privilege(
                            reachable_roles.role_oid, relation.oid, attribute.attnum, 'SELECT'
                        )
                        OR pg_catalog.has_column_privilege(
                            reachable_roles.role_oid, relation.oid, attribute.attnum, 'INSERT'
                        )
                        OR pg_catalog.has_column_privilege(
                            reachable_roles.role_oid, relation.oid, attribute.attnum, 'UPDATE'
                        )
                    )
              )
          )
          AND (
              pg_catalog.pg_get_ruledef(rewrite_record.oid) ILIKE '%public.leads%'
              OR pg_catalog.pg_get_ruledef(rewrite_record.oid) ILIKE '%public.email_log%'
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_depend AS dependency
                  WHERE dependency.classid = 'pg_catalog.pg_rewrite'::pg_catalog.regclass
                    AND dependency.objid = rewrite_record.oid
                    AND dependency.refobjid IN (
                        'public.leads'::pg_catalog.regclass,
                        'public.email_log'::pg_catalog.regclass
                    )
              )
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_depend AS dependency
                  JOIN dangerous_routines
                    ON dangerous_routines.procedure_oid = dependency.refobjid
                  WHERE dependency.classid = 'pg_catalog.pg_rewrite'::pg_catalog.regclass
                    AND dependency.objid = rewrite_record.oid
              )
              OR EXISTS (
                  SELECT 1
                  FROM dangerous_routines
                  JOIN pg_catalog.pg_proc AS dangerous_procedure
                    ON dangerous_procedure.oid = dangerous_routines.procedure_oid
                  JOIN pg_catalog.pg_namespace AS dangerous_schema
                    ON dangerous_schema.oid = dangerous_procedure.pronamespace
                  WHERE pg_catalog.pg_get_ruledef(rewrite_record.oid) ILIKE '%' ||
                        dangerous_schema.nspname || '.' || dangerous_procedure.proname || '%'
                     OR pg_catalog.pg_get_ruledef(rewrite_record.oid) ILIKE '%' ||
                        pg_catalog.format(
                            '%I.%I', dangerous_schema.nspname, dangerous_procedure.proname
                        ) || '%'
                     OR pg_catalog.pg_get_ruledef(rewrite_record.oid) ILIKE '%' ||
                        dangerous_procedure.proname || '%'
              )
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        WITH RECURSIVE reachable_roles(role_oid, path) AS (
            SELECT role.oid, ARRAY[role.oid]
            FROM pg_catalog.pg_roles AS role
            WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
            UNION ALL
            SELECT parent_role.oid, reachable_roles.path || parent_role.oid
            FROM reachable_roles
            JOIN pg_catalog.pg_auth_members AS membership
              ON membership.member = reachable_roles.role_oid
            JOIN pg_catalog.pg_roles AS parent_role
              ON parent_role.oid = membership.roleid
            WHERE parent_role.oid <> ALL(reachable_roles.path)
              AND (
                  membership.inherit_option
                  OR membership.set_option
                  OR membership.admin_option
              )
        )
        SELECT 1
        FROM pg_catalog.pg_constraint AS constraint_record
        JOIN pg_catalog.pg_class AS relation
          ON relation.oid = constraint_record.conrelid
        JOIN pg_catalog.pg_namespace AS relation_schema
          ON relation_schema.oid = relation.relnamespace
        CROSS JOIN reachable_roles
        WHERE constraint_record.contype = 'f'
          AND constraint_record.confrelid IN (
              'public.leads'::pg_catalog.regclass,
              'public.email_log'::pg_catalog.regclass
          )
          AND constraint_record.conrelid <> ALL(ARRAY[
              'public.leads'::pg_catalog.regclass,
              'public.email_log'::pg_catalog.regclass
          ])
          AND pg_catalog.has_schema_privilege(
              reachable_roles.role_oid, relation_schema.oid, 'USAGE'
          )
          AND (
              pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'INSERT')
              OR pg_catalog.has_table_privilege(reachable_roles.role_oid, relation.oid, 'UPDATE')
              OR EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_attribute AS attribute
                  WHERE attribute.attrelid = relation.oid
                    AND attribute.attnum = ANY(constraint_record.conkey)
                    AND NOT attribute.attisdropped
                    AND (
                        pg_catalog.has_column_privilege(
                            reachable_roles.role_oid, relation.oid, attribute.attnum, 'INSERT'
                        )
                        OR pg_catalog.has_column_privilege(
                            reachable_roles.role_oid, relation.oid, attribute.attnum, 'UPDATE'
                        )
                    )
              )
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        WITH RECURSIVE reachable_roles(role_oid, path) AS (
            SELECT role.oid, ARRAY[role.oid]
            FROM pg_catalog.pg_roles AS role
            WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
            UNION ALL
            SELECT parent_role.oid, reachable_roles.path || parent_role.oid
            FROM reachable_roles
            JOIN pg_catalog.pg_auth_members AS membership
              ON membership.member = reachable_roles.role_oid
            JOIN pg_catalog.pg_roles AS parent_role
              ON parent_role.oid = membership.roleid
            WHERE parent_role.oid <> ALL(reachable_roles.path)
              AND (
                  membership.inherit_option
                  OR membership.set_option
                  OR membership.admin_option
              )
        ),
        dependent_views(view_oid, path) AS (
            SELECT view_record.oid, ARRAY[view_record.oid]
            FROM pg_catalog.pg_rewrite AS rewrite_record
            JOIN pg_catalog.pg_depend AS dependency
              ON dependency.classid = 'pg_catalog.pg_rewrite'::pg_catalog.regclass
             AND dependency.objid = rewrite_record.oid
            JOIN pg_catalog.pg_class AS view_record
              ON view_record.oid = rewrite_record.ev_class
            WHERE dependency.refobjid IN (
                'public.leads'::pg_catalog.regclass,
                'public.email_log'::pg_catalog.regclass
            )
              AND view_record.relkind IN ('v', 'm')
            UNION ALL
            SELECT next_view.oid, dependent_views.path || next_view.oid
            FROM dependent_views
            JOIN pg_catalog.pg_rewrite AS rewrite_record
              ON true
            JOIN pg_catalog.pg_depend AS dependency
              ON dependency.classid = 'pg_catalog.pg_rewrite'::pg_catalog.regclass
             AND dependency.objid = rewrite_record.oid
             AND dependency.refobjid = dependent_views.view_oid
            JOIN pg_catalog.pg_class AS next_view
              ON next_view.oid = rewrite_record.ev_class
            WHERE next_view.relkind IN ('v', 'm')
              AND next_view.oid <> ALL(dependent_views.path)
        )
        SELECT 1
        FROM dependent_views
        JOIN pg_catalog.pg_class AS view_record
          ON view_record.oid = dependent_views.view_oid
        JOIN pg_catalog.pg_namespace AS view_schema
          ON view_schema.oid = view_record.relnamespace
        CROSS JOIN reachable_roles
        WHERE (view_record.relkind = 'm' AND view_record.relispopulated)
           OR (
               pg_catalog.has_schema_privilege(reachable_roles.role_oid, view_schema.oid, 'USAGE')
               AND (
                   pg_catalog.has_table_privilege(reachable_roles.role_oid, view_record.oid, 'SELECT')
                   OR pg_catalog.has_table_privilege(reachable_roles.role_oid, view_record.oid, 'INSERT')
                   OR pg_catalog.has_table_privilege(reachable_roles.role_oid, view_record.oid, 'UPDATE')
                   OR pg_catalog.has_table_privilege(reachable_roles.role_oid, view_record.oid, 'DELETE')
                   OR pg_catalog.has_table_privilege(reachable_roles.role_oid, view_record.oid, 'REFERENCES')
                   OR EXISTS (
                       SELECT 1
                       FROM pg_catalog.pg_attribute AS attribute
                       WHERE attribute.attrelid = view_record.oid
                         AND attribute.attnum > 0
                          AND NOT attribute.attisdropped
                          AND (
                              pg_catalog.has_column_privilege(
                                  reachable_roles.role_oid, view_record.oid, attribute.attnum, 'SELECT'
                              )
                              OR pg_catalog.has_column_privilege(
                                  reachable_roles.role_oid, view_record.oid, attribute.attnum, 'INSERT'
                              )
                              OR pg_catalog.has_column_privilege(
                                  reachable_roles.role_oid, view_record.oid, attribute.attnum, 'UPDATE'
                              )
                              OR pg_catalog.has_column_privilege(
                                  reachable_roles.role_oid, view_record.oid, attribute.attnum, 'REFERENCES'
                              )
                          )
                   )
               )
           )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_publication_rel AS publication_relation
        WHERE publication_relation.prrelid IN (
            'public.leads'::pg_catalog.regclass,
            'public.email_log'::pg_catalog.regclass
        )
        UNION ALL
        SELECT 1
        FROM pg_catalog.pg_publication AS publication
        WHERE publication.puballtables
        UNION ALL
        SELECT 1
        FROM pg_catalog.pg_publication_namespace AS publication_namespace
        WHERE publication_namespace.pnnspid = 'public'::pg_catalog.regnamespace
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_inherits AS inheritance_record
        WHERE inheritance_record.inhrelid IN (
            'public.leads'::pg_catalog.regclass,
            'public.email_log'::pg_catalog.regclass
        )
           OR inheritance_record.inhparent IN (
            'public.leads'::pg_catalog.regclass,
            'public.email_log'::pg_catalog.regclass
        )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        WITH RECURSIVE reachable_roles(role_oid, path) AS (
            SELECT role.oid, ARRAY[role.oid]
            FROM pg_catalog.pg_roles AS role
            WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
            UNION ALL
            SELECT parent_role.oid, reachable_roles.path || parent_role.oid
            FROM reachable_roles
            JOIN pg_catalog.pg_auth_members AS membership
              ON membership.member = reachable_roles.role_oid
            JOIN pg_catalog.pg_roles AS parent_role
              ON parent_role.oid = membership.roleid
            WHERE parent_role.oid <> ALL(reachable_roles.path)
              AND (
                  membership.inherit_option
                  OR membership.set_option
                  OR membership.admin_option
              )
        ),
        dangerous_routines(procedure_oid, path) AS (
            SELECT procedure_record.oid, ARRAY[procedure_record.oid]
            FROM pg_catalog.pg_proc AS procedure_record
            WHERE procedure_record.prokind IN ('f', 'p')
              AND (
                  procedure_record.prosrc ILIKE '%public.leads%'
                  OR procedure_record.prosrc ILIKE '%public.email_log%'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ILIKE
                     '%public.leads%'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ILIKE
                     '%public.email_log%'
                  OR procedure_record.prosrc ~* '\m(leads|email_log)\M'
                  OR pg_catalog.pg_get_functiondef(procedure_record.oid) ~*
                     '\m(leads|email_log)\M'
                  OR EXISTS (
                      SELECT 1
                      FROM pg_catalog.pg_depend AS dependency
                      WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.objid = procedure_record.oid
                        AND dependency.refobjid IN (
                            'public.leads'::pg_catalog.regclass,
                            'public.email_log'::pg_catalog.regclass
                      )
                  )
                  OR procedure_record.prosrc ~* '\mEXECUTE\M'
              )
            UNION ALL
            SELECT caller.oid, dangerous_routines.path || caller.oid
            FROM dangerous_routines
            JOIN pg_catalog.pg_proc AS dangerous_procedure
              ON dangerous_procedure.oid = dangerous_routines.procedure_oid
            JOIN pg_catalog.pg_namespace AS dangerous_schema
              ON dangerous_schema.oid = dangerous_procedure.pronamespace
            JOIN pg_catalog.pg_proc AS caller
              ON caller.prokind IN ('f', 'p')
            WHERE caller.oid <> ALL(dangerous_routines.path)
              AND (
                  EXISTS (
                      SELECT 1
                      FROM pg_catalog.pg_depend AS dependency
                      WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                        AND dependency.objid = caller.oid
                        AND dependency.refobjid = dangerous_routines.procedure_oid
                  )
                  OR caller.prosrc ILIKE '%' || dangerous_schema.nspname || '.' ||
                     dangerous_procedure.proname || '%'
                  OR caller.prosrc ILIKE '%' || pg_catalog.format(
                      '%I.%I', dangerous_schema.nspname, dangerous_procedure.proname
                  ) || '%'
                  OR caller.prosrc ILIKE '%' || dangerous_procedure.proname || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     dangerous_schema.nspname || '.' || dangerous_procedure.proname || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     pg_catalog.format(
                         '%I.%I', dangerous_schema.nspname, dangerous_procedure.proname
                     ) || '%'
                  OR pg_catalog.pg_get_functiondef(caller.oid) ILIKE '%' ||
                     dangerous_procedure.proname || '%'
              )
        )
        SELECT 1
        FROM dangerous_routines
        JOIN pg_catalog.pg_proc AS procedure_record
          ON procedure_record.oid = dangerous_routines.procedure_oid
        JOIN pg_catalog.pg_namespace AS procedure_schema
          ON procedure_schema.oid = procedure_record.pronamespace
        CROSS JOIN reachable_roles
        WHERE procedure_record.oid NOT IN (
              pg_catalog.to_regprocedure('public.verify_fase06_g1b_reconciliation()'),
              pg_catalog.to_regprocedure('public.verify_fase06_hito1_contract()'),
              pg_catalog.to_regprocedure('public.verify_fase07_g1b_closure()'),
              pg_catalog.to_regprocedure('public.verify_fase08_hito1_contract()'),
              pg_catalog.to_regprocedure('public.verify_fase09_7_public_access_closure()'),
              pg_catalog.to_regprocedure('public.verify_fase09_7_notify_new_lead_retirement()'),
              pg_catalog.to_regprocedure('public.verify_fase09_7_leads_email_security_hold()'),
              pg_catalog.to_regprocedure('public.exec_sql(text)')
          )
          AND pg_catalog.has_schema_privilege(
              reachable_roles.role_oid, procedure_schema.oid, 'USAGE'
          )
          AND pg_catalog.has_function_privilege(
              reachable_roles.role_oid, procedure_record.oid, 'EXECUTE'
          )
    ) THEN
        RETURN false;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS procedure_schema
          ON procedure_schema.oid = procedure_record.pronamespace
        WHERE procedure_schema.nspname = 'public'
          AND procedure_record.proname IN (
              'verify_fase09_7_public_access_closure',
              'verify_fase09_7_notify_new_lead_retirement',
              'verify_fase09_7_leads_email_security_hold',
              'exec_sql'
          )
          AND procedure_record.oid NOT IN (
              pg_catalog.to_regprocedure('public.verify_fase09_7_public_access_closure()'),
              pg_catalog.to_regprocedure('public.verify_fase09_7_notify_new_lead_retirement()'),
              pg_catalog.to_regprocedure('public.verify_fase09_7_leads_email_security_hold()'),
              pg_catalog.to_regprocedure('public.exec_sql(text)')
          )
    ) THEN
        RETURN false;
    END IF;

    IF NOT (
        SELECT pg_catalog.count(*) = 1
           AND pg_catalog.bool_and(
               owner.rolname = 'postgres'
               AND language_record.lanname = 'plpgsql'
               AND return_namespace.nspname = 'pg_catalog'
               AND return_type.typname = 'jsonb'
               AND procedure_record.prokind = 'f'
               AND procedure_record.prosecdef
               AND procedure_record.proconfig IS NOT DISTINCT FROM
                   ARRAY['search_path=""']::text[]
               AND NOT pg_catalog.has_function_privilege(
                   'anon', procedure_record.oid, 'EXECUTE'
               )
               AND NOT pg_catalog.has_function_privilege(
                   'authenticated', procedure_record.oid, 'EXECUTE'
               )
               AND NOT pg_catalog.has_function_privilege(
                   'authenticator', procedure_record.oid, 'EXECUTE'
               )
                AND pg_catalog.has_function_privilege(
                    'service_role', procedure_record.oid, 'EXECUTE'
                )
                AND (
                    SELECT pg_catalog.count(*)
                    FROM pg_catalog.aclexplode(COALESCE(
                        procedure_record.proacl,
                        pg_catalog.acldefault('f', procedure_record.proowner)
                    )) AS acl
                ) = 2
                AND (
                    SELECT pg_catalog.count(*)
                    FROM pg_catalog.aclexplode(COALESCE(
                        procedure_record.proacl,
                        pg_catalog.acldefault('f', procedure_record.proowner)
                    )) AS acl
                    WHERE acl.privilege_type = 'EXECUTE'
                      AND NOT acl.is_grantable
                      AND acl.grantee = procedure_record.proowner
                ) = 1
                AND (
                    SELECT pg_catalog.count(*)
                    FROM pg_catalog.aclexplode(COALESCE(
                        procedure_record.proacl,
                        pg_catalog.acldefault('f', procedure_record.proowner)
                    )) AS acl
                    WHERE acl.privilege_type = 'EXECUTE'
                      AND NOT acl.is_grantable
                      AND acl.grantee = service_role_oid
                ) = 1
            )
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        JOIN pg_catalog.pg_type AS return_type
          ON return_type.oid = procedure_record.prorettype
        JOIN pg_catalog.pg_namespace AS return_namespace
          ON return_namespace.oid = return_type.typnamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.oid =
              pg_catalog.to_regprocedure('public.exec_sql(text)')
    ) THEN
        RETURN false;
    END IF;

    FOR actual_record IN
        SELECT * FROM (VALUES
            ('public.verify_fase09_7_public_access_closure()', 'plpgsql'::name),
            ('public.verify_fase09_7_notify_new_lead_retirement()', 'sql'::name),
            ('public.verify_fase09_7_leads_email_security_hold()', 'plpgsql'::name)
        ) AS expected(function_signature, language_name)
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_proc AS procedure_record
            JOIN pg_catalog.pg_namespace AS procedure_schema
              ON procedure_schema.oid = procedure_record.pronamespace
            JOIN pg_catalog.pg_language AS language_record
              ON language_record.oid = procedure_record.prolang
            JOIN pg_catalog.pg_roles AS owner
              ON owner.oid = procedure_record.proowner
            WHERE procedure_record.oid =
                  pg_catalog.to_regprocedure(actual_record.function_signature)
              AND procedure_schema.nspname = 'public'
              AND owner.rolname = 'postgres'
              AND language_record.lanname = actual_record.language_name
              AND NOT procedure_record.prosecdef
              AND procedure_record.provolatile = 's'
               AND procedure_record.proconfig IS NOT DISTINCT FROM
                   ARRAY['search_path=""']::text[]
               AND NOT pg_catalog.has_function_privilege(
                   'anon', procedure_record.oid, 'EXECUTE'
               )
               AND NOT pg_catalog.has_function_privilege(
                   'authenticated', procedure_record.oid, 'EXECUTE'
               )
               AND NOT pg_catalog.has_function_privilege(
                   'authenticator', procedure_record.oid, 'EXECUTE'
               )
               AND pg_catalog.has_function_privilege(
                   'service_role', procedure_record.oid, 'EXECUTE'
               )
        ) THEN
            RETURN false;
        END IF;
    END LOOP;

    RETURN true;
END;
$function$;

ALTER FUNCTION public.verify_fase09_7_leads_email_security_hold()
OWNER TO postgres;
REVOKE ALL ON FUNCTION public.verify_fase09_7_leads_email_security_hold()
FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.verify_fase09_7_leads_email_security_hold()
TO service_role;

-- security-hold-stage-verifier-complete

DO $security_hold_verify$
BEGIN
    IF public.verify_fase09_7_leads_email_security_hold() IS NOT TRUE THEN
        RAISE EXCEPTION 'F9.7 security hold verifier failed'
            USING ERRCODE = '55000';
    END IF;
END;
$security_hold_verify$;

-- security-hold-stage-postcondition-complete
