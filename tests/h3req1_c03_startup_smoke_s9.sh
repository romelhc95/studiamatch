#!/usr/bin/env bash
set -Eeuo pipefail

readonly JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S9-VALIDATION-DIAGNOSTIC'
readonly RUNNER='tests/h3req1_c03_startup_smoke_s9.sh'
readonly MANIFEST='tests/h3req1-c03-startup-smoke-s9.sha256'
readonly RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s9.md'
readonly PROBE_SCRIPT='tests/h3req1_c03_startup_runtime_probe_s8.mjs'
readonly OUTPUT_FILTER='tests/h3req1_c03_startup_output_filter_s8.sh'
readonly PRELOAD_SCRIPT='tests/h3req1_c03_startup_validation_preload_s8.cjs'
readonly PRELOAD_SCRIPT_SHA256='682b6b412f497e384ff543f73a8cff1390cfc2fc9a8e2e35893db5e6b1dbc0af'
readonly OUTPUT_FILTER_SHA256='c41ff1d5a1f8fe70930101f747549df3dcfa83df93d58fb2945e682056fbbfd1'
readonly S4_RUNNER='tests/h3req1_c03_startup_smoke_s3_resume_s4.sh'
readonly S4_RUNNER_SHA256='c4659f16889a41987c6512d7167ffe397d6a31edf58b645a77bc888d627eca7c'
readonly S4_MANIFEST='tests/h3req1-c03-startup-smoke-s3-resume-s4.sha256'
readonly S4_MANIFEST_SHA256='1cb90249466e65ccf59fc6ae3d2d7088f8c658917d91ece5f55c66bfd9268f29'
readonly S4_RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s4.md'
readonly S4_RESULT_SHA256='4136061965cde82eb926c450ac2efaafcd3832551097fd7767de0393398fea87'
readonly S4_DIAGNOSIS='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s4_diagnosis.md'
readonly S4_DIAGNOSIS_SHA256='581b7230713344142911357f63d890408705f6bde0c7124de3414df941517fc4'
readonly S5_RUNNER='tests/h3req1_c03_startup_smoke_s5.sh'
readonly S5_RUNNER_SHA256='6e886754cde2c4a3feb998adaea6d8d5ecde03558eae15841e4cdb2c60347fdf'
readonly S5_MANIFEST='tests/h3req1-c03-startup-smoke-s5.sha256'
readonly S5_MANIFEST_SHA256='08a428daf847d690f4f72fdad03379eab4faeeba64362b78762c28e6f9e4ab03'
readonly S5_RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s5.md'
readonly S5_RESULT_SHA256='c7d32cbe20929e5db473fa6331d5a34117a30a7ad24776ebb412d88e06b45f3b'
readonly S5_RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s5'
readonly S6_JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S6-DIAGNOSTIC'
readonly S6_RUNNER='tests/h3req1_c03_startup_smoke_s6.sh'
readonly S6_RUNNER_SHA256='74d7ae4285a27741cc698caa55ff47363e8fd26efbed4c577ca6464bcd40e354'
readonly S6_MANIFEST='tests/h3req1-c03-startup-smoke-s6.sha256'
readonly S6_MANIFEST_SHA256='6590fee0612153c22e902b00c378c48803424b56277a1fd1db841e20f10be8ad'
readonly S6_RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s6.md'
readonly S6_RESULT_SHA256='38f5ff8c466886ae405db19bc26ad498accacf14e9de95218d1f7816bcde9b74'
readonly S6_RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s6'
readonly S7_RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s7.md'
readonly S7_RESULT_SHA256='f947a115e9f269376bef4103dce53a4817ded48085e3df855de5ccd6bfcd12ac'
readonly S7_RUNNER='tests/h3req1_c03_startup_smoke_s7.sh'
readonly S7_RUNNER_SHA256='2770cf0fc5f9b2115aee0ac23502dbdfe921590b082fed699da372b42c176244'
readonly S7_MANIFEST='tests/h3req1-c03-startup-smoke-s7.sha256'
readonly S7_MANIFEST_SHA256='21a2237d77d2e77e84f4e2341f0ec02cf063b4383f9e49fb11728e6044d54eee'
readonly S7_RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s7'
readonly S7_RUNTIME_ID='03253c5007b5e1228a0dc9712329180603dbdc5449ae9b414595c49aed14b803'
readonly S7_JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S7-PACKAGE-DIAGNOSTIC'
readonly S3_JIT='H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S3'
readonly S3_RUNNER='tests/h3req1_c03_startup_smoke_s3.sh'
readonly S3_RUNNER_SHA256='4077a9c6e14a0588fb972f77c4b27385cc223306a63bbaea553b239c87af1689'
readonly S3_MANIFEST='tests/h3req1-c03-startup-smoke-s3.sha256'
readonly S3_MANIFEST_SHA256='351c6590c24c466fe8af531f1d9661ef7a6fcc1f7170c617f223fefc70bdc018'
readonly S3_RESULT_LOG='.context/evidencia/h3req1_c03_startup_smoke_2026-10-10_s3.md'
readonly S3_RESULT_SHA256='b8aed3fedcbfab899b8c4a72a619e522bc156d94cfb04711d31661ffcca0224e'
readonly SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v4.sha256'
readonly SOURCE_MANIFEST_SHA256='fdcba48af1ec5ffeba91de0a6fa44022dd3027b85d6b9a5c02afea4c79678233'
readonly S3_SOURCE_MANIFEST='tests/h3req1-c03-startup-source-s1-v3.sha256'
readonly S3_SOURCE_MANIFEST_SHA256='4b6e99fb6feb85eb8b4ea8e899e69c2d3c497657b507b03004d45981b97417c8'
readonly RUNTIME_SOURCE_PATH='tests/h3req1_c03_integrated_runtime.mjs'
readonly -a DEPENDENCY_MANIFEST_PATHS=(
  'tests/h3req1-c03-bootstrap/package.json'
  'tests/h3req1-c03-bootstrap/package-lock.json'
  'web/package.json'
  'web/package-lock.json'
)
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly EXPECTED_DOCKER_CONTEXT='default'
readonly EXPECTED_DOCKER_ENDPOINT='unix:///var/run/docker.sock'
readonly EXPECTED_DOCKER_ENGINE='fc2115b2-c3c4-440e-89c6-26899eb7cb04|docker-desktop|Docker Desktop'
readonly NODE_IMAGE='node@sha256:dd5847a04b0deee391fa145f1f4c6d214196668b6bcc7988ebed67249f226844'
readonly S3_SOURCE_VOLUME='h3req1-c03-startup-source-20261010-s3'
readonly CANDIDATE_SOURCE_VOLUME='h3req1-c03-startup-source-20261010-s12'
readonly TOOLS_VOLUME='h3req1-c03-startup-tools-20261010-s3'
readonly PAGES_VOLUME='h3req1-c03-startup-pages-20261010-s3'
readonly NETWORK='h3req1-c03-startup-net-20261010-s3'
readonly S3_SNAPSHOT='h3req1-c03-startup-snapshot-20261010-s3'
readonly S3_TOOLS='h3req1-c03-startup-tools-20261010-s3'
readonly S3_PAGES='h3req1-c03-startup-pages-20261010-s3'
readonly S3_HOLDER='h3req1-c03-startup-volume-holder-20261010-s3'
readonly S4_RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s4'
readonly RUNTIME_CONTAINER='h3req1-c03-startup-runtime-20261010-s9'
readonly S12_EVIDENCE='.context/evidencia/h3req1_c03_source_snapshot_2026-10-10_s12.md'
readonly S12_SNAPSHOT_CONTAINER='h3req1-c03-startup-snapshot-20261010-s12'
readonly S12_SNAPSHOT_CONTAINER_ID='deed0a611eae8a8052d9fb21907a7ab6bc75c7c099d20532dbd28590045d1401'
readonly S12_SOURCE_VOLUME='h3req1-c03-startup-source-20261010-s12'
readonly S12_JIT='H3-CLOSE-03-SOURCE-SNAPSHOT-S12-2026-10-10'
readonly S12_RUNNER='tests/h3req1_c03_source_snapshot_s12.sh'
readonly S12_RUNNER_SHA256='e03287ad6d05bbb497f7cfc87aac3ad4fe9ef33a7e059396dd2d9fe0ebd69807'
readonly S12_SIDECAR='tests/h3req1-c03-source-snapshot-s12.sha256'
readonly S12_SIDECAR_SHA256='2d89fa0edc87f744a5e602acd5ddf8e9417083c94b1eb4842ef365f2e7028872'
readonly S12_EVIDENCE_SHA256='b95b4bfaa77e75e1af5ee9d751a461bb83d4deb686f113f50fa9bca7791735fd'
RUN_NONCE="${BASHPID}-$(date +%s%N)-${RANDOM}-${RANDOM}"
readonly RUN_NONCE
readonly -a EMPTY_PROXY_ENV=(
  --env HTTP_PROXY= --env HTTPS_PROXY= --env FTP_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env ftp_proxy= --env all_proxy= --env no_proxy= \
  --env npm_config_proxy= --env npm_config_http_proxy= --env npm_config_https_proxy=
)
ACTIVE_CONTAINER=''
STOP_ATTEMPTED_CONTAINER=''
S3_RUN_NONCE=''

