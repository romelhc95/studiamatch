#!/usr/bin/env bash
# StudIAMatch-Docs: .context/componentes/database_migrations.md#migration-20261102-h3-legacy-public-withdrawal
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT
readonly CONTAINER="h3-legacy-withdrawal-pg17-$$"
readonly IMAGE='sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly SNAPSHOT="$ROOT/db/migrations/20261028_h3_editorial_publication_snapshot.sql"
readonly PRICE_GUARD="$ROOT/db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql"
readonly MIGRATION="$ROOT/db/migrations/20261102_h3_legacy_public_withdrawal_guard.sql"

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
  --env POSTGRES_DB=h3_legacy_withdrawal \
  "$IMAGE" >/dev/null

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U postgres -d h3_legacy_withdrawal >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  printf '%s\n' 'PostgreSQL 17 readiness timeout' >&2
  exit 3
fi

docker exec -i "$CONTAINER" psql -U postgres -d h3_legacy_withdrawal -v ON_ERROR_STOP=1 \
  < "$ROOT/tests/sql/h3_legacy_public_withdrawal_pg17_setup.sql"

awk '
  /^CREATE OR REPLACE FUNCTION private\.h2_public_courses_effective\(\)/ { capture = 1 }
  capture { print }
  capture && /^\$\$;/ { exit }
' "$SNAPSHOT" | docker exec -i "$CONTAINER" psql -U postgres -d h3_legacy_withdrawal -v ON_ERROR_STOP=1

docker exec -i "$CONTAINER" psql -U postgres -d h3_legacy_withdrawal -v ON_ERROR_STOP=1 \
  < "$PRICE_GUARD"
docker exec -i "$CONTAINER" psql -U postgres -d h3_legacy_withdrawal -v ON_ERROR_STOP=1 \
  < "$MIGRATION"
docker exec -i "$CONTAINER" psql -U postgres -d h3_legacy_withdrawal -v ON_ERROR_STOP=1 \
  < "$MIGRATION"

docker exec -i "$CONTAINER" psql -U postgres -d h3_legacy_withdrawal -v ON_ERROR_STOP=1 \
  < "$ROOT/tests/sql/h3_legacy_public_withdrawal_pg17_reader_view.sql"
docker exec -i "$CONTAINER" psql -U postgres -d h3_legacy_withdrawal -v ON_ERROR_STOP=1 \
  < "$ROOT/tests/sql/h3_legacy_public_withdrawal_pg17_assert.sql"
