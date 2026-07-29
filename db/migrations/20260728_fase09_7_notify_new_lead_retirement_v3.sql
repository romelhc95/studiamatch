-- F9.7 v3 forward-only retirement of the unapproved lead notification path.
-- Accepts only versioned historical variants reconstructed offline on PG17.

SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path = '';

LOCK TABLE public.leads IN ACCESS EXCLUSIVE MODE;

DO $retirement_guard$
DECLARE
    function_count integer;
    function_record record;
    trigger_record record;
    leads_oid oid := 'public.leads'::regclass;
    service_role_oid oid;
    notify_oid oid;
    prosrc_lf text;
    definition_lf text;
    prosrc_normalized text;
    definition_normalized text;
    prosrc_redacted text;
    definition_redacted text;
    prosrc_normalized_redacted text;
    definition_normalized_redacted text;
    url_pattern text := 'https://[a-z0-9]{20}[.]' || 'supabase[.]co/' ||
        'functions' || '/v1/' || 'send-lead-' || 'emails';
    url_redaction text := 'https://<project-ref>.' || 'supabase' || '.co/' ||
        'functions' || '/v1/' || 'send-lead-' || 'emails';
    secure_trigger_exact boolean;
    secure_trigger_project_ref boolean;
    email_infrastructure_exact boolean;
    absent_clean boolean := false;
