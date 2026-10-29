#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
source tests/h3req1_c03_source_snapshot_projection_v2.sh

fail() {
  printf 'source snapshot projection v2 regression failed: %s\n' "$1" >&2
  exit 1
}

tmp_dir="$(mktemp -d /tmp/h3req1-source-projection-v2.XXXXXX)" || fail 'temporary directory unavailable'
trap 'rm -rf -- "$tmp_dir"' EXIT
CALL_TRACE="$tmp_dir/calls"
touch "$CALL_TRACE"

readonly SYNTHETIC_CONTAINER_ID='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
readonly TEMPFS_VALUE='rw,noexec,nosuid,nodev,size=96m,uid=1001,gid=1001,mode=0700'
readonly -a ISOLATED_INDEXES=(15 18 19 24)

make_fixture() {
  local maps_present=$1
  FIXTURE_FIELDS=(
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    '/h3req1-synthetic' 'created' '0' 'false'
    'H3-CLOSE-03-SOURCE-SNAPSHOT-F1-2026-10-07'
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc'
    '1000-1-2-3' 'none' 'true' '1001:1001' '["ALL"]'
    '["no-new-privileges:true"]' '134217728' '134217728' '500000000'
    '64' 'no' "$TEMPFS_VALUE" '1' 'none' 'null' '16777216' 'null' 'null'
  )
  if [[ "$maps_present" == false ]]; then
    FIXTURE_FIELDS[5]=''
    FIXTURE_FIELDS[6]=''
    FIXTURE_FIELDS[7]=''
    FIXTURE_FIELDS[18]=''
    FIXTURE_FIELDS[19]='0'
  fi
}

join_fields() {
  local IFS='|'
  printf '%s' "$*"
}

expected_base_format() {
  local format
  format="$(h3_source_snapshot_inspect_format)"
  local -a expressions=()
  IFS='|' read -r -a expressions <<< "$format"
  local -a selected=()
  local index isolated
  for index in "${!expressions[@]}"; do
    isolated=false
    for isolated_index in "${ISOLATED_INDEXES[@]}"; do
      [[ "$index" == "$isolated_index" ]] && isolated=true
    done
    [[ "$isolated" == true ]] || selected+=("${expressions[$index]}")
  done
  join_fields "${selected[@]}"
}

docker_control_with_limit() {
  local limit=$1 command=$2 option=$3 format=$4 container_id=$5
  [[ "$limit" =~ ^[1-9][0-9]*$ && "$command" == inspect && "$option" == --format \
    && "$container_id" == "$SYNTHETIC_CONTAINER_ID" ]] || return 90
  printf '%s\n' "$format" >> "$CALL_TRACE"

  case "$MOCK_MODE" in
    fail-docker) return 17 ;;
    fail-isolated)
      [[ "$format" == "$(expected_base_format)" ]] || return 17
      ;;
    fail-second-isolated) : ;;
    oversize)
      head -c 8193 /dev/zero | tr '\000' 'x'
      return 0
      ;;
  esac

  local full_format expected_base index
  full_format="$(h3_source_snapshot_inspect_format)"
  expected_base="$(expected_base_format)"
  if [[ "$format" == "$expected_base" ]]; then
    local -a base_values=()
    for index in "${!FIXTURE_FIELDS[@]}"; do
      local isolated=false isolated_index
      for isolated_index in "${ISOLATED_INDEXES[@]}"; do
        [[ "$index" == "$isolated_index" ]] && isolated=true
      done
      [[ "$isolated" == true ]] || base_values+=("${FIXTURE_FIELDS[$index]}")
    done
    join_fields "${base_values[@]}"
    printf '\n'
    return 0
  fi

  local -a expressions=()
  IFS='|' read -r -a expressions <<< "$full_format"
  for index in "${ISOLATED_INDEXES[@]}"; do
    if [[ "$format" == "${expressions[$index]}" ]]; then
      case "$MOCK_MODE:$index" in
        fail-second-isolated:18) return 17 ;;
        pipe-field:15) printf 'bad|field\n' ;;
        newline-field:15) printf 'bad\nfield\n' ;;
        double-newline:15) printf '%s\n\n' "${FIXTURE_FIELDS[$index]}" ;;
        cr-field:15) printf 'bad\rfield\n' ;;
        nul-field:15) printf 'bad\0field\n' ;;
        *) printf '%s\n' "${FIXTURE_FIELDS[$index]}" ;;
      esac
      return 0
    fi
  done
  return 91
}

