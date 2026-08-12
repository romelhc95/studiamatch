#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${F10_10_M3_READER_TEST_SOCKET:-}" ]]; then
  case "$F10_10_M3_READER_TEST_SOCKET" in
    "$RUNNER_TEMP"/f1010-m3-reader.????????/postgres-socket) ;;
    *) echo 'F10_10_M3_READER_TEST_SOCKET must be the dedicated runner socket' >&2; exit 1 ;;
  esac
  readonly EXPECTED_URL="postgresql://postgres:postgres@/postgres?host=$F10_10_M3_READER_TEST_SOCKET"
  readonly READER_URL="postgresql://studiamatch_m3_reader@/postgres?host=$F10_10_M3_READER_TEST_SOCKET"
else
  readonly EXPECTED_URL='postgresql://postgres:postgres@studiamatch-m3-reader-postgres:5432/postgres'
  readonly READER_URL='postgresql://studiamatch_m3_reader@studiamatch-m3-reader-postgres:5432/postgres'
fi
readonly MIGRATION='db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql'
readonly ROLLBACK='db/rollbacks/20260811_fase10_10_m3_free_reader_compensating.sql'
readonly TEST_SQL='tests/sql/20260811_fase10_10_m3_free_reader_test.sql'
readonly LOCAL_TEST_PASSWORD='F10_10_M3_LOCAL_TEST_ONLY_2026!'
readonly LOCAL_TEST_EXPIRY='2099-12-31 23:59:59+00'
readonly LOCAL_TEST_EXPIRED='2000-01-01 00:00:00+00'
projection_sql="$(mktemp /tmp/f10_10_m3_projection.XXXXXX.sql)"
wrong_projection_sql="$(mktemp /tmp/f10_10_m3_wrong_projection.XXXXXX.sql)"
trap 'rm -f "$projection_sql" "$wrong_projection_sql"' EXIT

if [[ "${TEST_DATABASE_URL:-}" != "$EXPECTED_URL" ]]; then
  echo 'TEST_DATABASE_URL must exactly equal the dedicated local PostgreSQL 17 URL' >&2
  exit 1
fi
if [[ "${ALLOW_DESTRUCTIVE_LOCAL_TEST_DB:-}" != 'F10_10_M3_READER_LOCAL_POSTGRES17_ONLY' ]]; then
  echo 'ALLOW_DESTRUCTIVE_LOCAL_TEST_DB=F10_10_M3_READER_LOCAL_POSTGRES17_ONLY is required' >&2
  exit 1
fi

psql_safe=(psql "$TEST_DATABASE_URL" -X --no-psqlrc -v ON_ERROR_STOP=1)

server_facts="$("${psql_safe[@]}" -Atqc \
  "select current_database() || '|' || current_setting('server_version_num') || '|' || coalesce(inet_server_addr()::text, 'local')")"
case "$server_facts" in
  postgres\|17????\|local|postgres\|17????\|10.*|postgres\|17????\|172.1[6-9].*|postgres\|17????\|172.2?.*|postgres\|17????\|172.3[01].*) ;;
  *) echo "refusing non-local/non-PostgreSQL-17 target: $server_facts" >&2; exit 1 ;;
esac

expect_failure() {
  local label="$1"
  local failure_output
  shift
  failure_output="$(mktemp /tmp/f10_10_m3_expected_failure.XXXXXX)"
  if "$@" >"$failure_output" 2>&1; then
    rm -f "$failure_output"
    echo "expected failure unexpectedly passed: $label" >&2
    exit 1
  fi
  rm -f "$failure_output"
}

assert_reader_absent() {
  "${psql_safe[@]}" -Atqc \
    "select count(*) from pg_roles where rolname='studiamatch_m3_reader'" | grep -qx '0'
}

assert_reader_quarantined() {
  "${psql_safe[@]}" -Atqc "
    select count(*)
    from pg_roles r
    join pg_authid a on a.oid = r.oid
    where r.rolname = 'studiamatch_m3_reader'
      and not r.rolcanlogin
      and not r.rolbypassrls
      and not r.rolsuper
      and not r.rolinherit
      and not r.rolcreaterole
      and not r.rolcreatedb
      and not r.rolreplication
      and r.rolconnlimit = 1
      and a.rolpassword is null
      and (r.rolvaliduntil is null or isfinite(r.rolvaliduntil))
      and shobj_description(r.oid, 'pg_authid') =
        'studiamatch:f10.10:m3:free-reader:v1;activation-private'
      and not exists (
        select 1 from pg_db_role_setting s where s.setrole = r.oid
      )" | grep -qx '1'
}

