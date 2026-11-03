#!/usr/bin/env bash
set -Eeuo pipefail
exec 3>&1
CURRENT_PHASE='preflight'
CUTOVER_ACTIVE=0
CUTOVER_COMPLETE=0
report_error() {
  local status=$?
  trap - ERR
  printf 'phase=%s|error_code=COMMAND_FAILED\n' "$CURRENT_PHASE" >&3
  return "$status"
}
trap report_error ERR
trap 'exit 124' TERM
trap 'exit 130' INT
set -Eeuo pipefail
readonly CANDIDATE='/home/romel/src/studiamatch-h3req1-sync-20261002'
cd "$CANDIDATE"
[[ "$(git branch --show-current)" == 'feat/h3req1-sync-20261002' ]]
[[ "$(git rev-parse HEAD)" == '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]]
python3 - <<'PY'
import subprocess
raw=subprocess.check_output(['git','status','--porcelain=v1','-z'])
entries=[e for e in raw.split(b'\0') if e]
tracked=sum(e[:2] != b'??' for e in entries)
untracked=sum(e[:2] == b'??' for e in entries)
staged=sum(e[:1] not in (b' ',b'?') for e in entries)
if (tracked,untracked,staged) != (54,235,0):
    print('phase=candidate-wip|error_code=STATUS_DRIFT')
    raise SystemExit(1)
print('phase=candidate-wip|error_code=OK')
PY
sha256sum -c <(cat <<'HASHES'
34dc73ac9e5548b7c794e0987b8b2681ce26458a61b7d372f1146a4613f2f1c4  Dockerfile
8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca  init-container.sh
922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0  requirements-pipeline.txt
4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a  web/package.json
8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc  web/package-lock.json
70ecf0a27054cec54151eee1b01957450f70abf6be6a6019e35104d7bb681575  docker-compose.yml
32997839538f071219fe6174f3d20f2a0481ecb25b25e1cc3816f53d19fd48c0  .context/operaciones/h3req1_docker_candidate_override_2026-10-09.yml
HASHES
)
[[ "$(docker image inspect --format '{{.Id}}' node:20-bookworm)" == \
  'sha256:8f693eaa7e0a8e71560c9a82b55fd54c2ae920a2ba5d2cde28bac7d1c01c9ba5' ]]
if docker image inspect studiamatch-h3req1:20261009-v1 >/dev/null 2>&1; then exit 1; fi
if docker volume inspect studiamatch_h3req1_node_modules >/dev/null 2>&1; then exit 1; fi
if docker network inspect studiamatch-h3req1_default >/dev/null 2>&1; then exit 1; fi
for name in studiamatch-h3req1-node-deps studiamatch-original-dev-20261009 \
  studiamatch-h3req1-failed-20261009; do
  if docker inspect "$name" >/dev/null 2>&1; then exit 1; fi
done
readonly OLD_ID='115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a'
[[ "$(docker inspect --format '{{.Id}}|{{.Config.Image}}|{{.HostConfig.RestartPolicy.Name}}' studiamatch-dev)" == \
  "$OLD_ID|studiamatch-dev:local|unless-stopped" ]]
mounts="$(docker inspect --format '{{range .Mounts}}{{.Type}}|{{.Source}}|{{.Destination}};{{end}}' "$OLD_ID")"
[[ "$mounts" == *'bind|/home/romel/src/studiamatch|/app;'* ]]
[[ "$mounts" == *'volume|/var/lib/docker/volumes/studiamatch_node_modules/_data|/app/web/node_modules;'* ]]
published="$(docker ps --no-trunc --filter publish=3000 --format '{{.ID}}' | sort -u)"
[[ -z "$published" || "$published" == "$OLD_ID" ]]


printf 'phase=preflight|error_code=OK\n' >&3
CURRENT_PHASE='build-context'
set -Eeuo pipefail
readonly BUILD_CONTEXT="$(mktemp -d /tmp/h3req1-docker-build-v1.XXXXXX)"
readonly INPUT_MANIFEST="${BUILD_CONTEXT}.inputs.sha256"
mkdir -p "$BUILD_CONTEXT/web"
cp -- "$CANDIDATE/Dockerfile" "$CANDIDATE/init-container.sh" \
  "$CANDIDATE/requirements-pipeline.txt" "$BUILD_CONTEXT/"
cp -- "$CANDIDATE/web/package.json" "$CANDIDATE/web/package-lock.json" \
  "$BUILD_CONTEXT/web/"
(
  cd "$CANDIDATE"
  sha256sum -c <(cat <<'HASHES'
34dc73ac9e5548b7c794e0987b8b2681ce26458a61b7d372f1146a4613f2f1c4  Dockerfile
8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca  init-container.sh
922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0  requirements-pipeline.txt
4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a  web/package.json
8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc  web/package-lock.json
HASHES
  )
)
(
  cd "$BUILD_CONTEXT"
  sha256sum -c <(cat <<'HASHES'
34dc73ac9e5548b7c794e0987b8b2681ce26458a61b7d372f1146a4613f2f1c4  Dockerfile
8dd14ad53e9b23b6741786f1b2716707b2577d78d2e2791a68f1f95deaa173ca  init-container.sh
922db6ec7a6cf13978ab9e3f27ecc4e82b3e1d8807c0b519cea0ab7608ba1bf0  requirements-pipeline.txt
4567e008756097437c0ef586f1c112c97db3a198bcd521bd62e8342242f7cd8a  web/package.json
8bd9c50605a8ce92e87b0ad81e4513fd47fc01ca328079eef792d264c2a292bc  web/package-lock.json
HASHES
  )
  sha256sum Dockerfile init-container.sh requirements-pipeline.txt \
    web/package.json web/package-lock.json > "$INPUT_MANIFEST"
  sha256sum -c "$INPUT_MANIFEST"
)


printf 'phase=build-context|error_code=OK\n' >&3
CURRENT_PHASE='image-build'
/usr/bin/timeout --foreground --signal=TERM --kill-after=10s 1800s \
  docker build --pull=false --build-arg STUDIAMATCH_UID=1000 --build-arg STUDIAMATCH_GID=1000 \
  --tag studiamatch-h3req1:20261009-v1 "$BUILD_CONTEXT"


printf 'phase=image-build|error_code=OK\n' >&3
CURRENT_PHASE='image-smoke'
/usr/bin/timeout --foreground --signal=TERM --kill-after=5s 60s \
  docker run --rm --pull=never --network=none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m --user 1000:1000 \
  --entrypoint /bin/bash studiamatch-h3req1:20261009-v1 -lc \
  'cd /opt/node-staging/web && printf "%s  %s\n%s  %s\n" 7f42e397a859d7d5108f1f17a613e8722493ecfb368c25dd4a12b0e414e7e7bb package.json a6f707e516fbb0d4dc3067b809573b9ac64d8543c54dfe28998cd13901bf4ccf package-lock.json | sha256sum -c - && node --version && npm --version && /opt/venv/bin/python --version && /opt/venv/bin/python -m playwright --version'


printf 'phase=image-smoke|error_code=OK\n' >&3
rollback_failure() {
  printf 'phase=cutover-rollback|error_code=%s\n' "$1" >&3
  return 1
}
rollback_cutover() {
  local original_projection original_id original_name original_image original_policy
  local candidate_ids candidate_id candidate_identity candidate_mounts expected_mounts candidate_state
  if ! original_projection="$(docker inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.HostConfig.RestartPolicy.Name}}' "$OLD_ID" 2>/dev/null)"; then
    rollback_failure ORIGINAL_READ_FAILED
    return 1
  fi
  IFS='|' read -r original_id original_name original_image original_policy <<< "$original_projection"
  [[ "$original_id" == "$OLD_ID" && "$original_image" == 'studiamatch-dev:local' ]] || {
    rollback_failure ORIGINAL_IDENTITY_MISMATCH
    return 1
  }
  [[ "$original_name" == '/studiamatch-dev' || "$original_name" == '/studiamatch-original-dev-20261009' ]] || {
    rollback_failure ORIGINAL_NAME_MISMATCH
    return 1
  }
  [[ "$original_policy" == 'no' || "$original_policy" == 'unless-stopped' ]] || {
    rollback_failure ORIGINAL_POLICY_MISMATCH
    return 1
  }
  if ! candidate_ids="$(docker ps -a --no-trunc --filter 'name=^/studiamatch-dev$' --format '{{.ID}}' 2>/dev/null)"; then
    rollback_failure CANDIDATE_LIST_FAILED
    return 1
  fi
  if [[ -n "$candidate_ids" && "$candidate_ids" != "$OLD_ID" ]]; then
    [[ "$candidate_ids" =~ ^[0-9a-f]{64}$ ]] || {
      rollback_failure CANDIDATE_ID_AMBIGUOUS
      return 1
    }
    candidate_id="$candidate_ids"
    if ! candidate_identity="$(docker inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.service"}}' "$candidate_id" 2>/dev/null)"; then
      rollback_failure CANDIDATE_READ_FAILED
      return 1
    fi
    [[ "$candidate_identity" == "$candidate_id|/studiamatch-dev|studiamatch-h3req1:20261009-v1|studiamatch-h3req1|app" ]] || {
      rollback_failure CANDIDATE_IDENTITY_MISMATCH
      return 1
    }
    if ! candidate_mounts="$(docker inspect --format '{{range .Mounts}}{{if eq .Type "bind"}}bind|{{.Source}}|{{.Destination}}{{else if eq .Type "volume"}}volume|{{.Name}}|{{.Destination}}{{else}}other|{{.Type}}|{{.Destination}}{{end}};{{end}}' "$candidate_id" 2>/dev/null | tr ';' '\n' | sed '/^$/d' | sort)"; then
      rollback_failure CANDIDATE_MOUNT_READ_FAILED
      return 1
    fi
    expected_mounts="$(printf '%s\n' \
      'bind|/home/romel/src/studiamatch-h3req1-sync-20261002|/app' \
      'volume|studiamatch_h3req1_node_modules|/app/web/node_modules' | sort)"
    [[ "$candidate_mounts" == "$expected_mounts" ]] || {
      rollback_failure CANDIDATE_MOUNT_MISMATCH
      return 1
    }
    [[ "$original_name" == '/studiamatch-original-dev-20261009' ]] || {
      rollback_failure ORIGINAL_RENAME_STATE_MISMATCH
      return 1
    }
    if docker inspect studiamatch-h3req1-failed-20261009 >/dev/null 2>&1; then
      rollback_failure FAILED_NAME_COLLISION
      return 1
    fi
    if ! candidate_state="$(docker inspect --format '{{.State.Status}}' "$candidate_id" 2>/dev/null)"; then
      rollback_failure CANDIDATE_STATE_READ_FAILED
      return 1
    fi
    case "$candidate_state" in
      running|restarting)
        if ! docker stop --time 10 "$candidate_id" >/dev/null 2>&1; then
          rollback_failure CANDIDATE_STOP_FAILED
          return 1
        fi
        ;;
      created|exited) ;;
      *) rollback_failure CANDIDATE_STATE_MISMATCH; return 1 ;;
    esac
    if ! docker rename "$candidate_id" studiamatch-h3req1-failed-20261009 >/dev/null 2>&1; then
      rollback_failure CANDIDATE_RENAME_FAILED
      return 1
    fi
  fi
  if [[ "$original_name" == '/studiamatch-original-dev-20261009' ]]; then
    if docker inspect studiamatch-dev >/dev/null 2>&1; then
      rollback_failure DEV_NAME_OCCUPIED
      return 1
    fi
    if ! docker rename "$OLD_ID" studiamatch-dev >/dev/null 2>&1; then
      rollback_failure ORIGINAL_RENAME_FAILED
      return 1
    fi
  fi
  if ! docker update --restart=unless-stopped "$OLD_ID" >/dev/null 2>&1; then
    rollback_failure ORIGINAL_POLICY_RESTORE_FAILED
    return 1
  fi
  if ! original_projection="$(docker inspect --format '{{.State.Status}}' "$OLD_ID" 2>/dev/null)"; then
    rollback_failure ORIGINAL_STATE_READ_FAILED
    return 1
  fi
  case "$original_projection" in
    running|restarting) ;;
    created|exited)
      if ! docker start "$OLD_ID" >/dev/null 2>&1; then
        rollback_failure ORIGINAL_START_FAILED
        return 1
      fi
      ;;
    *) rollback_failure ORIGINAL_STATE_MISMATCH; return 1 ;;
  esac
  printf 'phase=cutover-rollback|error_code=RESTORED_ORIGINAL\n' >&3
}
on_exit() {
  local status=$?
  trap - EXIT ERR
  if (( CUTOVER_ACTIVE == 1 && CUTOVER_COMPLETE == 0 )); then
    if ! rollback_cutover; then
      printf 'phase=cutover-rollback|error_code=RECOVERY_INCOMPLETE\n' >&3
    fi
    (( status != 0 )) || status=1
  fi
  exit "$status"
}
trap on_exit EXIT
CUTOVER_ACTIVE=1
CURRENT_PHASE='cutover'
docker update --restart=no 115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a
docker stop --time 10 115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a
docker rename 115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a studiamatch-original-dev-20261009
STUDIAMATCH_UID=1000 STUDIAMATCH_GID=1000 docker compose --env-file /dev/null \
  -p studiamatch-h3req1 -f docker-compose.yml \
  -f .context/operaciones/h3req1_docker_candidate_override_2026-10-09.yml \
  up -d --no-build node-deps app


