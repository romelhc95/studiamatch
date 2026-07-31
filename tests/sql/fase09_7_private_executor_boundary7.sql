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
allowed_sources(source_name) AS (
    VALUES
        ('pg_catalog'),
        ('migration_ledger_digest'),
        ('artifact_digest'),
        ('edge_state_digest')
),
forbidden_surfaces(surface_name, is_absent) AS (
    VALUES
        ('data_api_rpc', true),
        ('public_executor', true),
        ('role_executor_access', true),
        ('business_rows', true),
        ('protected_table_scan', true)
)
SELECT
    contract.package_id,
    contract.boundary_id,
    contract.read_only_mode,
    pg_catalog.bool_and(forbidden_surfaces.is_absent) AS forbidden_surface_absent,
    pg_catalog.count(allowed_sources.source_name) AS allowed_source_count,
    contract.final_executor_state
FROM contract
CROSS JOIN allowed_sources
CROSS JOIN forbidden_surfaces
GROUP BY
    contract.package_id,
    contract.boundary_id,
    contract.read_only_mode,
    contract.final_executor_state
HAVING contract.boundary_id = 7
   AND contract.read_only_mode IS TRUE
   AND contract.final_executor_state = 'private_executor_without_exec_sql'
   AND pg_catalog.bool_and(forbidden_surfaces.is_absent) IS TRUE;
