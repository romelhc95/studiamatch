#!/usr/bin/env bash
set -Eeuo pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly MANIFEST="$ROOT/.context/operaciones/manifest_h3req1_editorial_atomicity_pg17_2026-10-09.sha256"
readonly EXPECTED_MANIFEST_SHA256='0ed63a7b439275121caa9255ea033030f20e363fdb71eb202a47a94792ab2bc5'
readonly HARNESS='tests/sql/h3_pg17_harness.sql'
readonly IMAGE='postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly CONTAINER_NAME='h3req1-editorial-atomicity-pg17-v2-once-20261009'
readonly EVIDENCE="$ROOT/.context/evidencia/h3req1_editorial_atomicity_pg17_v2_once_2026-10-09.md"

container_id=''
log_file=''
cleanup_failed=0

record() {
    local phase="$1" code="$2"
    [[ "$phase" =~ ^[a-z][a-z0-9-]{0,47}$ ]] || return 1
    [[ "$code" =~ ^[A-Z][A-Z0-9_]{0,47}$ ]] || return 1
    printf 'phase=%s|error_code=%s\n' "$phase" "$code" | tee -a "$EVIDENCE"
}

parse_pg_version() {
    local version_output="${1%$'\r'}"
    PG_VERSION_CODE='VERSION_OUTPUT_INVALID'
    if [[ "$version_output" =~ ^postgres\ \(PostgreSQL\)\ ([0-9]{1,2})\.([0-9]{1,2})([ ][A-Za-z0-9\ \(\)_\.\+~-]{1,100})?$ ]]; then
        PG_VERSION_CODE="VERSION_${BASH_REMATCH[1]}_${BASH_REMATCH[2]}"
        return 0
    fi
    return 1
}

test_pg_version_parser() {
    parse_pg_version 'postgres (PostgreSQL) 17.11' && [[ "$PG_VERSION_CODE" == 'VERSION_17_11' ]] || return 1
    parse_pg_version 'postgres (PostgreSQL) 17.11 (Debian 17.11-1.pgdg12+1)' && [[ "$PG_VERSION_CODE" == 'VERSION_17_11' ]] || return 1
    parse_pg_version 'postgres (PostgreSQL) 17.5 (Debian 17.5-1.pgdg12+1)' && [[ "$PG_VERSION_CODE" == 'VERSION_17_5' ]] || return 1
    parse_pg_version 'postgres (PostgreSQL) 16.11 (Debian 16.11-1.pgdg12+1)' && [[ "$PG_VERSION_CODE" == 'VERSION_16_11' ]] || return 1
    parse_pg_version $'postgres (PostgreSQL) 17.11\r' && [[ "$PG_VERSION_CODE" == 'VERSION_17_11' ]] || return 1
    if parse_pg_version 'postgres (PostgreSQL) 17.11;unclassified'; then return 1; fi
    if parse_pg_version $'postgres (PostgreSQL) 17.11\nraw'; then return 1; fi
}