printf 'phase=cutover|error_code=COMMANDS_OK\n' >&3
CURRENT_PHASE='healthcheck'
deadline=$((SECONDS + 180))
while :; do
  health="$(docker inspect --format '{{.State.Health.Status}}' studiamatch-dev 2>/dev/null || true)"
  if [[ "$health" == healthy ]]; then
    printf 'phase=candidate-health|error_code=OK\n'
    break
  fi
  if [[ "$health" == unhealthy || "$health" == '' || $SECONDS -ge $deadline ]]; then
    printf 'phase=candidate-health|error_code=HEALTHCHECK_FAILED\n'
    exit 1
  fi
  sleep 5
done


CUTOVER_COMPLETE=1
CUTOVER_ACTIVE=0
printf 'phase=cutover-complete|error_code=OK\n' >&3
CURRENT_PHASE='temporary-cleanup'
[[ "$BUILD_CONTEXT" == /tmp/h3req1-docker-build-v1.* && -d "$BUILD_CONTEXT" ]] || exit 1
[[ "$INPUT_MANIFEST" == /tmp/h3req1-docker-build-v1.*.inputs.sha256 && -f "$INPUT_MANIFEST" ]] || exit 1
rm -rf -- "$BUILD_CONTEXT"
rm -f -- "$INPUT_MANIFEST"
STUDIAMATCH_UID=1000 STUDIAMATCH_GID=1000 docker compose --env-file /dev/null \
  -p studiamatch-h3req1 -f docker-compose.yml \
  -f .context/operaciones/h3req1_docker_candidate_override_2026-10-09.yml \
  rm -f node-deps


