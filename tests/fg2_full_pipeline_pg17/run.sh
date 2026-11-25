#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURE="$ROOT/tests/fg2_full_pipeline_pg17"
readonly ROOT FIXTURE
readonly PG_IMAGE='postgres:17'
readonly PGRST_IMAGE='postgrest/postgrest:v13.0.7'
readonly APP_IMAGE="${FG2_FIXTURE_APP_IMAGE:-studiamatch-h3req1:20261009-v3}"
readonly PG_IMAGE_ID='sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly PGRST_IMAGE_ID='sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228'
readonly APP_IMAGE_ID="${FG2_FIXTURE_APP_IMAGE_ID:-sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63}"
readonly DATABASE='fg2_full_pipeline_fixture'

suffix="$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')"
net="fg2-full-${suffix}-net"
pg="fg2-full-${suffix}-pg17"
pgrst="fg2-full-${suffix}-postgrest"
out="$(mktemp -d /tmp/fg2-full-pg17.XXXXXX)"
run_dir="$out/run"
mkdir "$run_dir"
chmod 711 "$out"
chmod 1777 "$run_dir"
jwt_secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
pg_password="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
fixture_publishable_key="sb_publishable_$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
fixture_secret_key="sb_secret_$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
source_sha="${FG2_FIXTURE_SOURCE_SHA:-467406edcb1ea70ada36036c73d024110ed4a5a5}"
if [[ ! "$source_sha" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'phase=fixture_configuration|result=FAIL|code=invalid_source_sha\n' >&2
  exit 2
fi
manifest="$run_dir/fg2-cohort-manifest.json"
events="$run_dir/fg2-http-events.jsonl"
touch "$manifest" "$events"
chmod 666 "$manifest" "$events"

net_id=''
pg_id=''
pgrst_id=''

fail() {
  printf 'phase=%s|result=FAIL|code=%s\n' "$1" "$2"
  exit 2
}

cleanup() {
  local status=$?
  trap - EXIT
  local containers=()
  [[ -n "$pgrst_id" ]] && containers+=("$pgrst_id")
  [[ -n "$pg_id" ]] && containers+=("$pg_id")
  if ((${#containers[@]})); then docker rm -f "${containers[@]}" >/dev/null 2>&1 || true; fi
  [[ -n "$net_id" ]] && docker network rm "$net_id" >/dev/null 2>&1 || true
  if (( status == 0 )); then
    rm -rf "$out"
  else
    printf 'phase=fixture_diagnostics|result=RETAINED|path=%s\n' "$out"
  fi
  exit "$status"
}
trap cleanup EXIT

images=("$PG_IMAGE" "$PGRST_IMAGE" "$APP_IMAGE")
expected_image_ids=("$PG_IMAGE_ID" "$PGRST_IMAGE_ID" "$APP_IMAGE_ID")
for index in 0 1 2; do
  image="${images[$index]}"
  expected="${expected_image_ids[$index]}"
  actual="$(docker image inspect --format '{{.Id}}' "$image" 2>/dev/null)" \
    || fail preflight IMAGE_PIN_NOT_LOCAL
  [[ "$actual" == "$expected" ]] || fail preflight IMAGE_PIN_MISMATCH
done
for name in "$net" "$pg" "$pgrst"; do
  if docker network inspect "$name" >/dev/null 2>&1 || docker container inspect "$name" >/dev/null 2>&1; then
    fail preflight RANDOM_RESOURCE_COLLISION
  fi
done

net_id="$(docker network create --internal --driver bridge "$net")"
pg_id="$(docker run --pull=never --detach --name "$pg" --network "$net" --network-alias pg \
  --cpus 2 --memory 4g --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=2g \
  --env POSTGRES_DB="$DATABASE" --env POSTGRES_USER=postgres --env POSTGRES_PASSWORD="$pg_password" \
  --mount "type=bind,src=$ROOT/tests/sql/h3req1_pipeline_postgrest_pg17_setup_r1.sql,dst=/fixture/setup.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260430_intermediate_tables_ddl.sql,dst=/fixture/20260430_intermediate_tables_ddl.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260505_add_provider_tracking.sql,dst=/fixture/20260505_add_provider_tracking.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260808_fase10_8_atomic_cleansing_provenance.sql,dst=/fixture/20260808_fase10_8_atomic_cleansing_provenance.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260525_fase113_pro_rls_and_rpc_sync.sql,dst=/fixture/20260525_fase113_pro_rls_and_rpc_sync.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20261125152449_fg2_enrichment_modality_provenance.sql,dst=/fixture/20261125152449_fg2_enrichment_modality_provenance.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260825_h2_editorial_layer.sql,dst=/fixture/20260825_h2_editorial_layer.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260825_h2_editorial_layer_grants_fix.sql,dst=/fixture/20260825_h2_editorial_layer_grants_fix.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260825_h2_editorial_layer_start_date_view_fix.sql,dst=/fixture/20260825_h2_editorial_layer_start_date_view_fix.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260825_h2_editorial_layer_allowlist_fix.sql,dst=/fixture/20260825_h2_editorial_layer_allowlist_fix.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260826_h2_editorial_layer_forward_fix.sql,dst=/fixture/20260826_h2_editorial_layer_forward_fix.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260826_h2_security_advisor_remediation.sql,dst=/fixture/20260826_h2_security_advisor_remediation.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260826_h2_seed_editorial_field_definitions.sql,dst=/fixture/20260826_h2_seed_editorial_field_definitions.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260826_h2_public_effective_view_public_fields_fix.sql,dst=/fixture/20260826_h2_public_effective_view_public_fields_fix.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260827_h2_pro_expand_schema_compat.sql,dst=/fixture/20260827_h2_pro_expand_schema_compat.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/fixture_schema.sql,dst=/fixture/fixture_schema.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/seed_profiles.sql,dst=/fixture/seed_profiles.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/seed_admin.sql,dst=/fixture/seed_admin.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/assert_state.sql,dst=/fixture/assert_state.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/prepare_refresh.sql,dst=/fixture/prepare_refresh.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/prepare_post272_recovery.sql,dst=/fixture/prepare_post272_recovery.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/assert_post272_recovery.sql,dst=/fixture/assert_post272_recovery.sql,readonly" \
  --mount "type=bind,src=$FIXTURE/inject_one_cleansing_failure.sql,dst=/fixture/inject_one_cleansing_failure.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260531_fase121_auto_generated.sql,dst=/fixture/20260531_fase121_auto_generated.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20261120120000_fg2_profile_onboarding_state.sql,dst=/fixture/20261120120000_fg2_profile_onboarding_state.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260828_h3_admin_auth.sql,dst=/fixture/20260828_h3_admin_auth.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260830_h3_expanded_contract.sql,dst=/fixture/20260830_h3_expanded_contract.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260828_h3_admin_course_queue_view.sql,dst=/fixture/20260828_h3_admin_course_queue_view.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260828_h3_admin_queue_rpc.sql,dst=/fixture/20260828_h3_admin_queue_rpc.sql,readonly" \
  --mount "type=bind,src=$ROOT/db/migrations/20260927_h3_admin_queue_facets_filter.sql,dst=/fixture/20260927_h3_admin_queue_facets_filter.sql,readonly" \
  "$PG_IMAGE")"

ready=0
for _ in $(seq 1 45); do
  # pg_isready can accept the temporary initialization server before
  # POSTGRES_DB has been created. Require a successful query on the target DB.
  if docker exec "$pg" psql -X -U postgres -d "$DATABASE" -Atqc 'SELECT 1' >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
(( ready == 1 )) || fail pg17 PG17_READINESS_TIMEOUT
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/setup.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20261125152449_fg2_enrichment_modality_provenance.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/fixture_schema.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20260531_fase121_auto_generated.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20261120120000_fg2_profile_onboarding_state.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/seed_profiles.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20260828_h3_admin_auth.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20260830_h3_expanded_contract.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20260828_h3_admin_course_queue_view.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20260828_h3_admin_queue_rpc.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/20260927_h3_admin_queue_facets_filter.sql >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/seed_admin.sql >/dev/null
printf 'phase=pg17_migrations_and_seed|result=PASS|postgres=17|admin_rpc=versioned\n'

pgrst_id="$(docker run --pull=never --detach --name "$pgrst" --network "$net" --network-alias postgrest \
  --cpus 1 --memory 1g --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --env PGRST_DB_URI="postgres://postgres:${pg_password}@pg:5432/${DATABASE}" \
  --env PGRST_DB_SCHEMAS=public --env PGRST_DB_ANON_ROLE=anon \
  --env PGRST_DB_EXTRA_SEARCH_PATH=public,extensions \
  --env PGRST_JWT_SECRET="$jwt_secret" --env PGRST_LOG_LEVEL=error \
  "$PGRST_IMAGE")"

common_docker_args=(
  --pull=never --rm --network "$net" --cpus 2 --memory 4g --shm-size 512m
  --read-only --tmpfs "/tmp:rw,noexec,nosuid,size=256m" --user 1000:1000 --workdir /workspace
  --env PYTHONDONTWRITEBYTECODE=1 --env PYTHON_DOTENV_DISABLED=1
  --env PYTHONPATH=/workspace/tests/fg2_full_pipeline_pg17:/workspace/scripts:/workspace
  --env PYTHONUNBUFFERED=1 --env SUPABASE_URL=http://postgrest:3000
  --env NEXT_PUBLIC_SUPABASE_URL=http://postgrest:3000
  --env FG2_FIXTURE_JWT_SECRET="$jwt_secret"
  --env FG2_FIXTURE_PUBLISHABLE_API_KEY="$fixture_publishable_key"
  --env FG2_FIXTURE_SECRET_API_KEY="$fixture_secret_key"
  --env FG2_FIXTURE_PROVIDER_ADAPTER=1
  --env FG2_FIXTURE_RESPONSE_FILE=/workspace/tests/fg2_full_pipeline_pg17/responses_initial.json
  --env FG2_FIXTURE_EVENT_LOG=/run/fg2-http-events.jsonl
  --env GITHUB_EVENT_NAME=schedule --env GITHUB_REF=refs/heads/main
  --env GITHUB_SHA="$source_sha" --env GITHUB_RUN_ATTEMPT=1
  --env AUTOMATION_ENABLED=true --env PRODUCTION_WRITERS_PAUSED=false
  --env HTTP_PROXY= --env HTTPS_PROXY= --env ALL_PROXY= --env http_proxy= --env https_proxy= --env all_proxy=
  --env NO_PROXY='*' --env no_proxy='*'
  --mount "type=bind,src=$ROOT/scripts,dst=/workspace/scripts,readonly"
  --mount "type=bind,src=$ROOT/db,dst=/workspace/db,readonly"
  --mount "type=bind,src=$ROOT/tests,dst=/workspace/tests,readonly"
  --mount "type=bind,src=$ROOT/.github,dst=/workspace/.github,readonly"
  --mount "type=bind,src=$run_dir,dst=/run"
)
approved_docker_args=("${common_docker_args[@]}")
for index in "${!approved_docker_args[@]}"; do
  case "${approved_docker_args[$index]}" in
    GITHUB_EVENT_NAME=schedule) approved_docker_args[index]='GITHUB_EVENT_NAME=workflow_dispatch' ;;
    AUTOMATION_ENABLED=true) approved_docker_args[index]='AUTOMATION_ENABLED=false' ;;
  esac
done

# Exercise the versioned production control gate separately from the local
# synthetic writer run. No remote environment or flags are touched.
blocked_control_log="$out/production_control_paused.log"
docker run --pull=never --rm --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --mount "type=bind,src=$ROOT/.github,dst=/workspace/.github,readonly" \
  --env GITHUB_EVENT_NAME=schedule --env GITHUB_REF=refs/heads/main --env GITHUB_REF_NAME=main \
  --env AUTOMATION_ENABLED=false --env PRODUCTION_WRITERS_PAUSED=true \
  "$APP_IMAGE" /bin/bash -lc 'bash /workspace/.github/scripts/production_control_preflight.sh FG2-HARVEST' \
  >"$blocked_control_log" 2>&1 || fail production_control BLOCKED_SCHEDULE_PROBE_FAILED
grep -q 'allow_writer=false reason=automation_disabled' "$blocked_control_log" \
  || fail production_control PAUSED_SCHEDULE_NOT_BLOCKED
printf 'phase=production_control_paused_schedule|result=PASS|writer=blocked\n'

enabled_control_log="$out/production_control_enabled.log"
docker run --pull=never --rm --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --mount "type=bind,src=$ROOT/.github,dst=/workspace/.github,readonly" \
  --env GITHUB_EVENT_NAME=schedule --env GITHUB_REF=refs/heads/main --env GITHUB_REF_NAME=main \
  --env AUTOMATION_ENABLED=true --env PRODUCTION_WRITERS_PAUSED=false \
  "$APP_IMAGE" /bin/bash -lc 'for writer in FG2-HARVEST FG2-CLEANSING FG2-ENRICHMENT FG2-SYNC; do bash /workspace/.github/scripts/production_control_preflight.sh "$writer" --enforce || exit; done' \
  >"$enabled_control_log" 2>&1 || { tail -n 30 "$enabled_control_log"; fail production_control ENABLED_SCHEDULE_WRITERS_REJECTED; }
if grep -E 'allow_writer=false|blocked' "$enabled_control_log" >/dev/null; then
  fail production_control ENABLED_SCHEDULE_WRITER_BLOCKED
fi
printf 'phase=production_control_enabled_schedule|result=PASS|writers=4\n'

non_main_log="$out/production_control_non_main.log"
if docker run --pull=never --rm --network none --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=32m \
    --mount "type=bind,src=$ROOT/.github,dst=/workspace/.github,readonly" \
    --env GITHUB_EVENT_NAME=schedule --env GITHUB_REF=refs/heads/certificacion --env GITHUB_REF_NAME=certificacion \
    --env AUTOMATION_ENABLED=true --env PRODUCTION_WRITERS_PAUSED=false \
    "$APP_IMAGE" /bin/bash -lc 'bash /workspace/.github/scripts/production_control_preflight.sh FG2-HARVEST --enforce' \
    >"$non_main_log" 2>&1; then
  fail production_control NON_MAIN_REF_WAS_ALLOWED
fi
grep -q 'reason=non_main_production_ref_blocked' "$non_main_log" \
  || fail production_control NON_MAIN_REF_REASON_MISMATCH
printf 'phase=production_control_non_main|result=PASS|writer=blocked\n'

run_cli() {
  local phase="$1" response_file="$2" run_id="$3"
  shift 3
  local log="$out/${phase}.log"
  if ! docker run "${common_docker_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_RESPONSE_FILE="/workspace/tests/fg2_full_pipeline_pg17/$response_file" \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py "$@" >"$log" 2>&1; then
    printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
    tail -n 80 "$log"
    exit 2
  fi
  printf 'phase=%s|result=PASS\n' "$phase"
  if grep -E '^phase=(manifest_restore|admin_queue_rpc)\|' "$log"; then :; fi
}

run_master() {
  local phase="$1" response_file="$2" run_id="$3"
  local manifest_sha log="$out/${phase}.log"
  # A prior container exports this file as UID 1000 and mode 0644. The host
  # runner may have a different UID, so replace the directory entry instead
  # of trying to truncate a file it does not own. The sticky bit lets the
  # directory owner reset it without allowing unrelated users to unlink it.
  rm -f -- "$manifest"
  if ! docker run "${common_docker_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_RESPONSE_FILE="/workspace/tests/fg2_full_pipeline_pg17/$response_file" \
      --env FG2_PROFILE_DIAGNOSTICS_ENABLED=true \
      --env FG2_PROFILE_DIAGNOSTIC_SLUGS=fg2-ssr-onboard,fg2-ambiguous \
      --env FG2_PROFILE_DIAGNOSTIC_PERSIST_ENABLED=true \
      --env FG2_PROFILE_AUTO_ACTIVATE_VERIFIED=true \
      --env FG2_FIXTURE_EXPORT_MANIFEST=/run/fg2-cohort-manifest.json \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
      /workspace/scripts/core/master_orchestrator.py --limit 10 --max-urls 10 --skip-cleansing \
      --scheduled-cohort --cohort-manifest /run/fg2-cohort-manifest.json >"$log" 2>&1; then
    printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
    tail -n 100 "$log"
    grep -E '"boundary":"postgrest_api"' "$events" | tail -n 20 || true
    exit 2
  fi
  if ! manifest_sha="$(sha256sum "$manifest" | cut -d' ' -f1)" || [[ ! "$manifest_sha" =~ ^[0-9a-f]{64}$ ]]; then
    fail "$phase" MANIFEST_EXPORT_NOT_READABLE
  fi
  printf 'phase=%s|result=PASS|manifest_sha256=%s\n' "$phase" "$manifest_sha"
  grep -E '^phase=fg2_diagnostic\|' "$log" || true
}

prepare_approved_lot() {
  local phase="$1" run_id="$2" log
  log="$out/${phase}.log"
  rm -f -- "$run_dir/fg2-approved-lot.json"
  if ! docker run "${common_docker_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_RESPONSE_FILE=/workspace/tests/fg2_full_pipeline_pg17/responses_refresh.json \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
      /workspace/tests/fg2_full_pipeline_pg17/prepare_approved_lot.py >"$log" 2>&1; then
    printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
    tail -n 60 "$log"
    exit 2
  fi
  grep -E '^phase=approved_lot_fixture\|' "$log"
}

run_approved_master() {
  local phase="$1" run_id="$2" expect_noop="${3:-false}"
  local response_file="${4:-responses_refresh.json}"
  local log="$out/${phase}.log" lot_path=/run/fg2-approved-lot.json
  local cohort_path=/run/fg2-cohort-manifest.json
  local lot_sha lot_b64
  lot_sha="$(sha256sum "$run_dir/fg2-approved-lot.json" | cut -d' ' -f1)"
  lot_b64="$(base64 -w0 "$run_dir/fg2-approved-lot.json")"
  rm -f -- "$manifest"
  if docker run "${approved_docker_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_RESPONSE_FILE="/workspace/tests/fg2_full_pipeline_pg17/$response_file" \
      --env FG2_APPROVED_LOT_MANIFEST_B64="$lot_b64" \
      --env FG2_FIXTURE_EXPORT_MANIFEST=/run/fg2-cohort-manifest.json \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
      /workspace/scripts/core/master_orchestrator.py --limit 10 --max-urls 10 --skip-cleansing \
      --controlled-first-run --cohort-manifest "$cohort_path" \
      --approved-lot-manifest "$lot_path" \
      --approved-lot-reference fixture-processed-refresh-existing-course \
      --approved-lot-sha256 "$lot_sha" >"$log" 2>&1; then
    if [[ "$expect_noop" == true ]]; then
      fail "$phase" IDENTICAL_REFRESH_UNEXPECTEDLY_PRODUCED_A_COHORT
    fi
  else
    if [[ "$expect_noop" != true ]]; then
      printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
      tail -n 100 "$log"
      grep -E '"boundary":"postgrest_api"' "$events" | tail -n 20 || true
      exit 2
    fi
    if ! grep -q 'Controlled first run produced no cohort rows; no downstream stage may run' "$log"; then
      printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
      tail -n 80 "$log"
      fail "$phase" NOOP_DID_NOT_STOP_AT_EMPTY_COHORT_GUARD
    fi
  fi
  if [[ "$expect_noop" == true ]]; then
    printf 'phase=%s|result=PASS|expected=empty_cohort_guard|manifest_sha256=%s\n' \
      "$phase" "$(sha256sum "$manifest" | cut -d' ' -f1)"
  else
    local manifest_sha
    if ! manifest_sha="$(sha256sum "$manifest" | cut -d' ' -f1)" || [[ ! "$manifest_sha" =~ ^[0-9a-f]{64}$ ]]; then
      fail "$phase" MANIFEST_EXPORT_NOT_READABLE
    fi
    printf 'phase=%s|result=PASS|manifest_sha256=%s\n' "$phase" "$manifest_sha"
  fi
}

run_worker() {
  local phase="$1" script="$2" run_id="$3" expected_result="${4:-success}" recovery_source="${5:-false}"
  local manifest_sha manifest_b64 log
  local recovery_args=()
  if [[ "$recovery_source" == "true" ]]; then
    recovery_args+=(--env FG2_FIXTURE_RECOVERY_SOURCE=1)
  fi
  manifest_sha="$(sha256sum "$manifest" | cut -d' ' -f1)"
  manifest_b64="$(base64 -w0 "$manifest")"
  log="$out/${phase}.log"
  if docker run "${common_docker_args[@]}" \
      "${recovery_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_MANIFEST_B64="$manifest_b64" \
      --env FG2_FIXTURE_MANIFEST_SHA256="$manifest_sha" \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
      "/workspace/scripts/core/$script" --cohort-manifest /tmp/fg2-cohort-manifest.json \
      --cohort-manifest-sha256 "$manifest_sha" >"$log" 2>&1; then
    if [[ "$expected_result" == "failure" ]]; then
      fail "$phase" EXPECTED_FAILURE_RETURNED_SUCCESS
    fi
  else
    if [[ "$expected_result" != "failure" ]]; then
      printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
      tail -n 100 "$log"
      exit 2
    fi
    printf 'phase=%s|result=PASS|expected=controlled_failure\n' "$phase"
    return 0
  fi
  if [[ "$expected_result" != "success" ]]; then
    fail "$phase" EXPECTED_FAILURE_DID_NOT_OCCUR
  fi
  printf 'phase=%s|result=PASS|manifest_sha256=%s\n' "$phase" "$manifest_sha"
  grep -E '^phase=manifest_restore\|' "$log" || true
}

run_worker_with_openai_http_fixture() {
  local phase="$1" script="$2" run_id="$3" provider_mode="${4:-success}" expected_result="${5:-success}" recovery_source="${6:-false}" provider_modality_mode="${7:-valid}"
  local manifest_sha manifest_b64 log
  local provider_http_args=("${approved_docker_args[@]}")
  if [[ "$recovery_source" == "true" ]]; then
    provider_http_args+=(--env FG2_FIXTURE_RECOVERY_SOURCE=1)
  fi
  manifest_sha="$(sha256sum "$manifest" | cut -d' ' -f1)"
  manifest_b64="$(base64 -w0 "$manifest")"
  log="$out/${phase}.log"
  for index in "${!provider_http_args[@]}"; do
    if [[ "${provider_http_args[index]}" == "FG2_FIXTURE_PROVIDER_ADAPTER=1" ]]; then
      provider_http_args[index]='FG2_FIXTURE_PROVIDER_ADAPTER=0'
    fi
  done
  if docker run "${provider_http_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_PROVIDER_HTTP=1 \
      --env FG2_FIXTURE_PROVIDER_MODE="$provider_mode" \
      --env FG2_FIXTURE_PROVIDER_MODALITY_MODE="$provider_modality_mode" \
      --env FG2_REQUIRE_REAL_PROVIDER=true \
      --env OPENAI_API_KEY=synthetic-openai-key \
      --env CF_API_TOKEN=fixture-cf \
      --env CF_ACCOUNT_ID=synthetic-cloudflare-account \
      --env FG2_FIXTURE_MANIFEST_B64="$manifest_b64" \
      --env FG2_FIXTURE_MANIFEST_SHA256="$manifest_sha" \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
      "/workspace/scripts/core/$script" --cohort-manifest /tmp/fg2-cohort-manifest.json \
      --cohort-manifest-sha256 "$manifest_sha" >"$log" 2>&1; then
    if [[ "$expected_result" == "failure" ]]; then
      fail "$phase" EXPECTED_FAILURE_RETURNED_SUCCESS
    fi
  else
    if [[ "$expected_result" != "failure" ]]; then
      printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
      tail -n 100 "$log"
      exit 2
    fi
    printf 'phase=%s|result=PASS|expected=controlled_failure\n' "$phase"
    if grep -Eq 'synthetic-openai-key|fixture-cf|synthetic-cloudflare-account' "$log"; then
      fail "$phase" SYNTHETIC_PROVIDER_CREDENTIAL_LEAKED
    fi
    return 0
  fi
  if [[ "$expected_result" != "success" ]]; then
    fail "$phase" EXPECTED_FAILURE_DID_NOT_OCCUR
  fi
  printf 'phase=%s|result=PASS|manifest_sha256=%s\n' "$phase" "$manifest_sha"
  grep -E '^phase=manifest_restore\|' "$log" || true
}

assert_counts() {
  local staging="$1" cleansed="$2" enriched="$3" courses="$4"
  docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 \
    -c "SELECT set_config('fg2.fixture_expected_staging','$staging',false), set_config('fg2.fixture_expected_cleansed','$cleansed',false), set_config('fg2.fixture_expected_enriched','$enriched',false), set_config('fg2.fixture_expected_courses','$courses',false)" \
    -f /fixture/assert_state.sql >/dev/null
}

docker run --pull=never --rm --network "$net" --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --env SUPABASE_URL=http://postgrest:3000 --env FG2_FIXTURE_JWT_SECRET="$jwt_secret" \
  --env PYTHON_DOTENV_DISABLED=1 --env PYTHONDONTWRITEBYTECODE=1 \
  --mount "type=bind,src=$ROOT/tests,dst=/workspace/tests,readonly" \
  "$APP_IMAGE" /opt/venv/bin/python -c 'import requests,sys; r=requests.get("http://postgrest:3000/",timeout=3); sys.exit(0 if r.status_code == 200 else 1)' \
  >/dev/null 2>&1 || fail postgrest POSTGREST_NOT_READY
printf 'phase=postgrest_readiness|result=PASS|network=internal_no_egress\n'

# Exercise actual onboarding classifier for all supported source types with
# synthetic HTTP fixtures before the database-backed workflow stages.
diagnostic_log="$out/diagnostic_modes.log"
if ! docker run "${common_docker_args[@]}" --env GITHUB_RUN_ID=8999999 \
    "$APP_IMAGE" /opt/venv/bin/python -c 'import json; from scripts.shared.site_diagnostics import diagnose_site; expected={"ssr.fg2.example":("verified","traditional_ssr","sitemap_bfs"),"spa.fg2.example":("verified","spa_js_heavy","catalog_link_extraction"),"ecommerce.fg2.example":("verified","ecommerce","paginated_catalog"),"ambiguous.fg2.example":("review_required","traditional_ssr","hardcoded_urls")}; results=[];
for host,want in expected.items():
 r=diagnose_site("https://"+host+"/"); got=(r.get("status"),r.get("suggested",{}).get("site_type"),r.get("suggested",{}).get("discovery_mode")); v=r.get("verification",{}); results.append((host,got,v.get("verified_detail_count"),v.get("automatic_activation_ready")));
 if got!=want or (want[0]=="verified" and (v.get("verified_detail_count",0)<2 or not v.get("automatic_activation_ready"))) or (want[0]=="review_required" and (v.get("eligible") is not False or v.get("automatic_activation_ready") is not False)): raise SystemExit("diagnostic_fixture_expectation_failed:"+host)
print("phase=diagnostic_modes|result=PASS|modes=traditional_ssr,spa_js_heavy,ecommerce|ambiguous=review_required|verified_details=2_each")' \
    >"$diagnostic_log" 2>&1; then
  tail -n 50 "$diagnostic_log"
  fail diagnostic_modes SOURCE_TYPE_CLASSIFICATION_OR_EVIDENCE_MISMATCH
fi
grep -E '^phase=diagnostic_modes\|' "$diagnostic_log"

# In-memory syntax/import gate precedes any scenario execution.
docker run "${common_docker_args[@]}" --env GITHUB_RUN_ID=0 \
  "$APP_IMAGE" /opt/venv/bin/python -c 'import ast,pathlib; paths=["/workspace/scripts/core/master_orchestrator.py","/workspace/scripts/core/universal_harvester.py","/workspace/scripts/core/cleansing_worker.py","/workspace/scripts/core/enrichment_worker.py","/workspace/scripts/core/sync_vector_worker.py","/workspace/scripts/core/profile_onboarding.py"]; [ast.parse(pathlib.Path(p).read_text(encoding="utf-8"), filename=p) for p in paths]; import scripts.core.universal_harvester, scripts.core.master_orchestrator; print("phase=fg2_syntax_import|result=PASS")' \
  >"$out/syntax.log" 2>&1 || { tail -n 50 "$out/syntax.log"; fail syntax IMPORT_OR_SYNTAX_ERROR; }
grep -E '^phase=fg2_syntax_import\|' "$out/syntax.log"

# The onboarding job diagnoses a previously unprofiled SSR source while
# harvesting only existing runnable profiles; the next schedule consumes the
# newly verified SSR profile without a manual seed edit.
run_master run_1_onboarding_harvest responses_initial.json 9000001
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM public.institution_site_profiles WHERE institution_id='20000000-0000-0000-0000-000000000001' AND profile_status='active' AND site_type='traditional_ssr' AND discovery_mode='sitemap_bfs' AND production_enabled=false AND diagnostic_status='verified') THEN RAISE EXCEPTION 'ssr_onboarding_activation_assertion'; END IF; IF NOT EXISTS (SELECT 1 FROM public.institution_site_profiles WHERE institution_id='20000000-0000-0000-0000-000000000005' AND profile_status='pending_review' AND site_type IS NULL AND discovery_enabled=false) THEN RAISE EXCEPTION 'ambiguous_pending_review_assertion'; END IF; END \$\$" >/dev/null
run_worker run_1_cleansing cleansing_worker.py 9000001
assert_counts 4 4 0 0
run_worker run_1_enrichment enrichment_worker.py 9000001
assert_counts 4 4 4 0
run_worker run_1_sync sync_vector_worker.py 9000001
assert_counts 4 4 4 4

# New profile now enters an ordinary schedule. No hardcoded course URL is
# inserted; sitemap discovery must produce two fresh detail identities.
run_master run_2_ssr_harvest responses_initial.json 9000002
run_worker run_2_cleansing cleansing_worker.py 9000002
assert_counts 6 6 4 4
run_worker run_2_enrichment enrichment_worker.py 9000002
assert_counts 6 6 6 4
run_worker run_2_sync sync_vector_worker.py 9000002
assert_counts 6 6 6 6

# Create one local synthetic editorial publication with a manual override to
# prove the refresh writer preserves existing editorial ownership.
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -At -c \
  "SELECT 'fixture_course|path=' || regexp_replace(url, '^https?://[^/]+', '') FROM public.courses WHERE institution_id='20000000-0000-0000-0000-000000000001' ORDER BY url" \
  >"$out/ssr_course_paths.log"
cat "$out/ssr_course_paths.log"
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/prepare_refresh.sql >/dev/null

# The unchanged-content case runs first against the same fresh synthetic
# rotation snapshot. A completed content-changing harvest advances
# last_harvest_at and can legitimately move this institution out of the
# rotation prefix for a subsequent, separately approved dispatch.
prepare_approved_lot run_4_identical_refresh_manifest 9000004
noop_event_start="$(wc -l <"$events")"
noop_staging_before="$(docker exec "$pg" psql -X -U postgres -d "$DATABASE" -At -c \
  "SELECT status || '|' || content_hash FROM public.staging_raw WHERE rtrim(url, '/')='https://ssr.fg2.example/programas/analitica-aplicada'")"
run_approved_master run_4_identical_refresh 9000004 true responses_initial.json
noop_staging_after="$(docker exec "$pg" psql -X -U postgres -d "$DATABASE" -At -c \
  "SELECT status || '|' || content_hash FROM public.staging_raw WHERE rtrim(url, '/')='https://ssr.fg2.example/programas/analitica-aplicada'")"
[[ "$noop_staging_before" == "$noop_staging_after" ]] || fail run_4_identical_refresh STAGING_CHANGED_DURING_NOOP
docker run --pull=never --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --mount "type=bind,src=$manifest,dst=/run/cohort.json,readonly" \
  "$APP_IMAGE" /opt/venv/bin/python -c 'import json,pathlib,sys; m=json.loads(pathlib.Path("/run/cohort.json").read_text()); rows=m.get("discovery_rows", []); ok=not m.get("entries") and len(rows)==1 and rows[0].get("initial_status")=="processed" and rows[0].get("kind")=="refresh_existing"; ok or sys.exit("phase=approved_refresh_identical_noop|result=FAIL|code=cohort_not_empty_guarded"); print("phase=approved_refresh_identical_noop|result=PASS|cohort_entries=0|processed_discovery=1")' \
  >"$out/identical_refresh_manifest.log" 2>&1 || { cat "$out/identical_refresh_manifest.log"; fail run_4_identical_refresh NOOP_COHORT_ASSERTION; }
cat "$out/identical_refresh_manifest.log"
docker run --pull=never --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --mount "type=bind,src=$events,dst=/run/events.jsonl,readonly" \
  --env FG2_EVENT_OFFSET="$noop_event_start" \
  "$APP_IMAGE" /opt/venv/bin/python -c 'import json,os,pathlib,sys; lines=pathlib.Path("/run/events.jsonl").read_text().splitlines()[int(os.environ["FG2_EVENT_OFFSET"]):]; events=[json.loads(line) for line in lines if line]; writes=[event for event in events if event.get("boundary")=="postgrest_api" and event.get("method") in {"POST","PATCH","DELETE"}]; not writes or sys.exit("phase=approved_refresh_identical_noop|result=FAIL|code=unexpected_database_write"); print("phase=approved_refresh_identical_noop|result=PASS|database_writes=0|downstream_jobs=not_started")' \
  >"$out/identical_refresh_audit.log" 2>&1 || { cat "$out/identical_refresh_audit.log"; fail run_4_identical_refresh DATABASE_WRITE_DURING_NOOP; }
cat "$out/identical_refresh_audit.log"
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "DO \$\$ BEGIN IF (SELECT count(*) FROM public.staging_raw WHERE status='processed') <> 6 THEN RAISE EXCEPTION 'no_op_stage_status_changed'; END IF; IF NOT EXISTS (SELECT 1 FROM public.staging_raw WHERE url='https://ssr.fg2.example/programas/outside-approved-cohort' AND status='pending') THEN RAISE EXCEPTION 'out_of_cohort_sentinel_changed'; END IF; IF (SELECT count(*) FROM public.enriched_programs WHERE status='synced') <> 6 THEN RAISE EXCEPTION 'no_op_enrichment_changed'; END IF; IF (SELECT count(*) FROM public.courses_public_effective) <> 0 THEN RAISE EXCEPTION 'no_op_publication_changed'; END IF; END \$\$" >/dev/null
printf 'phase=approved_refresh_identical_noop|result=PASS|staging=unchanged|providers=not_invoked|cohort_entries=0\n'

docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/inject_one_cleansing_failure.sql >/dev/null

prepare_approved_lot run_3_processed_refresh_manifest 9000003
run_approved_master run_3_processed_refresh 9000003
manifest_sha="$(sha256sum "$manifest" | cut -d' ' -f1)"
manifest_b64="$(base64 -w0 "$manifest")"
fault_log="$out/refresh_expected_failure.log"
if docker run "${common_docker_args[@]}" --env GITHUB_RUN_ID=9000003 \
    --env FG2_FIXTURE_MANIFEST_B64="$manifest_b64" --env FG2_FIXTURE_MANIFEST_SHA256="$manifest_sha" \
    "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
    /workspace/scripts/core/cleansing_worker.py --cohort-manifest /tmp/fg2-cohort-manifest.json \
    --cohort-manifest-sha256 "$manifest_sha" >"$fault_log" 2>&1; then
  fail refresh_recovery INJECTED_RPC_FAILURE_WAS_NOT_PROPAGATED
fi
printf 'phase=refresh_rpc_failure|result=PASS|expected=cleansing_nonzero\n'
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM public.staging_raw WHERE rtrim(url, '/')='https://ssr.fg2.example/programas/analitica-aplicada' AND status='pending') THEN RAISE EXCEPTION 'refresh_pending_rollback_assertion'; END IF; IF NOT EXISTS (SELECT 1 FROM public.staging_raw WHERE rtrim(url, '/')='https://ssr.fg2.example/programas/outside-approved-cohort' AND status='pending') THEN RAISE EXCEPTION 'out_of_cohort_sentinel_changed_after_failure'; END IF; IF (SELECT count(*) FROM public.cleansed_programs) <> 6 THEN RAISE EXCEPTION 'refresh_no_partial_cleansing_assertion'; END IF; END \$\$" >/dev/null
run_worker run_3_cleansing_recovery cleansing_worker.py 9000003
assert_counts 7 6 6 6
run_worker_with_openai_http_fixture run_3_enrichment enrichment_worker.py 9000003
assert_counts 7 6 6 6
run_worker run_3_sync sync_vector_worker.py 9000003
assert_counts 7 6 6 6

docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "DO \$\$ BEGIN IF (SELECT count(*) FROM public.staging_raw WHERE status='processed') <> 6 THEN RAISE EXCEPTION 'staging_processed_count_assertion'; END IF; IF (SELECT count(*) FROM public.cleansed_programs WHERE status='enriched') <> 6 THEN RAISE EXCEPTION 'cleansed_enriched_count_assertion'; END IF; IF (SELECT count(*) FROM public.enriched_programs WHERE status='synced') <> 6 THEN RAISE EXCEPTION 'enriched_synced_count_assertion'; END IF; IF (SELECT count(*) FROM public.enriched_programs WHERE status='synced' AND is_mock_data IS FALSE) <> 6 THEN RAISE EXCEPTION 'synthetic_provider_boundary_contract_assertion'; END IF; IF (SELECT count(*) FROM public.enriched_programs WHERE rtrim(url, '/')='https://ssr.fg2.example/programas/analitica-aplicada' AND provider_used='OpenAI') <> 1 THEN RAISE EXCEPTION 'openai_http_provider_not_persisted'; END IF; IF (SELECT count(*) FROM public.enriched_programs WHERE rtrim(url, '/')<>'https://ssr.fg2.example/programas/analitica-aplicada' AND provider_used='fixture-provider') <> 5 THEN RAISE EXCEPTION 'synthetic_provider_fixture_rows_changed'; END IF; IF (SELECT count(*) FROM public.course_editorial_state WHERE editorial_status='pending_review') <> 5 THEN RAISE EXCEPTION 'pending_editorial_count_assertion'; END IF; IF (SELECT count(*) FROM public.courses_public_effective) <> 0 THEN RAISE EXCEPTION 'public_effective_must_be_empty_assertion'; END IF; IF EXISTS (SELECT 1 FROM public.staging_raw WHERE institution_id='20000000-0000-0000-0000-000000000004') THEN RAISE EXCEPTION 'blocked_source_must_not_create_staging'; END IF; IF NOT EXISTS (SELECT 1 FROM public.institution_site_profiles WHERE institution_id='20000000-0000-0000-0000-000000000005' AND profile_status='pending_review') THEN RAISE EXCEPTION 'ambiguous_profile_must_remain_pending'; END IF; IF NOT EXISTS (SELECT 1 FROM public.course_editorial_state es JOIN public.courses c ON c.id=es.course_id WHERE rtrim(c.url, '/')='https://ssr.fg2.example/programas/analitica-aplicada' AND es.editorial_status='published' AND es.manual_overrides->>'name'='Título manual sintético preservado') THEN RAISE EXCEPTION 'editorial_override_was_not_preserved'; END IF; IF EXISTS (SELECT 1 FROM public.course_editorial_state es JOIN public.courses c ON c.id=es.course_id WHERE es.editorial_status='pending_review' AND c.is_active IS TRUE) THEN RAISE EXCEPTION 'pending_new_course_active_assertion'; END IF; END \$\$" >/dev/null