[[ "${1:-}" == '--jit' && "${2:-}" == "$JIT" \
  && "${3:-}" == '--runner-sha256' && "${5:-}" == '--manifest-sha256' && $# -eq 6 ]] || {
  echo "Refusing to run: exact JIT $JIT, runner SHA-256, and manifest SHA-256 required." >&2
  exit 77
}
readonly APPROVED_RUNNER_SHA256="${4:-}"
readonly APPROVED_MANIFEST_SHA256="${6:-}"
[[ "$APPROVED_RUNNER_SHA256" =~ ^[a-f0-9]{64}$ && "$APPROVED_MANIFEST_SHA256" =~ ^[a-f0-9]{64}$ ]] \
  || { echo 'Refusing to run: invalid SHA-256 pin.' >&2; exit 77; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
[[ "$ROOT" == "$EXPECTED_ROOT" ]] || { echo 'Refusing to run: candidate checkout path changed.' >&2; exit 77; }
exec 3>&1
phase='preflight'
fail() { printf 'NO-GO: %s\n' "$1" >&2; return 1; }
docker_control() { timeout --foreground --signal=TERM --kill-after=5s 20s docker "$@"; }

stop_runtime() {
  local metadata container_id jit_label manifest_label run_label
  [[ "$RUNTIME_CONTAINER" == "${1:-}" ]] || { printf 'Refusing stop outside S9 runtime allowlist.\n' >&2; return 2; }
  metadata="$(docker_control inspect --format '{{.Id}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$RUNTIME_CONTAINER")" \
    || { printf 'Refusing stop: runtime ownership metadata unavailable.\n' >&2; return 1; }
  IFS='|' read -r container_id jit_label manifest_label run_label <<< "$metadata"
  [[ "$container_id" =~ ^[a-f0-9]{64}$ && "$jit_label" == "$JIT" \
    && "$manifest_label" == "$APPROVED_MANIFEST_SHA256" && "$run_label" == "$RUN_NONCE" ]] \
    || { printf 'Refusing stop: runtime ownership labels do not match this run.\n' >&2; return 2; }
  if timeout --foreground --signal=TERM --kill-after=5s 20s docker stop --time 10 "$container_id" >/dev/null 2>&1; then
    printf 'bounded-stop=completed container=%s owner=verified; resource preserved\n' "$RUNTIME_CONTAINER"
  else
    printf 'bounded-stop=failed-or-timed-out container=%s; resource preserved\n' "$RUNTIME_CONTAINER"
    return 1
  fi
}

stop_active_runtime() {
  [[ -n "$ACTIVE_CONTAINER" && "$ACTIVE_CONTAINER" != "$STOP_ATTEMPTED_CONTAINER" ]] || return 0
  STOP_ATTEMPTED_CONTAINER="$ACTIVE_CONTAINER"
  if stop_runtime "$ACTIVE_CONTAINER"; then
    printf 'bounded-stop=completed container=%s; resource preserved\n' "$ACTIVE_CONTAINER" >&2
  else
    printf 'bounded-stop=failed-or-timed-out container=%s; preserve resource and report NO-GO\n' "$ACTIVE_CONTAINER" >&2
  fi
}

on_error() {
  local status=$?
  stop_active_runtime
  printf 'Startup continuation halted phase=%s exit=%s; preserve all S3 resources.\n' "$phase" "$status" >&2
  printf 'Startup continuation halted phase=%s exit=%s; no cleanup/resume.\n' "$phase" "$status" >&3
}

on_signal() {
  local signal=$1 status=1
  case "$signal" in HUP) status=129 ;; INT) status=130 ;; TERM) status=143 ;; esac
  stop_active_runtime
  printf 'Startup continuation interrupted phase=%s signal=%s; preserve all resources.\n' "$phase" "$signal" >&2
  printf 'Startup continuation interrupted phase=%s signal=%s; no cleanup/resume.\n' "$phase" "$signal" >&3
  trap - ERR HUP INT TERM
  exit "$status"
}

trap on_error ERR
trap 'on_signal HUP' HUP
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

[[ -f "$ROOT/$MANIFEST" && ! -L "$ROOT/$MANIFEST" ]] || fail 'S9 manifest missing or symlinked'
[[ -d "$ROOT/.context" && ! -L "$ROOT/.context" \
  && -d "$ROOT/.context/evidencia" && ! -L "$ROOT/.context/evidencia" ]] \
  || fail 'S9 evidence parent is missing, non-directory, or symlinked'