printf 'phase=temporary-cleanup|error_code=OK\n' >&3
CURRENT_PHASE='historical-cleanup'
set -Eeuo pipefail
readonly R4_LOG='.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log'
readonly R4_LOG_SHA256='208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34'
r4_log_hash="$(sha256sum "$R4_LOG" 2>/dev/null | cut -d' ' -f1)" || {
  printf 'phase=cleanup-preflight|error_code=R4_EVIDENCE_READ_FAILED\n'
  exit 1
}
[[ "$r4_log_hash" == "$R4_LOG_SHA256" ]] || {
  printf 'phase=cleanup-preflight|error_code=R4_EVIDENCE_HASH_MISMATCH\n'
  exit 1
}

verify_container() {
  local id="$1" expected="$2" actual
  if ! actual="$(docker inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.RestartCount}}' "$id" 2>/dev/null)"; then
    printf 'phase=cleanup-preflight|error_code=CONTAINER_READ_FAILED\n'
    return 1
  fi
  if [[ "$actual" != "$expected" ]]; then
    printf 'phase=cleanup-preflight|error_code=CONTAINER_MISMATCH\n'
    return 1
  fi
}
verify_no_named_volumes() {
  local id="$1" volumes
  if ! volumes="$(docker inspect --format '{{range .Mounts}}{{if eq .Type "volume"}}volume;{{end}}{{end}}' "$id" 2>/dev/null)"; then
    printf 'phase=cleanup-preflight|error_code=MOUNT_READ_FAILED\n'
    return 1
  fi
  if [[ -n "$volumes" ]]; then
    printf 'phase=cleanup-preflight|error_code=UNEXPECTED_VOLUME\n'
    return 1
  fi
}
verify_mount_map() {
  local id="$1" expected="$2" actual
  if ! actual="$(docker inspect --format '{{range .Mounts}}{{.Type}}|{{.Name}}|{{.Destination}}|{{.RW}};{{end}}' "$id" 2>/dev/null | tr ';' '\n' | sed '/^$/d' | sort)"; then
    printf 'phase=cleanup-preflight|error_code=MOUNT_READ_FAILED\n'
    return 1
  fi
  expected="$(printf '%s\n' "$expected" | sed '/^$/d' | sort)"
  if [[ "$actual" != "$expected" ]]; then
    printf 'phase=cleanup-preflight|error_code=VOLUME_MAP_MISMATCH\n'
    return 1
  fi
}
verify_network() {
  local name="$1" expected_id="$2" actual
  if ! actual="$(docker network inspect --format '{{.Id}}|{{.Internal}}|{{len .Containers}}' "$name" 2>/dev/null)"; then
    printf 'phase=cleanup-preflight|error_code=NETWORK_READ_FAILED\n'
    return 1
  fi
  if [[ "$actual" != "$expected_id|true|0" ]]; then
    printf 'phase=cleanup-preflight|error_code=NETWORK_MISMATCH\n'
    return 1
  fi
}

