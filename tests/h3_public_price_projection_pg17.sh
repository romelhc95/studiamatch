#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT
readonly CONTAINER='h3req1-public-price-projection-pg17-20261028'
readonly IMAGE='sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'

if [[ -n "$(docker ps -a --filter "name=^/${CONTAINER}$" --format '{{.Names}}')" ]]; then
  printf 'Refusing to reuse existing container %s\n' "$CONTAINER" >&2
  exit 2
fi

docker run --rm --detach \
  --name "$CONTAINER" \
  --network none \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=256m \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  --env POSTGRES_USER=postgres \
  --env POSTGRES_DB=h3_price_projection \
  "$IMAGE" >/dev/null

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U postgres -d h3_price_projection >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  printf '%s\n' 'PostgreSQL 17 readiness timeout' >&2
  exit 3
fi

docker exec -i "$CONTAINER" psql -U postgres -d h3_price_projection -v ON_ERROR_STOP=1 \
  < "$ROOT/tests/sql/h3_public_price_projection_pg17_setup.sql"
docker exec -i "$CONTAINER" psql -U postgres -d h3_price_projection -v ON_ERROR_STOP=1 \
  < "$ROOT/db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql"
docker exec -i "$CONTAINER" psql -U postgres -d h3_price_projection -v ON_ERROR_STOP=1 \
  < "$ROOT/db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql"
docker exec -i "$CONTAINER" psql -U postgres -d h3_price_projection -v ON_ERROR_STOP=1 \
  < "$ROOT/tests/sql/h3_public_price_projection_pg17_assert.sql"
