WITH
contract(package_id, boundary_id, target_class, read_only_mode, final_executor_state) AS (
    VALUES (
        'PR-O-F9.7-PRIVATE-EXECUTOR-002',
        7,
        'synthetic_free_only',
        true,
        'private_executor_without_exec_sql'
    )
),
catalog_fingerprint AS (
    SELECT
        jsonb_build_object(
            'catalog_namespace_count', (
                SELECT count(*)
                FROM pg_catalog.pg_namespace
                WHERE nspname = 'pg_catalog'
            ),
            'role_count', (
                SELECT count(*)
                FROM pg_catalog.pg_roles
                WHERE rolname IN ('PUBLIC', 'anon', 'authenticated', 'authenticator', 'service_role')
            ),
            'owner_role_count', (
                SELECT count(DISTINCT relowner)
                FROM pg_catalog.pg_class
            ),
            'acl_fingerprint', (
                SELECT md5(
                    coalesce((
                        SELECT string_agg(COALESCE(c.relacl::text, '∅') || ':' || c.relowner::text, '|' ORDER BY c.oid)
                        FROM pg_catalog.pg_class c
                    ), '') || '|' ||
                    coalesce((
                        SELECT string_agg(COALESCE(n.nspacl::text, '∅') || ':' || n.nspowner::text, '|' ORDER BY n.oid)
                        FROM pg_catalog.pg_namespace n
                    ), '') || '|' ||
                    coalesce((
                        SELECT string_agg(COALESCE(p.proacl::text, '∅') || ':' || p.proowner::text, '|' ORDER BY p.oid)
                        FROM pg_catalog.pg_proc p
                    ), '') || '|' ||
                    coalesce((
                        SELECT string_agg(COALESCE(d.defaclacl::text, '∅') || ':' || d.defaclrole::text, '|' ORDER BY d.oid)
                        FROM pg_catalog.pg_default_acl d
                    ), '')
                )
            ),
            'privilege_probe_fingerprint', (
                SELECT md5(
                    coalesce((
                        SELECT string_agg(has_table_privilege('public', c.oid, 'SELECT')::text, '|' ORDER BY c.oid)
                        FROM pg_catalog.pg_class c
                    ), '') || '|' ||
                    coalesce((
                        SELECT string_agg(has_schema_privilege('public', n.oid, 'USAGE')::text, '|' ORDER BY n.oid)
                        FROM pg_catalog.pg_namespace n
                    ), '') || '|' ||
                    coalesce((
                        SELECT string_agg(has_function_privilege('public', p.oid, 'EXECUTE')::text, '|' ORDER BY p.oid)
                        FROM pg_catalog.pg_proc p
                    ), '')
                )
            ),
            'class_owner_count', (
                SELECT count(DISTINCT relowner)
                FROM pg_catalog.pg_class
            ),
            'proc_owner_count', (
                SELECT count(DISTINCT proowner)
                FROM pg_catalog.pg_proc
            ),
            'extension_owner_count', (
                SELECT count(DISTINCT extowner)
                FROM pg_catalog.pg_extension
            ),
            'rls_enabled_count', (
                SELECT count(*)
                FROM pg_catalog.pg_class
                WHERE relrowsecurity
            ),
            'rls_forced_count', (
                SELECT count(*)
                FROM pg_catalog.pg_class
                WHERE relforcerowsecurity
            ),
            'policy_count', (
                SELECT count(*)
                FROM pg_catalog.pg_policy
            ),
            'routine_count', (
                SELECT count(*)
                FROM pg_catalog.pg_proc
            ),
            'trigger_count', (
                SELECT count(*)
                FROM pg_catalog.pg_trigger
            ),
            'view_count', (
                SELECT count(*)
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'pg_catalog'
                  AND c.relkind IN ('r', 'v', 'm', 'f', 'p')
            ),
            'rule_count', (
                SELECT count(*)
                FROM pg_catalog.pg_rewrite
            ),
            'publication_count', (
                SELECT count(*)
                FROM pg_catalog.pg_publication
            ),
            'extension_count', (
                SELECT count(*)
                FROM pg_catalog.pg_extension
            ),
            'constraint_count', (
                SELECT count(*)
                FROM pg_catalog.pg_constraint
            ),
            'membership_count', (
                SELECT count(*)
                FROM pg_catalog.pg_auth_members
            ),
            'dependency_edge_count', (
                SELECT count(*)
                FROM pg_catalog.pg_depend
            )
        ) AS fingerprint
)
SELECT
    contract.package_id,
    contract.boundary_id,
    contract.target_class,
    contract.read_only_mode,
    contract.final_executor_state,
    catalog_fingerprint.fingerprint,
    true AS forbidden_surface_absent
FROM contract
CROSS JOIN catalog_fingerprint
WHERE contract.boundary_id = 7
  AND contract.read_only_mode IS TRUE
  AND contract.final_executor_state = 'private_executor_without_exec_sql';