BEGIN
    IF pg_catalog.current_setting('server_version_num')::integer < 170000
       OR pg_catalog.current_setting('server_version_num')::integer >= 180000
       OR pg_catalog.to_regprocedure(
           'public.verify_fase09_7_public_access_closure()'
       ) IS NULL
       OR public.verify_fase09_7_public_access_closure() IS NOT TRUE THEN
        RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
            USING ERRCODE = '55000';
    END IF;

    SELECT role.oid
    INTO service_role_oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'service_role';

    IF service_role_oid IS NULL THEN
        RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
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
                     AND acl.grantee = service_role_oid
               ) = 1
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.pg_depend AS dependency
                   WHERE dependency.classid =
                         'pg_catalog.pg_proc'::pg_catalog.regclass
                     AND dependency.objid = procedure_record.oid
                     AND dependency.objsubid = 0
               ) = 2
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.pg_depend AS dependency
                   WHERE dependency.classid =
                         'pg_catalog.pg_proc'::pg_catalog.regclass
                     AND dependency.objid = procedure_record.oid
                     AND dependency.objsubid = 0
                     AND dependency.refclassid =
                         'pg_catalog.pg_namespace'::pg_catalog.regclass
                     AND dependency.refobjid = procedure_record.pronamespace
                     AND dependency.refobjsubid = 0
                     AND dependency.deptype = 'n'
               ) = 1
               AND (
                   SELECT pg_catalog.count(*)
                   FROM pg_catalog.pg_depend AS dependency
                   WHERE dependency.classid =
                         'pg_catalog.pg_proc'::pg_catalog.regclass
                     AND dependency.objid = procedure_record.oid
                     AND dependency.objsubid = 0
                     AND dependency.refclassid =
                         'pg_catalog.pg_language'::pg_catalog.regclass
                     AND dependency.refobjid = procedure_record.prolang
                     AND dependency.refobjsubid = 0
                     AND dependency.deptype = 'n'
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
          AND procedure_record.proname = 'verify_fase09_7_public_access_closure'
    ) THEN
        RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
            USING ERRCODE = '55000';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace
          ON namespace.oid = procedure_record.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure_record.proname =
              'verify_fase09_7_notify_new_lead_retirement'
    ) THEN
        RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
            USING ERRCODE = '55000';
    END IF;

    SELECT pg_catalog.count(*)::integer
    INTO function_count
    FROM pg_catalog.pg_proc AS procedure_record
    JOIN pg_catalog.pg_namespace AS namespace
      ON namespace.oid = procedure_record.pronamespace
    WHERE namespace.nspname = 'public'
      AND procedure_record.proname = 'notify_new_lead';

    IF function_count = 0 THEN
        IF EXISTS (
            SELECT 1
            FROM pg_catalog.pg_trigger AS trigger_candidate
            WHERE NOT trigger_candidate.tgisinternal
              AND (
                  trigger_candidate.tgrelid = leads_oid
                  OR trigger_candidate.tgname = 'trg_notify_new_lead'
              )
        ) THEN
            RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
                USING ERRCODE = '55000';
        END IF;
        absent_clean := true;
    ELSIF function_count <> 1 THEN
        RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
            USING ERRCODE = '55000';
    END IF;

    IF NOT absent_clean THEN
        notify_oid := pg_catalog.to_regprocedure('public.notify_new_lead()');
        IF notify_oid IS NULL THEN
            RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
                USING ERRCODE = '55000';
        END IF;

        SELECT
            procedure_record.oid,
            procedure_record.pronamespace,
            procedure_record.prolang,
            procedure_record.proowner,
            procedure_record.proacl,
            procedure_record.prokind,
            procedure_record.prosecdef,
            procedure_record.provolatile,
            procedure_record.proisstrict,
            procedure_record.proleakproof,
            procedure_record.proparallel,
            procedure_record.proretset,
            procedure_record.pronargs,
            procedure_record.pronargdefaults,
            procedure_record.proconfig,
            procedure_record.prosrc,
            owner.rolname AS owner_name,
            language_record.lanname AS language_name,
            return_type.typname AS return_type_name,
            return_namespace.nspname AS return_type_namespace,
            pg_catalog.pg_get_functiondef(procedure_record.oid) AS definition
        INTO STRICT function_record
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_roles AS owner
          ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record
          ON language_record.oid = procedure_record.prolang
        JOIN pg_catalog.pg_type AS return_type
          ON return_type.oid = procedure_record.prorettype
        JOIN pg_catalog.pg_namespace AS return_namespace
          ON return_namespace.oid = return_type.typnamespace
        WHERE procedure_record.oid = notify_oid;

        prosrc_lf := pg_catalog.replace(function_record.prosrc, E'\r\n', E'\n');
        definition_lf := pg_catalog.replace(
            function_record.definition, E'\r\n', E'\n'
        );
        prosrc_normalized := pg_catalog.btrim(pg_catalog.regexp_replace(
            function_record.prosrc, E'\\s+', ' ', 'g'
        ));
        definition_normalized := pg_catalog.btrim(pg_catalog.regexp_replace(
            function_record.definition, E'\\s+', ' ', 'g'
        ));
        prosrc_redacted := pg_catalog.regexp_replace(
            prosrc_lf, url_pattern, url_redaction, 'g'
        );
        definition_redacted := pg_catalog.regexp_replace(
            definition_lf, url_pattern, url_redaction, 'g'
        );
        prosrc_normalized_redacted := pg_catalog.regexp_replace(
            prosrc_normalized, url_pattern, url_redaction, 'g'
        );
        definition_normalized_redacted := pg_catalog.regexp_replace(
            definition_normalized, url_pattern, url_redaction, 'g'
        );

        secure_trigger_exact :=
            pg_catalog.octet_length(prosrc_lf) = 1251
            AND pg_catalog.octet_length(definition_lf) = 1423
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                prosrc_lf, 'UTF8'
            )), 'hex') = '5fa712326d4c331c074caabafc8957dc4edd3e85404ad31ad0f5f7304fc6b32e'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                prosrc_normalized, 'UTF8'
            )), 'hex') = '42dab6c9e511e61ad04f8dbd8bccf070e23b598d6877de1dd27865b4b2734ccc'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                definition_lf, 'UTF8'
            )), 'hex') = 'c05c403dc06c7a03379591de7bc729f6aa15366566aa5dcf6a00de2e7f3e0d12'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                definition_normalized, 'UTF8'
            )), 'hex') = '7844c0c19a151091d05ba33800013edc4709125725221bd313e59363f647d020';

        secure_trigger_project_ref :=
            pg_catalog.octet_length(prosrc_lf) = 1251
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                prosrc_redacted, 'UTF8'
            )), 'hex') = 'b0b03f57d6d6416f71cebc3fded4e715fbb34867c35c5616d9c6cb561e0ecd8c'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                prosrc_normalized_redacted, 'UTF8'
            )), 'hex') = '57b2644f3c023f18d10f696459704195d24a0c2cca2b3b5bdb9895b21d4a829c'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                definition_redacted, 'UTF8'
            )), 'hex') = '1f81d3a05c5b01dc459bb59a92ece636d34c490c681db3a82ce8ba67c6e99774'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                definition_normalized_redacted, 'UTF8'
            )), 'hex') = 'd1b5dba4a69b44926db4906401099603d0a511858f0d599d41ad18ceb683de56';

        email_infrastructure_exact :=
            pg_catalog.octet_length(prosrc_lf) = 954
            AND pg_catalog.octet_length(definition_lf) = 1126
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                prosrc_lf, 'UTF8'
            )), 'hex') = 'e802821baeabb39968b37529d14d889296b65bf34bdfce41dc0639f57f75bcf9'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                prosrc_normalized, 'UTF8'
            )), 'hex') = '79ac9190efc739367216aec867aa2119afa3085892aa2a9092fb080d83b9b753'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                definition_lf, 'UTF8'
            )), 'hex') = 'e23bf811d4c0f288a8e6d58fb1edcf8571c0348c8cc8697cbe4458dc76642164'
            AND pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                definition_normalized, 'UTF8'
            )), 'hex') = '04ef62b7aaea62d2653b8971114624829ba08a13c09eb3e4f4340b09e094ddc4';

        IF function_record.prokind <> 'f'
           OR function_record.language_name <> 'plpgsql'
           OR function_record.return_type_namespace <> 'pg_catalog'
           OR function_record.return_type_name <> 'trigger'
           OR NOT function_record.prosecdef
           OR function_record.provolatile <> 'v'
           OR function_record.proisstrict
           OR function_record.proleakproof
           OR function_record.proparallel <> 'u'
           OR function_record.proretset
           OR function_record.pronargs <> 0
           OR function_record.pronargdefaults <> 0
           OR function_record.owner_name <> 'postgres'
           OR function_record.proconfig IS DISTINCT FROM
              ARRAY['search_path=pg_catalog, public']::text[]
           OR NOT (
               secure_trigger_exact
               OR secure_trigger_project_ref
               OR email_infrastructure_exact
           )
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   function_record.proacl,
                   pg_catalog.acldefault('f', function_record.proowner)
               )) AS acl
           ) <> 2
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   function_record.proacl,
                   pg_catalog.acldefault('f', function_record.proowner)
               )) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND NOT acl.is_grantable
                 AND acl.grantee = function_record.proowner
           ) <> 1
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.aclexplode(COALESCE(
                   function_record.proacl,
                   pg_catalog.acldefault('f', function_record.proowner)
               )) AS acl
               WHERE acl.privilege_type = 'EXECUTE'
                 AND NOT acl.is_grantable
                 AND acl.grantee = service_role_oid
           ) <> 1 THEN
            RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
                USING ERRCODE = '55000';
        END IF;

        IF (
            SELECT pg_catalog.count(*)
            FROM pg_catalog.pg_depend AS dependency
            WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
              AND dependency.objid = notify_oid
              AND dependency.objsubid = 0
        ) <> 2
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.objid = notify_oid
                 AND dependency.objsubid = 0
                 AND dependency.refclassid =
                     'pg_catalog.pg_namespace'::pg_catalog.regclass
                 AND dependency.refobjid = function_record.pronamespace
                 AND dependency.refobjsubid = 0
                 AND dependency.deptype = 'n'
           ) <> 1
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.objid = notify_oid
                 AND dependency.objsubid = 0
                 AND dependency.refclassid =
                     'pg_catalog.pg_language'::pg_catalog.regclass
                 AND dependency.refobjid = function_record.prolang
                 AND dependency.refobjsubid = 0
                 AND dependency.deptype = 'n'
           ) <> 1 THEN
            RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
                USING ERRCODE = '55000';
        END IF;

        IF (
            SELECT pg_catalog.count(*)
            FROM pg_catalog.pg_trigger AS trigger_candidate
            WHERE NOT trigger_candidate.tgisinternal
              AND (
                  trigger_candidate.tgrelid = leads_oid
                  OR trigger_candidate.tgname = 'trg_notify_new_lead'
                  OR trigger_candidate.tgfoid = notify_oid
              )
        ) <> 1 THEN
            RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
                USING ERRCODE = '55000';
        END IF;

        SELECT trigger_candidate.*
        INTO STRICT trigger_record
        FROM pg_catalog.pg_trigger AS trigger_candidate
        WHERE NOT trigger_candidate.tgisinternal
          AND trigger_candidate.tgrelid = leads_oid
          AND trigger_candidate.tgname = 'trg_notify_new_lead'
          AND trigger_candidate.tgfoid = notify_oid;

        IF trigger_record.tgtype <> 5
           OR trigger_record.tgenabled <> 'O'
           OR trigger_record.tgconstraint <> 0
           OR trigger_record.tgconstrrelid <> 0
           OR trigger_record.tgdeferrable
           OR trigger_record.tginitdeferred
           OR trigger_record.tgnargs <> 0
           OR pg_catalog.octet_length(trigger_record.tgargs) <> 0
           OR trigger_record.tgqual IS NOT NULL
           OR trigger_record.tgoldtable IS NOT NULL
           OR trigger_record.tgnewtable IS NOT NULL
           OR trigger_record.tgparentid <> 0
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid = 'pg_catalog.pg_trigger'::pg_catalog.regclass
                 AND dependency.objid = trigger_record.oid
                 AND dependency.objsubid = 0
           ) <> 2
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid = 'pg_catalog.pg_trigger'::pg_catalog.regclass
                 AND dependency.objid = trigger_record.oid
                 AND dependency.objsubid = 0
                 AND dependency.refclassid = 'pg_catalog.pg_class'::pg_catalog.regclass
                 AND dependency.refobjid = leads_oid
                 AND dependency.refobjsubid = 0
                 AND dependency.deptype = 'a'
           ) <> 1
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.classid = 'pg_catalog.pg_trigger'::pg_catalog.regclass
                 AND dependency.objid = trigger_record.oid
                 AND dependency.objsubid = 0
                 AND dependency.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.refobjid = notify_oid
                 AND dependency.refobjsubid = 0
                 AND dependency.deptype = 'n'
           ) <> 1
           OR (
               SELECT pg_catalog.count(*)
               FROM pg_catalog.pg_depend AS dependency
               WHERE dependency.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                 AND dependency.refobjid = notify_oid
                 AND dependency.refobjsubid = 0
           ) <> 1 THEN
            RAISE EXCEPTION 'F9.7 trigger retirement precondition failed'
                USING ERRCODE = '55000';
        END IF;
    END IF;
