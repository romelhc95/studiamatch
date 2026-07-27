WITH RECURSIVE
expected_ledger(ordinal, migration_name, checksum_marker) AS (
    VALUES
        (1, '20260724_fase06_g1b_reconciliation', 'sha256:d239f7080c709cdccf7227523ff2b89b48f99a57ace376a18bbdaa4d1a4d75df'),
        (2, '20260724_fase06_hito1_editorial_contract', 'sha256:b8badde99ada9de16aae126497304cfa7d02f9f6df89f3e22604965446c1af8a'),
        (3, '20260725_fase07_g1b_closure', 'sha256:9b83b36e0d90be048ccdfdea8fc1c175b8c7d7ac1fe25d7589d4c653f6a1c120'),
        (4, '20260725_fase08_hito1_functional_closure', 'sha256:7e392473e464df07edbcfcd7b8597ead8d7e10a47d990eedcfe6ed6cee70b527'),
        (5, '20260727_fase09_7_public_access_closure', 'sha256:040584e96996c705add37ae84e163aa51c35c4f65357279146bd6840e61e1d6b')
),
ledger_flags AS (
    SELECT
        expected.ordinal,
        expected.migration_name,
        ledger.name IS NOT NULL AS is_present,
        ledger.statements IS NOT DISTINCT FROM expected.checksum_marker AS is_exact
    FROM expected_ledger AS expected
    LEFT JOIN public.supabase_migrations AS ledger
      ON ledger.name = expected.migration_name
),
ledger_summary AS (
    SELECT
        pg_catalog.count(*) FILTER (WHERE is_exact)::integer AS exact_count,
        pg_catalog.count(*) FILTER (WHERE is_present AND NOT is_exact)::integer AS collision_count,
        coalesce((
            SELECT pg_catalog.max(candidate.ordinal)
            FROM ledger_flags AS candidate
            WHERE NOT EXISTS (
                SELECT 1
                FROM ledger_flags AS required
                WHERE required.ordinal <= candidate.ordinal
                  AND NOT required.is_exact
            )
        ), 0)::integer AS prefix_size
    FROM ledger_flags
),
expected_relations(relation_name) AS (
    VALUES
        ('public.leads'),
        ('public.email_log'),
        ('public.courses'),
        ('public.ratings'),
        ('public.reviews'),
        ('public.institution_site_profiles'),
        ('public.institutions'),
        ('public.categories'),
        ('public.category_rules'),
        ('public.market_salaries'),
        ('public.staging_raw'),
        ('public.cleansed_programs'),
        ('public.enriched_programs')
),
relation_state AS (
    SELECT
        expected.relation_name,
        pg_catalog.to_regclass(expected.relation_name) AS relation_oid
    FROM expected_relations AS expected
),
expected_columns(relation_name, column_name) AS (
    VALUES
        ('public.leads', 'id'),
        ('public.leads', 'first_name'),
        ('public.leads', 'last_name'),
        ('public.leads', 'email'),
        ('public.leads', 'whatsapp'),
        ('public.leads', 'source_page'),
        ('public.leads', 'type'),
        ('public.leads', 'course_id'),
        ('public.leads', 'area_interest'),
        ('public.leads', 'budget'),
        ('public.leads', 'modality'),
        ('public.leads', 'description'),
        ('public.leads', 'is_late_enrollment_request'),
        ('public.leads', 'status'),
        ('public.leads', 'created_at'),
        ('public.leads', 'lead_source_type'),
        ('public.email_log', 'id'),
        ('public.email_log', 'lead_id'),
        ('public.email_log', 'recipient_type'),
        ('public.email_log', 'recipient_email'),
        ('public.email_log', 'subject'),
        ('public.email_log', 'status'),
        ('public.email_log', 'resend_id'),
        ('public.email_log', 'error_message'),
        ('public.email_log', 'created_at'),
        ('public.courses', 'id'),
        ('public.courses', 'institution_id'),
        ('public.courses', 'is_active'),
        ('public.courses', 'is_verified'),
        ('public.courses', 'publication_status'),
        ('public.institution_site_profiles', 'institution_id'),
        ('public.institution_site_profiles', 'production_enabled')
),
expected_insert_columns(column_name) AS (
    VALUES
        ('first_name'),
        ('last_name'),
        ('email'),
        ('whatsapp'),
        ('source_page'),
        ('type'),
        ('course_id'),
        ('area_interest'),
        ('budget'),
        ('modality'),
        ('description'),
        ('is_late_enrollment_request')
),
public_roles(role_name, role_oid) AS (
    SELECT role.rolname, role.oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname IN ('anon', 'authenticated')
),
target_roles(role_name, role_oid) AS (
    SELECT role.rolname, role.oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname IN ('anon', 'authenticated', 'service_role')
),
service_role(role_oid) AS (
    SELECT role.oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'service_role'
),
role_closure(root_role_oid, role_oid) AS (
    SELECT target.role_oid, target.role_oid
    FROM target_roles AS target
    UNION
    SELECT closure.root_role_oid, membership.roleid
    FROM role_closure AS closure
    JOIN pg_catalog.pg_auth_members AS membership
      ON membership.member = closure.role_oid
),
target_attributes AS (
    SELECT
        namespace.nspname || '.' || relation.relname AS relation_name,
        relation.oid AS relation_oid,
        attribute.attnum,
        attribute.attname
    FROM pg_catalog.pg_class AS relation
    JOIN pg_catalog.pg_namespace AS namespace
      ON namespace.oid = relation.relnamespace
    JOIN pg_catalog.pg_attribute AS attribute
      ON attribute.attrelid = relation.oid
    WHERE namespace.nspname = 'public'
      AND relation.relname IN ('leads', 'email_log')
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped
),
public_policy_scope AS (
    SELECT DISTINCT
        policy.schemaname,
        policy.tablename,
        policy.policyname,
        policy.cmd,
        public_role.role_name
    FROM pg_catalog.pg_policies AS policy
    CROSS JOIN public_roles AS public_role
    WHERE policy.schemaname = 'public'
      AND policy.tablename IN ('leads', 'email_log')
      AND (
          'public'::name = ANY(policy.roles)
          OR EXISTS (
              SELECT 1
              FROM pg_catalog.unnest(policy.roles) AS policy_role(role_name)
              JOIN pg_catalog.pg_roles AS inherited_role
                ON inherited_role.rolname = policy_role.role_name
              WHERE pg_catalog.pg_has_role(
                  public_role.role_oid, inherited_role.oid, 'USAGE'
              )
          )
      )
),
aggregate_evidence AS (
    SELECT
        (SELECT prefix_size FROM ledger_summary) AS ledger_prefix_size,
        (SELECT exact_count FROM ledger_summary) AS ledger_exact_count,
        (SELECT collision_count FROM ledger_summary) AS ledger_collision_count,
        (SELECT exact_count - prefix_size FROM ledger_summary) AS ledger_gap_count,
        (SELECT
            collision_count = 0
            AND exact_count = prefix_size
            AND prefix_size = ANY(ARRAY[0, 3, 4, 5])
         FROM ledger_summary) AS ledger_boundary_valid,
        (SELECT pg_catalog.count(*)::integer
         FROM public.supabase_migrations AS ledger
         WHERE ledger.name IN (
             '20260726_fase09_5_rls_canary_reconciliation',
             '20260726_fase09_5_policy_inventory_reconciliation'
         )) AS historical_nonpromotable_ledger_count,
        (SELECT pg_catalog.count(*)::integer
         FROM relation_state
         WHERE relation_oid IS NULL) AS missing_relation_count,
        (SELECT pg_catalog.count(*)::integer
         FROM expected_columns AS expected
         WHERE NOT EXISTS (
             SELECT 1
             FROM pg_catalog.pg_attribute AS attribute
             WHERE attribute.attrelid = pg_catalog.to_regclass(expected.relation_name)
               AND attribute.attnum > 0
               AND NOT attribute.attisdropped
               AND attribute.attname = expected.column_name
         )) AS missing_column_count,
        (SELECT pg_catalog.count(*)::integer
         FROM relation_state AS target
         LEFT JOIN pg_catalog.pg_class AS relation
           ON relation.oid = target.relation_oid
         WHERE target.relation_name IN (
             'public.courses', 'public.leads', 'public.email_log',
             'public.ratings', 'public.reviews',
             'public.institution_site_profiles'
         )
           AND relation.relrowsecurity IS DISTINCT FROM true) AS rls_missing_count,
        (SELECT pg_catalog.count(*)::integer
         FROM relation_state AS target
         JOIN pg_catalog.pg_class AS relation
           ON relation.oid = target.relation_oid
         JOIN pg_catalog.pg_roles AS owner
           ON owner.oid = relation.relowner
         WHERE target.relation_name IN ('public.leads', 'public.email_log')
           AND owner.rolname <> 'postgres') AS owner_mismatch_count,
        (3 - (SELECT pg_catalog.count(*)::integer FROM target_roles)) AS role_missing_count,
        (SELECT pg_catalog.count(*)::integer
         FROM pg_catalog.pg_roles AS role
         WHERE (
             role.rolname IN ('anon', 'authenticated')
             AND (
                 role.rolsuper OR role.rolbypassrls OR role.rolcanlogin
                 OR role.rolcreaterole OR role.rolcreatedb OR role.rolreplication
             )
         ) OR (
             role.rolname = 'service_role'
             AND (
                 role.rolsuper OR NOT role.rolbypassrls OR role.rolcanlogin
                 OR role.rolcreaterole OR role.rolcreatedb OR role.rolreplication
             )
         )) AS role_posture_violation_count,
        (SELECT pg_catalog.count(*)::integer
         FROM role_closure AS closure
         JOIN pg_catalog.pg_roles AS elevated_role
           ON elevated_role.oid = closure.role_oid
         WHERE closure.root_role_oid <> closure.role_oid
           AND (
               elevated_role.rolsuper OR elevated_role.rolbypassrls
               OR elevated_role.rolcreaterole OR elevated_role.rolcreatedb
               OR elevated_role.rolreplication
           )) AS privileged_membership_count,
        (SELECT pg_catalog.count(*)::integer
         FROM target_roles AS target_role
         WHERE NOT pg_catalog.has_schema_privilege(
             target_role.role_oid, 'public', 'USAGE'
         )) AS schema_usage_missing_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         WHERE pg_catalog.has_schema_privilege(
             public_role.role_oid, 'public', 'CREATE'
         )) AS public_schema_create_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_policy_scope
         WHERE cmd IN ('SELECT', 'ALL')) AS public_select_policy_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_policy_scope
         WHERE (tablename, policyname) NOT IN (
             ('leads', 'leads_select_public'),
             ('leads', 'leads_select_authenticated'),
             ('leads', 'leads_insert_public'),
             ('leads', 'leads_insert_authenticated'),
             ('email_log', 'email_log_select_public'),
             ('email_log', 'email_log_select_authenticated')
         )) AS unmanaged_public_policy_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         CROSS JOIN relation_state AS target
         WHERE target.relation_name IN ('public.leads', 'public.email_log')
           AND pg_catalog.has_table_privilege(
               public_role.role_oid, target.relation_oid, 'SELECT'
           )) AS public_select_table_acl_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         CROSS JOIN target_attributes AS attribute
         WHERE pg_catalog.has_column_privilege(
             public_role.role_oid,
             attribute.relation_oid,
             attribute.attnum,
             'SELECT'
         )) AS public_select_column_acl_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         WHERE pg_catalog.has_table_privilege(
             public_role.role_oid,
             pg_catalog.to_regclass('public.leads'),
             'INSERT'
         )) AS leads_insert_table_acl_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         CROSS JOIN expected_insert_columns AS expected
         JOIN target_attributes AS attribute
           ON attribute.relation_name = 'public.leads'
          AND attribute.attname = expected.column_name
         WHERE NOT pg_catalog.has_column_privilege(
             public_role.role_oid,
             attribute.relation_oid,
             attribute.attnum,
             'INSERT'
         )) AS leads_insert_allowed_missing_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         CROSS JOIN target_attributes AS attribute
         WHERE attribute.relation_name = 'public.leads'
           AND attribute.attname NOT IN (
               SELECT expected.column_name FROM expected_insert_columns AS expected
           )
           AND pg_catalog.has_column_privilege(
               public_role.role_oid,
               attribute.relation_oid,
               attribute.attnum,
               'INSERT'
           )) AS leads_insert_extra_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         CROSS JOIN target_attributes AS attribute
         CROSS JOIN LATERAL pg_catalog.unnest(
             CASE
                 WHEN attribute.relation_name = 'public.leads'
                 THEN ARRAY['SELECT', 'UPDATE', 'REFERENCES']::text[]
                 ELSE ARRAY['SELECT', 'INSERT', 'UPDATE', 'REFERENCES']::text[]
             END
         ) AS denied(privilege_name)
         WHERE pg_catalog.has_column_privilege(
             public_role.role_oid,
             attribute.relation_oid,
             attribute.attnum,
             denied.privilege_name
         )) AS public_denied_column_acl_count,
        (SELECT pg_catalog.count(*)::integer
         FROM public_roles AS public_role
         CROSS JOIN relation_state AS target
         CROSS JOIN LATERAL pg_catalog.unnest(
              ARRAY[
                  'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                  'REFERENCES', 'TRIGGER'
              ]::text[]
         ) AS denied(privilege_name)
         WHERE target.relation_name IN ('public.leads', 'public.email_log')
           AND pg_catalog.has_table_privilege(
               public_role.role_oid,
               target.relation_oid,
               denied.privilege_name
           )) AS public_dangerous_table_acl_count,
        (SELECT pg_catalog.count(*)::integer
         FROM relation_state AS target
         LEFT JOIN service_role AS service ON true
         WHERE service.role_oid IS NULL
            OR target.relation_oid IS NULL
            OR pg_catalog.has_table_privilege(
                service.role_oid, target.relation_oid, 'SELECT'
            ) IS DISTINCT FROM true) AS service_select_missing_count,
        (SELECT pg_catalog.count(*)::integer
         FROM (VALUES
             ('public.courses'),
             ('public.leads'),
             ('public.ratings'),
             ('public.reviews'),
             ('public.institution_site_profiles')
         ) AS required_table(relation_name)
         CROSS JOIN (VALUES
             ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE')
         ) AS required_privilege(privilege_name)
         LEFT JOIN service_role AS service ON true
         WHERE service.role_oid IS NULL
            OR pg_catalog.to_regclass(required_table.relation_name) IS NULL
            OR pg_catalog.has_table_privilege(
                service.role_oid,
                pg_catalog.to_regclass(required_table.relation_name),
                required_privilege.privilege_name
            ) IS DISTINCT FROM true) AS service_write_missing_count,
        (SELECT pg_catalog.count(*)::integer
         FROM (
             SELECT relation.oid, public_role.role_oid
             FROM pg_catalog.pg_class AS relation
             CROSS JOIN LATERAL pg_catalog.aclexplode(
                 coalesce(
                     relation.relacl,
                     pg_catalog.acldefault('r', relation.relowner)
                 )
             ) AS acl
             CROSS JOIN target_roles AS public_role
             WHERE relation.oid IN (
                 SELECT target.relation_oid
                 FROM relation_state AS target
                 WHERE target.relation_oid IS NOT NULL
             )
               AND acl.is_grantable
               AND (
                   acl.grantee = 0
                   OR pg_catalog.pg_has_role(
                       public_role.role_oid, acl.grantee, 'USAGE'
                   )
               )
             UNION ALL
             SELECT attribute.attrelid, public_role.role_oid
             FROM pg_catalog.pg_attribute AS attribute
             CROSS JOIN LATERAL pg_catalog.aclexplode(
                 attribute.attacl
             ) AS acl
             CROSS JOIN target_roles AS public_role
             WHERE attribute.attrelid IN (
                 SELECT target.relation_oid
                 FROM relation_state AS target
                 WHERE target.relation_oid IS NOT NULL
             )
               AND attribute.attnum > 0
               AND NOT attribute.attisdropped
               AND acl.is_grantable
               AND (
                   acl.grantee = 0
                   OR pg_catalog.pg_has_role(
                       public_role.role_oid, acl.grantee, 'USAGE'
                   )
               )
             UNION ALL
             SELECT namespace.oid, target_role.role_oid
             FROM pg_catalog.pg_namespace AS namespace
             CROSS JOIN LATERAL pg_catalog.aclexplode(
                 coalesce(
                     namespace.nspacl,
                     pg_catalog.acldefault('n', namespace.nspowner)
                 )
             ) AS acl
             CROSS JOIN target_roles AS target_role
             WHERE namespace.nspname = 'public'
               AND acl.is_grantable
               AND (
                   acl.grantee = 0
                   OR pg_catalog.pg_has_role(
                       target_role.role_oid, acl.grantee, 'USAGE'
                   )
               )
             UNION ALL
             SELECT procedure.oid, target_role.role_oid
             FROM pg_catalog.pg_proc AS procedure
             CROSS JOIN LATERAL pg_catalog.aclexplode(
                 coalesce(
                     procedure.proacl,
                     pg_catalog.acldefault('f', procedure.proowner)
                 )
             ) AS acl
             CROSS JOIN target_roles AS target_role
             WHERE procedure.pronamespace = 'public'::regnamespace
               AND acl.is_grantable
               AND (
                   acl.grantee = 0
                   OR pg_catalog.pg_has_role(
                       target_role.role_oid, acl.grantee, 'USAGE'
                   )
               )
         ) AS grant_option) AS target_grant_option_count,
        (SELECT pg_catalog.count(*)::integer
         FROM pg_catalog.pg_auth_members AS membership
         JOIN role_closure AS closure
           ON closure.role_oid = membership.member
         WHERE membership.admin_option) AS role_admin_option_count,
        (SELECT pg_catalog.count(*)::integer
         FROM pg_catalog.pg_class AS relation
         CROSS JOIN LATERAL pg_catalog.aclexplode(
             coalesce(
                 relation.relacl,
                 pg_catalog.acldefault('r', relation.relowner)
             )
         ) AS acl
         CROSS JOIN public_roles AS public_role
         WHERE relation.oid IN (
             pg_catalog.to_regclass('public.leads'),
             pg_catalog.to_regclass('public.email_log')
         )
           AND acl.privilege_type = 'MAINTAIN'
           AND (
               acl.grantee = 0
               OR pg_catalog.pg_has_role(
                   public_role.role_oid, acl.grantee, 'USAGE'
               )
           )) AS public_maintain_acl_count,
        (SELECT pg_catalog.count(DISTINCT (procedure.oid, public_role.role_oid))::integer
         FROM pg_catalog.pg_proc AS procedure
         CROSS JOIN public_roles AS public_role
         WHERE procedure.pronamespace = 'public'::regnamespace
           AND procedure.prosecdef
           AND pg_catalog.has_function_privilege(
               public_role.role_oid, procedure.oid, 'EXECUTE'
           )) AS public_security_definer_execute_count,
        (SELECT pg_catalog.count(DISTINCT (view_relation.oid, public_role.role_oid))::integer
         FROM pg_catalog.pg_class AS view_relation
         JOIN pg_catalog.pg_namespace AS namespace
           ON namespace.oid = view_relation.relnamespace
         CROSS JOIN public_roles AS public_role
         WHERE namespace.nspname = 'public'
           AND view_relation.relkind IN ('v', 'm')
           AND (
               pg_catalog.has_table_privilege(
                   public_role.role_oid, view_relation.oid, 'SELECT'
               )
               OR EXISTS (
                   SELECT 1
                   FROM pg_catalog.pg_attribute AS attribute
                   WHERE attribute.attrelid = view_relation.oid
                     AND attribute.attnum > 0
                     AND NOT attribute.attisdropped
                     AND pg_catalog.has_column_privilege(
                         public_role.role_oid,
                         attribute.attrelid,
                         attribute.attnum,
                         'SELECT'
                     )
               )
           )) AS public_readable_view_count
)
SELECT
    'F9.7-GATE-B-CATALOG-V1'::text AS query_id,
    'free'::text AS target_scope,
    evidence.ledger_prefix_size,
    evidence.ledger_exact_count,
    evidence.ledger_collision_count,
    evidence.ledger_gap_count,
    evidence.ledger_boundary_valid,
    evidence.historical_nonpromotable_ledger_count,
    evidence.missing_relation_count,
    evidence.missing_column_count,
    evidence.rls_missing_count,
    evidence.owner_mismatch_count,
    evidence.role_missing_count,
    evidence.role_posture_violation_count,
    evidence.privileged_membership_count,
    evidence.schema_usage_missing_count,
    evidence.public_schema_create_count,
    evidence.public_select_policy_count,
    evidence.unmanaged_public_policy_count,
    evidence.public_select_table_acl_count,
    evidence.public_select_column_acl_count,
    evidence.leads_insert_table_acl_count,
    evidence.leads_insert_allowed_missing_count,
    evidence.leads_insert_extra_count,
    evidence.public_denied_column_acl_count,
    evidence.public_dangerous_table_acl_count,
    evidence.service_select_missing_count,
    evidence.service_write_missing_count,
    evidence.target_grant_option_count,
    evidence.role_admin_option_count,
    evidence.public_maintain_acl_count,
    evidence.public_security_definer_execute_count,
    evidence.public_readable_view_count,
    (
        evidence.public_select_policy_count = 0
        AND evidence.public_select_table_acl_count = 0
        AND evidence.public_select_column_acl_count = 0
    ) AS public_read_absent,
    (
        evidence.leads_insert_table_acl_count = 0
        AND evidence.leads_insert_allowed_missing_count = 0
        AND evidence.leads_insert_extra_count = 0
    ) AS leads_insert_columns_exact,
    (
        evidence.ledger_boundary_valid
        AND evidence.historical_nonpromotable_ledger_count = 0
        AND evidence.missing_relation_count = 0
        AND evidence.missing_column_count = 0
        AND evidence.rls_missing_count = 0
        AND evidence.owner_mismatch_count = 0
        AND evidence.role_missing_count = 0
        AND evidence.role_posture_violation_count = 0
        AND evidence.privileged_membership_count = 0
        AND evidence.schema_usage_missing_count = 0
        AND evidence.public_schema_create_count = 0
        AND evidence.unmanaged_public_policy_count = 0
        AND evidence.service_select_missing_count = 0
        AND evidence.service_write_missing_count = 0
        AND evidence.target_grant_option_count = 0
        AND evidence.role_admin_option_count = 0
        AND evidence.public_maintain_acl_count = 0
        AND evidence.public_security_definer_execute_count = 0
        AND evidence.public_readable_view_count = 0
    ) AS candidate_compatible,
    (
        evidence.ledger_boundary_valid
        AND evidence.historical_nonpromotable_ledger_count = 0
        AND evidence.missing_relation_count = 0
        AND evidence.missing_column_count = 0
        AND evidence.rls_missing_count = 0
        AND evidence.owner_mismatch_count = 0
        AND evidence.role_missing_count = 0
        AND evidence.role_posture_violation_count = 0
        AND evidence.privileged_membership_count = 0
        AND evidence.schema_usage_missing_count = 0
        AND evidence.public_schema_create_count = 0
        AND evidence.public_select_policy_count = 0
        AND evidence.unmanaged_public_policy_count = 0
        AND evidence.public_select_table_acl_count = 0
        AND evidence.public_select_column_acl_count = 0
        AND evidence.leads_insert_table_acl_count = 0
        AND evidence.leads_insert_allowed_missing_count = 0
        AND evidence.leads_insert_extra_count = 0
        AND evidence.public_denied_column_acl_count = 0
        AND evidence.public_dangerous_table_acl_count = 0
        AND evidence.service_select_missing_count = 0
        AND evidence.service_write_missing_count = 0
        AND evidence.target_grant_option_count = 0
        AND evidence.role_admin_option_count = 0
        AND evidence.public_maintain_acl_count = 0
        AND evidence.public_security_definer_execute_count = 0
        AND evidence.public_readable_view_count = 0
    ) AS gate_b_catalog_pass
FROM aggregate_evidence AS evidence;