verify_container 8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c \
  '8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c|/h3req1-node22-jit-20261005|node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|255|0'
verify_container 544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 \
  '544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02|/h3req1-node22-jit-v2-20261005|node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|255|0'
verify_container 51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a \
  '51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a|/h3req1-pg17-jit-v3-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
verify_container 4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 \
  '4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27|/h3req1-pg17-jit-v4-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
verify_container 4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 \
  '4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6|/h3req1-postgrest-jit-20261005|postgrest/postgrest:v13.0.7@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228|exited|255|0'
verify_container 88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d \
  '88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d|/h3req1-c03-safe-suspend-pg17-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
for id in 8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c \
  544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 \
  51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a \
  4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 \
  4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 \
  88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d; do
  verify_no_named_volumes "$id"
done
verify_container dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 \
  'dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36|/h3req1-c03-bootstrap-miniflare-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 $'volume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/out|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container 8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb \
  '8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb|/h3req1-c03-bootstrap-pages-deps-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map 8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb $'volume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/out|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 \
  'd6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929|/h3req1-c03-bootstrap-edge-deps-20261006-r5|denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9|exited|0|0'
verify_mount_map d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|true\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/source/supabase/functions/admin-invite/node_modules|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|true'
verify_container 94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 \
  '94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4|/h3req1-c03-dependency-cache-verify-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map 94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|false\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/edge-node-modules|false\nvolume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/tools|false\nvolume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/web-deps|false\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4 \
  'e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4|/h3req1-c03-source-snapshot-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|0|0'
