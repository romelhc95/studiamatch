#!/usr/bin/env bash
set -Eeuo pipefail

result=1
v3_package=""
hold_package=""
exec_wrapper=""
failure_package=""
failure_log=""
trigger_fixture_wrapper=""

finish() {
  local exit_status=$?
  trap - EXIT
  set +e
  for temporary_file in "$v3_package" "$hold_package" "$exec_wrapper" "$failure_package" "$failure_log" "$trigger_fixture_wrapper"; do
    [[ -z "$temporary_file" ]] || rm -f -- "$temporary_file"
  done
  if [[ $exit_status -eq 0 && $result -eq 0 ]]; then
    printf '%s\n' 'F9.7 leads/email security hold PostgreSQL 17 contract: PASS'
    exit 0
  fi
  printf '%s\n' 'F9.7 leads/email security hold PostgreSQL 17 contract: FAIL' >&2
  [[ $exit_status -eq 0 ]] && exit 1
  exit "$exit_status"
}
trap finish EXIT
trap 'status=$?; printf "F9.7 security hold runner failed near line %s (exit %s)\n" "$LINENO" "$status" >&2; exit "$status"' ERR
trap 'exit 130' HUP INT TERM

: "${TEST_DATABASE_URL:?TEST_DATABASE_URL must point to an ephemeral PostgreSQL 17 database}"
[[ "$TEST_DATABASE_URL" =~ ^postgresql://postgres:postgres@(127\.0\.0\.1|localhost|studiamatch-f97-postgres):[0-9]+/studiamatch_f97$ \
  || "$TEST_DATABASE_URL" =~ ^postgresql://postgres:postgres@/studiamatch_f97\?host=/[A-Za-z0-9._/-]+/postgres-socket$ ]]

for variable_name in $(compgen -e); do
  case "$variable_name" in
    SUPABASE*|NEXT_SUPABASE*|NEXT_PUBLIC_SUPABASE*|CF_*|OPENCODE_*|RESEND_*|GITHUB_TOKEN|GH_TOKEN|DATABASE_URL|POSTGRES_*|PG*)
      exit 1
      ;;
  esac
done

ROOT="${FASE097_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
V3_MANIFEST="$ROOT/db/manifests/fase09_7_free_schema_rls_v3.json"
HOLD_MANIFEST="$ROOT/db/manifests/fase09_7_leads_email_security_hold.json"
BASELINE="$ROOT/tests/sql/fase08_minimal_baseline.sql"
ACCESS_FIXTURE="$ROOT/tests/sql/fase09_7_access_fixture.sql"
EXEC_FIXTURE="$ROOT/tests/sql/fase09_exec_sql_fixture.sql"
FUNCTIONAL="$ROOT/tests/sql/fase09_7_leads_email_security_hold_test.sql"
HISTORICAL_TRIGGER_SOURCE="$ROOT/db/migrations/20260531_fase67b_secure_trigger.sql"

command -v psql >/dev/null
command -v python3 >/dev/null
server_version_num="$(psql -X --quiet --tuples-only --no-align \
  --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  'SHOW server_version_num;' | tr -d '[:space:]')"
[[ "$server_version_num" -ge 170000 && "$server_version_num" -lt 180000 ]]

tmp_parent="${TMPDIR:-/tmp}"
v3_package="$(mktemp "$tmp_parent/studiamatch-f97-v3.XXXXXX.sql")"
hold_package="$(mktemp "$tmp_parent/studiamatch-f97-hold.XXXXXX.sql")"
exec_wrapper="$(mktemp "$tmp_parent/studiamatch-f97-exec.XXXXXX.sql")"
failure_package="$(mktemp "$tmp_parent/studiamatch-f97-hold-failure.XXXXXX.sql")"
failure_log="$(mktemp "$tmp_parent/studiamatch-f97-hold-failure.XXXXXX.log")"
trigger_fixture_wrapper="$(mktemp "$tmp_parent/studiamatch-f97-trigger.XXXXXX.sql")"

python3 - "$HISTORICAL_TRIGGER_SOURCE" "$trigger_fixture_wrapper" <<'PY'
import sys
from pathlib import Path

source_path, output_path = sys.argv[1:]
source = Path(source_path).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
fixture_lines = (
    "\\set ON_ERROR_STOP on",
    "DROP FUNCTION public.notify_new_lead();",
    source.rstrip(),
    "REVOKE ALL ON FUNCTION public.notify_new_lead() FROM PUBLIC, anon, authenticated, service_role CASCADE;",
    "GRANT EXECUTE ON FUNCTION public.notify_new_lead() TO service_role;",
    "CREATE TRIGGER trg_notify_new_lead AFTER INSERT ON public.leads FOR EACH ROW EXECUTE FUNCTION public.notify_new_lead();",
)
Path(output_path).write_text("\n".join(fixture_lines) + "\n", encoding="utf-8", newline="\n")
PY

reset_database() {
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
SELECT pg_catalog.format('DROP OWNED BY %I;', role.rolname)
FROM pg_catalog.pg_roles AS role
    WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
ORDER BY role.rolname
\gexec
SELECT pg_catalog.format('DROP ROLE %I;', role.rolname)
FROM pg_catalog.pg_roles AS role
    WHERE role.rolname IN ('anon', 'authenticated', 'authenticator', 'service_role')
ORDER BY role.rolname
\gexec
CREATE SCHEMA public AUTHORIZATION pg_database_owner;
GRANT USAGE ON SCHEMA public TO PUBLIC;
SQL
}

wrap_exec_sql() {
  local input_sql="$1"
  python3 - "$input_sql" "$exec_wrapper" <<'PY'
import sys
from pathlib import Path

source, output = sys.argv[1:]
payload = Path(source).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
tag = "security_hold_exec_sql_payload"
if f"${tag}$" in payload:
    raise SystemExit("exec_sql dollar quote tag collision")
Path(output).write_text(
    "\\set ON_ERROR_STOP on\n"
    "SET ROLE service_role;\n"
    f"SELECT public.exec_sql(${tag}$\n{payload}\n${tag}$);\n"
    "RESET ROLE;\n",
    encoding="utf-8",
    newline="\n",
)
PY
}

normalize_authenticator_role() {
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
CREATE ROLE authenticator LOGIN NOINHERIT NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
GRANT anon TO authenticator WITH ADMIN FALSE, INHERIT FALSE, SET TRUE;
GRANT authenticated TO authenticator WITH ADMIN FALSE, INHERIT FALSE, SET TRUE;
GRANT service_role TO authenticator WITH ADMIN FALSE, INHERIT FALSE, SET TRUE;
SQL
}

capture_fingerprint() {
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" <<'SQL'
SELECT pg_catalog.jsonb_build_object(
    'ledger', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'version', version,
            'name', name,
            'statements', statements
        ) ORDER BY name)
        FROM public.supabase_migrations
    ), '[]'::pg_catalog.jsonb),
    'table_acl', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'relation', relation.relname,
            'acl', acl.acl_item::text
        ) ORDER BY relation.relname, acl.acl_item::text)
        FROM pg_catalog.pg_class AS relation
        LEFT JOIN LATERAL pg_catalog.unnest(COALESCE(relation.relacl, '{}'::aclitem[])) AS acl(acl_item) ON true
        WHERE relation.oid IN ('public.leads'::pg_catalog.regclass, 'public.email_log'::pg_catalog.regclass)
    ), '[]'::pg_catalog.jsonb),
    'column_acl', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'relation', relation.relname,
            'column', attribute.attname,
            'acl', acl.acl_item::text
        ) ORDER BY relation.relname, attribute.attnum, acl.acl_item::text)
        FROM pg_catalog.pg_attribute AS attribute
        JOIN pg_catalog.pg_class AS relation ON relation.oid = attribute.attrelid
        LEFT JOIN LATERAL pg_catalog.unnest(COALESCE(attribute.attacl, '{}'::aclitem[])) AS acl(acl_item) ON true
        WHERE attribute.attrelid IN ('public.leads'::pg_catalog.regclass, 'public.email_log'::pg_catalog.regclass)
          AND attribute.attnum > 0
          AND NOT attribute.attisdropped
    ), '[]'::pg_catalog.jsonb),
    'policies', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(policy) ORDER BY policy.schemaname, policy.tablename, policy.policyname)
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
          AND policy.tablename IN ('leads', 'email_log')
    ), '[]'::pg_catalog.jsonb),
    'constraints', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'relation', relation.relname,
            'name', constraint_record.conname,
            'type', constraint_record.contype,
            'validated', constraint_record.convalidated,
            'definition', pg_catalog.pg_get_constraintdef(constraint_record.oid, true)
        ) ORDER BY relation.relname, constraint_record.conname)
        FROM pg_catalog.pg_constraint AS constraint_record
        JOIN pg_catalog.pg_class AS relation ON relation.oid = constraint_record.conrelid
        WHERE constraint_record.conrelid IN ('public.leads'::pg_catalog.regclass, 'public.email_log'::pg_catalog.regclass)
    ), '[]'::pg_catalog.jsonb),
    'functions', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'schema', namespace.nspname,
            'name', procedure_record.proname,
            'kind', procedure_record.prokind,
            'security_definer', procedure_record.prosecdef,
            'config', procedure_record.proconfig,
            'acl', COALESCE(procedure_record.proacl, pg_catalog.acldefault('f', procedure_record.proowner))::text,
            'source_sha256', pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(pg_catalog.replace(procedure_record.prosrc, E'\r\n', E'\n'), 'UTF8')), 'hex')
        ) ORDER BY namespace.nspname, procedure_record.proname, procedure_record.oid)
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = procedure_record.pronamespace
        WHERE namespace.nspname = 'public'
    ), '[]'::pg_catalog.jsonb),
    'memberships', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'role', role_record.rolname,
            'member', member_record.rolname,
            'admin', membership.admin_option,
            'inherit', membership.inherit_option,
            'set', membership.set_option
        ) ORDER BY role_record.rolname, member_record.rolname)
        FROM pg_catalog.pg_auth_members AS membership
        JOIN pg_catalog.pg_roles AS role_record ON role_record.oid = membership.roleid
        JOIN pg_catalog.pg_roles AS member_record ON member_record.oid = membership.member
        WHERE role_record.rolname IN ('anon', 'authenticated', 'service_role', 'authenticator', 'postgres')
           OR member_record.rolname IN ('anon', 'authenticated', 'service_role', 'authenticator', 'postgres')
    ), '[]'::pg_catalog.jsonb),
    'triggers', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'relation', relation.relname,
            'name', trigger_record.tgname,
            'enabled', trigger_record.tgenabled,
            'definition', pg_catalog.pg_get_triggerdef(trigger_record.oid, true)
        ) ORDER BY relation.relname, trigger_record.tgname)
        FROM pg_catalog.pg_trigger AS trigger_record
        JOIN pg_catalog.pg_class AS relation ON relation.oid = trigger_record.tgrelid
        WHERE relation.oid IN ('public.leads'::pg_catalog.regclass, 'public.email_log'::pg_catalog.regclass)
          AND NOT trigger_record.tgisinternal
    ), '[]'::pg_catalog.jsonb),
    'rules', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'relation', relation.relname,
            'name', rewrite_record.rulename,
            'event', rewrite_record.ev_type,
            'enabled', rewrite_record.ev_enabled
        ) ORDER BY relation.relname, rewrite_record.rulename)
        FROM pg_catalog.pg_rewrite AS rewrite_record
        JOIN pg_catalog.pg_class AS relation ON relation.oid = rewrite_record.ev_class
        WHERE relation.oid IN ('public.leads'::pg_catalog.regclass, 'public.email_log'::pg_catalog.regclass)
    ), '[]'::pg_catalog.jsonb),
    'publications', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'publication', publication.pubname,
            'all_tables', publication.puballtables,
            'relation', relation.relname
        ) ORDER BY publication.pubname, relation.relname)
        FROM pg_catalog.pg_publication AS publication
        LEFT JOIN pg_catalog.pg_publication_rel AS publication_relation ON publication_relation.prpubid = publication.oid
        LEFT JOIN pg_catalog.pg_class AS relation ON relation.oid = publication_relation.prrelid
        WHERE publication.puballtables
           OR relation.oid IN ('public.leads'::pg_catalog.regclass, 'public.email_log'::pg_catalog.regclass)
    ), '[]'::pg_catalog.jsonb),
    'legacy_row_digests', pg_catalog.jsonb_build_object(
        'leads', (
            SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(leads) ORDER BY leads.id)::text, '[]'),
                'UTF8'
            )), 'hex')
            FROM public.leads AS leads
        ),
        'email_log', (
            SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(email_log) ORDER BY email_log.id)::text, '[]'),
                'UTF8'
            )), 'hex')
            FROM public.email_log AS email_log
        )
    )
)::text;
SQL
}

