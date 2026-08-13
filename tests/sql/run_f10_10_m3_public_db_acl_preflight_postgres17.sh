#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly IMAGE='postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193'
readonly PYTHON_IMAGE='python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93'
readonly CONTAINER="f1010-acl-preflight-${RANDOM}-${RANDOM}"
readonly COLLECTOR_CONTAINER="f1010-acl-collector-${RANDOM}-${RANDOM}"
readonly PYTHON_CONTAINER="f1010-acl-generator-${RANDOM}-${RANDOM}"
STAGE='initialize'
WORK=''
CONTAINER_CREATED=0
COLLECTOR_CONTAINER_CREATED=0
PYTHON_CONTAINER_CREATED=0

stop_with_context() {
  local status="$1"
  local line="$2"
  printf 'F10.10 ACL preflight harness STOP: stage=%s line=%s status=%s\n' \
    "$STAGE" "$line" "$status" >&2
  exit "$status"
}

cleanup() {
  local status="$?"
  local cleanup_status=0
  trap - ERR EXIT
  if [ "$CONTAINER_CREATED" -eq 1 ]; then
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || cleanup_status=1
  fi
  if [ "$COLLECTOR_CONTAINER_CREATED" -eq 1 ]; then
    docker rm -f "$COLLECTOR_CONTAINER" >/dev/null 2>&1 || cleanup_status=1
  fi
  if [ "$PYTHON_CONTAINER_CREATED" -eq 1 ]; then
    docker rm -f "$PYTHON_CONTAINER" >/dev/null 2>&1 || cleanup_status=1
  fi
  if [ -n "$WORK" ] && [ -d "$WORK" ]; then
    rm -rf -- "$WORK" || cleanup_status=1
  fi
  if [ "$cleanup_status" -ne 0 ]; then
    printf 'F10.10 ACL preflight harness STOP: stage=cleanup status=1\n' >&2
    if [ "$status" -eq 0 ]; then
      status=1
    fi
  fi
  exit "$status"
}
trap 'stop_with_context "$?" "$LINENO"' ERR
trap cleanup EXIT

WORK="$(mktemp -d "${TMPDIR:-/tmp}/f10_10_acl_preflight.XXXXXX")"
readonly WORK
STAGE='work-created'
docker image inspect "$IMAGE" >/dev/null || stop_with_context "$?" "$LINENO"
STAGE='image-present'
. tests/sql/f10_10_m3_postgres_final_readiness.sh
docker run -d --rm --pull never --network none --name "$CONTAINER" \
  -e POSTGRES_PASSWORD=postgres "$IMAGE" >/dev/null
CONTAINER_CREATED=1
STAGE='postgres-final-readiness'
f1010_wait_for_final_postgres "$CONTAINER"
STAGE='postgres-final-ready'

docker exec -i "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  < tests/sql/f10_10_m3_public_db_acl_preflight_fixture.sql
echo 'F10.10 ACL stage: fixture-ready'

cat > "$WORK/collect.py" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "preflight", "/usr/local/lib/f10_10_m3_public_db_acl_preflight.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
code, output = module.run(["--mode", "sql"])
if code != 0:
    raise SystemExit(code)
print(output["sql"], end="")
PY
docker create --name "$COLLECTOR_CONTAINER" --pull never --network none "$PYTHON_IMAGE" \
  python3 /tmp/collect.py >/dev/null
COLLECTOR_CONTAINER_CREATED=1
docker cp scripts/maintenance/f10_10_m3_public_db_acl_preflight.py \
  "$COLLECTOR_CONTAINER:/usr/local/lib/f10_10_m3_public_db_acl_preflight.py"
docker cp "$WORK/collect.py" "$COLLECTOR_CONTAINER:/tmp/collect.py"
docker start --attach "$COLLECTOR_CONTAINER" > "$WORK/collector.sql"
docker rm "$COLLECTOR_CONTAINER" >/dev/null
COLLECTOR_CONTAINER_CREATED=0
echo 'F10.10 ACL stage: collector-ready'
docker cp "$WORK/collector.sql" "$CONTAINER:/tmp/collector.sql"
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
  -f /tmp/collector.sql > "$WORK/result.json"
