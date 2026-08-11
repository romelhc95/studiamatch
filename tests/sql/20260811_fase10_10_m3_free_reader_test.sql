\set ON_ERROR_STOP on

DO $assert_server$
BEGIN
  IF pg_catalog.current_database() <> 'postgres'
     OR pg_catalog.current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999 THEN
    RAISE EXCEPTION 'test requires the exact postgres database on PostgreSQL 17';
  END IF;
END
$assert_server$;

DO $assert_reader$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_roles
    WHERE rolname = 'studiamatch_m3_reader'
      AND NOT rolcanlogin AND rolbypassrls AND NOT rolinherit
      AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
      AND NOT rolreplication AND rolconnlimit = 1
  ) THEN
    RAISE EXCEPTION 'reader attributes are not exact';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM pg_catalog.pg_auth_members AS m
    JOIN pg_catalog.pg_roles AS reader ON reader.oid = m.member
    WHERE reader.rolname = 'studiamatch_m3_reader'
  ) OR (
    SELECT pg_catalog.count(*)
    FROM pg_catalog.pg_auth_members AS m
    JOIN pg_catalog.pg_roles AS reader ON reader.oid = m.roleid
    WHERE reader.rolname = 'studiamatch_m3_reader'
  ) <> 1 OR NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_auth_members AS m
    JOIN pg_catalog.pg_roles AS reader ON reader.oid = m.roleid
    WHERE reader.rolname = 'studiamatch_m3_reader'
      AND m.admin_option
      AND NOT m.inherit_option
      AND NOT m.set_option
  ) THEN
    RAISE EXCEPTION 'reader creator-management edge is not exact';
  END IF;

END
$assert_reader$;

SET ROLE studiamatch_m3_reader;
SELECT pg_catalog.count(*) = 2 AS full_population_visible
FROM public.courses
WHERE id IS NOT NULL
  AND is_active IN (true, false)
  AND (syllabus IS NULL OR syllabus IS NOT NULL)
  AND (objectives IS NULL OR objectives IS NOT NULL)
\gset
RESET ROLE;

\if :full_population_visible
\else
  \echo 'BYPASSRLS reader did not see the full two-row population'
  \quit 1
\endif
