\set ON_ERROR_STOP on

\if :{?FASE097_MATRIX_SENTINEL}
\else
\echo 'FASE097_MATRIX_SENTINEL is required'
\quit 1
\endif

SET application_name = :'FASE097_MATRIX_SENTINEL';

DO $fixture_guard$
BEGIN
    IF pg_catalog.current_database() <> 'studiamatch_f97'
       OR pg_catalog.current_setting('server_version_num')::integer < 170000
       OR pg_catalog.current_setting('server_version_num')::integer >= 180000
       OR pg_catalog.current_setting('application_name') !~
          '^fase09_7_notify_matrix_[a-z0-9_]+$' THEN
        RAISE EXCEPTION 'F9.7 offline notify matrix requires ephemeral PostgreSQL 17 studiamatch_f97 database and session sentinel'
            USING ERRCODE = '55000';
    END IF;
END;
$fixture_guard$;

CREATE TEMP TABLE IF NOT EXISTS notify_variant_summary (
    variant_name text PRIMARY KEY,
    expected_route_class text NOT NULL,
    actual_route_class text NOT NULL,
    package_applied boolean NOT NULL,
    prosrc_lf_sha256 text,
    prosrc_normalized_sha256 text,
    prosrc_redacted_sha256 text,
    prosrc_normalized_redacted_sha256 text,
    definition_lf_sha256 text,
    definition_normalized_sha256 text,
    definition_redacted_sha256 text,
    definition_normalized_redacted_sha256 text,
    prosrc_lf_octets integer,
    definition_lf_octets integer,
    metadata_exact boolean NOT NULL,
    owner_exact boolean NOT NULL,
    search_path_exact boolean NOT NULL,
    acl_exact_after_fixture boolean NOT NULL,
    dependency_exact boolean NOT NULL,
    trigger_exact boolean NOT NULL,
    function_trigger_reference_count integer NOT NULL,
    egress_category text NOT NULL
) ON COMMIT PRESERVE ROWS;

CREATE OR REPLACE FUNCTION pg_temp.capture_notify_variant(
    p_variant_name text,
    p_expected_route_class text,
    p_actual_route_class text,
    p_package_applied boolean
)
RETURNS void
LANGUAGE plpgsql
SET search_path = ''
AS $function$
DECLARE
    function_record record;
    service_role_oid oid;
    prosrc_lf text;
    definition_lf text;
    prosrc_normalized text;
    definition_normalized text;
    url_pattern text := 'https://[a-z0-9]{20}[.]' || 'supabase[.]co/' ||
        'functions' || '/v1/' || 'send-lead-' || 'emails';
    url_redaction text := 'https://<project-ref>.' || 'supabase' || '.co/' ||
        'functions' || '/v1/' || 'send-lead-' || 'emails';
