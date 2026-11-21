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
chmod 777 "$run_dir"
jwt_secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
pg_password="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
fixture_publishable_key="sb_publishable_$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
fixture_secret_key="sb_secret_$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
source_sha="${FG2_FIXTURE_SOURCE_SHA:-95d0e7d52e5c2c67eb473a2f12fc7df4d89fc40b}"
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
  if docker exec "$pg" pg_isready -U postgres -d "$DATABASE" >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
(( ready == 1 )) || fail pg17 PG17_READINESS_TIMEOUT
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/setup.sql >/dev/null
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
  local log="$out/${phase}.log"
  : > "$manifest"
  if ! docker run "${common_docker_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_RESPONSE_FILE="/workspace/tests/fg2_full_pipeline_pg17/$response_file" \
      --env FG2_PROFILE_DIAGNOSTICS_ENABLED=true \
      --env FG2_PROFILE_DIAGNOSTIC_SLUGS=fg2-ssr-onboard,fg2-ambiguous \
      --env FG2_PROFILE_DIAGNOSTIC_PERSIST_ENABLED=true \
      --env FG2_PROFILE_AUTO_ACTIVATE_VERIFIED=true \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
      /workspace/scripts/core/master_orchestrator.py --limit 10 --max-urls 10 --skip-cleansing \
      --scheduled-cohort --cohort-manifest /run/fg2-cohort-manifest.json >"$log" 2>&1; then
    printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
    tail -n 100 "$log"
    grep -E '"boundary":"postgrest_api"' "$events" | tail -n 20 || true
    exit 2
  fi
  printf 'phase=%s|result=PASS|manifest_sha256=%s\n' "$phase" "$(sha256sum "$manifest" | cut -d' ' -f1)"
  grep -E '^phase=fg2_diagnostic\|' "$log" || true
}

