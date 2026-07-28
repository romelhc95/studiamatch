#!/usr/bin/env bash
set -euo pipefail

result=1
package_wrapper=""
prefix3_wrapper=""
prefix4_wrapper=""
prefix5_wrapper=""
trigger_fixture_wrapper=""
trigger_crlf_fixture_wrapper=""
failure_log=""

finish() {
  local exit_status=$?
  trap - EXIT
  set +e
  [[ -z "$package_wrapper" ]] || rm -f -- "$package_wrapper"
  [[ -z "$prefix3_wrapper" ]] || rm -f -- "$prefix3_wrapper"
  [[ -z "$prefix4_wrapper" ]] || rm -f -- "$prefix4_wrapper"
  [[ -z "$prefix5_wrapper" ]] || rm -f -- "$prefix5_wrapper"
  [[ -z "$trigger_fixture_wrapper" ]] || rm -f -- "$trigger_fixture_wrapper"
  [[ -z "$trigger_crlf_fixture_wrapper" ]] || rm -f -- "$trigger_crlf_fixture_wrapper"
  [[ -z "$failure_log" ]] || rm -f -- "$failure_log"
  if [[ $exit_status -eq 0 && $result -eq 0 ]]; then
    printf '%s\n' 'F9.7 PostgreSQL 17 public access and trigger retirement: PASS'
    exit 0
  fi
  printf '%s\n' 'F9.7 PostgreSQL 17 public access and trigger retirement: FAIL' >&2
  [[ $exit_status -eq 0 ]] && exit 1
  exit "$exit_status"
}
trap finish EXIT
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
MANIFEST="$ROOT/db/manifests/fase09_7_free_schema_rls_v2.json"
BASELINE="$ROOT/tests/sql/fase08_minimal_baseline.sql"
ACCESS_FIXTURE="$ROOT/tests/sql/fase09_7_access_fixture.sql"
EXEC_FIXTURE="$ROOT/tests/sql/fase09_exec_sql_fixture.sql"
FUNCTIONAL="$ROOT/tests/sql/fase09_7_functional_test.sql"
CLOSURE="$ROOT/db/migrations/20260727_fase09_7_public_access_closure.sql"
RETIREMENT="$ROOT/db/migrations/20260727_fase09_7_notify_new_lead_retirement.sql"
HISTORICAL_TRIGGER_SOURCE="$ROOT/db/migrations/20260531_fase67b_secure_trigger.sql"
GATE_B_QUERY="$ROOT/scripts/maintenance/fase09_7_gate_b_catalog_v1.sql"

command -v psql >/dev/null
command -v python3 >/dev/null
server_version_num="$(psql -X --quiet --tuples-only --no-align \
  --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  'SHOW server_version_num;' | tr -d '[:space:]')"
[[ "$server_version_num" -ge 170000 && "$server_version_num" -lt 180000 ]]

