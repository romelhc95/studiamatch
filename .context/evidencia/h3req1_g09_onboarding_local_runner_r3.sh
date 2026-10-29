#!/usr/bin/env bash
set -Eeuo pipefail
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly APP_IMAGE='studiamatch-h3req1:20261009-v3'
readonly APP_IMAGE_ID='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly PG_IMAGE_ID='sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly WEB_MODULES='h3req1-g08-web-node-modules-r1'
readonly MOCK_MODULES='h3req1-g08-mock-node-modules-20261010-r1'
readonly TOOLS_MODULES='h3req1-c03-integrated-miniflare-node-modules-20261006-r4'
readonly EXPECTED_WEB_DIGEST='ea36c13c72f0b1c13f2791118b4eb7ad89c17ba9ecbce44d413b794e6837e625'
readonly EXPECTED_TOOLS_DIGEST='637d7c16a194ec553e6cec3cd07efa1d06ba4a323a40f3ef72062f758e70088f'
readonly NETWORK='h3req1-g09-onboarding-net-20261010-r3'
readonly PG='h3req1-g09-onboarding-pg17-20261010-r3'
readonly APP='h3req1-g09-onboarding-app-20261010-r3'
readonly DB='h3_final_uat_onboarding_g09_20261010_r3'
readonly EVIDENCE_ROOT="$ROOT/.context/evidencia/h3req1_g09_onboarding_2026-10-10_r3"
readonly UAT_OUT="$EVIDENCE_ROOT/onboarding-r3"
readonly OUT="$ROOT/.context/evidencia/h3req1_final_build_2026-10-10_r2/out"
readonly RUN_LABEL='h3req1-g09-onboarding-20261010-r3'
readonly APP_RUN_LABEL='h3req1-g09-onboarding-20261010-r3'
phase='preflight'
pg_id=''
network_id=''
app_id=''
cleanup_stop=0
cd "$ROOT"
die() { printf 'phase=%s|error_code=%s\n' "$phase" "$1" >&2; exit 1; }
stop_exact() {
  local name="$1" expected_id="$2" expected_label="$3" current
  [[ -n "$expected_id" ]] || return 0
  current="$(docker inspect --type container --format '{{.Id}}|{{index .Config.Labels "com.studiamatch.h3.g09.run"}}|{{.State.Status}}' "$name" 2>/dev/null)" || return 0
  if [[ "$current" == "$expected_id|$expected_label|running" ]]; then
    docker stop --time 5 "$expected_id" >/dev/null 2>&1 || cleanup_stop=1
  fi
}
on_exit() {
  local status=$?
  trap - EXIT
  if (( status != 0 )); then
    stop_exact "$APP" "$app_id" "$APP_RUN_LABEL"
    printf 'halted_phase=%s|exit=%s|run=%s|stop_failed=%s|pg_preserved=1\n' "$phase" "$status" "$RUN_LABEL" "$cleanup_stop" >&2
  fi
}
trap on_exit EXIT
printf 'candidate=%s|branch=%s|head=%s|wip_entries=%s\n' "$ROOT" "$(git branch --show-current)" "$(git rev-parse HEAD)" "$(git status --short | wc -l | tr -d ' ')"
[[ "$(git branch --show-current)" == "$BRANCH" && "$(git rev-parse HEAD)" == "$HEAD" ]] || die CANDIDATE_IDENTITY_DRIFT
[[ "$(id -u)" != 0 ]] || die HOST_RUNNER_ROOT
[[ -d "$EVIDENCE_ROOT" && ! -e "$UAT_OUT" ]] || die EVIDENCE_SUBDIRECTORY_COLLISION
[[ -d "$OUT" && -f "$OUT/index.html" && -f "$OUT/admin/index.html" ]] || die MOCK_BUILD_INPUT_MISSING
[[ "$(docker image inspect --format '{{.Id}}' "$APP_IMAGE")" == "$APP_IMAGE_ID" ]] || die APP_IMAGE_ID_MISMATCH
[[ "$(docker image inspect --format '{{.Id}}' postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f)" == "$PG_IMAGE_ID" ]] || die PG_IMAGE_ID_MISMATCH
for volume in "$WEB_MODULES" "$MOCK_MODULES" "$TOOLS_MODULES"; do docker volume inspect "$volume" >/dev/null; done
if docker ps -a --format '{{.Names}}' | grep -Fxq "$APP"; then die APP_NAME_COLLISION; fi
if docker ps -a --format '{{.Names}}' | grep -Fxq "$PG"; then die PG_NAME_COLLISION; fi
if docker network ls --format '{{.Name}}' | grep -Fxq "$NETWORK"; then die NETWORK_NAME_COLLISION; fi
phase='prior-harness-evidence'
awk '$1=="h3_pg17_harness_ok"{found=1} END{exit !found}' "$ROOT/.context/evidencia/h3req1_g09_pg17_harness_2026-10-10_r1.txt" || die PG17_H3_HARNESS_MARKER_NOT_RECONCILED
grep -Fq 'h3_pg17_harness_ok' "$ROOT/.context/evidencia/h3req1_g09_pg17_harness_2026-10-10_r1.txt" || die PG17_H3_HARNESS_MARKER_MISSING
printf 'phase=prior-harness-evidence|error_code=EXIT_0_MARKER_CELL_RECOVERED\n'
phase='mock-build-integrity'
(cd "$ROOT/.context/evidencia/h3req1_final_build_2026-10-10_r2" && sha256sum --check --strict mock-out.sha256 >/tmp/h3req1_g09_uat_resume_r3_build_check.txt 2>&1)
[[ "$(find "$OUT" -type f | wc -l | tr -d ' ')" == 126 ]] || die MOCK_BUILD_FILE_COUNT_MISMATCH
printf 'phase=mock-build-integrity|error_code=126_FILES_HASH_VERIFIED\n'
phase='dependency-volume-integrity'
mkdir -p "$EVIDENCE_ROOT/runtime-logs" "$EVIDENCE_ROOT/input-manifests"
digest_output="$(docker run --rm --pull=never --platform linux/amd64 --network none --read-only --cap-drop=ALL --security-opt no-new-privileges:true --tmpfs /tmp:rw,nosuid,nodev,size=16m --mount "type=bind,src=$ROOT/tests,dst=/app/tests,readonly" --mount "type=volume,src=$WEB_MODULES,dst=/web/node_modules,readonly" --mount "type=volume,src=$MOCK_MODULES,dst=/mock/node_modules,readonly" --mount "type=volume,src=$TOOLS_MODULES,dst=/tools,readonly" --entrypoint /bin/sh "$APP_IMAGE" -c "node /app/tests/h3req1_c03_cache_digest.mjs web=/web/node_modules mock=/mock/node_modules tools=/tools/node_modules")"
# JavaScript is intentionally passed literally; Node evaluates its template strings.
# shellcheck disable=SC2016
node -e 'const d=JSON.parse(process.argv[1]); if(d.web!==process.argv[2]||d.tools!==process.argv[3]||!/^([a-f0-9]{64})$/.test(d.mock))process.exit(1);require("fs").writeFileSync(process.argv[4],`web=${d.web}\ntools=${d.tools}\nmock=${d.mock}\n`);console.log("phase=dependency-volume-integrity|error_code=WEB_TOOLS_MATCH_MOCK_DIGESTED")' "$digest_output" "$EXPECTED_WEB_DIGEST" "$EXPECTED_TOOLS_DIGEST" "$EVIDENCE_ROOT/input-manifests/module-digests-onboarding-r3.txt"
mkdir -p "$EVIDENCE_ROOT/runtime-logs" "$EVIDENCE_ROOT/input-manifests"
(cd "$ROOT" && find tests scripts/core web/functions web/src workers/admin-quota mock-server db/migrations db/seeds \
  -type d \( -name node_modules -o -name .git \) -prune -o -type f -print0 \
  | sort -z | xargs -0 sha256sum) > "$EVIDENCE_ROOT/input-manifests/source-onboarding-r3.sha256"
