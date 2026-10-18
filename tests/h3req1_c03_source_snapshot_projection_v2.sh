#!/usr/bin/env bash

h3_source_snapshot_inspect_format() {
  cat <<'H3_SOURCE_SNAPSHOT_INSPECT_FORMAT'
{{.Id}}|{{.Name}}|{{.State.Status}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{with .Config.Labels}}{{index . "com.studiamatch.h3.snapshot.jit"}}{{end}}|{{with .Config.Labels}}{{index . "com.studiamatch.h3.snapshot.manifest"}}{{end}}|{{with .Config.Labels}}{{index . "com.studiamatch.h3.snapshot.run"}}{{end}}|{{.HostConfig.NetworkMode}}|{{.HostConfig.ReadonlyRootfs}}|{{.Config.User}}|{{json .HostConfig.CapDrop}}|{{json .HostConfig.SecurityOpt}}|{{.HostConfig.Memory}}|{{.HostConfig.MemorySwap}}|{{.HostConfig.NanoCpus}}|{{.HostConfig.PidsLimit}}|{{.HostConfig.RestartPolicy.Name}}|{{with .HostConfig.Tmpfs}}{{index . "/snapshot"}}{{end}}|{{len .HostConfig.Tmpfs}}|{{.HostConfig.LogConfig.Type}}|{{json .HostConfig.PortBindings}}|{{.HostConfig.ShmSize}}|{{json .HostConfig.Binds}}|{{json .HostConfig.Mounts}}
H3_SOURCE_SNAPSHOT_INSPECT_FORMAT
}

h3_source_snapshot_read_bounded_template() {
  local container_id=$1 maximum_seconds=$2 template=$3
  local encoded byte_count hex decoded byte_offset byte_pair

  H3_SOURCE_SNAPSHOT_READ_RESULT=''
  [[ "$container_id" =~ ^[a-f0-9]{64}$ && "$maximum_seconds" =~ ^([1-9]|1[0-5])$ \
    && ${#template} -le 8192 ]] || return 1
  encoded="$(set -o pipefail; docker_control_with_limit "$maximum_seconds" inspect \
    --format "$template" "$container_id" 2>/dev/null | head -c 8193 | base64 -w0)" || return 1
  [[ "$encoded" =~ ^[A-Za-z0-9+/]*={0,2}$ && ${#encoded} -le 10924 ]] || return 1

  byte_count="$(set -o pipefail; printf '%s' "$encoded" | base64 --decode 2>/dev/null | wc -c)" \
    || return 1
  byte_count="${byte_count//[[:space:]]/}"
  [[ "$byte_count" =~ ^[0-9]+$ ]] && (( byte_count <= 8192 )) || return 1
  hex="$(set -o pipefail; printf '%s' "$encoded" | base64 --decode 2>/dev/null \
    | od -An -v -tx1 | tr -d '[:space:]')" || return 1
  [[ ${#hex} -le 16384 && "$hex" =~ ^([a-f0-9]{2})*$ ]] || return 1
  for ((byte_offset = 0; byte_offset < ${#hex}; byte_offset += 2)); do
    byte_pair="${hex:byte_offset:2}"
    [[ "$byte_pair" != 0d && "$byte_pair" != 00 ]] || return 1
    if [[ "$byte_pair" == 0a && $((byte_offset + 2)) -ne ${#hex} ]]; then
      return 1
    fi
  done
  # Docker CLI terminates each --format result with one LF; accept only that
  # framing byte and reject embedded or repeated line breaks.
  if [[ "$hex" == *0a ]]; then
    hex="${hex%0a}"
  fi
  decoded="$(printf '%s' "$encoded" | base64 --decode 2>/dev/null)" || return 1
  H3_SOURCE_SNAPSHOT_READ_RESULT="$decoded"
}

h3_source_snapshot_collect_metadata_inner() {
  local container_id=$1 maximum_seconds=$2 format base_format value index next_base
  local -a expressions=() base_expressions=() base_values=() metadata_fields=()
  local -a isolated_indexes=(15 18 19 24)
  local isolated candidate

  H3_SOURCE_SNAPSHOT_METADATA=''
  H3_SOURCE_SNAPSHOT_READ_RESULT=''
  [[ "$maximum_seconds" =~ ^([1-9]|1[0-5])$ ]] || return 1
  format="$(h3_source_snapshot_inspect_format)" || return 1
  [[ ${#format} -le 8192 ]] || return 1
  IFS='|' read -r -a expressions <<< "$format"
  [[ ${#expressions[@]} -eq 25 ]] || return 1
  for candidate in "${expressions[@]}"; do
    [[ "$candidate" == '{{'*'}}' ]] || return 1
  done

  for index in "${!expressions[@]}"; do
    isolated=false
    for candidate in "${isolated_indexes[@]}"; do
      [[ "$index" == "$candidate" ]] && isolated=true
    done
    [[ "$isolated" == true ]] || base_expressions+=("${expressions[$index]}")
  done
  [[ ${#base_expressions[@]} -eq 21 ]] || return 1
  base_format="$(IFS='|'; printf '%s' "${base_expressions[*]}")"

  h3_source_snapshot_read_bounded_template "$container_id" "$maximum_seconds" "$base_format" \
    || return 1
  IFS='|' read -r -a base_values <<< "$H3_SOURCE_SNAPSHOT_READ_RESULT"
  [[ ${#base_values[@]} -eq 21 ]] || return 1

  next_base=0
  for index in "${!expressions[@]}"; do
    isolated=false
    for candidate in "${isolated_indexes[@]}"; do
      [[ "$index" == "$candidate" ]] && isolated=true
    done
    if [[ "$isolated" == true ]]; then
      h3_source_snapshot_read_bounded_template "$container_id" "$maximum_seconds" \
        "${expressions[$index]}" || return 1
      value="$H3_SOURCE_SNAPSHOT_READ_RESULT"
      [[ "$value" != *'|'* && "$value" != *$'\n'* && "$value" != *$'\r'* ]] || return 1
      metadata_fields+=("$value")
    else
      (( next_base < ${#base_values[@]} )) || return 1
      metadata_fields+=("${base_values[$next_base]}")
      next_base=$((next_base + 1))
    fi
  done
  [[ "$next_base" -eq 21 && ${#metadata_fields[@]} -eq 25 ]] || return 1

  H3_SOURCE_SNAPSHOT_METADATA="$(IFS='|'; printf '%s' "${metadata_fields[*]}")"
  [[ ${#H3_SOURCE_SNAPSHOT_METADATA} -le 8192 \
    && "$H3_SOURCE_SNAPSHOT_METADATA" != *$'\n'* \
    && "$H3_SOURCE_SNAPSHOT_METADATA" != *$'\r'* ]] || {
      H3_SOURCE_SNAPSHOT_METADATA=''
      return 1
    }
  return 0
}

h3_source_snapshot_collect_metadata() {
  H3_SOURCE_SNAPSHOT_METADATA=''
  H3_SOURCE_SNAPSHOT_READ_RESULT=''
  if h3_source_snapshot_collect_metadata_inner "$@"; then
    return 0
  fi
  H3_SOURCE_SNAPSHOT_METADATA=''
  H3_SOURCE_SNAPSHOT_READ_RESULT=''
  return 1
}
