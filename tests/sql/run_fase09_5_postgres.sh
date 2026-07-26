#!/usr/bin/env bash
set -euo pipefail

result=1
package_wrapper=""
probe_wrapper=""
failure_log=""
prefix3_wrapper=""
prefix4_wrapper=""
prefix5_wrapper=""

finish() {
  local exit_status=$?
  trap - EXIT
  set +e
  [[ -z "$package_wrapper" ]] || rm -f -- "$package_wrapper"
  [[ -z "$probe_wrapper" ]] || rm -f -- "$probe_wrapper"
  [[ -z "$failure_log" ]] || rm -f -- "$failure_log"
  [[ -z "$prefix3_wrapper" ]] || rm -f -- "$prefix3_wrapper"
  [[ -z "$prefix4_wrapper" ]] || rm -f -- "$prefix4_wrapper"
  [[ -z "$prefix5_wrapper" ]] || rm -f -- "$prefix5_wrapper"
  if [[ $exit_status -eq 0 && $result -eq 0 ]]; then
    printf '%s\n' 'F9.5 PostgreSQL 17 RLS reconciliation contract: PASS'
    exit 0
  fi
  printf '%s\n' 'F9.5 PostgreSQL 17 RLS reconciliation contract: FAIL' >&2
  [[ $exit_status -eq 0 ]] && exit 1
  exit "$exit_status"
}
trap finish EXIT
trap 'exit 130' HUP INT TERM