[[ ! -e "$ROOT/$RESULT_LOG" && ! -L "$ROOT/$RESULT_LOG" ]] || fail 'S9 evidence path already exists'
[[ -f "$ROOT/$S3_RUNNER" && ! -L "$ROOT/$S3_RUNNER" \
  && -f "$ROOT/$S3_MANIFEST" && ! -L "$ROOT/$S3_MANIFEST" \
  && -f "$ROOT/$S3_RESULT_LOG" && ! -L "$ROOT/$S3_RESULT_LOG" \
  && -f "$ROOT/$PROBE_SCRIPT" && ! -L "$ROOT/$PROBE_SCRIPT" \
  && -f "$ROOT/$S4_RUNNER" && ! -L "$ROOT/$S4_RUNNER" \
  && -f "$ROOT/$S4_MANIFEST" && ! -L "$ROOT/$S4_MANIFEST" \
  && -f "$ROOT/$S4_RESULT_LOG" && ! -L "$ROOT/$S4_RESULT_LOG" \
  && -f "$ROOT/$S4_DIAGNOSIS" && ! -L "$ROOT/$S4_DIAGNOSIS" \
  && -f "$ROOT/$S5_RUNNER" && ! -L "$ROOT/$S5_RUNNER" \
  && -f "$ROOT/$S5_MANIFEST" && ! -L "$ROOT/$S5_MANIFEST" \
  && -f "$ROOT/$S5_RESULT_LOG" && ! -L "$ROOT/$S5_RESULT_LOG" \
  && -f "$ROOT/$S6_RUNNER" && ! -L "$ROOT/$S6_RUNNER" \
  && -f "$ROOT/$S6_MANIFEST" && ! -L "$ROOT/$S6_MANIFEST" \
  && -f "$ROOT/$S6_RESULT_LOG" && ! -L "$ROOT/$S6_RESULT_LOG" \
  && -f "$ROOT/$S7_RESULT_LOG" && ! -L "$ROOT/$S7_RESULT_LOG" \
  && -f "$ROOT/$S7_RUNNER" && ! -L "$ROOT/$S7_RUNNER" \
  && -f "$ROOT/$S7_MANIFEST" && ! -L "$ROOT/$S7_MANIFEST" \
  && -f "$ROOT/$S3_SOURCE_MANIFEST" && ! -L "$ROOT/$S3_SOURCE_MANIFEST" \
  && -f "$ROOT/$OUTPUT_FILTER" && ! -L "$ROOT/$OUTPUT_FILTER" \
  && -f "$ROOT/$PRELOAD_SCRIPT" && ! -L "$ROOT/$PRELOAD_SCRIPT" \
  && -f "$ROOT/$S12_RUNNER" && ! -L "$ROOT/$S12_RUNNER" \
  && -f "$ROOT/$S12_SIDECAR" && ! -L "$ROOT/$S12_SIDECAR" \
  && -f "$ROOT/$S12_EVIDENCE" && ! -L "$ROOT/$S12_EVIDENCE" ]] \
  || fail 'pinned startup or S12 snapshot artifact missing or symlinked'