verify_mount_map e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4 $'volume|h3req1-c03-integrated-source-snapshot-20261006-r4|/snapshot|true'
verify_container b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f \
  'b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f|/h3req1-c03-integrated-runtime-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844|exited|1|0'
verify_mount_map b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|false\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/candidate/supabase/functions/admin-invite/node_modules|false\nvolume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/tools|false\nvolume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/web-deps|false\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/candidate|false\nvolume|h3req1-c03-integrated-tls-20261006-r4|/run/c03-certs|true'

verify_network h3req1-jit-internal-20261005 f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9
verify_network h3req1-jit-internal-v3-20261005 da6a40654b6cc5af86a38b9df73fe873814a0b249f1ded6d03ed5426ca4ddbe7
verify_network h3req1-jit-internal-v4-20261005 f8851397653ad3eb5f013331de5bb947a6b74f338ba813c3fb233855a73daa3c
verify_network h3req1-c03-integrated-edge-20261006-r4 b1f633b40c7b11bdce27eed62eecade67609b66fc327ffd6e92d413788cd78dc
verify_network h3req1-c03-integrated-data-20261006-r4 da562797a7a6323bde4094cf08905f4f8f7f20cbdc4f498eb34425b07219ca75
printf 'phase=cleanup-preflight|error_code=OK\n'

cleanup_container() {
  local id="$1" ordinal="$2"
  if docker rm "$id" >/dev/null 2>&1; then
    printf 'phase=cleanup-container-%02d|error_code=OK\n' "$ordinal"
  else
    printf 'phase=cleanup-container-%02d|error_code=REMOVE_FAILED\n' "$ordinal"
    return 1
  fi
}
ordinal=0
for id in \
  8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c \
  544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 \
  51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a \
  4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 \
  4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 \
  88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d \
  dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 \
  8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb \
  d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 \
  94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 \
  e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4; do
  ordinal=$((ordinal + 1))
  cleanup_container "$id" "$ordinal"
done

cleanup_network() {
  local name="$1" ordinal="$2"
  if docker network rm "$name" >/dev/null 2>&1; then
    printf 'phase=cleanup-network-%02d|error_code=OK\n' "$ordinal"
  else
    printf 'phase=cleanup-network-%02d|error_code=REMOVE_FAILED\n' "$ordinal"
    return 1
  fi
}
ordinal=0
for network in \
  h3req1-jit-internal-20261005 \
  h3req1-jit-internal-v3-20261005 \
  h3req1-jit-internal-v4-20261005 \
  h3req1-c03-integrated-edge-20261006-r4 \
  h3req1-c03-integrated-data-20261006-r4; do
  ordinal=$((ordinal + 1))
  cleanup_network "$network" "$ordinal"
done
printf 'phase=cleanup|error_code=OK\n'


printf 'phase=dispatch-complete|error_code=OK\n' >&3
