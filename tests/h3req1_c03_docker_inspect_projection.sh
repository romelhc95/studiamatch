#!/usr/bin/env bash

h3_docker_inspect_projection_format() {
  cat <<'H3_DOCKER_INSPECT_PROJECTION'
{{printf "id\t%s\n" (json .Id)}}
{{printf "name\t%s\n" (json .Name)}}
{{printf "state\t%s\n" (json .State.Status)}}
{{printf "exit_code\t%s\n" (json .State.ExitCode)}}
{{printf "oom\t%s\n" (json .State.OOMKilled)}}
{{printf "jit_label\t%s\n" (json (index .Config.Labels "com.studiamatch.h3.snapshot.jit"))}}
{{printf "manifest_label\t%s\n" (json (index .Config.Labels "com.studiamatch.h3.snapshot.manifest"))}}
{{printf "run_label\t%s\n" (json (index .Config.Labels "com.studiamatch.h3.snapshot.run"))}}
{{printf "network_mode\t%s\n" (json .HostConfig.NetworkMode)}}
{{printf "readonly_root\t%s\n" (json .HostConfig.ReadonlyRootfs)}}
{{printf "configured_user\t%s\n" (json .Config.User)}}
{{printf "cap_drop\t%s\n" (json .HostConfig.CapDrop)}}
{{printf "security_opt\t%s\n" (json .HostConfig.SecurityOpt)}}
{{printf "memory\t%s\n" (json .HostConfig.Memory)}}
{{printf "memory_swap\t%s\n" (json .HostConfig.MemorySwap)}}
{{printf "nano_cpus\t%s\n" (json .HostConfig.NanoCpus)}}
{{printf "pids_limit\t%s\n" (json .HostConfig.PidsLimit)}}
{{printf "restart\t%s\n" (json .HostConfig.RestartPolicy.Name)}}
{{printf "tmpfs\t%s\n" (json .HostConfig.Tmpfs)}}
{{printf "tmpfs_count\t%s\n" (json (len .HostConfig.Tmpfs))}}
{{printf "log_type\t%s\n" (json .HostConfig.LogConfig.Type)}}
{{printf "port_bindings\t%s\n" (json .HostConfig.PortBindings)}}
{{printf "shm_size\t%s\n" (json .HostConfig.ShmSize)}}
{{printf "binds\t%s\n" (json .HostConfig.Binds)}}
{{printf "host_config_mounts\t%s\n" (json .HostConfig.Mounts)}}
{{printf "mounts\t%s\n" (json .Mounts)}}
{{printf "image_id\t%s\n" (json .Image)}}
H3_DOCKER_INSPECT_PROJECTION
}