BEGIN
    SELECT role.oid
    INTO service_role_oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'service_role';

    SELECT
        procedure_record.oid,
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
    INTO function_record
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
      AND procedure_record.proname = 'notify_new_lead'
      AND procedure_record.prokind = 'f'
      AND procedure_record.pronargs = 0;

    IF function_record.oid IS NULL THEN
        INSERT INTO notify_variant_summary (
            variant_name, expected_route_class, actual_route_class,
            package_applied, metadata_exact, owner_exact, search_path_exact,
            acl_exact_after_fixture, dependency_exact, trigger_exact,
            function_trigger_reference_count, egress_category
        ) VALUES (
            p_variant_name, p_expected_route_class, p_actual_route_class,
            p_package_applied, true, true, true, true, true, true, 0,
            'absent_clean'
        ) ON CONFLICT (variant_name) DO UPDATE SET
            actual_route_class = EXCLUDED.actual_route_class,
            package_applied = EXCLUDED.package_applied;
        RETURN;
    END IF;

    prosrc_lf := pg_catalog.replace(function_record.prosrc, E'\r\n', E'\n');
    definition_lf := pg_catalog.replace(function_record.definition, E'\r\n', E'\n');
    prosrc_normalized := pg_catalog.btrim(pg_catalog.regexp_replace(
        function_record.prosrc, E'\\s+', ' ', 'g'
    ));
    definition_normalized := pg_catalog.btrim(pg_catalog.regexp_replace(
        function_record.definition, E'\\s+', ' ', 'g'
    ));

    INSERT INTO notify_variant_summary
    SELECT
        p_variant_name,
        p_expected_route_class,
        p_actual_route_class,
        p_package_applied,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            prosrc_lf, 'UTF8'
        )), 'hex'),
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            prosrc_normalized, 'UTF8'
        )), 'hex'),
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(prosrc_lf, url_pattern, url_redaction, 'g'),
            'UTF8'
        )), 'hex'),
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(
                prosrc_normalized, url_pattern, url_redaction, 'g'
            ),
            'UTF8'
        )), 'hex'),
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            definition_lf, 'UTF8'
        )), 'hex'),
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            definition_normalized, 'UTF8'
        )), 'hex'),
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(
                definition_lf, url_pattern, url_redaction, 'g'
            ),
            'UTF8'
        )), 'hex'),
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(
                definition_normalized, url_pattern, url_redaction, 'g'
            ),
            'UTF8'
        )), 'hex'),
        pg_catalog.octet_length(prosrc_lf),
        pg_catalog.octet_length(definition_lf),
        function_record.prokind = 'f'
            AND function_record.language_name = 'plpgsql'
            AND function_record.return_type_namespace = 'pg_catalog'
            AND function_record.return_type_name = 'trigger'
            AND function_record.prosecdef
            AND function_record.provolatile = 'v'
            AND NOT function_record.proisstrict
            AND NOT function_record.proleakproof
            AND function_record.proparallel = 'u'
            AND NOT function_record.proretset
            AND function_record.pronargs = 0
            AND function_record.pronargdefaults = 0,
        function_record.owner_name = 'postgres',
        function_record.proconfig IS NOT DISTINCT FROM
            ARRAY['search_path=pg_catalog, public']::text[],
        (
            SELECT pg_catalog.count(*)
            FROM pg_catalog.aclexplode(COALESCE(
                function_record.proacl,
                pg_catalog.acldefault('f', function_record.proowner)
            )) AS acl
        ) = 2
            AND (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.aclexplode(COALESCE(
                    function_record.proacl,
                    pg_catalog.acldefault('f', function_record.proowner)
                )) AS acl
                WHERE acl.privilege_type = 'EXECUTE'
                  AND NOT acl.is_grantable
                  AND acl.grantee = function_record.proowner
            ) = 1
            AND (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.aclexplode(COALESCE(
                    function_record.proacl,
                    pg_catalog.acldefault('f', function_record.proowner)
                )) AS acl
                WHERE acl.privilege_type = 'EXECUTE'
                  AND NOT acl.is_grantable
                  AND acl.grantee = service_role_oid
            ) = 1,
        (
            SELECT pg_catalog.count(*)
            FROM pg_catalog.pg_depend AS dependency
            WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
              AND dependency.objid = function_record.oid
              AND dependency.objsubid = 0
        ) = 2,
        (
            SELECT pg_catalog.count(*) = 1
               AND pg_catalog.bool_and(
                   trigger_record.tgtype = 5
                   AND trigger_record.tgenabled = 'O'
                   AND trigger_record.tgrelid = 'public.leads'::regclass
                   AND trigger_record.tgname = 'trg_notify_new_lead'
                   AND trigger_record.tgfoid = function_record.oid
               )
            FROM pg_catalog.pg_trigger AS trigger_record
            WHERE NOT trigger_record.tgisinternal
              AND (
                  trigger_record.tgrelid = 'public.leads'::regclass
                  OR trigger_record.tgname = 'trg_notify_new_lead'
                  OR trigger_record.tgfoid = function_record.oid
              )
        ),
        (
            SELECT pg_catalog.count(*)::integer
            FROM pg_catalog.pg_depend AS dependency
            WHERE dependency.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
              AND dependency.refobjid = function_record.oid
              AND dependency.refobjsubid = 0
        ),
        CASE
            WHEN prosrc_lf ~ 'current_setting[(]''app[.]settings[.]anon_key''' THEN
                'historical_settings_auth_header'
            WHEN prosrc_lf ~ url_pattern
                 AND prosrc_lf ~ 'net[.]http_post'
                 AND prosrc_lf ~ 'to_jsonb[(]NEW[)]' THEN
                'historical_project_ref_edge_no_auth'
            ELSE 'unknown'
        END
    ON CONFLICT (variant_name) DO UPDATE SET
        actual_route_class = EXCLUDED.actual_route_class,
        package_applied = EXCLUDED.package_applied;
END;
$function$;

SELECT *
FROM notify_variant_summary
ORDER BY variant_name;
