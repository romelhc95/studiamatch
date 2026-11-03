#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly ROOT
readonly NET='h3req1-g09-pipeline-postgrest-r147-net'
readonly PG='h3req1-g09-pipeline-postgrest-r147-pg17'
readonly PGRST='h3req1-g09-pipeline-postgrest-r147-postgrest'
readonly PG_IMAGE='sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f'
readonly PGRST_IMAGE='sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228'
readonly APP_IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly DATABASE='h3_pipeline_postgrest_r1'
readonly APP_ENV_ALLOWLIST=$'DEBIAN_FRONTEND\nHOME\nNODE_VERSION\nPATH\nPIP_DISABLE_PIP_VERSION_CHECK\nPIP_NO_CACHE_DIR\nPLAYWRIGHT_BROWSERS_PATH\nPYTHONUNBUFFERED\nSTUDIAMATCH_GID\nSTUDIAMATCH_UID\nYARN_VERSION'

fail() {
  printf 'phase=preflight|result=FAIL|code=%s\n' "$1"
  exit 2
}

for image in "$PG_IMAGE" "$PGRST_IMAGE" "$APP_IMAGE"; do
  docker image inspect "$image" >/dev/null 2>&1 || fail IMAGE_PIN_NOT_LOCAL
done
APP_ENV_NAMES="$(docker image inspect --format '{{range .Config.Env}}{{println (index (split . "=") 0)}}{{end}}' "$APP_IMAGE" 2>/dev/null)" || fail IMAGE_ENV_METADATA_UNAVAILABLE
APP_ENV_NAMES_SORTED="$(printf '%s\n' "$APP_ENV_NAMES" | sed '/^$/d' | LC_ALL=C sort -u)"
[[ "$APP_ENV_NAMES_SORTED" == "$APP_ENV_ALLOWLIST" ]] || fail IMAGE_ENV_NAME_SET_NOT_ALLOWLISTED
for name in "$NET" "$PG" "$PGRST"; do
  if docker network inspect "$name" >/dev/null 2>&1 || docker container inspect "$name" >/dev/null 2>&1; then
    fail RESOURCE_NAME_ALREADY_EXISTS
  fi
done

NET_ID=''
PG_ID=''
PGRST_ID=''

cleanup() {
  local status=$?
  trap - EXIT
  local owned_containers=()
  [[ -n "$PGRST_ID" ]] && owned_containers+=("$PGRST_ID")
  [[ -n "$PG_ID" ]] && owned_containers+=("$PG_ID")
  if ((${#owned_containers[@]})); then
    docker rm -f "${owned_containers[@]}" >/dev/null 2>&1 || true
  fi
  [[ -n "$NET_ID" ]] && docker network rm "$NET_ID" >/dev/null 2>&1 || true
  exit "$status"
}
trap cleanup EXIT

NET_ID="$(docker network create --internal --driver bridge "$NET")"
PG_ID="$(docker run --pull=never --detach --name "$PG" --network "$NET" --network-alias pg \
  --cpus 2 --memory 4g \
  --tmpfs /var/lib/postgresql/data:rw,noexec,nosuid,size=2g \
  --env POSTGRES_DB="$DATABASE" \
  --env POSTGRES_USER=postgres \
  --env POSTGRES_PASSWORD=h3-local-only-fixture \
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
  "$PG_IMAGE")"

ready=0
for _ in $(seq 1 30); do
  if docker exec "$PG" pg_isready -U postgres -d "$DATABASE" >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
(( ready == 1 )) || fail PG17_READINESS_TIMEOUT
docker exec "$PG" psql -X -U postgres -d "$DATABASE" -v ON_ERROR_STOP=1 -f /fixture/setup.sql >/dev/null
printf 'phase=pg17-bootstrap|result=PASS|postgres=17.11|network=internal\n'

PGRST_ID="$(docker run --pull=never --detach --name "$PGRST" --network "$NET" --network-alias postgrest \
  --cpus 1 --memory 1g --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --env PGRST_DB_URI='postgres://postgres:h3-local-only-fixture@pg:5432/h3_pipeline_postgrest_r1' \
  --env PGRST_DB_SCHEMAS=public --env PGRST_DB_ANON_ROLE=anon \
  --env PGRST_DB_EXTRA_SEARCH_PATH=public,extensions \
  --env PGRST_JWT_SECRET='h3req1-pg17-postgrest-local-fixture-secret' \
  --env PGRST_LOG_LEVEL=error \
  "$PGRST_IMAGE")"

printf 'phase=python-postgrest-pipeline|result=START|image=studiamatch-h3req1-v3|network=internal\n'
timeout --foreground --signal=TERM --kill-after=2s 180s \
  docker run --pull=never --rm --network "$NET" --cpus 2 --memory 4g \
    --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m \
    --user 1000:1000 \
    --workdir /workspace \
    --env PYTHONDONTWRITEBYTECODE=1 --env PYTHON_DOTENV_DISABLED=1 \
    --env PYTHONPATH=/workspace/scripts/core:/workspace/scripts/shared:/workspace \
    --mount "type=bind,src=$ROOT/scripts,dst=/workspace/scripts,readonly" \
    --mount "type=bind,src=$ROOT/tests,dst=/workspace/tests,readonly" \
    "$APP_IMAGE" /opt/venv/bin/python /workspace/tests/h3req1_pipeline_postgrest_pg17_integration.py

printf 'phase=pipeline-postgrest-pg17-r1|result=PASS\n'