generate_v3_package() {
  python3 - "$V3_MANIFEST" "$v3_package" <<'PY'
import sys
from pathlib import Path

from scripts.maintenance.fase09_7_candidate import (
    build_manifest_package_sql,
    classify_manifest_ledger,
    load_manifest,
)

manifest, output = sys.argv[1:]
paths = load_manifest(Path(manifest), "free")
plan = classify_manifest_ledger(paths, {})
Path(output).write_text(
    build_manifest_package_sql(plan, version=20260729000000),
    encoding="utf-8",
    newline="\n",
)
PY
}

generate_hold_package() {
  local replay_flag="${1:-apply}"
  python3 - "$HOLD_MANIFEST" "$hold_package" "$replay_flag" <<'PY'
import sys
from pathlib import Path

from scripts.maintenance.fase09_7_leads_email_security_hold_candidate import (
    build_security_hold_package_sql,
    classify_security_hold_ledger,
    load_security_hold_manifest,
    canonical_sql_sha256,
)

manifest, output, replay_flag = sys.argv[1:]
v3_paths, hold_path = load_security_hold_manifest(Path(manifest), "free")
applied = {path.stem: f"sha256:{canonical_sql_sha256(path)}" for path in v3_paths}
if replay_flag == "replay":
    applied[hold_path.stem] = f"sha256:{canonical_sql_sha256(hold_path)}"
plan = classify_security_hold_ledger(v3_paths, hold_path, applied)
Path(output).write_text(
    build_security_hold_package_sql(plan, version=20260729000100),
    encoding="utf-8",
    newline="\n",
)
PY
}

