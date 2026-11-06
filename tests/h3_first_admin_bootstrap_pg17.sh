#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT
readonly CONTAINER="h3-first-admin-bootstrap-pg17-$$"
readonly IMAGE='sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  printf 'Pinned PostgreSQL 17 image is not present locally: %s\n' "$IMAGE" >&2
  exit 5
fi

if [[ -n "$(docker ps -a --filter "name=^/${CONTAINER}$" --format '{{.Names}}')" ]]; then
  printf 'Refusing to reuse existing container %s\n' "$CONTAINER" >&2
  exit 2
fi

docker run --pull=never --rm --detach \
  --name "$CONTAINER" \
  --network none \
  --mount "type=bind,source=$ROOT,target=/workspace,readonly" \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=256m \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  --env POSTGRES_USER=postgres \
  --env POSTGRES_DB=h3_first_admin \
  "$IMAGE" >/dev/null

cleanup() {
  local status=$?
  trap - EXIT
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  if [[ -n "$(docker ps -a --filter "name=^/${CONTAINER}$" --format '{{.Names}}')" ]]; then
    printf 'Disposable PostgreSQL container remains: %s\n' "$CONTAINER" >&2
    status=4
  fi
  exit "$status"
}
trap cleanup EXIT

ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U postgres -d h3_first_admin >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  printf '%s\n' 'PostgreSQL 17 readiness timeout' >&2
  exit 3
fi

docker exec "$CONTAINER" psql -U postgres -d h3_first_admin -v ON_ERROR_STOP=1 \
  -f /workspace/tests/sql/h3_first_admin_bootstrap_pg17_harness.sql

printf '%s\n' 'h3_first_admin_bootstrap_pg17 PASS'
