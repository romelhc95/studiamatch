#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT
readonly RUN_ID="$$"
readonly CONTAINER="h1-fg3-atomic-pg17-${RUN_ID}"
readonly LOG_DIR="${TMPDIR:-/tmp}/h1-fg3-atomic-pg17-${RUN_ID}"
readonly PG_IMAGE='postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly SNAPSHOT="$ROOT/db/migrations/20261028_h3_editorial_publication_snapshot.sql"
readonly PRICE_GUARD="$ROOT/db/migrations/20261028_h3_public_price_projection_empty_price_guard.sql"
readonly WITHDRAWAL_GUARD="$ROOT/db/migrations/20261102_h3_legacy_public_withdrawal_guard.sql"
readonly MIGRATION="$ROOT/db/migrations/20261115234509_h1_fg3_atomic_public_transition.sql"

if [[ -n "$(docker ps -a --filter "name=^/${CONTAINER}$" --format '{{.Names}}')" ]]; then
  printf 'Refusing to reuse existing container %s\n' "$CONTAINER" >&2
  exit 2
fi
mkdir -m 700 "$LOG_DIR"

docker run --rm --detach \
  --name "$CONTAINER" \
  --network none \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=256m \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  --env POSTGRES_USER=postgres \
  --env POSTGRES_DB=h1_fg3_atomic \
  "$PG_IMAGE" >/dev/null

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf -- "$LOG_DIR"
}
trap cleanup EXIT

ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U postgres -d h1_fg3_atomic >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then
  printf '%s\n' 'PostgreSQL 17 readiness timeout' >&2
  exit 3
fi

run_sql() {
  docker exec -i "$CONTAINER" psql -U postgres -d h1_fg3_atomic -v ON_ERROR_STOP=1 < "$1"
}

run_sql "$ROOT/tests/sql/h3_legacy_public_withdrawal_pg17_setup.sql"
run_sql "$ROOT/tests/sql/h1_fg3_atomic_public_transition_pg17_expand.sql"
awk '
  /^CREATE OR REPLACE FUNCTION private\.h2_public_courses_effective\(\)/ { capture = 1 }
  capture { print }
  capture && /^\$\$;/ { exit }
' "$SNAPSHOT" | docker exec -i "$CONTAINER" psql -U postgres -d h1_fg3_atomic -v ON_ERROR_STOP=1
run_sql "$PRICE_GUARD"
run_sql "$WITHDRAWAL_GUARD"
run_sql "$WITHDRAWAL_GUARD"
run_sql "$ROOT/tests/sql/h3_legacy_public_withdrawal_pg17_reader_view.sql"
run_sql "$MIGRATION"
run_sql "$MIGRATION"
run_sql "$ROOT/tests/sql/h3_legacy_public_withdrawal_pg17_assert.sql"
run_sql "$ROOT/tests/sql/h1_fg3_atomic_public_transition_pg17_assert.sql"

readonly TARGET_COURSE='10000000-0000-0000-0000-000000000012'
readonly TARGET_INSTITUTION='10000000-0000-0000-0000-000000000001'
marker="$(docker exec "$CONTAINER" psql -U postgres -d h1_fg3_atomic -Atq \
  -c "SELECT last_404_at FROM public.courses WHERE id = '${TARGET_COURSE}'")"
if [[ ! "$marker" =~ ^[0-9T:+.Z\ -]+$ ]]; then
  printf 'Unexpected synthetic last_404_at representation\n' >&2
  exit 4
fi

docker exec -i "$CONTAINER" psql -U postgres -d h1_fg3_atomic -v ON_ERROR_STOP=1 \
  >"$LOG_DIR/eligibility-writer.log" 2>&1 <<'SQL' &
BEGIN;
UPDATE public.course_editorial_state
   SET editorial_status = 'pending_review'
 WHERE course_id = '10000000-0000-0000-0000-000000000012';
INSERT INTO public.course_editorial_audit (course_id, action)
VALUES ('10000000-0000-0000-0000-000000000012', 'unpublish');
SELECT pg_catalog.pg_sleep(5) /* h1_fg3_atomic_eligibility_lock */;
COMMIT;
SQL
writer_pid=$!

locked=0
for _ in $(seq 1 50); do
  active_writer="$(docker exec "$CONTAINER" psql -U postgres -d h1_fg3_atomic -Atq \
    -c "SELECT count(*) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND state = 'active' AND position('h1_fg3_atomic_eligibility_lock' in query) > 0")"
  if [[ "$active_writer" == 1 ]]; then
    locked=1
    break
  fi
  sleep 0.1
