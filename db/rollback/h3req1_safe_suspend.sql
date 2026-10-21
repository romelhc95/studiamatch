-- H3REQ1 compensating rollback: SAFE SUSPENSION, not a downgrade to old SQL.
-- Local Docker drill only unless a separate exact remote DDL JIT is approved.
-- Keep hardened readers, functions, additive columns, cohorts and append-only
-- audit/history. Never restore a reader that ignores fresh unavailable evidence.
-- Block initiating mutations before rolling back the BFF/Edge artifact. Allow
-- completion/failure/reconciliation of in-flight invitations to finish safely.
-- The private ACL snapshot is durable across sessions; it is metadata, not a secret.
BEGIN;
CREATE TABLE IF NOT EXISTS private.h3req1_safe_suspend_acl_snapshots (
  snapshot_id UUID PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
  database_oid OID NOT NULL,
  database_name NAME NOT NULL,
  captured_by NAME NOT NULL,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT pg_catalog.clock_timestamp(),
  state TEXT NOT NULL CHECK (state IN ('suspended','resumed')),
  grant_snapshot JSONB NOT NULL CHECK (pg_catalog.jsonb_typeof(grant_snapshot) = 'array'),
  original_fingerprint TEXT NOT NULL CHECK (original_fingerprint ~ '^[0-9a-f]{64}$'),
  snapshot_fingerprint TEXT NOT NULL CHECK (snapshot_fingerprint ~ '^[0-9a-f]{64}$'),
  suspended_fingerprint TEXT NOT NULL CHECK (suspended_fingerprint ~ '^[0-9a-f]{64}$'),
  resumed_fingerprint TEXT,
  resumed_at TIMESTAMPTZ,
  CHECK (
    (state = 'suspended' AND resumed_fingerprint IS NULL AND resumed_at IS NULL)
    OR (state = 'resumed' AND resumed_fingerprint IS NOT NULL AND resumed_at IS NOT NULL)
  )
);
CREATE UNIQUE INDEX IF NOT EXISTS h3req1_safe_suspend_one_active_snapshot
  ON private.h3req1_safe_suspend_acl_snapshots (state) WHERE state = 'suspended';
REVOKE ALL ON TABLE private.h3req1_safe_suspend_acl_snapshots FROM PUBLIC, anon, authenticated, service_role;

