#!/usr/bin/env bash
set -euo pipefail

result=1
package_wrapper=""
prefix3_wrapper=""
prefix4_wrapper=""
failure_log=""

finish() {
  local exit_status=$?
  trap - EXIT
  set +e
  [[ -z "$package_wrapper" ]] || rm -f -- "$package_wrapper"
  [[ -z "$prefix3_wrapper" ]] || rm -f -- "$prefix3_wrapper"
  [[ -z "$prefix4_wrapper" ]] || rm -f -- "$prefix4_wrapper"
  [[ -z "$failure_log" ]] || rm -f -- "$failure_log"
  if [[ $exit_status -eq 0 && $result -eq 0 ]]; then
    printf '%s\n' 'F9.7 PostgreSQL 17 public access closure: PASS'
    exit 0
  fi
  printf '%s\n' 'F9.7 PostgreSQL 17 public access closure: FAIL' >&2
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
MANIFEST="$ROOT/db/manifests/fase09_7_free_schema_rls.json"
BASELINE="$ROOT/tests/sql/fase08_minimal_baseline.sql"
ACCESS_FIXTURE="$ROOT/tests/sql/fase09_7_access_fixture.sql"
EXEC_FIXTURE="$ROOT/tests/sql/fase09_exec_sql_fixture.sql"
FUNCTIONAL="$ROOT/tests/sql/fase09_7_functional_test.sql"
CLOSURE="$ROOT/db/migrations/20260727_fase09_7_public_access_closure.sql"

command -v psql >/dev/null
command -v python3 >/dev/null

mapfile -t migrations < <(
  python3 - "$MANIFEST" <<'PY'
import sys
from pathlib import Path

from scripts.maintenance.fase09_7_candidate import load_manifest

for migration in load_manifest(Path(sys.argv[1]), "free"):
    print(migration)
PY
)
[[ ${#migrations[@]} -eq 5 ]]

package_wrapper="$(mktemp /tmp/studiamatch-f97-package.XXXXXX.sql)"
prefix3_wrapper="$(mktemp /tmp/studiamatch-f97-prefix3.XXXXXX.sql)"
prefix4_wrapper="$(mktemp /tmp/studiamatch-f97-prefix4.XXXXXX.sql)"
failure_log="$(mktemp /tmp/studiamatch-f97-failure.XXXXXX.log)"

python3 - "$MANIFEST" "$prefix3_wrapper" "$prefix4_wrapper" <<'PY'
import sys
from pathlib import Path

from scripts.maintenance.fase09_7_candidate import (
    canonical_sql_sha256,
    load_manifest,
)

paths = load_manifest(Path(sys.argv[1]), "free")
for prefix_size, wrapper_path in zip((3, 4), sys.argv[2:]):
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
    'fase097_insert_parent'
)
ORDER BY role.rolname
\gexec
SELECT pg_catalog.format('DROP ROLE %I;', role.rolname)
FROM pg_catalog.pg_roles AS role
WHERE role.rolname IN (
    'anon', 'authenticated', 'service_role', 'fase097_policy_parent',
    'fase097_private_reader', 'fase097_courses_parent',
    'fase097_insert_parent'
)
ORDER BY role.rolname
\gexec
CREATE SCHEMA public AUTHORIZATION pg_database_owner;
GRANT USAGE ON SCHEMA public TO PUBLIC;
SQL
}

setup_database() {
  reset_database
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$BASELINE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$ACCESS_FIXTURE" >/dev/null
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
        procedure.prosecdef, procedure.provolatile, procedure.proconfig::text,
        procedure.proacl::text, procedure.prosrc
    )
    FROM pg_catalog.pg_proc AS procedure
    WHERE procedure.pronamespace = 'public'::regnamespace
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

# Accepted immutable predecessor boundaries converge to the same five entries.
for prefix_size in 3 4; do
  setup_database
  prefix_wrapper="$prefix3_wrapper"
  [[ "$prefix_size" -ne 4 ]] || prefix_wrapper="$prefix4_wrapper"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$prefix_wrapper" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
    "INSERT INTO public.supabase_migrations (version, name, statements, applied_at) VALUES (20260101000000, '20260101_unrelated_history', 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', pg_catalog.clock_timestamp());" \
    >/dev/null
  plan_manifest "$((5 - prefix_size))" "$package_wrapper"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$package_wrapper" >/dev/null
  plan_manifest 0
  unrelated_state="$(psql -X --quiet --tuples-only --no-align \
    --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
    "SELECT statements FROM public.supabase_migrations WHERE name = '20260101_unrelated_history';" | tr -d '[:space:]')"
  [[ "$unrelated_state" == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" ]]
done

# Empty ledger boundary applies atomically, passes role tests, replays, then is zero-pending.
setup_database
plan_manifest 5 "$package_wrapper"
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
    'SET ROLE service_role; SELECT public.verify_fase09_7_public_access_closure() AND public.verify_fase08_hito1_contract();'
} | tail -n 1 | tr -d '[:space:]')"
[[ "$replay_state" == "t" ]]
plan_manifest 0

# Unknown policy drift makes the final semantic verifier roll back schema and ledger.
setup_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  'CREATE POLICY fase097_atomic_fault ON public.leads FOR SELECT TO PUBLIC USING (true);' \
  >/dev/null
plan_manifest 5 "$package_wrapper"
before_rollback="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'Postcondicion fallida: 20260725_fase08_hito1_functional_closure' \
  "$failure_log"
after_rollback="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_rollback" == "$after_rollback" ]]
rollback_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations) = 0 AND pg_catalog.to_regprocedure('public.verify_fase09_7_public_access_closure()') IS NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_policies WHERE schemaname = 'public' AND policyname = 'fase097_atomic_fault');"
} | tr -d '[:space:]')"
[[ "$rollback_state" == "t" ]]

reset_database
result=0