mapfile -t migrations < <(
  python3 - "$MANIFEST" <<'PY'
import sys
from pathlib import Path

from scripts.maintenance.fase09_7_candidate import load_manifest

for migration in load_manifest(Path(sys.argv[1]), "free"):
    print(migration)
PY
)
[[ ${#migrations[@]} -eq 6 ]]

package_wrapper="$(mktemp /tmp/studiamatch-f97-package.XXXXXX.sql)"
prefix3_wrapper="$(mktemp /tmp/studiamatch-f97-prefix3.XXXXXX.sql)"
prefix4_wrapper="$(mktemp /tmp/studiamatch-f97-prefix4.XXXXXX.sql)"
prefix5_wrapper="$(mktemp /tmp/studiamatch-f97-prefix5.XXXXXX.sql)"
trigger_fixture_wrapper="$(mktemp /tmp/studiamatch-f97-trigger.XXXXXX.sql)"
trigger_crlf_fixture_wrapper="$(mktemp /tmp/studiamatch-f97-trigger-crlf.XXXXXX.sql)"
failure_log="$(mktemp /tmp/studiamatch-f97-failure.XXXXXX.log)"

python3 - "$MANIFEST" "$HISTORICAL_TRIGGER_SOURCE" \
  "$trigger_fixture_wrapper" "$trigger_crlf_fixture_wrapper" \
  "$prefix3_wrapper" "$prefix4_wrapper" "$prefix5_wrapper" <<'PY'
import sys
from pathlib import Path

from scripts.maintenance.fase09_7_candidate import (
    canonical_sql_sha256,
    load_manifest,
)

manifest, trigger_source, trigger_wrapper, trigger_crlf_wrapper, *prefix_wrappers = sys.argv[1:]
paths = load_manifest(Path(manifest), "free")
source = Path(trigger_source).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
fixture_lines = (
        "\\set ON_ERROR_STOP on",
        "DROP FUNCTION public.notify_new_lead();",
        "{source}",
        "REVOKE ALL ON FUNCTION public.notify_new_lead() "
        "FROM PUBLIC, anon, authenticated, service_role CASCADE;",
        "GRANT EXECUTE ON FUNCTION public.notify_new_lead() TO service_role;",
        "CREATE TRIGGER trg_notify_new_lead AFTER INSERT ON public.leads "
        "FOR EACH ROW EXECUTE FUNCTION public.notify_new_lead();",
)
Path(trigger_wrapper).write_text(
    "\n".join(fixture_lines).format(source=source.rstrip()) + "\n",
    encoding="utf-8",
    newline="\n",
)
crlf_source = source.replace("\n", "\r\n").rstrip("\r\n")
Path(trigger_crlf_wrapper).write_text(
    "\n".join(fixture_lines).format(source=crlf_source) + "\n",
    encoding="utf-8",
    newline="",
)
for prefix_size, wrapper_path in zip((3, 4, 5), prefix_wrappers):
    lines = ["\\set ON_ERROR_STOP on"]
    for index, path in enumerate(paths[:prefix_size], start=1):
        lines.append(f"\\i {path}")
        marker = f"sha256:{canonical_sql_sha256(path)}"
        lines.append(
            "INSERT INTO public.supabase_migrations "
            "(version, name, statements, applied_at) VALUES "
            f"({20260727090000 + index}, '{path.stem}', '{marker}', "
            "pg_catalog.clock_timestamp());"
        )
    Path(wrapper_path).write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
PY

reset_database() {
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
SELECT pg_catalog.format('DROP OWNED BY %I;', role.rolname)
FROM pg_catalog.pg_roles AS role
WHERE role.rolname IN (
    'anon', 'authenticated', 'service_role', 'fase097_policy_parent',
    'fase097_private_reader', 'fase097_courses_parent',
    'fase097_inherited_reader',
    'fase097_insert_parent'
)
ORDER BY role.rolname
\gexec
SELECT pg_catalog.format('DROP ROLE %I;', role.rolname)
FROM pg_catalog.pg_roles AS role
WHERE role.rolname IN (
    'anon', 'authenticated', 'service_role', 'fase097_policy_parent',
    'fase097_private_reader', 'fase097_courses_parent',
    'fase097_inherited_reader',
    'fase097_insert_parent'
)
ORDER BY role.rolname
\gexec
CREATE SCHEMA public AUTHORIZATION pg_database_owner;
GRANT USAGE ON SCHEMA public TO PUBLIC;
SQL
}

setup_database() {
  local reviewed_trigger_fixture="${1:-$trigger_fixture_wrapper}"
  reset_database
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$BASELINE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$ACCESS_FIXTURE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$reviewed_trigger_fixture" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$EXEC_FIXTURE" >/dev/null
}

plan_manifest() {
  local expected_pending="$1"
  local output_wrapper="${2:-}"
  python3 - "$TEST_DATABASE_URL" "$MANIFEST" "$expected_pending" \
    "$output_wrapper" <<'PY'
import re
import subprocess
import sys
from pathlib import Path

from scripts.maintenance.fase09_7_candidate import (
    build_manifest_package_sql,
    load_manifest,
    validate_manifest_ledger_state,
)

dsn, manifest, expected_pending, output_wrapper = sys.argv[1:]
paths = load_manifest(Path(manifest), "free")
rows = subprocess.run(
    [
        "psql", "-X", "--quiet", "--tuples-only", "--no-align",
        "--field-separator", "\t", dsn, "--command",
        "SELECT name, statements FROM public.supabase_migrations ORDER BY name;",
    ],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
applied = dict(row.split("\t", 1) for row in rows)


class Adapter:
    @staticmethod
    def rpc_raise(name, _params):
        if re.fullmatch(r"verify_[a-z0-9_]+", name) is None:
            raise RuntimeError("invalid verifier name")
        output = subprocess.run(
            [
                "psql", "-X", "--quiet", "--tuples-only", "--no-align",
                dsn, "--command",
                f"SET ROLE service_role; SELECT public.{name}();",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().splitlines()
        return bool(output and output[-1] == "t")

    @staticmethod
    def scalar_bool(sql):
        output = subprocess.run(
            [
                "psql", "-X", "--quiet", "--tuples-only", "--no-align",
                dsn, "--command", f"SET ROLE service_role; SELECT ({sql});",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().splitlines()
        return bool(output and output[-1] == "t")


pending = validate_manifest_ledger_state(Adapter(), paths, applied)
if len(pending) != int(expected_pending):
    raise RuntimeError(
        f"planner returned {len(pending)} pending; expected {expected_pending}"
    )
if output_wrapper:
    if not pending:
        raise RuntimeError("cannot emit a zero-pending package")
    expected_prefix = {
        path.stem: applied[path.stem] for path in paths if path.stem in applied
    }
    payload = build_manifest_package_sql(
        pending,
        expected_prefix=expected_prefix,
        version=20260727090500 + len(applied),
    )
    delimiter = "$fase097_planned_package$"
    if delimiter in payload:
        raise RuntimeError("reserved package delimiter collision")
    Path(output_wrapper).write_text(
        "\\set ON_ERROR_STOP on\n"
        "SET ROLE service_role;\n"
        f"SELECT public.exec_sql({delimiter}{payload}{delimiter});\n"
        "RESET ROLE;\n",
        encoding="utf-8",
        newline="\n",
    )
PY
}

schema_fingerprint() {
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" <<'SQL'
WITH catalog_rows AS (
    SELECT 'class' AS kind, pg_catalog.concat_ws(
        '|', relation.relname, relation.relrowsecurity, relation.relacl::text
    ) AS value
    FROM pg_catalog.pg_class AS relation
    WHERE relation.relnamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'attribute', pg_catalog.concat_ws(
        '|', relation.relname, attribute.attname, attribute.attacl::text
    )
    FROM pg_catalog.pg_attribute AS attribute
    JOIN pg_catalog.pg_class AS relation ON relation.oid = attribute.attrelid
    WHERE relation.relnamespace = 'public'::regnamespace
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped
    UNION ALL
    SELECT 'policy', pg_catalog.concat_ws(
        '|', policy.tablename, policy.policyname, policy.permissive,
        policy.roles::text, policy.cmd, policy.qual, policy.with_check
    )
    FROM pg_catalog.pg_policies AS policy
    WHERE policy.schemaname = 'public'
    UNION ALL
    SELECT 'function', pg_catalog.concat_ws(
        '|', procedure.proname,
        pg_catalog.pg_get_function_identity_arguments(procedure.oid),
        owner.rolname,
        procedure.prokind, procedure.prosecdef, procedure.provolatile,
        procedure.proconfig::text,
        procedure.proacl::text, procedure.prosrc
    )
    FROM pg_catalog.pg_proc AS procedure
    JOIN pg_catalog.pg_roles AS owner ON owner.oid = procedure.proowner
    WHERE procedure.pronamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'trigger', pg_catalog.concat_ws(
        '|', trigger_record.tgname, trigger_record.tgrelid,
        trigger_record.tgfoid, trigger_record.tgtype,
        trigger_record.tgenabled, trigger_record.tgargs::text,
        trigger_record.tgqual::text, trigger_record.tgparentid
    )
    FROM pg_catalog.pg_trigger AS trigger_record
    WHERE NOT trigger_record.tgisinternal
    UNION ALL
    SELECT 'ledger', pg_catalog.concat_ws('|', name, statements)
    FROM public.supabase_migrations
)
SELECT pg_catalog.md5(COALESCE(pg_catalog.string_agg(
    kind || ':' || value, E'\n' ORDER BY kind, value
), ''))
FROM catalog_rows;
SQL
}

gate_b_row() {
  local output
  local -a rows
  output="$(
    psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
      "$TEST_DATABASE_URL" --file "$GATE_B_QUERY"
  )"
  mapfile -t rows <<< "$output"
  [[ ${#rows[@]} -eq 1 ]]
  printf '%s\n' "${rows[0]}"
}

expect_boundary5_retirement_rejects() {
  local label="$1"
  local setup_sql="$2"
  setup_database
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$prefix5_wrapper" >/dev/null
  plan_manifest 1 "$package_wrapper"
  printf '%s\n' "$setup_sql" | psql -X --quiet --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" >/dev/null
  before_rollback="$(schema_fingerprint | tr -d '[:space:]')"
  if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
    printf 'expected F9.7 retirement rejection for %s\n' "$label" >&2
    exit 1
  fi
  grep -Fq 'F9.7 trigger retirement precondition failed' "$failure_log"
  after_rollback="$(schema_fingerprint | tr -d '[:space:]')"
  [[ "$before_rollback" == "$after_rollback" ]]
  guard_rollback_state="$(psql -X --quiet --tuples-only --no-align \
    --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations WHERE name LIKE '202607%') = 5 AND pg_catalog.to_regprocedure('public.notify_new_lead()') IS NOT NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_trigger WHERE NOT tgisinternal AND tgname = 'trg_notify_new_lead');" \
    | tr -d '[:space:]')"
  [[ "$guard_rollback_state" == "t" ]]
}

# Accepted immutable predecessor boundaries converge to the same six entries.
for prefix_size in 3 4 5; do
  setup_database
  prefix_wrapper="$prefix3_wrapper"
  [[ "$prefix_size" -ne 4 ]] || prefix_wrapper="$prefix4_wrapper"
  [[ "$prefix_size" -ne 5 ]] || prefix_wrapper="$prefix5_wrapper"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$prefix_wrapper" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
    "INSERT INTO public.supabase_migrations (version, name, statements, applied_at) VALUES (20260101000000, '20260101_unrelated_history', 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', pg_catalog.clock_timestamp());" \
    >/dev/null
  if [[ "$prefix_size" -eq 4 ]]; then
    before_direct_repair="$(gate_b_row)"
    IFS='|' read -r -a before_fields <<< "$before_direct_repair"
    [[ ${#before_fields[@]} -eq 37 ]]
    [[ "${before_fields[2]}" == "4" ]]
    [[ "${before_fields[33]}" == "f" ]]
    [[ "${before_fields[34]}" == "f" ]]
    [[ "${before_fields[35]}" == "f" ]]
    [[ "${before_fields[36]}" == "f" ]]
    [[ "${before_fields[24]}" -gt 0 ]]
    [[ "${before_fields[25]}" -gt 0 ]]
  fi
  if [[ "$prefix_size" -eq 5 ]]; then
    before_retirement="$(gate_b_row)"
    IFS='|' read -r -a before_retirement_fields <<< "$before_retirement"
    [[ ${#before_retirement_fields[@]} -eq 37 ]]
    [[ "${before_retirement_fields[2]}" == "5" ]]
    [[ "${before_retirement_fields[36]}" == "t" ]]
  fi
  plan_manifest "$((6 - prefix_size))" "$package_wrapper"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$package_wrapper" >/dev/null
  plan_manifest 0
  retirement_state="$({
    psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
      "$TEST_DATABASE_URL" --command \
      "SET ROLE service_role; SELECT public.verify_fase09_7_notify_new_lead_retirement() AND pg_catalog.to_regprocedure('public.notify_new_lead()') IS NULL AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_trigger WHERE NOT tgisinternal AND tgname = 'trg_notify_new_lead');"
  } | tail -n 1 | tr -d '[:space:]')"
  [[ "$retirement_state" == "t" ]]
  unrelated_state="$(psql -X --quiet --tuples-only --no-align \
    --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
    "SELECT statements FROM public.supabase_migrations WHERE name = '20260101_unrelated_history';" | tr -d '[:space:]')"
  [[ "$unrelated_state" == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" ]]
done

# CRLF in the historical function body is canonicalized without relaxing bytes.
setup_database "$trigger_crlf_fixture_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$prefix5_wrapper" >/dev/null
plan_manifest 1 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null
plan_manifest 0

# Empty ledger applies atomically, passes role tests, and is zero-pending.
setup_database
plan_manifest 6 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$FUNCTIONAL" >/dev/null
before_replay="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT pg_catalog.md5(pg_catalog.string_agg(pg_catalog.concat_ws('|', tablename, policyname, permissive, roles::text, cmd, qual, with_check), E'\\n' ORDER BY tablename, policyname)) FROM pg_catalog.pg_policies WHERE schemaname = 'public' AND tablename IN ('leads', 'email_log');"
} | tr -d '[:space:]')"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$CLOSURE" >/dev/null
after_replay="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT pg_catalog.md5(pg_catalog.string_agg(pg_catalog.concat_ws('|', tablename, policyname, permissive, roles::text, cmd, qual, with_check), E'\\n' ORDER BY tablename, policyname)) FROM pg_catalog.pg_policies WHERE schemaname = 'public' AND tablename IN ('leads', 'email_log');"
} | tr -d '[:space:]')"
[[ "$before_replay" == "$after_replay" ]]
replay_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    'SET ROLE service_role; SELECT public.verify_fase09_7_notify_new_lead_retirement() AND public.verify_fase09_7_public_access_closure() AND public.verify_fase08_hito1_contract();'
} | tail -n 1 | tr -d '[:space:]')"
[[ "$replay_state" == "t" ]]
plan_manifest 0

# Direct replay of the non-idempotent sixth migration fails closed without drift.
before_replay="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --single-transaction --set=ON_ERROR_STOP=1 \
  "$TEST_DATABASE_URL" --file "$RETIREMENT" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'F9.7 trigger retirement precondition failed' "$failure_log"
after_replay="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_replay" == "$after_replay" ]]
plan_manifest 0

# Unknown F9.7 policy drift at prefix four rolls back schema and ledger.
setup_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$prefix4_wrapper" >/dev/null
plan_manifest 2 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  'CREATE POLICY fase097_atomic_fault ON public.email_log FOR SELECT TO PUBLIC USING (true);' \
  >/dev/null
before_rollback="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'Postcondicion fallida: 20260727_fase09_7_public_access_closure' \
  "$failure_log"
after_rollback="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_rollback" == "$after_rollback" ]]
rollback_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations WHERE name LIKE '202607%') = 4 AND pg_catalog.to_regprocedure('public.verify_fase09_7_public_access_closure()') IS NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_policies WHERE schemaname = 'public' AND policyname = 'fase097_atomic_fault');"
} | tr -d '[:space:]')"
[[ "$rollback_state" == "t" ]]

