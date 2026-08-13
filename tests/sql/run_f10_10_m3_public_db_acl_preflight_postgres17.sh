#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly IMAGE='postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193'
readonly PYTHON_IMAGE='python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93'
readonly CONTAINER="f1010-acl-preflight-${RANDOM}-${RANDOM}"
WORK="$(mktemp -d /tmp/f10_10_acl_preflight.XXXXXX)"
readonly WORK

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

docker image inspect "$IMAGE" >/dev/null || {
  echo 'pinned PostgreSQL 17 image unavailable locally' >&2
  exit 1
}
docker run -d --rm --pull never --network none --name "$CONTAINER" \
  -e POSTGRES_PASSWORD=postgres "$IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER" pg_isready -U postgres -d postgres >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec "$CONTAINER" pg_isready -U postgres -d postgres >/dev/null

docker exec -i "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  < tests/sql/f10_10_m3_public_db_acl_preflight_fixture.sql

docker run --rm --pull never --network none -v "$PWD:/app" -w /app "$PYTHON_IMAGE" \
  python3 -c 'import json,subprocess; result=subprocess.run(["python3","scripts/maintenance/f10_10_m3_public_db_acl_preflight.py","--mode","sql"],check=True,capture_output=True,text=True); print(json.loads(result.stdout)["sql"],end="")' \
  > "$WORK/collector.sql"
docker cp "$WORK/collector.sql" "$CONTAINER:/tmp/collector.sql"
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
  -f /tmp/collector.sql > "$WORK/result.json"

docker run --rm --pull never --network none -v "$PWD:/app" -v "$WORK:/work" -w /app "$PYTHON_IMAGE" \
  python3 - /work/result.json /work/candidate.sql /work/projected.sql <<'PY'
import json
import pathlib
import sys

from scripts.maintenance.f10_10_m3_public_db_acl_preflight import (
    build_target_attestation,
    generate_candidate_sql,
    project_apply_migration_candidate,
    validate_private_result,
)

raw = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
result = json.loads(next(line for line in raw if line.startswith("{")))
expected_target_binding_digest = "sha256:09467d8124e639534aae8bc2d28e6ad3150144ec860e15ef05fdf87020976a56"
target_attestation = build_target_attestation("sha256:" + "1" * 64, "sha256:" + "2" * 64)
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
validated = validate_private_result(result, expected_target_binding_digest)
pathlib.Path(sys.argv[2]).write_text(generate_candidate_sql(validated), encoding="utf-8", newline="\n")
pathlib.Path(sys.argv[3]).write_text(project_apply_migration_candidate(validated), encoding="utf-8", newline="\n")
PY

docker cp "$WORK/candidate.sql" "$CONTAINER:/tmp/candidate.sql"
docker cp "$WORK/projected.sql" "$CONTAINER:/tmp/projected.sql"
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 \
  -c "SELECT pg_catalog.md5(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(d.oid,d.datacl::text) ORDER BY d.oid)::text) FROM pg_catalog.pg_database AS d WHERE NOT d.datallowconn" \
  > "$WORK/nonconnectable-before.txt"
awk '1; !injected && /^REVOKE / { print "SELECT 1 / 0;"; injected=1 }' \
  "$WORK/projected.sql" > "$WORK/projected-failure.sql"
docker cp "$WORK/projected-failure.sql" "$CONTAINER:/tmp/projected-failure.sql"
if docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -f /tmp/projected-failure.sql -c 'COMMIT' >/dev/null 2>&1; then
  echo 'injected failure unexpectedly committed' >&2
  exit 1
fi
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 <<'SQL' \
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
docker exec "$CONTAINER" psql -X -U postgres -d postgres -At -v ON_ERROR_STOP=1 <<'SQL' \
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

if docker exec "$CONTAINER" psql -X -U postgres -d postgres -v ON_ERROR_STOP=1 \
  -c 'BEGIN' -f /tmp/projected.sql -c 'COMMIT' >/dev/null 2>&1; then
  echo 'stale candidate unexpectedly replayed' >&2
  exit 1
fi

echo 'F10.10 PUBLIC database ACL PostgreSQL 17 contract: PASS'
