#!/usr/bin/env bash
set -Eeuo pipefail
exec 3>&1
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly EVIDENCE="$ROOT/.context/evidencia/h3req1_docker_candidate_cleanup_v6_once_2026-10-09.log"
readonly CANDIDATE_ID='500931b0f086d29ec9e751e1fd652f9b7ccd357f3eb64daa8751344776162049'
readonly ORIGINAL_ID='115d4041bf3f23a5fcb109a4a33bf3a9abf038e72655040f676aa5cb0c89a68a'
readonly IMAGE_ID='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly R4_LOG='.context/evidencia/h3req1_c03_integrated_run_2026-10-06_r4.log'
readonly R4_LOG_SHA256='208e42cb55cd7de5d74a9960655ac3cdec6accbeab1fc5f00a7a3e8eb047eb34'
CURRENT_PHASE='preflight'

if [[ -e "$EVIDENCE" ]]; then
  printf 'phase=preflight|error_code=EVIDENCE_ALREADY_EXISTS\n'
  exit 1
fi
: > "$EVIDENCE" || { printf 'phase=preflight|error_code=EVIDENCE_CREATE_FAILED\n'; exit 1; }
record_phase() {
  local phase="$1" code="$2"
  [[ "$phase" =~ ^[a-z][a-z0-9-]{0,47}$ && "$code" =~ ^[A-Z][A-Z0-9_]{0,47}$ ]] || return 1
  printf 'phase=%s|error_code=%s\n' "$phase" "$code" | tee -a "$EVIDENCE" >&3
}
on_error() {
  local status=$?
  trap - ERR
  record_phase "$CURRENT_PHASE" COMMAND_FAILED || true
  return "$status"
}
on_exit() {
  local status=$?
  trap - EXIT ERR
  record_phase runner-exit "EXIT_$status" || true
  exit "$status"
}
trap on_error ERR
trap on_exit EXIT
trap 'exit 124' TERM
trap 'exit 130' INT

if (( EUID == 0 )); then record_phase preflight RUN_AS_WSL_USER; exit 1; fi
if [[ ! -t 0 ]]; then record_phase preflight INTERACTIVE_TTY_REQUIRED; exit 1; fi
if [[ "$(uname -s 2>/dev/null)" != Linux || "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" != *microsoft* ]]; then
  record_phase preflight WSL_REQUIRED; exit 1
fi
cd "$ROOT"
if [[ "$(git branch --show-current 2>/dev/null)" != 'feat/h3req1-sync-20261002' ||
      "$(git rev-parse HEAD 2>/dev/null)" != '4eb4d877a50b012bb630a129bd0c74482c33be9c' ]]; then
  record_phase candidate-identity MISMATCH; exit 1
fi
wip_counts="$(python3 - <<'PY'
import subprocess
raw = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z'])
entries = [entry for entry in raw.split(b'\0') if entry]
tracked = sum(entry[:2] != b'??' for entry in entries)
untracked = sum(entry[:2] == b'??' for entry in entries)
staged = sum(entry[:1] not in (b' ', b'?') for entry in entries)
print(f'{tracked}/{untracked}/{staged}')
PY
)"
if [[ "$wip_counts" != '55/269/0' ]]; then record_phase candidate-wip STATUS_DRIFT; exit 1; fi
record_phase candidate-wip OK
if [[ "$(docker context show 2>/dev/null)" != default ]]; then record_phase docker-context MISMATCH; exit 1; fi
if [[ "$(docker image inspect --format '{{.Id}}' studiamatch-h3req1:20261009-v3 2>/dev/null)" != "$IMAGE_ID" ]]; then
  record_phase candidate-image IMAGE_MISMATCH; exit 1
fi
candidate="$(docker inspect --format '{{.Id}}|{{.Image}}|{{.Config.Image}}|{{.State.Status}}|{{.State.Health.Status}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.service"}}' studiamatch-dev 2>/dev/null)"
if [[ "$candidate" != "$CANDIDATE_ID|$IMAGE_ID|studiamatch-h3req1:20261009-v3|running|healthy|studiamatch-h3req1|app" ]]; then
  record_phase candidate-runtime IDENTITY_OR_HEALTH_MISMATCH; exit 1
