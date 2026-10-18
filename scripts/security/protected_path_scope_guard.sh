#!/usr/bin/env bash
# Convert Git's NUL-delimited path list to safe line records for the allowlist.

protected_path_scope_capture() {
  local paths_file=$1 candidate=''

  if [[ ! -f "$paths_file" || ! -r "$paths_file" ]]; then
    printf '%s\n' '::error::protected path list is missing or unreadable' >&2
    return 2
  fi

  while :; do
    candidate=''
    if IFS= read -r -d '' candidate; then
      if [[ -z "$candidate" ]]; then
        printf '%s\n' '::error::protected path list contains an empty record' >&2
        return 2
      fi
      if [[ "$candidate" == *$'\n'* || "$candidate" == *$'\r'* || "$candidate" == *$'\t'* ]]; then
        printf '%s\n' '::error::protected path list contains an unsupported control character' >&2
        return 2
      fi
      printf '%s\n' "$candidate"
    else
      if [[ -z "$candidate" ]]; then
        break
      fi
      printf '%s\n' '::error::protected path list is malformed' >&2
      return 2
    fi
  done <"$paths_file"
}
