#!/usr/bin/env bash
set -Eeuo pipefail
readonly JIT='H3-CLOSE-03-INTEGRATED-2026-10-06-R4'
readonly MANIFEST='tests/h3req1-c03-integrated.sha256'
[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" && "${3:-}" == '--manifest-sha256' && $# -eq 4 ]] || { echo "Refusing to run: exact JIT $JIT and approved manifest SHA-256 required." >&2; exit 77; }
readonly APPROVED_MANIFEST_SHA256="${4:-}"
[[ "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] || { echo 'Refusing to run: invalid manifest SHA-256.' >&2; exit 77; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
exec 3>&1

readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EDGE_NETWORK='h3req1-c03-integrated-edge-20261006-r4'
readonly DATA_NETWORK='h3req1-c03-integrated-data-20261006-r4'
readonly PG='h3req1-c03-integrated-pg17-20261006-r4'
readonly POSTGREST='h3req1-c03-integrated-postgrest-20261006-r4'
readonly RUNTIME='h3req1-c03-integrated-runtime-20261006-r4'
readonly EDGE_ACTIVE='h3req1-c03-integrated-edge-active-20261006-r4'
readonly EDGE_SUSPENDED='h3req1-c03-integrated-edge-suspended-20261006-r4'
readonly TLS_VOLUME='h3req1-c03-integrated-tls-20261006-r4'
readonly TOOLS_BOOTSTRAP='h3req1-c03-bootstrap-miniflare-20261006-r4'
readonly WEB_BOOTSTRAP='h3req1-c03-bootstrap-pages-deps-20261006-r4'
readonly EDGE_BOOTSTRAP='h3req1-c03-bootstrap-edge-deps-20261006-r5'
readonly CACHE_VERIFY='h3req1-c03-dependency-cache-verify-20261006-r4'
readonly SNAPSHOT_BOOTSTRAP='h3req1-c03-source-snapshot-20261006-r4'
readonly SOURCE_SNAPSHOT='h3req1-c03-integrated-source-snapshot-20261006-r4'
readonly TOOLS_MODULES='h3req1-c03-integrated-miniflare-node-modules-20261006-r4'
readonly WEB_MODULES='h3req1-c03-integrated-pages-node-modules-20261006-r4'
readonly DENO_CACHE='h3req1-c03-integrated-edge-deno-cache-20261006-r5'
readonly EDGE_NODE_MODULES='h3req1-c03-integrated-edge-node-modules-20261006-r5'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log'
readonly PG_IMAGE='postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly POSTGREST_IMAGE='postgrest/postgrest@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly DENO_IMAGE='denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9'
readonly EDGE_IMAGE='supabase/edge-runtime:v1.74.3_amd64@sha256:cc355c3d0e9c063a351cad56d1c4c52a3c4d85aff4e1fad9d91688e75f9aad09'
readonly JWT_SEED='Studiamatch H3REQ1 C03 disposable PostgREST JWT fixture 2026-10-06'
readonly SERVICE_SEED='Studiamatch H3REQ1 C03 service fixture 2026-10-06'
readonly QUOTA_SEED='Studiamatch H3REQ1 C03 admin quota fixture 2026-10-06'
readonly RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"
phase='preflight'
on_error() {
  local status=$?
  printf 'Halted phase=%s exit=%s; no automatic cleanup/resume; preserve resources at their current state.\n' "$phase" "$status" >&2
  printf 'C03 integrated drill halted in phase=%s (exit=%s); no automatic cleanup/resume.\n' "$phase" "$status" >&3
}
on_signal() {
  local signal=$1 status
  case "$signal" in
    HUP) status=129 ;;
    INT) status=130 ;;
    TERM) status=143 ;;
    *) status=1 ;;
  esac
  printf 'Interrupted phase=%s signal=%s exit=%s; no automatic cleanup/resume; preserve resources at their current state.\n' "$phase" "$signal" "$status" >&2
  printf 'C03 integrated drill interrupted in phase=%s (signal=%s); no automatic cleanup/resume.\n' "$phase" "$signal" >&3
  trap - ERR HUP INT TERM
  exit "$status"
}
trap on_error ERR
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }
sanitize_dynamic_output() {
  local line normalized
  while IFS= read -r line || [[ -n "$line" ]]; do
    normalized="${line,,}"
    if [[ "$normalized" == *token* || "$normalized" == *secret* || "$normalized" == *password* \
      || "$normalized" == *authorization* || "$normalized" == *api_key* || "$normalized" == *apikey* \
      || "$normalized" == *service_role_key* || "$normalized" == *publishable_key* || "$normalized" == *anon_key* \
      || "$normalized" == *bearer* || "$normalized" == *eyj* ]]; then
      printf '[redacted sensitive output line]\n'
      continue
    fi
    printf '%s\n' "$line" | sed -E \
      -e 's/(eyJhbG[A-Za-z0-9_-]{10,}|sb_publishable_[A-Za-z0-9_-]{20,}|sb_secret_[A-Za-z0-9_-]{10,}|sbp_[A-Za-z0-9_-]{10,}|sk-(proj-)?[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|ghs_[A-Za-z0-9]{20,}|opencode_[A-Za-z0-9_-]{20,}|oc_[A-Za-z0-9_-]{30,})/[REDACTED credential-like value]/g' \
      -e 's/[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/[REDACTED JWT]/g' \
      -e 's#([A-Za-z][A-Za-z0-9+.-]*://)[^/@[:space:]]+(:[^/@[:space:]]*)?@#\1[REDACTED]@#g' \
      -e 's/(Bearer[[:space:]]+)[A-Za-z0-9._~+\/=-]+/\1[REDACTED]/Ig'
  done
}
summarize_bootstrap_output() {
  local line normalized category seen='|'
  while IFS= read -r line || [[ -n "$line" ]]; do
    normalized="${line,,}"
    category=''
    case "$normalized" in
      *permissiondenied*|*'permission denied'*|*eacces*|*eperm*) category='permission-denied' ;;
      *notcapable*) category='not-capable' ;;
      *'no such file or directory'*|*enoent*) category='missing-file-or-directory' ;;
      *'checksum mismatch'*|*'integrity check failed'*|*eintegrity*) category='integrity-or-checksum-failure' ;;
      *'lock file is out of date'*|*'lockfile configuration mismatch'*|*'lockfile is out of date'*) category='lockfile-resolution-failure' ;;
      *'module not found'*|*'specifier not found'*|*eresolve*) category='module-resolution-failure' ;;
      *'failed to resolve'*|*'error sending request'*|*'connection refused'*|*'connection reset'*|*'timed out'*|*'network is unreachable'*|*'fetch failed'*|*enotfound*|*eai_again*|*econnreset*|*etimedout*|*dns*) category='network-or-registry-failure' ;;
      *'npm err!'*|*'error:'*|*uncaught*) category='bootstrap-error' ;;
    esac
    if [[ -n "$category" && "$seen" != *"|$category|"* ]]; then
      printf 'bootstrap-diagnostic-class=%s\n' "$category"
      seen+="$category|"
    fi
  done
  if [[ "$seen" == '|' ]]; then
    printf '%s\n' 'bootstrap-diagnostic-class=no-recognized-safe-category'
  fi
}
if ! ACTUAL_MANIFEST_SHA256="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"; then fail 'unable to hash integrated manifest'; fi
[[ "$ACTUAL_MANIFEST_SHA256" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'manifest bytes differ from the SHA-256 approved in the JIT'
check_free_container() {
  local requested=$1 matches existing
  matches="$(docker ps -a --format '{{.Names}}' --filter "name=$requested")" || fail 'unable to list matching container names'
  while IFS= read -r existing; do
    [[ "$existing" != "$requested" ]] || fail "container name occupied: $requested"
  done <<< "$matches"
}
check_free_volume() {
  local requested=$1 matches existing
  matches="$(docker volume ls --format '{{.Name}}' --filter "name=$requested")" || fail "unable to list matching volume names: $requested"
  while IFS= read -r existing; do
    [[ "$existing" != "$requested" ]] || fail "volume name occupied: $requested"
  done <<< "$matches"
}
create_fresh_volume() {
  local requested=$1 created run_label
  check_free_volume "$requested"
  created="$(docker volume create \
    --label "com.studiamatch.h3.c03.jit=$JIT" \
    --label "com.studiamatch.h3.c03.manifest=$APPROVED_MANIFEST_SHA256" \
    --label "com.studiamatch.h3.c03.run=$RUN_NONCE" "$requested")" || fail "unable to create fresh volume: $requested"
  [[ "$created" == "$requested" ]] || fail "Docker returned an unexpected volume name: $requested"
  run_label="$(docker volume inspect -f '{{ index .Labels "com.studiamatch.h3.c03.run" }}' "$requested")" || fail "unable to verify new volume label: $requested"
  [[ "$run_label" == "$RUN_NONCE" ]] || fail "volume was not created by this exact invocation: $requested"
}
control() { docker exec "$RUNTIME" node /candidate/tests/h3req1_c03_integrated_runtime.mjs --control "$1" 2>&1 | sanitize_dynamic_output; }
wait_control() {
  local command=$1 i
  for ((i=0; i<60; i+=1)); do if control "$command" >/dev/null 2>&1; then return 0; fi; sleep 1; done
  fail "runtime state timeout: $command"
}
run_sql() {
  local path=$1 label=$2
  docker exec "$PG" psql -X -q -U postgres -d h3_c03_chain -v ON_ERROR_STOP=1 -o /dev/null -f "/candidate/$path" >/dev/null 2>&1 || fail "SQL gate failed: $label"
  printf '%s PASS (psql exit=0)\n' "$label"
}
start_edge() {
  local name=$1 alias=$2 safe=$3
  docker run --platform linux/amd64 --log-driver none -d --name "$name" --network "$EDGE_NETWORK" --network-alias "$alias" --read-only \
    --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
    --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache,readonly" \
    --mount "type=volume,src=$EDGE_NODE_MODULES,dst=/candidate/supabase/functions/admin-invite/node_modules,readonly" \
    --mount "type=volume,src=$TLS_VOLUME,dst=/run/c03-certs,readonly" \
    --tmpfs /tmp:rw,noexec,nosuid,size=256m \
    --env DENO_DIR=/deno-cache --env DENO_CERT=/run/c03-certs/ca.pem \
    --env SUPABASE_URL=https://local.supabase.co:5443/ \
    --env NEXT_SUPABASE_SECRET_KEY="sb_secret_$(printf '%s' "$SERVICE_SEED" | sha256sum | cut -d' ' -f1)" \
    --env ADMIN_QUOTA_HMAC_KEY="$(printf '%s' "$QUOTA_SEED" | sha256sum | cut -d' ' -f1)" \
    --env ADMIN_INVITE_SAFE_SUSPEND="$safe" \
    --env ADMIN_INVITE_ALLOWED_ORIGINS=https://admin.local.test \
    --env ADMIN_INVITE_ALLOWED_REDIRECTS=https://admin.local.test/admin/auth/callback/ \
    --env ADMIN_INVITE_REDIRECT_URL=https://admin.local.test/admin/auth/callback/ \
    --env ADMIN_INVITE_RECOVERY_REDIRECT_URL=https://admin.local.test/admin/auth/callback/ \
    --env APP_ENV=development "$EDGE_IMAGE" start --main-service /candidate/tests/h3req1-c03-edge-main -p 9000 >/dev/null 2>&1
}

[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'
[[ -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context" && ! -L "$ROOT/.context/evidencia" ]] || fail 'evidence log directory is missing or symlinked'
[[ ! -e "$ROOT/$RESULT_LOG" && ! -L "$ROOT/$RESULT_LOG" ]] || fail "result log path already exists: $RESULT_LOG"
set -o noclobber
exec >"$ROOT/$RESULT_LOG" 2>&1
set +o noclobber
sha256sum -c "$MANIFEST" || fail 'integrated manifest mismatch'
for image in "$PG_IMAGE" "$POSTGREST_IMAGE" "$NODE_IMAGE" "$DENO_IMAGE" "$EDGE_IMAGE"; do docker image inspect "$image" >/dev/null 2>&1 || fail "pinned image not local (no pulls): $image"; done
for name in "$PG" "$POSTGREST" "$RUNTIME" "$EDGE_ACTIVE" "$EDGE_SUSPENDED" "$TOOLS_BOOTSTRAP" "$WEB_BOOTSTRAP" "$EDGE_BOOTSTRAP" "$CACHE_VERIFY" "$SNAPSHOT_BOOTSTRAP"; do check_free_container "$name"; done
for volume in "$SOURCE_SNAPSHOT" "$TLS_VOLUME" "$TOOLS_MODULES" "$WEB_MODULES" "$DENO_CACHE" "$EDGE_NODE_MODULES"; do
  check_free_volume "$volume"
done
for network in "$EDGE_NETWORK" "$DATA_NETWORK"; do
  docker network inspect "$network" >/dev/null 2>&1 && fail "internal network name occupied: $network"
done

phase='immutable-manifest-verified-source-snapshot'
create_fresh_volume "$SOURCE_SNAPSHOT"
mapfile -t SNAPSHOT_FILES < <(awk '{print $2}' "$MANIFEST")
for source_path in "${SNAPSHOT_FILES[@]}"; do
  [[ "$source_path" =~ ^[A-Za-z0-9._/-]+$ && "$source_path" != /* && "$source_path" != '.' && "$source_path" != "$MANIFEST" && "/$source_path/" != *"/../"* ]] || fail "unsafe path in approved manifest: $source_path"
done
if ! tar -C "$ROOT" --no-recursion -cf - -- "${SNAPSHOT_FILES[@]}" "$MANIFEST" |
  docker run --platform linux/amd64 --interactive --log-driver none --name "$SNAPSHOT_BOOTSTRAP" --network none --read-only \
    --tmpfs /tmp:rw,nosuid,size=32m --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/snapshot" \
    --env H3_C03_MANIFEST_SHA256="$APPROVED_MANIFEST_SHA256" \
    "$NODE_IMAGE" sh -lc 'set -eu; test -z "$(find /snapshot -mindepth 1 -print -quit)"; tar -xf - -C /snapshot; cd /snapshot; actual="$(sha256sum tests/h3req1-c03-integrated.sha256 | cut -d" " -f1)"; test "$actual" = "$H3_C03_MANIFEST_SHA256"; if find . -type l -print -quit | grep -q .; then exit 41; fi; sha256sum -c tests/h3req1-c03-integrated.sha256; test ! -e supabase/functions/admin-invite/package.json; cp tests/h3req1-c03-edge-lock-resolver/deno.json supabase/functions/admin-invite/deno.json; cp tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock supabase/functions/admin-invite/deno.lock; cmp tests/h3req1-c03-edge-lock-resolver/deno.json supabase/functions/admin-invite/deno.json; cmp tests/h3req1-c03-edge-lock-output-r3/deno-edge-runtime-v1.74.3-r3.lock supabase/functions/admin-invite/deno.lock; mkdir -p supabase/functions/admin-invite/node_modules; test -z "$(find supabase/functions/admin-invite/node_modules -mindepth 1 -print -quit)"' \
    >/dev/null 2>&1; then
  fail 'manifest-pinned source snapshot failed verification; output suppressed'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$SNAPSHOT_BOOTSTRAP")" == '0' ]] || fail 'source snapshot verification exited non-zero'

phase='isolated-npm-tool-bootstrap-with-registry-egress'
create_fresh_volume "$TOOLS_MODULES"
if docker run --platform linux/amd64 --log-driver none --name "$TOOLS_BOOTSTRAP" --network bridge --read-only \
  --tmpfs /tmp:rw,nosuid,size=512m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/source,readonly" \
  --mount "type=volume,src=$TOOLS_MODULES,dst=/out" --workdir /out \
  --env HOME=/tmp --env npm_config_cache=/tmp/npm-cache \
  "$NODE_IMAGE" sh -lc 'cp /source/tests/h3req1-c03-bootstrap/package.json /source/tests/h3req1-c03-bootstrap/package-lock.json /out/ && npm ci --no-audit --no-fund --foreground-scripts --registry=https://registry.npmjs.org/' \
  2>&1 | summarize_bootstrap_output; then
  :
else
  bootstrap_status=$?
  printf 'Miniflare/workerd bootstrap process exit=%s\n' "$bootstrap_status"
  fail 'Miniflare/workerd npm bootstrap failed; safe diagnostic classes are retained in the R4 run log'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$TOOLS_BOOTSTRAP")" == '0' ]] || fail 'Miniflare/workerd npm bootstrap failed'

phase='isolated-npm-pages-dependency-bootstrap-with-registry-egress'
create_fresh_volume "$WEB_MODULES"
if docker run --platform linux/amd64 --log-driver none --name "$WEB_BOOTSTRAP" --network bridge --read-only \
  --tmpfs /tmp:rw,nosuid,size=512m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/source,readonly" \
  --mount "type=volume,src=$WEB_MODULES,dst=/out" --workdir /out \
  --env HOME=/tmp --env npm_config_cache=/tmp/npm-cache \
  "$NODE_IMAGE" sh -lc 'cp /source/web/package.json /source/web/package-lock.json /out/ && cp -a /source/web/vendor /out/vendor && npm ci --omit=dev --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org/' \
  2>&1 | summarize_bootstrap_output; then
  :
else
  bootstrap_status=$?
  printf 'Pages dependency bootstrap process exit=%s\n' "$bootstrap_status"
  fail 'Pages dependency npm bootstrap failed; safe diagnostic classes are retained in the R4 run log'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$WEB_BOOTSTRAP")" == '0' ]] || fail 'Pages bundle dependency npm bootstrap failed'

phase='isolated-deno-edge-dependency-bootstrap-with-registry-egress'
create_fresh_volume "$DENO_CACHE"
create_fresh_volume "$EDGE_NODE_MODULES"
if docker run --platform linux/amd64 --log-driver none --name "$EDGE_BOOTSTRAP" --network bridge --read-only \
  --tmpfs /tmp:rw,nosuid,size=512m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/source,readonly" \
  --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache" \
  --mount "type=volume,src=$EDGE_NODE_MODULES,dst=/source/supabase/functions/admin-invite/node_modules" \
  --env HOME=/tmp --env DENO_DIR=/deno-cache --workdir /source/supabase/functions/admin-invite \
  "$DENO_IMAGE" cache --node-modules-dir=auto --config=/source/supabase/functions/admin-invite/deno.json --lock=/source/supabase/functions/admin-invite/deno.lock --frozen /source/supabase/functions/admin-invite/index.ts \
  2>&1 | summarize_bootstrap_output; then
  :
else
  bootstrap_status=$?
  printf 'Deno Edge bootstrap process exit=%s\n' "$bootstrap_status"
  fail 'fresh Edge dependency bootstrap failed; safe diagnostic classes are retained in the R4 run log'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$EDGE_BOOTSTRAP")" == '0' ]] || fail 'fresh Edge dependency bootstrap failed'

phase='verify-dependency-volume-content-before-runtime'
if ! DEPENDENCY_DIGESTS="$(docker run --platform linux/amd64 --log-driver none --name "$CACHE_VERIFY" --network none --read-only \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/source,readonly" \
  --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache,readonly" \
  --mount "type=volume,src=$EDGE_NODE_MODULES,dst=/edge-node-modules,readonly" \
  --mount "type=volume,src=$TOOLS_MODULES,dst=/tools,readonly" \
  --mount "type=volume,src=$WEB_MODULES,dst=/web-deps,readonly" \
  "$NODE_IMAGE" node /source/tests/h3req1_c03_cache_digest.mjs deno-cache=/deno-cache edge-node-modules=/edge-node-modules \
  miniflare-node-modules=/tools/node_modules pages-node-modules=/web-deps/node_modules 2>/dev/null)"; then
  fail 'dependency-volume content verification failed; output suppressed'
fi
[[ "$(docker inspect -f '{{.State.ExitCode}}' "$CACHE_VERIFY")" == '0' ]] || fail 'dependency-volume content verifier exited non-zero'
readonly DEPENDENCY_DIGEST_PATTERN='^\{"deno-cache":"[a-f0-9]{64}","edge-node-modules":"[a-f0-9]{64}","miniflare-node-modules":"[a-f0-9]{64}","pages-node-modules":"[a-f0-9]{64}"\}$'
[[ "$DEPENDENCY_DIGESTS" =~ $DEPENDENCY_DIGEST_PATTERN ]] || fail 'dependency-volume digest output does not match the exact safe schema'
printf 'Locked dependency volume SHA-256: %s\n' "$DEPENDENCY_DIGESTS"

phase='isolated-workerd-bootstrap'
docker network create --internal "$EDGE_NETWORK" >/dev/null
docker network create --internal "$DATA_NETWORK" >/dev/null
create_fresh_volume "$TLS_VOLUME"
docker run --platform linux/amd64 --log-driver none -d --name "$RUNTIME" --network "$EDGE_NETWORK" --network-alias local.supabase.co --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m --tmpfs /run/c03-private:rw,noexec,nosuid,size=8m \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" \
  --mount "type=volume,src=$TLS_VOLUME,dst=/run/c03-certs" \
  --mount "type=volume,src=$TOOLS_MODULES,dst=/tools,readonly" \
  --mount "type=volume,src=$WEB_MODULES,dst=/web-deps,readonly" \
  --mount "type=volume,src=$DENO_CACHE,dst=/deno-cache,readonly" \
  --mount "type=volume,src=$EDGE_NODE_MODULES,dst=/edge-node-modules,readonly" \
  --env H3_C03_ROOT=/candidate --env H3_C03_TOOLS_ROOT=/tools --env H3_C03_CERTS_ROOT=/run/c03-certs \
  --env H3_C03_WEB_DEPS_ROOT=/web-deps --env H3_C03_PRIVATE_ROOT=/run/c03-private \
  --env H3_C03_EXPECTED_DEPENDENCY_DIGESTS="$DEPENDENCY_DIGESTS" \
  --env H3_C03_MANIFEST_SHA256="$APPROVED_MANIFEST_SHA256" \
  "$NODE_IMAGE" node /candidate/tests/h3req1_c03_integrated_runtime.mjs >/dev/null 2>&1
wait_control healthz
docker network connect "$DATA_NETWORK" "$RUNTIME"

phase='fresh-pg17-schema-and-synthetic-fixtures'
readonly PG_PASSWORD="$(od -An -N32 -tx1 /dev/urandom | tr -d '[:space:]')"
[[ "$PG_PASSWORD" =~ ^[a-f0-9]{64}$ ]] || fail 'synthetic PostgreSQL password generation failed'
docker run --platform linux/amd64 --log-driver none -d --name "$PG" --network "$DATA_NETWORK" --network-alias h3req1-c03-pg17 --read-only \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=1g --tmpfs /var/run/postgresql:rw,noexec,nosuid,size=16m \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --env POSTGRES_HOST_AUTH_METHOD=scram-sha-256 --env POSTGRES_PASSWORD="$PG_PASSWORD" \
  --env POSTGRES_DB=h3_c03_chain --env PGDATA=/var/lib/postgresql/data/pgdata \
  --mount "type=volume,src=$SOURCE_SNAPSHOT,dst=/candidate,readonly" "$PG_IMAGE" >/dev/null
for _ in {1..60}; do if docker exec "$PG" pg_isready -U postgres -d h3_c03_chain >/dev/null 2>&1; then break; fi; sleep 1; done
docker exec "$PG" pg_isready -U postgres -d h3_c03_chain >/dev/null 2>&1 || fail 'fresh PG17 not ready'
run_sql tests/sql/h3_from_h2_pro_pg17_harness.sql 'H2-Pro-to-H3 schema bootstrap'
run_sql tests/sql/h3req1_c03_integrated_extension_setup.sql 'integrated-only quota and signed-dispatcher schema setup'
run_sql tests/sql/h3req1_c03_integrated_setup.sql 'synthetic in-flight/editorial fixture'

phase='isolated-postgrest'
JWT_SECRET="$(printf '%s' "$JWT_SEED" | sha256sum | cut -d' ' -f1)"
docker run --platform linux/amd64 --log-driver none -d --name "$POSTGREST" --network "$DATA_NETWORK" --network-alias h3req1-c03-postgrest --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --env PGRST_DB_URI="postgres://postgres:${PG_PASSWORD}@h3req1-c03-pg17:5432/h3_c03_chain" \
  --env PGRST_DB_SCHEMAS=public --env PGRST_DB_ANON_ROLE=anon \
  --env PGRST_DB_PRE_REQUEST=public.h3_admin_rpc_signed_gateway_pre_request \
  --env PGRST_JWT_SECRET="$JWT_SECRET" --env PGRST_DB_EXTRA_SEARCH_PATH=public,extensions "$POSTGREST_IMAGE" >/dev/null
for _ in {1..60}; do
  if docker exec "$RUNTIME" node -e "fetch('http://h3req1-c03-postgrest:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$RUNTIME" node -e "fetch('http://h3req1-c03-postgrest:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1 || fail 'isolated PostgREST not ready'

phase='real-edge-invite-held-after-reservation'
start_edge "$EDGE_ACTIVE" h3req1-c03-edge-active false
wait_control edge-active-ready
control login
control trigger-inflight
run_sql tests/sql/h3req1_c03_integrated_assert_inflight.sql 'reservation confirmed before Auth hold'

phase='safe-suspend-and-runtime-denials'
run_sql db/rollback/h3req1_safe_suspend.sql 'persistent safe suspension'
start_edge "$EDGE_SUSPENDED" h3req1-c03-edge-suspended true
wait_control edge-suspended-ready
control pages-suspended
control edge-suspended
control signed-dispatcher
run_sql tests/sql/h3req1_c03_integrated_assert_suspended.sql 'suspended ACL/data/quota/audit assertions'

phase='in-flight-finalization-under-suspension'
control release-inflight
run_sql tests/sql/h3req1_c03_integrated_assert_completed_suspended.sql 'finalizer completed while SQL suspended'

phase='same-database-safe-resume'
run_sql db/rollback/h3req1_safe_resume.sql 'persistent safe resume on a new psql connection'
run_sql tests/sql/h3req1_c03_integrated_assert_recovered.sql 'recovered ACL/data/audit assertions'

phase='edge-first-pages-last-recovery-smoke'
control recovery
run_sql tests/sql/h3req1_c03_integrated_assert_final.sql 'final idempotency/quota/audit assertions'
control finish

phase='verify-runtime-graceful-shutdown'
for _ in {1..100}; do
  [[ "$(docker inspect -f '{{.State.Status}}' "$RUNTIME")" == 'exited' ]] && break
  sleep 0.2
done
RUNTIME_STATE="$(docker inspect -f '{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}' "$RUNTIME")"
[[ "$RUNTIME_STATE" == 'exited|0|false' ]] || fail "runtime did not complete graceful shutdown: $RUNTIME_STATE"
phase='stop-new-services-preserve-resources'
docker stop --time 30 "$EDGE_SUSPENDED" "$EDGE_ACTIVE" "$POSTGREST" "$PG" >/dev/null
for name in "$EDGE_SUSPENDED" "$EDGE_ACTIVE" "$RUNTIME" "$POSTGREST" "$PG"; do
  state="$(docker inspect -f '{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}' "$name")"
  IFS='|' read -r status exit_code oom_killed <<< "$state"
  [[ "$status" == 'exited' && "$oom_killed" == 'false' && "$exit_code" != '137' ]] || fail "unclean shutdown for $name: $state"
done
PASS_LINE='C03 integrated drill: PASS (local synthetic scope only; no Development GO).'
printf '%s\n' "$PASS_LINE" \
  'Containers and volumes remain preserved; stopping PG17 discards its tmpfs database. No container/image/volume removal was performed.' \
  "Sanitized run log: $RESULT_LOG"
if ! grep -Fqx "$PASS_LINE" "$ROOT/$RESULT_LOG"; then
  printf 'NO-GO: result log did not retain the final PASS record.\n' >&3
  exit 1
fi
trap - ERR
printf '%s\n' "$PASS_LINE" "Sanitized run log: $RESULT_LOG" >&3
exec 3>&-