# The refresh above used the real Requests/OpenAI caller through a synthetic
# loopback endpoint; PostgREST and the persistence RPC remained real.
assert_openai_http_boundary() {
  local phase="$1" event_file="$2" expected="$3" run_id="${4:-9000003}" expected_count="${5:-1}" event_offset="${6:-0}" log="$out/${1}.log"
  local result=0
  docker run --pull=never --rm --interactive --network none --read-only \
  --tmpfs "/tmp:rw,noexec,nosuid,size=32m" \
  --mount "type=bind,src=$event_file,dst=/run/fg2-provider-events.jsonl,readonly" \
  --env FG2_PROVIDER_RUN_ID="$run_id" \
  --env FG2_PROVIDER_EVENT_OFFSET="$event_offset" \
  --env FG2_PROVIDER_EXPECTED_COUNT="$expected_count" \
  --env FG2_PROVIDER_EXPECTATION="$expected" \
  "$APP_IMAGE" /opt/venv/bin/python - /run/fg2-provider-events.jsonl >"$log" 2>&1 <<'PY' || result=$?
import json, os, pathlib, sys
events = [json.loads(line) for line in pathlib.Path(sys.argv[1]).read_text().splitlines() if line]
events = events[int(os.environ["FG2_PROVIDER_EVENT_OFFSET"]):]
run_id = os.environ["FG2_PROVIDER_RUN_ID"]
provider_events = [event for event in events if event.get("boundary") == "provider_loopback" and event.get("run_id") == run_id]
expected = os.environ["FG2_PROVIDER_EXPECTATION"]
expected_count = int(os.environ["FG2_PROVIDER_EXPECTED_COUNT"])
valid = len(provider_events) == expected_count and all(
    event.get("provider") == "OpenAI"
    and event.get("status") == 200
    and event.get("valid_schema_request") is True
    for event in provider_events
)
if expected == "accept" and (len(provider_events) != expected_count or not valid):
    raise SystemExit("phase=pg17_openai_http_boundary|result=FAIL|code=provider_caller_contract_mismatch")
if expected == "reject" and valid:
    raise SystemExit("phase=pg17_openai_http_boundary|result=FAIL|code=invalid_fixture_was_accepted")
print("phase=pg17_openai_http_boundary|result=PASS|expectation=" + expected + "|requests=" + str(len(provider_events)) + "|assertions_executed=true")
PY

  if [[ "$expected" == "accept" ]]; then
    if ((result != 0)) || ! grep -q "^phase=pg17_openai_http_boundary|result=PASS|expectation=accept|requests=${expected_count}|assertions_executed=true$" "$log"; then
      cat "$log"
      fail "$phase" OPENAI_HTTP_BOUNDARY_ASSERTION_NOT_EXECUTED_OR_FAILED
    fi
    printf 'phase=%s|result=PASS|assertions=executed\n' "$phase"
  else
    if ((result != 0)) || ! grep -Eq '^phase=pg17_openai_http_boundary\|result=PASS\|expectation=reject\|requests=[01]\|assertions_executed=true$' "$log"; then
      cat "$log"
      fail "$phase" OPENAI_HTTP_BOUNDARY_NEGATIVE_FIXTURE_NOT_REJECTED
    fi
    printf 'phase=%s|result=PASS|negative_fixture=rejected|assertions=executed\n' "$phase"
  fi
}

