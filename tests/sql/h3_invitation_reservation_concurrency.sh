#!/usr/bin/env bash
set -euo pipefail

command -v psql >/dev/null 2>&1 || {
  echo "psql is required for the invitation concurrency test" >&2
  exit 2
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

suffix="$(date +%s)-$$"
email="h3-concurrency-${suffix}@local.test"
first_output="$tmp_dir/first.txt"
second_output="$tmp_dir/second.txt"
psql_args=(-X -q -A -t -F '|' -v ON_ERROR_STOP=1)

psql "${psql_args[@]}" >"$first_output" <<SQL &
BEGIN;
SELECT success, COALESCE(error_code, '')
FROM public.admin_invitation_reserve(
  '$email', 'user', '30000000-0000-0000-0000-000000000001', NULL,
  false, 'concurrent-request-a-${suffix}', '{}'::jsonb, NULL
);
SELECT pg_sleep(1);
COMMIT;
SQL
first_pid=$!

# The first transaction keeps the per-email advisory lock during this sleep;
# the second reservation must wait and then observe the existing pending row.
sleep 0.15
psql "${psql_args[@]}" >"$second_output" <<SQL &
SELECT success, COALESCE(error_code, '')
FROM public.admin_invitation_reserve(
  '$email', 'user', '30000000-0000-0000-0000-000000000001', NULL,
  false, 'concurrent-request-b-${suffix}', '{}'::jsonb, NULL
);
SQL
second_pid=$!

wait "$first_pid"
wait "$second_pid"

if ! grep -Fxq 't|' "$first_output"; then
  cat "$first_output" >&2
  echo "first invitation reservation did not succeed" >&2
  exit 1
fi
if ! grep -Fxq 'f|duplicate_pending' "$second_output"; then
  cat "$second_output" >&2
  echo "concurrent invitation request was not serialized as duplicate_pending" >&2
  exit 1
fi

pending_count="$(psql "${psql_args[@]}" -c \
  "SELECT count(*) FROM public.admin_invitations WHERE email = '$email' AND status = 'pending'")"
if [[ "$pending_count" != "1" ]]; then
echo "expected one pending reservation for the racing email, got $pending_count" >&2
exit 1
fi

# A same-key resend that races the original reservation must be rejected under
# the per-email lock rather than superseding it and emitting a second Auth call.
idempotency_email="h3-same-request-${suffix}@local.test"
idempotency_request="same-request-${suffix}"
first_output="$tmp_dir/idempotency-first.txt"
second_output="$tmp_dir/idempotency-second.txt"
psql "${psql_args[@]}" >"$first_output" <<SQL &
BEGIN;
SELECT success, COALESCE(error_code, '')
FROM public.admin_invitation_reserve(
  '$idempotency_email', 'user', '30000000-0000-0000-0000-000000000001', NULL,
  false, '$idempotency_request', '{}'::jsonb, NULL
);
SELECT pg_sleep(1);
COMMIT;
SQL
first_pid=$!
sleep 0.15
psql "${psql_args[@]}" >"$second_output" <<SQL &
SELECT success, COALESCE(error_code, '')
FROM public.admin_invitation_reserve(
  '$idempotency_email', 'user', '30000000-0000-0000-0000-000000000001', NULL,
  true, '$idempotency_request', '{}'::jsonb, NULL
);
SQL
second_pid=$!
wait "$first_pid"
wait "$second_pid"
if ! grep -Fxq 'f|reconciliation_required' "$second_output"; then
  cat "$second_output" >&2
  echo "same request id raced into a duplicate invitation reservation" >&2
  exit 1
fi
idempotency_rows="$(psql "${psql_args[@]}" -c \
  "SELECT count(*) FROM public.admin_invitations WHERE email = '$idempotency_email'")"
if [[ "$idempotency_rows" != "1" ]]; then
  echo "same request id created $idempotency_rows invitation reservations" >&2
  exit 1
fi

# Acceptance and a simultaneous resend share the per-email lock. Acceptance
# must finish first; the resend then observes password_pending instead of
# deadlocking across invitation/member row locks.
auth_race_email="h3-accept-resend-${suffix}@local.test"
auth_race_id="$(psql "${psql_args[@]}" -c 'SELECT gen_random_uuid()')"
psql "${psql_args[@]}" -c \
  "INSERT INTO auth.users (id, email, encrypted_password, role, aud, created_at, updated_at) VALUES ('$auth_race_id', '$auth_race_email', 'x', 'authenticated', 'authenticated', now(), now())" >/dev/null
invitation_id="$(psql "${psql_args[@]}" -c \
  "SELECT invitation_id FROM public.admin_invitation_reserve('$auth_race_email', 'user', '30000000-0000-0000-0000-000000000001', '$auth_race_id', false, 'accept-resend-initial-${suffix}', '{}'::jsonb, NULL)")"
if [[ -z "$invitation_id" ]]; then
  echo "could not prepare invitation for acceptance/resend race" >&2
  exit 1
fi

accept_output="$tmp_dir/accept.txt"
resend_output="$tmp_dir/resend.txt"
psql "${psql_args[@]}" >"$accept_output" <<SQL &
BEGIN;
SELECT set_config('request.jwt.claim.sub', '$auth_race_id', true);
SELECT success, account_status, COALESCE(error_code, '')
FROM public.admin_accept_current_invitation('$invitation_id');
SELECT pg_sleep(1);
COMMIT;
SQL
accept_pid=$!
sleep 0.15
psql "${psql_args[@]}" >"$resend_output" <<SQL &
SELECT success, COALESCE(error_code, '')
FROM public.admin_invitation_reserve(
  '$auth_race_email', 'user', '30000000-0000-0000-0000-000000000001', '$auth_race_id',
  true, 'accept-resend-racing-${suffix}', '{}'::jsonb, NULL
);
SQL
resend_pid=$!
wait "$accept_pid"
wait "$resend_pid"

if ! grep -Fxq 't|password_pending|' "$accept_output"; then
  cat "$accept_output" >&2
  echo "concurrent invitation acceptance did not complete before resend" >&2
  exit 1
fi
if ! grep -Fxq 'f|onboarding_in_progress' "$resend_output"; then
  cat "$resend_output" >&2
  echo "resend did not observe the completed acceptance state" >&2
  exit 1
fi

# A status read locks membership before invitation. Completion must use the
# same row order; if it locks invitation first this orchestration deadlocks.
lock_race_email="h3-status-completion-${suffix}@local.test"
lock_race_id="$(psql "${psql_args[@]}" -c 'SELECT gen_random_uuid()')"
psql "${psql_args[@]}" -c \
  "INSERT INTO auth.users (id, email, encrypted_password, role, aud, created_at, updated_at) VALUES ('$lock_race_id', '$lock_race_email', 'x', 'authenticated', 'authenticated', now(), now())" >/dev/null
lock_race_invitation="$(psql "${psql_args[@]}" -c \
  "SELECT invitation_id FROM public.admin_invitation_reserve('$lock_race_email', 'user', '30000000-0000-0000-0000-000000000001', '$lock_race_id', false, 'status-completion-initial-${suffix}', '{}'::jsonb, NULL)")"
status_output="$tmp_dir/status.txt"
complete_output="$tmp_dir/complete.txt"
psql "${psql_args[@]}" >"$status_output" <<SQL &
BEGIN;
SELECT member.user_id FROM public.admin_members member
WHERE member.user_id = '$lock_race_id' FOR UPDATE;
SELECT pg_sleep(0.5);
SELECT set_config('request.jwt.claim.sub', '$lock_race_id', true);
SELECT success FROM public.admin_get_onboarding_status();
COMMIT;
SQL
status_pid=$!
sleep 0.15
psql "${psql_args[@]}" >"$complete_output" <<SQL &
SELECT success, member_id, COALESCE(error_code, '')
FROM public.admin_invitation_complete('$lock_race_invitation', '$lock_race_id');
SQL
complete_pid=$!
wait "$status_pid"
wait "$complete_pid"

if ! grep -Fxq 't' "$status_output"; then
  cat "$status_output" >&2
  echo "onboarding status did not complete during completion lock-order test" >&2
  exit 1
fi
if ! grep -Fxq "t|$lock_race_id|" "$complete_output"; then
  cat "$complete_output" >&2
  echo "invitation completion did not complete during onboarding status read" >&2
  exit 1
fi

echo "h3_invitation_reservation_concurrency_ok"
