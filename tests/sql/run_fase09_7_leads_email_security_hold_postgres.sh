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

capture_legacy_digests() {
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" <<'SQL'
RESET ROLE;
SELECT pg_catalog.jsonb_build_object(
    'email_log', (
        SELECT pg_catalog.jsonb_build_object(
            'rows', pg_catalog.count(*),
            'sha256', pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(email_log) ORDER BY email_log.id)::text, '[]'),
                'UTF8'
            )), 'hex')
        )
        FROM public.email_log AS email_log
    ),
    'leads', (
        SELECT pg_catalog.jsonb_build_object(
            'rows', pg_catalog.count(*),
            'sha256', pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(leads) ORDER BY leads.id)::text, '[]'),
                'UTF8'
            )), 'hex')
        )
        FROM public.leads AS leads
    )
)::text;
SQL
}

capture_fingerprint() {
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" <<'SQL'
RESET ROLE;
WITH RECURSIVE target_relations(relation_oid) AS (
    VALUES ('public.leads'::pg_catalog.regclass), ('public.email_log'::pg_catalog.regclass)
), dependent_views(view_oid, path) AS (
    SELECT view_record.oid, ARRAY[view_record.oid]
    FROM pg_catalog.pg_rewrite AS rewrite_record
    JOIN pg_catalog.pg_depend AS dependency
      ON dependency.classid = 'pg_catalog.pg_rewrite'::pg_catalog.regclass
     AND dependency.objid = rewrite_record.oid
    JOIN pg_catalog.pg_class AS view_record
      ON view_record.oid = rewrite_record.ev_class
    WHERE dependency.refobjid IN (SELECT relation_oid FROM target_relations)
      AND view_record.relkind IN ('v', 'm')
    UNION ALL
    SELECT next_view.oid, dependent_views.path || next_view.oid
    FROM dependent_views
    JOIN pg_catalog.pg_rewrite AS rewrite_record ON true
    JOIN pg_catalog.pg_depend AS dependency
      ON dependency.classid = 'pg_catalog.pg_rewrite'::pg_catalog.regclass
     AND dependency.objid = rewrite_record.oid
     AND dependency.refobjid = dependent_views.view_oid
    JOIN pg_catalog.pg_class AS next_view
      ON next_view.oid = rewrite_record.ev_class
    WHERE next_view.relkind IN ('v', 'm')
      AND next_view.oid <> ALL(dependent_views.path)
), relevant_relations(relation_oid) AS (
    SELECT relation_oid FROM target_relations
    UNION
    SELECT view_oid FROM dependent_views
    UNION
    SELECT relation.oid
    FROM pg_catalog.pg_class AS relation
    JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
    WHERE namespace.nspname LIKE 'f97\_%' ESCAPE '\'
       OR relation.relname LIKE 'f97\_%' ESCAPE '\'
)
SELECT pg_catalog.jsonb_build_object(
    'columns', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'acl', attribute.attacl::text,
            'column', attribute.attname,
            'position', attribute.attnum,
            'relation', relation.relname,
            'schema', namespace.nspname,
            'type', attribute.atttypid::pg_catalog.regtype::text
        ) ORDER BY namespace.nspname, relation.relname, attribute.attnum)
        FROM pg_catalog.pg_attribute AS attribute
        JOIN pg_catalog.pg_class AS relation ON relation.oid = attribute.attrelid
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE attribute.attrelid IN (SELECT relation_oid FROM relevant_relations)
          AND attribute.attnum > 0
          AND NOT attribute.attisdropped
    ), '[]'::pg_catalog.jsonb),
    'constraints', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'definition', pg_catalog.pg_get_constraintdef(constraint_record.oid, true),
            'name', constraint_record.conname,
            'reference_relation', reference_relation.relname,
            'reference_schema', reference_schema.nspname,
            'relation', relation.relname,
            'schema', namespace.nspname,
            'type', constraint_record.contype,
            'validated', constraint_record.convalidated
        ) ORDER BY namespace.nspname, relation.relname, constraint_record.conname)
        FROM pg_catalog.pg_constraint AS constraint_record
        JOIN pg_catalog.pg_class AS relation ON relation.oid = constraint_record.conrelid
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        LEFT JOIN pg_catalog.pg_class AS reference_relation ON reference_relation.oid = constraint_record.confrelid
        LEFT JOIN pg_catalog.pg_namespace AS reference_schema ON reference_schema.oid = reference_relation.relnamespace
        WHERE constraint_record.conrelid IN (SELECT relation_oid FROM relevant_relations)
           OR constraint_record.confrelid IN (SELECT relation_oid FROM target_relations)
    ), '[]'::pg_catalog.jsonb),
    'legacy_row_digests', (
        SELECT digest.payload
        FROM (
            SELECT pg_catalog.jsonb_build_object(
                'email_log', (
                    SELECT pg_catalog.jsonb_build_object(
                        'rows', pg_catalog.count(*),
                        'sha256', pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                            COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(email_log) ORDER BY email_log.id)::text, '[]'),
                            'UTF8'
                        )), 'hex')
                    )
                    FROM public.email_log AS email_log
                ),
                'leads', (
                    SELECT pg_catalog.jsonb_build_object(
                        'rows', pg_catalog.count(*),
                        'sha256', pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
                            COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(leads) ORDER BY leads.id)::text, '[]'),
                            'UTF8'
                        )), 'hex')
                    )
                    FROM public.leads AS leads
                )
            ) AS payload
        ) AS digest
    ),
    'ledger', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'applied_at', ledger.applied_at::text,
            'name', ledger.name,
            'statements', ledger.statements,
            'version', ledger.version
        ) ORDER BY ledger.name)
        FROM public.supabase_migrations AS ledger
    ), '[]'::pg_catalog.jsonb),
    'memberships', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'admin', membership.admin_option,
            'inherit', membership.inherit_option,
            'member', member_record.rolname,
            'role', role_record.rolname,
            'set', membership.set_option
        ) ORDER BY role_record.rolname, member_record.rolname)
        FROM pg_catalog.pg_auth_members AS membership
        JOIN pg_catalog.pg_roles AS role_record ON role_record.oid = membership.roleid
        JOIN pg_catalog.pg_roles AS member_record ON member_record.oid = membership.member
        WHERE role_record.rolname !~ '^pg_'
          AND member_record.rolname !~ '^pg_'
    ), '[]'::pg_catalog.jsonb),
    'policies', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(policy)
            ORDER BY policy.schemaname, policy.tablename, policy.policyname)
        FROM pg_catalog.pg_policies AS policy
        WHERE policy.schemaname = 'public'
           OR policy.schemaname LIKE 'f97\_%' ESCAPE '\'
    ), '[]'::pg_catalog.jsonb),
    'publication_namespaces', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'publication', publication.pubname,
            'schema', namespace.nspname
        ) ORDER BY publication.pubname, namespace.nspname)
        FROM pg_catalog.pg_publication_namespace AS publication_namespace
        JOIN pg_catalog.pg_publication AS publication ON publication.oid = publication_namespace.pnpubid
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = publication_namespace.pnnspid
    ), '[]'::pg_catalog.jsonb),
    'publication_relations', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'publication', publication.pubname,
            'relation', relation.relname,
            'schema', namespace.nspname
        ) ORDER BY publication.pubname, namespace.nspname, relation.relname)
        FROM pg_catalog.pg_publication_rel AS publication_relation
        JOIN pg_catalog.pg_publication AS publication ON publication.oid = publication_relation.prpubid
        JOIN pg_catalog.pg_class AS relation ON relation.oid = publication_relation.prrelid
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
    ), '[]'::pg_catalog.jsonb),
    'publications', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'all_tables', publication.puballtables,
            'delete', publication.pubdelete,
            'insert', publication.pubinsert,
            'name', publication.pubname,
            'truncate', publication.pubtruncate,
            'update', publication.pubupdate
        ) ORDER BY publication.pubname)
        FROM pg_catalog.pg_publication AS publication
    ), '[]'::pg_catalog.jsonb),
    'relations', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'acl', relation.relacl::text,
            'force_rls', relation.relforcerowsecurity,
            'kind', relation.relkind,
            'name', relation.relname,
            'owner', owner.rolname,
            'reloptions', relation.reloptions,
            'rls', relation.relrowsecurity,
            'schema', namespace.nspname
        ) ORDER BY namespace.nspname, relation.relname)
        FROM pg_catalog.pg_class AS relation
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = relation.relowner
        WHERE relation.oid IN (SELECT relation_oid FROM relevant_relations)
    ), '[]'::pg_catalog.jsonb),
    'routines', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'acl', COALESCE(procedure_record.proacl, pg_catalog.acldefault('f', procedure_record.proowner))::text,
            'config', procedure_record.proconfig,
            'definition', pg_catalog.pg_get_functiondef(procedure_record.oid),
            'kind', procedure_record.prokind,
            'language', language_record.lanname,
            'owner', owner.rolname,
            'return_type', procedure_record.prorettype::pg_catalog.regtype::text,
            'schema', namespace.nspname,
            'security_definer', procedure_record.prosecdef,
            'signature', namespace.nspname || '.' || procedure_record.proname || '(' ||
                pg_catalog.pg_get_function_identity_arguments(procedure_record.oid) || ')',
            'source', pg_catalog.replace(procedure_record.prosrc, E'\r\n', E'\n'),
            'volatility', procedure_record.provolatile
        ) ORDER BY namespace.nspname, procedure_record.proname, procedure_record.oid)
        FROM pg_catalog.pg_proc AS procedure_record
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = procedure_record.pronamespace
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = procedure_record.proowner
        JOIN pg_catalog.pg_language AS language_record ON language_record.oid = procedure_record.prolang
        WHERE procedure_record.prokind IN ('f', 'p')
          AND namespace.nspname NOT IN ('pg_catalog', 'information_schema')
          AND (
              namespace.nspname = 'public'
              OR namespace.nspname LIKE 'f97\_%' ESCAPE '\'
              OR procedure_record.proname LIKE 'f97\_%' ESCAPE '\'
              OR procedure_record.prosrc ~* '\m(leads|email_log)\M'
              OR pg_catalog.pg_get_functiondef(procedure_record.oid) ~* '\m(leads|email_log)\M'
          )
    ), '[]'::pg_catalog.jsonb),
    'rules', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'definition', pg_catalog.pg_get_ruledef(rewrite_record.oid),
            'enabled', rewrite_record.ev_enabled,
            'event', rewrite_record.ev_type,
            'name', rewrite_record.rulename,
            'relation', relation.relname,
            'schema', namespace.nspname
        ) ORDER BY namespace.nspname, relation.relname, rewrite_record.rulename)
        FROM pg_catalog.pg_rewrite AS rewrite_record
        JOIN pg_catalog.pg_class AS relation ON relation.oid = rewrite_record.ev_class
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE rewrite_record.rulename <> '_RETURN'
          AND (
              relation.oid IN (SELECT relation_oid FROM relevant_relations)
              OR namespace.nspname = 'public'
              OR namespace.nspname LIKE 'f97\_%' ESCAPE '\'
          )
    ), '[]'::pg_catalog.jsonb),
    'schemas', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'acl', namespace.nspacl::text,
            'owner', owner.rolname,
            'schema', namespace.nspname
        ) ORDER BY namespace.nspname)
        FROM pg_catalog.pg_namespace AS namespace
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = namespace.nspowner
        WHERE namespace.oid IN (
            SELECT relation.relnamespace
            FROM pg_catalog.pg_class AS relation
            WHERE relation.oid IN (SELECT relation_oid FROM relevant_relations)
        )
           OR namespace.nspname = 'public'
           OR namespace.nspname LIKE 'f97\_%' ESCAPE '\'
    ), '[]'::pg_catalog.jsonb),
    'triggers', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'definition', pg_catalog.pg_get_triggerdef(trigger_record.oid, true),
            'enabled', trigger_record.tgenabled,
            'function', trigger_schema.nspname || '.' || trigger_function.proname || '(' ||
                pg_catalog.pg_get_function_identity_arguments(trigger_function.oid) || ')',
            'name', trigger_record.tgname,
            'relation', relation.relname,
            'schema', namespace.nspname
        ) ORDER BY namespace.nspname, relation.relname, trigger_record.tgname)
        FROM pg_catalog.pg_trigger AS trigger_record
        JOIN pg_catalog.pg_class AS relation ON relation.oid = trigger_record.tgrelid
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        JOIN pg_catalog.pg_proc AS trigger_function ON trigger_function.oid = trigger_record.tgfoid
        JOIN pg_catalog.pg_namespace AS trigger_schema ON trigger_schema.oid = trigger_function.pronamespace
        WHERE NOT trigger_record.tgisinternal
          AND (
              relation.oid IN (SELECT relation_oid FROM relevant_relations)
              OR namespace.nspname = 'public'
              OR namespace.nspname LIKE 'f97\_%' ESCAPE '\'
          )
    ), '[]'::pg_catalog.jsonb),
    'views', COALESCE((
        SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
            'acl', view_record.relacl::text,
            'definition', pg_catalog.pg_get_viewdef(view_record.oid, true),
            'kind', view_record.relkind,
            'name', view_record.relname,
            'owner', owner.rolname,
            'reloptions', view_record.reloptions,
            'schema', namespace.nspname
        ) ORDER BY namespace.nspname, view_record.relname)
        FROM dependent_views
        JOIN pg_catalog.pg_class AS view_record ON view_record.oid = dependent_views.view_oid
        JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = view_record.relnamespace
        JOIN pg_catalog.pg_roles AS owner ON owner.oid = view_record.relowner
    ), '[]'::pg_catalog.jsonb)
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
  local expected_error="${marker#-- }"
  setup_v3_boundary
  local before_fingerprint
  local before_legacy_digests
  before_fingerprint="$(capture_fingerprint)"
  before_legacy_digests="$(capture_legacy_digests)"
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
  if ! grep -Fq "$expected_error" "$failure_log"; then
    printf 'Injected failure did not report expected marker: %s\n' "$marker" >&2
    return 1
  fi
  local after_fingerprint
  local after_legacy_digests
  after_fingerprint="$(capture_fingerprint)"
  after_legacy_digests="$(capture_legacy_digests)"
  if [[ "$before_fingerprint" != "$after_fingerprint" ]]; then
    printf 'Injected failure left catalog/data drift after marker: %s\n' "$marker" >&2
    return 1
  fi
  if [[ "$before_legacy_digests" != "$after_legacy_digests" ]]; then
    printf 'Injected failure changed legacy digests after marker: %s\n' "$marker" >&2
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