run_worker() {
  local phase="$1" script="$2" run_id="$3"
  local manifest_sha manifest_b64 log
  manifest_sha="$(sha256sum "$manifest" | cut -d' ' -f1)"
  manifest_b64="$(base64 -w0 "$manifest")"
  log="$out/${phase}.log"
  if ! docker run "${common_docker_args[@]}" \
      --env GITHUB_RUN_ID="$run_id" \
      --env FG2_FIXTURE_MANIFEST_B64="$manifest_b64" \
      --env FG2_FIXTURE_MANIFEST_SHA256="$manifest_sha" \
      "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/run_entrypoint.py \
      "/workspace/scripts/core/$script" --cohort-manifest /tmp/fg2-cohort-manifest.json \
      --cohort-manifest-sha256 "$manifest_sha" >"$log" 2>&1; then
    printf 'phase=%s|result=FAIL|diagnostic_log=%s\n' "$phase" "$log"
    tail -n 100 "$log"
    exit 2
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
docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/inject_one_cleansing_failure.sql >/dev/null

run_master run_3_processed_refresh responses_refresh.json 9000003
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
  "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM public.staging_raw WHERE rtrim(url, '/')='https://ssr.fg2.example/programas/analitica-aplicada' AND status='pending') THEN RAISE EXCEPTION 'refresh_pending_rollback_assertion'; END IF; IF (SELECT count(*) FROM public.cleansed_programs) <> 6 THEN RAISE EXCEPTION 'refresh_no_partial_cleansing_assertion'; END IF; END \$\$" >/dev/null
run_worker run_3_cleansing_recovery cleansing_worker.py 9000003
assert_counts 6 6 6 6
run_worker run_3_enrichment enrichment_worker.py 9000003
assert_counts 6 6 6 6
run_worker run_3_sync sync_vector_worker.py 9000003
assert_counts 6 6 6 6

docker exec "$pg" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -c \
  "DO \$\$ BEGIN IF (SELECT count(*) FROM public.staging_raw WHERE status='processed') <> 6 THEN RAISE EXCEPTION 'staging_processed_count_assertion'; END IF; IF (SELECT count(*) FROM public.cleansed_programs WHERE status='enriched') <> 6 THEN RAISE EXCEPTION 'cleansed_enriched_count_assertion'; END IF; IF (SELECT count(*) FROM public.enriched_programs WHERE status='synced') <> 6 THEN RAISE EXCEPTION 'enriched_synced_count_assertion'; END IF; IF (SELECT count(*) FROM public.course_editorial_state WHERE editorial_status='pending_review') <> 5 THEN RAISE EXCEPTION 'pending_editorial_count_assertion'; END IF; IF (SELECT count(*) FROM public.courses_public_effective) <> 0 THEN RAISE EXCEPTION 'public_effective_must_be_empty_assertion'; END IF; IF EXISTS (SELECT 1 FROM public.staging_raw WHERE institution_id='20000000-0000-0000-0000-000000000004') THEN RAISE EXCEPTION 'blocked_source_must_not_create_staging'; END IF; IF NOT EXISTS (SELECT 1 FROM public.institution_site_profiles WHERE institution_id='20000000-0000-0000-0000-000000000005' AND profile_status='pending_review') THEN RAISE EXCEPTION 'ambiguous_profile_must_remain_pending'; END IF; IF NOT EXISTS (SELECT 1 FROM public.course_editorial_state es JOIN public.courses c ON c.id=es.course_id WHERE rtrim(c.url, '/')='https://ssr.fg2.example/programas/analitica-aplicada' AND es.editorial_status='published' AND es.manual_overrides->>'name'='Título manual sintético preservado') THEN RAISE EXCEPTION 'editorial_override_was_not_preserved'; END IF; IF EXISTS (SELECT 1 FROM public.courses WHERE is_active OR is_verified OR is_mock_data IS DISTINCT FROM true) THEN RAISE EXCEPTION 'new_mock_courses_public_eligibility_assertion'; END IF; END \$\$" >/dev/null

# The same HTTP route and budget serve HTTP, browser navigation and scripts.
# A 429 response is recorded once per blocked cohort run; no request is retried.
docker run "${common_docker_args[@]}" --env GITHUB_RUN_ID=9000003 \
  "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/fg2_full_pipeline_pg17/verify_admin_queue.py \
  >"$out/admin.log" 2>&1 || { cat "$out/admin.log"; fail admin_queue ADMIN_RPC_OR_PUBLIC_VIEW_ASSERTION; }
grep -E '^phase=admin_queue_rpc\|' "$out/admin.log"

docker run --pull=never --rm --network none --read-only \
  --tmpfs "/tmp:rw,noexec,nosuid,size=32m" \
  --mount "type=bind,src=$events,dst=/run/fg2-http-events.jsonl,readonly" \
  "$APP_IMAGE" /opt/venv/bin/python - /run/fg2-http-events.jsonl <<'PY'
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
if blocked_per_run != Counter({"9000001": 1, "9000002": 1, "9000003": 1}):
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=blocked_retry_or_selection_count")
spa_script=[event for event in http_events if event.get("host") == "spa.fg2.example" and event.get("path") == "/assets/catalogo.js"]
catalog_pages=[event for event in http_events if event.get("host") == "ecommerce.fg2.example" and event.get("path") == "/catalogo/"]
if not spa_script or not any(event.get("query") == "page=1" for event in catalog_pages) or not any(event.get("query") == "page=2" for event in catalog_pages):
    raise SystemExit("phase=synthetic_http_audit|result=FAIL|code=browser_or_pagination_missing")
print(f"phase=synthetic_http_audit|result=PASS|attempts={len(http_events)}|blocked_429={len(blocked)}|blocked_runs={len(blocked_per_run)}|spa_js=observed|ecommerce_pages=2|pinned_config=checked")
PY

printf 'phase=fg2_full_pipeline_pg17|result=PASS|courses=6|pending_review=5|public_effective=0|providers=local_smart_mock\n'
printf 'phase=limits|result=LOCAL_EVIDENCE_ONLY|network=internal_no_egress|db=ephemeral_pg17|production=untouched\n'