echo 'F10.10 ACL stage: result-ready'

cat > "$WORK/generate.py" <<'PY'
import importlib.util
import json
import pathlib
import sys

spec = importlib.util.spec_from_file_location(
    "preflight", "/usr/local/lib/f10_10_m3_public_db_acl_preflight.py"
)
preflight = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = preflight
spec.loader.exec_module(preflight)

raw = pathlib.Path("/tmp/result.json").read_text(encoding="utf-8").splitlines()
result = json.loads(next(line for line in raw if line.startswith("{")))
expected_target_binding_digest = "sha256:09467d8124e639534aae8bc2d28e6ad3150144ec860e15ef05fdf87020976a56"
target_attestation = preflight.build_target_attestation("sha256:" + "1" * 64, "sha256:" + "2" * 64)
result["target_binding"] = target_attestation
entries = []
for dependency in result["login_public_dependencies"]:
    database = next(db for db in result["databases"] if db["oid"] == dependency["database_oid"])
    source = next(
        acl for acl in database["effective_acl"]
        if acl["grantee_oid"] != 0 and acl["privilege"] == dependency["privilege"]
        and acl["grantee_oid"] == dependency["role_oid"]
    )
    entries.append({
        **dependency, "service": "postgrest", "source_grantee_oid": source["grantee_oid"],
        "source_grantor_oid": source["grantor_oid"],
        "source_is_grantable": source["is_grantable"], "membership": "USAGE",
    })
result["managed_service_evaluation"] = {
    "schema": "f10.10-m3-managed-dependency-attestation-v1", "entries": entries,
}
validated = preflight.validate_private_result(result, expected_target_binding_digest)
pathlib.Path("/tmp/candidate.sql").write_text(preflight.generate_candidate_sql(validated), encoding="utf-8", newline="\n")
pathlib.Path("/tmp/projected.sql").write_text(preflight.project_apply_migration_candidate(validated), encoding="utf-8", newline="\n")
PY
docker create --name "$PYTHON_CONTAINER" --pull never --network none \
  "$PYTHON_IMAGE" python3 /tmp/generate.py >/dev/null
PYTHON_CONTAINER_CREATED=1
docker cp scripts/maintenance/f10_10_m3_public_db_acl_preflight.py \
  "$PYTHON_CONTAINER:/usr/local/lib/f10_10_m3_public_db_acl_preflight.py"
docker cp "$WORK/generate.py" "$PYTHON_CONTAINER:/tmp/generate.py"
docker cp "$WORK/result.json" "$PYTHON_CONTAINER:/tmp/result.json"
docker start --attach "$PYTHON_CONTAINER" >/dev/null
docker cp "$PYTHON_CONTAINER:/tmp/candidate.sql" "$WORK/candidate.sql"
docker cp "$PYTHON_CONTAINER:/tmp/projected.sql" "$WORK/projected.sql"
docker rm "$PYTHON_CONTAINER" >/dev/null
PYTHON_CONTAINER_CREATED=0
echo 'F10.10 ACL stage: candidate-ready'

docker cp "$WORK/candidate.sql" "$CONTAINER:/tmp/candidate.sql"
docker cp "$WORK/projected.sql" "$CONTAINER:/tmp/projected.sql"
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
  -c "SELECT pg_catalog.md5(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(d.oid,d.datacl::text) ORDER BY d.oid)::text) FROM pg_catalog.pg_database AS d WHERE NOT d.datallowconn" \
  > "$WORK/nonconnectable-before.txt"
awk '1; !injected && /^REVOKE .*"other_nonconformant"/ { print "SELECT 1 / 0;"; injected=1 }' \
  "$WORK/projected.sql" > "$WORK/projected-failure.sql"