[[ -s "$EVIDENCE_ROOT/input-manifests/source-onboarding-r3.sha256" ]] || die SOURCE_INPUT_MANIFEST_EMPTY
printf 'phase=source-input-manifest|error_code=FILES_%s_SHA256_%s\n' \
  "$(wc -l < "$EVIDENCE_ROOT/input-manifests/source-onboarding-r3.sha256" | tr -d ' ')" \
  "$(sha256sum "$EVIDENCE_ROOT/input-manifests/source-onboarding-r3.sha256" | cut -d ' ' -f1)"
pg_password="$(od -An -N32 -tx1 /dev/urandom | tr -d '[:space:]')"
reset_token="h3-uat-$(od -An -N16 -tx1 /dev/urandom | tr -d '[:space:]')"
quota_key="$(od -An -N32 -tx1 /dev/urandom | tr -d '[:space:]')"
admin_password="Synthetic-Admin-$(od -An -N8 -tx1 /dev/urandom | tr -d '[:space:]')!A2"
user_password="Synthetic-User-$(od -An -N8 -tx1 /dev/urandom | tr -d '[:space:]')!U2"
auth_password="Synthetic-Auth-$(od -An -N8 -tx1 /dev/urandom | tr -d '[:space:]')!X2"
inactive_password="Synthetic-Inactive-$(od -An -N8 -tx1 /dev/urandom | tr -d '[:space:]')!I2"
[[ "$pg_password" =~ ^[a-f0-9]{64}$ && "$quota_key" =~ ^[a-f0-9]{64}$ ]] || die SYNTHETIC_CREDENTIAL_GENERATION_FAILED
phase='internal-network-create'
network_id="$(docker network create --internal --label "com.studiamatch.h3.g09.run=$RUN_LABEL" "$NETWORK")"
network_metadata="$(docker network inspect --format '{{.Id}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.g09.run"}}' "$NETWORK")"
IFS='|' read -r network_id network_internal network_label <<< "$network_metadata"
[[ "$network_internal" == true && "$network_label" == "$RUN_LABEL" ]] || die INTERNAL_NETWORK_IDENTITY_MISMATCH
printf 'phase=internal-network-create|error_code=INTERNAL_ONLY_NETWORK_READY\n'
phase='pg17-start'
docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$PG" --network "$NETWORK" --network-alias h3-final-pg --read-only --memory=2g --memory-swap=2g --cpus=2 --pids-limit=256 --tmpfs /tmp:rw,nosuid,nodev,size=64m --tmpfs /var/lib/postgresql/data:rw,nosuid,nodev,size=1g --tmpfs /var/run/postgresql:rw,nosuid,nodev,size=16m --env POSTGRES_PASSWORD="$pg_password" --label "com.studiamatch.h3.g09.run=$RUN_LABEL" --mount "type=bind,src=$ROOT/tests/sql,dst=/candidate/tests/sql,readonly" --mount "type=bind,src=$ROOT/db/migrations,dst=/candidate/db/migrations,readonly" --mount "type=bind,src=$ROOT/db/seeds,dst=/candidate/db/seeds,readonly" "postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f" >/dev/null
pg_id="$(docker inspect --type container --format '{{.Id}}' "$PG")"
pg_ready=0
for _ in $(seq 1 60); do
  if docker exec "$PG" pg_isready -U postgres -d postgres >/dev/null 2>&1; then pg_ready=1; break; fi
  sleep 1