done
if [[ "$locked" != 1 ]]; then
  cat "$LOG_DIR/eligibility-writer.log" >&2
  wait "$writer_pid" || true
  printf '%s\n' 'Concurrent eligibility writer did not reach its held-lock state' >&2
  exit 5
fi

outcome="$(docker exec "$CONTAINER" psql -U postgres -d h1_fg3_atomic -Atq \
  -c "SELECT outcome FROM public.fg3_apply_public_course_transition(
        '${TARGET_COURSE}', '${TARGET_INSTITUTION}', NULL,
        '${marker}'::timestamptz, 200, 'clear_404_grace')")"
wait "$writer_pid"
if [[ "$outcome" != 'stale' ]]; then
  printf 'Expected concurrent public withdrawal to return stale, got: %s\n' "$outcome" >&2
  exit 6
fi

unchanged="$(docker exec "$CONTAINER" psql -U postgres -d h1_fg3_atomic -Atq \
  -c "SELECT last_404_at IS NOT DISTINCT FROM '${marker}'::timestamptz
      FROM public.courses WHERE id = '${TARGET_COURSE}'")"
if [[ "$unchanged" != 't' ]]; then
  printf '%s\n' 'Concurrent loss of public eligibility did not preserve the observed course state' >&2
  exit 7
fi
if [[ -n "$(docker exec "$CONTAINER" psql -U postgres -d h1_fg3_atomic -Atq \
  -c "SELECT 1 FROM public.courses_public_effective WHERE id = '${TARGET_COURSE}'")" ]]; then
  printf '%s\n' 'Concurrent withdrawal unexpectedly remains visible in the public view' >&2
  exit 8
fi

# H2's contracted Production schema drops the legacy base table. H3 keeps an
# empty compatibility view in that case; the FG3 transition must still work
# for strict-public courses without planning a reference to the missing table.
docker exec -i "$CONTAINER" psql -U postgres -d h1_fg3_atomic -v ON_ERROR_STOP=1 <<'SQL'
CREATE OR REPLACE VIEW private.h3_legacy_public_course_cohort AS
SELECT NULL::UUID AS course_id WHERE false;
DROP TABLE private.h2_legacy_public_course_cohort;
SQL
run_sql "$WITHDRAWAL_GUARD"
docker exec -i "$CONTAINER" psql -U postgres -d h1_fg3_atomic -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO public.courses (id, institution_id, name, is_active, is_verified)
VALUES ('10000000-0000-0000-0000-000000000017',
        '10000000-0000-0000-0000-000000000001',
        'Atomic strict-public without legacy table', true, true);
INSERT INTO public.course_editorial_state (
  course_id, editorial_status, published_editorial_values, availability_status
)
VALUES ('10000000-0000-0000-0000-000000000017', 'published', '{}', 'available');

DO $contracted_schema_assertions$
DECLARE
  _outcome TEXT;
  _marker TIMESTAMPTZ;
BEGIN
  IF pg_catalog.to_regclass('private.h2_legacy_public_course_cohort') IS NOT NULL THEN
    RAISE EXCEPTION 'contracted schema must not contain the H2 legacy base table';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.courses_public_effective
     WHERE id = '10000000-0000-0000-0000-000000000017'
  ) THEN
    RAISE EXCEPTION 'strict-public course must remain visible without the H2 legacy table';
  END IF;

  SELECT transition.outcome INTO _outcome
    FROM public.fg3_apply_public_course_transition(
      '10000000-0000-0000-0000-000000000017',
      '10000000-0000-0000-0000-000000000001',
      NULL, NULL, 404, 'start_404_grace'
    ) AS transition;
  SELECT last_404_at INTO _marker FROM public.courses
   WHERE id = '10000000-0000-0000-0000-000000000017';
  IF _outcome IS DISTINCT FROM 'applied' OR _marker IS NULL THEN
    RAISE EXCEPTION 'atomic FG3 must work for strict-public courses after H2 contract';
  END IF;
END;
$contracted_schema_assertions$;
SQL

printf '%s\n' 'h1_fg3_atomic_public_transition_pg17_ok'
printf '%s\n' 'concurrent eligibility loss: stale; zero course write'
printf '%s\n' 'contracted H2 schema: strict-public transition applied without legacy base table'
