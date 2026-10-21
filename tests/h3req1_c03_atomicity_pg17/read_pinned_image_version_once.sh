#!/usr/bin/env bash
set -Eeuo pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly IMAGE='postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly CONTAINER_NAME='h3req1-pg17-image-version-once-20261009'
readonly EVIDENCE="$ROOT/.context/evidencia/h3req1_pg17_image_version_once_2026-10-09.md"

container_id=''
create_attempted=0
cleanup_failed=0

record() {
    local phase="$1" code="$2"
    [[ "$phase" =~ ^[a-z][a-z0-9-]{0,47}$ ]] || return 1
    [[ "$code" =~ ^[A-Z][A-Z0-9_]{0,47}$ ]] || return 1
    printf 'phase=%s|error_code=%s\n' "$phase" "$code" | tee -a "$EVIDENCE"
}

cleanup() {
    local original_status=$?
    trap - EXIT INT TERM
    if [[ -z "$container_id" ]] && (( create_attempted == 1 )); then
        container_id="$(docker container inspect --format '{{.Id}}' "$CONTAINER_NAME" 2>/dev/null || true)"
    fi
    if [[ -n "$container_id" ]] && docker container inspect "$container_id" >/dev/null 2>&1; then
        docker rm -f "$container_id" >/dev/null 2>&1 || cleanup_failed=1
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
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    record preflight CONTAINER_NAME_COLLISION
    exit 1
fi
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    record preflight PINNED_IMAGE_UNAVAILABLE
    exit 1
fi
record preflight OK

create_attempted=1
if ! container_id="$(docker create --pull=never \
    --name "$CONTAINER_NAME" \
    --network none \
    --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=16 \
    --read-only --cap-drop=ALL --security-opt=no-new-privileges:true \
    --tmpfs /tmp:rw,noexec,nosuid,nodev,size=8m \
    --entrypoint postgres \
    "$IMAGE" --version 2>/dev/null)"; then
    record version-read CONTAINER_CREATE_FAILED
    exit 1
fi
if [[ ! "$container_id" =~ ^[0-9a-f]{64}$ ]]; then
    container_id="$(docker container inspect --format '{{.Id}}' "$CONTAINER_NAME" 2>/dev/null || true)"
    record version-read CONTAINER_ID_INVALID
    exit 1
fi
record container-create OK

set +e
version_output="$(/usr/bin/timeout --foreground --signal=TERM --kill-after=2s 20s \
    docker start --attach "$container_id" 2>/dev/null)"
version_status=$?
set -e
if (( version_status != 0 )); then
    record version-read VERSION_COMMAND_FAILED
    exit 1
fi
if [[ "$version_output" =~ ^postgres\ \(PostgreSQL\)\ 17\.([0-9]{1,2})$ ]]; then
    record version-read "VERSION_17_${BASH_REMATCH[1]}"
else
    record version-read VERSION_OUTPUT_INVALID
    exit 1
fi