assert_recovery_provider_failure() {
  local phase="$1" run_id="$2" log="$out/${1}.log"
  if ! docker run --pull=never --rm --interactive --network none --read-only \
    --tmpfs "/tmp:rw,noexec,nosuid,size=32m" \
    --mount "type=bind,src=$events,dst=/run/fg2-provider-events.jsonl,readonly" \
    --env FG2_PROVIDER_RUN_ID="$run_id" "$APP_IMAGE" /opt/venv/bin/python - \
    /run/fg2-provider-events.jsonl >"$log" 2>&1 <<'PY'
import json, os, pathlib, sys
events = [json.loads(line) for line in pathlib.Path(sys.argv[1]).read_text().splitlines() if line]
run_id = os.environ["FG2_PROVIDER_RUN_ID"]
requests = [event for event in events if event.get("boundary") == "provider_loopback" and event.get("run_id") == run_id]
providers = {event.get("provider") for event in requests}
if providers != {"OpenAI", "Cloudflare"} or not requests:
    raise SystemExit("phase=post272_provider_failure|result=FAIL|code=fallback_path_not_exercised")
if any(event.get("status") != 503 or event.get("valid_schema_request") is not True for event in requests):
    raise SystemExit("phase=post272_provider_failure|result=FAIL|code=provider_failure_fixture_mismatch")
print(f"phase=post272_provider_failure|result=PASS|providers=OpenAI,Cloudflare|requests={len(requests)}|mock_rejected=true")
PY
  then
    cat "$log"
    fail "$phase" PROVIDER_FAILURE_ASSERTION_FAILED
  fi
  cat "$log"
}

