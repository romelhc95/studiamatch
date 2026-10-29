#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly SOURCE_VOL='h3req1-c03-startup-source-20261010-s18'
readonly SNAPSHOT='h3req1-c03-startup-snapshot-20261010-s18'
readonly SNAPSHOT_ID='48116e932a4756e9180191e69655fc4b7a571c37fc0e4ccfd627e2ad9857f9ea'
readonly SNAPSHOT_JIT='H3-CLOSE-03-SOURCE-SNAPSHOT-S18-2026-10-10'
readonly SNAPSHOT_MANIFEST='13a4bea55ed248d1ec0567f21258c5ccbc8dbfc9fb02667016aba0298ab262cf'
readonly SNAPSHOT_RUN='1947538-1791683899378609117-13244'
readonly S11_JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S11-CURRENT-LOCKS'
readonly S11_MANIFEST='a261d0f3933f5a70180ebc62ba66c54f7a089aeb5bf1c858a3da4c0be8deab82'
readonly S11_RUN='1924564-1791679969529341635-32359-29852'
readonly TOOLS_VOL='h3req1-c03-startup-tools-20261010-s11'
readonly PAGES_VOL='h3req1-c03-startup-pages-20261010-s11'
readonly HOLDER='h3req1-c03-startup-volume-holder-20261010-s11'
readonly HOLDER_ID='265584eaf5d218c90725f14080cae10f6cd6a5818c3befb65c2ee89aee9a65f5'
readonly NETWORK='h3req1-c03-startup-net-20261010-s11'
readonly NETWORK_ID='9c4fcd8afed0b66562ce1c12ee52c5a290daf7ee177d2411f5505f1bcbade1fa'
readonly OLD_RUNTIME='h3req1-c03-startup-runtime-20261010-s14'
readonly OLD_RUNTIME_ID='5243c9e452f397f8194501418c897905ac43fda9c298479eaff6d2756a748f5c'
readonly OLD_JIT='H3-CLOSE-03-WORKERD-STARTUP-DIAGNOSTIC-S14-2026-10-10'
readonly OLD_MANIFEST='e787a7cd371b2f5705646ef6b5322d3562d8bc6c401079bfefc9bef32d3555eb'
readonly OLD_RUN='1791682275-1938696-16707'
readonly INPUTS='tests/h3req1-c03-startup-s15-diagnostic-inputs.sha256'
readonly INPUTS_SHA='b2a6a47c4407caef78b2c731b223c4fc5c8fd5f7226982c9baa8aae671852484'
readonly SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v10.sha256'
readonly SOURCE_MANIFEST_SHA='29d8459b81656d5947a6e2c771616ff6a59d1719af13b1f686a8d58b7ce5bc6e'
readonly SNAPSHOT_EVIDENCE='.context/evidencia/h3req1_c03_source_snapshot_2026-10-10_s18.md'
readonly OLD_EVIDENCE='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s14_diagnostic.md'
readonly HOLDER_SOURCE_VOL='h3req1-c03-startup-source-20261010-s16'
readonly SIDECAR='tests/h3req1-c03-startup-runtime-s15.sha256'
readonly RECOVERY_TEST='tests/h3req1_c03_startup_runtime_recovery_s15_selftest.sh'
readonly RECOVERY_TEST_SHA='bb44bebdd6c1c7b116a259e7ef391350c302e2e434d23e4bb89251d571d21060'
readonly CONTRACT_TEST='tests/h3req1_c03_startup_runtime_contract_s15.test.mjs'
readonly CONTRACT_TEST_SHA='298e0d824236f87d33674d241012d7c6527299b7ffdcb2470c8e710a161e680d'
readonly HEALTHZ_PROBE='tests/h3req1_c03_startup_healthz_probe.mjs'
readonly EXPECTED_DEPENDENCY_DIGESTS='{"miniflare-node-modules":"82385e75623f0a0b7f6c2919232634b92b0d1c0709cef6d3af34730676b3629e","pages-node-modules":"b7bb98f751194c0c28c793bf64debdccedbe94c5b8f5e0157374b5accf555ea1"}'
readonly RUNNER='tests/h3req1_c03_startup_runtime_diagnostic_s15.sh'
readonly PROBE='tests/h3req1_c03_startup_runtime_probe_s8.mjs'
readonly PRELOAD='tests/h3req1_c03_startup_validation_preload_s8.cjs'
readonly FILTER='tests/h3req1_c03_startup_output_filter_s8.sh'
readonly JIT='H3-CLOSE-03-WORKERD-STARTUP-DIAGNOSTIC-S15-2026-10-10'
readonly RUNTIME='h3req1-c03-startup-runtime-20261010-s15'
readonly RESULT='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s15_diagnostic.md'
APPROVED_RUNNER_SHA=''
APPROVED_SIDECAR_SHA=''
RUN_ID="$(date +%s)-$BASHPID-$RANDOM"
readonly RUN_ID