expect_domain_return_verifier_not_invoked() {
  local sequence_name="f97_domain_nontransactional_probe"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<SQL
DROP SEQUENCE IF EXISTS public.${sequence_name};
CREATE SEQUENCE public.${sequence_name};
CREATE OR REPLACE FUNCTION public.f97_domain_probe(value boolean)
RETURNS boolean
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = ''
AS \$domain_probe\$
BEGIN
    PERFORM pg_catalog.nextval('public.${sequence_name}'::pg_catalog.regclass);
    RETURN true;
END;
\$domain_probe\$;
ALTER FUNCTION public.f97_domain_probe(boolean) OWNER TO postgres;
REVOKE ALL ON FUNCTION public.f97_domain_probe(boolean) FROM PUBLIC, anon, authenticated, authenticator, service_role;
CREATE DOMAIN public.f97_boolean_domain AS boolean
CHECK (public.f97_domain_probe(VALUE));
SQL
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --command "SELECT procedure_record.prosrc FROM pg_catalog.pg_proc AS procedure_record WHERE procedure_record.oid = pg_catalog.to_regprocedure('public.verify_fase09_7_leads_email_security_hold()');" \
    >"$failure_package"
  python3 - "$failure_package" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
body = path.read_text(encoding="utf-8")
tag = "domain_return_verifier"
if f"${tag}$" in body:
    raise SystemExit("domain return verifier dollar quote tag collision")
path.write_text(
    "\\set ON_ERROR_STOP on\n"
    "DROP FUNCTION public.verify_fase09_7_leads_email_security_hold();\n"
    "CREATE FUNCTION public.verify_fase09_7_leads_email_security_hold()\n"
    "RETURNS public.f97_boolean_domain\n"
    "LANGUAGE plpgsql\n"
    "STABLE\n"
    "SECURITY INVOKER\n"
    "SET search_path = ''\n"
    f"AS ${tag}$\n{body}${tag}$;\n"
    "ALTER FUNCTION public.verify_fase09_7_leads_email_security_hold() OWNER TO postgres;\n"
    "REVOKE ALL ON FUNCTION public.verify_fase09_7_leads_email_security_hold() "
    "FROM PUBLIC, anon, authenticated, authenticator, service_role;\n"
    "GRANT EXECUTE ON FUNCTION public.verify_fase09_7_leads_email_security_hold() TO service_role;\n",
    encoding="utf-8",
    newline="\n",
)
PY
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$failure_package" >/dev/null
  generate_hold_package replay
  wrap_exec_sql "$hold_package"
  if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null 2>"$failure_log"; then
    printf '%s\n' 'Domain-return verifier unexpectedly passed replay' >&2
    return 1
  fi
  sequence_called="$(psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command "SELECT is_called FROM public.${sequence_name};")"
  if [[ "$sequence_called" != "f" ]]; then
    printf '%s\n' 'Domain-return verifier was invoked before return type attestation' >&2
    return 1
  fi
  reset_database
}

