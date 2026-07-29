WITH
expected_ledger(ordinal, migration_name, checksum_marker) AS (
    VALUES
        (1, '20260724_fase06_g1b_reconciliation', 'sha256:d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df'),
        (2, '20260724_fase06_hito1_editorial_contract', 'sha256:b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a'),
        (3, '20260725_fase07_g1b_closure', 'sha256:9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120'),
        (4, '20260725_fase08_hito1_functional_closure', 'sha256:7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527'),
        (5, '20260727_fase09_7_public_access_closure', 'sha256:040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b'),
        (6, '20260728_fase09_7_notify_new_lead_retirement_v3', 'sha256:f1fd6e618bd16ff4216f46587ce897756e465ada92ee9bc398335cd9239fe188')
),
service_role_oid AS (
    SELECT role.oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'service_role'
),
notify_rows AS (
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
),
notify_one AS (
    SELECT *
    FROM notify_rows
    WHERE prokind = 'f'
      AND pronargs = 0
      AND return_type_namespace = 'pg_catalog'
      AND return_type_name = 'trigger'
    LIMIT 1
),
digest_material AS (
    SELECT
        pg_catalog.replace(prosrc, E'\r\n', E'\n') AS prosrc_lf,
        pg_catalog.replace(definition, E'\r\n', E'\n') AS definition_lf,
        pg_catalog.btrim(pg_catalog.regexp_replace(
            prosrc, E'\\s+', ' ', 'g'
        )) AS prosrc_normalized,
        pg_catalog.btrim(pg_catalog.regexp_replace(
            definition, E'\\s+', ' ', 'g'
        )) AS definition_normalized,
        'https://[a-z0-9]{20}[.]' || 'supabase[.]co/' ||
            'functions' || '/v1/' || 'send-lead-' || 'emails'
            AS url_pattern,
        'https://<project-ref>.' || 'supabase' || '.co/' ||
            'functions' || '/v1/' || 'send-lead-' || 'emails'
            AS url_redaction
    FROM notify_one
),
hash_flags AS (
    SELECT
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            prosrc_lf, 'UTF8'
        )), 'hex') AS prosrc_lf_sha256,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            prosrc_normalized, 'UTF8'
        )), 'hex') AS prosrc_normalized_sha256,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            definition_lf, 'UTF8'
        )), 'hex') AS definition_lf_sha256,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            definition_normalized, 'UTF8'
        )), 'hex') AS definition_normalized_sha256,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(prosrc_lf, url_pattern, url_redaction, 'g'),
            'UTF8'
        )), 'hex') AS prosrc_redacted_sha256,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(
                prosrc_normalized, url_pattern, url_redaction, 'g'
            ),
            'UTF8'
        )), 'hex') AS prosrc_normalized_redacted_sha256,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(
                definition_lf, url_pattern, url_redaction, 'g'
            ),
            'UTF8'
        )), 'hex') AS definition_redacted_sha256,
        pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
            pg_catalog.regexp_replace(
                definition_normalized, url_pattern, url_redaction, 'g'
            ),
            'UTF8'
        )), 'hex') AS definition_normalized_redacted_sha256
    FROM digest_material
),
source_variant AS (
    SELECT CASE
        WHEN NOT EXISTS (SELECT 1 FROM notify_one) THEN 'absent_clean'
        WHEN prosrc_lf_sha256 =
             '5fa712326d4c331c074caabafc8957dc4edd3e85404ad31ad0f5f7304fc6b32e'
         AND prosrc_normalized_sha256 =
             '42dab6c9e511e61ad04f8dbd8bccf070e23b598d6877de1dd27865b4b2734ccc'
         AND definition_lf_sha256 =
             'c05c403dc06c7a03379591de7bc729f6aa15366566aa5dcf6a00de2e7f3e0d12'
         AND definition_normalized_sha256 =
             '7844c0c19a151091d05ba33800013edc4709125725221bd313e59363f647d020'
            THEN 'secure_trigger_exact'
        WHEN prosrc_redacted_sha256 =
             'b0b03f57d6d6416f71cebc3fded4e715fbb34867c35c5616d9c6cb561e0ecd8c'
         AND prosrc_normalized_redacted_sha256 =
             '57b2644f3c023f18d10f696459704195d24a0c2cca2b3b5bdb9895b21d4a829c'
         AND definition_redacted_sha256 =
             '1f81d3a05c5b01dc459bb59a92ece636d34c490c681db3a82ce8ba67c6e99774'
         AND definition_normalized_redacted_sha256 =
             'd1b5dba4a69b44926db4906401099603d0a511858f0d599d41ad18ceb683de56'
            THEN 'secure_trigger_project_ref_redacted'
        WHEN prosrc_lf_sha256 =
             'e802821baeabb39968b37529d14d889296b65bf34bdfce41dc0639f57f75bcf9'
         AND prosrc_normalized_sha256 =
             '79ac9190efc739367216aec867aa2119afa3085892aa2a9092fb080d83b9b753'
         AND definition_lf_sha256 =
             'e23bf811d4c0f288a8e6d58fb1edcf8571c0348c8cc8697cbe4458dc76642164'
         AND definition_normalized_sha256 =
             '04ef62b7aaea62d2653b8971114624829ba08a13c09eb3e4f4340b09e094ddc4'
            THEN 'email_infrastructure_exact'
        ELSE 'unknown'
    END AS notify_source_variant
    FROM hash_flags
    UNION ALL
    SELECT 'absent_clean'
    WHERE NOT EXISTS (SELECT 1 FROM hash_flags)
),
shape AS (
    SELECT
        pg_catalog.current_setting('server_version_num')::integer >= 170000
            AND pg_catalog.current_setting('server_version_num')::integer < 180000
            AS pg17_semantics_supported,
        (SELECT pg_catalog.count(*)::integer FROM notify_rows)
            AS notify_named_routine_count,
        (SELECT pg_catalog.count(*)::integer
         FROM notify_rows
         WHERE prokind = 'f'
           AND pronargs = 0
           AND return_type_namespace = 'pg_catalog'
           AND return_type_name = 'trigger') AS notify_exact_signature_count,
        (SELECT pg_catalog.count(*)::integer
         FROM notify_rows
         WHERE NOT (
             prokind = 'f'
             AND pronargs = 0
             AND return_type_namespace = 'pg_catalog'
             AND return_type_name = 'trigger'
         )) AS notify_other_signature_count,
        COALESCE((SELECT owner_name = 'postgres' FROM notify_one), false)
            AS notify_owner_exact,
        COALESCE((SELECT proconfig IS NOT DISTINCT FROM
            ARRAY['search_path=pg_catalog, public']::text[]
            FROM notify_one), false) AS notify_search_path_exact,
        COALESCE((SELECT
            prokind = 'f'
            AND language_name = 'plpgsql'
            AND return_type_namespace = 'pg_catalog'
            AND return_type_name = 'trigger'
            AND prosecdef
            AND provolatile = 'v'
            AND NOT proisstrict
            AND NOT proleakproof
            AND proparallel = 'u'
            AND NOT proretset
            AND pronargs = 0
            AND pronargdefaults = 0
            FROM notify_one), false) AS notify_metadata_exact,
        COALESCE((SELECT
            (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.aclexplode(COALESCE(
                    proacl,
                    pg_catalog.acldefault('f', proowner)
                )) AS acl
            ) = 2
            AND (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.aclexplode(COALESCE(
                    proacl,
                    pg_catalog.acldefault('f', proowner)
                )) AS acl
                WHERE acl.privilege_type = 'EXECUTE'
                  AND NOT acl.is_grantable
                  AND acl.grantee = proowner
            ) = 1
            AND (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.aclexplode(COALESCE(
                    proacl,
                    pg_catalog.acldefault('f', proowner)
                )) AS acl
                WHERE acl.privilege_type = 'EXECUTE'
                  AND NOT acl.is_grantable
                  AND acl.grantee = (SELECT oid FROM service_role_oid)
            ) = 1
            FROM notify_one), false) AS notify_acl_exact_now,
        COALESCE((SELECT pg_catalog.count(*)::integer
            FROM notify_one AS selected_notify
            CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(
                selected_notify.proacl,
                pg_catalog.acldefault('f', selected_notify.proowner)
            )) AS acl
            WHERE acl.privilege_type <> 'EXECUTE'
               OR acl.is_grantable
               OR acl.grantee NOT IN (
                   selected_notify.proowner, (SELECT oid FROM service_role_oid)
               )), 0) AS notify_acl_unknown_entry_count,
        COALESCE((SELECT
            (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.pg_depend AS dependency
                WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                  AND dependency.objid = notify_one.oid
                  AND dependency.objsubid = 0
            ) = 2
            AND (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.pg_depend AS dependency
                WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                  AND dependency.objid = notify_one.oid
                  AND dependency.objsubid = 0
                  AND dependency.refclassid =
                      'pg_catalog.pg_namespace'::pg_catalog.regclass
                  AND dependency.refobjid = (
                      SELECT namespace.oid
                      FROM pg_catalog.pg_namespace AS namespace
                      WHERE namespace.nspname = 'public'
                  )
                  AND dependency.refobjsubid = 0
                  AND dependency.deptype = 'n'
            ) = 1
            AND (
                SELECT pg_catalog.count(*)
                FROM pg_catalog.pg_depend AS dependency
                WHERE dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
                  AND dependency.objid = notify_one.oid
                  AND dependency.objsubid = 0
                  AND dependency.refclassid =
                      'pg_catalog.pg_language'::pg_catalog.regclass
                  AND dependency.refobjid = notify_one.prolang
                  AND dependency.refobjsubid = 0
                  AND dependency.deptype = 'n'
            ) = 1
            FROM notify_one), false) AS notify_dependency_exact,
        COALESCE((SELECT pg_catalog.count(*) = 1
               AND pg_catalog.bool_and(
                   trigger_record.tgtype = 5
                   AND trigger_record.tgenabled = 'O'
                   AND trigger_record.tgconstraint = 0
                   AND trigger_record.tgconstrrelid = 0
                   AND NOT trigger_record.tgdeferrable
                   AND NOT trigger_record.tginitdeferred
                   AND trigger_record.tgnargs = 0
                   AND pg_catalog.octet_length(trigger_record.tgargs) = 0
                   AND trigger_record.tgqual IS NULL
                   AND trigger_record.tgoldtable IS NULL
                   AND trigger_record.tgnewtable IS NULL
                   AND trigger_record.tgparentid = 0
                   AND trigger_record.tgrelid = 'public.leads'::regclass
                   AND trigger_record.tgname = 'trg_notify_new_lead'
                   AND trigger_record.tgfoid = selected_notify.oid
               )
            FROM notify_one AS selected_notify
            CROSS JOIN LATERAL (
                SELECT *
                FROM pg_catalog.pg_trigger AS trigger_record
                WHERE NOT trigger_record.tgisinternal
                  AND (
                      trigger_record.tgrelid = 'public.leads'::regclass
                      OR trigger_record.tgname = 'trg_notify_new_lead'
                      OR trigger_record.tgfoid = selected_notify.oid
                  )
            ) AS trigger_record
            ), false) AS notify_trigger_exact,
        COALESCE((SELECT pg_catalog.count(*)::integer
            FROM notify_one AS selected_notify
            JOIN pg_catalog.pg_depend AS dependency
              ON dependency.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass
             AND dependency.refobjid = selected_notify.oid
             AND dependency.refobjsubid = 0), 0)
             AS notify_function_trigger_reference_count,
        NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_trigger AS trigger_record
            WHERE NOT trigger_record.tgisinternal
              AND (
                  trigger_record.tgrelid = 'public.leads'::regclass
                  OR trigger_record.tgname = 'trg_notify_new_lead'
              )
        ) AS absent_clean_trigger_surface_exact
),
ledger_state AS (
    SELECT
        EXISTS (
            SELECT 1
            FROM pg_catalog.pg_class AS relation
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE namespace.nspname = 'public'
              AND relation.relname = 'supabase_migrations'
        ) AS ledger_table_present
),
ledger_rows AS (
    SELECT
        migration.name,
        migration.statements
    FROM public.supabase_migrations AS migration
    WHERE (SELECT ledger_table_present FROM ledger_state)
),
ledger_name_counts AS (
    SELECT
        ledger.name,
        pg_catalog.count(*)::integer AS name_count
    FROM ledger_rows AS ledger
    GROUP BY ledger.name
),
ledger_expected_state AS (
    SELECT
        expected.ordinal,
        expected.migration_name,
        expected.checksum_marker,
        ledger.name IS NOT NULL AS is_present,
        ledger.statements IS NOT DISTINCT FROM expected.checksum_marker AS is_exact,
        COALESCE(name_counts.name_count, 0) AS name_count
    FROM expected_ledger AS expected
    LEFT JOIN ledger_rows AS ledger
      ON ledger.name = expected.migration_name
    LEFT JOIN ledger_name_counts AS name_counts
      ON name_counts.name = expected.migration_name
),
ledger_class AS (
    SELECT
        (SELECT ledger_table_present FROM ledger_state) AS ledger_table_present,
        COALESCE((
            SELECT pg_catalog.count(*)::integer
            FROM ledger_expected_state
            WHERE is_exact
        ), 0) AS exact_count,
        COALESCE((
            SELECT pg_catalog.count(*)::integer
            FROM ledger_expected_state
            WHERE is_present AND NOT is_exact
        ), 0) AS checksum_drift_count,
        COALESCE((
            SELECT pg_catalog.count(*)::integer
            FROM ledger_expected_state
            WHERE name_count > 1
        ), 0) AS duplicate_count,
        COALESCE((
            SELECT pg_catalog.max(candidate.ordinal)
            FROM ledger_expected_state AS candidate
            WHERE NOT EXISTS (
                SELECT 1
                FROM ledger_expected_state AS required
                WHERE required.ordinal <= candidate.ordinal
                  AND NOT required.is_exact
            )
        ), 0)::integer AS boundary_count,
        COALESCE((
            SELECT pg_catalog.count(*)::integer
            FROM ledger_expected_state AS expected
            WHERE expected.is_exact
              AND expected.ordinal > COALESCE((
                  SELECT pg_catalog.max(candidate.ordinal)
                  FROM ledger_expected_state AS candidate
                  WHERE NOT EXISTS (
                      SELECT 1
                      FROM ledger_expected_state AS required
                      WHERE required.ordinal <= candidate.ordinal
                        AND NOT required.is_exact
                  )
              ), 0)
        ), 0) AS gap_count,
        COALESCE((
            SELECT pg_catalog.count(*)::integer
            FROM ledger_rows
            WHERE name = '20260727_fase09_7_notify_new_lead_retirement'
        ), 0) AS v2_stem_count,
        COALESCE((
            SELECT pg_catalog.count(*)::integer
            FROM ledger_rows
            WHERE name IN (
                '20260726_fase09_5_rls_canary_reconciliation',
                '20260726_fase09_5_policy_inventory_reconciliation'
            )
        ), 0) AS f95_stem_count
),
public_access_verifier AS (
    SELECT
        COALESCE((
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
                         AND acl.grantee = (SELECT oid FROM service_role_oid)
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
        ), false) AS public_access_verifier_exact
),
retirement_verifier AS (
    SELECT
        COALESCE((
            SELECT pg_catalog.count(*)::integer
            FROM pg_catalog.pg_proc AS procedure_record
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = procedure_record.pronamespace
            WHERE namespace.nspname = 'public'
              AND procedure_record.proname =
                  'verify_fase09_7_notify_new_lead_retirement'
        ), 0) AS retirement_verifier_count,
        COALESCE((
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
                         AND acl.grantee = (SELECT oid FROM service_role_oid)
                   ) = 1
                   AND (
                       SELECT pg_catalog.count(*)
                       FROM pg_catalog.pg_depend AS dependency
                       WHERE dependency.classid =
                             'pg_catalog.pg_proc'::pg_catalog.regclass
                         AND dependency.objid = procedure_record.oid
                         AND dependency.objsubid = 0
                   ) = 1
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
              AND procedure_record.proname =
                  'verify_fase09_7_notify_new_lead_retirement'
        ), false) AS retirement_verifier_shape_exact
),
decision AS (
    SELECT
        shape.*,
        ledger_class.boundary_count,
        ledger_class.ledger_table_present,
        ledger_class.exact_count,
        ledger_class.checksum_drift_count,
        ledger_class.duplicate_count,
        ledger_class.gap_count,
        ledger_class.v2_stem_count,
        ledger_class.f95_stem_count,
        COALESCE((SELECT oid IS NOT NULL FROM service_role_oid), false)
            AS service_role_present,
        public_access_verifier.public_access_verifier_exact,
        retirement_verifier.retirement_verifier_count,
        retirement_verifier.retirement_verifier_shape_exact,
        source_variant.notify_source_variant,
        source_variant.notify_source_variant IN (
            'secure_trigger_exact',
            'secure_trigger_project_ref_redacted',
            'email_infrastructure_exact',
            'absent_clean'
        ) AS notify_source_reviewed,
        shape.notify_acl_exact_now AS notify_acl_repairable_by_prefix,
        ledger_class.ledger_table_present
            AND ledger_class.checksum_drift_count = 0
            AND ledger_class.duplicate_count = 0
            AND ledger_class.gap_count = 0
            AND ledger_class.exact_count = ledger_class.boundary_count
            AND ledger_class.boundary_count IN (0, 3, 4, 5, 6)
            AS ledger_boundary_exact,
        source_variant.notify_source_variant = 'secure_trigger_exact'
            AND shape.notify_metadata_exact
            AND shape.notify_owner_exact
            AND shape.notify_search_path_exact
            AND shape.notify_acl_exact_now
            AND shape.notify_dependency_exact
            AND shape.notify_trigger_exact
            AND shape.notify_function_trigger_reference_count = 1
            AS v2_guard_exact_now,
        source_variant.notify_source_variant = 'secure_trigger_exact'
            AND shape.notify_metadata_exact
            AND shape.notify_owner_exact
            AND shape.notify_search_path_exact
            AND shape.notify_acl_exact_now
            AND shape.notify_dependency_exact
            AND shape.notify_trigger_exact
            AND shape.notify_function_trigger_reference_count = 1
            AS v2_guard_expected_after_prefix,
        source_variant.notify_source_variant IN (
            'secure_trigger_exact',
            'secure_trigger_project_ref_redacted',
            'email_infrastructure_exact',
            'absent_clean'
        )
            AND shape.pg17_semantics_supported
            AND COALESCE((SELECT oid IS NOT NULL FROM service_role_oid), false)
            AND ledger_class.v2_stem_count = 0
            AND ledger_class.f95_stem_count = 0
            AND ledger_class.ledger_table_present
            AND ledger_class.checksum_drift_count = 0
            AND ledger_class.duplicate_count = 0
            AND ledger_class.gap_count = 0
            AND ledger_class.exact_count = ledger_class.boundary_count
            AND ledger_class.boundary_count IN (0, 3, 4, 5, 6)
            AND (
                ledger_class.boundary_count < 5
                OR public_access_verifier.public_access_verifier_exact
            )
            AND (
                ledger_class.boundary_count = 6
                OR retirement_verifier.retirement_verifier_count = 0
            )
            AND (
                ledger_class.boundary_count <> 6
                OR retirement_verifier.retirement_verifier_shape_exact
            )
            AND shape.notify_named_routine_count <= 1
            AND shape.notify_other_signature_count = 0
            AND (
                (
                    source_variant.notify_source_variant = 'absent_clean'
                    AND ledger_class.boundary_count <> 0
                    AND shape.absent_clean_trigger_surface_exact
                )
                OR (
                    shape.notify_exact_signature_count = 1
                    AND shape.notify_metadata_exact
                    AND shape.notify_owner_exact
                    AND shape.notify_search_path_exact
                    AND shape.notify_acl_exact_now
                    AND shape.notify_acl_unknown_entry_count = 0
                    AND shape.notify_dependency_exact
                    AND shape.notify_trigger_exact
                    AND shape.notify_function_trigger_reference_count = 1
                )
            ) AS successor_guard_eligible
    FROM shape, source_variant, ledger_class, public_access_verifier,
         retirement_verifier
),
classification AS (
    SELECT CASE
        WHEN NOT pg17_semantics_supported THEN 'STOP_PG_VERSION'
        WHEN NOT ledger_table_present THEN 'STOP_LEDGER_TABLE_ABSENT'
        WHEN v2_stem_count <> 0 THEN 'STOP_F9_7_V2_STEM'
        WHEN f95_stem_count <> 0 THEN 'STOP_F9_5_HISTORICAL_NON_PROMOTABLE'
        WHEN checksum_drift_count <> 0 THEN 'STOP_LEDGER_CHECKSUM_DRIFT'
        WHEN duplicate_count <> 0 THEN 'STOP_LEDGER_DUPLICATE'
        WHEN gap_count <> 0 THEN 'STOP_LEDGER_GAP'
        WHEN boundary_count NOT IN (0, 3, 4, 5, 6)
          OR exact_count <> boundary_count THEN 'STOP_LEDGER_BOUNDARY'
        WHEN NOT service_role_present THEN 'STOP_SERVICE_ROLE_ABSENT'
        WHEN boundary_count >= 5 AND NOT public_access_verifier_exact
            THEN 'STOP_PUBLIC_ACCESS_VERIFIER_DRIFT'
        WHEN boundary_count < 6 AND retirement_verifier_count <> 0
            THEN 'STOP_RETIREMENT_VERIFIER_COLLISION'
        WHEN boundary_count = 6 AND NOT retirement_verifier_shape_exact
            THEN 'STOP_RETIREMENT_VERIFIER_DRIFT'
        WHEN notify_named_routine_count = 0 AND NOT absent_clean_trigger_surface_exact THEN 'STOP_TRIGGER_DRIFT'
        WHEN notify_named_routine_count = 0 AND boundary_count = 0 THEN 'STOP_ABSENT_CLEAN_BOUNDARY_0'
        WHEN successor_guard_eligible THEN 'SUCCESSOR_V3_ELIGIBLE'
        WHEN notify_named_routine_count <> 1
          OR notify_exact_signature_count <> 1
          OR notify_other_signature_count <> 0 THEN 'STOP_OVERLOAD_OR_SIGNATURE'
        WHEN notify_source_variant = 'unknown' THEN 'STOP_UNKNOWN_SOURCE'
        WHEN NOT notify_metadata_exact THEN 'STOP_METADATA_DRIFT'
        WHEN NOT notify_owner_exact THEN 'STOP_OWNER_DRIFT'
        WHEN NOT notify_search_path_exact THEN 'STOP_SEARCH_PATH_DRIFT'
        WHEN NOT notify_acl_exact_now
          OR notify_acl_unknown_entry_count <> 0 THEN 'STOP_ACL_DRIFT'
        WHEN NOT notify_dependency_exact
          OR notify_function_trigger_reference_count <> 1 THEN 'STOP_DEPENDENCY_DRIFT'
        WHEN NOT notify_trigger_exact THEN 'STOP_TRIGGER_DRIFT'
        WHEN v2_guard_exact_now THEN 'V2_GUARD_EXACT_ANTECEDENT'
        ELSE 'STOP_UNCLASSIFIED'
    END AS diagnostic_class
    FROM decision
)
SELECT
    CASE decision.boundary_count
        WHEN 0 THEN 'boundary_0'
        WHEN 3 THEN 'boundary_3'
        WHEN 4 THEN 'boundary_4'
        WHEN 5 THEN 'boundary_5'
        WHEN 6 THEN 'boundary_6'
        ELSE 'stop_boundary'
    END AS boundary_class,
    CASE
        WHEN classification.diagnostic_class = 'SUCCESSOR_V3_ELIGIBLE'
            THEN 'successor_v3'
        WHEN classification.diagnostic_class = 'V2_GUARD_EXACT_ANTECEDENT'
            THEN 'historical_v2_not_applicable'
        ELSE 'stop'
    END AS route_class,
    decision.pg17_semantics_supported,
    decision.boundary_count,
    decision.ledger_table_present,
    decision.exact_count,
    decision.checksum_drift_count,
    decision.duplicate_count,
    decision.gap_count,
    decision.v2_stem_count,
    decision.f95_stem_count,
    decision.service_role_present,
    decision.public_access_verifier_exact,
    decision.retirement_verifier_count,
    decision.retirement_verifier_shape_exact,
    decision.ledger_boundary_exact,
    decision.notify_named_routine_count,
    decision.notify_exact_signature_count,
    decision.notify_other_signature_count,
    decision.notify_source_variant,
    decision.notify_source_reviewed,
    decision.notify_metadata_exact,
    decision.notify_owner_exact,
    decision.notify_search_path_exact,
    decision.notify_acl_exact_now,
    decision.notify_acl_repairable_by_prefix,
    decision.notify_acl_unknown_entry_count,
    decision.notify_dependency_exact,
    decision.notify_trigger_exact,
    decision.notify_function_trigger_reference_count,
    decision.v2_guard_exact_now,
    decision.v2_guard_expected_after_prefix,
    decision.successor_guard_eligible,
    decision.successor_guard_eligible AS successor_v3_eligible,
    classification.diagnostic_class,
    false AS application_authorized,
    NOT decision.successor_guard_eligible AS diagnostic_fail_closed
FROM decision, classification;