phase='preflight'
report_open=false
runtime_attempted=false
stop_event=''
exec 3>&1
fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }
docker_control() { timeout --foreground --signal=TERM --kill-after=5s 20s docker "$@" 2>/dev/null; }
verify_source_volume_ownership() {
  local metadata attachments
  metadata="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{json .Options}}|{{index .Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Labels "com.studiamatch.h3.snapshot.run"}}' "$SOURCE_VOL")" || return 1
  [[ "$metadata" == "$SOURCE_VOL|local|null|$SNAPSHOT_JIT|$SNAPSHOT_MANIFEST|$SNAPSHOT_RUN" ]] || return 1
  attachments="$(docker_control ps -a --no-trunc --filter "volume=$SOURCE_VOL" --format '{{.ID}}|{{.Names}}')" || return 1
  [[ "$attachments" == "$SNAPSHOT_ID|$SNAPSHOT" ]]
}

stop_running_owned_runtime() {
  local row id state jit manifest run verify_id verify_state verify_jit verify_manifest verify_run
  stop_event="runtime-stop=not-confirmed|reason=inspect-failed|container-name=$RUNTIME|resource-state=unknown"
  row="$(docker_control inspect --format '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$RUNTIME")" || return 1
  IFS='|' read -r id state jit manifest run <<< "$row"
  if [[ ! "$id" =~ ^[a-f0-9]{64}$ || "$jit" != "$JIT" || "$manifest" != "$INPUTS_SHA" || "$run" != "$RUN_ID" ]]; then
    stop_event="runtime-stop=not-confirmed|reason=ownership-mismatch|container-name=$RUNTIME|resource-state=unknown"
    return 1
  fi
  if [[ "$state" == created || "$state" == exited || "$state" == dead ]]; then
    stop_event="runtime-stop=not-required|state=$state|container-id=$id|resource=preserved"
    return 0
  fi
  if [[ "$state" != running && "$state" != paused && "$state" != restarting ]]; then
    stop_event="runtime-stop=not-confirmed|reason=unknown-state|container-id=$id|resource-state=unknown"
    return 1
  fi
  if ! docker_control stop --time 10 "$id" >/dev/null; then
    stop_event="runtime-stop=not-confirmed|reason=stop-command-failed|container-id=$id|resource-state=unknown"
    return 1
  fi
  row="$(docker_control inspect --format '{{.Id}}|{{.State.Status}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$id")" || {
    stop_event="runtime-stop=not-confirmed|reason=post-stop-inspect-failed|container-id=$id|resource-state=unknown"
    return 1
  }
  IFS='|' read -r verify_id verify_state verify_jit verify_manifest verify_run <<< "$row"
  if [[ "$verify_id" != "$id" || "$verify_jit" != "$JIT" || "$verify_manifest" != "$INPUTS_SHA" || "$verify_run" != "$RUN_ID" ]]; then
    stop_event="runtime-stop=not-confirmed|reason=post-stop-ownership-mismatch|container-id=$id|resource-state=unknown"
    return 1
  fi
  if [[ "$verify_state" != exited && "$verify_state" != dead ]]; then
    stop_event="runtime-stop=not-confirmed|reason=post-stop-state-active|container-id=$id|resource-state=unknown"
    return 1
  fi
  stop_event="runtime-stop=completed|container-id=$id|resource=preserved"
  return 0
}
on_exit() {
  local status=$?
  trap - EXIT
  if [[ "$status" -ne 0 && "$runtime_attempted" == true ]]; then
    if ! stop_running_owned_runtime; then :; fi
    printf '%s\n' "$stop_event" >&2
  fi
  if [[ "$report_open" == true ]]; then
    if [[ "$status" -eq 0 ]]; then printf 'diagnostic-result=PASS\n'
    else printf 'diagnostic-result=NO-GO|phase=%s|exit=%s\n' "$phase" "$status"; fi
  fi
  printf 'startup-diagnostic-exit=%s|phase=%s|evidence=%s\n' "$status" "$phase" "$RESULT" >&3
  exit "$status"
}
trap on_exit EXIT