setup_v3_boundary
before_apply_legacy_digests="$(capture_legacy_digests)"
apply_hold
after_apply_legacy_digests="$(capture_legacy_digests)"
[[ "$before_apply_legacy_digests" == "$after_apply_legacy_digests" ]]
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$FUNCTIONAL" >/dev/null

expect_verifier_accepts "non-exposed administrative routine" \
  "CREATE SCHEMA f97_admin AUTHORIZATION postgres;
   REVOKE ALL ON SCHEMA f97_admin FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE FUNCTION f97_admin.noop() RETURNS integer LANGUAGE sql STABLE AS 'SELECT 1';
   REVOKE ALL ON FUNCTION f97_admin.noop() FROM PUBLIC, anon, authenticated, authenticator, service_role;"
expect_verifier_accepts "private incoming FK and trigger audit" \
  "CREATE SCHEMA f97_private AUTHORIZATION postgres;
   REVOKE ALL ON SCHEMA f97_private FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE TABLE f97_private.f97_lead_fk_audit (id uuid PRIMARY KEY, lead_id uuid REFERENCES public.leads(id));
   CREATE TABLE f97_private.f97_trigger_audit (id uuid PRIMARY KEY);
   CREATE FUNCTION f97_private.f97_trigger_audit_fn() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS 'BEGIN PERFORM 1 FROM public.leads LIMIT 1; RETURN NEW; END';
   CREATE TRIGGER f97_private_trigger BEFORE INSERT ON f97_private.f97_trigger_audit FOR EACH ROW EXECUTE FUNCTION f97_private.f97_trigger_audit_fn();
   REVOKE ALL ON FUNCTION f97_private.f97_trigger_audit_fn() FROM PUBLIC, anon, authenticated, authenticator, service_role;"
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
expect_verifier_rejects "trigger relay oracle" \
  "CREATE TABLE public.f97_trigger_oracle (id uuid PRIMARY KEY);
   CREATE FUNCTION public.f97_trigger_oracle_fn() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS 'BEGIN IF EXISTS (SELECT 1 FROM public.leads) THEN RAISE EXCEPTION ''lead oracle''; END IF; RETURN NEW; END';
   CREATE TRIGGER f97_trigger_oracle BEFORE INSERT ON public.f97_trigger_oracle FOR EACH ROW EXECUTE FUNCTION public.f97_trigger_oracle_fn();
   REVOKE ALL ON FUNCTION public.f97_trigger_oracle_fn() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   GRANT INSERT ON public.f97_trigger_oracle TO anon;"
