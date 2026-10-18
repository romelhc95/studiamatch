#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-SOURCE-SNAPSHOT-S10-2026-10-10'
readonly RUNNER='tests/h3req1_c03_source_snapshot_s10.sh'
readonly SIDECAR='tests/h3req1-c03-source-snapshot-s10.sha256'
readonly SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v4.sha256'
readonly SOURCE_MANIFEST_SHA256='fdcba48af1ec5ffeba91de0a6fa44022dd3027b85d6b9a5c02afea4c79678233'
readonly EVIDENCE='.context/evidencia/h3req1_c03_source_snapshot_2026-10-10_s10.md'
readonly SOURCE_VOLUME='h3req1-c03-startup-source-20261010-s10'
readonly SNAPSHOT_CONTAINER='h3req1-c03-startup-snapshot-20261010-s10'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly ROOT_EXPECTED='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH_EXPECTED='feat/h3req1-sync-20261002'
readonly HEAD_EXPECTED='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly DOCKER_CONTEXT_EXPECTED='default'
readonly DOCKER_ENDPOINT_EXPECTED='unix:///var/run/docker.sock'
readonly DOCKER_ENGINE_EXPECTED='fc2115b2-c3c4-440e-89c6-26899eb7cb04|docker-desktop|Docker Desktop'
RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}"
readonly RUN_NONCE
readonly CIDFILE_SUFFIX="${BASHPID}-${RANDOM}"

ROOT=''
APPROVED_RUNNER_SHA256=''
APPROVED_SIDECAR_SHA256=''
CIDFILE=''
phase='preflight'
report_open=false
created_container_id=''
container_started=false
exec 3>&1

fail() { printf 'NO-GO: %s\n' "$1" >&2; exit 1; }
docker_control() { timeout --foreground --signal=TERM --kill-after=1s 20s docker "$@" 2>/dev/null; }

stop_owned_container() {
  local metadata id name state jit manifest run
  [[ "$container_started" == true && "$created_container_id" =~ ^[a-f0-9]{64}$ ]] || return 0
  metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}' "$created_container_id")" || return 1
  IFS='|' read -r id name state jit manifest run <<< "$metadata"
  [[ "$id" == "$created_container_id" && "$name" == "/$SNAPSHOT_CONTAINER" \
    && "$jit" == "$JIT" \
    && "$manifest" == "$APPROVED_SIDECAR_SHA256" && "$run" == "$RUN_NONCE" ]] || return 1
  [[ "$state" == running ]] || return 0
  timeout --foreground --signal=TERM --kill-after=1s 10s docker stop --time 5 "$id" >/dev/null 2>&1
}

on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$status" -ne 0 && "$container_started" == true ]]; then
    if stop_owned_container; then printf 'bounded-stop=completed|container-preserved=true\n'; else printf 'bounded-stop=not-performed-or-failed|resource-preserved=true\n'; fi
  fi
  if [[ "$report_open" == true ]]; then
    if [[ "$status" -eq 0 ]]; then printf 'source-snapshot-result=PASS\n' || status=96
    else printf 'source-snapshot-result=NO-GO|phase=%s|exit=%s\n' "$phase" "$status" || status=96; fi
  fi
  printf 'source-snapshot-exit=%s|phase=%s|evidence=%s\n' "$status" "$phase" "$EVIDENCE" >&3 || status=96
  exit "$status"
}
trap on_exit EXIT