[[ "$#" -eq 4 && "${1:-}" == '--runner-sha256' && "${3:-}" == '--sidecar-sha256' ]] \
  || fail 'exact runner and sidecar pins required'
APPROVED_RUNNER_SHA="$2"
APPROVED_SIDECAR_SHA="$4"
[[ "$APPROVED_RUNNER_SHA" =~ ^[a-f0-9]{64}$ && "$APPROVED_SIDECAR_SHA" =~ ^[a-f0-9]{64}$ ]] \
  || fail 'invalid runner or sidecar digest'

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$ROOT"
[[ "$ROOT" == "$EXPECTED_ROOT" ]] || fail 'candidate path changed'
[[ "$(git branch --show-current)" == "$BRANCH" && "$(git rev-parse HEAD)" == "$HEAD" ]] || fail 'candidate branch or HEAD changed'
[[ -f "$RUNNER" && ! -L "$RUNNER" && "$(realpath -e -- "$0")" == "$ROOT/$RUNNER" ]] || fail 'runner path missing, symlinked, or changed'
[[ "$(sha256sum "$RUNNER" | cut -d' ' -f1)" == "$APPROVED_RUNNER_SHA" ]] || fail 'runner digest differs from reviewed pin'
[[ -f "$SIDECAR" && ! -L "$SIDECAR" \
  && "$(sha256sum "$SIDECAR" | cut -d' ' -f1)" == "$APPROVED_SIDECAR_SHA" \
  && "$(cat "$SIDECAR")" == "$APPROVED_RUNNER_SHA  $RUNNER" ]] || fail 'runner sidecar differs from reviewed pin'
[[ -f "$INPUTS" && ! -L "$INPUTS" && "$(sha256sum "$INPUTS" | cut -d' ' -f1)" == "$INPUTS_SHA" ]] || fail 'diagnostic manifest pin differs'
sha256sum -c "$INPUTS" >/dev/null || fail 'diagnostic helper/evidence inputs differ'
[[ -f "$RECOVERY_TEST" && ! -L "$RECOVERY_TEST" \
  && "$(sha256sum "$RECOVERY_TEST" | cut -d' ' -f1)" == "$RECOVERY_TEST_SHA" ]] \
  || fail 'runtime recovery self-test pin differs'
[[ -f "$CONTRACT_TEST" && ! -L "$CONTRACT_TEST" \
  && "$(sha256sum "$CONTRACT_TEST" | cut -d' ' -f1)" == "$CONTRACT_TEST_SHA" \
  && -f "$HEALTHZ_PROBE" && ! -L "$HEALTHZ_PROBE" ]] \
  || fail 'runtime contract test digest or Pages probe path differs'
recovery_test_output="$(bash "$RECOVERY_TEST" "$RUNNER")" || fail 'runtime recovery self-test failed'
[[ "$recovery_test_output" == 'phase=runtime-stop-recovery-synthetic|error_code=PASS|cases=9' ]] \
  || fail 'runtime recovery self-test output differs'
