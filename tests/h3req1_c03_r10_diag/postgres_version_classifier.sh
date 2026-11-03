#!/usr/bin/env bash

h3req1_is_postgres_17_11() {
  local output="${1-}"
  [[ "$output" =~ ^postgres[[:space:]]\(PostgreSQL\)[[:space:]]([0-9]+\.[0-9]+)([[:space:]]\(Debian[[:space:]]([0-9]+\.[0-9]+)-[^()]+\))?$ ]] \
    || return 1
  [[ "${BASH_REMATCH[1]}" == '17.11' ]] || return 1
  [[ -z "${BASH_REMATCH[3]:-}" || "${BASH_REMATCH[3]}" == '17.11' ]]
}