activate_reader() {
  "${psql_safe[@]}" -v activation_password="$LOCAL_TEST_PASSWORD" \
    -v activation_expiry="$LOCAL_TEST_EXPIRY" <<'SQL'
ALTER ROLE studiamatch_m3_reader
  LOGIN
  PASSWORD :'activation_password'
  VALID UNTIL :'activation_expiry';

DO $assert_activation$
DECLARE
  v_role pg_catalog.pg_roles%ROWTYPE;
  v_password text;
BEGIN
  SELECT r.* INTO STRICT v_role
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = 'studiamatch_m3_reader';
  SELECT a.rolpassword INTO v_password
  FROM pg_catalog.pg_authid AS a
  WHERE a.oid = v_role.oid;
  IF NOT v_role.rolcanlogin
     OR NOT v_role.rolbypassrls
     OR v_password IS NULL
     OR v_role.rolvaliduntil IS NULL
     OR NOT pg_catalog.isfinite(v_role.rolvaliduntil)
     OR v_role.rolvaliduntil <= pg_catalog.statement_timestamp() THEN
    RAISE EXCEPTION 'test-only private activation did not produce exact active state';
  END IF;
END
$assert_activation$;
SQL
}

activate_reader_expired() {
  "${psql_safe[@]}" -v activation_password="$LOCAL_TEST_PASSWORD" \
    -v activation_expiry="$LOCAL_TEST_EXPIRED" <<'SQL'
ALTER ROLE studiamatch_m3_reader
  LOGIN
  PASSWORD :'activation_password'
  VALID UNTIL :'activation_expiry';

DO $assert_expired_activation$
DECLARE
  v_role pg_catalog.pg_roles%ROWTYPE;
  v_password text;
BEGIN
  SELECT r.* INTO STRICT v_role
  FROM pg_catalog.pg_roles AS r
  WHERE r.rolname = 'studiamatch_m3_reader';
  SELECT a.rolpassword INTO v_password
  FROM pg_catalog.pg_authid AS a
  WHERE a.oid = v_role.oid;
  IF NOT v_role.rolcanlogin
     OR NOT v_role.rolbypassrls
     OR v_password IS NULL
     OR v_role.rolvaliduntil IS NULL
     OR NOT pg_catalog.isfinite(v_role.rolvaliduntil)
     OR v_role.rolvaliduntil >= pg_catalog.statement_timestamp() THEN
    RAISE EXCEPTION 'test-only expired activation did not produce exact expired state';
  END IF;
END
$assert_expired_activation$;
SQL
}

verify_activated_login() {
  PGPASSWORD="$LOCAL_TEST_PASSWORD" psql "$READER_URL" -X --no-psqlrc \
    -v ON_ERROR_STOP=1 -Atqc "
      select case when
        current_user = 'studiamatch_m3_reader'
        and current_setting('default_transaction_read_only') = 'on'
        and current_setting('transaction_read_only') = 'on'
        and current_setting('search_path') = 'pg_catalog'
        and current_setting('client_encoding') = 'UTF8'
        and count(*) = 2
      then 1 else 0 end
      from public.courses
      where id is not null
        and is_active in (true, false)
        and (syllabus is null or syllabus is not null)
        and (objectives is null or objectives is not null)" | grep -qx '1'
}

provision_and_activate() {
  "${psql_safe[@]}" -f "$MIGRATION"
  activate_reader
}

"${psql_safe[@]}" <<'SQL'
DO $fresh_cluster$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_roles
    WHERE rolname IN (
      'studiamatch_m3_reader',
      'm3_non_super_executor',
      'm3_non_super_child',
      'm3_membership_blocker',
      'm3_other_member_blocker'
    )
  ) THEN
    RAISE EXCEPTION 'dedicated local cluster is not fresh';
  END IF;
END
$fresh_cluster$;

REVOKE ALL ON DATABASE postgres FROM PUBLIC;
REVOKE ALL ON DATABASE template0 FROM PUBLIC;
REVOKE ALL ON DATABASE template1 FROM PUBLIC;
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public AUTHORIZATION postgres;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE TABLE public.courses (
  id uuid PRIMARY KEY,
  is_active boolean DEFAULT true,
  syllabus text,
  objectives text,
  internal_notes text,
  created_at timestamptz NOT NULL DEFAULT pg_catalog.now()
);
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses FORCE ROW LEVEL SECURITY;
CREATE POLICY courses_public_active_only ON public.courses
  FOR SELECT TO PUBLIC USING (is_active);

