#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-EDGE-LOCK-RESOLVER-2026-10-06-R3'
readonly MANIFEST='tests/h3req1-c03-edge-lock-resolver-r3.sha256'
[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" && "${3:-}" == '--manifest-sha256' && $# -eq 4 ]] || {
  echo "Refusing to run: exact JIT $JIT and approved manifest SHA-256 required." >&2
  exit 77
}
readonly APPROVED_MANIFEST_SHA256="${4:-}"
[[ "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] || {
  echo 'Refusing to run: invalid manifest SHA-256.' >&2
  exit 77
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
exec 3>&1

readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly SOURCE_DIR='supabase/functions/admin-invite'
readonly FIXTURE_DIR='tests/h3req1-c03-edge-lock-resolver'
readonly WORKSPACE_DIR='tests/h3req1-c03-edge-lock-output-r3'
readonly CONTAINER='h3req1-c03-edge-lock-resolver-20261006-r3'
readonly DENO_CACHE='h3req1-c03-edge-lock-deno-cache-20261006-r5'
readonly WORKSPACE_VOLUME='h3req1-c03-edge-lock-workspace-20261006-r3'
readonly LOCK_FILE="$WORKSPACE_DIR/deno-edge-runtime-v1.74.3-r3.lock"
readonly LOCK_STAGE='.context/evidencia/h3req1_c03_edge_lock_r3_candidate.tmp'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_edge_lock_resolver_2026-10-06_r3.log'
readonly DENO_IMAGE='denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9'
readonly RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"

phase='preflight'
on_error() {
  local status=$?
  printf 'R3 lock resolver halted in phase=%s (exit=%s); no automatic cleanup; preserve resources.\n' "$phase" "$status" >&3
}
trap on_error ERR
fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }
assert_container_name_free() {
  local matches existing
  matches="$(docker ps -a --format '{{.Names}}' --filter "name=$CONTAINER")" || fail 'unable to list matching container names'
  while IFS= read -r existing; do
    [[ "$existing" != "$CONTAINER" ]] || fail "container name occupied: $CONTAINER"
  done <<< "$matches"
}
assert_volume_name_free() {
  local requested=$1 matches existing
  matches="$(docker volume ls --format '{{.Name}}' --filter "name=$requested")" || fail "unable to list matching volume names: $requested"
  while IFS= read -r existing; do
    [[ "$existing" != "$requested" ]] || fail "volume name occupied: $requested"
  done <<< "$matches"
}
create_fresh_volume() {
  local requested=$1 created nonce_label
  created="$(docker volume create \
    --label "com.studiamatch.h3.c03.jit=$JIT" \
    --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.c03.run=$RUN_NONCE" "$requested")" || fail "unable to create fresh volume: $requested"
  [[ "$created" == "$requested" ]] || fail "Docker returned an unexpected volume name: $requested"
  nonce_label="$(docker volume inspect -f '{{ index .Labels "com.studiamatch.h3.c03.run" }}' "$requested")" || fail "unable to verify new volume label: $requested"
  [[ "$nonce_label" == "$RUN_NONCE" ]] || fail "volume was not created by this exact R3 invocation: $requested"
}

summarize_resolver_output() {
  local line normalized category seen='|'
  while IFS= read -r line || [[ -n "$line" ]]; do
    normalized="${line,,}"
    category=''
    case "$normalized" in
      *permissiondenied*|*'permission denied'*|*eacces*|*eperm*) category='permission-denied' ;;
      *notcapable*) category='not-capable' ;;
      *'no such file or directory'*|*enoent*) category='missing-file-or-directory' ;;
      *'checksum mismatch'*|*'integrity check failed'*|*eintegrity*) category='integrity-or-checksum-failure' ;;
      *lock*|*'out of date'*) category='lockfile-resolution-failure' ;;
      *'module not found'*|*'specifier not found'*|*eresolve*) category='module-resolution-failure' ;;
      *'failed to resolve'*|*'error sending request'*|*'connection refused'*|*'connection reset'*|*'timed out'*|*'network is unreachable'*|*'fetch failed'*|*enotfound*|*eai_again*|*econnreset*|*etimedout*|*dns*) category='network-or-registry-failure' ;;
      *'error:'*|*uncaught*) category='resolver-error' ;;
    esac
    if [[ -n "$category" && "$seen" != *"|$category|"* ]]; then
      printf 'resolver-diagnostic-class=%s\n' "$category"
      seen+="$category|"
    fi
  done
  if [[ "$seen" == '|' ]]; then
    printf '%s\n' 'resolver-diagnostic-class=no-recognized-safe-category'
  fi
}

if ! ACTUAL_MANIFEST_SHA256="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"; then
  fail 'unable to hash resolver manifest'
