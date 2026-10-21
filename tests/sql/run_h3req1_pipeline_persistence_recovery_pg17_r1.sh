#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly ROOT
readonly CONTAINER='h3req1-g09-pipeline-pg17-r144'
readonly DATABASE='h3_pipeline_recovery_r1'
readonly PG_IMAGE_ID='sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'

if ! command -v docker >/dev/null 2>&1; then
  printf 'phase=preflight|result=FAIL|code=DOCKER_UNAVAILABLE\n' >&2
  exit 2
fi
if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
  printf 'phase=preflight|result=FAIL|code=CONTAINER_NAME_ALREADY_EXISTS\n' >&2
  exit 2
fi
if [[ "$(docker image inspect --format '{{.Id}}' "$PG_IMAGE_ID")" != "$PG_IMAGE_ID" ]]; then
  printf 'phase=preflight|result=FAIL|code=PG17_IMAGE_PIN_MISMATCH\n' >&2
  exit 2
fi

cleanup() {
  local status=$?
  trap - EXIT
  if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
    docker rm -f "$CONTAINER" >/dev/null
  fi
  exit "$status"
}
trap cleanup EXIT

printf 'phase=pg17-start|result=START\n'
docker run --pull=never --detach \
  --name "$CONTAINER" \
  --network none \
  --cpus 2 \
  --memory 4g \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=2g \
  --env POSTGRES_DB="$DATABASE" \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  --mount "type=bind,src=$ROOT/tests/sql/h3req1_pipeline_persistence_recovery_pg17_r1.sql,dst=/fixture/pipeline.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260430_intermediate_tables_ddl.sql,dst=/fixture/20260430_intermediate_tables_ddl.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql,dst=/fixture/20260808_fase10_8_atomic_cleansing_provenance.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260525_fase113_pro_rls_and_rpc_sync.sql,dst=/fixture/20260525_fase113_pro_rls_and_rpc_sync.sql,readonly" \
  "$PG_IMAGE_ID" >/dev/null

ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U postgres -d "$DATABASE" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if (( ready != 1 )); then
  printf 'phase=pg17-start|result=FAIL|code=READINESS_TIMEOUT\n' >&2
  exit 1
fi
printf 'phase=pg17-start|result=PASS|postgres=17-fixture\n'

printf 'phase=pipeline-persistence-recovery|result=START\n'
docker exec "$CONTAINER" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/pipeline.sql
printf 'phase=pipeline-persistence-recovery|result=PASS\n'