done
[[ "$pg_ready" == 1 ]] || die PG17_NOT_READY
pg_metadata="$(docker inspect --type container --format '{{.Id}}|{{.Image}}|{{.State.Status}}|{{.HostConfig.NetworkMode}}|{{index .Config.Labels "com.studiamatch.h3.g09.run"}}' "$PG")"
[[ "$pg_metadata" == "$pg_id|$PG_IMAGE_ID|running|$NETWORK|$RUN_LABEL" ]] || die PG17_IDENTITY_MISMATCH
attachment="$(docker inspect --type container --format '{{with index .NetworkSettings.Networks "h3req1-g09-onboarding-net-20261010-r3"}}{{json .Aliases}}{{end}}' "$PG")"
[[ "$attachment" == *'"h3-final-pg"'* ]] || die PG_NETWORK_ALIAS_MISMATCH
printf 'phase=pg17-start|error_code=17_11_SYNTHETIC_PG_READY\n'
phase='pg17-database-create'
db_present="$(docker exec "$PG" psql -X -At -U postgres -d postgres -c "SELECT 1 FROM pg_database WHERE datname='$DB'")"
if [[ "$db_present" == 1 ]]; then
  printf 'phase=pg17-database-create|error_code=CLEAN_UAT_DATABASE_REUSED\n'