assert_no_successful_db_writes_since() {
  local phase="$1" offset="$2" expected="${3:-none}" log="$out/${1}.log"
  if ! docker run --pull=never --rm --interactive --network none --read-only \
    --tmpfs "/tmp:rw,noexec,nosuid,size=32m" \
    --mount "type=bind,src=$events,dst=/run/fg2-http-events.jsonl,readonly" \
    --env FG2_EVENT_OFFSET="$offset" --env FG2_EXPECTED_WRITE_REQUESTS="$expected" "$APP_IMAGE" /opt/venv/bin/python - \
    /run/fg2-http-events.jsonl >"$log" 2>&1 <<'PY'
import json, os, pathlib, sys
events = [json.loads(line) for line in pathlib.Path(sys.argv[1]).read_text().splitlines() if line]
events = events[int(os.environ["FG2_EVENT_OFFSET"]):]
writes = [event for event in events if event.get("boundary") == "postgrest_api" and event.get("method") in {"POST", "PATCH", "DELETE"}]
successful = [event for event in writes if 200 <= int(event.get("status", 0)) < 300]
if successful:
    raise SystemExit("phase=post272_write_audit|result=FAIL|code=successful_db_write_observed")
expected = os.environ["FG2_EXPECTED_WRITE_REQUESTS"]
if expected == "none" and writes:
    raise SystemExit("phase=post272_write_audit|result=FAIL|code=unexpected_write_request")
if expected == "failed" and (not writes or any(200 <= int(event.get("status", 0)) < 300 for event in writes)):
    raise SystemExit("phase=post272_write_audit|result=FAIL|code=failed_write_not_observed")
print(f"phase=post272_write_audit|result=PASS|write_requests={len(writes)}|successful_writes=0")
PY
  then
    cat "$log"
    fail "$phase" DB_WRITE_AUDIT_FAILED
  fi
  cat "$log"
}