: "${TEST_DATABASE_URL:?TEST_DATABASE_URL must point to an ephemeral PostgreSQL 17 database}"
[[ "$TEST_DATABASE_URL" =~ ^postgresql://postgres:postgres@(127\.0\.0\.1|localhost|studiamatch-f95-postgres):5432/studiamatch_f95$ \
  || "$TEST_DATABASE_URL" =~ ^postgresql://postgres:postgres@/studiamatch_f95\?host=/[A-Za-z0-9._/-]+/postgres-socket$ ]]

for variable_name in $(compgen -e); do
  case "$variable_name" in
    SUPABASE*|NEXT_SUPABASE*|NEXT_PUBLIC_SUPABASE*|CF_*|OPENCODE_*|RESEND_*|GITHUB_TOKEN|GH_TOKEN|DATABASE_URL|POSTGRES_*|PG*)
      exit 1
      ;;
  esac
done

ROOT="${FASE095_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MANIFEST="$ROOT/db/manifests/fase09_5_rls_candidate_v2.json"
BASELINE="$ROOT/tests/sql/fase08_minimal_baseline.sql"
HISTORICAL_FIXTURE="$ROOT/tests/sql/fase09_5_historical_rls_fixture.sql"
OBSERVED_POLICY_FIXTURE="$ROOT/tests/sql/fase09_5_observed_policy_fixture.sql"
EXEC_FIXTURE="$ROOT/tests/sql/fase09_exec_sql_fixture.sql"
FUNCTIONAL="$ROOT/tests/sql/fase09_5_rls_test.sql"
SUCCESSOR="$ROOT/db/migrations/20260726_fase09_5_policy_inventory_reconciliation.sql"

command -v psql >/dev/null
command -v python3 >/dev/null

python3 "$ROOT/scripts/maintenance/db_migrate.py" \
  --env free --manifest "$MANIFEST" --validate-only >/dev/null 2>&1

mapfile -t migrations < <(
  python3 - "$MANIFEST" <<'PY'
import sys
from pathlib import Path
from scripts.maintenance.migration_manifest import load_manifest

for migration in load_manifest(Path(sys.argv[1]), "free"):
    print(migration)
PY
)
[[ ${#migrations[@]} -eq 6 ]]

package_wrapper="$(mktemp /tmp/studiamatch-f95-package.XXXXXX.sql)"
probe_wrapper="$(mktemp /tmp/studiamatch-f95-probe.XXXXXX.sql)"
failure_log="$(mktemp /tmp/studiamatch-f95-failure.XXXXXX.log)"
prefix3_wrapper="$(mktemp /tmp/studiamatch-f95-prefix3.XXXXXX.sql)"
prefix4_wrapper="$(mktemp /tmp/studiamatch-f95-prefix4.XXXXXX.sql)"
prefix5_wrapper="$(mktemp /tmp/studiamatch-f95-prefix5.XXXXXX.sql)"
python3 - "$MANIFEST" "$package_wrapper" "$probe_wrapper" \
  "$prefix3_wrapper" "$prefix4_wrapper" "$prefix5_wrapper" <<'PY'
import sys
from pathlib import Path
from scripts.maintenance.migration_manifest import canonical_sql_sha256, load_manifest

paths = load_manifest(Path(sys.argv[1]), "free")
probe = ["\\set ON_ERROR_STOP on", "BEGIN;"]
probe.extend(f"\\i {path}" for path in paths[:4])
probe.extend([
    f"\\i {Path(sys.argv[1]).resolve().parents[2] / 'tests/sql/fase09_5_historical_baseline_test.sql'}",
    f"\\i {Path(sys.argv[1]).resolve().parents[2] / 'tests/sql/fase09_5_v2_baseline_test.sql'}",
    "ROLLBACK;",
])
Path(sys.argv[3]).write_text(
    "\n".join(probe) + "\n", encoding="utf-8", newline="\n"
)

for prefix_size, wrapper_path in zip((3, 4, 5), sys.argv[4:]):
    expected_prefix = {
        path.stem: f"sha256:{canonical_sql_sha256(path)}"
        for path in paths[:prefix_size]
    }
    lines = ["\\set ON_ERROR_STOP on"]
    for index, path in enumerate(paths[:prefix_size], start=1):
        lines.append(f"\\i {path}")
        marker = expected_prefix[path.stem]
        lines.append(
            "INSERT INTO public.supabase_migrations "
            "(version, name, statements, applied_at) VALUES "
            f"({20260726090000 + index}, '{path.stem}', '{marker}', "
            "pg_catalog.clock_timestamp());"
        )
    Path(wrapper_path).write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
PY

plan_manifest() {
  local expected_pending="$1"
  local output_wrapper="${2:-}"
  python3 - "$TEST_DATABASE_URL" "$MANIFEST" "$expected_pending" \
    "$output_wrapper" <<'PY'
import re
import subprocess
import sys
from pathlib import Path

from scripts.maintenance.db_migrate import (
    build_manifest_package_sql,
    validate_manifest_ledger_state,
)
from scripts.maintenance.migration_manifest import load_manifest

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
        result = subprocess.run(
            [
                "psql", "-X", "--quiet", "--tuples-only", "--no-align",
                dsn, "--command", f"SET ROLE service_role; SELECT public.{name}();",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().splitlines()
        return bool(result and result[-1] == "t")


pending = validate_manifest_ledger_state(Adapter(), paths, applied)
if len(pending) != int(expected_pending):
    raise RuntimeError(
        f"real planner returned {len(pending)} pending; expected {expected_pending}"
    )
if output_wrapper:
    if not pending:
        raise RuntimeError("cannot write an execution wrapper for a zero-pending plan")
    expected_prefix = {
        path.stem: applied[path.stem]
        for path in paths
        if path.stem in applied
    }
    payload = build_manifest_package_sql(
        pending,
        expected_prefix=expected_prefix,
        version=20260726090500 + len(applied),
    )
    delimiter = "$fase095_planned_package$"
    if delimiter in payload:
        raise RuntimeError("reserved planner delimiter collision")
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

reset_database() {
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" >/dev/null <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
SELECT pg_catalog.format('DROP OWNED BY %I;', role.rolname)
FROM pg_catalog.pg_roles AS role
WHERE role.rolname IN (
    'anon', 'authenticated', 'authenticator', 'service_role', 'canary_runner'
)
ORDER BY role.rolname
\gexec
SELECT pg_catalog.format('DROP ROLE %I;', role.rolname)
FROM pg_catalog.pg_roles AS role
WHERE role.rolname IN (
    'anon', 'authenticated', 'authenticator', 'service_role', 'canary_runner'
)
ORDER BY role.rolname
\gexec
CREATE SCHEMA public AUTHORIZATION pg_database_owner;
GRANT USAGE ON SCHEMA public TO PUBLIC;
SQL
}

schema_fingerprint() {
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" <<'SQL'
WITH public_objects AS (
    SELECT relation.oid
    FROM pg_catalog.pg_class AS relation
    WHERE relation.relnamespace = 'public'::regnamespace
    UNION
    SELECT procedure.oid
    FROM pg_catalog.pg_proc AS procedure
    WHERE procedure.pronamespace = 'public'::regnamespace
), catalog_rows AS (
    SELECT 'class' AS kind, pg_catalog.to_jsonb(record)::text AS value
    FROM pg_catalog.pg_class AS record
    WHERE record.relnamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'namespace', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_namespace AS record
    WHERE record.nspname = 'public'
    UNION ALL
    SELECT 'proc', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_proc AS record
    WHERE record.pronamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'attribute', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_attribute AS record
    WHERE record.attrelid IN (SELECT oid FROM public_objects)
    UNION ALL
    SELECT 'constraint', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_constraint AS record
    WHERE record.connamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'policy', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_policy AS record
    WHERE record.polrelid IN (SELECT oid FROM public_objects)
)
SELECT pg_catalog.md5(
    COALESCE(
        pg_catalog.string_agg(kind || ':' || value, E'\n' ORDER BY kind, value),
        ''
    )
)
FROM catalog_rows;
SQL
}

policy_fingerprint() {
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" <<'SQL'
SELECT pg_catalog.md5(
    pg_catalog.string_agg(
        pg_catalog.concat_ws('|', schemaname, tablename, policyname,
            permissive, roles::text, cmd, qual, with_check),
        E'\n' ORDER BY schemaname, tablename, policyname
    )
)
FROM pg_catalog.pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
      'institutions', 'institution_site_profiles', 'courses', 'leads',
      'ratings', 'reviews'
  );
SQL
}

# Execute every reviewed aggregate query against the observed synthetic state.
reset_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$BASELINE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$HISTORICAL_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$OBSERVED_POLICY_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$EXEC_FIXTURE" >/dev/null
for migration in "${migrations[@]:0:4}"; do
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$migration" >/dev/null
done
python3 - "$TEST_DATABASE_URL" <<'PY'
import subprocess
import sys

from scripts.maintenance.fase09_5_preflight import (
    CHECK_SQL,
    EXPECTED_COUNTS,
    EXPECTED_DIGESTS,
    H00_COUNTS,
)

dsn = sys.argv[1]


def execute(sql):
    return subprocess.run(
        [
            "psql", "-X", "--quiet", "--tuples-only", "--no-align",
            "--field-separator", "|", dsn, "--command", sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().splitlines()


for name in (
    "columns", "constraints", "indexes", "rls", "policies", "roles", "acl",
    "rpc",
):
    rows = execute(CHECK_SQL[name])
    expected = f"{EXPECTED_COUNTS[name]}|{EXPECTED_DIGESTS[name]}"
    if rows != [expected]:
        raise RuntimeError(f"aggregate preflight query mismatch: {name}")

execute(
    "CREATE ROLE fase095_preflight_auth_child NOLOGIN; "
    "GRANT authenticator TO fase095_preflight_auth_child"
)
roles_expected = (
    f"{EXPECTED_COUNTS['roles']}|{EXPECTED_DIGESTS['roles']}"
)
if execute(CHECK_SQL["roles"]) == [roles_expected]:
    raise RuntimeError("roles inventory missed reverse authenticator membership")
execute(
    "REVOKE authenticator FROM fase095_preflight_auth_child; "
    "DROP ROLE fase095_preflight_auth_child"
)
if execute(CHECK_SQL["roles"]) != [roles_expected]:
    raise RuntimeError("roles inventory did not recover after mutation")

for name in ("data_conflicts", "backup_gate", "writers_gate"):
    if execute(CHECK_SQL[name]) != [str(EXPECTED_COUNTS[name])]:
        raise RuntimeError(f"scalar preflight query mismatch: {name}")

h00_sql = (
    "BEGIN; CREATE TABLE public.email_log (id uuid PRIMARY KEY); "
    "INSERT INTO public.leads (id, first_name, email, whatsapp, created_at) VALUES "
    "('90000000-0000-0000-0000-000000000001','A','a@example.invalid','1',"
    "'2026-07-18T00:00:00Z'),"
    "('90000000-0000-0000-0000-000000000002','B','b@example.invalid','2',"
    "'2026-07-18T01:00:00Z'),"
    "('90000000-0000-0000-0000-000000000003','C','c@example.invalid','3',"
    "'2026-07-18T02:00:00Z'); "
    f"{CHECK_SQL['h00']}; ROLLBACK;"
)
expected_h00 = "|".join(str(value) for value in H00_COUNTS.values())
if expected_h00 not in execute(h00_sql):
    raise RuntimeError("snapshot-consistent H-00 query mismatch")
PY

for prefix_size in 3 4 5; do
  prefix_wrapper="$prefix3_wrapper"
  [[ "$prefix_size" -ne 4 ]] || prefix_wrapper="$prefix4_wrapper"
  [[ "$prefix_size" -ne 5 ]] || prefix_wrapper="$prefix5_wrapper"
  reset_database
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$BASELINE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$HISTORICAL_FIXTURE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$OBSERVED_POLICY_FIXTURE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$EXEC_FIXTURE" >/dev/null
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$prefix_wrapper" >/dev/null
  plan_manifest "$((6 - prefix_size))" "$package_wrapper"
  psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
    --file "$package_wrapper" >/dev/null
  plan_manifest 0
  prefix_state="$({
    psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
      "$TEST_DATABASE_URL" --command \
      "SET ROLE service_role; SELECT (SELECT pg_catalog.count(*) FROM public.supabase_migrations) = 6 AND public.verify_fase08_hito1_contract() AND public.verify_fase09_5_rls_canary_reconciliation() AND public.verify_fase09_5_policy_inventory_reconciliation();"
  } | tail -n 1 | tr -d '[:space:]')"
  [[ "$prefix_state" == "t" ]]
done

reset_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$BASELINE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$HISTORICAL_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$OBSERVED_POLICY_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$EXEC_FIXTURE" >/dev/null

psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$probe_wrapper" >/dev/null

# The real planner starts from an empty ledger and converges atomically.
plan_manifest 6 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$FUNCTIONAL" >/dev/null

before_policy_fingerprint="$(policy_fingerprint | tr -d '[:space:]')"
[[ "$before_policy_fingerprint" =~ ^[0-9a-f]{32}$ ]]
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$SUCCESSOR" >/dev/null
after_policy_fingerprint="$(policy_fingerprint | tr -d '[:space:]')"
[[ "$before_policy_fingerprint" == "$after_policy_fingerprint" ]]
replay_verifiers="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    'SET ROLE service_role; SELECT public.verify_fase08_hito1_contract() AND public.verify_fase09_5_rls_canary_reconciliation() AND public.verify_fase09_5_policy_inventory_reconciliation();'
} | tail -n 1 | tr -d '[:space:]')"
[[ "$replay_verifiers" == "t" ]]

plan_manifest 0

# A final-verifier failure rolls back migrations and all six ledger markers.
reset_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$BASELINE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$HISTORICAL_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$OBSERVED_POLICY_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$EXEC_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  'CREATE POLICY fase09_5_atomic_fault ON public.leads FOR SELECT TO PUBLIC USING (true);' \
  >/dev/null
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
    "SELECT (SELECT count(*) FROM public.supabase_migrations) = 0 AND pg_catalog.to_regprocedure('public.verify_fase09_5_policy_inventory_reconciliation()') IS NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_policies WHERE schemaname = 'public' AND policyname = 'fase09_5_atomic_fault');"
} | tr -d '[:space:]')"
[[ "$rollback_state" == "t" ]]

# The same final-verifier failure rolls back the v2-only 5/6 suffix.
reset_database
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$BASELINE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$HISTORICAL_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$OBSERVED_POLICY_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$EXEC_FIXTURE" >/dev/null
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$prefix5_wrapper" >/dev/null
plan_manifest 1 "$package_wrapper"
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command \
  'CREATE POLICY fase09_5_suffix_fault ON public.leads FOR SELECT TO PUBLIC USING (true);' \
  >/dev/null
before_suffix_rollback="$(schema_fingerprint | tr -d '[:space:]')"
if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq 'Postcondicion fallida: 20260726_fase09_5_policy_inventory_reconciliation' \
  "$failure_log"
after_suffix_rollback="$(schema_fingerprint | tr -d '[:space:]')"
[[ "$before_suffix_rollback" == "$after_suffix_rollback" ]]
suffix_rollback_state="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" --command \
    "SELECT (SELECT count(*) FROM public.supabase_migrations) = 5 AND pg_catalog.to_regprocedure('public.verify_fase09_5_policy_inventory_reconciliation()') IS NULL AND EXISTS (SELECT 1 FROM pg_catalog.pg_policies WHERE schemaname = 'public' AND policyname = 'fase09_5_suffix_fault');"
} | tr -d '[:space:]')"
[[ "$suffix_rollback_state" == "t" ]]

reset_database
result=0