elif [[ -z "$db_present" ]]; then
  docker exec "$PG" createdb -U postgres "$DB"
  printf 'phase=pg17-database-create|error_code=CLEAN_UAT_DATABASE_CREATED\n'
else
  die PG17_DATABASE_LOOKUP_UNEXPECTED
fi
phase='synthetic-pg-password-rotation'
printf "ALTER ROLE postgres WITH PASSWORD '%s';\n" "$pg_password" | docker exec -i "$PG" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" >/tmp/h3req1_g09_uat_resume_r3_alter.out 2>&1
docker exec "$PG" pg_isready -U postgres -d "$DB" >/dev/null 2>&1 || die PG17_NOT_READY
printf 'phase=synthetic-pg-password-rotation|error_code=TEST_ONLY_CREDENTIAL_SET\n'
phase='pg17-version-check'
pg_version="$(docker exec "$PG" postgres --version)"
[[ "$pg_version" == 'postgres (PostgreSQL) 17.11'* ]] || die PG17_VERSION_MISMATCH
printf 'phase=pg17-version-check|error_code=17_11_DEBIAN_BUILD\n'
fixture_state="$(docker exec "$PG" psql -X -At -U postgres -d "$DB" -c "SELECT CASE WHEN to_regclass('public.course_editorial_audit') IS NULL THEN 'empty' ELSE 'seeded' END")"
if [[ "$fixture_state" == empty ]]; then
  phase='pg17-fixture-seed-after-tmpfs-reset'
  set +e
  docker exec "$PG" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" -f /candidate/tests/sql/h3_pg17_harness.sql > "$EVIDENCE_ROOT/pg17-harness-onboarding-r3.txt" 2>&1
  seed_status=$?
  set -e
  [[ "$seed_status" == 0 ]] || die PG17_H3_HARNESS_RESEED_FAILED
  for marker in h3_invitation_onboarding_harness_ok h3_onboarding_rbac_hardening_harness_ok h3_invitation_edge_runtime_harness_ok h3_pg17_harness_ok; do
    awk -v expected="$marker" '$1==expected {found=1} END{exit !found}' "$EVIDENCE_ROOT/pg17-harness-onboarding-r3.txt" || die PG17_H3_HARNESS_RESEED_MARKER_MISSING
  done
  printf 'phase=pg17-fixture-seed-after-tmpfs-reset|error_code=EXIT_0_ALL_4_MARKERS\n'
elif [[ "$fixture_state" == seeded ]]; then
  printf 'phase=pg17-fixture-seed-after-tmpfs-reset|error_code=SEEDED_FIXTURE_REUSED\n'
else
  die PG17_FIXTURE_STATE_UNEXPECTED
fi
phase='pg17-quota-migrations'
quota_state="$(docker exec "$PG" psql -X -At -U postgres -d "$DB" -c "SELECT CASE WHEN to_regclass('private.h3_admin_quota_events') IS NULL THEN 'missing-table' WHEN EXISTS (SELECT 1 FROM pg_proc WHERE prosrc LIKE '%H3_QUOTA_WRAPPER_V1%') THEN 'ready' ELSE 'missing-wrapper' END")"
if [[ "$quota_state" != ready ]]; then
  set +e
  docker exec "$PG" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" -f /candidate/db/migrations/20261002_h3_admin_quota_expand.sql > "$EVIDENCE_ROOT/quota-expand-migration-onboarding-r3.txt" 2>&1
  expand_status=$?
  set -e
  [[ "$expand_status" == 0 ]] || die PG17_QUOTA_EXPAND_MIGRATION_FAILED
  set +e
  docker exec "$PG" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" -f /candidate/db/migrations/20261002_h3_admin_quotas.sql > "$EVIDENCE_ROOT/quota-wrapper-migration-onboarding-r3.txt" 2>&1
  wrapper_status=$?
  set -e
  [[ "$wrapper_status" == 0 ]] || die PG17_QUOTA_WRAPPER_MIGRATION_FAILED
  quota_state="$(docker exec "$PG" psql -X -At -U postgres -d "$DB" -c "SELECT CASE WHEN to_regclass('private.h3_admin_quota_events') IS NULL THEN 'missing-table' WHEN EXISTS (SELECT 1 FROM pg_proc WHERE prosrc LIKE '%H3_QUOTA_WRAPPER_V1%') THEN 'ready' ELSE 'missing-wrapper' END")"
