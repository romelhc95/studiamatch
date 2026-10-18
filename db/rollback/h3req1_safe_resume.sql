-- H3REQ1 controlled recovery from a persistent safe-suspend ACL snapshot.
-- Restores only captured authenticated/service_role grants after strict identity,
-- signature, owner and fingerprint checks. It never changes Pages/Edge flags.
-- Keep both suspended until this SQL result and a controlled smoke are verified.
-- Local Docker only unless a separate exact remote DDL JIT is approved.
DO $$
DECLARE
  active_snapshot private.h3req1_safe_suspend_acl_snapshots%ROWTYPE;
  item JSONB;
  target REGPROCEDURE;
  target_oid OID;
  current_role_oid OID;
  anon_role_oid OID;
  authenticated_role_oid OID;
  service_role_oid OID;
  current_database_oid OID;
  table_owner_oid OID;
  target_count INTEGER;
  active_snapshot_count INTEGER;
  snapshot_fingerprint TEXT;
  current_fingerprint TEXT;
  restored_fingerprint TEXT;
  snapshot_entries INTEGER := 0;
  already_resumed BOOLEAN := FALSE;
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
BEGIN
  PERFORM pg_catalog.set_config('search_path', 'pg_catalog, public', TRUE);
  PERFORM pg_catalog.pg_advisory_xact_lock(753131, 5042026);
  IF pg_catalog.to_regclass('private.h3req1_safe_suspend_acl_snapshots') IS NULL THEN
    RAISE EXCEPTION 'Persistent safe-suspend snapshot is missing; do not resume';
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
    RAISE EXCEPTION 'Safe resume identity, database or snapshot owner check failed';
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
    RAISE EXCEPTION 'Safe resume snapshot table shape drift';
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
    RAISE EXCEPTION 'Safe resume active-snapshot uniqueness index drifted';
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
    RAISE EXCEPTION 'Safe resume snapshot is exposed beyond its owner';
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
     ) OR EXISTS (
       SELECT 1 FROM pg_catalog.jsonb_each(expected_grants) expected(operation_name, contract)
       JOIN pg_catalog.pg_proc p
         ON p.oid = pg_catalog.to_regprocedure(expected.contract ->> 'signature')::OID
       WHERE p.proowner <> current_role_oid
     ) THEN
    RAISE EXCEPTION 'Safe resume target signatures, overload count or owner drifted';
  END IF;

  SELECT count(*) INTO active_snapshot_count
  FROM private.h3req1_safe_suspend_acl_snapshots
  WHERE state = 'suspended';
  IF active_snapshot_count > 1 THEN
    RAISE EXCEPTION 'Multiple active safe-suspend snapshots exist; do not resume';
  END IF;
  SELECT * INTO active_snapshot
  FROM private.h3req1_safe_suspend_acl_snapshots
  WHERE state = 'suspended'
  FOR UPDATE;
  IF NOT FOUND THEN
    SELECT * INTO active_snapshot
    FROM private.h3req1_safe_suspend_acl_snapshots
    WHERE state = 'resumed'
    ORDER BY resumed_at DESC
    LIMIT 1;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'No persistent safe-suspend snapshot exists; do not resume';
    END IF;
    already_resumed := TRUE;
  END IF;

  snapshot_fingerprint := pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(pg_catalog.concat_ws('|', active_snapshot.snapshot_id::TEXT,
    active_snapshot.database_oid::TEXT, active_snapshot.database_name::TEXT,
    active_snapshot.captured_by::TEXT,
    pg_catalog.to_char(active_snapshot.captured_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US'),
    active_snapshot.grant_snapshot::TEXT, active_snapshot.original_fingerprint,
    active_snapshot.suspended_fingerprint), 'UTF8')), 'hex');
  IF active_snapshot.database_oid <> current_database_oid
     OR active_snapshot.database_name <> pg_catalog.current_database()
     OR active_snapshot.captured_by <> current_user
     OR active_snapshot.snapshot_fingerprint <> snapshot_fingerprint
     OR pg_catalog.jsonb_typeof(active_snapshot.grant_snapshot) <> 'array'
     OR pg_catalog.jsonb_array_length(active_snapshot.grant_snapshot) <> target_count THEN
    RAISE EXCEPTION 'Safe resume snapshot identity, integrity or coverage check failed';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_catalog.jsonb_array_elements(active_snapshot.grant_snapshot) e(value)
    WHERE pg_catalog.jsonb_typeof(e.value -> 'function_oid') <> 'string'
       OR pg_catalog.jsonb_typeof(e.value -> 'signature') <> 'string'
       OR pg_catalog.jsonb_typeof(e.value -> 'owner_oid') <> 'string'
       OR pg_catalog.jsonb_typeof(e.value -> 'authenticated_execute') <> 'boolean'
       OR pg_catalog.jsonb_typeof(e.value -> 'service_role_execute') <> 'boolean'
  ) OR (
    SELECT count(DISTINCT e.value ->> 'function_oid')
    FROM pg_catalog.jsonb_array_elements(active_snapshot.grant_snapshot) e(value)
  ) <> target_count OR EXISTS (
    SELECT 1 FROM pg_catalog.jsonb_each(expected_grants) expected(operation_name, contract)
    JOIN pg_catalog.pg_proc p
      ON p.oid = pg_catalog.to_regprocedure(expected.contract ->> 'signature')::OID
    WHERE NOT EXISTS (
      SELECT 1 FROM pg_catalog.jsonb_array_elements(active_snapshot.grant_snapshot) e(value)
      WHERE (e.value ->> 'function_oid')::OID = p.oid
        AND e.value ->> 'signature' = p.oid::REGPROCEDURE::TEXT
        AND e.value ->> 'owner_oid' = p.proowner::TEXT
        AND (e.value ->> 'authenticated_execute')::BOOLEAN
          IS NOT DISTINCT FROM (expected.contract ->> 'authenticated_execute')::BOOLEAN
        AND (e.value ->> 'service_role_execute')::BOOLEAN
          IS NOT DISTINCT FROM (expected.contract ->> 'service_role_execute')::BOOLEAN
    )
  ) THEN
    RAISE EXCEPTION 'Safe resume snapshot entries are malformed, duplicated or incomplete';
  END IF;

  SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(COALESCE(pg_catalog.string_agg(
    pg_catalog.concat_ws(':', p.oid::TEXT, p.oid::REGPROCEDURE::TEXT, p.proowner::TEXT,
      COALESCE((SELECT pg_catalog.string_agg(
        pg_catalog.concat_ws(':', acl.grantee::TEXT, acl.grantor::TEXT,
          acl.privilege_type, acl.is_grantable::TEXT), ','
        ORDER BY acl.grantee, acl.grantor, acl.privilege_type, acl.is_grantable)
        FROM pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl
        WHERE acl.privilege_type = 'EXECUTE'), '<no-acl>')),
    E'\n' ORDER BY p.oid), 'no-target-functions'), 'UTF8')), 'hex') INTO current_fingerprint
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations);

  IF already_resumed THEN
    IF active_snapshot.resumed_fingerprint <> current_fingerprint
       OR EXISTS (
         SELECT 1 FROM pg_catalog.pg_proc p
         JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
         JOIN LATERAL pg_catalog.jsonb_array_elements(active_snapshot.grant_snapshot) e(value)
           ON (e.value ->> 'function_oid')::OID = p.oid
         WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
           AND (pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
             OR pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
               IS DISTINCT FROM (e.value ->> 'authenticated_execute')::BOOLEAN
             OR pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE')
               IS DISTINCT FROM (e.value ->> 'service_role_execute')::BOOLEAN)
       ) THEN
      RAISE EXCEPTION 'Safe resume idempotency check failed; keep the system suspended';
    END IF;
    RAISE NOTICE 'Safe resume already completed; persistent ACL fingerprint verified';
    RETURN;
  END IF;

  IF active_snapshot.suspended_fingerprint <> current_fingerprint
     OR EXISTS (
       SELECT 1 FROM pg_catalog.pg_proc p
       JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
       WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
         AND (pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
           OR pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
           OR pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE'))
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'H3D01',
      MESSAGE = 'Current ACL is not the captured suspended state; keep the system suspended';
  END IF;

  FOR item IN SELECT value FROM pg_catalog.jsonb_array_elements(active_snapshot.grant_snapshot)
  LOOP
    target_oid := (item ->> 'function_oid')::OID;
    SELECT p.oid::REGPROCEDURE INTO target
    FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.oid = target_oid
      AND p.oid::REGPROCEDURE::TEXT = item ->> 'signature'
      AND p.proowner::TEXT = item ->> 'owner_oid'
      AND p.proowner = current_role_oid;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Safe resume function signature or owner changed';
    END IF;
    snapshot_entries := snapshot_entries + 1;
    IF (item ->> 'authenticated_execute')::BOOLEAN THEN
      EXECUTE pg_catalog.format('GRANT EXECUTE ON FUNCTION %s TO authenticated', target);
    END IF;
    IF (item ->> 'service_role_execute')::BOOLEAN THEN
      EXECUTE pg_catalog.format('GRANT EXECUTE ON FUNCTION %s TO service_role', target);
    END IF;
  END LOOP;
  IF snapshot_entries <> target_count THEN
    RAISE EXCEPTION 'Safe resume snapshot contains duplicate or missing function entries';
  END IF;

  SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(COALESCE(pg_catalog.string_agg(
    pg_catalog.concat_ws(':', p.oid::TEXT, p.oid::REGPROCEDURE::TEXT, p.proowner::TEXT,
      COALESCE((SELECT pg_catalog.string_agg(
        pg_catalog.concat_ws(':', acl.grantee::TEXT, acl.grantor::TEXT,
          acl.privilege_type, acl.is_grantable::TEXT), ','
        ORDER BY acl.grantee, acl.grantor, acl.privilege_type, acl.is_grantable)
        FROM pg_catalog.aclexplode(COALESCE(p.proacl, pg_catalog.acldefault('f', p.proowner))) acl
        WHERE acl.privilege_type = 'EXECUTE'), '<no-acl>')),
    E'\n' ORDER BY p.oid), 'no-target-functions'), 'UTF8')), 'hex') INTO restored_fingerprint
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations);
  IF restored_fingerprint <> active_snapshot.original_fingerprint
     OR EXISTS (
       SELECT 1 FROM pg_catalog.pg_proc p
       JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
       JOIN LATERAL pg_catalog.jsonb_array_elements(active_snapshot.grant_snapshot) e(value)
         ON (e.value ->> 'function_oid')::OID = p.oid
       WHERE n.nspname = 'public' AND p.proname = ANY(blocked_operations)
         AND (pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
           OR pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
             IS DISTINCT FROM (e.value ->> 'authenticated_execute')::BOOLEAN
           OR pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE')
             IS DISTINCT FROM (e.value ->> 'service_role_execute')::BOOLEAN)
     ) THEN
    RAISE EXCEPTION 'Safe resume did not reproduce the captured ACL state';
  END IF;

  UPDATE private.h3req1_safe_suspend_acl_snapshots
  SET state = 'resumed', resumed_fingerprint = restored_fingerprint,
      resumed_at = pg_catalog.clock_timestamp()
  WHERE snapshot_id = active_snapshot.snapshot_id AND state = 'suspended';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Safe resume snapshot state changed concurrently';
  END IF;
END;
$$;