setup_v3_boundary() {
  reset_database
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$BASELINE" >/dev/null
  normalize_authenticator_role
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$ACCESS_FIXTURE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$trigger_fixture_wrapper" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$EXEC_FIXTURE" >/dev/null
  generate_v3_package
  wrap_exec_sql "$v3_package"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure();
SELECT public.verify_fase09_7_notify_new_lead_retirement();
RESET ROLE;
INSERT INTO public.leads (id, first_name, email, whatsapp) VALUES (
    '94000000-0000-0000-0000-000000000001', 'Existing',
    'existing@example.test', '+51000000000'
);
INSERT INTO public.email_log (id, lead_id, recipient_type, recipient_email, status) VALUES (
    '95000000-0000-0000-0000-000000000001',
    '94000000-0000-0000-0000-000000000001', 'audit',
    'audit@example.test', 'pending'
);
SQL
}

apply_hold() {
  generate_hold_package apply
  wrap_exec_sql "$hold_package"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null
}

assert_v3_still_live_without_hold() {
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
SET ROLE service_role;
SELECT public.verify_fase09_7_public_access_closure();
SELECT public.verify_fase09_7_notify_new_lead_retirement();
RESET ROLE;
DO $assert_no_hold$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.supabase_migrations
        WHERE name = '20260729_fase09_7_leads_email_security_hold'
    ) THEN
        RAISE EXCEPTION 'security hold ledger row survived failed transaction';
    END IF;