[[ "$(sha256sum "$RUNNER" | cut -d' ' -f1)" == "$APPROVED_RUNNER_SHA256" ]] || fail 'S9 runner digest changed'
[[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" == "$APPROVED_MANIFEST_SHA256" ]] || fail 'S9 manifest digest changed'
[[ "$(sha256sum "$S3_RUNNER" | cut -d' ' -f1)" == "$S3_RUNNER_SHA256" ]] || fail 'S3 runner digest changed'
[[ "$(sha256sum "$S3_MANIFEST" | cut -d' ' -f1)" == "$S3_MANIFEST_SHA256" ]] || fail 'S3 manifest digest changed'
[[ "$(sha256sum "$S3_RESULT_LOG" | cut -d' ' -f1)" == "$S3_RESULT_SHA256" ]] || fail 'S3 result evidence digest changed'
[[ "$(sha256sum "$S4_RUNNER" | cut -d' ' -f1)" == "$S4_RUNNER_SHA256" ]] || fail 'S4 runner digest changed'
[[ "$(sha256sum "$S4_MANIFEST" | cut -d' ' -f1)" == "$S4_MANIFEST_SHA256" ]] || fail 'S4 manifest digest changed'
[[ "$(sha256sum "$S4_RESULT_LOG" | cut -d' ' -f1)" == "$S4_RESULT_SHA256" ]] || fail 'S4 result evidence digest changed'
[[ "$(sha256sum "$S4_DIAGNOSIS" | cut -d' ' -f1)" == "$S4_DIAGNOSIS_SHA256" ]] || fail 'S4 diagnosis digest changed'
[[ "$(sha256sum "$S5_RUNNER" | cut -d' ' -f1)" == "$S5_RUNNER_SHA256" ]] || fail 'S5 runner digest changed'
[[ "$(sha256sum "$S5_MANIFEST" | cut -d' ' -f1)" == "$S5_MANIFEST_SHA256" ]] || fail 'S5 manifest digest changed'
[[ "$(sha256sum "$S5_RESULT_LOG" | cut -d' ' -f1)" == "$S5_RESULT_SHA256" ]] || fail 'S5 result evidence digest changed'
[[ "$(sha256sum "$S6_RUNNER" | cut -d' ' -f1)" == "$S6_RUNNER_SHA256" ]] || fail 'S6 runner digest changed'
[[ "$(sha256sum "$S6_MANIFEST" | cut -d' ' -f1)" == "$S6_MANIFEST_SHA256" ]] || fail 'S6 manifest digest changed'
[[ "$(sha256sum "$S6_RESULT_LOG" | cut -d' ' -f1)" == "$S6_RESULT_SHA256" ]] || fail 'S6 result evidence digest changed'
[[ "$(sha256sum "$S7_RESULT_LOG" | cut -d' ' -f1)" == "$S7_RESULT_SHA256" ]] || fail 'S7 result evidence digest changed'
[[ "$(sha256sum "$S7_RUNNER" | cut -d' ' -f1)" == "$S7_RUNNER_SHA256" ]] || fail 'S7 runner digest changed'
[[ "$(sha256sum "$S7_MANIFEST" | cut -d' ' -f1)" == "$S7_MANIFEST_SHA256" ]] || fail 'S7 manifest digest changed'
[[ "$(sha256sum "$S12_RUNNER" | cut -d' ' -f1)" == "$S12_RUNNER_SHA256" ]] || fail 'S12 snapshot runner digest changed'
[[ "$(sha256sum "$S12_SIDECAR" | cut -d' ' -f1)" == "$S12_SIDECAR_SHA256" ]] || fail 'S12 snapshot sidecar digest changed'
[[ "$(cat "$S12_SIDECAR")" == "$S12_RUNNER_SHA256  $S12_RUNNER" ]] || fail 'S12 snapshot sidecar content changed'
[[ "$(sha256sum "$S12_EVIDENCE" | cut -d' ' -f1)" == "$S12_EVIDENCE_SHA256" ]] || fail 'S12 snapshot evidence digest changed'
[[ "$(sha256sum "$OUTPUT_FILTER" | cut -d' ' -f1)" == "$OUTPUT_FILTER_SHA256" ]] || fail 'S9 output filter digest changed'
[[ "$(sha256sum "$PRELOAD_SCRIPT" | cut -d' ' -f1)" == "$PRELOAD_SCRIPT_SHA256" ]] || fail 'S9 diagnostic preload digest changed'
[[ "$(sha256sum "$SOURCE_MANIFEST" | cut -d' ' -f1)" == "$SOURCE_MANIFEST_SHA256" ]] || fail 'source manifest digest changed'
[[ "$(sha256sum "$S3_SOURCE_MANIFEST" | cut -d' ' -f1)" == "$S3_SOURCE_MANIFEST_SHA256" ]] || fail 'S3 source manifest digest changed'
[[ "$(awk -v path="$RUNNER" '$2 == path { print $1 }' "$MANIFEST")" == "$APPROVED_RUNNER_SHA256" ]] || fail 'S9 manifest does not pin its runner'
sha256sum -c "$MANIFEST" >/dev/null || fail 'S9 inputs differ from manifest'
sha256sum -c "$S6_MANIFEST" >/dev/null || fail 'S6 inputs differ from the preserved manifest'
sha256sum -c "$S7_MANIFEST" >/dev/null || fail 'S7 inputs differ from the preserved manifest'
# shellcheck source=tests/h3req1_c03_startup_output_filter_s8.sh
source "$OUTPUT_FILTER"
sha256sum -c "$SOURCE_MANIFEST" >/dev/null || fail 'source inputs differ from source manifest'

verify_preserved_manifest_compatible() {
  local manifest_path=$1 manifest_label=$2 old_runtime_hash=$3
  local -a runtime_hashes=()

  mapfile -t runtime_hashes < <(awk -v expected_path="$RUNTIME_SOURCE_PATH" '$2 == expected_path { print $1 }' "$manifest_path")
  if ((${#runtime_hashes[@]} == 0)); then
    sha256sum -c "$manifest_path" >/dev/null \
      || fail "$manifest_label inputs differ from the preserved manifest"
    return 0
  fi
  [[ "${#runtime_hashes[@]}" == 1 && "${runtime_hashes[0]}" == "$old_runtime_hash" ]] \
    || fail "$manifest_label does not pin exactly the preserved V3 runtime source"
  awk -v runtime_path="$RUNTIME_SOURCE_PATH" '$2 != runtime_path { print }' "$manifest_path" \
    | sha256sum -c - >/dev/null \
    || fail "$manifest_label has an unexpected delta outside the integrated runtime"
}

verify_s3_dependency_inputs_compatible() {
  local source_count candidate_count old_hash old_runtime_hash path new_hash changed_runtime=0
  local -a old_paths=() candidate_paths=()

  [[ -f "$ROOT/$S3_SOURCE_MANIFEST" && ! -L "$ROOT/$S3_SOURCE_MANIFEST" ]] \
    || fail 'preserved S3 source manifest missing or symlinked'
  [[ "$(sha256sum "$S3_SOURCE_MANIFEST" | cut -d' ' -f1)" == "$S3_SOURCE_MANIFEST_SHA256" ]] \
    || fail 'preserved S3 source manifest digest changed'
  sha256sum -c "$SOURCE_MANIFEST" >/dev/null \
    || fail 'S12 candidate source manifest no longer matches its inputs'

  source_count="$(awk 'NF == 2 { count++ } END { print count+0 }' "$S3_SOURCE_MANIFEST")"
  candidate_count="$(awk 'NF == 2 { count++ } END { print count+0 }' "$SOURCE_MANIFEST")"
  [[ "$source_count" == 13 && "$candidate_count" == 13 ]] \
    || fail 'S3 and S12 source manifests do not contain the expected complete source set'
  [[ "$(awk 'NF != 2 || length($1) != 64 || $1 ~ /[^a-f0-9]/ || seen[$2]++ { bad=1 } END { print bad+0 }' "$S3_SOURCE_MANIFEST")" == 0 \
    && "$(awk 'NF != 2 || length($1) != 64 || $1 ~ /[^a-f0-9]/ || seen[$2]++ { bad=1 } END { print bad+0 }' "$SOURCE_MANIFEST")" == 0 ]] \
    || fail 'S3 or S12 source manifest contains malformed or duplicate entries'

  mapfile -t old_paths < <(awk '{ print $2 }' "$S3_SOURCE_MANIFEST" | LC_ALL=C sort)
  mapfile -t candidate_paths < <(awk '{ print $2 }' "$SOURCE_MANIFEST" | LC_ALL=C sort)
  [[ "${old_paths[*]}" == "${candidate_paths[*]}" ]] \
    || fail 'S3 dependency source set differs from the S12 candidate source set'

  old_runtime_hash="$(awk -v expected_path="$RUNTIME_SOURCE_PATH" '$2 == expected_path { print $1 }' "$S3_SOURCE_MANIFEST")"
  [[ "$old_runtime_hash" =~ ^[a-f0-9]{64}$ ]] || fail 'V3 runtime hash is missing or malformed'
  verify_preserved_manifest_compatible "$S3_MANIFEST" S3 "$old_runtime_hash"
  verify_preserved_manifest_compatible "$S4_MANIFEST" S4 "$old_runtime_hash"
  verify_preserved_manifest_compatible "$S5_MANIFEST" S5 "$old_runtime_hash"

  while IFS=' ' read -r old_hash path; do
    new_hash="$(awk -v expected_path="$path" '$2 == expected_path { print $1 }' "$SOURCE_MANIFEST")"
    [[ "$new_hash" =~ ^[a-f0-9]{64}$ ]] || fail "candidate source entry is missing or duplicated: $path"
    if [[ "$path" == "$RUNTIME_SOURCE_PATH" ]]; then
      [[ "$old_hash" != "$new_hash" ]] || fail 'expected runtime-only source delta is absent'
      changed_runtime=$((changed_runtime + 1))
    else
      [[ "$old_hash" == "$new_hash" ]] || fail "S3 source delta affects a non-runtime input: $path"
    fi
  done < "$S3_SOURCE_MANIFEST"
  [[ "$changed_runtime" == 1 ]] || fail 'S3 to S12 source delta is not exactly the integrated runtime'

  for path in "${DEPENDENCY_MANIFEST_PATHS[@]}"; do
    old_hash="$(awk -v expected_path="$path" '$2 == expected_path { print $1 }' "$S3_SOURCE_MANIFEST")"
    new_hash="$(awk -v expected_path="$path" '$2 == expected_path { print $1 }' "$SOURCE_MANIFEST")"
    [[ "$old_hash" =~ ^[a-f0-9]{64}$ && "$old_hash" == "$new_hash" ]] \
      || fail "S3 dependency manifest changed in S12 candidate: $path"
  done
}

verify_s3_dependency_inputs_compatible
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'candidate branch changed'
[[ "$(git rev-parse HEAD)" == "$EXPECTED_HEAD" ]] || fail 'candidate HEAD changed'
grep -Fqx "jit=$S3_JIT" "$S3_RESULT_LOG" || fail 'S3 evidence identity changed'
grep -Fqx "manifest-sha256=$S3_MANIFEST_SHA256" "$S3_RESULT_LOG" || fail 'S3 evidence manifest pin changed'
grep -Fqx 'source-snapshot=PASS files=14 symlinks=0 extraction-owner-restore=disabled' "$S3_RESULT_LOG" \
  || fail 'S3 snapshot PASS marker missing'
grep -Fqx "container=$S3_SNAPSHOT state=exited|0|false network=none" "$S3_RESULT_LOG" || fail 'S3 snapshot exit evidence missing'
grep -Fqx "container=$S3_TOOLS state=exited|0|false network=bridge" "$S3_RESULT_LOG" || fail 'S3 tools bootstrap exit evidence missing'
grep -Fqx "container=$S3_PAGES state=exited|0|false network=bridge" "$S3_RESULT_LOG" || fail 'S3 Pages bootstrap exit evidence missing'
grep -Fqx 'NO-GO: unexpected network name returned' "$S3_RESULT_LOG" || fail 'S3 stopped at an unexpected phase'
grep -Fqx 'phase=runtime-diagnostic-synthetic|error_code=PASS' "$S5_RESULT_LOG" || fail 'S5 diagnostic synthetic PASS missing'
grep -Fqx 'runtime-stage=dependency-roots-present' "$S5_RESULT_LOG" || fail 'S5 dependency-root marker missing'
grep -Fqx 'runtime-project-frame=line:800:column:3' "$S5_RESULT_LOG" || fail 'S5 failure frame evidence missing'
grep -Fqx 'healthz=NO-GO reason=runtime-not-ready attempts=3' "$S5_RESULT_LOG" || fail 'S5 healthz failure evidence changed'
grep -Fqx "container=$S5_RUNTIME_CONTAINER state=exited|1|false network=internal-s3" "$S5_RESULT_LOG" \
  || fail 'S5 preserved runtime exit evidence missing'
grep -Fqx 'phase=runtime-diagnostic-synthetic|error_code=PASS' "$S6_RESULT_LOG" || fail 'S6 diagnostic synthetic PASS missing'
grep -Fqx 'runtime-error-class=MINIFLARECOREERROR' "$S6_RESULT_LOG" || fail 'S6 classified error evidence missing'
grep -Fqx 'healthz=NO-GO reason=runtime-not-ready attempts=4' "$S6_RESULT_LOG" || fail 'S6 healthz failure evidence changed'
grep -Fqx "container=$S6_RUNTIME_CONTAINER state=exited|1|false network=internal-s3" "$S6_RESULT_LOG" \
  || fail 'S6 preserved runtime exit evidence missing'
grep -Fqx "jit=$S7_JIT" "$S7_RESULT_LOG" || fail 'S7 evidence identity changed'
grep -Fqx "manifest-sha256=$S7_MANIFEST_SHA256" "$S7_RESULT_LOG" || fail 'S7 evidence manifest pin changed'
grep -Fqx 'runtime-error-code=ERR_VALIDATION' "$S7_RESULT_LOG" || fail 'S7 validation code evidence missing'
grep -Fqx 'healthz=NO-GO reason=runtime-not-ready attempts=3' "$S7_RESULT_LOG" || fail 'S7 healthz failure evidence changed'
grep -Fqx "container=$S7_RUNTIME_CONTAINER state=exited|1|false network=internal-s3" "$S7_RESULT_LOG" \
  || fail 'S7 preserved runtime exit evidence missing'

[[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" && -z "${DOCKER_TLS_VERIFY:-}" && -z "${DOCKER_CERT_PATH:-}" ]] \
  || fail 'Docker endpoint override rejected; local Unix context only'
context_name="$(docker_control context show)" || fail 'cannot read Docker context within timeout'
[[ "$context_name" == "$EXPECTED_DOCKER_CONTEXT" ]] || fail 'Docker context differs from attested Desktop context'
endpoint="$(docker_control context inspect --format '{{ (index .Endpoints "docker").Host }}' "$context_name")" || fail 'cannot read Docker endpoint within timeout'
[[ "$endpoint" == "$EXPECTED_DOCKER_ENDPOINT" && -S "${endpoint#unix://}" ]] || fail 'Docker endpoint differs from attested Unix socket'
export DOCKER_CONTEXT="$context_name"
engine_identity="$(docker_control info --format '{{.ID}}|{{.Name}}|{{.OperatingSystem}}')" || fail 'cannot verify Docker Desktop identity'
[[ "$engine_identity" == "$EXPECTED_DOCKER_ENGINE" ]] || fail 'Docker engine identity differs from attested Desktop daemon'
docker_control image inspect "$NODE_IMAGE" >/dev/null 2>&1 || fail 'pinned Node image is not local; pulls are forbidden'

verify_s3_container() {
  local name=$1 expected_state=$2 expected_network=$3 metadata actual_name image state exit_code oom network jit manifest run
  metadata="$(docker_control inspect --format '{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}' "$name")" \
    || fail "cannot verify preserved S3 resource: $name"
  IFS='|' read -r actual_name image state exit_code oom network jit manifest run <<< "$metadata"
  [[ "$actual_name" == "/$name" && "$image" == "$NODE_IMAGE" && "$state" == "$expected_state" \
    && "$oom" == false && "$network" == "$expected_network" && "$jit" == "$S3_JIT" \
    && "$manifest" == "$S3_MANIFEST_SHA256" && "$run" =~ ^[0-9]+-[0-9]+-[0-9]+-[0-9]+$ ]] \
    || fail "preserved S3 container identity/state mismatch: $name"
  if [[ -z "$S3_RUN_NONCE" ]]; then S3_RUN_NONCE="$run"; else [[ "$run" == "$S3_RUN_NONCE" ]] || fail 'S3 run ownership labels differ'; fi
  if [[ "$expected_state" == exited ]]; then [[ "$exit_code" == 0 ]] || fail "S3 bootstrap container exit is not zero: $name"; fi
}

verify_s3_volume() {
  local name=$1 size=$2 metadata actual_name driver type device options jit manifest run
  metadata="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{index .Options "type"}}|{{index .Options "device"}}|{{index .Options "o"}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}' "$name")" \
    || fail "cannot verify preserved S3 volume: $name"
  IFS='|' read -r actual_name driver type device options jit manifest run <<< "$metadata"
  [[ "$actual_name" == "$name" && "$driver" == local && "$type" == tmpfs && "$device" == tmpfs \
    && "$options" == "nosuid,nodev,size=$size" && "$jit" == "$S3_JIT" \
    && "$manifest" == "$S3_MANIFEST_SHA256" && "$run" == "$S3_RUN_NONCE" ]] \
    || fail "preserved S3 volume identity/options mismatch: $name"
}

verify_s12_candidate_snapshot() {
  local snapshot_id snapshot_name snapshot_state snapshot_exit snapshot_oom snapshot_network snapshot_jit snapshot_manifest
  local snapshot_run snapshot_metadata snapshot_volume_metadata volume_name volume_driver volume_options volume_jit volume_manifest volume_run
  local expected_mode_manifest expected_mode_sha evidence_mode_sha verify_output
  grep -Fqx "jit=$S12_JIT" "$S12_EVIDENCE" || fail 'S12 snapshot evidence identity changed'
  grep -Fqx "runner-sha256=$S12_RUNNER_SHA256" "$S12_EVIDENCE" || fail 'S12 evidence runner pin changed'
  grep -Fqx "sidecar-sha256=$S12_SIDECAR_SHA256" "$S12_EVIDENCE" || fail 'S12 evidence sidecar pin changed'
  grep -Fqx "source-manifest-sha256=$SOURCE_MANIFEST_SHA256" "$S12_EVIDENCE" || fail 'S12 evidence source manifest pin changed'
  grep -Fqx "container-created-id=$S12_SNAPSHOT_CONTAINER_ID" "$S12_EVIDENCE" || fail 'S12 snapshot container ID evidence changed'
  grep -Fqx 'snapshot-container=h3req1-c03-startup-snapshot-20261010-s12|exited|0|oom=false|network=none' "$S12_EVIDENCE" \
    || fail 'S12 snapshot container PASS evidence changed'
  grep -Fqx 'snapshot-verifier=exit-0|network=none|mount=readonly' "$S12_EVIDENCE" \
    || fail 'S12 read-only verifier evidence changed'
  grep -Fqx 'source-snapshot=PASS files=14 symlinks=0 producer=0 receiver=0 verifier=0' "$S12_EVIDENCE" \
    || fail 'S12 complete snapshot PASS marker missing'

  snapshot_metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.HostConfig.NetworkMode}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.snapshot.run"}}' "$S12_SNAPSHOT_CONTAINER")" \
    || fail 'cannot verify S12 snapshot container metadata'
  IFS='|' read -r snapshot_id snapshot_name snapshot_state snapshot_exit snapshot_oom snapshot_network snapshot_jit snapshot_manifest snapshot_run <<< "$snapshot_metadata"
  [[ "$snapshot_id" == "$S12_SNAPSHOT_CONTAINER_ID" && "$snapshot_name" == "/$S12_SNAPSHOT_CONTAINER" \
    && "$snapshot_state" == exited && "$snapshot_exit" == 0 && "$snapshot_oom" == false \
    && "$snapshot_network" == none && "$snapshot_jit" == "$S12_JIT" \
    && "$snapshot_manifest" == "$S12_SIDECAR_SHA256" \
    && "$snapshot_run" =~ ^[0-9]+-[0-9]+-[0-9]+$ ]] || fail 'S12 snapshot container identity/owner state differs'

  snapshot_volume_metadata="$(docker_control volume inspect --format '{{.Name}}|{{.Driver}}|{{json .Options}}|{{index .Labels "com.studiamatch.h3.snapshot.jit"}}|{{index .Labels "com.studiamatch.h3.snapshot.manifest"}}|{{index .Labels "com.studiamatch.h3.snapshot.run"}}' "$S12_SOURCE_VOLUME")" \
    || fail 'cannot verify S12 snapshot volume metadata'
  IFS='|' read -r volume_name volume_driver volume_options volume_jit volume_manifest volume_run <<< "$snapshot_volume_metadata"
  [[ "$volume_name" == "$S12_SOURCE_VOLUME" && "$volume_driver" == local && "$volume_options" == null \
    && "$volume_jit" == "$S12_JIT" && "$volume_manifest" == "$S12_SIDECAR_SHA256" \
    && "$volume_run" == "$snapshot_run" ]] || fail 'S12 snapshot volume identity/owner metadata differs'

  expected_mode_manifest="$( {
    while IFS=' ' read -r _ source_path; do
      printf '%s|%s\n' "$source_path" "$(stat -Lc '%a' -- "$source_path")"
    done < "$SOURCE_MANIFEST"
    printf '%s|%s\n' "$SOURCE_MANIFEST" "$(stat -Lc '%a' -- "$SOURCE_MANIFEST")"
  } | LC_ALL=C sort | tr '\n' ';' )" || fail 'cannot rebuild S12 source permission map'
  expected_mode_sha="$(printf '%s' "$expected_mode_manifest" | sha256sum | cut -d' ' -f1)" \
    || fail 'cannot hash S12 source permission map'
  evidence_mode_sha="$(awk -F= '$1 == "source-permission-map-sha256" { print $2 }' "$S12_EVIDENCE")"
  [[ "$expected_mode_sha" =~ ^[a-f0-9]{64}$ && "$expected_mode_sha" == "$evidence_mode_sha" ]] \
    || fail 'candidate source permission map differs from S12 snapshot evidence'

  verify_output="$(docker_control run --rm --pull=never --platform linux/amd64 --network=none --log-driver none \
    --read-only --cpus=0.5 --memory=128m --memory-swap=128m --pids-limit=64 --cap-drop=ALL \
    --security-opt no-new-privileges:true --mount "type=volume,src=$S12_SOURCE_VOLUME,dst=/snapshot,readonly" \
    --env H3_SOURCE_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" \
    --env "H3_SOURCE_MODE_MANIFEST=$expected_mode_manifest" \
    "$NODE_IMAGE" sh -lc 'set -eu; cd /snapshot; test "$(sha256sum tests/h3req1-c03-startup-source-s1-v4.sha256 | cut -d" " -f1)" = "$H3_SOURCE_MANIFEST_SHA256"; sha256sum -c tests/h3req1-c03-startup-source-s1-v4.sha256 >/dev/null 2>&1; test -z "$(find . -type l -print -quit)"; test "$(find . -type f | wc -l | tr -d "[:space:]")" = 14; expected="$( { awk "{print \$2}" tests/h3req1-c03-startup-source-s1-v4.sha256; printf "%s\\n" tests/h3req1-c03-startup-source-s1-v4.sha256; } | LC_ALL=C sort -u )"; actual="$(find . -type f -printf "%P\\n" | LC_ALL=C sort)"; test "$expected" = "$actual"; actual_modes="$(find . -type f -printf "%P|%m\\n" | LC_ALL=C sort | tr "\\n" ";")"; test "$actual_modes" = "$H3_SOURCE_MODE_MANIFEST"; printf "snapshot-volume-verification=PASS\\n"' 2>/dev/null)" \
    || fail 'S12 snapshot volume read-only verification failed'
  [[ "$verify_output" == 'snapshot-volume-verification=PASS' ]] || fail 'S12 snapshot verifier output mismatch'
  printf 's12-snapshot=PASS|files=14|hashes=13/13|symlinks=0|permissions=exact|network=none|mount=readonly\n'
}

phase='verify-preserved-s3-resources-and-resolve-network-id'
verify_s3_container "$S3_SNAPSHOT" exited none
verify_s3_container "$S3_TOOLS" exited bridge
verify_s3_container "$S3_PAGES" exited bridge
verify_s3_container "$S3_HOLDER" running none
verify_s3_volume "$S3_SOURCE_VOLUME" 96m
verify_s3_volume "$TOOLS_VOLUME" 768m
verify_s3_volume "$PAGES_VOLUME" 1024m
network_meta="$(docker_control network inspect --format '{{.Id}}|{{.Name}}|{{.Driver}}|{{.Internal}}|{{index .Labels "com.studiamatch.h3.startup.jit"}}|{{index .Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Labels "com.studiamatch.h3.startup.run"}}' "$NETWORK")" \
  || fail 'cannot resolve preserved S3 network by name'
IFS='|' read -r network_id network_name network_driver network_internal network_jit network_manifest network_run <<< "$network_meta"
[[ "$network_id" =~ ^[a-f0-9]{64}$ && "$network_name" == "$NETWORK" && "$network_driver" == bridge \
  && "$network_internal" == true && "$network_jit" == "$S3_JIT" \
  && "$network_manifest" == "$S3_MANIFEST_SHA256" && "$network_run" == "$S3_RUN_NONCE" ]] \
  || fail 'preserved S3 network ID/name/internal/owner metadata mismatch'
network_container_count="$(docker_control network inspect --format '{{len .Containers}}' "$network_id")" \
  || fail 'cannot verify preserved S3 network endpoint count'
[[ "$network_container_count" == 0 ]] || fail 'S3 internal network already has an unexpected endpoint'

s7_metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}|{{.HostConfig.NetworkMode}}' "$S7_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S7 container metadata'
IFS='|' read -r s7_id s7_name s7_state s7_exit s7_oom s7_jit s7_manifest s7_run s7_network_mode <<< "$s7_metadata"
[[ "$s7_id" == "$S7_RUNTIME_ID" && "$s7_name" == "/$S7_RUNTIME_CONTAINER" \
  && "$s7_state" == exited && "$s7_exit" == 1 && "$s7_oom" == false \
  && "$s7_jit" == "$S7_JIT" && "$s7_manifest" == "$S7_MANIFEST_SHA256" \
  && "$s7_run" =~ ^[0-9]+-[0-9]+-[0-9]+-[0-9]+$ \
  && "$s7_network_mode" == "$network_id" ]] || fail 'preserved S7 container identity/state differs from evidence'
s7_network_attachment="$(docker_control inspect --format '{{range $name, $net := .NetworkSettings.Networks}}{{$name}}|{{$net.NetworkID}}{{end}}' "$S7_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S7 network attachment'
[[ "$s7_network_attachment" == "$NETWORK|$network_id" ]] || fail 'preserved S7 attachment differs from internal S3 network'

phase='verify-preserved-s4-failure-metadata'
s4_metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{.HostConfig.NetworkMode}}' "$S4_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S4 runtime metadata'
IFS='|' read -r s4_id s4_name s4_state s4_exit s4_oom s4_jit s4_manifest s4_network_mode <<< "$s4_metadata"
[[ "$s4_id" =~ ^[a-f0-9]{64}$ && "$s4_name" == "/$S4_RUNTIME_CONTAINER" \
  && "$s4_state" == exited && "$s4_exit" == 1 && "$s4_oom" == false \
  && "$s4_jit" == 'H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S4-RESUME-S3' \
  && "$s4_manifest" == "$S4_MANIFEST_SHA256" && "$s4_network_mode" == "$network_id" ]] \
  || fail 'preserved S4 runtime metadata differs from the recorded failure'
s4_network_attachment="$(docker_control inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}|{{$v.NetworkID}}{{end}}' "$S4_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S4 network attachment'
[[ "$s4_network_attachment" == "$NETWORK|$network_id" ]] \
  || fail 'preserved S4 runtime network attachment differs from the verified S3 network'

s5_metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{.HostConfig.NetworkMode}}' "$S5_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S5 runtime metadata'
IFS='|' read -r s5_id s5_name s5_state s5_exit s5_oom s5_jit s5_manifest s5_network_mode <<< "$s5_metadata"
[[ "$s5_id" =~ ^[a-f0-9]{64}$ && "$s5_name" == "/$S5_RUNTIME_CONTAINER" \
  && "$s5_state" == exited && "$s5_exit" == 1 && "$s5_oom" == false \
  && "$s5_jit" == 'H3-CLOSE-03-WORKERD-STARTUP-SMOKE-2026-10-10-S5-DIAGNOSTIC' \
  && "$s5_manifest" == "$S5_MANIFEST_SHA256" && "$s5_network_mode" == "$network_id" ]] \
  || fail 'preserved S5 runtime metadata differs from the recorded failure'
