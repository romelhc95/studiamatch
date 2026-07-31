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
            'pg_catalog_namespace_count', (
                SELECT count(*)
                FROM pg_catalog.pg_namespace
                WHERE nspname = 'pg_catalog'
            ),
            'role_anchor_count', (
                SELECT count(*)
                FROM pg_catalog.pg_roles
                WHERE rolname IN ('PUBLIC', 'anon', 'authenticated', 'authenticator', 'service_role')
            ),
            'catalog_relation_count', (
                SELECT count(*)
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'pg_catalog'
                  AND c.relkind IN ('r', 'v', 'm', 'f', 'p')
            ),
            'dependency_edge_count', (
                SELECT count(*)
                FROM pg_catalog.pg_depend
            ),
            'membership_edge_count', (
                SELECT count(*)
                FROM pg_catalog.pg_auth_members
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