END;
$assert_no_hold$;
SQL
}

expect_hold_failure_rolls_back() {
  local marker="$1"
  local injection="$2"
  setup_v3_boundary
  local before_fingerprint
  before_fingerprint="$(capture_fingerprint)"
  generate_hold_package apply
  python3 - "$hold_package" "$failure_package" "$marker" "$injection" <<'PY'
import sys
from pathlib import Path

source, output, marker, injection = sys.argv[1:]
sql = Path(source).read_text(encoding="utf-8")
if sql.count(marker) != 1:
    raise SystemExit(f"marker missing: {marker}")
Path(output).write_text(sql.replace(marker, marker + "\n" + injection, 1), encoding="utf-8", newline="\n")
PY
  wrap_exec_sql "$failure_package"
  if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null 2>"$failure_log"; then
    printf 'Injected failure unexpectedly passed: %s\n' "$marker" >&2
    return 1
  fi
  local after_fingerprint
  after_fingerprint="$(capture_fingerprint)"
  if [[ "$before_fingerprint" != "$after_fingerprint" ]]; then
    printf 'Injected failure left catalog/data drift after marker: %s\n' "$marker" >&2
    return 1
  fi
  assert_v3_still_live_without_hold
}

expect_verifier_rejects() {
  local label="$1"
  local injection="$2"
  local verifier_result
  verifier_result="$(psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" <<SQL
BEGIN;
$injection
SET ROLE service_role;
SELECT public.verify_fase09_7_leads_email_security_hold();
RESET ROLE;
ROLLBACK;
SQL
)"
  if [[ "$verifier_result" != "f" ]]; then
    printf 'Verifier did not reject adversarial case: %s\n' "$label" >&2
    return 1
  fi
}

