#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
source tests/h3req1_c03_docker_inspect_projection.sh

fail() {
  printf 'projection regression failed: %s\n' "$1" >&2
  exit 1
}

fixture_id="$(printf '%064d' 0 | tr '0' 'a')"
fixture_image_id="sha256:$(printf '%064d' 0 | tr '0' 'b')"
fixture_manifest="$(printf '%064d' 0 | tr '0' 'c')"
fixture_jit='H3-CLOSE-03-SNAPSHOT-DIAGNOSTIC-D4-2026-10-07'
fixture_run='12345-1760000000000-11-22'
fixture_name='/h3req1-c03-snapshot-diagnostic-d4-20261007'
fixture_path='/diag'
fixture_options='rw,noexec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700'
fixture_tmpfs_mode=valid
fixture_mounts_json='[]'
fixture_actual_image_id=$fixture_image_id

projection() {
  local tmpfs_json tmpfs_count
  if [[ "$fixture_tmpfs_mode" == missing ]]; then
    tmpfs_json=null
    tmpfs_count=0
  else
    tmpfs_json="{\"$fixture_path\":\"$fixture_options\"}"
    tmpfs_count=1
  fi
  printf 'id\t"%s"\n' "$fixture_id"
  printf 'name\t"%s"\n' "$fixture_name"
  printf 'state\t"exited"\n'
  printf 'exit_code\t0\n'
  printf 'oom\tfalse\n'
  printf 'jit_label\t"%s"\n' "$fixture_jit"
  printf 'manifest_label\t"%s"\n' "$fixture_manifest"
  printf 'run_label\t"%s"\n' "$fixture_run"
  printf 'network_mode\t"none"\n'
  printf 'readonly_root\ttrue\n'
  printf 'configured_user\t"1001:1001"\n'
  printf 'cap_drop\t["ALL"]\n'
  printf 'security_opt\t["no-new-privileges:true"]\n'
  printf 'memory\t134217728\n'
  printf 'memory_swap\t134217728\n'
  printf 'nano_cpus\t500000000\n'
  printf 'pids_limit\t64\n'
  printf 'restart\t"no"\n'
  printf 'tmpfs\t%s\n' "$tmpfs_json"
  printf 'tmpfs_count\t%s\n' "$tmpfs_count"
  printf 'log_type\t"local"\n'
  printf 'port_bindings\tnull\n'
  printf 'shm_size\t16777216\n'
  printf 'binds\tnull\n'
  printf 'host_config_mounts\t[]\n'
  printf 'mounts\t%s\n' "$fixture_mounts_json"
  printf 'image_id\t"%s"\n' "$fixture_actual_image_id"
}

assert_pass() {
  local candidate
  candidate=$(projection)
  h3_compare_docker_projection "$fixture_id" "$fixture_name" "$fixture_jit" "$fixture_manifest" \
    "$fixture_run" exited 0 "$fixture_path" "$fixture_options" local "$fixture_image_id" "$candidate" \
    || fail 'D4-shaped HostConfig.Tmpfs and empty .Mounts projection was rejected'
}

assert_pass

fixture_tmpfs_mode=missing
missing_tmpfs=$(projection)
fixture_tmpfs_mode=valid
if h3_compare_docker_projection "$fixture_id" "$fixture_name" "$fixture_jit" "$fixture_manifest" \
  "$fixture_run" exited 0 "$fixture_path" "$fixture_options" local "$fixture_image_id" "$missing_tmpfs"; then
  fail 'missing tmpfs was accepted'
else
  status=$?
fi
[ "$status" -eq 1 ] || fail 'missing tmpfs did not return a control mismatch'
[[ ",$CONTROL_MISMATCH_FIELDS," == *,tmpfs,* && ",$CONTROL_MISMATCH_FIELDS," == *,tmpfs_count,* ]] \
  || fail 'missing tmpfs field names were not reported'

fixture_mounts_json='[{"Type":"bind"}]'
unexpected_mount=$(projection)
fixture_mounts_json='[]'
if h3_compare_docker_projection "$fixture_id" "$fixture_name" "$fixture_jit" "$fixture_manifest" \
  "$fixture_run" exited 0 "$fixture_path" "$fixture_options" local "$fixture_image_id" "$unexpected_mount"; then
  fail 'unexpected persistent mount was accepted'
else
  status=$?
fi
[ "$status" -eq 1 ] || fail 'unexpected mount did not return a control mismatch'
[[ ",$CONTROL_MISMATCH_FIELDS," == *,mounts,* ]] || fail 'mount mismatch field was not reported'

fixture_actual_image_id="sha256:$(printf '%064d' 0 | tr '0' 'd')"
wrong_image=$(projection)
fixture_actual_image_id=$fixture_image_id
if h3_compare_docker_projection "$fixture_id" "$fixture_name" "$fixture_jit" "$fixture_manifest" \
  "$fixture_run" exited 0 "$fixture_path" "$fixture_options" local "$fixture_image_id" "$wrong_image"; then
  fail 'different immutable image ID was accepted'
else
  status=$?
fi
[ "$status" -eq 1 ] || fail 'image mismatch did not return a control mismatch'
[[ ",$CONTROL_MISMATCH_FIELDS," == *,image_id,* ]] || fail 'image mismatch field was not reported'

duplicate_field="$(projection)"
duplicate_field+=$'\nmounts\t[]'
if h3_compare_docker_projection "$fixture_id" "$fixture_name" "$fixture_jit" "$fixture_manifest" \
  "$fixture_run" exited 0 "$fixture_path" "$fixture_options" local "$fixture_image_id" "$duplicate_field"; then
  fail 'duplicate field was accepted'
else
  status=$?
fi
[ "$status" -eq 2 ] && [ "$CONTROL_SCHEMA_ERROR" = duplicate-field ] \
  || fail 'duplicate field did not fail closed as a schema error'

printf 'docker-inspect-projection-regressions=PASS|d4-tmpfs-shape=1|negative-controls=4|image-id=checked|schema=fail-closed\n'
