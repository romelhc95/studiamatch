#!/usr/bin/env bash
set -euo pipefail

: "${TEST_DATABASE_URL:?TEST_DATABASE_URL must point to an ephemeral PostgreSQL 17 database}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$ROOT/db/manifests/fase08_candidate.json"

command -v psql >/dev/null
command -v python3 >/dev/null

cd "$ROOT"
python3 scripts/maintenance/db_migrate.py \
  --env free \
  --manifest "$MANIFEST" \
  --validate-only >/dev/null

mapfile -t migrations < <(
  python3 - <<'PY'
from pathlib import Path

from scripts.maintenance.migration_manifest import load_manifest

root = Path.cwd()
for migration in load_manifest(
    root / "db/manifests/fase08_candidate.json", "free"
):
    print(migration)
PY
)

psql -X --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$ROOT/tests/sql/fase08_minimal_baseline.sql"

for migration in "${migrations[@]}"; do
  psql -X --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" --file "$migration"
done

psql -X --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$ROOT/tests/sql/fase08_functional_test.sql"

# The new forward-only overlay itself must remain safe to replay.
psql -X --set=ON_ERROR_STOP=1 "$TEST_DATABASE_URL" \
  --file "$ROOT/db/migrations/20260725_fase08_hito1_functional_closure.sql"

verifier="$({
  psql -X --quiet --tuples-only --no-align --set=ON_ERROR_STOP=1 \
    "$TEST_DATABASE_URL" \
    --command "SELECT public.verify_fase08_hito1_contract();"
} | tr -d '[:space:]')"

if [[ "$verifier" != "t" ]]; then
  echo "FASE-08 verifier did not return true after overlay replay" >&2
  exit 1
fi

echo "FASE-08 PostgreSQL 17 functional contract: PASS"