expect_verifier_rejects "trigger relay column grant" \
  "CREATE TABLE public.f97_trigger_column_oracle (id uuid PRIMARY KEY, note text);
   CREATE FUNCTION public.f97_trigger_column_oracle_fn() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS 'BEGIN PERFORM 1 FROM public.leads LIMIT 1; RETURN NEW; END';
   CREATE TRIGGER f97_trigger_column_oracle BEFORE INSERT ON public.f97_trigger_column_oracle FOR EACH ROW EXECUTE FUNCTION public.f97_trigger_column_oracle_fn();
   REVOKE ALL ON FUNCTION public.f97_trigger_column_oracle_fn() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   GRANT INSERT (id) ON public.f97_trigger_column_oracle TO anon;"
expect_verifier_rejects "trigger relay unqualified search path" \
  "CREATE TABLE public.f97_trigger_unqualified_oracle (id uuid PRIMARY KEY);
   CREATE FUNCTION public.f97_trigger_unqualified_oracle_fn() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS 'BEGIN PERFORM 1 FROM leads LIMIT 1; RETURN NEW; END';
   CREATE TRIGGER f97_trigger_unqualified_oracle BEFORE INSERT ON public.f97_trigger_unqualified_oracle FOR EACH ROW EXECUTE FUNCTION public.f97_trigger_unqualified_oracle_fn();
   REVOKE ALL ON FUNCTION public.f97_trigger_unqualified_oracle_fn() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   GRANT INSERT ON public.f97_trigger_unqualified_oracle TO anon;"