fi
[[ "$ACTUAL_MANIFEST_SHA256" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'manifest bytes differ from the SHA-256 approved in the JIT'
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'
[[ -f "$ROOT/$SOURCE_DIR/index.ts" && ! -L "$ROOT/$SOURCE_DIR/index.ts" ]] || fail 'Edge source is missing or symlinked'
[[ -d "$ROOT/$SOURCE_DIR" && ! -L "$ROOT/$SOURCE_DIR" ]] || fail 'Edge source directory is missing or symlinked'
[[ -z "$(find "$ROOT/$SOURCE_DIR" -mindepth 1 -maxdepth 1 ! -name index.ts -print -quit)" ]] || fail 'Edge source directory contains unmanifested inputs'
[[ -d "$ROOT/tests" && ! -L "$ROOT/tests" ]] || fail 'tests directory is missing or symlinked'
[[ -d "$ROOT/$FIXTURE_DIR" && ! -L "$ROOT/$FIXTURE_DIR" ]] || fail 'isolated resolver fixture is missing or symlinked'
[[ -f "$ROOT/$FIXTURE_DIR/deno.json" && ! -L "$ROOT/$FIXTURE_DIR/deno.json" ]] || fail 'isolated Deno config is missing or symlinked'
[[ -z "$(find "$ROOT/$FIXTURE_DIR" -mindepth 1 -maxdepth 1 ! -name deno.json -print -quit)" ]] || fail 'resolver fixture contains unexpected files'
[[ -d "$ROOT/$WORKSPACE_DIR" && ! -L "$ROOT/$WORKSPACE_DIR" ]] || fail 'empty resolver workspace is missing or symlinked'
[[ -f "$ROOT/$WORKSPACE_DIR/.gitkeep" && ! -L "$ROOT/$WORKSPACE_DIR/.gitkeep" ]] || fail 'resolver workspace marker is missing or symlinked'
[[ -z "$(find "$ROOT/$WORKSPACE_DIR" -mindepth 1 -maxdepth 1 ! -name .gitkeep -print -quit)" ]] || fail 'resolver workspace is not empty'
[[ -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context" && ! -L "$ROOT/.context/evidencia" ]] || fail 'evidence log directory is missing or symlinked'
[[ "$(stat -c '%d' "$ROOT/$WORKSPACE_DIR")" == "$(stat -c '%d' "$ROOT/.context/evidencia")" ]] || fail 'staging and final lock paths are not on the same filesystem'
[[ ! -e "$ROOT/$RESULT_LOG" && ! -L "$ROOT/$RESULT_LOG" ]] || fail "result log path already exists: $RESULT_LOG"
[[ ! -e "$ROOT/$LOCK_STAGE" && ! -L "$ROOT/$LOCK_STAGE" ]] || fail "staging lock path already exists: $LOCK_STAGE"
[[ ! -e "$ROOT/$LOCK_FILE" && ! -L "$ROOT/$LOCK_FILE" ]] || fail "lock output path already exists: $LOCK_FILE"

set -o noclobber
exec >"$ROOT/$RESULT_LOG" 2>&1
set +o noclobber

sha256sum -c "$MANIFEST" || fail 'resolver input manifest mismatch'
docker image inspect "$DENO_IMAGE" >/dev/null 2>&1 || fail 'pinned Deno image is not local; pulls are not permitted'
assert_container_name_free
for volume in "$DENO_CACHE" "$WORKSPACE_VOLUME"; do
  assert_volume_name_free "$volume"
done

phase='isolated-deno-lock-resolution-with-registry-egress'
create_fresh_volume "$DENO_CACHE"
create_fresh_volume "$WORKSPACE_VOLUME"
if docker run --pull=never --platform linux/amd64 --log-driver none --name "$CONTAINER" --network bridge --read-only \
  --user 0:0 --cap-drop=ALL --security-opt no-new-privileges --pids-limit 256 --cpus=2 --memory=2g --memory-swap=2g \
  --tmpfs /tmp:rw,nosuid,size=512m \
  --mount "type=bind,src=$ROOT/$SOURCE_DIR,dst=/source,readonly" \
  --mount "type=bind,src=$ROOT/$FIXTURE_DIR,dst=/resolver,readonly" \
  --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache" \
  --mount "type=volume,src=$WORKSPACE_VOLUME,dst=/workspace" \
  --env HOME=/tmp --env DENO_DIR=/deno-cache --workdir /workspace --entrypoint /bin/sh \
  "$DENO_IMAGE" -lc 'set -eu; cp /source/index.ts /workspace/index.ts; cp /resolver/deno.json /workspace/deno.json; deno cache --node-modules-dir=auto --config=/workspace/deno.json --lock=/workspace/deno-edge-runtime-v1.74.3-r3.lock --frozen=false /workspace/index.ts; test -s /workspace/deno-edge-runtime-v1.74.3-r3.lock; grep -Eq '\''"version"[[:space:]]*:[[:space:]]*"4"'\'' /workspace/deno-edge-runtime-v1.74.3-r3.lock' \
  2>&1 | summarize_resolver_output; then
  :
else
  resolver_status=$?
  printf 'Deno resolver process exit=%s\n' "$resolver_status"
  fail 'Deno lock resolution failed; keep R3 container and volumes preserved for review'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$CONTAINER")" == '0' ]] || fail 'Deno resolver container exited non-zero'

phase='stage-and-verify-resolved-lock'
docker cp "$CONTAINER:/workspace/deno-edge-runtime-v1.74.3-r3.lock" "$ROOT/$LOCK_STAGE" >/dev/null 2>&1 || fail 'resolved lock could not be staged after successful container validation'
[[ -f "$ROOT/$LOCK_STAGE" && ! -L "$ROOT/$LOCK_STAGE" && -s "$ROOT/$LOCK_STAGE" ]] || fail 'staged lock is missing, empty, or symlinked'
grep -Eq '"version"[[:space:]]*:[[:space:]]*"4"' "$ROOT/$LOCK_STAGE" || fail 'staged lock is not Deno lock format v4'

phase='atomically-promote-validated-lock'
mv -n -- "$ROOT/$LOCK_STAGE" "$ROOT/$LOCK_FILE"
[[ ! -e "$ROOT/$LOCK_STAGE" && -f "$ROOT/$LOCK_FILE" && ! -L "$ROOT/$LOCK_FILE" ]] || fail 'validated lock was not atomically promoted to its final path'
printf 'Resolved lock SHA-256: %s\n' "$(sha256sum "$ROOT/$LOCK_FILE" | cut -d' ' -f1)"
printf 'Resolved lock output: %s\n' "$LOCK_FILE"
printf 'R3 lock resolver completed locally; integrated drill remains unauthorized.\n'