openai_missing_events="$run_dir/provider-events-missing.jsonl"
openai_invalid_events="$run_dir/provider-events-invalid.jsonl"
: >"$openai_missing_events"
printf '%s\n' '{"boundary":"provider_loopback","run_id":"9000003","provider":"OpenAI","status":200,"valid_schema_request":false}' >"$openai_invalid_events"
assert_openai_http_boundary pg17_openai_http_boundary "$events" accept
assert_openai_http_boundary pg17_openai_http_boundary_missing "$openai_missing_events" reject
assert_openai_http_boundary pg17_openai_http_boundary_invalid "$openai_invalid_events" reject

# The same HTTP route and budget serve HTTP, browser navigation and scripts.
# A 429 response is recorded once per blocked cohort run; no request is retried.
docker run "${common_docker_args[@]}" --env GITHUB_RUN_ID=9000003 \
  "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/verify_admin_queue.py \
  >"$out/admin.log" 2>&1 || { cat "$out/admin.log"; fail admin_queue ADMIN_RPC_OR_PUBLIC_VIEW_ASSERTION; }
grep -E '^phase=(fg2_profile_schema_contract|admin_queue_rpc)\|' "$out/admin.log"

http_audit_log="$out/synthetic_http_audit.log"
if ! docker run --pull=never --rm --interactive --network none --read-only \
  --tmpfs "/tmp:rw,noexec,nosuid,size=32m" \
  --mount "type=bind,src=$events,dst=/run/fg2-http-events.jsonl,readonly" \
  "$APP_IMAGE" /opt/venv/bin/python - /run/fg2-http-events.jsonl >"$http_audit_log" 2>&1 <<'PY'