s5_network_attachment="$(docker_control inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}|{{$v.NetworkID}}{{end}}' "$S5_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S5 network attachment'
[[ "$s5_network_attachment" == "$NETWORK|$network_id" ]] \
  || fail 'preserved S5 runtime network attachment differs from the verified S3 network'

s6_metadata="$(docker_control inspect --format '{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{.HostConfig.NetworkMode}}' "$S6_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S6 runtime metadata'
IFS='|' read -r s6_id s6_name s6_state s6_exit s6_oom s6_jit s6_manifest s6_network_mode <<< "$s6_metadata"
[[ "$s6_id" =~ ^[a-f0-9]{64}$ && "$s6_name" == "/$S6_RUNTIME_CONTAINER" \
  && "$s6_state" == exited && "$s6_exit" == 1 && "$s6_oom" == false \
  && "$s6_jit" == "$S6_JIT" && "$s6_manifest" == "$S6_MANIFEST_SHA256" \
  && "$s6_network_mode" == "$network_id" ]] \
  || fail 'preserved S6 runtime metadata differs from its recorded failure'
s6_network_attachment="$(docker_control inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}|{{$v.NetworkID}}{{end}}' "$S6_RUNTIME_CONTAINER")" \
  || fail 'cannot verify preserved S6 network attachment'
