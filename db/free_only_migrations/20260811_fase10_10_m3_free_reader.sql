-- F10.10/M3: provision the inactive Free-only full-population reader.
--
-- This migration intentionally creates no login/password/VALID UNTIL activation.
-- A later, private operational gate must activate the login.  It is fail-closed:
-- it will not repair a pre-existing role or weaken unrelated PUBLIC grants.

BEGIN;

SET LOCAL search_path = pg_catalog;
SELECT pg_catalog.pg_advisory_xact_lock(101010, 300311);

DO $migration_preconditions$
DECLARE
  v_executor pg_catalog.pg_roles%ROWTYPE;
BEGIN
  IF pg_catalog.current_database() IS DISTINCT FROM 'postgres' THEN
    RAISE EXCEPTION 'F10.10 M3 reader: target database must be exactly postgres';
  END IF;

  IF current_user IS DISTINCT FROM session_user THEN
    RAISE EXCEPTION 'F10.10 M3 reader: SET ROLE/session authorization is forbidden';
  END IF;

  SELECT r.* INTO STRICT v_executor
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = current_user;

  -- PostgreSQL 17 reserves BYPASSRLS assignment to superusers or an executor
  -- that itself has CREATEROLE+BYPASSRLS.  The mandatory creator-management
  -- edge is normalized below rather than treated as reader privilege inheritance.
  IF NOT (
    v_executor.rolsuper
    OR (v_executor.rolcreaterole AND v_executor.rolbypassrls)
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: executor lacks CREATEROLE+BYPASSRLS capability';
  END IF;
  IF NOT pg_catalog.has_table_privilege(current_user, 'pg_catalog.pg_authid', 'SELECT') THEN
    RAISE EXCEPTION 'F10.10 M3 reader: executor cannot verify the null password postcondition';
  END IF;

  IF pg_catalog.current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999 THEN
    RAISE EXCEPTION 'F10.10 M3 reader: PostgreSQL 17 is required';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'studiamatch_m3_reader'
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: role collision; refusing to inspect or repair';
  END IF;

  IF pg_catalog.to_regclass('public.courses') IS NULL THEN
    RAISE EXCEPTION 'F10.10 M3 reader: public.courses is required';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = 'public'
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: public schema is required';
  END IF;

  IF (
    SELECT pg_catalog.count(*)
    FROM pg_catalog.pg_attribute AS a
    WHERE a.attrelid = 'public.courses'::pg_catalog.regclass
      AND a.attnum > 0
      AND NOT a.attisdropped
      AND (a.attname, a.atttypid, a.attnotnull) IN (
        ('id', 'uuid'::pg_catalog.regtype, true),
        ('is_active', 'boolean'::pg_catalog.regtype, true),
        ('syllabus', 'text'::pg_catalog.regtype, false),
        ('objectives', 'text'::pg_catalog.regtype, false)
      )
  ) <> 4 THEN
    RAISE EXCEPTION 'F10.10 M3 reader: required courses column contract is absent or drifted';
  END IF;

  -- PUBLIC is not modified here.  Standard grants on a fresh cluster must be
  -- hardened by the environment owner when they would broaden this role.
  IF EXISTS (
    SELECT 1
    FROM pg_catalog.pg_database AS d
    CROSS JOIN LATERAL pg_catalog.aclexplode(
      COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))
    ) AS x
    WHERE x.grantee = 0
      AND (
        x.privilege_type = 'TEMPORARY'
        OR (x.privilege_type = 'CONNECT' AND d.datname <> 'postgres')
      )
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: broad PUBLIC database privileges must be hardened separately';
  END IF;
END
$migration_preconditions$;

CREATE ROLE studiamatch_m3_reader
  NOLOGIN
  PASSWORD NULL
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION
  BYPASSRLS
  NOINHERIT
  CONNECTION LIMIT 1;

-- PostgreSQL 17 rejects the spelling VALID UNTIL NULL.  Omitting VALID UNTIL
-- is its canonical representation for pg_authid.rolvaliduntil IS NULL.

COMMENT ON ROLE studiamatch_m3_reader IS
  'studiamatch:f10.10:m3:free-reader:v1;activation-private';

ALTER ROLE studiamatch_m3_reader IN DATABASE postgres
  SET default_transaction_read_only = 'on';