expect_verifier_rejects "rule relay oracle" \
  "CREATE TABLE public.f97_rule_oracle (id uuid PRIMARY KEY);
   CREATE RULE f97_rule_oracle_rule AS ON INSERT TO public.f97_rule_oracle DO ALSO SELECT id FROM public.leads;
   GRANT INSERT ON public.f97_rule_oracle TO anon;"
expect_verifier_rejects "rule relay column grant" \
  "CREATE TABLE public.f97_rule_column_oracle (id uuid PRIMARY KEY, note text);
   CREATE RULE f97_rule_column_oracle_rule AS ON INSERT TO public.f97_rule_column_oracle DO ALSO SELECT id FROM public.leads;
   GRANT INSERT (id) ON public.f97_rule_column_oracle TO anon;"
expect_verifier_rejects "routine private helper wrapper" \
  "CREATE SCHEMA f97_private AUTHORIZATION postgres;
   REVOKE ALL ON SCHEMA f97_private FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE FUNCTION f97_private.hidden_counter() RETURNS integer LANGUAGE sql STABLE AS 'SELECT count(*)::integer FROM public.leads';
   REVOKE ALL ON FUNCTION f97_private.hidden_counter() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE FUNCTION public.f97_public_counter() RETURNS integer LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS 'SELECT f97_private.hidden_counter()';
   REVOKE ALL ON FUNCTION public.f97_public_counter() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   GRANT EXECUTE ON FUNCTION public.f97_public_counter() TO anon;"
