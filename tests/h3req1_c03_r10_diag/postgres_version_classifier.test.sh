#!/usr/bin/env bash
set -Eeuo pipefail

source /diag/postgres_version_classifier.sh

cases=0
expect_match() {
  h3req1_is_postgres_17_11 "$1"
  cases=$((cases + 1))
}
expect_reject() {
  if h3req1_is_postgres_17_11 "$1"; then
    printf 'phase=postgres-version-classifier-synthetic|error_code=REJECTED_CASE_ACCEPTED\n'
    exit 1
  fi
  cases=$((cases + 1))
}

expect_match 'postgres (PostgreSQL) 17.11 (Debian 17.11-1.pgdg13+2)'
expect_match 'postgres (PostgreSQL) 17.11'
expect_reject 'postgres (PostgreSQL) 17.10 (Debian 17.10-1.pgdg13+1)'
expect_reject 'postgres (PostgreSQL) 16.11 (Debian 16.11-1.pgdg13+1)'
expect_reject 'postgres (PostgreSQL) 17.11 (Debian 17.10-1.pgdg13+1)'
expect_reject 'postgres (PostgreSQL) 17.11 (Alpine 17.11-r0)'
expect_reject 'postgres (PostgreSQL) 17.11 (Debian 17.11-1.pgdg13+2) trailing'

printf 'phase=postgres-version-classifier-synthetic|error_code=PASS cases=%s\n' "$cases"