END;
$retirement_guard$;

DO $retirement_drop$
BEGIN
    IF pg_catalog.to_regprocedure('public.notify_new_lead()') IS NOT NULL THEN
        DROP TRIGGER trg_notify_new_lead ON public.leads;
        DROP FUNCTION public.notify_new_lead();
    END IF;
END;
$retirement_drop$;

CREATE FUNCTION public.verify_fase09_7_notify_new_lead_retirement()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $function$
    SELECT
        pg_catalog.current_setting('server_version_num')::integer >= 170000
        AND pg_catalog.current_setting('server_version_num')::integer < 180000
        AND public.verify_fase09_7_public_access_closure() IS TRUE
        AND (
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
                   AND (
                       SELECT pg_catalog.count(*)
                       FROM pg_catalog.pg_depend AS dependency
                       WHERE dependency.classid =
                             'pg_catalog.pg_proc'::pg_catalog.regclass
                         AND dependency.objid = procedure_record.oid
                         AND dependency.objsubid = 0
                         AND dependency.refclassid =
                             'pg_catalog.pg_namespace'::pg_catalog.regclass
                         AND dependency.refobjid = procedure_record.pronamespace
                         AND dependency.refobjsubid = 0
                         AND dependency.deptype = 'n'
                   ) = 1
                   AND (
                       SELECT pg_catalog.count(*)
                       FROM pg_catalog.pg_depend AS dependency
                       WHERE dependency.classid =
                             'pg_catalog.pg_proc'::pg_catalog.regclass
                         AND dependency.objid = procedure_record.oid
                         AND dependency.objsubid = 0
                         AND dependency.refclassid =
                             'pg_catalog.pg_language'::pg_catalog.regclass
                         AND dependency.refobjid = procedure_record.prolang
                         AND dependency.refobjsubid = 0
                         AND dependency.deptype = 'n'
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
              AND procedure_record.proname = 'verify_fase09_7_public_access_closure'
        )
        AND NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_proc AS procedure_record
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = procedure_record.pronamespace
            WHERE namespace.nspname = 'public'
              AND procedure_record.proname = 'notify_new_lead'
        )
        AND NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_trigger AS trigger_record
            WHERE NOT trigger_record.tgisinternal
              AND (
                  trigger_record.tgrelid = 'public.leads'::regclass
                  OR trigger_record.tgname = 'trg_notify_new_lead'
              )
        );
$function$;

ALTER FUNCTION public.verify_fase09_7_notify_new_lead_retirement()
OWNER TO postgres;
REVOKE ALL ON FUNCTION public.verify_fase09_7_notify_new_lead_retirement()
FROM PUBLIC, anon, authenticated, service_role CASCADE;
GRANT EXECUTE ON FUNCTION public.verify_fase09_7_notify_new_lead_retirement()
TO service_role;