import json, pathlib, sys
from collections import Counter
events=[json.loads(line) for line in pathlib.Path(sys.argv[1]).read_text().splitlines() if line]
http_events=[event for event in events if event.get("boundary") in {"harvester_budget", "site_diagnostics"}]
if not http_events:
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=no_requests")
if any(event.get("status") == 599 or not event.get("pinned") for event in http_events):
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=unmapped_or_unpinned")
blocked=[event for event in http_events if event.get("host") == "blocked.fg2.example" and event.get("status") == 429]
blocked_per_run=Counter(event.get("run_id") for event in blocked)
if blocked_per_run != Counter({"9000001": 1, "9000002": 1}):
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=blocked_retry_or_selection_count")
if any(event.get("host") != "ssr.fg2.example" for event in http_events if event.get("run_id") in {"9000003", "9000004"}):
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=approved_refresh_contacted_out_of_cohort_source")
noop_requests=[event for event in http_events if event.get("run_id")=="9000004" and event.get("boundary")=="harvester_budget"]
if len(noop_requests) != 1 or noop_requests[0].get("path") != "/programas/analitica-aplicada":
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=identical_refresh_request_scope_mismatch")
spa_script=[event for event in http_events if event.get("host") == "spa.fg2.example" and event.get("path") == "/assets/catalogo.js"]
catalog_pages=[event for event in http_events if event.get("host") == "ecommerce.fg2.example" and event.get("path") == "/catalogo/"]
if not spa_script or not any(event.get("query") == "page=1" for event in catalog_pages) or not any(event.get("query") == "page=2" for event in catalog_pages):
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=browser_or_pagination_missing")
print(f"phase=synthetic_http_audit|result=PASS|attempts={len(http_events)}|blocked_429={len(blocked)}|blocked_runs={len(blocked_per_run)}|spa_js=observed|ecommerce_pages=2|pinned_config=checked")
PY
then
  cat "$http_audit_log"
  fail synthetic_http_audit HTTP_AUDIT_ASSERTION_FAILED
fi
grep -q '^phase=synthetic_http_audit|result=PASS|' "$http_audit_log" \
  || { cat "$http_audit_log"; fail synthetic_http_audit HTTP_AUDIT_ASSERTION_NOT_EXECUTED; }
cat "$http_audit_log"

# Recovery case uses the immutable #272 artifact only as source evidence.
# The new run manifest binds five exact identities; the ambiguous sixth and
# two unchanged rows remain outside scope. No harvesting or cleansing runs.
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 \
  -f /fixture/prepare_post272_recovery.sql >"$out/post272_fixture.log"
cat "$out/post272_fixture.log"
recovery_manifest_log="$out/post272_manifest.log"
if ! docker run "${common_docker_args[@]}" --env GITHUB_RUN_ID=9000005 \
    --env FG2_FIXTURE_EXPORT_MANIFEST=/run/fg2-cohort-manifest.json \
    "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
    /workspace/tests/fg2_full_pipeline_pg17/prepare_post272_recovery.py \
    >"$recovery_manifest_log" 2>&1; then
  cat "$recovery_manifest_log"
  fail post272_recovery_manifest MANIFEST_BUILD_OR_POSTHARVEST_STATE_MISMATCH
fi
  grep -Eq '^phase=post272_recovery_manifest\|result=PASS\|mode=enrichment_sync_only\|entries=5\|authorized_modality_snapshots=5\|out_of_scope_excluded=1\|discovery_only_excluded=2\|source_run=9000004\|current_run=9000005\|current_sha=[0-9a-f]{40}\|artifact_digest_checked=true\|lot_digest_checked=true\|manifest_sha256=[0-9a-f]{64}\|source_result=deferred\|source_http_requests=7\|source_unique_urls=7\|source_entries=6\|source_discovery_rows=8\|prior_hashes_distinct=6\|url_alias_hashes_differ=6\|new_run_discovery_rows=0\|invalid_bindings_rejected=12\|hash_semantics=source_discovery_prior_vs_entry_stored_vs_current_snapshot$' "$recovery_manifest_log" \
  || { cat "$recovery_manifest_log"; fail post272_recovery_manifest ASSERTION_NOT_EXECUTED; }
cat "$recovery_manifest_log"

