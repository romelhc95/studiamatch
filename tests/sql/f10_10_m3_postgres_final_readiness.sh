#!/usr/bin/env bash

f1010_postgres_diagnostics() {
  local container="$1"
  local state
  state="$(docker inspect --format 'running={{.State.Running}} status={{.State.Status}} exit_code={{.State.ExitCode}}' \
    "$container" 2>/dev/null || printf 'unavailable')"
  printf 'F10.10 ACL PostgreSQL diagnostics: %s\n' "$state" >&2
  docker logs "$container" 2>&1 \
    | grep -E 'PostgreSQL init process complete|database system is ready|database system is shut down|FATAL|PANIC' \
    | tail -20 >&2 || true
}

f1010_wait_for_final_postgres() {
  local container="$1"
  local init_attempts="${F1010_ACL_INIT_ATTEMPTS:-60}"
  local final_attempts="${F1010_ACL_FINAL_ATTEMPTS:-60}"
  local stable_attempts="${F1010_ACL_STABLE_ATTEMPTS:-15}"
  local sleep_seconds="${F1010_ACL_READINESS_SLEEP_SECONDS:-1}"
  local init_complete=0
  local final_ready=0
  local stable_probes=0

  for _ in $(seq 1 "$init_attempts"); do
    if [ "$(docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null)" != "true" ]; then
      f1010_postgres_diagnostics "$container"
      return 1
    fi
    if docker logs "$container" 2>&1 \
        | grep -Fq 'PostgreSQL init process complete; ready for start up.'; then
      init_complete=1
      break
    fi
    sleep "$sleep_seconds"
  done
  if [ "$init_complete" -ne 1 ]; then
    f1010_postgres_diagnostics "$container"
    return 1
  fi

  for _ in $(seq 1 "$final_attempts"); do
    if [ "$(docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null)" != "true" ]; then
      f1010_postgres_diagnostics "$container"
      return 1
    fi
    if docker exec "$container" test -S /var/run/postgresql/.s.PGSQL.5432 >/dev/null 2>&1 \
        && docker exec "$container" pg_isready -U postgres -d postgres >/dev/null 2>&1; then
      final_ready=1
      break
    fi
    sleep "$sleep_seconds"
  done
  if [ "$final_ready" -ne 1 ]; then
    f1010_postgres_diagnostics "$container"
    return 1
  fi

  for _ in $(seq 1 "$stable_attempts"); do
    if [ "$(docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null)" = "true" ] \
        && docker exec "$container" test -S /var/run/postgresql/.s.PGSQL.5432 >/dev/null 2>&1 \
        && docker exec "$container" pg_isready -U postgres -d postgres >/dev/null 2>&1; then
      stable_probes=$((stable_probes + 1))
      if [ "$stable_probes" -eq 3 ]; then
        return 0
      fi
    else
      stable_probes=0
    fi
    sleep "$sleep_seconds"
  done
  f1010_postgres_diagnostics "$container"
  return 1
}