fi
[[ "$quota_state" == ready ]] || die PG17_QUOTA_MIGRATION_STATE_INCOMPLETE
printf 'phase=pg17-quota-migrations|error_code=EXPAND_AND_WRAPPER_READY\n'
phase='pg17-signed-gateway-migrations'
gateway_schema_state="$(docker exec "$PG" psql -X -At -U postgres -d "$DB" -c "SELECT CASE WHEN to_regclass('private.h3_admin_rpc_gateway_keys') IS NOT NULL AND to_regprocedure('public.admin_signed_rpc(text,jsonb,text)') IS NOT NULL THEN 'ready' ELSE 'missing' END")"
if [[ "$gateway_schema_state" != ready ]]; then
  set +e
  docker exec "$PG" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" -f /candidate/db/migrations/20261004_h3_admin_rpc_signed_gateway_expand.sql > "$EVIDENCE_ROOT/gateway-expand-migration-onboarding-r3.txt" 2>&1
  gateway_expand_status=$?
  set -e
  [[ "$gateway_expand_status" == 0 ]] || die PG17_GATEWAY_EXPAND_MIGRATION_FAILED
  set +e
  docker exec "$PG" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" -f /candidate/db/migrations/20261004_h3_admin_rpc_signed_gateway_payload_bound_wrapper.sql > "$EVIDENCE_ROOT/gateway-wrapper-migration-onboarding-r3.txt" 2>&1
  gateway_wrapper_status=$?
  set -e
  [[ "$gateway_wrapper_status" == 0 ]] || die PG17_GATEWAY_WRAPPER_MIGRATION_FAILED
  gateway_schema_state="$(docker exec "$PG" psql -X -At -U postgres -d "$DB" -c "SELECT CASE WHEN to_regclass('private.h3_admin_rpc_gateway_keys') IS NOT NULL AND to_regprocedure('public.admin_signed_rpc(text,jsonb,text)') IS NOT NULL THEN 'ready' ELSE 'missing' END")"