INSERT INTO public.courses (id, is_active, syllabus, objectives, internal_notes)
VALUES
  ('00000000-0000-0000-0000-000000000001', true, 'visible syllabus', 'visible objectives', 'private one'),
  ('00000000-0000-0000-0000-000000000002', false, NULL, NULL, 'private two');

CREATE FUNCTION public.fixture_safe_definer()
RETURNS integer
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog
AS 'SELECT 1';
REVOKE ALL ON FUNCTION public.fixture_safe_definer() FROM PUBLIC;
SQL

# Supabase apply_migration wraps the submitted query and ledger insert in one
# transaction.  The projected body must preserve that atomic boundary.
python3 - "$projection_sql" "$wrong_projection_sql" <<'PY'
import sys
from pathlib import Path

from scripts.maintenance.f10_10_m3_apply_projection import (
    project_apply_migration_query,
    provisioner_fingerprint,
)

source = Path("db/free_only_migrations/20260811_fase10_10_m3_free_reader.sql").read_bytes()
package_digest = "sha256:d68d44c6ae61bac120f460955f86547082c0e42b70868a35a330fda8fb7883aa"
for output, role in ((sys.argv[1], "postgres"), (sys.argv[2], "wrong_executor")):
    fingerprint = provisioner_fingerprint(role)
    projection = project_apply_migration_query(
        source,
        expected_source_package_digest=package_digest,
        provisioner=role,
        expected_provisioner_fingerprint=fingerprint,
    )
    Path(output).write_bytes(projection.applied_query)
PY

expect_failure projected_wrong_executor "${psql_safe[@]}" \
  -c 'BEGIN' -f "$wrong_projection_sql" -c 'COMMIT'
assert_reader_absent

"${psql_safe[@]}" -c 'CREATE TABLE public.m3_migration_ledger (name text PRIMARY KEY)'
"${psql_safe[@]}" -c \
  "INSERT INTO public.m3_migration_ledger VALUES ('f10_10_m3_reader_duplicate')"
expect_failure projected_duplicate_ledger "${psql_safe[@]}" \
  -c 'BEGIN' -f "$projection_sql" \
  -c "INSERT INTO public.m3_migration_ledger VALUES ('f10_10_m3_reader_duplicate')" \
  -c 'COMMIT'
assert_reader_absent
"${psql_safe[@]}" -Atqc \
  "select count(*) from public.m3_migration_ledger where name='f10_10_m3_reader_duplicate'" \
  | grep -qx '1'

"${psql_safe[@]}" -c 'BEGIN' -f "$projection_sql" \
  -c "INSERT INTO public.m3_migration_ledger VALUES ('f10_10_m3_reader')" -c 'COMMIT'
"${psql_safe[@]}" -Atqc \
  "select count(*) from public.m3_migration_ledger where name='f10_10_m3_reader'" \
  | grep -qx '1'
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent
"${psql_safe[@]}" -c 'DROP TABLE public.m3_migration_ledger'

# Hosted-feasibility path: execute the actual migration and rollback under a
# direct non-superuser CREATEROLE+BYPASSRLS session with only the required grant
# options and explicit pg_authid visibility.  PostgreSQL 17's automatic creator
# ADMIN edge is retained as the normalized management edge.
"${psql_safe[@]}" <<'SQL'
CREATE ROLE m3_non_super_executor
  NOLOGIN NOSUPERUSER CREATEROLE NOCREATEDB NOREPLICATION BYPASSRLS NOINHERIT;
GRANT SELECT ON pg_catalog.pg_authid TO m3_non_super_executor;
GRANT CONNECT ON DATABASE postgres TO m3_non_super_executor WITH GRANT OPTION;
GRANT USAGE ON SCHEMA public TO m3_non_super_executor WITH GRANT OPTION;
GRANT SELECT (id, is_active, syllabus, objectives)
  ON public.courses TO m3_non_super_executor WITH GRANT OPTION;
SQL

"${psql_safe[@]}" \
  -c 'SET SESSION AUTHORIZATION m3_non_super_executor' \
  -f "$MIGRATION" \
  -c 'RESET SESSION AUTHORIZATION'