cleanup() {
    local original_status=$?
    trap - EXIT INT TERM
    if [[ -n "$container_id" ]] && docker container inspect "$container_id" >/dev/null 2>&1; then
        docker stop --time 2 "$container_id" >/dev/null 2>&1 || true
        docker rm "$container_id" >/dev/null 2>&1 || cleanup_failed=1
    fi
    if [[ -n "$log_file" ]]; then
        rm -f -- "$log_file"
    fi
    if [[ -n "$container_id" ]]; then
        if (( cleanup_failed == 0 )); then
            record container-cleanup OK || cleanup_failed=1
        else
            record container-cleanup CLEANUP_FAILED || true
        fi
    fi
    if (( original_status == 0 && cleanup_failed != 0 )); then
        exit 1
    fi
    exit "$original_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if (( EUID == 0 )); then
    record preflight RUN_AS_NONROOT
    exit 1
fi
if [[ ! -x /usr/bin/sha256sum || ! -x /usr/bin/timeout || ! -x /usr/bin/grep ]]; then
    record preflight RUNTIME_UNAVAILABLE
    exit 1
fi
if [[ ! -d "$ROOT/.context/evidencia" || -e "$EVIDENCE" ]]; then
    record preflight EVIDENCE_PATH_UNAVAILABLE
    exit 1
fi
cd "$ROOT"
if [[ "$(git branch --show-current 2>/dev/null)" != 'feat/h3req1-sync-20261002' ]] ||
   [[ "$(git rev-parse HEAD 2>/dev/null)" != '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]]; then
    record preflight CANDIDATE_IDENTITY_MISMATCH
    exit 1
fi
manifest_line="$(/usr/bin/sha256sum -- "$MANIFEST" 2>/dev/null)" || {
    record preflight MANIFEST_READ_FAILED
    exit 1
}
if [[ "${manifest_line%% *}" != "$EXPECTED_MANIFEST_SHA256" ]]; then
    record preflight MANIFEST_HASH_MISMATCH
    exit 1
fi
if ! /usr/bin/sha256sum --check --strict "$MANIFEST" >/dev/null 2>&1; then
    record preflight INPUT_HASH_MISMATCH
    exit 1
fi
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    record preflight PINNED_IMAGE_UNAVAILABLE
    exit 1
fi
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    record preflight CONTAINER_NAME_COLLISION
    exit 1
fi
record preflight OK

if ! test_pg_version_parser; then
    record pg17-version-parser-synthetic SYNTHETIC_TESTS_FAILED
    exit 1
fi
record pg17-version-parser-synthetic OK

if ! container_id="$(docker run --pull=never -d \
    --name "$CONTAINER_NAME" \
    --network none \
    --cpus=2 --memory=2g --pids-limit=256 \
    --read-only \
    --tmpfs /var/lib/postgresql/data:rw,nosuid,nodev,size=1024m \
    --tmpfs /var/run/postgresql:rw,nosuid,nodev,size=64m \
    --tmpfs /tmp:rw,nosuid,nodev,size=64m \
    --env POSTGRES_HOST_AUTH_METHOD=trust \
    --mount "type=bind,src=$ROOT/tests/sql,dst=/candidate/tests/sql,readonly" \
    --mount "type=bind,src=$ROOT/db/migrations,dst=/candidate/db/migrations,readonly" \
    --mount "type=bind,src=$ROOT/db/seeds,dst=/candidate/db/seeds,readonly" \
    "$IMAGE" 2>/dev/null)"; then
    container_id="$(docker container inspect --format '{{.Id}}' "$CONTAINER_NAME" 2>/dev/null || true)"
    record pg17-start CONTAINER_START_FAILED
    exit 1
fi
if [[ ! "$container_id" =~ ^[0-9a-f]{64}$ ]]; then
    record pg17-start CONTAINER_ID_INVALID
    exit 1
fi
record pg17-start OK

ready=0
for ((attempt = 0; attempt < 60; attempt++)); do
    if docker exec "$container_id" pg_isready --quiet --username=postgres >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 0.5
done
if (( ready != 1 )); then
    record pg17-ready READY_TIMEOUT
    exit 1
fi
version_output="$(docker exec "$container_id" postgres --version 2>/dev/null)" || {
    record pg17-version VERSION_READ_FAILED
    exit 1
}
if ! parse_pg_version "$version_output"; then
    record pg17-version VERSION_OUTPUT_INVALID
    exit 1
fi
if [[ "$PG_VERSION_CODE" != 'VERSION_17_11' ]]; then
    record pg17-version "$PG_VERSION_CODE"
    exit 1
fi
record pg17-ready OK

log_file="$(mktemp /tmp/h3req1-atomicity-pg17-once.XXXXXX)" || {
    record sql-harness TEMP_OUTPUT_UNAVAILABLE
    exit 1
}
set +e
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 180s \
    docker exec "$container_id" psql -X -q -A -t \
      --set=ON_ERROR_STOP=1 --set=VERBOSITY=sqlstate \
      --username=postgres --dbname=postgres \
      --file="/candidate/$HARNESS" >"$log_file" 2>&1
psql_status=$?
set -e
if (( psql_status == 0 )) && grep -Fxq 'h3_pg17_harness_ok' "$log_file"; then
    record sql-harness OK
else
    sqlstate="$(sed -nE 's/^ERROR: ([A-Z0-9]{5})$/\1/p' "$log_file" | tail -n 1)"
    if [[ "$sqlstate" =~ ^[A-Z0-9]{5}$ ]]; then
        record sql-harness "SQLSTATE_$sqlstate"
    elif (( psql_status == 124 || psql_status == 137 )); then
        record sql-harness TIMEOUT
    else
        record sql-harness HARNESS_FAILED
    fi
    exit 1
fi