[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" \
  && "${3:-}" == '--runner-sha256' && "${5:-}" == '--sidecar-sha256' && $# -eq 6 ]] \
  || fail 'exact JIT, runner SHA-256, and sidecar SHA-256 required'
APPROVED_RUNNER_SHA256="${4:-}"
APPROVED_SIDECAR_SHA256="${6:-}"
[[ "$APPROVED_RUNNER_SHA256" =~ ^[a-f0-9]{64}$ && "$APPROVED_SIDECAR_SHA256" =~ ^[a-f0-9]{64}$ ]] \
  || fail 'invalid approved input hash'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
[[ "$ROOT" == "$ROOT_EXPECTED" ]] || fail 'candidate checkout path changed'
[[ "$(git branch --show-current)" == "$BRANCH_EXPECTED" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$HEAD_EXPECTED" ]] || fail 'candidate HEAD changed'
[[ -d .context/evidencia && ! -L .context && ! -L .context/evidencia ]] || fail 'evidence path missing or symlinked'
[[ ! -e "$EVIDENCE" && ! -L "$EVIDENCE" ]] || fail 'snapshot evidence path already exists'
[[ -f "$RUNNER" && ! -L "$RUNNER" && -f "$SIDECAR" && ! -L "$SIDECAR" \
  && -f "$SOURCE_MANIFEST" && ! -L "$SOURCE_MANIFEST" ]] || fail 'snapshot input missing or symlinked'
[[ "$(sha256sum "$RUNNER" | cut -d' ' -f1)" == "$APPROVED_RUNNER_SHA256" ]] || fail 'runner digest changed'
[[ "$(sha256sum "$SIDECAR" | cut -d' ' -f1)" == "$APPROVED_SIDECAR_SHA256" ]] || fail 'sidecar digest changed'
[[ "$(cat "$SIDECAR")" == "$APPROVED_RUNNER_SHA256  $RUNNER" ]] || fail 'sidecar does not pin runner bytes'
[[ "$(sha256sum "$SOURCE_MANIFEST" | cut -d' ' -f1)" == "$SOURCE_MANIFEST_SHA256" ]] || fail 'source manifest digest changed'
[[ "$(wc -l < "$SOURCE_MANIFEST" | tr -d '[:space:]')" == 13 ]] || fail 'source manifest record count differs'
awk 'NF != 2 || length($1) != 64 || $1 !~ /^[a-f0-9]+$/ || $2 !~ /^[A-Za-z0-9._/-]+$/ || $2 ~ /(^|\/)\.\.?($|\/)/ { exit 1 } END { if (NR != 13) exit 1 }' "$SOURCE_MANIFEST" \
  || fail 'source manifest schema/path validation failed'
sha256sum --check "$SOURCE_MANIFEST" >/dev/null 2>&1 || fail 'candidate inputs differ from source manifest'
total_bytes=0
while IFS=' ' read -r _ source_path; do
  [[ -f "$source_path" && ! -L "$source_path" ]] || fail 'manifest source is missing or symlinked'
  resolved_path="$(realpath -e -- "$source_path")" || fail 'cannot resolve manifest source'
  [[ "$resolved_path" == "$ROOT/$source_path" ]] || fail 'manifest source escapes candidate checkout'
  source_bytes="$(stat -Lc '%s' -- "$source_path")" || fail 'cannot read manifest source size'
  [[ "$source_bytes" =~ ^[0-9]+$ && "$source_bytes" -le 4194304 ]] || fail 'manifest source exceeds 4 MiB bound'
  total_bytes=$((total_bytes + source_bytes))
  (( total_bytes <= 8388608 )) || fail 'manifest source set exceeds 8 MiB bound'
done < "$SOURCE_MANIFEST"
source_mode_manifest="$( {
  while IFS=' ' read -r _ source_path; do
    source_mode="$(stat -Lc '%a' -- "$source_path")" || fail 'cannot read source mode'
    [[ "$source_mode" =~ ^[0-7]{3,4}$ ]] || fail 'source mode is outside the octal schema'
    (( (8#$source_mode & 06000) == 0 )) || fail 'setuid/setgid source mode rejected'
    printf '%s|%s\n' "$source_path" "$source_mode"
  done < "$SOURCE_MANIFEST"
  source_mode="$(stat -Lc '%a' -- "$SOURCE_MANIFEST")" || fail 'cannot read source manifest mode'
  [[ "$source_mode" =~ ^[0-7]{3,4}$ ]] || fail 'source manifest mode is outside the octal schema'
  (( (8#$source_mode & 06000) == 0 )) || fail 'setuid/setgid manifest mode rejected'
  printf '%s|%s\n' "$SOURCE_MANIFEST" "$source_mode"
} | LC_ALL=C sort | tr '\n' ';' )" || fail 'cannot construct source permission manifest'
source_mode_manifest_sha256="$(printf '%s' "$source_mode_manifest" | sha256sum | cut -d' ' -f1)" \
  || fail 'cannot hash source permission manifest'

[[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" \
  && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] || fail 'Docker endpoint override rejected'
context_name="$(docker_control context show)" || fail 'cannot read Docker context'
[[ "$context_name" == "$DOCKER_CONTEXT_EXPECTED" ]] || fail 'Docker context differs from attested Desktop context'
endpoint="$(docker_control context inspect --format '{{ (index .Endpoints "docker").Host }}' "$context_name")" || fail 'cannot read Docker endpoint'
[[ "$endpoint" == "$DOCKER_ENDPOINT_EXPECTED" && -S "${endpoint#unix://}" ]] || fail 'Docker endpoint differs from attested local socket'
engine_identity="$(docker_control info --format '{{.ID}}|{{.Name}}|{{.OperatingSystem}}')" || fail 'cannot verify Docker engine identity'
[[ "$engine_identity" == "$DOCKER_ENGINE_EXPECTED" ]] || fail 'Docker engine differs from attested Desktop daemon'
docker_control image inspect "$NODE_IMAGE" >/dev/null || fail 'pinned Node image is not already local'

existing="$(docker_control volume ls --format '{{.Name}}' --filter "name=$SOURCE_VOLUME")" || fail 'cannot check snapshot volume collision'
while IFS= read -r name; do [[ "$name" != "$SOURCE_VOLUME" ]] || fail 'snapshot volume name is occupied'; done <<< "$existing"
existing="$(docker_control ps -a --format '{{.Names}}' --filter "name=$SNAPSHOT_CONTAINER")" || fail 'cannot check snapshot container collision'
while IFS= read -r name; do [[ "$name" != "$SNAPSHOT_CONTAINER" ]] || fail 'snapshot container name is occupied'; done <<< "$existing"
CIDFILE="$ROOT/.context/evidencia/h3req1_c03_source_snapshot_s10_${CIDFILE_SUFFIX}.cid"
[[ ! -e "$CIDFILE" && ! -L "$CIDFILE" ]] || fail 'snapshot cidfile path is occupied'
mapfile -t snapshot_files < <({ awk '{print $2}' "$SOURCE_MANIFEST"; printf '%s\n' "$SOURCE_MANIFEST"; } | LC_ALL=C sort -u)
[[ "${#snapshot_files[@]}" -eq 14 ]] || fail 'snapshot path set is not exactly 14 files'

set -o noclobber
exec >"$EVIDENCE" 2>&1
set +o noclobber
report_open=true
printf 'jit=%s\nrunner-sha256=%s\nsidecar-sha256=%s\nsource-manifest-sha256=%s\n' \
  "$JIT" "$APPROVED_RUNNER_SHA256" "$APPROVED_SIDECAR_SHA256" "$SOURCE_MANIFEST_SHA256"
printf '# H3REQ1 complete source snapshot S10\n\n'
printf 'scope=14 allowlisted files only (13 source inputs plus v4 source manifest); no dependency install, egress, DB, Edge, SQL, credentials, or remotes\n'
printf 'branch=%s\nhead=%s\nimage=%s\nsource-volume=%s\nsnapshot-container=%s\nsource-files=14\nsource-bytes=%s\nsource-permission-files=14\nsource-permission-map-sha256=%s\nnetwork=none\n' \
  "$BRANCH_EXPECTED" "$HEAD_EXPECTED" "$NODE_IMAGE" "$SOURCE_VOLUME" "$SNAPSHOT_CONTAINER" "$total_bytes" "$source_mode_manifest_sha256"

phase='create-and-verify-bounded-source-volume'
created_volume="$(docker_control volume create --driver local --opt type=tmpfs --opt device=tmpfs \
  --opt o=nosuid,nodev,size=96m --label "com.studiamatch.h3.snapshot.jit=$JIT" \
  --label "com.studiamatch.h3.snapshot.manifest=$APPROVED_SIDECAR_SHA256" \
  --label "com.studiamatch.h3.snapshot.run=$RUN_NONCE" "$SOURCE_VOLUME")" || fail 'cannot create bounded source volume'
[[ "$created_volume" == "$SOURCE_VOLUME" ]] || fail 'unexpected source volume name returned'
volume_metadata="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}|{{index .Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Labels "com.studiamatch.h3.snapshot.run"}}' "$SOURCE_VOLUME")" \
  || fail 'cannot verify newly created source volume'
[[ "$volume_metadata" == "$SOURCE_VOLUME|local|tmpfs|tmpfs|nosuid,nodev,size=96m|$JIT|$APPROVED_SIDECAR_SHA256|$RUN_NONCE" ]] \
  || fail 'source volume identity/options differ'

SNAPSHOT_SCRIPT='set -eu; test -z "$(find /snapshot -mindepth 1 -print -quit)"; tar --no-same-owner -xf - -C /snapshot 2>/dev/null; cd /snapshot; test -z "$(find . -type l -print -quit)"; test "$(sha256sum tests/h3req1-c03-startup-source-s1-v4.sha256 | cut -d" " -f1)" = "$H3_SOURCE_MANIFEST_SHA256"; sha256sum -c tests/h3req1-c03-startup-source-s1-v4.sha256 >/dev/null 2>&1; expected="$( { awk "{print \$2}" tests/h3req1-c03-startup-source-s1-v4.sha256; printf "%s\\n" tests/h3req1-c03-startup-source-s1-v4.sha256; } | LC_ALL=C sort -u )"; actual="$(find . -type f -printf "%P\\n" | LC_ALL=C sort)"; test "$expected" = "$actual"; test "$(find . -type f | wc -l | tr -d "[:space:]")" = 14; actual_modes="$(find . -type f -printf "%P|%m\\n" | LC_ALL=C sort | tr "\\n" ";")"; test "$actual_modes" = "$H3_SOURCE_MODE_MANIFEST"; printf "source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true\\n"'
phase='create-container-and-verify-controls-before-start'
created_container_id="$(docker_control create --pull=never --platform linux/amd64 --attach=stdin --attach=stdout --attach=stderr --interactive \
  --cidfile "$CIDFILE" --name "$SNAPSHOT_CONTAINER" --network none --log-driver none --restart=no --read-only \
  --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 --shm-size=16m --cap-drop=ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:rw,noexec,nosuid,nodev,size=8m \
  --mount "type=volume,src=$SOURCE_VOLUME,dst=/snapshot" \
  --label "com.studiamatch.h3.snapshot.jit=$JIT" --label "com.studiamatch.h3.snapshot.manifest=$APPROVED_SIDECAR_SHA256" \
  --label "com.studiamatch.h3.snapshot.run=$RUN_NONCE" --env H3_SOURCE_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" \
  --env "H3_SOURCE_MODE_MANIFEST=$source_mode_manifest" \
  "$NODE_IMAGE" sh -lc "$SNAPSHOT_SCRIPT")" || fail 'Docker create failed; container was not started'
[[ "$created_container_id" =~ ^[a-f0-9]{64}$ ]] || fail 'Docker create did not return a full container ID'
[[ "$(cat "$CIDFILE")" == "$created_container_id" ]] || fail 'cidfile differs from created container ID'
metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{.HostConfig.Memory}}|{{.HostConfig.MemorySwap}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.PidsLimit}}|{{.HostConfig.RestartPolicy.Name}}|{{.HostConfig.LogConfig.Type}}|{{json .HostConfig.CapDrop}}|{{json .HostConfig.SecurityOpt}}|{{json .HostConfig.PortBindings}}|{{range .Mounts}}{{.Type}}|{{.Name}}|{{.Destination}}|{{.RW}}{{end}}' "$created_container_id")" \
  || fail 'cannot inspect created snapshot container'
[[ "$metadata" == "$created_container_id|/$SNAPSHOT_CONTAINER|$NODE_IMAGE|created|none|true|134217728|134217728|500000000|64|no|none|[\"ALL\"]|[\"no-new-privileges:true\"]|{}|volume|$SOURCE_VOLUME|/snapshot|true" ]] \
  || fail 'created snapshot container controls or mount differ; it was not started'
printf 'container-created-id=%s\ncontainer-controls=PASS|state=created|network=none|rootfs=read-only|memory=128m|cpus=0.5|pids=64|mount=source-volume-rw\n' "$created_container_id"

phase='stream-allowlisted-source-snapshot'
container_started=true
set +e
timeout --foreground --signal=TERM --kill-after=1s 120s tar --format=ustar --numeric-owner -C "$ROOT" --no-recursion -cf - -- "${snapshot_files[@]}" 2>/dev/null |
  timeout --foreground --signal=TERM --kill-after=5s 120s docker start --attach --interactive "$created_container_id" 2>/dev/null |
  awk 'BEGIN { count=0; bad=0 } { if ($0 == "source-snapshot=PASS|files=14|source-manifest=13/13|permissions=exact|no-same-owner=true") { print $0; count++ } else { print "snapshot-output=suppressed"; bad=1 } } END { if (count != 1 || bad) exit 1 }'
pipeline_status=("${PIPESTATUS[@]}")
set -e
tar_status="${pipeline_status[0]:-1}"
receiver_status="${pipeline_status[1]:-1}"
filter_status="${pipeline_status[2]:-1}"
printf 'source-tar-producer-status=%s|snapshot-receiver-status=%s|output-filter-status=%s\n' "$tar_status" "$receiver_status" "$filter_status"
[[ "$tar_status" == 0 && "$receiver_status" == 0 && "$filter_status" == 0 ]] || fail 'snapshot producer, receiver, or output predicate failed'

phase='verify-exited-snapshot-container-and-volume'
metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}|{{.HostConfig.NetworkMode}}' "$created_container_id")" \
  || fail 'cannot verify exited snapshot container'
[[ "$metadata" == "$created_container_id|/$SNAPSHOT_CONTAINER|exited|0|false|$JIT|$APPROVED_SIDECAR_SHA256|$RUN_NONCE|none" ]] \
  || fail 'snapshot container exit metadata differs'
volume_metadata="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}|{{index .Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Labels "com.studiamatch.h3.snapshot.run"}}' "$SOURCE_VOLUME")" \
  || fail 'cannot verify preserved source volume'
[[ "$volume_metadata" == "$SOURCE_VOLUME|local|tmpfs|tmpfs|nosuid,nodev,size=96m|$JIT|$APPROVED_SIDECAR_SHA256|$RUN_NONCE" ]] \
  || fail 'preserved source volume identity/options differ'

phase='independent-read-only-volume-verification'
set +e
verify_output="$(docker_control run --rm --pull=never --platform linux/amd64 --network=none --log-driver none --read-only \
  --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 --cap-drop=ALL \
  --security-opt no-new-privileges:true --mount "type=volume,src=$SOURCE_VOLUME,dst=/snapshot,readonly" \
  --env H3_SOURCE_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" --env "H3_SOURCE_MODE_MANIFEST=$source_mode_manifest" \
  "$NODE_IMAGE" sh -lc 'set -eu; cd /snapshot; test "$(sha256sum tests/h3req1-c03-startup-source-s1-v4.sha256 | cut -d" " -f1)" = "$H3_SOURCE_MANIFEST_SHA256"; sha256sum -c tests/h3req1-c03-startup-source-s1-v4.sha256 >/dev/null 2>&1; test -z "$(find . -type l -print -quit)"; test "$(find . -type f | wc -l | tr -d "[:space:]")" = 14; actual_modes="$(find . -type f -printf "%P|%m\\n" | LC_ALL=C sort | tr "\\n" ";")"; test "$actual_modes" = "$H3_SOURCE_MODE_MANIFEST"; printf "snapshot-volume-verification=PASS\\n"' 2>/dev/null)"
verify_status=$?
set -e
[[ "$verify_status" == 0 && "$verify_output" == 'snapshot-volume-verification=PASS' ]] || fail 'read-only snapshot verifier failed'
printf 'snapshot-container=%s|exited|0|oom=false|network=none\nsnapshot-volume=%s|tmpfs-96m|owner-verified\n' "$SNAPSHOT_CONTAINER" "$SOURCE_VOLUME"
printf 'snapshot-verifier=exit-0|network=none|mount=readonly\nsource-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0\n'
phase='complete'
trap - ERR
printf 'Source snapshot S10: PASS; volume and exited container preserved.\n'
printf 'Source snapshot S10: PASS; evidence=%s\n' "$EVIDENCE" >&3