expect_verifier_rejects "routine unqualified search path" \
  "CREATE FUNCTION public.f97_unqualified_counter() RETURNS integer LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public AS 'BEGIN RETURN (SELECT count(*)::integer FROM leads); END';
   REVOKE ALL ON FUNCTION public.f97_unqualified_counter() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   GRANT EXECUTE ON FUNCTION public.f97_unqualified_counter() TO authenticated;"
expect_verifier_rejects "routine unqualified private helper" \
  "CREATE SCHEMA f97_private AUTHORIZATION postgres;
   REVOKE ALL ON SCHEMA f97_private FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE FUNCTION f97_private.hidden_counter() RETURNS integer LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public AS 'BEGIN RETURN (SELECT count(*)::integer FROM leads); END';
   REVOKE ALL ON FUNCTION f97_private.hidden_counter() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE FUNCTION public.f97_public_unqualified_counter() RETURNS integer LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = f97_private AS 'BEGIN RETURN hidden_counter(); END';
   REVOKE ALL ON FUNCTION public.f97_public_unqualified_counter() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   GRANT EXECUTE ON FUNCTION public.f97_public_unqualified_counter() TO anon;"
expect_verifier_rejects "rule private helper wrapper" \
  "CREATE SCHEMA f97_private AUTHORIZATION postgres;
   REVOKE ALL ON SCHEMA f97_private FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE FUNCTION f97_private.hidden_reader() RETURNS integer LANGUAGE sql STABLE AS 'SELECT count(*)::integer FROM public.leads';
   REVOKE ALL ON FUNCTION f97_private.hidden_reader() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE TABLE public.f97_rule_helper_oracle (id uuid PRIMARY KEY);
   CREATE RULE f97_rule_helper_oracle_rule AS ON INSERT TO public.f97_rule_helper_oracle DO ALSO SELECT f97_private.hidden_reader();
   GRANT INSERT ON public.f97_rule_helper_oracle TO anon;"