# An inherited ACL source not attributable by the consumed evidence is not
# silently repaired; the exact package fails closed and preserves prefix four.
setup_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$prefix4_wrapper" >/dev/null
plan_manifest 2 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
CREATE ROLE fase097_inherited_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
GRANT fase097_inherited_reader TO anon;
GRANT SELECT ON public.leads TO fase097_inherited_reader;
SQL
before_rollback="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'Postcondicion fallida: 20260727_fase09_7_public_access_closure' \
  "$failure_log"
after_rollback="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_rollback" == "$after_rollback" ]]
inherited_rollback_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations WHERE name LIKE '202607%') = 4 AND pg_catalog.to_regprocedure('public.verify_fase09_7_public_access_closure()') IS NULL AND pg_catalog.has_table_privilege('anon', 'public.leads', 'SELECT');"
} | tr -d '[:space:]')"
[[ "$inherited_rollback_state" == "t" ]]

# Trigger/function drift at boundary five fails before either object is dropped.
expect_boundary5_retirement_rejects "function config drift" \
  "ALTER FUNCTION public.notify_new_lead() SET search_path = '';"
expect_boundary5_retirement_rejects "notify overload" \
  $'CREATE FUNCTION public.notify_new_lead(p_value integer)\nRETURNS integer\nLANGUAGE sql\nAS $overload$\n    SELECT p_value;\n$overload$;'