ALTER ROLE studiamatch_m3_reader IN DATABASE postgres
  SET search_path = 'pg_catalog';
ALTER ROLE studiamatch_m3_reader IN DATABASE postgres
  SET client_encoding = 'UTF8';

GRANT CONNECT ON DATABASE postgres TO studiamatch_m3_reader;
GRANT USAGE ON SCHEMA public TO studiamatch_m3_reader;
GRANT SELECT (id, is_active, syllabus, objectives)
  ON TABLE public.courses TO studiamatch_m3_reader;

-- A non-superuser CREATEROLE creator receives this exact edge automatically,
-- granted by the bootstrap superuser.  Superuser creation produces no edge, so
-- create the same management shape explicitly and converge both paths.
DO $normalize_creator_management_edge$
DECLARE
  v_reader_oid pg_catalog.oid;
  v_executor_oid pg_catalog.oid;
BEGIN
  SELECT r.oid INTO STRICT v_reader_oid
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = 'studiamatch_m3_reader';
  SELECT r.oid INTO STRICT v_executor_oid
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = current_user;

  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_auth_members AS m
    WHERE m.roleid = v_reader_oid AND m.member = v_executor_oid
  ) THEN
    GRANT studiamatch_m3_reader TO CURRENT_USER
      WITH ADMIN TRUE, INHERIT FALSE, SET FALSE;
  END IF;
END
$normalize_creator_management_edge$;

DO $migration_postconditions$
DECLARE
  v_role_oid pg_catalog.oid;
  v_role pg_catalog.pg_roles%ROWTYPE;
  v_role_password text;
  v_setting_count integer;
  v_bad_grants integer;
  v_total_grants integer;
  v_column record;
  v_database record;
  v_relation record;
  v_schema record;
  v_sequence record;
  v_executor_oid pg_catalog.oid;
