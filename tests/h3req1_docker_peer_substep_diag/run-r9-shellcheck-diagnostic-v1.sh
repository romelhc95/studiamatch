#!/usr/bin/env bash
set -u -o pipefail
readonly PACKAGE='/tmp/h3req1-g03-validation-29d8fff9-r5'
readonly TOOLS='/tmp/h3req1-g03-validation-29d8fff9-r2.tools'
readonly ROOT='/home/romel/src/studiamatch-h3req1-sync-20261002'
readonly EXPECTED_BRANCH='feat/h3req1-sync-20261002'
readonly EXPECTED_HEAD='4eb4d877a50b012bb630a129bd0c74482c33be9c'
readonly EXPECTED_WIP='55/276/0'
readonly INNER_RUNNER='/home/romel/src/studiamatch-h3req1-sync-20261002/tests/h3req1_docker_peer_substep_diag/run-r9-shellcheck-diagnostic-inner-v1.sh'
readonly INNER_RUNNER_SHA256='4d5ded37449829a364f9c6655107e0e1af5ebbd3b62f79a1b41c24cdbdffe47d'
readonly IMAGE='sha256:5a1c95a749ec56d332265bc161c3d0b9da497d31349911d4f19abfeacc12ca63'
readonly IMAGE_TAG='studiamatch-h3req1:20261009-v3'
readonly MAX_OUTPUT_BYTES=8192

fail() {
  printf 'phase=%s|error_code=%s\nexit=%s\n' "$1" "$2" "${3:-1}"
  exit "${3:-1}"
}
verify_hash() {
  local got
  [[ -f "$1" && ! -L "$1" ]] || return 1
  got="$(/usr/bin/sha256sum -- "$1" 2>/dev/null)" || return 1
  [[ "${got%% *}" == "$2" ]]
}

[[ "$EUID" != 0 ]] || fail shellcheck-diagnostic-preflight RUN_AS_WSL_USER
[[ -t 0 ]] || fail shellcheck-diagnostic-preflight INTERACTIVE_TTY_REQUIRED
[[ "$(uname -s 2>/dev/null)" == Linux && "$(uname -r 2>/dev/null | tr '[:upper:]' '[:lower:]')" == *microsoft* ]] || fail shellcheck-diagnostic-preflight WSL_REQUIRED
[[ -n "$INNER_RUNNER_SHA256" ]] || fail shellcheck-diagnostic-preflight INNER_PIN_MISSING
verify_hash "$INNER_RUNNER" "$INNER_RUNNER_SHA256" || fail shellcheck-diagnostic-preflight INNER_RUNNER_HASH_MISMATCH
verify_hash "$PACKAGE/r4-package.sha256" '5363610a5fd28558f3e2168dd926aaf1c26037d01b2645de815da7201c00b0ae' || fail shellcheck-diagnostic-preflight PACKAGE_HASH_MISMATCH
verify_hash "$PACKAGE/inputs.sha256" '290905c8c88f56ce8c17aaf112e6536185068ea644008c685f299beeaeb1c57b' || fail shellcheck-diagnostic-preflight INPUT_MANIFEST_MISMATCH
verify_hash "$TOOLS/tools.sha256" '4c1b3551ac9f09c56f38b441ea33b560e72419c40a942c0103fea689cb094daa' || fail shellcheck-diagnostic-preflight TOOLS_MANIFEST_MISMATCH
(cd "$PACKAGE" && sha256sum -c r4-package.sha256 >/dev/null 2>&1 && sha256sum -c inputs.sha256 >/dev/null 2>&1) || fail shellcheck-diagnostic-preflight PACKAGE_MANIFEST_MISMATCH
(cd "$TOOLS" && sha256sum -c tools.sha256 >/dev/null 2>&1) || fail shellcheck-diagnostic-preflight TOOLS_MANIFEST_MISMATCH

[[ "$(git -C "$ROOT" branch --show-current 2>/dev/null)" == "$EXPECTED_BRANCH" ]] || fail shellcheck-diagnostic-identity BRANCH_MISMATCH
[[ "$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" == "$EXPECTED_HEAD" ]] || fail shellcheck-diagnostic-identity HEAD_MISMATCH
wip="$(git -C "$ROOT" status --porcelain=v1 2>/dev/null | awk 'BEGIN{m=0;u=0;s=0}{if(substr($0,1,2)=="??")u++;else m++;if(substr($0,1,1)!=" "&&substr($0,1,1)!="?")s++}END{printf "%d/%d/%d",m,u,s}')" || fail shellcheck-diagnostic-identity WIP_READ_FAILED
[[ "$wip" == "$EXPECTED_WIP" ]] || fail shellcheck-diagnostic-identity WIP_MISMATCH
if ! python3 - "$ROOT" "$PACKAGE/inputs.sha256" 2>/dev/null <<'PYSOURCE'
import hashlib
import sys
from pathlib import Path
root = Path(sys.argv[1])
rows = Path(sys.argv[2]).read_text(encoding='utf-8').splitlines()
package_only = {'fetch-linters.sh', 'run-in-container.sh', 'run-r8.sh'}
if len(rows) != 71:
    raise SystemExit(1)