expect_boundary5_retirement_rejects "extra leads trigger" \
  $'CREATE FUNCTION public.fase097_extra_trigger()\nRETURNS trigger\nLANGUAGE plpgsql\nAS $extra$\nBEGIN\n    RETURN NEW;\nEND;\n$extra$;\nCREATE TRIGGER fase097_extra_trigger\nAFTER INSERT ON public.leads\nFOR EACH ROW EXECUTE FUNCTION public.fase097_extra_trigger();'
expect_boundary5_retirement_rejects "same trigger name other table" \
  $'CREATE TABLE public.fase097_other (id integer);\nCREATE FUNCTION public.fase097_other_trigger()\nRETURNS trigger\nLANGUAGE plpgsql\nAS $other$\nBEGIN\n    RETURN NEW;\nEND;\n$other$;\nCREATE TRIGGER trg_notify_new_lead\nAFTER INSERT ON public.fase097_other\nFOR EACH ROW EXECUTE FUNCTION public.fase097_other_trigger();'
expect_boundary5_retirement_rejects "function reuse by another trigger" \
  $'CREATE TABLE public.fase097_other (id integer);\nCREATE TRIGGER fase097_reuse_notify\nAFTER INSERT ON public.fase097_other\nFOR EACH ROW EXECUTE FUNCTION public.notify_new_lead();'
