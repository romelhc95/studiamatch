#!/usr/bin/env bash
set -euo pipefail

result=1
package_wrapper=""
failure_log=""
dsn_valid=0

schema_fingerprint() {
  psql -X --quiet --set=ON_ERROR_STOP=1 --tuples-only --no-align \
    "$TEST_DATABASE_URL" <<'SQL'
WITH public_objects AS (
    SELECT relation.oid
    FROM pg_catalog.pg_class AS relation
    WHERE relation.relnamespace = 'public'::regnamespace
    UNION
    SELECT procedure.oid
    FROM pg_catalog.pg_proc AS procedure
    WHERE procedure.pronamespace = 'public'::regnamespace
    UNION
    SELECT type_record.oid
    FROM pg_catalog.pg_type AS type_record
    WHERE type_record.typnamespace = 'public'::regnamespace
), catalog_rows AS (
    SELECT 'class' AS kind, pg_catalog.to_jsonb(record)::text AS value
    FROM pg_catalog.pg_class AS record
    WHERE record.relnamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'proc', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_proc AS record
    WHERE record.pronamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'type', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_type AS record
    WHERE record.typnamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'attribute', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_attribute AS record
    WHERE record.attrelid IN (SELECT oid FROM public_objects)
    UNION ALL
    SELECT 'attrdef', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_attrdef AS record
    WHERE record.adrelid IN (SELECT oid FROM public_objects)
    UNION ALL
    SELECT 'constraint', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_constraint AS record
    WHERE record.connamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'index', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_index AS record
    WHERE record.indrelid IN (SELECT oid FROM public_objects)
    UNION ALL
    SELECT 'policy', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_policy AS record
    WHERE record.polrelid IN (SELECT oid FROM public_objects)
    UNION ALL
    SELECT 'trigger', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_trigger AS record
    WHERE record.tgrelid IN (SELECT oid FROM public_objects)
    UNION ALL
    SELECT 'depend', pg_catalog.to_jsonb(record)::text
    FROM pg_catalog.pg_depend AS record
    WHERE record.objid IN (SELECT oid FROM public_objects)
       OR record.refobjid IN (SELECT oid FROM public_objects)
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

finish() {
  local exit_status=$?
  local cleanup_failed=0
  trap - EXIT
  set +e
  if [[ $dsn_valid -eq 1 ]] && command -v psql >/dev/null 2>&1; then
    psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
      >/dev/null 2>&1 <<'SQL'
DO $cleanup$
BEGIN
    IF pg_catalog.to_regclass('public.leads') IS NOT NULL THEN
        EXECUTE 'DROP POLICY IF EXISTS fase09_final_verifier_fault ON public.leads';
    END IF;
END;
$cleanup$;
DROP FUNCTION IF EXISTS public.exec_sql(text);
DROP TABLE IF EXISTS public.supabase_migrations;
SQL
    [[ $? -eq 0 ]] || cleanup_failed=1
  fi
  for temporary_file in "$package_wrapper" "$failure_log"; do
    if [[ -n "$temporary_file" ]]; then
      rm -f -- "$temporary_file" || cleanup_failed=1
    fi
  done
  if [[ $exit_status -eq 0 && $result -eq 0 && $cleanup_failed -eq 0 ]]; then
    printf '%s\n' 'FASE-09 PostgreSQL 17 package contract: PASS'
    exit 0
  else
    printf '%s\n' 'FASE-09 PostgreSQL 17 package contract: FAIL' >&2
    [[ $exit_status -ne 0 ]] && exit "$exit_status"
    exit 1
  fi
}
trap finish EXIT
trap 'exit 130' HUP INT TERM

[[ -n "${TEST_DATABASE_URL:-}" ]]
[[ "$TEST_DATABASE_URL" =~ ^postgresql://postgres:postgres@(127\.0\.0\.1|localhost|studiamatch-f9-postgres):5432/studiamatch_f9$ ]]

for variable_name in $(compgen -e); do
  case "$variable_name" in
    SUPABASE*|NEXT_SUPABASE*|NEXT_PUBLIC_SUPABASE*|CF_*|OPENCODE_*|RESEND_*|GITHUB_TOKEN|GH_TOKEN|DATABASE_URL|POSTGRES_*|PG*)
      exit 1
      ;;
  esac
done
dsn_valid=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$ROOT/db/manifests/fase08_candidate.json"
BASELINE="$ROOT/tests/sql/fase08_minimal_baseline.sql"
FIXTURE="$ROOT/tests/sql/fase09_exec_sql_fixture.sql"
FUNCTIONAL="$ROOT/tests/sql/fase09_functional_test.sql"

command -v psql >/dev/null
command -v python3 >/dev/null

python3 "$ROOT/scripts/maintenance/db_migrate.py" \
  --env free --manifest "$MANIFEST" --validate-only >/dev/null 2>&1

package_wrapper="$(mktemp /tmp/studiamatch-f9-package.XXXXXX.sql)"
failure_log="$(mktemp /tmp/studiamatch-f9-failure.XXXXXX.log)"
python3 - "$MANIFEST" "$package_wrapper" <<'PY' >/dev/null 2>&1
import sys
from pathlib import Path

from scripts.maintenance.db_migrate import build_manifest_package_sql
from scripts.maintenance.migration_manifest import load_manifest

manifest = Path(sys.argv[1])
output = Path(sys.argv[2])
payload = build_manifest_package_sql(
    load_manifest(manifest, "free"), version=20260725090000
)
delimiter = "$fase09_package$"
if delimiter in payload:
    raise RuntimeError("reserved package delimiter collision")
wrapper = (
    "\\set ON_ERROR_STOP on\n"
    "SET ROLE service_role;\n"
    f"SELECT public.exec_sql({delimiter}{payload}{delimiter});\n"
    "RESET ROLE;\n"
)
output.write_bytes(wrapper.encode("utf-8"))
PY

psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$BASELINE" >/dev/null 2>&1
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$FIXTURE" >/dev/null 2>&1
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>&1
psql -X --quiet --set=ON_ERROR_STOP=1 --set=expect_applied=true \
  "$TEST_DATABASE_URL" --file "$FUNCTIONAL" >/dev/null 2>&1

python3 - "$TEST_DATABASE_URL" "$MANIFEST" <<'PY' >/dev/null 2>&1
import re
import subprocess
import sys
from pathlib import Path

from scripts.maintenance.db_migrate import validate_manifest_ledger_state
from scripts.maintenance.migration_manifest import load_manifest

dsn = sys.argv[1]
paths = load_manifest(Path(sys.argv[2]), "free")
ledger_output = subprocess.run(
    [
        "psql", "-X", "--quiet", "--tuples-only", "--no-align",
        "--field-separator", "\t", dsn,
        "--command", "SELECT name, statements FROM public.supabase_migrations ORDER BY name;",
    ],
    check=True,
    capture_output=True,
    text=True,
).stdout
applied = {}
for line in ledger_output.splitlines():
    name, marker = line.split("\t", 1)
    if name in applied:
        raise RuntimeError("duplicate migration in local ledger")
    applied[name] = marker

class LocalVerifierAdapter:
    @staticmethod
    def rpc_raise(name, _params):
        if re.fullmatch(r"verify_[a-z0-9_]+", name) is None:
            raise RuntimeError("invalid verifier name")
        output = subprocess.run(
            [
                "psql", "-X", "--quiet", "--tuples-only", "--no-align",
                dsn,
                "--command", f"SET ROLE service_role; SELECT public.{name}();",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().splitlines()
        return bool(output and output[-1] == "t")

pending = validate_manifest_ledger_state(LocalVerifierAdapter(), paths, applied)
if pending:
    raise RuntimeError("second plan contains pending migrations")
PY

psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command '
  DROP SCHEMA public CASCADE;
  DROP OWNED BY anon;
  DROP OWNED BY authenticated;
  DROP OWNED BY service_role;
  DROP ROLE anon;
  DROP ROLE authenticated;
  DROP ROLE service_role;
  CREATE SCHEMA public AUTHORIZATION pg_database_owner;
  GRANT USAGE ON SCHEMA public TO PUBLIC;
' >/dev/null 2>&1

psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$BASELINE" >/dev/null 2>&1
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$FIXTURE" >/dev/null 2>&1
psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --command '
  CREATE POLICY fase09_final_verifier_fault
  ON public.leads FOR SELECT TO anon USING (true);
' >/dev/null 2>&1

before_fingerprint="$(schema_fingerprint)"
[[ "$before_fingerprint" =~ ^[0-9a-f]{32}$ ]]

if psql -X --quiet --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$package_wrapper" >/dev/null 2>"$failure_log"; then
  exit 1
fi
grep -Fq \
  'Postcondicion fallida: 20260725_fase08_hito1_functional_closure' \
  "$failure_log"
after_fingerprint="$(schema_fingerprint)"
[[ "$after_fingerprint" =~ ^[0-9a-f]{32}$ ]]
[[ "$before_fingerprint" == "$after_fingerprint" ]]
psql -X --quiet --set=ON_ERROR_STOP=1 --set=expect_applied=false \
  "$TEST_DATABASE_URL" --file "$FUNCTIONAL" >/dev/null 2>&1

result=0