[[ "$s6_network_attachment" == "$NETWORK|$network_id" ]] \
  || fail 'preserved S6 runtime network attachment differs from the verified S3 network'

container_names="$(docker_control ps -a --format '{{.Names}}' --filter "name=$RUNTIME_CONTAINER")" || fail 'cannot check S9 runtime-name collision'
while IFS= read -r existing_name; do [[ "$existing_name" != "$RUNTIME_CONTAINER" ]] || fail 'S9 runtime container name is already occupied'; done <<< "$container_names"

set -o noclobber
exec >"$ROOT/$RESULT_LOG" 2>&1
set +o noclobber
printf 'jit=%s\nmanifest-sha256=%s\nrunner-sha256=%s\n' "$JIT" "$APPROVED_MANIFEST_SHA256" "$APPROVED_RUNNER_SHA256"
printf '# H3REQ1 C03 startup smoke S9 — Pages/workerd healthz from the verified S12 candidate snapshot\n\n'
printf 'scope=Pages/workerd startup and healthz only; candidate source volume S12 plus S3 tools/pages dependency volumes; internal network without egress; no DB, PostgREST, Edge, SQL, Auth, email, credentials, or remotes\n'
printf 'dependency-inputs=compatible|package-locks=unchanged|source-delta=integrated-runtime-only\n'
sha256sum -c "$MANIFEST"
phase='verify-s12-candidate-snapshot'
verify_s12_candidate_snapshot
printf 'phase=s12-candidate-snapshot|error_code=OK\n'
printf 'phase=s3-resources|error_code=OK\nphase=s3-network-id-resolution|error_code=OK\n'
filter_test_output="$(docker_control run --rm --pull=never --platform linux/amd64 --network=none --log-driver none \
  --read-only --cpus=1 --memory=128m --memory-swap=128m --pids-limit=64 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  --mount "type=bind,src=$ROOT/$OUTPUT_FILTER,dst=/filter.sh,readonly" \
  "$NODE_IMAGE" bash /filter.sh --self-test)" || fail 'S9 output-filter synthetic tests failed'