fi
candidate_mounts="$(docker inspect --format '{{range .Mounts}}{{if eq .Type "bind"}}bind|{{.Source}}|{{.Destination}}|{{.RW}}{{else if eq .Type "volume"}}volume|{{.Name}}|{{.Destination}}|{{.RW}}{{else}}other|{{.Type}}|{{.Destination}}|{{.RW}}{{end}};{{end}}' studiamatch-dev 2>/dev/null | tr ';' '\n' | sed '/^$/d' | sort)"
expected_candidate_mounts="$(printf '%s\n' 'bind|/home/romel/src/studiamatch-h3req1-sync-20261002|/app|true' 'volume|studiamatch_h3req1_node_modules|/app/web/node_modules|true' | sort)"
if [[ "$candidate_mounts" != "$expected_candidate_mounts" ]]; then record_phase candidate-runtime MOUNT_MISMATCH; exit 1; fi
deps="$(docker inspect --format '{{.Id}}|{{.Image}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.service"}}' studiamatch-h3req1-node-deps 2>/dev/null)"
if [[ "$deps" != '1e9d942bd3236b9a2cb860976d7254583ef4ede953529e87b5a61cb67422e3d9|sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63|studiamatch-h3req1:20261009-v3|exited|0|studiamatch-h3req1|node-deps' ]]; then
  record_phase candidate-deps IDENTITY_MISMATCH; exit 1
fi
original="$(docker inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.HostConfig.RestartPolicy.Name}}' "$ORIGINAL_ID" 2>/dev/null)"
if [[ "$original" != "$ORIGINAL_ID|/studiamatch-original-dev-20261009|studiamatch-dev:local|exited|1|no" ]]; then
  record_phase original-rollback IDENTITY_MISMATCH; exit 1
fi
original_mounts="$(docker inspect --format '{{range .Mounts}}{{if eq .Type "bind"}}bind|{{.Source}}|{{.Destination}}|{{.RW}}{{else if eq .Type "volume"}}volume|{{.Name}}|{{.Destination}}|{{.RW}}{{end}};{{end}}' "$ORIGINAL_ID" 2>/dev/null | tr ';' '\n' | sed '/^$/d' | sort)"
expected_original_mounts="$(printf '%s\n' 'bind|/home/romel/src/studiamatch|/app|true' 'volume|studiamatch_node_modules|/app/web/node_modules|true' | sort)"
if [[ "$original_mounts" != "$expected_original_mounts" ]]; then record_phase original-rollback MOUNT_MISMATCH; exit 1; fi
r4_log_hash="$(sha256sum "$R4_LOG" 2>/dev/null | cut -d' ' -f1)"
if [[ "$r4_log_hash" != "$R4_LOG_SHA256" ]]; then record_phase cleanup-preflight R4_EVIDENCE_HASH_MISMATCH; exit 1; fi

verify_container() {
  local id="$1" expected="$2" actual
  actual="$(docker inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.RestartCount}}' "$id" 2>/dev/null)"
  if [[ "$actual" != "$expected" ]]; then record_phase cleanup-preflight CONTAINER_MISMATCH; exit 1; fi
}
verify_no_named_volumes() {
  local id="$1" volumes
  volumes="$(docker inspect --format '{{range .Mounts}}{{if eq .Type "volume"}}volume;{{end}}{{end}}' "$id" 2>/dev/null)"
  if [[ -n "$volumes" ]]; then record_phase cleanup-preflight UNEXPECTED_VOLUME; exit 1; fi
}
verify_mount_map() {
  local id="$1" expected="$2" actual
  actual="$(docker inspect --format '{{range .Mounts}}{{.Type}}|{{.Name}}|{{.Destination}}|{{.RW}};{{end}}' "$id" 2>/dev/null | tr ';' '\n' | sed '/^$/d' | sort)"
  expected="$(printf '%s\n' "$expected" | sed '/^$/d' | sort)"
  if [[ "$actual" != "$expected" ]]; then record_phase cleanup-preflight VOLUME_MAP_MISMATCH; exit 1; fi
}
verify_network() {
  local name="$1" expected_id="$2" actual
  actual="$(docker network inspect --format '{{.Id}}|{{.Internal}}|{{len .Containers}}' "$name" 2>/dev/null)"
  if [[ "$actual" != "$expected_id|true|0" ]]; then record_phase cleanup-preflight NETWORK_MISMATCH; exit 1; fi
}