last_read_class() {
  local last_call index
  local -a expressions=()
  last_call="$(tail -n 1 "$CALL_TRACE")"
  [[ "$last_call" == "$(expected_base_format)" ]] && { printf 'base'; return; }
  IFS='|' read -r -a expressions <<< "$(h3_source_snapshot_inspect_format)"
  for index in "${ISOLATED_INDEXES[@]}"; do
    [[ "$last_call" == "${expressions[$index]}" ]] && { printf 'isolated-%s' "$index"; return; }
  done
  printf 'unmatched'
}

assert_expected_projection() {
  local label=$1 index
  local expected
  expected="$(join_fields "${FIXTURE_FIELDS[@]}")"
  [[ "$H3_SOURCE_SNAPSHOT_METADATA" == "$expected" ]] || fail "$label field order/composition changed"
  [[ "$(wc -l < "$CALL_TRACE" | tr -d '[:space:]')" == 5 ]] || fail "$label did not use one base plus four isolated reads"
  local -a calls=()
  mapfile -t calls < "$CALL_TRACE"
  [[ "${calls[0]}" == "$(expected_base_format)" ]] || fail "$label base read contains isolated field"
  local call_index=1
  local -a expressions=()
  IFS='|' read -r -a expressions <<< "$(h3_source_snapshot_inspect_format)"
  for index in "${ISOLATED_INDEXES[@]}"; do
    [[ "${calls[$call_index]}" == "${expressions[$index]}" ]] || fail "$label isolated field order differs"
    call_index=$((call_index + 1))
  done
}

MOCK_MODE=valid
make_fixture true
if ! h3_source_snapshot_collect_metadata "$SYNTHETIC_CONTAINER_ID" 5; then
  fail "present-map composition rejected at $(last_read_class) after $(wc -l < "$CALL_TRACE" | tr -d '[:space:]') reads"
fi
assert_expected_projection 'present-map'

: > "$CALL_TRACE"
make_fixture false
if ! h3_source_snapshot_collect_metadata "$SYNTHETIC_CONTAINER_ID" 5; then
  fail 'absent-map projection composition was rejected'
fi
assert_expected_projection 'absent-map'

for MOCK_MODE in fail-docker fail-isolated fail-second-isolated pipe-field newline-field \
  double-newline cr-field nul-field oversize; do
  : > "$CALL_TRACE"
  make_fixture true
  H3_SOURCE_SNAPSHOT_METADATA='stale-metadata'
  if h3_source_snapshot_collect_metadata "$SYNTHETIC_CONTAINER_ID" 5; then
    fail "$MOCK_MODE was accepted"
  fi
  [[ -z "$H3_SOURCE_SNAPSHOT_METADATA" ]] || fail "$MOCK_MODE left stale metadata available"
  [[ -z "$H3_SOURCE_SNAPSHOT_READ_RESULT" ]] || fail "$MOCK_MODE left intermediate metadata available"
done

MOCK_MODE=valid
make_fixture true
: > "$CALL_TRACE"
if h3_source_snapshot_collect_metadata "$SYNTHETIC_CONTAINER_ID" 16; then
  fail 'timeout above the hard cap was accepted'
fi
[[ -z "$H3_SOURCE_SNAPSHOT_METADATA" && -z "$H3_SOURCE_SNAPSHOT_READ_RESULT" ]] \
  || fail 'timeout rejection retained metadata'
[[ ! -s "$CALL_TRACE" ]] || fail 'timeout above hard cap reached Docker'

if h3_source_snapshot_collect_metadata \
  "$SYNTHETIC_CONTAINER_ID" 999999999999999999999999999999999999999999999999; then
  fail 'overflow-sized timeout was accepted'
fi
[[ -z "$H3_SOURCE_SNAPSHOT_METADATA" && -z "$H3_SOURCE_SNAPSHOT_READ_RESULT" ]] \
  || fail 'overflow-sized timeout rejection retained metadata'
[[ ! -s "$CALL_TRACE" ]] || fail 'overflow-sized timeout reached Docker'

printf 'source-snapshot-projection-v2=PASS|composition=25|maps=present-absent|isolated-fields=4|negative-cases=11\n'