fi
[[ "$gateway_schema_state" == ready ]] || die PG17_GATEWAY_SCHEMA_INCOMPLETE
cat <<'SQL' | docker exec -i "$PG" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" > "$EVIDENCE_ROOT/gateway-synthetic-key-onboarding-r3.txt" 2>&1
INSERT INTO private.h3_admin_rpc_gateway_keys(key_id, project_ref, secret, valid_until)
VALUES ('local-runtime-k1', 'local', 'local-only-runtime-rpc-gateway-fixture-key-32-bytes', 'infinity'::timestamptz)
ON CONFLICT (key_id) DO UPDATE
SET project_ref = EXCLUDED.project_ref, secret = EXCLUDED.secret, valid_until = EXCLUDED.valid_until;
SQL
gateway_key_state="$(docker exec "$PG" psql -X -At -U postgres -d "$DB" -c "SELECT CASE WHEN EXISTS (SELECT 1 FROM private.h3_admin_rpc_gateway_keys WHERE key_id='local-runtime-k1' AND project_ref='local' AND valid_until > now()) THEN 'ready' ELSE 'missing' END")"
[[ "$gateway_key_state" == ready ]] || die PG17_GATEWAY_SYNTHETIC_KEY_MISSING
printf 'phase=pg17-signed-gateway-migrations|error_code=SCHEMA_AND_SYNTHETIC_KEY_READY\n'
phase='runtime-start'
docker run --pull=never --platform linux/amd64 --log-driver none -d --name "$APP" --entrypoint /bin/sh --network "$NETWORK" --read-only --memory=4g --memory-swap=4g --cpus=2 --pids-limit=512 --shm-size=128m --tmpfs /tmp:rw,nosuid,nodev,size=512m --tmpfs /run:rw,nosuid,nodev,size=16m --env HOME=/tmp --env NODE_ENV=test --env PORT=3332 --env MOCK_DB_HOST=h3-final-pg --env MOCK_DB_NAME="$DB" --env MOCK_DB_USER=postgres --env MOCK_DB_PASSWORD="$pg_password" --env MOCK_TOTP_CODE=123456 --env H3_TEST_RESET_TOKEN="$reset_token" --env MOCK_ADMIN_PASSWORD="$admin_password" --env MOCK_USER_PASSWORD="$user_password" --env MOCK_AUTH_PASSWORD="$auth_password" --env MOCK_INACTIVE_PASSWORD="$inactive_password" --env MOCK_QUOTA_TEST_ISOLATION=true --env MOCK_QUOTA_HMAC_KEY="$quota_key" --env MOCK_APP_ORIGIN=http://localhost:3330 --env MOCK_PUBLIC_ORIGIN=http://localhost:3332 --env MOCK_ADMIN_INVITE_REDIRECT_URL=http://localhost:3330/admin/auth/callback/ --env MOCK_ADMIN_INVITE_ALLOWED_REDIRECTS=http://localhost:3330/admin/auth/callback/ --env H3_RUNTIME_ROOT=/app --env H3_QUOTA_TOOLS=/tmp/h3-quota-runtime-tools --env H3_ADMIN_PASSWORD="$admin_password" --env H3_USER_PASSWORD="$user_password" --env H3_BASE_URL=http://localhost:3330 --env H3_MOCK_URL=http://localhost:3331 --env H3_PERIMETER_URL=http://localhost:3333 --env H3_PLAYWRIGHT_MODULE=/app/mock-server/node_modules/playwright --env H3_CHROMIUM_PATH=/ms-playwright/chromium-1228/chrome-linux64/chrome --env H3_EVIDENCE_DIR=/evidence/onboarding-r3 --env H3_REPO_ROOT=/app --env H3_QUOTA_TEST_ISOLATION=true --env H3_TEST_RESET_TOKEN="$reset_token" --env MOCK_QUOTA_HMAC_KEY="$quota_key" --label "com.studiamatch.h3.g09.run=$APP_RUN_LABEL" --mount "type=bind,src=$ROOT/tests,dst=/app/tests,readonly" --mount "type=bind,src=$ROOT/scripts/core,dst=/app/scripts/core,readonly" --mount "type=bind,src=$ROOT/db/migrations,dst=/app/db/migrations,readonly" --mount "type=bind,src=$ROOT/web/functions,dst=/app/web/functions,readonly" --mount "type=bind,src=$ROOT/web/src,dst=/app/web/src,readonly" --mount "type=bind,src=$ROOT/workers/admin-quota,dst=/app/workers/admin-quota,readonly" --mount "type=bind,src=$ROOT/mock-server,dst=/app/mock-server,readonly" --mount "type=bind,src=$OUT,dst=/app/web/out,readonly" --mount "type=volume,src=$WEB_MODULES,dst=/app/web/node_modules,readonly" --mount "type=volume,src=$MOCK_MODULES,dst=/app/mock-server/node_modules,readonly" --mount "type=volume,src=$TOOLS_MODULES,dst=/tmp/h3-quota-runtime-tools,readonly" --mount "type=bind,src=$EVIDENCE_ROOT,dst=/evidence" "$APP_IMAGE" -c 'mkdir -p /evidence/runtime-logs; node /app/mock-server/server.js >/evidence/runtime-logs/mock-server.log 2>&1 & node /app/tests/h3_local_runtime_server.mjs >/evidence/runtime-logs/local-runtime.log 2>&1 & wait' >/dev/null
app_id="$(docker inspect --format '{{.Id}}' "$APP")"
phase='runtime-readiness'
runtime_ready=0
for _ in $(seq 1 60); do
  if docker exec "$APP" node -e "Promise.all([fetch('http://127.0.0.1:3330/'),fetch('http://127.0.0.1:3331/healthz')]).then(async r=>{if(r[0].status!==200||!(r[0].headers.get('content-type')||'').includes('text/html')||r[1].status!==404)process.exit(1);console.log('ready')}).catch(()=>process.exit(1))" >/tmp/h3req1_g09_uat_resume_r3_runtime_probe.txt 2>&1; then runtime_ready=1; break; fi
  sleep 1