CURRENT_PHASE='cleanup-preflight'
verify_container 8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c '8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c|/h3req1-node22-jit-20261005|node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844f|exited|255|0'
verify_container 544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 '544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02|/h3req1-node22-jit-v2-20261005|node:22@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844f|exited|255|0'
verify_container 51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a '51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a|/h3req1-pg17-jit-v3-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
verify_container 4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 '4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27|/h3req1-pg17-jit-v4-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
verify_container 4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 '4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6|/h3req1-postgrest-jit-20261005|postgrest/postgrest:v13.0.7@sha256:0a46780309a604cdc8b56c776c6e5e15788ce58174d709e40459ab5a2d44d228|exited|255|0'
verify_container 88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d '88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d|/h3req1-c03-safe-suspend-pg17-20261005|postgres@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f|exited|255|0'
for id in 8e0a4df5074c7a62a1dcd80731e55b8035d8451594f95ae7e605676db7e2103c 544616a0c1b601d3d2adff49655182da3566ffe5018ddea192aa919b98ac0d02 51b1967bc60a37747671f161c091bf07d225447d2b0f5f564d8de9fbeae73f9a 4e26f117f76eab6ab3e6adbe3fd328ff8b463ffaef677f460d83be5c86314b27 4cbde5dbc489032b8ce142d5c03457d852118e3f595e8b0afd5370d9f52aecf6 88aa68bc11372f5efad73e114be1e5fea822754bf525907d180a8ba46b643d2d; do verify_no_named_volumes "$id"; done
verify_container dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 'dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36|/h3req1-c03-bootstrap-miniflare-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844f|exited|0|0'
verify_mount_map dec76d0a52f9c651e528f012636941ef951e477442eac923af9c999293369f36 $'volume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/out|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container 8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb '8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb|/h3req1-c03-bootstrap-pages-deps-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844f|exited|0|0'
verify_mount_map 8cf1e6278cf9339b5c7e86f0caf64a29a1ae6a10d3b1b54fd9e5819a0c822beb $'volume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/out|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 'd6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929|/h3req1-c03-bootstrap-edge-deps-20261006-r5|denoland/deno:2.1.4@sha256:bc48369c9b1810da957cabcac234094a691f94cb6cd0e88d533ccac89f2f0cb9|exited|0|0'
verify_mount_map d6a26afbaf943b58d6f0f529331139dad4efff47f2509371229f817b03e0c929 $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|true\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/source/supabase/functions/admin-invite/node_modules|true\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container 94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 '94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4|/h3req1-c03-dependency-cache-verify-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844f|exited|0|0'
verify_mount_map 94ef3d0b9ff6ae48db00d75a222f2dd85a63c5a2bcb61354a816d9011c18d0e4 $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|false\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/edge-node-modules|false\nvolume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/tools|false\nvolume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/web-deps|false\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/source|false'
verify_container e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4 'e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4|/h3req1-c03-source-snapshot-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844f|exited|0|0'
verify_mount_map e5e9cf70424f8fc756c455cdf841822b61027e0ffa0a7b28b68f428148ae3dd4 $'volume|h3req1-c03-integrated-source-snapshot-20261006-r4|/snapshot|true'
verify_container b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f 'b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f|/h3req1-c03-integrated-runtime-20261006-r4|node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844f|exited|1|0'
verify_mount_map b8aff87745e80a82265be0019be5530e9173fc621ab3ff47754f85e933a1508f $'volume|h3req1-c03-integrated-edge-deno-cache-20261006-r5|/deno-cache|false\nvolume|h3req1-c03-integrated-edge-node-modules-20261006-r5|/candidate/supabase/functions/admin-invite/node_modules|false\nvolume|h3req1-c03-integrated-miniflare-node-modules-20261006-r4|/tools|false\nvolume|h3req1-c03-integrated-pages-node-modules-20261006-r4|/web-deps|false\nvolume|h3req1-c03-integrated-source-snapshot-20261006-r4|/candidate|false\nvolume|h3req1-c03-integrated-tls-20261006-r4|/run/c03-certs|true'
for entry in \
  'h3req1-jit-internal-20261005|f54379669c125d32f02120b0c0f74d07b56cf3df8c973a3ae6c869e0cf8646b9' \
  'h3req1-jit-internal-v3-20261005|da6a40654b6cc5af86a38b9df73fe873814a0b249f1ded6d03ed5426ca4ddbe7' \
  'h3req1-jit-internal-v4-20261005|f8851397653ad3eb5f013331de5bb947a6b74f338ba813c3fb233855a73daa3c'; do
  IFS='|' read -r name id <<< "$entry"
  network="$(docker network inspect --format '{{.Id}}|{{.Internal}}|{{len .Containers}}' "$name" 2>/dev/null)"
  if [[ "$network" != "$id|true|0" ]]; then record_phase cleanup-preflight NETWORK_MISMATCH; exit 1; fi
done
record_phase cleanup-preflight OK

CURRENT_PHASE='historical-cleanup'
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
  if docker rm "$id" >/dev/null 2>&1; then record_phase "cleanup-container-$(printf '%02d' "$ordinal")" OK
  else record_phase "cleanup-container-$(printf '%02d' "$ordinal")" REMOVE_FAILED; exit 1; fi
done
ordinal=0
for name in h3req1-jit-internal-20261005 h3req1-jit-internal-v3-20261005 h3req1-jit-internal-v4-20261005; do
  ordinal=$((ordinal + 1))
  if docker network rm "$name" >/dev/null 2>&1; then record_phase "cleanup-network-$(printf '%02d' "$ordinal")" OK
  else record_phase "cleanup-network-$(printf '%02d' "$ordinal")" REMOVE_FAILED; exit 1; fi
done
record_phase cleanup OK
record_phase dispatch-complete OK