h3_compare_docker_projection() {
  local expected_id=$1 expected_name=$2 expected_jit=$3 expected_manifest=$4
  local expected_run=$5 expected_state=$6 expected_exit=$7 expected_tmpfs_path=$8
  local expected_tmpfs_options=$9 expected_log_type=${10} expected_image_id=${11} projection=${12}
  local tab key value seen='|' count=0
  local expected_tmpfs_json
  local -a mismatches=()
  tab=$(printf '\t')
  expected_tmpfs_json="{\"$expected_tmpfs_path\":\"$expected_tmpfs_options\"}"
  CONTROL_MISMATCH_FIELDS=''
  CONTROL_SCHEMA_ERROR=''

  [[ "$expected_id" =~ ^[a-f0-9]{64}$ ]] || { CONTROL_SCHEMA_ERROR=expected-id; return 2; }
  [[ "$expected_image_id" =~ ^sha256:[a-f0-9]{64}$ ]] || { CONTROL_SCHEMA_ERROR=expected-image-id; return 2; }
  [[ "$expected_tmpfs_path" == /* && "$expected_tmpfs_options" != *'"'* ]] \
    || { CONTROL_SCHEMA_ERROR=expected-tmpfs; return 2; }

  while IFS="$tab" read -r key value || [[ -n "$key" || -n "$value" ]]; do
    [[ -n "$key" && -n "$value" ]] || { CONTROL_SCHEMA_ERROR=empty-field; return 2; }
    case "$seen" in
      *"|$key|"*) CONTROL_SCHEMA_ERROR=duplicate-field; return 2 ;;
    esac
    seen+="$key|"
    count=$((count + 1))
    case "$key" in
      id) [[ "$value" == "\"$expected_id\"" ]] || mismatches+=(id) ;;
      name) [[ "$value" == "\"$expected_name\"" ]] || mismatches+=(name) ;;
      state) [[ "$value" == "\"$expected_state\"" ]] || mismatches+=(state) ;;
      exit_code) [[ "$value" == "$expected_exit" ]] || mismatches+=(exit_code) ;;
      oom) [[ "$value" == false ]] || mismatches+=(oom) ;;
      jit_label) [[ "$value" == "\"$expected_jit\"" ]] || mismatches+=(jit_label) ;;
      manifest_label) [[ "$value" == "\"$expected_manifest\"" ]] || mismatches+=(manifest_label) ;;
      run_label) [[ "$value" == "\"$expected_run\"" ]] || mismatches+=(run_label) ;;
      network_mode) [[ "$value" == '"none"' ]] || mismatches+=(network_mode) ;;
      readonly_root) [[ "$value" == true ]] || mismatches+=(readonly_root) ;;
      configured_user) [[ "$value" == '"1001:1001"' ]] || mismatches+=(configured_user) ;;
      cap_drop) [[ "$value" == '["ALL"]' ]] || mismatches+=(cap_drop) ;;
      security_opt) [[ "$value" == '["no-new-privileges:true"]' ]] || mismatches+=(security_opt) ;;
      memory) [[ "$value" == 134217728 ]] || mismatches+=(memory) ;;
      memory_swap) [[ "$value" == 134217728 ]] || mismatches+=(memory_swap) ;;
      nano_cpus) [[ "$value" == 500000000 ]] || mismatches+=(nano_cpus) ;;
      pids_limit) [[ "$value" == 64 ]] || mismatches+=(pids_limit) ;;
      restart) [[ "$value" == '"no"' ]] || mismatches+=(restart) ;;
      tmpfs) [[ "$value" == "$expected_tmpfs_json" ]] || mismatches+=(tmpfs) ;;
      tmpfs_count) [[ "$value" == 1 ]] || mismatches+=(tmpfs_count) ;;
      log_type) [[ "$value" == "\"$expected_log_type\"" ]] || mismatches+=(log_type) ;;
      port_bindings) [[ "$value" == null || "$value" == '{}' ]] || mismatches+=(port_bindings) ;;
      shm_size) [[ "$value" == 16777216 ]] || mismatches+=(shm_size) ;;
      binds) [[ "$value" == null || "$value" == '[]' ]] || mismatches+=(binds) ;;
      host_config_mounts) [[ "$value" == null || "$value" == '[]' ]] || mismatches+=(host_config_mounts) ;;
      mounts) [[ "$value" == null || "$value" == '[]' ]] || mismatches+=(mounts) ;;
      image_id) [[ "$value" == "\"$expected_image_id\"" ]] || mismatches+=(image_id) ;;
      *) CONTROL_SCHEMA_ERROR=unknown-field; return 2 ;;
    esac
  done <<< "$projection"

  [[ "$count" -eq 27 ]] || { CONTROL_SCHEMA_ERROR=field-count; return 2; }
  local required
  for required in id name state exit_code oom jit_label manifest_label run_label network_mode \
    readonly_root configured_user cap_drop security_opt memory memory_swap nano_cpus pids_limit \
    restart tmpfs tmpfs_count log_type port_bindings shm_size binds host_config_mounts mounts image_id; do
    case "$seen" in *"|$required|"*) ;; *) CONTROL_SCHEMA_ERROR=missing-field; return 2 ;; esac
  done
  if (("${#mismatches[@]}" > 0)); then
    CONTROL_MISMATCH_FIELDS=$(IFS=,; printf '%s' "${mismatches[*]}")
    return 1
  fi
  return 0
}