done
[[ "$runtime_ready" == 1 ]] || die PAGES_WORKER_OR_MOCK_RUNTIME_NOT_READY
printf 'phase=runtime-readiness|error_code=PAGES_ROOT_HTML_AND_MOCK_PROXY_OK\n'
phase='onboarding-source-preflight'
docker exec "$APP" node --check /app/tests/h3_invitation_uat.mjs >/dev/null
printf 'phase=onboarding-source-preflight|error_code=NODE_SYNTAX_VALID\n'
phase='mock-reset-preflight'
reset_status="$(docker exec "$APP" node -e "fetch('http://localhost:3331/__test/reset',{method:'POST',headers:{'x-h3-test-token':process.env.H3_TEST_RESET_TOKEN}}).then(r=>process.stdout.write(String(r.status))).catch(e=>process.stdout.write('ERR_'+(e.cause?.code||e.name)))")"
[[ "$reset_status" == 204 ]] || die MOCK_PROXY_RESET_PRECHECK_FAILED
printf 'phase=mock-reset-preflight|error_code=HTTP_204\n'
phase='onboarding-execution'
mkdir -p "$UAT_OUT"
set +e
onboarding_output="$(timeout --foreground --signal=TERM --kill-after=10s 1800s docker exec "$APP" node /app/tests/h3_invitation_uat.mjs 2>/dev/null)"
onboarding_status=$?
set -e
printf '%s' "$onboarding_output" | python3 -c 'import json,os,re,sys; from pathlib import Path
status=int(sys.argv[1]); output=Path(sys.argv[2]); output.parent.mkdir(parents=True,exist_ok=True); raw=sys.stdin.read()
expected=["INV-013","INV-008","INV-001","INV-002","INV-009","INV-007","INV-003","INV-004","INV-005","INV-012"]
try: data=json.loads(raw)
except Exception: data={}
if status!=0 or data.get("result")!="PASS":
 message=str(data.get("error","")); code="TIMEOUT" if status==124 else "BROWSER_TARGET_CLOSED" if "Target page, context or browser has been closed" in message else "PLAYWRIGHT_TIMEOUT" if "Timeout" in message or "waiting for" in message else "ONBOARDING_TEST_FAILED"
 result={"result":"FAIL","exit":status,"error_code":code,"retries":0}; output.write_text(json.dumps(result,indent=2)+"\n"); print(f"phase=onboarding-execution|exit={status}|error_code={code}"); sys.exit(1)
cases=data.get("cases")
if [x.get("id") for x in cases or []]!=expected or any(x.get("result")!="PASS" for x in cases) or data.get("minimumInviteSpacingMs")!=20100:
 result={"result":"FAIL","exit":0,"error_code":"CASE_SET_OR_PACING_MISMATCH","retries":0}; output.write_text(json.dumps(result,indent=2)+"\n"); print("phase=onboarding-evidence|exit=0|error_code=CASE_SET_OR_PACING_MISMATCH"); sys.exit(1)
result={"result":"PASS","cases":cases,"caseCount":len(cases),"minimumInviteSpacingMs":data["minimumInviteSpacingMs"],"retries":0,"environment":"isolated-synthetic-local"}
output.write_text(json.dumps(result,indent=2)+"\n"); print("phase=onboarding-evidence|error_code=10_OF_10_ZERO_RETRIES")' "$onboarding_status" "$UAT_OUT/onboarding-summary-r3.json"
[[ -s "$UAT_OUT/onboarding-summary-r3.json" ]] || die ONBOARDING_EVIDENCE_MISSING
phase='resource-cleanup'
app_meta="$(docker inspect --type container --format '{{.Id}}|{{index .Config.Labels "com.studiamatch.h3.g09.run"}}|{{.State.Status}}' "$APP")"
pg_meta="$(docker inspect --type container --format '{{.Id}}|{{index .Config.Labels "com.studiamatch.h3.g09.run"}}|{{.State.Status}}' "$PG")"
[[ "$app_meta" == "$app_id|$APP_RUN_LABEL|running" && "$pg_meta" == "$pg_id|$RUN_LABEL|running" ]] || die CLEANUP_IDENTITY_MISMATCH
docker rm -f "$app_id" "$pg_id" >/dev/null
docker network rm "$network_id" >/dev/null
trap - EXIT
printf 'phase=resource-cleanup|error_code=EXACT_FIXTURES_REMOVED_NO_VOLUMES\n'
printf 'result=PASS|image=%s|postgres=17.11|network=internal-only|env=synthetic-only|evidence=%s\n' "$APP_IMAGE" "$UAT_OUT"
