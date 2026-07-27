WITH RECURSIVE
contract_constants(membership_depth_limit, policy_expression_attested) AS (
    VALUES (128::integer, false)
),
expected_targets(target_name) AS (
    VALUES ('leads'::pg_catalog.name), ('email_log'::pg_catalog.name)
),
expected_roles(role_class, role_name) AS (
    VALUES
        ('anon'::text, 'anon'::pg_catalog.name),
        ('authenticated'::text, 'authenticated'::pg_catalog.name),
        ('service_role'::text, 'service_role'::pg_catalog.name)
),
requested_principals(role_class, role_oid) AS (
    SELECT 'PUBLIC'::text, NULL::pg_catalog.oid
    UNION ALL
    SELECT expected.role_class, role.oid
    FROM expected_roles AS expected
    LEFT JOIN pg_catalog.pg_roles AS role
      ON role.rolname = expected.role_name
),
role_labels(role_oid, role_class) AS (
    SELECT
        role.oid,
        CASE
            WHEN role.rolname = 'anon' THEN 'anon'
            WHEN role.rolname = 'authenticated' THEN 'authenticated'
            WHEN role.rolname = 'service_role' THEN 'service_role'
            WHEN role.rolname = 'postgres' THEN 'platform_owner'
            WHEN role.rolname = 'pg_database_owner' THEN 'database_owner'
            WHEN role.rolname = 'pg_read_all_data' THEN 'global_read'
            WHEN role.rolname = 'pg_write_all_data' THEN 'global_write'
            WHEN role.rolname = 'pg_maintain' THEN 'global_maintain'
            ELSE 'other_role'
        END::text
    FROM pg_catalog.pg_roles AS role
),
current_database_owner(owner_oid) AS (
    SELECT database_record.datdba
    FROM pg_catalog.pg_database AS database_record
    WHERE database_record.datname = pg_catalog.current_database()
),
database_owner_role(role_oid) AS (
    SELECT role.oid
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname = 'pg_database_owner'
),
membership_edges(member_oid, role_oid, admin_option, inherit_option, set_option) AS (
    SELECT
        membership.member,
        membership.roleid,
        COALESCE(
            (pg_catalog.to_jsonb(membership) ->> 'admin_option')::boolean,
            false
        ),
        COALESCE(
            (pg_catalog.to_jsonb(membership) ->> 'inherit_option')::boolean,
            false
        ),
        COALESCE(
            (pg_catalog.to_jsonb(membership) ->> 'set_option')::boolean,
            false
        )
    FROM pg_catalog.pg_auth_members AS membership
    UNION
    SELECT
        database_owner.owner_oid,
        database_role.role_oid,
        false,
        true,
        true
    FROM current_database_owner AS database_owner
    CROSS JOIN database_owner_role AS database_role
),
targets(target_name, relation_oid, relation_kind, rls_enabled, force_rls, owner_oid) AS (
    SELECT
        expected.target_name::text,
        relation.oid,
        relation.relkind,
        relation.relrowsecurity,
        relation.relforcerowsecurity,
        relation.relowner
    FROM expected_targets AS expected
    LEFT JOIN pg_catalog.pg_namespace AS namespace
      ON namespace.nspname = 'public'
    LEFT JOIN pg_catalog.pg_class AS relation
      ON relation.relnamespace = namespace.oid
     AND relation.relname = expected.target_name
),
membership_walk(root_class, root_oid, reached_oid, route, depth, visited) AS (
    SELECT
        principal.role_class,
        principal.role_oid,
        principal.role_oid,
        'direct'::text,
        0,
        ARRAY[principal.role_oid]::pg_catalog.oid[]
    FROM requested_principals AS principal
    WHERE principal.role_oid IS NOT NULL
    UNION ALL
    SELECT
        walk.root_class,
        walk.root_oid,
        membership.role_oid,
        transition.next_route,
        walk.depth + 1,
        walk.visited || membership.role_oid
    FROM membership_walk AS walk
    JOIN membership_edges AS membership
      ON membership.member_oid = walk.reached_oid
    CROSS JOIN LATERAL (
        VALUES
            ('inherit'::text, membership.inherit_option AND walk.route IN ('direct', 'inherit')),
            ('set'::text, membership.set_option AND walk.route IN ('direct', 'set')),
            ('set_then_inherit'::text, membership.inherit_option AND walk.route IN ('set', 'set_then_inherit'))
    ) AS transition(next_route, is_allowed)
    WHERE transition.is_allowed
      AND NOT membership.role_oid = ANY(walk.visited)
      AND walk.depth < (SELECT membership_depth_limit FROM contract_constants)
),
effective_routes(root_class, root_oid, reached_oid, route, min_depth, path_count) AS (
    SELECT
        walk.root_class,
        walk.root_oid,
        walk.reached_oid,
        walk.route,
        pg_catalog.min(walk.depth)::integer,
        pg_catalog.count(*)::integer
    FROM membership_walk AS walk
    GROUP BY walk.root_class, walk.root_oid, walk.reached_oid, walk.route
),
reachable_members AS (
    SELECT DISTINCT walk.root_class, walk.root_oid, walk.reached_oid
    FROM membership_walk AS walk
),
membership_depth_truncations AS (
    SELECT walk.root_class, walk.reached_oid, membership.role_oid
    FROM membership_walk AS walk
    JOIN membership_edges AS membership
      ON membership.member_oid = walk.reached_oid
    CROSS JOIN LATERAL (
        VALUES
            (membership.inherit_option AND walk.route IN ('direct', 'inherit')),
            (membership.set_option AND walk.route IN ('direct', 'set')),
            (membership.inherit_option AND walk.route IN ('set', 'set_then_inherit'))
    ) AS transition(is_allowed)
    WHERE walk.depth = (SELECT membership_depth_limit FROM contract_constants)
      AND transition.is_allowed
      AND NOT membership.role_oid = ANY(walk.visited)
),
all_namespace_acl_entries(namespace_oid, owner_oid, privilege_name, grantee_oid) AS (
    SELECT
        namespace.oid,
        namespace.nspowner,
        acl.privilege_type,
        acl.grantee
    FROM pg_catalog.pg_namespace AS namespace
    CROSS JOIN LATERAL pg_catalog.aclexplode(
        COALESCE(
            namespace.nspacl,
            pg_catalog.acldefault('n', namespace.nspowner)
        )
    ) AS acl
),
effective_namespace_usage(root_class, namespace_oid) AS (
    SELECT principal.role_class, acl.namespace_oid
    FROM all_namespace_acl_entries AS acl
    CROSS JOIN requested_principals AS principal
    WHERE acl.privilege_name = 'USAGE'
      AND acl.grantee_oid = 0
    UNION
    SELECT route.root_class, acl.namespace_oid
    FROM all_namespace_acl_entries AS acl
    JOIN effective_routes AS route
      ON route.reached_oid = acl.grantee_oid
    WHERE acl.privilege_name = 'USAGE'
    UNION
    SELECT route.root_class, namespace.oid
    FROM pg_catalog.pg_namespace AS namespace
    JOIN effective_routes AS route
      ON route.reached_oid = namespace.nspowner
    UNION
    SELECT route.root_class, namespace.oid
    FROM pg_catalog.pg_namespace AS namespace
    CROSS JOIN effective_routes AS route
    JOIN role_labels AS label
      ON label.role_oid = route.reached_oid
    WHERE label.role_class IN ('global_read', 'global_write')
    UNION
    SELECT route.root_class, namespace.oid
    FROM pg_catalog.pg_namespace AS namespace
    CROSS JOIN effective_routes AS route
    JOIN pg_catalog.pg_roles AS role
      ON role.oid = route.reached_oid
    WHERE route.route IN ('direct', 'set')
      AND role.rolsuper
),
usable_public_schemas(namespace_oid) AS (
    SELECT DISTINCT usage_record.namespace_oid
    FROM effective_namespace_usage AS usage_record
    WHERE usage_record.root_class IN ('PUBLIC', 'anon', 'authenticated')
),
target_columns(target_name, relation_oid, attnum, column_name) AS (
    SELECT target.target_name, target.relation_oid, attribute.attnum, attribute.attname::text
    FROM targets AS target
    JOIN pg_catalog.pg_attribute AS attribute
      ON attribute.attrelid = target.relation_oid
    WHERE attribute.attnum > 0
      AND NOT attribute.attisdropped
),
allowed_insert_columns(column_name) AS (
    VALUES
        ('first_name'::text), ('last_name'), ('email'), ('whatsapp'),
        ('source_page'), ('type'), ('course_id'), ('area_interest'),
        ('budget'), ('modality'), ('description'),
        ('is_late_enrollment_request')
),
public_namespace(namespace_oid, owner_oid, namespace_acl) AS (
    SELECT namespace.oid, namespace.nspowner, namespace.nspacl
    FROM pg_catalog.pg_namespace AS namespace
    WHERE namespace.nspname = 'public'
),
schema_acl_entries(privilege_name, grantee_oid, grantor_oid, grantable) AS (
    SELECT acl.privilege_type, acl.grantee, acl.grantor, acl.is_grantable
    FROM public_namespace AS namespace
    CROSS JOIN LATERAL pg_catalog.aclexplode(
        COALESCE(
            namespace.namespace_acl,
            pg_catalog.acldefault('n', namespace.owner_oid)
        )
    ) AS acl
),
effective_schema_acl(root_class, privilege_name, source_class, route, grantable) AS (
    SELECT
        principal.role_class,
        acl.privilege_name,
        'PUBLIC'::text,
        'public'::text,
        acl.grantable
    FROM schema_acl_entries AS acl
    CROSS JOIN requested_principals AS principal
    WHERE acl.grantee_oid = 0
    UNION ALL
    SELECT
        route.root_class,
        acl.privilege_name,
        COALESCE(label.role_class, 'orphaned_role'),
        route.route,
        acl.grantable
    FROM schema_acl_entries AS acl
    JOIN effective_routes AS route
      ON route.reached_oid = acl.grantee_oid
    LEFT JOIN role_labels AS label
      ON label.role_oid = acl.grantee_oid
),
table_acl_entries(target_name, relation_oid, privilege_name, grantee_oid, grantor_oid, grantable) AS (
    SELECT
        target.target_name,
        target.relation_oid,
        acl.privilege_type,
        acl.grantee,
        acl.grantor,
        acl.is_grantable
    FROM targets AS target
    JOIN pg_catalog.pg_class AS relation
      ON relation.oid = target.relation_oid
    CROSS JOIN LATERAL pg_catalog.aclexplode(relation.relacl) AS acl
),
column_acl_entries(target_name, relation_oid, attnum, column_name, privilege_name, grantee_oid, grantor_oid, grantable) AS (
    SELECT
        column_record.target_name,
        column_record.relation_oid,
        column_record.attnum,
        column_record.column_name,
        acl.privilege_type,
        acl.grantee,
        acl.grantor,
        acl.is_grantable
    FROM target_columns AS column_record
    JOIN pg_catalog.pg_attribute AS attribute
      ON attribute.attrelid = column_record.relation_oid
     AND attribute.attnum = column_record.attnum
    CROSS JOIN LATERAL pg_catalog.aclexplode(attribute.attacl) AS acl
),
effective_table_acl(root_class, target_name, privilege_name, source_class, route, grantable) AS (
    SELECT
        principal.role_class,
        acl.target_name,
        acl.privilege_name,
        'PUBLIC'::text,
        'public'::text,
        acl.grantable
    FROM table_acl_entries AS acl
    CROSS JOIN requested_principals AS principal
    WHERE acl.grantee_oid = 0
    UNION ALL
    SELECT
        route.root_class,
        acl.target_name,
        acl.privilege_name,
        COALESCE(label.role_class, 'orphaned_role'),
        route.route,
        acl.grantable
    FROM table_acl_entries AS acl
    JOIN effective_routes AS route
      ON route.reached_oid = acl.grantee_oid
    LEFT JOIN role_labels AS label
      ON label.role_oid = acl.grantee_oid
),
effective_column_acl(root_class, target_name, column_name, privilege_name, source_class, route, grantable) AS (
    SELECT
        principal.role_class,
        acl.target_name,
        acl.column_name,
        acl.privilege_name,
        'PUBLIC'::text,
        'public'::text,
        acl.grantable
    FROM column_acl_entries AS acl
    CROSS JOIN requested_principals AS principal
    WHERE acl.grantee_oid = 0
    UNION ALL
    SELECT
        route.root_class,
        acl.target_name,
        acl.column_name,
        acl.privilege_name,
        COALESCE(label.role_class, 'orphaned_role'),
        route.route,
        acl.grantable
    FROM column_acl_entries AS acl
    JOIN effective_routes AS route
      ON route.reached_oid = acl.grantee_oid
    LEFT JOIN role_labels AS label
      ON label.role_oid = acl.grantee_oid
),
relation_privileges(privilege_name) AS (
    VALUES
        ('SELECT'::text), ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE'),
        ('REFERENCES'), ('TRIGGER'), ('MAINTAIN')
),
owner_capabilities(root_class, target_name, privilege_name, source_class, route) AS (
    SELECT
        route.root_class,
        target.target_name,
        privilege.privilege_name,
        COALESCE(label.role_class, 'orphaned_role'),
        route.route
    FROM targets AS target
    JOIN effective_routes AS route
      ON route.reached_oid = target.owner_oid
    CROSS JOIN relation_privileges AS privilege
    LEFT JOIN role_labels AS label
      ON label.role_oid = target.owner_oid
),
attribute_capabilities(root_class, target_name, privilege_name, source_class, route) AS (
    SELECT
        route.root_class,
        target.target_name,
        privilege.privilege_name,
        COALESCE(label.role_class, 'orphaned_role'),
        route.route
    FROM effective_routes AS route
    JOIN pg_catalog.pg_roles AS role
      ON role.oid = route.reached_oid
    CROSS JOIN targets AS target
    CROSS JOIN relation_privileges AS privilege
    LEFT JOIN role_labels AS label
      ON label.role_oid = role.oid
    WHERE route.route IN ('direct', 'set')
      AND role.rolsuper
    UNION ALL
    SELECT
        route.root_class,
        target.target_name,
        privilege.privilege_name,
        label.role_class,
        route.route
    FROM effective_routes AS route
    JOIN role_labels AS label
      ON label.role_oid = route.reached_oid
    CROSS JOIN targets AS target
    CROSS JOIN relation_privileges AS privilege
    WHERE (label.role_class = 'global_read' AND privilege.privilege_name = 'SELECT')
       OR (label.role_class = 'global_write' AND privilege.privilege_name IN ('INSERT', 'UPDATE', 'DELETE'))
       OR (label.role_class = 'global_maintain' AND privilege.privilege_name = 'MAINTAIN')
),
effective_table_capabilities(root_class, target_name, privilege_name, source_class, route, grantable) AS (
    SELECT root_class, target_name, privilege_name, source_class, route, grantable
    FROM effective_table_acl
    UNION ALL
    SELECT root_class, target_name, privilege_name, source_class, route, true
    FROM owner_capabilities
    UNION ALL
    SELECT root_class, target_name, privilege_name, source_class, route, true
    FROM attribute_capabilities
),
policy_rows(target_name, policy_name, command_code, permissive, role_oid) AS (
    SELECT
        target.target_name,
        policy.polname::text,
        policy.polcmd,
        policy.polpermissive,
        policy_role.role_oid
    FROM targets AS target
    JOIN pg_catalog.pg_policy AS policy
      ON policy.polrelid = target.relation_oid
    CROSS JOIN LATERAL pg_catalog.unnest(policy.polroles) AS policy_role(role_oid)
),
applicable_policies(root_class, target_name, policy_name, command_code, permissive, source_class, route) AS (
    SELECT
        principal.role_class,
        policy.target_name,
        policy.policy_name,
        policy.command_code,
        policy.permissive,
        'PUBLIC'::text,
        'public'::text
    FROM policy_rows AS policy
    CROSS JOIN requested_principals AS principal
    WHERE policy.role_oid = 0
    UNION ALL
    SELECT
        route.root_class,
        policy.target_name,
        policy.policy_name,
        policy.command_code,
        policy.permissive,
        COALESCE(label.role_class, 'orphaned_role'),
        route.route
    FROM policy_rows AS policy
    JOIN effective_routes AS route
      ON route.reached_oid = policy.role_oid
    LEFT JOIN role_labels AS label
      ON label.role_oid = policy.role_oid
),
known_policy_shape AS (
    SELECT policy.target_name, policy.policy_name
    FROM policy_rows AS policy
    WHERE (policy.target_name = 'leads' AND policy.policy_name = 'leads_insert_public'
           AND policy.command_code = 'a' AND policy.permissive
           AND policy.role_oid = (SELECT role_oid FROM requested_principals WHERE role_class = 'anon'))
       OR (policy.target_name = 'leads' AND policy.policy_name = 'leads_insert_authenticated'
           AND policy.command_code = 'a' AND policy.permissive
           AND policy.role_oid = (SELECT role_oid FROM requested_principals WHERE role_class = 'authenticated'))
       OR (policy.target_name = 'leads' AND policy.policy_name = 'leads_service_role'
           AND policy.command_code = '*' AND policy.permissive
           AND policy.role_oid = (SELECT role_oid FROM requested_principals WHERE role_class = 'service_role'))
       OR (policy.target_name = 'email_log' AND policy.policy_name = 'email_log_service_role'
           AND policy.command_code = '*' AND policy.permissive
           AND policy.role_oid = (SELECT role_oid FROM requested_principals WHERE role_class = 'service_role'))
),
managed_policy_names(target_name, policy_name) AS (
    VALUES
        ('leads'::text, 'leads_insert_public'::text),
        ('leads', 'leads_insert_authenticated'),
        ('leads', 'leads_service_role'),
        ('email_log', 'email_log_service_role'),
        ('leads', 'leads_select_public'),
        ('leads', 'leads_select_authenticated'),
        ('email_log', 'email_log_select_public'),
        ('email_log', 'email_log_select_authenticated')
),
rewrite_edges(rule_oid, dependent_oid, referenced_oid, event_code, rule_name) AS (
    SELECT rewrite.oid, rewrite.ev_class, dependency.refobjid, rewrite.ev_type, rewrite.rulename::text
    FROM pg_catalog.pg_depend AS dependency
    JOIN pg_catalog.pg_rewrite AS rewrite
      ON rewrite.oid = dependency.objid
    WHERE dependency.classid = 'pg_catalog.pg_rewrite'::pg_catalog.regclass
      AND dependency.refclassid = 'pg_catalog.pg_class'::pg_catalog.regclass
),
target_rule_paths(target_name, rule_oid) AS (
    SELECT DISTINCT target.target_name, edge.rule_oid
    FROM targets AS target
    JOIN pg_catalog.pg_class AS relation
      ON relation.oid = target.relation_oid
    JOIN rewrite_edges AS edge
      ON edge.dependent_oid = target.relation_oid
    WHERE relation.relkind NOT IN ('v', 'm')
      AND edge.rule_name <> '_RETURN'
),
rewrite_paths(target_name, dependent_oid, rule_oid, event_code, rule_name) AS (
    SELECT target.target_name, edge.dependent_oid, edge.rule_oid, edge.event_code, edge.rule_name
    FROM targets AS target
    JOIN rewrite_edges AS edge
      ON edge.referenced_oid = target.relation_oid
     AND edge.dependent_oid <> target.relation_oid
    UNION
    SELECT path.target_name, edge.dependent_oid, edge.rule_oid, edge.event_code, edge.rule_name
    FROM rewrite_paths AS path
    JOIN rewrite_edges AS edge
      ON edge.referenced_oid = path.dependent_oid
     AND edge.dependent_oid <> path.dependent_oid
),
indirect_relation_acl(root_class, relation_oid, privilege_name, route) AS (
    SELECT principal.role_class, relation.oid, acl.privilege_type, 'public'::text
    FROM pg_catalog.pg_class AS relation
    CROSS JOIN LATERAL pg_catalog.aclexplode(relation.relacl) AS acl
    CROSS JOIN requested_principals AS principal
    WHERE acl.grantee = 0
    UNION ALL
    SELECT route.root_class, relation.oid, acl.privilege_type, route.route
    FROM pg_catalog.pg_class AS relation
    CROSS JOIN LATERAL pg_catalog.aclexplode(relation.relacl) AS acl
    JOIN effective_routes AS route
      ON route.reached_oid = acl.grantee
),
indirect_read_access(root_class, relation_oid, route) AS (
    SELECT access.root_class, access.relation_oid, access.route
    FROM indirect_relation_acl AS access
    WHERE access.privilege_name = 'SELECT'
    UNION
    SELECT principal.role_class, attribute.attrelid, 'public'::text
    FROM pg_catalog.pg_attribute AS attribute
    CROSS JOIN LATERAL pg_catalog.aclexplode(attribute.attacl) AS acl
    CROSS JOIN requested_principals AS principal
    WHERE attribute.attnum > 0
      AND NOT attribute.attisdropped
      AND acl.grantee = 0
      AND acl.privilege_type = 'SELECT'
    UNION
    SELECT route.root_class, attribute.attrelid, route.route
    FROM pg_catalog.pg_attribute AS attribute
    CROSS JOIN LATERAL pg_catalog.aclexplode(attribute.attacl) AS acl
    JOIN effective_routes AS route
      ON route.reached_oid = acl.grantee
    WHERE attribute.attnum > 0
      AND NOT attribute.attisdropped
      AND acl.privilege_type = 'SELECT'
    UNION
    SELECT route.root_class, relation.oid, route.route
    FROM pg_catalog.pg_class AS relation
    JOIN effective_routes AS route
      ON route.reached_oid = relation.relowner
    UNION
    SELECT route.root_class, relation.oid, route.route
    FROM pg_catalog.pg_class AS relation
    CROSS JOIN effective_routes AS route
    JOIN role_labels AS label
      ON label.role_oid = route.reached_oid
    WHERE label.role_class = 'global_read'
    UNION
    SELECT route.root_class, relation.oid, route.route
    FROM pg_catalog.pg_class AS relation
    CROSS JOIN effective_routes AS route
    JOIN pg_catalog.pg_roles AS role
      ON role.oid = route.reached_oid
    WHERE route.route IN ('direct', 'set')
      AND role.rolsuper
),
routine_candidates(target_name, routine_oid, dependency_kind) AS (
    SELECT target.target_name, procedure.oid, 'catalog_dependency'::text
    FROM targets AS target
    JOIN pg_catalog.pg_depend AS dependency
      ON dependency.refclassid = 'pg_catalog.pg_class'::pg_catalog.regclass
     AND dependency.refobjid = target.relation_oid
     AND dependency.classid = 'pg_catalog.pg_proc'::pg_catalog.regclass
    JOIN pg_catalog.pg_proc AS procedure
      ON procedure.oid = dependency.objid
    JOIN usable_public_schemas AS usable_schema
      ON usable_schema.namespace_oid = procedure.pronamespace
    UNION
    SELECT target.target_name, procedure.oid, 'lexical_candidate'::text
    FROM targets AS target
    JOIN pg_catalog.pg_proc AS procedure
      ON true
    JOIN usable_public_schemas AS usable_schema
      ON usable_schema.namespace_oid = procedure.pronamespace
    WHERE pg_catalog.lower(procedure.prosrc) LIKE ('%' || target.target_name || '%')
),
routine_execute_acl(root_class, routine_oid, route) AS (
    SELECT principal.role_class, procedure.oid, 'public'::text
    FROM pg_catalog.pg_proc AS procedure
    CROSS JOIN LATERAL pg_catalog.aclexplode(
        COALESCE(
            procedure.proacl,
            pg_catalog.acldefault('f', procedure.proowner)
        )
    ) AS acl
    CROSS JOIN requested_principals AS principal
    WHERE acl.grantee = 0
      AND acl.privilege_type = 'EXECUTE'
    UNION ALL
    SELECT route.root_class, procedure.oid, route.route
    FROM pg_catalog.pg_proc AS procedure
    CROSS JOIN LATERAL pg_catalog.aclexplode(
        COALESCE(
            procedure.proacl,
            pg_catalog.acldefault('f', procedure.proowner)
        )
    ) AS acl
    JOIN effective_routes AS route
      ON route.reached_oid = acl.grantee
    WHERE acl.privilege_type = 'EXECUTE'
    UNION ALL
    SELECT route.root_class, procedure.oid, route.route
    FROM pg_catalog.pg_proc AS procedure
    JOIN effective_routes AS route
      ON route.reached_oid = procedure.proowner
    UNION ALL
    SELECT route.root_class, procedure.oid, route.route
    FROM pg_catalog.pg_proc AS procedure
    CROSS JOIN effective_routes AS route
    JOIN pg_catalog.pg_roles AS role
      ON role.oid = route.reached_oid
    WHERE route.route IN ('direct', 'set')
      AND role.rolsuper
),
trigger_paths(root_class, target_name, trigger_oid, is_known, dependency_kind) AS (
    SELECT DISTINCT
        principal.root_class,
        target.target_name,
        trigger_record.oid,
        (
            trigger_record.tgname = 'trg_notify_new_lead'
            AND trigger_relation.relname = 'leads'
            AND trigger_namespace.nspname = 'public'
            AND procedure.proname = 'notify_new_lead'
            AND procedure.pronargs = 0
            AND trigger_record.tgenabled <> 'D'
        ),
        CASE
            WHEN trigger_record.tgrelid = target.relation_oid THEN 'target_trigger'
            ELSE 'routine_dependency'
        END::text
    FROM targets AS target
    JOIN pg_catalog.pg_trigger AS trigger_record
      ON NOT trigger_record.tgisinternal
    JOIN pg_catalog.pg_class AS trigger_relation
      ON trigger_relation.oid = trigger_record.tgrelid
    JOIN pg_catalog.pg_namespace AS trigger_namespace
      ON trigger_namespace.oid = trigger_relation.relnamespace
    JOIN pg_catalog.pg_proc AS procedure
      ON procedure.oid = trigger_record.tgfoid
    JOIN (
        SELECT capability.root_class, capability.target_name
        FROM effective_table_capabilities AS capability
        WHERE capability.privilege_name IN ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')
        UNION
        SELECT column_acl.root_class, column_acl.target_name
        FROM effective_column_acl AS column_acl
        WHERE column_acl.privilege_name IN ('INSERT', 'UPDATE')
    ) AS principal
      ON principal.target_name = (
          SELECT source_target.target_name
          FROM targets AS source_target
          WHERE source_target.relation_oid = trigger_record.tgrelid
      )
    WHERE trigger_record.tgrelid = target.relation_oid
       OR EXISTS (
           SELECT 1
           FROM routine_candidates AS candidate
           WHERE candidate.routine_oid = procedure.oid
             AND candidate.target_name = target.target_name
       )
),
inheritance_descendants(target_name, descendant_oid, visited) AS (
    SELECT
        target.target_name,
        inheritance.inhrelid,
        ARRAY[target.relation_oid, inheritance.inhrelid]::pg_catalog.oid[]
    FROM targets AS target
    JOIN pg_catalog.pg_inherits AS inheritance
      ON inheritance.inhparent = target.relation_oid
    UNION ALL
    SELECT
        descendant.target_name,
        inheritance.inhrelid,
        descendant.visited || inheritance.inhrelid
    FROM inheritance_descendants AS descendant
    JOIN pg_catalog.pg_inherits AS inheritance
      ON inheritance.inhparent = descendant.descendant_oid
    WHERE NOT inheritance.inhrelid = ANY(descendant.visited)
),
publication_paths AS (
    SELECT target.target_name
    FROM targets AS target
    JOIN pg_catalog.pg_publication_rel AS publication_relation
      ON publication_relation.prrelid = target.relation_oid
    UNION ALL
    SELECT target.target_name
    FROM targets AS target
    CROSS JOIN pg_catalog.pg_publication AS publication
    WHERE publication.puballtables
),
summary AS (
    SELECT
        (SELECT pg_catalog.count(*) FROM targets WHERE relation_oid IS NOT NULL AND relation_kind IN ('r', 'p'))::integer AS target_relation_count,
        (SELECT pg_catalog.count(*) FROM targets WHERE relation_oid IS NULL OR relation_kind NOT IN ('r', 'p'))::integer AS missing_target_count,
        (SELECT pg_catalog.count(*) FROM targets WHERE rls_enabled)::integer AS rls_enabled_count,
        (SELECT pg_catalog.count(*) FROM targets AS target LEFT JOIN role_labels AS label ON label.role_oid = target.owner_oid WHERE label.role_class IS DISTINCT FROM 'platform_owner')::integer AS owner_mismatch_count,
        (SELECT pg_catalog.count(*) FROM requested_principals WHERE role_class <> 'PUBLIC' AND role_oid IS NOT NULL)::integer AS requested_role_count,
        (SELECT pg_catalog.count(*) FROM effective_routes)::integer AS membership_route_count,
        (SELECT pg_catalog.count(*) FROM effective_routes WHERE route = 'inherit')::integer AS inherited_route_count,
        (SELECT pg_catalog.count(*) FROM effective_routes WHERE route = 'set')::integer AS set_route_count,
        (SELECT pg_catalog.count(*) FROM effective_routes WHERE route = 'set_then_inherit')::integer AS set_then_inherit_route_count,
        (SELECT pg_catalog.count(*) FROM effective_routes AS route JOIN role_labels AS label ON label.role_oid = route.reached_oid WHERE label.role_class = 'database_owner' AND route.min_depth > 0)::integer AS implicit_database_owner_route_count,
        (SELECT pg_catalog.count(DISTINCT (root_class, reached_oid, role_oid)) FROM membership_depth_truncations)::integer AS membership_depth_truncated_count,
        (SELECT pg_catalog.count(*) FROM membership_edges AS membership JOIN reachable_members AS reachable ON reachable.reached_oid = membership.member_oid WHERE membership.admin_option)::integer AS admin_option_count,
        (SELECT pg_catalog.count(*) FROM effective_routes AS route JOIN pg_catalog.pg_roles AS role ON role.oid = route.reached_oid WHERE route.root_class IN ('anon', 'authenticated') AND route.route IN ('direct', 'set') AND (role.rolsuper OR role.rolbypassrls OR role.rolcreaterole OR role.rolcreatedb OR role.rolreplication))::integer AS elevated_role_path_count,
        (SELECT pg_catalog.count(*) FROM requested_principals AS principal JOIN pg_catalog.pg_roles AS role ON role.oid = principal.role_oid WHERE (principal.role_class IN ('anon', 'authenticated') AND (role.rolsuper OR role.rolbypassrls OR role.rolcanlogin OR role.rolcreaterole OR role.rolcreatedb OR role.rolreplication)) OR (principal.role_class = 'service_role' AND (role.rolsuper OR NOT role.rolbypassrls OR role.rolcanlogin OR role.rolcreaterole OR role.rolcreatedb OR role.rolreplication)))::integer AS role_posture_violation_count,
        (SELECT pg_catalog.count(*) FROM requested_principals AS principal JOIN pg_catalog.pg_roles AS role ON role.oid = principal.role_oid WHERE NOT role.rolinherit)::integer AS role_inherit_default_off_count,
        (SELECT pg_catalog.count(*) FROM effective_table_acl)::integer AS table_acl_source_count,
        (SELECT pg_catalog.count(*) FROM effective_column_acl)::integer AS column_acl_source_count,
        (SELECT pg_catalog.count(*) FROM effective_schema_acl)::integer AS schema_acl_source_count,
        (SELECT pg_catalog.count(*) FROM effective_table_acl WHERE route = 'direct')::integer + (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE route = 'direct')::integer AS direct_acl_source_count,
        (SELECT pg_catalog.count(*) FROM effective_table_acl WHERE route = 'public')::integer + (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE route = 'public')::integer AS public_acl_source_count,
        (SELECT pg_catalog.count(*) FROM effective_table_acl WHERE route = 'inherit')::integer + (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE route = 'inherit')::integer AS inherited_acl_source_count,
        (SELECT pg_catalog.count(*) FROM effective_table_acl WHERE route IN ('set', 'set_then_inherit'))::integer + (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE route IN ('set', 'set_then_inherit'))::integer AS set_acl_source_count,
        (SELECT pg_catalog.count(*) FROM effective_schema_acl WHERE grantable)::integer + (SELECT pg_catalog.count(*) FROM effective_table_acl WHERE grantable)::integer + (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE grantable)::integer AS grant_option_source_count,
        (SELECT pg_catalog.count(*) FROM effective_schema_acl WHERE source_class IN ('other_role', 'orphaned_role'))::integer + (SELECT pg_catalog.count(*) FROM effective_table_acl WHERE source_class IN ('other_role', 'orphaned_role'))::integer + (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE source_class IN ('other_role', 'orphaned_role'))::integer AS unknown_acl_source_count,
        (SELECT pg_catalog.count(*) FROM requested_principals AS principal WHERE principal.role_class <> 'PUBLIC' AND (principal.role_oid IS NULL OR NOT pg_catalog.has_schema_privilege(principal.role_oid, 'public', 'USAGE')))::integer AS schema_usage_missing_count,
        (SELECT pg_catalog.count(*) FROM requested_principals AS principal WHERE principal.role_class IN ('anon', 'authenticated') AND principal.role_oid IS NOT NULL AND pg_catalog.has_schema_privilege(principal.role_oid, 'public', 'CREATE'))::integer AS public_schema_create_count,
        (SELECT pg_catalog.count(*) FROM effective_table_capabilities WHERE root_class IN ('PUBLIC', 'anon', 'authenticated'))::integer AS public_table_capability_count,
        (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE root_class IN ('PUBLIC', 'anon', 'authenticated') AND NOT (target_name = 'leads' AND privilege_name = 'INSERT' AND column_name IN (SELECT column_name FROM allowed_insert_columns) AND root_class IN ('anon', 'authenticated')))::integer AS public_denied_column_capability_count,
        (SELECT pg_catalog.count(*) FROM effective_table_capabilities WHERE root_class IN ('PUBLIC', 'anon', 'authenticated') AND privilege_name = 'SELECT')::integer + (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE root_class IN ('PUBLIC', 'anon', 'authenticated') AND privilege_name = 'SELECT')::integer AS public_select_source_count,
        (SELECT pg_catalog.count(*) FROM (SELECT role_class, column_name FROM (VALUES ('anon'::text), ('authenticated'::text)) AS expected_role(role_class) CROSS JOIN allowed_insert_columns EXCEPT SELECT root_class, column_name FROM effective_column_acl WHERE target_name = 'leads' AND privilege_name = 'INSERT') AS missing)::integer AS leads_missing_insert_column_count,
        (SELECT pg_catalog.count(*) FROM effective_column_acl WHERE target_name = 'leads' AND root_class IN ('anon', 'authenticated') AND privilege_name = 'INSERT' AND column_name NOT IN (SELECT column_name FROM allowed_insert_columns))::integer AS leads_extra_insert_column_count,
        (SELECT pg_catalog.count(*) FROM targets AS target WHERE NOT EXISTS (SELECT 1 FROM effective_table_capabilities AS capability WHERE capability.root_class = 'service_role' AND capability.target_name = target.target_name AND capability.privilege_name = 'SELECT'))::integer AS service_select_missing_count,
        (SELECT pg_catalog.count(*) FROM (VALUES ('leads'::text, 'SELECT'::text), ('leads', 'INSERT'), ('leads', 'UPDATE'), ('leads', 'DELETE'), ('email_log', 'SELECT')) AS required(target_name, privilege_name) WHERE NOT EXISTS (SELECT 1 FROM effective_table_capabilities AS capability WHERE capability.root_class = 'service_role' AND capability.target_name = required.target_name AND capability.privilege_name = required.privilege_name))::integer AS service_required_capability_missing_count,
        (SELECT pg_catalog.count(DISTINCT (target_name, policy_name)) FROM policy_rows)::integer AS policy_count,
        (SELECT pg_catalog.count(DISTINCT (policy.target_name, policy.policy_name)) FROM policy_rows AS policy JOIN managed_policy_names AS managed ON managed.target_name = policy.target_name AND managed.policy_name = policy.policy_name)::integer AS managed_preclosure_policy_count,
        (SELECT pg_catalog.count(DISTINCT (policy.target_name, policy.policy_name)) FROM applicable_policies AS policy WHERE NOT EXISTS (SELECT 1 FROM managed_policy_names AS managed WHERE managed.target_name = policy.target_name AND managed.policy_name = policy.policy_name))::integer AS unmanaged_policy_count,
        (SELECT pg_catalog.count(*) FROM applicable_policies)::integer AS applicable_policy_source_count,
        (SELECT pg_catalog.count(*) FROM applicable_policies WHERE root_class IN ('PUBLIC', 'anon', 'authenticated') AND command_code IN ('r', '*'))::integer AS public_select_policy_count,
        ((SELECT pg_catalog.count(*) FROM policy_rows) - (SELECT pg_catalog.count(*) FROM known_policy_shape) + pg_catalog.abs(4 - (SELECT pg_catalog.count(*) FROM known_policy_shape)))::integer AS unexpected_policy_count,
        (SELECT pg_catalog.count(*) FROM owner_capabilities)::integer AS owner_access_source_count,
        (SELECT pg_catalog.count(*) FROM owner_capabilities WHERE root_class IN ('PUBLIC', 'anon', 'authenticated'))::integer AS public_owner_access_count,
        (SELECT pg_catalog.count(*) FROM rewrite_paths AS path JOIN pg_catalog.pg_class AS relation ON relation.oid = path.dependent_oid JOIN indirect_read_access AS access ON access.relation_oid = path.dependent_oid WHERE relation.relkind IN ('v', 'm') AND access.root_class IN ('PUBLIC', 'anon', 'authenticated'))::integer AS indirect_view_path_count,
        (SELECT pg_catalog.count(*) FROM rewrite_paths AS path JOIN pg_catalog.pg_class AS relation ON relation.oid = path.dependent_oid JOIN indirect_relation_acl AS access ON access.relation_oid = path.dependent_oid WHERE relation.relkind NOT IN ('v', 'm') AND access.root_class IN ('PUBLIC', 'anon', 'authenticated'))::integer AS indirect_rule_path_count,
        (SELECT pg_catalog.count(*) FROM target_rule_paths)::integer AS target_rule_path_count,
        (SELECT pg_catalog.count(*) FROM routine_candidates AS candidate JOIN pg_catalog.pg_proc AS procedure ON procedure.oid = candidate.routine_oid JOIN routine_execute_acl AS access ON access.routine_oid = candidate.routine_oid WHERE procedure.prosecdef AND access.root_class IN ('PUBLIC', 'anon', 'authenticated'))::integer AS indirect_security_definer_path_count,
        (SELECT pg_catalog.count(*) FROM trigger_paths WHERE root_class IN ('PUBLIC', 'anon', 'authenticated'))::integer AS indirect_trigger_path_count,
        (SELECT pg_catalog.count(*) FROM trigger_paths WHERE root_class IN ('PUBLIC', 'anon', 'authenticated') AND NOT is_known)::integer AS unexpected_trigger_path_count,
        (SELECT pg_catalog.count(*) FROM pg_catalog.pg_proc AS procedure JOIN usable_public_schemas AS usable_schema ON usable_schema.namespace_oid = procedure.pronamespace JOIN routine_execute_acl AS access ON access.routine_oid = procedure.oid WHERE procedure.prosecdef AND access.root_class IN ('PUBLIC', 'anon', 'authenticated') AND (pg_catalog.lower(procedure.prosrc) LIKE '%execute%' OR NOT EXISTS (SELECT 1 FROM routine_candidates AS candidate WHERE candidate.routine_oid = procedure.oid)))::integer AS dynamic_indirect_path_count,
        (SELECT pg_catalog.count(*) FROM publication_paths)::integer AS publication_path_count,
        (SELECT pg_catalog.count(DISTINCT (target_name, descendant_oid)) FROM inheritance_descendants)::integer AS partition_descendant_count
),
decision AS (
    SELECT
        summary.*,
        (
            pg_catalog.current_setting('server_version_num')::integer >= 170000
            AND pg_catalog.current_setting('server_version_num')::integer < 180000
            AND (SELECT policy_expression_attested FROM contract_constants)
            AND summary.missing_target_count = 0
            AND summary.requested_role_count = 3
            AND summary.membership_depth_truncated_count = 0
            AND summary.rls_enabled_count = 2
            AND summary.owner_mismatch_count = 0
            AND summary.role_posture_violation_count = 0
            AND summary.elevated_role_path_count = 0
            AND summary.admin_option_count = 0
            AND summary.unknown_acl_source_count = 0
            AND summary.schema_usage_missing_count = 0
            AND summary.public_schema_create_count = 0
            AND summary.public_table_capability_count = 0
            AND summary.public_denied_column_capability_count = 0
            AND summary.public_select_source_count = 0
            AND summary.leads_missing_insert_column_count = 0
            AND summary.leads_extra_insert_column_count = 0
            AND summary.service_select_missing_count = 0
            AND summary.service_required_capability_missing_count = 0
            AND summary.policy_count = 4
            AND summary.unexpected_policy_count = 0
            AND summary.public_select_policy_count = 0
            AND summary.public_owner_access_count = 0
            AND summary.indirect_view_path_count = 0
            AND summary.indirect_rule_path_count = 0
            AND summary.target_rule_path_count = 0
            AND summary.indirect_security_definer_path_count = 0
            AND summary.unexpected_trigger_path_count = 0
            AND summary.dynamic_indirect_path_count = 0
            AND summary.publication_path_count = 0
            AND summary.partition_descendant_count = 0
        ) AS catalog_comparison_pass
    FROM summary
),
assessment AS (
    SELECT
        decision.*,
        CASE
            WHEN pg_catalog.current_setting('server_version_num')::integer < 170000
              OR pg_catalog.current_setting('server_version_num')::integer >= 180000
              OR decision.missing_target_count > 0
              OR decision.requested_role_count <> 3
              OR decision.membership_depth_truncated_count > 0 THEN 'unknown'
            WHEN decision.inherited_acl_source_count > 0
              OR decision.set_acl_source_count > 0
              OR decision.public_owner_access_count > 0
              OR decision.elevated_role_path_count > 0
              OR decision.admin_option_count > 0
              OR decision.role_posture_violation_count > 0
              OR decision.role_inherit_default_off_count > 0
              OR decision.owner_mismatch_count > 0
              OR decision.unknown_acl_source_count > 0
              OR decision.schema_usage_missing_count > 0
              OR decision.public_schema_create_count > 0
              OR decision.service_required_capability_missing_count > decision.service_select_missing_count
              OR decision.unmanaged_policy_count > 0
              OR decision.indirect_view_path_count > 0
              OR decision.indirect_rule_path_count > 0
              OR decision.target_rule_path_count > 0
              OR decision.indirect_security_definer_path_count > 0
              OR decision.unexpected_trigger_path_count > 0
              OR decision.dynamic_indirect_path_count > 0
              OR decision.publication_path_count > 0
              OR decision.partition_descendant_count > 0
              OR EXISTS (
                  SELECT 1
                  FROM effective_schema_acl AS acl
                  WHERE acl.grantable
              )
              OR EXISTS (
                  SELECT 1
                  FROM effective_table_acl AS acl
                  WHERE acl.grantable
                    AND NOT (
                        acl.root_class IN ('PUBLIC', 'anon', 'authenticated')
                        AND acl.route IN ('public', 'direct')
                    )
              )
              OR EXISTS (
                  SELECT 1
                  FROM effective_column_acl AS acl
                  WHERE acl.grantable
                    AND NOT (
                        acl.root_class IN ('PUBLIC', 'anon', 'authenticated')
                        AND acl.route IN ('public', 'direct')
                    )
              ) THEN 'incomplete'
            ELSE 'complete'
        END::text AS package_source_coverage,
        (decision.indirect_trigger_path_count > 0
         OR decision.dynamic_indirect_path_count > 0) AS supplemental_required
    FROM decision
)
SELECT
    'F9.7-ACL-SOURCE-CATALOG-PG17-V1'::text AS query_id,
    1::integer AS schema_version,
    'observed_only_not_convergence'::text AS snapshot_claim,
    CASE
        WHEN pg_catalog.current_setting('server_version_num')::integer < 170000
          OR pg_catalog.current_setting('server_version_num')::integer >= 180000
          OR assessment.missing_target_count > 0
          OR assessment.requested_role_count <> 3
          OR assessment.membership_depth_truncated_count > 0 THEN 'unknown'
        WHEN assessment.catalog_comparison_pass THEN 'complete'
        ELSE 'incomplete'
    END::text AS closure_coverage,
    assessment.package_source_coverage,
    (SELECT policy_expression_attested FROM contract_constants) AS policy_expression_attested,
    (pg_catalog.current_setting('server_version_num')::integer >= 170000
     AND pg_catalog.current_setting('server_version_num')::integer < 180000) AS pg17_semantics_supported,
    assessment.target_relation_count,
    assessment.missing_target_count,
    assessment.rls_enabled_count,
    assessment.owner_mismatch_count,
    assessment.requested_role_count,
    assessment.role_posture_violation_count,
    assessment.role_inherit_default_off_count,
    assessment.membership_route_count,
    assessment.inherited_route_count,
    assessment.set_route_count,
    assessment.set_then_inherit_route_count,
    assessment.implicit_database_owner_route_count,
    assessment.membership_depth_truncated_count,
    assessment.admin_option_count,
    assessment.elevated_role_path_count,
    assessment.table_acl_source_count,
    assessment.column_acl_source_count,
    assessment.schema_acl_source_count,
    assessment.direct_acl_source_count,
    assessment.public_acl_source_count,
    assessment.inherited_acl_source_count,
    assessment.set_acl_source_count,
    assessment.grant_option_source_count,
    assessment.unknown_acl_source_count,
    assessment.schema_usage_missing_count,
    assessment.public_schema_create_count,
    assessment.public_table_capability_count,
    assessment.public_denied_column_capability_count,
    assessment.public_select_source_count,
    assessment.leads_missing_insert_column_count,
    assessment.leads_extra_insert_column_count,
    assessment.service_select_missing_count,
    assessment.service_required_capability_missing_count,
    assessment.policy_count,
    assessment.managed_preclosure_policy_count,
    assessment.unmanaged_policy_count,
    assessment.applicable_policy_source_count,
    assessment.public_select_policy_count,
    assessment.unexpected_policy_count,
    assessment.owner_access_source_count,
    assessment.public_owner_access_count,
    assessment.indirect_view_path_count,
    assessment.indirect_rule_path_count,
    assessment.target_rule_path_count,
    assessment.indirect_security_definer_path_count,
    assessment.indirect_trigger_path_count,
    assessment.unexpected_trigger_path_count,
    assessment.dynamic_indirect_path_count,
    assessment.publication_path_count,
    assessment.partition_descendant_count,
    assessment.catalog_comparison_pass,
    (
        NOT assessment.catalog_comparison_pass
        OR assessment.package_source_coverage <> 'complete'
        OR assessment.supplemental_required
    ) AS fail_closed,
    assessment.supplemental_required AS requires_supplemental_attestation
FROM assessment;