assert_post272_failure_state() {
  local phase="$1"
  docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
    "DO \$\$ BEGIN
      IF (SELECT count(*) FROM public.staging_raw WHERE id::text LIKE '52000000-0000-0000-0000-%' AND status='processed') <> 8
         OR (SELECT count(*) FROM public.cleansed_programs WHERE id::text LIKE '54000000-0000-0000-0000-%' AND status='pending') <> 6
         OR (SELECT count(*) FROM public.cleansed_programs WHERE id::text LIKE '54000000-0000-0000-0000-%' AND status='synced') <> 2
         OR (SELECT count(*) FROM public.enriched_programs WHERE id::text LIKE '55000000-0000-0000-0000-%' AND status='synced' AND provider_used='prior-fixture') <> 8
         OR (SELECT count(*) FROM public.courses WHERE split_part(id::text, '-', 1)='53000000' AND provider_used='prior-fixture') <> 8
         OR (SELECT count(*) FROM public.course_editorial_state WHERE course_id::text LIKE '53000000-0000-0000-0000-%' AND editorial_status='pending_review') <> 8
         OR (SELECT count(*) FROM public.courses_public_effective) <> 0 THEN
        RAISE EXCEPTION 'post272_failed_recovery_state_mutated';
      END IF;
      IF (SELECT manual_overrides->>'name' FROM public.course_editorial_state WHERE course_id='53000000-0000-0000-0000-000000000001') <> 'Manual recovery title preserved' THEN
        RAISE EXCEPTION 'post272_failed_recovery_editorial_override_changed';
      END IF;
    END \$\$" >/dev/null
  printf 'phase=%s|result=PASS|persisted_effects=0|editorial_preserved=true|public_effective=0\n' "$phase"
}

provider_failure_offset="$(wc -l <"$events")"
run_worker_with_openai_http_fixture run_5_provider_failure enrichment_worker.py 9000005 fail_all failure true
grep -q 'FG2_ENRICHMENT_ABORT stage=provider_fallback category=real_provider_result_missing' "$out/run_5_provider_failure.log" \
  || fail post272_provider_failure SANITIZED_ABORT_CATEGORY_MISSING
assert_recovery_provider_failure post272_provider_failure 9000005
assert_no_successful_db_writes_since post272_provider_failure "$provider_failure_offset"
assert_post272_failure_state post272_provider_failure

# The fixture transaction fails at the real atomic enrichment RPC boundary.
# Postgres rolls the entire call back; the test inspects that state before a
# separately controlled local retry.
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "UPDATE public.fg2_recovery_fault_switch SET fail_next_enrichment=true WHERE singleton=true" >/dev/null
write_failure_offset="$(wc -l <"$events")"
run_worker_with_openai_http_fixture run_5_write_failure enrichment_worker.py 9000005 success failure true
grep -q 'synthetic_recovery_enrichment_write_failure' "$out/run_5_write_failure.log" \
  || fail post272_write_failure INJECTED_WRITE_FAILURE_NOT_OBSERVED
assert_openai_http_boundary pg17_post272_write_failure "$events" accept 9000005 1 "$write_failure_offset"
assert_no_successful_db_writes_since post272_write_failure "$write_failure_offset" failed
assert_post272_failure_state post272_write_failure
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "UPDATE public.fg2_recovery_fault_switch SET fail_next_enrichment=false WHERE singleton=true" >/dev/null

success_enrichment_offset="$(wc -l <"$events")"
run_worker_with_openai_http_fixture run_5_post272_enrichment enrichment_worker.py 9000005 success success true null
assert_openai_http_boundary pg17_post272_openai_http_boundary "$events" accept 9000005 5 "$success_enrichment_offset"

# All-mock enrichment output is rejected by the real Sync worker before any
# course write. The fixture restores only its synthetic rows, then tests Sync
# with the successful OpenAI-boundary results.
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "UPDATE public.enriched_programs SET provider_used='mock', is_mock_data=true WHERE cleansed_id IN (SELECT id FROM public.cleansed_programs WHERE staging_id IN ('52000000-0000-0000-0000-000000000001'::uuid,'52000000-0000-0000-0000-000000000002'::uuid,'52000000-0000-0000-0000-000000000003'::uuid,'52000000-0000-0000-0000-000000000004'::uuid,'52000000-0000-0000-0000-000000000005'::uuid))" >/dev/null
mock_sync_offset="$(wc -l <"$events")"
run_worker run_5_mock_sync_rejected sync_vector_worker.py 9000005 failure true
grep -q 'FG2_SYNC_ABORT stage=sync category=controlled_mock_enrichment' "$out/run_5_mock_sync_rejected.log" \
  || fail post272_mock_rejection MOCK_RESULT_WAS_NOT_REJECTED
assert_no_successful_db_writes_since post272_mock_rejection "$mock_sync_offset"
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "DO \$\$
  BEGIN
    IF (SELECT count(*) FROM public.courses
        WHERE id IN (
          '53000000-0000-0000-0000-000000000001'::uuid,
          '53000000-0000-0000-0000-000000000002'::uuid,
          '53000000-0000-0000-0000-000000000003'::uuid,
          '53000000-0000-0000-0000-000000000004'::uuid,
          '53000000-0000-0000-0000-000000000005'::uuid
        ) AND provider_used='prior-fixture') <> 5
       OR (SELECT count(*) FROM public.enriched_programs
           WHERE cleansed_id IN (
             SELECT id FROM public.cleansed_programs
             WHERE staging_id IN (
               '52000000-0000-0000-0000-000000000001'::uuid,
               '52000000-0000-0000-0000-000000000002'::uuid,
               '52000000-0000-0000-0000-000000000003'::uuid,
               '52000000-0000-0000-0000-000000000004'::uuid,
               '52000000-0000-0000-0000-000000000005'::uuid
             ) AND status='enriched'
           ) AND is_mock_data=true) <> 5 THEN
      RAISE EXCEPTION 'post272_mock_sync_mutated_course_state';
    END IF;
  END;
  \$\$" >/dev/null
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "UPDATE public.enriched_programs SET provider_used='OpenAI', is_mock_data=false WHERE cleansed_id IN (SELECT id FROM public.cleansed_programs WHERE staging_id IN ('52000000-0000-0000-0000-000000000001'::uuid,'52000000-0000-0000-0000-000000000002'::uuid,'52000000-0000-0000-0000-000000000003'::uuid,'52000000-0000-0000-0000-000000000004'::uuid,'52000000-0000-0000-0000-000000000005'::uuid))" >/dev/null

run_worker run_5_post272_sync sync_vector_worker.py 9000005 success true

# Replaying the same manifest after both stages finish fails closed before a
# provider call or successful write; no scraping or cleansing is repeated.
enrichment_replay_offset="$(wc -l <"$events")"
run_worker run_5_enrichment_replay_rejected enrichment_worker.py 9000005 failure true
grep -q 'FG2_ENRICHMENT_ABORT stage=recovery_scope category=cohort_state_drift' "$out/run_5_enrichment_replay_rejected.log" \
  || fail post272_replay_enrichment IDEMPOTENCY_GUARD_MISSING
sync_replay_offset="$(wc -l <"$events")"
run_worker run_5_sync_replay_rejected sync_vector_worker.py 9000005 failure true
grep -q 'FG2_SYNC_ABORT stage=recovery_scope category=cohort_state_drift' "$out/run_5_sync_replay_rejected.log" \
  || fail post272_replay_sync IDEMPOTENCY_GUARD_MISSING
assert_no_successful_db_writes_since post272_replay "$enrichment_replay_offset"
assert_no_successful_db_writes_since post272_replay "$sync_replay_offset"

docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 \
  -f /fixture/assert_post272_recovery.sql >"$out/post272_postflight.log"
cat "$out/post272_postflight.log"

printf 'phase=fg2_full_pipeline_pg17|result=PASS|initial_courses=6|post272_recovery_stations=Enrichment+Sync|post272_refresh_synced=5|out_of_scope_excluded=1|discovery_only_unchanged=2|public_effective=0|provider_boundary=synthetic_loopback_openai|harvest_cleansing_replayed=false\n'
printf 'phase=limits|result=LOCAL_EVIDENCE_ONLY|network=internal_no_egress|db=ephemeral_pg17|production=untouched\n'
