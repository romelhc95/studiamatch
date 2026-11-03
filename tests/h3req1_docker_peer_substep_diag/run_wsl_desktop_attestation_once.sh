#!/bin/bash
set -Eeuo pipefail

readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly BRANCH='feat/h3req1-sync-20261002'
readonly HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly HELPER='tests/h3req1_docker_peer_substep_diag/desktop_wsl_attestation_once.py'
readonly HELPER_SHA256='c25aa3d3d91bb0cadc160b090c49c4bc61362baefaf3415d046ce7a9cabea4cb'
readonly PROJECTION='tests/h3req1_docker_peer_substep_diag/diagnostic_once.py'
readonly PROJECTION_SHA256='794b49ce5560c8cacebbd403c05b4cdbe78fd0c0062d30b6690b901838831463'

emit_failure() {
  printf 'phase=wsl-attestation-runner|error_code=%s\n' "$1"
  exit 1
}

[[ -d "$ROOT" && ! -L "$ROOT" ]] || emit_failure 'CHECKOUT_UNAVAILABLE'
cd -- "$ROOT" || emit_failure 'CHECKOUT_UNAVAILABLE'
[[ "$(pwd -P 2>/dev/null)" == "$ROOT" ]] || emit_failure 'CHECKOUT_MISMATCH'
[[ -f "$HELPER" && ! -L "$HELPER" && -f "$PROJECTION" && ! -L "$PROJECTION" ]] \
  || emit_failure 'HELPER_UNAVAILABLE'

git_root="$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse --show-toplevel 2>/dev/null)" \
  || emit_failure 'GIT_PREFLIGHT_FAILED'
branch="$(/usr/bin/git -c "safe.directory=$ROOT" branch --show-current 2>/dev/null)" \
  || emit_failure 'GIT_PREFLIGHT_FAILED'
head="$(/usr/bin/git -c "safe.directory=$ROOT" rev-parse HEAD 2>/dev/null)" \
  || emit_failure 'GIT_PREFLIGHT_FAILED'
[[ "$git_root" == "$ROOT" && "$branch" == "$BRANCH" && "$head" == "$HEAD" ]] \
  || emit_failure 'CANDIDATE_MISMATCH'

helper_hash_line="$(/usr/bin/sha256sum -- "$HELPER" 2>/dev/null)" \
  || emit_failure 'HELPER_HASH_FAILED'
[[ "${helper_hash_line%% *}" == "$HELPER_SHA256" ]] || emit_failure 'HELPER_HASH_MISMATCH'
projection_hash_line="$(/usr/bin/sha256sum -- "$PROJECTION" 2>/dev/null)" \
  || emit_failure 'PROJECTION_HASH_FAILED'
[[ "${projection_hash_line%% *}" == "$PROJECTION_SHA256" ]] \
  || emit_failure 'PROJECTION_HASH_MISMATCH'
[[ -x /usr/bin/python3 && -x /usr/bin/timeout && -x /usr/bin/docker ]] \
  || emit_failure 'RUNTIME_UNAVAILABLE'

exec /usr/bin/timeout --foreground --signal=TERM --kill-after=1s 50s \
  /usr/bin/env -i \
  HOME=/home/romel \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/python3 -B "$ROOT/$HELPER" 2>/dev/null
