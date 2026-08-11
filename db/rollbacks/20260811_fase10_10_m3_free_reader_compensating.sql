-- F10.10/M3 compensating rollback.
--
-- Three committed phases are deliberate.  If sessions or dependencies block
-- DROP, the marked identity remains NOLOGIN/NOBYPASSRLS/PASSWORD NULL with the
-- package grants revoked and package settings reset.  Unrelated residual grants
-- or dependencies can remain until explicitly remediated.  VALID UNTIL is
-- harmless after PASSWORD NULL and is retained until DROP so an activated role
-- can be quarantined first.

BEGIN;
SET LOCAL search_path = pg_catalog;
SELECT pg_catalog.pg_advisory_xact_lock(101010, 300311);

DO $rollback_identity_precondition$
DECLARE
  v_role pg_catalog.pg_roles%ROWTYPE;
  v_role_password text;
  v_is_provisioned boolean;
  v_is_activated boolean;
  v_is_quarantined_retry boolean;
BEGIN
  IF pg_catalog.current_database() IS DISTINCT FROM 'postgres' THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: target database must be exactly postgres';
  END IF;
  IF current_user IS DISTINCT FROM session_user
     OR NOT EXISTS (
       SELECT 1 FROM pg_catalog.pg_roles AS r
       WHERE r.rolname = current_user
         AND (r.rolsuper OR (r.rolcreaterole AND r.rolbypassrls))
     ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: direct CREATEROLE+BYPASSRLS-capable executor required';
  END IF;
  IF NOT pg_catalog.has_table_privilege(current_user, 'pg_catalog.pg_authid', 'SELECT') THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: executor cannot verify password state';
  END IF;

  SELECT r.* INTO STRICT v_role
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = 'studiamatch_m3_reader';
  SELECT r.rolpassword INTO v_role_password
  FROM pg_catalog.pg_authid AS r
  WHERE r.oid = v_role.oid;

  IF pg_catalog.shobj_description(v_role.oid, 'pg_authid') IS DISTINCT FROM
       'studiamatch:f10.10:m3:free-reader:v1;activation-private' THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: refusing an unmarked or drifted role collision';
  END IF;

  IF v_role.rolsuper
     OR v_role.rolinherit
     OR v_role.rolcreaterole
     OR v_role.rolcreatedb
     OR v_role.rolreplication
     OR v_role.rolconnlimit <> 1
     OR v_role.rolconfig IS NOT NULL THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: common role attributes drifted';
  END IF;

  v_is_provisioned :=
    NOT v_role.rolcanlogin
    AND v_role.rolbypassrls
    AND v_role_password IS NULL
    AND v_role.rolvaliduntil IS NULL;
  v_is_activated :=
    v_role.rolcanlogin
    AND v_role.rolbypassrls
    AND v_role_password IS NOT NULL
    AND v_role.rolvaliduntil IS NOT NULL
    AND pg_catalog.isfinite(v_role.rolvaliduntil);
  v_is_quarantined_retry :=
    NOT v_role.rolcanlogin
    AND NOT v_role.rolbypassrls
    AND v_role_password IS NULL
    AND (
      v_role.rolvaliduntil IS NULL
      OR pg_catalog.isfinite(v_role.rolvaliduntil)
    );

  IF NOT (v_is_provisioned OR v_is_activated OR v_is_quarantined_retry) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: role is not exact provisioned, activated, or quarantined package state';
  END IF;
END
$rollback_identity_precondition$;

-- First durable mutation: disable authentication and RLS bypass, and destroy
-- any private activation password.  Do not clear a finite expiry yet.
ALTER ROLE studiamatch_m3_reader
  NOLOGIN NOBYPASSRLS PASSWORD NULL;
COMMIT;

BEGIN;
SET LOCAL search_path = pg_catalog;
SELECT pg_catalog.pg_advisory_xact_lock(101010, 300311);

REVOKE CONNECT ON DATABASE postgres FROM studiamatch_m3_reader;
REVOKE USAGE ON SCHEMA public FROM studiamatch_m3_reader;
REVOKE SELECT (id, is_active, syllabus, objectives)
  ON TABLE public.courses FROM studiamatch_m3_reader;

ALTER ROLE studiamatch_m3_reader IN DATABASE postgres
  RESET default_transaction_read_only;
ALTER ROLE studiamatch_m3_reader IN DATABASE postgres
  RESET search_path;
ALTER ROLE studiamatch_m3_reader IN DATABASE postgres
  RESET client_encoding;
COMMIT;

BEGIN;
SET LOCAL search_path = pg_catalog;
SELECT pg_catalog.pg_advisory_xact_lock(101010, 300311);

DO $rollback_drop_preconditions$
DECLARE
  v_role pg_catalog.pg_roles%ROWTYPE;
  v_role_password text;
BEGIN
  SELECT r.* INTO STRICT v_role
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = 'studiamatch_m3_reader';
  SELECT r.rolpassword INTO v_role_password
  FROM pg_catalog.pg_authid AS r
  WHERE r.oid = v_role.oid;

  IF v_role.rolcanlogin
     OR v_role.rolbypassrls
     OR v_role.rolsuper
     OR v_role.rolinherit
     OR v_role.rolcreaterole
     OR v_role.rolcreatedb
     OR v_role.rolreplication
     OR v_role.rolconnlimit <> 1
     OR v_role_password IS NOT NULL
     OR v_role.rolconfig IS NOT NULL
     OR (
       v_role.rolvaliduntil IS NOT NULL
       AND NOT pg_catalog.isfinite(v_role.rolvaliduntil)
     ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: quarantine postcondition failed';
  END IF;

  IF pg_catalog.shobj_description(v_role.oid, 'pg_authid') IS DISTINCT FROM
       'studiamatch:f10.10:m3:free-reader:v1;activation-private' THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: package identity marker drifted after quarantine';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_stat_activity AS a
    WHERE a.usename = 'studiamatch_m3_reader'
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: active reader sessions require manual termination';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_auth_members AS m
    WHERE m.member = v_role.oid
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: reader membership in another role blocks DROP';
  END IF;
  IF (
    SELECT pg_catalog.count(*) FROM pg_catalog.pg_auth_members AS m
    WHERE m.roleid = v_role.oid
  ) <> 1
     OR NOT EXISTS (
       SELECT 1
       FROM pg_catalog.pg_auth_members AS m
       JOIN pg_catalog.pg_roles AS executor_role ON executor_role.oid = m.member
       WHERE m.roleid = v_role.oid
         AND executor_role.rolname = current_user
         AND m.admin_option
         AND NOT m.inherit_option
         AND NOT m.set_option
     ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: creator-management edge is absent, duplicated, or drifted';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_db_role_setting AS s
    WHERE s.setrole = v_role.oid
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: unexpected role/database settings block DROP';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_shdepend AS d
    WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
      AND d.refobjid = v_role.oid
      AND d.deptype = 'o'
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: role ownership blocks DROP';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_catalog.pg_shdepend AS d
    WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass
      AND d.refobjid = v_role.oid
  ) THEN
    RAISE EXCEPTION 'F10.10 M3 rollback: unexpected dependencies/direct grants block DROP';
  END IF;
END
$rollback_drop_preconditions$;

DROP ROLE studiamatch_m3_reader;
COMMIT;