expect_verifier_accepts() {
  local label="$1"
  local injection="$2"
  local verifier_result
  verifier_result="$(psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" <<SQL
BEGIN;
$injection
SET ROLE service_role;
SELECT public.verify_fase09_7_leads_email_security_hold();
RESET ROLE;
ROLLBACK;
SQL
)"
  if [[ "$verifier_result" != "t" ]]; then
    printf 'Verifier rejected control case: %s\n' "$label" >&2
    return 1
  fi
}

expect_drifted_verifier_not_invoked() {
  local verifier_signature="$1"
  local verifier_language="$2"
  local replacement_body="$3"
  local replay_flag="$4"
  local sequence_name="f97_nontransactional_probe"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<SQL
DROP SEQUENCE IF EXISTS public.${sequence_name};
CREATE SEQUENCE public.${sequence_name};
CREATE OR REPLACE FUNCTION ${verifier_signature}
RETURNS boolean
LANGUAGE ${verifier_language}
STABLE
SECURITY INVOKER
SET search_path = ''
AS \$drifted\$
${replacement_body}
\$drifted\$;
ALTER FUNCTION ${verifier_signature} OWNER TO postgres;
REVOKE ALL ON FUNCTION ${verifier_signature} FROM PUBLIC, anon, authenticated, authenticator, service_role;
GRANT EXECUTE ON FUNCTION ${verifier_signature} TO service_role;
SQL
  generate_hold_package "$replay_flag"
  wrap_exec_sql "$hold_package"
  if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null 2>"$failure_log"; then
    printf 'Drifted verifier unexpectedly passed: %s\n' "$verifier_signature" >&2
    return 1
  fi
  sequence_called="$(psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command "SELECT is_called FROM public.${sequence_name};")"
  if [[ "$sequence_called" != "f" ]]; then
    printf 'Drifted verifier was invoked before identity attestation: %s\n' "$verifier_signature" >&2
    return 1
  fi
}

setup_v3_boundary
apply_hold
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$FUNCTIONAL" >/dev/null

expect_verifier_accepts "non-exposed administrative routine" \
  "CREATE SCHEMA f97_admin AUTHORIZATION postgres;
   REVOKE ALL ON SCHEMA f97_admin FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE FUNCTION f97_admin.noop() RETURNS integer LANGUAGE sql STABLE AS 'SELECT 1';
   REVOKE ALL ON FUNCTION f97_admin.noop() FROM PUBLIC, anon, authenticated, authenticator, service_role;"
expect_verifier_rejects "direct view" \
  "CREATE VIEW public.f97_leads_direct_view AS SELECT id FROM public.leads;
   GRANT SELECT ON public.f97_leads_direct_view TO anon;"
expect_verifier_rejects "column grant" \
  "GRANT SELECT (id) ON public.leads TO anon;"
expect_verifier_rejects "updatable view DML" \
  "CREATE VIEW public.f97_leads_dml_view AS SELECT id, first_name, email, whatsapp FROM public.leads;
   GRANT INSERT ON public.f97_leads_dml_view TO authenticated;"
expect_verifier_rejects "view chain" \
  "CREATE VIEW public.f97_leads_chain_1 AS SELECT id FROM public.leads;
   CREATE VIEW public.f97_leads_chain_2 AS SELECT id FROM public.f97_leads_chain_1;
   GRANT SELECT ON public.f97_leads_chain_2 TO authenticated;"
expect_verifier_rejects "populated materialized view" \
  "CREATE MATERIALIZED VIEW public.f97_leads_mv AS SELECT id FROM public.leads WITH DATA;"