missing = set()
checked = 0
for row in rows:
    digest, relative = row.split('  ', 1)
    if not relative.startswith('./'):
        raise SystemExit(1)
    relative = relative[2:]
    path = root / relative
    if not path.is_file() or path.is_symlink():
        if relative in package_only and not path.exists():
            missing.add(relative)
            continue
        raise SystemExit(1)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise SystemExit(1)
    checked += 1
if checked != 68 or missing != package_only:
    raise SystemExit(1)
PYSOURCE
then
  fail shellcheck-diagnostic-source SOURCE_DRIFT
fi

endpoint="$(/usr/bin/docker --context default context inspect default --format '{{ .Endpoints.docker.Host }}' 2>/dev/null)" || fail shellcheck-diagnostic-context CHECK_FAILED
[[ "$endpoint" == 'unix:///var/run/docker.sock' ]] || fail shellcheck-diagnostic-context ENDPOINT_MISMATCH
image_id="$(/usr/bin/docker --context default image inspect --format '{{.Id}}' "$IMAGE_TAG" 2>/dev/null)" || fail shellcheck-diagnostic-context IMAGE_READ_FAILED
[[ "$image_id" == "$IMAGE" ]] || fail shellcheck-diagnostic-context IMAGE_MISMATCH
printf 'phase=shellcheck-diagnostic-preflight|error_code=OK\n'

if output="$(/usr/bin/docker --context default run --rm --pull=never --network=none --read-only \
  --user 1001:1001 --cap-drop=ALL --security-opt=no-new-privileges --memory=384m --memory-swap=384m --cpus=1 --pids-limit=48 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=48m,uid=1001,gid=1001,mode=0700 \
  --tmpfs /lint-tools:rw,exec,nosuid,nodev,size=16m,uid=1001,gid=1001,mode=0700 \
  --mount "type=bind,src=$PACKAGE,dst=/validation,readonly" \
  --mount "type=bind,src=$TOOLS,dst=/validation-tools,readonly" \
  --mount "type=bind,src=$INNER_RUNNER,dst=/shellcheck-diagnostic.sh,readonly" \
  --workdir /validation --env PYTHONDONTWRITEBYTECODE=1 --env HOME=/tmp --env NO_COLOR=1 --env TERM=dumb \
  --entrypoint bash "$IMAGE" -euc 'bash /shellcheck-diagnostic.sh' 2>/dev/null)"; then
  status=0
else
  status=$?
fi
if (( ${#output} > MAX_OUTPUT_BYTES )); then fail shellcheck-diagnostic-output OUTPUT_REJECTED; fi

safe=''
invalid=0
readonly PHASE_RE='^phase=(shellcheck-diagnostic-preflight|shellcheck-diagnostic-tool-extraction|shellcheck-diagnostic-synthetics|shellcheck-diagnostic|shellcheck-diagnostic-output)[|]error_code=[A-Z_]{1,48}$'
readonly DIAG_RE='^diagnostic=script=(\.githooks/(pre-commit|pre-push)|scripts/security/(h2_web_mock_smoke|protected_path_scope_guard|scan_credentials)[.]sh|tests/sql/h3_invitation_reservation_concurrency[.]sh|tests/test_protected_path_scope_guard[.]sh)[|]line=[0-9]{1,6}[|]column=[0-9]{1,6}[|]rule=SC[0-9]{4}$'
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  if [[ "$line" =~ $PHASE_RE || "$line" =~ $DIAG_RE || "$line" =~ ^exit=[0-9]{1,3}$ ]]; then
    safe+="${line}"$'\n'
  else
    invalid=1
    break
  fi
done <<< "$output"
(( invalid == 0 )) || fail shellcheck-diagnostic-output OUTPUT_REJECTED
if (( status == 0 )); then
  expected=$'phase=shellcheck-diagnostic-preflight|error_code=OK\nphase=shellcheck-diagnostic-tool-extraction|error_code=OK\nphase=shellcheck-diagnostic-synthetics|error_code=OK\nphase=shellcheck-diagnostic|error_code=OK\nexit=0\n'
  [[ "$safe" == "$expected" ]] || fail shellcheck-diagnostic-summary OUTPUT_MISMATCH
  printf '%s' "$safe"
  exit 0
fi
[[ -n "$safe" ]] || fail shellcheck-diagnostic-container CHECK_FAILED "$status"
printf '%s' "$safe"
[[ "$safe" == *$'exit='* ]] || printf 'exit=%s\n' "$status"
exit "$status"