grep -qx 'SELECT 1 / 0;' "$WORK/projected-failure.sql"
docker cp "$WORK/projected-failure.sql" "$CONTAINER:/tmp/projected-failure.sql"
if docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -f /tmp/projected-failure.sql -c 'COMMIT' >/dev/null 2>&1; then
  echo 'injected failure unexpectedly committed' >&2
  exit 1
fi
docker exec -i "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 <<'SQL' \
  | grep -qx '3|3'
WITH acl AS (
  SELECT d.datname, x.grantee, x.privilege_type
  FROM pg_catalog.pg_database AS d
  CROSS JOIN LATERAL pg_catalog.aclexplode(
    COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x
)
SELECT
  count(*) FILTER (WHERE datname='postgres' AND grantee=0) || '|' ||
  count(*) FILTER (WHERE datname='other_nonconformant' AND grantee=0)
FROM acl;
SQL
echo 'F10.10 ACL stage: rollback-ready'

# A stale executor must fail before any revoke.
if docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -c 'SET ROLE alternate_super' -f /tmp/projected.sql -c 'COMMIT' >/dev/null 2>&1; then
  echo 'stale executor unexpectedly applied candidate' >&2
  exit 1
fi

# A stale ACL must fail before mutation and preserve the drift.
docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'REVOKE CREATE ON DATABASE other_nonconformant FROM explicit_reader'
if docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -f /tmp/projected.sql -c 'COMMIT' >/dev/null 2>&1; then
  echo 'stale ACL unexpectedly applied candidate' >&2
  exit 1
fi
docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'GRANT CREATE ON DATABASE other_nonconformant TO explicit_reader'

# Simulate apply_migration: projected body and ledger insert share one transaction.
docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'CREATE TABLE public.local_migration_ledger(name text PRIMARY KEY)'
docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c "INSERT INTO public.local_migration_ledger VALUES ('acl-ledger-failure')"
if docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -f /tmp/projected.sql \
  -c "INSERT INTO public.local_migration_ledger VALUES ('acl-ledger-failure')" -c 'COMMIT' >/dev/null 2>&1; then
  echo 'ledger failure unexpectedly committed' >&2
  exit 1
fi
docker exec -i "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 <<'SQL' \
  | grep -qx '3|3'
WITH acl AS (
  SELECT d.datname, x.grantee
  FROM pg_catalog.pg_database AS d
  CROSS JOIN LATERAL pg_catalog.aclexplode(
    COALESCE(d.datacl, pg_catalog.acldefault('d', d.datdba))) AS x
)
SELECT
  count(*) FILTER (WHERE datname='postgres' AND grantee=0) || '|' ||
  count(*) FILTER (WHERE datname='other_nonconformant' AND grantee=0)
FROM acl;
SQL
echo 'F10.10 ACL stage: ledger-rollback-ready'
docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -f /tmp/projected.sql \
  -c "INSERT INTO public.local_migration_ledger VALUES ('acl-success')" -c 'COMMIT' >/dev/null
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
  -c "SELECT count(*) FROM public.local_migration_ledger WHERE name='acl-success'" | grep -qx '1'
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
  -c "SELECT pg_catalog.md5(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(d.oid,d.datacl::text) ORDER BY d.oid)::text) FROM pg_catalog.pg_database AS d WHERE NOT d.datallowconn" \
  | cmp -s - "$WORK/nonconnectable-before.txt"

docker exec -i "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
  < tests/sql/f10_10_m3_public_db_acl_preflight_assert.sql | grep -qx '1|0|0|0|0|1|6'
echo 'F10.10 ACL stage: apply-ready'

if docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -f /tmp/projected.sql -c 'COMMIT' >/dev/null 2>&1; then
  echo 'stale candidate unexpectedly replayed' >&2
  exit 1
fi

echo 'F10.10 PUBLIC database ACL PostgreSQL 17 contract: PASS'