expect_boundary5_retirement_rejects "disabled trigger" \
  "ALTER TABLE public.leads DISABLE TRIGGER trg_notify_new_lead;"
expect_boundary5_retirement_rejects "wrong trigger timing" \
  $'DROP TRIGGER trg_notify_new_lead ON public.leads;\nCREATE TRIGGER trg_notify_new_lead\nBEFORE INSERT ON public.leads\nFOR EACH ROW EXECUTE FUNCTION public.notify_new_lead();'
expect_boundary5_retirement_rejects "function owner drift" \
  "ALTER FUNCTION public.notify_new_lead() OWNER TO service_role;"
expect_boundary5_retirement_rejects "function ACL drift" \
  "GRANT EXECUTE ON FUNCTION public.notify_new_lead() TO authenticated;"
expect_boundary5_retirement_rejects "function body drift" \
  $'CREATE OR REPLACE FUNCTION public.notify_new_lead()\nRETURNS trigger\nLANGUAGE plpgsql\nSECURITY DEFINER\nSET search_path = \'pg_catalog, public\'\nAS $function$\nBEGIN\n    RETURN NEW;\nEND;\n$function$;'

# A compatible verifier-name collision is rejected before either drop.
setup_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$prefix5_wrapper" >/dev/null
plan_manifest 1 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  "CREATE FUNCTION public.verify_fase09_7_notify_new_lead_retirement() RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS 'SELECT true';" >/dev/null
before_rollback="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'F9.7 trigger retirement precondition failed' "$failure_log"
after_rollback="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_rollback" == "$after_rollback" ]]
collision_rollback_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations WHERE name LIKE '202607%') = 5 AND pg_catalog.to_regprocedure('public.notify_new_lead()') IS NOT NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_trigger WHERE NOT tgisinternal AND tgname = 'trg_notify_new_lead');"
} | tr -d '[:space:]')"
[[ "$collision_rollback_state" == "t" ]]