[[ "$filter_test_output" == 'phase=runtime-output-filter-synthetic|error_code=PASS' ]] \
  || fail 'S9 output-filter synthetic result did not match the closed PASS marker'
printf '%s\n' "$filter_test_output"

diag_test_output="$(docker_control run --rm --pull=never --platform linux/amd64 --network=none --log-driver none \
  --read-only --cpus=1 --memory=128m --memory-swap=128m --pids-limit=64 \
  --cap-drop=ALL --security-opt no-new-privileges:true \
  --mount "type=bind,src=$ROOT/$PROBE_SCRIPT,dst=/probe.mjs,readonly" \
  --mount "type=bind,src=$ROOT/$PRELOAD_SCRIPT,dst=/diag-preload.cjs,readonly" \
  "$NODE_IMAGE" sh -lc 'node --check /diag-preload.cjs && node /probe.mjs --self-test')" \
  || fail 'S9 diagnostic parser/preload syntax or synthetic tests failed'
[[ "$diag_test_output" == 'phase=runtime-diagnostic-synthetic|error_code=PASS' ]] \
  || fail 'S9 diagnostic synthetic result did not match the closed PASS marker'
printf '%s\n' "$diag_test_output"

phase='one-shot-pages-workerd-runtime-healthz'
set +e
ACTIVE_CONTAINER="$RUNTIME_CONTAINER"
timeout --foreground --signal=TERM --kill-after=10s 180s docker run --pull=never --platform linux/amd64 \
  --name "$RUNTIME_CONTAINER" --network "$network_id" --log-driver none --read-only \
  --cpus=2 --memory=2g --memory-swap=2g --pids-limit=256 --stop-timeout 10 \
  --cap-drop=ALL --security-opt no-new-privileges:true "${EMPTY_PROXY_ENV[@]}" \
  --label "com.studiamatch.h3.startup.jit=$JIT" --label "com.studiamatch.h3.startup.manifest=$APPROVED_MANIFEST_SHA256" \
  --label "com.studiamatch.h3.startup.run=$RUN_NONCE" \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m --tmpfs /run/c03-private:rw,noexec,nosuid,size=8m \
  --tmpfs /run/c03-certs:rw,nosuid,size=16m \
  --mount "type=volume,src=$CANDIDATE_SOURCE_VOLUME,dst=/candidate,readonly" \
  --mount "type=volume,src=$TOOLS_VOLUME,dst=/tools,readonly" \
  --mount "type=volume,src=$PAGES_VOLUME,dst=/web-deps,readonly" \
  --mount "type=bind,src=$ROOT/$PROBE_SCRIPT,dst=/probe.mjs,readonly" \
  --mount "type=bind,src=$ROOT/$PRELOAD_SCRIPT,dst=/diag-preload.cjs,readonly" \
  --env H3_C03_ROOT=/candidate --env H3_C03_TOOLS_ROOT=/tools --env H3_C03_CERTS_ROOT=/run/c03-certs \
  --env H3_C03_WEB_DEPS_ROOT=/web-deps --env H3_C03_PRIVATE_ROOT=/run/c03-private \
  --env H3_C03_MANIFEST_SHA256="$SOURCE_MANIFEST_SHA256" --env H3_C03_DEPENDENCY_BOOTSTRAP_COMPLETE=true \
  "$NODE_IMAGE" node /probe.mjs 2>&1 | sanitize_runtime_output