BEGIN
  SELECT r.* INTO STRICT v_role
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = 'studiamatch_m3_reader';
  v_role_oid := v_role.oid;
  SELECT r.oid INTO STRICT v_executor_oid
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = current_user;
  SELECT r.rolpassword INTO v_role_password
  FROM pg_catalog.pg_authid AS r
  WHERE r.oid = v_role_oid;

  IF pg_catalog.shobj_description(v_role_oid, 'pg_authid') IS DISTINCT FROM
       'studiamatch:f10.10:m3:free-reader:v1;activation-private' THEN
    RAISE EXCEPTION 'F10.10 M3 reader: package identity marker is absent or drifted';
  END IF;

  IF v_role.rolsuper
     OR v_role.rolinherit
     OR v_role.rolcreaterole
     OR v_role.rolcreatedb
     OR v_role.rolcanlogin
     OR v_role.rolreplication
     OR NOT v_role.rolbypassrls
     OR v_role.rolconnlimit <> 1
     OR v_role_password IS NOT NULL
     OR v_role.rolvaliduntil IS NOT NULL
     OR v_role.rolconfig IS NOT NULL THEN
    RAISE EXCEPTION 'F10.10 M3 reader: role attributes differ from the closed contract';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_auth_members AS m
    WHERE m.member = v_role_oid
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: reader must not be a member of any role';
  END IF;
  IF (
    SELECT pg_catalog.count(*) FROM pg_catalog.pg_auth_members AS m
    WHERE m.roleid = v_role_oid
  ) <> 1
     OR NOT EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS m
       WHERE m.roleid = v_role_oid
         AND m.member = v_executor_oid
         AND m.admin_option
         AND NOT m.inherit_option
         AND NOT m.set_option
     ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: creator management edge is absent, duplicated, or drifted';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_shdepend AS d
    WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
      AND d.refobjid = v_role_oid
      AND d.deptype = 'o'
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: role must not own database objects';
  END IF;

  SELECT pg_catalog.count(*) INTO v_setting_count
  FROM pg_catalog.pg_db_role_setting AS s
  CROSS JOIN LATERAL pg_catalog.unnest(s.setconfig) AS cfg(value)
  WHERE s.setrole = v_role_oid
    AND s.setdatabase = (
      SELECT d.oid FROM pg_catalog.pg_database AS d WHERE d.datname = 'postgres'
    )
    AND cfg.value IN (
      'default_transaction_read_only=on',
      'search_path=pg_catalog',
      'client_encoding=UTF8'
    );

  IF v_setting_count <> 3
     OR EXISTS (
       SELECT 1
       FROM pg_catalog.pg_db_role_setting AS s
       CROSS JOIN LATERAL pg_catalog.unnest(s.setconfig) AS cfg(value)
       WHERE s.setrole = v_role_oid
         AND (
           s.setdatabase <> (
             SELECT d.oid FROM pg_catalog.pg_database AS d WHERE d.datname = 'postgres'
           )
           OR cfg.value NOT IN (
             'default_transaction_read_only=on',
             'search_path=pg_catalog',
             'client_encoding=UTF8'
           )
         )
     ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: database-specific settings differ from the closed contract';
  END IF;

  FOR v_database IN SELECT d.oid, d.datname FROM pg_catalog.pg_database AS d LOOP
    IF pg_catalog.has_database_privilege(v_role_oid, v_database.oid, 'CONNECT')
         IS DISTINCT FROM (v_database.datname = 'postgres')
       OR pg_catalog.has_database_privilege(v_role_oid, v_database.oid, 'TEMPORARY')
       OR pg_catalog.has_database_privilege(v_role_oid, v_database.oid, 'CREATE') THEN
      RAISE EXCEPTION 'F10.10 M3 reader: unexpected effective database privilege on %', v_database.datname;
    END IF;
  END LOOP;

  FOR v_schema IN
    SELECT n.oid, n.nspname
    FROM pg_catalog.pg_namespace AS n
    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
      AND n.nspname !~ '^pg_toast'
  LOOP
    IF pg_catalog.has_schema_privilege(v_role_oid, v_schema.oid, 'USAGE')
         IS DISTINCT FROM (v_schema.nspname = 'public')
       OR pg_catalog.has_schema_privilege(v_role_oid, v_schema.oid, 'CREATE') THEN
      RAISE EXCEPTION 'F10.10 M3 reader: unexpected effective schema privilege on %', v_schema.nspname;
    END IF;
  END LOOP;

  FOR v_relation IN
    SELECT c.oid, n.nspname, c.relname
    FROM pg_catalog.pg_class AS c
    JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
      AND n.nspname !~ '^pg_toast'
      AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
  LOOP
    IF pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'SELECT')
       OR pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'INSERT')
       OR pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'UPDATE')
       OR pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'DELETE')
       OR pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'TRUNCATE')
       OR pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'REFERENCES')
       OR pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'TRIGGER')
       OR pg_catalog.has_table_privilege(v_role_oid, v_relation.oid, 'MAINTAIN') THEN
      RAISE EXCEPTION 'F10.10 M3 reader: table-level privilege is forbidden on %.%',
        v_relation.nspname, v_relation.relname;
    END IF;
  END LOOP;

  FOR v_sequence IN
    SELECT c.oid, n.nspname, c.relname
    FROM pg_catalog.pg_class AS c
    JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
    WHERE c.relkind = 'S'
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
      AND n.nspname !~ '^pg_toast'
  LOOP
    IF pg_catalog.has_sequence_privilege(v_role_oid, v_sequence.oid, 'SELECT')
       OR pg_catalog.has_sequence_privilege(v_role_oid, v_sequence.oid, 'UPDATE')
       OR pg_catalog.has_sequence_privilege(v_role_oid, v_sequence.oid, 'USAGE') THEN
      RAISE EXCEPTION 'F10.10 M3 reader: sequence privilege is forbidden on %.%',
        v_sequence.nspname, v_sequence.relname;
    END IF;
  END LOOP;

  FOR v_column IN
    SELECT a.attrelid, a.attnum, a.attname, n.nspname, c.relname
    FROM pg_catalog.pg_attribute AS a
    JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid
    JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
      AND n.nspname !~ '^pg_toast'
      AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
      AND a.attnum > 0
      AND NOT a.attisdropped
  LOOP
    IF pg_catalog.has_column_privilege(
         v_role_oid, v_column.attrelid, v_column.attnum, 'SELECT'
       ) IS DISTINCT FROM (
         v_column.attrelid = 'public.courses'::pg_catalog.regclass
         AND v_column.attname IN ('id', 'is_active', 'syllabus', 'objectives')
       )
       OR pg_catalog.has_column_privilege(
         v_role_oid, v_column.attrelid, v_column.attnum, 'INSERT'
       )
       OR pg_catalog.has_column_privilege(
         v_role_oid, v_column.attrelid, v_column.attnum, 'UPDATE'
       )
       OR pg_catalog.has_column_privilege(
         v_role_oid, v_column.attrelid, v_column.attnum, 'REFERENCES'
       ) THEN
      RAISE EXCEPTION 'F10.10 M3 reader: unexpected column privilege on %.%.%',
        v_column.nspname, v_column.relname, v_column.attname;
    END IF;
  END LOOP;

  IF EXISTS (
    SELECT 1
    FROM pg_catalog.pg_proc AS p
    JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
    WHERE p.prosecdef
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
      AND n.nspname !~ '^pg_toast'
      AND pg_catalog.has_function_privilege(v_role_oid, p.oid, 'EXECUTE')
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 reader: effective EXECUTE on a non-system SECURITY DEFINER routine is forbidden';
  END IF;

  WITH direct_grants AS (
    SELECT 'database'::text AS kind, d.oid AS object_oid, 0::integer AS sub_id,
           x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_database AS d
    CROSS JOIN LATERAL pg_catalog.aclexplode(
      COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))
    ) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'schema', n.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_namespace AS n
    CROSS JOIN LATERAL pg_catalog.aclexplode(n.nspacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'relation', c.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_class AS c
    CROSS JOIN LATERAL pg_catalog.aclexplode(c.relacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'column', a.attrelid, a.attnum, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_attribute AS a
    CROSS JOIN LATERAL pg_catalog.aclexplode(a.attacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'routine', p.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_proc AS p
    CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'type', t.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_type AS t
    CROSS JOIN LATERAL pg_catalog.aclexplode(t.typacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'language', l.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_language AS l
    CROSS JOIN LATERAL pg_catalog.aclexplode(l.lanacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'tablespace', t.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_tablespace AS t
    CROSS JOIN LATERAL pg_catalog.aclexplode(t.spcacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'fdw', f.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_foreign_data_wrapper AS f
    CROSS JOIN LATERAL pg_catalog.aclexplode(f.fdwacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'server', s.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_foreign_server AS s
    CROSS JOIN LATERAL pg_catalog.aclexplode(s.srvacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'large_object', l.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_largeobject_metadata AS l
    CROSS JOIN LATERAL pg_catalog.aclexplode(l.lomacl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'parameter', p.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_parameter_acl AS p
    CROSS JOIN LATERAL pg_catalog.aclexplode(p.paracl) AS x
    WHERE x.grantee = v_role_oid
    UNION ALL
    SELECT 'default_acl', d.oid, 0, x.privilege_type, x.is_grantable
    FROM pg_catalog.pg_default_acl AS d
    CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) AS x
    WHERE x.grantee = v_role_oid
  )
  SELECT pg_catalog.count(*),
         pg_catalog.count(*) FILTER (WHERE NOT (
           (kind = 'database' AND object_oid = (
               SELECT d.oid FROM pg_catalog.pg_database AS d WHERE d.datname = 'postgres'
             )
             AND sub_id = 0 AND privilege_type = 'CONNECT' AND NOT is_grantable)
           OR (kind = 'schema' AND object_oid = 'public'::pg_catalog.regnamespace
             AND sub_id = 0 AND privilege_type = 'USAGE' AND NOT is_grantable)
           OR (kind = 'column' AND object_oid = 'public.courses'::pg_catalog.regclass
             AND sub_id IN (
               SELECT a.attnum FROM pg_catalog.pg_attribute AS a
               WHERE a.attrelid = 'public.courses'::pg_catalog.regclass
                 AND a.attname IN ('id', 'is_active', 'syllabus', 'objectives')
             )
             AND privilege_type = 'SELECT' AND NOT is_grantable)
         ))
  INTO v_total_grants, v_bad_grants
  FROM direct_grants;

  IF v_total_grants <> 6 OR v_bad_grants <> 0 THEN
    RAISE EXCEPTION 'F10.10 M3 reader: direct grants differ from the six package grants';
  END IF;
END
$migration_postconditions$;

COMMIT;