[[ "$(sha256sum "$SOURCE_MANIFEST" | cut -d' ' -f1)" == "$SOURCE_MANIFEST_SHA" ]] || fail 'S18 source manifest pin differs'
sha256sum -c "$SOURCE_MANIFEST" >/dev/null || fail 'candidate source inputs differ from S18'
grep -Fqx 'source-snapshot=PASS files=18 symlinks=0 producer=0 receiver=0 verifier=0' "$SNAPSHOT_EVIDENCE" || fail 'S18 snapshot marker missing'
grep -Fqx 'runtime-docker-exit=1|filter-exit=0' "$OLD_EVIDENCE" || fail 'S14 runtime failure evidence changed'
grep -Fqx 'runtime-error-code=ERR_MODULE_NOT_FOUND' "$OLD_EVIDENCE" || fail 'S14 module-resolution diagnosis changed'
grep -Fqx 'runtime-missing-module=relative-module|from=candidate-tests' "$OLD_EVIDENCE" || fail 'S14 relative-module diagnosis changed'
grep -Fqx 'runtime-missing-module-shape=module-import' "$OLD_EVIDENCE" || fail 'S14 module-import shape changed'
[[ -d "$ROOT/.context" && ! -L "$ROOT/.context" \
  && -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context/evidencia" ]] \
  || fail 'S15 evidence parent must be physical directories'
context_real="$(realpath -e -- "$ROOT/.context")" || fail 'cannot canonicalize S15 context directory'
evidence_real="$(realpath -e -- "$ROOT/.context/evidencia")" || fail 'cannot canonicalize S15 evidence directory'
[[ "$context_real" == "$ROOT/.context" && "$evidence_real" == "$ROOT/.context/evidencia" ]] \
  || fail 'S15 evidence parent resolves outside the candidate checkout'
[[ ! -e "$RESULT" && ! -L "$RESULT" ]] || fail 'S15 evidence path occupied'
[[ -z "$(printenv DOCKER_HOST 2>/dev/null || true)" && -z "$(printenv DOCKER_CONTEXT 2>/dev/null || true)" \
  && -z "$(printenv DOCKER_TLS_VERIFY 2>/dev/null || true)" && -z "$(printenv DOCKER_CERT_PATH 2>/dev/null || true)" ]] || fail 'Docker endpoint override rejected'
[[ "$(docker_control context show)" == default ]] || fail 'Docker context differs'
[[ "$(docker_control context inspect --format '{{ (index .Endpoints "docker").Host }}' default)" == unix:///var/run/docker.sock ]] || fail 'Docker endpoint differs'
[[ "$(docker_control info --format '{{.ID}}|{{.Name}}|{{.OperatingSystem}}')" == 'fc2115b2-c3c4-440e-89c6-26899eb7cb04|docker-desktop|Docker Desktop' ]] || fail 'Docker Desktop identity differs'
docker_control image inspect "$IMAGE" >/dev/null || fail 'pinned Node image is unavailable locally'

row="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}' "$SNAPSHOT")" || fail 'S18 snapshot container unavailable'
[[ "$row" == "$SNAPSHOT_ID|/$SNAPSHOT|$IMAGE|exited|0|false|none|true|$SNAPSHOT_JIT|$SNAPSHOT_MANIFEST|$SNAPSHOT_RUN" ]] || fail 'S18 snapshot identity differs'
[[ "$(docker_control inspect --format '{{range .Mounts}}{{.Type}}|{{.Name}}|{{.Destination}}|{{.RW}}{{end}}' "$SNAPSHOT")" == "volume|$SOURCE_VOL|/snapshot|true" ]] || fail 'S18 source mount differs'
verify_source_volume_ownership || fail 'S18 source volume options or attachments differ'

tools="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}' "$TOOLS_VOL")" || fail 'S11 tools volume unavailable'
pages="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}' "$PAGES_VOL")" || fail 'S11 Pages volume unavailable'
[[ "$tools" == "$TOOLS_VOL|local|tmpfs|tmpfs|nosuid,nodev,size=768m|$S11_JIT|$S11_MANIFEST|$S11_RUN" \
  && "$pages" == "$PAGES_VOL|local|tmpfs|tmpfs|nosuid,nodev,size=1024m|$S11_JIT|$S11_MANIFEST|$S11_RUN" ]] || fail 'S11 fresh dependency volume metadata differs'
row="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.HostConfig.NetworkMode}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$HOLDER")" || fail 'S11 volume holder unavailable'
[[ "$row" == "$HOLDER_ID|/$HOLDER|$IMAGE|running|none|$S11_JIT|$S11_MANIFEST|$S11_RUN" ]] || fail 'S11 volume holder identity differs'
holder_mounts="$(docker_control inspect --format '{{range .Mounts}}{{.Name}}|{{.Destination}}|{{.RW}};{{end}}' "$HOLDER")"
holder_mount_count="$(printf '%s' "$holder_mounts" | tr -cd ';' | wc -c | tr -d '[:space:]')"
[[ "$holder_mounts" == *"$HOLDER_SOURCE_VOL|/source|false;"* && "$holder_mounts" == *"$TOOLS_VOL|/tools|false;"* \
  && "$holder_mounts" == *"$PAGES_VOL|/pages|false;"* && "$holder_mount_count" == 3 ]] || fail 'S11 volume holder mounts differ'

row="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$OLD_RUNTIME")" || fail 'S14 failed runtime unavailable'
[[ "$row" == "$OLD_RUNTIME_ID|/$OLD_RUNTIME|$IMAGE|exited|1|false|$NETWORK_ID|true|$OLD_JIT|$OLD_MANIFEST|$OLD_RUN" ]] || fail 'S14 failed runtime identity differs'
network="$(docker_control network inspect --format '{{.Id}}|{{.Name}}|{{.Driver}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}|{{len .Containers}}' "$NETWORK")" || fail 'S11 internal network unavailable'
[[ "$network" == "$NETWORK_ID|$NETWORK|bridge|true|$S11_JIT|$S11_MANIFEST|$S11_RUN|0" ]] || fail 'S11 internal network identity/endpoints differ'
matches="$(docker_control ps -a --format '{{.Names}}' --filter "name=$RUNTIME")" || fail 'cannot check S15 name'
while IFS= read -r name; do [[ "$name" != "$RUNTIME" ]] || fail 'S15 runtime name occupied'; done <<< "$matches"

# The filter emits only closed markers; raw runtime output never enters the evidence.
set -o noclobber
exec >"$RESULT" 2>&1
set +o noclobber
report_open=true
printf 'jit=%s\nrunner-sha256=%s\nsidecar-sha256=%s\ninputs-sha256=%s\nbranch=%s\nhead=%s\n' "$JIT" "$APPROVED_RUNNER_SHA" "$APPROVED_SIDECAR_SHA" "$INPUTS_SHA" "$BRANCH" "$HEAD"
printf 'scope=single Pages/workerd diagnostic; reused S18 snapshot and S11 fresh locks; no bootstrap, DB, PostgREST, Edge, SQL, Auth, email, secrets, remotes, or original-checkout writes\n'
printf '%s\n' "$recovery_test_output"
printf 'prior-runtime=s14|id=%s|exit=1|oom=false|last-stage=runtime-uncaught-error|error=ERR_MODULE_NOT_FOUND|module=relative-module|healthz=NO-GO\n' "$OLD_RUNTIME_ID"
printf 'runtime-image=%s|network=%s|network-id=%s|internal=true|resources=2GiB-2CPU|timeout=180s\n' "$IMAGE" "$NETWORK" "$NETWORK_ID"
printf 'phase=preflight|error_code=PASS\n'
phase='s15-runtime-contract-test'
contract_test_output=''
if ! contract_test_output="$(docker_control run --rm --pull=never --platform linux/amd64 --network=none --log-driver none --read-only \
  --cpus=0.5 --memory=256m --memory-swap=256m --pids-limit=64 --cap-drop=ALL \
  --security-opt no-new-privileges:true --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --mount "type=volume,src=$SOURCE_VOL,dst=/candidate,readonly" \
  --mount "type=bind,src=$ROOT/$CONTRACT_TEST,dst=/contract.test.mjs,readonly" \
  --mount "type=bind,src=$ROOT/$HEALTHZ_PROBE,dst=/h3req1_c03_startup_healthz_probe.mjs,readonly" \
  --mount "type=bind,src=$ROOT/$RUNNER,dst=/s15-runner.sh,readonly" \
  --env H3_TEST_RUNTIME_SOURCE=/candidate/tests/h3req1_c03_integrated_runtime.mjs \
  --env H3_TEST_RUNNER_SOURCE=/s15-runner.sh \
  "$IMAGE" node /contract.test.mjs 2>/dev/null)"; then
  printf 'phase=s15-runtime-contract|error_code=EXECUTION_FAILED\n'
  fail 'S15 runtime contract tests did not execute successfully'
fi
[[ "$contract_test_output" == 'phase=s15-runtime-contract|error_code=PASS|cases=7' ]] \
  || { printf 'phase=s15-runtime-contract|error_code=OUTPUT_MISMATCH\n'; fail 'S15 runtime contract output differed'; }
printf '%s\n' "$contract_test_output"
verify_source_volume_ownership || { printf 'phase=source-volume-recheck|error_code=OWNERSHIP_MISMATCH\n'; fail 'S18 source volume options or attachments changed before runtime'; }
phase='one-shot-pages-workerd-runtime-diagnostic'
runtime_attempted=true
set +e
timeout --foreground --signal=TERM --kill-after=10s 180s docker run --pull=never --platform linux/amd64 \
  --name "$RUNTIME" --network "$NETWORK_ID" --log-driver none --read-only --cpus=2 --memory=2g --memory-swap=2g \
  --pids-limit=256 --stop-timeout 10 --cap-drop=ALL --security-opt no-new-privileges:true \
  --env HTTP_PROXY= --env HTTPS_PROXY= --env FTP_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env ftp_proxy= --env all_proxy= --env no_proxy= \
  --env npm_config_proxy= --env npm_config_http_proxy= --env npm_config_https_proxy= \
  --env NPM_CONFIG_USERCONFIG=/dev/null --env npm_config_userconfig=/dev/null \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$INPUTS_SHA" \
  --label "com.studiamatch.h3.startup.run=$RUN_ID" \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m --tmpfs /run/c03-private:rw,noexec,nosuid,size=8m --tmpfs /run/c03-certs:rw,nosuid,size=16m \
  --mount "type=volume,src=$SOURCE_VOL,dst=/candidate,readonly" \
  --mount "type=volume,src=$TOOLS_VOL,dst=/tools,readonly" \
  --mount "type=volume,src=$PAGES_VOL,dst=/web-deps,readonly" \
  --mount "type=bind,src=$ROOT/$PROBE,dst=/probe.mjs,readonly" \
  --mount "type=bind,src=$ROOT/$PRELOAD,dst=/diag-preload.cjs,readonly" \
  --env H3_C03_ROOT=/candidate --env H3_C03_TOOLS_ROOT=/tools --env H3_C03_CERTS_ROOT=/run/c03-certs \
  --env H3_C03_WEB_DEPS_ROOT=/web-deps --env H3_C03_PRIVATE_ROOT=/run/c03-private \
  --env H3_C03_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA" --env H3_C03_DEPENDENCY_BOOTSTRAP_COMPLETE=true \
  --env H3_C03_EXPECTED_DEPENDENCY_DIGESTS="$EXPECTED_DEPENDENCY_DIGESTS" \
  "$IMAGE" node /probe.mjs 2>&1 | bash "$FILTER" --sanitize
runtime_status=$?
set -e
if grep -Fqx 'runtime-output-sanitization=allowlisted-events-only' "$RESULT"; then
  printf 'runtime-docker-exit=%s|filter-exit=0\n' "$runtime_status"
else
  printf 'runtime-docker-exit=%s|filter-exit=1\n' "$runtime_status"
  fail 'runtime output filter did not complete'
fi
row="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}|{{range .Mounts}}{{.Destination}}:{{.RW}};{{end}}' "$RUNTIME")" || fail 'runtime container metadata unavailable'
IFS='|' read -r runtime_id runtime_name runtime_image runtime_state runtime_exit runtime_oom runtime_network runtime_readonly runtime_jit runtime_manifest runtime_run runtime_mounts <<< "$row"
[[ "$runtime_id" =~ ^[a-f0-9]{64}$ && "$runtime_name" == "/$RUNTIME" && "$runtime_image" == "$IMAGE" \
  && "$runtime_state" == exited && "$runtime_exit" =~ ^[0-9]+$ && "$runtime_oom" == false \
  && "$runtime_network" == "$NETWORK_ID" && "$runtime_readonly" == true && "$runtime_jit" == "$JIT" \
  && "$runtime_manifest" == "$INPUTS_SHA" && "$runtime_run" == "$RUN_ID" \
  && "$runtime_mounts" == '/candidate:false;/diag-preload.cjs:false;/probe.mjs:false;/tools:false;/web-deps:false;' ]] || fail 'runtime container identity/state/mount policy differs'
printf 'runtime-container=%s|id=%s|state=%s|exit=%s|oom=%s|network=%s|readonly=true|mounts=5-readonly\n' "$RUNTIME" "$runtime_id" "$runtime_state" "$runtime_exit" "$runtime_oom" "$runtime_network"
[[ "$runtime_status" == "$runtime_exit" ]] || fail 'runtime Docker exit differs from inspected exit'
grep -Fqx 'runtime-dependency-digests=PASS|groups=2' "$RESULT" || fail 'startup dependency content digests were not verified'
grep -Eq '^healthz=PASS workerd=true pages-worker=root-asset attempts=[1-9][0-9]?$' "$RESULT" || fail 'actual Pages worker root response was not reached'
grep -Fqx 'smoke=PASS workerd-pages-healthz=true pages-worker=root-asset edge-runtime=not-started database=not-started' "$RESULT" || fail 'Pages/workerd PASS marker missing'
[[ "$runtime_exit" == 0 ]] || fail 'Pages/workerd runtime exited nonzero'
printf 'phase=pages-workerd-healthz|error_code=PASS\nexit=0\n'
phase='verify-network-after-runtime'
network="$(docker_control network inspect --format '{{.Id}}|{{.Name}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{len .Containers}}' "$NETWORK_ID")" || fail 'cannot verify internal network after runtime'
[[ "$network" == "$NETWORK_ID|$NETWORK|true|$S11_JIT|$S11_MANIFEST|0" ]] || fail 'internal network identity/endpoints changed'
printf 'phase=internal-network-after-runtime|error_code=PASS\n'
phase='retire-successful-runtime-container'
docker_control rm "$runtime_id" >/dev/null || fail 'successful diagnostic container could not be retired'
remaining="$(docker_control ps -a --no-trunc --filter "id=$runtime_id" --format '{{.ID}}')" || fail 'cannot verify runtime retirement'
[[ -z "$remaining" ]] || fail 'successful diagnostic container remains'
printf 'runtime-container-retirement=completed|id=%s|volumes-preserved=true|network-preserved=true\n' "$runtime_id"
printf 'retained-for-next-local-gates=source-volume-s18,tools-volume-s11,pages-volume-s11,volume-holder-s11,network-s11\n'
printf 'diagnostic-result=PASS\n'
trap - EXIT
report_open=false
printf '%s\n' 'Pages/workerd runtime diagnostic S15: PASS (worker response healthz, dependency digests, isolated runtime, sanitized classifier).' >&3
exec 3>&-