"${psql_safe[@]}" -f "$TEST_SQL"
"${psql_safe[@]}" -Atqc "
  select count(*)
  from pg_auth_members m
  join pg_roles reader on reader.oid = m.roleid
  join pg_roles creator on creator.oid = m.member
  join pg_roles grantor_role on grantor_role.oid = m.grantor
  where reader.rolname = 'studiamatch_m3_reader'
    and creator.rolname = 'm3_non_super_executor'
    and grantor_role.rolsuper
    and m.admin_option
    and not m.inherit_option
    and not m.set_option" | grep -qx '1'
non_super_reader_oid="$("${psql_safe[@]}" -Atqc \
  "select oid from pg_roles where rolname='studiamatch_m3_reader'")"
activate_reader
verify_activated_login
"${psql_safe[@]}" \
  -c 'SET SESSION AUTHORIZATION m3_non_super_executor' \
  -f "$ROLLBACK" \
  -c 'RESET SESSION AUTHORIZATION'
assert_reader_absent
"${psql_safe[@]}" -Atqc \
  "select count(*) from pg_auth_members where roleid=$non_super_reader_oid or member=$non_super_reader_oid" \
  | grep -qx '0'
"${psql_safe[@]}" <<'SQL'
REVOKE SELECT (id, is_active, syllabus, objectives)
  ON public.courses FROM m3_non_super_executor;
REVOKE USAGE ON SCHEMA public FROM m3_non_super_executor;
REVOKE CONNECT ON DATABASE postgres FROM m3_non_super_executor;
REVOKE SELECT ON pg_catalog.pg_authid FROM m3_non_super_executor;
DROP ROLE m3_non_super_executor;
SQL

# PUBLIC defaults are never changed by the package itself.
"${psql_safe[@]}" -c 'GRANT TEMPORARY ON DATABASE postgres TO PUBLIC'
expect_failure public_temporary "${psql_safe[@]}" -f "$MIGRATION"
assert_reader_absent
"${psql_safe[@]}" -c 'REVOKE TEMPORARY ON DATABASE postgres FROM PUBLIC'

# Unknown-role collision fails without repair.
"${psql_safe[@]}" -c \
  'CREATE ROLE studiamatch_m3_reader NOLOGIN NOSUPERUSER NOBYPASSRLS CONNECTION LIMIT 7'
expect_failure collision "${psql_safe[@]}" -f "$MIGRATION"
"${psql_safe[@]}" -Atqc \
  "select case when rolcanlogin or rolbypassrls or rolconnlimit <> 7 then 1 else 0 end from pg_roles where rolname='studiamatch_m3_reader'" \
  | grep -qx '0'
"${psql_safe[@]}" -c 'DROP ROLE studiamatch_m3_reader'

# Effective PUBLIC EXECUTE on SECURITY DEFINER routines fails closed.
"${psql_safe[@]}" <<'SQL'
CREATE FUNCTION public.fixture_unsafe_definer()
RETURNS integer
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog
AS 'SELECT 2';
SQL
expect_failure security_definer_public_execute "${psql_safe[@]}" -f "$MIGRATION"
assert_reader_absent
"${psql_safe[@]}" -c 'DROP FUNCTION public.fixture_unsafe_definer()'

# Provisioned NOLOGIN state, exact RLS-bypassing read surface, private activation,
# real password-authenticated local login, then active-state compensation.
"${psql_safe[@]}" -f "$MIGRATION"
"${psql_safe[@]}" -f "$TEST_SQL"
expect_failure other_column "${psql_safe[@]}" -c \
  'SET ROLE studiamatch_m3_reader; SELECT internal_notes FROM public.courses'
expect_failure table_select "${psql_safe[@]}" -c \
  'SET ROLE studiamatch_m3_reader; SELECT * FROM public.courses'
expect_failure insert "${psql_safe[@]}" -c \
  "SET ROLE studiamatch_m3_reader; INSERT INTO public.courses (id,is_active) VALUES ('00000000-0000-0000-0000-000000000003',true)"
expect_failure update "${psql_safe[@]}" -c \
  'SET ROLE studiamatch_m3_reader; UPDATE public.courses SET syllabus=NULL'
expect_failure delete "${psql_safe[@]}" -c \
  'SET ROLE studiamatch_m3_reader; DELETE FROM public.courses'
expect_failure function_execute "${psql_safe[@]}" -c \
  'SET ROLE studiamatch_m3_reader; SELECT public.fixture_safe_definer()'