DO $$
DECLARE
  operation TEXT;
  target REGPROCEDURE;
  active_snapshot private.h3req1_safe_suspend_acl_snapshots%ROWTYPE;
  blocked_operations TEXT[] := ARRAY[
    'admin_update_course', 'admin_set_course_availability',
    'admin_publish_course', 'admin_unpublish_course', 'admin_archive_course',
    'admin_update_quality_status', 'admin_update_member',
    'admin_create_member', 'admin_invitation_reserve', 'admin_signed_rpc'
  ];
  expected_grants JSONB := '{
    "admin_update_course":{"signature":"public.admin_update_course(uuid,jsonb,integer,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_set_course_availability":{"signature":"public.admin_set_course_availability(uuid,text,text,timestamp with time zone,timestamp with time zone,integer,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_publish_course":{"signature":"public.admin_publish_course(uuid,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_unpublish_course":{"signature":"public.admin_unpublish_course(uuid,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_archive_course":{"signature":"public.admin_archive_course(uuid,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_update_quality_status":{"signature":"public.admin_update_quality_status(uuid,text,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_update_member":{"signature":"public.admin_update_member(uuid,text,boolean,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_create_member":{"signature":"public.admin_create_member(text,text)","authenticated_execute":true,"service_role_execute":true},
    "admin_invitation_reserve":{"signature":"public.admin_invitation_reserve(text,text,uuid,uuid,boolean,text,jsonb,timestamp with time zone)","authenticated_execute":false,"service_role_execute":true},
    "admin_signed_rpc":{"signature":"public.admin_signed_rpc(text,jsonb,text)","authenticated_execute":true,"service_role_execute":false}
  }'::JSONB;
  current_role_oid OID;
  anon_role_oid OID;
  authenticated_role_oid OID;
  service_role_oid OID;
  current_database_oid OID;
  table_owner_oid OID;
  target_count INTEGER;
  active_snapshot_count INTEGER;
  snapshot_id UUID;
  grant_snapshot JSONB;
  original_fingerprint TEXT;
  suspended_fingerprint TEXT;
  snapshot_fingerprint TEXT;
  captured_at TIMESTAMPTZ := pg_catalog.clock_timestamp();
BEGIN
  PERFORM pg_catalog.set_config('search_path', 'pg_catalog, public', TRUE);
  PERFORM pg_catalog.pg_advisory_xact_lock(753131, 5042026);
  IF pg_catalog.to_regnamespace('private') IS NULL
     OR pg_catalog.to_regclass('public.course_editorial_audit') IS NULL
     OR pg_catalog.to_regclass('public.admin_invitations') IS NULL THEN
    RAISE EXCEPTION 'Safe suspension requires the reviewed H3 schema';
  END IF;

  SELECT oid INTO current_role_oid FROM pg_catalog.pg_roles WHERE rolname = current_user;
  SELECT oid INTO anon_role_oid FROM pg_catalog.pg_roles WHERE rolname = 'anon';
  SELECT oid INTO authenticated_role_oid FROM pg_catalog.pg_roles WHERE rolname = 'authenticated';
  SELECT oid INTO service_role_oid FROM pg_catalog.pg_roles WHERE rolname = 'service_role';
  SELECT oid INTO current_database_oid FROM pg_catalog.pg_database
  WHERE datname = pg_catalog.current_database();
  SELECT relowner INTO table_owner_oid FROM pg_catalog.pg_class
  WHERE oid = 'private.h3req1_safe_suspend_acl_snapshots'::regclass;

  IF current_role_oid IS NULL OR anon_role_oid IS NULL
     OR authenticated_role_oid IS NULL OR service_role_oid IS NULL
     OR current_database_oid IS NULL OR table_owner_oid <> current_role_oid THEN
    RAISE EXCEPTION 'Safe suspension identity, database or snapshot owner check failed';
  END IF;
  IF (SELECT count(*) FROM pg_catalog.pg_attribute
      WHERE attrelid = 'private.h3req1_safe_suspend_acl_snapshots'::regclass
        AND attnum > 0 AND NOT attisdropped) <> 12
     OR EXISTS (
       SELECT 1 FROM (VALUES
         ('snapshot_id', 'uuid'::regtype::OID),
         ('database_oid', 'oid'::regtype::OID),
         ('database_name', 'name'::regtype::OID),
         ('captured_by', 'name'::regtype::OID),
         ('captured_at', 'timestamptz'::regtype::OID),
         ('state', 'text'::regtype::OID),
         ('grant_snapshot', 'jsonb'::regtype::OID),
         ('original_fingerprint', 'text'::regtype::OID),
         ('snapshot_fingerprint', 'text'::regtype::OID),
         ('suspended_fingerprint', 'text'::regtype::OID),
         ('resumed_fingerprint', 'text'::regtype::OID),
         ('resumed_at', 'timestamptz'::regtype::OID)
       ) expected(column_name, type_oid)
       LEFT JOIN pg_catalog.pg_attribute a
         ON a.attrelid = 'private.h3req1_safe_suspend_acl_snapshots'::regclass
        AND a.attname::TEXT = expected.column_name AND a.attnum > 0 AND NOT a.attisdropped
       WHERE a.attname IS NULL OR a.atttypid <> expected.type_oid
     ) THEN
    RAISE EXCEPTION 'Safe suspension snapshot table shape drift';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_index i
    JOIN pg_catalog.pg_class index_relation ON index_relation.oid = i.indexrelid
    WHERE i.indrelid = 'private.h3req1_safe_suspend_acl_snapshots'::regclass
      AND index_relation.relname = 'h3req1_safe_suspend_one_active_snapshot'
      AND i.indisunique AND i.indisvalid AND i.indisready
      AND i.indnkeyatts = 1 AND i.indnatts = 1
      AND pg_catalog.pg_get_indexdef(i.indexrelid, 1, TRUE) = 'state'
      AND i.indpred IS NOT NULL
      AND pg_catalog.pg_get_expr(i.indpred, i.indrelid)
        ~ '^\(*state\)* = ''suspended''(::text)?\)*$'
  ) THEN
    RAISE EXCEPTION 'Safe suspension active-snapshot uniqueness index drifted';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM pg_catalog.pg_class c
    CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(c.relacl, pg_catalog.acldefault('r', c.relowner))) acl
    WHERE c.oid = 'private.h3req1_safe_suspend_acl_snapshots'::regclass
      AND acl.grantee <> c.relowner
  ) OR EXISTS (
    SELECT 1 FROM pg_catalog.pg_attribute a
    WHERE a.attrelid = 'private.h3req1_safe_suspend_acl_snapshots'::regclass
      AND a.attnum > 0 AND NOT a.attisdropped AND a.attacl IS NOT NULL
  ) OR EXISTS (
    SELECT 1 FROM (VALUES ('anon'), ('authenticated'), ('service_role')) roles(role_name)
    CROSS JOIN (VALUES ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE'),
                       ('TRUNCATE'), ('REFERENCES'), ('TRIGGER')) privileges(privilege_name)
    WHERE pg_catalog.has_table_privilege(roles.role_name,
      'private.h3req1_safe_suspend_acl_snapshots', privileges.privilege_name)
  ) THEN
    RAISE EXCEPTION 'Safe suspension snapshot is exposed beyond its owner';
  END IF;

  SELECT count(*) INTO target_count
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations);
  IF target_count <> pg_catalog.cardinality(blocked_operations)
     OR (SELECT count(*) FROM pg_catalog.jsonb_object_keys(expected_grants))
       <> pg_catalog.cardinality(blocked_operations)
     OR EXISTS (
       SELECT 1 FROM pg_catalog.jsonb_each(expected_grants) expected(operation_name, contract)
       WHERE pg_catalog.to_regprocedure(expected.contract ->> 'signature') IS NULL
          OR NOT EXISTS (
            SELECT 1 FROM pg_catalog.pg_proc p
            JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public'
              AND p.oid = pg_catalog.to_regprocedure(expected.contract ->> 'signature')::OID
              AND p.proname = expected.operation_name
          )
     ) THEN
    RAISE EXCEPTION 'Safe suspension target signatures or overload count drifted';
  END IF;

  SELECT count(*) INTO active_snapshot_count
  FROM private.h3req1_safe_suspend_acl_snapshots
  WHERE state = 'suspended';
  IF active_snapshot_count > 1 THEN
    RAISE EXCEPTION 'Multiple persistent safe-suspend snapshots exist; keep the system suspended';
  END IF;
  SELECT * INTO active_snapshot
  FROM private.h3req1_safe_suspend_acl_snapshots
  WHERE state = 'suspended'
  FOR UPDATE;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.jsonb_each(expected_grants) expected(operation_name, contract)
    JOIN pg_catalog.pg_proc p
      ON p.oid = pg_catalog.to_regprocedure(expected.contract ->> 'signature')::OID
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proowner <> current_role_oid
  ) THEN
    RAISE EXCEPTION 'Safe suspension must run as the owner of every target function';
  END IF;
  IF active_snapshot_count = 0 AND EXISTS (
    SELECT 1 FROM pg_catalog.jsonb_each(expected_grants) expected(operation_name, contract)
    JOIN pg_catalog.pg_proc p
      ON p.oid = pg_catalog.to_regprocedure(expected.contract ->> 'signature')::OID
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND (
      COALESCE((SELECT pg_catalog.bool_or(acl.grantee = authenticated_role_oid
           AND acl.privilege_type = 'EXECUTE')
         FROM pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl), FALSE)
         IS DISTINCT FROM (expected.contract ->> 'authenticated_execute')::BOOLEAN
      OR COALESCE((SELECT pg_catalog.bool_or(acl.grantee = service_role_oid
           AND acl.privilege_type = 'EXECUTE')
         FROM pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl), FALSE)
         IS DISTINCT FROM (expected.contract ->> 'service_role_execute')::BOOLEAN
      OR pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
      OR pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
         IS DISTINCT FROM (expected.contract ->> 'authenticated_execute')::BOOLEAN
      OR pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE')
         IS DISTINCT FROM (expected.contract ->> 'service_role_execute')::BOOLEAN
    )
  ) THEN
    RAISE EXCEPTION 'Safe suspension expected role ACL drifted';
  END IF;

  IF active_snapshot_count = 1 THEN
    SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(pg_catalog.concat_ws('|', active_snapshot.snapshot_id::TEXT,
      active_snapshot.database_oid::TEXT, active_snapshot.database_name::TEXT,
      active_snapshot.captured_by::TEXT,
      pg_catalog.to_char(active_snapshot.captured_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US'),
      active_snapshot.grant_snapshot::TEXT, active_snapshot.original_fingerprint,
      active_snapshot.suspended_fingerprint), 'UTF8')), 'hex') INTO snapshot_fingerprint;
    IF active_snapshot.database_oid <> current_database_oid
       OR active_snapshot.database_name <> pg_catalog.current_database()
       OR active_snapshot.captured_by <> current_user
       OR active_snapshot.snapshot_fingerprint <> snapshot_fingerprint
       OR pg_catalog.jsonb_typeof(active_snapshot.grant_snapshot) <> 'array'
       OR pg_catalog.jsonb_array_length(active_snapshot.grant_snapshot) <> target_count THEN
      RAISE EXCEPTION 'Safe suspension snapshot identity or integrity check failed';
    END IF;
    SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(COALESCE(pg_catalog.string_agg(
      pg_catalog.concat_ws(':', p.oid::TEXT, p.oid::REGPROCEDURE::TEXT, p.proowner::TEXT,
        COALESCE((SELECT pg_catalog.string_agg(
          pg_catalog.concat_ws(':', acl.grantee::TEXT, acl.grantor::TEXT,
            acl.privilege_type, acl.is_grantable::TEXT), ','
          ORDER BY acl.grantee, acl.grantor, acl.privilege_type, acl.is_grantable)
          FROM pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl
          WHERE acl.privilege_type = 'EXECUTE'), '<no-acl>')),
      E'\n' ORDER BY p.oid), 'no-target-functions'), 'UTF8')), 'hex') INTO suspended_fingerprint
    FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations);
    IF active_snapshot.suspended_fingerprint <> suspended_fingerprint
       OR EXISTS (
         SELECT 1 FROM pg_catalog.pg_proc p
         JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
         WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
           AND (pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
             OR pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
             OR pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE'))
       ) THEN
      RAISE EXCEPTION 'Safe suspension idempotency check failed; keep the system suspended';
    END IF;
    SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
      'function_oid', p.oid::TEXT,
      'signature', p.oid::REGPROCEDURE::TEXT,
      'owner_oid', p.proowner::TEXT,
      'authenticated_execute', (expected.contract ->> 'authenticated_execute')::BOOLEAN,
      'service_role_execute', (expected.contract ->> 'service_role_execute')::BOOLEAN
    ) ORDER BY p.oid), '[]'::JSONB) INTO grant_snapshot
    FROM pg_catalog.jsonb_each(expected_grants) expected(operation_name, contract)
    JOIN pg_catalog.pg_proc p
      ON p.oid = pg_catalog.to_regprocedure(expected.contract ->> 'signature')::OID;
    IF active_snapshot.grant_snapshot <> grant_snapshot THEN
      RAISE EXCEPTION 'Safe suspension persistent allowlist snapshot does not match the approved ACL contract';
    END IF;
    RAISE NOTICE 'Safe suspension already active; persistent recovery snapshot verified';
    RETURN;
  END IF;

  IF active_snapshot_count = 0 AND EXISTS (
    SELECT 1 FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    CROSS JOIN LATERAL pg_catalog.aclexplode(
      COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl
    WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
      AND acl.privilege_type = 'EXECUTE'
      AND acl.grantee NOT IN (p.proowner, authenticated_role_oid, service_role_oid)
  ) THEN
    RAISE EXCEPTION 'Safe suspension found PUBLIC, anon or an unknown EXECUTE grantee';
  END IF;
  IF active_snapshot_count = 0 AND EXISTS (
    SELECT 1 FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    CROSS JOIN LATERAL pg_catalog.aclexplode(
      COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl
    WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
      AND acl.privilege_type = 'EXECUTE'
      AND acl.grantee IN (authenticated_role_oid, service_role_oid)
      AND (acl.grantor <> p.proowner OR acl.is_grantable)
  ) THEN
    RAISE EXCEPTION 'Safe suspension found an unreviewed grantor or grant option';
  END IF;
  IF active_snapshot_count = 0 AND EXISTS (
    SELECT 1 FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
      AND pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
  ) THEN
    RAISE EXCEPTION 'Safe suspension found effective anon access before capture';
  END IF;

  SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
    'function_oid', p.oid::TEXT,
    'signature', p.oid::REGPROCEDURE::TEXT,
    'owner_oid', p.proowner::TEXT,
    'authenticated_execute', (expected.contract ->> 'authenticated_execute')::BOOLEAN,
    'service_role_execute', (expected.contract ->> 'service_role_execute')::BOOLEAN
  ) ORDER BY p.oid), '[]'::JSONB) INTO grant_snapshot
  FROM pg_catalog.jsonb_each(expected_grants) expected(operation_name, contract)
  JOIN pg_catalog.pg_proc p
    ON p.oid = pg_catalog.to_regprocedure(expected.contract ->> 'signature')::OID;

  SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(COALESCE(pg_catalog.string_agg(
    pg_catalog.concat_ws(':', p.oid::TEXT, p.oid::REGPROCEDURE::TEXT, p.proowner::TEXT,
      COALESCE((SELECT pg_catalog.string_agg(
        pg_catalog.concat_ws(':', acl.grantee::TEXT, acl.grantor::TEXT,
          acl.privilege_type, acl.is_grantable::TEXT), ','
        ORDER BY acl.grantee, acl.grantor, acl.privilege_type, acl.is_grantable)
        FROM pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl
        WHERE acl.privilege_type = 'EXECUTE'), '<no-acl>')),
    E'\n' ORDER BY p.oid), 'no-target-functions'), 'UTF8')), 'hex') INTO original_fingerprint
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations);

  FOREACH operation IN ARRAY blocked_operations LOOP
    FOR target IN
      SELECT p.oid::REGPROCEDURE
      FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
      WHERE n.nspname = 'public' AND p.proname = operation
    LOOP
      EXECUTE pg_catalog.format(
        'REVOKE ALL ON FUNCTION %s FROM PUBLIC, anon, authenticated, service_role', target);
    END LOOP;
  END LOOP;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
      AND (pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
        OR pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
        OR pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE'))
  ) THEN
    RAISE EXCEPTION 'Safe suspension left effective API EXECUTE access; transaction aborted';
  END IF;

  SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(COALESCE(pg_catalog.string_agg(
    pg_catalog.concat_ws(':', p.oid::TEXT, p.oid::REGPROCEDURE::TEXT, p.proowner::TEXT,
      COALESCE((SELECT pg_catalog.string_agg(
        pg_catalog.concat_ws(':', acl.grantee::TEXT, acl.grantor::TEXT,
          acl.privilege_type, acl.is_grantable::TEXT), ','
        ORDER BY acl.grantee, acl.grantor, acl.privilege_type, acl.is_grantable)
        FROM pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl
        WHERE acl.privilege_type = 'EXECUTE'), '<no-acl>')),
    E'\n' ORDER BY p.oid), 'no-target-functions'), 'UTF8')), 'hex') INTO suspended_fingerprint
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations);

  snapshot_id := pg_catalog.gen_random_uuid();
  snapshot_fingerprint := pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
    pg_catalog.concat_ws('|', snapshot_id::TEXT, current_database_oid::TEXT,
      pg_catalog.current_database(), current_user,
      pg_catalog.to_char(captured_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US'),
      grant_snapshot::TEXT, original_fingerprint, suspended_fingerprint), 'UTF8')), 'hex');
  INSERT INTO private.h3req1_safe_suspend_acl_snapshots (
    snapshot_id, database_oid, database_name, captured_by, captured_at, state, grant_snapshot,
    original_fingerprint, snapshot_fingerprint, suspended_fingerprint
  ) VALUES (
    snapshot_id, current_database_oid, pg_catalog.current_database(), current_user, captured_at,
    'suspended', grant_snapshot, original_fingerprint, snapshot_fingerprint,
    suspended_fingerprint
  );
END;
$$;
COMMIT;