expect_verifier_rejects "routine wrapper" \
  "CREATE FUNCTION public.f97_leads_count() RETURNS integer LANGUAGE sql STABLE AS 'SELECT count(*)::integer FROM public.leads';
   GRANT EXECUTE ON FUNCTION public.f97_leads_count() TO anon;"
expect_verifier_rejects "protected overload" \
  "CREATE FUNCTION public.verify_fase09_7_leads_email_security_hold(integer) RETURNS boolean LANGUAGE sql STABLE AS 'SELECT true';"
expect_verifier_rejects "direct publication" \
  "CREATE PUBLICATION f97_direct_pub FOR TABLE public.leads;"
expect_verifier_rejects "all tables publication" \
  "CREATE PUBLICATION f97_all_pub FOR ALL TABLES;"
expect_verifier_rejects "schema publication" \
  "CREATE PUBLICATION f97_schema_pub FOR TABLES IN SCHEMA public;"
expect_verifier_rejects "unexpected policy" \
  "CREATE POLICY f97_unexpected_policy ON public.leads FOR SELECT TO anon USING (true);"
expect_verifier_rejects "unexpected trigger" \
  "CREATE FUNCTION public.f97_trigger_noop() RETURNS trigger LANGUAGE plpgsql AS 'BEGIN RETURN NEW; END';
   CREATE TRIGGER f97_unexpected_trigger BEFORE INSERT ON public.leads FOR EACH ROW EXECUTE FUNCTION public.f97_trigger_noop();"
expect_verifier_rejects "unexpected rule" \
  "CREATE RULE f97_unexpected_rule AS ON INSERT TO public.leads DO INSTEAD NOTHING;"
expect_verifier_rejects "schema create ACL" \
  "GRANT CREATE ON SCHEMA public TO anon;"
expect_verifier_rejects "membership data-plane path" \
  "CREATE ROLE f97_parent_reader NOLOGIN;
   GRANT SELECT ON public.leads TO f97_parent_reader;
   GRANT f97_parent_reader TO authenticated WITH INHERIT TRUE, SET FALSE;"
expect_verifier_rejects "exec_sql extra grantee" \
  "CREATE ROLE f97_extra_exec_sql NOLOGIN;
   GRANT EXECUTE ON FUNCTION public.exec_sql(text) TO f97_extra_exec_sql;"
expect_verifier_rejects "exec_sql public ACL" \
  "GRANT EXECUTE ON FUNCTION public.exec_sql(text) TO anon;"
expect_verifier_rejects "exec_sql overload" \
  "CREATE FUNCTION public.exec_sql(sql_text text, label text) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS 'BEGIN RETURN jsonb_build_object(''status'', ''blocked''); END';"

generate_hold_package replay
before_replay_fingerprint="$(capture_fingerprint)"
wrap_exec_sql "$hold_package"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null
after_replay_fingerprint="$(capture_fingerprint)"
[[ "$before_replay_fingerprint" == "$after_replay_fingerprint" ]]
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$FUNCTIONAL" >/dev/null

setup_v3_boundary
expect_drifted_verifier_not_invoked \
  "public.verify_fase09_7_public_access_closure()" \
  "plpgsql" \
  "BEGIN PERFORM pg_catalog.nextval('public.f97_nontransactional_probe'); RETURN true; END" \
  "apply"

setup_v3_boundary
apply_hold
expect_drifted_verifier_not_invoked \
  "public.verify_fase09_7_leads_email_security_hold()" \
  "plpgsql" \
  "BEGIN PERFORM pg_catalog.nextval('public.f97_nontransactional_probe'); RETURN true; END" \
  "replay"

reset_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$BASELINE" >/dev/null
normalize_authenticator_role
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$ACCESS_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$EXEC_FIXTURE" >/dev/null
generate_hold_package apply
wrap_exec_sql "$hold_package"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null 2>"$failure_log"; then
  printf '%s\n' 'Hold without v3 unexpectedly passed' >&2
  exit 1
fi

expect_hold_failure_rolls_back \
  "-- security-hold-stage-revokes-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'injected after revokes'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-policies-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'injected after policies'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-constraints-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'injected after constraints'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-verifier-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'injected after verifier'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-before-ledger" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'injected before ledger'; END; \$injected\$;"

result=0