runtime_status=$?
set -e
if [[ "$runtime_status" -eq 124 || "$runtime_status" -eq 137 || "$runtime_status" -eq 143 || "$runtime_status" -eq 129 || "$runtime_status" -eq 130 ]]; then
  printf 'runtime-time-limit-reached; stopping only this new runtime container\n'
  stop_active_runtime || true
fi
runtime_metadata="$(docker_control inspect --format '{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{index .Config.Labels "com.studiamatch.h3.startup.jit"}}|{{index .Config.Labels "com.studiamatch.h3.startup.manifest"}}|{{index .Config.Labels "com.studiamatch.h3.startup.run"}}|{{.HostConfig.NetworkMode}}' "$RUNTIME_CONTAINER")" \
  || fail 'cannot verify S9 runtime exit'
IFS='|' read -r actual_name runtime_state runtime_exit oom jit manifest run network_mode <<< "$runtime_metadata"
[[ "$actual_name" == "/$RUNTIME_CONTAINER" && "$runtime_state" == exited && "$runtime_exit" =~ ^[0-9]+$ \
  && "$oom" == false && "$jit" == "$JIT" && "$manifest" == "$APPROVED_MANIFEST_SHA256" \
  && "$run" == "$RUN_NONCE" && "$network_mode" == "$network_id" ]] \
  || fail 'S9 runtime identity/state/exit predicate failed'
network_attachment="$(docker_control inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}|{{$v.NetworkID}}{{end}}' "$RUNTIME_CONTAINER")" \
  || fail 'cannot verify S9 runtime network attachment'
[[ "$network_attachment" == "$NETWORK|$network_id" ]] \
  || fail 'S9 runtime network attachment differs from the exact preflighted internal network ID'
ACTIVE_CONTAINER=''
printf 'container=%s state=%s|%s|%s network=internal-s3\n' "$RUNTIME_CONTAINER" "$runtime_state" "$runtime_exit" "$oom"
[[ "$runtime_status" -eq 0 && "$runtime_exit" == 0 ]] || fail 'Pages/workerd startup runtime failed'
grep -Fqx 'smoke=PASS workerd-pages-healthz=true edge-runtime=not-started database=not-started' "$RESULT_LOG" \
  || fail 'sanitized evidence lacks exact Pages/workerd healthz PASS'
printf 'phase=pages-workerd-healthz|error_code=OK\nexit=0\n'
printf '%s\n' 'Startup continuation: PASS (fresh real Miniflare/workerd Pages workers only).' \
  'S3 snapshot/dependency volumes and internal network remain preserved; no cleanup was performed.' \
  "Sanitized evidence: $RESULT_LOG"
trap - ERR
printf '%s\n' 'Startup continuation: PASS (fresh real Miniflare/workerd Pages workers only).' "Sanitized evidence: $RESULT_LOG" >&3
exec 3>&-