activate_reader
verify_activated_login
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent

# An activated identity remains compensable after its finite VALID UNTIL expires.
"${psql_safe[@]}" -f "$MIGRATION"
activate_reader_expired
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent

# Membership blocker: compensation commits quarantine/revocation before STOP.
provision_and_activate
"${psql_safe[@]}" -c 'CREATE ROLE m3_membership_blocker NOLOGIN'
"${psql_safe[@]}" -c 'GRANT m3_membership_blocker TO studiamatch_m3_reader'
expect_failure rollback_membership "${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_quarantined
"${psql_safe[@]}" -c 'REVOKE m3_membership_blocker FROM studiamatch_m3_reader'
"${psql_safe[@]}" -c 'DROP ROLE m3_membership_blocker'
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent

# Additional member edge: only the normalized creator may manage the reader.
provision_and_activate
"${psql_safe[@]}" -c 'CREATE ROLE m3_other_member_blocker NOLOGIN'
"${psql_safe[@]}" -c \
  'GRANT studiamatch_m3_reader TO m3_other_member_blocker WITH ADMIN FALSE, INHERIT FALSE, SET FALSE'
expect_failure rollback_other_member "${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_quarantined
"${psql_safe[@]}" -c 'REVOKE studiamatch_m3_reader FROM m3_other_member_blocker'
"${psql_safe[@]}" -c 'DROP ROLE m3_other_member_blocker'
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent

# Ownership blocker: no DROP OWNED/REASSIGN; ownership must be removed explicitly.
provision_and_activate
"${psql_safe[@]}" <<'SQL'
CREATE TABLE public.m3_reader_owned_blocker (id integer);
ALTER TABLE public.m3_reader_owned_blocker OWNER TO studiamatch_m3_reader;
SQL
expect_failure rollback_ownership "${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_quarantined
"${psql_safe[@]}" <<'SQL'
ALTER TABLE public.m3_reader_owned_blocker OWNER TO postgres;
DROP TABLE public.m3_reader_owned_blocker;
SQL
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent

# Unexpected direct dependency blocker remains quarantined until explicitly revoked.
provision_and_activate
"${psql_safe[@]}" <<'SQL'
CREATE TABLE public.m3_reader_dependency_blocker (id integer);
GRANT SELECT ON public.m3_reader_dependency_blocker TO studiamatch_m3_reader;
SQL
expect_failure rollback_dependency "${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_quarantined
"${psql_safe[@]}" <<'SQL'
REVOKE SELECT ON public.m3_reader_dependency_blocker FROM studiamatch_m3_reader;
DROP TABLE public.m3_reader_dependency_blocker;
SQL
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent

# Active session blocker: NOLOGIN does not terminate an existing backend, so DROP
# stops after durable quarantine until the local backend is explicitly terminated.
provision_and_activate
session_output="$(mktemp /tmp/f10_10_m3_reader_session.XXXXXX)"
PGPASSWORD="$LOCAL_TEST_PASSWORD" psql "$READER_URL" -X --no-psqlrc \
  -v ON_ERROR_STOP=1 -c 'select pg_sleep(60)' >"$session_output" 2>&1 &
reader_client_pid=$!
for _ in $(seq 1 50); do
  if "${psql_safe[@]}" -Atqc \
    "select count(*) from pg_stat_activity where usename='studiamatch_m3_reader'" | grep -qx '1'; then
    break
  fi
  sleep 0.1
done
"${psql_safe[@]}" -Atqc \
  "select count(*) from pg_stat_activity where usename='studiamatch_m3_reader'" | grep -qx '1'
expect_failure rollback_session "${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_quarantined
"${psql_safe[@]}" -Atqc \
  "select count(*) from pg_stat_activity where usename='studiamatch_m3_reader'" | grep -qx '1'
"${psql_safe[@]}" -Atqc \
  "select pg_terminate_backend(pid) from pg_stat_activity where usename='studiamatch_m3_reader'" \
  | grep -qx 't'
wait "$reader_client_pid" 2>/dev/null || true
"${psql_safe[@]}" -Atqc \
  "select count(*) from pg_stat_activity where usename='studiamatch_m3_reader'" | grep -qx '0'
rm -f "$session_output"
"${psql_safe[@]}" -f "$ROLLBACK"
assert_reader_absent

echo 'F10.10 M3 Free reader PostgreSQL 17 networkless tests: PASS'