# A NULL-returning applied-prefix verifier is rejected again in the package.
setup_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$prefix5_wrapper" >/dev/null
plan_manifest 1 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
CREATE OR REPLACE FUNCTION public.verify_fase09_7_public_access_closure()
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $function$
BEGIN
    RETURN NULL;
END;
$function$;
SQL
before_rollback="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'Postcondicion de prefijo fallida: 20260727_fase09_7_public_access_closure' \
  "$failure_log"
after_rollback="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_rollback" == "$after_rollback" ]]
null_prefix_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations WHERE name LIKE '202607%') = 5 AND pg_catalog.to_regprocedure('public.notify_new_lead()') IS NOT NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_trigger WHERE NOT tgisinternal AND tgname = 'trg_notify_new_lead');"
} | tr -d '[:space:]')"
[[ "$null_prefix_state" == "t" ]]

# A failure injected after both drops still rolls back schema and the ledger.
setup_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$prefix5_wrapper" >/dev/null
plan_manifest 1 "$package_wrapper"
python3 - "$package_wrapper" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = path.read_text(encoding="utf-8")
needle = "DROP FUNCTION public.notify_new_lead();"
replacement = needle + """
DO $fase097_fault$
BEGIN
    RAISE EXCEPTION 'F9.7 induced post-drop rollback';
END;
$fase097_fault$;"""
if payload.count(needle) != 1:
    raise RuntimeError("post-drop fault injection target drift")
path.write_text(payload.replace(needle, replacement), encoding="utf-8", newline="\n")
PY
before_rollback="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'F9.7 induced post-drop rollback' "$failure_log"
after_rollback="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_rollback" == "$after_rollback" ]]
post_drop_rollback_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations WHERE name LIKE '202607%') = 5 AND pg_catalog.to_regprocedure('public.notify_new_lead()') IS NOT NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_trigger WHERE NOT tgisinternal AND tgname = 'trg_notify_new_lead');"
} | tr -d '[:space:]')"
[[ "$post_drop_rollback_state" == "t" ]]

# Boundary six rejects verifier body drift through the external catalog check.
setup_database
plan_manifest 6 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  "CREATE OR REPLACE FUNCTION public.verify_fase09_7_notify_new_lead_retirement() RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS 'SELECT true';" >/dev/null
if plan_manifest 0 >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'Postcondicion externa fallida: 20260727_fase09_7_notify_new_lead_retirement' \
  "$failure_log"
verifier_drift_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations WHERE name LIKE '202607%') = 6 AND pg_catalog.to_regprocedure('public.notify_new_lead()') IS NULL AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_trigger WHERE NOT tgisinternal AND tgname = 'trg_notify_new_lead');"
} | tr -d '[:space:]')"
[[ "$verifier_drift_state" == "t" ]]

reset_database
result=0