expect_verifier_rejects "rule unqualified helper wrapper" \
  "CREATE FUNCTION public.f97_hidden_reader() RETURNS integer LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public AS 'BEGIN RETURN (SELECT count(*)::integer FROM leads); END';
   REVOKE ALL ON FUNCTION public.f97_hidden_reader() FROM PUBLIC, anon, authenticated, authenticator, service_role;
   CREATE TABLE public.f97_rule_unqualified_helper_oracle (id uuid PRIMARY KEY);
   CREATE RULE f97_rule_unqualified_helper_oracle_rule AS ON INSERT TO public.f97_rule_unqualified_helper_oracle DO ALSO SELECT f97_hidden_reader();
   GRANT INSERT ON public.f97_rule_unqualified_helper_oracle TO anon;"
expect_verifier_rejects "incoming FK oracle" \
  "CREATE TABLE public.f97_lead_fk_oracle (id uuid PRIMARY KEY, lead_id uuid REFERENCES public.leads(id));
   GRANT INSERT ON public.f97_lead_fk_oracle TO anon;"
expect_verifier_rejects "schema create ACL" \
  "GRANT CREATE ON SCHEMA public TO anon;"
expect_verifier_rejects "membership inherit option transitive path" \
  "CREATE ROLE f97_parent_reader NOLOGIN;
   CREATE ROLE f97_mid_reader NOLOGIN;
   GRANT SELECT ON public.leads TO f97_parent_reader;
   GRANT f97_parent_reader TO f97_mid_reader WITH INHERIT TRUE, SET FALSE, ADMIN FALSE;
   GRANT f97_mid_reader TO authenticated WITH INHERIT TRUE, SET FALSE, ADMIN FALSE;"
expect_verifier_rejects "membership set option transitive path" \
  "CREATE ROLE f97_parent_reader NOLOGIN;
   CREATE ROLE f97_mid_reader NOLOGIN;
   GRANT SELECT ON public.email_log TO f97_parent_reader;
   GRANT f97_parent_reader TO f97_mid_reader WITH INHERIT TRUE, SET FALSE, ADMIN FALSE;
   GRANT f97_mid_reader TO authenticated WITH INHERIT FALSE, SET TRUE, ADMIN FALSE;"
expect_verifier_rejects "membership admin option transitive path" \
  "CREATE ROLE f97_parent_reader NOLOGIN;
   CREATE ROLE f97_mid_reader NOLOGIN;
   GRANT SELECT ON public.leads TO f97_parent_reader;
   GRANT f97_parent_reader TO f97_mid_reader WITH INHERIT TRUE, SET FALSE, ADMIN FALSE;
   GRANT f97_mid_reader TO service_role WITH INHERIT FALSE, SET FALSE, ADMIN TRUE;"
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
before_replay_legacy_digests="$(capture_legacy_digests)"
wrap_exec_sql "$hold_package"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$exec_wrapper" >/dev/null
after_replay_fingerprint="$(capture_fingerprint)"
after_replay_legacy_digests="$(capture_legacy_digests)"
[[ "$before_replay_fingerprint" == "$after_replay_fingerprint" ]]
[[ "$before_replay_legacy_digests" == "$after_replay_legacy_digests" ]]
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

setup_v3_boundary
apply_hold
expect_domain_return_verifier_not_invoked

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
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-revokes-complete'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-policies-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-policies-complete'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-constraints-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-constraints-complete'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-verifier-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-verifier-complete'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-postcondition-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-postcondition-complete'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-terminal-verification-complete" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-terminal-verification-complete'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-before-ledger" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-before-ledger'; END; \$injected\$;"
expect_hold_failure_rolls_back \
  "-- security-hold-stage-after-ledger" \
  "DO \$injected\$ BEGIN RAISE EXCEPTION 'security-hold-stage-after-ledger'; END; \$injected\$;"

result=0
